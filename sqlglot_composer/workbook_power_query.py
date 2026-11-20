"""A Formula workbook's Power Queries written as Hive, by Copilot file 12's rules (Toolbox 8.9,
ticket 05; ADR 0016).

A query's M is read into its tree (`read_m`, in `workbook_m_reader.py`), then each step it gives
is written into the SELECT it builds (`Rows`): a filter into its WHERE, or its HAVING after a
group (Q2 to Q4), a column step into its columns (Q5 to Q7), a group, a join, a stack, a sort
(G1 to G5, S1 to S3), each by its rule's ID. A step goes into the SELECT the step before it
built while the rows allow, so a filter stays with the table it reads and a chain of steps that
rename or add a column is one SELECT; where they don't, as a filter after a FirstN, that SELECT
is read in brackets. A step file 12 doesn't list is refused: NULL in place of a column it
makes, or else the query left out, each named with why (file 12's Terms, X1).

`power_query_hive` gives a query's SELECT, which `workbook_hive.py` puts in its place; file 12's
whole-column totals and Total Rows are `workbook_totals.py`'s.
"""

from __future__ import annotations

import datetime

import copy
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlglot import exp

from .shared import in_words
from .workbook_formula_reader import Refused
from .workbook_formulas import (
    ARITHMETIC,
    COMPARISONS,
    EXCEL_TABLE,
    MARK,
    REFUSED,
    Book,
    Note,
    all_of,
    binary,
    check_argument_count,
    column_hive,
    constant_hive,
    free_alias,
    hive_call,
    hive_name,
    identifier,
    operand_hive,
    rule_hive,
    tables_of,
    value_text,
    window_order,
)
from .workbook_m_reader import (
    MCall,
    MEach,
    MField,
    MIf,
    MItem,
    MLet,
    MList,
    MName,
    MNegative,
    MNot,
    MOperation,
    MPart,
    MRecord,
    MValue,
    read_m,
)
from .workbook_reader import POWER_QUERY, Piece, Query

# A source outside the workbook that file 12's M1 reads the table of: a database, by its M.
DATABASE_SOURCES = ("Sql.Database", "Oracle.Database", "PostgreSQL.Database", "MySQL.Database")
# A query reading the web, which file 12's X1 leaves out.
WEB_SOURCE = re.compile(r"\b(Web\.[A-Za-z]+|OData\.Feed|SharePoint\.[A-Za-z]+)\s*\(")
# What a SELECT already holds, each of which a later step may need it read in brackets for.
FACETS = {"where", "joins", "group", "distinct", "window", "limit"}
# M's functions that have a twin in Hive (file 12's Q7), each as its Hive with a placeholder for
# each argument, one text for each number of arguments M's form of it takes.
M_TWINS = {
    "Text.Upper": ("UPPER(p0)",), "Text.Lower": ("LOWER(p0)",), "Text.Trim": ("TRIM(p0)",),
    "Text.Length": ("LENGTH(p0)",), "Text.Start": ("SUBSTR(p0, 1, p1)",),
    "Text.End": ("SUBSTR(p0, -p1)",),
    "Text.Middle": ("SUBSTR(p0, p1 + 1)", "SUBSTR(p0, p1 + 1, p2)"),
    "Text.Replace": ("REPLACE(p0, p1, p2)",), "Text.Proper": ("INITCAP(p0)",),
    "Number.Round": ("BROUND(p0)", "BROUND(p0, p1)"), "Number.RoundDown": ("FLOOR(p0)",),
    "Number.RoundUp": ("CEIL(p0)",), "Number.Abs": ("ABS(p0)",),
    "Number.Mod": ("PMOD(p0, p1)",), "Date.Year": ("YEAR(p0)",), "Date.Month": ("MONTH(p0)",),
    "Date.Day": ("DAY(p0)",), "Date.AddDays": ("DATE_ADD(p0, p1)",),
    "Date.AddMonths": ("ADD_MONTHS(p0, p1)",), "Date.AddYears": ("ADD_MONTHS(p0, 12 * p1)",),
    "Date.EndOfMonth": ("LAST_DAY(p0)",),
    "Date.StartOfMonth": ("CAST(TRUNC(p0, 'MM') AS STRING)",),
}
# Text.Contains and its like (file 12's Q3), each as the LIKE pattern around its text.
# What goes before and after the text in each one's LIKE pattern.
LIKE_PATTERNS = {"Text.Contains": ("%", "%"), "Text.StartsWith": ("", "%"),
                 "Text.EndsWith": ("%", "")}
# A Table.Group's aggregates of a column (file 12's G1), by their M names.
LIST_AGGREGATES = {"List.Sum": "SUM", "List.Max": "MAX", "List.Min": "MIN",
                   "List.Average": "AVG", "List.StandardDeviation": "STDDEV_SAMP"}
# A Table.Pivot's aggregate (file 12's M2), by its M name: it counts or adds up, as the file
# lists; List.Max, List.Min and List.Average are refused (ticket 13).
PIVOT_AGGREGATES = {"List.Sum": "SUM", "List.Count": "SUM"}
# M's JoinKinds (file 12's G2), each as the join it is.
JOIN_KINDS = ("LeftOuter", "Inner", "RightOuter", "FullOuter", "LeftAnti", "RightAnti")


@dataclass
class Nested:
    """A column of tables a step made, a NestedJoin's or a Group's, which ExpandTableColumn
    takes columns from: each column's Hive, and its sample."""

    columns: dict[str, exp.Expression]
    samples: dict[str, list[object]]


@dataclass
class Rows:
    """The rows a step of a query gives, as the SELECT they are written into: the name of what
    it reads, for its alias; what its FROM reads, a table or a query; each column's Hive, by
    its name, in order, and whether those are all its columns (False for a table outside the
    workbook, M1); its FROM's alias, if it has one, and every alias taken; its joins, WHERE,
    GROUP BY (None where it doesn't group), HAVING, a sort not yet written (S1 to S3) and
    whether a FirstN or an index used it, LIMIT and DISTINCT; each column of tables not yet
    expanded; each column's sample, where it is a Table's column; a UNION, INTERSECT or EXCEPT
    a later step reads in brackets; and a NestedJoin on every column, which a Table.Distinct
    makes INTERSECT or EXCEPT (G3)."""

    name: str
    source: exp.Expression | None
    columns: dict[str, exp.Expression]
    all_known: bool = True
    alias: str = ""
    taken: set[str] = field(default_factory=set)
    joins: list[exp.Join] = field(default_factory=list)
    where: list[exp.Expression] = field(default_factory=list)
    group: list[exp.Expression] | None = None
    having: list[exp.Expression] = field(default_factory=list)
    order: list[exp.Ordered] = field(default_factory=list)
    order_used: bool = False
    limit: int | None = None
    distinct: bool = False
    nested: dict[str, Nested] = field(default_factory=dict)
    samples: dict[str, list[object]] = field(default_factory=dict)
    set_query: exp.Query | None = None
    exact: tuple[str, exp.Query, exp.Query] | None = None


@dataclass
class Reading:
    """One query's M as it is read: the query, its steps by name and the expression it gives,
    the Book, each step's rows once read, the steps being read, for a loop between them, and
    what its map names."""

    query: Query
    steps: dict[str, MPart]
    result: MPart
    book: Book
    done: dict[str, Rows] = field(default_factory=dict)
    reading: list[str] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)

    @property
    def where(self) -> str:
        """Where the map says the query's notes are."""
        return f'Power Query "{self.query.name}"'


# --- A query ---------------------------------------------------------------------------------


def power_query_hive(name: str, book: Book) -> tuple[exp.Query, list[Note]]:
    """Power Query `name`'s rows as Hive, by file 12's rules, and what its map names; refused
    (Refused) where it reads the web or a step that can't be written leaves no right rows."""
    reading = query_reading(name, book)
    web = web_source(reading.query.m)
    if web is not None:
        raise Refused("X1", f"{web} reads the web, so the query is left out")
    rows = finished_rows(reading)
    return select_of(rows), reading.notes


