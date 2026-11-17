"""The Lineage difference: what changed in the Lineage state between two points (Toolbox 8.8,
ticket 05).

difference(...) reads the rows of admin/lineage/lineage_state.csv and gives back a Difference:
each table whose columns changed since a recording, each column's own change with its logic
before and after, each inherited change with its chain down to the change it comes from, the
Building blocks that changed, what an Upgrade's recording found apart from the rest, and when
each changed Saved table was next written, from admin/sent.csv. write_difference(...) writes it
as an HTML page and its Markdown twin into admin/lineage/, as
project.export_lineage_difference() asks. Nothing here reaches the warehouse.
"""

from __future__ import annotations

import csv
import datetime
import difflib
import html
import re
from dataclasses import dataclass
from pathlib import Path

from . import html_page, project_lineage, unchecked
from .effective_logic import (REFERENCE, SAVED_TABLE, SCHEDULED_RUN, WHOLE_TABLE, column_key,
                              each_column)
from .lineage import shortened
from .lineage_state import (ADDED, BLOCK, INHERITED, OPAQUE, OWN, REMOVED, RETYPED,
                            ROOT_CHANGES, STATE_FILE, TOOLBOX, columns_at, read_rows)
from .refusals import refuse
from .shared import counted, in_words, items_of
from .unchecked import SENT

# How `since=` may give a time: a day, a minute or a second, as the state's recorded_at says.
TIMES_GIVEN = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")
# A commit, as git shows it, short or whole.
COMMIT = re.compile(r"[0-9a-f]{4,40}")
# What changed of a table, in the words the pages use, and the kind its box is drawn as.
TABLE_WORDS = {OWN: "own change", INHERITED: "inherited change only"}
TABLE_KINDS = {OWN: "own-change", INHERITED: "inherited-change"}
# Each change in the words the pages use.
CHANGE_WORDS = {OWN: "own change", OPAQUE: "own change, opaque", RETYPED: "retyped",
                ADDED: "added", REMOVED: "removed", INHERITED: "inherited change"}
# The building_block: a Building block's cause starts with, in an own change's because.
BLOCK_CAUSE = f"{BLOCK}:"


@dataclass(frozen=True)
class ChangedColumn:
    """One column that changed: its table and name; its change, one of OWN, OPAQUE,
    RETYPED, ADDED, REMOVED and INHERITED; when its last change was recorded, and at which
    commit, empty outside git; its row in the Lineage state before and after, None where it
    had none; its Effective logic before and after, written out; for an inherited change,
    each chain from it down to a column whose own change it comes from, as
    <db>.<table>.<column> names, the column first; and the Building blocks its own change came
    with."""

    table: str
    column: str
    change: str
    recorded_at: str
    commit: str
    before: dict[str, str] | None
    after: dict[str, str] | None
    effective_before: str
    effective_after: str
    chains: tuple[tuple[str, ...], ...]
    blocks: tuple[str, ...]


@dataclass(frozen=True)
class ChangedTable:
    """One table some of whose columns changed: its name; its kind, as effective_logic names
    it; OWN when a column changed at the table itself, else INHERITED; its changed columns;
    and, for a Saved table, when admin/sent.csv says it was first written after its last
    change, or None when it wasn't, or isn't a Saved table."""

    table: str
    kind: str
    change: str
    columns: tuple[ChangedColumn, ...]
    first_written: str | None


@dataclass(frozen=True)
class ToolboxRewrite:
    """What one Upgrade's recording found changed: when, by which Toolbox version and call,
    and each column, as <db>.<table>.<column>: the Toolbox writing the same logic as other
    Hive, never an own change (ADR 0015)."""

    recorded_at: str
    toolbox_version: str
    recorded_by: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class Difference:
    """What changed in the Lineage state: `since`, the comparison in words; `start`, the
    recording compared from, and `end`, the newest compared to, None where there is none;
    each changed table, those with an own change first; each Building block that changed, as
    (its name, its change, when); each Upgrade's rewrite, apart; each table or Scheduled run
    not recorded, with why; and every table either end holds, or, given tables=, those named
    and those on their chains, with its kind and the tables it reads, for the drawing."""

    since: str
    start: str | None
    end: str | None
    tables: tuple[ChangedTable, ...]
    blocks: tuple[tuple[str, str, str], ...]
    toolbox: tuple[ToolboxRewrite, ...]
    not_recorded: dict[str, str]
    kinds: dict[str, str]
    reads: dict[str, tuple[str, ...]]


# --- Working out the difference ---------------------------------------------------------------


