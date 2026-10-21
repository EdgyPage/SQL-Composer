"""ops.job_owners - one row per job per day: the team and owner it had that day.

Why: the project's Statements read the table through this file, so each column they name, and
the key each join and count relies on, is checked as the Statement is built.

write_table_reference wrote this file from the table's DESCRIBE and SHOW PARTITIONS. Its three
TODO lines were then filled in by hand: this docstring's first line, the key, and
does_not_add_up.
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
    date_partition="dt",
    key=["job_id", "dt"],  # filled in by hand
    # filled in by hand: none of the columns is an average, a ratio or a distinct count
    does_not_add_up=[],
    descriptions={
        "owner": "NULL when nobody owns the job",
    },
)

# --- Aliases ----------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below this heading.
# Import one beside the table: from references.ops__job_owners import job_owners, <alias>
#
# A column Alias is a plainer name for one column. It is only a shorter name: the Hive, the
# output and the lineage still say the column's own name. To name an output, use AS(...).
#     <alias> = job_owners.job_id
# A condition Alias names a condition on this table alone, for WHERE or count_rows(where=...).
# Add what it calls, such as equals, to the import from sqlglot_composer above.
#     <alias> = equals(job_owners.job_id, <value>)
