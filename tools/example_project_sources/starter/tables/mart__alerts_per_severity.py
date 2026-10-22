# %% [markdown]
# # mart.alerts_per_severity
#
# One row per severity and day: how many alerts of that severity the runs raised that day.
#
# A Saved table worked out from a table it reads: a count per group of the rows READS picks.
# It is partitioned however its Table reference says, or not at all.
#
# Made by `project.new_table("mart.alerts_per_severity")` from
# `admin/templates/saved_table.py`, which filled in the database, the table and its file's name,
# mart__alerts_per_severity. Run the cells top to bottom once both are filled in.
#
# The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet. The logic only imports and defines, so
# `project.load("mart.alerts_per_severity")` can run it from anywhere else, for lineage across your
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
from references.mart__alerts_per_severity import alerts_per_severity  # this table's own Table reference
# each table it reads, such as: from references.ops__job_runs import job_runs
from references.ops__run_alerts import run_alerts

# The rows write() reads: change it to write others. A condition that calls something other
# than equals, such as between or is_in, needs it added to the import above.
READS = equals(run_alerts.dt, "2026-09-24")


def create() -> Statement:
    """Step 1: create mart.alerts_per_severity from its Table reference, if it isn't there yet."""
    return create_table(alerts_per_severity, may_exist=True)


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
            run_alerts.severity,  # what each row is for
            AS(count_rows(), "alerts"),
            run_alerts.dt,  # this table's partition column, last
        ),
        FROM(run_alerts),
        WHERE(READS),
        GROUP_BY(
            run_alerts.severity,
            run_alerts.dt,  # kept, so each Partition's rows stay apart
        ),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows())


def write() -> Statement:
    """Step 3: save the rows, replacing the Partitions they fill, or the whole table if it
    isn't partitioned: sent twice, it leaves the same rows, not twice as many."""
    return statement(INSERT_OVERWRITE(alerts_per_severity), *rows())

# %%
# 3. Try it: the Hive of each step, then the rows
show_hive([create(), write()])
run(preview(), query=query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. The Reference sheet: this table's rows, from references/mart__alerts_per_severity.py
project.refresh_reference_sheet("mart.alerts_per_severity")
