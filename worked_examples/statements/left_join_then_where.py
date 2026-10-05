"""LEFT_JOIN then WHERE: counting runs per job loses the job that never ran.

Why: LEFT_JOIN keeps cache_warm with NULL in every job_runs column, and a WHERE on job_runs
then throws that row away again.
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, all_of, between, count_rows, equals,
    example_database, is_not_null, statement,
)

jobs = example_database.jobs
job_runs = example_database.job_runs

FIRST_DAY = "2026-09-23"
LAST_DAY = "2026-09-24"


def careless(keeps_only_matches=False):
    """What most people write first: the days go in WHERE. The Guard refuses it.

    careless(keeps_only_matches=True) pastes the Guard's opt-out and shows what goes wrong:
    three jobs come back, and cache_warm, with no runs, is missing.
    """
    return statement(
        SELECT(jobs.job_name, AS(count_rows(where=is_not_null(job_runs.run_id)), "runs")),
        FROM(jobs),
        # Each job matches several runs, and counting them is the point: many_matches=True.
        LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id),
                  many_matches=True, keeps_only_matches=keeps_only_matches),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY)),
        GROUP_BY(jobs.job_name),
    )


def fixed():
    """Put the days in LEFT_JOIN's ON=, so they only decide which runs match."""
    return statement(
        SELECT(jobs.job_name, AS(count_rows(where=is_not_null(job_runs.run_id)), "runs")),
        FROM(jobs),
        LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
                                      between(job_runs.dt, FIRST_DAY, LAST_DAY)),
                  many_matches=True),
        GROUP_BY(jobs.job_name),
    )
