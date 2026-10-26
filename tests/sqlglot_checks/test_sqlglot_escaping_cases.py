"""The escaping matrix checked against sqlglot: the tripwire for a sqlglot upgrade.

Nothing here imports the Toolbox. These tests say what sqlglot's Hive writes for each case in
`escaping_cases.py` when it escapes a string by the Toolbox's table
(`trees.HIVE_ESCAPES`), as sqlglot Composer has it do, so a sqlglot version that changes how it
applies that table, quotes, or reads back fails here first. CI runs them at sqlglot's pin. A
failure means sqlglot changed how it escapes: check the new output against Hive's own lexer
rules before re-recording a case. (sqlglot's own table changed within the range, 30.23.0
writing NUL and SUB as \\0 and \\Z, which is why the Toolbox brings its own.)

The round trips parse with sqlglot's own Hive parser. That proves sqlglot's writer and reader
agree, not that Hive agrees with either; nothing on `dev` can ask Hive.
"""

from __future__ import annotations

import pytest
import sqlglot
from sqlglot import exp

from sqlglot_composer.trees import HIVE_ESCAPES
from escaping_cases import (
    CONTROL_CHARACTER_LABELS,
    IDENTIFIER_CASES,
    INJECTION,
    INJECTION_PAYLOADS,
    QUOTE,
    REFUSED_CONTROL_CHARACTERS,
    STRING_CASES,
    has_bare_quote,
)


def _hive_with_the_cores_escapes() -> sqlglot.Dialect:
    """sqlglot's Hive escaping a string's characters by the Toolbox's table, as sqlglot
    Composer's writer has it do; the quote is left to sqlglot."""
    hive = type(sqlglot.Dialect.get_or_raise("hive"))()
    hive.ESCAPED_SEQUENCES = {character: escaped for character, escaped
                              in HIVE_ESCAPES.items() if character != QUOTE}
    return hive


HIVE = _hive_with_the_cores_escapes()

STRING_IDS = [label for label, _value, _expected in STRING_CASES]
IDENTIFIER_IDS = [label for label, _name, _expected in IDENTIFIER_CASES]
ROUND_TRIP_CASES = [pytest.param(*case, id=case[0]) for case in IDENTIFIER_CASES]

CONTROL_CHARACTER_VALUES = [
    value
    for label, value, _expected in sorted(STRING_CASES)
    if label in CONTROL_CHARACTER_LABELS
]


def _where_equals(value: str) -> str:
    """A whole statement comparing a column to `value`, built as a tree and never as text."""
    condition = exp.EQ(this=exp.column("reason"), expression=exp.Literal.string(value))
    return exp.select("1").from_("mart.deliveries").where(condition).sql(dialect=HIVE)


@pytest.mark.parametrize(("_label", "value", "expected"), STRING_CASES, ids=STRING_IDS)
def test_a_string_literal_is_written_exactly_like_this(
    _label: str, value: str, expected: str
) -> None:
    assert exp.Literal.string(value).sql(dialect=HIVE) == expected
    assert exp.convert(value).sql(dialect=HIVE) == expected


@pytest.mark.parametrize(("_label", "value", "expected"), STRING_CASES, ids=STRING_IDS)
def test_no_bare_quote_survives_inside_a_literal(
    _label: str, value: str, expected: str
) -> None:
    written = exp.Literal.string(value).sql(dialect=HIVE)
    assert written.startswith(QUOTE) and written.endswith(QUOTE)
    assert not has_bare_quote(written), "the value closed its own literal"


@pytest.mark.parametrize(
    "value", CONTROL_CHARACTER_VALUES, ids=sorted(CONTROL_CHARACTER_LABELS)
)
def test_a_control_character_never_reaches_the_sql_text(value: str) -> None:
    written = exp.Literal.string(value).sql(dialect=HIVE)
    assert not {"\n", "\r", "\t"} & set(written)


READ_BACK_CASES = [
    pytest.param(
        *case,
        id=case[0],
        marks=pytest.mark.skipif(
            case[0] in REFUSED_CONTROL_CHARACTERS,
            reason="the Toolbox refuses this value: Hive reads its escape as a letter, and so "
            "does a newer sqlglot, such as 30.23.0",
        ),
    )
    for case in STRING_CASES
]


@pytest.mark.parametrize(("_label", "value", "expected"), READ_BACK_CASES)
def test_a_written_literal_reads_back_as_the_same_value(
    _label: str, value: str, expected: str
) -> None:
    parsed = sqlglot.parse_one(expected, read=HIVE)
    assert isinstance(parsed, exp.Literal)
    assert parsed.is_string
    assert parsed.this == value


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
def test_an_injection_payload_stays_one_value(payload: str) -> None:
    statements = [s for s in sqlglot.parse(_where_equals(payload), read=HIVE) if s]

    assert len(statements) == 1, "the payload started a second statement"
    tree = statements[0]
    assert not list(tree.find_all(exp.Or)), "the payload became an OR"
    comparisons = list(tree.find_all(exp.EQ))
    assert len(comparisons) == 1
    assert comparisons[0].expression.this == payload, "the value did not survive intact"
    assert {table.name for table in tree.find_all(exp.Table)} == {"deliveries"}


def test_the_breakout_check_has_teeth() -> None:
    """The same payload pasted into SQL text does break out, so the checks above can fail."""
    pasted = "SELECT 1 FROM mart.deliveries WHERE reason = " + QUOTE + INJECTION + QUOTE
    tree = sqlglot.parse_one(pasted, read=HIVE)

    assert list(tree.find_all(exp.Or)), "the control payload failed to break out"
    assert has_bare_quote(QUOTE + INJECTION + QUOTE)


@pytest.mark.parametrize(("_label", "name", "expected"), IDENTIFIER_CASES, ids=IDENTIFIER_IDS)
def test_an_identifier_is_quoted_exactly_like_this(
    _label: str, name: str, expected: str
) -> None:
    assert exp.to_identifier(name, quoted=True).sql(dialect=HIVE) == expected


@pytest.mark.parametrize(("_label", "name", "expected"), ROUND_TRIP_CASES)
def test_a_quoted_identifier_stays_one_name(_label: str, name: str, expected: str) -> None:
    column = exp.Column(this=exp.to_identifier(name, quoted=True))
    written = exp.select(column).from_("mart.deliveries").sql(dialect=HIVE)
    statements = [s for s in sqlglot.parse(written, read=HIVE) if s]

    assert len(statements) == 1
    assert {table.name for table in statements[0].find_all(exp.Table)} == {"deliveries"}
    assert name in {node.name for node in statements[0].find_all(exp.Identifier)}
