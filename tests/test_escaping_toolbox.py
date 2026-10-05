"""The escaping matrix, pushed through every way a value reaches a Statement.

`escaping_cases.py` holds the cases. Here each case goes in through the Toolbox: each comparison
function, both ends of a range, each item of a list, a calculation and a Date partition bound,
and a number's text is written by the Toolbox, not by its own str(). The last checks read a whole
Statement's Hive back by its characters, with `hive_literals.py`, so they hold in both Editions.
"""

from __future__ import annotations

import datetime
import decimal
import re

import pytest

import hive_literals
from conftest import in_this_edition
from escaping_cases import (
    IDENTIFIER_CASES,
    INJECTION_PAYLOADS,
    NON_FINITE_NUMBERS,
    NUMBER_CASES,
    NUMBER_TEXT,
    REFUSED_CONTROL_CHARACTERS,
    SNEAKY_NUMBERS,
    STRING_CASES,
    WRITTEN,
    WRITTEN_IDS,
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
from composer_core.example_database import job_runs

# The cases the Toolbox refuses, checked on their own below; it writes the rest (WRITTEN).
REFUSED = [case for case in STRING_CASES if case[0] in REFUSED_CONTROL_CHARACTERS]

COMPARISONS = [
    (equals, "="),
    (not_equals, "<>"),
    (at_least, ">="),
    (at_most, "<="),
    (more_than, ">"),
    (less_than, "<"),
]


@pytest.mark.parametrize(("_label", "value", "expected"), WRITTEN, ids=WRITTEN_IDS)
@pytest.mark.parametrize(("function", "operator"), COMPARISONS,
                         ids=[f.__name__ for f, _ in COMPARISONS])
def test_each_comparison_writes_the_literal_exactly(function, operator, _label, value,
                                                    expected) -> None:
    assert repr(function(job_runs.status, value)) == f"job_runs.status {operator} {expected}"


@pytest.mark.parametrize(("_label", "value", "expected"), WRITTEN, ids=WRITTEN_IDS)
def test_both_ends_of_a_range(_label, value, expected) -> None:
    condition = between(job_runs.status, value, value)
    assert repr(condition) == f"job_runs.status BETWEEN {expected} AND {expected}"


@pytest.mark.parametrize(("_label", "value", "expected"), WRITTEN, ids=WRITTEN_IDS)
def test_each_item_of_a_list(_label, value, expected) -> None:
    assert repr(is_in(job_runs.status, ["a", value])) == f"job_runs.status IN ('a', {expected})"
    assert repr(is_not_in(job_runs.status, [value])) == f"NOT job_runs.status IN ({expected})"


@pytest.mark.parametrize(("_label", "value", "expected"), WRITTEN, ids=WRITTEN_IDS)
def test_calculations_escape_their_values(_label, value, expected) -> None:
    assert repr(fill_null(job_runs.status, value)) == f"COALESCE(job_runs.status, {expected})"
    assert expected in repr(if_else(equals(job_runs.status, "x"), value, "y"))
    assert repr(hive_function("upper", value)) == f"UPPER({expected})"


@pytest.mark.parametrize(("_label", "value", "_expected"), REFUSED,
                         ids=[label for label, _value, _expected in REFUSED])
def test_a_control_character_hive_reads_as_a_letter_is_refused_everywhere(_label, value,
                                                                           _expected) -> None:
    for make in (lambda: equals(job_runs.status, value),
                 lambda: not_equals(job_runs.status, value),
                 lambda: between(job_runs.status, "a", value),
                 lambda: is_in(job_runs.status, ["a", value]),
                 lambda: is_not_in(job_runs.status, [value]),
                 lambda: fill_null(job_runs.status, value),
                 lambda: if_else(equals(job_runs.status, "x"), value, "y"),
                 lambda: hive_function("upper", value),
                 lambda: contains(job_runs.status, value),
                 lambda: starts_with(job_runs.status, value)):
        with pytest.raises(GuardRefused, match="reads back as the plain letter"):
            make()


def test_a_date_format_holding_a_control_character_is_refused() -> None:
    with pytest.raises(ValueError, match="isn't printed"):
        Table("ops.t", columns={"dt": "string"}, date_partition="dt", date_format="%Y\x07%m%d")


@pytest.mark.parametrize(("_label", "value", "_expected"), WRITTEN, ids=WRITTEN_IDS)
def test_a_date_partition_bound_refuses_anything_but_a_day(_label, value, _expected) -> None:
    with pytest.raises(ValueError, match="isn't a day"):
        equals(job_runs.dt, value)
    with pytest.raises(ValueError, match="isn't a day"):
        between(job_runs.dt, "2026-09-23", value)


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


@pytest.mark.parametrize(("hive_type", "value", "sql_composer", "spark_composer"), NUMBER_CASES)
def test_a_number_is_written_like_this(hive_type, value, sql_composer, spark_composer) -> None:
    column = COLUMN_OF[hive_type]
    written = repr(equals(column, value)).split(" = ")[1]
    assert written == in_this_edition(sql_composer, spark_composer)
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


# --- A value stays one value in a whole Statement, read back by its characters -------------


def _statement_with(condition) -> str:
    return to_hive(statement(
        SELECT(job_runs.run_id),
        FROM(job_runs),
        WHERE(condition, equals(job_runs.dt, "2026-09-24")),
    ))


@pytest.mark.parametrize(("_label", "value", "_expected"), WRITTEN, ids=WRITTEN_IDS)
@pytest.mark.parametrize("function", [contains, starts_with])
def test_a_like_pattern_keeps_the_value_whole(function, _label, value, _expected) -> None:
    hive = _statement_with(function(job_runs.status, value))
    patterns = [found for found in hive_literals.values(hive) if found != "2026-09-24"]
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    assert escaped in patterns[0]


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
@pytest.mark.parametrize(("function", "_operator"), COMPARISONS,
                         ids=[f.__name__ for f, _ in COMPARISONS])
def test_an_injection_payload_stays_one_value_in_a_whole_statement(function, _operator,
                                                                    payload) -> None:
    hive = _statement_with(function(job_runs.status, payload))
    assert payload in hive_literals.values(hive)
    assert " OR " not in hive_literals.outside_values(hive), "the payload became an OR"


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
    assert hive_literals.values(hive) == ["2026-09-24", "2026-09-24"]
