"""The Templates project.start() copies into a Project's admin/templates/, each as its text.

A Template is a file with placeholders written <LIKE_THIS>. project.new_table fills in <DB>,
<TABLE> and <NAME> (the database, the table, and the two joined by two underscores, such as
mart__daily_job_runs); every other placeholder is yours to fill in, and Python stops at the
first one left in, so a half-filled file can't run.

A Table notebook's Template is a .py file whose cells start with a "# %%" line, or
"# %% [markdown]" for a text cell, whose lines each start with "# ". Every one has the same
five code cells: 1 the Project and your query, 2 the logic, 3 try it, 4 its lineage, 5 its rows
in the Reference sheet; they differ in the logic. The copies in admin/templates/ are yours:
edit one, or add your own beside them, and the next project.new_table(...) uses it. Editing a
Template changes only the notebooks made after.
"""

from __future__ import annotations

TOOLBOX_VERSION = "7.0"


def _notebook(name: str, about: str, saves: str, fill_in: str, logic: str, try_it: str,
              lineage: str = "export_lineage(write_day(DAY))") -> str:
    """A Table notebook's Template: its text cell, then its five code cells, the logic and the
    try-it cell its own, the others the same in every Template. `saves` says what the table's
    Table reference lists, `fill_in` each placeholder of the notebook with an example."""
    return f'''# %% [markdown]
# # <DB>.<TABLE>
#
# TODO: say in one line what one row of <DB>.<TABLE> is.
#
{about}
#
# Made by `project.new_table("<DB>.<TABLE>", template="{name}")` from
# `admin/templates/{name}.py`, which filled in the database, the table and its file's name,
# <NAME>. Run the cells top to bottom, once you have filled in two things.
#
# First, this table's Table reference, `references/<NAME>.py`: its `<...>` and TODO lines.
{saves}
#
# Then every `<...>` left in this notebook: the notebook won't run with one left. They are:
#
{fill_in}
#
# The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet. The logic only imports and defines, so
# `project.load("<DB>.<TABLE>")` can run it from anywhere else, for lineage across your
# tables and for `admin/run_tables.ipynb`.

# %%
# 1. The Project, your query, and a day to try things on
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_lineage, project, run, show_hive
from warehouse import query

DAY = <DAY>  # a day to try the cells on, in quotes, such as "2026-09-24"

# %%
{logic}
# %%
# 3. Try it: the Hive of each step, then the rows
{try_it}

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
{lineage}

# %%
# 5. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
'''


# The placeholders of the table a Template reads, which every one but quality_checks has.
_SOURCE_FILL_IN = '''\
#   - `<SOURCE_NAME>` and `<SOURCE_TABLE>`: the table it reads, by its file in
#     references/ and its name there, such as `ops__job_runs` and `job_runs`;
#   - `<DATE_PARTITION>`: that table's Date partition, its day column, such as `dt`;'''
_DAY_FILL_IN = '''\
#   - `<DAY>`: a day the table it reads has, in quotes, such as `"2026-09-24"`.'''
# Why a write's rows never select the day, which every Template's rows() says.
_NO_DAY = '''\
The day stays in GROUP_BY, so the days stay apart, and out of SELECT: INSERT_OVERWRITE
    writes it as this table's Date partition, the day the table read is bounded to.'''

