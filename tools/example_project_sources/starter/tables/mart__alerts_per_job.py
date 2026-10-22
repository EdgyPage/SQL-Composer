# %% [markdown]
# # mart.alerts_per_job
#
# Each job's alerts and high alerts per day, saved every day.
#
# Why: an alert names only its run, so finding its job means joining every alert to
# ops.job_runs, which is worth doing once a day and saving, rather than in every Statement that
# counts alerts.
#
# Made by `project.new_table("mart.alerts_per_job")` from `admin/templates/daily_table.py`, then
# filled in. A run can raise an alert after midnight, so ops.job_runs is read from the day
# before as well: an alert counts on the day it was raised, whichever of the two days its run
# is in. Each alert joins its run on run_id, ops.job_runs' Key, so it is counted once.
#
# The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet.

# %%
# 1. The Project and your query
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_lineage, project, run, show_hive
from warehouse import query

# %%
# logic
# 2. The logic: imports, the day it writes, and functions only
import datetime

from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, JOIN, SELECT, WHERE, Clause, Statement, between,
    count_rows, create_table, equals, statement,
)
from references.mart__alerts_per_job import alerts_per_job
from references.ops__job_runs import job_runs
from references.ops__run_alerts import high, run_alerts  # high: an Alias, severity is "high"

DAY = "2026-09-24"  # the day write() writes, the Example database's last day


def day_before(day: str) -> str:
    """The day before `day`, written the same way: day_before("2026-09-24") is "2026-09-23"."""
    return (datetime.date.fromisoformat(day) - datetime.timedelta(days=1)).isoformat()


def create() -> Statement:
    """Step 1: create mart.alerts_per_job from its Table reference, if it isn't there yet."""
    return create_table(alerts_per_job, may_exist=True)


def rows(first_day: str, last_day: str) -> list[Clause]:
    """The clauses every step below shares: each job's alerts per day. The day comes last in
    SELECT, as run_alerts.dt, the day each alert was raised: INSERT_OVERWRITE writes each
    day's rows into that day's Partition. job_runs is joined from the day before first_day
    too, since an alert can come the day after its run."""
    return [
        SELECT(job_runs.job_id, AS(count_rows(), "alerts"),
               AS(count_rows(where=high), "high_alerts"), run_alerts.dt),
        FROM(run_alerts),
        JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
        WHERE(between(run_alerts.dt, first_day, last_day),
              between(job_runs.dt, day_before(first_day), last_day)),
        GROUP_BY(run_alerts.dt, job_runs.job_id),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows(DAY, DAY))


def write() -> Statement:
    """Step 3: save DAY's rows, replacing whatever DAY held."""
    return statement(INSERT_OVERWRITE(alerts_per_job), *rows(DAY, DAY))


def backfill(first_day: str, last_day: str) -> Statement:
    """Step 4, when needed: save every day from first_day to last_day in one write, replacing
    those days."""
    return statement(INSERT_OVERWRITE(alerts_per_job), *rows(first_day, last_day))

# %%
# 3. Try it: the Hive of each step, then the day's rows
show_hive([create(), write()])
run(preview(), query=query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. The Reference sheet: this table's rows, from references/mart__alerts_per_job.py
project.refresh_reference_sheet("mart.alerts_per_job")
