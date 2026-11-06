# sqlglot Composer 8.5 - copy it, then edit your copy
"""<DB>.<TABLE> - TODO: say in one line what one row is.

project.reference_from_logic("<DB>.<TABLE>") writes this file again from the table's logic,
filling in what is left. They are:
    <COLUMNS>: the columns write() saves and their types, from its logic's preview().

Why: TODO: who reads this table, and why it is saved rather than worked out each time.

project.new_table wrote this file from admin/templates/saved_table_reference.py, to stand in
until the table's logic is written: then project.reference_from_logic writes it again, its
columns and types from preview(), its partition columns from PARTITIONED_BY, and the Key its
query makes. A Saved table doesn't exist until its notebook's create() makes it from this
file, so nothing can be asked of it: its logic says what it holds.
"""

from sqlglot_composer import Table

<TABLE> = Table(
    "<DB>.<TABLE>",
    columns={"<COLUMNS>": "string"},  # project.reference_from_logic writes them, from the logic
    location=None,  # TODO: its own folder, such as "/data/your_team/<DB>.db/<TABLE>"
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
