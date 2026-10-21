# sqlglot Composer 6.0, exported 2026-10-21 07:24 - copy it, then edit your copy
"""<BLOCK> - TODO: say in one line what one row of it is.

Why: TODO: which tables' notebooks read it, so they can never work it out two ways.

Copied by hand from admin/templates/building_block.py into building_blocks/<BLOCK>.py. A
Building block is a piece several notebooks share; this one is a Derived table, a Statement
given a name, which each Statement reading it writes at its top, as WITH <BLOCK> AS (...). In a
notebook's logic cell, import it and read it like a table:

    from building_blocks.<BLOCK> import <BLOCK>


    def preview(day):
        per_group = <BLOCK>(day, day)
        return statement(SELECT(per_group.<GROUP_COLUMN>, per_group.row_count),
                         FROM(per_group))

Fill in every <...>:
    <BLOCK> and <BLOCK_NAME>: its name, as a name and in quotes, such as minutes_per_job_day
        and "minutes_per_job_day".
    <SOURCE_NAME> and <SOURCE_TABLE>: the table it reads, by its file in references/ and its
        name there, such as ops__job_runs and job_runs.
    <GROUP_COLUMN>: the column each row is for, such as job_id.
    <DATE_PARTITION>: the table's Date partition, its day column, such as dt.
    <NUMBER_COLUMN>: a column of numbers to add up, such as duration_mins.
    <TOTAL_NAME>: the name of what it adds up to, in quotes, such as "minutes".
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows, derived, statement, sum_of,
)
from references.<SOURCE_NAME> import <SOURCE_TABLE>  # the Table reference it reads


def <BLOCK>(first_day, last_day):  # named as its file is
    """One row per group and day from first_day to last_day: its rows, and its total."""
    return derived(
        <BLOCK_NAME>,  # the name the Hive gives it
        statement(
            SELECT(
                <SOURCE_TABLE>.<GROUP_COLUMN>,  # what each row is for
                <SOURCE_TABLE>.<DATE_PARTITION>,  # the day, kept so that each day stays apart
                AS(count_rows(), "row_count"),
                # add a line like the next for each number to add up
                AS(sum_of(<SOURCE_TABLE>.<NUMBER_COLUMN>), <TOTAL_NAME>),
            ),
            FROM(<SOURCE_TABLE>),
            WHERE(between(<SOURCE_TABLE>.<DATE_PARTITION>, first_day, last_day)),
            GROUP_BY(<SOURCE_TABLE>.<GROUP_COLUMN>, <SOURCE_TABLE>.<DATE_PARTITION>),
        ),
    )
