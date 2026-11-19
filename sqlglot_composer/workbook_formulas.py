"""Each formula of a Formula workbook's Table written as Hive, by Copilot file 11's rules
(Toolbox 8.9, ticket 04; ADR 0016).

A formula is read as the workbook saves it, `=job_runs[[#This Row],[duration_mins]]/60`, or as
a person types it, `=[@duration_mins]/60`, into a small tree of its parts (`read_formula`).
Each part is then written as sqlglot's tree of the Hive that file 11's rule with its ID gives:
converted (F1 to F10, I1 to I6, V1, V2), converted with its mark (M1 to M5), or refused (X1),
NULL in its place and named, with the names in the Hive written as N1 and N2 say.
`table_query` writes one Table's SELECT: each typed column read from what the Table reads, each
formula column by its rule, and each lookup and total it needs as a join.

`workbook_hive.py` gives each piece its role and puts each final together from these. Each
function a formula calls is written by its entry in the Book's `functions`, which starts as
`FUNCTIONS` here: a file adding more (file 12's whole-column totals, GETPIVOTDATA) gives its
own entries, which `workbook_hive.py` puts beside these.
"""

from __future__ import annotations

import datetime
import functools
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field, replace

from sqlglot import exp

from .shared import in_words
from .workbook_reader import TYPED, Column, Piece, Table, Workbook
from .writing import read_hive

# What a Note is, in Copilot file 15's map's words.
WRITTEN_IN = "written in"
TYPED_OVER = "typed over"
MARK = "mark"
REFUSED = "refused"
LEFT_ALONE = "left alone"
TO_FILL_IN = "to fill in"
EXCEL_TABLE = "Excel Table"
# The two Tables of settings a Formula workbook holds (file 15's P10), by their names.
PARAMETERS = "Parameters"
KEYS = "Keys"
# A name file 11's N1 keeps as it is: letters, digits and `_`.
PLAIN_NAME = re.compile(r"[A-Za-z0-9_]+")
# Excel's prefixes on its newer functions, read past (file 11's Terms).
PREFIXES = re.compile(r"^(?:_xlfn\.|_xlws\.)+", re.IGNORECASE)
# A date written in a cell as text: ISO, as 2026-09-24, or 8 digits, as 20260911 (file 11's M3).
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
TEXT_DATE = re.compile(r"(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])")
# The pieces of a formula, as `read_formula` reads them, in the order they are tried.
FORMULA_TOKEN = re.compile(r"""
    (?P<number>\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+)
  | (?P<cell>(?:(?:'(?:[^']|'')+'|[A-Za-z_][\w.]*)!)?\$?[A-Z]{1,3}\$?\d+
        (?::\$?[A-Z]{1,3}\$?\d+)?(?![\w(\[.!]))
  | (?P<word>[A-Za-z_\\][\w.\\]*)
  | (?P<operator><>|<=|>=|[-+*/^&=<>%(),])
  | (?P<other>.)
""", re.VERBOSE)
COMPARISONS = {"=": exp.EQ, "<>": exp.NEQ, "<": exp.LT, ">": exp.GT, "<=": exp.LTE,
               ">=": exp.GTE}
ARITHMETIC = {"+": exp.Add, "-": exp.Sub, "*": exp.Mul, "/": exp.Div}
# How tightly each of Hive's operators holds its sides, so a side is bracketed only where it
# must be: `(a + b) * c`, never `a + (b * c)`.
PRECEDENCE = {exp.Or: 1, exp.And: 2, exp.Not: 3, exp.EQ: 4, exp.NEQ: 4, exp.LT: 4, exp.GT: 4,
              exp.LTE: 4, exp.GTE: 4, exp.Is: 4, exp.Like: 4, exp.In: 4, exp.Add: 5,
              exp.Sub: 5, exp.Mul: 6, exp.Div: 6, exp.Neg: 7}
# The functions file 11's X1 refuses by name, with why.
NAMED_REFUSALS = {
    "INDIRECT": "INDIRECT reads a cell by its address, which a table has no place for",
    "OFFSET": "OFFSET reads cells by their place on the sheet, and a table's rows have none",
    "RAND": "RAND gives a new number each time it is worked out",
    "RANDBETWEEN": "RANDBETWEEN gives a new number each time it is worked out",
    "ROW": "ROW() reads the sheet's row order, and a table's rows have none",
    "ROWS": "ROWS reads the sheet's row order, and a table's rows have none",
    "MEDIAN": "MEDIAN has no Hive here",
    "FILTER": "FILTER spills an array over the sheet",
    "UNIQUE": "UNIQUE spills an array over the sheet",
    "SORT": "SORT spills an array over the sheet",
    "SORTBY": "SORTBY spills an array over the sheet",
    "SEQUENCE": "SEQUENCE spills an array over the sheet",
    "NETWORKDAYS": "NETWORKDAYS needs a calendar of working days",
    "LAMBDA": "a LAMBDA is a function of the workbook's own",
    "LET": "LET names values inside a formula, which file 11 doesn't list",
}
# The -IF(S) forms (file 11's F9), each by the aggregate it is.
IFS_FORMS = {"SUMIFS": "SUM", "COUNTIFS": "COUNT", "AVERAGEIFS": "AVG", "MAXIFS": "MAX",
             "MINIFS": "MIN", "SUMIF": "SUM", "COUNTIF": "COUNT", "AVERAGEIF": "AVG"}
# Excel's date letters in TEXT's format, as Hive's DATE_FORMAT writes them (file 11's F6).
DATE_LETTERS = (("yyyy", "yyyy"), ("yy", "yy"), ("mmmm", "MMMM"), ("mmm", "MMM"),
                ("mm", "MM"), ("m", "M"), ("dddd", "EEEE"), ("ddd", "EEE"), ("dd", "dd"),
                ("d", "d"))


@dataclass(frozen=True)
class Note:
    """One thing a workbook's map names (file 15's Output): its kind, WRITTEN_IN, TYPED_OVER,
    MARK, REFUSED, LEFT_ALONE or TO_FILL_IN; the rule of Copilot file 11, 12 or 15 that gives
    it, such as "M1"; where it is, such as `job_runs[hours]`; and what it is, and why."""

    kind: str
    rule: str
    where: str
    text: str


class Refused(Exception):
    """A formula, or a part of one, with no Hive by file 11's rules: the rule that refuses it,
    and why, in a few words."""

    def __init__(self, rule: str, why: str) -> None:
        super().__init__(why)
        self.rule = rule
        self.why = why


# --- A formula, read into its tree ----------------------------------------------------------


@dataclass(frozen=True)
class FormulaPart:
    """One part of a formula, read into its tree."""


@dataclass(frozen=True)
class Constant(FormulaPart):
    """A number, a text, or TRUE or FALSE, as the formula writes it."""

    value: str | int | float | bool


@dataclass(frozen=True)
class ThisRow(FormulaPart):
    """One column of the same row, `[@units]` or `sales[[#This Row],[units]]`; its Table is ""
    where the formula doesn't name it."""

    table: str
    column: str


@dataclass(frozen=True)
class WholeColumn(FormulaPart):
    """A Table's whole column, `sales[units]`."""

    table: str
    column: str


@dataclass(frozen=True)
class WholeTable(FormulaPart):
    """A whole Table, as in `VLOOKUP(k, jobs, 2, FALSE)`."""

    table: str


@dataclass(frozen=True)
class TablePart(FormulaPart):
    """A part of a Table read by its place, such as its headers, `t[[#Headers],[x]]`."""

    table: str
    text: str


@dataclass(frozen=True)
class CellAddress(FormulaPart):
    """A cell or range by its address, such as `Summary!$C$2`."""

    text: str


@dataclass(frozen=True)
class Name(FormulaPart):
    """A name: a defined name, or a Table's."""

    name: str


@dataclass(frozen=True)
class Call(FormulaPart):
    """A function called, its name in capitals with Excel's prefix read past, and its
    arguments."""

    name: str
    args: tuple[FormulaPart, ...]


@dataclass(frozen=True)
class Operation(FormulaPart):
    """An operator between two parts, such as `+`, `&` or `<>`."""

    operator: str
    left: FormulaPart
    right: FormulaPart


@dataclass(frozen=True)
class Negative(FormulaPart):
    """A part with `-` before it."""

    operand: FormulaPart


@dataclass(frozen=True)
class Percent(FormulaPart):
    """A part with `%` after it."""

    operand: FormulaPart


@dataclass(frozen=True)
class Omitted(FormulaPart):
    """An argument left empty, as in `IF(a,,b)`."""


@dataclass(frozen=True)
class AnyOf(FormulaPart):
    """The values two -IFS forms added match on in one place (file 11's I2), as one form's
    condition: `s IN ('x', 'y')`."""

    values: tuple[Constant, ...]


def read_formula(formula: str) -> FormulaPart:
    """A formula's tree, read from its text with or without its "=", Excel's operators in
    Excel's order: `-` before a part, then `%`, `^`, `*` and `/`, `+` and `-`, `&`, and the
    comparisons. A formula that can't be read is refused."""
    reader = FormulaReader(formula_tokens(formula.removeprefix("=")))
    part = reader.comparison()
    if reader.at < len(reader.tokens):
        raise Refused("X1", f"its formula can't be read past {reader.tokens[reader.at][1]}")
    return part


def formula_tokens(formula: str) -> list[tuple[str, str]]:
    """A formula's pieces in order, each as its kind and its text: a number, a text, a cell's
    address, a word (a name, or a function's before its "("), a Table's part in brackets, or an
    operator."""
    tokens = []
    at = 0
    while at < len(formula):
        if formula[at].isspace():
            at += 1
        elif formula[at] == '"':
            end = _text_end(formula, at)
            tokens.append(("text", formula[at + 1:end].replace('""', '"')))
            at = end + 1
        elif formula[at] == "[":
            end = _bracket_end(formula, at)
            tokens.append(("structured", formula[at:end]))
            at = end
        else:
            found = FORMULA_TOKEN.match(formula, at)
            kind, text = found.lastgroup, found.group()
            at = found.end()
            if kind == "word" and formula.startswith("[", at):
                end = _bracket_end(formula, at)
                kind, text = "structured", text + formula[at:end]
                at = end
            tokens.append((kind, text))
    return tokens


def _text_end(formula: str, at: int) -> int:
    """Where the text starting with the `"` at `at` ends: its closing `"`, past each `""`."""
    at += 1
    while at < len(formula):
        if formula.startswith('""', at):
            at += 2
        elif formula[at] == '"':
            return at
        else:
            at += 1
    raise Refused("X1", "its formula has a text with no closing quote")


def _bracket_end(formula: str, at: int) -> int:
    """Just past the `]` that closes the `[` at `at`, past each `'`-escaped bracket."""
    depth = 0
    while at < len(formula):
        if formula[at] == "'":
            at += 2
            continue
        if formula[at] == "[":
            depth += 1
        elif formula[at] == "]":
            depth -= 1
            if depth == 0:
                return at + 1
        at += 1
    raise Refused("X1", "its formula has a [ with no ] to close it")


