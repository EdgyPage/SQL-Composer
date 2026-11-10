# %% [markdown]
# # <DB>.<TABLE>
#
# Fill in every `<...>` in the code cells below, brackets and all: the notebook won't run with
# one left. They are:
#   - `<SOURCE_NAME>` and `<SOURCE_TABLE>`: the table it reads, by its file in references/ and
#     its name there, such as `ops__job_runs` and `job_runs`;
#   - `<READS>`: which of its rows write() reads, as a condition on it, such as
#     `equals(job_runs.dt, "2026-09-24")` or `equals(region_costs.region, "eu")`. On a
#     partitioned table, it must filter one of its partition columns. A table that isn't
#     partitioned can be read whole: delete the line `READS = <READS>` and each line
#     `WHERE(READS),` instead;
#   - `<GROUP_COLUMN>`: the column each row is for, such as `job_id`;
#   - `<COUNT_NAME>`: the name of the count it saves, in quotes, such as `"runs"`;
#   - `<PARTITION_COLUMN>`: the column of the table it reads that fills this table's partition
#     column, such as `dt` or `region`. If this table isn't partitioned, delete the two lines
#     of rows() naming `<PARTITION_COLUMN>`, and write `PARTITIONED_BY = []`, instead.
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
#    writes `references/<NAME>.py` from the logic, for you to answer.
#    It lists the columns write() saves, in the order its SELECT gives them: here
#    <GROUP_COLUMN>, typed as the table read types it, then <COUNT_NAME>, a count, "bigint",
#    and last its partition column, if it has one, as PARTITIONED_BY names it. Its Key,
#    proposed from the logic, is the column each row is for, and the partition column if it
#    has one, such as key=["job_id", "region"].
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
#
# A Saved table worked out from a table it reads: a count per group of the rows READS picks.
# It is partitioned as PARTITIONED_BY says, or not at all.
#
# Made by `project.new_table("<DB>.<TABLE>")` from
# `admin/templates/saved_table.py`, which filled in the database, the table and its file's name,
# <NAME>.
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
# - Each code cell runs top to bottom with no error.

# %%
# 1. The Project and your query
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_hive, export_lineage, project, run_query, show_hive
from warehouse import connect, query

# Your connection to the warehouse. Each notebook runs on its own, so each connects here, at
# its top, before it calls query or execute: write yours in the line below and delete its #,
# such as connect(your_library.connect(...)). A connection kept in a file outside the Project,
# such as team_connection.py, is imported by these lines, written in that line's place:
#     sys.path.append("C:/work/connections")  # the folder team_connection.py is in
#     from team_connection import conn
#     connect(conn)
sys.path.append('C:\\Users\\myfir\\AppData\\Local\\Temp\\usability-loop\\runs\\2026-11-09-W8-3')  # the folder team_connection.py is in
from team_connection import conn
connect(conn)

# %%
# logic
# 2. The logic: imports, the rows it reads, and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, count_rows,
    create_table, equals, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference
# each table it reads, such as: from references.ops__job_runs import job_runs
from references.<SOURCE_NAME> import <SOURCE_TABLE>

# The rows write() reads: change it to write others. A condition that calls something other
# than equals, such as between or is_in, needs it added to the import above.
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

# %%
# 3. Try it: the Hive of each step, then the rows
show_hive([create(), write()])
run_query(preview(), query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. Its Hive: <NAME>.hql beside this notebook, from the logic as last saved
export_hive()

# %%
# 6. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
