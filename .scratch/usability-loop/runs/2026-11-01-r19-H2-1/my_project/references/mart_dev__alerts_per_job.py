"""mart_dev.alerts_per_job - one row per job and day with alerts: alerts, high alerts."""
from sqlglot_composer import Table

alerts_per_job = Table(
    "mart_dev.alerts_per_job",
    columns={
        "job_id": "bigint",
        "alerts": "bigint",
        "high_alerts": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["job_id", "dt"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/mart_dev.db/alerts_per_job",
    does_not_add_up=[],
    descriptions={
        "alerts": "every alert the job's runs raised that day",
        "high_alerts": "those whose severity is high",
        "dt": "the day the alerts were raised, as yyyy-MM-dd",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__alerts_per_job import alerts_per_job, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = alerts_per_job.alerts
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(alerts_per_job.alerts, <value>)
