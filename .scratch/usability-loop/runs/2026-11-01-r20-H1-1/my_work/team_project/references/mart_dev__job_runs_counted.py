"""mart_dev.job_runs_counted - one row per job per day: how many runs the job had that day."""
from sqlglot_composer import Table

job_runs_counted = Table(
    "mart_dev.job_runs_counted",
    columns={
        "job_id": "bigint",
        "runs": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["job_id", "dt"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/mart_dev.db/job_runs_counted",
    does_not_add_up=[],  # none: every column is a count or a key
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__job_runs_counted import job_runs_counted, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_runs_counted.runs
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_runs_counted.runs, <value>)
