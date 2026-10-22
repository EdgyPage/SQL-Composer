# %% [markdown]
# # mart.job_day_costs
#
# Each job's cost per day, the last 3 days saved again on every run.
#
# Why: a day's bill can come in after the day was saved, so each run saves the last few days
# again, and a day saved twice must hold the same rows, not twice as many.
#
# Made by `project.new_table("mart.job_day_costs", template="incremental_load")`, then filled
# in. Its rows come from the Building block `building_blocks/costs_per_job_day.py`, and the days
# each run writes from `building_blocks/days_rewritten.py`, which each counting table of the
# project shares. A bill lands in the partition of the day it is for, but can come in later:
# invoice_sync's (job 2's) for 2026-09-24 is still NULL in ops.region_costs, and the next run
# that writes the day again saves it.
#
# ops.region_costs writes its days like 20260924; this table writes them like 2026-09-24, as
# the project's other tables do, so mart.team_days can join it to them on the day: the Building
# block writes each day the project's way.
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
from building_blocks.costs_per_job_day import costs_per_job_day
from building_blocks.days_rewritten import first_day_written
from references.mart__job_day_costs import job_day_costs

DAY = "2026-09-24"  # the last day write() writes, the Example database's last day


def create() -> Statement:
    """Step 1: create mart.job_day_costs from its Table reference, if it isn't there yet."""
    return create_table(job_day_costs, may_exist=True)


def rows(first_day: str, last_day: str) -> list[Clause]:
    """The clauses every step below shares: each job's cost per day. The day comes last in
    SELECT: INSERT_OVERWRITE writes each day's rows into that day's Partition, and replaces
    only the days the rows hold."""
    costs = costs_per_job_day(first_day, last_day)
    return [SELECT(costs.job_id, costs.cost_cents, costs.dt), FROM(costs)]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows(first_day_written(DAY), DAY))


def write_days(first_day: str, last_day: str) -> Statement:
    """Every day from first_day to last_day, in one write: also a backfill, given an earlier
    first_day."""
    return statement(INSERT_OVERWRITE(job_day_costs), *rows(first_day, last_day))


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
# 5. The Reference sheet: this table's rows, from references/mart__job_day_costs.py
project.refresh_reference_sheet("mart.job_day_costs")
