"""A Formula workbook's PivotTables written as Hive, by the Toolbox (Toolbox 8.9, ticket 06; ADR
0016).

Each pivot the workbook reader reads (`workbook_reader.PivotTable`) is one query, written as
sqlglot's tree by the rules below, each with its ID, which Copilot file 20 gives the same Hive
by: its Row and Column fields the GROUP BY, a Column field written as rows, never a column per
item, so a new item flows in; each value its aggregate, Show Values As a window over it; each
calculated item a column beside the real rows; each Pivot filter the condition it is, its
values written in. Each total level the pivot shows is a final of its own, `<pivot> (grand
total)` or `<pivot> (by <fields>)`, never a Subtotal row in the pivot's own final. A Table's
GETPIVOTDATA reads the pivot as a CTE, by a LEFT JOIN on the fields it names.

What is refused is named, as file 11's are: a value with no Hive is `NULL AS` its column, and a
pivot whose rows can't be written (its source, a grouping, a filter or "Show items with no
data") has no final.

The rules, by their IDs:

- PR1 Row and Column fields: the GROUP BY, each field a column, Row fields first, then each
  value, its column its caption in snake case, `sum_of_duration_mins`.
- PR2 a Column field: written as rows, one per item, marked "Column field <name>: written as
  rows".
- PR3 a date grouping: Years `YEAR(d)`, Quarters `CONCAT('Qtr', QUARTER(d))`, Months
  `DATE_FORMAT(d, 'MMM')`, Days `DATE_FORMAT(d, 'd-MMM')`, in the GROUP BY.
- PR4 a number grouping: a CASE giving each bin's label, `'<0'`, `'0-9'` .. `'>49'`.
- PR5 items grouped by hand: a CASE giving each group's name, any other item as it is.
- PV1 a summary: Sum SUM, Count and Count Numbers COUNT, Average AVG, Max MAX, Min MIN, StdDev
  STDDEV_SAMP, StdDevp STDDEV_POP, Var and Varp `POWER(STDDEV_SAMP(x), 2)` and
  `POWER(STDDEV_POP(x), 2)`.
- PV2 Distinct Count: `COUNT(DISTINCT x)`.
- PV3 a calculated field: its formula over the Sum of each field it names.
- PV4 % of Grand, Row or Column Total: `v / SUM(v) OVER (...)`, over the level's Row fields
  or Column fields.
- PV5 Running Total In: `SUM(v) OVER (PARTITION BY <other fields> ORDER BY <base field> ROWS
  BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`.
- PV6 Difference From, % Of and % Difference From a base item: `v` and the base item's own
  value, `MAX(CASE WHEN <base> = <item> THEN v END) OVER (PARTITION BY <other fields>)`, NULL
  on the base item's row where Excel leaves it blank.
- PV7 Rank: `RANK() OVER (PARTITION BY <other fields> ORDER BY v DESC)`, ASC for Smallest to
  Largest.
- PV8 at a total level that doesn't group by the base field of a Running Total In (PV5), a
  Difference From, % Of or % Difference From (PV6) or a Rank (PV7): the value is NULL, as Excel
  shows it blank, marked. It never applies to the pivot's own final, which groups by every
  field, nor to % of a total (PV4), which has no base field.
- PC1 a calculated item of items added up: a column beside the real rows, `SUM(SUM(CASE WHEN f
  IN (a, b) THEN v END)) OVER (PARTITION BY <the row's other fields>)`, repeated on each of
  their rows.
- PC2 any other calculated item, such as a ratio: its formula over each item's own conditional
  sum, so a ratio of sums, never a sum of ratios.
- PC3 at a total level that doesn't group by a calculated item's field, such as the grand
  total: the item's value added into each value's total, `SUM(x) + COALESCE(<the item>, 0)`, as
  Excel adds it, marked. At a level that groups by the field, the item is its column (PC1,
  PC2) and adds nothing.
- PL1 each total level the pivot shows: a final of its own, `<pivot> (grand total)` or
  `<pivot> (by <fields>)`; never a Subtotal row.
- PL2 a pivot showing no total: its own final alone; a field's subtotals of functions it chose
  are refused and named.
- PF1 a Report filter: `f = x` or `f IN (...)`; (All) is no condition.
- PF2 items hidden on a Row or Column field: `f <> x` or `NOT f IN (...)`, a blank kept with
  `f IS NULL OR`.
- PF3 a slicer's selection: `f IN (...)`, on each pivot it is connected to.
- PF4 a Timeline's dates: `d BETWEEN 'start' AND 'end'`.
- PF5 a Top or Bottom value filter of a number of items: `f IN` a subquery, the items a RANK
  window over the field's grouped rows keeps, `f IN (SELECT f FROM (SELECT f, RANK() OVER (ORDER
  BY SUM(x) DESC) AS item_rank FROM .. GROUP BY f) AS ranked WHERE item_rank <= 2)`.
  Each Pivot filter is marked "Pivot filter: <kind> <field>", for its Decision (ticket 08).
- PG1 GETPIVOTDATA: a LEFT JOIN of the pivot, a CTE, on the fields it names; NULL where Excel
  shows #REF!, marked.
- PG2 GETPIVOTDATA naming fewer fields: the total level it reads, as its own query; a total
  the pivot doesn't show refused.
- PS1 a Table: FROM what the Table is read as, `<database>.<table>` or a step's CTE.
- PS2 a query's Table: FROM the Table the query loads, as PS1.
- PS3 a plain range: the Table it would be, `<database>.<sheet>` for the person to fill in.
- PS4 a Data Model pivot of one model table: FROM the Table or query feeding it.
- PN1 a pivot's name: its own, in snake case.
- PN2 Excel's default name, PivotTable1: `<sheet name>_pivot`, proposed for a Decision.
- PX1 a DAX measure: refused, NULL in its place.
- PX2 an OLAP cube or any other outside source: refused, no final.
- PX3 "Show items with no data" on a Row or Column field: refused, no final.
- PX4 a value with no Hive here: a Product, Show Values As Index, % of a Parent Total or %
  Running Total In, a base field that isn't a Row or Column field, the (previous) or (next)
  base item: NULL in its place, named.
- PX5 a filter the code doesn't write: a label or date filter, a value filter of a percent or a
  sum, or on a field inside another: refused, no final.
- PX6 a grouping the code doesn't write: by seconds, minutes, hours, or days of more than one,
  or bins not labelled as Excel labels them: refused, no final.
- PX7 a calculated formula of more than names, numbers and + - * / ^, or naming what it can't
  read: a calculated field's value or a calculated item's column NULL in its place, named; a
  calculated item beside a value that isn't a plain Sum: refused, no final.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass

from sqlglot import exp

from .shared import in_words
from .workbook_formula_reader import (
    Call,
    Constant,
    FormulaPart,
    Name,
    Negative,
    Operation,
    Refused,
    parts_of,
    read_formula,
)
from .workbook_formulas import (
    ARITHMETIC,
    MARK,
    REFUSED,
    Book,
    Note,
    PivotJoin,
    Place,
    all_of,
    binary,
    column_hive,
    constant_hive,
    free_alias,
    hive_call,
    hive_of,
    identifier,
    is_formula_text,
    operand_hive,
    rule_hive,
    snake_case,
    tables_of,
    window_order,
)
from .workbook_reader import (
    AUTOMATIC,
    CONSOLIDATION,
    DATA_CONNECTION,
    DATA_MODEL,
    DAX_MEASURE,
    EXCEL_TABLE,
    OLAP,
    OTHER_WORKBOOK,
    PIVOT_TABLE,
    RANGE,
    VALUE_FILTER,
    VALUES,
    Grouping,
    Piece,
    PivotTable,
    PivotValue,
    Slicer,
    Timeline,
    Workbook,
    piece_name,
)

# The final of a pivot's grand total, after the pivot's name (PL1).
GRAND_TOTAL_FINAL = " (grand total)"
# Excel's default name for a pivot (PN2).
DEFAULT_NAME = re.compile(r"PivotTable\d*")
# Each summary, by Excel's word, as the Hive aggregate it is (PV1); Var and Varp are a
# STDDEV squared, since sqlglot writes VAR_SAMP as VARIANCE, the population's in Hive.
AGGREGATES = {"Sum": "SUM", "Count": "COUNT", "Count Numbers": "COUNT", "Average": "AVG",
              "Max": "MAX", "Min": "MIN", "StdDev": "STDDEV_SAMP", "StdDevp": "STDDEV_POP"}
SQUARED = {"Var": "STDDEV_SAMP", "Varp": "STDDEV_POP"}
DISTINCT_COUNT = "Distinct Count"
# Each Show Values As the code writes, in Excel's words (PV4 to PV7).
PERCENT_OF_TOTALS = ("% of Grand Total", "% of Row Total", "% of Column Total")
RUNNING_TOTAL = "Running Total In"
FROM_BASE_ITEM = ("Difference From", "% Of", "% Difference From")
RANKS = {"Rank Largest to Smallest": True, "Rank Smallest to Largest": False}
# Each date level a grouping writes, as Hive giving Excel's label for it (PR3).
DATE_GROUPS = {"Years": "YEAR(p0)", "Quarters": "CONCAT('Qtr', QUARTER(p0))",
               "Months": "DATE_FORMAT(p0, 'MMM')", "Days": "DATE_FORMAT(p0, 'd-MMM')"}
# The kinds of Pivot filter, in CONTEXT.md's words (PF1 to PF5), each by its rule.
REPORT_FILTER = "Report filter"
HIDDEN_ITEMS = "hidden items"
SLICER = "slicer"
TIMELINE = "Timeline"
TOP_FILTER = "value filter"
FILTER_RULES = {REPORT_FILTER: "PF1", HIDDEN_ITEMS: "PF2", SLICER: "PF3", TIMELINE: "PF4",
                TOP_FILTER: "PF5"}
# Each source a pivot may read from outside the workbook's Tables, in words (PX2).
OUTSIDE_SOURCES = {OLAP: "an OLAP cube", DATA_CONNECTION: "a data connection",
                   OTHER_WORKBOOK: "another workbook",
                   CONSOLIDATION: "multiple consolidation ranges"}
# The column a value filter's subquery ranks each item in (PF5).
ITEM_RANK = "item_rank"
# The notes a total level's final has of its own, beside its pivot's (PV8, PC3).
LEVEL_RULES = ("PV8", "PC3")
# A name in a calculated formula written in quotes, such as 'Unit Price'.
QUOTED_NAME = re.compile(r"'((?:[^']|'')+)'")


@dataclass(frozen=True)
class PivotLevel:
    """One total level of a pivot: the Row fields and the Column fields it groups by,
    outermost first. The pivot's own level groups by all of them; its grand total by none."""

    rows: tuple[str, ...]
    columns: tuple[str, ...]


