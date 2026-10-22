# sqlglot Composer 7.1, exported 2026-10-22 13:22 - copy it, then edit your copy
"""mart.job_notes - one row per note and each job its team owned that day.

Why: a note in ops.team_notes names only a team, so finding the jobs it is about means looking
up which jobs the team owned that day; its notebook does it once and saves it.

It isn't partitioned, so each write replaces the whole table, and it has no Key: nothing names
one row, since a team can write the same note twice on one day.

project.new_table wrote this file from admin/templates/saved_table_reference.py; it was
filled in by hand, since the table doesn't exist until its notebook's create() makes it.
"""

from sqlglot_composer import Table

job_notes = Table(
    "mart.job_notes",
    columns={
        "job_id": "bigint",
        "team": "string",
        "note": "string",
        "written_on": "string",
    },
    partitioned_by=[],  # none: a write replaces the whole table
    key=None,  # none: nothing names one row
    location="/data/your_team/mart.db/job_notes",  # its own folder
    descriptions={
        "job_id": "a job the team owned on the day the note was written",
        "written_on": "the day the note was written, as yyyy-MM-dd",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table, such as:
#     from references.mart__job_notes import job_notes, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_notes.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_notes.<column>, <value>)