def difference(rows: list[dict[str, str]], since: str | None = None,
               tables: str | list[str] | None = None, sent: list[dict[str, str]] | None = None,
               not_built: dict[str, str] | None = None, call: str = "difference()"
               ) -> Difference:
    """What changed in the Lineage state `rows` hold, oldest first: since the recording before
    the newest, or since `since`, a time or a commit; for every table, or only `tables` and
    the chains that reach them. `sent` is admin/sent.csv's rows, `not_built` each table or
    Scheduled run the state couldn't record now, with why. Refused, by `call`'s name, with no
    recording, or a time, commit or table no recording matches."""
    if not rows:
        refuse(what=f"{call}: the Project has no Lineage state yet, so there is nothing to "
               "compare.",
               why=f"The difference compares recordings of {STATE_FILE.as_posix()}, and "
               "none is there.",
               fix="Record one first: project.record_lineage_state(), in "
               "admin/lineage.ipynb, then again once something has changed.",
               error=ValueError)
    start, words = _compared_from(rows, since, call)
    end = rows[-1]["recorded_at"]
    if start == end:
        end = None
    base = {}
    if start is not None:
        base = columns_at(rows, start)
    latest = columns_at(rows)
    later = [row for row in rows if start is None or row["recorded_at"] > start]
    changed = _changed_columns(later, base, latest)
    kinds, reads = _tables_drawn(base, latest)
    if tables is not None:
        shown = _tables_shown(items_of(tables), changed, kinds, call)
        changed = [column for column in changed if column.table in shown]
        kinds = {table: kind for table, kind in kinds.items() if table in shown}
        reads = {table: _reads_shown(reads[table], shown) for table in kinds}
    return Difference(since=words, start=start, end=end,
                      tables=_changed_tables(changed, kinds, sent or []),
                      blocks=tuple((row["table"], row["change"], row["recorded_at"])
                                   for row in later if row["kind"] == BLOCK),
                      toolbox=_toolbox_rewrites(later),
                      not_recorded=dict(not_built or {}), kinds=kinds, reads=reads)


def _reads_shown(reads: tuple[str, ...], shown: set[str]) -> tuple[str, ...]:
    """Of the tables a table reads, those a difference given tables= shows."""
    return tuple(read for read in reads if read in shown)


def _compared_from(rows: list[dict[str, str]], since: str | None, call: str
                   ) -> tuple[str | None, str]:
    """The recording a difference compares from, by its recorded_at, and the comparison in
    words: the recording before the newest, or the last at or before `since`, a time, the first
    for a time before it, or the last made at `since`, a commit."""
    recordings = list(dict.fromkeys(row["recorded_at"] for row in rows))
    if since is None:
        if len(recordings) == 1:
            return recordings[0], f"since the only recording, of {recordings[0]}"
        return recordings[-2], (f"since the recording of {recordings[-2]}, to the newest, of "
                                f"{recordings[-1]}")
    given = _time_given(since)
    if given is not None and given < recordings[0]:
        return recordings[0], (f"since {since}, from the first recording, of "
                               f"{recordings[0]}")
    if given is not None:
        return [recording for recording in recordings if recording <= given][-1], (
            f"since {since}")
    if COMMIT.fullmatch(since.lower()):
        return _compared_from_a_commit(rows, since.lower(), call), f"since commit {since}"
    refuse(what=f"{call}: since={since!r} is neither a time nor a commit.",
           why="since= says where the difference starts: a time, such as \"2026-11-20\" or "
           "\"2026-11-20 06:00\", or a commit, such as \"1a2b3c4\".",
           fix=f"Give one of those, or leave since= out to compare the newest recording, of "
           f"{recordings[-1]}, with the one before it.", error=ValueError)


def _time_given(since: str) -> str | None:
    """`since` as a time, written as the state writes recorded_at, or None when it isn't one
    of TIMES_GIVEN."""
    for shape in TIMES_GIVEN:
        try:
            return datetime.datetime.strptime(since, shape).strftime(unchecked.TIME_SHOWN)
        except ValueError:
            continue
    return None


def _compared_from_a_commit(rows: list[dict[str, str]], commit: str, call: str) -> str:
    """The last recording made at `commit`, a whole or short commit; refused when none was,
    naming the nearest commit a recording was made at."""
    made_at = [row["recorded_at"] for row in rows if row["commit"].startswith(commit)]
    if made_at:
        return made_at[-1]
    commits = list(dict.fromkeys(row["commit"] for row in rows if row["commit"]))
    close = difflib.get_close_matches(commit, commits, n=1)
    nearest = "No recording was made inside git, so none has a commit."
    if close:
        nearest = f"The nearest a recording was made at is {close[0]}."
    elif commits:
        nearest = f"Recordings were made at {in_words(commits)}."
    refuse(what=f"{call}: no recording of the Lineage state was made at commit {commit}.",
           why="since= given a commit starts the difference from the last recording made at "
           f"it. {nearest}",
           fix="Give a commit a recording was made at, or a time, such as \"2026-11-20\".",
           error=ValueError)


