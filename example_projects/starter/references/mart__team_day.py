# sqlglot Composer 6.0, exported 2026-10-21 07:24 - copy it, then edit your copy
"""mart.team_day - one row per team and day: runs, failed runs, minutes, alerts.

Why: its notebook saves each team's day here, made from what mart.daily_job_runs and
mart.alerts_per_job saved, so a Statement about teams reads a few rows instead of every run and
alert.

project.new_table wrote this file from admin/templates/saved_table_reference.py; it was
filled in by hand, since the table doesn't exist until its notebook's create() makes it.
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
        "dt": "string",
    },
    date_partition="dt",
    key=["team", "dt"],
    location="/data/your_team/tables",  # the folder your Saved tables go in
    descriptions={
        "team": "the team that owns the jobs",
        "alerts": "0 when the team's runs raised none",
        "dt": "the day, as yyyy-MM-dd",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table, such as:
#     from references.mart__team_day import team_day, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
# gives back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = team_day.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(team_day.<column>, <value>)
