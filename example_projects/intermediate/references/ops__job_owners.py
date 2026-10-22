"""ops.job_owners - one row per job per day: the team and owner it had that day.

Why: the project's notebooks read the table through this file, so each column they name, and the
key each join and count relies on, where it has one, is checked as the Statement is built.

project.add_references wrote this file from the table's DESCRIBE, its partition columns, if any,
among it. Its three TODO lines were then filled in by hand: this docstring's first line, the
key, and does_not_add_up.
"""
from sqlglot_composer import Table

job_owners = Table(
    "ops.job_owners",
    columns={
        "job_id": "bigint",
        "team": "string",
        "owner": "string",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["job_id", "dt"],  # filled in by hand
    # filled in by hand: none of the columns is an average, a ratio or a distinct count
    does_not_add_up=[],
    descriptions={
        "owner": "NULL when nobody owns the job",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.ops__job_owners import job_owners, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_owners.team
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_owners.team, <value>)
