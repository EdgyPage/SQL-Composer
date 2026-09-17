"""The tripwire suite: Hive string escaping, identifier quoting, and the literal discipline.

This file exists because the library's safety against a quote in a value rests entirely on
sqlglot behaviour that sqlglot does not document. There is no injection guidance in its
docs, `Generator`'s Hive string escaping is an implementation detail, and sqlglot's minor
releases are deliberately backwards-incompatible (see
`docs/adr/0001-sqlglot-over-sqlalchemy.md` and the pin in `pyproject.toml`). An upgrade that
changed the escaping would otherwise be discovered in production, by a wrong number or by a
statement that ran something nobody wrote. Every golden string below is a snapshot of
30.18.0's actual output, taken by running it; a diff here on an upgrade is the signal, and
the correct response is to re-verify against Hive before re-recording it.

Three separate things are asserted, because each fails differently:

* EXACT OUTPUT (`test_hive_string_literal_escaping_is_exactly_this`). Catches any change at
  all, including one that is still safe. Deliberately brittle - that is the job.
* BEHAVIOUR (`test_..._round_trips`, `test_injection_payload_stays_inside_the_literal`).
  Catches a change that is not merely different but wrong: a payload that stops being a
  value and becomes syntax. `test_the_breakout_check_has_teeth` builds the same payload the
  forbidden way and asserts that check fires, so the passing ones are not vacuous.
* DISCIPLINE (the `discipline` tests at the bottom). A value must reach the AST as a
  string-literal node and never as text. These read the library's own source with Python's
  `ast` module, so an f-string or a `parse_one` added to the compiler fails here even if the
  payload it was tested with happened to be harmless.

One honest limit, worth knowing before trusting this file: the round-trip checks parse the
emitted SQL with sqlglot's own Hive parser, which proves sqlglot's generator and parser
agree - not that Hive agrees with either. Nothing in this environment can ask Hive. Do NOT
reach for duckdb as the oracle here: duckdb follows the SQL standard and treats a backslash
as an ordinary character, so `'O\\'Brien'` means something different to it than to Hive, and
a duckdb cross-check of escaping would report a failure that is not one (and, worse, could
pass something Hive would reject). duckdb is the right oracle for the VALUE tests, not for
this file.

The source is deliberately pure ASCII: every non-ASCII payload is written with `\\u`
escapes, so that a failure message printed to a cp1252 Windows console cannot itself raise
`UnicodeEncodeError` and hide the assertion that failed.
"""
from __future__ import annotations

import ast as python_ast
import datetime
import decimal
import pathlib
import re
from typing import Callable, Iterator

import pytest
import sqlglot
from sqlglot import exp

import sqlcomposer
from declarations import deliveries as fixture
from sqlcomposer import compile as compiler
from sqlcomposer import model, write
from sqlcomposer.declaration import Column, ColumnRef, Predicate, Registry, Source, Value

NUMERIC_TEXT = re.compile(r"^-?\d+(\.\d+)?([eE][+-]?\d+)?$")
"""The shape a numeric literal must render as. Written out here rather than imported from
the library, so that a change to the library's own pattern has to be re-argued here."""

# --------------------------------------------------------------------------------------
# Payloads. Built from `chr()`-free explicit constants so that reading the test does not
# require counting backslashes in a Python literal.
# --------------------------------------------------------------------------------------

BACKSLASH = "\\"
QUOTE = "'"
BACKTICK = "`"

INJECTION = QUOTE + " OR 1=1 --"
"""The classic payload: closes the literal, disjoins a tautology, comments out the rest."""

DROP_PAYLOAD = QUOTE + "; DROP TABLE mart.deliveries; --"
"""The other classic: closes the literal and starts a second statement."""

ESCAPED_QUOTE_INJECTION = BACKSLASH + QUOTE + " OR " + QUOTE + "1" + QUOTE + "=" + QUOTE + "1"
r"""`\' OR '1'='1` - the payload aimed at an escaper that handles a quote but forgets the
backslash in front of it. Hive escapes the backslash FIRST, so this one cannot break out;
if that order ever flips, this is the payload that proves it."""

UNICODE = "Berlin \u2013 M\u00fcnchen \u65e5\u672c\u8a9e \U0001f600"
"""En dash, umlaut, CJK and an emoji: a value Hive passes through as UTF-8 bytes."""

