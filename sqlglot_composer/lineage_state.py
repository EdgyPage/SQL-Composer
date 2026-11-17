"""The Lineage state: the Project's record of each column's own logic and Effective logic, a
row added each time one changes (Toolbox 8.8, ticket 02).

admin/lineage/lineage_state.csv is added to, never rewritten. record(...) compares the
columns effective_logic.project_logic gives with the file's last word on each, and adds a row
for each column that changed: on the first recording, a row for every column, `first`; after
it `added`, `removed`, `own`, `opaque`, `retyped` or `inherited`, an inherited change naming in
`because` the changes up its chain it comes from; and, in the recording an Upgrade makes,
`toolbox` for each change but a removal, since it is the Toolbox writing the same logic as
other Hive (ADR 0015). Each Building block file's hash is kept in the same file, as rows of
kind building_block, so an own change that came with a change to a block its table imports
names that block. columns_at(...) replays the file up to any recording. Nothing here reaches
the warehouse: it reads only the Project's files.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from . import unchecked
from .effective_logic import REFERENCE, SAVED_TABLE, SCHEDULED_RUN, ColumnLogic, ProjectLogic
from .lineage import scripts_commit
from .project_files import BUILDING_BLOCK, REGISTRY, Registry
from .shared import counted, in_words

# The Lineage state, in a Project, and its columns, in the order the file holds them.
STATE_FILE = Path("admin") / "lineage" / "lineage_state.csv"
STATE_COLUMNS = ["recorded_at", "commit", "recorded_by", "toolbox_version", "table", "column",
                 "kind", "change", "type", "own_logic", "reads", "rows_that_count", "own_hash",
                 "effective_hash", "because"]
# The kind of a Building block's row: its table is the block's name, and its column is empty.
BLOCK = BUILDING_BLOCK.kind

# What a row says changed.
FIRST = "first"
ADDED = "added"
REMOVED = "removed"
OWN = "own"
OPAQUE = "opaque"
RETYPED = "retyped"
INHERITED = "inherited"
TOOLBOX = "toolbox"
# The changes an inherited change comes from: those made at a column itself, up its chain.
ROOT_CHANGES = (OWN, OPAQUE, RETYPED, ADDED, REMOVED)
# The changes the printed line counts, in the order it names them.
COUNTED_CHANGES = (OWN, INHERITED, RETYPED, OPAQUE, ADDED, REMOVED, TOOLBOX)
# The registry's kind for each kind of recorded column, whose removal there marks it removed.
REGISTRY_KINDS = {SAVED_TABLE: "table_folder", SCHEDULED_RUN: "scheduled_run",
                  REFERENCE: "reference"}
# The first line a recording that found nothing changed prints.
NO_CHANGE = "Lineage state: no change since the last recording."


def read_rows(root: Path) -> list[dict[str, str]]:
    """The rows of the Project's Lineage state, oldest first, or none when it has none yet."""
    path = root / STATE_FILE
    if not path.is_file():
        return []
    with open(path, encoding="utf-8", newline="") as state:
        return list(csv.DictReader(state))


def columns_at(rows: list[dict[str, str]], recorded_at: str | None = None
               ) -> dict[tuple[str, str], dict[str, str]]:
    """Each column's last row as of the recording at `recorded_at` (every row, given None), by
    (table, column): what the Project held then. A Building block's is by (its name, "").
    A column removed by then isn't there."""
    columns: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        if recorded_at is not None and row["recorded_at"] > recorded_at:
            break
        key = (row["table"], row["column"])
        if row["change"] == REMOVED:
            columns.pop(key, None)
        else:
            columns[key] = row
    return columns


def record(root: Path, logic: ProjectLogic, recorded_by: str, by_upgrade: bool = False
           ) -> list[str]:
    """Add to the Lineage state of the Project at `root` a row for each column, and each
    Building block, that changed since its last recording, as `logic` holds them now, made by
    `recorded_by`: the lines a Project action prints. `by_upgrade` marks each change an
    Upgrade's recording finds `toolbox`."""
    rows = read_rows(root)
    before = columns_at(rows)
    stamp = _stamp(root, recorded_by)
    blocks = _block_hashes(root)
    if not rows:
        new_rows = [_column_row(stamp, logic.columns[key], FIRST)
                    for key in sorted(logic.columns)]
        new_rows += [_block_row(stamp, name, digest, FIRST) for name, digest in blocks.items()]
        _write_rows(root, new_rows)
        tables = {column.table for column in logic.columns.values()}
        return [f"Lineage state: the first recording, "
                f"{counted(len(logic.columns), 'column')} of {counted(len(tables), 'table')}, "
                f"in {STATE_FILE.as_posix()}.", *_kept_lines(logic, [])]
    block_changes = _block_changes(before, blocks)
    changes = _column_changes(before, logic)
    removed, kept = _tables_gone(root, before, logic)
    changes.update(dict.fromkeys(removed, REMOVED))
    new_rows = [_changed_row(stamp, key, change, before, logic, changes, block_changes)
                for key, change in sorted(changes.items())]
    new_rows += _block_rows(stamp, before, blocks, block_changes)
    if by_upgrade:
        new_rows = [_as_toolbox(row) for row in new_rows]
    _write_rows(root, new_rows)
    return [*_summary_lines(new_rows), *_kept_lines(logic, kept)]


