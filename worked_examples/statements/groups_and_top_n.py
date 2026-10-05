"""Distinct values, counts per group, groups kept by HAVING, and the top N.

Why: most questions about a table are "how many per something", and these are the four
shapes that answer them.
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, HAVING, LIMIT, ORDER_BY, SELECT, SELECT_DISTINCT, WHERE, at_least,
    between, count_distinct, count_rows, descending, example_database, statement, sum_of,
)

jobs = example_database.jobs
job_runs = example_database.job_runs

FIRST_DAY = "2026-09-23"
LAST_DAY = "2026-09-24"


def teams():
    """Each team once (SELECT DISTINCT), to see which values a column holds."""
    return statement(
        SELECT_DISTINCT(jobs.team),
        FROM(jobs),
    )


def runs_and_days_per_job():
    """How many runs each job had, and on how many different days (COUNT DISTINCT).

    count_rows counts every run; count_distinct counts each day once, however many runs
    fell on it.
    """
    return statement(
        SELECT(
            job_runs.job_id,
            AS(count_rows(), "runs"),
            AS(count_distinct(job_runs.dt), "days_with_runs"),
        ),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY)),
        GROUP_BY(job_runs.job_id),
    )


def busy_jobs():
    """Only the jobs with 3 runs or more (HAVING).

    WHERE picks rows before they are counted, so it can't test a count. HAVING tests each
    group after GROUP_BY has counted it.
    """
    return statement(
        SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY)),
        GROUP_BY(job_runs.job_id),
        HAVING(at_least(count_rows(), 3)),
    )


def two_longest_running_jobs():
    """The 2 jobs with the most minutes in total (ORDER BY with LIMIT).

    A sort needs a LIMIT: without one, the warehouse puts every row in order before any comes
    back, so the Toolbox refuses a sort that would bring back every row. To sort a whole result, sort it in pandas.
    """
    return statement(
        SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY)),
        GROUP_BY(job_runs.job_id),
        ORDER_BY(descending("minutes")),
        LIMIT(2),
    )
