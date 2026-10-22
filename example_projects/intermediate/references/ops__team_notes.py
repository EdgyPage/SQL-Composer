"""ops.team_notes - one row per note a team wrote about its jobs.

Why: the project's notebooks read the table through this file, so each column they name, and the
key each join and count relies on, where it has one, is checked as the Statement is built.

project.add_references wrote this file from the table's DESCRIBE, its partition columns, if any,
among it. Its three TODO lines were then filled in by hand: this docstring's first line, the
key, and does_not_add_up.
"""
from sqlglot_composer import Table

team_notes = Table(
    "ops.team_notes",
    columns={
        "team": "string",
        "note": "string",
        "written_on": "string",
    },
    key=None,  # filled in by hand: nothing names one row
    # filled in by hand: none of the columns is an average, a ratio or a distinct count
    does_not_add_up=[],
    descriptions={
        "written_on": "the day the note was written, as yyyy-MM-dd",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.ops__team_notes import team_notes, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
# gives back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = team_notes.team
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(team_notes.team, <value>)
