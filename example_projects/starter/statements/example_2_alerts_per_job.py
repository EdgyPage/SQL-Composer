"""Example 2: each job's alerts and high alerts per day, saved every day.

Why: an alert names only its run, so finding its job means joining every alert to job_runs,
which is worth doing once a day and saving rather than again in every report.

They are saved in mart.alerts_per_job, whose Table reference is
table_references/alerts_per_job.py. The steps are example 1's: create() once, look(day) to check a day's rows, write_day(day)
every day, and backfill(first_day, last_day) for days already past.
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, JOIN, SELECT, WHERE, between, by_day, count_rows,
    create_table, equals, statement,
)
from table_references.alerts_per_job import alerts_per_job
from table_references.job_runs import job_runs
from table_references.run_alerts import run_alerts

FIRST_DAY = "2026-09-23"
LAST_DAY = "2026-09-24"


def create():
    """Step 1: create mart.alerts_per_job from its Table reference, if it isn't there yet."""
    return create_table(alerts_per_job, may_exist=True)


def look(day=LAST_DAY):
    """Step 2: the rows write_day(day) would save, as a SELECT to run and check first.

    Each alert is joined to its run on run_id, job_runs' key, so each alert matches one run
    and is counted once. The joined table's Date partition is bounded too, in WHERE.
    """
    return statement(
        SELECT(job_runs.job_id, AS(count_rows(), "alerts"),
               AS(count_rows(where=equals(run_alerts.severity, "high")), "high_alerts")),
        FROM(run_alerts),
        JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
        WHERE(equals(run_alerts.dt, day), equals(job_runs.dt, day)),
        GROUP_BY(job_runs.job_id),
    )


def write_day(day=LAST_DAY):
    """Step 3, every day: save the day's rows, replacing whatever the day held."""
    return statement(
        INSERT_OVERWRITE(alerts_per_job),
        SELECT(job_runs.job_id, AS(count_rows(), "alerts"),
               AS(count_rows(where=equals(run_alerts.severity, "high")), "high_alerts")),
        FROM(run_alerts),
        JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
        WHERE(equals(run_alerts.dt, day), equals(job_runs.dt, day)),
        GROUP_BY(job_runs.job_id),
    )


def backfill(first_day=FIRST_DAY, last_day=LAST_DAY):
    """Step 4, when needed: save every day from first_day to last_day, one Statement per day.

    by_day splits on the days of the table in FROM, run_alerts, so the group keeps the day,
    run_alerts.dt: each day's counts are then whole. The joined job_runs keeps its own bound,
    every day of the backfill.
    """
    return by_day(statement(
        INSERT_OVERWRITE(alerts_per_job),
        SELECT(job_runs.job_id, AS(count_rows(), "alerts"),
               AS(count_rows(where=equals(run_alerts.severity, "high")), "high_alerts")),
        FROM(run_alerts),
        JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
        WHERE(between(run_alerts.dt, first_day, last_day),
              between(job_runs.dt, first_day, last_day)),
        GROUP_BY(run_alerts.dt, job_runs.job_id),
    ))
