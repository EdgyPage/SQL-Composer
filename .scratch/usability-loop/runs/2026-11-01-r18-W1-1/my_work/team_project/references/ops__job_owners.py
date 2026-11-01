"""ops.job_owners - one row is the team and owner of one job on one day."""
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
    key=["job_id", "dt"],
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
