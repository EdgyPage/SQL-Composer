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
# The code cells: 1 the Project and your send; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet. The Example database can be read but not
# written, so cell 3 prints each write's Hive and runs only the preview.

# %%
# 1. The Project, your send, and a day to try things on
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_lineage, project, run, show_hive
from send import send

DAY = "2026-09-24"  # the Example database's last day

# %%
# logic
from sqlglot_composer import FROM, INSERT_OVERWRITE, SELECT, by_day, create_table, statement
from building_blocks.runs_per_job_day import runs_per_job_day
from references.mart__daily_job_runs import daily_job_runs


def create():
    """Step 1: create mart.daily_job_runs from its Table reference, if it isn't there yet.
    may_exist=True writes CREATE EXTERNAL TABLE IF NOT EXISTS, so it never changes a table
    that is there."""
    return create_table(daily_job_runs, may_exist=True)


def rows(first_day, last_day):
    """The clauses every step below shares: each job's numbers per day, from the Building
    block. The day, dt, isn't selected: INSERT_OVERWRITE writes it as the partition, from the
    Building block's bound on ops.job_runs."""
    per_job_day = runs_per_job_day(first_day, last_day)
    return [
        SELECT(per_job_day.job_id, per_job_day.runs, per_job_day.failed_runs,
               per_job_day.minutes),
        FROM(per_job_day),
    ]


def preview(day):
    """Step 2: the rows write_day(day) would save, as a SELECT to run and check first."""
    return statement(*rows(day, day))


def write_day(day):
    """Step 3, every day: save the day's rows, replacing whatever the day held, so sending it
    twice leaves the same rows, not twice as many."""
    return statement(INSERT_OVERWRITE(daily_job_runs), *rows(day, day))


def backfill(first_day, last_day):
    """Step 4, when needed: one write per day from first_day to last_day, oldest first. The
    Building block keeps the day in its GROUP_BY, so no day's counts mix with another's."""
    return by_day(statement(INSERT_OVERWRITE(daily_job_runs), *rows(first_day, last_day)))

# %%
# 3. Try it: the Hive of each step, then the day's rows
show_hive([create(), write_day(DAY)])
run(preview(DAY), send=send)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write_day(DAY))

# %%
# 5. The Reference sheet: this table's rows, from references/mart__daily_job_runs.py
project.refresh_reference_sheet("mart.daily_job_runs")
