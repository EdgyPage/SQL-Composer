"""The Workbook check: a Formula workbook's Hive run over the workbook's own Tables and compared
with the values the workbook shows, as last saved (Toolbox 8.9, ticket 09; ADR 0016;
CONTEXT.md's Workbook check).

A convert of a batch holding a workbook ends with it. Each final the batch converted, from the
workbook's own Hive or from a script Copilot wrote for it, runs on sqlglot's executor
(`hive_executor.run_on_executor`) on this computer, each `<database>.<table>` it reads standing
for the rows of the workbook's Table of that name, or a plain range's rows for the table its
pivot reads. Its rows are then compared with the values Excel last saved in the workbook: a
Table's cells, formulas' results among them, a Total Row's, or a PivotTable's, cell by cell, at
each total level.

- **A match**: numbers within a relative 1e-9, and within 1e-12 of zero, where a relative test
  can't hold, on the values saved, not as shown; a day as its date; a blank as NULL. Excel's 0
  or "" for a blank a formula reads, where Hive gives NULL, matches only where file 11's M1
  marks that formula's column: the check's reading of M1.
- **An Excel error**, such as #DIV/0! or #REF!, where Hive gives NULL, is neither a match nor a
  difference: each such cell is listed apart, for the person to look at.
- **Rows** are matched on the Table's Key, from the Keys sheet, else on the columns the final
  groups by, else the Table's typed columns, else every column; a pivot's on its fields' items;
  in any order.
- **A difference** is a cell whose value the Hive doesn't give: one line each, such as
  "region East, dt Mar: Excel 1,204, Hive 1,198". It stops nothing. A final the executor can't
  run, such as one using a function it has no Python for, is named with why, never guessed at.
- **A Pivot filter answered** "fold", "batch" or "tables" (ticket 08) rewrote its table, whose
  rows are no longer the PivotTable's selection: the table is checked as converted, on the Hive
  it was converted from, and the report says so in a line. A table per value made beside the
  first stands for no final of the workbook, so it is not checked, and the report says why.

It never reads the warehouse, and never calls the user's `query`: the workbook's rows are an
old sample, which the warehouse's rows have moved on from, so it compares the Hive with the
workbook alone.
"""

from __future__ import annotations

import datetime
import math
import statistics
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

from .hive_executor import (
    HIVE_DAYS,
    MissingPart,
    NtileWithNoParts,
    reason_without_place,
    run_on_executor,
)
from .shared import counted, in_words, singular_or_plural
from .workbook_formulas import MARK, PLAIN_NAME, hive_name, snake_case, tables_of
from .workbook_hive import workbook_hive
from .workbook_pivot_hive import (
    PivotLevel,
    level_final_name,
    own_level,
    pivot_of,
    pivot_pieces,
    range_table_name,
    value_captioned,
    value_column_name,
)
from .workbook_reader import (
    FORMULA,
    RANGE,
    TYPED,
    VALUES,
    PivotCell,
    PivotTable,
    Table,
    Workbook,
    is_formula,
)
from .workbook_totals import TOTAL_ROW
from .writing import read_hive

# How close two numbers must be to match: a relative 1e-9, and 1e-12 of zero, where a relative
# test can't hold.
RELATIVE = 1e-9
NEAR_ZERO = 1e-12
# The errors Excel saves in a cell in place of a value: where Hive gives NULL, each is listed
# apart, neither a match nor a difference.
EXCEL_ERRORS = frozenset({"#DIV/0!", "#N/A", "#NAME?", "#NULL!", "#NUM!", "#REF!", "#VALUE!",
                          "#SPILL!", "#CALC!", "#GETTING_DATA"})
# What the report says of every workbook it checks, after "The Workbook check of runs.xlsx":
# what the check did, what a difference means, and why one from the warehouse is expected.
ABOUT = ("ran the Hive of each table the workbook gave, on this computer, over the workbook's "
         "own Tables, and compared its rows with the values the workbook shows, as last "
         "saved. A difference means the Hive doesn't give what the workbook's formula, query "
         "or PivotTable gave on the same rows: look at each one, though none stops anything. "
         "The workbook's rows are an old sample, so the warehouse's rows will differ from "
         "them: this compares the Hive with the workbook alone, never with the warehouse.")