def _stamp(root: Path, recorded_by: str) -> dict[str, str]:
    """What every row of one recording says of it: when, at which commit, by which call and
    with which Toolbox version. The commit is empty outside git."""
    from . import TOOLBOX_VERSION  # __init__.py sets it before importing this module

    commit = scripts_commit(root)
    if commit in ("nogit", "nocommits"):
        commit = ""
    return {"recorded_at": unchecked.now().strftime(unchecked.TIME_SHOWN), "commit": commit,
            "recorded_by": recorded_by, "toolbox_version": TOOLBOX_VERSION}


def _column_row(stamp: dict[str, str], column: ColumnLogic, change: str, because: str = ""
                ) -> dict[str, str]:
    """One recorded column's row: its stamp, what it is and holds, and what changed."""
    return {**stamp, "table": column.table, "column": column.column, "kind": column.kind,
            "change": change, "type": column.type, "own_logic": column.own_logic,
            "reads": ";".join(column.reads), "rows_that_count": column.rows_that_count,
            "own_hash": column.own_hash, "effective_hash": column.effective_hash,
            "because": because}


def _block_row(stamp: dict[str, str], name: str, digest: str, change: str) -> dict[str, str]:
    """One Building block's row: its name in place of a table, and its file's hash."""
    row = dict.fromkeys(STATE_COLUMNS, "")
    row.update(stamp)
    row.update({"table": name, "kind": BLOCK, "change": change, "own_hash": digest})
    return row


def _block_hashes(root: Path) -> dict[str, str]:
    """Each Building block's file hash, by its name, the file's line endings read as one, so
    a checkout on another computer hashes the same."""
    blocks = {}
    for path in sorted((root / BUILDING_BLOCK.folder).glob("*.py")):
        if path.name != "__init__.py":
            text = path.read_bytes().replace(b"\r\n", b"\n")
            blocks[path.stem] = hashlib.sha256(text).hexdigest()[:16]
    return blocks


def _block_changes(before: dict[tuple[str, str], dict[str, str]], blocks: dict[str, str]
                   ) -> dict[str, str]:
    """What changed of each Building block since the last recording, by its name."""
    known = {table: row["own_hash"] for (table, _), row in before.items()
             if row["kind"] == BLOCK}
    changes = dict.fromkeys([name for name in blocks if name not in known], ADDED)
    changes.update({name: REMOVED for name in known if name not in blocks})
    changes.update({name: OWN for name, digest in blocks.items()
                    if name in known and known[name] != digest})
    return changes


def _block_rows(stamp: dict[str, str], before: dict[tuple[str, str], dict[str, str]],
                blocks: dict[str, str], block_changes: dict[str, str]) -> list[dict[str, str]]:
    """The row of each Building block that changed: its hash now, or, removed, as it last
    was."""
    rows = []
    for name, change in sorted(block_changes.items()):
        if change == REMOVED:
            digest = before[(name, "")]["own_hash"]
        else:
            digest = blocks[name]
        rows.append(_block_row(stamp, name, digest, change))
    return rows


def _column_changes(before: dict[tuple[str, str], dict[str, str]], logic: ProjectLogic
                    ) -> dict[tuple[str, str], str]:
    """What changed of each column `logic` holds since the last recording, and each column
    gone from a table that still builds, by (table, column). A Table reference's column is
    retyped before its logic is looked at, since its logic is its type."""
    changes = {}
    for key, column in logic.columns.items():
        last = before.get(key)
        if last is None:
            changes[key] = ADDED
        elif column.kind == REFERENCE and column.type != last["type"]:
            changes[key] = RETYPED
        elif column.own_hash != last["own_hash"]:
            changes[key] = _own_or_opaque(column)
        elif column.type != last["type"]:
            changes[key] = RETYPED
        elif column.effective_hash != last["effective_hash"]:
            changes[key] = INHERITED
    tables = {column.table for column in logic.columns.values()}
    for key, last in before.items():
        if last["kind"] != BLOCK and key[0] in tables and key not in logic.columns:
            changes[key] = REMOVED
    return changes


def _own_or_opaque(column: ColumnLogic) -> str:
    """An own change, said as opaque for a column an opaque step writes."""
    if column.opaque:
        return OPAQUE
    return OWN


