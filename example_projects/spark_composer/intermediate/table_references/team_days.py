# Spark Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy
"""mart.team_days - one row per team and day: events, runs, minutes and cost.

Why: example 3 saves each team's day here, made from what examples 1 and 2 saved, so each
team's weeks are added up from a few rows instead of every event and bill.

A Saved table's Table reference is written by hand, since the table doesn't exist until
create_table makes it from this file. It holds days, not weeks: a write fills one day of a
Saved table, so example 3's week_totals adds each week's days up when it reads them.
"""

from spark_composer import Table

team_days = Table(
    "mart.team_days",
    columns={
        "team": "string",  # NULL for the jobs whose day had no snapshot to say
        "events": "bigint",
        "runs": "bigint",
        "minutes": "bigint",
        "cost_cents": "bigint",  # NULL while none of the team's bills for the day has come in
        "dt": "string",  # the day, as yyyy-MM-dd
    },
    date_partition="dt",
    key=["team", "dt"],
)
