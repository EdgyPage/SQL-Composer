"""mart_dev.job_costs - one job: its cost in cents, its runs' minutes times cents_a_minute, job 3 typed over as agreed"""
from sqlglot_composer import Table

job_costs = Table(
    "mart_dev.job_costs",
    columns={
        "job_id": "int",
        "cost_cents": "bigint",
    },
    key=["job_id"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/mart_dev.db/job_costs",
    does_not_add_up=[],  # none: each column is a total or a count
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__job_costs import job_costs, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_costs.cost_cents
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_costs.cost_cents, <value>)
