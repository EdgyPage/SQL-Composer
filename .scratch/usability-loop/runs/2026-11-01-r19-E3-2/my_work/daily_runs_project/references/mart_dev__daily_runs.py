"""mart_dev.daily_runs - one row per day of the clean runs, with no-status and TEST runs left out."""
from sqlglot_composer import Table

daily_runs = Table(
    "mart_dev.daily_runs",
    columns={
        "dt": "string",
        "runs": "bigint",
        "total_duration_mins": "bigint",
    },
    key=["dt"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/mart_dev.db/daily_runs",
    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__daily_runs import daily_runs, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = daily_runs.dt
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(daily_runs.dt, <value>)
