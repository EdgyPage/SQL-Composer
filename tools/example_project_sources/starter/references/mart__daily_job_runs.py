"""mart.daily_job_runs - one row per job and day: runs, failed runs and minutes.

Why: its notebook saves these numbers once a day, so mart.team_day and anyone else can read
them without counting every run again.

project.new_table wrote this file from admin/templates/saved_table_reference.py; it was
filled in by hand, since the table doesn't exist until its notebook's create() makes it.
"""

from sqlglot_composer import Table

daily_job_runs = Table(
    "mart.daily_job_runs",
    columns={
        "job_id": "bigint",
        "runs": "bigint",
        "failed_runs": "bigint",
        "minutes": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["job_id", "dt"],
    location="/data/your_team/mart.db/daily_job_runs",  # its own folder
    descriptions={
        "runs": "every run of the job that day, TEST runs among them",
        "failed_runs": "its runs whose status is FAILED",
        "minutes": "the minutes of all the job's runs that day",
        "dt": "the day of the runs, as yyyy-MM-dd",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table, such as:
#     from references.mart__daily_job_runs import daily_job_runs, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
# gives back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = daily_job_runs.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(daily_job_runs.<column>, <value>)