ESCAPING_CASES: tuple[tuple[str, str, str], ...] = (
    # (label, value, the exact Hive literal sqlglot 30.18.0 generates for it)
    ("plain", "delivered", "'delivered'"),
    ("single_quote", "O" + QUOTE + "Brien", r"'O\'Brien'"),
    ("backslash", "C:" + BACKSLASH + "temp", r"'C:\\temp'"),
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

CONTROL_CHARACTER_CASES: tuple[tuple[str, str, str], ...] = tuple(
    case for case in ESCAPING_CASES if case[0] in {"newline", "tab", "carriage_return"}
)
"""Derived rather than listed, so a control character added to the table above joins the
"never reaches the SQL text" test without a second edit."""


def _labels(cases: tuple[tuple[str, str, str], ...]) -> list[str]:
    return [label for label, _value, _expected in cases]


def _value_and_expected(
    cases: tuple[tuple[str, str, str], ...],
) -> list[tuple[str, str]]:
    return [(value, expected) for _label, value, expected in cases]


# --------------------------------------------------------------------------------------
# The columns every value test renders against, and the helpers around them.
# --------------------------------------------------------------------------------------

TEXT: ColumnRef = fixture.DELIVERIES.failure_reason
"""A plain STRING column. Not a Partition column, so `Column.literal` renders it through
`exp.convert` - the common path, and the one a Case-level Filter takes."""

PARTITIONED: ColumnRef = fixture.DELIVERIES.dt
"""A STRING PARTITION column. `Column.literal` renders this one as a bare
`exp.Literal.string` to keep Hive partition pruning, which is a second code path into the
AST and therefore a second place escaping could be skipped."""


def _render_literal(ref: ColumnRef, value: Value) -> str:
    """A value as Hive text, rendered the library's own way and nobody else's.

    `compile.literal` -> `ColumnRef.literal` -> `Column.literal` is the only supported way a
    Python value becomes a node, and `compile.render` is the only `.sql()` call in the
    library. Going through both is what makes these assertions statements about the library
    rather than about sqlglot in isolation.
    """
    return compiler.render(compiler.literal(ref, value))


def _parse(sql: str) -> list[exp.Expr]:
    """Every statement in `sql`, read back as Hive."""
    return [statement for statement in sqlglot.parse(sql, read=compiler.DIALECT) if statement]


def _parse_one(sql: str) -> exp.Expr:
    return sqlglot.parse_one(sql, read=compiler.DIALECT)


def _string_literals(tree: exp.Expr) -> set[str]:
    """Every string-literal VALUE in a tree, unescaped, as the parser recovered it."""
    return {node.this for node in tree.find_all(exp.Literal) if node.is_string}


def _has_bare_quote(literal_text: str) -> bool:
    """True when a `'` inside a rendered literal's body is not backslash-escaped.

    This is the one invariant that survives a change of escaping scheme: Hive ends a string
    literal at the first unescaped quote, so a bare quote in the body IS the breakout, and
    nothing after it is a value any more. Scanning left to right and letting a backslash
    consume the character after it is exactly how Hive's lexer reads it.

    Deliberately not "the raw payload is absent from the SQL": it is not, and cannot be.
    Escaping `' OR 1=1 --` inserts a backslash BEFORE the quote, so the payload still appears
    verbatim one character later, harmlessly. That near-miss assertion passes on the
    payloads a contributor tries first and fails on the ones that matter.
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


def _identifier_names(tree: exp.Expr) -> set[str]:
    return {node.name for node in tree.find_all(exp.Identifier)}


def _nodes_holding(tree: exp.Expr, value: str) -> list[exp.Expr]:
    """Every node whose own `this` is exactly `value`.

    This is the discipline probe. A value that entered the AST correctly is a
    `Literal(is_string=True)`; a value that entered as `exp.Var`, `exp.Identifier`,
    `exp.RawString` or the `this` of an `exp.Anonymous` function call is one of those types
    instead, and every one of those renders the value into the SQL with escaping that is
    either absent or wrong for a string.
    """
    return [node for node in tree.find_all(exp.Expr) if node.args.get("this") == value]


def _registry_with(*declared: object) -> Registry:
    """The fixture Declarations plus whatever this test needs, frozen.

    A fresh Registry per test rather than the session-scoped `registry` fixture: that one is
    frozen, and these tests need to add a Filter and a Case carrying a hostile value. Frozen
    here too, because `compile.plan` refuses an unfrozen Registry.
    """
    return Registry.from_modules(fixture, name="escaping").add(*declared).freeze()


def _case_filtered_by(label: str, value: str) -> tuple[Registry, model.Case]:
    """A one-Metric, one-Dimension Case whose WHERE clause compares to `value`.

    Everything is on `mart.deliveries`, so the Case needs no Join path and the emitted SQL
    is small enough that an assertion about its whole shape stays readable.
    """
    narrow = model.Filter("escaping_" + label, TEXT.eq(value))
    case = model.Case(
        name="escaping_" + label,
        metrics=model.by_name(fixture.DELIVERY_ATTEMPTS),
        grain=model.Grain.of(fixture.BY_DAY),
        filters=(narrow,),
    )
    return _registry_with(narrow, case), case


# ======================================================================================
# 1. Exact output. The upgrade tripwire.
# ======================================================================================


@pytest.mark.parametrize(
    ("value", "expected"), _value_and_expected(ESCAPING_CASES), ids=_labels(ESCAPING_CASES)
)
def test_hive_string_literal_escaping_is_exactly_this(value: str, expected: str) -> None:
    """Golden Hive text for every value shape that has ever broken an escaper.

    Recorded from sqlglot 30.18.0. A failure here means the pinned version changed how it
    escapes, which is exactly the event this file exists to catch; do not re-record the
    golden string without checking the new output against Hive's own lexer rules.

    The load-bearing row is `backslash_then_quote`: `\\'` becomes `'\\\\\\''`, which is the
    backslash doubled and THEN the quote escaped. An escaper that handled the quote first
    would emit `'\\\\''` and hand the payload a way out of the literal.
    """
    assert _render_literal(TEXT, value) == expected


@pytest.mark.parametrize(
    ("value", "expected"), _value_and_expected(ESCAPING_CASES), ids=_labels(ESCAPING_CASES)
)
def test_the_same_escaping_applies_on_a_partition_column(value: str, expected: str) -> None:
    """The bare-literal Partition path escapes identically to the `exp.convert` path.

    `Column.literal` renders a Partition column through `exp.Literal.string` instead of
    `exp.convert`, because a `CAST` in a PARTITION predicate defeats pruning. That is a
    second, hand-rolled way to a node, and the reason it is tested separately is that
    "bare" must mean "no CAST", never "no escaping".
    """
    rendered = _render_literal(PARTITIONED, value)
    assert rendered == expected
    assert "CAST(" not in rendered


def test_empty_string_is_two_quotes_and_is_not_null() -> None:
    """`''` and `NULL` are different values, and Hive treats them differently.

    An escaper that renders the empty string as nothing at all produces `column = ` and a
    parse error; one that renders it as NULL produces a predicate that is never true and a
    Case that silently reports zero rows.
    """
    assert _render_literal(TEXT, "") == "''"
    assert _render_literal(TEXT, None) == "NULL"


def test_unicode_is_passed_through_unchanged() -> None:
    """Non-ASCII text is not escaped, mangled or transliterated.

    Hive literals are UTF-8, so the right behaviour is no behaviour. This is here because an
    escaper that starts `\\u`-escaping non-ASCII would change the value silently: the query
    still runs, and `region = 'M\\u00fcnchen'` simply matches nothing.
    """
    rendered = _render_literal(TEXT, UNICODE)
    assert rendered == QUOTE + UNICODE + QUOTE
    assert _string_literals(_parse_one(rendered)) == {UNICODE}


@pytest.mark.parametrize(
    ("value", "expected"), _value_and_expected(ESCAPING_CASES), ids=_labels(ESCAPING_CASES)
)
def test_no_bare_quote_survives_inside_the_literal(value: str, expected: str) -> None:
    """The scheme-independent half of the golden assertion: nothing closes the literal early.

    The golden test above fails on any change at all, which is what a tripwire should do but
    says nothing about which changes are dangerous. This one says it: whatever escaping
    sqlglot uses, a `'` in the body must be backslash-escaped, because Hive ends the literal
    at the first one that is not.

    Run over EVERY payload rather than only the risky ones, so a payload added to the table
    above with no quote in it still gets this check for free.
    """
    rendered = _render_literal(TEXT, value)
    assert rendered.startswith(QUOTE) and rendered.endswith(QUOTE)
    assert not _has_bare_quote(rendered), "the value closed its own literal"
    assert rendered == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    _value_and_expected(CONTROL_CHARACTER_CASES),
    ids=_labels(CONTROL_CHARACTER_CASES),
)
def test_control_characters_are_escaped_not_embedded(value: str, expected: str) -> None:
    """A newline, tab or carriage return in a value stays out of the SQL TEXT.

    This is not cosmetic. `write.StatementPlan.to_script()` emits `-- <purpose>` comment
    lines and `;`-terminated statements, and a rendered Partition literal appears inside
    that comment. A raw newline inside a literal would end the comment line, and everything
    after it in the payload would be parsed as SQL.
    """
    rendered = _render_literal(TEXT, value)
    assert rendered == expected
    assert "\n" not in rendered
    assert "\r" not in rendered
    assert "\t" not in rendered
    assert len(rendered.splitlines()) == 1


# ======================================================================================
# 2. Behaviour. The payload stays a value.
# ======================================================================================


@pytest.mark.parametrize(
    ("value", "_expected"), _value_and_expected(ESCAPING_CASES), ids=_labels(ESCAPING_CASES)
)
def test_an_escaped_literal_parses_back_to_the_original_value(value: str, _expected: str) -> None:
    """Round trip: generate, re-read, and get the same Python value back.

    Proves the escaping is not merely different from the raw text but reversible - an
    escaper that dropped a backslash would pass the "not verbatim" test and still corrupt
    the value. Parsed with sqlglot's own Hive parser, which is the only Hive-shaped reader
    available here; see the module docstring for what that does and does not prove.
    """
    parsed = _parse_one(_render_literal(TEXT, value))
    assert isinstance(parsed, exp.Literal)
    assert parsed.is_string
    assert parsed.this == value


@pytest.mark.parametrize(
    ("payload", "expected_literal"),
    [
        (INJECTION, r"'\' OR 1=1 --'"),
        (DROP_PAYLOAD, r"'\'; DROP TABLE mart.deliveries; --'"),
        (ESCAPED_QUOTE_INJECTION, r"'\\\' OR \'1\'=\'1'"),
    ],
    ids=["or_1_eq_1", "stacked_drop", "escaped_quote"],
)
def test_injection_payload_stays_inside_the_literal(payload: str, expected_literal: str) -> None:
    """The whole compiler, end to end, with a payload where a business value goes.

    Goes through `compile_case` rather than `Column.literal` so that the qualify() gate and
    `ErrorLevel.RAISE` generation are in the path: qualify rewrites the tree it is handed,
    and a rewrite that re-parsed a literal would undo the escaping at the last moment.

    The four assertions are the four shapes a breakout takes: a second statement, a
    tautology disjoined onto the WHERE clause, a comment swallowing the rest of the
    statement, and a different table being read.
    """
    registry, case = _case_filtered_by("payload", payload)
    compiled = compiler.compile_case(registry, case)

    statements = _parse(compiled.sql)
    assert len(statements) == 1, "the payload started a second statement"
    tree = statements[0]

    assert not list(tree.find_all(exp.Or)), "the payload became a disjunction"
    comparisons = list(tree.find_all(exp.EQ))
    assert len(comparisons) == 1, "the payload added a comparison"
    assert comparisons[0].expression.this == payload, "the value did not survive intact"
    assert {table.name for table in tree.find_all(exp.Table)} == {"deliveries"}
    assert expected_literal in compiled.sql, "the payload reached the statement unescaped"


def test_the_breakout_check_has_teeth() -> None:
    """The negative control: the SAME payload, assembled the forbidden way, does break out.

    Without this, every assertion in `test_injection_payload_stays_inside_the_literal` could
    be passing for a trivial reason - a parser that never produces `exp.Or`, say - and the
    suite would report safety it had not checked. Here the payload is interpolated into SQL
    text exactly as `decision 10` forbids, and the parse shows what that costs: the value
    stops being a value.

    Nothing in `sqlcomposer` may build SQL this way, which is what the discipline tests at
    the bottom of this file enforce statically.
    """
    interpolated = (
        "SELECT 1 FROM mart.deliveries WHERE failure_reason = " + QUOTE + INJECTION + QUOTE
    )
    tree = _parse_one(interpolated)

    assert list(tree.find_all(exp.Or)), "the control payload failed to break out"
    assert INJECTION not in _string_literals(tree)
    # and the cheap detector the golden tests lean on sees it too
    assert _has_bare_quote(QUOTE + INJECTION + QUOTE)
    assert not _has_bare_quote(r"'\' OR 1=1 --'")


PREDICATE_BUILDERS: dict[str, Callable[[ColumnRef, str], Predicate]] = {
    "eq": lambda ref, value: ref.eq(value),
    "ne": lambda ref, value: ref.ne(value),
    "gt": lambda ref, value: ref.gt(value),
    "ge": lambda ref, value: ref.ge(value),
    "lt": lambda ref, value: ref.lt(value),
    "le": lambda ref, value: ref.le(value),
    "isin": lambda ref, value: ref.isin(value, "other"),
    "not_in": lambda ref, value: ref.not_in(value, "other"),
    "between": lambda ref, value: ref.between(value, value),
    "like": lambda ref, value: ref.like("%" + value + "%"),
}
"""Every public way from a Python value into a predicate. `like` is listed because it is
the one builder that does NOT go through `Column.literal` - it builds `exp.Literal.string`
itself - so it is the likeliest place for the discipline to be broken by accident."""


@pytest.mark.parametrize("builder", sorted(PREDICATE_BUILDERS), ids=sorted(PREDICATE_BUILDERS))
def test_every_predicate_constructor_escapes_its_values(builder: str) -> None:
    """One payload through each predicate builder, because each one renders its own values.

    `isin` renders a list, `between` renders two ends, `like` renders a pattern that a
    contributor is invited to concatenate into. A single tested builder would say nothing
    about the other nine.
    """
    predicate = PREDICATE_BUILDERS[builder](TEXT, INJECTION)
    rendered = compiler.render(predicate.to_sqlglot())

    assert BACKSLASH + QUOTE in rendered, "nothing was escaped at all"
    assert len(_parse(rendered)) == 1
    tree = _parse_one(rendered)
    assert not list(tree.find_all(exp.Or))
    assert any(INJECTION in literal for literal in _string_literals(tree))


def test_a_metric_scoped_filter_escapes_too(registry: Registry) -> None:
    """A `when` Filter becomes a conditional aggregate, and that is a different renderer.

    A Case-level Filter is rendered by `compile.build` into a WHERE clause; a Metric-scoped
    one is rendered by `grain.aggregate_expression` into `CASE WHEN ... THEN 1 ELSE 0 END`.
    Two renderers, one guarantee - and the second one is easy to forget, because no Case in
    the fixture carries a hostile value.
    """
    scoped = model.Filter("nasty_when", TEXT.eq(INJECTION))
    metric = model.count_rows("nasty_when_metric", fixture.DELIVERIES, when=scoped)

    rendered = compiler.compile_metric_only(registry, metric)

    assert r"'\' OR 1=1 --'" in rendered
    assert not list(_parse_one(rendered).find_all(exp.Or))
    assert _string_literals(_parse_one(rendered)) == {INJECTION}


# ======================================================================================
# 3. The write path: PARTITION clauses and `;`-separated scripts.
# ======================================================================================


def test_insert_overwrite_partition_literal_is_escaped(
    registry: Registry, run_date: datetime.date
) -> None:
    """A Partition value is rendered by `write`, not by `compile.build` - check it too.

    `Statement.partition` carries the literal as text, quotes included, so an operator can
    see which Partition a retry replaces. That text is generated by `compile.render` off
    `Column.literal`, and this asserts it stays escaped all the way into that field and into
    the INSERT statement itself.
    """
    payload = "2026-09-17" + INJECTION
    statement = write.insert_overwrite(
        registry, fixture.ACCOUNTABLE_BY_DAY, run_date=run_date, partition={"dt": payload}
    )

    assert statement.partition == (("dt", r"'2026-09-17\' OR 1=1 --'"),)
    assert payload not in statement.sql
    assert len(_parse(statement.sql)) == 1
    assert payload in _string_literals(_parse_one(statement.sql))


@pytest.mark.parametrize(
    "payload",
    ["2026-09-17" + DROP_PAYLOAD, "2026-09-17" + QUOTE + "\n-- hidden\nSELECT 1"],
    ids=["stacked_drop", "newline_escape"],
)
def test_a_payload_cannot_terminate_a_statement_in_a_script(
    registry: Registry, run_date: datetime.date, payload: str
) -> None:
    """The end of the chain: a payload pasted into a `;`-separated execution script.

    `StatementPlan.to_script()` is the lossy convenience an execution script pastes into a
    scheduler, and it is where an escaped literal meets two new pieces of syntax it did not
    meet before: a `;` terminator and a `--` comment line carrying the statement's purpose.
    The `newline_escape` payload is the one that matters - a raw newline inside the literal
    would end the purpose comment and turn the rest of the payload into script.
    """
    plan = write.plan(
        registry, [fixture.ACCOUNTABLE_BY_DAY], run_date=run_date, partition={"dt": payload}
    )
    script = plan.to_script()
    statements = _parse(script)

    assert len(statements) == len(plan) == 1, "the payload split the script"
    assert isinstance(statements[0], exp.Insert), "the payload changed what the script does"
    assert payload not in script, "the payload reached the script unescaped"
    assert payload in _string_literals(statements[0]), "the payload was corrupted"


# ======================================================================================
# 4. Identifiers. A declared name is data too.
# ======================================================================================
#
# Declaration names are checked in rather than user-supplied, so a hostile column name is a
# smaller risk than a hostile value - but it is the same mechanism, it is generated from a
# warehouse nobody in this repo controls, and the quoting that protects it is the same
# undocumented sqlglot behaviour. All fixture names below are lower-case on purpose:
# qualify() normalises identifier case for Hive, and a mixed-case name would make these
# tests fail for a reason that has nothing to do with quoting.


def _compiled_for_column(table: str, column_name: str, *, alias: str | None = None) -> str:
    """Compile a minimal Case over a Source carrying `column_name`, and return the SQL."""
    source = Source(
        db="mart",
        table=table,
        columns=(Column(column_name, "STRING"), Column("dt", "STRING")),
    )
    metric = model.count_of(table + "_count", source.column(column_name))
    dimension = model.Dimension(source.dt, alias=alias)
    case = model.Case(
        name=table + "_case",
        metrics=model.by_name(metric),
        grain=model.Grain.of(dimension),
    )
    registry = Registry(name=table).add(source, metric, case).freeze()
    return compiler.compile_case(registry, case).sql


def test_identifiers_are_backtick_quoted() -> None:
    """Every identifier in the output is quoted, so a reserved word cannot be syntax.

    `select` is a legal Hive column name and an illegal bare identifier. Unquoted, the
    statement is a parse error at best; the same is true of any column a future Hive adds to
    its keyword list, which is why the gate quotes everything rather than guessing.
    """
    sql = _compiled_for_column("reserved", "select")

    assert "`select`" in sql
    assert "COUNT(`reserved`.`select`)" in sql
    assert len(_parse(sql)) == 1


def test_an_embedded_backtick_in_a_column_name_is_doubled() -> None:
    """A backtick inside an identifier is escaped by doubling, Hive's own rule.

    The identifier counterpart of the string tests, and it fails differently: a single
    backtick would close the quoted identifier early, and the remainder of the name would be
    parsed as SQL rather than as a name.
    """
    sql = _compiled_for_column("backticked", "ok" + BACKTICK + "id")

    assert "`ok``id`" in sql
    assert "ok" + BACKTICK + "id" in _identifier_names(_parse_one(sql))


def test_a_hostile_column_name_cannot_break_out_of_its_quotes() -> None:
    """A declared name that tries to add a FROM clause stays a name.

    The identifier equivalent of the injection payload. The assertion that matters is the
    table set: a breakout would read `mart.other`, and a Case that silently reads a
    different table reports numbers that are wrong in a way no review would catch.
    """
    hostile = "id" + BACKTICK + " from mart.other --"
    sql = _compiled_for_column("hostile", hostile)

    statements = _parse(sql)
    assert len(statements) == 1
    assert {table.name for table in statements[0].find_all(exp.Table)} == {"hostile"}
    assert hostile in _identifier_names(statements[0])


def test_a_dimension_alias_is_quoted_and_its_backtick_doubled() -> None:
    """An output name is an identifier too, and it is the one a contributor types freely.

    `Dimension(alias=...)` is free text in a Declaration and lands in `AS <alias>`, which is
    the same escaping surface as a column name reached from the far side of the statement.
    """
    sql = _compiled_for_column("aliased", "col", alias="we" + BACKTICK + "ird")

    assert "AS `we``ird`" in sql
    assert "we" + BACKTICK + "ird" in _identifier_names(_parse_one(sql))


# ======================================================================================
# 4b. Numbers. A number is not a string, so NOTHING escapes it.
# ======================================================================================
#
# Everything above rests on "sqlglot escapes string-literal nodes". A numeric literal node
# is not one: sqlglot stores the TEXT it was handed (`Literal(this=str(value),
# is_string=False)`) and emits it verbatim. So for numbers the guarantee has to come from
# this library formatting that text itself, because `Column.accepts` constrains a value's
# TYPE and says nothing about the characters its `__str__` produces.


class _SneakyInt(int):
    """A well-typed BIGINT whose `str()` is SQL. `isinstance(x, int)` is True."""

    def __str__(self) -> str:  # pragma: no cover - called only if the library regresses
        return "0 OR 1=1"

    def __format__(self, spec: str) -> str:  # pragma: no cover - same
        return "0 OR 1=1"


class _SneakyDecimal(decimal.Decimal):
    """The same trick through the DECIMAL path."""

    def __str__(self) -> str:  # pragma: no cover - same
        return "1) /*"

    def __format__(self, spec: str) -> str:  # pragma: no cover - same
        return "1) /*"


def test_a_numeric_values_own_str_cannot_reach_the_sql() -> None:
    """The payload is the value's `__str__`, which no escaping anywhere would catch.

    `exp.convert(number)` funnels into `Literal.number(str(value))`, so this used to be a
    literal channel from a value's own code into the statement as SYNTAX: the WHERE clause
    became `late_flag = 0 OR 1=1`, a tautology, and the Case reported every row with no
    refusal. Neither the `qualify()` gate nor `ErrorLevel.RAISE` catches it - a Literal is
    not re-resolved and is not an unsupported construct.
    """
    predicate = fixture.DELIVERIES.late_flag.eq(_SneakyInt(7))
    sql = compiler.render(predicate.to_sqlglot())

    assert sql == "deliveries.late_flag = 7"
    assert "OR" not in sql

    # ...and through the Partition branch, which decides which Partition a write destroys.
    partitioned = Column("bucket", "BIGINT", partition=True)
    assert compiler.render(partitioned.literal(_SneakyInt(1))) == "1"
    assert compiler.render(fixture.DELIVERIES.fee_amount.literal(_SneakyDecimal("2.50"))) == "2.50"


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        decimal.Decimal("NaN"),
        decimal.Decimal("Infinity"),
        decimal.Decimal("-sNaN"),
    ],
    ids=["nan", "inf", "-inf", "decimal-nan", "decimal-inf", "decimal-snan"],
)
def test_a_non_finite_number_is_refused_rather_than_rendered(value: object) -> None:
    """Both spellings of a non-finite number are silent wrong numbers, so neither renders.

    `exp.convert(nan)` is `NULL`, and `fee_amount > NULL` is never true - the Case reports
    zero rows and looks like a quiet day. On a Partition column the same value renders as
    the bare token `nan`, which Hive resolves as a column reference. A NaN from a `0/0` or
    an upstream pandas aggregation is the realistic source, and there is nothing it could
    correctly mean against a warehouse column.
    """
    with pytest.raises(sqlcomposer.DeclarationError) as refused:
        fixture.DELIVERIES.fee_amount.gt(value)  # type: ignore[arg-type]

    assert refused.value.column == "mart.deliveries.fee_amount"
    assert "finite" in refused.value.problem

    with pytest.raises(sqlcomposer.DeclarationError):
        Column("rate", "DOUBLE", partition=True).literal(value)  # type: ignore[arg-type]

    # The adjacent build: a finite value of the same type still renders.
    assert compiler.render(
        fixture.DELIVERIES.fee_amount.gt(decimal.Decimal("1.50")).to_sqlglot()
    ) == "deliveries.fee_amount > 1.50"


@pytest.mark.parametrize(
    ("declared", "value", "expected"),
    [
        ("BIGINT", 0, "0"),
        ("BIGINT", -12, "-12"),
        ("DECIMAL(18,2)", decimal.Decimal("1.50"), "1.50"),
        ("DECIMAL(18,2)", decimal.Decimal("1E+3"), "1000"),
        ("DOUBLE", 0.1, "0.1"),
        ("DOUBLE", 1e-5, "1e-05"),
        ("DOUBLE", -0.0, "-0.0"),
    ],
)
def test_every_numeric_literal_renders_as_a_bare_number(
    declared: str, value: object, expected: str
) -> None:
    """The text of a numeric node always matches `-?digits[.digits][e[+-]digits]`.

    Asserted as exact output rather than as a regex over the implementation, so a future
    formatting change - a Decimal rendered as `1E+3`, say, which Hive reads as an
    identifier - fails here with the text that changed.
    """
    column = Column("n", declared)
    rendered = compiler.render(column.literal(value))  # type: ignore[arg-type]

    assert rendered == expected
    assert NUMERIC_TEXT.match(rendered), rendered


# ======================================================================================
# 5. Discipline. Read the library's own source, so a new f-string path fails here.
# ======================================================================================
#
# The tests above prove the CURRENT paths escape. These prove no new path exists: the
# guarantee is "sqlglot escapes string-literal nodes and nothing else", so any way from a
# Python value to SQL text that does not pass through a node is outside it, no matter how
# harmless the value that way was first written for.


def _library_sources() -> Iterator[tuple[str, str]]:
    """Every module of the library, as (file name, source text)."""
    root = pathlib.Path(sqlcomposer.__file__).resolve().parent
    for path in sorted(root.glob("*.py")):
        yield path.name, path.read_text(encoding="utf-8")


def _library_calls() -> Iterator[tuple[str, python_ast.Call]]:
    """Every call expression in the library, with the file it appears in.

    Parsed with Python's `ast` rather than grepped, so a mention of `.sql()` in a docstring
    or a comment - and this library is mostly docstrings - is not a finding.
    """
    for name, source in _library_sources():
        for node in python_ast.walk(python_ast.parse(source)):
            if isinstance(node, python_ast.Call):
                yield name, node


def _callee(call: python_ast.Call) -> str:
    return python_ast.unparse(call.func)


def _enclosing_function(file_name: str, line: int) -> str:
    """The innermost function containing `line`, for naming the offender in a failure."""
    for name, source in _library_sources():
        if name != file_name:
            continue
        best = ""
        best_line = -1
        for node in python_ast.walk(python_ast.parse(source)):
            if isinstance(node, (python_ast.FunctionDef, python_ast.AsyncFunctionDef)):
                end = node.end_lineno or node.lineno
                if node.lineno <= line <= end and node.lineno > best_line:
                    best, best_line = node.name, node.lineno
        return best
    return ""


def test_the_library_generates_sql_in_exactly_one_place() -> None:
    """One `.sql()` call, in `compile.render`, passing `unsupported_level`.

    Generation is where escaping happens, so every additional generation site is a place the
    escaping discipline has to be re-established - and, historically, the place someone adds
    a second `.sql()` call without `unsupported_level=ErrorLevel.RAISE` and gets sqlglot's
    default best-effort translation with a log line nobody reads.
    """
    generation = [
        (file_name, call) for file_name, call in _library_calls() if _callee(call).endswith(".sql")
    ]

    assert len(generation) == 1, [
        (name, call.lineno, _enclosing_function(name, call.lineno)) for name, call in generation
    ]
    file_name, call = generation[0]
    assert file_name == "compile.py"
    assert _enclosing_function(file_name, call.lineno) == "render"

    # The keyword's VALUE, not merely its name. Asserting the name alone let
    # `unsupported_level=ErrorLevel.IGNORE` pass this test - the exact mistake the docstring
    # above names - because a keyword that is present and wrong looks identical to a
    # keyword that is present and right.
    passed = {keyword.arg: python_ast.unparse(keyword.value) for keyword in call.keywords}
    assert passed.get("unsupported_level") == "ERROR_LEVEL"
    assert compiler.ERROR_LEVEL is sqlglot.ErrorLevel.RAISE


def test_an_untranslatable_construct_raises_instead_of_being_best_effort_translated() -> None:
    """The behavioural half of `ErrorLevel.RAISE`: what the static check above cannot see.

    sqlglot's default is WARN, which best-effort translates a construct the target dialect
    cannot express and logs a line nobody reads. `exp.func("trunc", col, "MM")` is the case
    this library actually meets - it is why `grain._anonymous` exists - and under IGNORE it
    renders as `CAST(... AS BIGINT)`: a query that runs, returns numbers, and means
    something else entirely.

    Both halves are asserted, so the test cannot pass by the construct having become
    translatable: the same tree under IGNORE must still produce that different SQL.
    """
    column = fixture.DELIVERIES.dt.to_sqlglot()
    untranslatable = exp.func("trunc", column, "MM")

    with pytest.raises(sqlcomposer.RenderError) as refused:
        compiler.render(untranslatable)

    assert "trunc" in str(refused.value).lower() or "TRUNC" in refused.value.sqlglot_message
    best_effort = untranslatable.sql(
        dialect=compiler.DIALECT, unsupported_level=sqlglot.ErrorLevel.IGNORE
    )
    assert best_effort != "TRUNC(deliveries.dt, 'MM')", (
        "the construct is translatable now, so this test no longer proves anything"
    )

    # The adjacent build: a tree Hive CAN express renders, so this is not a test of a
    # renderer that refuses everything.
    assert compiler.render(exp.func("upper", column)) == "UPPER(deliveries.dt)"


FORBIDDEN_PARSERS = frozenset(
    {"parse", "parse_one", "maybe_parse", "condition", "transpile", "from_sql"}
)
"""sqlglot entry points that turn TEXT into an AST. Every one of them is a way for an
interpolated value to re-enter the tree as syntax, which is precisely what a string-literal
node prevents."""


def test_the_library_never_parses_sql_text() -> None:
    """No way from a string to an AST exists inside the library.

    `Predicate` documents "no `from_sql`, ever", and this is the check that keeps that a
    fact: a predicate parsed from text bypasses `Column.literal` and with it the whole
    escaping and declared-type guarantee, and it would look entirely reasonable in review.
    """
    offenders = [
        (file_name, call.lineno, _callee(call))
        for file_name, call in _library_calls()
        if _callee(call).rsplit(".", 1)[-1] in FORBIDDEN_PARSERS
    ]

    assert offenders == []
    assert not hasattr(Predicate, "from_sql")


def _is_interpolated(node: python_ast.expr) -> bool:
    """True for an f-string, a `.format(...)` call or a `"..." % ...` expression."""
    if isinstance(node, python_ast.JoinedStr):
        return True
    if isinstance(node, python_ast.Call) and isinstance(node.func, python_ast.Attribute):
        return node.func.attr == "format"
    return isinstance(node, python_ast.BinOp) and isinstance(node.op, python_ast.Mod)


def test_no_interpolated_string_is_passed_to_sqlglot() -> None:
    """No f-string, `.format` or `%` reaches a sqlglot constructor as an argument.

    This is the test that fails the day someone adds an f-string path into the compiler.
    `exp.Literal.string(f"{value}")` is the shape that looks harmless and is not: it works
    for every value anybody tries by hand, and it hands the AST a value the generator will
    escape a second time or not at all, depending on what was already in it.

    Scoped to arguments of `exp.*` and `sqlglot.*` calls on purpose: the library assembles
    plenty of prose with f-strings - refusal messages, Lineage text, the `-- purpose`
    comment in a script - and none of that is SQL.
    """
    offenders = [
        (file_name, call.lineno, _callee(call))
        for file_name, call in _library_calls()
        if _callee(call).startswith(("exp.", "sqlglot."))
        for argument in list(call.args) + [keyword.value for keyword in call.keywords]
        if _is_interpolated(argument)
    ]

    assert offenders == []


def test_a_value_lands_as_a_string_literal_node_and_never_as_raw_text() -> None:
    """The discipline, asserted on the tree rather than on the library's source.

    Every builder in `PREDICATE_BUILDERS` is walked for nodes whose `this` is the payload.
    There must be at least one - otherwise the value never made it in - and every one must
    be `Literal(is_string=True)`. An `exp.Var`, an `exp.Identifier` or the `this` of an
    `exp.Anonymous` would all carry the same payload and all render it into the statement
    with no string escaping at all.

    It also asserts the node holds the RAW value: escaping belongs to generation, and a node
    that stored the escaped text would be escaped twice the moment the tree is re-rendered -
    which is what `write.py` does when it embeds a gated SELECT into an INSERT.
    """
    for name, build in sorted(PREDICATE_BUILDERS.items()):
        if name == "like":
            continue  # its value is a pattern, asserted below with the % wrapper
        tree = build(TEXT, INJECTION).to_sqlglot()
        carriers = _nodes_holding(tree, INJECTION)

        assert carriers, name + " did not put the value into the tree at all"
        for node in carriers:
            assert isinstance(node, exp.Literal), name + " built a " + type(node).__name__
            assert node.is_string, name + " built a numeric literal from a string"
            assert node.this == INJECTION

    pattern = "%" + INJECTION + "%"
    like_carriers = _nodes_holding(PREDICATE_BUILDERS["like"](TEXT, INJECTION).to_sqlglot(), pattern)
    assert like_carriers
    assert all(isinstance(node, exp.Literal) and node.is_string for node in like_carriers)


def test_a_compiled_case_carries_the_payload_only_as_a_string_literal() -> None:
    """The same discipline over a whole compiled statement, after the qualify() gate.

    `qualify()` rewrites the tree - it quotes identifiers, adds aliases and expands stars -
    and the tree it returns is the one that gets rendered. This asserts the payload came out
    of that rewrite still a string-literal node, and that nothing in the rewrite turned it
    into an identifier or a function name along the way.
    """
    registry, case = _case_filtered_by("qualified", INJECTION)
    compiled = compiler.compile_case(registry, case)

    carriers = _nodes_holding(compiled.ast, INJECTION)
    assert len(carriers) == 1
    assert isinstance(carriers[0], exp.Literal)
    assert carriers[0].is_string
    assert compiled.ast.sql(dialect=compiler.DIALECT) == compiled.sql
