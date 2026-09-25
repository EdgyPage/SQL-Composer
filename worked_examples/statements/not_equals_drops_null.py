"""not_equals: leaving out TEST runs also leaves out the run still going.

Why: SQL's `<>` drops the rows where the column is NULL, while pandas' `!=` keeps them.

No Guard catches this, since the Toolbox can't know which columns may be NULL; not_equals'
docstring says so instead.
"""

from sql_composer import (
    AS, FROM, SELECT, WHERE, any_of, count_rows, equals, example_database, is_null,
    not_equals, statement,
)

job_runs = example_database.job_runs

DAY = "2026-09-23"


def careless():
    """What most people write first, expecting pandas' !=: it counts 3 runs, not 4.

    Run 98 is still running, so its status is NULL, and `status <> 'TEST'` drops it.
    """
    return statement(
        SELECT(AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, DAY), not_equals(job_runs.status, "TEST")),
    )


def fixed():
    """Keep the NULL rows by asking for them too: the 4 runs pandas' != would give."""
    return statement(
        SELECT(AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, DAY),
              any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
    )
