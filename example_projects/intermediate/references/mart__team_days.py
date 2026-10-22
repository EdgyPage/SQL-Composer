# sqlglot Composer 7.1, exported 2026-10-22 13:22 - copy it, then edit your copy
"""mart.team_days - one row per team and day: its events, runs, minutes and cost.

Why: its notebook saves each team's day, made from what mart.job_day_costs and
mart.job_day_facts saved, and week_totals adds its days up into weeks.

project.new_table wrote this file from admin/templates/saved_table_reference.py; it was
filled in by hand, since the table doesn't exist until its notebook's create() makes it.
"""

from sqlglot_composer import Table

team_days = Table(
    "mart.team_days",
    columns={
        "team": "string",
        "events": "bigint",
        "runs": "bigint",
        "minutes": "bigint",
        "cost_cents": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["team", "dt"],
    location="/data/your_team/mart.db/team_days",  # its own folder
    descriptions={
        "team": "NULL for the jobs whose day had no snapshot to say",
        "cost_cents": "NULL while none of the team's bills for the day has come in",
        "dt": "the day, as yyyy-MM-dd",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table, such as:
#     from references.mart__team_days import team_days, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = team_days.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(team_days.<column>, <value>)