@dataclass(frozen=True)
class ConvertedPivotFilter:
    """One Pivot filter as the conversion writes it, for its Decision (ticket 08): the `final`
    of the pivot it is in, by its name in the workbook; its `kind`, REPORT_FILTER,
    HIDDEN_ITEMS, SLICER, TIMELINE or TOP_FILTER; its field; its `values`, the items kept (a
    Report filter's or a slicer's), the items dropped (hidden), the first and last day (a
    Timeline's), or how many items are kept (a value filter's); `field_values`, every value
    the field takes, for how many tables a table per value would make (`field_values`); and,
    for a value filter, the value it is `ranked_by` and whether it keeps the `bottom` ones.

    A Conversion keeps each for the table it ends up in, `final` then that table's name in
    dev (`pivot_filters.py`). Read from a script's Hive, Copilot's, `field_values` is the
    workbook's when the batch holds the workbook too, and else empty: Hive holds no pivot
    cache, so ticket 08's Decision counts no tables for it then."""

    final: str
    kind: str
    field: str
    values: tuple[object, ...]
    field_values: tuple[object, ...]
    ranked_by: str = ""
    bottom: bool = False


# --- Each pivot, by its piece --------------------------------------------------------------


def pivot_of(piece: Piece, workbook: Workbook) -> PivotTable:
    """The pivot a piece of the Order is: by its name, or by its sheet and name where another
    pivot has the name too."""
    for pivot in workbook.pivot_tables:
        if piece.name in (pivot.name, f"{pivot.sheet}!{pivot.name}"):
            return pivot
    raise KeyError(piece.name)


def pivot_pieces(workbook: Workbook) -> list[Piece]:
    """Each pivot's piece, in the Order."""
    return [piece for piece in workbook.order if piece.kind == PIVOT_TABLE]


def pivot_table_names(workbook: Workbook) -> dict[str, str]:
    """The table each pivot's final writes, by the final's name: its own name in snake case
    (PN1), or for Excel's default name `<sheet name>_pivot` (PN2), the sheet's name alone
    where it is or ends with "pivot" already, as `pivot` for a sheet named Pivot, with a
    number after it where two pivots would share one."""
    names: dict[str, str] = {}
    for piece in pivot_pieces(workbook):
        pivot = pivot_of(piece, workbook)
        name = snake_case(pivot.name)
        if DEFAULT_NAME.fullmatch(pivot.name):
            name = snake_case(pivot.sheet)
            if name != "pivot" and not name.endswith("_pivot"):
                name += "_pivot"
        taken = set(names.values())
        number = 2
        proposed = name
        while proposed in taken:
            proposed = f"{name}_{number}"
            number += 1
        names[piece.name] = proposed
    return names


def axis_fields(fields: list[str]) -> tuple[str, ...]:
    """A pivot's Row or Column fields, without the field Excel names for its values."""
    return tuple(name for name in fields if name != VALUES)


def own_level(pivot: PivotTable) -> PivotLevel:
    """The level of the pivot's own final: every Row field and every Column field."""
    return PivotLevel(axis_fields(pivot.rows), axis_fields(pivot.columns))