NEXT = ("For each difference, compare the table's Hive, in the `# logic` cell of its notebook, "
        "with the workbook's formula, query or PivotTable; the rule its checklist names may "
        "explain it. Convert again after a change to check again.")
# What the report says of a table it couldn't check: how to compare it by hand.
BY_HAND = ("To compare it by hand, run its table's preview() on your warehouse and look for "
           "the same rows in the workbook, though the warehouse's rows may have moved on.")
# What to do about a row the Hive gives that the workbook doesn't show.
FIX_THE_HIVE = "fix the Hive, in the `# logic` cell of its table's notebook"


def _to_date(day: object, *_: object) -> datetime.date | None:
    """Hive's to_date, which YEAR, MONTH and DAY read a day through: the day of a text such as
    '2026-09-24', or of a date."""
    if day is None:
        return None
    if isinstance(day, datetime.date):
        return datetime.date(day.year, day.month, day.day)
    return datetime.date.fromisoformat(str(day)[:10])


def _date_format(day: object, pattern: object, *_: object) -> str | None:
    """Hive's date_format, its pattern as sqlglot reads it, such as '%b' for 'MMM'."""
    if day is None or pattern is None:
        return None
    return day.strftime(str(pattern))


def _quarter(day: object) -> int | None:
    """Hive's quarter: 1 to 4, of a day as text or a date."""
    found = _to_date(day)
    if found is None:
        return None
    return (found.month + 2) // 3


def _spread(measure: Callable[[list[float]], float], fewest: int
            ) -> Callable[[Iterable[object]], float | None]:
    """An aggregate of the values given, NULL left out, by `measure`: NULL with fewer than
    `fewest` values, as Excel's STDEV.S of one value has none."""
    def aggregate(values: Iterable[object]) -> float | None:
        found = [value for value in values if value is not None]
        if len(found) < fewest:
            return None
        return measure(found)
    return aggregate


# The functions the check teaches sqlglot's executor, by its name for each, beside the Hive
# day functions: what a Formula workbook's Hive writes that it has no Python for.
WORKBOOK_FUNCTIONS: dict[str, Callable[..., object]] = {
    **HIVE_DAYS,
    "TSORDSTODATE": _to_date,
    "TIMETOSTR": _date_format,
    "QUARTER": _quarter,
    "STDDEVSAMP": _spread(statistics.stdev, 2),
    "STDDEVPOP": _spread(statistics.pstdev, 1),
    "VARIANCEPOP": _spread(statistics.pvariance, 1),
}


@dataclass(frozen=True)
class FinalHive:
    """One final to check: its name in the workbook, such as `PivotTable1`; the Saved table it
    became, by its full name, such as `mart_dev.pivot`; its Hive; and the script it is, where
    Copilot wrote it, "" for the workbook's own.

    Where its table's Pivot filters were answered other than "keep" since, its rows are no
    longer the PivotTable's selection, so its Hive is the one it was converted from, never the
    one the answers wrote: `as_converted` says what the answers made of the table, such as
    `before its Pivot filter's answer "fold"; the table now holds every status`, "" where they
    made nothing; and `beside` names each table per value made beside it, which no final of
    the workbook stands for, so none is checked."""

    final: str
    table: str
    hive: str
    script: str = ""
    as_converted: str = ""
    beside: tuple[str, ...] = ()


@dataclass
class CheckedFinal:
    """What the check found of one final: the final, as FinalHive gives it; what the workbook
    calls it, such as `PivotTable "PivotTable1"`; how many cells it compared, and how many of
    them differ; each difference, a line a cell or a row; each cell where the workbook shows
    an Excel error and Hive gives NULL; each column it couldn't compare, as the workbook holds
    no value saved for it; and why it wasn't checked, "" where it was."""

    final: FinalHive
    place: str = ""
    compared: int = 0
    differing: int = 0
    differences: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    unstored: list[str] = field(default_factory=list)
    not_checked: str = ""


@dataclass
class WorkbookCheck:
    """The Workbook check of one workbook: its file's name, and each final it checked."""

    file: str
    finals: list[CheckedFinal]


class _NotRun(Exception):
    """Why a final's Hive couldn't be run over the workbook's rows."""


