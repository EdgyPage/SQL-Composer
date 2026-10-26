"""The Templates project.start() copies into a Project's admin/templates/, each as its text.

A Template is a file with placeholders written <LIKE_THIS>. project.new_table fills in <DB>,
<TABLE> and <NAME> (the database, the table, and the two joined by two underscores, such as
mart__daily_job_runs), and project.new_block fills in <BLOCK>, the Building block's name, such
as runs_per_job; every other placeholder is yours to fill in, and Python stops at the
first one left in, so a half-filled file can't run. Each Template's first lines list its
placeholders, with an example of each.

A Table notebook's Template is a .py file whose cells start with a "# %%" line, or
"# %% [markdown]" for a text cell, whose lines each start with "# ". Every one has the same
five code cells: 1 the Project and your query, 2 the logic, 3 try it, 4 its lineage, 5 its rows
in the Reference sheet; they differ in the logic, which defines write(), the function that
writes the table. The copies in admin/templates/ are yours: edit one, or add your own beside
them, and the next project.new_table(...) uses it. Editing a Template changes only the
notebooks made after.
"""

from __future__ import annotations


def _notebook(name: str, about: str, saves: str, fill_in: str, logic: str, try_it: str
              ) -> str:
    """A Table notebook's Template: its text cell, then its five code cells, the logic and the
    try-it cell its own, the others the same in every Template. `fill_in` lists each
    placeholder of the notebook with an example, first; `saves` says what the table's Table
    reference lists."""
    # The call that made the notebook: new_table's own Template needs no template=.
    call = ('"<DB>.<TABLE>"' if name == "saved_table"
            else f'"<DB>.<TABLE>", template="{name}"')
    return f'''# %% [markdown]
# # <DB>.<TABLE>
#
# Fill in every `<...>` in the code cells below, brackets and all: the notebook won't run with
# one left. They are:
{fill_in}
#
# Then fill in this table's Table reference, `references/<NAME>.py`: its `<...>` and TODO
# lines.
{saves}
#
# TODO: say in one line what one row of <DB>.<TABLE> is.
#
{about}
#
# Made by `project.new_table({call})` from
# `admin/templates/{name}.py`, which filled in the database, the table and its file's name,
# <NAME>. Run the cells top to bottom once both are filled in.
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

from sqlglot_composer import export_lineage, project, run_query, show_hive
from warehouse import query

# %%
{logic}
# %%
# 3. Try it: the Hive of each step, then the rows
{try_it}

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
'''


# What every Table notebook Template says of READS, the rows its write() reads.
_READS_FILL_IN = '''\
#   - `<READS>`: which of its rows write() reads, as a condition on it, such as
#     `equals(job_runs.dt, "2026-09-24")` or `equals(region_costs.region, "eu")`. On a
#     partitioned table, it must filter one of its partition columns. A table that isn't
#     partitioned can be read whole: delete the line `READS = <READS>` and each line
#     `WHERE(READS),` instead;'''
# What every Table notebook Template says of a partition column it writes, or doesn't.
_PARTITION_FILL_IN = '''\
#   - `<PARTITION_COLUMN>`: the column of the table it reads that fills this table's partition
#     column, such as `dt` or `region`. If this table isn't partitioned, delete the two lines
#     naming `<PARTITION_COLUMN>` instead.'''
# The comment above READS in every logic cell.
_READS_COMMENT = '''\
# The rows write() reads: change it to write others. A condition that calls something other
# than equals, such as between or is_in, needs it added to the import above.'''
# What quality_checks says of READS and of the partition column, and above READS: the same,
# for the rows it checks. Written out in full, so a rewording of one can't miss the other.
_CHECKED_READS_FILL_IN = '''#   - `<READS>`: which of its rows are checked, as a condition on it, such as
#     `equals(job_runs.dt, "2026-09-24")` or `equals(region_costs.region, "eu")`. On a
#     partitioned table, it must filter one of its partition columns. A table that isn't
#     partitioned can be read whole: delete the line `READS = <READS>` and each line
#     `WHERE(READS),` instead;'''
_CHECKED_PARTITION_FILL_IN = '''#   - `<PARTITION_COLUMN>`: the column of the table checked that fills this table's partition
#     column, such as `dt` or `region`. If this table isn't partitioned, delete the two lines
#     naming `<PARTITION_COLUMN>` instead.'''
_CHECKED_READS_COMMENT = '''# The rows checked: change it to check others. A condition that calls something other
# than equals, such as between or is_in, needs it added to the import above.'''

