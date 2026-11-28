"""The Seed: a History table's past rows, loaded once, before its first write (Toolbox 8.10).

A History table keeps the rows each write adds, so a new copy of one, in dev or prod, holds
only what its writes have added since it was made: its Seed loads the past rows first, so it
is usable from its first day. Its limit, SEED in its Table reference, picks which:
{"months": N}, N calendar months back from the newest Partition its source holds, both ends
included, by its column of dates, the one partition column whose every value SHOW PARTITIONS
lists reads as a date; or, by partition column, a value, a range or a list, as 8.4's seed
limits are.

- With an Original, the Seed copies the Original's rows, as seed_copy writes it. In prod it
  copies from the dev copy's Original, or, for a table with no Original, from the dev copy
  itself.
- With none, it runs the table's own write once for each past day, oldest first, as of that
  day: the day goes wherever the write reads today, CURRENT_DATE in its Hive, or today() in
  its logic, as last_n_days and a Run value count from it, so a write that targets yesterday
  runs as of the day after. Only the run's today changes, never the logic, so each run writes
  the one Partition a scheduled write writes. It never runs the write as of today: that run is
  the table's first write, which follows the Seed, so no day is written twice.

project.seed_tables runs it, in the step of each Workflow that writes the table, while the
table holds no Partitions yet (no row, for a table with no partition columns), so running
the step again never
loads twice. A day that fails doesn't stop it: its report lists each day not loaded, with the
warehouse's error, and each that wrote no rows. Afterwards project.check(query=query), as
admin/check_project.ipynb runs it, warns of each History table still short of the days its
Seed loads, or holding one with no rows, so a day the report named isn't forgotten.
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
from .shared import counted, in_words, number_read_from, singular_or_plural
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
from .workflows import (BATCH_RECORD, BATCHES, FINISHED, SEED_SENT, promoted_record,
                        write_times)

if TYPE_CHECKING:  # project.py imports this file, so its names are for the hints alone
    import pandas as pd

    from .project import TableLogic


# The Project action that sends a Seed, as each refusal and line of the Admin log names it.
SEED_ACTION = "project.seed_tables(...)"
# Why a table with no Original whose write reads no today has no Seed: a run as of each past
# day would write the same rows. What reads today is anything that counts from today(), as
# the Seed sets it for each day it runs: last_n_days, a Run value, or CURRENT_DATE in Hive.
NO_TODAY_READ = ("its write reads no today, as nothing in it counts from today(): not "
                 "last_n_days, a Run value starting from today(), nor CURRENT_DATE in its "
                 "Hive. So each day's run would write the same rows, and its first write "
                 "loads them")


@dataclass
class SeedRun:
    """What one table's Seed needs and says: the table, its Table reference, your query and
    execute (None for a dry run, which sends nothing), the Project action it runs in,
    SEED_ACTION, or CHECK_ACTION for check(), which reads its days too, and its report's
    lines so far."""

    name: str
    table: Table
    query: Callable[[str], pd.DataFrame]
    execute: Callable[[str], None] | None
    action: str
    lines: list[str] = field(default_factory=list)

    @property
    def call(self) -> str:
        """The call each line of the Admin log, and each refusal, names for this Seed."""
        return f"{self.action} of {self.name}"

    def send(self, hive: str, heading: str) -> None:
        """Send one Statement of the Seed through your execute, its Admin log entry headed
        `heading`, such as "Seed", and record it in admin/sent.csv; in a dry run, say it would
        send it."""
        if self.execute is None:
            self.lines += [f"would send: {line}" for line in hive.split("\n")]
            return
        logged_run(heading, self.call, hive, self.execute)
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


def column_values(listed: list[dict[str, str]], column: str) -> list[str]:
    """Each value of a partition column that `listed`, as listed_partitions gives them, holds,
    in its order, Hive's Partition for no value passed over."""
    return [partition[column] for partition in listed
            if partition.get(column) not in (None, HIVE_DEFAULT_PARTITION)]


