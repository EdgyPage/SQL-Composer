"""A Saved table's Table reference, by hand: name, columns, Date partition, key.

Why: a Saved table doesn't exist until create_table makes it from this file, so
write_table_reference, which asks a table for its columns, can't write this one for you.

Copy it to: table_references/<SAVED_TABLE>.py

The columns are the ones the Statement that writes the table selects, in the same order, then
the Date partition, dt, last. A write doesn't select the Date partition: the Toolbox writes the
day into it. Once it is filled in, write this docstring again to say what one row is and why
the table is saved, as the file below does.

Mirrors example_projects/starter/table_references/daily_job_runs.py.

Replace each placeholder, brackets and all, wherever it is written:

Fill in:
    <SAVED_TABLE>: the Table reference's name, which is also its file's name, such as
        job_day_minutes.
    <SAVED_TABLE_NAME>: the table's name in the warehouse, in quotes, in a database you may
        write to, such as "mart.job_day_minutes".
    <GROUP_COLUMN_NAME>: the column each row is for, in quotes, such as "job_id".
    <GROUP_COLUMN_TYPE>: its type, in quotes, as the table it is read from has it, such as
        "bigint".
    <TOTAL_NAME>: a column of numbers added up for each row, in quotes, such as "minutes".
"""

from sqlglot_composer import Table

<SAVED_TABLE> = Table(
    <SAVED_TABLE_NAME>,  # the name create_table makes it by
    columns={
        <GROUP_COLUMN_NAME>: <GROUP_COLUMN_TYPE>,  # what each row is for, such as each job
        "row_count": "bigint",  # the rows counted for it that day
        <TOTAL_NAME>: "bigint",  # a number added up for it that day; a line per number
        "dt": "string",  # the Date partition, dt: the day, as yyyy-MM-dd
    },
    date_partition="dt",
    key=[<GROUP_COLUMN_NAME>, "dt"],  # one row per group and day
)
