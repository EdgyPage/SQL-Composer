"""runs_per_job - each job's runs, failed runs and minutes for each dt it reads.

Why: more than one Statement needs each job's runs, failed runs and minutes, such as each
team's failed runs and a check of one day, and writing them once here means they can never
be counted two different ways.

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

    `reads` is a condition on ops.job_runs, such as equals(job_runs.dt, "2026-09-24"):
    the table is partitioned by dt, so it must filter dt. dt is kept in GROUP_BY, so the
    counts of each dt stay apart when `reads` picks several, and in SELECT, so a Statement
    that reads this can tell its days apart, or keep them apart in its own GROUP_BY.
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
