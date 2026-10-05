"""mart.job_day_costs - one row per job and day it was billed: its cost in cents.

Why: example 1 saves each job's cost per day here with its days written like 2026-09-24, as
the other tables write theirs, so a Statement can join the costs to them on the day.

A Saved table's Table reference is written by hand, since the table doesn't exist until
create_table makes it from this file. ops.region_costs writes its days like 20260924; this
table writes them like 2026-09-24, the Toolbox's usual way, so it needs no date_format.
"""

from sqlglot_composer import Table

job_day_costs = Table(
    "mart.job_day_costs",
    columns={
        "job_id": "bigint",
        "cost_cents": "bigint",  # every region's cost added up; NULL until the bill comes in
        "dt": "string",  # the day, as yyyy-MM-dd
    },
    date_partition="dt",
    key=["job_id", "dt"],
)