@dataclass
class _HiveRows:
    """A final's rows as the executor gave them: its columns, in lower case, and its rows."""

    columns: list[str]
    rows: list[tuple[object, ...]]

    def as_dicts(self) -> list[dict[str, object]]:
        """Each row, by its columns."""
        return [dict(zip(self.columns, row, strict=True)) for row in self.rows]


def check_workbook(workbook: Workbook, file: str, finals: list[FinalHive],
                   database: str) -> WorkbookCheck:
    """The Workbook check of `finals`, each a final of `workbook`, the file `file`: each run
    over the workbook's own Tables, a table it names without a database read in `database`,
    and compared with the values Excel last stored, as the module docstring says."""
    marked = _marked_blanks(workbook)
    checked: dict[str, CheckedFinal] = {}
    results: dict[str, _HiveRows] = {}
    for final in finals:
        checked[final.final] = CheckedFinal(final, _workbook_name_of(final.final, workbook))
        try:
            tree = _query_of(final.hive)
            results[final.final] = _run_over_the_workbook(tree, workbook, database)
        except _NotRun as why:
            checked[final.final].not_checked = str(why)
            continue
        _compare_table_or_total(checked[final.final], tree, workbook,
                                results[final.final], marked)
    for piece in pivot_pieces(workbook):
        _compare_pivot(pivot_of(piece, workbook), piece.name, results, checked)
    for found in checked.values():
        if not (found.compared or found.not_checked or found.differences or found.unstored
                or found.errors):
            found.not_checked = ("the workbook holds no Table, Total Row or PivotTable "
                                 f"of this name, {found.final.final}, whose cells it could "
                                 "compare")
    return WorkbookCheck(file, list(checked.values()))


# --- Running a final over the workbook's rows ------------------------------------------------


def _query_of(hive: str) -> exp.Query:
    """The one query a final's Hive is, read by sqlglot."""
    try:
        trees = read_hive(hive)
    except sqlglot.errors.SqlglotError as error:
        raise _NotRun(f"the check couldn't read its Hive: {reason_without_place(error)}"
                      ) from error
    queries = [tree for tree in trees if isinstance(tree, exp.Query)]
    if len(queries) != 1 or len(trees) != 1:
        raise _NotRun(f"its Hive holds {counted(len(trees), 'statement')}, and the check runs "
                      "one query alone")
    return queries[0]


def _run_over_the_workbook(tree: exp.Query, workbook: Workbook, database: str) -> _HiveRows:
    """A final's rows, its query run on sqlglot's executor over the workbook's Tables."""
    tree = tree.copy()
    schema: dict[str, dict[str, dict[str, str]]] = {}
    rows: dict[str, dict[str, list[dict[str, object]]]] = {}
    ctes = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if name in ctes and not table.db:
            continue
        source = _table_standing_for(name, workbook)
        if source is None:
            raise _NotRun(f"it reads {table.db or database}.{table.name}, which is no Table of "
                          "the workbook, so the workbook holds no rows to run it over")
        held = (table.db or database).lower()
        table.set("db", exp.to_identifier(held))
        table.set("this", exp.to_identifier(name))
        schema.setdefault(held, {})[name] = _column_types(source)
        rows.setdefault(held, {})[name] = _stand_in_rows(source)
    try:
        columns, found = run_on_executor(tree, schema, rows, WORKBOOK_FUNCTIONS)
    except MissingPart as missing:
        raise _NotRun(f"the check can't run {missing.missing} on this computer"
                      ) from missing
    except NtileWithNoParts as ntile:
        raise _NotRun(f"its Hive splits each group into NTILE({ntile.parts}) parts, which "
                      "Hive refuses too") from ntile
    except Exception as error:  # the check stops nothing: whatever stops the executor is named
        raise _NotRun("the check couldn't run its Hive on this computer: "
                      f"{reason_without_place(error)}") from error
    return _HiveRows([column.lower() for column in columns], found)


def _table_standing_for(name: str, workbook: Workbook) -> Table | None:
    """The workbook's Table a database table stands for, by its name, or the rows of a plain
    range a pivot reads, by the table proposed for it (PS3); None where there is neither."""
    found = tables_of(workbook).get(name)
    if found is not None:
        return found
    for pivot in workbook.pivot_tables:
        pieces = pivot.source.pieces
        if (len(pieces) == 1 and pieces[0].kind == RANGE and pivot.source.table is not None
                and range_table_name(pieces[0], workbook) == name):
            return pivot.source.table
    return None


