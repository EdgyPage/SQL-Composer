# Spark Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy
"""Data quality Statements for a table: repeated keys, NULL counts, rows per day.

Why: the same three Statements catch most bad days in any table, so they are worth writing
once for each table you build on, and running after each day comes in.

Copy it to: statements/<TABLE>_quality.py

- repeated_keys: each key that picks out more than one row, which should find none: a join on
  a repeated key matches one row twice, and counts it twice.
- null_counts: how many rows hold NULL in each column, as one row of counts, each named null_
  and the column's name, every column from all_columns(...), so a column added to the Table
  reference later is counted too. The Date partition is left out: a row read by its day always
  has one.
- rows_per_day: each day's rows, to spot a day missing or too small.

Each is a SELECT to run and look at, not a write. run_all(send, first_day, last_day) runs them
all and gives back a dict of pandas DataFrames, by name.

The days are given written like "2026-09-24", and handed to between(...) as a datetime.date,
which the Toolbox writes the way the Table reference says the table writes its days. So the
same Statements work on a table whose days are written like 20260924. A day given as text, as
the starter Templates give it, must be written the table's way already, or the Toolbox stops
and says how to write it.

Mirrors example_projects/spark_composer/intermediate/statements/quality_checks.py, for one table.

Replace each placeholder, brackets and all, wherever it is written in the code, then delete
this Fill in: block:

Fill in:
    <TABLE>: the Table reference to look at, which is also its file's name in
        table_references/, such as job_events.
    <KEY_COLUMN>: the column that picks out one row, such as event_id; for a key of several
        columns, list each in KEY.
    <DATE_PARTITION>: its Date partition, such as dt.
"""

import datetime

from spark_composer import (
    AS, FROM, GROUP_BY, HAVING, SELECT, WHERE, all_columns, between, count_rows, is_null,
    more_than, run, statement,
)
from table_references.<TABLE> import <TABLE>  # the Table reference to look at

KEY = [<TABLE>.<KEY_COLUMN>]  # the columns that pick out one row, as the Table reference's key


def on_the_days(first_day, last_day):
    """The condition bounding the Date partition from first_day to last_day, both written like
    "2026-09-24"."""
    return between(<TABLE>.<DATE_PARTITION>, datetime.date.fromisoformat(first_day),
                   datetime.date.fromisoformat(last_day))


def column_name(column):
    """A column's own name, to name its count: a column prints as its Table reference's name,
    a dot, then its own name, such as job_events.minutes, and this keeps the part after the
    dot."""
    return str(column).split(".")[-1]


def repeated_keys(first_day, last_day):
    """Each key that picks out more than one row on the days: it should find no rows."""
    return statement(
        SELECT(*KEY, AS(count_rows(), "times_seen")),
        FROM(<TABLE>),
        WHERE(on_the_days(first_day, last_day)),
        GROUP_BY(*KEY),
        HAVING(more_than(count_rows(), 1)),  # tested once the rows of each key are counted
    )


def null_counts(first_day, last_day):
    """How many rows on the days hold NULL in each column but the Date partition, as one
    row."""
    columns = [column for column in all_columns(<TABLE>)
               if column_name(column) != column_name(<TABLE>.<DATE_PARTITION>)]
    return statement(
        SELECT(*[AS(count_rows(where=is_null(column)), f"null_{column_name(column)}")
                 for column in columns]),
        FROM(<TABLE>),
        WHERE(on_the_days(first_day, last_day)),
    )


def rows_per_day(first_day, last_day):
    """Each day's rows. A day with no rows has no row here, rather than a 0."""
    return statement(
        SELECT(<TABLE>.<DATE_PARTITION>, AS(count_rows(), "row_count")),
        FROM(<TABLE>),
        WHERE(on_the_days(first_day, last_day)),
        GROUP_BY(<TABLE>.<DATE_PARTITION>),
    )


def run_all(send, first_day, last_day):
    """Run every Statement above for the days, and give back what each found, by name: a dict
    of pandas DataFrames. Look at each, or keep those with rows."""
    statements = {
        "repeated_keys": repeated_keys(first_day, last_day),
        "null_counts": null_counts(first_day, last_day),
        "rows_per_day": rows_per_day(first_day, last_day),
    }
    return {name: run(each, send=send) for name, each in statements.items()}
