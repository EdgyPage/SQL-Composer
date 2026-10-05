"""A Saved table's steps: create, preview a day, write a day, backfill past days.

Why: numbers counted once a day and saved can be read by anyone, quickly, without counting
every row again each time someone asks.

Copy it to: statements/<SAVED_TABLE>.py

The steps, in order: create() once, preview(day) to look at a day's rows before writing them,
write_day(day) every day, and backfill(first_day, last_day) for days already past. Each
returns Statements; send each with run(step, send=send), or every day's steps at once with
run_pipeline.py, a copy of daily_pipeline.py.

write_day and backfill save the same rows for a day. backfill builds the Statement once over
all the days, then by_day cuts it into one write per day, oldest first. No step selects the
Saved table's Date partition, dt: the Toolbox reads the day from the Building block's WHERE
bound, one day only, and writes it as PARTITION(dt = '...').

Mirrors example_projects/starter/statements/example_1_daily_job_runs.py.

Replace each placeholder, brackets and all, wherever it is written:

Fill in:
    <SAVED_TABLE>: the Saved table's Table reference, which is also its file's name in
        table_references/, such as job_day_minutes: a copy of table_reference.py.
    <BLOCK>: the Building block giving one row per group and day, which is also its file's
        name in building_blocks/, such as minutes_per_job_day: a copy of building_block.py.
    <GROUP_COLUMN>: the block's column each row is for, such as job_id.
    <TOTAL>: the block's added-up column, such as minutes.
"""

from sqlglot_composer import FROM, INSERT_OVERWRITE, SELECT, by_day, create_table, statement
from building_blocks.<BLOCK> import <BLOCK>
from table_references.<SAVED_TABLE> import <SAVED_TABLE>


def create():
    """Step 1: create the Saved table from its Table reference, if it isn't there yet.

    may_exist=True writes CREATE TABLE IF NOT EXISTS, so this step can run every day, and does
    nothing once the table is there.
    """
    return create_table(<SAVED_TABLE>, may_exist=True)


def preview(day):
    """Step 2: the rows write_day(day) would save, as a SELECT to run and look at first."""
    rows = <BLOCK>(day, day)
    return statement(
        # the Saved table's columns, in its order, all but its Date partition
        SELECT(rows.<GROUP_COLUMN>, rows.row_count, rows.<TOTAL>),
        FROM(rows),
    )


def write_day(day):
    """Step 3, every day: save the day's rows, replacing whatever the day held.

    INSERT_OVERWRITE replaces the day, so sending this twice leaves the same rows, not twice as
    many.
    """
    rows = <BLOCK>(day, day)
    return statement(
        INSERT_OVERWRITE(<SAVED_TABLE>),
        SELECT(rows.<GROUP_COLUMN>, rows.row_count, rows.<TOTAL>),
        FROM(rows),
    )


def backfill(first_day, last_day):
    """Step 4, when needed: save every day from first_day to last_day, one write per day.

    It returns a list of writes, oldest first. Send them in that order:

        for write in backfill("2026-09-01", "2026-09-24"):
            run(write, send=send)
    """
    rows = <BLOCK>(first_day, last_day)
    return by_day(statement(
        INSERT_OVERWRITE(<SAVED_TABLE>),
        SELECT(rows.<GROUP_COLUMN>, rows.row_count, rows.<TOTAL>),
        FROM(rows),
    ))
