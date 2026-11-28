"""The Seed: a History table's past rows, loaded once, before its first write (Toolbox 8.10).

A History table keeps the rows each write adds, so a new copy of one, in dev or prod, holds
only what its writes have added since it was made: its Seed loads the past rows first, so it
is usable from its first day. Its limit, SEED in its Table reference, picks which:
{"months": N}, the N calendar months up to the newest Partition its source holds, both ends
included, by its column of dates, the one partition column whose every value SHOW PARTITIONS
lists reads as a date; or, by partition column, a value, a range or a list, as 8.4's seed
limits are.

- With an Original, the Seed copies the Original's rows, as seed_copy writes it. In prod it
  copies from the dev copy's Original, or, for a table with none, from the dev copy itself.
- With none, it runs the table's own write once for each past day, oldest first, as of that
  day: the day goes wherever the write reads today, CURRENT_DATE in its Hive or today() in a
  Run value, so a write that targets yesterday runs as of the day after. Only the run's today
  changes, never the logic, so each run writes the one Partition a scheduled write writes.

project.seed_tables runs it, in the step of each Workflow that writes the table, while the
table holds no Partitions yet (no row, for one with none), so running the step again never
loads twice. A day that fails doesn't stop it: its report lists each day not loaded, with the
warehouse's error, and each that wrote no rows.
"""

from __future__ import annotations

import calendar
import datetime
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from . import decisions, kinds
from .clauses import Statement
from .conditions import run_as_of, today
from .converting import day_on_column, day_written
from .describe import printed_answer
from .project_files import REFERENCE, table_stem
from .refusals import callers_frame
from .run_values import HIVE_DEFAULT_PARTITION, listed_text
from .shared import counted, in_words
from .tables import Table, type_family
from .unchecked import (
    SessionSettings,
    UncheckedStatement,
    hive_settings,
    logged_run,
    record_sent,
    seed_copy,
    tables_read_and_written,
)
from .workflows import BATCH_RECORD, BATCHES, FINISHED, SEED_SENT, promoted_record

if TYPE_CHECKING:  # project.py imports this file, so its names are for the hints alone
    import pandas as pd

    from .project import TableLogic


@dataclass
class SeedRun:
    """What one table's Seed needs and says: the table, its Table reference, your query and
    execute (None for a dry run, which sends nothing), and its report's lines so far."""

    name: str
    table: Table
    query: Callable[[str], pd.DataFrame]
    execute: Callable[[str], None] | None
    lines: list[str] = field(default_factory=list)

    @property
    def call(self) -> str:
        """The call each line of the Admin log names for this Seed."""
        return f"project.seed_tables(...) of {self.name}"

    def send(self, hive: str, said: str) -> None:
        """Send one Statement of the Seed through your execute, its Admin log entry headed
        `said`, and record it in admin/sent.csv; in a dry run, say it would send it."""
        if self.execute is None:
            self.lines += [f"would send: {line}" for line in hive.split("\n")]
            return
        logged_run(said, self.call, hive, self.execute)
        record_sent(SEED_SENT, hive, callers_frame())

    def send_settings(self, settings: SessionSettings) -> None:
        """Send Session settings the Seed needs, each SET line in a call of its own, as Hive
        takes them; in a dry run, say it would send each."""
        for line in settings._lines:
            if self.execute is None:
                self.lines.append(f"would send: {line}")
            else:
                self.execute(line)


# --- The column of dates, and the months form -----------------------------------------------


def listed_partitions(query: Callable[[str], pd.DataFrame], name: str,
                      call: str) -> list[dict[str, str]]:
    """Each Partition a table holds, as SHOW PARTITIONS lists it through your query, as its
    value by each partition column, such as {"region": "eu", "dt": "20260911"}."""
    listed = printed_answer(query, f"SHOW PARTITIONS {name}", call)
    found = []
    for row in listed.itertuples(index=False):
        values = {}
        for part in str(row[0]).split("/"):
            column, _, value = part.partition("=")
            values[column.strip().lower()] = listed_text(value.strip())
        found.append(values)
    return found


