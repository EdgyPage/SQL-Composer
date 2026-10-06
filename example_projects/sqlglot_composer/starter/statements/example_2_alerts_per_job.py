# sqlglot Composer 4.0, exported 2026-10-06 00:26 - copy it, then edit your copy
"""Example 2: each job's alerts and high alerts per day, saved every day.

Why: an alert names only its run, so finding its job means joining every alert to job_runs,
which is worth doing once a day and saving, rather than in every Statement that counts alerts.

They are saved in mart.alerts_per_job, whose Table reference is
table_references/alerts_per_job.py. The steps are example 1's: create() once, preview(day) to
check a day's rows, write_day(day) every day, and backfill(first_day, last_day) for days
already past.

A run can raise an alert after midnight, so job_runs is read from the day before as well: an
alert counts on the day it was raised, whichever of the two days its run is in. A run raises
its alerts by the end of the next day, so no alert's run is older than that.
"""

import datetime

from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, JOIN, SELECT, WHERE, between, by_day, count_rows,
    create_table, equals, statement,
)
from table_references.alerts_per_job import alerts_per_job
from table_references.job_runs import job_runs
from table_references.run_alerts import run_alerts

LAST_DAY = "2026-09-24"  # the Example database's last day, which preview reads unless told


def day_before(day):
    """The day before `day`, written the same way: day_before("2026-09-24") is "2026-09-23"."""
    return (datetime.date.fromisoformat(day) - datetime.timedelta(days=1)).isoformat()


def create():
    """Step 1: create mart.alerts_per_job from its Table reference, if it isn't there yet."""
    return create_table(alerts_per_job, may_exist=True)


def preview(day=LAST_DAY):
    """Step 2: the rows write_day(day) would save, as a SELECT to run and check first.

    Each alert is joined to its run on run_id, job_runs' key, so each alert matches one run
    and is counted once. Every read of a table must bound its Date partition at both ends, the
    joined job_runs too: here from the day before, for the runs that raised an alert after
    midnight.
    """
    return statement(
        SELECT(job_runs.job_id, AS(count_rows(), "alerts"),
               AS(count_rows(where=equals(run_alerts.severity, "high")), "high_alerts")),
        FROM(run_alerts),
        JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
        WHERE(equals(run_alerts.dt, day), between(job_runs.dt, day_before(day), day)),
        GROUP_BY(job_runs.job_id),
    )


def write_day(day):
    """Step 3, every day: save the day's rows, replacing whatever the day held.

    The Toolbox reads the day from the WHERE bound on run_alerts, the table in FROM, which
    must name one day only, and writes it as PARTITION(dt = '...').
    """
    return statement(
        INSERT_OVERWRITE(alerts_per_job),
        SELECT(job_runs.job_id, AS(count_rows(), "alerts"),
               AS(count_rows(where=equals(run_alerts.severity, "high")), "high_alerts")),
        FROM(run_alerts),
        JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
        WHERE(equals(run_alerts.dt, day), between(job_runs.dt, day_before(day), day)),
        GROUP_BY(job_runs.job_id),
    )


def backfill(first_day, last_day):
    """Step 4, when needed: save every day from first_day to last_day, one write per day.

    It builds one Statement over all the days, then by_day cuts it into one write per day of
    the table in FROM, run_alerts, oldest first. GROUP_BY keeps that day, run_alerts.dt, so no
    day's counts are mixed with another's. by_day leaves the joined job_runs' bound as
    written, so each day's write reads job_runs from the day before first_day to last_day.
    That is more days than write_day reads, but an alert names one run, from its own day or
    the day before, so each day's write finds the same runs and saves the same rows as
    write_day.
    """
    return by_day(statement(
        INSERT_OVERWRITE(alerts_per_job),
        SELECT(job_runs.job_id, AS(count_rows(), "alerts"),
               AS(count_rows(where=equals(run_alerts.severity, "high")), "high_alerts")),
        FROM(run_alerts),
        JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
        WHERE(between(run_alerts.dt, first_day, last_day),
              between(job_runs.dt, day_before(first_day), last_day)),
        GROUP_BY(run_alerts.dt, job_runs.job_id),
    ))
