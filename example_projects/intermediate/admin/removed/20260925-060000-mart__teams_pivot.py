"""mart.teams_pivot - TODO: say in one line what one row is."""
from sqlglot_composer import Table

teams_pivot = Table(
    "mart.teams_pivot",
    columns={
        "job_id": "bigint",
        "sum_of_hours": "double",
    },
    key=["job_id"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/mart.db/job_hours",
    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
)

# The name of this table, proposed for its final in the workbook. Answer "name" in the
# decisions cell: "proposed" keeps it; a name of your own renames this table, and its
# Total Row's table, if it has one, with it.
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

# Rebuilt or History: "rebuilt" if each write replaces the whole table; "history" if
# each write keeps the rows already there, adding rows or replacing some, such as one
# day's Partition, so the table needs its past rows loaded first, its Seed. Answer
# "kind" in the decisions cell: "proposed" accepts the kind proposed below.
KIND = "rebuilt"  # answered, proposed rebuilt: it is a query alone, which each write writes whole

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart__teams_pivot import teams_pivot, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = teams_pivot.sum_of_hours
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(teams_pivot.sum_of_hours, <value>)