def date_partitions(listed: list[dict[str, str]]) -> list[str]:
    """Each partition column whose every value `listed` gives reads as a date, 2026-09-24 or
    20260924, Hive's Partition for no value passed over; none when nothing is listed."""
    columns = list(dict.fromkeys(column for partition in listed for column in partition))
    found = []
    for column in columns:
        values = [partition.get(column, "") for partition in listed
                  if partition.get(column) != HIVE_DEFAULT_PARTITION]
        if values and all(day_written(value) is not None for value in values):
            found.append(column)
    return found


def months_before(day: datetime.date, months: int) -> datetime.date:
    """The day `months` calendar months before `day`, the last of its month where that month
    is shorter: 2 months before 2026-11-27 is 2026-09-27, 1 before 2026-03-31 is 2026-02-28."""
    month = day.month - months
    year = day.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    return datetime.date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def written_like(day: datetime.date, like: str) -> str:
    """A day written as `like`, a value of the same partition column, writes one: 20260924 for
    one written so, else 2026-09-24."""
    if re.fullmatch(r"\d{8}", like):
        return day.strftime("%Y%m%d")
    return day.isoformat()


def proposed_seed(query: Callable[[str], pd.DataFrame] | None, sources: list[str],
                  partitions: list[str], original: bool
                  ) -> tuple[dict[str, object] | None, str]:
    """The seed limits proposed for a table, and why, as seed_block writes them: one month,
    {"months": 1}, where a partition column of its source holds dates alone; else none, saying
    why. `sources` are the tables to read for it: its Original, or, with none, each table its
    write reads, the first with a column of dates its source. A table with no Partitions copies
    every row of its Original, or, with none, counts the months back from today."""
    if not partitions and original:
        return {}, f"no Partitions: its Seed copies every row of {sources[0]}"
    if not partitions:
        return dict(decisions.PROPOSED_MONTHS), ("no Partitions, no Original: its write runs "
                                                 "as of each day of the month")
    if query is None:
        return None, "no query was given to read the Partitions of what it reads"
    found, why = date_source(query, sources, "a seed limit's proposal")
    if found is None:
        return None, why
    source, column, _ = found
    return dict(decisions.PROPOSED_MONTHS), f"{column} holds dates in {source}"


def date_source(query: Callable[[str], pd.DataFrame], sources: list[str], call: str
                ) -> tuple[tuple[str, str, list[str]] | None, str]:
    """The first of `sources` with a column of dates: its name, the column, and each of its
    values, as SHOW PARTITIONS lists them; or None, and why none is. A table that can't be
    read, or isn't partitioned, is passed over."""
    why = f"no partition column of {in_words(sources) or 'what it reads'} holds dates alone"
    unread = []
    for source in sources:
        try:
            listed = listed_partitions(query, source, call)
        # What the warehouse says of a table it can't list, or that isn't partitioned.
        except Exception:  # noqa: BLE001
            unread.append(source)
            if unread == sources:
                why = (f"the Partitions of {in_words(unread)} couldn't be read through your "
                       "query")
            continue
        columns = date_partitions(listed)
        if len(columns) > 1:
            return None, f"{in_words(columns)} each hold dates alone in {source}"
        if columns:
            values = [partition[columns[0]] for partition in listed
                      if partition.get(columns[0]) not in (None, HIVE_DEFAULT_PARTITION)]
            return (source, columns[0], values), ""
        if not listed:
            why = f"{source} holds no Partition yet, so nothing says which column holds dates"
    return None, why


# --- One table's Seed ------------------------------------------------------------------------


