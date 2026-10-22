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
#     naming `<PARTITION_COLUMN>` instead.
#
# Then fill in this table's Table reference, `references/<NAME>.py`: its `<...>` and TODO
# lines.
# It lists the columns write() saves, in the order its SELECT gives them: here
# <GROUP_COLUMN>, typed as the table read types it, then <COUNT_NAME>, a count, "bigint", and
# last its partition column, if it has one, also named in partitioned_by=[...]. Its Key is
# the column each row is for, and the partition column if it has one, such as
# key=["job_id", "region"].
#
# TODO: say in one line what one row of <DB>.<TABLE> is.
#
# A Saved table worked out from a table it reads: a count per group of the rows READS picks.
# It is partitioned however its Table reference says, or not at all.
#
# Made by `project.new_table("<DB>.<TABLE>")` from
# `admin/templates/saved_table.py`, which filled in the database, the table and its file's name,
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

from sqlglot_composer import export_lineage, project, run, show_hive
from warehouse import query

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
run(preview(), query=query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
