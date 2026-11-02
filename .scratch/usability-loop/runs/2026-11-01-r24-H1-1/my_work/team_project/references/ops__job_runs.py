"""ops.job_runs - TODO: say in one line what one row is."""
from sqlglot_composer import Table

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
    key=None,  # TODO: the columns that pick out one row, such as key=["run_id"]
    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
    descriptions={
        "status": "SUCCESS / FAILED / TEST, NULL while running",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.ops__job_runs import job_runs, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_runs.status
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_runs.status, <value>)
