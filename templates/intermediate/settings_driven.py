"""Statements from settings: one dict per table, the same Statement for each.

Why: when the same Statement repeats over many tables, writing what differs once per table, as
settings, means adding a table is one more dict, and a fix to the Statement reaches every
table at once.

Copy it to: statements/daily_totals.py

Each dict in SETTINGS names a table's Table reference, its Date partition, and the columns to
add up each day. daily_totals(setting, first_day, last_day) makes one Statement from one dict:
each day's rows and the total of each column to add up. every_daily_total(first_day,
last_day) makes it for every dict, in order: print their Hive with show_hive(*...), or send
each with run(...). The days are handed to between(...) as a datetime.date, which the Toolbox
writes the way each Table reference says its table writes its days, so the same Statement
works on a table whose days are written like 20260924.

The settings sit in this file, beside the Statement made from them, so each dict can hold the
Table reference itself. When several Statement files read the same settings, keep them in a
settings.py of their own, beside table_references/, as the intermediate Example project does:
there they are Level 0, so they name each table by its name as text.

Mirrors example_projects/intermediate/settings.py and rows_per_day in
example_projects/intermediate/statements/quality_checks.py.

Replace each placeholder, brackets and all, wherever it is written:

Fill in:
    <FIRST_TABLE>: the first table's Table reference, which is also its file's name in
        table_references/, such as region_costs.
    <FIRST_DATE_PARTITION>: its Date partition, such as dt.
    <ADD_UP_COLUMN>: a column of the first table to add up each day, such as cost_cents.
    <SECOND_TABLE>: a second table's Table reference, such as job_events. Its dict adds
        nothing up, which leaves each day's rows.
    <SECOND_DATE_PARTITION>: its Date partition, such as dt.
"""

import datetime

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows, statement, sum_of,
)
from table_references.<FIRST_TABLE> import <FIRST_TABLE>
from table_references.<SECOND_TABLE> import <SECOND_TABLE>

# One dict per table: its Table reference, its Date partition, and the columns to add up each
# day, which may be none. Add a dict per table, and import its Table reference above.
SETTINGS = [
    {
        "table": <FIRST_TABLE>,
        "day": <FIRST_TABLE>.<FIRST_DATE_PARTITION>,
        "add_up": [<FIRST_TABLE>.<ADD_UP_COLUMN>],  # a column per entry
    },
    {
        "table": <SECOND_TABLE>,
        "day": <SECOND_TABLE>.<SECOND_DATE_PARTITION>,
        "add_up": [],  # nothing to add up: each day's rows only
    },
]


def column_name(column):
    """A column's own name: a column prints as its Table reference's name, a dot, then its
    own name, and this keeps the part after the dot."""
    return str(column).split(".")[-1]


def daily_totals(setting, first_day, last_day):
    """One table's rows and totals per day from first_day to last_day, both written like
    "2026-09-24", from one dict of SETTINGS."""
    totals = [AS(sum_of(column), f"total_{column_name(column)}") for column in setting["add_up"]]
    return statement(
        SELECT(setting["day"], AS(count_rows(), "row_count"), *totals),
        FROM(setting["table"]),
        WHERE(between(setting["day"], datetime.date.fromisoformat(first_day),
                      datetime.date.fromisoformat(last_day))),
        GROUP_BY(setting["day"]),
    )


def every_daily_total(first_day, last_day):
    """daily_totals for every dict of SETTINGS, in order, as a list of Statements."""
    return [daily_totals(setting, first_day, last_day) for setting in SETTINGS]
