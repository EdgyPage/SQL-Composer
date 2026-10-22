# %% [markdown]
# # <DB>.<TABLE>
#
# TODO: say in one line what one row of <DB>.<TABLE> is.
#
# A table written a day at a time: each day's rows, worked out from a table it reads.
#
# Made by `project.new_table("<DB>.<TABLE>", template="daily_table")` from
# `admin/templates/daily_table.py`, which filled in the database, the table and its file's name,
# <NAME>. Run the cells top to bottom, once you have filled in two things.
#
# First, this table's Table reference, `references/<NAME>.py`: its `<...>` and TODO lines.
# It lists the columns write() saves, as its SELECT names them: here <KEY_COLUMN>, typed as
# the table read types it, and <COUNT_NAME>, a count, "bigint"; then "dt", the day, the
# partition column. Give it key=[<KEY_COLUMN>, "dt"]: one row per <KEY_COLUMN> and day.
#
# Then every `<...>` left in this notebook: the notebook won't run with one left. They are:
#
#   - `<SOURCE_NAME>` and `<SOURCE_TABLE>`: the table it reads, by its file in
#     references/ and its name there, such as `ops__job_runs` and `job_runs`;
#   - `<DATE_PARTITION>`: that table's partition column holding the day, such as `dt`;
#   - `<KEY_COLUMN>`: the column each row is for, such as `job_id`;
#   - `<COUNT_NAME>`: the name of the count it saves, in quotes, such as `"runs"`;
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
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, between,
    count_rows, create_table, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference
# each table it reads, such as: from references.ops__job_runs import job_runs
from references.<SOURCE_NAME> import <SOURCE_TABLE>

DAY = <DAY>  # the day write() writes: change it to write another


def create() -> Statement:
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows(first_day: str, last_day: str) -> list[Clause]:
    """The clauses every step below shares, so preview, write and backfill can never
    disagree. The day stays in GROUP_BY, so the days stay apart, and comes last in SELECT, as "dt":
    INSERT_OVERWRITE writes each day's rows into that day's partition of this table,
    replacing only the days the rows hold."""
    return [
        SELECT(<SOURCE_TABLE>.<KEY_COLUMN>, AS(count_rows(), <COUNT_NAME>),
               AS(<SOURCE_TABLE>.<DATE_PARTITION>, "dt")),
        FROM(<SOURCE_TABLE>),
        WHERE(between(<SOURCE_TABLE>.<DATE_PARTITION>, first_day, last_day)),
        GROUP_BY(<SOURCE_TABLE>.<DATE_PARTITION>, <SOURCE_TABLE>.<KEY_COLUMN>),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows(DAY, DAY))


def write() -> Statement:
    """Step 3: save DAY's rows, replacing whatever DAY held."""
    return statement(INSERT_OVERWRITE(<TABLE>), *rows(DAY, DAY))


def backfill(first_day: str, last_day: str) -> Statement:
    """Step 4, when needed: save every day from first_day to last_day in one write,
    replacing those days."""
    return statement(INSERT_OVERWRITE(<TABLE>), *rows(first_day, last_day))

# %%
# 3. Try it: the Hive of each step, then the rows
show_hive([create(), write()])
run(preview(), query=query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