def web_source(m: str) -> str | None:
    """The web source an M reads, such as Web.Contents, or None (file 12's X1)."""
    found = WEB_SOURCE.search(m)
    if found is None:
        return None
    return found.group(1)


def query_reading(name: str, book: Book) -> Reading:
    """Power Query `name`'s M, read into its steps, ready to be written."""
    for query in book.workbook.queries:
        if query.name == name:
            part = read_m(query.m)
            if isinstance(part, MLet):
                return Reading(query, dict(part.steps), part.result, book)
            return Reading(query, {}, part, book)
    raise Refused("Q1", f"the workbook has no Power Query {name}")


def finished_rows(reading: Reading) -> Rows:
    """The rows a query gives: its last step's, each column known, any sort with no FirstN
    after it dropped (S3)."""
    rows = rows_of(reading.result, reading)
    if not rows.all_known:
        table = tables_of(reading.book.workbook).get(reading.query.loads.lower())
        if table is None:
            raise Refused("M1", "it reads a table outside the workbook and loads no Table, so "
                                "its columns aren't known")
        rows.columns = {column.header: query_column(rows, column.header)
                        for column in table.columns}
        rows.all_known = True
    if rows.nested:
        raise Refused("X1", f"it gives {in_words(list(rows.nested))}, a column of tables, "
                            "which a Hive table can't hold")
    settle_order(rows, reading)
    return rows


def rows_of(part: MPart, reading: Reading) -> Rows:
    """The rows a part of the M gives: a step's, another query's, a table's it reads, or a
    Table function's (`TABLE_STEPS`); refused where it gives none file 12 lists."""
    if isinstance(part, MName):
        return named_rows(part.name, reading)
    if isinstance(part, MField) and isinstance(part.record, MItem):
        return navigated_rows(part.record, part.name, reading)
    if isinstance(part, MCall) and isinstance(part.function, MName):
        step = TABLE_STEPS.get(part.function.name)
        if step is None:
            raise Refused("X1", f"{part.function.name} isn't a step file 12 lists")
        rows = step(part.args, reading)
        if part.function.name not in ("Table.NestedJoin", "Table.RemoveColumns"):
            rows.exact = None
        return rows
    raise Refused("X1", "a step gives no table file 12 reads")


def named_rows(name: str, reading: Reading) -> Rows:
    """The rows a name gives: a step of the query's, read once, or another query's (Q1)."""
    if name in reading.steps:
        if name not in reading.done:
            if name in reading.reading:
                raise Refused("X1", f"its step {name} reads itself")
            reading.reading.append(name)
            try:
                reading.done[name] = rows_of(reading.steps[name], reading)
            finally:
                reading.reading.pop()
        return copy.deepcopy(reading.done[name])
    if any(query.name == name for query in reading.book.workbook.queries):
        return query_read(name, reading.book)
    raise Refused("X1", f"it reads {name}, which is no step of it, nor a query")


def resolved(part: MPart, reading: Reading) -> MPart:
    """A part, or the step's part a name stands for, at any depth."""
    seen: list[str] = []
    while isinstance(part, MName) and part.name in reading.steps and part.name not in seen:
        seen.append(part.name)
        part = reading.steps[part.name]
    return part


# --- What a query reads (Q1, M1) -------------------------------------------------------------


def navigated_rows(item: MItem, field_name: str, reading: Reading) -> Rows:
    """A table a query reads by its place: `Excel.CurrentWorkbook(){[Name="t"]}[Content]`, the
    workbook's Table t (Q1), or `Sql.Database(..){[Schema="s", Item="t"]}[Data]`, a table
    outside the workbook (M1)."""
    target = resolved(item.target, reading)
    selector = resolved(item.selector, reading)
    if not isinstance(target, MCall) or not isinstance(target.function, MName) or not (
            isinstance(selector, MRecord)):
        raise Refused("X1", "it reads a table by a place file 12 doesn't list")
    named = dict(selector.fields)
    if target.function.name == "Excel.CurrentWorkbook" and field_name == "Content":
        return table_read(text_of(named.get("Name"), reading), reading)
    if target.function.name in DATABASE_SOURCES and field_name == "Data":
        return outside_read(target, text_of(named.get("Item", named.get("Name")), reading),
                            reading)
    raise Refused("X1", f"it reads {target.function.name}, a source file 12 doesn't list")


def table_read(name: str, reading: Reading) -> Rows:
    """The workbook's Table `name`, as a query reads it: by its Hive, `<database>.<table>` or a
    step's CTE (Q1), each of its columns with its sample."""
    table = tables_of(reading.book.workbook).get(name.lower())
    if table is None:
        raise Refused("Q1", f"it reads {name}, which is no Table of the workbook")
    read = reading.book.reads.get(Piece(EXCEL_TABLE, table.name))
    if read is None:
        raise Refused("Q1", f"it reads Table {table.name}, which has no Hive")
    columns = {column.header: column_hive(column.header) for column in table.columns}
    samples = {column.header: list(column.cells) for column in table.columns}
    return Rows(table.name, read.copy(), columns, samples=samples)


def query_read(name: str, book: Book) -> Rows:
    """Another query's rows, read by its CTE's name (Q1, C3), each of its columns with its
    sample, as its own M gives them."""
    read = book.reads.get(Piece(POWER_QUERY, name))
    if read is None:
        raise Refused("Q1", f"it reads Power Query {name}, which has no Hive")
    given = finished_rows(query_reading(name, book))
    columns = {column: column_hive(column) for column in given.columns}
    return Rows(name, read.copy(), columns, samples=dict(given.samples))


def outside_read(source: MCall, name: str, reading: Reading) -> Rows:
    """A table outside the workbook, as Sql.Database names it: read as `<database>.<table>`,
    its columns as the steps after it name them, marked (M1)."""
    if len(source.args) > 2:
        raise Refused("X1", f"{source.function.name} with a query of its own isn't a source "
                            "file 12 lists")
    table = exp.Table(this=identifier(name), db=identifier(reading.book.database))
    reading.notes.append(Note(MARK, "M1", reading.where,
                              f"{source.function.name}: it reads {name}, a table outside the "
                              f"workbook, as {reading.book.database}.{hive_name(name)}"))
    return Rows(name, table, {}, all_known=False)


# --- The SELECT a query's rows are -----------------------------------------------------------


def select_of(rows: Rows) -> exp.Query:
    """The rows as one SELECT: its columns in order, its FROM, joins, WHERE, GROUP BY, HAVING,
    ORDER BY and LIMIT (S1), and DISTINCT; or the UNION, INTERSECT or EXCEPT they are."""
    if rows.set_query is not None:
        return rows.set_query.copy()
    if rows.nested:
        raise Refused("X1", f"{in_words(list(rows.nested))} is a column of tables no step "
                            "expands")
    select = exp.select(*[named_hive(expression, name)
                          for name, expression in rows.columns.items()])
    select = select.from_(from_hive(rows))
    for join in rows.joins:
        select = select.join(join.copy())
    if rows.where:
        select = select.where(all_of([each.copy() for each in rows.where]))
    if rows.group:
        select = select.group_by(*[each.copy() for each in rows.group])
    if rows.having:
        select = select.having(all_of([each.copy() for each in rows.having]))
    if rows.limit is not None:
        if rows.order:
            select = select.order_by(*[each.copy() for each in rows.order])
        select = select.limit(rows.limit)
    if rows.distinct:
        select = select.distinct()
    return select


def named_hive(expression: exp.Expression, name: str) -> exp.Expression:
    """A column as a SELECT writes it: as it is where it is a column of that name, else AS its
    name."""
    if isinstance(expression, exp.Column) and expression.name == hive_name(name):
        return expression.copy()
    return exp.alias_(expression.copy(), identifier(name))


