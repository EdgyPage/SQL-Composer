# Spark Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy
"""Runs, failed runs and minutes per job and day, as a Derived table to read.

Why: examples 1 and 3 both need these numbers, and writing them once here means the two can
never count them two different ways.

A Derived table is a Statement given a name, so another Statement can read it like a table.
The Toolbox writes it at the top of the reading Statement's Hive, as WITH runs_per_job_day AS
(...), and checks every column read from it, as it checks a Table reference's.

Every run counts, TEST runs and runs still going among them, since each one takes the
cluster's time: a team that wants TEST runs left out says so in its own Statement.
"""

from spark_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows, derived, equals, statement, sum_of,
)
from table_references.job_runs import job_runs


def runs_per_job_day(first_day, last_day):
    """One row per job and day from first_day to last_day: its runs, failed runs and minutes.

    The Date partition, dt, is kept in GROUP_BY, so each day's counts stay apart when
    first_day and last_day are days apart, and in SELECT, so a Statement that reads this over
    several days and groups its rows again can keep the day in its own GROUP_BY too, as by_day
    asks of a Statement it splits.
    """
    return derived(
        "runs_per_job_day",
        statement(
            SELECT(
                job_runs.job_id,
                job_runs.dt,
                AS(count_rows(), "runs"),
                AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
                AS(sum_of(job_runs.duration_mins), "minutes"),
            ),
            FROM(job_runs),
            WHERE(between(job_runs.dt, first_day, last_day)),
            GROUP_BY(job_runs.job_id, job_runs.dt),
        ),
    )
