# sqlglot Composer 6.0, exported 2026-10-21 07:05 - copy it, then edit your copy
# %% [markdown]
# # <DB>.<TABLE>
#
# TODO: say in one line what one row of <DB>.<TABLE> is.
#
# An incremental load: each run writes its day and the few days before it again, since rows
# can come in a day or two late, such as a bill for a day already saved. A day written again
# replaces itself, so a run sent twice does no harm.
#
# Made by `project.new_table("<DB>.<TABLE>", template="incremental_load")` from
# `admin/templates/incremental_load.py`, which filled in the database, the table and its file's name,
# <NAME>. Run the cells top to bottom, once you have filled in two things.
#
# First, this table's Table reference, `references/<NAME>.py`: its `<...>` and TODO lines.
# It lists the columns each write saves, as its SELECT names them: here <KEY_COLUMN>, typed as
# the table read types it, and <COUNT_NAME>, a count, "bigint"; then "dt", the day. Its key is
# [<KEY_COLUMN>, "dt"], one row per <KEY_COLUMN> and day.
#
# Then every `<...>` left in this notebook: the notebook won't run with one left. They are:
#
#   - `<SOURCE_NAME>` and `<SOURCE_TABLE>`: the table it reads, by its file in
#     references/ and its name there, such as `ops__job_runs` and `job_runs`;
#   - `<DATE_PARTITION>`: that table's Date partition, its day column, such as `dt`;
#   - `<KEY_COLUMN>`: the column each row is for, such as `job_id`;
#   - `<COUNT_NAME>`: the name of the count it saves, in quotes, such as `"runs"`;
#   - `<DAYS_REWRITTEN>`: how many days each run writes, its own included, such as `3`;
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
import datetime

from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, between, by_day, count_rows,
    create_table, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference
# each table it reads, such as: from references.ops__job_runs import job_runs
from references.<SOURCE_NAME> import <SOURCE_TABLE>

DAYS_REWRITTEN = <DAYS_REWRITTEN>  # each run writes its own day and the days just before it


def first_day_written(day):
    """The first day a run for `day` writes: with 3 days rewritten,
    first_day_written("2026-09-24") is "2026-09-22"."""
    first_day = datetime.date.fromisoformat(day) - datetime.timedelta(days=DAYS_REWRITTEN - 1)
    return first_day.isoformat()


def create():
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows(first_day, last_day):
    """The clauses every step below shares. The day stays in GROUP_BY, so the days stay apart, and out of SELECT: INSERT_OVERWRITE
    writes it as this table's Date partition, the day the table read is bounded to."""
    return [
        SELECT(<SOURCE_TABLE>.<KEY_COLUMN>, AS(count_rows(), <COUNT_NAME>)),
        FROM(<SOURCE_TABLE>),
        WHERE(between(<SOURCE_TABLE>.<DATE_PARTITION>, first_day, last_day)),
        GROUP_BY(<SOURCE_TABLE>.<DATE_PARTITION>, <SOURCE_TABLE>.<KEY_COLUMN>),
    ]


def preview(day):
    """Step 2: the rows a write of the day would save, as a SELECT to run and check first."""
    return statement(*rows(day, day))


def write_days(first_day, last_day):
    """One write per day from first_day to last_day, oldest first: also a backfill, given an
    earlier first_day."""
    return by_day(statement(INSERT_OVERWRITE(<TABLE>), *rows(first_day, last_day)))


def write_day(day):
    """Step 3, every run: the writes of the last DAYS_REWRITTEN days, ending on the day, as a
    list, oldest first. run_tables sends each in turn."""
    return write_days(first_day_written(day), day)

# %%
# 3. Try it: the Hive of each step, then the rows
show_hive([create(), *write_day(DAY)])
run(preview(DAY), send=send)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(*write_day(DAY))

# %%
# 5. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
