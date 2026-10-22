"""mart.alerts_per_severity - one row per severity and day: the alerts raised.

Why: its notebook saves the day's count of low and high alerts, so a dashboard of alerts
reads two rows a day rather than every alert.

project.new_table wrote this file from admin/templates/saved_table_reference.py. A Saved
table's Table reference is filled in by hand, since the table doesn't exist until its
notebook's create() makes it from this file. Its notebook's text cell says which columns it
lists, and its Key.
"""

from sqlglot_composer import Table

alerts_per_severity = Table(
    "mart.alerts_per_severity",
    columns={
        "severity": "string",
        "alerts": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["severity", "dt"],
    location="/data/your_team/mart.db/alerts_per_severity",  # its own folder
    descriptions={
        "severity": "low / high, as ops.run_alerts holds it",
        "alerts": "the alerts of that severity raised that day",
        "dt": "the day the alerts were raised, as yyyy-MM-dd",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart__alerts_per_severity import alerts_per_severity, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
# gives back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = alerts_per_severity.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(alerts_per_severity.<column>, <value>)
