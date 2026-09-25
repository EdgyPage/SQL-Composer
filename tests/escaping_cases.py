"""The escaping matrix, salvaged from v1 as plain cases for the Toolbox's tests to adopt.

A value in a Statement is safe only because sqlglot escapes a string-literal node when it
generates Hive, and that is behaviour sqlglot does not document. These cases are every value
shape that has broken an escaper somewhere, with the exact Hive sqlglot writes for it. They
hold, byte for byte, across the supported range 25.24.2 to 30.19.0 (see the research behind
"Which sqlglot APIs can the Toolbox use at work?").

`test_escaping_cases.py` checks them against sqlglot alone. The Toolbox's own tests should
push the same cases through every way a value reaches a Statement: each comparison function,
both ends of a range, each item of a list, a Date partition bound, and the PARTITION of an
`INSERT_OVERWRITE`. v1's tests also proved two things these cases can't, because they are
about the Toolbox's code rather than sqlglot's:

- **One place generates SQL.** The Toolbox calls `.sql()` in exactly one function, with
  `unsupported_level=ErrorLevel.RAISE`, and never builds SQL text with an f-string. v1 read its
  own source with Python's `ast` module to check this.
- **A number is formatted by the Toolbox, not by its own `str()`.** sqlglot writes a numeric
  literal's text verbatim, so `SNEAKY_NUMBERS` and `NON_FINITE_NUMBERS` below are the cases.

This file is pure ASCII: every non-ASCII payload is written with `\\u` escapes, so a failure
printed to a cp1252 Windows console can't itself raise `UnicodeEncodeError`.
"""

from __future__ import annotations

import decimal

BACKSLASH = "\\"
QUOTE = "'"
BACKTICK = "`"

INJECTION = QUOTE + " OR 1=1 --"
"""Closes the literal, adds a condition that is always true, and comments out the rest."""

DROP_PAYLOAD = QUOTE + "; DROP TABLE mart.deliveries; --"
"""Closes the literal and starts a second statement."""

ESCAPED_QUOTE_INJECTION = BACKSLASH + QUOTE + " OR " + QUOTE + "1" + QUOTE + "=" + QUOTE + "1"
r"""`\' OR '1'='1`, aimed at an escaper that handles a quote but forgets the backslash in
front of it. Hive escapes the backslash first, so this one can't break out; if that order
ever flips, this is the payload that shows it."""

UNICODE = "Berlin \u2013 M\u00fcnchen \u65e5\u672c\u8a9e \U0001f600"
"""An en dash, an umlaut, CJK and an emoji. Hive takes these as UTF-8, unchanged."""

STRING_CASES: tuple[tuple[str, str, str], ...] = (
    # (label, value, the exact Hive literal sqlglot writes for it)
    ("plain", "delivered", "'delivered'"),
    ("single_quote", "O" + QUOTE + "Brien", r"'O\'Brien'"),
    ("backslash", "C:" + BACKSLASH + "temp", r"'C:\\temp'"),
    # The row that matters most: the backslash is doubled and THEN the quote escaped. An
    # escaper that handled the quote first would write '\\'' and let the value out.
    ("backslash_then_quote", BACKSLASH + QUOTE, r"'\\\''"),
    ("newline", "a\nb", r"'a\nb'"),
    ("tab", "a\tb", r"'a\tb'"),
    ("carriage_return", "a\rb", r"'a\rb'"),
    ("unicode", UNICODE, "'" + UNICODE + "'"),
    ("empty", "", "''"),
    ("injection", INJECTION, r"'\' OR 1=1 --'"),
    ("injection_drop", DROP_PAYLOAD, r"'\'; DROP TABLE mart.deliveries; --'"),
    ("escaped_quote_injection", ESCAPED_QUOTE_INJECTION, r"'\\\' OR \'1\'=\'1'"),
)

CONTROL_CHARACTER_LABELS = frozenset({"newline", "tab", "carriage_return"})
"""Cases whose raw character must never reach the SQL text. A raw newline inside a literal
would end a `--` comment line written above it and turn the rest of the value into SQL."""

INJECTION_PAYLOADS = (INJECTION, DROP_PAYLOAD, ESCAPED_QUOTE_INJECTION)

IDENTIFIER_CASES: tuple[tuple[str, str, str], ...] = (
    # (label, column name, the exact quoted Hive identifier sqlglot writes for it)
    # `select` is a legal Hive column name and an illegal bare identifier.
    ("reserved_word", "select", "`select`"),
    # A backtick inside a name is doubled, Hive's own rule. Below sqlglot 25.24.2 it isn't.
    ("embedded_backtick", "ok" + BACKTICK + "id", "`ok``id`"),
    # A name that tries to add a FROM clause stays one name.
    (
        "hostile_name",
        "id" + BACKTICK + " from mart.other --",
        "`id`` from mart.other --`",
    ),
)


class SneakyInt(int):
    """A well-typed whole number whose `str()` is SQL. `isinstance(x, int)` is True.

    sqlglot turns a number into a literal by calling `str()` on it and writes that text
    verbatim, so a Toolbox that relied on that would write `late_flag = 0 OR 1=1`.
    """

    def __str__(self) -> str:
        return "0 OR 1=1"

    def __format__(self, spec: str) -> str:
        return "0 OR 1=1"


class SneakyDecimal(decimal.Decimal):
    """The same trick through a decimal."""

    def __str__(self) -> str:
        return "1) /*"

    def __format__(self, spec: str) -> str:
        return "1) /*"


SNEAKY_NUMBERS: tuple[tuple[object, str], ...] = (
    # (value, the only Hive text the Toolbox may write for it)
    (SneakyInt(7), "7"),
    (SneakyDecimal("2.50"), "2.50"),
)

NON_FINITE_NUMBERS: tuple[object, ...] = (
    float("nan"),
    float("inf"),
    float("-inf"),
    decimal.Decimal("NaN"),
    decimal.Decimal("Infinity"),
    decimal.Decimal("-sNaN"),
)
"""Values the Toolbox must refuse rather than write. `exp.convert(nan)` is `NULL`, so
`amount > NULL` is never true and a Statement quietly returns no rows."""

NUMBER_CASES: tuple[tuple[str, object, str], ...] = (
    # (Hive type, value, the Hive text the Toolbox should write for it)
    ("BIGINT", 0, "0"),
    ("BIGINT", -12, "-12"),
    ("DECIMAL(18,2)", decimal.Decimal("1.50"), "1.50"),
    # `1E+3` would read as an identifier in Hive.
    ("DECIMAL(18,2)", decimal.Decimal("1E+3"), "1000"),
    ("DOUBLE", 0.1, "0.1"),
    ("DOUBLE", 1e-5, "1e-05"),
    ("DOUBLE", -0.0, "-0.0"),
)

NUMBER_TEXT = r"^-?\d+(\.\d+)?([eE][+-]?\d+)?$"
"""The shape every number the Toolbox writes must match."""


def has_bare_quote(literal_text: str) -> bool:
    """True when a `'` inside a written literal is not backslash-escaped.

    Hive ends a string literal at the first unescaped quote, so a bare quote inside is the
    breakout. This holds whatever escaping scheme sqlglot uses. Reading left to right and
    letting a backslash take the character after it is how Hive's lexer reads it.
    """
    body = literal_text[1:-1]
    index = 0
    while index < len(body):
        if body[index] == BACKSLASH:
            index += 2
            continue
        if body[index] == QUOTE:
            return True
        index += 1
    return False
