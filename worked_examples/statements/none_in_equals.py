"""None in equals: a search for a missing status finds nothing.

Why: in SQL nothing equals NULL, not even NULL, so `status = NULL` matches no rows at all.
"""

from sqlglot_composer import (
    AS, FROM, SELECT, WHERE, count_rows, equals, example_database, is_null, statement,
)

job_runs = example_database.job_runs

DAY = "2026-09-23"


def careless():
    """What most people write first. The Guard refuses it at equals(...), with no opt-out.

    In Hive it would count 0 runs, when one run (98) is still running with no status.
    """
    return statement(
        SELECT(AS(count_rows(), "running")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, DAY), equals(job_runs.status, None)),
    )


def fixed():
    """Use is_null(...) to find a missing value: it finds the one run still going."""
    return statement(
        SELECT(AS(count_rows(), "running")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, DAY), is_null(job_runs.status)),
    )
