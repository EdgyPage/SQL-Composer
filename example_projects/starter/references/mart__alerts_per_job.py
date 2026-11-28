"""mart.alerts_per_job - one row per job and day with alerts: alerts, high alerts.

Why: its notebook saves these numbers once a day, so mart.team_day and anyone else can read
them without joining every alert to its run again.

A job whose runs raised no alert that day has no row.

project.new_table wrote this file from admin/templates/saved_table_reference.py; it was
filled in by hand, since the table doesn't exist until its notebook's create() makes it.
"""

from sqlglot_composer import Table

alerts_per_job = Table(
    "mart.alerts_per_job",
    columns={
        "job_id": "bigint",
        "alerts": "bigint",
        "high_alerts": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["job_id", "dt"],
    location="/data/your_team/mart.db/alerts_per_job",  # its own folder
    descriptions={
        "alerts": "every alert the job's runs raised that day",
        "high_alerts": "those whose severity is high",
        "dt": "the day the alerts were raised, as yyyy-MM-dd",
    },
)

# Rebuilt or History: "rebuilt" if each write replaces the whole table; "history" if
# each write keeps the rows already there, adding rows or replacing some, such as one
# day's Partition, so the table needs its past rows loaded first, its Seed. Answer
# "kind" in the decisions cell: "proposed" accepts the kind proposed below.
KIND = None  # TODO: nothing proposed: its INSERT OVERWRITE fills dt from its rows' own values, PARTITION (dt), so it may replace every Partition or only some

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table, such as:
#     from references.mart__alerts_per_job import alerts_per_job, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = alerts_per_job.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(alerts_per_job.<column>, <value>)
