"""A Formula workbook's whole-column totals and Total Rows written as Hive, by Copilot file 12's
rules T1 to T4 (Toolbox 8.9, ticket 05; ADR 0016).

`WHOLE_COLUMN_FUNCTIONS` writes a formula's total of a whole column, `SUM(t[v])`, as a window
over every row of its own Table, or another Table's total (T1); `workbook_hive.py` puts them
beside file 11's functions. `total_row_finals` writes each Table's Total Row as a final of its
own, reading the Table's final as a CTE (T2), or none where the person said no one needs it
(T3); the Table's own final holds only its rows (T4).
"""

from __future__ import annotations

from collections.abc import Callable

from sqlglot import exp

from .lean_hive import lean_ctes, with_ctes
from .workbook_formula_reader import Call, Constant, Refused, WholeColumn, read_formula
from .workbook_formulas import (
    EXCEL_AGGREGATES,
    EXCEL_TABLE,
    FUNCTIONS,
    LEFT_ALONE,
    REFUSED,
    Book,
    Note,
    Place,
    binary,
    column_hive,
    column_named,
    hive_call,
    hive_name,
    identifier,
    is_own,
    table_named,
    tables_of,
    this_row,
    totals_read,
)
from .workbook_reader import Piece, Table, Workbook

# What a Table's Total Row's final is named after (file 15's P9, file 12's T2).
TOTAL_ROW = " (Total Row)"
# A Total Row's SUBTOTAL, by its function number, as the Excel aggregate it is (file 12's T2).
SUBTOTALS = {109: "SUM", 101: "AVERAGE", 102: "COUNT", 103: "COUNTA", 104: "MAX", 105: "MIN"}


# --- A whole column's total in a formula (T1) ------------------------------------------------


def column_total_hive(call: Call, place: Place) -> exp.Expression:
    """SUM(t[v]), AVERAGE, COUNT, COUNTA, MIN, MAX, STDEV.S and VAR.S of a whole column in a
    formula column: over its own Table `SUM(v) OVER ()`, COUNTA as COUNT(v), STDEV.S
    STDDEV_SAMP, VAR.S VAR_SAMP; over another Table, a CROSS JOIN of its total (T1). MIN and
    MAX of a row's cells are file 11's."""
    if len(call.args) != 1 or not isinstance(call.args[0], WholeColumn):
        if call.name in FUNCTIONS:
            return FUNCTIONS[call.name](call, place)
        raise Refused("T1", f"{call.name} of anything but one whole column isn't a form file "
                            "12 lists")
    (column,) = call.args
    return whole_table_total(column.table, [column.column], EXCEL_AGGREGATES[call.name],
                             place)


def sumproduct_total_hive(call: Call, place: Place) -> exp.Expression:
    """SUMPRODUCT(t[a], t[b]) of whole columns alone: `SUM(a * b) OVER ()` (T1); over
    conditions, file 11's I3."""
    columns = call.args
    if not columns or not all(isinstance(each, WholeColumn) for each in columns) or len(
            {each.table.lower() for each in columns}) > 1:
        return FUNCTIONS["SUMPRODUCT"](call, place)
    return whole_table_total(columns[0].table, [each.column for each in columns], "SUM", place)


def whole_table_total(table_name: str, headers: list[str], aggregate: str,
                      place: Place) -> exp.Expression:
    """An aggregate of a Table's whole columns, multiplied: over its own Table a window over
    every row, `SUM(v) OVER ()`; over another, its total, a CROSS JOIN (T1)."""
    table = table_named(table_name, place)
    if is_own(table_name, place):
        values = [this_row(header, place) for header in headers]
    else:
        if Piece(EXCEL_TABLE, table.name) not in place.query.book.reads:
            raise Refused("X1", f"it reads {table.name}, which has no Hive")
        values = [other_table_column(table, header) for header in headers]
    product = values[0]
    for each in values[1:]:
        product = binary(exp.Mul, product, each)
    total = hive_call(aggregate, [product])
    if aggregate == "VAR_SAMP":
        # sqlglot writes its sample variance as Hive's VARIANCE, which is the population's.
        total = exp.Anonymous(this="VAR_SAMP", expressions=[product])
    if is_own(table_name, place):
        return exp.Window(this=total, over="OVER")
    return totals_read(table, [], None, total, False, place)


def other_table_column(table: Table, header: str) -> exp.Column:
    """Another Table's column a whole-column total reads, by its header as that Table writes
    it; refused where it has none of that header."""
    column = column_named(table, header)
    if column is None:
        raise Refused("X1", f"it reads {table.name}[{header}], which {table.name} doesn't have")
    return column_hive(column.header)


