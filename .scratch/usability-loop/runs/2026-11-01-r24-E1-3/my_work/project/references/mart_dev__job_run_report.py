"""mart_dev.job_run_report - one row per job_id: its runs, its failed runs and its average minutes."""
from sqlglot_composer import Table

job_run_report = Table(
    "mart_dev.job_run_report",
    columns={
        "job_id": "int",
        "runs": "bigint",
        "failed_runs": "bigint",
        "avg_duration_mins": "double",
    },
    key=["job_id"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/mart_dev.db/job_run_report",
    does_not_add_up=["avg_duration_mins"],  # an average: it does not add up across jobs
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__job_run_report import job_run_report, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_run_report.runs
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_run_report.runs, <value>)