def seed_lines(root: Path, name: str, query: Callable[[str], pd.DataFrame],
               execute: Callable[[str], None] | None) -> list[str]:
    """One table's Seed, sent through your execute, or, with none, shown as a dry run: its
    report's lines. Only a History table that holds no Partitions yet, or no row for one with
    none, is seeded; a table seeded before 8.10 keeps its seed()."""
    from . import project  # project.py imports this file

    text = (root / REFERENCE.shown(table_stem(name))).read_text(encoding="utf-8")
    logic = project.load(name)
    kind = decisions.table_kind(text)
    old_seed = hasattr(logic, "seed") and kind != decisions.TableKind.REBUILT
    if kind != decisions.TableKind.HISTORY and not old_seed:
        return [f"{name}: no Seed, as {_why_no_seed(kind)}."]
    run = SeedRun(name, project.table_reference(name), query, execute)
    if _holds_rows(run):
        return [f"{name}: no Seed: it holds rows already, so it was seeded, or written, "
                "before."]
    if old_seed:
        return _old_seed_sent(run, logic)
    if decisions.open_decisions(text, name, (decisions.SEED_LIMIT,)):
        return [f"{name}: no Seed: its SEED is still open. Answer \"seed\" in the decisions "
                "cell, write the answers in, and run this step again."]
    limits = project.run_logic(root, f"from references.{table_stem(name)} import SEED",
                               "seed_limits")["SEED"]
    source, said = source_to_copy(root, name)
    if source is not None:
        return _copied(run, source, said, dict(limits))
    return _run_as_of_each_day(run, logic, dict(limits))


def _why_no_seed(kind: decisions.TableKind | None) -> str:
    """Why a table that isn't a History table has no Seed."""
    if kind == decisions.TableKind.REBUILT:
        return "it is a Rebuilt table, which each write replaces whole"
    return "its Table reference says no kind, Rebuilt or History"


def _holds_rows(run: SeedRun) -> bool:
    """Whether the table holds a Partition, or a row for one with none, through your query: in
    a dry run, one that can't be read isn't created yet, so it holds none."""
    hive = f"SELECT 1 AS one FROM {run.name} LIMIT 1"
    if run.table._partitioned_by:
        hive = f"SHOW PARTITIONS {run.name}"
    try:
        return len(printed_answer(run.query, hive, run.call)) > 0
    # In a dry run the table isn't created yet: whatever the warehouse says, it holds nothing.
    except Exception:
        if run.execute is None:
            return False
        raise


def _old_seed_sent(run: SeedRun, logic: TableLogic) -> list[str]:
    """The seed() a table converted before 8.10 has in its logic, sent as it was, after the
    Session setting its Partitions need."""
    from .running import to_hive  # running imports what imports this

    run.lines.append(f"{run.name}: its Seed, its seed() as converted before 8.10:")
    if run.table._partitioned_by:
        run.send_settings(hive_settings("dynamic_partitions"))
    run.send(to_hive(logic.seed()), "Seed")
    if run.execute is not None:
        run.lines.append(f"Seeded {run.name} with its seed().")
    return run.lines


def source_to_copy(root: Path, name: str) -> tuple[str | None, str]:
    """The table a Seed copies, and what it is to `name`: its Original; for a prod copy, its
    dev copy's Original, or the dev copy where that has none; None for a table with no
    Original, which runs its own write as of each day."""
    record = promoted_record(root)
    if name in record:
        dev = str(record[name]["dev"])
        original = _original_in_records(root, dev)
        if original is None:
            return dev, f"{dev}, its dev copy, which has no Original"
        return original, f"{original}, its dev copy's Original"
    original = _original_in_records(root, name)
    if original is None:
        return None, ""
    return original, f"{original}, its Original"


def _original_in_records(root: Path, table: str) -> str | None:
    """The Original of a dev table, as the record of the batch that converted it says; None
    for a table no batch converted, or one made from a query alone."""
    folder = root / BATCHES
    for path in sorted([*folder.glob(f"*/{BATCH_RECORD}"),
                        *folder.glob(f"{FINISHED}/*/{BATCH_RECORD}")]):
        originals = json.loads(path.read_text(encoding="utf-8")).get("originals", {})
        if originals.get(table):
            return str(originals[table])
    return None


# --- A Seed copied from an Original ----------------------------------------------------------


def _copied(run: SeedRun, source: str, said: str, limits: dict[str, object]) -> list[str]:
    """A Seed copied from `source`, what `said` says it is, limited by `limits`, the months
    form worked out from its newest Partition: the lines saying what was loaded."""
    resolved, why = _with_months_worked_out(run, source, limits)
    if resolved is None:
        return [f"{run.name}: no Seed: {why}."]
    run.lines.append(f"{run.name}: its Seed, copied from {said}:")
    if run.table._partitioned_by:
        run.send_settings(hive_settings("dynamic_partitions"))
    try:
        run.send(seed_copy(run.table, source, resolved)._text, "Seed")
    # The warehouse's error is the Seed's to report: the write after it still runs.
    except Exception as error:  # noqa: BLE001
        run.lines.append(f"  Not loaded: {_first_line(error)}")
        return run.lines
    if run.execute is not None:
        run.lines.append(_loaded_line(run, source, resolved))
    return run.lines


