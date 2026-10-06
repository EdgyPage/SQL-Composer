# Spark Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy
"""ops.job_events - one row per event of a run: start, retry, finish or fail.

Why: the project's Statements read the table through this file, so each column they name, and
the key each join and count relies on, is checked as the Statement is built.

write_table_reference wrote this file from the table's DESCRIBE and SHOW PARTITIONS. Its three
TODO lines were then filled in by hand: this docstring's first line, the key, and
does_not_add_up.
"""
from spark_composer import Table

job_events = Table(
    "ops.job_events",
    columns={
        "event_id": "bigint",
        "job_id": "bigint",
        "event_type": "string",  # start / finish / retry / fail
        "minutes": "int",  # minutes since the run started
        "dt": "string",
    },
    date_partition="dt",
    key=["event_id"],  # filled in by hand
    # filled in by hand: none of the columns is an average, a ratio or a distinct count
    does_not_add_up=[],
)
