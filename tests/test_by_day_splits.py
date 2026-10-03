"""What by_day splits and what it refuses, and the dates Load limit at every step."""

from __future__ import annotations

import pytest

from sql_composer import (
    AS,
    FROM,
    GROUP_BY,
    INSERT_OVERWRITE,
    JOIN,
    LIMIT,
    SELECT,
    SELECT_DISTINCT,
    WHERE,
    GuardRefused,
    LoadRefused,
    Table,
    between,
    by_day,
    count_distinct,
    count_rows,
    derived,
    descending,
    equals,
    row_number,
    set_load_limits,
    statement,
    to_hive,
)
from sql_composer.example_database import job_runs, jobs, run_alerts

DAYS = between(job_runs.dt, "2026-09-23", "2026-09-24")


def per_day(*clauses):
    """A Derived table over job_runs' two days, from its clauses after FROM and WHERE."""
    select, *rest = clauses
    return derived("per_day", statement(select, FROM(job_runs), WHERE(DAYS), *rest))


# --- What by_day refuses ---------------------------------------------------------------------


def test_by_day_refuses_a_limit_inside_a_derived_table() -> None:
    sample = per_day(SELECT(job_runs.run_id, job_runs.dt), LIMIT(5))
    with pytest.raises(GuardRefused, match=r"derived\('per_day', \.\.\.\) has LIMIT 5"):
        by_day(statement(SELECT(sample.run_id), FROM(sample)))


def test_by_day_refuses_a_distinct_without_the_date() -> None:
    s = statement(SELECT_DISTINCT(job_runs.status), FROM(job_runs), WHERE(DAYS))
    with pytest.raises(GuardRefused, match="without keeping the Date partition dt"):
        by_day(s)


def test_by_day_refuses_a_total_over_the_days() -> None:
    s = statement(SELECT(AS(count_distinct(job_runs.job_id), "jobs")), FROM(job_runs),
                  WHERE(DAYS))
    with pytest.raises(GuardRefused, match="without keeping the Date partition dt"):
        by_day(s)


def test_by_day_refuses_grouping_by_another_tables_dt() -> None:
    s = statement(
        SELECT(run_alerts.dt, AS(count_rows(), "runs")),
        FROM(job_runs),
        JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id), many_matches=True),
        WHERE(DAYS, between(run_alerts.dt, "2026-09-23", "2026-09-24")),
        GROUP_BY(run_alerts.dt),
    )
    with pytest.raises(GuardRefused, match="without keeping the Date partition dt"):
        by_day(s)


def test_by_day_refuses_an_output_only_named_like_the_date() -> None:
    teams = per_day(SELECT(job_runs.job_id, AS(job_runs.status, "dt")))
    s = statement(SELECT(teams.dt, AS(count_rows(), "runs")), FROM(teams), GROUP_BY(teams.dt))
    with pytest.raises(GuardRefused, match="without keeping the Date partition dt"):
        by_day(s)


@pytest.mark.parametrize("call", [
    lambda: by_day(statement(SELECT(jobs.team), FROM(jobs))),
    lambda: to_hive(statement(INSERT_OVERWRITE(Table("mart.teams",
                                                     columns={"team": "string", "dt": "string"},
                                                     date_partition="dt")),
                              SELECT(jobs.team), FROM(jobs))),
])
def test_a_from_table_with_no_date_partition_is_named_plainly(call) -> None:
    with pytest.raises(ValueError) as refused:
        call()
    message = str(refused.value)
    assert "ops.jobs has no Date partition" in message
    assert "jobs.dt" not in message


# --- What by_day splits ----------------------------------------------------------------------


def test_by_day_follows_a_renamed_date_up_through_a_derived_table() -> None:
    renamed = per_day(SELECT(AS(job_runs.dt, "day"), job_runs.job_id))
    s = statement(SELECT(renamed.day, AS(count_rows(), "runs")), FROM(renamed),
                  GROUP_BY(renamed.day))
    assert [to_hive(day).count("job_runs.dt = '2026-09-2") for day in by_day(s)] == [1, 1]


def test_by_day_splits_a_distinct_that_keeps_the_date() -> None:
    s = statement(SELECT_DISTINCT(job_runs.dt, job_runs.status), FROM(job_runs), WHERE(DAYS))
    assert len(by_day(s)) == 2


def test_by_day_splits_a_window_partitioned_by_a_renamed_date() -> None:
    renamed = per_day(SELECT(AS(job_runs.dt, "day"), job_runs.job_id, job_runs.run_id))
    ranked = statement(SELECT(renamed.run_id, AS(row_number(
        PARTITION_BY=[renamed.day, renamed.job_id], ORDER_BY=descending(renamed.run_id)),
        "rn")), FROM(renamed))
    assert len(by_day(ranked)) == 2


# --- The dates Load limit --------------------------------------------------------------------


def test_the_dates_cap_counts_the_days_a_derived_table_reads() -> None:
    set_load_limits(dates=1)
    inner = per_day(SELECT(job_runs.run_id, job_runs.dt))
    with pytest.raises(LoadRefused, match="reads 2 days of ops.job_runs"):
        to_hive(statement(SELECT(inner.run_id), FROM(inner)))


def test_the_dates_cap_sends_a_joined_table_to_its_own_bound() -> None:
    set_load_limits(dates=1)
    s = statement(
        SELECT(job_runs.run_id),
        FROM(job_runs),
        JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id), many_matches=True),
        WHERE(equals(job_runs.dt, "2026-09-24"), between(run_alerts.dt, "2026-09-23",
                                                         "2026-09-24")),
    )
    with pytest.raises(LoadRefused) as refused:
        to_hive(s)
    message = str(refused.value)
    assert "reads 2 days of ops.run_alerts" in message
    assert "for day in by_day" not in message
    assert "Narrow the between(...) or last_n_days(...) on ops.run_alerts" in message


def test_the_dates_cap_sends_the_from_table_to_by_day() -> None:
    set_load_limits(dates=1)
    with pytest.raises(LoadRefused, match=r"for day in by_day\(s\)"):
        to_hive(statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(DAYS)))
