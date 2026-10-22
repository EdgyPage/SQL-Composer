# %% [markdown]
# # mart.job_day_facts
#
# Each job's events, runs and minutes per day, beside the team that owned the job that day,
# the last 3 days saved again on every run.
#
# Why: a job can change teams, so counting a team's day means looking each job up as of that
# day, which is worth doing once and saving.
#
# Made by `project.new_table("mart.job_day_facts", template="as_of_lookup")`, then filled in,
# writing its last 3 days on each run, as mart.job_day_costs does. Its rows come from the
# Building block `building_blocks/events_per_job_day.py`, joined to the day's team by
# `building_blocks/owner_on_day.py`. A day with no snapshot in ops.job_owners keeps its numbers
# with a NULL team.
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
# 2. The logic: imports, the days it writes, and functions only
from sqlglot_composer import (
    FROM, INSERT_OVERWRITE, SELECT, Clause, Statement, create_table, statement,
)
from building_blocks.days_rewritten import first_day_written
from building_blocks.events_per_job_day import events_per_job_day
from building_blocks.owner_on_day import owner_on_day
from references.mart__job_day_facts import job_day_facts
from references.ops__job_owners import job_owners

DAY = "2026-09-24"  # the last day write() writes, the Example database's last day


def create() -> Statement:
    """Step 1: create mart.job_day_facts from its Table reference, if it isn't there yet."""
    return create_table(job_day_facts, may_exist=True)


def rows(first_day: str, last_day: str) -> list[Clause]:
    """The clauses every step below shares: each job's day beside its team that day. The day
    comes last in SELECT: INSERT_OVERWRITE writes each day's rows into that day's Partition."""
    events = events_per_job_day(first_day, last_day)
    return [
        SELECT(events.job_id, job_owners.team, events.events, events.runs, events.minutes,
               events.dt),
        FROM(events),
        owner_on_day(events.job_id, events.dt, first_day=first_day, last_day=last_day),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows(first_day_written(DAY), DAY))


def write_days(first_day: str, last_day: str) -> Statement:
    """Every day from first_day to last_day, in one write; owner_on_day matches each day to
    that day's snapshot."""
    return statement(INSERT_OVERWRITE(job_day_facts), *rows(first_day, last_day))


def write() -> Statement:
    """Step 3, every run: the last 3 days, ending on DAY, in one write."""
    return write_days(first_day_written(DAY), DAY)

# %%
# 3. Try it: the Hive of each step, then the rows write() saves
show_hive([create(), write()])
run(preview(), query=query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. The Reference sheet: this table's rows, from references/mart__job_day_facts.py
project.refresh_reference_sheet("mart.job_day_facts")