class FormulaReader:
    """Reads one formula's pieces into its tree, one level of Excel's operators a method."""

    def __init__(self, tokens: list[tuple[str, str]]) -> None:
        self.tokens = tokens
        self.at = 0

    def peek(self) -> str:
        """The next piece's text if it is an operator, else ""."""
        if self.at < len(self.tokens) and self.tokens[self.at][0] == "operator":
            return self.tokens[self.at][1]
        return ""

    def take(self) -> tuple[str, str]:
        """The next piece, taken; past the end, a refusal."""
        if self.at >= len(self.tokens):
            raise Refused("X1", "its formula ends where it needs more")
        token = self.tokens[self.at]
        self.at += 1
        return token

    def comparison(self) -> FormulaPart:
        part = self.concatenation()
        while self.peek() in COMPARISONS:
            part = Operation(self.take()[1], part, self.concatenation())
        return part

    def concatenation(self) -> FormulaPart:
        part = self.addition()
        while self.peek() == "&":
            part = Operation(self.take()[1], part, self.addition())
        return part

    def addition(self) -> FormulaPart:
        part = self.multiplication()
        while self.peek() in ("+", "-"):
            part = Operation(self.take()[1], part, self.multiplication())
        return part

    def multiplication(self) -> FormulaPart:
        part = self.power()
        while self.peek() in ("*", "/"):
            part = Operation(self.take()[1], part, self.power())
        return part

    def power(self) -> FormulaPart:
        part = self.unary()
        while self.peek() == "^":
            part = Operation(self.take()[1], part, self.unary())
        return part

    def unary(self) -> FormulaPart:
        if self.peek() == "-":
            self.take()
            return Negative(self.unary())
        if self.peek() == "+":
            self.take()
            return self.unary()
        part = self.primary()
        while self.peek() == "%":
            self.take()
            part = Percent(part)
        return part

    def primary(self) -> FormulaPart:
        kind, text = self.take()
        if kind == "number":
            return Constant(float(text) if re.search(r"[.eE]", text) else int(text))
        if kind == "text":
            return Constant(text)
        if kind == "structured":
            return structured_part(text)
        if kind == "cell":
            return CellAddress(text)
        if kind == "word":
            return self.word(text)
        if text == "(":
            part = self.comparison()
            self.closing()
            return part
        raise Refused("X1", f"its formula holds {text}, which file 11 doesn't list")

    def word(self, text: str) -> FormulaPart:
        """A word: a function called, TRUE or FALSE, or a name."""
        if self.peek() == "(":
            self.take()
            return Call(PREFIXES.sub("", text).upper(), self.arguments())
        if text.upper() in ("TRUE", "FALSE"):
            return Constant(text.upper() == "TRUE")
        return Name(text)

    def arguments(self) -> tuple[FormulaPart, ...]:
        """A function's arguments, after its "(" up to its ")"."""
        args: list[FormulaPart] = []
        if self.peek() == ")":
            self.take()
            return ()
        while True:
            if self.peek() in (",", ")"):
                args.append(Omitted())
            else:
                args.append(self.comparison())
            _, text = self.take()
            if text == ")":
                return tuple(args)
            if text != ",":
                raise Refused("X1", f"its formula holds {text} where a , or ) goes")

    def closing(self) -> None:
        if self.take()[1] != ")":
            raise Refused("X1", "its formula has a ( with no ) to close it")


def structured_part(text: str) -> FormulaPart:
    """A Table's part in brackets, `t[x]`, `t[[#This Row],[x]]`, `[@x]` or `[@[A b]]`, as the
    part it is."""
    table, _, inside = text.partition("[")
    inside = inside[:-1]
    if inside.startswith("@"):
        return ThisRow(table, _bracketed_column_name(inside[1:]))
    items = _bracket_items(inside)
    specials = [item for item in items if item.startswith("#")]
    columns = [item for item in items if not item.startswith("#")]
    part: FormulaPart = TablePart(table, text)
    if not items or (specials == ["#Data"] and not columns):
        part = WholeTable(table)
    elif len(columns) != 1 or ":" in columns[0]:
        part = TablePart(table, text)
    elif specials == ["#This Row"]:
        part = ThisRow(table, columns[0])
    elif specials in ([], ["#Data"]):
        part = WholeColumn(table, columns[0])
    return part


def _bracket_items(inside: str) -> list[str]:
    """The items of a Table's part between its outer brackets, each without its own brackets:
    `[#This Row],[x]` is `#This Row` and `x`, and `x` alone is `x`."""
    if not inside.startswith("["):
        return [_bracketed_column_name(inside)] if inside else []
    items = []
    at = 0
    while at < len(inside):
        if inside[at] == "[":
            end = _bracket_end(inside, at)
            items.append(_bracketed_column_name(inside[at:end]))
            at = end
        else:
            at += 1
    return items


def _bracketed_column_name(text: str) -> str:
    """A column's name as a Table's part writes it, without its brackets or Excel's `'`
    escapes."""
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    return re.sub(r"'(.)", r"\1", text)


def parts_of(part: FormulaPart) -> Iterator[FormulaPart]:
    """A part, then each part inside it, at any depth, in the order the formula writes them."""
    yield part
    inner: tuple[FormulaPart, ...] = ()
    if isinstance(part, Call):
        inner = part.args
    elif isinstance(part, Operation):
        inner = (part.left, part.right)
    elif isinstance(part, (Negative, Percent)):
        inner = (part.operand,)
    for each in inner:
        yield from parts_of(each)


# --- What a formula reads ------------------------------------------------------------------


@dataclass
class Book:
    """What each formula of a workbook can read: the workbook, the database its sources are in
    (`<database>` for the person to fill in, N1), the function each name calls, how each piece
    is read in a FROM, by its Piece (a source as `<database>.<table>`, a step by its CTE's
    name), and what the map names, as it is found."""

    workbook: Workbook
    database: str
    functions: dict[str, Callable[[Call, Place], exp.Expression]]
    reads: dict[Piece, exp.Expression] = field(default_factory=dict)
    notes: list[Note] = field(default_factory=list)


@dataclass
class Lookup:
    """A LEFT JOIN of another Table on one of its columns (file 11's F8): its alias, the Table,
    the column matched, and the Hive of this row's key."""

    alias: str
    table: Table
    column: str
    key: exp.Expression


@dataclass
class Totals:
    """A LEFT JOIN of another Table's totals by group (file 11's F9): its alias, the Table,
    each column grouped on with the Hive of this row's value it matches, the WHERE of its
    conditions, and each total, named."""

    alias: str
    table: Table
    keys: list[tuple[str, exp.Expression]]
    where: exp.Expression | None
    totals: list[exp.Alias] = field(default_factory=list)


@dataclass
class TableQuery:
    """One Table's SELECT as it is written: the Table, the Book, the alias its FROM has, every
    alias taken in it, its joins, each formula column's Hive once written (None once refused),
    the formula columns being written, for a loop between them, and what its map names."""

    table: Table
    book: Book
    alias: str
    taken: set[str]
    joins: list[Lookup | Totals] = field(default_factory=list)
    written: dict[str, exp.Expression | None] = field(default_factory=dict)
    writing: list[str] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)


@dataclass
class Place:
    """Where one formula is written: its Table's SELECT, its column's header, the marks it has
    made so far, and the Table whose whole columns read as one row's cells, inside SUMPRODUCT
    or an -IFS form."""

    query: TableQuery
    column: str
    marks: list[Note]
    row_table: str = ""


def tables_of(workbook: Workbook) -> dict[str, Table]:
    """Each Table of the workbook, by its name in lower case, as Excel matches it."""
    found = {}
    for sheet in workbook.sheets:
        for table in sheet.tables:
            found[table.name.lower()] = table
    return found


def table_named(name: str, place: Place) -> Table:
    """The Table a formula names; "" is its own. A name no Table has is refused."""
    if not name:
        return place.query.table
    found = tables_of(place.query.book.workbook).get(name.lower())
    if found is None:
        raise Refused("X1", f"it reads {name}, which is no Table of the workbook")
    return found


def is_own(name: str, place: Place) -> bool:
    return not name or name.lower() == place.query.table.name.lower()


def column_named(table: Table, header: str) -> Column | None:
    """A Table's column by its header, as Excel matches it, whatever its case."""
    for column in table.columns:
        if column.header.lower() == header.lower():
            return column
    return None


def hive_name(name: str) -> str:
    """A Table's or header's name as the Hive writes it: a plain name as it is (N1), any other
    in snake case in brackets, for the person to fill in (N2): `Unit Price` is
    `<unit_price>`."""
    if PLAIN_NAME.fullmatch(name):
        return name
    return "<" + re.sub(r"[^0-9a-z]+", "_", name.lower()).strip("_") + ">"


def identifier(name: str) -> exp.Identifier:
    """The Hive identifier of a name as `hive_name` writes it, never quoted, so a `<...>`
    stays one for the person to fill in."""
    return exp.Identifier(this=hive_name(name), quoted=False)


def column_hive(header: str, alias: str = "") -> exp.Column:
    """A column read by its header, after its table's alias where one is given."""
    if alias:
        return exp.Column(this=identifier(header), table=exp.Identifier(this=alias))
    return exp.Column(this=identifier(header))


def constant_hive(value: object) -> exp.Expression:
    """A value from the workbook as Hive: NULL, TRUE or FALSE, a number, or a text, a date as
    its ISO text."""
    if value is None:
        return exp.Null()
    if isinstance(value, bool):
        return exp.Boolean(this=value)
    if isinstance(value, (int, float)):
        return exp.Literal.number(_written_number(value))
    if isinstance(value, datetime.datetime):
        return exp.Literal.string(value.date().isoformat())
    return exp.Literal.string(str(value))


def _written_number(value: int | float) -> str:
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e15:
        return str(int(value))
    return str(value)


def new_alias(name: str, taken: set[str]) -> str:
    """A short alias for a table, taken: the first letter of its name's last word, as file
    15's W1 writes `job_runs r`, else of its first, else that letter and a number."""
    words = re.findall(r"[a-z]+", name.lower()) or ["t"]
    for letter in (words[-1][0], words[0][0]):
        if letter not in taken:
            taken.add(letter)
            return letter
    number = 2
    while f"{words[-1][0]}{number}" in taken:
        number += 1
    taken.add(f"{words[-1][0]}{number}")
    return f"{words[-1][0]}{number}"


# --- Hive from a rule's text ----------------------------------------------------------------


@functools.cache
def _rule_tree(text: str) -> exp.Expression:
    return read_hive(f"SELECT {text}")[0].expressions[0]


def written(text: str, **parts: exp.Expression) -> exp.Expression:
    """The Hive of a rule as file 11 writes it, such as `SUBSTR(p0, 1, p1)`, each placeholder
    column in it, p0, p1 and so on, replaced by its part, bracketed where an operator holds
    it. sqlglot reads the rule's text, so the tree is the one it reads the same Hive into."""
    def put(node: exp.Expression) -> exp.Expression:
        if isinstance(node, exp.Column) and not node.table and node.name in parts:
            part = parts[node.name].copy()
            if isinstance(node.parent, (exp.Binary, exp.Not, exp.Neg)):
                return bracketed(part, type(node.parent))
            return part
        return node
    return _rule_tree(text).transform(put)


