"""A notebook's first cell: import the Toolbox, write your send, run a Statement.

Why: a first Statement run on a table you know shows that the import, your send and your Table
reference all work, before you build anything on them.

Copy it to: first_notebook.py, in your project's folder, or paste it into a notebook's first
cell there. The project's folder holds the Toolbox's two folders, composer_core and
sqlglot_composer, and your table_references/ folder.

Each word in angle brackets, such as <TABLE>, is a placeholder: replace it, brackets and all,
with your own, everywhere it is written. Python stops at the first one left in, so the file
can't run half filled in.

Mirrors the first lines of how-to 1, Start a notebook, and the notebook lines in
example_projects/starter/README.md.

Fill in:
    <RUN_HIVE>: the call that runs the text `hive` on your warehouse and gives back a pandas
        DataFrame, such as spark.sql(hive).toPandas() with a Spark session, or
        pd.DataFrame(my_api.query(hive)) with your team's query API (import pandas as pd
        first). To practise on the Example database's made-up tables: example_database.send(hive).
    <TABLE>: the Table reference to read, which is also its file's name in table_references/,
        such as job_runs. write_table_reference writes one: see keep_table_references_true.py.
    <DATE_PARTITION>: that table's Date partition, the column holding each row's day, such as dt.
    <DAY>: a day the table holds, in quotes, written as the table writes its days, such as
        "2026-09-24".
"""

# Every Toolbox name comes from the Edition's folder, never from a file inside it.
# example_database holds the made-up tables to practise on.
from sqlglot_composer import (
    FROM, LIMIT, SELECT, WHERE, all_columns, equals, example_database, run, show_hive, statement,
)
from table_references.<TABLE> import <TABLE>  # your table's Table reference


def send(hive):
    """Run a Hive string on your warehouse and give back a pandas DataFrame."""
    return <RUN_HIVE>  # the one line that reaches your warehouse


# Try your send alone first: it should give back one column, named one, holding 1.
print(send("SELECT 1 AS one"))

# A first Statement: 20 rows of one day of your table, every column.
first_rows = statement(
    SELECT(all_columns(<TABLE>)),  # every column the Table reference lists
    FROM(<TABLE>),
    WHERE(equals(<TABLE>.<DATE_PARTITION>, <DAY>)),  # every read bounds the Date partition
    LIMIT(20),
)
show_hive(first_rows)  # prints the Hive that runs, ready to paste into another program
print(run(first_rows, send=send))  # sends it through your send, and shows what comes back
