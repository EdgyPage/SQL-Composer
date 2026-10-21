# %% [markdown]
# # <DB>.<TABLE>
#
# TODO: say in one line what one row of <DB>.<TABLE> is.
#
# A table written a day at a time and read a week at a time: each day's totals are saved,
# and week_totals adds the saved days up into weeks. A write fills one day, so the table holds
# days, not weeks. Only numbers that add up, such as counts and sums, can be added up into
# weeks; a count of different values can't.
#
# Made by `project.new_table("<DB>.<TABLE>", template="weekly_rollup")` from
# `admin/templates/weekly_rollup.py`, which filled in the database, the table and its file's name,
# <NAME>. Run the cells top to bottom, once you have filled in two things.
#
# First, this table's Table reference, `references/<NAME>.py`: its `<...>` and TODO lines.
# It lists the columns write_day saves, as its SELECT names them: here <GROUP_COLUMN>, typed as
# the table read types it, and <TOTAL>, a sum: "bigint" for whole numbers, "double" for
# others; then "dt", the day. Its key is [<GROUP_COLUMN>, "dt"].
#
# Then every `<...>` left in this notebook: the notebook won't run with one left. They are:
#
#   - `<SOURCE_NAME>` and `<SOURCE_TABLE>`: the table it reads, by its file in
#     references/ and its name there, such as `ops__job_runs` and `job_runs`;
#   - `<DATE_PARTITION>`: that table's Date partition, its day column, such as `dt`;
#   - `<GROUP_COLUMN>`: the column each row is for, such as `job_id`;
#   - `<NUMBER_COLUMN>`: the column of numbers to add up, such as `duration_mins`;
#   - `<TOTAL>` and `<TOTAL_NAME>`: one name for the total, twice: without quotes,
#     `<TOTAL>` reads the saved column back in week_totals, such as `minutes`; in quotes,
#     `<TOTAL_NAME>` names it as write_day saves it, such as `"minutes"`;
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
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, between,
    create_table, statement, sum_of, week_start,
)
from references.<NAME> import <TABLE>  # this table's own Table reference
# each table it reads, such as: from references.ops__job_runs import job_runs
from references.<SOURCE_NAME> import <SOURCE_TABLE>


def create() -> Statement:
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows(day: str) -> list[Clause]:
    """The day's totals per group: the clauses preview and write_day share. The day stays in GROUP_BY, so the days stay apart, and out of SELECT: INSERT_OVERWRITE
    writes it as this table's Date partition, the day the table read is bounded to."""
    return [
        SELECT(<SOURCE_TABLE>.<GROUP_COLUMN>,
               AS(sum_of(<SOURCE_TABLE>.<NUMBER_COLUMN>), <TOTAL_NAME>)),
        FROM(<SOURCE_TABLE>),
        WHERE(between(<SOURCE_TABLE>.<DATE_PARTITION>, day, day)),
        GROUP_BY(<SOURCE_TABLE>.<DATE_PARTITION>, <SOURCE_TABLE>.<GROUP_COLUMN>),
    ]


def preview(day: str) -> Statement:
    """Step 2: the rows write_day(day) would save, as a SELECT to run and check first."""
    return statement(*rows(day))


def write_day(day: str) -> Statement:
    """Step 3, every day: save the day's totals, replacing whatever the day held."""
    return statement(INSERT_OVERWRITE(<TABLE>), *rows(day))


def week_totals(first_day: str, last_day: str) -> Statement:
    """Each group's totals per week, read from the days this table saved, first_day to
    last_day: the week is the Monday it starts on. dt is this table's Date partition, as its
    Table reference names it."""
    return statement(
        SELECT(AS(week_start(<TABLE>.dt), "week"), <TABLE>.<GROUP_COLUMN>,
               AS(sum_of(<TABLE>.<TOTAL>), <TOTAL_NAME>)),
        FROM(<TABLE>),
        WHERE(between(<TABLE>.dt, first_day, last_day)),
        # GROUP_BY takes the SELECT's name for the week, "week"; the Hive writes the
        # week_start(...) calculation out again there, as Hive needs it
        GROUP_BY("week", <TABLE>.<GROUP_COLUMN>),
    )

# %%
# 3. Try it: the Hive of each step, then the rows
show_hive([create(), write_day(DAY), week_totals(DAY, DAY)])
run(preview(DAY), send=send)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write_day(DAY))

# %%
# 5. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
