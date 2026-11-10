"""The Templates project.start() copies into a Project's admin/templates/, each as its text.

A Template is a file with placeholders written <LIKE_THIS>. project.new_table fills in <DB>,
<TABLE> and <NAME> (the database, the table, and the two joined by two underscores, such as
mart__daily_job_runs), and project.new_block fills in <BLOCK>, the Building block's name, such
as runs_per_job; every other placeholder is yours to fill in, and Python stops at the
first one left in, so a half-filled file can't run. Each Template's first lines list its
placeholders, with an example of each.

A Table notebook's Template is a .py file whose cells start with a "# %%" line, or
"# %% [markdown]" for a text cell, whose lines each start with "# ". Every one has the same
six code cells: 1 the Project and your query, connected by connect(...), 2 the logic, 3 try it,
4 its lineage, 5 its Hive, in <NAME>.hql beside the notebook, 6 its rows in the Reference
sheet; they differ in the logic, which defines write(), the function that writes the table.
The copies in admin/templates/ are yours: edit one, or add your own beside them, and the next
project.new_table(...) uses it.
Editing a Template changes only the notebooks made after.
"""

from __future__ import annotations

# The line of a notebook's setup cell the user fills in with their connection: each notebook
# runs on its own, so each gives warehouse.py its connection at its top (Toolbox 8.6). The
# Example projects fill it in as connect(example_database).
CONNECT_PLACEHOLDER = "# connect(your_connection)"
# What a notebook's setup cell holds under its import from warehouse, in every notebook the
# Toolbox writes that reaches the warehouse: the comment, then the line to fill in.
CONNECT_LINES = f'''
# Your connection to the warehouse. Each notebook runs on its own, so each connects here, at
# its top, before it calls query or execute: write yours in the line below and delete its #,
# such as connect(your_library.connect(...)). A connection kept in a file outside the Project,
# such as team_connection.py, is imported by these lines, written in that line's place:
#     sys.path.append("C:/work/connections")  # the folder team_connection.py is in
#     from team_connection import conn
#     connect(conn)
{CONNECT_PLACEHOLDER}'''

# The code cells every Table notebook Template ends with, after its try-it cell: its lineage,
# its Hive in a file beside it, and its rows in the Reference sheet.
_LAST_CELLS = '''
# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. Its Hive: <NAME>.hql beside this notebook, from the logic as last saved
export_hive()

# %%
# 6. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
'''

# The text cell of every Table notebook Template, after its list of placeholders: its Terms
# and its steps up to the one that writes its Table reference, which `saves` goes on.
_TERMS_AND_FIRST_STEPS = '''\
#
# ## Terms
#
# - **Logic**: the code cell that starts `# logic`, cell 2. It only imports and defines, so
#   `project.load("<DB>.<TABLE>")` can run it from anywhere else, for lineage across your
#   tables and for `admin/run_tables.ipynb`, which sends its `write()`.
# - **Table reference**: `references/<NAME>.py`, the script describing this table: its
#   columns and their types, its Partitions and its Key.
# - **Partition**: the rows of a table that share one value of each column it is partitioned
#   by.
# - **Key**: the columns whose values name exactly one row of the table.
# - **Decision**: one thing about this table that only you decide, such as its location; its
#   Table reference says whether it is made.
#
# ## Steps
#
# 1. **Fill in each `<...>`.** Goal: logic that runs. Action: type over each one listed above,
#    in the code cells. Done when no code cell holds a `<...>`; then step 2.
# 2. **Save the notebook.** Goal: the logic its Table reference is written from. Action: save
#    it. Done when it is saved; then step 3.
# 3. **Write its Table reference.** Goal: a Table reference written from the logic. Action:
#    run `project.reference_from_logic("<DB>.<TABLE>")`, a new_table Workflow step, which
#    writes `references/<NAME>.py` from the logic, for you to answer.'''
# Its steps after `saves`, and the start of what it says of this table, which `about` goes on.
_LAST_STEPS = '''\
#    Done when `references/<NAME>.py` lists those columns; then step 4.
# 4. **Answer its Decisions.** Goal: each Decision made. Action: answer each open Decision its
#    Table reference leaves, such as its location, in the new_table Workflow's decisions
#    cell. Done when its Table reference leaves no Decision open; then step 5.
# 5. **Say what one row is.** Goal: a reader knows what the table holds. Action: write one
#    line saying what one row of <DB>.<TABLE> is, in place of the TODO line below. Done when
#    no TODO line is left in this cell; then step 6.
# 6. **Run the cells.** Goal: the logic tried, its lineage and Hive written, and its rows in
#    the Reference sheet. Action: run the code cells top to bottom, once its Table reference
#    is written from the logic. Done when each runs with no error, and cell 3 shows the rows
#    `preview()` gives.
#
# ## This table
#
# TODO: say in one line what one row of <DB>.<TABLE> is.
#'''
# Its last lines: what each code cell is for, and its Self-check.
_CODE_CELLS_AND_SELF_CHECK = '''\
#
# ## The code cells
#
# - 1: the Project, your connection, connected with `connect(...)`, and your query.
# - 2: the logic, which starts `# logic`.
# - 3: try it.
# - 4: its lineage.
# - 5: its Hive, in <NAME>.hql.
# - 6: its rows in the Reference sheet.
#
# ## Self-check
#
# - No code cell holds a `<...>`.
# - `references/<NAME>.py` lists the columns `write()` saves, and leaves no Decision open.
# - One line above says what one row is, and no TODO line is left.
# - Each code cell runs top to bottom with no error.'''