def hive_call(name: str, args: list[exp.Expression]) -> exp.Expression:
    """Hive's function `name` called on `args`, as sqlglot reads `NAME(a, b)`."""
    places = ", ".join(f"p{number}" for number in range(len(args)))
    parts = {f"p{number}": arg for number, arg in enumerate(args)}
    return written(f"{name}({places})", **parts)


def bracketed(side: exp.Expression, holder: type[exp.Expression],
              right: bool = False) -> exp.Expression:
    """`side` as an operator `holder` holds it: in brackets where it holds its own sides less
    tightly, or as tightly on the right but for `+`, `*`, AND and OR, which may chain."""
    inner = PRECEDENCE.get(type(side))
    outer = PRECEDENCE.get(holder)
    if inner is None or outer is None:
        return side
    chains = type(side) is holder and holder in (exp.Add, exp.Mul, exp.And, exp.Or)
    if inner < outer or (right and inner == outer and not chains):
        return exp.Paren(this=side)
    return side


def binary(kind: type[exp.Expression], left: exp.Expression,
           right: exp.Expression) -> exp.Expression:
    """Two sides joined by Hive's operator `kind`, each bracketed where it must be."""
    return kind(this=bracketed(left, kind), expression=bracketed(right, kind, right=True))


def all_of(conditions: list[exp.Expression]) -> exp.Expression:
    """Conditions joined with AND (file 11's F2, I2)."""
    joined = conditions[0]
    for condition in conditions[1:]:
        joined = binary(exp.And, joined, condition)
    return joined


# --- A Table's SELECT -----------------------------------------------------------------------


def table_query(table: Table, base: exp.Expression, book: Book) -> exp.Select:
    """A Table's SELECT, its columns in the Table's order: each typed column read from `base`,
    what the Table reads (`<database>.<table>`, a step's CTE, or a query's or a summary's
    rows), each formula column by file 11's rule or `NULL AS` its header, and each join its
    formulas need. What its map names goes into the Book's notes."""
    taken: set[str] = set()
    query = TableQuery(table, book, new_alias(table.name, taken), taken)
    for column in table.columns:
        if column.kind != TYPED and column.header not in query.written:
            write_formula_column(column, query)
    columns = [_select_column(column, query) for column in table.columns]
    _drop_unread_joins(query, columns)
    select = exp.select(*columns).from_(_aliased(base, query.alias))
    for join in query.joins:
        select = select.join(_join_hive(join, book))
    if not query.joins and isinstance(base, exp.Table):
        select = _without_alias(select, query.alias)
    book.notes += query.notes
    return select


def _select_column(column: Column, query: TableQuery) -> exp.Expression:
    if column.kind == TYPED:
        return column_hive(column.header, query.alias)
    expression = query.written[column.header]
    if expression is None:
        expression = exp.Null()
    if isinstance(expression, exp.Column) and expression.name == hive_name(column.header):
        return expression
    return exp.alias_(expression, identifier(column.header))


def _aliased(base: exp.Expression, alias: str) -> exp.Expression:
    """What a SELECT reads, as its FROM writes it, after its alias."""
    if isinstance(base, exp.Table):
        held = base.copy()
        held.set("alias", exp.TableAlias(this=exp.Identifier(this=alias)))
        return held
    return exp.Subquery(this=base.copy(), alias=exp.TableAlias(this=exp.Identifier(this=alias)))


def _without_alias(select: exp.Select, alias: str) -> exp.Select:
    """A SELECT that joins nothing, written without its FROM's alias, as file 11's W1 is."""
    def plain(node: exp.Expression) -> exp.Expression:
        if isinstance(node, exp.Column) and node.table == alias:
            return exp.Column(this=node.this.copy())
        return node
    select = select.transform(plain)
    select.find(exp.From).this.set("alias", None)
    return select


def _join_hive(join: Lookup | Totals, book: Book) -> exp.Join:
    """A join a formula needs: a lookup's LEFT JOIN on its key (F8), or a LEFT JOIN of a
    Table's totals on its groups, or a CROSS JOIN of totals with no group (F9, I3)."""
    read = book.reads[Piece(EXCEL_TABLE, join.table.name)]
    if isinstance(join, Lookup):
        on = binary(exp.EQ, join.key, column_hive(join.column, join.alias))
        return exp.Join(this=_aliased(read, join.alias), side="LEFT", on=on)
    groups = [column_hive(name) for name, _ in join.keys]
    source = read.copy()
    if not isinstance(read, exp.Table):
        source = _aliased(read, join.table.name[0].lower())
    totals = exp.select(*groups, *join.totals).from_(source)
    if join.where is not None:
        totals = totals.where(join.where)
    if not groups:
        return exp.Join(this=_aliased(totals, join.alias), kind="CROSS")
    totals = totals.group_by(*[group.copy() for group in groups])
    on = all_of([binary(exp.EQ, value, column_hive(name, join.alias))
                 for name, value in join.keys])
    return exp.Join(this=_aliased(totals, join.alias), side="LEFT", on=on)


def _drop_unread_joins(query: TableQuery, columns: list[exp.Expression]) -> None:
    """Leave out each join no column reads, such as one a refused formula added, and each
    total no column reads; a lookup whose key reads another join keeps that one."""
    read = _join_aliases_read(columns)
    kept: list[Lookup | Totals] = []
    for join in reversed(query.joins):
        if join.alias not in read:
            continue
        kept.insert(0, join)
        if isinstance(join, Lookup):
            read |= _join_aliases_read([join.key])
        else:
            read |= _join_aliases_read([value for _, value in join.keys])
            names = _columns_read(columns, join.alias)
            join.totals = [total for total in join.totals if total.alias in names]
    query.joins = kept


def _join_aliases_read(expressions: list[exp.Expression]) -> set[str]:
    found = set()
    for expression in expressions:
        found |= {column.table for column in expression.find_all(exp.Column) if column.table}
    return found


def _columns_read(expressions: list[exp.Expression], alias: str) -> set[str]:
    found = set()
    for expression in expressions:
        found |= {column.name for column in expression.find_all(exp.Column)
                  if column.table == alias}
    return found


# --- A formula column -----------------------------------------------------------------------


def write_formula_column(column: Column, query: TableQuery) -> None:
    """Write one formula column's Hive into `query.written`: its formula by its rule, each
    value typed over it in a CASE (V1, V2); or, refused, None, named with why (X1)."""
    query.writing.append(column.header)
    place = Place(query, column.header, [])
    where = f"{query.table.name}[{column.header}]"
    try:
        expression = _formula_column_hive(column, place)
    except Refused as refusal:
        query.written[column.header] = None
        query.notes.append(Note(REFUSED, refusal.rule, where, f"NULL in its place: "
                                f"{refusal.why}"))
        return
    finally:
        query.writing.pop()
    query.written[column.header] = expression
    query.notes += list(dict.fromkeys(place.marks))


def _formula_column_hive(column: Column, place: Place) -> exp.Expression:
    formulas = [cell for cell in column.cells if is_formula_text(cell)]
    if any(formula != formulas[0] for formula in formulas):
        raise Refused("X1", "its rows hold different formulas")
    part = read_formula(formulas[0])
    check_named_refusals(part, place)
    expression = hive_of(part, place)
    typed = [(row, cell) for row, cell in enumerate(column.cells) if not is_formula_text(cell)]
    if typed:
        expression = typed_over_hive(column, typed, expression, place)
    return expression


def is_formula_text(cell: object) -> bool:
    return isinstance(cell, str) and cell.startswith("=")


def check_named_refusals(part: FormulaPart, place: Place) -> None:
    """Refuse a formula holding anything file 11's X1 refuses by name, before the rest of it
    is read: the first such part it writes names it."""
    names = place.query.book.workbook.defined_names
    for each in parts_of(part):
        if isinstance(each, Call) and each.name in NAMED_REFUSALS:
            raise Refused("X1", NAMED_REFUSALS[each.name])
        if isinstance(each, Call) and _defined_name(each.name, names) is not None:
            raise Refused("X1", f"{each.name} is a defined name holding a formula, "
                                f"{_defined_name(each.name, names)}")
        if isinstance(each, CellAddress):
            raise Refused("X1", f"it reads {each.text.replace('$', '')}, a cell outside a "
                                "Table, by its address")
        if isinstance(each, ThisRow) and is_own(each.table, place) and (
                each.column.lower() == place.column.lower()):
            raise Refused("X1", "circular: it reads its own column")


def _defined_name(name: str, names: dict[str, str]) -> str | None:
    for defined, refers_to in names.items():
        if defined.lower() == name.lower():
            return refers_to
    return None


def this_row(header: str, place: Place) -> exp.Expression:
    """A column of the formula's own row: a typed column as its Table reads it, a formula
    column as its own Hive, written in its place (file 11's I6: never a name AS made)."""
    table = place.query.table
    column = column_named(table, header)
    if column is None:
        raise Refused("X1", f"it reads [{header}], which {table.name} doesn't have")
    if column.kind == TYPED:
        return column_hive(column.header, place.query.alias)
    query = place.query
    if column.header in query.writing:
        raise Refused("X1", f"circular: it reads {column.header}, which reads it")
    if column.header not in query.written:
        write_formula_column(column, query)
    expression = query.written[column.header]
    if expression is None:
        raise Refused("X1", f"it reads {column.header}, which is refused")
    return expression.copy()


def typed_over_hive(column: Column, typed: list[tuple[int, object]],
                    expression: exp.Expression, place: Place) -> exp.Expression:
    """A formula column with values typed over it: a CASE on each such row, matched on the
    columns its Keys row names (V1), or else on every typed column of the row, said (V2)."""
    table = place.query.table
    keys = _key_columns(table, place)
    where = f"{table.name}[{column.header}]"
    if not keys:
        keys = [other.header for other in table.columns if other.kind == TYPED]
        place.marks.append(Note(MARK, "V2", where, "no Keys row names its Table, so each "
                                "typed-over value is matched on every typed column of its "
                                "row"))
    case = exp.Case()
    for row, value in typed:
        match = all_of([_matched(key, row, place) for key in keys])
        case = case.when(match, constant_hive(value))
        shown = in_words([f"{key} is {_cell_of(table, key, row)}" for key in keys])
        place.query.notes.append(Note(TYPED_OVER, "V1", where,
                                      f"{_shown(value)} typed over its formula where {shown}"))
    return case.else_(expression)


def _key_columns(table: Table, place: Place) -> list[str]:
    """The columns the Keys Table's row for `table` names, each one the Table has."""
    keys = tables_of(place.query.book.workbook).get(KEYS.lower())
    if keys is None or len(keys.columns) < 2:
        return []
    for name, columns in zip(keys.columns[0].cells, keys.columns[1].cells, strict=True):
        if str(name or "").lower() == table.name.lower():
            found = [column_named(table, key.strip()) for key in str(columns).split(",")]
            return [column.header for column in found if column is not None]
    return []


