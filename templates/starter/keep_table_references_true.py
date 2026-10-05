"""Write Table references for new tables; compare those you keep with the tables.

Why: a table can change under you, a column added or a type changed, and comparing each Table
reference with its table every week finds the change before a Statement gives a wrong number.

Copy it to: keep_table_references_true.py, in your project's folder, beside the Level folders.

Use it from a notebook in your project's folder, with your own send:

    import keep_table_references_true as references
    references.write_new_table_references(send)
    references.compare_with_the_tables(send)

write_new_table_references writes table_references/<table>.py for each table in NEW_TABLES,
asking the table for its columns, and never writes over a file that is there. Fill in each
TODO line it leaves (what one row is, the key, the columns that don't add up), then move the
table from NEW_TABLES to TABLE_REFERENCES, importing its Table reference as <TABLE>'s is.

compare_with_the_tables prints, for each Table reference in TABLE_REFERENCES, what
check_table_reference finds (each column and its type, and how the Date partition writes its
days), then whether check_key finds the key still picks out one row on the newest day.

Mirrors how example_projects/starter/table_references/jobs.py, job_runs.py and run_alerts.py
were written, and how-to 18, Keep a Table reference true over time.

Replace each placeholder, brackets and all, wherever it is written:

Fill in:
    <NEW_TABLE_NAME>: a table with no Table reference yet, in quotes, such as "ops.job_events";
        add one per table, or leave the list empty: NEW_TABLES = [].
    <TABLE>: a Table reference you keep, which is also its file's name in table_references/,
        such as job_runs; add an import and a list entry for each.
"""

import contextlib
from pathlib import Path

from sqlglot_composer import check_key, check_table_reference, write_table_reference
from table_references.<TABLE> import <TABLE>  # an import per Table reference you keep

TABLE_REFERENCES_FOLDER = Path(__file__).resolve().parent / "table_references"
NEW_TABLES = [<NEW_TABLE_NAME>]  # each table to write a Table reference for, by its name
TABLE_REFERENCES = [<TABLE>]  # each Table reference you keep, to compare with its table


def write_new_table_references(send):
    """Write a Table reference file in table_references/ for each table in NEW_TABLES, and
    return the files written. A table whose file is there already is left as it is."""
    written = []
    # write_table_reference writes into the folder Python is working in, so this works in
    # table_references/ while it writes, then goes back
    with contextlib.chdir(TABLE_REFERENCES_FOLDER):
        for name in NEW_TABLES:
            try:
                written.append(TABLE_REFERENCES_FOLDER / write_table_reference(name, send=send))
            except FileExistsError:
                print(f"{name}: its Table reference is there already, and is yours to edit.")
    return written


def compare_with_the_tables(send):
    """Print, for each Table reference in TABLE_REFERENCES, what differs from its table, and
    whether its key holds on the newest day."""
    for t in TABLE_REFERENCES:
        # in a loop nothing is shown unless it is printed
        print(check_table_reference(t, send=send))
        print(check_key(t, send=send))
