"""ops.jobs - one row per job: its name, the team that owns it and its region.

Why: the project's Statements read the table through this file, so each column they name, and
the key each join and count relies on, is checked as the Statement is built.

write_table_reference wrote this file from the table's DESCRIBE and SHOW PARTITIONS. Its three
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
    key=["job_id"],
    does_not_add_up=[],
)