def _cell_of(table: Table, header: str, row: int) -> object:
    return column_named(table, header).cells[row]


def _matched(header: str, row: int, place: Place) -> exp.Expression:
    value = _cell_of(place.query.table, header, row)
    if value is None:
        return written("p0 IS NULL", p0=this_row(header, place))
    return binary(exp.EQ, this_row(header, place), constant_hive(value))


def _shown(value: object) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


# --- Each part of a formula ----------------------------------------------------------------


def hive_of(part: FormulaPart, place: Place) -> exp.Expression:
    """A part of a formula as the Hive its rule in file 11 gives, or refused."""
    if isinstance(part, Constant):
        return constant_hive(part.value)
    if isinstance(part, ThisRow):
        if not is_own(part.table, place):
            raise Refused("X1", f"it reads one row of {part.table} by its place")
        return this_row(part.column, place)
    if isinstance(part, WholeColumn):
        return _whole_column_hive(part, place)
    if isinstance(part, Call):
        return _call_hive(part, place)
    if isinstance(part, Operation):
        return operation_hive(part, place)
    return _other_part_hive(part, place)


def _other_part_hive(part: FormulaPart, place: Place) -> exp.Expression:
    """A part with `-` before it or `%` after it, or a name; any other part is refused."""
    if isinstance(part, Negative):
        return exp.Neg(this=bracketed(hive_of(part.operand, place), exp.Neg))
    if isinstance(part, Percent):
        return binary(exp.Div, hive_of(part.operand, place), exp.Literal.number("100"))
    if isinstance(part, Name):
        return _name_hive(part, place)
    raise Refused("X1", _unread_part(part))


def _unread_part(part: FormulaPart) -> str:
    if isinstance(part, WholeTable):
        return f"it reads the whole Table {part.table}, which spills an array"
    if isinstance(part, TablePart):
        return f"it reads {part.text}, a part of a Table by its place"
    if isinstance(part, AnyOf):
        return "it matches several values outside an -IFS form"
    return "an argument is left empty"


def _whole_column_hive(part: WholeColumn, place: Place) -> exp.Expression:
    """A whole column, inside SUMPRODUCT or an -IFS form's window, as one row's cell of it;
    anywhere else, a spilled array, refused."""
    if place.row_table and part.table.lower() == place.row_table.lower():
        if is_own(part.table, place):
            return this_row(part.column, place)
        table = table_named(part.table, place)
        if column_named(table, part.column) is None:
            raise Refused("X1", f"it reads {part.table}[{part.column}], which {part.table} "
                                "doesn't have")
        return column_hive(column_named(table, part.column).header)
    raise Refused("X1", f"it reads the whole column {part.table}[{part.column}], which "
                        "spills an array")


def _call_hive(call: Call, place: Place) -> exp.Expression:
    write = place.query.book.functions.get(call.name)
    if write is None:
        raise Refused("X1", f"{call.name} is a formula files 11 and 12 don't list")
    return write(call, place)


def _name_hive(part: Name, place: Place) -> exp.Expression:
    """A defined name for a cell outside a Table: its value, written in, marked to move it to
    Parameters (M5). Any other name is refused."""
    book = place.query.book
    if part.name.lower() in tables_of(book.workbook):
        raise Refused("X1", f"it reads the whole Table {part.name}, which spills an array")
    refers_to = _defined_name(part.name, book.workbook.defined_names)
    if refers_to is None:
        raise Refused("X1", f"it reads {part.name}, which the workbook doesn't define")
    value = _cell_value(refers_to, book.workbook)
    if value is None:
        raise Refused("X1", f"{part.name} is a defined name holding a formula, {refers_to}")
    place.marks.append(Note(MARK, "M5", f"{place.query.table.name}[{place.column}]",
                            f"defined name {part.name}: its value, {_shown(value)}, written in "
                            "from its cell; move it to Parameters, so a change to it is "
                            "read by name"))
    return constant_hive(value)


def _cell_value(refers_to: str, workbook: Workbook) -> object:
    """The value of the one cell outside a Table a defined name refers to, such as
    `Summary!$B$3`, or None for anything else."""
    found = re.fullmatch(r"(?:'((?:[^']|'')+)'|([^!]+))!\$?([A-Z]{1,3})\$?(\d+)", refers_to)
    if found is None:
        return None
    sheet_name = (found.group(1) or "").replace("''", "'") or found.group(2)
    column = 0
    for letter in found.group(3):
        column = column * 26 + ord(letter) - 64
    for sheet in workbook.sheets:
        if sheet.title == sheet_name:
            value = sheet.cells.get((int(found.group(4)), column))
            if value is not None and not is_formula_text(value):
                return value
    return None


# --- Operators (F1, F6, F7, I2, I5) ---------------------------------------------------------


def operation_hive(part: Operation, place: Place) -> exp.Expression:
    """An operator as Hive: `+ - * /` as they are, `^` POWER, `&` CONCAT (F1), the comparisons
    as they are; a date plus or minus days, or a date minus a date (F6); and the patterns F7,
    I2 and I5 name."""
    special = _pattern_hive(part, place)
    if special is not None:
        return special
    if part.operator == "&":
        sides = [_blank_as(each, place, "") for each in _concatenated(part)]
        return hive_call("CONCAT", sides)
    if part.operator == "^":
        return hive_call("POWER", [hive_of(part.left, place), hive_of(part.right, place)])
    if part.operator in ARITHMETIC:
        left = _blank_as(part.left, place, 0)
        if part.operator == "/":
            right = hive_of(part.right, place)
        else:
            right = _blank_as(part.right, place, 0)
        return binary(ARITHMETIC[part.operator], left, right)
    blank = _blank_in_comparison(part)
    if blank is None:
        return binary(COMPARISONS[part.operator], hive_of(part.left, place),
                      hive_of(part.right, place))
    return binary(COMPARISONS[part.operator], _blank_as(part.left, place, blank),
                  _blank_as(part.right, place, blank))


def _blank_in_comparison(part: Operation) -> str | int | None:
    """What a blank reads as in a comparison with a constant, as Excel reads it: "" against a
    text, 0 against a number; None with no constant, where the column is as it is."""
    for side in (part.left, part.right):
        if isinstance(side, Constant) and isinstance(side.value, str):
            return ""
        if isinstance(side, Constant):
            return 0
    return None


def _concatenated(part: FormulaPart) -> list[FormulaPart]:
    """Each part `&` joins, in order: `a & b & c` is a, b and c."""
    if isinstance(part, Operation) and part.operator == "&":
        return _concatenated(part.left) + _concatenated(part.right)
    return [part]


def _blank_as(part: FormulaPart, place: Place, value: object) -> exp.Expression:
    """A part as Hive; where it is a typed column of the row with a blank in the workbook,
    COALESCE(x, 0) or COALESCE(x, ''), as Excel reads a blank there, marked "blank" (M1)."""
    expression = hive_of(part, place)
    if not isinstance(part, ThisRow) or not is_own(part.table, place):
        return expression
    column = column_named(place.query.table, part.column)
    if column.kind != TYPED or None not in column.cells:
        return expression
    shown = "''" if value == "" else str(value)
    place.marks.append(Note(MARK, "M1", f"{place.query.table.name}[{place.column}]",
                            f"blank: {column.header} has a blank in the workbook, which Excel "
                            f"reads as {shown} here and Hive as NULL, so it is "
                            f"COALESCE({hive_name(column.header)}, {shown})"))
    return hive_call("COALESCE", [expression, constant_hive(value)])


def _pattern_hive(part: Operation, place: Place) -> exp.Expression | None:
    """The Hive of an operation one of file 11's patterns names, or None for any other: two
    -IFS forms added (I2), a COUNTIFS plus 1 (I5), the first of a month or the Monday of a
    week (F7), and a date's days (F6)."""
    if part.operator == "+":
        merged = merged_ifs(part)
        if merged is not None:
            return hive_of(merged, place)
        if is_number(part.right, 1) and _is_countifs_rank(part.left):
            return countifs_rank(part.left, place)
        first = _month_or_week_start(part, place)
        if first is not None:
            return first
    if part.operator in ("+", "-"):
        return _date_arithmetic(part, place)
    return None


def is_number(part: FormulaPart, number: float) -> bool:
    """Whether a part is the number `number`, `-1` as Excel writes it among them."""
    if isinstance(part, Negative):
        return is_number(part.operand, -number)
    return (isinstance(part, Constant) and not isinstance(part.value, (bool, str))
            and part.value == number)


def _month_or_week_start(part: Operation, place: Place) -> exp.Expression | None:
    """EOMONTH(d,-1)+1, the first of d's month, and d-WEEKDAY(d,2)+1, the Monday of its week
    (F7)."""
    if not is_number(part.right, 1):
        return None
    left = part.left
    if isinstance(left, Call) and left.name == "EOMONTH" and len(left.args) == 2 and (
            is_number(left.args[1], -1)):
        return written("CAST(TRUNC(p0, 'MM') AS STRING)", p0=as_date(left.args[0], place))
    if isinstance(left, Operation) and left.operator == "-" and isinstance(left.right, Call):
        weekday = left.right
        if weekday.name == "WEEKDAY" and len(weekday.args) == 2 and (
                is_number(weekday.args[1], 2) and weekday.args[0] == left.left):
            return written("CAST(NEXT_DAY(DATE_ADD(p0, 7 * -1), 'MO') AS STRING)",
                           p0=as_date(left.left, place))
    return None


def _date_arithmetic(part: Operation, place: Place) -> exp.Expression | None:
    """A date plus or minus days, DATE_ADD(d, n) and DATE_SUB(d, n), and a date minus a date,
    DATEDIFF(b, a) (F6); None where neither side is a date."""
    left_date, right_date = is_date(part.left, place), is_date(part.right, place)
    if left_date and right_date and part.operator == "-":
        return hive_call("DATEDIFF", [as_date(part.left, place), as_date(part.right, place)])
    if left_date and not right_date:
        name = "DATE_ADD" if part.operator == "+" else "DATE_SUB"
        return hive_call(name, [as_date(part.left, place), hive_of(part.right, place)])
    if right_date and not left_date and part.operator == "+":
        return hive_call("DATE_ADD", [as_date(part.right, place), hive_of(part.left, place)])
    return None


def is_date(part: FormulaPart, place: Place) -> bool:
    """Whether a part is a date: a typed column of the row whose values are dates, as dates or
    as text; a formula column whose formula is one; or a date a function or `+` makes."""
    if isinstance(part, ThisRow) and is_own(part.table, place):
        column = column_named(place.query.table, part.column)
        if column is None:
            return False
        if column.kind == TYPED:
            return _holds_dates(column)
        formulas = [cell for cell in column.cells if is_formula_text(cell)]
        return bool(formulas) and _formula_is_date(formulas[0], place)
    if isinstance(part, Call):
        return part.name in ("DATE", "TODAY", "EOMONTH", "EDATE")
    if isinstance(part, Operation) and part.operator in ("+", "-"):
        return is_date(part.left, place) != is_date(part.right, place)
    return False


