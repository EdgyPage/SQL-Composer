"""A Power Query's M read into a small tree of its parts (Toolbox 8.9, ticket 05; ADR 0016).

`read_m` reads a query's M as Copilot file 12's Terms say it is: a `let` of named steps, each
reading the one before, and `in` naming the one it gives, each step an expression of M's: a
call such as `Table.SelectRows(Source, each [status] = "SUCCESS")`, a list `{1, 3}`, a record
`[Name="job_runs"]`, a column of the row `[status]`, a table's item `x{[Name="t"]}` or field
`x[Content]`, `each`, `if .. then .. else`, and M's operators in M's order. What M has beyond
these, a function of its own (`(x) => ..`), `try`, `error` and `meta`, is refused, as file 12's
Terms refuse a step no rule lists. `workbook_power_query.py` writes each step as Hive.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .workbook_formula_reader import Refused

# The pieces of M, as `m_tokens` reads them, in the order they are tried: a column of the row
# in brackets, such as `[status]` or `[Unit Price]`, is one piece, as M allows a space in it.
M_TOKEN = re.compile(r"""
    (?P<space>\s+|//[^\n]*|/\*.*?\*/)
  | (?P<field>\[\s*(?:\#"(?:[^"]|"")*"|[A-Za-z_][\w. ]*?)\s*\])
  | (?P<text>"(?:[^"]|"")*")
  | (?P<quoted>\#"(?:[^"]|"")*")
  | (?P<number>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)
  | (?P<word>\#?[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)
  | (?P<operator>=>|<=|>=|<>|\.\.\.|\.\.|[-+*/&=<>(),\[\]{};?@!])
  | (?P<other>.)
""", re.VERBOSE | re.DOTALL)
# M's words that are never a name.
KEYWORDS = {"let", "in", "each", "if", "then", "else", "and", "or", "not", "type", "meta", "as",
            "is", "try", "otherwise", "error", "true", "false", "null", "section", "shared"}
# M's constants, by their words.
CONSTANTS = {"true": True, "false": False, "null": None}
# M's operators between two parts, each with how tightly it holds its sides, as M's grammar
# orders them: `or` last, then `and`, then `=` and `<>`, then `<` and the like, then `+ - &`,
# then `* /`.
BINARY_OPERATORS = {"or": 1, "and": 2, "=": 3, "<>": 3, "<": 4, ">": 4, "<=": 4, ">=": 4,
                    "+": 5, "-": 5, "&": 5, "*": 6, "/": 6}


@dataclass(frozen=True)
class MPart:
    """One part of a query's M, read into its tree."""


@dataclass(frozen=True)
class MValue(MPart):
    """A text, a number, true, false or null (None), as the M writes it."""

    value: str | int | float | bool | None


@dataclass(frozen=True)
class MName(MPart):
    """A name: a step's, another query's, a function's such as `Table.SelectRows`, a constant
    such as `Order.Descending`, or `_`, the row or the group an `each` reads."""

    name: str


@dataclass(frozen=True)
class MField(MPart):
    """A field: `[c]`, a column of the row an `each` reads (`record` None), or `x[c]`, a field
    of a record or a column of a table."""

    record: MPart | None
    name: str


@dataclass(frozen=True)
class MItem(MPart):
    """An item of a table or a list, such as `x{0}`, or the row `x{[Name="t"]}` picks."""

    target: MPart
    selector: MPart


@dataclass(frozen=True)
class MCall(MPart):
    """A function called, such as `Table.SelectRows`, and its arguments."""

    function: MPart
    args: tuple[MPart, ...]


@dataclass(frozen=True)
class MList(MPart):
    """A list, `{1, 3}`."""

    items: tuple[MPart, ...]


@dataclass(frozen=True)
class MRecord(MPart):
    """A record, such as the one `x{[Name="t"]}` picks a row by: its fields in order."""

    fields: tuple[tuple[str, MPart], ...]


@dataclass(frozen=True)
class MEach(MPart):
    """`each` and the expression it gives for each row, or each group."""

    body: MPart


@dataclass(frozen=True)
class MIf(MPart):
    """`if condition then value else otherwise`."""

    condition: MPart
    value: MPart
    otherwise: MPart


@dataclass(frozen=True)
class MOperation(MPart):
    """An operator between two parts, such as `and`, `<>` or `&`."""

    operator: str
    left: MPart
    right: MPart


@dataclass(frozen=True)
class MNot(MPart):
    """`not` and the part it holds."""

    operand: MPart


@dataclass(frozen=True)
class MNegative(MPart):
    """A part with `-` before it."""

    operand: MPart


@dataclass(frozen=True)
class MLet(MPart):
    """A `let`: each step by its name, in the M's order, and the expression `in` gives."""

    steps: tuple[tuple[str, MPart], ...]
    result: MPart


@dataclass(frozen=True)
class MType(MPart):
    """A type, such as `type number`: read past, as a column's type changes none of its rows
    (file 12's Q5)."""

    name: str


def read_m(m: str) -> MPart:
    """A query's M read into its tree, refused with why where it holds what file 12's Terms
    don't read."""
    reader = MReader(m_tokens(m))
    part = reader.expression()
    if reader.peek() == ";":
        reader.take()
    if reader.peek():
        raise Refused("X1", f"its M goes on after its expression, at {reader.peek()}")
    return part


def m_tokens(m: str) -> list[tuple[str, str]]:
    """Each piece of M, as its kind and its text, its spaces and comments left out."""
    tokens = []
    for found in M_TOKEN.finditer(m):
        kind = found.lastgroup or "other"
        if kind == "other":
            raise Refused("X1", f"its M holds {found.group()!r}, which isn't M file 12 reads")
        if kind != "space":
            tokens.append((kind, found.group()))
    return tokens


def unquoted(text: str) -> str:
    """A text or a quoted name as the M writes it, in double quotes with each quote inside
    doubled, `#` before a name's, as the text it is."""
    return text.removeprefix("#")[1:-1].replace('""', '"')


class MReader:
    """Reads M's pieces into a tree, by M's grammar, one rule a method."""

    def __init__(self, tokens: list[tuple[str, str]]) -> None:
        self.tokens = tokens
        self.at = 0

    def peek(self) -> str:
        """The next piece's text, or "" at the end."""
        if self.at < len(self.tokens):
            return self.tokens[self.at][1]
        return ""

    def peek_kind(self) -> str:
        """The next piece's kind, or "" at the end."""
        if self.at < len(self.tokens):
            return self.tokens[self.at][0]
        return ""

    def take(self) -> tuple[str, str]:
        """The next piece, as its kind and its text, taken."""
        if self.at >= len(self.tokens):
            raise Refused("X1", "its M ends too soon")
        token = self.tokens[self.at]
        self.at += 1
        return token

    def expect(self, text: str) -> None:
        """Take the next piece, which must be `text`."""
        _, found = self.take()
        if found != text:
            raise Refused("X1", f"its M has {found} where M has {text}")

    def expression(self) -> MPart:
        """An expression: a `let`, an `each`, an `if`, or one of M's operators' parts."""
        word = self.peek()
        if word == "let":
            return self.let()
        if word == "each":
            self.take()
            return MEach(self.expression())
        if word == "if":
            self.take()
            condition = self.expression()
            self.expect("then")
            value = self.expression()
            self.expect("else")
            return MIf(condition, value, self.expression())
        if word in ("try", "error"):
            raise Refused("X1", f"M's {word} isn't a step file 12 lists")
        return self.binary(1)

    def let(self) -> MLet:
        """`let name = expression, .. in expression`."""
        self.expect("let")
        steps = [self.step()]
        while self.peek() == ",":
            self.take()
            steps.append(self.step())
        self.expect("in")
        return MLet(tuple(steps), self.expression())

    def step(self) -> tuple[str, MPart]:
        """One step of a `let`: its name, quoted or not, and its expression."""
        kind, text = self.take()
        if kind not in ("word", "quoted") or text in KEYWORDS:
            raise Refused("X1", f"its M names a step {text}, which isn't a name")
        self.expect("=")
        name = text
        if kind == "quoted":
            name = unquoted(text)
        return name, self.expression()

    def binary(self, tightness: int) -> MPart:
        """Operators that hold their sides at least as tightly as `tightness`, left to right."""
        if tightness > max(BINARY_OPERATORS.values()):
            return self.unary()
        part = self.binary(tightness + 1)
        while BINARY_OPERATORS.get(self.peek()) == tightness:
            _, operator = self.take()
            part = MOperation(operator, part, self.binary(tightness + 1))
        if self.peek() in ("meta", "as", "is"):
            raise Refused("X1", f"M's {self.peek()} isn't a step file 12 lists")
        return part

    def unary(self) -> MPart:
        """`not x`, `-x`, `+x`, or a primary part with what follows it."""
        word = self.peek()
        if word == "not":
            self.take()
            return MNot(self.unary())
        if word == "-":
            self.take()
            return MNegative(self.unary())
        if word == "+":
            self.take()
            return self.unary()
        return self.postfix(self.primary())

    def postfix(self, part: MPart) -> MPart:
        """A part with each call, item and field after it: `f(a)`, `x{0}`, `x[c]`; a `?` after
        one is read past."""
        while True:
            word = self.peek()
            if word == "(":
                part = MCall(part, self.arguments())
            elif word == "{":
                self.take()
                selector = self.expression()
                self.expect("}")
                part = MItem(part, selector)
            elif self.peek_kind() == "field":
                part = MField(part, self.field_name())
            elif word == "?":
                self.take()
            else:
                return part

    def arguments(self) -> tuple[MPart, ...]:
        """A call's arguments, in brackets, separated by commas."""
        self.expect("(")
        args: list[MPart] = []
        while self.peek() != ")":
            args.append(self.expression())
            if self.peek() != ",":
                break
            self.take()
        self.expect(")")
        return tuple(args)

    def field_name(self) -> str:
        """A field's name in its brackets, `[c]` or `[#"a b"]`, taken."""
        _, text = self.take()
        inside = text[1:-1].strip()
        if inside.startswith("#"):
            return unquoted(inside)
        return inside

    def primary(self) -> MPart:
        """A constant, a name, a field of the row, a list, a record, a type, or an expression
        in brackets."""
        if self.peek_kind() == "field":
            return MField(None, self.field_name())
        kind, text = self.take()
        if text == "(":
            return self.bracketed()
        if text == "{":
            return MList(self.items())
        if text == "[":
            return self.record()
        return self.token_part(kind, text)

    def token_part(self, kind: str, text: str) -> MPart:
        """One piece taken that is a part alone: a text, a number, a quoted name or a word."""
        if kind == "text":
            return MValue(unquoted(text))
        if kind == "number":
            return MValue(float(text) if "." in text or "e" in text.lower() else int(text))
        if kind == "quoted":
            return MName(unquoted(text))
        if kind == "word":
            return self.word(text)
        raise Refused("X1", f"its M has {text} where M has a value")

    def word(self, text: str) -> MPart:
        """A word where a value is: a constant, a type, or a name."""
        if text in CONSTANTS:
            return MValue(CONSTANTS[text])
        if text == "type":
            return self.type_name()
        if text in KEYWORDS:
            raise Refused("X1", f"its M has {text} where M has a value")
        return MName(text)

    def type_name(self) -> MType:
        """A type after `type`, such as `number`, `nullable text` or `table [a = text]`."""
        _, name = self.take()
        if name == "nullable":
            _, name = self.take()
        if self.peek() == "[" and name in ("table", "record"):
            depth = 0
            while True:
                _, text = self.take()
                depth += {"[": 1, "]": -1}.get(text, 0)
                if depth == 0:
                    break
        return MType(name)

    def bracketed(self) -> MPart:
        """An expression in brackets, after its `(`; a function of the query's own, `(x) =>
        ..`, is refused."""
        start = self.at
        depth = 1
        while depth and self.at < len(self.tokens):
            depth += {"(": 1, ")": -1}.get(self.tokens[self.at][1], 0)
            self.at += 1
        if self.peek() == "=>":
            raise Refused("X1", "a function of the query's own, (x) => .., isn't a step file "
                                "12 lists")
        self.at = start
        part = self.expression()
        self.expect(")")
        return part

    def items(self) -> tuple[MPart, ...]:
        """A list's items, after its `{`, up to its `}`; a range such as `{1..3}` is
        refused."""
        items: list[MPart] = []
        while self.peek() != "}":
            items.append(self.expression())
            if self.peek() == "..":
                raise Refused("X1", "a list of a range, {a..b}, isn't one file 12 lists")
            if self.peek() != ",":
                break
            self.take()
        self.expect("}")
        return tuple(items)

    def record(self) -> MRecord:
        """A record's fields, `[Name="t", Kind="Table"]`, after its `[`."""
        fields: list[tuple[str, MPart]] = []
        while self.peek() != "]":
            kind, text = self.take()
            if kind not in ("word", "quoted"):
                raise Refused("X1", f"its M has a record field {text}, which isn't a name")
            self.expect("=")
            name = text
            if kind == "quoted":
                name = unquoted(text)
            fields.append((name, self.expression()))
            if self.peek() != ",":
                break
            self.take()
        self.expect("]")
        return MRecord(tuple(fields))
