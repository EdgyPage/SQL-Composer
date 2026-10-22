"""mart.budget_overruns - one row per job and region: its budget and days over it.

Why: its notebook saves, for each region, how often each job's daily cost went over its
budget there, so whoever pays for a region reads its own Partition without adding up every
bill again.

It is partitioned by region, the region the job is billed in, as ops.region_budgets is, and
holds no day: each write replaces a region's Partition whole, with the days its notebook's
FIRST_DAY and LAST_DAY name.

project.new_table wrote this file from admin/templates/saved_table_reference.py; it was
filled in by hand, since the table doesn't exist until its notebook's create() makes it.
"""

from sqlglot_composer import Table

budget_overruns = Table(
    "mart.budget_overruns",
    columns={
        "job_id": "bigint",
        "budget_cents": "bigint",
        "days": "bigint",
        "days_over": "bigint",
        "region": "string",
    },
    partitioned_by=["region"],
    key=["job_id", "region"],
    location="/data/your_team/mart.db/budget_overruns",  # its own folder
    descriptions={
        "budget_cents": "the most a day of the job should cost in the region",
        "days": "the days the job has a cost row in the region, its bill in or not",
        "days_over": "those whose cost was more than the budget",
        "region": "where the job is billed: eu or us",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table, such as:
#     from references.mart__budget_overruns import budget_overruns, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
# gives back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = budget_overruns.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(budget_overruns.<column>, <value>)