def _changed_columns(later: list[dict[str, str]], base: dict[tuple[str, str], dict[str, str]],
                     latest: dict[tuple[str, str], dict[str, str]]) -> list[ChangedColumn]:
    """Each column the rows recorded after the start changed, as the start and the newest
    recording hold it, those an Upgrade's recording alone changed left out. A column added
    and removed again in between is left out too."""
    rows_of: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in later:
        if row["kind"] != BLOCK and row["change"] != TOOLBOX:
            rows_of.setdefault((row["table"], row["column"]), []).append(row)
    changed = []
    for key, rows in rows_of.items():
        change = _change_over(key, rows, base, latest)
        if change is not None:
            changed.append(_changed_column(key, change, rows, base, latest))
    return changed


def _change_over(key: tuple[str, str], rows: list[dict[str, str]],
                 base: dict[tuple[str, str], dict[str, str]],
                 latest: dict[tuple[str, str], dict[str, str]]) -> str | None:
    """What changed of the column at `key`, over the recordings its `rows` are of: added or
    removed between the two ends, else the change of most weight its rows say; None for a
    column there at neither end."""
    if key not in base and key not in latest:
        return None
    if key not in base:
        return ADDED
    if key not in latest:
        return REMOVED
    said = {row["change"] for row in rows}
    for change in (OPAQUE, OWN, ADDED, REMOVED, RETYPED):
        if change in said:
            return _at_the_column(change)
    return INHERITED


def _at_the_column(change: str) -> str:
    """A change made at the column itself, as a column there at both ends shows it: added or
    removed and back again is an own change."""
    if change in (ADDED, REMOVED):
        return OWN
    return change


def _changed_column(key: tuple[str, str], change: str, rows: list[dict[str, str]],
                    base: dict[tuple[str, str], dict[str, str]],
                    latest: dict[tuple[str, str], dict[str, str]]) -> ChangedColumn:
    """The column at `key`, which `change` changed over its `rows`: its ends, its Effective
    logic at each, its chains and its Building blocks."""
    name = ".".join(key)
    roots: list[str] = []
    blocks: list[str] = []
    for row in rows:
        for cause in filter(None, row["because"].split(";")):
            if cause.startswith(BLOCK_CAUSE):
                blocks.append(cause.removeprefix(BLOCK_CAUSE))
            elif row["change"] == INHERITED:
                roots.append(cause)
    chains: tuple[tuple[str, ...], ...] = ()
    if change == INHERITED:
        both = {**base, **latest}
        chains = tuple(_chain(name, root, both) for root in dict.fromkeys(roots))
    return ChangedColumn(
        table=key[0], column=key[1], change=change, recorded_at=rows[-1]["recorded_at"],
        commit=rows[-1]["commit"], before=base.get(key), after=latest.get(key),
        effective_before=effective_logic_text(base, name),
        effective_after=effective_logic_text(latest, name), chains=chains,
        blocks=tuple(dict.fromkeys(blocks)))


def _chain(name: str, root: str, state: dict[tuple[str, str], dict[str, str]]
           ) -> tuple[str, ...]:
    """The shortest chain of reads from the column `name` up to `root`, both named, or the
    two alone when no chain of reads the state holds reaches it."""
    came_from = {name: ""}
    waiting = [name]
    while waiting:
        column = waiting.pop(0)
        if column == root:
            break
        for read in _reads_of(state, column):
            if read not in came_from:
                came_from[read] = column
                waiting.append(read)
    if root not in came_from:
        return (name, root)
    chain = [root]
    while came_from[chain[-1]]:
        chain.append(came_from[chain[-1]])
    return tuple(reversed(chain))


def _reads_of(state: dict[tuple[str, str], dict[str, str]], name: str) -> list[str]:
    """The columns the column `name` reads, as the state holds it, a whole-table read given
    as every column of its table."""
    row = state.get(column_key(name))
    if row is None:
        return []
    return each_column(filter(None, row["reads"].split(";")), state)


def _tables_drawn(base: dict[tuple[str, str], dict[str, str]],
                  latest: dict[tuple[str, str], dict[str, str]]
                  ) -> tuple[dict[str, str], dict[str, tuple[str, ...]]]:
    """Every table either end holds, by name, with its kind, and the tables each reads, by
    name, a Building block's rows left out."""
    kinds: dict[str, str] = {}
    reads: dict[str, set[str]] = {}
    for (table, _), row in sorted({**base, **latest}.items()):
        if row["kind"] == BLOCK:
            continue
        kinds[table] = row["kind"]
        read_tables = {read.rsplit(".", 1)[0] for read in row["reads"].split(";") if read}
        reads.setdefault(table, set()).update(read_tables - {table})
    return kinds, {table: tuple(sorted(read)) for table, read in reads.items()}


