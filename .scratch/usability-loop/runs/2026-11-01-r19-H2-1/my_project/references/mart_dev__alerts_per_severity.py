"""mart_dev.alerts_per_severity - one row per severity and day: the alerts raised."""
from sqlglot_composer import Table

alerts_per_severity = Table(
    "mart_dev.alerts_per_severity",
    columns={
        "severity": "string",
        "alerts": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["severity", "dt"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/mart_dev.db/alerts_per_severity",
    does_not_add_up=[],
    descriptions={
        "severity": "low / high, as ops.run_alerts holds it",
        "alerts": "the alerts of that severity raised that day",
        "dt": "the day the alerts were raised, as yyyy-MM-dd",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__alerts_per_severity import alerts_per_severity, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = alerts_per_severity.severity
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(alerts_per_severity.severity, <value>)