def date_partitions(listed: list[dict[str, str]]) -> list[str]:
    """Each partition column whose every value `listed` gives reads as a date, 2026-09-24 or
    20260924, Hive's Partition for no value passed over; none when nothing is listed."""
    named: list[str] = []
    for partition in listed:
        named += list(partition)
    found = []
    for column in dict.fromkeys(named):
        values = column_values(listed, column)
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


def months_range(values: list[str], months: int) -> dict[str, str]:
    """The months form, {"months": N}, as the range it loads on a column of dates whose values
    are `values`: from N calendar months before the newest of them to that newest, both ends
    included, each written as the newest is, such as {"from": "20260824", "to": "20260924"}.
    The Seed's copy, the days it runs a write for, and check()'s count of the days it loads
    each take it from here."""
    newest = max(values, key=day_written)
    start = months_before(day_written(newest), months)
    return {"from": written_like(start, newest), "to": newest}


def days_in_words(days: list[str]) -> str:
    """Days, oldest first, as a report lists them: each run of days in a row as one range,
    "from 2026-09-11 to 2026-09-14", a day alone as it is, in a list, such as "from
    2026-09-11 to 2026-09-13, 2026-09-15 and from 2026-09-17 to 2026-09-18"."""
    return in_words([run[0] if len(run) == 1 else f"from {run[0]} to {run[-1]}"
                     for run in day_runs(days)])


def day_runs(days: list[str]) -> list[list[str]]:
    """Days, oldest first, as their runs of days in a row: ["2026-09-11", "2026-09-12",
    "2026-09-15"] as [["2026-09-11", "2026-09-12"], ["2026-09-15"]]."""
    runs: list[list[str]] = []
    for day in days:
        if runs and day_written(day) - day_written(runs[-1][-1]) == datetime.timedelta(days=1):
            runs[-1].append(day)
        else:
            runs.append([day])
    return runs


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
    return dict(decisions.PROPOSED_MONTHS), f"{found.column} holds dates in {found.table}"


@dataclass(frozen=True)
class ColumnOfDates:
    """A table's partition column whose every value is a date: the table, by its name, the
    column, and each of its values, as SHOW PARTITIONS lists them, such as "20260924"."""

    table: str
    column: str
    values: list[str]


def date_source(query: Callable[[str], pd.DataFrame], sources: list[str], call: str
                ) -> tuple[ColumnOfDates | None, str]:
    """The column of dates of the first of `sources` that has one; or None, and why none is.
    A table that can't be read, or isn't partitioned, is passed over."""
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
            return ColumnOfDates(source, columns[0], column_values(listed, columns[0])), ""
        if not listed:
            why = f"{source} holds no Partition yet, so nothing says which column holds dates"
    return None, why


# --- One table's Seed ------------------------------------------------------------------------


def seed_lines(root: Path, name: str, query: Callable[[str], pd.DataFrame],
               execute: Callable[[str], None] | None) -> list[str]:
    """One table's Seed, sent through your execute, or, with none, shown as a dry run: its
    report's lines. Only a History table that holds no Partitions yet, or no row for one with
    none, is seeded; a table seeded before 8.10 keeps its seed(), and one whose Table reference
    has no SEED loads the proposed {"months": 1}."""
    from . import project  # project.py imports this file

    text = (root / REFERENCE.shown(table_stem(name))).read_text(encoding="utf-8")
    logic = project.load(name)
    kind = decisions.table_kind(text)
    old_seed = hasattr(logic, "seed") and kind != decisions.TableKind.REBUILT
    if kind != decisions.TableKind.HISTORY and not old_seed:
        return [f"{name}: no Seed, as {_why_no_seed(kind)}."]
    run = SeedRun(name, project.table_reference(name), query, execute, SEED_ACTION)
    if _holds_rows(run):
        return [f"{name}: no Seed: it holds rows already, so it was seeded, or written, "
                "before."]
    if old_seed:
        return _send_old_seed(run, logic)
    if decisions.open_decisions(text, name, (decisions.SEED_LIMIT,)):
        return [f"{name}: no Seed: its SEED is still open. Answer \"seed\" in the decisions "
                "cell, write the answers in, and run this step again."]
    first_lines = []
    limits = dict(decisions.PROPOSED_MONTHS)
    if decisions.seed_partitions(text) is None:
        first_lines = [_proposed_month_line(name, limits)]
    else:
        limits = project.run_logic(root, f"from references.{table_stem(name)} import SEED",
                                   "seed_limits")["SEED"]
    source, described = source_to_copy(root, name)
    if source is not None:
        return [*first_lines, *_send_copy(run, source, described, dict(limits))]
    return [*first_lines, *_run_as_of_each_day(run, logic, dict(limits))]


