"""Where counts, sums and row numbers can go, and what GROUP_BY must hold, before Hive sees it."""

from __future__ import annotations

import pytest

from sql_composer import (
    AS,
    FROM,
    GROUP_BY,
    HAVING,
    JOIN,
    LIMIT,
    ORDER_BY,
    SELECT,
    WHERE,
    GuardRefused,
    all_of,
    count_rows,
    descending,
    equals,
    fill_null,
    hive_function,
    max_of,
    more_than,
    row_number,
    statement,
    sum_of,
    to_hive,
    week_start,
)
from sql_composer.example_database import job_runs, jobs

DAYS = equals(job_runs.dt, "2026-09-24")


def numbered():
    return row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id))


def per_job(*clauses):
    """A Statement over one day of job_runs grouped by job_id, with the clauses given."""
    select, *rest = clauses
    return statement(select, FROM(job_runs), WHERE(DAYS), GROUP_BY(job_runs.job_id), *rest)


# --- The GROUP BY Guard ----------------------------------------------------------------------


@pytest.mark.parametrize(("make", "said"), [
    pytest.param(lambda: statement(SELECT(job_runs.dt, AS(count_rows(), "runs")), FROM(job_runs),
                                   WHERE(DAYS), GROUP_BY(week_start(job_runs.dt))),
                 "SELECT has job_runs.dt, which GROUP_BY leaves out",
                 id="a_column_inside_a_grouped_calculation"),
    pytest.param(lambda: per_job(SELECT(job_runs.job_id, AS(
        job_runs.duration_mins - max_of(job_runs.duration_mins), "gap"))),
                 "SELECT has job_runs.duration_mins", id="a_column_beside_an_aggregate"),
    pytest.param(lambda: per_job(SELECT(job_runs.job_id, AS(count_rows(), "runs")),
                                 HAVING(more_than(job_runs.duration_mins, 5))),
                 "HAVING has job_runs.duration_mins", id="having"),
    pytest.param(lambda: per_job(SELECT(job_runs.job_id, AS(count_rows(), "runs")),
                                 ORDER_BY(job_runs.duration_mins), LIMIT(3)),
                 "ORDER_BY has job_runs.duration_mins", id="order_by"),
    pytest.param(lambda: statement(SELECT(AS(fill_null(job_runs.status, max_of(job_runs.status)),
                                             "status")), FROM(job_runs), WHERE(DAYS)),
                 "SELECT has job_runs.status, but the Statement counts or adds up rows "
                 "and has no GROUP_BY", id="fill_null_beside_an_aggregate"),
    pytest.param(lambda: statement(SELECT(job_runs.job_id), FROM(job_runs), WHERE(DAYS),
                                   HAVING(more_than(count_rows(), 1))),
                 "SELECT has job_runs.job_id, but the Statement counts", id="having_alone"),
    pytest.param(lambda: statement(SELECT(job_runs.job_id), FROM(job_runs), WHERE(DAYS),
                                   ORDER_BY(sum_of(job_runs.duration_mins)), LIMIT(3)),
                 "SELECT has job_runs.job_id, but the Statement counts",
                 id="a_count_only_in_order_by"),
])
def test_the_group_by_guard_refuses_what_hive_refuses(make, said) -> None:
    with pytest.raises(GuardRefused, match=said):
        make()


def test_the_group_by_guard_takes_what_hive_takes() -> None:
    per_job(SELECT(job_runs.job_id, AS(count_rows(), "runs"),
                   AS(sum_of(job_runs.duration_mins) - max_of(job_runs.duration_mins), "rest")),
            HAVING(more_than(count_rows(), 1)), ORDER_BY(descending("runs")), LIMIT(3))
    statement(SELECT(AS(week_start(job_runs.dt), "week"), AS(count_rows(), "runs")),
              FROM(job_runs), WHERE(DAYS), GROUP_BY(week_start(job_runs.dt)))


# --- Where a count, a sum or a row number can go ---------------------------------------------