def _hive_column(header: str) -> str:
    """A Table's column as its Hive names it, in lower case: its header, or a header that
    isn't a plain name in snake case."""
    if PLAIN_NAME.fullmatch(header):
        return header.lower()
    return snake_case(header)


def _stand_in_rows(table: Table) -> list[dict[str, object]]:
    """A Table's rows as the check stands them in for its database table: each column's
    values as Excel last stored them, a day as its text, as Hive holds a date."""
    rows = []
    for stored in _rows_of_stored(table):
        rows.append({name: _hive_value(value) for name, value in stored.items()})
    return rows


def _rows_of_stored(table: Table) -> list[dict[str, object]]:
    """A Table's rows as Excel last stored them, each by its columns' names."""
    names = [_hive_column(column.header) for column in table.columns]
    count = 0
    if table.columns:
        count = len(table.columns[0].stored)
    rows = []
    for row in range(count):
        rows.append({name: column.stored[row] for name, column in zip(names, table.columns)})
    return rows


def _hive_value(value: object) -> object:
    """A value the workbook saved, as Hive holds it: a day as its text, such as '2026-09-24', a
    time of day after it where it has one."""
    if isinstance(value, datetime.datetime) and value.time() == datetime.time():
        return value.date().isoformat()
    if isinstance(value, datetime.datetime):
        return value.isoformat(sep=" ")
    return value


def _column_types(table: Table) -> dict[str, str]:
    """Each column's Hive type, by the values Excel stored in it."""
    types = {}
    for column in table.columns:
        values = [_hive_value(value) for value in column.stored if value is not None]
        kind = "string"
        if values and all(isinstance(value, bool) for value in values):
            kind = "boolean"
        elif values and all(isinstance(value, int) and not isinstance(value, bool)
                            for value in values):
            kind = "bigint"
        elif values and all(isinstance(value, (int, float)) and not isinstance(value, bool)
                            for value in values):
            kind = "double"
        types[_hive_column(column.header)] = kind
    return types


# --- Comparing a Table's rows, or a Total Row's ----------------------------------------------


def _compare_table_or_total(checked: CheckedFinal, tree: exp.Query, workbook: Workbook,
                            given: _HiveRows, marked: dict[str, set[str]]) -> None:
    """Compare a final that is a Table, or a Table's Total Row, with its stored cells."""
    name = checked.final.final
    tables = tables_of(workbook)
    if name.endswith(TOTAL_ROW) and name.removesuffix(TOTAL_ROW).lower() in tables:
        _compare_total_row(checked, tables[name.removesuffix(TOTAL_ROW).lower()], given)
    elif name.lower() in tables:
        table = tables[name.lower()]
        _compare_rows(checked, table, _key_columns(table, workbook, tree), given,
                      marked.get(table.name.lower(), set()))


def _compared_columns(checked: CheckedFinal, table: Table, given: _HiveRows) -> list[str]:
    """The columns of a Table whose stored values the check compares: each whose values the
    workbook holds, Excel having stored them; each other is noted as unstored, and each the
    Hive doesn't give is a difference."""
    compared = []
    for column in table.columns:
        name = _hive_column(column.header)
        results = [stored for stored, cell in zip(column.stored, column.cells)
                   if is_formula(cell)]
        if column.kind == FORMULA and all(result is None for result in results):
            checked.unstored.append(name)
        elif name not in given.columns:
            checked.differences.append(f"{name}: Excel has the column, Hive gives no column "
                                       "of that name")
        else:
            compared.append(name)
    return compared


