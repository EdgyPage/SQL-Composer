"""mart_dev.job_fails_counted - One row per job_id and dt: the failed runs of that job that day."""
from sqlglot_composer import Table

job_fails_counted = Table(
    "mart_dev.job_fails_counted",
    columns={
        "job_id": "bigint",
        "fails": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["job_id", "dt"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/mart_dev.db/job_fails_counted",  # under its Database's location_root, in admin/databases.py
    does_not_add_up=[],  # none: each column is a count, which adds up
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__job_fails_counted import job_fails_counted, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_fails_counted.fails
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_fails_counted.fails, <value>)
