"""ops.job_events - one row per event of a run: start, retry, finish or fail.

Why: the project's notebooks read the table through this file, so each column they name, and the
key each join and count relies on, where it has one, is checked as the Statement is built.

project.add_references wrote this file from the table's DESCRIBE, its partition columns, if any,
among it. Its three TODO lines were then filled in by hand: this docstring's first line, the
key, and does_not_add_up.
"""
from sqlglot_composer import Table, is_in

job_events = Table(
    "ops.job_events",
    columns={
        "event_id": "bigint",
        "job_id": "bigint",
        "event_type": "string",
        "minutes": "int",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["event_id"],  # filled in by hand
    # filled in by hand: none of the columns is an average, a ratio or a distinct count
    does_not_add_up=[],
    descriptions={
        "event_type": "start / finish / retry / fail",
        "minutes": "minutes since the run started",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.ops__job_events import job_events, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = job_events.event_type
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(job_events.event_type, <value>)

ends_a_run = is_in(job_events.event_type, ["finish", "fail"])
