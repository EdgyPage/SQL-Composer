"""mart_dev.team_fails - one row is one team's failed job runs on one day, by dt."""
from sqlglot_composer import Table

team_fails = Table(
    "mart_dev.team_fails",
    columns={
        "team": "string",
        "fails": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["team", "dt"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/mart_dev.db/team_fails",
    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__team_fails import team_fails, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = team_fails.team
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(team_fails.team, <value>)
