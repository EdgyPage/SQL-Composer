# Spark Composer 4.0, exported 2026-10-06 00:26 - copy it, then edit your copy
"""ops.run_alerts - one row per alert a run raised.

Why: the project's Statements read the table through this file, so each column they name, and
the key each join and count relies on, is checked as the Statement is built.

write_table_reference wrote this file from the table's DESCRIBE and SHOW PARTITIONS. Its three
TODO lines were then filled in by hand: this docstring's first line, the key, and
does_not_add_up.
"""
from spark_composer import Table

run_alerts = Table(
    "ops.run_alerts",
    columns={
        "alert_id": "bigint",
        "run_id": "bigint",
        "severity": "string",  # low / high
        "dt": "string",
    },
    date_partition="dt",
    key=["alert_id"],  # filled in by hand
    # filled in by hand: none of the columns is an average, a ratio or a distinct count
    does_not_add_up=[],
)
