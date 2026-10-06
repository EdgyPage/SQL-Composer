# sqlglot Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy
"""Weekly totals from a Saved table's days, added up when they are read.

Why: a write fills one day of a Saved table, so weeks are added up from its saved days when
they are read, rather than saved themselves.

Copy it to: statements/<SAVED_TABLE>_weeks.py

week_totals(first_day, last_day) groups the days by week_start, the Monday that starts each
day's week. A week that first_day or last_day cuts through counts only its days in between,
so start on a Monday and end on a Sunday for whole weeks. Adding a week's days up is right for
counts and totals; a count of different things, such as count_distinct of the jobs that ran,
isn't, since one that ran on two days would be counted twice.

It reads a Saved table, which only your warehouse holds, so it runs there, not on the Example
database.

Mirrors week_totals in example_projects/sqlglot_composer/intermediate/statements/example_3_team_week.py.

Replace each placeholder, brackets and all, wherever it is written in the code, then delete
this Fill in: block:

Fill in:
    <SAVED_TABLE>: the Saved table's Table reference, which is also its file's name in
        table_references/, such as job_day_minutes: a copy of saved_table_reference.py.
    <DATE_PARTITION>: its Date partition, such as dt.
    <GROUP_COLUMN>: its column each row is for, such as job_id.
    <TOTAL>: a column of numbers to add up, such as minutes.
    <TOTAL_NAME>: the same name, in quotes, such as "minutes": the week's column.
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, between, statement, sum_of, week_start,
)
from table_references.<SAVED_TABLE> import <SAVED_TABLE>  # the Saved table it reads


def week_totals(first_day, last_day):
    """Each group's totals per week, from the Saved table's days from first_day to last_day."""
    return statement(
        SELECT(
            AS(week_start(<SAVED_TABLE>.<DATE_PARTITION>), "week"),  # the week's Monday
            <SAVED_TABLE>.<GROUP_COLUMN>,  # one row per week and value of this column
            # add a line like the next for each number to add up
            AS(sum_of(<SAVED_TABLE>.<TOTAL>), <TOTAL_NAME>),
        ),
        FROM(<SAVED_TABLE>),
        WHERE(between(<SAVED_TABLE>.<DATE_PARTITION>, first_day, last_day)),
        # "week" names the SELECT's week_start(...) column: the Hive repeats the calculation
        GROUP_BY("week", <SAVED_TABLE>.<GROUP_COLUMN>),
    )