def levels_shown(pivot: PivotTable) -> list[PivotLevel]:
    """Each total level the pivot shows, but its own (PL1): its Grand Total row, which groups
    by the Column fields alone; its Grand Total column, by the Row fields alone; each outer
    field's subtotals, by it and the fields outside it; and where they meet."""
    rows, columns = axis_fields(pivot.rows), axis_fields(pivot.columns)
    row_depths = [len(rows), *_subtotal_depths(pivot, rows)]
    column_depths = [len(columns), *_subtotal_depths(pivot, columns)]
    if pivot.grand_total_row:
        row_depths.append(0)
    if pivot.grand_total_column:
        column_depths.append(0)
    levels = []
    for row_depth in row_depths:
        levels += [PivotLevel(rows[:row_depth], columns[:depth]) for depth in column_depths]
    return [level for level in dict.fromkeys(levels) if level != own_level(pivot)]


def _subtotal_depths(pivot: PivotTable, fields: tuple[str, ...]) -> list[int]:
    """How many fields each subtotal of an outer field groups by, of Excel's own subtotals
    alone."""
    return [number + 1 for number, name in enumerate(fields[:-1])
            if name in pivot.subtotals and pivot.fields[name].subtotals == [AUTOMATIC]]


def level_final_name(name: str, level: PivotLevel) -> str:
    """A total level's final: `<pivot> (grand total)`, or `<pivot> (by <fields>)` (PL1)."""
    fields = [*level.rows, *level.columns]
    if not fields:
        return name + GRAND_TOTAL_FINAL
    return f"{name} (by {in_words(fields)})"


def value_column_name(value: PivotValue) -> str:
    """A value's column: its caption in snake case, `sum_of_duration_mins` (PR1)."""
    return snake_case(value.caption)


# --- A pivot's final and its total levels' -------------------------------------------------


def is_read(piece: Piece, workbook: Workbook) -> bool:
    """Whether another piece reads this one, as a Table's GETPIVOTDATA reads its pivot."""
    return any(piece in reads for reads in workbook.order.values())


def write_pivot_query(piece: Piece, book: Book) -> exp.Select | None:
    """Write a pivot's own query, every Row and Column field its GROUP BY, and give it back;
    add what its map names to the Book's notes. None, refused and named, where its rows can't
    be written. A pivot a GETPIVOTDATA reads, a step, carries only the values one reads."""
    pivot = pivot_of(piece, book.workbook)
    try:
        source_read = _source_read(pivot, book)
        check_pivot_rows(pivot)
    except Refused as refusal:
        book.notes.append(Note(REFUSED, refusal.rule, piece_name(piece),
                               f"no final: {refusal.why}"))
        return None
    book.notes += pivot_notes(piece.name, pivot, book.workbook)
    step_values = None
    if is_read(piece, book.workbook):
        step_values = values_read_by_getpivotdata(piece, pivot, book.workbook)
    select, notes = level_select(pivot, own_level(pivot), source_read, piece.name,
                                 step_values)
    book.notes += notes
    return select


def write_pivot_total_finals(workbook: Workbook, finals: dict[str, exp.Query],
                             book: Book) -> dict[str, exp.Query]:
    """Write each total level's final of each pivot that is a final, and give them back by
    their names (PL1), each with the CTEs of its pivot's final it reads; add the notes each
    level has of its own (PV8, PC3) to the Book's."""
    found: dict[str, exp.Query] = {}
    for piece in pivot_pieces(workbook):
        own = finals.get(piece.name)
        if own is None or is_read(piece, workbook):
            continue
        pivot = pivot_of(piece, workbook)
        source_read = _source_read(pivot, book)
        for level in levels_shown(pivot):
            name = level_final_name(piece.name, level)
            select, notes = level_select(pivot, level, source_read, name)
            book.notes += [note for note in notes if note.rule in LEVEL_RULES]
            for cte in ctes_read(select, own.ctes):
                select = select.with_(cte.alias, as_=cte.this.copy())
            found[name] = select
    return found


def ctes_read(select: exp.Select, ctes: list[exp.CTE]) -> list[exp.CTE]:
    """The CTEs of `ctes`, in their order, that `select` reads, or a CTE it reads reads, at any
    depth: a total level's final carries only these of its pivot's final."""
    read = {table.name for table in select.find_all(exp.Table)}
    kept = []
    for cte in reversed(ctes):
        if cte.alias in read:
            kept.insert(0, cte)
            read |= {table.name for table in cte.this.find_all(exp.Table)}
    return kept


def values_read_by_getpivotdata(piece: Piece, pivot: PivotTable,
                                workbook: Workbook) -> list[PivotValue]:
    """The pivot's values a GETPIVOTDATA reads, in each Table that reads the pivot, so its CTE
    carries no other; every value where none names one of them."""
    tables = tables_of(workbook)
    named: list[str] = []
    for reader, read in workbook.order.items():
        if reader.kind != EXCEL_TABLE or piece not in read:
            continue
        for column in tables[reader.name.lower()].columns:
            named += _getpivotdata_values(column.cells)
    values = []
    for value in pivot.values:
        if any(is_value_named(value, name) for name in named):
            values.append(value)
    return values or list(pivot.values)


def _getpivotdata_values(cells: list[object]) -> list[str]:
    """The value each GETPIVOTDATA in a column's formulas names, its first argument."""
    found = []
    for cell in dict.fromkeys(cells):
        if not is_formula_text(cell) or "GETPIVOTDATA" not in str(cell).upper():
            continue
        try:
            parts = parts_of(read_formula(str(cell)))
            calls = [part for part in parts if isinstance(part, Call)]
        except Refused:
            continue
        for call in calls:
            if call.name == "GETPIVOTDATA" and call.args and isinstance(call.args[0], Constant):
                found.append(str(call.args[0].value))
    return found


def level_select(pivot: PivotTable, level: PivotLevel, source_read: exp.Expression,
                 final_name: str, step_values: list[PivotValue] | None = None
                 ) -> tuple[exp.Select, list[Note]]:
    """One level's SELECT: each field it groups by (PR1), each value (PV1 to PV8), each
    calculated item of a field it groups by (PC1, PC2), from `source_read`, with every Pivot
    filter's condition (PF1 to PF5); and what its map names, each note on `final_name`.
    A step's own level, which GETPIVOTDATA reads, writes only `step_values`, the values
    a GETPIVOTDATA reads, and no calculated item, so its CTE carries no column nothing
    reads."""
    keys = {name: field_key(pivot, name) for name in (*level.rows, *level.columns)}
    notes: list[Note] = []
    columns = [_key_column(name, key) for name, key in keys.items()]
    for value in pivot.values if step_values is None else step_values:
        columns.append(_value_column(pivot, value, level, keys, final_name, notes))
    if step_values is None:
        columns += _calculated_item_columns(pivot, keys, final_name, notes)
    if not keys and not any(column.find(exp.AggFunc) for column in columns):
        # A grand total of values all NULL (PV8) is the one blank cell Excel shows: one row,
        # read from nothing, as a FROM with no aggregate would give a row per source row.
        return exp.select(*columns), notes
    select = exp.select(*columns).from_(source_read.copy())
    conditions = filter_conditions(pivot, source_read)
    if conditions:
        select = select.where(all_of(conditions))
    if keys:
        select = select.group_by(*[key.copy() for key in keys.values()])
    return select, notes


def _key_column(name: str, key: exp.Expression) -> exp.Expression:
    if isinstance(key, exp.Column) and key.name == identifier(name).name:
        return key.copy()
    return exp.alias_(key.copy(), identifier(name))


