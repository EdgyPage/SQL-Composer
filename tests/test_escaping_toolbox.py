"""The escaping matrix, pushed through every way a value reaches a Statement.

`escaping_cases.py` holds the cases and `test_escaping_cases.py` checks them against sqlglot
alone. Here each case goes in through the Toolbox: each comparison function, both ends of a
range, each item of a list, a LIKE pattern, a calculation, a Date partition bound and the
PARTITION of an INSERT_OVERWRITE. Two more tests hold what the cases can't: SQL text is written
in exactly one function, and a number's text is written by the Toolbox, not by its own str().
"""

from __future__ import annotations

import ast
import datetime
import decimal
import re
from pathlib import Path

import pytest
import sqlglot
from sqlglot import exp

from escaping_cases import (
    IDENTIFIER_CASES,
    INJECTION_PAYLOADS,
    NON_FINITE_NUMBERS,
    NUMBER_CASES,
    NUMBER_TEXT,
    SNEAKY_NUMBERS,
    STRING_CASES,
)
from sql_composer import (
    AS,
    FROM,
    GROUP_BY,
    INSERT_OVERWRITE,
    SELECT,
    WHERE,
    GuardRefused,
    Table,
    at_least,
    at_most,
    between,
    contains,
    count_rows,
    equals,
    fill_null,
    hive_function,
    if_else,
    is_in,
    is_not_in,
    less_than,
    more_than,
    not_equals,
    starts_with,
    statement,
    to_hive,
)
from sql_composer.example_database import job_runs

TOOLBOX = Path(__file__).resolve().parent.parent / "sql_composer"
STRING_IDS = [label for label, _value, _expected in STRING_CASES]

COMPARISONS = [
    (equals, "="),
    (not_equals, "<>"),
    (at_least, ">="),
    (at_most, "<="),
    (more_than, ">"),
    (less_than, "<"),
]


def _statement_with(condition) -> str:
    return to_hive(statement(
        SELECT(job_runs.run_id),
        FROM(job_runs),
        WHERE(condition, equals(job_runs.dt, "2026-09-24")),
    ))


def _literals(hive: str) -> list[str]:
    """Every string literal's value in a Hive string, read back by sqlglot's Hive parser."""
    statements = [s for s in sqlglot.parse(hive, read="hive") if s]
    assert len(statements) == 1, "a value started a second statement"
    return [node.this for node in statements[0].find_all(exp.Literal) if node.is_string]


@pytest.mark.parametrize(("_label", "value", "expected"), STRING_CASES, ids=STRING_IDS)
@pytest.mark.parametrize(("function", "operator"), COMPARISONS,
                         ids=[f.__name__ for f, _ in COMPARISONS])
def test_each_comparison_writes_the_literal_exactly(function, operator, _label, value,
                                                    expected) -> None:
    assert repr(function(job_runs.status, value)) == f"job_runs.status {operator} {expected}"


@pytest.mark.parametrize(("_label", "value", "expected"), STRING_CASES, ids=STRING_IDS)
def test_both_ends_of_a_range(_label, value, expected) -> None:
    condition = between(job_runs.status, value, value)
    assert repr(condition) == f"job_runs.status BETWEEN {expected} AND {expected}"


@pytest.mark.parametrize(("_label", "value", "expected"), STRING_CASES, ids=STRING_IDS)
def test_each_item_of_a_list(_label, value, expected) -> None:
    assert repr(is_in(job_runs.status, ["a", value])) == f"job_runs.status IN ('a', {expected})"
    assert repr(is_not_in(job_runs.status, [value])) == f"NOT job_runs.status IN ({expected})"


@pytest.mark.parametrize(("_label", "value", "expected"), STRING_CASES, ids=STRING_IDS)
def test_calculations_escape_their_values(_label, value, expected) -> None:
    assert repr(fill_null(job_runs.status, value)) == f"COALESCE(job_runs.status, {expected})"
    assert expected in repr(if_else(equals(job_runs.status, "x"), value, "y"))
    assert repr(hive_function("upper", value)) == f"UPPER({expected})"


@pytest.mark.parametrize(("_label", "value", "_expected"), STRING_CASES, ids=STRING_IDS)
@pytest.mark.parametrize("function", [contains, starts_with])
def test_a_like_pattern_keeps_the_value_whole(function, _label, value, _expected) -> None:
    hive = _statement_with(function(job_runs.status, value))
    patterns = [literal for literal in _literals(hive) if literal != "2026-09-24"]
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    assert escaped in patterns[0]


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
@pytest.mark.parametrize(("function", "_operator"), COMPARISONS,
                         ids=[f.__name__ for f, _ in COMPARISONS])
def test_an_injection_payload_stays_one_value_in_a_whole_statement(function, _operator,
                                                                    payload) -> None:
    hive = _statement_with(function(job_runs.status, payload))
    assert payload in _literals(hive)
    tree = sqlglot.parse_one(hive, read="hive")
    assert not list(tree.find_all(exp.Or)), "the payload became an OR"


