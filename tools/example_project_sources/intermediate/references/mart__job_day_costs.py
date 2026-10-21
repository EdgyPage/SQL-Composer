"""mart.job_day_costs - one row per job and day it was billed: its cost in cents.

Why: its notebook saves each job's cost per day, written like 2026-09-24, so mart.team_days can
join it on the day to the project's other tables; ops.region_costs writes its days like
20260924.

project.new_table wrote this file from admin/templates/saved_table_reference.py; it was
filled in by hand, since the table doesn't exist until its notebook's create() makes it.
"""

from sqlglot_composer import Table

job_day_costs = Table(
    "mart.job_day_costs",
    columns={
        "job_id": "bigint",
        "cost_cents": "bigint",
        "dt": "string",
    },
    date_partition="dt",
    key=["job_id", "dt"],
    location="/data/your_team/tables",  # the folder your Saved tables go in
    descriptions={
        "cost_cents": "every region's cost added up; NULL until the bill comes in",
        "dt": "the day the cost is for, as yyyy-MM-dd",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table, such as:
#     from references.mart__job_day_costs import job_day_costs, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
# gives back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_day_costs.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_day_costs.<column>, <value>)