def _proposed_month_line(name: str, limits: dict[str, object]) -> str:
    """The line the Seed of a History table whose Table reference has no SEED starts with, as
    a table converted before 8.10 whose write doesn't read itself has none until
    project.upgrade() asks for it: it loads the limit every History table's Seed is proposed,
    one month."""
    return (f"{name}: its Table reference has no SEED, as a table converted before 8.10 whose "
            "write doesn't read itself has none, so its Seed loads the limit proposed for "
            f"every History table, {decisions.seed_python(limits)}. To load others, add a "
            'SEED line above its Aliases, such as SEED = {"months": 3}.')


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


def _send_old_seed(run: SeedRun, logic: TableLogic) -> list[str]:
    """Send the seed() a table converted before 8.10 has in its logic, as it was, after the
    Session setting its Partitions need: the lines saying so."""
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


def _send_copy(run: SeedRun, source: str, described: str,
               limits: dict[str, object]) -> list[str]:
    """Send a Seed copied from `source`, which `described` names to the table, such as
    "mart.x, its Original", limited by `limits`, the months form worked out from its newest
    Partition: the lines saying what was loaded."""
    resolved, why = _with_months_worked_out(run, source, limits)
    if resolved is None:
        return [f"{run.name}: no Seed: {why}."]
    run.lines.append(f"{run.name}: its Seed, copied from {described}:")
    if run.table._partitioned_by:
        run.send_settings(hive_settings("dynamic_partitions"))
    try:
        run.send(seed_copy(run.table, source, resolved)._text, "Seed")
    # The warehouse's error is the Seed's to report: the write after it still runs.
    except Exception as error:  # noqa: BLE001
        run.lines.append(f"  Not loaded: {_error_first_line(error)}")
        return run.lines
    if run.execute is not None:
        run.lines.append(_loaded_line(run, source))
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
    return {**limits, found.column: months_range(found.values, int(months))}, ""


def _loaded_line(run: SeedRun, source: str) -> str:
    """What a copied Seed loaded, read back through your query: how many Partitions, and each
    day of its column of dates they hold, a run of days in a row as one range; or every row of
    `source`, for a table with no Partitions."""
    if not run.table._partitioned_by:
        return f"Seeded {run.name}: every row of {source}."
    loaded = listed_partitions(run.query, run.name, run.call)
    line = f"Seeded {run.name}: {counted(len(loaded), 'Partition')} loaded"
    columns = date_partitions(loaded)
    if len(columns) == 1:
        days = sorted(set(column_values(loaded, columns[0])), key=day_written)
        line += f", {columns[0]} {days_in_words(days)}"
    return line + "."


def _error_first_line(error: Exception) -> str:
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
        where = f"from {days.written[0]} to {days.written[-1]}"
    as_of = "each run as of that day"
    if days.days_after == 1:
        as_of = "each run as of the day after"
    elif days.days_after > 1:
        as_of = f"each run as of {days.days_after} days after"
    run.lines.append(f"{run.name}: its Seed, its write run as of each past day, oldest first, "
                     f"{where}, {as_of}:")
    _send_settings(run, logic)
    failed = {}
    for written in days.written:
        failed.update(_send_one_day(run, written, days))
    if run.execute is None:
        return run.lines
    return run.lines + _days_report(run, days, failed)


