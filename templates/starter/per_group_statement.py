"""A Statement counting and adding up per group, keeping groups that pass a test.

Why: GROUP_BY makes one row per group, and HAVING then keeps the groups whose counts pass a
test, which WHERE can't do, since WHERE sees each row before the rows are counted.

Copy it to: statements/<STATEMENT>.py

<STATEMENT>(first_day, last_day) reads the days from first_day to last_day, both included, and
adds them all up into one row per group: the day isn't in GROUP_BY, so the days are added
together. It is a SELECT, to run and look at from a notebook started in your project's folder,
with send as notebook_start.py writes it:

    from statements.<STATEMENT> import <STATEMENT>
    run(<STATEMENT>("2026-09-23", "2026-09-24"), send=send)

Mirrors the GROUP_BY of example_projects/starter/statements/example_2_alerts_per_job.py and
the HAVING of example_projects/intermediate/statements/quality_checks.py.

Replace each placeholder, brackets and all, wherever it is written in the code, then delete
this Fill in: block:

Fill in:
    <STATEMENT>: what one row is, such as minutes_per_job: the function's name, and its file's
        name in statements/.
    <TABLE>: the Table reference it reads, which is also its file's name in table_references/,
        such as job_runs.
    <GROUP_COLUMN>: the column to make one row per value of, such as job_id.
    <NUMBER_COLUMN>: a column of numbers to add up, such as duration_mins.
    <TOTAL_NAME>: the name of what it adds up to, in quotes, such as "minutes".
    <DATE_PARTITION>: the table's Date partition, the column holding each row's day, such as dt.
    <MORE_THAN_ROWS>: keep a group only if it has more rows than this: a number, without
        quotes, such as 1.
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, HAVING, SELECT, WHERE, between, count_rows, more_than, statement, sum_of,
)
from table_references.<TABLE> import <TABLE>  # the Table reference it reads


def <STATEMENT>(first_day, last_day):  # named as its file is
    """Each group's rows and total from first_day to last_day, for the groups with more rows
    than the test in HAVING."""
    return statement(
        SELECT(
            <TABLE>.<GROUP_COLUMN>,  # one row per value of this column
            AS(count_rows(), "row_count"),
            # add a line like the next for each number to add up
            AS(sum_of(<TABLE>.<NUMBER_COLUMN>), <TOTAL_NAME>),
        ),
        FROM(<TABLE>),
        WHERE(between(<TABLE>.<DATE_PARTITION>, first_day, last_day)),  # the days read
        GROUP_BY(<TABLE>.<GROUP_COLUMN>),
        HAVING(more_than(count_rows(), <MORE_THAN_ROWS>)),  # tested once the rows are counted
    )