def _tables_shown(names: list[object], changed: list[ChangedColumn], kinds: dict[str, str],
                  call: str) -> set[str]:
    """The tables a difference given tables= shows: each named, refused when the state holds
    no such table, and each on the chain of a changed column of one."""
    for name in names:
        if name not in kinds:
            close = difflib.get_close_matches(str(name), list(kinds), n=1)
            nearest = ""
            if close:
                nearest = f" Did you mean {close[0]}?"
            refuse(what=f"{call}: tables= names {name}, which the Lineage state holds "
                   f"nothing of.{nearest}",
                   why="tables= keeps the difference to the tables it names and the chains "
                   "that reach them, so each must be a table, or a Scheduled run's "
                   "Statement as <run>.<result>, the state has recorded.",
                   fix="Name it as the Lineage state does, <db>.<table>, or leave tables= out "
                   "to see every table.", error=ValueError)
    shown = {str(name) for name in names}
    for column in changed:
        if column.table in shown:
            for chain in column.chains:
                shown.update(column_key(link)[0] for link in chain)
    return shown


def _changed_tables(changed: list[ChangedColumn], kinds: dict[str, str],
                    sent: list[dict[str, str]]) -> tuple[ChangedTable, ...]:
    """Each table some of `changed` belongs to, those with a change at the table itself
    first, then by name."""
    by_table: dict[str, list[ChangedColumn]] = {}
    for column in changed:
        by_table.setdefault(column.table, []).append(column)
    found = []
    for table, columns in by_table.items():
        change = INHERITED
        if any(column.change in ROOT_CHANGES for column in columns):
            change = OWN
        kind = kinds.get(table, SAVED_TABLE)
        written = None
        if kind == SAVED_TABLE:
            written = _first_written(table, max(column.recorded_at for column in columns),
                                     sent)
        found.append(ChangedTable(table=table, kind=kind, change=change,
                                  columns=tuple(columns), first_written=written))
    return tuple(sorted(found, key=lambda table: (table.change != OWN, table.table)))


def _first_written(table: str, changed_at: str, sent: list[dict[str, str]]) -> str | None:
    """When admin/sent.csv says `table` was first written after `changed_at`, or None."""
    for row in sent:
        if row["time"] > changed_at and table in row["tables"].split(";"):
            return row["time"]
    return None


def _toolbox_rewrites(later: list[dict[str, str]]) -> tuple[ToolboxRewrite, ...]:
    """What each Upgrade's recording among `later` found changed, a rewrite each."""
    found: dict[str, list[dict[str, str]]] = {}
    for row in later:
        if row["change"] == TOOLBOX and row["kind"] != BLOCK:
            found.setdefault(row["recorded_at"], []).append(row)
    rewrites = []
    for at, rows in found.items():
        columns = tuple(f"{row['table']}.{row['column']}" for row in rows)
        rewrites.append(ToolboxRewrite(recorded_at=at,
                                       toolbox_version=rows[0]["toolbox_version"],
                                       recorded_by=rows[0]["recorded_by"], columns=columns))
    return tuple(rewrites)


# --- Effective logic, written out -------------------------------------------------------------


def effective_logic_text(state: dict[tuple[str, str], dict[str, str]], name: str) -> str:
    """The Effective logic of the column `name`, <db>.<table>.<column>, as `state` holds it:
    its own logic and the rows that count for it, then each column it reads, written out in
    turn, down to the tables the Project doesn't write; a column met twice is written once.
    "" when the state doesn't hold it."""
    if column_key(name) not in state:
        return ""
    return "\n".join(_tree_lines(state, name, "", "", set()))


def _tree_lines(state: dict[tuple[str, str], dict[str, str]], name: str, first: str, rest: str,
                seen: set[str]) -> list[str]:
    """The lines of the column `name` and what it reads: its first line after `first`, each
    line under it after `rest`, the tree's branches."""
    row = state.get(column_key(name))
    if name.endswith(f".{WHOLE_TABLE}"):
        return [f"{first}{name}  (every column of {name[:-2]}: an Unchecked step names only "
                "its tables)"]
    if row is None:
        return [f"{first}{name}  (not in the Lineage state)"]
    if name in seen:
        return [f"{first}{name}  (as above)"]
    seen.add(name)
    if row["kind"] == REFERENCE:
        return [f"{first}{name}  ({row['type']})"]
    lines = [f"{first}{name} = {' '.join(row['own_logic'].split())}"]
    if row["rows_that_count"]:
        lines.append(f"{rest}  rows that count: {' '.join(row['rows_that_count'].split())}")
    reads = [read for read in row["reads"].split(";") if read]
    for number, read in enumerate(reads, 1):
        branch, under = "├─ ", "│  "
        if number == len(reads):
            branch, under = "└─ ", "   "
        lines += _tree_lines(state, read, rest + branch, rest + under, seen)
    return lines


# --- The pages --------------------------------------------------------------------------------