def _tables_gone(root: Path, before: dict[tuple[str, str], dict[str, str]],
                 logic: ProjectLogic) -> tuple[list[tuple[str, str]], list[str]]:
    """Of the tables the last recording holds that `logic` holds none of: the columns of each
    the registry marks removed, now removed, and each other one, whose rows stand, by name.
    One that didn't build is neither: logic.not_built names it."""
    tables = {column.table for column in logic.columns.values()}
    removed, kept = [], []
    for key, last in before.items():
        table = key[0]
        if last["kind"] == BLOCK or table in tables or table in logic.not_built:
            continue
        if _is_removed(root, last["kind"], table):
            removed.append(key)
        elif table not in kept:
            kept.append(table)
    return removed, kept


def _is_removed(root: Path, kind: str, table: str) -> bool:
    """Whether the registry marks removed what a recorded column of `kind` belongs to: its
    Table folder or Table reference, or, for a Scheduled run's Statement, <run>.<result>, its
    run."""
    if not (root / REGISTRY).is_file():
        return False
    name = table
    if kind == SCHEDULED_RUN:
        name = table.split(".", 1)[0]
    registry = Registry(root)
    listed = [row for row in registry.rows
              if row["kind"] == REGISTRY_KINDS[kind] and row["table"] == name]
    return bool(listed) and all(row["removed_at"] for row in listed)


def _changed_row(stamp: dict[str, str], key: tuple[str, str], change: str,
                 before: dict[tuple[str, str], dict[str, str]], logic: ProjectLogic,
                 changes: dict[tuple[str, str], str], block_changes: dict[str, str]
                 ) -> dict[str, str]:
    """The row of a column that changed: as it is now, or, removed, as it last was."""
    if change == REMOVED:
        return {**before[key], **stamp, "change": REMOVED, "because": ""}
    column = logic.columns[key]
    because = ""
    if change == INHERITED:
        because = ";".join(_roots(key, logic, changes))
    elif change in (OWN, OPAQUE):
        blocks = logic.blocks_of.get(column.table, ())
        because = ";".join(f"{BLOCK}:{name}" for name in blocks if name in block_changes)
    return _column_row(stamp, column, change, because)


def _roots(key: tuple[str, str], logic: ProjectLogic, changes: dict[tuple[str, str], str]
           ) -> list[str]:
    """The columns up the chain of the column at `key` whose own change, retyping, addition
    or removal in this recording its inherited change comes from, as <db>.<table>.<column>,
    nearest first."""
    roots, seen = [], set()
    waiting = list(logic.columns[key].reads)
    while waiting:
        read = waiting.pop(0)
        if read in seen:
            continue
        seen.add(read)
        table, column = read.rsplit(".", 1)
        if changes.get((table, column)) in ROOT_CHANGES:
            roots.append(read)
        if (table, column) in logic.columns:
            waiting += logic.columns[(table, column)].reads
    return roots


def _as_toolbox(row: dict[str, str]) -> dict[str, str]:
    """A row of an Upgrade's recording: each change marked `toolbox`, the Toolbox writing the
    same logic as other Hive, but a removal, which the replay needs as it is."""
    if row["change"] == REMOVED:
        return row
    return {**row, "change": TOOLBOX, "because": ""}


def _write_rows(root: Path, rows: list[dict[str, str]]) -> None:
    """Add `rows` to the end of the Project's Lineage state, writing its header first when
    the file is new."""
    path = root / STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.is_file()
    with open(path, "a", encoding="utf-8", newline="") as state:
        writer = csv.DictWriter(state, STATE_COLUMNS, lineterminator="\n")
        if is_new:
            writer.writeheader()
        writer.writerows(rows)


def _summary_lines(new_rows: list[dict[str, str]]) -> list[str]:
    """What a recording after the first says it found: the columns changed, counted by what
    changed, and the Building blocks changed."""
    columns = [row for row in new_rows if row["kind"] != BLOCK]
    blocks = [row["table"] for row in new_rows if row["kind"] == BLOCK]
    if not new_rows:
        return [NO_CHANGE]
    lines = ["Lineage state: no column changed."]
    if columns:
        found = [row["change"] for row in columns]
        counts = [f"{found.count(change)} {change}" for change in COUNTED_CHANGES
                  if change in found]
        lines = [f"Lineage state: {counted(len(columns), 'column')} changed "
                 f"({', '.join(counts)}): project.export_lineage_difference() shows them."]
    if blocks:
        lines.append(f"Building blocks changed: {in_words(blocks)}.")
    return lines


def _kept_lines(logic: ProjectLogic, kept: list[str]) -> list[str]:
    """A line for each table or Scheduled run not recorded, whose rows from before stand: each
    that didn't build, with why, and each gone that the registry doesn't mark removed."""
    lines = [f"Not recorded, its rows from before kept: {name}: {why}"
             for name, why in logic.not_built.items()]
    lines += [f"Not recorded, its rows from before kept: {table} isn't in the Project, and the "
              "registry doesn't mark it removed. If you took it out by hand, mark it removed "
              "with its Project action: remove_table, remove_reference or "
              "remove_scheduled_run." for table in kept]
    return lines