DAILY_TABLE = _notebook(
    "daily_table",
    about='''\
# A table written a day at a time: each day's rows, worked out from a table it reads.''',
    saves='''\
# It lists the columns write_day saves, as its SELECT names them: here <KEY_COLUMN>, typed as
# the table read types it, and <COUNT_NAME>, a count, "bigint"; then "dt", the day. Its key is
# [<KEY_COLUMN>, "dt"], one row per <KEY_COLUMN> and day.''',
    fill_in=_SOURCE_FILL_IN + '''
#   - `<KEY_COLUMN>`: the column each row is for, such as `job_id`;
#   - `<COUNT_NAME>`: the name of the count it saves, in quotes, such as `"runs"`;
''' + _DAY_FILL_IN,
    logic=f'''# logic
# 2. The logic: imports and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, between,
    by_day, count_rows, create_table, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference
# each table it reads, such as: from references.ops__job_runs import job_runs
from references.<SOURCE_NAME> import <SOURCE_TABLE>


def create() -> Statement:
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows(first_day: str, last_day: str) -> list[Clause]:
    """The clauses every step below shares, so preview, write_day and backfill can never
    disagree. {_NO_DAY}"""
    return [
        SELECT(<SOURCE_TABLE>.<KEY_COLUMN>, AS(count_rows(), <COUNT_NAME>)),
        FROM(<SOURCE_TABLE>),
        WHERE(between(<SOURCE_TABLE>.<DATE_PARTITION>, first_day, last_day)),
        GROUP_BY(<SOURCE_TABLE>.<DATE_PARTITION>, <SOURCE_TABLE>.<KEY_COLUMN>),
    ]


def preview(day: str) -> Statement:
    """Step 2: the rows write_day(day) would save, as a SELECT to run and check first."""
    return statement(*rows(day, day))


def write_day(day: str) -> Statement:
    """Step 3, every day: save the day's rows, replacing whatever the day held."""
    return statement(INSERT_OVERWRITE(<TABLE>), *rows(day, day))


def backfill(first_day: str, last_day: str) -> list[Statement]:
    """Step 4, when needed: one write per day from first_day to last_day, oldest first."""
    return by_day(statement(INSERT_OVERWRITE(<TABLE>), *rows(first_day, last_day)))
''',
    try_it='''show_hive([create(), write_day(DAY)])
run(preview(DAY), query=query)''',
)

INCREMENTAL_LOAD = _notebook(
    "incremental_load",
    about='''\
# An incremental load: each run writes its day and the few days before it again, since rows
# can come in a day or two late, such as a bill for a day already saved. A day written again
# replaces itself, so a run sent twice does no harm.''',
    saves='''\
# It lists the columns each write saves, as its SELECT names them: here <KEY_COLUMN>, typed as
# the table read types it, and <COUNT_NAME>, a count, "bigint"; then "dt", the day. Its key is
# [<KEY_COLUMN>, "dt"], one row per <KEY_COLUMN> and day.''',
    fill_in=_SOURCE_FILL_IN + '''
#   - `<KEY_COLUMN>`: the column each row is for, such as `job_id`;
#   - `<COUNT_NAME>`: the name of the count it saves, in quotes, such as `"runs"`;
#   - `<DAYS_REWRITTEN>`: how many days each run writes, its own included, such as `3`;
''' + _DAY_FILL_IN,
    logic=f'''# logic
# 2. The logic: imports and functions only
import datetime

from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, between,
    by_day, count_rows, create_table, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference
# each table it reads, such as: from references.ops__job_runs import job_runs
from references.<SOURCE_NAME> import <SOURCE_TABLE>

DAYS_REWRITTEN = <DAYS_REWRITTEN>  # each run writes its own day and the days just before it


def first_day_written(day: str) -> str:
    """The first day a run for `day` writes: with 3 days rewritten,
    first_day_written("2026-09-24") is "2026-09-22"."""
    first_day = datetime.date.fromisoformat(day) - datetime.timedelta(days=DAYS_REWRITTEN - 1)
    return first_day.isoformat()


def create() -> Statement:
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows(first_day: str, last_day: str) -> list[Clause]:
    """The clauses every step below shares. {_NO_DAY}"""
    return [
        SELECT(<SOURCE_TABLE>.<KEY_COLUMN>, AS(count_rows(), <COUNT_NAME>)),
        FROM(<SOURCE_TABLE>),
        WHERE(between(<SOURCE_TABLE>.<DATE_PARTITION>, first_day, last_day)),
        GROUP_BY(<SOURCE_TABLE>.<DATE_PARTITION>, <SOURCE_TABLE>.<KEY_COLUMN>),
    ]


def preview(day: str) -> Statement:
    """Step 2: the rows a write of the day would save, as a SELECT to run and check first."""
    return statement(*rows(day, day))


def write_days(first_day: str, last_day: str) -> list[Statement]:
    """One write per day from first_day to last_day, oldest first: also a backfill, given an
    earlier first_day."""
    return by_day(statement(INSERT_OVERWRITE(<TABLE>), *rows(first_day, last_day)))


def write_day(day: str) -> list[Statement]:
    """Step 3, every run: the writes of the last DAYS_REWRITTEN days, ending on the day, as a
    list, oldest first. run_tables sends each in turn."""
    return write_days(first_day_written(day), day)
''',
    try_it='''show_hive([create(), *write_day(DAY)])
run(preview(DAY), query=query)''',
    lineage="export_lineage(*write_day(DAY))",
)