# What both files say under the title.
ABOUT = ("What changed in the Lineage state, admin/lineage/lineage_state.csv: each table whose "
         "columns changed, each column with an own change, its logic before and after, and "
         "each with an inherited change, whose own logic stayed the same while a column it "
         "reads, up its chain, had an own change. Each changed Saved table says when it was "
         "next written, from admin/sent.csv.")
# The page's own CSS, after the page module's: text wrapped, the Upgrade's rewrites folded, and
# a table that didn't change drawn faded, unless a click lights its path; a dimmed one stays as
# dim as the rest.
CSS = """\
header p{margin:0 0 8px;max-width:72em}
pre{white-space:pre-wrap;overflow-wrap:anywhere}
.part{max-width:72em} .after{padding:0 16px}
details.toolbox{margin:12px 0} details.toolbox summary{cursor:pointer}
.n.unchanged:not(.hit){opacity:.45} .n.unchanged.dim{opacity:.15}"""
# The legend under the title: each kind of box, by its class in html_page.KINDS, then what an
# arrow means and what the mouse and keyboard do.
LEGEND = [
    ("own-change", "a column of it changed at the table itself"),
    ("inherited-change", "only inherited changes: something it reads changed"),
    ("unchanged", "no column of it changed, drawn faded"),
    (None, "arrow: from a table to each table that reads it · click a box, or Tab to it and "
           "press Enter, to light up what feeds it and what it feeds and open what changed "
           "of it · Escape closes it · scroll zooms, drag pans"),
]
# The page's own script, after html_page.DRAWING_SCRIPT and html_page.PANEL_SCRIPT, whose
# functions it calls: the picture is in the page already; to_html fills in its one marker,
# __DATA__, with the boxes and arrows to light up.
SCRIPT = """\
// The difference page's own script: the picture is in the page already, so this only makes it
// zoom, pan and light up a path, and its boxes open the panel, whose Copy buttons copy the
// logic beside them. It is plain JavaScript that any browser runs, with nothing to install or
// download.
const drawing = document.querySelector('.wrap');
addMouseHandlers(drawing.querySelector('svg'), __DATA__);
addPanelHandlers(drawing);"""
# What a box says its table is, by its kind.
KIND_WORDS = {SAVED_TABLE: "Saved table", SCHEDULED_RUN: "a Scheduled run's Statement",
              REFERENCE: "read, not written here"}


def counts_line(found: Difference) -> str:
    """How much changed, in one sentence: the tables, then the columns by change."""
    if found.end is None:
        return (f"Nothing to compare yet: no recording was made {found.since}. Record again "
                "once something has changed.")
    if not found.tables and not found.toolbox:
        return f"No column changed, {found.since}."
    columns: list[ChangedColumn] = []
    for table in found.tables:
        columns += table.columns
    changes = [column.change for column in columns]
    counts = [f"{changes.count(change)} {CHANGE_WORDS[change]}"
              for change in CHANGE_WORDS if change in changes]
    line = (f"{counted(len(found.tables), 'table')} changed, {found.since}: "
            f"{counted(len(columns), 'column')} ({', '.join(counts)}).")
    if not columns:
        line = f"No column of yours changed, {found.since}."
    for rewrite in found.toolbox:
        line += (f" {counted(len(rewrite.columns), 'column')} rewritten by the Toolbox's "
                 f"upgrade to {rewrite.toolbox_version}, shown apart.")
    return line


def difference_parts(found: Difference) -> list[html_page.Part]:
    """The sections both files show: the tables and runs not recorded, each changed table,
    the Building blocks that changed, then each Upgrade's rewrite."""
    parts = []
    if found.not_recorded:
        why_not = [f"`{name}`: {why}" for name, why in found.not_recorded.items()]
        parts.append(html_page.Part("not-recorded", 2, "Not recorded",
                                    [html_page.Piece(html_page.ITEMS, why_not)]))
    parts += [_changed_table_part(table) for table in found.tables]
    if found.blocks:
        parts.append(html_page.Part("blocks", 2, "Building blocks changed", [html_page.Piece(
            html_page.ITEMS, [f"`{name}`: {CHANGE_WORDS.get(change, change)}, recorded {at}"
                              for name, change, at in found.blocks])]))
    parts += [_rewrite_part(rewrite) for rewrite in found.toolbox]
    return parts


def part_key(table: str) -> str:
    """The id of a table's section on the page, from its name."""
    return "table-" + re.sub(r"[^0-9A-Za-z_-]", "-", table)


def _changed_table_part(table: ChangedTable) -> html_page.Part:
    """A changed table's section: what changed of it, when it was next written, and a section
    for each changed column."""
    words = TABLE_WORDS[table.change]
    written = "A table the Project doesn't write."
    if table.kind == SCHEDULED_RUN:
        written = ("A Scheduled run's Statement: the run sends it as it is now the next time "
                   "it runs.")
    elif table.first_written is not None:
        written = f"First written with this logic: {table.first_written} (admin/sent.csv)."
    elif table.kind == SAVED_TABLE:
        written = "Not written since the change (admin/sent.csv)."
    key = part_key(table.table)
    pieces: list[html_page.Piece | html_page.Part] = [
        html_page.Piece(html_page.TEXT, [written])]
    pieces += [_column_part(key, column) for column in table.columns]
    return html_page.Part(key, 2, f"`{table.table}`: {words}", pieces)


