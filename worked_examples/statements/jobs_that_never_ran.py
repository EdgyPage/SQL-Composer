"""Jobs with no runs, and jobs with at least one: anti-join and semi-join.

Why: a job missing from the runs is often the very problem you're looking for, and a plain
JOIN can't show it, since JOIN keeps only the rows that match.
"""

from sql_composer import (
    FROM, JOIN, LEFT_JOIN, SELECT, SELECT_DISTINCT, WHERE, all_of, between, derived, equals,
    example_database, is_null, statement,
)

jobs = example_database.jobs
job_runs = example_database.job_runs

FIRST_DAY = "2026-09-23"
LAST_DAY = "2026-09-24"


def jobs_that_never_ran():
    """Every job with no run on these days (in SQL, an anti-join).

    LEFT_JOIN keeps every job, and a job with no run gets NULL in job_runs' columns, so
    is_null(job_runs.run_id) keeps just those. The day bound goes in ON=, not in WHERE: in
    WHERE it would throw away the very jobs with no runs, whose dt is NULL too.
    """
    return statement(
        SELECT(jobs.job_id, jobs.job_name),
        FROM(jobs),
        LEFT_JOIN(
            job_runs,
            ON=all_of(equals(job_runs.job_id, jobs.job_id),
                      between(job_runs.dt, FIRST_DAY, LAST_DAY)),
            # A job has many runs. That is fine here: the jobs kept are those with none.
            many_matches=True,
        ),
        WHERE(is_null(job_runs.run_id)),
    )


def jobs_that_ran():
    """Every job with at least one run on these days, each job once (in SQL, a semi-join).

    A JOIN straight to job_runs would repeat a job once per run. So first make the list of
    job_ids that ran, each once, with SELECT_DISTINCT, then JOIN to that list.
    """
    ran = derived("ran", statement(
        SELECT_DISTINCT(job_runs.job_id),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY)),
    ))
    return statement(
        SELECT(jobs.job_id, jobs.job_name),
        FROM(jobs),
        JOIN(ran, ON=equals(ran.job_id, jobs.job_id)),
    )
