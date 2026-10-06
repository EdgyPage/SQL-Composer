# Spark Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy
"""A notebook's first cells: your send, a Table reference and a first Statement.

Why: a first Statement run on a table you know shows that the import, your send and your Table
reference all work, before you build anything on them.

Copy it to: first_notebook.py, in your project's folder, or paste each cell below into a
notebook started there. The project's folder holds the Toolbox's two folders, composer_core
and spark_composer; cell 2 makes a table_references/ folder beside them, for your Table
references, if it isn't there yet.

Each word in angle brackets, such as <TABLE>, is a placeholder: replace it, brackets and all,
with your own, everywhere it is written in the code. Python stops at the first one left in,
so the file can't run half filled in. Then delete the Fill in: block below.

The cells, in order:

1. Import the Toolbox and write send, your function that runs a Hive string on your warehouse
   and gives back a pandas DataFrame. Try it on a query that reads no table, then on one you
   have run before on a table you know, to see its rows come back with their columns named.
2. Write the table's Table reference: write_table_reference asks the table for its columns and
   writes table_references/<TABLE>.py. Fill in each TODO line it leaves, such as the key, before
   cell 3. It never writes over a file that is there, so running cell 2 again leaves your
   filled-in file as it is.
3. Import the Table reference and run a first Statement: 20 rows of one day of the table.

To practise on the Example database's made-up tables first, fill each placeholder in with the
example its line below gives: every cell then runs as it is, on ops.job_runs.

Mirrors how-to 1, Start a notebook, and how-to 2, Import a table's column names
programmatically, on how_to.html in the spark_composer folder, and the notebook lines in
example_projects/spark_composer/starter/README.md.

Fill in:
    <RUN_HIVE>: the call that runs hive, the Hive text send is given, on your warehouse, and
        gives back a pandas DataFrame. To practise on the Example database: example_database.send(hive). For your
        warehouse, how-to 1's step Write your send shows how to write it. If your call gives
        each row as a tuple rather than a dict, pandas needs the column names too: that step
        shows how to pass them.
    <KNOWN_QUERY>: a query you have run before on a table you know, as text in quotes, such as
        "SELECT * FROM ops.job_runs WHERE dt = '2026-09-24' LIMIT 5".
    <TABLE_NAME>: the table to read, by its name in the warehouse, in quotes, such as
        "ops.job_runs".
    <TABLE>: that name after the dot, such as job_runs: write_table_reference names the file
        and the Table reference by it (with t_ in front of a name Python already uses, such
        as t_calendar).
    <DATE_PARTITION>: the table's Date partition, the column holding each row's day, such as dt.
    <DAY>: a day the table holds, in quotes, written as the table writes its days, such as
        "2026-09-24".
"""

# --- Cell 1: the Toolbox and your send ---

import contextlib
from pathlib import Path

import pandas as pd  # for your send, if it builds its DataFrame with pd.DataFrame(...)

# Every Toolbox name comes from spark_composer, never from a file inside it.
# example_database holds the made-up tables to practise on.
from spark_composer import (
    FROM, LIMIT, SELECT, WHERE, all_columns, equals, example_database, run, show_hive, statement,
    write_table_reference,
)


def send(hive):
    """Run a Hive string on your warehouse and give back a pandas DataFrame."""
    return <RUN_HIVE>  # the one line that reaches your warehouse


print(send("SELECT 1 AS one"))  # one column, named one, holding 1
print(send(<KNOWN_QUERY>))  # the rows you know, each column named

# --- Cell 2: the table's Table reference, written once ---

Path("table_references").mkdir(exist_ok=True)  # the folder for your Table references
# write_table_reference writes into the folder Python is working in, so this works in
# table_references/ while it writes, then goes back
with contextlib.chdir("table_references"):
    try:
        write_table_reference(<TABLE_NAME>, send=send)
    except FileExistsError:
        print(<TABLE_NAME>, "has its Table reference already: the file is yours to edit.")

# --- Cell 3: a first Statement, once each TODO line is filled in ---

from table_references.<TABLE> import <TABLE>  # the Table reference cell 2 wrote
# To practise on the Example database without cell 2, its tables' Table references come with
# the Toolbox: write <TABLE> = example_database.<TABLE> in place of the import above.

first_rows = statement(
    SELECT(all_columns(<TABLE>)),  # every column the Table reference lists
    FROM(<TABLE>),
    WHERE(equals(<TABLE>.<DATE_PARTITION>, <DAY>)),  # every read bounds the Date partition
    LIMIT(20),
)
show_hive(first_rows)  # prints the Hive that runs, ready to paste into another program
print(run(first_rows, send=send))  # sends it through your send, and shows what comes back
