"""ops.jobs - one row is one job."""
from sqlglot_composer import Table

jobs = Table(
    "ops.jobs",
    columns={
        "job_id": "bigint",
        "job_name": "string",
        "team": "string",
        "region": "string",
    },
    key=["job_id"],
    does_not_add_up=[],  # none: no column here is an average, ratio or distinct count
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.ops__jobs import jobs, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = jobs.job_name
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(jobs.job_name, <value>)
