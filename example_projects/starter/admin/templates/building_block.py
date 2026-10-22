"""<BLOCK> - TODO: say in one line what one row of it is.

Fill in every <...> below, brackets and all: Python stops at one left in. They are:
    <BLOCK> and <BLOCK_NAME>: its name, as a name and in quotes, such as runs_per_job and
        "runs_per_job": its file is building_blocks/<BLOCK>.py, named the same.
    <SOURCE_NAME> and <SOURCE_TABLE>: the table it reads, by its file in references/ and its
        name there, such as ops__job_runs and job_runs.
    <GROUP_COLUMN>: the column each row is for, such as job_id.
    <NUMBER_COLUMN>: a column of numbers to add up, such as duration_mins.
    <TOTAL_NAME>: the name of what it adds up to, in quotes, such as "minutes".

Why: TODO: which tables' notebooks read it, so they can never work it out two ways.

Copied by hand from admin/templates/building_block.py into building_blocks/<BLOCK>.py. A
Building block is a piece several notebooks share; this one is a Derived table, a Statement
given a name, which each Statement reading it writes at its top, as WITH <BLOCK> AS (...). In a
notebook's logic cell, import it, and read it like a table, given the rows it reads:

    from building_blocks.<BLOCK> import <BLOCK>


    def preview() -> Statement:
        per_group = <BLOCK>(READS)
        return statement(SELECT(per_group.<GROUP_COLUMN>, per_group.row_count),
                         FROM(per_group))
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, Condition, Table, count_rows, derived, statement,
    sum_of,
)
from references.<SOURCE_NAME> import <SOURCE_TABLE>  # the Table reference it reads


def <BLOCK>(reads: Condition) -> Table:  # named as its file is
    """One row per group of the rows `reads` picks: its rows, and its total.

    `reads` is a condition on the table it reads, such as equals(job_runs.dt, "2026-09-24").
    On a partitioned table, it must filter one of its partition columns.
    """
    return derived(
        <BLOCK_NAME>,  # the name the Hive gives it
        statement(
            SELECT(
                <SOURCE_TABLE>.<GROUP_COLUMN>,  # what each row is for
                # to keep each Partition's rows apart, add its partition column here and in
                # GROUP_BY, such as job_runs.dt
                AS(count_rows(), "row_count"),
                # add a line like the next for each number to add up
                AS(sum_of(<SOURCE_TABLE>.<NUMBER_COLUMN>), <TOTAL_NAME>),
            ),
            FROM(<SOURCE_TABLE>),
            WHERE(reads),
            GROUP_BY(<SOURCE_TABLE>.<GROUP_COLUMN>),
        ),
    )
