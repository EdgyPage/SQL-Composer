"""mart_dev.runs_per_day - one row per job and day: how many runs that job had that day."""
from sqlglot_composer import Table

runs_per_day = Table(
    "mart_dev.runs_per_day",
    columns={
        "job_id": "bigint",
        "runs": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["job_id", "dt"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/mart_dev.db/runs_per_day",
    does_not_add_up=[],  # a count of runs adds up across jobs and days, so nothing here
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__runs_per_day import runs_per_day, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = runs_per_day.runs
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(runs_per_day.runs, <value>)
