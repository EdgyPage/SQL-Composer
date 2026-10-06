# Spark Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy
"""A Saved table's Table reference, by hand: name, columns, Date partition, key.

Why: a Saved table doesn't exist until create_table makes it from this file, so
write_table_reference, which asks a table for its columns, can't write this one for you.

Copy it to: table_references/<SAVED_TABLE>.py

This is for a table your own Statement saves. A table already in your warehouse gets its Table
reference from write_table_reference instead: see notebook_start.py.

The columns are the Building block's, each named as the Building block's AS(...) names it, then
the Date partition, dt. The write matches its columns to these by name. The Building block
keeps its day, but the write leaves the Date partition out of its SELECT: the Toolbox writes
the day into it, as PARTITION(dt = '...'). Once it is filled in, write this
docstring again to say what one row is and why the table is saved, as
example_projects/spark_composer/starter/table_references/daily_job_runs.py does.

Mirrors example_projects/spark_composer/starter/table_references/daily_job_runs.py.

Replace each placeholder, brackets and all, wherever it is written in the code, then delete
this Fill in: block:

Fill in:
    <SAVED_TABLE>: the Table reference's name, which is also its file's name, such as
        job_day_minutes.
    <SAVED_TABLE_NAME>: the table's name in the warehouse, in quotes, in a database you may
        write to, such as "mart.job_day_minutes".
    <GROUP_COLUMN_NAME>: the column each row is for, the one the Building block groups by, in
        quotes, such as "job_id".
    <GROUP_COLUMN_TYPE>: its type, in quotes, as the Table reference of the table it is read
        from gives it, such as "bigint".
    <TOTAL_NAME>: the name the Building block gives what it adds up, the same name in quotes,
        such as "minutes".
    <TOTAL_TYPE>: its type, in quotes: "bigint" when the column added up holds whole numbers,
        "double" when it holds numbers with a fraction.
"""

from spark_composer import Table

<SAVED_TABLE> = Table(  # the Table reference, named as its file is
    <SAVED_TABLE_NAME>,  # the name create_table makes it by
    columns={
        <GROUP_COLUMN_NAME>: <GROUP_COLUMN_TYPE>,  # what each row is for, such as each job
        "row_count": "bigint",  # the rows counted for it that day
        # add a line like the next for each number the Building block adds up
        <TOTAL_NAME>: <TOTAL_TYPE>,  # a number added up for it that day
        "dt": "string",  # the Date partition: the day, written like 2026-09-24
    },
    date_partition="dt",
    key=[<GROUP_COLUMN_NAME>, "dt"],  # one row per group and day
)