def _source_read(pivot: PivotTable, book: Book) -> exp.Expression:
    """What a pivot's query reads, as its FROM writes it: its Table's or its range's read
    (PS1 to PS3), or the Table or query feeding its one Data Model table (PS4); refused for
    any other source (PX2)."""
    source = pivot.source
    if source.kind not in (EXCEL_TABLE, RANGE, DATA_MODEL):
        raise Refused("PX2", f"its source is {OUTSIDE_SOURCES.get(source.kind, source.kind)}, "
                             "which the code doesn't read")
    if source.kind == DATA_MODEL and (len(source.model_tables) != 1 or len(source.pieces) != 1):
        raise Refused("PS4", "it reads several Data Model tables, whose relationships the "
                             "code doesn't read")
    if not source.pieces or source.pieces[0] not in book.reads:
        raise Refused("PS1", f"its source, {source.name}, has no Hive")
    source_read = book.reads[source.pieces[0]]
    if isinstance(source_read, exp.Table):
        return source_read.copy()
    return exp.Subquery(this=source_read.copy(),
                        alias=exp.TableAlias(this=exp.Identifier(this="s")))


def add_range_read(piece: Piece, book: Book) -> None:
    """Add to the Book how a plain range a pivot reads is read, as the Table it would be
    (PS3): its defined name's, or its sheet's, in snake case, `<database>.runs`, the name of
    the database table it samples proposed, a Decision of the table reading it; and name it in
    the map."""
    name = range_table_name(piece, book.workbook)
    book.reads[piece] = exp.Table(this=exp.Identifier(this=name, quoted=False),
                                  db=exp.Identifier(this=book.database, quoted=False))
    book.notes.append(Note(MARK, "PS3", piece_name(piece),
                           f"read as the Table it would be, {name}: the database table it "
                           "samples is proposed as that, a Decision of its table"))


def range_table_name(piece: Piece, workbook: Workbook) -> str:
    """The database table a plain range a pivot reads is proposed to sample: its defined
    name's, or its sheet's, in snake case (PS3)."""
    range_name = piece.name
    for pivot in workbook.pivot_tables:
        if pivot.source.pieces == [piece] and pivot.source.table is not None:
            range_name = pivot.source.table.name
    return snake_case(range_name.split("!")[0].strip("'"))


def check_pivot_rows(pivot: PivotTable) -> None:
    """Refuse a pivot whose rows the code can't write: a Row or Column field showing items
    with no data (PX3), a filter (PX5), a grouping (PX6) or a calculated item (PX7) it
    doesn't write."""
    for name in (*own_level(pivot).rows, *own_level(pivot).columns):
        if pivot.fields[name].shows_items_with_no_data:
            raise Refused("PX3", f"{name} shows items with no data, which have no rows")
        field_key(pivot, name)
    for pivot_filter in pivot.filters:
        if pivot_filter.kind != VALUE_FILTER or pivot_filter.test not in ("Top", "Bottom"):
            raise Refused("PX5", f"its {pivot_filter.kind} on {pivot_filter.field}, "
                                 f"{pivot_filter.test}, isn't converted by the code")
        if pivot_filter.unit != "Items":
            raise Refused("PX5", f"its value filter on {pivot_filter.field} keeps a "
                                 f"{pivot_filter.unit}, not a number of items, which the code "
                                 "doesn't convert")
        outer = (*own_level(pivot).rows[:1], *own_level(pivot).columns[:1])
        if pivot_filter.field not in outer:
            raise Refused("PX5", f"its value filter is on {pivot_filter.field}, inside another "
                                 "field, which the code doesn't convert")
    has_items = any(pivot_field.calculated_items for pivot_field in pivot.fields.values())
    if has_items and not all(_is_plain_sum(pivot, value) for value in pivot.values):
        raise Refused("PX7", "a calculated item beside a value that isn't a plain Sum")


def _is_plain_sum(pivot: PivotTable, value: PivotValue) -> bool:
    """Whether a value is a field's Sum, shown as itself: what a calculated item adds up."""
    pivot_field = pivot.fields.get(value.field)
    is_calculated = pivot_field is not None and bool(pivot_field.formula)
    return value.summary == "Sum" and not value.shown_as and not is_calculated


# --- What a pivot's map names --------------------------------------------------------------


def pivot_notes(name: str, pivot: PivotTable, workbook: Workbook) -> list[Note]:
    """What the map names of a pivot as a whole: the name of its table proposed, where it is
    a final (PN2), each Column field written as rows (PR2), each Pivot filter (PF1 to PF5),
    and each field's subtotals of functions it chose, refused (PL2)."""
    notes = []
    if DEFAULT_NAME.fullmatch(pivot.name) and not is_read(Piece(PIVOT_TABLE, name), workbook):
        proposed = pivot_table_names(workbook)[name]
        notes.append(Note(MARK, "PN2", name, f"Excel's default name: its table is proposed as "
                                             f"{proposed}, for you to decide"))
    notes += [Note(MARK, "PR2", name, f"Column field {column}: written as rows")
              for column in own_level(pivot).columns]
    for written in pivot_filters_of(name, pivot):
        notes.append(Note(MARK, FILTER_RULES[written.kind], name,
                          f"{pivot_filter_text(written)}: a Decision of its table"))
    for field_name in pivot.subtotals:
        if pivot.fields[field_name].subtotals != [AUTOMATIC]:
            chosen = in_words(pivot.fields[field_name].subtotals)
            notes.append(Note(REFUSED, "PL2", name, f"the subtotals of {field_name} are "
                                                    f"{chosen}: no final"))
    return notes


def pivot_filter_text(written: ConvertedPivotFilter) -> str:
    """A Pivot filter in words, as the map and a checklist say it: "Pivot filter: slicer
    status, FAILED and SUCCESS kept"; its kind and field alone where its values weren't
    read, as from Hive whose marked condition is written otherwise."""
    said = f"Pivot filter: {written.kind} {written.field}"
    if not written.values:
        return said
    return f"{said}, {_filter_values_text(written)}"


def _filter_values_text(written: ConvertedPivotFilter) -> str:
    """What a Pivot filter keeps or leaves out, in words."""
    shown = [str(value) for value in written.values]
    if written.kind == HIDDEN_ITEMS:
        return f"{in_words(shown)} left out"
    if written.kind == TIMELINE:
        return f"{shown[0][:10]} to {shown[1][:10]}"
    if written.kind == TOP_FILTER:
        return f"{'Bottom' if written.bottom else 'Top'} {shown[0]} by {written.ranked_by}"
    return f"{in_words(shown)} kept"


# --- Each field, value and calculated item --------------------------------------------------


def field_key(pivot: PivotTable, name: str) -> exp.Expression:
    """A Row or Column field as the GROUP BY reads it: its column (PR1), or its grouping's
    expression, a date level (PR3), a number's bin (PR4) or a group made by hand (PR5)."""
    pivot_field = pivot.fields.get(name)
    if pivot_field is None or pivot_field.grouping is None:
        return column_hive(name)
    grouping = pivot_field.grouping
    base = column_hive(grouping.field)
    if grouping.by == "Number":
        return _bins_hive(base, grouping, pivot_field.items)
    if grouping.by == "Items":
        return _groups_hive(base, grouping)
    if grouping.by in DATE_GROUPS and (grouping.by != "Days" or grouping.interval == 1):
        return rule_hive(DATE_GROUPS[grouping.by], p0=base)
    raise Refused("PX6", f"{name} groups {grouping.field} by {grouping.by}, which the code "
                         "doesn't convert")


