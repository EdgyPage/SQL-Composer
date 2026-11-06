"""mart_dev.failed_runs - One row per job_id."""
from sqlglot_composer import Table

failed_runs = Table(
    "mart_dev.failed_runs",
    columns={
        "job_id": "bigint",
        "fails": "bigint",
    },
    key=["job_id"],
    location="/data/team/mart_dev.db/failed_runs",  # under its Database's location_root, in admin/databases.py
    does_not_add_up=[],  # no column is an average, a ratio or a distinct count: fails is a count
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__failed_runs import failed_runs, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = failed_runs.fails
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(failed_runs.fails, <value>)
