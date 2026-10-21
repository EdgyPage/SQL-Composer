# sqlglot Composer 6.0, exported 2026-10-21 07:24 - copy it, then edit your copy
"""ops.region_costs - one row per job, region and day: its cost there, in cents.

Why: the project's notebooks read the table through this file, so each column they name, and the
key each join and count relies on, is checked as the Statement is built.

project.add_references wrote this file from the table's DESCRIBE and SHOW PARTITIONS. The
table's first partition, region, holds no day, so it left the Date partition as a TODO too. Its
four TODO lines were then filled in by hand: this docstring's first line, the Date partition,
dt, with the way it writes its days, the key, and does_not_add_up.
"""
from sqlglot_composer import Table

region_costs = Table(
    "ops.region_costs",
    columns={
        "job_id": "bigint",
        "cost_cents": "bigint",
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
    descriptions={
        "cost_cents": "NULL until the bill comes in",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.ops__region_costs import region_costs, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
# gives back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = region_costs.cost_cents
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(region_costs.cost_cents, <value>)
