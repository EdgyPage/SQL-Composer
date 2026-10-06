# Spark Composer 4.0, exported 2026-10-06 00:26 - copy it, then edit your copy
"""mart.alerts_per_job - one row per job and day with alerts: alerts, high alerts.

Why: example 2 saves these numbers once a day, so example 3 and anyone else can read them
without joining every alert to its run again.

A Saved table's Table reference is written by hand, since the table doesn't exist until
create_table makes it from this file. A job whose runs raised no alert that day has no row.
"""

from spark_composer import Table

alerts_per_job = Table(
    "mart.alerts_per_job",
    columns={
        "job_id": "bigint",
        "alerts": "bigint",
        "high_alerts": "bigint",
        "dt": "string",  # the day of the alerts, as yyyy-MM-dd
    },
    date_partition="dt",
    key=["job_id", "dt"],
)
