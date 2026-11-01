# A prod copy project.promote made of references/mart_dev__team_report.py: change that one and promote it again. Its
# location= is the one line yours to change here.
"""team_prod.team_report - TODO: say in one line what one row is."""
from sqlglot_composer import Table

team_report = Table(
    "team_prod.team_report",
    columns={
        "team": "string",
        "runs": "bigint",
        "total_duration_mins": "bigint",
    },
    key=["team"],
    location="/data/team/team_prod.db/team_report",
    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.team_prod__team_report import team_report, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = team_report.team
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(team_report.team, <value>)