WEEKLY_ROLLUP = _notebook(
    "weekly_rollup",
    about='''\
# A table written a day at a time and read a week at a time: each day's totals are saved,
# and week_totals adds the saved days up into weeks. A write fills one day, so the table holds
# days, not weeks. Only numbers that add up, such as counts and sums, can be added up into
# weeks; a count of different values can't.''',
    saves='''\
# It lists the columns write_day saves, as its SELECT names them: here <GROUP_COLUMN>, typed as
# the table read types it, and <TOTAL>, a sum: "bigint" for whole numbers, "double" for
# others; then "dt", the day. Its key is [<GROUP_COLUMN>, "dt"].''',
    fill_in=_SOURCE_FILL_IN + '''
#   - `<GROUP_COLUMN>`: the column each row is for, such as `job_id`;
#   - `<NUMBER_COLUMN>`: the column of numbers to add up, such as `duration_mins`;
#   - `<TOTAL>` and `<TOTAL_NAME>`: one name for the total, twice: without quotes,
#     `<TOTAL>` reads the saved column back in week_totals, such as `minutes`; in quotes,
#     `<TOTAL_NAME>` names it as write_day saves it, such as `"minutes"`;
''' + _DAY_FILL_IN,
    logic=f'''# logic
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
    """The day's totals per group: the clauses preview and write_day share. {_NO_DAY}"""
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
''',
    try_it='''show_hive([create(), write_day(DAY), week_totals(DAY, DAY)])
run(preview(DAY), query=query)''',
)