def _column_part(key: str, column: ChangedColumn) -> html_page.Part:
    """A changed column's section: when it changed, then its logic before and after, its
    chains, or its type, as its change needs."""
    commit = "outside git"
    if column.commit:
        commit = f"at commit {column.commit}"
    pieces: list[html_page.Piece | html_page.Part] = [
        html_page.Piece(html_page.TEXT, [f"Recorded {column.recorded_at}, {commit}."])]
    if column.blocks:
        pieces.append(html_page.Piece(html_page.TEXT, [
            f"It came with a change to the Building block "
            f"{in_words([f'`{block}`' for block in column.blocks])}."]))
    if column.change == OPAQUE:
        pieces.append(html_page.Piece(html_page.TEXT, [
            "Opaque: the whole step that writes it changed, an Unchecked statement, Unchecked "
            "derived table or Python step: read it."]))
    if column.change == RETYPED:
        pieces.append(html_page.Piece(html_page.TEXT, [
            f"Its type: `{_field(column.before, 'type')}` before, "
            f"`{_field(column.after, 'type')}` after."]))
    if column.change in (OWN, OPAQUE, ADDED, REMOVED):
        pieces += _own_logic_pieces(column)
    if column.chains:
        pieces.append(html_page.Piece(html_page.ITEMS, [_chain_line(chain)
                                                        for chain in column.chains]))
    pieces += _effective_pieces(column)
    return html_page.Part(f"{key}-{column.column}", 3,
                          f"`{column.column}`: {CHANGE_WORDS[column.change]}", pieces)


def _chain_line(chain: tuple[str, ...]) -> str:
    """A chain of reads as a line: the changed column first, each column it reads after an
    arrow, down to the one whose own change it comes from."""
    return " ← ".join(f"`{link}`" for link in chain)


def _field(row: dict[str, str] | None, name: str) -> str:
    """One field of a column's row, or "" where it has no row."""
    if row is None:
        return ""
    return row[name]


def _own_logic_pieces(column: ChangedColumn) -> list[html_page.Piece | html_page.Part]:
    """A column's own logic, and the rows that count for it, before and after, each end it
    has."""
    pieces: list[html_page.Piece | html_page.Part] = []
    for words, row in (("before", column.before), ("after", column.after)):
        if row is None or not row["own_logic"]:
            continue
        pieces += [html_page.Piece(html_page.TEXT, [f"Its own logic {words}:"]),
                   html_page.Piece(html_page.HIVE, [row["own_logic"]])]
        if row["rows_that_count"]:
            pieces += [html_page.Piece(html_page.TEXT, [f"The rows that count {words}:"]),
                       html_page.Piece(html_page.BLOCK, [row["rows_that_count"]])]
    return pieces


def _effective_pieces(column: ChangedColumn) -> list[html_page.Piece | html_page.Part]:
    """A column's Effective logic before and after, written out, each end it has."""
    pieces: list[html_page.Piece | html_page.Part] = []
    for words, text in (("before", column.effective_before), ("after", column.effective_after)):
        if text:
            pieces += [html_page.Piece(html_page.TEXT, [f"Its Effective logic {words}:"]),
                       html_page.Piece(html_page.BLOCK, [text])]
    return pieces


def _rewrite_part(rewrite: ToolboxRewrite) -> html_page.Part:
    """An Upgrade's rewrite, apart from the user's changes."""
    return html_page.Part(
        f"toolbox-{re.sub(r'[^0-9]', '', rewrite.recorded_at)}", 2,
        f"Rewritten by the Toolbox's upgrade to {rewrite.toolbox_version}",
        [html_page.Piece(html_page.TEXT, [
            f"Recorded {rewrite.recorded_at} by {rewrite.recorded_by}: the Toolbox writes the "
            "same logic as other Hive, so these are no change of yours."]),
         html_page.Piece(html_page.ITEMS, [f"`{name}`" for name in rewrite.columns])])


def to_markdown(found: Difference, footer: str) -> str:
    """The Markdown twin: its title, what it shows, each section, then the footer."""
    lines = ["# Lineage difference", "", ABOUT, "", counts_line(found), ""]
    for part in difference_parts(found):
        lines += html_page.part_markdown(part)
    return "\n".join(lines + ["---", "", footer, ""])


