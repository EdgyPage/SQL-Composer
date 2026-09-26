"""Label rows with if_else, fill NULL with fill_null, and count by condition.

Why: codes and NULLs make a result hard to read, and a count of each kind side by side gives
one row per job instead of one row per job and status.
"""

from sql_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows, equals, example_database,
    fill_null, if_else, is_null, more_than, statement,
)

job_runs = example_database.job_runs

FIRST_DAY = "2026-09-23"
LAST_DAY = "2026-09-24"


def labelled_runs():
    """Each run with a readable status and a length label (in SQL, COALESCE and CASE WHEN).

    A run still going has no status yet (NULL), which fill_null shows as RUNNING. if_else
    gives one value where its condition holds and the other where it doesn't.
    """
    return statement(
        SELECT(
            job_runs.run_id,
            AS(fill_null(job_runs.status, "RUNNING"), "status"),
            AS(if_else(more_than(job_runs.duration_mins, 20), "long", "short"), "length"),
        ),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY)),
    )


def outcomes_per_job():
    """One row per job, with a column for each outcome (a pivot).

    count_rows(where=...) counts only the rows where its condition holds, so each column
    counts one kind of run. A run still going is counted with is_null, since equals can't
    find NULL. A TEST run is in none of the three columns, so they needn't add up to the runs.
    """
    return statement(
        SELECT(
            job_runs.job_id,
            AS(count_rows(where=equals(job_runs.status, "SUCCESS")), "succeeded"),
            AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed"),
            AS(count_rows(where=is_null(job_runs.status)), "still_running"),
        ),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY)),
        GROUP_BY(job_runs.job_id),
    )
