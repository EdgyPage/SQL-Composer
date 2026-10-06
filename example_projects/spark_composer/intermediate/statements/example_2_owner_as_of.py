# Spark Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy
"""Example 2: each job's day, with the team that owned it that day, saved each run.

Why: a job can move team, so each day's events must go to the team that owned the job on that
day, which only a lookup in that day's snapshot of ops.job_owners can tell.

The days are saved in mart.job_day_facts, whose Table reference is
table_references/job_day_facts.py. The steps are example 1's: create() once, preview(day) to
check a day's rows, and write_days(first_day, last_day) on every run, for the last 3 days, as
events can come in late too: an event lands in the partition of the day it happened, but can
reach the table after that day was saved. A run that ends on a later day counts its minutes on
that later day.

The team is looked up as of each day: owner_on_day joins each job's day to ops.job_owners'
snapshot of the same day. So report_build's events count for data up to 2026-09-17, and for
finance from 2026-09-18, the day it moved.

Two more steps answer a different question: who owns each job now? newest_owners(day) takes
each job's newest snapshot in the 7 days up to the day, so a job is still found when the day's
snapshot hasn't come in yet. It numbers each job's snapshots with row_number, newest first,
and keeps number 1. row_number is a window function. Each Edition ships its own Example
database, and the one that runs its queries with sqlglot, rather than on Spark, has no window
functions: it stops with a message saying so. newest_owners_by_newest_day(day) gives the same
rows without one, so either Example database runs it: each job's newest day with max_of,
joined back to that day's snapshot. At work, either runs.
"""

import datetime

from spark_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, JOIN, SELECT, WHERE, all_of, between, by_day,
    create_table, derived, descending, equals, max_of, row_number, statement,
)
from building_blocks.events_per_job_day import events_per_job_day
from building_blocks.owner_on_day import owner_on_day
from table_references.job_day_facts import job_day_facts
from table_references.job_owners import job_owners

LAST_DAY = "2026-09-24"  # the Example database's last day, which the previews read unless told
SNAPSHOT_DAYS = 7  # newest_owners looks from 6 days before the day to the day: 7 days


def create():
    """Step 1: create mart.job_day_facts from its Table reference, if it isn't there yet."""
    return create_table(job_day_facts, may_exist=True)


def preview(day=LAST_DAY):
    """Step 2: the rows write_days would save for the day, as a SELECT to run and check first."""
    events = events_per_job_day(day, day)
    return statement(
        SELECT(events.job_id, job_owners.team, events.events, events.runs, events.minutes),
        FROM(events),
        owner_on_day(events.job_id, events.dt, first_day=day, last_day=day),
    )


def write_days(first_day, last_day):
    """Step 3, every run: save every day from first_day to last_day, one write per day.

    by_day cuts the Statement into one write per day of ops.job_events, the table in the
    Building block's FROM, oldest first. owner_on_day bounds job_owners from first_day to
    last_day, which by_day leaves as written, and matches each job's day to the snapshot of
    the same day, so each day's write finds that day's team.
    """
    events = events_per_job_day(first_day, last_day)
    return by_day(statement(
        INSERT_OVERWRITE(job_day_facts),
        SELECT(events.job_id, job_owners.team, events.events, events.runs, events.minutes),
        FROM(events),
        owner_on_day(events.job_id, events.dt, first_day=first_day, last_day=last_day),
    ))


def days_before(day, days):
    """The day `days` days before `day`, written the same way: days_before("2026-09-24", 6) is
    "2026-09-18"."""
    return (datetime.date.fromisoformat(day) - datetime.timedelta(days=days)).isoformat()


def newest_owners(day=LAST_DAY):
    """Each job's team and owner in its newest snapshot from the 7 days up to the day.

    Hive can't keep only row number 1 in the SELECT that numbers the rows, so the numbering is
    a Derived table, and the Statement that reads it keeps the rows numbered 1.
    """
    numbered = derived(
        "numbered",
        statement(
            SELECT(job_owners.job_id, job_owners.team, job_owners.owner, job_owners.dt,
                   AS(row_number(PARTITION_BY=job_owners.job_id,
                                 ORDER_BY=descending(job_owners.dt)), "newest_first")),
            FROM(job_owners),
            WHERE(between(job_owners.dt, days_before(day, SNAPSHOT_DAYS - 1), day)),
        ),
    )
    return statement(
        SELECT(numbered.job_id, numbered.team, numbered.owner, numbered.dt),
        FROM(numbered),
        WHERE(equals(numbered.newest_first, 1)),
    )


def newest_owners_by_newest_day(day=LAST_DAY):
    """The rows newest_owners gives, worked out without row_number, so an Example database
    that runs its queries with sqlglot can run it too.

    It finds each job's newest day with a snapshot, one row per job, then joins that day's
    snapshot back on. ON= names job_owners' whole key, the job and the day, so each job
    matches one snapshot.
    """
    first_day = days_before(day, SNAPSHOT_DAYS - 1)
    newest = derived(
        "newest",
        statement(
            SELECT(job_owners.job_id, AS(max_of(job_owners.dt), "newest_day")),
            FROM(job_owners),
            WHERE(between(job_owners.dt, first_day, day)),
            GROUP_BY(job_owners.job_id),
        ),
    )
    return statement(
        SELECT(newest.job_id, job_owners.team, job_owners.owner, job_owners.dt),
        FROM(newest),
        JOIN(job_owners, ON=all_of(equals(job_owners.job_id, newest.job_id),
                                   equals(job_owners.dt, newest.newest_day),
                                   between(job_owners.dt, first_day, day))),
    )