def _bins_hive(base: exp.Expression, grouping: Grouping,
               labels: list[object]) -> exp.Expression:
    """A number's bin, as Excel labels it: below the start, each bin `interval` wide, the
    last one up to the end, then above it (PR4)."""
    if len(labels) < 3 or not str(labels[0]).startswith("<") or grouping.start is None:
        raise Refused("PX6", f"the bins of {grouping.field} aren't labelled as Excel labels "
                             "them")
    start, interval = grouping.start, grouping.interval or 1
    branches = [(binary(exp.LT, base.copy(), constant_hive(start)), labels[0])]
    for number, label in enumerate(labels[1:-2], 1):
        bound = constant_hive(start + number * interval)
        branches.append((binary(exp.LT, base.copy(), bound), label))
    branches.append((binary(exp.LTE, base.copy(), constant_hive(grouping.end)), labels[-2]))
    ifs = [exp.If(this=condition, true=constant_hive(label)) for condition, label in branches]
    return exp.Case(ifs=ifs, default=constant_hive(labels[-1]))


def _groups_hive(base: exp.Expression, grouping: Grouping) -> exp.Expression:
    """Items grouped by hand: each group's name for its items, any other item as it is (PR5)."""
    ifs = [exp.If(this=_kept_condition(base, items), true=constant_hive(group))
           for group, items in grouping.groups.items()]
    return exp.Case(ifs=ifs, default=base.copy())


def _value_column(pivot: PivotTable, value: PivotValue, level: PivotLevel,
                  keys: dict[str, exp.Expression], final_name: str, notes: list[Note]
                  ) -> exp.Expression:
    """One value's column at a level: its aggregate, with each calculated item the level
    doesn't group by added in (PC3), as Show Values As shows it (PV4 to PV8); refused, NULL
    in its place and named."""
    try:
        aggregate = value_aggregate(pivot, value)
        aggregate = _items_added(pivot, value, level, aggregate, final_name, notes)
        shown = _shown_as_hive(pivot, value, level, keys, aggregate, final_name, notes)
    except Refused as refusal:
        notes.append(Note(REFUSED, refusal.rule, f"{final_name}[{value.caption}]",
                          f"NULL in its place: {refusal.why}"))
        shown = exp.Null()
    return exp.alias_(shown, exp.Identifier(this=value_column_name(value), quoted=False))


def value_aggregate(pivot: PivotTable, value: PivotValue) -> exp.Expression:
    """A value's aggregate over a group's rows: its summary's (PV1), COUNT(DISTINCT) (PV2), or
    a calculated field's formula over the Sums (PV3); a DAX measure refused (PX1)."""
    if value.summary == DAX_MEASURE:
        raise Refused("PX1", f"{value.caption} is a DAX measure, which has no Hive here")
    pivot_field = pivot.fields.get(value.field)
    if pivot_field is not None and pivot_field.formula:
        sums = {name.lower(): hive_call("SUM", [column_hive(name)])
                for name, each in pivot.fields.items() if not each.formula}
        return _arithmetic_hive(pivot_field.formula, sums)
    column = column_hive(value.field)
    if value.summary == DISTINCT_COUNT:
        return exp.Count(this=exp.Distinct(expressions=[column]))
    if value.summary in SQUARED:
        return hive_call("POWER", [hive_call(SQUARED[value.summary], [column]),
                                   exp.Literal.number(2)])
    if value.summary not in AGGREGATES:
        raise Refused("PX4", f"{value.summary} has no Hive aggregate here")
    return hive_call(AGGREGATES[value.summary], [column])


def _arithmetic_hive(formula: str, names: dict[str, exp.Expression]) -> exp.Expression:
    """A calculated field's or item's formula as Hive, each name in it, quoted or not, as
    `names` gives it by its name in lower case: names, numbers, + - * / ^ and brackets."""
    quoted: dict[str, str] = {}
    for number, found in enumerate(QUOTED_NAME.finditer(formula)):
        quoted[f"_quoted_{number}"] = found.group(1).replace("''", "'")
    for placeholder, found in zip(quoted, QUOTED_NAME.findall(formula), strict=True):
        formula = formula.replace(f"'{found}'", placeholder, 1)
    return _formula_part_hive(read_formula(formula), names, quoted)


def _formula_part_hive(part: FormulaPart, names: dict[str, exp.Expression],
                       quoted: dict[str, str]) -> exp.Expression:
    if isinstance(part, Name):
        name = quoted.get(part.name, part.name).lower()
        if name not in names:
            raise Refused("PX7", f"its formula names {part.name}, which isn't one it can read")
        return names[name].copy()
    is_number = isinstance(part, Constant) and isinstance(part.value, (int, float))
    if is_number and not isinstance(part.value, bool):
        return constant_hive(part.value)
    if isinstance(part, Negative):
        operand = _formula_part_hive(part.operand, names, quoted)
        return exp.Neg(this=operand_hive(operand, exp.Neg))
    if isinstance(part, Operation) and part.operator == "^":
        return hive_call("POWER", [_formula_part_hive(part.left, names, quoted),
                                   _formula_part_hive(part.right, names, quoted)])
    if isinstance(part, Operation) and part.operator in ARITHMETIC:
        return binary(ARITHMETIC[part.operator], _formula_part_hive(part.left, names, quoted),
                      _formula_part_hive(part.right, names, quoted))
    raise Refused("PX7", "a calculated formula of more than names, numbers and + - * / ^")


def _shown_as_hive(pivot: PivotTable, value: PivotValue, level: PivotLevel,
                   keys: dict[str, exp.Expression], aggregate: exp.Expression,
                   final_name: str,
                   notes: list[Note]) -> exp.Expression:
    """A value as Show Values As shows it, a window over its aggregate (PV4 to PV7); NULL at
    a level without its base field (PV8)."""
    shown = value.shown_as
    if not shown:
        return aggregate
    if shown in PERCENT_OF_TOTALS:
        over = {PERCENT_OF_TOTALS[0]: (), PERCENT_OF_TOTALS[1]: level.rows,
                PERCENT_OF_TOTALS[2]: level.columns}[shown]
        total = _windowed(hive_call("SUM", [aggregate]), [keys[name] for name in over])
        return binary(exp.Div, aggregate, total)
    if shown not in (RUNNING_TOTAL, *RANKS, *FROM_BASE_ITEM):
        raise Refused("PX4", f"Show Values As {shown} isn't converted by the code")
    base = value.base_field
    if base not in (*own_level(pivot).rows, *own_level(pivot).columns):
        raise Refused("PX4", f"its base field {base or '(none)'} isn't a Row or Column field")
    if base not in keys:
        notes.append(Note(MARK, "PV8", f"{final_name}[{value.caption}]",
                          f"{shown} {base}: blank at this total, as Excel shows it"))
        return exp.Null()
    others = [key for name, key in keys.items() if name != base]
    if shown == RUNNING_TOTAL:
        return _windowed(hive_call("SUM", [aggregate]), others,
                         _base_order(pivot, base, keys[base]), running=True)
    if shown in RANKS:
        order = window_order(aggregate.copy(), descending=RANKS[shown])
        return _windowed(hive_call("RANK", []), others, order)
    return _from_base_item(value, keys[base], aggregate, others)


