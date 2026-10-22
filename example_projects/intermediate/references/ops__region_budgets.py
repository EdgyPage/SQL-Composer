# sqlglot Composer 7.1, exported 2026-10-22 13:22 - copy it, then edit your copy
"""ops.region_budgets - one row per job and region: its budget for a day's cost.

Why: the project's notebooks read the table through this file, so each column they name, and the
key each join and count relies on, where it has one, is checked as the Statement is built.

project.add_references wrote this file from the table's DESCRIBE, its partition columns, if any,
among it. Its three TODO lines were then filled in by hand: this docstring's first line, the
key, and does_not_add_up.
"""
from sqlglot_composer import Table

region_budgets = Table(
    "ops.region_budgets",
    columns={
        "job_id": "bigint",
        "budget_cents": "bigint",
        "region": "string",
    },
    partitioned_by=["region"],
    key=["job_id", "region"],  # filled in by hand
    # filled in by hand: none of the columns is an average, a ratio or a distinct count
    does_not_add_up=[],
    descriptions={
        "budget_cents": "the most a day of the job should cost there",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.ops__region_budgets import region_budgets, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = region_budgets.budget_cents
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(region_budgets.budget_cents, <value>)
