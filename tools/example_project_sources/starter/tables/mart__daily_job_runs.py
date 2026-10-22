# %% [markdown]
# # mart.daily_job_runs
#
# Each job's runs, failed runs and minutes per day, saved every day.
#
# Why: counting every run again each time someone asks is slow, so the counts are worked out
# once a day and saved in a Saved table that anyone can read, mart.team_day among them.
#
# Made by `project.new_table("mart.daily_job_runs")` from `admin/templates/saved_table.py`, then
# filled in. Its rows come from the Building block `building_blocks/runs_per_job.py`, which
# mart.team_day's notebook reads too, so the two can never count runs two ways. Every run
# counts, TEST runs among them. It is partitioned by dt, as ops.job_runs is.
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
    FROM, INSERT_OVERWRITE, SELECT, Clause, Statement, create_table, equals, statement,
)
from building_blocks.runs_per_job import runs_per_job
from references.mart__daily_job_runs import daily_job_runs
from references.ops__job_runs import job_runs

DAY = "2026-09-24"  # the dt write() writes: change it to write another


def create() -> Statement:
    """Step 1: create mart.daily_job_runs from its Table reference, if it isn't there yet.
    may_exist=True writes CREATE EXTERNAL TABLE IF NOT EXISTS, so it never changes a table
    that is there."""
    return create_table(daily_job_runs, may_exist=True)


def rows() -> list[Clause]:
    """The clauses preview and write share: each job's numbers on DAY, from the Building
    block. dt comes last in SELECT: INSERT_OVERWRITE(daily_job_runs) writes the rows into the
    Partition their dt names, PARTITION(dt), and replaces only that one. Cell 3 prints the Hive
    it makes."""
    per_job = runs_per_job(equals(job_runs.dt, DAY))
    return [
        SELECT(per_job.job_id, per_job.runs, per_job.failed_runs, per_job.minutes, per_job.dt),
        FROM(per_job),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows())


def write() -> Statement:
    """Step 3: save DAY's rows, replacing whatever DAY's Partition held, so sending it twice
    leaves the same rows, not twice as many."""
    return statement(INSERT_OVERWRITE(daily_job_runs), *rows())

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
