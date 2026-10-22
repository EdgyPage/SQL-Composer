# %% [markdown]
# # mart.alerts_per_job
#
# Each job's alerts and high alerts per day, saved every day.
#
# Why: an alert names only its run, so finding its job means joining every alert to
# ops.job_runs, which is worth doing once a day and saving, rather than in every Statement that
# counts alerts.
#
# Made by `project.new_table("mart.alerts_per_job")` from `admin/templates/saved_table.py`, then
# filled in. Its rows join each alert to its run, for the run's job, so READS filters both
# tables. A run can raise an alert after midnight, so ops.job_runs is read from the day before
# as well: an alert counts on the day it was raised, whichever of the two days its run is in.
# Each alert joins its run on run_id, ops.job_runs' Key, so it is counted once.
#
# The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet.

# %%
# 1. The Project and your query
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_lineage, project, run_query, show_hive
from warehouse import query

# %%
# logic
# 2. The logic: imports, the rows it reads, and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, JOIN, SELECT, WHERE, Clause, Statement, all_of,
    between, count_rows, create_table, equals, statement,
)
from references.mart__alerts_per_job import alerts_per_job
from references.ops__job_runs import job_runs
from references.ops__run_alerts import high, run_alerts  # high: an Alias, severity is "high"

# The rows write() reads: change it to write others. It reads two tables, so it filters
# both: the alerts raised on a day, and the runs of that day and the day before, since a run
# can raise an alert after midnight.
READS = all_of(equals(run_alerts.dt, "2026-09-24"),
               between(job_runs.dt, "2026-09-23", "2026-09-24"))


def create() -> Statement:
    """Step 1: create mart.alerts_per_job from its Table reference, if it isn't there yet."""
    return create_table(alerts_per_job, may_exist=True)


def rows() -> list[Clause]:
    """The clauses preview and write share: each job's alerts for each dt of the alerts READS
    picks. dt comes last in SELECT, as run_alerts.dt, the day each alert was raised:
    INSERT_OVERWRITE writes the rows into the Partitions their dt names."""
    return [
        SELECT(job_runs.job_id, AS(count_rows(), "alerts"),
               AS(count_rows(where=high), "high_alerts"), run_alerts.dt),
        FROM(run_alerts),
        JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
        WHERE(READS),
        GROUP_BY(job_runs.job_id, run_alerts.dt),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows())


def write() -> Statement:
    """Step 3: save the rows, replacing whatever the Partitions they fill held."""
    return statement(INSERT_OVERWRITE(alerts_per_job), *rows())

# %%
# 3. Try it: the Hive of each step, then the rows
show_hive([create(), write()])
run_query(preview(), query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. The Reference sheet: this table's rows, from references/mart__alerts_per_job.py
project.refresh_reference_sheet("mart.alerts_per_job")
