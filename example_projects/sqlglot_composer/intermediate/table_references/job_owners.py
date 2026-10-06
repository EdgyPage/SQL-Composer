# sqlglot Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy
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
        "owner": "string",  # NULL when nobody owns the job
        "dt": "string",
    },
    date_partition="dt",
    key=["job_id", "dt"],  # filled in by hand
    # filled in by hand: none of the columns is an average, a ratio or a distinct count
    does_not_add_up=[],
)
