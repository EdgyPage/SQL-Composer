"""The escaping matrix, pushed through every way a value reaches a Statement.

`escaping_cases.py` holds the cases. Here each case goes in through the Toolbox: each comparison
function, both ends of a range, each item of a list, a calculation and a Date partition bound,
and a number's text is written by the Toolbox, not by its own str(). The checks that read the Hive
back with sqlglot are in `sqlglot_edition/test_sqlglot_escaping_toolbox.py`.
"""

from __future__ import annotations

import decimal
import re

import pytest

from escaping_cases import (
    IDENTIFIER_CASES,
    NON_FINITE_NUMBERS,
    NUMBER_CASES,
    NUMBER_TEXT,
    REFUSED_CONTROL_CHARACTERS,
    SNEAKY_NUMBERS,
    STRING_CASES,
)
from sql_composer import (
    GuardRefused,
    Table,
    at_least,
    at_most,
    between,
    contains,
    equals,
    fill_null,
    hive_function,
    if_else,
    is_in,
    is_not_in,
    less_than,
    more_than,
    not_equals,
)
from sql_composer.example_database import job_runs

# The cases the Toolbox writes; the ones it refuses are checked on their own, below.
WRITTEN = [case for case in STRING_CASES if case[0] not in REFUSED_CONTROL_CHARACTERS]
WRITTEN_IDS = [label for label, _value, _expected in WRITTEN]
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
                 lambda: between(job_runs.status, "a", value),
                 lambda: is_in(job_runs.status, ["a", value]),
                 lambda: fill_null(job_runs.status, value),
                 lambda: hive_function("upper", value),
                 lambda: contains(job_runs.status, value)):
        with pytest.raises(GuardRefused, match="control character"):
            make()


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


