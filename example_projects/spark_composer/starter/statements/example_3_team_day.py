# Spark Composer 4.0, exported 2026-10-06 00:26 - copy it, then edit your copy
"""Example 3: examples 1 and 2 combined into each team's day, saved every day.

Why: once examples 1 and 2 have saved a day, each team's numbers come from a few saved rows
per job, not from every run and alert again.

It reads the two Saved tables through their Table references, like any other table, and
ops.jobs for each job's team, so it runs after examples 1 and 2 have written the day. It saves
each team's day in mart.team_day, whose Table reference is table_references/team_day.py. The
steps are theirs: create(), preview(day), write_day(day) and backfill(first_day, last_day).

The Saved tables are in your warehouse, not in the Example database, so preview can't run
here. team_runs_from_job_runs(day) can: it groups by team the way this example does, but it
reads only ops tables, not the Saved tables, so it runs on the Example database too.
"""

from spark_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, JOIN, LEFT_JOIN, SELECT, WHERE, all_of, between,
    by_day, create_table, equals, fill_null, statement, sum_of,
)
from building_blocks.runs_per_job_day import runs_per_job_day
from table_references.alerts_per_job import alerts_per_job
from table_references.daily_job_runs import daily_job_runs
from table_references.jobs import jobs
from table_references.team_day import team_day

LAST_DAY = "2026-09-24"  # the Example database's last day, which the previews read unless told


def create():
    """Step 1: create mart.team_day from its Table reference, if it isn't there yet."""
    return create_table(team_day, may_exist=True)


def preview(day=LAST_DAY):
    """Step 2: the rows write_day(day) would save, as a SELECT to run and check first.

    A job whose runs raised no alert has no row in alerts_per_job, so LEFT_JOIN keeps its runs
    with NULL alerts, and fill_null makes a team with no alert at all count 0. The alerts' day
    goes in LEFT_JOIN's ON=, not in WHERE, since a WHERE on alerts_per_job would drop the jobs
    LEFT_JOIN keeps for having no alert.
    """
    return statement(
        SELECT(
            jobs.team,
            AS(sum_of(daily_job_runs.runs), "runs"),
            AS(sum_of(daily_job_runs.failed_runs), "failed_runs"),
            AS(sum_of(daily_job_runs.minutes), "minutes"),
            AS(fill_null(sum_of(alerts_per_job.alerts), 0), "alerts"),
            AS(fill_null(sum_of(alerts_per_job.high_alerts), 0), "high_alerts"),
        ),
        FROM(daily_job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, daily_job_runs.job_id)),
        LEFT_JOIN(alerts_per_job,
                  ON=all_of(equals(alerts_per_job.job_id, daily_job_runs.job_id),
                            equals(alerts_per_job.dt, day))),
        WHERE(equals(daily_job_runs.dt, day)),
        GROUP_BY(jobs.team),
    )


def write_day(day):
    """Step 3, every day, once examples 1 and 2 have written the day: save the day's rows.

    The Toolbox reads the day from the WHERE bound on daily_job_runs, the table in FROM, and
    writes it as PARTITION(dt = '...').
    """
    return statement(
        INSERT_OVERWRITE(team_day),
        SELECT(
            jobs.team,
            AS(sum_of(daily_job_runs.runs), "runs"),
            AS(sum_of(daily_job_runs.failed_runs), "failed_runs"),
            AS(sum_of(daily_job_runs.minutes), "minutes"),
            AS(fill_null(sum_of(alerts_per_job.alerts), 0), "alerts"),
            AS(fill_null(sum_of(alerts_per_job.high_alerts), 0), "high_alerts"),
        ),
        FROM(daily_job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, daily_job_runs.job_id)),
        LEFT_JOIN(alerts_per_job,
                  ON=all_of(equals(alerts_per_job.job_id, daily_job_runs.job_id),
                            equals(alerts_per_job.dt, day))),
        WHERE(equals(daily_job_runs.dt, day)),
        GROUP_BY(jobs.team),
    )


def backfill(first_day, last_day):
    """Step 4, when needed, once examples 1 and 2 have backfilled the same days.

    It builds one Statement over all the days, then by_day cuts it into one write per day of
    daily_job_runs, the table in FROM. GROUP_BY keeps that day, daily_job_runs.dt, so no
    day's counts are mixed with another's. The alerts are joined on their day as well as their
    job, so each day's runs meet only that day's alerts. Every read of a table must bound its
    Date partition at both ends, and by_day leaves a joined table's bound as written, so
    alerts_per_job's goes in LEFT_JOIN's ON= too, as between(alerts_per_job.dt, ...).
    """
    return by_day(statement(
        INSERT_OVERWRITE(team_day),
        SELECT(
            jobs.team,
            AS(sum_of(daily_job_runs.runs), "runs"),
            AS(sum_of(daily_job_runs.failed_runs), "failed_runs"),
            AS(sum_of(daily_job_runs.minutes), "minutes"),
            AS(fill_null(sum_of(alerts_per_job.alerts), 0), "alerts"),
            AS(fill_null(sum_of(alerts_per_job.high_alerts), 0), "high_alerts"),
        ),
        FROM(daily_job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, daily_job_runs.job_id)),
        LEFT_JOIN(alerts_per_job,
                  ON=all_of(equals(alerts_per_job.job_id, daily_job_runs.job_id),
                            equals(alerts_per_job.dt, daily_job_runs.dt),
                            between(alerts_per_job.dt, first_day, last_day))),
        WHERE(between(daily_job_runs.dt, first_day, last_day)),
        GROUP_BY(daily_job_runs.dt, jobs.team),
    ))


def team_runs_from_job_runs(day=LAST_DAY):
    """Try example 3's team grouping on the Example database: each team's runs, failed runs
    and minutes for a day, from ops.job_runs itself.

    It reads example 1's Building block, so the numbers are worked out exactly as example 1
    saves them, then groups them by team as preview does. At work, run it to check a day that
    example 1 hasn't saved yet, or that mart.team_day still matches ops.job_runs, such as after
    runs arrived late.
    """
    per_job_day = runs_per_job_day(day, day)
    return statement(
        SELECT(
            jobs.team,
            AS(sum_of(per_job_day.runs), "runs"),
            AS(sum_of(per_job_day.failed_runs), "failed_runs"),
            AS(sum_of(per_job_day.minutes), "minutes"),
        ),
        FROM(per_job_day),
        JOIN(jobs, ON=equals(jobs.job_id, per_job_day.job_id)),
        GROUP_BY(jobs.team),
    )
