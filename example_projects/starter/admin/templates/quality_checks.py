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
# It lists one column, "row_count", a count, "bigint"; then "dt", the day, the partition
# column. Give it key=["dt"]: one row per day.
#
# Then every `<...>` left in this notebook: the notebook won't run with one left. They are:
#
#   - `<CHECKED_NAME>` and `<CHECKED>`: the table checked, by its file in references/ and
#     its name there, such as `ops__job_events` and `job_events`;
#   - `<DATE_PARTITION>`: its partition column holding the day, such as `dt`;
#   - `<KEY_COLUMN>`: the column that picks out one row, such as `event_id`;
#   - `<DAY>`: the day write() writes, one the table it reads has, in quotes, such as
#     `"2026-09-24"`.
#
# The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet. The logic only imports and defines, so
# `project.load("<DB>.<TABLE>")` can run it from anywhere else, for lineage across your
# tables and for `admin/run_tables.ipynb`, which sends its `write()`.

# %%
# 1. The Project and your query
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_lineage, project, run, show_hive
from warehouse import query

# %%
# logic
# 2. The logic: imports, the day it writes, and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, HAVING, INSERT_OVERWRITE, SELECT, WHERE, Clause, Column,
    Statement, all_columns, between, count_rows, create_table, is_null, more_than, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference, of row counts
# the table checked, such as: from references.ops__job_events import job_events
from references.<CHECKED_NAME> import <CHECKED>

DAY = <DAY>  # the day write() writes: change it to write another


def create() -> Statement:
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows(day: str) -> list[Clause]:
    """The day's row count: the clauses preview and write share. The day stays in GROUP_BY, so the days stay apart, and comes last in SELECT, as "dt":
    INSERT_OVERWRITE writes each day's rows into that day's partition of this table,
    replacing only the days the rows hold."""
    return [
        SELECT(AS(count_rows(), "row_count"), AS(<CHECKED>.<DATE_PARTITION>, "dt")),
        FROM(<CHECKED>),
        WHERE(between(<CHECKED>.<DATE_PARTITION>, day, day)),
        GROUP_BY(<CHECKED>.<DATE_PARTITION>),
    ]


def preview() -> Statement:
    """Step 2: the row write() would save, as a SELECT to run and check first."""
    return statement(*rows(DAY))


def write() -> Statement:
    """Step 3: save DAY's row count, replacing whatever DAY held."""
    return statement(INSERT_OVERWRITE(<TABLE>), *rows(DAY))


def repeated_keys(first_day: str, last_day: str) -> Statement:
    """Each key that picks out more than one row on the days: it should find no rows."""
    return statement(
        SELECT(<CHECKED>.<KEY_COLUMN>, AS(count_rows(), "times_seen")),
        FROM(<CHECKED>),
        WHERE(between(<CHECKED>.<DATE_PARTITION>, first_day, last_day)),
        GROUP_BY(<CHECKED>.<KEY_COLUMN>),
        HAVING(more_than(count_rows(), 1)),  # tested once the rows of each key are counted
    )


def column_name(column: Column) -> str:
    """A column's own name: a column prints as its table and its name, such as
    job_events.minutes, and this keeps the part after the dot."""
    return str(column).split(".")[-1]


def null_counts(first_day: str, last_day: str) -> Statement:
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
show_hive([create(), write()])
run(preview(), query=query)
run(repeated_keys(DAY, DAY), query=query)  # should have no rows
run(null_counts(DAY, DAY), query=query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
