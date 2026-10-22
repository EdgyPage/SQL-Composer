# %% [markdown]
# # mart.daily_job_runs
#
# Each job's runs, failed runs and minutes per day, saved every day.
#
# Why: counting every run again each time someone asks is slow, so the counts are worked out
# once a day and saved in a Saved table that anyone can read, mart.team_day among them.
#
# Made by `project.new_table("mart.daily_job_runs")` from `admin/templates/daily_table.py`, then
# filled in. Its rows come from the Building block `building_blocks/runs_per_job_day.py`, which
# mart.team_day's notebook reads too, so the two can never count runs two ways. Every run
# counts, TEST runs among them.
#
# The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet. The Example database can be read but not
# written, so cell 3 prints each write's Hive and runs only the preview.

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
    FROM, INSERT_OVERWRITE, SELECT, Clause, Statement, create_table, statement,
)
from building_blocks.runs_per_job_day import runs_per_job_day
from references.mart__daily_job_runs import daily_job_runs

DAY = "2026-09-24"  # the day write() writes, the Example database's last day


def create() -> Statement:
    """Step 1: create mart.daily_job_runs from its Table reference, if it isn't there yet.
    may_exist=True writes CREATE EXTERNAL TABLE IF NOT EXISTS, so it never changes a table
    that is there."""
    return create_table(daily_job_runs, may_exist=True)


def rows(first_day: str, last_day: str) -> list[Clause]:
    """The clauses every step below shares: each job's numbers per day, from the Building
    block. The day, dt, comes last in SELECT: INSERT_OVERWRITE(daily_job_runs) writes each
    day's rows into that day's Partition, PARTITION(dt), and replaces only the days the rows
    hold. Cell 3 prints the Hive it makes."""
    per_job_day = runs_per_job_day(first_day, last_day)
    return [
        SELECT(per_job_day.job_id, per_job_day.runs, per_job_day.failed_runs,
               per_job_day.minutes, per_job_day.dt),
        FROM(per_job_day),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows(DAY, DAY))


def write() -> Statement:
    """Step 3: save DAY's rows, replacing whatever DAY held, so sending it twice leaves the
    same rows, not twice as many."""
    return statement(INSERT_OVERWRITE(daily_job_runs), *rows(DAY, DAY))


def backfill(first_day: str, last_day: str) -> Statement:
    """Step 4, when needed: save every day from first_day to last_day in one write, replacing
    those days. The Building block keeps the day in its GROUP_BY, so no day's counts mix with
    another's."""
    return statement(INSERT_OVERWRITE(daily_job_runs), *rows(first_day, last_day))

# %%
# 3. Try it: the Hive of each step, then the day's rows
show_hive([create(), write()])
run(preview(), query=query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. The Reference sheet: this table's rows, from references/mart__daily_job_runs.py
project.refresh_reference_sheet("mart.daily_job_runs")
