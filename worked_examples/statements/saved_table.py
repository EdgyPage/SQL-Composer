"""Build a Saved table: create it, write a day, add to a day, backfill, rebuild.

Why: a result that is slow to work out, or read by many notebooks, is cheaper to work out once
a day and save than to work out again every time someone reads it.

A Saved table is written one day at a time, and each function below is one step. The
Example database can't be written to, so the steps show their Hive but no result. At work,
send each one with run(step(), send=run_query), run_query being your own send function,
and loop over the ones that return a list.
"""

from sql_composer import (
    FROM, INSERT_INTO, INSERT_OVERWRITE, JOIN, SELECT, SELECT_DISTINCT, WHERE, create_table,
    drop_table, equals, example_database, statement,
)
from table_references.runs_to_review import runs_to_review

job_runs = example_database.job_runs
run_alerts = example_database.run_alerts

FIRST_DAY = "2026-09-23"
LAST_DAY = "2026-09-24"


def create():
    """Step 1, once: create the table from its Table reference.

    The warehouse refuses if the table already exists. That is on purpose: after you edit the Table
    reference, sending this again can't quietly look like it changed the real table.
    """
    return create_table(runs_to_review)


def create_if_missing():
    """Step 1, in a notebook you run from the top every day: create the table only if missing.

    may_exist=True writes CREATE TABLE IF NOT EXISTS, so the second day's run skips it
    instead of failing. It never changes a table that is already there.
    """
    return create_table(runs_to_review, may_exist=True)


def failed_runs(day=LAST_DAY):
    """Step 2: fill one day with that day's failed runs, replacing whatever the day held.

    Because INSERT_OVERWRITE replaces the day, sending it twice leaves the same rows, not
    twice as many. That makes it the safe first write of each day.
    """
    return statement(
        INSERT_OVERWRITE(runs_to_review),
        # dt isn't selected: PARTITION(dt = ...) in the Hive fills it with the day read.
        SELECT(job_runs.run_id, job_runs.job_id),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, day), equals(job_runs.status, "FAILED")),
    )


def alerted_runs(day=LAST_DAY):
    """Step 3: add that day's runs that succeeded but raised a high alert.

    INSERT_INTO keeps the failed runs step 2 wrote, and adds these beside them. They come
    from a second table, run_alerts, which is why they are a second Statement rather than
    another condition in step 2. Send it once, after step 2. Sent twice, these runs would be in
    the day twice; to redo a day, send step 2 again first, which clears it.
    """
    return statement(
        INSERT_INTO(runs_to_review),
        # A run can raise several high alerts, so DISTINCT keeps each run once.
        SELECT_DISTINCT(job_runs.run_id, job_runs.job_id),
        FROM(run_alerts),
        JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
        WHERE(
            equals(run_alerts.dt, day),
            equals(job_runs.dt, day),  # the joined table's Date partition needs a bound too
            equals(run_alerts.severity, "high"),
            equals(job_runs.status, "SUCCESS"),
        ),
    )


def backfill(days=(FIRST_DAY, LAST_DAY)):
    """Step 4: write past days, oldest first, each the way steps 2 and 3 write one.

    To backfill is to write days that have already happened: a new table's past days, every
    day again after rebuild(), or a day again after fixing a mistake in a step. Each day
    gets step 2 then step 3, in that order, so it starts clean and keeps both sources. A
    day filled by one Statement alone can be split into days with by_day(s) instead.

        for s in backfill():
            run(s, send=run_query)
    """
    return [s for day in days for s in (failed_runs(day), alerted_runs(day))]


def rebuild():
    """Step 5, rarely: after changing the table's columns, drop it and create it again.

    create_table refuses while the old table exists, so the old one has to go first.
    drop_table deletes every day of the table, so write them all again with backfill().
    IF EXISTS means the drop does nothing, rather than failing, if the table isn't there.
    """
    return [drop_table(runs_to_review), create_table(runs_to_review)]
