"""How many different jobs ran each day, as a Derived table other Statements can read."""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, between, count_distinct, derived, example_database,
    statement,
)

job_runs = example_database.job_runs


def jobs_per_day(first_day, last_day):
    """One row per day, with how many different jobs ran that day."""
    return derived(
        "jobs_per_day",
        statement(
            SELECT(job_runs.dt, AS(count_distinct(job_runs.job_id), "jobs_that_ran")),
            FROM(job_runs),
            WHERE(between(job_runs.dt, first_day, last_day)),
            GROUP_BY(job_runs.dt),
        ),
    )
