"""mart.team_failures - one row per team and day: its events, and how many were fails.

Written by project.finish_conversion("team_failures", table="mart.team_failures"), from the
ops team's Hive, then filled in by hand: this line, the two column types, the key and the
location.
"""

from sqlglot_composer import Table

team_failures = Table(
    "mart.team_failures",
    columns={
        "team": "string",
        "team_name": "string",  # filled in by hand
        "events": "bigint",
        "fails": "bigint",  # filled in by hand
        "dt": "string",
    },
    partitioned_by=["dt"],  # filled in from the original's PARTITION(...)
    key=["team", "dt"],  # filled in by hand
    location="/data/mart.db/team_failures",  # filled in by hand
)
