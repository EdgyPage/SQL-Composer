# Spark Composer 4.0, exported 2026-10-06 00:26 - copy it, then edit your copy
"""ops.region_costs - one row per job, region and day: its cost there, in cents.

Why: the project's Statements read the table through this file, so each column they name, and
the key each join and count relies on, is checked as the Statement is built.

write_table_reference wrote this file from the table's DESCRIBE and SHOW PARTITIONS. The table's
first partition, region, holds no day, so it left the Date partition as a TODO too. Its four
TODO lines were then filled in by hand: this docstring's first line, the Date partition, dt,
with the way it writes its days, the key, and does_not_add_up.
"""
from spark_composer import Table

region_costs = Table(
    "ops.region_costs",
    columns={
        "job_id": "bigint",
        "cost_cents": "bigint",  # NULL until the bill comes in
        "region": "string",
        "dt": "string",
    },
    # filled in by hand: region, the first partition, holds no day; the Date partition,
    # dt, holds the days, written like 20260911
    date_partition="dt",
    date_format="%Y%m%d",
    key=["job_id", "region", "dt"],  # filled in by hand
    # filled in by hand: none of the columns is an average, a ratio or a distinct count
    does_not_add_up=[],
)
