"""runs_per_job - each job's runs, failed runs and minutes for each dt it reads.

Why: mart.daily_job_runs saves these numbers, and mart.team_day's notebook checks a day from
them too, and writing them once here means the two can never count them two different ways.

A Building block is a piece several notebooks share; this one is a Derived table, a Statement
given a name, which another Statement reads like a table. The Toolbox writes it at the top of
the reading Statement's Hive, as WITH runs_per_job AS (...), and checks every column read
from it, as it checks a Table reference's.

Every run counts, TEST runs and runs still going among them, since each one takes the
cluster's time: a team that wants TEST runs left out says so in its own Statement.
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, Condition, Table, count_rows, derived, statement,
    sum_of,
)
from references.ops__job_runs import failed, job_runs, minutes  # failed, minutes: Aliases


def runs_per_job(reads: Condition) -> Table:
    """One row per job for each dt of the rows `reads` picks: its runs, failed runs and
    minutes.

    `reads` is a condition on ops.job_runs, such as equals(job_runs.dt, "2026-09-24"): the
    table is partitioned by dt, so it must filter dt. dt is kept in GROUP_BY, so the counts of
    each dt stay apart when `reads` picks several, and in SELECT, so a write that reads this
    fills each dt's Partition from it, and a Statement that groups its rows again can keep dt
    in its own GROUP_BY too.
    """
    return derived(
        "runs_per_job",
        statement(
            SELECT(
                job_runs.job_id,
                job_runs.dt,
                AS(count_rows(), "runs"),
                AS(count_rows(where=failed), "failed_runs"),
                AS(sum_of(minutes), "minutes"),
            ),
            FROM(job_runs),
            WHERE(reads),
            GROUP_BY(job_runs.job_id, job_runs.dt),
        ),
    )
