"""Keep rows by a list of values, by either of two conditions, or by text.

Why: filters like "these three jobs", "failed or still running" and "names starting with"
come up in almost every Statement, and each has one trap worth knowing.
"""

from sql_composer import (
    FROM, SELECT, WHERE, any_of, between, contains, equals, example_database, is_in,
    is_not_in, is_null, starts_with, statement,
)

jobs = example_database.jobs
job_runs = example_database.job_runs

FIRST_DAY = "2026-09-23"
LAST_DAY = "2026-09-24"


def runs_of_listed_jobs():
    """Runs of jobs 1 and 3 only (IN a list)."""
    return statement(
        SELECT(job_runs.run_id, job_runs.job_id),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY), is_in(job_runs.job_id, [1, 3])),
    )


def runs_that_did_not_pass():
    """Runs whose status is neither TEST nor SUCCESS (NOT IN a list).

    The trap: a run still going has status NULL, and NOT IN drops NULL rows too, so it is
    missing here. The next Statement keeps it on purpose.
    """
    return statement(
        SELECT(job_runs.run_id, job_runs.status),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY),
              is_not_in(job_runs.status, ["TEST", "SUCCESS"])),
    )


def runs_to_check():
    """Runs that failed or are still going (OR).

    any_of keeps a row where at least one of its conditions holds. is_null finds the runs
    still going, which equals can't: in SQL, NULL equals nothing.
    """
    return statement(
        SELECT(job_runs.run_id, job_runs.status),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY),
              any_of(equals(job_runs.status, "FAILED"), is_null(job_runs.status))),
    )


def jobs_by_name():
    """Jobs whose name starts with "invoice" or contains "_build" (LIKE).

    The trap: in LIKE, _ means "any one character". contains and starts_with match _ and %
    as themselves, so "_build" finds only an underscore followed by build.
    """
    return statement(
        SELECT(jobs.job_id, jobs.job_name),
        FROM(jobs),
        WHERE(any_of(starts_with(jobs.job_name, "invoice"), contains(jobs.job_name, "_build"))),
    )
