# %% [markdown]
# # mart.team_day
#
# Each team's runs, failed runs, minutes and alerts per day, saved every day.
#
# Why: once mart.daily_job_runs and mart.alerts_per_job have saved a day, each team's numbers
# come from a few saved rows per job, not from every run and alert again.
#
# Made by `project.new_table("mart.team_day")` from `admin/templates/saved_table.py`, then
# filled in. It reads the two Saved tables through their Table references, like any other
# table, and ops.jobs for each job's team, so it is written after them: `run_tables` sends it
# last. A job whose runs raised no alert has no row in mart.alerts_per_job, so LEFT_JOIN keeps
# its runs with NULL alerts, and fill_null counts them as 0.
#
# The Saved tables are in your warehouse, not in the Example database, so its preview can't
# run here. `team_runs_from_job_runs(DAY)` can: it groups the Building block's rows by team the
# same way, from ops.job_runs itself. Its lineage, cell 4, draws all three tables, from
# ops.job_runs and ops.run_alerts to here, through the other two notebooks' logic.
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
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, JOIN, LEFT_JOIN, SELECT, WHERE, Clause, Statement,
    all_of, create_table, equals, fill_null, statement, sum_of,
)
from building_blocks.runs_per_job import runs_per_job
from references.mart__alerts_per_job import alerts_per_job
from references.mart__daily_job_runs import daily_job_runs
from references.mart__team_day import team_day
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

DAY = "2026-09-24"  # the dt write() writes: change it to write another


def create() -> Statement:
    """Step 1: create mart.team_day from its Table reference, if it isn't there yet."""
    return create_table(team_day, may_exist=True)


def rows() -> list[Clause]:
    """The clauses preview and write share: each team's numbers on DAY, from daily_job_runs,
    the table in FROM, whose dt comes last in SELECT: INSERT_OVERWRITE writes the rows into the
    Partition their dt names. The alerts are joined on their dt as well as their job, so the
    day's runs meet only that day's alerts; their dt goes in LEFT_JOIN's ON=, not WHERE, since
    a WHERE on alerts_per_job would drop the jobs LEFT_JOIN keeps for having no alert."""
    return [
        SELECT(
            jobs.team,
            AS(sum_of(daily_job_runs.runs), "runs"),
            AS(sum_of(daily_job_runs.failed_runs), "failed_runs"),
            AS(sum_of(daily_job_runs.minutes), "minutes"),
            AS(fill_null(sum_of(alerts_per_job.alerts), 0), "alerts"),
            AS(fill_null(sum_of(alerts_per_job.high_alerts), 0), "high_alerts"),
            daily_job_runs.dt,
        ),
        FROM(daily_job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, daily_job_runs.job_id)),
        LEFT_JOIN(alerts_per_job,
                  ON=all_of(equals(alerts_per_job.job_id, daily_job_runs.job_id),
                            equals(alerts_per_job.dt, daily_job_runs.dt),
                            equals(alerts_per_job.dt, DAY))),
        WHERE(equals(daily_job_runs.dt, DAY)),
        GROUP_BY(daily_job_runs.dt, jobs.team),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows())


def write() -> Statement:
    """Step 3: save DAY's rows, once the two tables it reads have written DAY."""
    return statement(INSERT_OVERWRITE(team_day), *rows())


def team_runs_from_job_runs(day: str) -> Statement:
    """Each team's runs, failed runs and minutes for a day, from ops.job_runs itself, through
    the Building block mart.daily_job_runs saves: so it runs on the Example database, and at
    work checks a day mart.daily_job_runs hasn't saved yet."""
    per_job = runs_per_job(equals(job_runs.dt, day))
    return statement(
        SELECT(
            jobs.team,
            AS(sum_of(per_job.runs), "runs"),
            AS(sum_of(per_job.failed_runs), "failed_runs"),
            AS(sum_of(per_job.minutes), "minutes"),
        ),
        FROM(per_job),
        JOIN(jobs, ON=equals(jobs.job_id, per_job.job_id)),
        GROUP_BY(jobs.team),
    )

# %%
# 3. Try it: the Hive of each step, then each team's runs from ops.job_runs
show_hive([create(), write()])
run(team_runs_from_job_runs(DAY), query=query)

# %%
# 4. Lineage: the three tables together, in a new pair in lineage/ named by the time and this
# table. project.load gives another notebook's logic cell, run, so its write() can be drawn
# here too.
daily = project.load("mart.daily_job_runs")
alerts = project.load("mart.alerts_per_job")
export_lineage(daily.write(), alerts.write(), write())

# %%
# 5. The Reference sheet: this table's rows, from references/mart__team_day.py
project.refresh_reference_sheet("mart.team_day")