def _with_months_worked_out(run: SeedRun, source: str, limits: dict[str, object]
                            ) -> tuple[dict[str, object] | None, str]:
    """Seed limits with their months form, {"months": N}, as a range on its column of dates,
    from N calendar months before the newest Partition `source` holds to that one, each
    written as its values are; None, and why, where `source` has no column of dates. A table
    with no Partitions is copied whole."""
    months = limits.pop(decisions.MONTHS, None)
    if months is None or not run.table._partitioned_by:
        return limits, ""
    found, why = date_source(run.query, [source], run.call)
    if found is None:
        return None, (f"its SEED's months form needs a partition column whose every value is "
                      f"a date, and {why}")
    _, column, values = found
    newest = max(values, key=day_written)
    start = months_before(day_written(newest), int(months))
    return {**limits, column: {"from": written_like(start, newest), "to": newest}}, ""


def _loaded_line(run: SeedRun, source: str, limits: dict[str, object]) -> str:
    """What a copied Seed loaded: its Partitions, read back through your query, or every row
    of a table with none."""
    if not run.table._partitioned_by:
        return f"Seeded {run.name}: every row of {source}."
    limited = [f"{column} from {limit['from']} to {limit['to']}"
               for column, limit in limits.items() if isinstance(limit, dict)
               and {"from", "to"} <= set(limit)]
    loaded = listed_partitions(run.query, run.name, run.call)
    said = f"Seeded {run.name}: {counted(len(loaded), 'Partition')} loaded"
    if limited:
        said += f", {in_words(limited)}"
    return said + "."


def _first_line(error: Exception) -> str:
    """The first line of what an error says, the warehouse's or a refusal's."""
    lines = [line.strip() for line in str(error).strip().split("\n") if line.strip()]
    return lines[0] if lines else type(error).__name__


# --- A Seed run as of each past day ----------------------------------------------------------


@dataclass(frozen=True)
class DaysToRun:
    """The days a Seed runs a write for: each day it writes, oldest first, as written in its
    partition column; the column, None for a table with no Partitions; and how many days
    after the day it writes each run is run as of, as 1 for a write that targets yesterday."""

    written: list[str]
    column: str | None
    days_after: int


def _run_as_of_each_day(run: SeedRun, logic: TableLogic, limits: dict[str, object]
                        ) -> list[str]:
    """A Seed with no Original: its write run once for each day `limits` picks, oldest first,
    as of the day after the one it writes where it targets yesterday; the lines saying each day
    not loaded and each that wrote no rows. A day that fails doesn't stop it."""
    days, why = _days_to_run(run, limits)
    if days is None:
        return [f"{run.name}: no Seed: {why}."]
    where = f"{days.column} from {days.written[0]} to {days.written[-1]}"
    if days.column is None:
        where = f"{days.written[0]} to {days.written[-1]}"
    run.lines.append(f"{run.name}: its Seed, its write run as of each day, oldest first, "
                     f"{where}:")
    _send_settings(run, logic)
    failed = {}
    for written in days.written:
        failed.update(_one_day_sent(run, written, days))
    if run.execute is None:
        return run.lines
    return run.lines + _days_report(run, days, failed)


