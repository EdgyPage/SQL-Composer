"""An incremental load: each run writes the last few days of a Saved table again.

Why: rows can come in a day or two after their day was saved, so each run writes the last few
days again, and INSERT_OVERWRITE replaces each day it writes rather than adding to it.

Copy it to: statements/<SAVED_TABLE>.py

Each run sends write_last_days(day): one write per day from first_day_written(day) to the day,
oldest first. by_day cuts one Statement over all those days into a write per day, each with
its own PARTITION(dt = '...'). A late row lands in the partition of its own day, so the next
run that writes that day again saves it, and a run sent twice by mistake does no harm. To fill
in days already past, such as when the Saved table is new, send write_days with an earlier
first_day: that is a backfill, the same Statement over more days.

The Building block must keep its Date partition in SELECT and GROUP_BY, as the starter
Template building_block.py does, so by_day can cut it into days.

Mirrors example_projects/intermediate/statements/example_1_job_day_costs.py.

Replace each placeholder, brackets and all, wherever it is written:

Fill in:
    <SAVED_TABLE>: the Saved table's Table reference, which is also its file's name in
        table_references/, such as job_day_costs.
    <BLOCK>: the Building block giving one row per group and day, which is also its file's
        name in building_blocks/, such as costs_per_job_day.
    <GROUP_COLUMN>: the block's column each row is for, such as job_id.
    <TOTAL>: the block's added-up column, such as cost_cents. Select every column the Saved
        table holds but its Date partition, in its order.
    <DAYS_REWRITTEN>: how many days each run writes, ending on its own day, such as 3.
"""

import datetime

from sqlglot_composer import FROM, INSERT_OVERWRITE, SELECT, by_day, create_table, statement
from building_blocks.<BLOCK> import <BLOCK>
from table_references.<SAVED_TABLE> import <SAVED_TABLE>

DAYS_REWRITTEN = <DAYS_REWRITTEN>  # each run writes its own day and the days just before it


def first_day_written(day):
    """The first day a run for `day` writes: with 3 days rewritten,
    first_day_written("2026-09-24") is "2026-09-22"."""
    first_day = datetime.date.fromisoformat(day) - datetime.timedelta(days=DAYS_REWRITTEN - 1)
    return first_day.isoformat()


def create():
    """Step 1: create the Saved table from its Table reference, if it isn't there yet."""
    return create_table(<SAVED_TABLE>, may_exist=True)


def preview(day):
    """Step 2: the rows a write of the day would save, as a SELECT to run and look at first."""
    rows = <BLOCK>(day, day)
    return statement(
        SELECT(rows.<GROUP_COLUMN>, rows.<TOTAL>),  # the Saved table's columns but its dt
        FROM(rows),
    )


def write_days(first_day, last_day):
    """Save every day from first_day to last_day, one write per day, oldest first."""
    rows = <BLOCK>(first_day, last_day)
    return by_day(statement(
        INSERT_OVERWRITE(<SAVED_TABLE>),
        SELECT(rows.<GROUP_COLUMN>, rows.<TOTAL>),
        FROM(rows),
    ))


def write_last_days(day):
    """Step 3, every run: write the last DAYS_REWRITTEN days, ending on the day. Send the
    writes in order:

        for write in write_last_days("2026-09-24"):
            run(write, send=send)
    """
    return write_days(first_day_written(day), day)
