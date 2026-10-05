"""Example 1: each job's runs, failed runs and minutes per day, saved every day.

Why: counting every run again each time someone asks is slow, so the counts are worked out
once a day and saved in a Saved table that anyone can read.

They are saved in mart.daily_job_runs, whose Table reference is
table_references/daily_job_runs.py. The steps, in order: create() once, preview(day) to check
a day's rows before writing them, write_day(day) every day, and backfill(first_day, last_day)
for days already past. Every run counts, TEST runs among them (see the Building block).

Here, on the Example database, run the preview with
run(preview("2026-09-24"), send=example_database.send); the Example database can't be written
to, so print the other steps' Hive with show_hive(...). At work, send each step with
run(step, send=run_query), run_query being your own send function.
"""

from sqlglot_composer import FROM, INSERT_OVERWRITE, SELECT, by_day, create_table, statement
from building_blocks.runs_per_job_day import runs_per_job_day
from table_references.daily_job_runs import daily_job_runs

LAST_DAY = "2026-09-24"  # the Example database's last day, which preview reads unless told


def create():
    """Step 1: create mart.daily_job_runs from its Table reference, if it isn't there yet.

    may_exist=True writes CREATE TABLE IF NOT EXISTS, so running every step from the top each
    day skips this one once the table is there. It never changes a table that is.
    """
    return create_table(daily_job_runs, may_exist=True)


def preview(day=LAST_DAY):
    """Step 2: the rows write_day(day) would save, as a SELECT to run and check first."""
    per_job_day = runs_per_job_day(day, day)
    return statement(
        SELECT(per_job_day.job_id, per_job_day.runs, per_job_day.failed_runs,
               per_job_day.minutes),
        FROM(per_job_day),
    )


def write_day(day):
    """Step 3, every day: save the day's rows, replacing whatever the day held.

    INSERT_OVERWRITE replaces the day, so sending this twice leaves the same rows, not twice
    as many. The Date partition, dt, isn't selected: the Toolbox reads the day from the WHERE
    bound in the Building block, which must name one day only, and writes it as
    PARTITION(dt = '...'), which fills it in.
    """
    per_job_day = runs_per_job_day(day, day)
    return statement(
        INSERT_OVERWRITE(daily_job_runs),
        SELECT(per_job_day.job_id, per_job_day.runs, per_job_day.failed_runs,
               per_job_day.minutes),
        FROM(per_job_day),
    )


def backfill(first_day, last_day):
    """Step 4, when needed: save every day from first_day to last_day, one write per day.

    It builds write_day's Statement once over all the days, then by_day cuts it into one
    write per day, oldest first, each with its own PARTITION(dt = '...'). The Building block
    keeps the day in its GROUP_BY, so no day's counts are mixed with another's. Send the
    writes in that order:

        for write in backfill("2026-09-01", "2026-09-24"):
            run(write, send=run_query)
    """
    per_job_day = runs_per_job_day(first_day, last_day)
    return by_day(statement(
        INSERT_OVERWRITE(daily_job_runs),
        SELECT(per_job_day.job_id, per_job_day.runs, per_job_day.failed_runs,
               per_job_day.minutes),
        FROM(per_job_day),
    ))