def _notebook(name: str, about: str, saves: str, fill_in: str, logic: str, try_it: str
              ) -> str:
    """A Table notebook's Template: its text cell, then its six code cells, the logic and the
    try-it cell its own, the others the same in every Template. `fill_in` lists each
    placeholder of the notebook with an example, first; `saves` says what the table's Table
    reference lists, indented as a line of its text cell's step 3."""
    # The call that made the notebook: new_table's own Template needs no template=.
    call = ('"<DB>.<TABLE>"' if name == "saved_table"
            else f'"<DB>.<TABLE>", template="{name}"')
    return f'''# %% [markdown]
# # <DB>.<TABLE>
#
# Fill in every `<...>` in the code cells below, brackets and all: the notebook won't run with
# one left. They are:
{fill_in}
{_TERMS_AND_FIRST_STEPS}
{saves}
{_LAST_STEPS}
{about}
#
# Made by `project.new_table({call})` from
# `admin/templates/{name}.py`, which filled in the database, the table and its file's name,
# <NAME>.
{_CODE_CELLS_AND_SELF_CHECK}

# %%
# 1. The Project and your query
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_hive, export_lineage, project, run_query, show_hive
from warehouse import connect, query
{CONNECT_LINES}

# %%
{logic}
# %%
# 3. Try it: the Hive of each step, then the rows
{try_it}
{_LAST_CELLS}'''


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
#     of rows() naming `<PARTITION_COLUMN>`, and write `PARTITIONED_BY = []`, instead.'''
# The comment above READS in every logic cell.
_READS_COMMENT = '''\
# The rows write() reads: change it to write others. A condition that calls something other
# than equals, such as between or is_in, needs it added to the import above.'''
# What quality_checks says of READS and of the partition column, and above READS: the same,
# for the rows it checks. Written out in full, so a rewording of one can't miss the other.
_CHECKED_READS_FILL_IN = '''\
#   - `<READS>`: which of its rows are checked, as a condition on it, such as
#     `equals(job_runs.dt, "2026-09-24")` or `equals(region_costs.region, "eu")`. On a
#     partitioned table, it must filter one of its partition columns. A table that isn't
#     partitioned can be read whole: delete the line `READS = <READS>` and each line
#     `WHERE(READS),` instead;'''
_CHECKED_PARTITION_FILL_IN = '''\
#   - `<PARTITION_COLUMN>`: the column of the table checked that fills this table's partition
#     column, such as `dt` or `region`. If this table isn't partitioned, delete the two lines
#     of rows() naming `<PARTITION_COLUMN>`, and write `PARTITIONED_BY = []`, instead.'''
_CHECKED_READS_COMMENT = '''\
# The rows checked: change it to check others. A condition that calls something other
# than equals, such as between or is_in, needs it added to the import above.'''

