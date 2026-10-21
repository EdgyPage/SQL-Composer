"""The Templates project.start() copies into a Project's admin/templates/, each as its text.

A Template is a file with placeholders written <LIKE_THIS>. project.new_table fills in <DB>,
<TABLE> and <NAME> (the database, the table, and the two joined by two underscores, such as
mart__daily_job_runs); every other placeholder is yours to fill in, and Python stops at the
first one left in, so a half-filled file can't run.

A Table notebook's Template is a .py file whose cells start with a "# %%" line, "# %% [markdown]"
for a text cell, whose lines each start with "# ". The copies in admin/templates/ are yours:
edit one, or add your own beside them, and the next project.new_table(...) uses it. Editing a
Template changes only the notebooks made after.
"""

from __future__ import annotations

TOOLBOX_VERSION = "6.0"

DAILY_TABLE = '''# %% [markdown]
# # <DB>.<TABLE>
#
# TODO: say in one line what one row of <DB>.<TABLE> is.
#
# Made by `project.new_table("<DB>.<TABLE>")` from `admin/templates/daily_table.py`. Run the
# cells top to bottom. Fill in every `<...>` first: the notebook won't run with one left.
#
# Cell 2, the logic, only imports and defines. `project.load("<DB>.<TABLE>")` runs it from
# anywhere else, for lineage across your tables and for `admin/run_tables.ipynb`.

# %%
# 1. The Project, your send, and a day to try things on
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_lineage, project, run, show_hive
from send import send

DAY = <DAY>  # a day to try the cells on, in quotes, such as "2026-10-20"

# %%
# logic
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, between, by_day, count_rows,
    create_table, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference
from references.<SOURCE_NAME> import <SOURCE_TABLE>  # each table it reads, such as ops__job_runs


def create():
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows(first_day, last_day):
    """The clauses every step below shares, so preview, write_day and backfill can never
    disagree. Keep the day in GROUP_BY, so backfill's days stay apart."""
    return [
        SELECT(<SOURCE_TABLE>.<KEY_COLUMN>, AS(count_rows(), <COUNT_NAME>)),
        FROM(<SOURCE_TABLE>),
        WHERE(between(<SOURCE_TABLE>.<DATE_PARTITION>, first_day, last_day)),
        GROUP_BY(<SOURCE_TABLE>.<DATE_PARTITION>, <SOURCE_TABLE>.<KEY_COLUMN>),
    ]


def preview(day):
    """Step 2: the rows write_day(day) would save, as a SELECT to run and check first."""
    return statement(*rows(day, day))


def write_day(day):
    """Step 3, every day: save the day's rows, replacing whatever the day held."""
    return statement(INSERT_OVERWRITE(<TABLE>), *rows(day, day))


def backfill(first_day, last_day):
    """Step 4, when needed: one write per day from first_day to last_day, oldest first."""
    return by_day(statement(INSERT_OVERWRITE(<TABLE>), *rows(first_day, last_day)))

# %%
# 3. Try it: the Hive of each step, then the day's rows
show_hive([create(), write_day(DAY)])
run(preview(DAY), send=send)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write_day(DAY))

# %%
# 5. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
'''

SAVED_TABLE_REFERENCE = '''"""<DB>.<TABLE> - TODO: say in one line what one row is.

Why: TODO: who reads this table, and why it is saved rather than worked out each time.

project.new_table wrote this file from admin/templates/saved_table_reference.py. A Saved
table's Table reference is filled in by hand, since the table doesn't exist until its
notebook's create() makes it from this file.
"""

from sqlglot_composer import Table

<TABLE> = Table(
    "<DB>.<TABLE>",
    columns={
        <COLUMN>: <COLUMN_TYPE>,  # every column write_day saves, in order, each in quotes
        "dt": "string",  # the day, as yyyy-MM-dd
    },
    date_partition="dt",
    key=[<COLUMN>, "dt"],  # the columns that pick out one row of a day
    location=<LOCATION>,  # the folder your Saved tables go in, such as "/data/your_team/tables"
    descriptions={},  # optional: {"column": "what it holds"}, for the Reference sheet
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.<NAME> import <TABLE>, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
# gives back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = <TABLE>.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(<TABLE>.<column>, <value>)
'''

# Each Template by the name new_table's template= takes, as start() writes it into
# admin/templates/<name>.py.
TEMPLATES = {
    "daily_table": DAILY_TABLE,
    "saved_table_reference": SAVED_TABLE_REFERENCE,
}
