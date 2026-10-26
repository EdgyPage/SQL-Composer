# sqlglot Composer 7.2 - copy it, then edit your copy
"""mart.job_day_facts - one row per job and day: events, runs, minutes and team.

Why: its notebook saves each job's day beside the team that owned the job that day, so
mart.team_days counts each team's day from a few saved rows.

project.new_table wrote this file from admin/templates/saved_table_reference.py; it was
filled in by hand, since the table doesn't exist until its notebook's create() makes it.
"""

from sqlglot_composer import Table

job_day_facts = Table(
    "mart.job_day_facts",
    columns={
        "job_id": "bigint",
        "team": "string",
        "events": "bigint",
        "runs": "bigint",
        "minutes": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["job_id", "dt"],
    location="/data/your_team/mart.db/job_day_facts",  # its own folder
    descriptions={
        "team": "the team that owned the job that day; NULL if no snapshot says",
        "minutes": "the minutes of the runs that ended that day",
        "dt": "the day, as yyyy-MM-dd",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table, such as:
#     from references.mart__job_day_facts import job_day_facts, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_day_facts.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_day_facts.<column>, <value>)