SAVED_TABLE = _notebook(
    "saved_table",
    about='''\
# A Saved table worked out from a table it reads: a count per group of the rows READS picks.
# It is partitioned however its Table reference says, or not at all.''',
    saves='''\
# It lists the columns write() saves, in the order its SELECT gives them: here
# <GROUP_COLUMN>, typed as the table read types it, then <COUNT_NAME>, a count, "bigint", and
# last its partition column, if it has one, also named in partitioned_by=[...]. Its Key is
# the column each row is for, and the partition column if it has one, such as
# key=["job_id", "region"].''',
    fill_in='''\
#   - `<SOURCE_NAME>` and `<SOURCE_TABLE>`: the table it reads, by its file in references/ and
#     its name there, such as `ops__job_runs` and `job_runs`;
''' + _READS_FILL_IN + '''
#   - `<GROUP_COLUMN>`: the column each row is for, such as `job_id`;
#   - `<COUNT_NAME>`: the name of the count it saves, in quotes, such as `"runs"`;
''' + _PARTITION_FILL_IN,
    logic=f'''# logic
# 2. The logic: imports, the rows it reads, and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, count_rows,
    create_table, equals, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference
# each table it reads, such as: from references.ops__job_runs import job_runs
from references.<SOURCE_NAME> import <SOURCE_TABLE>

{_READS_COMMENT}
READS = <READS>


def create() -> Statement:
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows() -> list[Clause]:
    """The clauses preview and write share, so the two can never disagree: a count per group
    of the rows READS picks.

    A partitioned table's partition columns come last in SELECT, in its Table reference's
    order, named as it names them: INSERT_OVERWRITE fills each Partition from the rows' own
    values, and replaces only the Partitions they fill. They stay in GROUP_BY too, so each
    Partition's rows stay apart.
    """
    return [
        SELECT(
            <SOURCE_TABLE>.<GROUP_COLUMN>,  # what each row is for
            AS(count_rows(), <COUNT_NAME>),
            <SOURCE_TABLE>.<PARTITION_COLUMN>,  # this table's partition column, last
        ),
        FROM(<SOURCE_TABLE>),
        WHERE(READS),
        GROUP_BY(
            <SOURCE_TABLE>.<GROUP_COLUMN>,
            <SOURCE_TABLE>.<PARTITION_COLUMN>,  # kept, so each Partition's rows stay apart
        ),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows())


def write() -> Statement:
    """Step 3: save the rows, replacing the Partitions they fill, or the whole table if it
    isn't partitioned: sent twice, it leaves the same rows, not twice as many."""
    return statement(INSERT_OVERWRITE(<TABLE>), *rows())
''',
    try_it='''show_hive([create(), write()])
run_query(preview(), query)''',
)

QUALITY_CHECKS = _notebook(
    "quality_checks",
    about='''\
# Quality checks on a table you read. The row count of each of its Partitions READS picks is
# saved, so you can read them side by side and see one that looks too small; and checks run on
# the same rows: repeated_keys looks for a key with more than one row, and null_counts counts
# NULLs.''',
    saves='''\
# It lists one column, "row_count", a count, "bigint", then the partition column counted,
# typed as the table checked types it, also named in partitioned_by=[...]. Give it that
# partition column as its Key: one row per Partition counted.''',
    fill_in='''\
#   - `<CHECKED_NAME>` and `<CHECKED>`: the table checked, by its file in references/ and
#     its name there, such as `ops__job_events` and `job_events`;
''' + _CHECKED_READS_FILL_IN + '''
#   - `<KEY_COLUMN>`: the column that picks out one row, such as `event_id`;
''' + _CHECKED_PARTITION_FILL_IN,
    logic=f'''# logic
# 2. The logic: imports, the rows it checks, and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, HAVING, INSERT_OVERWRITE, SELECT, WHERE, Clause, Column,
    Statement, all_columns, count_rows, create_table, equals, is_null, more_than, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference, of row counts
# the table checked, such as: from references.ops__job_events import job_events
from references.<CHECKED_NAME> import <CHECKED>

{_CHECKED_READS_COMMENT}
READS = <READS>


def create() -> Statement:
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows() -> list[Clause]:
    """The row count of each Partition READS picks: the clauses preview and write share. The
    partition column comes last in SELECT, so INSERT_OVERWRITE writes each count into the
    Partition of the same value, replacing only those."""
    return [
        SELECT(
            AS(count_rows(), "row_count"),
            <CHECKED>.<PARTITION_COLUMN>,  # the Partition counted: this table's partition column
        ),
        FROM(<CHECKED>),
        WHERE(READS),
        GROUP_BY(<CHECKED>.<PARTITION_COLUMN>),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows())


def write() -> Statement:
    """Step 3: save the row counts, replacing the Partitions they fill."""
    return statement(INSERT_OVERWRITE(<TABLE>), *rows())


def repeated_keys() -> Statement:
    """Each key that picks out more than one of the rows READS picks: it should find no
    rows."""
    return statement(
        SELECT(<CHECKED>.<KEY_COLUMN>, AS(count_rows(), "times_seen")),
        FROM(<CHECKED>),
        WHERE(READS),
        GROUP_BY(<CHECKED>.<KEY_COLUMN>),
        HAVING(more_than(count_rows(), 1)),  # tested once the rows of each key are counted
    )


def column_name(column: Column) -> str:
    """A column's own name: a column prints as its table and its name, such as
    job_events.minutes, and this keeps the part after the dot."""
    return str(column).split(".")[-1]


def null_counts() -> Statement:
    """How many of the rows READS picks hold NULL in each column, as one row: null_minutes
    counts the rows whose minutes is NULL, and so on."""
    counts = [AS(count_rows(where=is_null(column)), f"null_{{column_name(column)}}")
              for column in all_columns(<CHECKED>)]
    return statement(
        SELECT(*counts),
        FROM(<CHECKED>),
        WHERE(READS),
    )
''',
    try_it='''show_hive([create(), write()])
run_query(preview(), query)
run_query(repeated_keys(), query)  # should have no rows
run_query(null_counts(), query)''',
)

