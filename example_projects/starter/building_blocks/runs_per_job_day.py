"""runs_per_job_day - one row per job and day: its runs, failed runs and minutes.

Why: mart.daily_job_runs saves these numbers, and mart.team_day's notebook checks a day from
them too, and writing them once here means the two can never count them two different ways.

A Building block is a piece several notebooks share; this one is a Derived table, a Statement
given a name, which another Statement reads like a table. The Toolbox writes it at the top of
the reading Statement's Hive, as WITH runs_per_job_day AS (...), and checks every column read
from it, as it checks a Table reference's.

Every run counts, TEST runs and runs still going among them, since each one takes the
cluster's time: a team that wants TEST runs left out says so in its own Statement.
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows, derived, statement, sum_of,
)
from references.ops__job_runs import failed, job_runs, minutes  # failed, minutes: Aliases


def runs_per_job_day(first_day, last_day):
    """One row per job and day from first_day to last_day: its runs, failed runs and minutes.

    The Date partition, dt, is kept in GROUP_BY, so each day's counts stay apart when
    first_day and last_day are days apart, and in SELECT, so a Statement that reads this over
    several days and groups its rows again can keep the day in its own GROUP_BY too.
    """
    return derived(
        "runs_per_job_day",
        statement(
            SELECT(
                job_runs.job_id,
                job_runs.dt,
                AS(count_rows(), "runs"),
                AS(count_rows(where=failed), "failed_runs"),
                AS(sum_of(minutes), "minutes"),
            ),
            FROM(job_runs),
            WHERE(between(job_runs.dt, first_day, last_day)),
            GROUP_BY(job_runs.job_id, job_runs.dt),
        ),
    )