def _days_to_run(run: SeedRun, limits: dict[str, object]) -> tuple[DaysToRun | None, str]:
    """The days `limits` picks for a Seed run as of each day, and how far after each its run is
    run as of; None, and why, where there are none to run. A day whose run would be as of
    today is left out: that run is the table's first write, which follows the Seed."""
    as_of_today = _write_as_of(run, today())
    if not _reads_today(run, as_of_today):
        return None, NO_TODAY_READ
    if not run.table._partitioned_by:
        return _days_up_to_today(limits)
    found, why = date_source(run.query, [each for each in as_of_today.reads
                                         if each != run.name], run.call)
    if found is None:
        return None, f"nothing says which days to run its write for: {why}"
    target = _target_column(run.table, found.column)
    if target is None:
        return None, (f"none of its partition columns, {in_words(run.table._partitioned_by)},"
                      f" is {found.column}, the partition column of dates of {found.table}")
    as_of = day_written(max(found.values, key=day_written))
    day = day_on_column(_write_as_of(run, as_of).hive, found.column)
    days_after = 0 if day is None else (as_of - day).days
    picked = _days_limited(limits, target, found.values)
    # The day a run as of today writes is the first write's, which follows the Seed.
    last_past_day = today() - datetime.timedelta(days=days_after + 1)
    written = [each for each in picked
               if day_written(each) is not None and day_written(each) <= last_past_day]
    if not written:
        why = f"its SEED, {decisions.seed_python(limits)}, picks no day to run"
        if picked:
            why = (f"its SEED, {decisions.seed_python(limits)}, picks no day before the one "
                   "its first write writes")
        return None, why
    return DaysToRun(written, target, days_after), ""


def _days_up_to_today(limits: dict[str, object]) -> tuple[DaysToRun | None, str]:
    """The days a Seed of a table with no Partitions and no Original runs its write as of:
    each day of its months form, counted back from today, up to yesterday, as the run as of
    today is the table's first write, which follows the Seed."""
    months = limits.get(decisions.MONTHS)
    if months is None:
        return None, ("it has no Partitions and no Original, so only the months form, "
                      '{"months": N}, says which days to run its write as of')
    end = today() - datetime.timedelta(days=1)
    start = months_before(today(), int(months))
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


def _days_limited(limits: dict[str, object], column: str, values: list[str]) -> list[str]:
    """Each day a Seed run as of each day writes, oldest first, written as the newest of
    `values`, its source's days, is: the months form's, counted back from that newest; a
    value's, from it to the newest; a range's; a list's; or, with no limit on `column`, each
    day the source holds."""
    newest = max(values, key=day_written)
    limit = limits.get(column)
    if decisions.MONTHS in limits:
        limit = months_range(values, int(limits[decisions.MONTHS]))
    if limit is None:
        return sorted(set(values), key=day_written)
    if isinstance(limit, (list, tuple)):
        return sorted(_limit_text(each) for each in limit)
    if not isinstance(limit, dict):
        limit = {"from": limit}
    start = day_written(_limit_text(limit.get("from", min(values, key=day_written))))
    end = day_written(_limit_text(limit.get("to", newest)))
    if start is None or end is None:
        return []
    return [written_like(start + datetime.timedelta(days=each), newest)
            for each in range((end - start).days + 1)]


def _writes_as_of(run: SeedRun, day: datetime.date
                  ) -> list[Statement | UncheckedStatement]:
    """What a table's write() gives as of `day`, its logic run again while today() gives that
    day, so a Run value its logic works out at its top, as a Template's READS does, is worked
    out as of that day too; a Python step, which sends nothing, passed over."""
    from . import project  # project.py imports this file

    with run_as_of(day):
        logic = project.load(run.name)
        return [write for write in project.writes_of(run.name, logic, run.action)
                if kinds.kind(write) != kinds.PYTHON]


@dataclass(frozen=True)
class WriteAsOf:
    """A table's write() as of one day: its Hive, each CURRENT_DATE in it written as that day;
    whether its Hive held a CURRENT_DATE; and each table it reads, by its name."""

    hive: str
    holds_current_date: bool
    reads: list[str]


