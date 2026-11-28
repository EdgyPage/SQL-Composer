"""A number and a string compared as Hive compares them, '3' with 3 (Toolbox 8.10, ticket 09).

Hive reads a string and a number as one number to compare them: `job_id = '3'` matches the
row whose job_id is 3, and `dt = 20260911` the rows whose dt is '20260911'. So a comparison of
a column with a value takes text that reads as a number beside a number column, and a number
beside a string column, silently, and writes the value as given. Text that reads as no number,
'one', stays refused: Hive reads it as NULL, which matches no row. A CASE's values, a Python
step's and stacked columns stay of one kind, since there Hive picks one type for the whole
column.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

import example_database
from example_database import job_runs, region_costs
from sqlglot_composer import (
    FROM,
    SELECT,
    WHERE,
    Condition,
    at_least,
    at_most,
    between,
    equals,
    first_match,
    is_in,
    less_than,
    mapped,
    more_than,
    not_equals,
    run_query,
    statement,
)

COMPARISONS = [
    pytest.param(lambda: equals(job_runs.job_id, "3"), "job_runs.job_id = '3'", id="equals"),
    pytest.param(lambda: not_equals(job_runs.job_id, "3"), "job_runs.job_id <> '3'",
                 id="not_equals"),
    pytest.param(lambda: at_least(job_runs.job_id, "3"), "job_runs.job_id >= '3'",
                 id="at_least"),
    pytest.param(lambda: at_most(job_runs.job_id, "-2.5"), "job_runs.job_id <= '-2.5'",
                 id="at_most"),
    pytest.param(lambda: more_than(job_runs.job_id, "3"), "job_runs.job_id > '3'",
                 id="more_than"),
    pytest.param(lambda: less_than(job_runs.job_id, "3"), "job_runs.job_id < '3'",
                 id="less_than"),
    pytest.param(lambda: between(job_runs.job_id, "2", "3"),
                 "job_runs.job_id BETWEEN '2' AND '3'", id="between"),
    pytest.param(lambda: is_in(job_runs.job_id, ["2", "3"]), "job_runs.job_id IN ('2', '3')",
                 id="is_in"),
    pytest.param(lambda: equals(job_runs.status, 1), "job_runs.status = 1",
                 id="equals_a_string_column"),
    pytest.param(lambda: not_equals(job_runs.status, 1), "job_runs.status <> 1",
                 id="not_equals_a_string_column"),
    pytest.param(lambda: more_than(job_runs.status, 1.5), "job_runs.status > 1.5",
                 id="more_than_a_string_column"),
    pytest.param(lambda: is_in(job_runs.status, [1, 2]), "job_runs.status IN (1, 2)",
                 id="is_in_a_string_column"),
]


@pytest.mark.parametrize(("make", "hive"), COMPARISONS)
def test_a_number_and_a_string_compared_build_with_the_value_as_given(
        make: Callable[[], Condition], hive: str) -> None:
    assert repr(make()) == hive


def rows_of(condition: Condition) -> list[int]:
    every_day = FROM(job_runs, reads_all_partitions=True)
    found = run_query(statement(SELECT(job_runs.run_id), every_day, WHERE(condition)),
                      example_database.query)
    return list(found["run_id"])


def test_a_number_column_compared_with_text_gives_the_rows_of_its_number() -> None:
    assert rows_of(equals(job_runs.job_id, "3")) == rows_of(equals(job_runs.job_id, 3))
    assert rows_of(equals(job_runs.job_id, "3")) != []
    assert rows_of(is_in(job_runs.job_id, ["3"])) == rows_of(equals(job_runs.job_id, 3))
    assert rows_of(at_most(job_runs.job_id, "2.5")) == rows_of(at_most(job_runs.job_id, 2))


def test_a_string_column_compared_with_a_number_gives_the_rows_whose_text_reads_as_it() -> None:
    found = run_query(statement(SELECT(region_costs.job_id), FROM(region_costs),
                                WHERE(equals(region_costs.dt, 20260911))),
                      example_database.query)
    assert len(found) > 0
    # Text that reads as no number, as every status does, is NULL to Hive, and matches nothing.
    assert rows_of(equals(job_runs.status, 1)) == []
    assert rows_of(not_equals(job_runs.status, 1)) == []


def test_text_that_reads_as_no_number_beside_a_number_column_is_still_refused() -> None:
    with pytest.raises(TypeError) as refused:
        equals(job_runs.job_id, "one")
    said = str(refused.value)
    assert "compares job_runs.job_id, a bigint column, with 'one'" in said
    assert "would read 'one', which isn't a number, as NULL" in said and "match no row" in said


def test_a_value_of_another_kind_still_is_refused() -> None:
    with pytest.raises(TypeError, match="compares job_runs.job_id, a bigint column, with True"):
        equals(job_runs.job_id, True)


def test_a_cases_values_stay_of_one_kind() -> None:
    with pytest.raises(TypeError, match="gives values whose types don't mix"):
        first_match([(equals(job_runs.job_id, 3), "1")], otherwise=0)
    with pytest.raises(TypeError, match="gives keys whose types don't mix"):
        mapped(job_runs.job_id, {3: "three", "4": "four"})
