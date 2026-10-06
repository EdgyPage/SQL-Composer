# sqlglot Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy
"""mart.daily_job_runs - one row per job and day: runs, failed runs and minutes.

Why: example 1 saves these numbers once a day, so example 3 and anyone else can read them
without counting every run again.

A Saved table's Table reference is written by hand, since the table doesn't exist until
create_table makes it from this file.
"""

from sqlglot_composer import Table

daily_job_runs = Table(
    "mart.daily_job_runs",
    columns={
        "job_id": "bigint",
        "runs": "bigint",
        "failed_runs": "bigint",
        "minutes": "bigint",  # the minutes of all the job's runs that day
        "dt": "string",  # the day of the runs, as yyyy-MM-dd
    },
    date_partition="dt",
    key=["job_id", "dt"],
)
