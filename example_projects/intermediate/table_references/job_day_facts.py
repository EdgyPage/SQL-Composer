"""mart.job_day_facts - one row per job and day it ran, with that day's team.

Why: example 2 saves each job's day here with the team that owned the job that day, so a
Statement about teams counts each day for the team it belonged to then, not the team today.

A Saved table's Table reference is written by hand, since the table doesn't exist until
create_table makes it from this file.
"""

from sqlglot_composer import Table

job_day_facts = Table(
    "mart.job_day_facts",
    columns={
        "job_id": "bigint",
        "team": "string",  # the team that owned the job that day; NULL if no snapshot says
        "events": "bigint",
        "runs": "bigint",
        "minutes": "bigint",  # the minutes of the runs that ended that day
        "dt": "string",  # the day, as yyyy-MM-dd
    },
    date_partition="dt",
    key=["job_id", "dt"],
)