@pytest.mark.parametrize(("make", "said"), [
    pytest.param(lambda: statement(SELECT(job_runs.run_id), FROM(job_runs),
                                   JOIN(jobs, ON=all_of(equals(jobs.job_id, job_runs.job_id),
                                                        more_than(count_rows(), 1))),
                                   WHERE(DAYS)),
                 "ON= has", id="an_aggregate_in_on"),
    pytest.param(lambda: statement(SELECT(AS(count_rows(), "runs")), FROM(job_runs), WHERE(DAYS),
                                   GROUP_BY(count_rows())),
                 "GROUP_BY has", id="an_aggregate_in_group_by"),
    pytest.param(lambda: statement(SELECT(job_runs.run_id), FROM(job_runs),
                                   WHERE(DAYS, equals(numbered(), 1))),
                 "WHERE has", id="a_row_number_in_where"),
    pytest.param(lambda: per_job(SELECT(job_runs.job_id, AS(count_rows(), "runs")),
                                 HAVING(equals(numbered(), 1))),
                 "HAVING has", id="a_row_number_in_having"),
    pytest.param(lambda: statement(SELECT(job_runs.run_id), FROM(job_runs),
                                   JOIN(jobs, ON=all_of(equals(jobs.job_id, job_runs.job_id),
                                                        equals(numbered(), 1))),
                                   WHERE(DAYS)),
                 "ON= has", id="a_row_number_in_on"),
    pytest.param(lambda: statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(DAYS),
                                   GROUP_BY(numbered())),
                 "GROUP_BY has", id="a_row_number_in_group_by"),
])
def test_a_count_or_a_row_number_is_refused_where_hive_refuses_it(make, said) -> None:
    with pytest.raises(ValueError, match=said):
        make()


def test_a_row_number_in_where_is_sent_to_a_derived_table() -> None:
    with pytest.raises(ValueError, match=r"derived\(\.\.\.\)"):
        statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(DAYS, equals(numbered(), 1)))


@pytest.mark.parametrize("make", [
    pytest.param(lambda: sum_of(numbered()), id="a_row_number_in_a_sum"),
    pytest.param(lambda: max_of(max_of(job_runs.duration_mins)), id="an_aggregate_in_an_aggregate"),
    pytest.param(lambda: count_rows(where=more_than(count_rows(), 1)),
                 id="an_aggregate_in_where_of_an_aggregate"),
    pytest.param(lambda: hive_function("collect_set", sum_of(job_runs.duration_mins)),
                 id="an_aggregate_in_an_aggregate_hive_function"),
    pytest.param(lambda: hive_function("collect_set", numbered()),
                 id="a_row_number_in_an_aggregate_hive_function"),
])
def test_a_count_or_a_row_number_inside_a_count_is_refused(make) -> None:
    with pytest.raises(ValueError, match="inside"):
        make()


# --- Names and lists -------------------------------------------------------------------------


def test_order_by_refuses_a_name_select_has_not() -> None:
    with pytest.raises(ValueError, match="SELECT has no column called 'minutez'"):
        per_job(SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
                ORDER_BY(descending("minutez")), LIMIT(3))


@pytest.mark.parametrize("order", [[], "minutes", descending("minutes")])
def test_row_number_orders_by_columns_only(order) -> None:
    with pytest.raises((TypeError, ValueError), match="row_number"):
        row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=order)


def test_row_number_numbers_every_row_with_no_partition() -> None:
    s = statement(SELECT(job_runs.run_id, AS(row_number(PARTITION_BY=[], ORDER_BY=job_runs.run_id),
                                             "rn")), FROM(job_runs), WHERE(DAYS))
    assert "ROW_NUMBER() OVER (ORDER BY job_runs.run_id ASC) AS rn" in to_hive(s)


def test_group_by_refuses_nothing_to_group_by() -> None:
    with pytest.raises(TypeError, match="nothing to group by"):
        GROUP_BY()