def _formula_is_date(formula: str, place: Place) -> bool:
    try:
        return is_date(read_formula(formula), place)
    except Refused:
        return False


def _holds_dates(column: Column) -> bool:
    values = [cell for cell in column.cells if cell is not None]
    return bool(values) and all(_is_date_value(value) for value in values)


def _is_date_value(value: object) -> bool:
    if isinstance(value, datetime.datetime):
        return True
    return isinstance(value, str) and bool(ISO_DATE.fullmatch(value) or TEXT_DATE.fullmatch(
        value))


def as_date(part: FormulaPart, place: Place) -> exp.Expression:
    """A part a formula reads as a date. A typed column of dates held as text, such as
    20260911, is made one inside this formula, marked "text date" (M3); any other part is as
    it is."""
    if isinstance(part, ThisRow) and is_own(part.table, place):
        column = column_named(place.query.table, part.column)
        if column is not None and column.kind == TYPED and _holds_text_dates(column):
            return text_date(this_row(part.column, place), column.header, place)
    return hive_of(part, place)


def _holds_text_dates(column: Column) -> bool:
    values = [cell for cell in column.cells if cell is not None]
    return bool(values) and all(isinstance(value, str) and TEXT_DATE.fullmatch(value)
                                for value in values)


def text_date(column: exp.Expression, header: str, place: Place) -> exp.Expression:
    """A date held as 8 digits of text, as ISO's text, marked "text date" (M3)."""
    place.marks.append(Note(MARK, "M3", f"{place.query.table.name}[{place.column}]",
                            f"text date: {header} holds dates as text, such as 20260911, made "
                            "a date only inside this formula"))
    return written("CONCAT(SUBSTR(p0, 1, 4), '-', SUBSTR(p0, 5, 2), '-', SUBSTR(p0, 7, 2))",
                   p0=column)


# --- The functions file 11 lists -------------------------------------------------------------


def arguments(call: Call, fewest: int, most: int) -> tuple[FormulaPart, ...]:
    """A call's arguments, refused unless there are as many as file 11's form of it has."""
    if not fewest <= len(call.args) <= most:
        raise Refused("X1", f"{call.name} with {len(call.args)} arguments isn't a form file 11 "
                            "lists")
    return call.args


def given(call: Call, number: int) -> FormulaPart | None:
    """A call's argument `number`, counting from 0, or None where it is left out."""
    if number < len(call.args) and not isinstance(call.args[number], Omitted):
        return call.args[number]
    return None


# Functions Hive has, as they are or under another name (F4, F5, F6), by their Excel name: the
# Hive name and how many arguments Excel's form of it has.
SAME_IN_HIVE = {
    "ROUND": ("ROUND", 2, 2), "ABS": ("ABS", 1, 1), "POWER": ("POWER", 2, 2),
    "SQRT": ("SQRT", 1, 1), "MOD": ("PMOD", 2, 2), "INT": ("FLOOR", 1, 1),
    "LEN": ("LENGTH", 1, 1), "SUBSTITUTE": ("REPLACE", 3, 3), "PROPER": ("INITCAP", 1, 1),
    "UPPER": ("UPPER", 1, 1), "LOWER": ("LOWER", 1, 1), "TRIM": ("TRIM", 1, 1),
    "IFERROR": ("COALESCE", 2, 2), "IFNA": ("COALESCE", 2, 2),
}


def _same_in_hive(call: Call, place: Place) -> exp.Expression:
    """A function Hive has as Excel's: MOD as PMOD, INT as FLOOR, IFERROR as COALESCE, as a
    divide by 0 is NULL (F4); LEN as LENGTH, SUBSTITUTE as REPLACE, PROPER as INITCAP (F5)."""
    name, fewest, most = SAME_IN_HIVE[call.name]
    return hive_call(name, [hive_of(arg, place) for arg in arguments(call, fewest, most)])


def _and_hive(call: Call, place: Place) -> exp.Expression:
    """AND(a, b, c): `a AND b AND c` (F2)."""
    return all_of([hive_of(arg, place) for arg in arguments(call, 1, 255)])


def _or_hive(call: Call, place: Place) -> exp.Expression:
    """OR(a, b): `(a OR b)`, bracketed, as AND joins before OR (F2)."""
    sides = [hive_of(arg, place) for arg in arguments(call, 1, 255)]
    joined = sides[0]
    for side in sides[1:]:
        joined = binary(exp.Or, joined, side)
    return exp.Paren(this=joined)


def _not_hive(call: Call, place: Place) -> exp.Expression:
    """NOT(x): `NOT x` (F2)."""
    (part,) = arguments(call, 1, 1)
    return exp.Not(this=bracketed(hive_of(part, place), exp.Not))


def _if_hive(call: Call, place: Place) -> exp.Expression:
    """IF as it is; with no third argument, FALSE where Excel gives it (F3)."""
    arguments(call, 2, 3)
    parts = [hive_of(call.args[0], place), _branch(given(call, 1), place)]
    if len(call.args) == 3:
        parts.append(_branch(given(call, 2), place))
    else:
        parts.append(exp.Boolean(this=False))
    return hive_call("IF", parts)


def _branch(part: FormulaPart | None, place: Place) -> exp.Expression:
    """An IF's value; one left empty is 0, as Excel gives it."""
    if part is None:
        return exp.Literal.number("0")
    return hive_of(part, place)


def _ifs_case_hive(call: Call, place: Place) -> exp.Expression:
    """IFS(c1, v1, c2, v2): `CASE WHEN c1 THEN v1 WHEN c2 THEN v2 END` (F3)."""
    parts = arguments(call, 2, 254)
    if len(parts) % 2:
        raise Refused("X1", "IFS has a condition with no value")
    case = exp.Case()
    for number in range(0, len(parts), 2):
        case = case.when(hive_of(parts[number], place), hive_of(parts[number + 1], place))
    return case


def _switch_hive(call: Call, place: Place) -> exp.Expression:
    """SWITCH(x, "a", 1, 0): `CASE x WHEN 'a' THEN 1 ELSE 0 END` (F3)."""
    parts = arguments(call, 3, 254)
    case = exp.Case(this=hive_of(parts[0], place))
    pairs = parts[1:]
    for number in range(0, len(pairs) - 1, 2):
        case = case.when(hive_of(pairs[number], place), hive_of(pairs[number + 1], place))
    if len(pairs) % 2:
        case = case.else_(hive_of(pairs[-1], place))
    return case


def _isblank_hive(call: Call, place: Place) -> exp.Expression:
    """ISBLANK(x): `x IS NULL` (F4), the column as it is (M1)."""
    (part,) = arguments(call, 1, 1)
    return written("p0 IS NULL", p0=hive_of(part, place))


def _least_or_greatest(call: Call, place: Place) -> exp.Expression:
    """MIN(a, b) and MAX(a, b) of one row's cells: LEAST and GREATEST (F4). A whole column's
    is file 12's T1."""
    parts = arguments(call, 1, 255)
    if len(parts) < 2 or any(isinstance(part, WholeColumn) for part in parts):
        raise Refused("T1", f"{call.name} of a whole column is file 12's T1, which the code "
                            "doesn't write yet")
    name = "LEAST" if call.name == "MIN" else "GREATEST"
    return hive_call(name, [hive_of(part, place) for part in parts])


def _left_or_right(call: Call, place: Place) -> exp.Expression:
    """LEFT(x, n): SUBSTR(x, 1, n); RIGHT(x, n): SUBSTR(x, -n); n is 1 when it is left out
    (F5)."""
    arguments(call, 1, 2)
    text = hive_of(call.args[0], place)
    count = exp.Literal.number("1")
    if given(call, 1) is not None:
        count = hive_of(call.args[1], place)
    if call.name == "LEFT":
        return hive_call("SUBSTR", [text, exp.Literal.number("1"), count])
    return written("SUBSTR(p0, -p1)", p0=text, p1=count)


def _mid_hive(call: Call, place: Place) -> exp.Expression:
    """MID(x, s, n): SUBSTR(x, s, n) (F5)."""
    return hive_call("SUBSTR", [hive_of(part, place) for part in arguments(call, 3, 3)])


def _find_hive(call: Call, place: Place) -> exp.Expression:
    """FIND(a, x): INSTR(x, a); SEARCH(a, x): INSTR(LOWER(x), LOWER(a)), a text written in
    lower case (F5)."""
    sought, text = arguments(call, 2, 2)
    if call.name == "FIND":
        return hive_call("INSTR", [hive_of(text, place), hive_of(sought, place)])
    lowered = hive_call("LOWER", [hive_of(sought, place)])
    if isinstance(sought, Constant) and isinstance(sought.value, str):
        lowered = exp.Literal.string(sought.value.lower())
    return hive_call("INSTR", [hive_call("LOWER", [hive_of(text, place)]), lowered])


def _isnumber_hive(call: Call, place: Place) -> exp.Expression:
    """ISNUMBER(FIND(..)) and ISNUMBER(SEARCH(..)): `INSTR(..) > 0` (F5)."""
    (part,) = arguments(call, 1, 1)
    if not isinstance(part, Call) or part.name not in ("FIND", "SEARCH"):
        raise Refused("X1", "ISNUMBER of anything but FIND or SEARCH isn't a form file 11 "
                            "lists")
    return written("p0 > 0", p0=_find_hive(part, place))


def _concat_hive(call: Call, place: Place) -> exp.Expression:
    """CONCATENATE and CONCAT: CONCAT (F5), a blank as '' (M1)."""
    parts = arguments(call, 1, 255)
    if any(isinstance(part, (WholeColumn, WholeTable)) for part in parts):
        raise Refused("X1", f"{call.name} of a whole column spills an array")
    return hive_call("CONCAT", [_blank_as(part, place, "") for part in parts])


def _textjoin_hive(call: Call, place: Place) -> exp.Expression:
    """TEXTJOIN(",", TRUE, a, b): CONCAT_WS(',', a, b) (F5)."""
    parts = arguments(call, 3, 255)
    if parts[1] != Constant(True):
        raise Refused("X1", "TEXTJOIN keeping empty cells isn't a form file 11 lists")
    return hive_call("CONCAT_WS", [hive_of(parts[0], place),
                                   *[hive_of(part, place) for part in parts[2:]]])


def _value_hive(call: Call, place: Place) -> exp.Expression:
    """VALUE(x): CAST(x AS DOUBLE) (F5)."""
    (part,) = arguments(call, 1, 1)
    return written("CAST(p0 AS DOUBLE)", p0=hive_of(part, place))


def _date_part_hive(call: Call, place: Place) -> exp.Expression:
    """YEAR, MONTH, DAY as they are (F6), a text date made one (M3)."""
    (part,) = arguments(call, 1, 1)
    return hive_call(call.name, [as_date(part, place)])