def _write_as_of(run: SeedRun, day: datetime.date) -> WriteAsOf:
    """A table's write() as of `day`, its logic loaded once for it."""
    from .running import tables_read_by, to_hive  # running imports what imports this

    hive, reads, holds_current_date = [], [], False
    for write in _writes_as_of(run, day):
        raw = to_hive(write)
        hive.append(with_today(raw, day))
        holds_current_date = holds_current_date or hive[-1] != raw
        if kinds.kind(write) == kinds.UNCHECKED:
            reads += [table for table, how in tables_read_and_written(write._text)
                      if how == "reads"]
        else:
            reads += [table._name for table in tables_read_by(write)]
    return WriteAsOf("\n;\n".join(hive), holds_current_date, list(dict.fromkeys(reads)))


def _reads_today(run: SeedRun, as_of_today: WriteAsOf) -> bool:
    """Whether a table's write reads today: its write as of today, `as_of_today`, held
    CURRENT_DATE, or its Hive differs from its Hive as of the day before, as a Run value of
    today()'s makes it."""
    if as_of_today.holds_current_date:
        return True
    return as_of_today.hive != _write_as_of(run, today() - datetime.timedelta(days=1)).hive


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


def _send_one_day(run: SeedRun, written: str, days: DaysToRun) -> dict[str, str]:
    """Run a table's write as of the day after `written`, by `days.days_after`, sending each
    Statement it gives: nothing, or the day and the warehouse's error where it failed."""
    from .running import hivevar_values, refuse_failed_run_values, statement_tree, to_hive

    as_of = day_written(written) + datetime.timedelta(days=days.days_after)
    try:
        for write in _writes_as_of(run, as_of):
            if kinds.is_a_query(write):
                refuse_failed_run_values(statement_tree(write))
            hive = with_today(_hivevars_written(to_hive(write), hivevar_values(write)), as_of)
            run.send(hive, f"Seed, its write as of {as_of.isoformat()}")
    # The warehouse's error, or a Run value that failed, is that day's: the next day still runs.
    except Exception as error:  # noqa: BLE001
        if run.execute is None:
            raise
        return {written: _error_first_line(error)}
    return {}


def _hivevars_written(hive: str, values: dict[str, str]) -> str:
    """Hive with each Hivevar's value written in its place, so a run as of a day sends no SET
    hivevar line of its own."""
    for hivevar, value in values.items():
        hive = hive.replace(f"${{hivevar:{hivevar}}}", value)
    return hive


def _days_report(run: SeedRun, days: DaysToRun, failed: dict[str, str]) -> list[str]:
    """What a Seed run as of each day says once each day has run: how many days loaded, and
    which, each day not loaded with the warehouse's error, and each that wrote no rows, its
    empty Partition kept; a run of days in a row, loaded or with no rows, as one range, so a
    month of days reads in a line."""
    counts = {}
    if days.column is not None:
        counts = _rows_by_day(run, days.column, days.written)
    no_rows = [day for day in days.written if day not in failed and days.column is not None
               and not counts.get(day)]
    loaded = [day for day in days.written if day not in failed and day not in no_rows]
    line = f"Seeded {run.name}: {counted(len(loaded), 'day')} loaded of {len(days.written)}"
    if loaded:
        which = days_in_words(loaded)
        if days.column is not None:
            which = f"{days.column} {which}"
        line += f", {which}"
    lines = [line + "."]
    lines += [f"  {days.column} = {day}: not loaded: {error}" for day, error in failed.items()]
    for run_of_days in day_runs(no_rows):
        if len(run_of_days) == 1:
            lines.append(f"  {days.column} = {run_of_days[0]}: no rows, its empty Partition "
                         "kept")
        else:
            lines.append(f"  {days.column} from {run_of_days[0]} to {run_of_days[-1]}: no "
                         "rows, each empty Partition kept")
    return lines


def _rows_by_day(run: SeedRun, column: str, written: list[str]) -> dict[str, int]:
    """How many rows the table holds on each day of `written`, oldest first, by the day as its
    partition column of dates, `column`, writes it, read through your query."""
    quoted = type_family(run.table._columns.get(column)) != "number"
    first, last = written[0], written[-1]
    if quoted:
        first, last = f"'{first}'", f"'{last}'"
    counts = run.query(f"SELECT {column}, COUNT(*) AS row_count FROM {run.name} "
                       f"WHERE {column} >= {first} AND {column} <= {last} GROUP BY {column}")
    return {str(row[0]): int(row[1]) for row in counts.itertuples(index=False)}


