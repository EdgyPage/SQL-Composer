"""<DB>.<TABLE> - TODO: say in one line what one row is.

Why: TODO: who reads this table, and why it is saved rather than worked out each time.

project.new_table wrote this file from admin/templates/saved_table_reference.py. A Saved
table's Table reference is filled in by hand, since the table doesn't exist until its
notebook's create() makes it from this file. Its notebook's text cell says which columns it
lists, and its Key.
"""

from sqlglot_composer import Table

<TABLE> = Table(
    "<DB>.<TABLE>",
    columns={
        <COLUMN>: <COLUMN_TYPE>,  # every column write() saves, in order, each in quotes
        "dt": "string",  # the day, as yyyy-MM-dd: its partition column, last
    },
    partitioned_by=["dt"],  # its partition columns, in order, each also in columns
    key=None,  # or the columns that pick out one row, such as ["job_id", "dt"]
    location=<LOCATION>,  # its own folder, in quotes, such as "/data/your_team/<DB>.db/<TABLE>"
    descriptions={},  # optional: {"column": "what it holds"}, for the Reference sheet
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.<NAME> import <TABLE>, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
# gives back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = <TABLE>.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(<TABLE>.<column>, <value>)