def _date_hive(call: Call, place: Place) -> exp.Expression:
    """DATE(2026,9,1): '2026-09-01' (F6); DATE(YEAR(d), MONTH(d), 1), the first of d's month
    (F7); DATE(LEFT(x,4), MID(x,5,2), RIGHT(x,2)), a text date (M3)."""
    year, month, day = arguments(call, 3, 3)
    if all(isinstance(part, Constant) and isinstance(part.value, int)
           for part in (year, month, day)):
        try:
            return exp.Literal.string(datetime.date(year.value, month.value, day.value)
                                      .isoformat())
        except ValueError:
            raise Refused("X1", "its DATE is no day of the calendar") from None
    if (isinstance(year, Call) and isinstance(month, Call) and year.name == "YEAR"
            and month.name == "MONTH" and year.args == month.args and is_number(day, 1)):
        return written("CAST(TRUNC(p0, 'MM') AS STRING)", p0=as_date(year.args[0], place))
    text = _split_text_date(year, month, day)
    if text is not None:
        column = column_named(place.query.table, text.column)
        return text_date(this_row(text.column, place), column.header, place)
    raise Refused("X1", "this form of DATE isn't one file 11 lists")


def _split_text_date(year: FormulaPart, month: FormulaPart,
                     day: FormulaPart) -> ThisRow | None:
    """The column DATE(LEFT(x,4), MID(x,5,2), RIGHT(x,2)) reads, if `x` is one, else None."""
    pattern = (("LEFT", (Constant(4),)), ("MID", (Constant(5), Constant(2))),
               ("RIGHT", (Constant(2),)))
    columns = []
    for part, (name, rest) in zip((year, month, day), pattern, strict=True):
        if not isinstance(part, Call) or part.name != name or part.args[1:] != rest:
            return None
        columns.append(part.args[0])
    if not isinstance(columns[0], ThisRow) or columns.count(columns[0]) != 3:
        return None
    return columns[0]


def _today_hive(call: Call, place: Place) -> exp.Expression:
    """TODAY(): CURRENT_DATE (F6)."""
    arguments(call, 0, 0)
    return written("CURRENT_DATE")


def _datedif_hive(call: Call, place: Place) -> exp.Expression:
    """DATEDIF(a, b, "d"): DATEDIFF(b, a); "m": FLOOR(MONTHS_BETWEEN(b, a)); "y":
    FLOOR(MONTHS_BETWEEN(b, a) / 12) (F6)."""
    start, end, unit = arguments(call, 3, 3)
    days = {"d": "DATEDIFF(p1, p0)", "m": "FLOOR(MONTHS_BETWEEN(p1, p0))",
            "y": "FLOOR(MONTHS_BETWEEN(p1, p0) / 12)"}
    if not isinstance(unit, Constant) or str(unit.value).lower() not in days:
        raise Refused("X1", "DATEDIF in any unit but \"d\", \"m\" or \"y\" isn't a form file "
                            "11 lists")
    return written(days[str(unit.value).lower()], p0=as_date(start, place),
                   p1=as_date(end, place))


def _eomonth_hive(call: Call, place: Place) -> exp.Expression:
    """EOMONTH(d, 0): LAST_DAY(d) (F6)."""
    day, months = arguments(call, 2, 2)
    if not is_number(months, 0):
        raise Refused("X1", "EOMONTH of any month but d's own isn't a form file 11 lists")
    return hive_call("LAST_DAY", [as_date(day, place)])


def _edate_hive(call: Call, place: Place) -> exp.Expression:
    """EDATE(d, n): ADD_MONTHS(d, n), marked: a month's last day stays one (F6)."""
    day, months = arguments(call, 2, 2)
    place.marks.append(Note(MARK, "F6", f"{place.query.table.name}[{place.column}]",
                            "EDATE: Hive's ADD_MONTHS keeps a month's last day the last day, "
                            "as Excel's EDATE doesn't: 28 February and a month is 31 March "
                            "in Hive, 28 March in Excel"))
    return hive_call("ADD_MONTHS", [as_date(day, place), hive_of(months, place)])


def _weekday_hive(call: Call, place: Place) -> exp.Expression:
    """WEEKDAY(d): DAYOFWEEK(d), Sunday 1 in both (F6)."""
    arguments(call, 1, 2)
    if given(call, 1) is not None and not is_number(call.args[1], 1):
        raise Refused("X1", "WEEKDAY counting from any day but Sunday isn't a form file 11 "
                            "lists")
    return hive_call("DAYOFWEEK", [as_date(call.args[0], place)])


def _text_hive(call: Call, place: Place) -> exp.Expression:
    """TEXT(d, "yyyy-mm"): DATE_FORMAT(d, 'yyyy-MM') (F6)."""
    day, shown = arguments(call, 2, 2)
    if not isinstance(shown, Constant) or not isinstance(shown.value, str):
        raise Refused("X1", "TEXT with a format that isn't a text isn't a form file 11 lists")
    pattern = shown.value
    if re.search(r"[^ymd\-/. ,]", pattern.lower()) or not re.search(r"[ymd]", pattern.lower()):
        raise Refused("X1", f"TEXT in the format {pattern} isn't one file 11 lists")
    return hive_call("DATE_FORMAT", [as_date(day, place),
                                     exp.Literal.string(_hive_date_format(pattern.lower()))])


def _hive_date_format(pattern: str) -> str:
    """An Excel date format, in lower case, as Hive's DATE_FORMAT writes it: mm is MM."""
    found = []
    at = 0
    while at < len(pattern):
        for excel, hive in DATE_LETTERS:
            if pattern.startswith(excel, at):
                found.append(hive)
                at += len(excel)
                break
        else:
            found.append(pattern[at])
            at += 1
    return "".join(found)


# --- Lookups (F8, M2, M4) -------------------------------------------------------------------


def _xlookup_hive(call: Call, place: Place) -> exp.Expression:
    """XLOOKUP(k, t[a], t[b]): LEFT JOIN t ON k = t.a, then t.b; its fourth argument, v:
    COALESCE(.., v) (F4, F8)."""
    parts = arguments(call, 3, 6)
    key, match, result = parts[:3]
    if given(call, 4) is not None or given(call, 5) is not None:
        raise Refused("X1", "XLOOKUP with a match or search mode isn't a form file 11 lists")
    if not isinstance(match, WholeColumn) or not isinstance(result, WholeColumn) or (
            match.table.lower() != result.table.lower()):
        raise Refused("X1", "XLOOKUP is read from two columns of one Table")
    value = looked_up(key, match.table, match.column, result.column, place)
    fallback = given(call, 3)
    if fallback is not None:
        value = hive_call("COALESCE", [value, hive_of(fallback, place)])
    return value


def _vlookup_hive(call: Call, place: Place) -> exp.Expression:
    """VLOOKUP(k, t, n, FALSE): t's column n, joined on its first (F8); with TRUE, 1 or no
    fourth argument, the exact match, marked "approximate" (M2)."""
    key, table_part, number = arguments(call, 3, 4)[:3]
    table = None
    if isinstance(table_part, WholeTable):
        table = table_named(table_part.table, place)
    elif isinstance(table_part, Name):
        table = table_named(table_part.name, place)
    if table is None or not isinstance(number, Constant) or not isinstance(number.value, int):
        raise Refused("X1", "VLOOKUP is read from a Table and a column's number")
    if not 1 <= number.value <= len(table.columns):
        raise Refused("X1", f"VLOOKUP reads column {number.value} of {table.name}, which "
                            "it doesn't have")
    exact = given(call, 3)
    if exact is None or not (exact == Constant(False) or is_number(exact, 0)):
        _approximate(place)
    return looked_up(key, table.name, table.columns[0].header,
                     table.columns[number.value - 1].header, place)


def _index_hive(call: Call, place: Place) -> exp.Expression:
    """INDEX(t[b], MATCH(k, t[a], 0)): as XLOOKUP (F8); MATCH with 1 or none, the exact
    match, marked "approximate" (M2)."""
    result, row = arguments(call, 2, 2)
    if not isinstance(row, Call) or row.name != "MATCH" or not isinstance(result, WholeColumn):
        raise Refused("X1", "INDEX is read with MATCH, as INDEX(t[b], MATCH(k, t[a], 0))")
    key, match = arguments(row, 2, 3)[:2]
    kind = given(row, 2)
    if kind is not None and is_number(kind, -1):
        raise Refused("X1", "MATCH with -1 isn't a form file 11 lists")
    if kind is None or not is_number(kind, 0):
        _approximate(place)
    if not isinstance(match, WholeColumn) or match.table.lower() != result.table.lower():
        raise Refused("X1", "INDEX and MATCH are read from two columns of one Table")
    return looked_up(key, match.table, match.column, result.column, place)


def _approximate(place: Place) -> None:
    place.marks.append(Note(MARK, "M2", f"{place.query.table.name}[{place.column}]",
                            "approximate: its lookup matches the nearest smaller key in Excel, "
                            "and is written as the exact match"))


def looked_up(key: FormulaPart, table_name: str, match: str, result: str,
              place: Place) -> exp.Expression:
    """Column `result` of the Table `table_name`'s row whose `match` is this row's `key`: a
    LEFT JOIN of it, one a key (F8), marked "repeated key" where its key repeats in the
    workbook (M4). A lookup into Parameters by a name is its value, written in."""
    table = table_named(table_name, place)
    if table.name.lower() == PARAMETERS.lower():
        return parameter_value(key, place)
    if is_own(table.name, place) or table.name.lower() == KEYS.lower():
        raise Refused("X1", f"a lookup into {table.name} isn't a form file 11 lists")
    matched, wanted = column_named(table, match), column_named(table, result)
    if matched is None or wanted is None:
        raise Refused("X1", f"its lookup reads a column {table.name} doesn't have")
    if Piece(EXCEL_TABLE, table.name) not in place.query.book.reads:
        raise Refused("X1", f"it reads {table.name}, which has no Hive")
    key_hive = hive_of(key, place)
    join = _lookup_join(table, matched.header, key_hive, place.query)
    values = [cell for cell in matched.cells if cell is not None]
    if len(values) != len(set(values)):
        place.marks.append(Note(MARK, "M4", f"{place.query.table.name}[{place.column}]",
                                f"repeated key: {matched.header} repeats in {table.name}, "
                                "where Excel takes the first match and a LEFT JOIN every one"))
    return column_hive(wanted.header, join.alias)


def _lookup_join(table: Table, match: str, key: exp.Expression, query: TableQuery) -> Lookup:
    """The LEFT JOIN of `table` on `match` for `key`: one already there, or a new one."""
    for join in query.joins:
        if isinstance(join, Lookup) and join.table is table and join.column == match and (
                join.key == key):
            return join
    join = Lookup(new_alias(table.name, query.taken), table, match, key)
    query.joins.append(join)
    return join