def to_html(found: Difference, footer: str) -> str:
    """The HTML page, built from the page module: the title, what it shows, its legend and the
    tables or runs not recorded; the drawing of the tables, by what changed of each, and the
    side panel, holding each changed table's section and a line for each unchanged one; then
    the Building blocks that changed and each Upgrade's rewrite, folded; then the footer. The
    drawing is in the page, so it draws the same with scripts off, each section under it; with
    scripts on, it zooms, pans and lights up a path, and a box opens its panel."""
    changed = {table.table: table for table in found.tables}
    header, panel, after = [], [], []
    for part in difference_parts(found):
        if part.key == "not-recorded":
            header.append(html_page.part_html(part))
        elif part.key.startswith("toolbox-"):
            after.append(f'<details class="toolbox"><summary>{html.escape(part.heading)}'
                         f"</summary>{html_page.part_html(part)}</details>")
        elif part.key == "blocks":
            after.append(html_page.part_html(part))
        else:
            panel.append(part)
    panel += [_unchanged_part(found, table) for table in found.kinds if table not in changed]
    drawing = _difference_drawing(found, changed)
    body = (f"<header><h1>Lineage difference</h1><p>{html_page.inline_html(ABOUT)}</p>"
            f"<p>{html_page.inline_html(counts_line(found))}</p>"
            f"{html_page.legend(LEGEND)}{''.join(header)}</header>\n<main>\n"
            f'<div class="wrap">{drawing.svg}</div>\n{html_page.panel(panel)}\n</main>\n'
            f'<div class="after">{"".join(after)}</div>\n'
            f"<footer>{html.escape(footer)}</footer>")
    tables = list(found.kinds)
    # What the module's drawing script lights a path through: each box, its own group, and
    # each arrow.
    visible = {"boxes": [{"id": _box_id(table), "group": _box_id(table)} for table in tables],
               "arrows": [[_box_id(read), _box_id(table), "value"]
                          for read, table in _arrows(found)]}
    script = SCRIPT.replace("__DATA__", html_page.script_json(visible), 1)
    return html_page.page("Lineage difference", body,
                          [CSS, drawing.size_css, html_page.DRAWING_CSS, html_page.PANEL_CSS],
                          [html_page.DRAWING_SCRIPT, html_page.PANEL_SCRIPT, script])


# --- The drawing ------------------------------------------------------------------------------

# Sizes in the drawing, in pixels, as the Project lineage draws its boxes.
BOX_WIDTH = project_lineage.BOX_WIDTH
COLUMN_GAP = project_lineage.COLUMN_GAP
BOX_GAP = project_lineage.BOX_GAP
LINE_HEIGHT = project_lineage.LINE_HEIGHT


def _box_id(table: str) -> str:
    """The id of a table's box: its section's, with "box-" in front."""
    return f"box-{part_key(table)}"


def _arrows(found: Difference) -> list[tuple[str, str]]:
    """Each arrow the drawing shows, as (the table read, the table reading it), both drawn."""
    arrows = []
    for table in found.kinds:
        arrows += [(read, table) for read in _drawn_reads(found, table)]
    return arrows


def _drawn_reads(found: Difference, table: str) -> list[str]:
    """The tables `table` reads that the drawing shows."""
    return [read for read in found.reads.get(table, ()) if read in found.kinds]


def _changed_box_lines(found: Difference, table: str, changed: dict[str, ChangedTable]
                       ) -> list[str]:
    """The lines a table's box shows: its name, what it is, and what changed of it."""
    lines = [table, KIND_WORDS.get(found.kinds[table], found.kinds[table])]
    if table not in changed:
        return [*lines, "unchanged"]
    columns = changed[table].columns
    words = TABLE_WORDS[changed[table].change]
    return [*lines, f"{words}: {counted(len(columns), 'column')}"]


def _box_class(table: str, changed: dict[str, ChangedTable]) -> str:
    """The kind a table's box is drawn as, as html_page.KINDS names it."""
    if table not in changed:
        return "unchanged"
    return TABLE_KINDS[changed[table].change]


