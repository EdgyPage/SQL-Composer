"""Build a long Statement from named steps, each one reading the step before it.

Why: a query in named steps can be read, and checked, one step at a time, where the same
query written as one block has to be understood all at once.

Each step is a Derived table, which the Toolbox writes at the top of the Hive as a
WITH ... AS (...) part (a CTE). Run a step on its own to check it before building on it.
"""

from sql_composer import (
    AS, FROM, GROUP_BY, JOIN, SELECT, WHERE, at_least, between, count_rows, derived,
    equals, example_database, statement, sum_of,
)

jobs = example_database.jobs
job_runs = example_database.job_runs

FIRST_DAY = "2026-09-23"
LAST_DAY = "2026-09-24"


def minutes_per_job():
    """Step 1: each job's runs and minutes over the two days."""
    return statement(
        SELECT(job_runs.job_id, AS(count_rows(), "runs"),
               AS(sum_of(job_runs.duration_mins), "minutes")),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY)),
        GROUP_BY(job_runs.job_id),
    )


def minutes_per_team():
    """Step 2: add each job's team from jobs, then total the minutes per team.

    Summing step 1's minutes again is safe, since a sum of sums is still the right sum. The
    Toolbox refuses the unsafe kinds, such as a sum of counts of different values.
    """
    per_job = derived("per_job", minutes_per_job())
    return statement(
        SELECT(jobs.team, AS(sum_of(per_job.runs), "runs"),
               AS(sum_of(per_job.minutes), "minutes")),
        FROM(per_job),
        JOIN(jobs, ON=equals(jobs.job_id, per_job.job_id)),
        GROUP_BY(jobs.team),
    )


def busy_teams():
    """Step 3: keep the teams with 100 minutes of runs or more, reading step 2."""
    per_team = derived("per_team", minutes_per_team())
    return statement(
        SELECT(per_team.team, per_team.minutes),
        FROM(per_team),
        WHERE(at_least(per_team.minutes, 100)),
    )

