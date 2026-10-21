"""ops.jobs - one row per job: its name, the team that owns it and its region.

Why: the project's notebooks read the table through this file, so each column they name, and the
key each join and count relies on, is checked as the Statement is built.

project.add_references wrote this file from the table's DESCRIBE and SHOW PARTITIONS. Its three
TODO lines were then filled in by hand: this docstring's first line, the key, and
does_not_add_up.
"""
from sqlglot_composer import Table

jobs = Table(
    "ops.jobs",
    columns={
        "job_id": "bigint",
        "job_name": "string",
        "team": "string",
        "region": "string",
    },
    date_partition=None,
    key=["job_id"],  # filled in by hand
    # filled in by hand: none of the columns is an average, a ratio or a distinct count
    does_not_add_up=[],
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.ops__jobs import jobs, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
# gives back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = jobs.job_name
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(jobs.job_name, <value>)
