# %% [markdown]
# # <DB>.<TABLE>
#
# Fill in every `<...>` in the code cells below, brackets and all: the notebook won't run with
# one left. They are:
#   - `<CHECKED_NAME>` and `<CHECKED>`: the table checked, by its file in references/ and
#     its name there, such as `ops__job_events` and `job_events`;
#   - `<READS>`: which of its rows are checked, as a condition on it, such as
#     `equals(job_runs.dt, "2026-09-24")` or `equals(region_costs.region, "eu")`. On a
#     partitioned table, it must filter one of its partition columns. A table that isn't
#     partitioned can be read whole: delete the line `READS = <READS>` and each line
#     `WHERE(READS),` instead;
#   - `<KEY_COLUMN>`: the column that picks out one row, such as `event_id`;
#   - `<PARTITION_COLUMN>`: the column of the table checked that fills this table's partition
#     column, such as `dt` or `region`. If this table isn't partitioned, delete the two lines
#     naming `<PARTITION_COLUMN>` instead.
#
# Then fill in this table's Table reference, `references/<NAME>.py`: its `<...>` and TODO
# lines.
# It lists one column, "row_count", a count, "bigint", then the partition column counted,
# typed as the table checked types it, also named in partitioned_by=[...]. Give it that
# partition column as its Key: one row per Partition counted.
#
# TODO: say in one line what one row of <DB>.<TABLE> is.
#
# Quality checks on a table you read. The row count of each of its Partitions READS picks is
# saved, so you can read them side by side and see one that looks too small; and checks run on
# the same rows: repeated_keys looks for a key with more than one row, and null_counts counts
# NULLs.
#
# Made by `project.new_table("<DB>.<TABLE>", template="quality_checks")` from
# `admin/templates/quality_checks.py`, which filled in the database, the table and its file's name,
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
# 2. The logic: imports, the rows it checks, and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, HAVING, INSERT_OVERWRITE, SELECT, WHERE, Clause, Column,
    Statement, all_columns, count_rows, create_table, equals, is_null, more_than, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference, of row counts
# the table checked, such as: from references.ops__job_events import job_events
from references.<CHECKED_NAME> import <CHECKED>

# The rows checked: change it to check others. A condition that calls something other
# than equals, such as between or is_in, needs it added to the import above.
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
    counts = [AS(count_rows(where=is_null(column)), f"null_{column_name(column)}")
              for column in all_columns(<CHECKED>)]
    return statement(
        SELECT(*counts),
        FROM(<CHECKED>),
        WHERE(READS),
    )

# %%
# 3. Try it: the Hive of each step, then the rows
show_hive([create(), write()])
run(preview(), query=query)
run(repeated_keys(), query=query)  # should have no rows
run(null_counts(), query=query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
