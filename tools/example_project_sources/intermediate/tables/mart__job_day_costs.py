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
# the project's other tables do, so mart.team_days can join it to them on the day.
#
# The code cells: 1 the Project and your send; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet.

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
# 2. The logic: imports and functions only
from sqlglot_composer import (
    FROM, INSERT_OVERWRITE, SELECT, Clause, Statement, by_day, create_table, statement,
)
from building_blocks.costs_per_job_day import costs_per_job_day
from building_blocks.days_rewritten import first_day_written
from references.mart__job_day_costs import job_day_costs


def create() -> Statement:
    """Step 1: create mart.job_day_costs from its Table reference, if it isn't there yet."""
    return create_table(job_day_costs, may_exist=True)


def rows(first_day: str, last_day: str) -> list[Clause]:
    """The clauses every step below shares: each job's cost per day. The day isn't selected:
    INSERT_OVERWRITE writes it as this table's Date partition, written its own way."""
    costs = costs_per_job_day(first_day, last_day)
    return [SELECT(costs.job_id, costs.cost_cents), FROM(costs)]


def preview(day: str) -> Statement:
    """Step 2: the rows a write of the day would save, as a SELECT to run and check first."""
    return statement(*rows(day, day))


def write_days(first_day: str, last_day: str) -> list[Statement]:
    """One write per day from first_day to last_day, oldest first: also a backfill, given an
    earlier first_day."""
    return by_day(statement(INSERT_OVERWRITE(job_day_costs), *rows(first_day, last_day)))


def write_day(day: str) -> list[Statement]:
    """Step 3, every run: the writes of the last 3 days, ending on the day, as a list, oldest
    first, so cell 3 passes them on as *write_day(DAY). run_tables sends each in turn."""
    return write_days(first_day_written(day), day)

# %%
# 3. Try it: the Hive of each step, then the day's rows
show_hive([create(), *write_day(DAY)])
run(preview(DAY), send=send)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(*write_day(DAY))

# %%
# 5. The Reference sheet: this table's rows, from references/mart__job_day_costs.py
project.refresh_reference_sheet("mart.job_day_costs")
