"""mart_dev.job_costs - TODO: say in one line what one row is."""
from sqlglot_composer import Table

job_costs = Table(
    "mart_dev.job_costs",
    columns={
        "job_id": "bigint",
        "cost_cents": "bigint",
    },
    key=["job_id"],
    location="/data/team/mart_dev.db/job_costs",
    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
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
