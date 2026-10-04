"""The join Guards read the condition tree: what keeps a LEFT_JOIN's rows, and where the key is."""

from __future__ import annotations

import pytest

from sql_composer import (
    FROM,
    JOIN,
    LEFT_JOIN,
    SELECT,
    WHERE,
    GuardRefused,
    all_of,
    any_of,
    equals,
    is_null,
    statement,
)
from sql_composer.example_database import job_runs, jobs

DAY = equals(job_runs.dt, "2026-09-24")


def with_runs(*conditions):
    """Jobs, each with its runs on one day where it has some, kept by the conditions given."""
    return statement(SELECT(jobs.job_name, job_runs.status), FROM(jobs),
                     LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id), DAY),
                               many_matches=True),
                     WHERE(*conditions))


# --- The LEFT_JOIN Guard ---------------------------------------------------------------------


@pytest.mark.parametrize("condition", [
    pytest.param(is_null(job_runs.run_id), id="is_null"),
    pytest.param(any_of(is_null(job_runs.run_id), equals(job_runs.status, "FAILED")),
                 id="unmatched_or_failed"),
    pytest.param(all_of(is_null(job_runs.run_id), equals(jobs.team, "data")),
                 id="unmatched_and_a_test_on_the_other_table"),
])
def test_a_condition_that_keeps_the_unmatched_rows_is_let_through(condition) -> None:
    with_runs(condition)


@pytest.mark.parametrize("condition", [
    pytest.param(equals(job_runs.status, "FAILED"), id="a_plain_test"),
    pytest.param(all_of(is_null(job_runs.run_id), equals(job_runs.status, "FAILED")),
                 id="unmatched_and_failed"),
])
def test_a_condition_that_drops_the_unmatched_rows_is_refused(condition) -> None:
    with pytest.raises(GuardRefused, match="a condition on job_runs, which LEFT_JOIN brought in"):
        with_runs(condition)


# --- Where the key is ------------------------------------------------------------------------


def test_a_key_inside_a_building_block_is_found() -> None:
    """ON=all_of(key_block, ...) uses the key, though the key is inside the block's brackets."""
    key_block = all_of(equals(jobs.job_id, job_runs.job_id), equals(jobs.region, "PAR"))
    statement(SELECT(job_runs.run_id), FROM(job_runs),
              JOIN(jobs, ON=all_of(key_block, equals(jobs.team, "data"))), WHERE(DAY))