def _compare_rows(checked: CheckedFinal, table: Table, key: list[str], given: _HiveRows,
                  marked: set[str]) -> None:
    """Compare a Table's stored rows with the final's, each matched on `key`, in any order."""
    compared = _compared_columns(checked, table, given)
    key = [column for column in key if column in compared] or compared
    excel = _rows_of_stored(table)
    hive = given.as_dicts()
    waiting: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for row in hive:
        waiting.setdefault(_key_of(row, key), []).append(row)
    for row in excel:
        checked.compared += len(key)  # its key's cells are compared in matching it
        matching = waiting.get(_key_of(row, key), [])
        if not matching:
            checked.differences.append(f"{_said_key(row, key)}: the workbook's Table holds "
                                       "this row, and the Hive doesn't give it")
            continue
        found = matching.pop(0)
        for column in compared:
            if column not in key:
                _compare_cell(checked, f"{_said_key(row, key)}, {column}", row[column],
                              found[column], column in marked)
    for rows in waiting.values():
        checked.differences += [f"{_said_key(row, key)}: the Hive gives this row, and the "
                                f"workbook's Table doesn't hold it: {FIX_THE_HIVE}"
                                for row in rows]


def _compare_total_row(checked: CheckedFinal, table: Table, given: _HiveRows) -> None:
    """Compare a Table's Total Row's stored cells with its final's one row."""
    if len(given.rows) != 1:
        rows = counted(len(given.rows), "row")
        checked.differences.append(f"Total Row: the Hive gives {rows} where the workbook "
                                   f"shows one: {FIX_THE_HIVE}")
        return
    row = given.as_dicts()[0]
    for column in table.columns:
        name = _hive_column(column.header)
        if not is_formula(column.total):
            continue  # a label, such as "Total", or no total
        if column.total_stored is None:
            checked.unstored.append(f"{name}'s total")
        elif name not in row:
            checked.differences.append(f"Total Row, {name}: Excel {_shown(column.total_stored)}"
                                       ", Hive gives no column of that name")
        else:
            _compare_cell(checked, f"Total Row, {name}", column.total_stored, row[name], False)


def _key_of(row: dict[str, object], key: list[str]) -> tuple[object, ...]:
    """A row's values in its key's columns, as rows are matched on them: a number as a float,
    so 1 matches 1.0, and a day as its text."""
    values = []
    for column in key:
        value = _as_compared(row.get(column))
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value = float(value)
        values.append(value)
    return tuple(values)


def _key_columns(table: Table, workbook: Workbook, tree: exp.Query) -> list[str]:
    """The columns a Table's rows are matched on: its Key, from the Keys sheet's row naming
    it, else the columns the final groups by, else its typed columns, else every column."""
    keys = tables_of(workbook).get("keys")
    if keys is not None and len(keys.columns) >= 2:
        for named, listed in zip(keys.columns[0].stored, keys.columns[1].stored):
            if str(named).lower() == table.name.lower() and listed:
                return [_hive_column(part.strip()) for part in str(listed).split(",")]
    grouped = _grouped_outputs(tree)
    if grouped:
        return grouped
    typed = [_hive_column(column.header) for column in table.columns if column.kind == TYPED]
    return typed or [_hive_column(column.header) for column in table.columns]


def _grouped_outputs(tree: exp.Query) -> list[str]:
    """The outputs of a final's outer SELECT that are what it groups by, in lower case."""
    if not isinstance(tree, exp.Select) or tree.args.get("group") is None:
        return []
    keys = list(tree.args["group"].expressions)
    return [output.alias_or_name.lower() for output in tree.expressions
            if output.unalias() in keys]


def _marked_blanks(workbook: Workbook) -> dict[str, set[str]]:
    """Each formula column file 11's M1 marks, its blank read as 0 or "" by Excel and as NULL
    by Hive, by its Table's name in lower case."""
    marked: dict[str, set[str]] = {}
    for note in workbook_hive(workbook).notes:
        if note.kind != MARK or note.rule != "M1" or "[" not in note.where:
            continue
        table, _, column = note.where.rstrip("]").partition("[")
        marked.setdefault(table.lower(), set()).add(_hive_column(column))
    return marked


# --- Comparing a PivotTable's cells ----------------------------------------------------------


