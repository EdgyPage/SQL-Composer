"""mart.job_events_checks - one row per day: ops.job_events' row count that day.

Why: its notebook saves each day's count, so a day of ops.job_events that came in short shows
beside the days around it.

project.new_table wrote this file from admin/templates/saved_table_reference.py; it was
filled in by hand, since the table doesn't exist until its notebook's create() makes it.
"""

from sqlglot_composer import Table

job_events_checks = Table(
    "mart.job_events_checks",
    columns={
        "row_count": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["dt"],
    location="/data/your_team/mart.db/job_events_checks",  # its own folder
    descriptions={
        "row_count": "ops.job_events' rows that day",
        "dt": "the day counted, as yyyy-MM-dd",
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
#     from references.mart__job_events_checks import job_events_checks, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_events_checks.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_events_checks.<column>, <value>)
