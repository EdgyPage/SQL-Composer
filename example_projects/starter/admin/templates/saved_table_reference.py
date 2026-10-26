# sqlglot Composer 7.2 - copy it, then edit your copy
"""<DB>.<TABLE> - TODO: say in one line what one row is.

Fill in every <...> below, brackets and all: Python stops at one left in. They are:
    <COLUMN> and <COLUMN_TYPE>: a column write() saves and its Hive type, each in quotes,
        such as "job_id" and "bigint". Copy the line for each column, in the order write()
        saves them, its partition columns last.
    <LOCATION>: the table's own folder, in quotes, such as "/data/your_team/<DB>.db/<TABLE>".
Then partitioned_by= and key=, and the TODO lines.

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
        <COLUMN>: <COLUMN_TYPE>,  # a line per column write() saves, its partition columns last
    },
    partitioned_by=[],  # its partition columns, in order, such as ["region"]: [] for none
    key=None,  # the columns whose values name one row, such as ["job_id"]: None if none do
    location=<LOCATION>,  # its own folder, in quotes
    descriptions={},  # optional: {"column": "what it holds"}, for the Reference sheet
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.<NAME> import <TABLE>, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = <TABLE>.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(<TABLE>.<column>, <value>)
