"""Re-grouping: adding up each day's count of jobs gives too many for the week.

Why: a job that ran on two days is in both days' counts, so adding them up counts it twice.
"""

import pandas as pd

from building_blocks.jobs_per_day import jobs_per_day
from sql_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, all_columns, between, count_distinct, example_database,
    run, statement, sum_of, week_start,
)

job_runs = example_database.job_runs

FIRST_DAY = "2026-09-23"
LAST_DAY = "2026-09-24"


def careless(adds_up=False):
    """What most people write first: add up each day's count. The Guard refuses it.

    careless(adds_up=True) pastes the Guard's opt-out and shows the wrong number: 6 jobs,
    when only 3 different jobs ran that week.
    """
    daily = jobs_per_day(FIRST_DAY, LAST_DAY)
    return statement(
        SELECT(AS(week_start(daily.dt), "week"),
               AS(sum_of(daily.jobs_that_ran, adds_up=adds_up), "jobs_that_ran")),
        FROM(daily),
        GROUP_BY("week"),
    )


def fixed():
    """Count the different jobs over the whole week, straight from job_runs."""
    return statement(
        SELECT(AS(week_start(job_runs.dt), "week"),
               AS(count_distinct(job_runs.job_id), "jobs_that_ran")),
        FROM(job_runs),
        WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY)),
        GROUP_BY("week"),
    )


def every_run():
    """Every run on both days, read with a Statement the Example database can run."""
    return run(
        statement(SELECT(all_columns(job_runs)), FROM(job_runs),
                  WHERE(between(job_runs.dt, FIRST_DAY, LAST_DAY))),
        send=example_database.send,
    )


def with_week(runs):
    """The runs with a week column: the Monday that starts each day's week, as week_start."""
    days = pd.to_datetime(runs.dt)
    monday = days - pd.to_timedelta(days.dt.weekday, unit="D")
    return runs.assign(week=monday.dt.strftime("%Y-%m-%d"))


def careless_in_pandas():
    """careless(adds_up=True)'s result, computed in pandas, not by running this Hive."""
    runs = with_week(every_run())
    daily = runs.groupby(["week", "dt"], as_index=False).job_id.nunique()
    weekly = daily.groupby("week", as_index=False).job_id.sum()
    return weekly.rename(columns={"job_id": "jobs_that_ran"})


def fixed_in_pandas():
    """fixed()'s result, computed in pandas, not by running this Hive."""
    runs = with_week(every_run())
    weekly = runs.groupby("week", as_index=False).job_id.nunique()
    return weekly.rename(columns={"job_id": "jobs_that_ran"})