SAVED_TABLE_REFERENCE = '''"""<DB>.<TABLE> - TODO: say in one line what one row is.

Fill in every <...> below, brackets and all: Python stops at one left in. They are:
    <COLUMN> and <COLUMN_TYPE>: a column write() saves and its Hive type, each in quotes,
        such as "job_id" and "bigint". Copy the line for each column, in the order write()
        saves them, its partition columns last.
    <LOCATION>: the table's own folder, in quotes, such as "/data/your_team/<DB>.db/<TABLE>".
Then partitioned_by= and key=, and the TODO lines.

Why: TODO: who reads this table, and why it is saved rather than worked out each time.

project.new_table wrote this file from admin/templates/saved_table_reference.py. A Saved
table's Table reference is filled in by hand, since the table doesn't exist until its
notebook's create() makes it from this file. Its notebook's text cell says which columns it
lists, and its Key.
"""

from sqlglot_composer import Table

<TABLE> = Table(
    "<DB>.<TABLE>",
    columns={
        <COLUMN>: <COLUMN_TYPE>,  # a line per column write() saves, its partition columns last
    },
    partitioned_by=[],  # its partition columns, in order, such as ["region"]: [] for none
    key=None,  # the columns whose values name one row, such as ["job_id"]: None if none do
    location=<LOCATION>,  # its own folder, in quotes
    descriptions={},  # optional: {"column": "what it holds"}, for the Reference sheet
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.<NAME> import <TABLE>, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = <TABLE>.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(<TABLE>.<column>, <value>)
'''

BUILDING_BLOCK = '''"""<BLOCK> - TODO: say in one line what one row of it is.

Fill in every <...> in the code below this text, brackets and all: Python stops at one left
in. They are:
    <SOURCE_NAME> and <SOURCE_TABLE>: the table it reads, by its file in references/ and its
        name there, such as ops__job_runs and job_runs.
    <GROUP_COLUMN>: the column each row is for, such as job_id.
    <NUMBER_COLUMN>: a column of numbers to add up, such as duration_mins.
    <TOTAL_NAME>: the name of what it adds up to, in quotes, such as "minutes".

Why: TODO: which tables' notebooks read it, so they can never work it out two ways.

project.new_block("<BLOCK>") wrote this file from admin/templates/building_block.py. A
Building block is a piece several notebooks share; this one is a Derived table, a Statement
given a name, which each Statement reading it writes at its top, as WITH <BLOCK> AS (...). In a
notebook's logic cell, import it, and read it like a table, given the rows it reads, such
as READS, the condition at the top of a saved_table notebook's logic cell:

    from building_blocks.<BLOCK> import <BLOCK>


    def preview() -> Statement:
        per_group = <BLOCK>(READS)
        return statement(SELECT(per_group.<GROUP_COLUMN>, per_group.row_count),
                         FROM(per_group))
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, Condition, Table, count_rows, derived, statement,
    sum_of,
)
from references.<SOURCE_NAME> import <SOURCE_TABLE>  # the Table reference it reads


def <BLOCK>(reads: Condition) -> Table:  # named as its file is
    """One row per group of the rows `reads` picks: its rows, and its total.

    `reads` is a condition on the table it reads, such as equals(job_runs.dt, "2026-09-24").
    On a partitioned table, it must filter one of its partition columns.
    """
    return derived(
        "<BLOCK>",  # the name the Hive gives it, the same as its file's
        statement(
            SELECT(
                <SOURCE_TABLE>.<GROUP_COLUMN>,  # what each row is for
                # to keep each Partition's rows apart, add its partition column here and in
                # GROUP_BY, such as job_runs.dt
                AS(count_rows(), "row_count"),
                # add a line like the next for each number to add up
                AS(sum_of(<SOURCE_TABLE>.<NUMBER_COLUMN>), <TOTAL_NAME>),
            ),
            FROM(<SOURCE_TABLE>),
            WHERE(reads),
            GROUP_BY(<SOURCE_TABLE>.<GROUP_COLUMN>),
        ),
    )
'''

# Each Template by its name, as start() writes it into admin/templates/<name>.py. The Table
# notebook Templates are the ones new_table's template= takes; new_block makes a Building
# block from building_block.
NOTEBOOK_TEMPLATES = {
    "saved_table": SAVED_TABLE,
    "quality_checks": QUALITY_CHECKS,
}
TEMPLATES = {
    **NOTEBOOK_TEMPLATES,
    "saved_table_reference": SAVED_TABLE_REFERENCE,
    "building_block": BUILDING_BLOCK,
}
