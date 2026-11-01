# A prod copy project.promote made of references/mart_dev__job_fails_counted.py: change that one and promote it again. Its
# location= is the one line yours to change here.
"""team_prod.job_fails_counted - one row per job per day that had a failed run: how many of its runs failed that day."""
from sqlglot_composer import Table

job_fails_counted = Table(
    "team_prod.job_fails_counted",
    columns={
        "job_id": "bigint",
        "fails": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["job_id", "dt"],  # proposed from its query; if it is wrong, answer "key" in the decisions cell
    location="/data/team/team_prod.db/job_fails_counted",
    does_not_add_up=[],  # none: every column is a count or a key
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.team_prod__job_fails_counted import job_fails_counted, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_fails_counted.fails
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_fails_counted.fails, <value>)