def _days_to_run(run: SeedRun, limits: dict[str, object]) -> tuple[DaysToRun | None, str]:
    """The days `limits` picks for a Seed run as of each day, and how far after each its run is
    run as of; None, and why, where there are none to run."""
    hive, reads = _write_as_of(run.name, today())
    if not _reads_today(run.name, hive):
        return None, ("its write reads no today, CURRENT_DATE or a Run value of today(), so "
                      "each day's run would write the same rows: its first write loads them")
    if not run.table._partitioned_by:
        return _days_up_to_today(limits)
    found, why = date_source(run.query, [each for each in reads if each != run.name], run.call)
    if found is None:
        return None, f"nothing says which days to run its write for: {why}"
    source, column, values = found
    target = _target_column(run.table, column)
    if target is None:
        return None, (f"none of its partition columns, {in_words(run.table._partitioned_by)},"
                      f" is {column}, the partition column of dates of {source}")
    newest = max(values, key=day_written)
    written = _days_limited(limits, target, newest, values)
    if not written:
        return None, f"its SEED, {decisions.seed_python(limits)}, picks no day to run"
    as_of = day_written(newest)
    day = day_on_column(_write_as_of(run.name, as_of)[0], column)
    days_after = 0 if day is None else (as_of - day).days
    return DaysToRun(written, target, days_after), ""


def _days_up_to_today(limits: dict[str, object]) -> tuple[DaysToRun | None, str]:
    """The days a Seed of a table with no Partitions and no Original runs its write as of:
    each day of its months form, counted back from today."""
    months = limits.get(decisions.MONTHS)
    if months is None:
        return None, ("it has no Partitions and no Original, so only the months form, "
                      '{"months": N}, says which days to run its write as of')
    end = today()
    start = months_before(end, int(months))
    written = [(start + datetime.timedelta(days=each)).isoformat()
               for each in range((end - start).days + 1)]
    return DaysToRun(written, None, 0), ""


def _target_column(table: Table, column: str) -> str | None:
    """The partition column of a table that its source's column of dates, `column`, fills: the
    one of its name, else its only one; None where neither is."""
    if column in table._partitioned_by:
        return column
    if len(table._partitioned_by) == 1:
        return table._partitioned_by[0]
    return None


def _days_limited(limits: dict[str, object], column: str, newest: str,
                  values: list[str]) -> list[str]:
    """Each day a Seed run as of each day writes, oldest first, written as `newest` is: the
    months form's, counted back from `newest`; a value's, from it to `newest`; a range's; a
    list's; or, with no limit on `column`, each day the source holds."""
    newest_day = day_written(newest)
    limit = limits.get(column)
    if decisions.MONTHS in limits:
        start, end = months_before(newest_day, int(limits[decisions.MONTHS])), newest_day
    elif isinstance(limit, dict):
        start = day_written(str(limit.get("from", min(values, key=day_written))))
        end = day_written(str(limit.get("to", newest)))
    elif isinstance(limit, (list, tuple)):
        return sorted(str(each) for each in limit)
    elif limit is not None:
        start, end = day_written(str(limit)), newest_day
    else:
        return sorted(set(values), key=day_written)
    if start is None or end is None:
        return []
    return [written_like(start + datetime.timedelta(days=each), newest)
            for each in range((end - start).days + 1)]


def _writes_as_of(name: str, day: datetime.date
                  ) -> list[Statement | UncheckedStatement]:
    """What a table's write() gives as of `day`, its logic run again while today() gives that
    day, so a Run value its logic works out at its top, as a Template's READS does, is worked
    out as of that day too; a Python step, which sends nothing, passed over."""
    from . import project  # project.py imports this file

    with run_as_of(day):
        logic = project.load(name)
        return [write for write in project.writes_of(name, logic, "project.seed_tables(...)")
                if kinds.kind(write) != kinds.PYTHON]


def _write_as_of(name: str, day: datetime.date) -> tuple[str, list[str]]:
    """The Hive of a table's write() as of `day`, its CURRENT_DATE written as that day, and
    each table it reads, by its name."""
    from .running import tables_read_by, to_hive  # running imports what imports this

    hive, reads = [], []
    for write in _writes_as_of(name, day):
        hive.append(with_today(to_hive(write), day))
        if kinds.kind(write) == kinds.UNCHECKED:
            reads += [table for table, how in tables_read_and_written(write._text)
                      if how == "reads"]
        else:
            reads += [table._name for table in tables_read_by(write)]
    return "\n;\n".join(hive), list(dict.fromkeys(reads))