def from_hive(rows: Rows) -> exp.Expression:
    """What a SELECT's FROM reads: a table, after its alias if it has one, or a query in
    brackets, after its alias."""
    if isinstance(rows.source, exp.Table):
        source = rows.source.copy()
        if rows.alias:
            source.set("alias", exp.TableAlias(this=exp.Identifier(this=rows.alias)))
        return source
    if not rows.alias:
        rows.alias = free_alias(rows.name, rows.taken)
        rows.taken.add(rows.alias)
    return exp.Subquery(this=rows.source.copy(),
                        alias=exp.TableAlias(this=exp.Identifier(this=rows.alias)))


def facets_of(rows: Rows) -> set[str]:
    """What the rows' SELECT already holds, of FACETS."""
    held = set()
    for name, holds in (("where", rows.where), ("joins", rows.joins),
                        ("group", rows.group is not None), ("distinct", rows.distinct),
                        ("limit", rows.limit is not None)):
        if holds:
            held.add(name)
    if any(expression.find(exp.Window) for expression in rows.columns.values()):
        held.add("window")
    return held


def ready_rows(rows: Rows, reading: Reading, allowed: set[str]) -> Rows:
    """The rows a step writes into: their own SELECT where it holds nothing but `allowed`,
    else that SELECT read in brackets, so the step gives the rows M does."""
    if rows.set_query is None and not facets_of(rows) - allowed:
        return rows
    return wrapped_rows(rows, reading)


def wrapped_rows(rows: Rows, reading: Reading) -> Rows:
    """The rows' SELECT read in brackets, each column by its name."""
    settle_order(rows, reading)
    query = select_of(rows)
    columns = {name: column_hive(name) for name in rows.columns}
    return Rows(rows.name, query, columns, samples=dict(rows.samples))


def settle_order(rows: Rows, reading: Reading) -> None:
    """Drop a sort no FirstN or index used, as a Hive table holds no order, marked "order
    dropped" (S3)."""
    if rows.order and rows.limit is None and not rows.order_used:
        reading.notes.append(Note(MARK, "S3", reading.where,
                                  "order dropped: a Table.Sort with no FirstN or index after "
                                  "it has no ORDER BY, as a Hive table holds no order"))
    if rows.limit is None:
        rows.order = []


def qualify(rows: Rows, avoid: set[str]) -> None:
    """Give the rows' FROM an alias, if it has none, one `avoid` doesn't hold, and each column
    they read with no table's alias before it that alias, ready for a join."""
    if not rows.alias:
        rows.alias = free_alias(rows.name, rows.taken | avoid)
    rows.taken.add(rows.alias)
    alias = rows.alias

    def put(node: exp.Expression) -> exp.Expression:
        if isinstance(node, exp.Column) and not node.table:
            return exp.Column(this=node.this.copy(), table=exp.Identifier(this=alias))
        return node

    rows.columns = {name: each.transform(put) for name, each in rows.columns.items()}
    rows.where = [each.transform(put) for each in rows.where]
    rows.having = [each.transform(put) for each in rows.having]
    rows.order = [each.transform(put) for each in rows.order]
    if rows.group is not None:
        rows.group = [each.transform(put) for each in rows.group]
    for nested in rows.nested.values():
        nested.columns = {name: each.transform(put) for name, each in nested.columns.items()}


def alias_other(rows: Rows, other: Rows, hint: str) -> None:
    """Give `other`, a table joined to `rows`, an alias from `hint`, the first letter of its
    name, and `rows` one if it has none, neither the same, then each of them their columns
    after their alias."""
    alias = free_alias(hint, set())
    qualify(rows, {alias})
    if alias in rows.taken:
        alias = free_alias(hint, rows.taken)
    other.alias = alias
    qualify(other, set())
    rows.taken.add(alias)


def query_column(rows: Rows, name: str) -> exp.Expression:
    """A column the rows have, by its name, as Hive: the expression that gives it; in a table
    outside the workbook, the column of that name."""
    if name in rows.columns:
        return rows.columns[name].copy()
    if not rows.all_known:
        return column_hive(name, rows.alias)
    raise Refused("X1", f"it reads [{name}], which the step before doesn't have")


# --- Constants in the M ----------------------------------------------------------------------


def constant_of(part: MPart | None, reading: Reading) -> object:
    """A part that is a constant: a text, a number, true, false or null, or a list of them."""
    part = resolved(part, reading) if part is not None else None
    if isinstance(part, MValue):
        return part.value
    if isinstance(part, MNegative) and isinstance(part.operand, MValue) and isinstance(
            part.operand.value, (int, float)):
        return -part.operand.value
    if isinstance(part, MList):
        return [constant_of(item, reading) for item in part.items]
    raise Refused("X1", "a step's argument is no constant file 12 reads")


def text_of(part: MPart | None, reading: Reading) -> str:
    """A part that is a text, such as a column's name."""
    value = constant_of(part, reading)
    if not isinstance(value, str):
        raise Refused("X1", "a step's argument is no text, where M names a column")
    return value


def names_of(part: MPart, reading: Reading) -> list[str]:
    """A column's name, or a list of them."""
    value = constant_of(part, reading)
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list) or not all(isinstance(each, str) for each in value):
        raise Refused("X1", "a step's argument is no list of columns' names")
    return value


def step_arguments(args: tuple[MPart, ...], fewest: int, most: int,
                   name: str) -> tuple[MPart, ...]:
    """A step's arguments, refused unless there are as many as file 12's form of it has."""
    check_argument_count(name, len(args), fewest, most, "file 12")
    return args


def each_body(part: MPart, name: str) -> MPart:
    """What an `each` gives."""
    if not isinstance(part, MEach):
        raise Refused("X1", f"{name} without each isn't a form file 12 lists")
    return part.body


def m_name(part: MPart, reading: Reading) -> str:
    """A part that is a name, such as JoinKind.Inner or Text.Upper."""
    part = resolved(part, reading)
    if not isinstance(part, MName):
        raise Refused("X1", "a step's argument is no name, where M names a kind or a function")
    return part.name


def refuse_column(reading: Reading, column: str, refusal: Refused) -> exp.Expression:
    """NULL in place of a column a step makes, named with why (file 12's Terms)."""
    reading.notes.append(Note(REFUSED, refusal.rule, f"{reading.where}[{column}]",
                              f"NULL in its place: {refusal.why}"))
    return exp.Null()


# --- A row's values (Q2, Q3, Q6, Q7) ---------------------------------------------------------


def scalar_hive(part: MPart, rows: Rows, reading: Reading,
                value: exp.Expression | None = None) -> exp.Expression:
    """A part of an `each` as Hive, for one row of `rows`; `value` is what `_` is, a column's
    value in a Table.TransformColumns."""
    if isinstance(part, (MValue, MField, MName)):
        return leaf_hive(part, rows, reading, value)
    if isinstance(part, MOperation):
        return m_operation_hive(part, rows, reading, value)
    if isinstance(part, (MNot, MNegative)):
        operand = scalar_hive(part.operand, rows, reading, value)
        if isinstance(part, MNot):
            return exp.Not(this=operand_hive(operand, exp.Not))
        return exp.Neg(this=operand_hive(operand, exp.Neg))
    if isinstance(part, MIf):
        return hive_call("IF", [scalar_hive(each, rows, reading, value)
                                for each in (part.condition, part.value, part.otherwise)])
    if isinstance(part, MCall) and isinstance(part.function, MName):
        return m_call_hive(part, rows, reading, value)
    raise Refused("X1", "a value no rule of file 12 lists")


def leaf_hive(part: MValue | MField | MName, rows: Rows, reading: Reading,
              value: exp.Expression | None) -> exp.Expression:
    """A constant, a column of the row, `[c]` or `_[c]`, or a name, in an `each`."""
    if isinstance(part, MValue):
        return constant_hive(part.value)
    if isinstance(part, MField):
        if part.record is None or part.record == MName("_"):
            return query_column(rows, part.name)
        raise Refused("Q4", "a column of another table is read only by List.Contains, as one "
                            "of a SelectRows' conditions")
    return m_name_hive(part, rows, reading, value)


