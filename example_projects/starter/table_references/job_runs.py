"""ops.job_runs - one row per run of a job, on the day it ran.

Why: the project's Statements read the table through this file, so each column they name, and
the key each join and count relies on, is checked as the Statement is built.

write_table_reference wrote this file from the table's DESCRIBE and SHOW PARTITIONS. Its three
TODO lines were then filled in by hand: this docstring's first line, the key, and
does_not_add_up.
"""
from sqlglot_composer import Table

job_runs = Table(
    "ops.job_runs",
    columns={
        "run_id": "bigint",
        "job_id": "bigint",
        "status": "string",  # SUCCESS / FAILED / TEST, NULL while running
        "duration_mins": "int",
        "avg_retry_secs": "double",
        "dt": "string",
    },
    date_partition="dt",
    key=["run_id"],  # filled in by hand
    # filled in by hand: summing these gives a wrong total, since avg_retry_secs is an average
    does_not_add_up=["avg_retry_secs"],
)
