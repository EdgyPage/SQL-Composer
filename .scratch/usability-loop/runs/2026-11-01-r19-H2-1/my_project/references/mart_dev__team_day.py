"""mart_dev.team_day - one row per team and day: runs, failed runs and minutes."""
from sqlglot_composer import Table

team_day = Table(
    "mart_dev.team_day",
    columns={
        "team": "string",
        "runs": "bigint",
        "failed_runs": "bigint",
        "minutes": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["team", "dt"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/mart_dev.db/team_day",
    does_not_add_up=[],
    descriptions={
        "team": "the team that owns the jobs",
        "dt": "the day, as yyyy-MM-dd",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__team_day import team_day, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = team_day.team
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(team_day.team, <value>)
