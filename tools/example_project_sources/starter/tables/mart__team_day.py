# %% [markdown]
# # mart.team_day
#
# Each team's runs, failed runs and minutes per day, saved every day.
#
# Why: once mart.daily_job_runs has saved a day, each team's numbers come from a few saved rows
# per job, not from every run again.
#
# Made by `project.new_table("mart.team_day")` from `admin/templates/saved_table.py`, then
# filled in. It reads the Saved table mart.daily_job_runs through its Table reference, like any
# other table, and ops.jobs for each job's team, so it is written after mart.daily_job_runs:
# `run_tables` sends it last. Adding up the jobs' counts per team is safe: a sum of counts is
# the count of them all.
#
# The Saved table is in your warehouse, not in the Example database, so its preview can't run
# here. `team_runs_from_job_runs(...)` can: it groups the Building block's rows by team the same
# way, from ops.job_runs itself. Its lineage, cell 4, draws both tables, from ops.job_runs to
# here, through mart.daily_job_runs' logic.
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
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, JOIN, SELECT, WHERE, Clause, Condition, Statement,
    create_table, equals, statement, sum_of,
)
from building_blocks.runs_per_job import runs_per_job
from references.mart__daily_job_runs import daily_job_runs
from references.mart__team_day import team_day
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

# The rows write() reads: change it to write others.
READS = equals(daily_job_runs.dt, "2026-09-24")


def create() -> Statement:
    """Step 1: create mart.team_day from its Table reference, if it isn't there yet."""
    return create_table(team_day, may_exist=True)


def rows() -> list[Clause]:
    """The clauses preview and write share: each team's numbers for each dt of the rows READS
    picks, from daily_job_runs, the table in FROM, whose dt comes last in SELECT:
    INSERT_OVERWRITE writes the rows into the Partitions their dt names."""
    return [
        SELECT(
            jobs.team,
            AS(sum_of(daily_job_runs.runs), "runs"),
            AS(sum_of(daily_job_runs.failed_runs), "failed_runs"),
            AS(sum_of(daily_job_runs.minutes), "minutes"),
            daily_job_runs.dt,
        ),
        FROM(daily_job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, daily_job_runs.job_id)),
        WHERE(READS),
        GROUP_BY(jobs.team, daily_job_runs.dt),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows())


def write() -> Statement:
    """Step 3: save the rows, once mart.daily_job_runs has written them."""
    return statement(INSERT_OVERWRITE(team_day), *rows())


def team_runs_from_job_runs(reads: Condition) -> Statement:
    """Each team's runs, failed runs and minutes for the rows of ops.job_runs `reads` picks,
    such as equals(job_runs.dt, "2026-09-24"), through the Building block mart.daily_job_runs
    saves: so it runs on the Example database, and at work checks a day mart.daily_job_runs
    hasn't saved yet."""
    per_job = runs_per_job(reads)
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
run_query(team_runs_from_job_runs(equals(job_runs.dt, "2026-09-24")), query)

# %%
# 4. Lineage: both tables together, in a new pair in lineage/ named by the time and this
# table. project.load gives another notebook's logic cell, run, so its write() can be drawn
# here too. Each write is put in a variable first: the Lineage names it after the variable.
daily = project.load("mart.daily_job_runs")
write_daily_job_runs = daily.write()
write_team_day = write()
export_lineage(write_daily_job_runs, write_team_day)

# %%
# 5. The Reference sheet: this table's rows, from references/mart__team_day.py
project.refresh_reference_sheet("mart.team_day")