def parameter_value(key: FormulaPart, place: Place) -> exp.Expression:
    """A value of Parameters looked up by its name: the value, written into the Hive, and said
    in the map: change it in Parameters and the table won't follow (F8)."""
    parameters = table_named(PARAMETERS, place)
    if not isinstance(key, Constant) or len(parameters.columns) < 2:
        raise Refused("X1", "Parameters is read by a value's name, such as \"rate\"")
    for name, value in zip(parameters.columns[0].cells, parameters.columns[1].cells,
                           strict=True):
        if str(name).lower() == str(key.value).lower():
            place.query.notes.append(Note(
                WRITTEN_IN, "F8", f"{place.query.table.name}[{place.column}]",
                f"{name}, {_shown(value)}, from Parameters: change it in Parameters and the "
                "table won't follow"))
            return constant_hive(value)
    raise Refused("X1", f"Parameters has no value named {key.value}")


# --- -IF(S) forms, RANK and SUMPRODUCT (F9, F10, I1 to I6) ----------------------------------


@dataclass
class IfsForm:
    """An -IF(S) form, read: its aggregate, the column it adds up (None for a count), and each
    (column, criteria) pair it matches on, all of one Table."""

    aggregate: str
    table: str
    value: str | None
    pairs: list[tuple[str, FormulaPart]]


def read_ifs(call: Call) -> IfsForm:
    """An -IF(S) form's parts: SUMIFS(t[v], t[a], [@a], ...), COUNTIFS(t[a], [@a], ...),
    SUMIF and AVERAGEIF(t[a], [@a], t[v]), and COUNTIF(t[a], [@a]), the -IFS form with one
    match (F9)."""
    args = list(call.args)
    value: FormulaPart | None = None
    if call.name in ("SUMIF", "AVERAGEIF"):
        arguments(call, 2, 3)
        value = args[2] if len(args) == 3 else args[0]
        args = args[:2]
    elif call.name == "COUNTIF":
        arguments(call, 2, 2)
    elif call.name != "COUNTIFS":
        arguments(call, 3, 255)
        value, args = args[0], args[1:]
    if not args or len(args) % 2:
        raise Refused("X1", f"{call.name} has a column with no criteria")
    columns = [value, *args[0::2]] if value is not None else args[0::2]
    if not all(isinstance(column, WholeColumn) for column in columns) or len(
            {column.table.lower() for column in columns}) > 1:
        raise Refused("X1", f"{call.name} reads whole columns of one Table")
    pairs = [(column.column, criteria) for column, criteria in zip(args[0::2], args[1::2],
                                                                    strict=True)]
    return IfsForm(IFS_FORMS[call.name], columns[0].table,
                   value.column if value is not None else None, pairs)


def _ifs_form_hive(call: Call, place: Place) -> exp.Expression:
    """An -IF(S) form: over its own Table, a window, PARTITION BY each column matched on this
    row's (F9), ordered on one compared with this row's for a running total (I5); over another,
    a LEFT JOIN of its totals by group (F9). COALESCE(.., 0) but for AVERAGEIFS."""
    form = read_ifs(call)
    if is_own(form.table, place):
        return _window_ifs(form, place)
    return _joined_ifs(form, place)


def criteria_condition(column: exp.Expression, criteria: FormulaPart,
                       place: Place) -> exp.Expression:
    """An -IF(S) form's condition on `column` (I1): "x" `s = 'x'`; ">10" and the like that
    comparison; "<>x" `(s <> 'x' OR s IS NULL)`; "<>" alone `s IS NOT NULL`; a wildcard
    `LOWER(s) LIKE` (I4); two values `s IN (..)` (I2)."""
    if isinstance(criteria, AnyOf):
        return written("p0 IN (" + ", ".join(f"p{number + 1}" for number in range(
            len(criteria.values))) + ")", p0=column, **{
            f"p{number + 1}": constant_hive(value.value)
            for number, value in enumerate(criteria.values)})
    value = _criteria_value(criteria, place)
    if not isinstance(value, str):
        return binary(exp.EQ, column, constant_hive(value))
    operator, text = re.fullmatch(r"(<>|<=|>=|<|>|=)?(.*)", value, re.DOTALL).groups()
    if "~" in text:
        raise Refused("X1", "a criteria with ~ isn't a form file 11 lists")
    if not text:
        if operator == "<>":
            return written("p0 IS NOT NULL", p0=column)
        raise Refused("X1", "a criteria matching a blank isn't a form file 11 lists")
    if "*" in text or "?" in text:
        return _wildcard(column, operator, text)
    literal = _criteria_literal(text)
    if operator == "<>":
        return written("(p0 <> p1 OR p0 IS NULL)", p0=column, p1=literal)
    return binary(COMPARISONS[operator or "="], column, literal)


def _criteria_value(criteria: FormulaPart, place: Place) -> object:
    """A criteria's value: a constant, or a value written in, such as a defined name's."""
    if isinstance(criteria, Constant):
        return criteria.value
    joined = _concatenated(criteria)
    if len(joined) > 1 and all(isinstance(part, Constant) for part in joined):
        return "".join(_shown(part.value) for part in joined)
    expression = hive_of(criteria, place)
    if isinstance(expression, exp.Literal):
        return expression.this if expression.is_string else float(expression.this)
    raise Refused("X1", "its criteria is no value file 11 lists")


def _criteria_literal(text: str) -> exp.Expression:
    if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return exp.Literal.number(text)
    return exp.Literal.string(text)


def _wildcard(column: exp.Expression, operator: str | None, text: str) -> exp.Expression:
    """A wildcard, "*ail*": `LOWER(s) LIKE '%ail%'`, as Excel ignores case (I4)."""
    if operator not in (None, "="):
        raise Refused("X1", "a wildcard with a comparison isn't a form file 11 lists")
    pattern = text.lower().replace("%", "\\%").replace("_", "\\_")
    pattern = pattern.replace("*", "%").replace("?", "_")
    return written("LOWER(p0) LIKE p1", p0=column, p1=exp.Literal.string(pattern))


def _this_row_compared(criteria: FormulaPart) -> tuple[str, FormulaPart] | None:
    """A criteria compared with this row, as ">="&[@d]: the comparison and the part, or
    None."""
    if isinstance(criteria, Operation) and criteria.operator == "&" and isinstance(
            criteria.left, Constant) and criteria.left.value in COMPARISONS and not (
            isinstance(criteria.right, Constant)):
        return str(criteria.left.value), criteria.right
    return None


def _is_this_row_value(criteria: FormulaPart) -> bool:
    """Whether a criteria is a value of this row, such as [@a], not a value to match."""
    joined = _concatenated(criteria)
    if all(isinstance(part, Constant) for part in joined):
        return False
    return not isinstance(criteria, (AnyOf, Name)) and _this_row_compared(criteria) is None


def _window_ifs(form: IfsForm, place: Place) -> exp.Expression:
    """An -IF(S) form over its own Table: `SUM(CASE WHEN s = 'x' THEN v END) OVER (PARTITION
    BY a)` (F9); `t[d], "<="&[@d]` a running total, ties included (I5)."""
    rows = replace(place, row_table=place.query.table.name)
    partitions, conditions, order = [], [], None
    for header, criteria in form.pairs:
        compared = _this_row_compared(criteria)
        if compared is not None:
            order = _running_order(header, compared, order)
        elif _is_this_row_value(criteria):
            if not _is_matched_cell(criteria, header, place):
                raise Refused("X1", f"it matches {header} on another column of its row")
            partitions.append(this_row(header, place))
        else:
            conditions.append(criteria_condition(this_row(header, place), criteria, rows))
    total = _conditional_aggregate(form, conditions, rows)
    window = exp.Window(this=total, partition_by=partitions or None, over="OVER")
    if order is not None:
        window.set("order", exp.Order(expressions=[ordered(this_row(order[0], place),
                                                           order[1])]))
        window.set("spec", exp.WindowSpec(kind="RANGE", start="UNBOUNDED",
                                          start_side="PRECEDING", end="CURRENT ROW"))
        return window
    if form.aggregate in ("SUM", "MAX", "MIN"):
        return hive_call("COALESCE", [window, exp.Literal.number("0")])
    return window


def _is_matched_cell(criteria: FormulaPart, header: str, place: Place) -> bool:
    """Whether a criteria is this row's own cell of column `header`, as `t[a], [@a]`."""
    return (isinstance(criteria, ThisRow) and is_own(criteria.table, place)
            and criteria.column.lower() == header.lower())


def _running_order(header: str, compared: tuple[str, FormulaPart],
                   order: tuple[str, bool] | None) -> tuple[str, bool]:
    """The column a running total is ordered on, and whether DESC: "<="&[@d] counts each row up
    to this one, ">="&[@d] each from it (I5)."""
    operator, part = compared
    if order is not None or operator not in ("<=", ">=") or not isinstance(part, ThisRow) or (
            part.column.lower() != header.lower()):
        raise Refused("X1", "a criteria compared with this row is a form file 11 lists only "
                            "as a running total, t[d], \"<=\"&[@d]")
    return header, operator == ">="


def _conditional_aggregate(form: IfsForm, conditions: list[exp.Expression],
                           place: Place) -> exp.Expression:
    """The aggregate of an -IF(S) form over the rows its conditions keep: COUNT(*) with none,
    else `COUNT(CASE WHEN .. THEN 1 END)`, and `SUM(CASE WHEN .. THEN v END)`."""
    value: exp.Expression = exp.Literal.number("1")
    if form.value is not None:
        value = _whole_column_hive(WholeColumn(form.table, form.value), place)
    if conditions:
        value = exp.Case().when(all_of(conditions), value)
    elif form.value is None:
        return written("COUNT(*)")
    return hive_call(form.aggregate, [value])


def _joined_ifs(form: IfsForm, place: Place) -> exp.Expression:
    """An -IF(S) form over another Table: a LEFT JOIN of `(SELECT a, SUM(v) AS total FROM t
    WHERE s = 'x' GROUP BY a)` on this row's a, its total COALESCE(.., 0) but for AVERAGEIFS
    (F9)."""
    table = table_named(form.table, place)
    if table.name.lower() in (PARAMETERS.lower(), KEYS.lower()):
        raise Refused("X1", f"an -IFS form over {table.name} isn't one file 11 lists")
    if Piece(EXCEL_TABLE, table.name) not in place.query.book.reads:
        raise Refused("X1", f"it reads {table.name}, which has no Hive")
    rows = replace(place, row_table=table.name)
    keys, conditions = [], []
    for header, criteria in form.pairs:
        if column_named(table, header) is None:
            raise Refused("X1", f"it reads {table.name}[{header}], which {table.name} doesn't "
                                "have")
        if _this_row_compared(criteria) is not None:
            raise Refused("X1", "a criteria comparing another Table with this row isn't a "
                                "form file 11 lists")
        column = column_named(table, header).header
        if _is_this_row_value(criteria):
            keys.append((column, hive_of(criteria, place)))
        else:
            conditions.append(criteria_condition(column_hive(column), criteria, rows))
    total = _conditional_aggregate(form, [], rows)
    where = all_of(conditions) if conditions else None
    return totals_read(table, keys, where, total, form.aggregate != "AVG", place)