AS_OF_LOOKUP = _notebook(
    "as_of_lookup",
    about='''\
# A table that looks each row up as of its own day: each day's rows, counted per value a
# snapshot table held for them on that day, such as the team that owned each job then.''',
    saves='''\
# It lists the columns write_day saves, as its SELECT names them: here <LOOKED_UP_COLUMN>,
# typed as the snapshot types it, and "row_count", a count, "bigint"; then "dt", the day. Its
# key is [<LOOKED_UP_COLUMN>, "dt"].
#
# The snapshot's own Table reference must declare its Key too, such as key=["job_id", "dt"]:
# its key column and its day, so that each row matches one snapshot row. Without it, the join
# warns that a row may match several.''',
    fill_in=_SOURCE_FILL_IN + '''
#   - `<MATCH_COLUMN>`: its column holding the key looked up, such as `job_id`;
#   - `<SNAPSHOT_NAME>` and `<SNAPSHOT>`: the snapshot table, one row per key per day, by its
#     file in references/ and its name there, such as `ops__job_owners` and `job_owners`;
#   - `<SNAPSHOT_MATCH_COLUMN>`, `<SNAPSHOT_DATE_PARTITION>` and `<LOOKED_UP_COLUMN>`: its
#     key column, its day column, and the column looked up, such as `job_id`, `dt` and `team`;
#   - `<DAY>`: a day both tables have, in quotes, such as `"2026-09-24"`.''',
    logic=f'''# logic
# 2. The logic: imports and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, LEFT_JOIN, SELECT, WHERE, Clause, Statement,
    all_of, between, count_rows, create_table, equals, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference
# the rows looked up for, such as: from references.ops__job_runs import job_runs
from references.<SOURCE_NAME> import <SOURCE_TABLE>
# the snapshot, such as: from references.ops__job_owners import job_owners
from references.<SNAPSHOT_NAME> import <SNAPSHOT>


def create() -> Statement:
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows(day: str) -> list[Clause]:
    """The day's rows per value looked up as of the day: the clauses preview and write_day
    share. A row with no snapshot that day is counted under NULL. {_NO_DAY}"""
    return [
        SELECT(<SNAPSHOT>.<LOOKED_UP_COLUMN>, AS(count_rows(), "row_count")),
        FROM(<SOURCE_TABLE>),
        # The snapshot's day goes in ON=, not WHERE: a WHERE on it would drop the rows LEFT_JOIN
        # keeps for having no snapshot. Matching the days alone doesn't bound the snapshot's
        # days, which every read must, so between(...) bounds them too.
        LEFT_JOIN(<SNAPSHOT>, ON=all_of(  # all_of: every condition in it must hold
            equals(<SNAPSHOT>.<SNAPSHOT_MATCH_COLUMN>, <SOURCE_TABLE>.<MATCH_COLUMN>),
            equals(<SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>, <SOURCE_TABLE>.<DATE_PARTITION>),
            between(<SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>, day, day),
        )),
        WHERE(between(<SOURCE_TABLE>.<DATE_PARTITION>, day, day)),
        GROUP_BY(<SOURCE_TABLE>.<DATE_PARTITION>, <SNAPSHOT>.<LOOKED_UP_COLUMN>),
    ]


def preview(day: str) -> Statement:
    """Step 2: the rows write_day(day) would save, as a SELECT to run and check first."""
    return statement(*rows(day))


def write_day(day: str) -> Statement:
    """Step 3, every day: save the day's rows, replacing whatever the day held."""
    return statement(INSERT_OVERWRITE(<TABLE>), *rows(day))
''',
    try_it='''show_hive([create(), write_day(DAY)])
run(preview(DAY), query=query)''',
)

QUALITY_CHECKS = _notebook(
    "quality_checks",
    about='''\
# Quality checks on a table you read. Each day, its row count is saved, so you can read the
# days side by side and see one that looks too small; and checks run on any days you ask:
# repeated_keys looks for a key with more than one row, and null_counts counts NULLs.''',
    saves='''\
# It lists one column, "row_count", a count, "bigint"; then "dt", the day. Its key is ["dt"],
# one row per day.''',
    fill_in='''\
#   - `<CHECKED_NAME>` and `<CHECKED>`: the table checked, by its file in references/ and
#     its name there, such as `ops__job_events` and `job_events`;
#   - `<DATE_PARTITION>`: its Date partition, its day column, such as `dt`;
#   - `<KEY_COLUMN>`: the column that picks out one row, such as `event_id`;
''' + _DAY_FILL_IN,
    logic=f'''# logic
# 2. The logic: imports and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, HAVING, INSERT_OVERWRITE, SELECT, WHERE, Clause, Column,
    Statement, all_columns, between, count_rows, create_table, is_null, more_than, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference, of row counts
# the table checked, such as: from references.ops__job_events import job_events
from references.<CHECKED_NAME> import <CHECKED>


def create() -> Statement:
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows(day: str) -> list[Clause]:
    """The day's row count: the clauses preview and write_day share. {_NO_DAY}"""
    return [
        SELECT(AS(count_rows(), "row_count")),
        FROM(<CHECKED>),
        WHERE(between(<CHECKED>.<DATE_PARTITION>, day, day)),
        GROUP_BY(<CHECKED>.<DATE_PARTITION>),
    ]


def preview(day: str) -> Statement:
    """Step 2: the row write_day(day) would save, as a SELECT to run and check first."""
    return statement(*rows(day))


def write_day(day: str) -> Statement:
    """Step 3, every day: save the day's row count, replacing whatever the day held."""
    return statement(INSERT_OVERWRITE(<TABLE>), *rows(day))


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
    counts = [AS(count_rows(where=is_null(column)), f"null_{{column_name(column)}}")
              for column in all_columns(<CHECKED>)]
    return statement(
        SELECT(*counts),
        FROM(<CHECKED>),
        WHERE(between(<CHECKED>.<DATE_PARTITION>, first_day, last_day)),
    )
''',
    try_it='''show_hive([create(), write_day(DAY)])
run(preview(DAY), query=query)
run(repeated_keys(DAY, DAY), query=query)  # should have no rows
run(null_counts(DAY, DAY), query=query)''',
)

