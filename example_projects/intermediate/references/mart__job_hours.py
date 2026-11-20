"""mart.job_hours - one row per job and team: the hours its runs took.

Why: the project's notebooks read the table through this file, so each column they name, and the
key each join and count relies on, where it has one, is checked as the Statement is built.

project.convert wrote this file from the workbook's PivotTable, its columns from the Hive the
workbook gave; the convert Workflow's decisions cell then answered its name, its location and
its Pivot filter, and accepted its proposed Key. Its two TODO lines were then filled in by hand:
this docstring's first line and does_not_add_up.
"""
from sqlglot_composer import Table

job_hours = Table(
    "mart.job_hours",
    columns={
        "job_id": "bigint",
        "team": "string",
        "sum_of_hours": "double",
    },
    key=["job_id", "team"],
    location="/data/mart.db/job_hours",
    # filled in by hand: none of the columns is an average, a ratio or a distinct count
    does_not_add_up=[],
)

# The name of this table, proposed for its final in the workbook. Answer "name" in the
# decisions cell: "proposed" keeps it; a name of your own renames this table, and its
# total levels' tables with it.
NAME = "job_hours"  # for PivotTable1 of job_hours.xlsx

# The database table each Table or range of the workbook it reads samples, proposed from
# its name, which needn't be the one your warehouse gives it. Answer "sources" in the
# decisions cell with the table it samples, in any database, such as {"ops.table1":
# "ops.job_runs"}, or {"ops.table1": "proposed"} to keep it.
SOURCES = {
    "ops.job_events": "ops.job_events",  # the database table job_events of job_hours.xlsx samples
    "ops.job_owners": "ops.job_owners",  # the database table job_owners of job_hours.xlsx samples
}

# What the PivotTable this table was made from leaves out: each Pivot filter, by its
# field, a Decision. Answer "pivot_filters" in the decisions cell: "keep" keeps the
# selection as converted; "fold", "batch" or "tables" keeps every value instead, as its
# checklist says.
PIVOT_FILTERS = {
    "team": "fold",  # the slicer on team keeps data. "keep": 1 table, that selection; "fold": 1 table, every team; "batch": 1 table, a Partition per team; "tables": at least 2 tables, one per team the PivotTable's cache held (data and finance)
}

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart__job_hours import job_hours, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_hours.sum_of_hours
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_hours.sum_of_hours, <value>)