def _compare_pivot(pivot: PivotTable, name: str, results: dict[str, _HiveRows],
                   checked: dict[str, CheckedFinal]) -> None:
    """Compare each stored cell of a pivot, `name` its piece's, with the row of the final of
    its total level that holds the cell's items, in the column of its value: each its own
    final's, where that final ran. A column the final doesn't give, and a row of it no cell
    of the pivot stands for, are differences too."""
    matched: dict[str, set[int]] = {}
    for cell in pivot.cells:
        final = _final_of_cell(pivot, name, cell)
        if final not in results or final not in checked:
            continue
        column, items = _cell_columns(pivot, cell)
        needed = [column, *[field_name for field_name, _ in items]]
        missing = [one for one in needed if one not in results[final].columns]
        if missing:  # said once a final, not once a cell
            said = [f"{one}: the PivotTable shows it, Hive gives no column of that name"
                    for one in missing]
            checked[final].differences += [line for line in said
                                           if line not in checked[final].differences]
            continue
        matched.setdefault(final, set())
        found, place = _cell_in_rows(column, items, results[final])
        said = _said_cell(pivot, cell)
        if place is None and cell.stored is not None:
            checked[final].compared += 1
            checked[final].differing += 1
            checked[final].differences.append(f"{said}: Excel {_shown(cell.stored)}, and the "
                                              "Hive gives no such row")
            continue
        if place is not None:
            matched[final].add(place)
        _compare_cell(checked[final], said, cell.stored, found, False)
    for final, places in matched.items():
        checked[final].differences += _rows_not_shown(
            results[final].as_dicts(), places, _level_of_final(pivot, name, final))


def _rows_not_shown(rows: list[dict[str, object]], shown: set[int], level: list[str]
                    ) -> list[str]:
    """A line for each row of a level's final that no cell of its pivot stands for, by its
    fields' items, the rows of one set of items said once: `shown` the places of the rows the
    pivot's cells stand for."""
    shown_said = {_said_row(rows[place], level) for place in shown}
    extra = Counter(_said_row(rows[place], level) for place in range(len(rows))
                    if place not in shown)
    lines = []
    for said, count in extra.items():
        if said in shown_said:
            lines.append(f"{said}: the Hive gives {count + 1} rows where the PivotTable shows "
                         f"one: {FIX_THE_HIVE}")
        else:
            rows_said = singular_or_plural(count, "a row", f"{count} rows")
            lines.append(f"{said}: the Hive gives {rows_said} the PivotTable doesn't show: "
                         f"{FIX_THE_HIVE}")
    return lines


def _items_of(cell: PivotCell) -> list[tuple[str, object]]:
    """The items a pivot's cell stands for, each with its field, outermost Row field first."""
    return [(field_name, item) for field_name, item in [*cell.row.items, *cell.column.items]
            if field_name != VALUES]


def _calculated_item_of(pivot: PivotTable, cell: PivotCell) -> tuple[str, object] | None:
    """The calculated item a pivot's cell stands for, with its field, or None."""
    for field_name, item in _items_of(cell):
        if str(item) in pivot.fields[field_name].calculated_items:
            return field_name, item
    return None


def _final_of_cell(pivot: PivotTable, name: str, cell: PivotCell) -> str:
    """The final of the total level a pivot's cell is on."""
    level = PivotLevel(
        tuple(field_name for field_name, _ in cell.row.items if field_name != VALUES),
        tuple(field_name for field_name, _ in cell.column.items if field_name != VALUES))
    if level == own_level(pivot):
        return name
    return level_final_name(name, level)


def _level_of_final(pivot: PivotTable, name: str, final: str) -> list[str]:
    """The fields a pivot's final groups by, in lower case: every field, for its own."""
    for cell in pivot.cells:
        if _final_of_cell(pivot, name, cell) == final:
            calculated = _calculated_item_of(pivot, cell)
            return [hive_name(field_name).lower() for field_name, item in _items_of(cell)
                    if (field_name, item) != calculated]
    return []


def _cell_columns(pivot: PivotTable, cell: PivotCell
                  ) -> tuple[str, list[tuple[str, object]]]:
    """Where a final's rows hold one of a pivot's cells: the column of its value, or of the
    calculated item it stands for, and each of its fields' columns with the cell's item."""
    calculated = _calculated_item_of(pivot, cell)
    column = value_column_name(value_captioned(pivot, cell.value))
    if calculated is not None:
        column = snake_case(str(calculated[1]))
    items = [(hive_name(field_name).lower(), item) for field_name, item in _items_of(cell)
             if (field_name, item) != calculated]
    return column.lower(), items