def _base_order(pivot: PivotTable, base: str, key: exp.Expression) -> exp.Ordered:
    """The order a running total runs in: the base field's items, text ones A to Z whatever
    their case, a blank last, as Excel shows them, `LOWER(f) NULLS LAST`; a grouped field's by
    the smallest value of each group, as a date's or a bin's groups are in order (PV5)."""
    field = pivot.fields[base]
    grouping = field.grouping
    if grouping is not None and grouping.by != "Items":
        return window_order(hive_call("MIN", [column_hive(grouping.field)]), descending=False)
    if any(isinstance(item, str) for item in field.items):
        return exp.Ordered(this=hive_call("LOWER", [key.copy()]), nulls_first=False)
    return window_order(key.copy(), descending=False)


def _from_base_item(value: PivotValue, base: exp.Expression, aggregate: exp.Expression,
                    others: list[exp.Expression]) -> exp.Expression:
    """Difference From, % Of or % Difference From the base item's value, worked out by a
    window over the other fields' groups; NULL on the base item's own row where Excel leaves
    it blank (PV6)."""
    if value.base_item in ("(previous)", "(next)"):
        raise Refused("PX4", f"its base item {value.base_item} isn't converted by the code")
    on_base = binary(exp.EQ, base.copy(), constant_hive(value.base_item))
    base_case = exp.Case(ifs=[exp.If(this=on_base.copy(), true=aggregate.copy())])
    base_value = _windowed(hive_call("MAX", [base_case]), others)
    if value.shown_as == "% Of":
        return binary(exp.Div, aggregate, base_value)
    difference = binary(exp.Sub, aggregate, base_value)
    if value.shown_as == "% Difference From":
        difference = binary(exp.Div, difference, base_value.copy())
    return exp.Case(ifs=[exp.If(this=on_base, true=exp.Null())], default=difference)


def _windowed(function: exp.Expression, partition: list[exp.Expression],
              order: exp.Ordered | None = None, running: bool = False) -> exp.Window:
    """`function` OVER the groups of `partition`, in `order`, to this row where `running`."""
    window = exp.Window(this=function, partition_by=[part.copy() for part in partition])
    if order is not None:
        window.set("order", exp.Order(expressions=[order]))
    if running:
        window.set("spec", exp.WindowSpec(kind="ROWS", start="UNBOUNDED",
                                          start_side="PRECEDING", end="CURRENT ROW"))
    return window


def _calculated_items_of(pivot: PivotTable, name: str) -> dict[str, str]:
    pivot_field = pivot.fields.get(name)
    if pivot_field is None:
        return {}
    return pivot_field.calculated_items


def _item_sums(pivot: PivotTable, name: str, value: PivotValue,
               key: exp.Expression) -> dict[str, exp.Expression]:
    """Each real item's Sum of `value` over a group's rows, `SUM(CASE WHEN f = x THEN v
    END)`, by the item's name in lower case."""
    sums = {}
    for item in _field_items(pivot, name):
        sums[str(item).lower()] = _conditional_sum(key, [item], value)
    return sums


def _conditional_sum(key: exp.Expression, items: list[object],
                     value: PivotValue) -> exp.Expression:
    on_items = _kept_condition(key, items)
    case = exp.Case(ifs=[exp.If(this=on_items, true=column_hive(value.field))])
    return hive_call("SUM", [case])


def _added_items(formula: str) -> list[str] | None:
    """The items a calculated item adds up, such as SUCCESS and FAILED in SUCCESS+FAILED, or
    None for any other formula."""
    parts = [part.strip() for part in formula.split("+")]
    if all(re.fullmatch(r"[A-Za-z_][\w.]*|'(?:[^']|'')+'", part) for part in parts):
        return [part.strip("'").replace("''", "'") for part in parts]
    return None


def _item_hive(pivot: PivotTable, name: str, formula: str, value: PivotValue,
               key: exp.Expression) -> exp.Expression:
    """A calculated item's value over a group's rows: the Sum of the items it adds up, one
    CASE (PC1), or its formula over each item's Sum (PC2)."""
    added = _added_items(formula)
    sums = _item_sums(pivot, name, value, key)
    if added is not None and all(item.lower() in sums for item in added):
        items = [_item_named(pivot, name, item) for item in added]
        return _conditional_sum(key, items, value)
    return _arithmetic_hive(formula, sums)


def _item_named(pivot: PivotTable, name: str, item: str) -> object:
    """A field's item by its name in a formula, as the pivot holds it, such as 1 for '1'."""
    for each in _field_items(pivot, name):
        if str(each).lower() == item.lower():
            return each
    return item


def _calculated_item_columns(pivot: PivotTable, keys: dict[str, exp.Expression],
                             final_name: str, notes: list[Note]) -> list[exp.Expression]:
    """Each calculated item of a field the level groups by: a column beside the real rows,
    each Sum in it a window over the row's other fields, repeated on each of their rows (PC1,
    PC2); named for the item, and for the value too where the pivot has several. A formula
    the code can't read is NULL in its place, named (PX7)."""
    columns = []
    for name, key in keys.items():
        others = [other for each, other in keys.items() if each != name]
        for item, formula in _calculated_items_of(pivot, name).items():
            for value in pivot.values:
                column = snake_case(item)
                if len(pivot.values) > 1:
                    column += "_" + value_column_name(value)
                try:
                    item_value = _summed_over(_item_hive(pivot, name, formula, value, key),
                                              others)
                except Refused as refusal:
                    notes.append(Note(REFUSED, refusal.rule, f"{final_name}[{item}]",
                                      f"NULL in its place: {refusal.why}"))
                    item_value = exp.Null()
                named = exp.Identifier(this=column, quoted=False)
                columns.append(exp.alias_(item_value, named))
    return columns


def _summed_over(item_value: exp.Expression, others: list[exp.Expression]) -> exp.Expression:
    """A calculated item's value with each Sum in it summed again over the row's other
    fields, `SUM(SUM(..)) OVER (PARTITION BY ..)`, so a ratio is the ratio of the sums."""
    def over(node: exp.Expression) -> exp.Expression:
        if isinstance(node, exp.Sum):
            return _windowed(hive_call("SUM", [node.copy()]), others)
        return node
    return item_value.transform(over, copy=True)


def _items_added(pivot: PivotTable, value: PivotValue, level: PivotLevel,
                 aggregate: exp.Expression, final_name: str,
                 notes: list[Note]) -> exp.Expression:
    """A value at a level without a calculated item's field, with the item added in, as Excel
    adds it to the total, an item with no rows counting 0 (PC3)."""
    grouped = {*level.rows, *level.columns}
    for name, pivot_field in pivot.fields.items():
        if name in grouped:
            continue
        for item, formula in pivot_field.calculated_items.items():
            item_value = _item_hive(pivot, name, formula, value, field_key(pivot, name))
            aggregate = binary(exp.Add, aggregate,
                               hive_call("COALESCE", [item_value, exp.Literal.number(0)]))
            notes.append(Note(MARK, "PC3", f"{final_name}[{value.caption}]",
                              f"calculated item {item} on {name}: added into this total, as "
                              "Excel adds it"))
    return aggregate


