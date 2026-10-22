# sqlglot Composer 7.1, exported 2026-10-22 13:22 - copy it, then edit your copy
"""ops.region_costs - one row per job, region and day: its cost there, in cents.

Why: the project's notebooks read the table through this file, so each column they name, and the
key each join and count relies on, where it has one, is checked as the Statement is built.

project.add_references wrote this file from the table's DESCRIBE, its partition columns, if any,
among it. Its three TODO lines were then filled in by hand: this docstring's first line, the
key, and does_not_add_up.
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
    partitioned_by=["region", "dt"],
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
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = region_costs.cost_cents
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(region_costs.cost_cents, <value>)