SAVED_TABLE = _notebook(
    "saved_table",
    about='''\
# A Saved table worked out from a table it reads: a count per group of the rows READS picks.
# It is partitioned as PARTITIONED_BY says, or not at all.''',
    saves='''\
#    It lists the columns write() saves, in the order its SELECT gives them: here
#    <GROUP_COLUMN>, typed as the table read types it, then <COUNT_NAME>, a count, "bigint",
#    and last its partition column, if it has one, as PARTITIONED_BY names it. Its Key,
#    proposed from the logic, is the column each row is for, and the partition column if it
#    has one, such as key=["job_id", "region"].''',
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

# This table's partition columns, in the order its SELECT gives them, last: [] for none.
PARTITIONED_BY = ["<PARTITION_COLUMN>"]


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
#    It lists one column, "row_count", a count, "bigint", then the partition column counted,
#    typed as the table checked types it, as PARTITIONED_BY names it. Its Key, proposed from
#    the logic, is that partition column: one row per Partition counted.''',
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

# This table's partition columns, in the order its SELECT gives them, last: [] for none.
PARTITIONED_BY = ["<PARTITION_COLUMN>"]


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
            <CHECKED>.<PARTITION_COLUMN>,  # the Partition counted: this table's partition \
column
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

project.reference_from_logic("<DB>.<TABLE>") writes this file again from the table's logic,
filling in what is left. They are:
    <COLUMNS>: the columns write() saves and their types, from its logic's preview().

Why: TODO: who reads this table, and why it is saved rather than worked out each time.

project.new_table wrote this file from admin/templates/saved_table_reference.py, to stand in
until the table's logic is written: then project.reference_from_logic writes it again, its
columns and types from preview(), its partition columns from PARTITIONED_BY, and the Key its
query makes. A Saved table doesn't exist until its notebook's create() makes it from this
file, so nothing can be asked of it: its logic says what it holds.
"""

from sqlglot_composer import Table

<TABLE> = Table(
    "<DB>.<TABLE>",
    columns={"<COLUMNS>": "string"},  # project.reference_from_logic writes them, from the logic
    location=None,  # TODO: its own folder, such as "/data/your_team/<DB>.db/<TABLE>"
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

# A Scheduled run's notebook, which project.new_scheduled_run makes in scheduled_runs/<NAME>/
# (Toolbox 8.6): its cells top to bottom, the parameters cell first, which write_notebook tags
# parameters, as papermill finds it.
SCHEDULED_RUN = '''# %% [markdown]
# # Scheduled run: <NAME>
#
# Fill in every `<...>` in the code cells below, brackets and all: the notebook won't run with
# one left. They are:
#   - `<RESULT_NAME>`: the name a SELECT's rows come back by, in quotes, such as
#     `"week_totals"`;
#   - `<SAVED_TABLE>`: a Saved table whose Table notebook's logic it uses, such as
#     `mart.team_days`;
#   - `<LOGIC_FUNCTION>`: the function of that logic it calls, with what it takes, such as
#     `week_totals(FIRST_DAY, LAST_DAY)`, two parameters, or `write()`.
#
# Follow the steps in order, as written.
#
# ## Terms
#
# - **Scheduled run**: this notebook, which an outside scheduler runs top to bottom: building
#   the Statements and their Hive in the Build cell, then sending them in the Run cell.
# - **Parameter**: a value the scheduler passes in, one of the names in the `# parameters`
#   cell, read by its type hint: `"2026-11-01"` given for a `datetime.date` is that date.
# - **Run value**: what a Python function gives each time a Statement is built, such as the
#   latest Partition of a table; `run_values=` gives one a value of yours for this run.
#
# ## Steps
#
# 1. **Name the parameters.** Goal: each value the scheduler passes in. Action: write each in
#    the `# parameters` cell as a name, its type hint and its default, such as
#    `RUN_DATE: datetime.date | None = None`; keep `START_FROM`. Done when each has a hint;
#    then step 2.
# 2. **Connect.** Goal: this run's account. Action: in the setup cell, write your connection
#    in the `connect(...)` line and delete its `#`. Done when the setup cell runs; then step 3.
# 3. **Name the Statements.** Goal: what this run sends. Action: write each in the dict
#    `statements()` gives, in the `# scheduled` cell, by name. If it is a Table notebook's
#    logic, load it: `project.load("mart.team_days").week_totals(FIRST_DAY, LAST_DAY)`. If
#    it is your own, compose it there, with `statement(...)`. Done when each is named; then
#    step 4.
# 4. **Build.** Goal: the Hive, in order, to read before anything is sent. Action: run the
#    cells down to the Build cell. If a table it would write is written elsewhere, name it in
#    `leave_out=`. Done when it prints each Statement's Hive in order; then step 5.
# 5. **Run.** Goal: the Statements sent and the SELECTs' rows back. Action: run the Run cell,
#    or have the scheduler run the notebook. Done when it ends with no error; each SELECT's
#    rows are in `results` by the name `statements()` gives it, such as
#    `results["week_totals"]`.
#
# ## What the build prints
#
# First each parameter as used, then each Statement in the order it is sent, headed like
# `-- 3 of 7: mart.team_days (read by week_totals)`, and its Hive. The writes of each table of
# this Project the Statements read are added, all the way up, before what reads them.
#
# Made by `project.new_scheduled_run("<NAME>")` from `admin/templates/scheduled_run.py`.
#
# ## Self-check
#
# - No code cell holds a `<...>`.
# - Each parameter in the `# parameters` cell has a type hint.
# - The Build cell prints each Statement's Hive, in order, and sends nothing.

# %%
# parameters
# The values a scheduler passes in, each a name, its type hint and its default. A scheduler
# passes text, which the Build cell reads by the hint, and refuses a value it can't read. The
# hints it reads: datetime.date, int, float, bool, str, each alone, in list[...] or with
# | None, such as list[datetime.date] for "2026-11-01,2026-11-08".
import datetime  # for a datetime.date hint

START_FROM: str = ""  # a table or SELECT to start from, as a failed run prints it; "" sends all
# RUN_DATE: datetime.date | None = None  # such as "2026-11-01", passed in as text

# %%
# Setup: the Project on Python's path, the Toolbox and your connection
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import Statement, project, statement
from warehouse import connect, execute, query
''' + CONNECT_LINES + '''

# %%
# scheduled
# The Statements this run sends, each by its name: a SELECT's rows come back in results by it.
# A Table notebook's logic gives them through project.load, such as
#     "week_totals": project.load("mart.team_days").week_totals(FIRST_DAY, LAST_DAY),
# and a Statement of your own is composed here with statement(...). A value worked out each
# time the run is built goes in as run_value(function), a function of this cell, such as
# week_totals(run_value(week_start), ...): import run_value from sqlglot_composer here.


def statements() -> dict[str, Statement]:
    """What this run sends, by name: the build adds the writes of each table they read."""
    return {
        "<RESULT_NAME>": project.load("<SAVED_TABLE>").<LOGIC_FUNCTION>,
    }

# %%
# Build: the Statements, in order, and their Hive, printed; nothing sent
# It reads the parameters first, then builds each Statement, adding the writes of each table
# of this Project they read. run_values={"period_end": RUN_DATE} gives a parameter of yours,
# RUN_DATE, to each Run value whose function is named period_end, in the writes added too;
# leave_out=["mart.daily_job_runs"] leaves out that table's write, and what only it reads.
built = project.build_run(statements, run_values={}, leave_out=[])

# %%
# Run: each one sent, in the build's order
# Each write is sent through execute and each SELECT through query; each SELECT's rows are in
# results by the name statements() gives it, such as results["week_totals"]. One that fails
# stops the rest, and the run prints the START_FROM to send the rest from.
results = built.run(query, execute)
'''

# Each Template by its name, as start() writes it into admin/templates/<name>.py. The Table
# notebook Templates are the ones new_table's template= takes; new_block makes a Building
# block from building_block, and new_scheduled_run a Scheduled run from scheduled_run.
NOTEBOOK_TEMPLATES = {
    "saved_table": SAVED_TABLE,
    "quality_checks": QUALITY_CHECKS,
}
TEMPLATES = {
    **NOTEBOOK_TEMPLATES,
    "saved_table_reference": SAVED_TABLE_REFERENCE,
    "building_block": BUILDING_BLOCK,
    "scheduled_run": SCHEDULED_RUN,
}
