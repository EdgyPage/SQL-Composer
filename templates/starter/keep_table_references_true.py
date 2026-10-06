"""Write Table references for new tables; compare those you keep with their tables.

Why: a table can change under you, a column added or a type changed, and comparing each Table
reference with its table every week finds the change before a Statement gives a wrong number.

Copy it to: keep_table_references_true.py, in your project's folder, beside table_references/,
building_blocks/ and statements/.

Use it from a notebook started in your project's folder, once send is written, as
notebook_start.py's cell 1 writes it:

    import keep_table_references_true as references
    references.write_new_table_references(send)
    references.compare_with_the_tables(send)

write_new_table_references writes a Table reference file for each table in NEW_TABLES, asking
the table for its columns: a file named for the table, in table_references/, such as
table_references/job_events.py for "ops.job_events". It makes the folder if it isn't there,
and never writes over a file that is. Fill in each TODO line it leaves: what one row is, the
key, and does_not_add_up, the columns that mean nothing added up, such as averages. Then move
the table from NEW_TABLES to TABLE_REFERENCES, and import its Table reference beside the
others.

Python reads a file once, when it is first imported: an import of it again, in the same
notebook, gives the file as it was then. After editing a Table reference, restart the
notebook's Python before comparing: reloading this file would still import the Table reference
as it was. After editing only this file, importlib.reload(references) is enough.

On first use, when you keep no Table reference yet, delete the import line below and write
TABLE_REFERENCES = [].

compare_with_the_tables prints, for each Table reference in TABLE_REFERENCES, what
check_table_reference finds (each column and its type, and how the Date partition writes its
days), then whether check_key finds the key still picks out one row on the newest day.

Mirrors how example_projects/starter/table_references/jobs.py, job_runs.py and run_alerts.py
were written, and how-to 18, Keep a Table reference true over time, on how_to.html in the
sqlglot_composer folder.

Replace each placeholder, brackets and all, wherever it is written in the code, then delete
this Fill in: block:

Fill in:
    <NEW_TABLE_NAME>: a table with no Table reference yet, by its name in the warehouse, in
        quotes, such as "ops.job_events"; add one per table, or leave the list empty:
        NEW_TABLES = [].
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
    TABLE_REFERENCES_FOLDER.mkdir(exist_ok=True)
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
    if not TABLE_REFERENCES:
        print("TABLE_REFERENCES is empty: move each table there from NEW_TABLES once its "
              "TODO lines are filled in, then restart Python.")
    for table_reference in TABLE_REFERENCES:
        # in a loop nothing is shown unless it is printed
        print(check_table_reference(table_reference, send=send))
        print(check_key(table_reference, send=send))