def _cell_in_rows(column: str, items: list[tuple[str, object]], given: _HiveRows
                  ) -> tuple[object, int | None]:
    """The value a final's rows give in `column` on the row whose fields' columns hold
    `items`, and that row's place; None and None where no row holds them."""
    for place, row in enumerate(given.as_dicts()):
        if all(is_same(item, row[field_name], False) for field_name, item in items):
            return row[column], place
    return None, None


def _compare_cell(checked: CheckedFinal, said: str, excel: object, hive: object,
                  blank_marked: bool) -> None:
    """Compare one cell, `said` where it is: an Excel error where Hive gives NULL is listed
    apart, and a value Hive doesn't give is a difference."""
    checked.compared += 1
    if _is_excel_error(excel) and hive is None:
        checked.errors.append(f"{said}: the workbook shows {excel}, and the Hive gives NULL")
    elif not is_same(excel, hive, blank_marked):
        checked.differing += 1
        checked.differences.append(f"{said}: {_said_values(excel, hive)}")


def _is_excel_error(value: object) -> bool:
    """Whether a value the workbook saved is one of Excel's errors, such as #DIV/0!."""
    return isinstance(value, str) and value in EXCEL_ERRORS


def _workbook_name_of(final: str, workbook: Workbook) -> str:
    """What the workbook calls a final: `Excel Table "job_runs"`, `the Total Row of Excel
    Table "job_runs"`, `PivotTable "PivotTable1"`, or a total level of one, as `PivotTable
    "PivotTable1" (grand total)`."""
    tables = tables_of(workbook)
    if final.endswith(TOTAL_ROW) and final.removesuffix(TOTAL_ROW).lower() in tables:
        return f'the Total Row of Excel Table "{final.removesuffix(TOTAL_ROW)}"'
    if final.lower() in tables:
        return f'Excel Table "{final}"'
    for piece in pivot_pieces(workbook):
        if final == piece.name or final.startswith(f"{piece.name} ("):
            return f'PivotTable "{piece.name}"{final.removeprefix(piece.name)}'
    return f'"{final}"'


# --- Matching and saying values --------------------------------------------------------------


def is_same(excel: object, hive: object, blank_marked: bool) -> bool:
    """Whether the value Hive gives is the one Excel stored, as the module docstring says:
    `blank_marked` where M1 marks the column, so Excel's 0 or "" matches Hive's NULL."""
    excel, hive = _as_compared(excel), _as_compared(hive)
    if excel is None and hive is None:
        return True
    if excel is None or hive is None:
        given = hive if excel is None else excel
        return blank_marked and given in (0, "") and not isinstance(given, bool)
    numbers = (int, float)
    if isinstance(excel, numbers) and isinstance(hive, numbers):
        return math.isclose(excel, hive, rel_tol=RELATIVE, abs_tol=NEAR_ZERO)
    return str(excel) == str(hive)


def _as_compared(value: object) -> object:
    """A value as the check compares it: a day as its text, an Excel error as NULL."""
    if _is_excel_error(value):
        return None
    if isinstance(value, datetime.datetime):
        return _hive_value(value)
    if isinstance(value, datetime.date):
        return value.isoformat()
    return value


def _shown(value: object, blank: str = "blank") -> str:
    """A value as a difference's line shows it: a number with its thousands marked, a day as
    its date, a blank as `blank`."""
    if not isinstance(value, str):  # an Excel error, such as #DIV/0!, is shown as it is
        value = _as_compared(value)
    if value is None:
        return blank
    if isinstance(value, bool):
        return str(value).upper()
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e15:
        return f"{int(value):,}"
    if isinstance(value, float):
        return format(value, ",.15g")
    return str(value)


def _said_values(excel: object, hive: object) -> str:
    """"Excel 1,204, Hive 1,198": the value the workbook shows and the one Hive gives."""
    return f"Excel {_shown(excel)}, Hive {_shown(hive, 'NULL')}"


def _said_key(row: dict[str, object], key: list[str]) -> str:
    """A Table's row, by its key's columns and values: "job_id 1, dt 2026-09-24"."""
    return ", ".join(f"{column} {_shown(row[column])}" for column in key)


def _said_row(row: dict[str, object], fields: list[str]) -> str:
    """A final's row, by the fields it groups by, or "Grand Total" for none."""
    if not fields:
        return "Grand Total"
    return ", ".join(f"{name} {_shown(row.get(name))}" for name in fields)