def _difference_drawing(found: Difference, changed: dict[str, ChangedTable]
                        ) -> project_lineage.Drawing:
    """The SVG picture: each table's box, in its column, left of each table that reads it, and
    a curve for each arrow, data-a and data-b naming the boxes at its two ends, so a click
    lights up a path."""
    tables = list(found.kinds)
    reads = {table: _drawn_reads(found, table) for table in tables}
    columns = project_lineage.table_columns(tables, reads)
    places: dict[str, tuple[int, int]] = {}
    heights: dict[str, int] = {}
    tops = [0] * (max(columns.values(), default=0) + 1)
    for table in tables:
        heights[table] = 10 + LINE_HEIGHT * len(_changed_box_lines(found, table, changed))
        places[table] = (columns[table] * (BOX_WIDTH + COLUMN_GAP), tops[columns[table]])
        tops[columns[table]] += heights[table] + BOX_GAP
    parts: list[str] = []
    for read, table in _arrows(found):
        (x, y), (x2, y2) = places[read], places[table]
        start, end = (x + BOX_WIDTH, y + heights[read] // 2), (x2, y2 + heights[table] // 2)
        middle = (start[0] + end[0]) // 2
        parts.append(f'<path class="e" data-a="{_box_id(read)}" data-b="{_box_id(table)}" '
                     f'd="M{start[0]},{start[1]} C{middle},{start[1]} '
                     f'{middle},{end[1]} {end[0]},{end[1]}"/>')
    for table in tables:
        parts.append(_changed_box_svg(found, table, changed, places[table], heights[table]))
    width = len(tops) * (BOX_WIDTH + COLUMN_GAP) - COLUMN_GAP
    height = max(tops, default=0)
    # A 10-pixel margin all round.
    return project_lineage.Drawing(
        f'<svg viewBox="-10 -10 {width + 20} {height + 20}">{"".join(parts)}</svg>',
        f".wrap svg{{min-width:{round(width * 0.8)}px;"
        f"aspect-ratio:{width + 20}/{height + 20}}}")


def _changed_box_svg(found: Difference, table: str, changed: dict[str, ChangedTable],
             place: tuple[int, int], height: int) -> str:
    """The SVG for one table's box: its rectangle, its lines of text, the first in bold, and a
    tooltip holding every line whole. Tab reaches it, and it opens its table's section."""
    lines = _changed_box_lines(found, table, changed)
    texts: list[str] = []
    for number, line in enumerate(lines):
        bold = ' class="l"' if number == 0 else ""
        text = html.escape(shortened(line, 34 if number == 0 else 38))
        texts.append(f'<text x="8" y="{17 + number * LINE_HEIGHT}"{bold}>{text}</text>')
    return (f'<g class="n {_box_class(table, changed)}" id="{_box_id(table)}" tabindex="0" '
            f'role="button" data-parts="{part_key(table)}" '
            f'transform="translate({place[0]},{place[1]})">'
            f'<rect width="{BOX_WIDTH}" height="{height}" rx="4"/>{"".join(texts)}'
            f"<title>{html.escape(chr(10).join(lines))}</title></g>")


def _unchanged_part(found: Difference, table: str) -> html_page.Part:
    """What the panel shows for a table no column of which changed: that, and what it reads.
    Only the page holds it: the Markdown twin lists what changed."""
    reads = [f"`{read}`" for read in found.reads.get(table, ())]
    lines = [f"No column of it changed, {found.since}."]
    if reads:
        lines.append(f"It reads {in_words(reads)}.")
    return html_page.Part(part_key(table), 2, f"`{table}`: unchanged",
                          [html_page.Piece(html_page.TEXT, lines)])


# --- Writing the files ------------------------------------------------------------------------


def read_sent(root: Path) -> list[dict[str, str]]:
    """The rows of the Project's admin/sent.csv, oldest first, or none without it."""
    path = root / SENT
    if not path.is_file():
        return []
    with open(path, encoding="utf-8", newline="") as sent:
        return list(csv.DictReader(sent))


def write_difference(root: Path, call: str, since: str | None,
                     tables: str | list[str] | None, not_built: dict[str, str]
                     ) -> tuple[list[str], list[str]]:
    """Write the difference into admin/lineage/, as an HTML page and its Markdown twin named
    by the time, such as admin/lineage/20261120-093000-difference.html: what
    project.export_lineage_difference says it did, a line each, and the two files, by their
    paths in the Project."""
    from . import VERSION  # the folder's __init__ sets it once every file is imported

    rows = read_rows(root)
    if not rows and (root / STATE_FILE).is_file():
        # A recording of a Project with no column yet writes the file's header alone.
        found = Difference(since="since the first recording, which found no column",
                           start=None, end=None, tables=(), blocks=(), toolbox=(),
                           not_recorded=dict(not_built), kinds={}, reads={})
    else:
        found = difference(rows, since=since, tables=tables, sent=read_sent(root),
                           not_built=not_built, call=call)
    when = unchecked.now()
    footer = (f"Made by {call} on {when:%Y-%m-%d %H:%M}, from {STATE_FILE.as_posix()}, "
              f"with {VERSION}.")
    folder = root / STATE_FILE.parent
    stem = f"{when.strftime(unchecked.TIME_IN_A_NAME)}-difference"
    html_path, markdown_path = folder / f"{stem}.html", folder / f"{stem}.md"
    folder.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(to_markdown(found, footer), encoding="utf-8")
    html_path.write_text(to_html(found, footer), encoding="utf-8")
    lines = [f"Wrote {html_path.relative_to(root).as_posix()} and its Markdown twin, "
             f"{markdown_path.name}: {counts_line(found)}"]
    if found.not_recorded:
        lines.append(f"Not recorded, as the page shows: {in_words(list(found.not_recorded))}.")
    written = [path.relative_to(root).as_posix() for path in (html_path, markdown_path)]
    return lines, written