def m_name_hive(part: MName, rows: Rows, reading: Reading,
                value: exp.Expression | None) -> exp.Expression:
    """A name in an `each`: `_`, the value a Table.TransformColumns changes, or a step holding
    a constant."""
    if part.name == "_" and value is not None:
        return value.copy()
    found = resolved(part, reading)
    if found != part:
        return scalar_hive(found, rows, reading, value)
    raise Refused("X1", f"it reads {part.name}, which is no value file 12 lists")


def m_operation_hive(part: MOperation, rows: Rows, reading: Reading,
                     value: exp.Expression | None) -> exp.Expression:
    """An operator: `and`, `or` (F2's twins), `&` CONCAT, arithmetic and comparisons as they
    are; `= null` IS NULL and `<> null` IS NOT NULL; and M's `<>`, which keeps a null, `(c <>
    'x' OR c IS NULL)` (Q2)."""
    operator = part.operator
    if operator in ("=", "<>") and MValue(None) in (part.left, part.right):
        other = part.right if part.left == MValue(None) else part.left
        test = "p0 IS NULL" if operator == "=" else "p0 IS NOT NULL"
        return rule_hive(test, p0=scalar_hive(other, rows, reading, value))
    left = scalar_hive(part.left, rows, reading, value)
    right = scalar_hive(part.right, rows, reading, value)
    if operator in ("and", "or"):
        return binary(exp.And if operator == "and" else exp.Or, left, right)
    if operator == "&":
        return hive_call("CONCAT", [left, right])
    if operator == "<>":
        return not_equal_hive(part, left, right)
    if operator in COMPARISONS:
        return binary(COMPARISONS[operator], left, right)
    return binary(ARITHMETIC[operator], left, right)


def not_equal_hive(part: MOperation, left: exp.Expression,
                   right: exp.Expression) -> exp.Expression:
    """M's `<>`, which keeps a null, as Hive's doesn't: `(c <> 'x' OR c IS NULL)`, with a
    constant on one side; between two columns, kept where one alone is null, `(a <> b OR (a
    IS NULL) <> (b IS NULL))`, as M's null <> null is false (Q2)."""
    if isinstance(part.right, MValue):
        return rule_hive("(p0 <> p1 OR p0 IS NULL)", p0=left, p1=right)
    if isinstance(part.left, MValue):
        return rule_hive("(p0 <> p1 OR p0 IS NULL)", p0=right, p1=left)
    return rule_hive("(p0 <> p1 OR (p0 IS NULL) <> (p1 IS NULL))", p0=left, p1=right)


def m_call_hive(call: MCall, rows: Rows, reading: Reading,
                value: exp.Expression | None) -> exp.Expression:
    """An M function a row's value calls: its twin in Hive (Q7), a LIKE (Q3), List.Contains of
    a list, IN (Q4), Text.Combine (Q7), or a date, #date(2026, 9, 1), '2026-09-01' (Q1)."""
    name = call.function.name
    if name in LIKE_PATTERNS:
        return like_hive(call, rows, reading, value)
    if name == "List.Contains":
        return in_list_hive(call, rows, reading, value)
    if name == "Text.Combine":
        return combined_text_hive(call, rows, reading, value)
    if name == "#date":
        year, month, day = (int(each) for each in constant_of(MList(call.args), reading))
        return exp.Literal.string(datetime.date(year, month, day).isoformat())
    if name not in M_TWINS:
        raise Refused("X1", f"{name} is an M function file 12 doesn't list")
    args = {f"p{number}": scalar_hive(arg, rows, reading, value)
            for number, arg in enumerate(call.args)}
    for text in M_TWINS[name]:
        if len(set(re.findall(r"\bp\d\b", text))) == len(args):
            return folded_numbers(rule_hive(text, **args))
    raise Refused("X1", f"{name} with {len(args)} arguments isn't a form file 12 lists")


def folded_numbers(expression: exp.Expression) -> exp.Expression:
    """A twin's Hive with each sum or product of two numbers the M gives worked out, as
    `SUBSTR(status, 2, 2)` for Text.Middle([status], 1, 2) and `ADD_MONTHS(dt, 24)` for
    Date.AddYears([dt], 2) (Q7): lean Hive, as ticket 17 asks."""
    def fold(node: exp.Expression) -> exp.Expression:
        sides = (node.args.get("this"), node.args.get("expression"))
        if not isinstance(node, (exp.Add, exp.Mul)) or not all(
                isinstance(side, exp.Literal) and side.is_number for side in sides):
            return node
        left, right = (float(side.this) for side in sides)
        if isinstance(node, exp.Add):
            return exp.Literal.number(value_text(left + right))
        return exp.Literal.number(value_text(left * right))
    return expression.transform(fold)


def like_hive(call: MCall, rows: Rows, reading: Reading,
              value: exp.Expression | None) -> exp.Expression:
    """Text.Contains([c], "x"), Text.StartsWith, Text.EndsWith: `c LIKE '%x%'`, `'x%'`,
    `'%x'`, case kept, as M keeps it (Q3)."""
    name = call.function.name
    column, text = step_arguments(call.args, 2, 2, name)
    escaped = text_of(text, reading).replace("%", "\\%").replace("_", "\\_")
    before, after = LIKE_PATTERNS[name]
    pattern = before + escaped + after
    return rule_hive("p0 LIKE p1", p0=scalar_hive(column, rows, reading, value),
                     p1=exp.Literal.string(pattern))


def in_list_hive(call: MCall, rows: Rows, reading: Reading,
                 value: exp.Expression | None) -> exp.Expression:
    """List.Contains({1, 3}, [c]): `c IN (1, 3)` (Q4)."""
    listed, item = step_arguments(call.args, 2, 2, "List.Contains")
    if not isinstance(resolved(listed, reading), MList):
        raise Refused("Q4", "List.Contains of another table's column is a LEFT SEMI JOIN, "
                            "which file 12 writes only as one of a SelectRows' conditions")
    values = constant_of(listed, reading)
    return exp.In(this=scalar_hive(item, rows, reading, value),
                  expressions=[constant_hive(each) for each in values])


def combined_text_hive(call: MCall, rows: Rows, reading: Reading,
                       value: exp.Expression | None) -> exp.Expression:
    """Text.Combine({a, b}, ","): CONCAT_WS(',', a, b) (Q7)."""
    parts, *separator = step_arguments(call.args, 1, 2, "Text.Combine")
    parts = resolved(parts, reading)
    if not isinstance(parts, MList):
        raise Refused("X1", "Text.Combine of no list isn't a form file 12 lists")
    joiner = text_of(separator[0], reading) if separator else ""
    return hive_call("CONCAT_WS", [exp.Literal.string(joiner),
                                   *[scalar_hive(each, rows, reading, value)
                                     for each in parts.items]])


# --- Steps on rows and columns (Q2 to Q6) ----------------------------------------------------