def _said_cell(pivot: PivotTable, cell: PivotCell) -> str:
    """A pivot's cell by its items, "region East, dt Mar", or "Grand Total" for none; its
    value's caption after them where the pivot shows more than one value."""
    said = [f"{field_name} {_shown(item)}" for field_name, item in _items_of(cell)]
    if not said:
        said = ["Grand Total"]
    if len(pivot.values) > 1:
        said.append(cell.value)
    return ", ".join(said)


# --- The report ------------------------------------------------------------------------------


def _named(checked: CheckedFinal) -> str:
    """A final as the report names it: its table and what the workbook calls it, or Copilot's
    script."""
    if checked.final.script:
        return f"{checked.final.script}, Copilot's Hive of {checked.place}"
    return f"{checked.final.table}, from {checked.place}"


def _final_lines(checked: CheckedFinal) -> list[str]:
    """What the report says of one final: a line, then each difference and each cell where the
    workbook shows an Excel error indented below it, a line said more than once said once; and
    the lines of its Pivot filters' answers (_pivot_filter_lines)."""
    named = _named(checked)
    if checked.not_checked:
        return [f"{named}: not checked: {checked.not_checked}. {BY_HAND}",
                *_pivot_filter_lines(checked)]
    if not (checked.differences or checked.errors):
        compared = counted(checked.compared, "cell")
        lines = [f"{named}: every cell matches the workbook, {compared} compared."]
    else:
        matching = checked.compared - checked.differing - len(checked.errors)
        listed = [counted(len(checked.differences), "difference")]
        if checked.errors:
            listed.append(f"{counted(len(checked.errors), 'cell')} where the workbook shows an "
                          "Excel error and the Hive gives NULL, neither a match nor a "
                          "difference")
        lines = [f"{named}: {matching} of {counted(checked.compared, 'cell')} match the "
                 f"workbook; below, {in_words(listed)}:"]
        times = Counter(checked.differences)
        lines += [f"  {line}" if times[line] == 1 else f"  {line} ({times[line]} times)"
                  for line in dict.fromkeys(checked.differences)]
        lines += [f"  {line}" for line in checked.errors]
    if checked.unstored:
        lines.append(f"{named}: not compared: {in_words(checked.unstored)}, as the file holds "
                     "no value saved for them: a file saved by a tool, not by Excel, holds "
                     "none. Open it in Excel, save it, and convert again to compare them.")
    return lines + _pivot_filter_lines(checked)


def _pivot_filter_lines(checked: CheckedFinal) -> list[str]:
    """What the report says of a final whose table's Pivot filters were answered other than
    "keep": that it was checked as converted, where it was, and why each table per value made
    beside it is not checked."""
    table = checked.final.table
    lines = []
    if checked.final.as_converted and not checked.not_checked:
        lines.append(f"{table}: checked as converted, {checked.final.as_converted}.")
    beside = list(checked.final.beside)
    if beside:
        each = singular_or_plural(len(beside), "it is", "each is")
        lines.append(f"{in_words(beside)}: not checked: {each} a table per value, made beside "
                     f"{table} by its Pivot filter's answer \"tables\", and the workbook holds "
                     "no PivotTable of one value's rows alone to compare it with.")
    return lines


def report_lines(check: WorkbookCheck) -> list[str]:
    """What convert's report says of a workbook's check: what it is, then each final."""
    lines = [f"The Workbook check of {check.file} {ABOUT}"]
    for checked in check.finals:
        lines += _final_lines(checked)
    if any(checked.differences for checked in check.finals):
        lines.append(NEXT)
    return lines


def batch_md_lines(check: WorkbookCheck) -> list[str]:
    """batch.md's section for a workbook's check: its heading, what it is, and each final, as
    a list, each difference an item under its final's."""
    lines = ["", f"## The Workbook check of {check.file}", "", f"It {ABOUT}", ""]
    for checked in check.finals:
        for line in _final_lines(checked):
            if line.startswith("  "):
                lines.append(f"  - {line.strip()}")
            else:
                lines.append(f"- {line}")
    if any(checked.differences for checked in check.finals):
        lines += ["", NEXT]
    return lines
