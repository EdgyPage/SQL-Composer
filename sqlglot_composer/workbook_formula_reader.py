"""A Formula workbook's formula read into a small tree of its parts (Toolbox 8.9, ticket 04;
ADR 0016).

`read_formula` reads a formula as the workbook saves it, `=job_runs[[#This Row],[x]]/60`, or
as a person types it, `=[@x]/60`, into its parts, Excel's operators in Excel's order: a
Constant, one row's column (ThisRow), a whole column or Table, a Call, an Operation and the
rest. `parts_of` walks a tree. `workbook_formulas.py` writes each part as Hive; a formula that
can't be read is refused, as `Refused` says.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass

# Excel's prefixes on its newer functions, read past (file 11's Terms).
PREFIXES = re.compile(r"^(?:_xlfn\.|_xlws\.)+", re.IGNORECASE)
# The pieces of a formula, as `read_formula` reads them, in the order they are tried.
FORMULA_TOKEN = re.compile(r"""
    (?P<number>\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+)
  | (?P<cell>(?:(?:'(?:[^']|'')+'|[A-Za-z_][\w.]*)!)?\$?[A-Z]{1,3}\$?\d+
        (?::\$?[A-Z]{1,3}\$?\d+)?(?![\w(\[.!]))
  | (?P<word>[A-Za-z_\\][\w.\\]*)
  | (?P<operator><>|<=|>=|[-+*/^&=<>%(),])
  | (?P<other>.)
""", re.VERBOSE)
# Excel's comparisons, which join two parts after every other operator does.
COMPARISON_OPERATORS = ("=", "<>", "<", ">", "<=", ">=")


# Never shown to the user as it is, so not refusals.refuse: workbook_formulas.py turns each
# into a Note of the map, NULL in the refused formula's place.
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
        while self.peek() in COMPARISON_OPERATORS:
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
            return Call(PREFIXES.sub("", text).upper(), self.read_arguments())
        if text.upper() in ("TRUE", "FALSE"):
            return Constant(text.upper() == "TRUE")
        return Name(text)

    def read_arguments(self) -> tuple[FormulaPart, ...]:
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