# --- Pivot filters ---------------------------------------------------------------------------


def pivot_filters(workbook: Workbook) -> list[ConvertedPivotFilter]:
    """Every Pivot filter of the workbook's pivots, as the Hive writes each, for its Decision
    (ticket 08)."""
    found = []
    for piece in pivot_pieces(workbook):
        found += pivot_filters_of(piece.name, pivot_of(piece, workbook))
    return found


def pivot_filters_of(name: str, pivot: PivotTable) -> list[ConvertedPivotFilter]:
    """Each Pivot filter of one pivot, its final `name`: its Report filters of some items
    (PF1), the items hidden on a field (PF2), each slicer's selection of fewer than every
    item (PF3) and each Timeline's dates (PF4) on it, and each Top or Bottom value filter
    (PF5)."""
    found = []
    for report_filter in pivot.report_filters:
        if report_filter.selected:
            found.append(ConvertedPivotFilter(name, REPORT_FILTER, report_filter.field,
                                              tuple(report_filter.selected),
                                              field_values(pivot, report_filter.field)))
    for field_name, pivot_field in pivot.fields.items():
        if pivot_field.hidden:
            found.append(ConvertedPivotFilter(name, HIDDEN_ITEMS, field_name,
                                              tuple(pivot_field.hidden),
                                              field_values(pivot, field_name)))
    for connected in pivot.slicers:
        found += _slicer_filters(name, pivot, connected)
    for pivot_filter in pivot.filters:
        found.append(ConvertedPivotFilter(name, TOP_FILTER, pivot_filter.field,
                                          tuple(pivot_filter.values),
                                          field_values(pivot, pivot_filter.field),
                                          pivot_filter.by, pivot_filter.test == "Bottom"))
    return found


def _slicer_filters(name: str, pivot: PivotTable,
                    connected: Slicer | Timeline) -> list[ConvertedPivotFilter]:
    """A slicer's selection, or a Timeline's dates, as a Pivot filter of the pivot: none when
    it keeps every item or every date."""
    if isinstance(connected, Timeline):
        if connected.start is None:
            return []
        return [ConvertedPivotFilter(name, TIMELINE, connected.field,
                                     (connected.start, connected.end),
                                     timeline_days(pivot, connected.field))]
    values = field_values(pivot, connected.field)
    every = {str(value) for value in values}
    if not connected.selected or {str(item) for item in connected.selected} == every:
        return []
    return [ConvertedPivotFilter(name, SLICER, connected.field, tuple(connected.selected),
                                 values)]


def field_values(pivot: PivotTable, name: str) -> tuple[object, ...]:
    """Every value a field takes, for its Pivot filter's Decision to count tables by (ticket
    08): a grouped field's groups, Excel's labels for what falls before or after its range
    left out; any other field's items the pivot cache holds; or, where the cache holds none,
    as for a field on no axis, each value of its column in the source's rows. A calculated
    item is left out: it is no value of the data, and no table would hold its rows. A Data
    Model pivot's source rows aren't in the workbook, so its field values are its items
    alone."""
    pivot_field = pivot.fields.get(name)
    items = _field_items(pivot, name)
    if pivot_field is not None and pivot_field.grouping is not None:
        return tuple(item for item in items if str(item)[:1] not in ("<", ">"))
    if items:
        return items
    return tuple(dict.fromkeys(_source_column(pivot, name)))


def timeline_days(pivot: PivotTable, name: str) -> tuple[datetime.date, ...]:
    """Each day a Timeline's date field holds in the source's rows, in order: what a Timeline
    can select, one table a day."""
    days = [_day_of(value) for value in _source_column(pivot, name) if value is not None]
    return tuple(sorted(dict.fromkeys(days)))


def _day_of(value: object) -> datetime.date:
    if isinstance(value, datetime.datetime):
        return value.date()
    return datetime.date.fromisoformat(str(value)[:10])


def _source_column(pivot: PivotTable, name: str) -> list[object]:
    """Each row's value of a field's column in the pivot's source, a Table or a range; none for
    a source the workbook doesn't hold the rows of."""
    if pivot.source.table is None:
        return []
    for column in pivot.source.table.columns:
        if column.header.lower() == name.lower():
            return list(column.cells)
    return []


def _field_items(pivot: PivotTable, name: str) -> tuple[object, ...]:
    """Every real item the pivot cache holds of a field, its calculated items left out."""
    pivot_field = pivot.fields.get(name)
    if pivot_field is None:
        return ()
    calculated = set(pivot_field.calculated_items)
    return tuple(item for item in pivot_field.items if item not in calculated)


def filter_conditions(pivot: PivotTable,
                      source_read: exp.Expression) -> list[exp.Expression]:
    """Each Pivot filter's condition, in the WHERE of the pivot's read of its source, before
    it groups: a value filter's last, reading the rows the others keep. Each carries the mark
    Copilot file 20 writes above it, `-- Pivot filter: <kind> <field>`, as a comment sqlglot
    keeps on it, so the code path's Hive names each Pivot filter as the Copilot path's does
    (ticket 10's tasks score it); a value filter's subquery reads the others unmarked."""
    written = pivot_filters_of("", pivot)
    others = [each for each in written if each.kind != TOP_FILTER]
    tops = [each for each in written if each.kind == TOP_FILTER]
    plain = [_filter_condition(pivot, each) for each in others]
    conditions = plain + [_top_condition(pivot, each, source_read, plain) for each in tops]
    marked = []
    for each, condition in zip([*others, *tops], conditions, strict=True):
        condition = condition.copy()
        if isinstance(condition, exp.Binary):
            # In brackets, so sqlglot writes the mark after the whole condition, never
            # between `=` and its right side.
            condition = exp.Paren(this=condition)
        condition.add_comments([f"Pivot filter: {each.kind} {each.field}"])
        marked.append(condition)
    return marked


def _filter_condition(pivot: PivotTable, written: ConvertedPivotFilter) -> exp.Expression:
    """A Report filter's, a slicer's (PF1, PF3), the hidden items' (PF2) or a Timeline's
    (PF4) condition, its values written in."""
    if written.kind == TIMELINE:
        start, end = written.values
        return exp.Between(this=column_hive(written.field), low=constant_hive(start),
                           high=constant_hive(end))
    key = field_key(pivot, written.field)
    if written.kind == HIDDEN_ITEMS:
        return _dropped_condition(key, list(written.values), written.field_values)
    return _kept_condition(key, list(written.values))


def _values_written_in(values: list[object]) -> list[exp.Expression]:
    """Each value but a blank, written into the Hive, as a condition's IN lists them."""
    return [constant_hive(value) for value in values if value is not None]


