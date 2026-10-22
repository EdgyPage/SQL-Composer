"""ops.job_runs - one row per run of a job, on the day it ran.

Why: the project's notebooks read the table through this file, so each column they name, and the
key each join and count relies on, is checked as the Statement is built.

project.add_references wrote this file from the table's DESCRIBE, its partition columns among
it. Its three TODO lines were then filled in by hand: this docstring's first line, the key, and
does_not_add_up.
"""
from sqlglot_composer import Table, equals

job_runs = Table(
    "ops.job_runs",
    columns={
        "run_id": "bigint",
        "job_id": "bigint",
        "status": "string",
        "duration_mins": "int",
        "avg_retry_secs": "double",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["run_id"],  # filled in by hand
    # filled in by hand: summing these gives a wrong total, since avg_retry_secs is an average
    does_not_add_up=["avg_retry_secs"],
    descriptions={
        "status": "SUCCESS / FAILED / TEST, NULL while running",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.ops__job_runs import job_runs, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
# gives back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_runs.status
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_runs.status, <value>)

minutes = job_runs.duration_mins
failed = equals(job_runs.status, "FAILED")