@pytest.mark.parametrize(("_label", "value", "_expected"), STRING_CASES, ids=STRING_IDS)
def test_a_date_partition_bound_refuses_anything_but_a_day(_label, value, _expected) -> None:
    with pytest.raises(ValueError, match="isn't a day"):
        equals(job_runs.dt, value)
    with pytest.raises(ValueError, match="isn't a day"):
        between(job_runs.dt, "2026-09-23", value)


def test_the_partition_of_a_write_is_the_day_the_toolbox_formats() -> None:
    saved = Table("mart.odd", columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
                  date_partition="dt")
    hive = to_hive(statement(
        INSERT_OVERWRITE(saved),
        SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, datetime.date(2026, 9, 24))),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    ))
    assert "PARTITION(dt = '2026-09-24')" in hive
    assert _literals(hive) == ["2026-09-24", "2026-09-24"]


@pytest.mark.parametrize("pattern", ["%Y%m%d'", "%Y-%m-%d %H", "%Y%m"])
def test_a_date_format_that_could_carry_sql_is_refused(pattern) -> None:
    with pytest.raises(ValueError):
        Table("mart.odd", columns={"dt": "string"}, date_partition="dt", date_format=pattern)


@pytest.mark.parametrize(("label", "name", "expected"), IDENTIFIER_CASES,
                         ids=[label for label, _n, _e in IDENTIFIER_CASES])
def test_a_column_name_is_quoted_exactly_like_this(label, name, expected) -> None:
    odd = Table("ops.odd", columns={name: "string"}, date_partition=None)
    assert repr(getattr(odd, name)) == f"odd.{expected}"


# --- Numbers --------------------------------------------------------------------------------

numbers = Table(
    "ops.numbers",
    columns={"b": "bigint", "d": "decimal(18,2)", "x": "double"},
    date_partition=None,
)
COLUMN_OF = {"BIGINT": numbers.b, "DECIMAL(18,2)": numbers.d, "DOUBLE": numbers.x}


@pytest.mark.parametrize(("hive_type", "value", "expected"), NUMBER_CASES)
def test_a_number_is_written_like_this(hive_type, value, expected) -> None:
    column = COLUMN_OF[hive_type]
    written = repr(equals(column, value)).split(" = ")[1]
    assert written == expected
    assert re.fullmatch(NUMBER_TEXT, written)


@pytest.mark.parametrize(("value", "expected"), SNEAKY_NUMBERS, ids=["int", "decimal"])
def test_a_number_is_written_by_the_toolbox_not_by_its_own_str(value, expected) -> None:
    assert repr(equals(numbers.d, value)) == f"numbers.d = {expected}"
    assert repr(numbers.b + value) == f"numbers.b + {expected}"


@pytest.mark.parametrize("value", NON_FINITE_NUMBERS, ids=repr)
def test_a_non_finite_number_is_refused(value) -> None:
    with pytest.raises(GuardRefused):
        equals(numbers.x, value)
    with pytest.raises(GuardRefused, match="item 2"):
        is_in(numbers.x, [1.0, value])


def test_a_decimal_that_python_would_write_as_an_exponent_is_written_whole() -> None:
    assert repr(equals(numbers.d, decimal.Decimal("1E+3"))) == "numbers.d = 1000"


# --- Where SQL text comes from --------------------------------------------------------------


def _toolbox_trees():
    return {path.name: ast.parse(path.read_text(encoding="utf-8"))
            for path in sorted(TOOLBOX.glob("*.py"))}


def test_sql_text_is_written_in_exactly_one_function() -> None:
    callers = []
    for name, tree in _toolbox_trees().items():
        for function in ast.walk(tree):
            if not isinstance(function, ast.FunctionDef):
                continue
            for call in ast.walk(function):
                if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                        and call.func.attr == "sql"):
                    callers.append((name, function.name, call))
    # The import-time behaviour checks in __init__.py call .sql() on sqlglot's own nodes to
    # check sqlglot itself; they write nothing the Toolbox sends.
    writers = [(name, fn) for name, fn, _ in callers if name != "__init__.py"]
    assert writers == [("tables.py", "hive_text")]
    raising = [call for name, fn, call in callers if fn == "hive_text"][0]
    keywords = {k.arg: ast.unparse(k.value) for k in raising.keywords}
    assert keywords["unsupported_level"] == "ErrorLevel.RAISE"


def test_no_sql_text_is_built_with_an_f_string() -> None:
    """No f-string or .format() is handed to sqlglot, so no value can be pasted into SQL."""
    for name, tree in _toolbox_trees().items():
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call):
                continue
            target = ast.unparse(call.func)
            if not target.startswith(("exp.", "sqlglot.")):
                continue
            for argument in [*call.args, *(k.value for k in call.keywords)]:
                assert not isinstance(argument, ast.JoinedStr), f"{name}: {ast.unparse(call)}"
                assert not (isinstance(argument, ast.Call)
                            and ast.unparse(argument.func).endswith(".format")), name