# --- The days a Seed loads, checked: check()'s Warning (Toolbox 8.10, ticket 06) -----------

# The Project action that reads them, as a refusal of what your query gave back names it.
CHECK_ACTION = "project.check(query=...)"
# How many of the days a History table lacks its Warning names, before counting the rest.
DAYS_NAMED = 5


def missing_days_lines(root: Path, names: list[str],
                       query: Callable[[str], pd.DataFrame]) -> list[str]:
    """What check() says of the History tables among `names` short of the days their Seed
    loads: a Warning for each, naming how many and which, the first few and a count of the
    rest, a day it holds with no rows among them; then one line naming each whose Partitions
    your query couldn't read, with what it said. It blocks nothing. A table never written is
    passed over, as its Seed runs at its first write, and so is one whose days can't be told:
    no partition column of dates, or a write that reads no today."""
    warnings, unread, query_error = [], [], ""
    for name in names:
        run = _history_table_to_check(root, name, query)
        if run is None:
            continue
        try:
            warning = _missing_days_warning(root, run)
        # What your query said, the warehouse's error or a refusal of what it gave back, is
        # said once, below the Warnings: check() goes on, as it blocks nothing.
        except Exception as error:  # noqa: BLE001
            unread.append(name)
            query_error = query_error or _error_first_line(error).removeprefix(
                "What happened:").strip()
            continue
        if warning:
            warnings.append(warning)
    if unread:
        its = singular_or_plural(len(unread), "its", "their")
        warnings.append(f"Not checked for the days {its} Seed loads: {in_words(unread)}, as "
                        f"your query couldn't read {its} Partitions. Your query said: "
                        f"{query_error}")
    return warnings


def _history_table_to_check(root: Path, name: str, query: Callable[[str], pd.DataFrame]
                            ) -> SeedRun | None:
    """A History table check() reads the days of: partitioned, its SEED answered, and written
    at least once, as admin/sent.csv records; None for any other."""
    from . import project  # project.py imports this file

    path = root / REFERENCE.shown(table_stem(name))
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    seeded = any(decisions.kind_of(line) == decisions.SEED_LIMIT
                 for line in decisions.code_of(text).split("\n"))
    if (decisions.table_kind(text) != decisions.TableKind.HISTORY or not seeded
            or decisions.open_decisions(text, name, (decisions.SEED_LIMIT,))
            or not write_times(root, name)):
        return None
    try:
        table = project.table_reference(name)
    # A Table reference that doesn't load has no days to check: its own refusal says why
    # wherever it is imported.
    except Exception:  # noqa: BLE001
        return None
    if not table._partitioned_by:
        return None
    return SeedRun(name, table, query, None, CHECK_ACTION)


def _missing_days_warning(root: Path, run: SeedRun) -> str | None:
    """The Warning for a History table lacking days its Seed loads, or holding them with no
    rows; None for one holding every day, or whose days can't be told, and for one that has no
    Seed, whose Partitions are never read."""
    if not _has_a_seed(root, run):
        return None
    partitions_held = listed_partitions(run.query, run.name, run.call)
    if not partitions_held:
        return None  # no Partition yet: its Seed runs at its next write
    days = _days_seed_loads(root, run)
    if days is None:
        return None
    column, expected = days
    counts = _rows_by_day(run, column, expected)
    missing = [day for day in expected if not counts.get(day)]
    if not missing:
        return None
    days_held = {partition.get(column) for partition in partitions_held}
    shown = [f"{day} (no rows)" if day in days_held else day for day in missing]
    named = in_words(shown)
    if len(shown) > DAYS_NAMED:
        named = f"{', '.join(shown[:DAYS_NAMED])} and {len(shown) - DAYS_NAMED} more"
    return (f"Warning: {run.name} lacks {len(missing)} of the {counted(len(expected), 'day')} "
            f"its Seed loads: {named}. That stops nothing, but what reads it finds no rows "
            "for those days until each is written.")


