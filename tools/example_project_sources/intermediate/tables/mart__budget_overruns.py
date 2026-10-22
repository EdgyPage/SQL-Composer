# %% [markdown]
# # mart.budget_overruns
#
# Each job's budget in each region it is billed in, and how many of its days cost more, saved
# a region at a time.
#
# Why: a region's budget holder reads only that region's rows, so the table is partitioned by
# region, and each region's Partition is written on its own.
#
# Made by `project.new_table("mart.budget_overruns")` from `admin/templates/saved_table.py`,
# then filled in. Its write() gives one write per region, each naming its Partition with
# `partition={"region": ...}`: the region is then a value of the write, not a column of its
# SELECT, and each write replaces that region's Partition alone. ops.region_costs writes its
# days like 20260924, so FIRST_DAY and LAST_DAY are written its way by `as_written_here`, from
# `building_blocks/costs_per_job.py`. A bill not in yet, NULL, is never over budget.
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
# 2. The logic: imports, the regions and days it writes, and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, JOIN, SELECT, WHERE, Clause, Statement, all_of,
    between, count_rows, create_table, equals, more_than, statement,
)
from building_blocks.costs_per_job import as_written_here
from references.mart__budget_overruns import budget_overruns
from references.ops__region_budgets import region_budgets
from references.ops__region_costs import region_costs

REGIONS = ["eu", "us"]  # the Partitions write() writes, one write each
FIRST_DAY = "2026-09-11"  # the days of ops.region_costs it counts: the Example database's 14
LAST_DAY = "2026-09-24"


def create() -> Statement:
    """Step 1: create mart.budget_overruns from its Table reference, if it isn't there yet."""
    return create_table(budget_overruns, may_exist=True)


def rows(region: str) -> list[Clause]:
    """One region's rows, the clauses preview and write share: each job billed there, its
    budget, its days and the days it went over. Both tables are partitioned by region, so each
    filters it, region_budgets in JOIN's ON=; region_costs filters its dt too."""
    return [
        SELECT(
            region_costs.job_id,
            region_budgets.budget_cents,
            AS(count_rows(), "days"),
            AS(count_rows(where=more_than(region_costs.cost_cents,
                                          region_budgets.budget_cents)), "days_over"),
        ),
        FROM(region_costs),
        JOIN(region_budgets, ON=all_of(equals(region_budgets.job_id, region_costs.job_id),
                                       equals(region_budgets.region, region))),
        WHERE(equals(region_costs.region, region),
              between(region_costs.dt, as_written_here(FIRST_DAY), as_written_here(LAST_DAY))),
        GROUP_BY(region_costs.job_id, region_budgets.budget_cents),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save in the first region, as a SELECT to run and check
    first."""
    return statement(*rows(REGIONS[0]))


def write() -> list[Statement]:
    """Step 3: a write per region, each replacing that region's Partition alone."""
    return [statement(INSERT_OVERWRITE(budget_overruns, partition={"region": region}),
                      *rows(region))
            for region in REGIONS]

# %%
# 3. Try it: the Hive of each step, then the first region's rows
show_hive([create(), *write()])
run(preview(), query=query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(*write())

# %%
# 5. The Reference sheet: this table's rows, from references/mart__budget_overruns.py
project.refresh_reference_sheet("mart.budget_overruns")
