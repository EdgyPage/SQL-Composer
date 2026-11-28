"""mart.team_failures - one row per team and day: its events and its fails.

Why: the project's notebooks read the table through this file, so each column they name, and
the key each join and count relies on, is checked as the Statement is built.

Written by project.convert("team_failures", ...), from the ops team's Hive, its key
proposed from the Hive's GROUP BY, then filled in by hand: this line, the two column types
and the location.
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
    key=["team", "dt"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/mart.db/team_failures",  # filled in by hand
)

# Rebuilt or History: "rebuilt" if each write replaces the whole table; "history" if
# each write keeps the rows already there, adding rows or replacing some, such as one
# day's Partition, so the table needs its past rows loaded first, its Seed. Answer
# "kind" in the decisions cell: "proposed" accepts the kind proposed below.
KIND = None  # TODO: nothing proposed: its INSERT OVERWRITE fills dt from its rows' own values, PARTITION (dt), so it may replace every Partition or only some