SAVED_TABLE_REFERENCE = '''"""<DB>.<TABLE> - TODO: say in one line what one row is.

Why: TODO: who reads this table, and why it is saved rather than worked out each time.

project.new_table wrote this file from admin/templates/saved_table_reference.py. A Saved
table's Table reference is filled in by hand, since the table doesn't exist until its
notebook's create() makes it from this file. Its notebook's text cell says which columns it
lists.
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

BUILDING_BLOCK = '''"""<BLOCK> - TODO: say in one line what one row of it is.

Why: TODO: which tables' notebooks read it, so they can never work it out two ways.

Copied by hand from admin/templates/building_block.py into building_blocks/<BLOCK>.py. A
Building block is a piece several notebooks share; this one is a Derived table, a Statement
given a name, which each Statement reading it writes at its top, as WITH <BLOCK> AS (...). In a
notebook's logic cell, import it and read it like a table:

    from building_blocks.<BLOCK> import <BLOCK>


    def preview(day: str) -> Statement:
        per_group = <BLOCK>(day, day)
        return statement(SELECT(per_group.<GROUP_COLUMN>, per_group.row_count),
                         FROM(per_group))

Fill in every <...>:
    <BLOCK> and <BLOCK_NAME>: its name, as a name and in quotes, such as minutes_per_job_day
        and "minutes_per_job_day".
    <SOURCE_NAME> and <SOURCE_TABLE>: the table it reads, by its file in references/ and its
        name there, such as ops__job_runs and job_runs.
    <GROUP_COLUMN>: the column each row is for, such as job_id.
    <DATE_PARTITION>: the table's Date partition, its day column, such as dt.
    <NUMBER_COLUMN>: a column of numbers to add up, such as duration_mins.
    <TOTAL_NAME>: the name of what it adds up to, in quotes, such as "minutes".
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, Table, between, count_rows, derived, statement,
    sum_of,
)
from references.<SOURCE_NAME> import <SOURCE_TABLE>  # the Table reference it reads


def <BLOCK>(first_day: str, last_day: str) -> Table:  # named as its file is
    """One row per group and day from first_day to last_day: its rows, and its total."""
    return derived(
        <BLOCK_NAME>,  # the name the Hive gives it
        statement(
            SELECT(
                <SOURCE_TABLE>.<GROUP_COLUMN>,  # what each row is for
                <SOURCE_TABLE>.<DATE_PARTITION>,  # the day, kept so that each day stays apart
                AS(count_rows(), "row_count"),
                # add a line like the next for each number to add up
                AS(sum_of(<SOURCE_TABLE>.<NUMBER_COLUMN>), <TOTAL_NAME>),
            ),
            FROM(<SOURCE_TABLE>),
            WHERE(between(<SOURCE_TABLE>.<DATE_PARTITION>, first_day, last_day)),
            GROUP_BY(<SOURCE_TABLE>.<GROUP_COLUMN>, <SOURCE_TABLE>.<DATE_PARTITION>),
        ),
    )
'''

# Each Template by its name, as start() writes it into admin/templates/<name>.py. The Table
# notebook Templates are the ones new_table's template= takes.
NOTEBOOK_TEMPLATES = {
    "daily_table": DAILY_TABLE,
    "incremental_load": INCREMENTAL_LOAD,
    "weekly_rollup": WEEKLY_ROLLUP,
    "as_of_lookup": AS_OF_LOOKUP,
    "quality_checks": QUALITY_CHECKS,
}
TEMPLATES = {
    **NOTEBOOK_TEMPLATES,
    "saved_table_reference": SAVED_TABLE_REFERENCE,
    "building_block": BUILDING_BLOCK,
}