def _kept_condition(key: exp.Expression, values: list[object]) -> exp.Expression:
    """Hive keeping the rows whose `key` is one of `values`, a blank among them as IS NULL."""
    known = _values_written_in(values)
    parts = []
    if len(known) == 1:
        parts.append(binary(exp.EQ, key.copy(), known[0]))
    elif known:
        parts.append(exp.In(this=key.copy(), expressions=known))
    if None in values:
        parts.append(exp.Is(this=key.copy(), expression=exp.Null()))
    if len(parts) == 2:
        return binary(exp.Or, parts[0], parts[1])
    return parts[0]


def _dropped_condition(key: exp.Expression, values: list[object],
                       items: tuple[object, ...]) -> exp.Expression:
    """Hive dropping the rows whose `key` is one of `values`: a blank among them dropped with
    IS NOT NULL, or else kept with IS NULL where the field has a blank item."""
    known = _values_written_in(values)
    not_blank = exp.Not(this=exp.Is(this=key.copy(), expression=exp.Null()))
    if not known:
        return not_blank
    dropped = exp.Not(this=exp.In(this=key.copy(), expressions=known))
    if len(known) == 1:
        dropped = binary(exp.NEQ, key.copy(), known[0])
    if None in values:
        return binary(exp.And, not_blank, dropped)
    if None in items:
        return binary(exp.Or, exp.Is(this=key.copy(), expression=exp.Null()), dropped)
    return dropped


def _top_condition(pivot: PivotTable, top: ConvertedPivotFilter,
                   source_read: exp.Expression,
                   conditions: list[exp.Expression]) -> exp.Expression:
    """A Top or Bottom value filter's items, kept by a RANK window over the items' values,
    worked out on the rows the other filters keep, in a subquery of its own, which reads the
    source a second time: the totals of the kept items need them before the rows are grouped
    (PF5)."""
    key = field_key(pivot, top.field)
    value = value_captioned(pivot, top.ranked_by)
    order = window_order(value_aggregate(pivot, value), descending=not top.bottom)
    rank_column = exp.alias_(_windowed(hive_call("RANK", []), [], order),
                             exp.Identifier(this=ITEM_RANK, quoted=False))
    ranked = exp.select(_key_column(top.field, key), rank_column).from_(source_read.copy())
    if conditions:
        ranked = ranked.where(all_of([condition.copy() for condition in conditions]))
    ranked = ranked.group_by(key.copy())
    kept = exp.select(column_hive(top.field)).from_(exp.Subquery(
        this=ranked, alias=exp.TableAlias(this=exp.Identifier(this="ranked"))))
    kept = kept.where(binary(exp.LTE, column_hive(ITEM_RANK), constant_hive(top.values[0])))
    return exp.In(this=key.copy(), query=exp.Subquery(this=kept))


def is_value_named(value: PivotValue, name: str) -> bool:
    """Whether a value is the one `name` names, as GETPIVOTDATA and a value filter name one:
    by its caption, such as "Sum of hours", or by the field it sums, whatever the case."""
    return name.lower() in (value.caption.lower(), value.field.lower())


def value_captioned(pivot: PivotTable, caption: str) -> PivotValue:
    """The pivot's value by its caption, such as "Sum of hours", or by the field it sums."""
    for value in pivot.values:
        if is_value_named(value, caption):
            return value
    raise Refused("PX5", f"it reads the value {caption}, which the pivot doesn't show")


# --- GETPIVOTDATA ----------------------------------------------------------------------------


def getpivotdata_hive(call: Call, place: Place) -> exp.Expression:
    """GETPIVOTDATA: a LEFT JOIN of the pivot, its CTE, on the fields it names, each matched
    to the item it names, and the value's column of it (PG1); one naming fewer fields reads
    the total level it names, as its own query, if the pivot shows it (PG2)."""
    if len(call.args) < 2 or len(call.args) % 2:
        raise Refused("PG1", "GETPIVOTDATA needs its value, a cell of its pivot, and each "
                             "field with its item")
    piece, pivot, value = _pivot_value_read(call.args[0], place)
    named = _fields_named(call, pivot, place)
    own = own_level(pivot)
    level = PivotLevel(tuple(name for name in own.rows if name in named),
                       tuple(name for name in own.columns if name in named))
    book = place.query.book
    if level == own:
        if piece not in book.reads:
            raise Refused("PG1", f"it reads {piece_name(piece)}, which has no Hive")
        pivot_rows = book.reads[piece]
    elif level in levels_shown(pivot):
        pivot_rows, _ = level_select(pivot, level, _source_read(pivot, book), piece.name)
    else:
        fields = in_words([*level.rows, *level.columns]) or "nothing"
        raise Refused("PG2", f"it reads a total of {pivot.name} by {fields}, which the pivot "
                             "doesn't show")
    keys = [(name, named[name]) for name in (*level.rows, *level.columns)]
    join = _pivot_join(piece, pivot_rows, keys, place)
    place.marks.append(Note(MARK, "PG1", f"{place.query.table.name}[{place.column}]",
                            "GETPIVOTDATA: NULL where its pivot has no such value, where "
                            "Excel shows #REF!"))
    return column_hive(value_column_name(value), join.alias)


def _pivot_value_read(data_field: FormulaPart, place: Place
                      ) -> tuple[Piece, PivotTable, PivotValue]:
    """The pivot a GETPIVOTDATA reads, among those its Table reads in the Order, by the value
    it names, and that value."""
    if not isinstance(data_field, Constant) or not isinstance(data_field.value, str):
        raise Refused("PG1", "its value isn't named in the formula")
    workbook = place.query.book.workbook
    for piece in workbook.order.get(Piece(EXCEL_TABLE, place.query.table.name), []):
        if piece.kind != PIVOT_TABLE:
            continue
        pivot = pivot_of(piece, workbook)
        for value in pivot.values:
            if is_value_named(value, data_field.value):
                return piece, pivot, value
    raise Refused("PG1", f"no pivot it reads shows the value {data_field.value}")


def _fields_named(call: Call, pivot: PivotTable, place: Place) -> dict[str, exp.Expression]:
    """Each Row or Column field a GETPIVOTDATA names, by the pivot's name for it, with the
    Hive of the item it names."""
    own = own_level(pivot)
    fields = {name.lower(): name for name in (*own.rows, *own.columns)}
    named = {}
    for field_part, item in zip(call.args[2::2], call.args[3::2], strict=True):
        if not isinstance(field_part, Constant) or str(field_part.value).lower() not in fields:
            raise Refused("PG1", f"it names a field that isn't a Row or Column field of "
                                 f"{pivot.name}")
        named[fields[str(field_part.value).lower()]] = hive_of(item, place)
    return named


def _pivot_join(piece: Piece, pivot_rows: exp.Expression,
                keys: list[tuple[str, exp.Expression]], place: Place) -> PivotJoin:
    """The LEFT JOIN of a pivot's rows on `keys`: one already there, or a new one."""
    query = place.query
    for join in query.joins:
        if isinstance(join, PivotJoin) and join.pivot_rows == pivot_rows and (
                join.keys == keys):
            return join
    alias = free_alias(piece.name, query.taken)
    query.taken.add(alias)
    join = PivotJoin(alias, pivot_rows.copy(), keys)
    query.joins.append(join)
    return join


# The functions a formula may call that read a pivot, beside file 11's
# (`workbook_hive._functions`).
PIVOT_FUNCTIONS = {"GETPIVOTDATA": getpivotdata_hive}
