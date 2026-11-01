"""mart_dev.failed_runs - one job that had failed runs: its id, and how many of its runs failed."""
from sqlglot_composer import Table

failed_runs = Table(
    "mart_dev.failed_runs",
    columns={
        "job_id": "bigint",
        "fails": "bigint",
    },
    key=["job_id"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/mart_dev.db/failed_runs",
    does_not_add_up=[],  # none: fails is a count of runs, which adds up across jobs
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__failed_runs import failed_runs, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = failed_runs.fails
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(failed_runs.fails, <value>)
