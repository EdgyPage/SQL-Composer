# sqlglot Composer 6.0, exported 2026-10-21 07:05 - copy it, then edit your copy
# %% [markdown]
# # <DB>.<TABLE>
#
# TODO: say in one line what one row of <DB>.<TABLE> is.
#
# Quality checks on a table you read. Each day, its row count is saved, so you can read the
# days side by side and see one that looks too small; and checks run on any days you ask:
# repeated_keys looks for a key with more than one row, and null_counts counts NULLs.
#
# Made by `project.new_table("<DB>.<TABLE>", template="quality_checks")` from
# `admin/templates/quality_checks.py`, which filled in the database, the table and its file's name,
# <NAME>. Run the cells top to bottom, once you have filled in two things.
#
# First, this table's Table reference, `references/<NAME>.py`: its `<...>` and TODO lines.
# It lists one column, "row_count", a count, "bigint"; then "dt", the day. Its key is ["dt"],
# one row per day.
#
# Then every `<...>` left in this notebook: the notebook won't run with one left. They are:
#
#   - `<CHECKED_NAME>` and `<CHECKED>`: the table checked, by its file in references/ and
#     its name there, such as `ops__job_events` and `job_events`;
#   - `<DATE_PARTITION>`: its Date partition, its day column, such as `dt`;
#   - `<KEY_COLUMN>`: the column that picks out one row, such as `event_id`;
#   - `<DAY>`: a day the table it reads has, in quotes, such as `"2026-09-24"`.
#
# The code cells: 1 the Project and your send; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet. The logic only imports and defines, so
# `project.load("<DB>.<TABLE>")` can run it from anywhere else, for lineage across your
# tables and for `admin/run_tables.ipynb`.

# %%
# 1. The Project, your send, and a day to try things on
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_lineage, project, run, show_hive
from send import send

DAY = <DAY>  # a day to try the cells on, in quotes, such as "2026-09-24"

# %%
# logic
# 2. The logic: imports and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, HAVING, INSERT_OVERWRITE, SELECT, WHERE, all_columns, between,
    count_rows, create_table, is_null, more_than, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference, of row counts
# the table checked, such as: from references.ops__job_events import job_events
from references.<CHECKED_NAME> import <CHECKED>


def create():
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows(day):
    """The day's row count: the clauses preview and write_day share. The day stays in GROUP_BY, so the days stay apart, and out of SELECT: INSERT_OVERWRITE
    writes it as this table's Date partition, the day the table read is bounded to."""
    return [
        SELECT(AS(count_rows(), "row_count")),
        FROM(<CHECKED>),
        WHERE(between(<CHECKED>.<DATE_PARTITION>, day, day)),
        GROUP_BY(<CHECKED>.<DATE_PARTITION>),
    ]


def preview(day):
    """Step 2: the row write_day(day) would save, as a SELECT to run and check first."""
    return statement(*rows(day))


def write_day(day):
    """Step 3, every day: save the day's row count, replacing whatever the day held."""
    return statement(INSERT_OVERWRITE(<TABLE>), *rows(day))


def repeated_keys(first_day, last_day):
    """Each key that picks out more than one row on the days: it should find no rows."""
    return statement(
        SELECT(<CHECKED>.<KEY_COLUMN>, AS(count_rows(), "times_seen")),
        FROM(<CHECKED>),
        WHERE(between(<CHECKED>.<DATE_PARTITION>, first_day, last_day)),
        GROUP_BY(<CHECKED>.<KEY_COLUMN>),
        HAVING(more_than(count_rows(), 1)),  # tested once the rows of each key are counted
    )


def column_name(column):
    """A column's own name: a column prints as its table and its name, such as
    job_events.minutes, and this keeps the part after the dot."""
    return str(column).split(".")[-1]


def null_counts(first_day, last_day):
    """How many rows on the days hold NULL in each column, as one row: null_minutes counts
    the rows whose minutes is NULL, and so on."""
    counts = [AS(count_rows(where=is_null(column)), f"null_{column_name(column)}")
              for column in all_columns(<CHECKED>)]
    return statement(
        SELECT(*counts),
        FROM(<CHECKED>),
        WHERE(between(<CHECKED>.<DATE_PARTITION>, first_day, last_day)),
    )

# %%
# 3. Try it: the Hive of each step, then the rows
show_hive([create(), write_day(DAY)])
run(preview(DAY), send=send)
run(repeated_keys(DAY, DAY), send=send)  # should have no rows
run(null_counts(DAY, DAY), send=send)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write_day(DAY))

# %%
# 5. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
