"""mart_dev.team_report - one row is one team: its runs and the minutes they took."""
from sqlglot_composer import Table

team_report = Table(
    "mart_dev.team_report",
    columns={
        "team": "string",
        "runs": "bigint",
        "total_duration_mins": "bigint",
    },
    key=["team"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/mart_dev.db/team_report",
    does_not_add_up=[],  # no column is an average, ratio or distinct count: both are sums or counts
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__team_report import team_report, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = team_report.team
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(team_report.team, <value>)
