"""mart_dev.team_fails - One row per team and dt: its failed runs that day, counted by team."""
from sqlglot_composer import Table

team_fails = Table(
    "mart_dev.team_fails",
    columns={
        "team": "string",
        "fails": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["team", "dt"],
    location="/data/team/mart_dev.db/team_fails",  # under its Database's location_root, in admin/databases.py
    does_not_add_up=[],  # no column is an average, ratio or distinct count: they are counts of rows
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