def select_rows(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.SelectRows: its condition the WHERE, or after a Table.Group the HAVING, repeating
    the aggregate (Q2); List.Contains(u[k], [k]) a LEFT SEMI JOIN, and with `not` G2's LeftAnti
    (Q4)."""
    table, condition = step_arguments(args, 2, 2, "Table.SelectRows")
    conditions = conjuncts(each_body(condition, "Table.SelectRows"))
    rows = ready_rows(rows_of(table, reading), reading, {"where", "joins", "group", "distinct"})
    if any(contains_join(each) is not None for each in conditions):
        rows = ready_rows(rows, reading, {"where", "joins"})
    for each in conditions:
        if contains_join(each) is not None:
            add_contains_join(rows, each, reading)
        elif rows.group is not None:
            rows.having.append(scalar_hive(each, rows, reading))
        else:
            rows.where.append(scalar_hive(each, rows, reading))
    return rows


def conjuncts(part: MPart) -> list[MPart]:
    """A condition's parts joined by `and`."""
    if isinstance(part, MOperation) and part.operator == "and":
        return conjuncts(part.left) + conjuncts(part.right)
    return [part]


def contains_join(part: MPart) -> MCall | None:
    """A condition that is List.Contains(u[k], [k]), or `not` it: the call, or None."""
    if isinstance(part, MNot):
        part = part.operand
    if isinstance(part, MCall) and part.function == MName("List.Contains") and part.args and (
            isinstance(part.args[0], MField) and part.args[0].record is not None):
        return part
    return None


def add_contains_join(rows: Rows, condition: MPart, reading: Reading) -> None:
    """List.Contains(u[k], [k]): `LEFT SEMI JOIN u ON u.k = t.k`; with `not`, `LEFT JOIN u ON
    u.k = t.k WHERE u.k IS NULL`, G2's LeftAnti (Q4)."""
    call = contains_join(condition)
    column, key = step_arguments(call.args, 2, 2, "List.Contains")
    other = ready_rows(rows_of(column.record, reading), reading, set())
    alias_other(rows, other, other.name)
    other_key = query_column(other, column.name)
    on = binary(exp.EQ, other_key, scalar_hive(key, rows, reading))
    if isinstance(condition, MNot):
        rows.joins.append(exp.Join(this=from_hive(other), side="LEFT", on=on))
        rows.where.append(rule_hive("p0 IS NULL", p0=other_key))
        return
    rows.joins.append(exp.Join(this=from_hive(other), side="LEFT", kind="SEMI", on=on))


def select_columns(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.SelectColumns: the SELECT list, in its order (Q5)."""
    table, names, *missing = step_arguments(args, 2, 3, "Table.SelectColumns")
    rows = ready_rows(rows_of(table, reading), reading, FACETS - {"distinct"})
    columns, nested = {}, {}
    for name in names_of(names, reading):
        if name in rows.nested:
            nested[name] = rows.nested[name]
        elif name in rows.columns or not rows.all_known or not missing:
            columns[name] = query_column(rows, name)
    rows.columns, rows.nested, rows.all_known = columns, nested, True
    return rows


def remove_columns(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.RemoveColumns: the SELECT list without them (Q5); a NestedJoin's column of tables
    removed keeps a join on every column ready for G3."""
    table, names, *_ = step_arguments(args, 2, 3, "Table.RemoveColumns")
    rows = rows_of(table, reading)
    exact = rows.exact
    rows = ready_rows(rows, reading, FACETS - {"distinct"})
    removed = names_of(names, reading)
    for name in removed:
        if name in rows.nested:
            del rows.nested[name]
        elif name in rows.columns:
            del rows.columns[name]
        elif not rows.all_known:
            raise Refused("X1", f"it removes {name} from a table whose columns aren't known")
    rows.exact = None
    if exact is not None and not rows.nested and len(removed) == 1:
        rows.exact = exact
    return rows


def rename_columns(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.RenameColumns: each column AS its new name, in its place (Q5)."""
    table, pairs, *_ = step_arguments(args, 2, 3, "Table.RenameColumns")
    rows = rows_of(table, reading)
    given = constant_of(pairs, reading)
    if given and isinstance(given[0], str):
        given = [given]
    renamed = dict(given)
    if not rows.all_known and set(renamed) - set(rows.columns):
        raise Refused("X1", "it renames a column of a table whose columns aren't known")
    rows.columns = {renamed.get(name, name): each for name, each in rows.columns.items()}
    rows.samples = {renamed.get(name, name): each for name, each in rows.samples.items()}
    rows.nested = {renamed.get(name, name): each for name, each in rows.nested.items()}
    return rows


def reorder_columns(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.ReorderColumns: the columns it names in its order, in the places they held (Q5)."""
    table, names, *_ = step_arguments(args, 2, 3, "Table.ReorderColumns")
    rows = rows_of(table, reading)
    listed = iter([name for name in names_of(names, reading) if name in rows.columns])
    named = set(names_of(names, reading))
    order = []
    for name in rows.columns:
        if name in named:
            order.append(next(listed))
        else:
            order.append(name)
    rows.columns = {name: rows.columns[name] for name in order}
    return rows


def duplicate_column(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.DuplicateColumn(t, "c", "d"): `c, c AS d` (Q5)."""
    table, name, new, *_ = step_arguments(args, 3, 4, "Table.DuplicateColumn")
    rows = rows_of(table, reading)
    rows.columns[text_of(new, reading)] = query_column(rows, text_of(name, reading))
    return rows


def types_buffer_or_headers(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.TransformColumnTypes, Table.Buffer, Table.PromoteHeaders: nothing (Q5)."""
    if not args:
        raise Refused("X1", "a step reads no table")
    return rows_of(args[0], reading)


def add_column(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.AddColumn: an expression AS its name, `if c then a else b` IF(c, a, b) (Q6); its
    value a table, read whole for each row, a CROSS JOIN (G3)."""
    table, name, body, *_ = step_arguments(args, 3, 4, "Table.AddColumn")
    column = text_of(name, reading)
    body = each_body(body, "Table.AddColumn")
    if is_table_part(body, reading):
        return cross_column(rows_of(table, reading), column, body, reading)
    rows = rows_of(table, reading)
    try:
        rows.columns[column] = scalar_hive(body, rows, reading)
    except Refused as refusal:
        rows.columns[column] = refuse_column(reading, column, refusal)
    return rows


def is_table_part(part: MPart, reading: Reading) -> bool:
    """Whether a part gives a table: a Table function's call, a table read by its place, or a
    name standing for one, a step's or another query's."""
    part = resolved(part, reading)
    if isinstance(part, MName):
        return any(query.name == part.name for query in reading.book.workbook.queries)
    if isinstance(part, MField):
        return isinstance(part.record, MItem)
    return isinstance(part, MCall) and isinstance(part.function, MName) and (
        part.function.name in TABLE_STEPS)


def transform_columns(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.TransformColumns(t, {{"c", Text.Upper}}): UPPER(c) AS c (Q6)."""
    table, changes, *_ = step_arguments(args, 2, 3, "Table.TransformColumns")
    rows = ready_rows(rows_of(table, reading), reading, FACETS - {"distinct"})
    changes = resolved(changes, reading)
    if isinstance(changes, MList) and changes.items and isinstance(changes.items[0], MValue):
        changes = MList((changes,))
    if not isinstance(changes, MList):
        raise Refused("X1", "Table.TransformColumns with no list of changes")
    for change in changes.items:
        if not isinstance(change, MList) or len(change.items) < 2:
            raise Refused("X1", "a Table.TransformColumns change isn't {column, function}")
        column = text_of(change.items[0], reading)
        function = resolved(change.items[1], reading)
        if isinstance(function, MEach):
            function = function.body
        else:
            function = MCall(function, (MName("_"),))
        try:
            rows.columns[column] = scalar_hive(function, rows, reading,
                                               query_column(rows, column))
        except Refused as refusal:
            rows.columns[column] = refuse_column(reading, column, refusal)
    return rows


def replace_value(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.ReplaceValue(t, null, 0, Replacer.ReplaceValue, {"c"}): COALESCE(c, 0) AS c; with
    "x", "y" and Replacer.ReplaceText, REPLACE(c, 'x', 'y'); with Replacer.ReplaceValue and a
    value, `IF(c = 'x', 'y', c)`, the whole cell matched (Q6)."""
    table, old, new, replacer, names = step_arguments(args, 5, 5, "Table.ReplaceValue")
    rows = ready_rows(rows_of(table, reading), reading, FACETS - {"distinct"})
    old_value, new_value = constant_of(old, reading), constant_of(new, reading)
    kind = m_name(replacer, reading)
    for name in names_of(names, reading):
        column = query_column(rows, name)
        if kind == "Replacer.ReplaceText":
            text = "REPLACE(p0, p1, p2)"
        elif kind == "Replacer.ReplaceValue" and old_value is None:
            text = "COALESCE(p0, p2)"
        elif kind == "Replacer.ReplaceValue":
            text = "IF(p0 = p1, p2, p0)"
        else:
            raise Refused("X1", f"{kind} isn't a replacer file 12 lists")
        rows.columns[name] = rule_hive(text, p0=column, p1=constant_hive(old_value),
                                       p2=constant_hive(new_value))
    return rows


def fill_down(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.FillDown and FillUp: refused, NULL in each column it fills, named (X1)."""
    table, names = step_arguments(args, 2, 2, "Table.FillDown")
    rows = rows_of(table, reading)
    for name in names_of(names, reading):
        query_column(rows, name)
        rows.columns[name] = refuse_column(reading, name, Refused(
            "X1", "Table.FillDown and FillUp fill a blank from the row next to it, which reads "
                  "the sheet's row order"))
    return rows


# --- Grouping, joining, stacking (G1 to G5, M2) ----------------------------------------------


def group_rows(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.Group: GROUP BY its keys, each aggregate as G1 writes it, and Table.RowCount(_)
    COUNT(*); an index of each group's sorted rows, `ROW_NUMBER() OVER (PARTITION BY ..)` (S2);
    an aggregate file 12 doesn't list NULL, named."""
    table, keys, aggregates = step_arguments(args, 3, 3, "Table.Group")
    rows = rows_of(table, reading)
    settle_order(rows, reading)
    rows = ready_rows(rows, reading, {"where", "joins"})
    keys = names_of(keys, reading)
    listed = aggregations_of(aggregates, reading)
    if len(listed) == 1 and isinstance(listed[0][1], MCall) and (
            listed[0][1].function == MName("Table.AddIndexColumn")):
        return indexed_groups(rows, keys, listed[0], reading)
    columns = {key: query_column(rows, key) for key in keys}
    for name, body in listed:
        try:
            columns[name] = aggregate_hive(body, rows, reading)
        except Refused as refusal:
            columns[name] = refuse_column(reading, name, refusal)
    rows.group = [query_column(rows, key) for key in keys]
    rows.columns = columns
    rows.samples = {key: rows.samples[key] for key in keys if key in rows.samples}
    return rows


def aggregations_of(part: MPart, reading: Reading) -> list[tuple[str, MPart]]:
    """A Table.Group's aggregates, `{{"runs", each Table.RowCount(_), Int64.Type}}`, each its
    name and what its `each` gives; one alone may be written without the outer list."""
    part = resolved(part, reading)
    if isinstance(part, MList) and part.items and isinstance(part.items[0], MValue):
        part = MList((part,))
    if not isinstance(part, MList):
        raise Refused("X1", "a Table.Group with no list of aggregates")
    found = []
    for each in part.items:
        if not isinstance(each, MList) or len(each.items) < 2:
            raise Refused("X1", "a Table.Group aggregate isn't {name, each ..}")
        found.append((text_of(each.items[0], reading),
                      each_body(each.items[1], "a Table.Group aggregate")))
    return found


def aggregate_hive(part: MPart, rows: Rows, reading: Reading) -> exp.Expression:
    """One aggregate of a group: Table.RowCount(_) COUNT(*); List.Sum, Max, Min, Average and
    StandardDeviation of a column SUM, MAX, MIN, AVG and STDDEV_SAMP; List.Count(List.Distinct
    ([c])) COUNT(DISTINCT c), named where c has a blank in the sample (G1); arithmetic of them
    as it is."""
    if isinstance(part, MValue):
        return constant_hive(part.value)
    if isinstance(part, MOperation) and part.operator in ARITHMETIC:
        return binary(ARITHMETIC[part.operator], aggregate_hive(part.left, rows, reading),
                      aggregate_hive(part.right, rows, reading))
    if not isinstance(part, MCall) or not isinstance(part.function, MName):
        raise Refused("X1", "a Table.Group aggregate file 12 doesn't list")
    name = part.function.name
    if name == "Table.RowCount" and part.args == (MName("_"),):
        return rule_hive("COUNT(*)")
    if name in LIST_AGGREGATES and len(part.args) == 1:
        return hive_call(LIST_AGGREGATES[name], [group_column(part.args[0], rows)])
    distinct = part.args[0] if len(part.args) == 1 else None
    if name == "List.Count" and isinstance(distinct, MCall) and (
            distinct.function == MName("List.Distinct")) and len(distinct.args) == 1:
        return distinct_count(distinct.args[0], rows, reading)
    if name == "List.Median":
        raise Refused("X1", "List.Median has no Hive here")
    raise Refused("X1", f"{name} in a Table.Group isn't an aggregate file 12 lists")


def group_column(part: MPart, rows: Rows) -> exp.Expression:
    """The column a group's aggregate reads, `[c]` or `_[c]`."""
    if isinstance(part, MField) and part.record in (None, MName("_")):
        return query_column(rows, part.name)
    raise Refused("X1", "a Table.Group aggregate reads no column file 12 lists")


def distinct_count(part: MPart, rows: Rows, reading: Reading) -> exp.Expression:
    """List.Count(List.Distinct([c])): COUNT(DISTINCT c), which leaves out NULL where M counts
    it: named where c has a blank in the sample (G1)."""
    column = group_column(part, rows)
    if None in rows.samples.get(part.name, []):
        reading.notes.append(Note(MARK, "G1", reading.where,
                                  f"blank: COUNT(DISTINCT {hive_name(part.name)}) leaves out a "
                                  f"blank, which M's List.Distinct counts, and {part.name} "
                                  "has a blank in the sample"))
    return rule_hive("COUNT(DISTINCT p0)", p0=column)


def indexed_groups(rows: Rows, keys: list[str], aggregate: tuple[str, MPart],
                   reading: Reading) -> Rows:
    """A Table.Group whose one aggregate numbers each group's sorted rows,
    `Table.AddIndexColumn(Table.Sort(_, ..), "n", 1, 1)`: each row kept, its number
    `ROW_NUMBER() OVER (PARTITION BY .. ORDER BY ..)`, for ExpandTableColumn to take (S2)."""
    name, call = aggregate
    inner, index, *numbering = step_arguments(call.args, 2, 5, "Table.AddIndexColumn")
    if not isinstance(inner, MCall) or inner.function != MName("Table.Sort") or (
            inner.args[:1] != (MName("_"),)):
        raise Refused("X1", "Table.AddIndexColumn with no Table.Sort before it numbers rows in "
                            "an order a Hive table doesn't hold")
    order = sort_order(step_arguments(inner.args, 2, 2, "Table.Sort")[1], rows, reading)
    window = exp.Window(this=rule_hive("ROW_NUMBER()"),
                        partition_by=[query_column(rows, key) for key in keys],
                        order=exp.Order(expressions=order), over="OVER")
    columns = copy.deepcopy(rows.columns)
    columns[text_of(index, reading)] = index_hive(window, numbering, reading)
    rows.nested = {name: Nested(columns, dict(rows.samples))}
    rows.columns = {key: query_column(rows, key) for key in keys}
    return rows


def nested_join(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.NestedJoin, by its JoinKind (G2): LeftOuter a LEFT JOIN, Inner a JOIN, RightOuter
    a LEFT JOIN with the tables swapped, FullOuter a FULL OUTER JOIN, LeftAnti `LEFT JOIN u ON
    t.k = u.k WHERE u.k IS NULL`, RightAnti the same swapped; the other table's columns for
    ExpandTableColumn to take. On every column, ready for G3's INTERSECT or EXCEPT."""
    table, keys, other_table, other_keys, name, kind, *_ = step_arguments(
        args, 6, 7, "Table.NestedJoin")
    left, right = rows_of(table, reading), rows_of(other_table, reading)
    keys, other_keys = names_of(keys, reading), names_of(other_keys, reading)
    column, kind = text_of(name, reading), m_name(kind, reading).removeprefix("JoinKind.")
    if kind not in JOIN_KINDS or len(keys) != len(other_keys):
        raise Refused("X1", f"a NestedJoin of JoinKind.{kind} isn't one file 12 lists")
    settle_order(left, reading)
    settle_order(right, reading)
    exact = exact_join(left, right, keys, other_keys, kind)
    if kind.startswith("Right"):
        rows, others = joined_rows(right, left, other_keys, keys, kind, column, reading)
        rows.columns, others = others, rows.columns
    else:
        rows, others = joined_rows(left, right, keys, other_keys, kind, column, reading)
    rows.nested[column] = Nested(others, dict(right.samples))
    rows.exact = exact
    return rows


def joined_rows(base: Rows, other: Rows, keys: list[str], other_keys: list[str], kind: str,
                column: str, reading: Reading) -> tuple[Rows, dict[str, exp.Expression]]:
    """`base` with `other` joined to it on their keys, as `kind` joins them, and `other`'s
    columns, each after its alias. The NestedJoin's new column names the alias of M's second
    table: `other`'s, or for a RightOuter or RightAnti, swapped, `base`'s."""
    allowed = {"joins"}
    if kind != "FullOuter":
        allowed.add("where")
    base = ready_rows(base, reading, allowed)
    other = ready_rows(other, reading, set())
    if kind.startswith("Right"):
        if not base.alias:
            base.alias = free_alias(column, base.taken)
        alias_other(base, other, other.name)
    else:
        alias_other(base, other, column)
    on = all_of([binary(exp.EQ, query_column(base, key), query_column(other, other_key))
                 for key, other_key in zip(keys, other_keys, strict=True)])
    join = exp.Join(this=from_hive(other), on=on)
    if kind == "FullOuter":
        join.set("side", "FULL")
        join.set("kind", "OUTER")
    elif kind != "Inner":
        join.set("side", "LEFT")
    base.joins.append(join)
    if kind.endswith("Anti"):
        base.where.append(rule_hive("p0 IS NULL", p0=query_column(other, other_keys[0])))
    return base, other.columns


def exact_join(left: Rows, right: Rows, keys: list[str], other_keys: list[str],
               kind: str) -> tuple[str, exp.Query, exp.Query] | None:
    """A NestedJoin on every column of both tables, Inner or LeftAnti: the INTERSECT or EXCEPT
    a Table.Distinct makes of it, its column of tables removed (G3), or None."""
    if kind not in ("Inner", "LeftAnti") or left.nested or right.nested or not (
            set(keys) == set(left.columns) and set(other_keys) == set(right.columns)
            and len(keys) == len(left.columns) == len(right.columns)):
        return None
    paired = dict(zip(keys, other_keys, strict=True))
    lined_up = copy.deepcopy(right)
    lined_up.columns = {paired[name]: right.columns[paired[name]] for name in left.columns}
    operation = "INTERSECT" if kind == "Inner" else "EXCEPT"
    return operation, select_of(copy.deepcopy(left)), select_of(lined_up)


def expand_table_column(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.ExpandTableColumn: each column it names of the column of tables, AS its new name
    where its fourth argument gives one (G2)."""
    table, name, names, *new_names = step_arguments(args, 3, 4, "Table.ExpandTableColumn")
    rows = rows_of(table, reading)
    nested = rows.nested.pop(text_of(name, reading), None)
    if nested is None:
        raise Refused("X1", "Table.ExpandTableColumn expands no column of tables a step made")
    taken = names_of(names, reading)
    given = taken
    if new_names:
        given = names_of(new_names[0], reading)
    for old, new in zip(taken, given, strict=True):
        if old not in nested.columns:
            raise Refused("X1", f"it expands {old}, which the joined table doesn't have")
        rows.columns[new] = nested.columns[old].copy()
        if old in nested.samples:
            rows.samples[new] = nested.samples[old]
    return rows


def cross_column(rows: Rows, column: str, body: MPart, reading: Reading) -> Rows:
    """Table.AddColumn(t, "u", each u): every row of u for each row of t, `CROSS JOIN u`, for
    ExpandTableColumn to take (G3)."""
    rows = ready_rows(rows, reading, {"where", "joins"})
    settle_order(rows, reading)
    other = ready_rows(rows_of(body, reading), reading, set())
    settle_order(other, reading)
    alias_other(rows, other, column)
    rows.joins.append(exp.Join(this=from_hive(other), kind="CROSS"))
    rows.nested[column] = Nested(other.columns, dict(other.samples))
    return rows


def combine(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.Combine({a, b}): UNION ALL, each table's columns by name, NULL where it has none
    (G4)."""
    (tables,) = step_arguments(args, 1, 1, "Table.Combine")
    tables = resolved(tables, reading)
    if not isinstance(tables, MList) or not tables.items:
        raise Refused("X1", "Table.Combine of no list of tables")
    parts = []
    for each in tables.items:
        part = rows_of(each, reading)
        settle_order(part, reading)
        parts.append(ready_rows(part, reading, FACETS - {"limit"}))
    names: list[str] = []
    samples: dict[str, list[object]] = {}
    for part in parts:
        if not part.all_known:
            raise Refused("M1", "Table.Combine of a table whose columns aren't known")
        names += [name for name in part.columns if name not in names]
        for name, sample in part.samples.items():
            samples[name] = samples.get(name, []) + sample
    stacked = None
    for part in parts:
        part.columns = {name: lined_up_column(part, name) for name in names}
        stacked = combined_query(stacked, select_of(part))
    return Rows("union", None, {name: column_hive(name) for name in names},
                samples=samples, set_query=stacked)


def lined_up_column(rows: Rows, name: str) -> exp.Expression:
    """A table's column in a Table.Combine, or NULL where it has none of that name."""
    if name in rows.columns:
        return rows.columns[name]
    return exp.Null()


def combined_query(stacked: exp.Query | None, query: exp.Query) -> exp.Query:
    if stacked is None:
        return query
    return exp.union(stacked, query, distinct=False)


def distinct_rows(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.Distinct: SELECT DISTINCT; of a Table.Combine, UNION; of a NestedJoin on every
    column, its column of tables removed, INTERSECT for Inner and EXCEPT for LeftAnti (G3, G4).
    With a column list, refused (X1)."""
    table, *columns = step_arguments(args, 1, 2, "Table.Distinct")
    if columns:
        raise Refused("X1", "Table.Distinct with a column list keeps one row of each value of "
                            "those columns, which file 12 doesn't write")
    rows = rows_of(table, reading)
    names = {name: column_hive(name) for name in rows.columns}
    if rows.exact is not None:
        operation, first, second = rows.exact
        query = exp.intersect(first, second) if operation == "INTERSECT" else exp.except_(
            first, second)
        return Rows(rows.name, None, names, samples=rows.samples, set_query=query)
    if isinstance(rows.set_query, exp.Union) and not rows.set_query.args.get("distinct"):
        stacked = rows.set_query
        while isinstance(stacked, exp.Union):
            stacked.set("distinct", True)
            stacked = stacked.this
        return rows
    rows = ready_rows(rows, reading, FACETS - {"limit"})
    rows.distinct = True
    return rows


def unpivot(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.Unpivot(t, {"a", "b"}, "measure", "amount"): G5's stack of the columns it names
    (`unpivoted_rows`)."""
    return unpivoted_rows(args, reading, others=False)


def unpivot_other_columns(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.UnpivotOtherColumns(t, {"run_id"}, "measure", "amount"): G5's stack of every column
    but those it names (`unpivoted_rows`)."""
    return unpivoted_rows(args, reading, others=True)


def unpivoted_rows(args: tuple[MPart, ...], reading: Reading, others: bool) -> Rows:
    """One SELECT per column turned into rows, stacked with UNION ALL, `'a' AS measure, a AS
    amount`, each `WHERE a IS NOT NULL`, as M drops a null there (G5): the columns the step
    names, or with `others` every other column."""
    table, listed, attribute, value = step_arguments(args, 4, 4, "Table.Unpivot")
    rows = rows_of(table, reading)
    settle_order(rows, reading)
    rows = ready_rows(rows, reading, {"where", "joins"})
    named = names_of(listed, reading)
    kept = [name for name in rows.columns if (name in named) == others]
    turned = [name for name in rows.columns if (name in named) != others]
    attribute, value = text_of(attribute, reading), text_of(value, reading)
    stacked = None
    for name in turned:
        part = copy.deepcopy(rows)
        part.columns = {each: rows.columns[each].copy() for each in kept}
        part.columns[attribute] = exp.Literal.string(name)
        part.columns[value] = rows.columns[name].copy()
        part.where.append(rule_hive("p0 IS NOT NULL", p0=rows.columns[name]))
        stacked = combined_query(stacked, select_of(part))
    if stacked is None:
        raise Refused("X1", "Table.Unpivot turns no column into rows")
    names = [*kept, attribute, value]
    return Rows(rows.name, None, {name: column_hive(name) for name in names},
                set_query=stacked)


def pivot(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.Pivot: a `SUM(CASE WHEN severity = 'high' THEN 1 END) AS high` column per value in
    the sample, THEN v to add up v, NULL where none, GROUP BY the other columns; marked
    "pivot", its columns now fixed (M2)."""
    table, values, attribute, value, *aggregate = step_arguments(args, 4, 5, "Table.Pivot")
    rows = rows_of(table, reading)
    settle_order(rows, reading)
    rows = ready_rows(rows, reading, {"where", "joins"})
    attribute, value = text_of(attribute, reading), text_of(value, reading)
    function = "List.Sum"
    if aggregate:
        function = m_name(aggregate[0], reading)
    if function not in PIVOT_AGGREGATES:
        raise Refused("M2", f"Table.Pivot with {function} isn't one file 12 lists")
    shown = pivot_values(values, attribute, reading)
    keys = [name for name in rows.columns if name not in (attribute, value)]
    counted = exp.Literal.number("1") if function == "List.Count" else query_column(rows, value)
    columns = {key: query_column(rows, key) for key in keys}
    for each in shown:
        case = exp.Case().when(binary(exp.EQ, query_column(rows, attribute),
                                      constant_hive(each)), counted.copy())
        columns[value_text(each)] = hive_call(PIVOT_AGGREGATES[function], [case])
    rows.group = [query_column(rows, key) for key in keys]
    rows.columns = columns
    reading.notes.append(Note(MARK, "M2", reading.where,
                              f"pivot: a column for each value of {attribute} in the sample, "
                              f"{in_words([value_text(each) for each in shown])}; its columns "
                              "are now fixed, so a new value won't get one"))
    return rows


def pivot_values(part: MPart, attribute: str, reading: Reading) -> list[object]:
    """The values a Table.Pivot makes a column of: a list, or List.Distinct(t[c]), each value of
    c in the sample, in order, but a blank."""
    part = resolved(part, reading)
    if isinstance(part, MList):
        return constant_of(part, reading)
    if isinstance(part, MCall) and part.function == MName("List.Distinct") and len(
            part.args) == 1 and isinstance(part.args[0], MField) and part.args[0].record:
        sample = rows_of(part.args[0].record, reading).samples.get(part.args[0].name)
        if sample is None:
            raise Refused("M2", f"Table.Pivot of {attribute}, which has no sample")
        return [each for each in dict.fromkeys(sample) if each is not None]
    raise Refused("M2", "Table.Pivot's values are no list file 12 reads")


# --- Sorting (S1 to S3) ----------------------------------------------------------------------


def sort_rows(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.Sort: an ORDER BY, written where a FirstN or an index uses it (S1, S2), else
    dropped and marked (S3)."""
    table, spec = step_arguments(args, 2, 2, "Table.Sort")
    rows = ready_rows(rows_of(table, reading), reading, FACETS - {"limit"})
    rows.order = sort_order(spec, rows, reading)
    rows.order_used = False
    return rows


def sort_order(part: MPart, rows: Rows, reading: Reading) -> list[exp.Ordered]:
    """A Table.Sort's order: a column's name, or a list of names and `{name, Order.Descending}`
    pairs, each DESC for Order.Descending (S1)."""
    part = resolved(part, reading)
    if isinstance(part, MList) and len(part.items) == 2 and isinstance(
            part.items[0], MValue) and isinstance(part.items[1], MName):
        part = MList((part,))
    items = part.items if isinstance(part, MList) else (part,)
    order = []
    for item in items:
        name, descending = item, False
        if isinstance(item, MList) and len(item.items) == 2:
            name = item.items[0]
            descending = m_name(item.items[1], reading) == "Order.Descending"
        order.append(window_order(query_column(rows, text_of(name, reading)), descending))
    return order


def first_rows(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.FirstN: LIMIT, after the ORDER BY of a Table.Sort before it (S1)."""
    table, count = step_arguments(args, 2, 2, "Table.FirstN")
    number = constant_of(count, reading)
    if not isinstance(number, int) or isinstance(number, bool):
        raise Refused("X1", "Table.FirstN of no whole number isn't a form file 12 lists")
    rows = ready_rows(rows_of(table, reading), reading, FACETS - {"limit"})
    rows.limit = number
    rows.order_used = bool(rows.order)
    return rows


def add_index_column(args: tuple[MPart, ...], reading: Reading) -> Rows:
    """Table.AddIndexColumn(t, "n", 1, 1) after a Table.Sort: `ROW_NUMBER() OVER (ORDER BY ..)
    AS n` (S2); with no Table.Sort before it, refused, NULL in its place (X1)."""
    table, name, *numbering = step_arguments(args, 2, 5, "Table.AddIndexColumn")
    rows = ready_rows(rows_of(table, reading), reading, FACETS - {"limit", "distinct"})
    column = text_of(name, reading)
    if not rows.order:
        rows.columns[column] = refuse_column(reading, column, Refused(
            "X1", "Table.AddIndexColumn with no Table.Sort before it numbers rows in an order "
                  "a Hive table doesn't hold"))
        return rows
    window = exp.Window(this=rule_hive("ROW_NUMBER()"),
                        order=exp.Order(expressions=[each.copy() for each in rows.order]),
                        over="OVER")
    rows.columns[column] = index_hive(window, numbering, reading)
    rows.order_used = True
    return rows


def index_hive(window: exp.Expression, numbering: list[MPart],
               reading: Reading) -> exp.Expression:
    """An index from a ROW_NUMBER(): as it is where it starts at 1 and counts by 1, else
    `(ROW_NUMBER() OVER (..) - 1) * step + start`; M starts one at 0 by default."""
    start, step = 0, 1
    if numbering:
        start = constant_of(numbering[0], reading)
    if len(numbering) > 1:
        step = constant_of(numbering[1], reading)
    if not isinstance(start, int) or not isinstance(step, int):
        raise Refused("X1", "Table.AddIndexColumn counting by no whole number")
    if (start, step) == (1, 1):
        return window
    return rule_hive("(p0 - 1) * p1 + p2", p0=window, p1=constant_hive(step),
                     p2=constant_hive(start))


# Each Table function file 12 lists, by its M name, and the function that writes its step.
TABLE_STEPS: dict[str, Callable[[tuple[MPart, ...], Reading], Rows]] = {
    "Table.SelectRows": select_rows, "Table.SelectColumns": select_columns,
    "Table.RemoveColumns": remove_columns, "Table.RenameColumns": rename_columns,
    "Table.ReorderColumns": reorder_columns, "Table.DuplicateColumn": duplicate_column,
    "Table.TransformColumnTypes": types_buffer_or_headers,
    "Table.Buffer": types_buffer_or_headers, "Table.PromoteHeaders": types_buffer_or_headers,
    "Table.AddColumn": add_column,
    "Table.TransformColumns": transform_columns, "Table.ReplaceValue": replace_value,
    "Table.Group": group_rows, "Table.NestedJoin": nested_join,
    "Table.ExpandTableColumn": expand_table_column, "Table.Combine": combine,
    "Table.Distinct": distinct_rows, "Table.Unpivot": unpivot,
    "Table.UnpivotOtherColumns": unpivot_other_columns, "Table.Pivot": pivot,
    "Table.Sort": sort_rows,
    "Table.FirstN": first_rows, "Table.AddIndexColumn": add_index_column,
    "Table.FillDown": fill_down, "Table.FillUp": fill_down,
}
