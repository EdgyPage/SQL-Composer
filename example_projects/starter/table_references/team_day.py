"""mart.team_day - one row per team and day: runs, failed runs, minutes, alerts.

Why: example 3 saves each team's day here, made from what examples 1 and 2 saved, so a
Statement about teams reads a few rows instead of every run and alert.

A Saved table's Table reference is written by hand, since the table doesn't exist until
create_table makes it from this file.
"""

from sqlglot_composer import Table

team_day = Table(
    "mart.team_day",
    columns={
        "team": "string",
        "runs": "bigint",
        "failed_runs": "bigint",
        "minutes": "bigint",
        "alerts": "bigint",
        "high_alerts": "bigint",
        "dt": "string",  # the day, as yyyy-MM-dd
    },
    date_partition="dt",
    key=["team", "dt"],
)