def _reads_today(name: str, hive: str) -> bool:
    """Whether a table's write reads today: its Hive, `hive` as of today, holds CURRENT_DATE,
    or it differs from its Hive as of the day before, as a Run value of today()'s makes it."""
    from .running import to_hive  # running imports what imports this

    day = today()
    raw = [to_hive(write) for write in _writes_as_of(name, day)]
    if any(with_today(each, day) != each for each in raw):
        return True
    return hive != _write_as_of(name, day - datetime.timedelta(days=1))[0]


def with_today(hive: str, day: datetime.date) -> str:
    """Hive with each CURRENT_DATE in it, or current_date(), outside quotes and comments,
    written as `day` in quotes, '2026-09-25': the run's today, its logic as it was."""
    found = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|`[^`]*`|--[^\n]*"
                       r"|\bcurrent_date\b(?:\s*\(\s*\))?", re.IGNORECASE)

    def in_place(piece: re.Match[str]) -> str:
        if piece.group()[:1] in ("'", '"', "`", "-"):
            return piece.group()
        return f"'{day.isoformat()}'"

    return found.sub(in_place, hive)


def _send_settings(run: SeedRun, logic: TableLogic) -> None:
    """Send what each run as of a day needs first: the Session setting a partitioned table's
    write needs, then the table's own session_settings(), if its logic gives them."""
    if run.table._partitioned_by:
        run.send_settings(hive_settings("dynamic_partitions"))
    if hasattr(logic, "session_settings"):
        run.send_settings(logic.session_settings())


def _one_day_sent(run: SeedRun, written: str, days: DaysToRun) -> dict[str, str]:
    """Run a table's write as of the day after `written`, by `days.days_after`, sending each
    Statement it gives: nothing, or the day and the warehouse's error where it failed."""
    from .running import hivevar_values, refuse_failed_run_values, statement_tree, to_hive

    as_of = day_written(written) + datetime.timedelta(days=days.days_after)
    try:
        for write in _writes_as_of(run.name, as_of):
            if kinds.is_a_query(write):
                refuse_failed_run_values(statement_tree(write))
            hive = with_today(_hivevars_written(to_hive(write), hivevar_values(write)), as_of)
            run.send(hive, f"Seed, its write as of {as_of.isoformat()}")
    # The warehouse's error, or a Run value that failed, is that day's: the next day still runs.
    except Exception as error:  # noqa: BLE001
        if run.execute is None:
            raise
        return {written: _first_line(error)}
    return {}


def _hivevars_written(hive: str, values: dict[str, str]) -> str:
    """Hive with each Hivevar's value written in its place, so a run as of a day sends no SET
    hivevar line of its own."""
    for hivevar, value in values.items():
        hive = hive.replace(f"${{hivevar:{hivevar}}}", value)
    return hive


def _days_report(run: SeedRun, days: DaysToRun, failed: dict[str, str]) -> list[str]:
    """What a Seed run as of each day says once each day has run: how many days loaded, each
    day not loaded with the warehouse's error, and each that wrote no rows, its empty Partition
    kept."""
    counts = {}
    if days.column is not None:
        counts = _rows_by_day(run, days)
    no_rows = [day for day in days.written if day not in failed and days.column is not None
               and not counts.get(day)]
    loaded = len(days.written) - len(failed) - len(no_rows)
    lines = [f"Seeded {run.name}: {counted(loaded, 'day')} loaded of "
             f"{len(days.written)}."]
    lines += [f"  {days.column} = {day}: not loaded: {error}" for day, error in failed.items()]
    lines += [f"  {days.column} = {day}: no rows, its empty Partition kept"
              for day in no_rows]
    return lines


def _rows_by_day(run: SeedRun, days: DaysToRun) -> dict[str, int]:
    """How many rows the table holds on each day of `days`, by the day as its column writes
    it, read through your query."""
    column = days.column
    quoted = type_family(run.table._columns.get(column)) != "number"
    first, last = days.written[0], days.written[-1]
    if quoted:
        first, last = f"'{first}'", f"'{last}'"
    counts = run.query(f"SELECT {column}, COUNT(*) AS row_count FROM {run.name} "
                       f"WHERE {column} >= {first} AND {column} <= {last} GROUP BY {column}")
    return {str(row[0]): int(row[1]) for row in counts.itertuples(index=False)}
