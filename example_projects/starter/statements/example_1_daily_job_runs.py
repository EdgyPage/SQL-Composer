"""Example 1: each job's runs, failed runs and minutes per day, saved every day.

Why: counting every run again each time someone asks is slow, so the counts are worked out
once a day and saved in a Saved table that anyone can read.

They are saved in mart.daily_job_runs, whose Table reference is
table_references/daily_job_runs.py. The steps, in order: create() once, look(day) to check a
day's rows before writing them, write_day(day) every day, and backfill(first_day, last_day)
for days already past. Here, on the Example database, run look() with
run(look(), send=example_database.send); the Example database can't be written to, so print
the other steps' Hive with show_hive(...). At work, send each step with
run(step, send=run_query), run_query being your own send function.
"""

from sqlglot_composer import FROM, INSERT_OVERWRITE, SELECT, by_day, create_table, statement
from building_blocks.runs_per_job_day import runs_per_job_day
from table_references.daily_job_runs import daily_job_runs

FIRST_DAY = "2026-09-23"
LAST_DAY = "2026-09-24"


def create():
    """Step 1: create mart.daily_job_runs from its Table reference, if it isn't there yet.

    may_exist=True writes CREATE TABLE IF NOT EXISTS, so running every step from the top each
    day skips this one once the table is there. It never changes a table that is.
    """
    return create_table(daily_job_runs, may_exist=True)


def look(day=LAST_DAY):
    """Step 2: the rows write_day(day) would save, as a SELECT to run and check first."""
    per_job_day = runs_per_job_day(day, day)
    return statement(
        SELECT(per_job_day.job_id, per_job_day.runs, per_job_day.failed_runs,
               per_job_day.minutes),
        FROM(per_job_day),
    )


def write_day(day=LAST_DAY):
    """Step 3, every day: save the day's rows, replacing whatever the day held.

    INSERT_OVERWRITE replaces the day, so sending this twice leaves the same rows, not twice
    as many. The day's column, dt, isn't selected: the Hive's PARTITION(dt = ...) fills it
    with the day the Building block reads.
    """
    per_job_day = runs_per_job_day(day, day)
    return statement(
        INSERT_OVERWRITE(daily_job_runs),
        SELECT(per_job_day.job_id, per_job_day.runs, per_job_day.failed_runs,
               per_job_day.minutes),
        FROM(per_job_day),
    )


def backfill(first_day=FIRST_DAY, last_day=LAST_DAY):
    """Step 4, when needed: save every day from first_day to last_day, one Statement per day.

    A write saves one day, so by_day splits the Statement for all the days into one per day,
    oldest first. Send them in that order:

        for s in backfill("2026-09-01", "2026-09-24"):
            run(s, send=run_query)
    """
    per_job_day = runs_per_job_day(first_day, last_day)
    return by_day(statement(
        INSERT_OVERWRITE(daily_job_runs),
        SELECT(per_job_day.job_id, per_job_day.runs, per_job_day.failed_runs,
               per_job_day.minutes),
        FROM(per_job_day),
    ))