# Each function a whole column's total calls (T1), by its name, and the function writing it.
WHOLE_COLUMN_FUNCTIONS: dict[str, Callable[[Call, Place], exp.Expression]] = {
    **dict.fromkeys(EXCEL_AGGREGATES, column_total_hive), "SUMPRODUCT": sumproduct_total_hive,
}


# --- A Table's Total Row (T2 to T4) ----------------------------------------------------------


def total_row_finals(workbook: Workbook, queries: dict[str, exp.Query], book: Book,
                     left_out: tuple[str, ...] = ()) -> dict[str, exp.Query]:
    """Each Table's Total Row as a final of its own, `<Table> (Total Row)`: one row, a column
    for each cell holding a total, in the Table's order, reading the Table's query, `queries`
    by its name, as a CTE (T2), or a source's database table; none for a Table `left_out`
    names, as the person said no one needs it kept, named as left out (T3). The Table's own
    final holds only its rows (T4)."""
    finals = {}
    unneeded = {name.lower() for name in left_out}
    for table in tables_of(workbook).values():
        where = table.name + TOTAL_ROW
        if not table.has_total_row:
            continue
        if table.name.lower() in unneeded:
            book.notes.append(Note(LEFT_ALONE, "T3", where, "no one needs it kept: left out"))
            continue
        source = book.reads.get(Piece(EXCEL_TABLE, table.name))
        if table.name not in queries and not isinstance(source, exp.Table):
            book.notes.append(Note(REFUSED, "T2", where, f"{table.name} has no Hive"))
            continue
        totals = total_cells(table, where, book)
        if not totals:
            book.notes.append(Note(LEFT_ALONE, "T2", where, "it holds no total, only labels"))
        elif table.name in queries:
            finals[where] = over_its_table(queries[table.name], table, totals)
        else:
            # A Table of typed columns alone is a source: its rows are its database table's.
            finals[where] = exp.select(*totals).from_(source.copy())
    return finals


def total_cells(table: Table, where: str, book: Book) -> list[exp.Expression]:
    """A Total Row's totals, each a column AS its header: SUBTOTAL(109, ..) a SUM, 101 AVG, 102
    or 103 COUNT, 104 MAX, 105 MIN; none for an empty cell or a label; any other formula NULL,
    named (T2)."""
    totals: list[exp.Expression] = []
    for column in table.columns:
        cell = column.total
        if not isinstance(cell, str) or not cell.startswith("="):
            continue
        try:
            total = subtotal_hive(read_formula(cell), table)
        except Refused as refusal:
            book.notes.append(Note(REFUSED, refusal.rule, f"{where}[{column.header}]",
                                   f"NULL in its place: {refusal.why}"))
            total = exp.Null()
        totals.append(exp.alias_(total, identifier(column.header)))
    return totals


def subtotal_hive(part: object, table: Table) -> exp.Expression:
    """A Total Row cell's SUBTOTAL(n, t[c]) as its aggregate of c (T2)."""
    if not isinstance(part, Call) or part.name != "SUBTOTAL" or len(part.args) != 2:
        raise Refused("T2", "a Total Row's total is a SUBTOTAL file 12 lists")
    code, column = part.args
    number = code.value if isinstance(code, Constant) else None
    if not isinstance(number, (int, float)) or int(number) not in SUBTOTALS:
        raise Refused("T2", "its SUBTOTAL's number isn't one file 12 lists")
    if not isinstance(column, WholeColumn) or column.table.lower() not in (
            "", table.name.lower()) or column_named(table, column.column) is None:
        raise Refused("T2", f"its SUBTOTAL reads no column of {table.name}")
    header = column_named(table, column.column).header
    return hive_call(EXCEL_AGGREGATES[SUBTOTALS[int(number)]], [column_hive(header)])


def over_its_table(query: exp.Query, table: Table,
                   totals: list[exp.Expression]) -> exp.Query:
    """A Total Row's final: its totals over the Table's query, read as a CTE named for the
    Table, after the CTEs that query reads (file 12's W2)."""
    body = query.copy()
    held = body.args.get("with_")
    ctes = []
    if held is not None:
        ctes = list(held.expressions)
        body.set("with_", None)
    name = hive_name(table.name)
    while name in {cte.alias for cte in ctes}:
        name = f"{name.strip('<>')}_rows"
    ctes.append(exp.CTE(this=body, alias=exp.TableAlias(this=identifier(name))))
    final = exp.select(*totals).from_(exp.Table(this=identifier(name)))
    # W2 reads the Table's final whole, as file 12 writes it, every column of it kept.
    return lean_ctes(with_ctes(final, ctes), (name,))
