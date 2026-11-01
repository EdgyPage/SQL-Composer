"""ops.run_alerts - one row is one alert, named by its alert_id, raised on one run."""
from sqlglot_composer import Table

run_alerts = Table(
    "ops.run_alerts",
    columns={
        "alert_id": "bigint",
        "run_id": "bigint",
        "severity": "string",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["alert_id"],
    does_not_add_up=[],  # none of its columns is an average, a ratio or a distinct count
    descriptions={
        "severity": "low / high",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.ops__run_alerts import run_alerts, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = run_alerts.severity
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(run_alerts.severity, <value>)