def _has_a_seed(root: Path, run: SeedRun) -> bool:
    """Whether a History table has a Seed, read from its files alone: an Original to copy, or
    a write that reads today, to run as of each past day. One whose logic stops has none to
    tell: check() names its failing logic apart."""
    if source_to_copy(root, run.name)[0] is not None:
        return True
    try:
        return _reads_today(run, _write_as_of(run, today()))
    # A logic that stops, which check() names as failing logic: no Seed can be told from it.
    except Exception:  # noqa: BLE001
        return False


def _days_seed_loads(root: Path, run: SeedRun) -> tuple[str, list[str]] | None:
    """The table's partition column of dates and each day its Seed loads, oldest first, as
    written, counted as the Seed counts them, from the same source: each day its source holds
    within its SEED, for a Seed copied; each day its write is run for, for one run as of each
    day. None where they can't be told."""
    from . import project  # project.py imports this file

    try:
        limits = dict(project.run_logic(root, f"from references.{table_stem(run.name)} "
                                        "import SEED", "seed_limits")["SEED"])
        source, _ = source_to_copy(root, run.name)
        if source is not None:
            return _days_copied_from(run, source, limits)
        days, _ = _days_to_run(run, limits)
    # A SEED or a logic that stops, which check() names as failing logic, or a source your
    # query can't list: nothing tells which days its Seed loads.
    except Exception:  # noqa: BLE001
        return None
    if days is None or days.column is None or not days.written:
        return None
    return days.column, days.written


def _days_copied_from(run: SeedRun, source: str, limits: dict[str, object]
                      ) -> tuple[str, list[str]] | None:
    """For a Seed copied from `source`: its partition column of dates, and each day `source`
    holds that `limits` keep, the months form counted back from its newest; None where it has
    no one column of dates the table is partitioned by too."""
    listed = listed_partitions(run.query, source, run.call)
    columns = date_partitions(listed)
    if len(columns) != 1 or columns[0] not in run.table._partitioned_by:
        return None
    column = columns[0]
    values = column_values(listed, column)
    months = limits.pop(decisions.MONTHS, None)
    if months is not None:
        limits[column] = months_range(values, int(months))
    days = set()
    for partition in listed:
        if partition.get(column) not in values:
            continue
        if all(_is_kept_by(partition.get(each), limit) for each, limit in limits.items()):
            days.add(partition[column])
    if not days:
        return None
    return column, sorted(days, key=day_written)


def _is_kept_by(value: str | None, limit: object) -> bool:
    """Whether a partition column's value, as SHOW PARTITIONS lists it, is one a seed limit
    keeps, as seed_copy's WHERE keeps it: a value, it or later; a range, within it, both ends
    included; a list, one of them. A Run value's function is called first, as seed_copy calls
    it."""
    if value is None:
        return False
    if isinstance(limit, dict):
        return (("from" not in limit or _ordering(value, limit["from"]) >= 0)
                and ("to" not in limit or _ordering(value, limit["to"]) <= 0))
    if isinstance(limit, (list, tuple)):
        return any(_ordering(value, each) == 0 for each in limit)
    return _ordering(value, limit) >= 0


def _ordering(value: str, limit: object) -> int:
    """-1, 0 or 1 as `value` comes before `limit`, is the same, or comes after: as days where
    both are, 20260924 the same as 2026-09-24; as numbers where both are; else as text."""
    limit_text = _limit_text(limit)
    one, other = _comparable(value), _comparable(limit_text)
    if type(one) is not type(other):
        one, other = value, limit_text
    return (one > other) - (one < other)


def _limit_text(limit: object) -> str:
    """One value of a seed limit as SHOW PARTITIONS would list it: a Run value's function
    called first, as seed_copy calls it, and a date written 2026-09-24."""
    if callable(limit):
        limit = limit()
    if isinstance(limit, datetime.date):
        return limit.isoformat()
    return str(limit)


def _comparable(text: str) -> datetime.date | float | str:
    """A value as it is put in order: a day, the number Hive reads it as, or text."""
    day = day_written(text.strip())
    if day is not None:
        return day
    number = number_read_from(text)
    if number is None:
        return text
    return number
