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

# Rebuilt or History: "rebuilt" if each write replaces the whole table; "history" if
# each write keeps the rows already there, adding rows or replacing some, such as one
# day's Partition, so the table needs its past rows loaded first, its Seed. Answer
# "kind" in the decisions cell: "proposed" accepts the kind proposed below.
KIND = "history"  # answered, proposed history: its INSERT OVERWRITE replaces one Partition, keeping the others

# The Seed: if this is a History table, the past rows loaded once, before its first
# write. Answer "seed" in the decisions cell: {"months": 1} loads one month back from
# the newest Partition, by the partition column whose every value is a date; or, by
# partition column, a value, that value or later, a range {"from": ..., "to": ...}, or a
# list, those values alone; {} loads every Partition. A Rebuilt table has no Seed.
SEED = {}  # TODO: nothing proposed: project.upgrade() reads no Partitions, so nothing says which partition column, if any, holds dates

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table, such as:
#     from references.mart__budget_overruns import budget_overruns, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = budget_overruns.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(budget_overruns.<column>, <value>)
