# sqlglot Composer 4.0, exported 2026-10-06 00:26 - copy it, then edit your copy
"""A Building block: a Derived table of each group's day, for several Statements.

Why: written once, in a function that takes the days, the numbers are worked out the same way
in every Statement that reads them.

Copy it to: building_blocks/<BLOCK>.py

A Derived table is a Statement given a name, which another Statement reads like a table. The
days are the function's arguments, so the same block serves a preview of one day, a write of
one day and a backfill of many. It keeps the Date partition in SELECT and GROUP_BY, so each
day's numbers stay apart when it reads many days.

It reads one table, through its Table reference, such as the one notebook_start.py writes. The
Saved table's Table reference, a copy of saved_table_reference.py, repeats the names its AS(...)
gives.

Mirrors example_projects/sqlglot_composer/starter/building_blocks/runs_per_job_day.py.

Replace each placeholder, brackets and all, wherever it is written in the code, then delete
this Fill in: block:

Fill in:
    <BLOCK>: the block's name, which is also its file's name, saying what one row is, such as
        minutes_per_job_day.
    <BLOCK_NAME>: the same name in quotes, such as "minutes_per_job_day": Python names the
        function by <BLOCK>, and the Hive names the Derived table by this text.
    <TABLE>: the Table reference it reads, which is also its file's name in table_references/,
        such as job_runs.
    <GROUP_COLUMN>: the column each row is for, such as job_id.
    <DATE_PARTITION>: the table's Date partition, the column holding each row's day, such as dt.
    <NUMBER_COLUMN>: a column of numbers to add up, such as duration_mins.
    <TOTAL_NAME>: the name of what it adds up to, in quotes, such as "minutes".
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows, derived, statement, sum_of,
)
from table_references.<TABLE> import <TABLE>  # the Table reference it reads


def <BLOCK>(first_day, last_day):  # named as its file is
    """One row per group and day from first_day to last_day: its rows, and its total."""
    return derived(
        <BLOCK_NAME>,  # the name the Hive gives it
        statement(
            SELECT(
                <TABLE>.<GROUP_COLUMN>,  # what each row is for
                <TABLE>.<DATE_PARTITION>,  # the day, kept so that each day stays apart
                AS(count_rows(), "row_count"),
                # add a line like the next for each number to add up
                AS(sum_of(<TABLE>.<NUMBER_COLUMN>), <TOTAL_NAME>),
            ),
            FROM(<TABLE>),
            WHERE(between(<TABLE>.<DATE_PARTITION>, first_day, last_day)),
            GROUP_BY(<TABLE>.<GROUP_COLUMN>, <TABLE>.<DATE_PARTITION>),
        ),
    )
