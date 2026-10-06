"""Statements from settings: the same ones for each table, its differences as text.

Why: when the same Statements repeat over many tables, writing each table's few differences
once, as settings, means adding a table is one more dict, and a fix to a Statement reaches
every table at once.

Copy it to: statements/quality_from_settings.py

SETTINGS holds one dict per table, all text:

- "name": the table's name, as its Table reference names it;
- "date_partition": its Date partition's name;
- "key": the names of the columns that pick out one row, as its Table reference's key names
  them;
- "add_up": the names of the columns to add up each day, which may be none.

TABLE_REFERENCES finds each table's Table reference by its name, and getattr finds a column by
its name: getattr(job_events, "dt") is job_events.dt. repeated_keys and rows_per_day each make
one table's Statement from its dict. every_statement(first_day, last_day) makes both for every
table, by name, such as "rows_per_day ops.region_costs"; run_all(send, first_day, last_day)
runs them all and gives back a dict of pandas DataFrames, by the same names. Print one's Hive
with show_hive(...).

The settings are text, as the intermediate Example project's settings.py keeps them, so they
can move unchanged into a settings.py of their own, beside table_references/, when several
Statement files read them. settings.py is Level 0, as the Table references are, so it can't
import them: that is why a dict names its table by its name, and TABLE_REFERENCES, here,
finds the Table reference.

The days are given written like "2026-09-24", and handed to between(...) as a datetime.date,
which the Toolbox writes the way each Table reference says its table writes its days, so the
same Statement works on a table whose days are written like 20260924.

Mirrors example_projects/intermediate/settings.py and
example_projects/intermediate/statements/quality_checks.py.

Replace each placeholder, brackets and all, wherever it is written in the code, then delete
this Fill in: block:

Fill in:
    <FIRST_TABLE>: the first table's Table reference, which is also its file's name in
        table_references/, such as region_costs.
    <FIRST_TABLE_NAME>: its name in the warehouse, in quotes, as its Table reference names it,
        such as "ops.region_costs".
    <FIRST_DATE_PARTITION>: its Date partition's name, in quotes, such as "dt".
    <FIRST_KEY>: the names of the columns that pick out one row, each in quotes, with commas
        between, such as "job_id", "region", "dt".
    <FIRST_ADD_UP>: the name of a column to add up each day, in quotes, such as "cost_cents".
    <SECOND_TABLE>: a second table's Table reference, such as job_events. Its dict adds
        nothing up, which leaves each day's rows.
    <SECOND_TABLE_NAME>: its name in the warehouse, in quotes, such as "ops.job_events".
    <SECOND_DATE_PARTITION>: its Date partition's name, in quotes, such as "dt".
    <SECOND_KEY>: the names of the columns that pick out one row, each in quotes, such as
        "event_id".
"""

import datetime

from sqlglot_composer import (
    AS, FROM, GROUP_BY, HAVING, SELECT, WHERE, between, count_rows, more_than, run, statement,
    sum_of,
)
from table_references.<FIRST_TABLE> import <FIRST_TABLE>  # an import per table
from table_references.<SECOND_TABLE> import <SECOND_TABLE>

# One dict per table, all text. Add a dict per table, and its Table reference to
# TABLE_REFERENCES below.
SETTINGS = [
    {
        "name": <FIRST_TABLE_NAME>,
        "date_partition": <FIRST_DATE_PARTITION>,
        "key": [<FIRST_KEY>],  # every column of the key
        "add_up": [<FIRST_ADD_UP>],  # each column to add up each day
    },
    {
        "name": <SECOND_TABLE_NAME>,
        "date_partition": <SECOND_DATE_PARTITION>,
        "key": [<SECOND_KEY>],
        "add_up": [],  # nothing to add up: each day's rows only
    },
]

# Each table's Table reference, by the name its dict gives it.
TABLE_REFERENCES = {
    <FIRST_TABLE_NAME>: <FIRST_TABLE>,
    <SECOND_TABLE_NAME>: <SECOND_TABLE>,
}


def on_the_days(table_reference, setting, first_day, last_day):
    """The condition bounding the table's Date partition from first_day to last_day."""
    date_partition = getattr(table_reference, setting["date_partition"])
    return between(date_partition, datetime.date.fromisoformat(first_day),
                   datetime.date.fromisoformat(last_day))


def repeated_keys(setting, first_day, last_day):
    """Each key of one table, from its dict, that picks out more than one row on the days: it
    should find no rows."""
    table_reference = TABLE_REFERENCES[setting["name"]]
    key = [getattr(table_reference, name) for name in setting["key"]]
    return statement(
        SELECT(*key, AS(count_rows(), "times_seen")),
        FROM(table_reference),
        WHERE(on_the_days(table_reference, setting, first_day, last_day)),
        GROUP_BY(*key),
        HAVING(more_than(count_rows(), 1)),  # tested once the rows of each key are counted
    )


def rows_per_day(setting, first_day, last_day):
    """Each day's rows in one table, from its dict, with each of its add_up columns added up
    for the day."""
    table_reference = TABLE_REFERENCES[setting["name"]]
    date_partition = getattr(table_reference, setting["date_partition"])
    added_up = [AS(sum_of(getattr(table_reference, name)), name) for name in setting["add_up"]]
    return statement(
        SELECT(date_partition, AS(count_rows(), "row_count"), *added_up),
        FROM(table_reference),
        WHERE(on_the_days(table_reference, setting, first_day, last_day)),
        GROUP_BY(date_partition),
    )


def every_statement(first_day, last_day):
    """Both Statements for every table in SETTINGS, by name, such as
    "repeated_keys ops.job_events"."""
    statements = {}
    for setting in SETTINGS:
        name = setting["name"]
        statements[f"repeated_keys {name}"] = repeated_keys(setting, first_day, last_day)
        statements[f"rows_per_day {name}"] = rows_per_day(setting, first_day, last_day)
    return statements


def run_all(send, first_day, last_day):
    """Run every Statement for the days, and give back what each found, by name: a dict of
    pandas DataFrames. Look at each, or keep those with rows."""
    statements = every_statement(first_day, last_day)
    return {name: run(each, send=send) for name, each in statements.items()}