def totals_read(table: Table, keys: list[tuple[str, exp.Expression]],
                where: exp.Expression | None, total: exp.Expression, zero_for_none: bool,
                place: Place) -> exp.Expression:
    """A total of another Table, read from its join: one with the same groups and conditions,
    or a new one. COALESCE(.., 0) where Excel gives 0 for no row (F9)."""
    join = None
    for each in place.query.joins:
        if isinstance(each, Totals) and each.table is table and each.keys == keys and (
                each.where == where):
            join = each
    if join is None:
        join = Totals(new_alias("c", place.query.taken), table, keys, where)
        place.query.joins.append(join)
    name = hive_name(place.column)
    taken = {each.alias for each in join.totals}
    number = 2
    while name in taken:
        name = f"{hive_name(place.column).strip('<>')}_{number}"
        number += 1
    join.totals.append(exp.alias_(total, exp.Identifier(this=name, quoted=False)))
    read = exp.Column(this=exp.Identifier(this=name, quoted=False),
                      table=exp.Identifier(this=join.alias))
    if zero_for_none:
        return hive_call("COALESCE", [read, exp.Literal.number("0")])
    return read


def merged_ifs(part: Operation) -> Call | None:
    """Two or more -IFS forms added that differ in one value only, as one form matching any of
    those values (I2); else None."""
    calls = _added(part)
    if len(calls) < 2 or not all(isinstance(call, Call) for call in calls):
        return None
    first = calls[0]
    if first.name not in IFS_FORMS or any(call.name != first.name or len(call.args) != len(
            first.args) for call in calls):
        return None
    differing = [number for number in range(len(first.args)) if _differs(calls, number)]
    if len(differing) != 1:
        return None
    values = tuple(call.args[differing[0]] for call in calls)
    if not all(isinstance(value, Constant) and isinstance(value.value, (str, int, float))
               and not re.match(r"[<>=]|.*[*?~]", str(value.value)) for value in values):
        return None
    args = list(first.args)
    args[differing[0]] = AnyOf(values)
    return Call(first.name, tuple(args))


def _differs(calls: list[Call], number: int) -> bool:
    """Whether the calls' argument `number` differs between any two of them."""
    return len({call.args[number] for call in calls}) > 1


def _added(part: FormulaPart) -> list[FormulaPart]:
    if isinstance(part, Operation) and part.operator == "+":
        return _added(part.left) + _added(part.right)
    return [part]


def _is_countifs_rank(part: FormulaPart) -> bool:
    return isinstance(part, Call) and part.name == "COUNTIFS" and any(
        _this_row_compared(criteria) is not None for criteria in part.args[1::2])


def countifs_rank(call: Call, place: Place) -> exp.Expression:
    """COUNTIFS(t[a], [@a], t[v], ">"&[@v])+1: `RANK() OVER (PARTITION BY a ORDER BY v DESC)`;
    with "<", ASC (I5)."""
    form = read_ifs(call)
    if not is_own(form.table, place):
        raise Refused("X1", "a COUNTIFS rank over another Table isn't a form file 11 lists")
    partitions, order = [], None
    for header, criteria in form.pairs:
        compared = _this_row_compared(criteria)
        if compared is not None and order is None and compared[0] in (">", "<") and (
                compared[1] == ThisRow(compared[1].table, header)):
            order = ordered(this_row(header, place), compared[0] == ">")
        elif isinstance(criteria, ThisRow) and criteria.column.lower() == header.lower():
            partitions.append(this_row(header, place))
        else:
            raise Refused("X1", "a COUNTIFS rank with any other criteria isn't a form file 11 "
                                "lists")
    if order is None:
        raise Refused("X1", "a COUNTIFS rank compares one column with this row's")
    return exp.Window(this=written("RANK()"), partition_by=partitions or None,
                      order=exp.Order(expressions=[order]), over="OVER")


def ordered(expression: exp.Expression, descending: bool) -> exp.Ordered:
    """A window's ORDER BY on `expression`, as sqlglot reads `x` or `x DESC` in Hive."""
    if descending:
        return exp.Ordered(this=expression, desc=True, nulls_first=False)
    return exp.Ordered(this=expression, nulls_first=True)


def _rank_hive(call: Call, place: Place) -> exp.Expression:
    """RANK.EQ(x, t[x]) or RANK: `RANK() OVER (ORDER BY x DESC)`; with 1 as a third argument,
    ASC (F10)."""
    value, column = arguments(call, 2, 3)[:2]
    ascending = given(call, 2) is not None and not is_number(call.args[2], 0)
    if not isinstance(column, WholeColumn) or not is_own(column.table, place) or not (
            isinstance(value, ThisRow) and value.column.lower() == column.column.lower()):
        raise Refused("X1", f"{call.name} ranks a row's value in its own Table's column")
    order = ordered(this_row(column.column, place), not ascending)
    return exp.Window(this=written("RANK()"), order=exp.Order(expressions=[order]),
                      over="OVER")


def _sumproduct_hive(call: Call, place: Place) -> exp.Expression:
    """SUMPRODUCT over conditions, its arguments multiplied: `*` is AND, `+` OR where both
    can't hold, or written `((..)+(..)>0)`; with a column to add `SUM(CASE WHEN .. THEN v ELSE
    0 END)`, with none `COUNT(CASE WHEN .. THEN 1 END)`; over its own Table `.. OVER ()`, over
    another a CROSS JOIN of its total (I3). Of whole columns alone, file 12's T1."""
    factors = []
    for product in arguments(call, 1, 255):
        factors += _multiplied(product)
    table = _sumproduct_table(factors, place)
    rows = replace(place, row_table=table.name)
    conditions, values = [], []
    for factor in factors:
        if isinstance(factor, WholeColumn):
            values.append(hive_of(factor, rows))
        elif not is_number(factor, 1):
            conditions.append(_product_condition(factor, rows))
    if len(values) > 1 or not conditions:
        raise Refused("T1", "SUMPRODUCT of whole columns is file 12's T1, which the code "
                            "doesn't write yet")
    if values:
        total = hive_call("SUM", [exp.Case().when(all_of(conditions), values[0]).else_(
            exp.Literal.number("0"))])
    else:
        total = hive_call("COUNT", [exp.Case().when(all_of(conditions),
                                                     exp.Literal.number("1"))])
    if is_own(table.name, place):
        return exp.Window(this=total, over="OVER")
    return totals_read(table, [], None, total, False, place)


def _sumproduct_table(factors: list[FormulaPart], place: Place) -> Table:
    """The one Table whose whole columns a SUMPRODUCT reads, which has Hive."""
    tables = set()
    for factor in factors:
        tables |= {part.table.lower() for part in parts_of(factor)
                   if isinstance(part, WholeColumn)}
    if len(tables) != 1:
        raise Refused("X1", "SUMPRODUCT reads whole columns of one Table")
    table = table_named(tables.pop(), place)
    if not is_own(table.name, place) and (
            Piece(EXCEL_TABLE, table.name) not in place.query.book.reads):
        raise Refused("X1", f"it reads {table.name}, which has no Hive")
    return table


def _multiplied(part: FormulaPart) -> list[FormulaPart]:
    if isinstance(part, Operation) and part.operator == "*":
        return _multiplied(part.left) + _multiplied(part.right)
    return [part]


def _product_condition(factor: FormulaPart, place: Place) -> exp.Expression:
    """One condition of a SUMPRODUCT: a comparison of a column, or two added, which is OR
    written `((..)+(..)>0)`, or where they can't both hold (I3)."""
    if isinstance(factor, Operation) and factor.operator == ">" and is_number(factor.right, 0):
        sides = _added(factor.left)
    elif isinstance(factor, Operation) and factor.operator == "+":
        sides = _added(factor)
        if not _exclusive(sides):
            raise Refused("X1", "SUMPRODUCT adds conditions that can both hold; write it "
                                "((..)+(..)>0)")
    else:
        if not isinstance(factor, Operation) or factor.operator not in COMPARISONS:
            raise Refused("X1", "a SUMPRODUCT factor is a condition, a column or 1")
        return hive_of(factor, place)
    joined = hive_of(sides[0], place)
    for side in sides[1:]:
        joined = binary(exp.Or, joined, hive_of(side, place))
    return exp.Paren(this=joined)


def _exclusive(sides: list[FormulaPart]) -> bool:
    """Whether conditions can't both hold: each `t[s] = "x"` on one column, with another
    value."""
    if not all(isinstance(side, Operation) and side.operator == "=" and isinstance(
            side.left, WholeColumn) and isinstance(side.right, Constant) for side in sides):
        return False
    return len({side.left for side in sides}) == 1 and len(
        {side.right for side in sides}) == len(sides)


# Each function file 11 lists, by its name, and the function that writes its Hive.
FUNCTIONS: dict[str, Callable[[Call, Place], exp.Expression]] = {
    **dict.fromkeys(SAME_IN_HIVE, _same_in_hive),
    "AND": _and_hive, "OR": _or_hive, "NOT": _not_hive, "IF": _if_hive, "IFS": _ifs_case_hive,
    "SWITCH": _switch_hive, "ISBLANK": _isblank_hive, "MIN": _least_or_greatest,
    "MAX": _least_or_greatest, "LEFT": _left_or_right, "RIGHT": _left_or_right,
    "MID": _mid_hive, "FIND": _find_hive, "SEARCH": _find_hive, "ISNUMBER": _isnumber_hive,
    "CONCATENATE": _concat_hive, "CONCAT": _concat_hive, "TEXTJOIN": _textjoin_hive,
    "VALUE": _value_hive, "YEAR": _date_part_hive, "MONTH": _date_part_hive,
    "DAY": _date_part_hive, "DATE": _date_hive, "TODAY": _today_hive,
    "DATEDIF": _datedif_hive, "EOMONTH": _eomonth_hive, "EDATE": _edate_hive,
    "WEEKDAY": _weekday_hive, "TEXT": _text_hive, "XLOOKUP": _xlookup_hive,
    "VLOOKUP": _vlookup_hive, "INDEX": _index_hive, "RANK": _rank_hive,
    "RANK.EQ": _rank_hive, "SUMPRODUCT": _sumproduct_hive,
    **dict.fromkeys(IFS_FORMS, _ifs_form_hive),
}


def summary_matches(table: Table) -> set[str]:
    """Each column of `table`, in lower case, that an -IF(S) form of its formulas over another
    Table matches on with this row's value (file 15's P4)."""
    found: set[str] = set()
    for column in table.columns:
        formulas = [cell for cell in column.cells if is_formula_text(cell)]
        if column.kind == TYPED or not formulas:
            continue
        try:
            parts = list(parts_of(read_formula(formulas[0])))
        except Refused:
            continue
        for part in parts:
            if isinstance(part, Call) and part.name in IFS_FORMS:
                found |= _matched_on(part, table)
    return found


def _matched_on(call: Call, table: Table) -> set[str]:
    try:
        form = read_ifs(call)
    except Refused:
        return set()
    if not form.table or form.table.lower() == table.name.lower():
        return set()
    return {criteria.column.lower() for _, criteria in form.pairs
            if isinstance(criteria, ThisRow) and criteria.table.lower() in (
                "", table.name.lower())}
