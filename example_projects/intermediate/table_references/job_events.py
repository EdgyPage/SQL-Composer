"""ops.job_events - one row per event of a run: start, retry, finish or fail.

Why: the project's Statements read the table through this file, so each column they name, and
the key each join and count relies on, is checked as the Statement is built.

write_table_reference wrote this file from the table's DESCRIBE and SHOW PARTITIONS. Its three
TODO lines were then filled in by hand: this docstring's first line, the key, and
does_not_add_up.
"""
from sqlglot_composer import Table

job_events = Table(
    "ops.job_events",
    columns={
        "event_id": "bigint",
        "job_id": "bigint",
        "event_type": "string",
        "minutes": "int",
        "dt": "string",
    },
    date_partition="dt",
    key=["event_id"],  # filled in by hand
    # filled in by hand: none of the columns is an average, a ratio or a distinct count
    does_not_add_up=[],
    descriptions={
        "event_type": "start / finish / retry / fail",
        "minutes": "minutes since the run started",
    },
)

# --- Aliases ----------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below this heading.
# Import one beside the table: from references.ops__job_events import job_events, <alias>
#
# A column Alias is a plainer name for one column. It is only a shorter name: the Hive, the
# output and the lineage still say the column's own name. To name an output, use AS(...).
#     <alias> = job_events.event_id
# A condition Alias names a condition on this table alone, for WHERE or count_rows(where=...).
# Add what it calls, such as equals, to the import from sqlglot_composer above.
#     <alias> = equals(job_events.event_id, <value>)
