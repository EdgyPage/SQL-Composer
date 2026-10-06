"""Import a table's column names programmatically

For: Getting started

## Goal

Get every column of a table, its name and its Hive type, into your notebook without typing
them. `write_table_reference` asks the table itself and writes its Table reference, a small
.py file describing the table. You fill in what it can't know, check the file against the
table, and then build Statements from its columns: all of them at once, or the ones
a list of names picks.

## When you'd use it

The first time you read a table at work. A Statement reads a table through its Table reference,
so every table you read needs one, and a table with forty columns is forty chances to mistype a
name or a type. Generate it instead, then keep the file beside your notebook, for every
notebook that reads the table.

A table that doesn't exist yet, such as a Saved table (a table of your own, which your
Statements write into) you are about to create, has nothing to ask: describe it by hand, as [Describe a table by hand](#describe_a_table_by_hand) shows.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *

Every step here passes `send=example_database.send`, the Example database's own send. At work,
pass your own send, from [Start a notebook](#start_a_notebook), and name your own tables.

### See what the table says about itself

A table in the warehouse can describe itself. The Hive command DESCRIBE lists its columns and
their types, and SHOW PARTITIONS lists the days it holds. Neither reads a single row, so both
are quick on the biggest table. Here is what DESCRIBE says of `ops.run_alerts`, sent straight
through the Example database's send:

>>> example_database.send("DESCRIBE ops.run_alerts")
                  col_name  data_type     comment
0                 alert_id     bigint
1                   run_id     bigint
2                 severity     string  low / high
3                       dt     string
4                                None        None
5  # Partition Information       None        None
6               # col_name  data_type     comment
7                       dt     string

The first four rows are its columns. The fifth is a blank line DESCRIBE leaves before its next
section: its name is empty, and its other two cells are missing, NULL in Hive, which this page
shows as NULL and pandas in your notebook as None. The rows under `# Partition Information` say which column
splits the table into days: dt, its Date partition.

### Write one table's Table reference

`write_table_reference` sends those two commands through your send and turns what comes back
into a Table reference file. It writes the file in the folder your notebook runs in, named
after the table, and gives back the file's path:

>>> path = write_table_reference("ops.job_runs", send=example_database.send)
>>> path.name
'job_runs.py'

Read the file it wrote. It imports `Table`, then makes one variable, `job_runs`, named like the
file:

- `columns` holds every column and its type, and a column's comment in the warehouse comes
  along as a `#` comment, such as status's `SUCCESS / FAILED / TEST, NULL while running`;
- `date_partition="dt"` comes from `SHOW PARTITIONS`;
- three lines say TODO: the description on the first line, `key=None` and
  `does_not_add_up=[]`. The table can't tell anyone those, so the file leaves them to you.

### Write several in a loop

`write_table_reference` is a plain function, so a Python `for` loop writes one file per table
in a list:

>>> for name in ["ops.jobs", "ops.run_alerts"]:
...     path = write_table_reference(name, send=example_database.send)
...     print(path.name)
jobs.py
run_alerts.py

Each file, and the variable in it, is named after the part of the table's name after the dot:
`ops.jobs` gives jobs.py, holding a variable named jobs. A table named like a word Python keeps
for itself, such as class, or like a module Python already has, such as calendar or pandas,
gets t_ in front: `ops.calendar` would give t_calendar.py, holding t_calendar, because
`import calendar` would bring in Python's own calendar module, not your file.

### Fill in the TODOs

Open job_runs.py in your editor and replace the three TODO lines. This is the file with
them filled in; nothing else changes:

    \"\"\"ops.job_runs - one row per run of a job.\"\"\"
    from sqlglot_composer import Table

    job_runs = Table(
        "ops.job_runs",
        columns={
            "run_id": "bigint",
            "job_id": "bigint",
            "status": "string",  # SUCCESS / FAILED / TEST, NULL while running
            "duration_mins": "int",
            "avg_retry_secs": "double",
            "dt": "string",
        },
        date_partition="dt",
        key=["run_id"],
        does_not_add_up=["avg_retry_secs"],
    )

- The first line says, in your own words, what one row is.
- `key=` lists the columns that pick out one row. Every run has its own `job_runs.run_id`, so
  it is `key=["run_id"]`. Ask whoever owns the table if you aren't sure: `check_key`, below,
  checks it. JOIN uses the key to warn you when a join would repeat rows.
- `does_not_add_up=` lists the columns that are averages, ratios or counts of different values.
  `job_runs.avg_retry_secs` is each run's average wait between retries: adding up two runs'
  averages gives a number that means nothing, so the Toolbox refuses to add it up once it is
  listed here.

Then import the file in your notebook, as you import any of your own .py files:

    from job_runs import job_runs

The Example database ships this same Table reference, filled in the same way, so the steps
here use its copy:

>>> job_runs = example_database.job_runs

### Check the file against the table

`check_table_reference` asks the table for its columns again and compares them with the file.
Run it after you edit a Table reference, and whenever the table may have changed:

>>> check_table_reference(job_runs, send=example_database.send)
ops.job_runs matches its Table reference.

When something differs, it lists each problem with the line to change in the file. It never
edits the file itself. A table that changed, and what it says then, is in
[Keep a Table reference true over time](#keep_a_table_reference_true_over_time).

### Check the key you wrote

The warehouse never checks a key: nothing stops two rows sharing one `job_runs.run_id`.
`check_key` counts the rows for each key on the newest day the table holds, and lists any key
that repeats:

>>> check_key(job_runs, send=example_database.send)
ops.job_runs: the key (run_id) holds on 2026-09-24.

### Take a first look at the rows

`first_look` builds an ordinary Statement that reads every column and 20 rows of yesterday,
so it is safe to run on a big table. `show_hive` prints its Hive, and `run` runs it. These
steps ran as if today were 2026-09-25, so yesterday is 2026-09-24:

>>> text = show_hive(first_look(job_runs))
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.status,
  job_runs.duration_mins,
  job_runs.avg_retry_secs,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24'
LIMIT 20;
>>> run(first_look(job_runs), send=example_database.send)
   run_id  job_id   status  duration_mins  avg_retry_secs          dt
0     101       1  SUCCESS             10             1.0  2026-09-24
1     102       2   FAILED             20             6.0  2026-09-24
2     103       3  SUCCESS             30             0.0  2026-09-24
3     104       1  SUCCESS             40             3.0  2026-09-24

This page was run as if today were 2026-09-25. In your own notebook, yesterday is your real
yesterday, and the Example database holds only 2026-09-23 and 2026-09-24, so on it this result
comes back empty, with its column names and no rows. At work, it shows your table's yesterday.

### Build a SELECT from every column

`all_columns` gives a Table reference's columns as a Python list, in the table's order:

>>> all_columns(job_runs)
[job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins, job_runs.avg_retry_secs, job_runs.dt]

`SELECT` takes a list as well as single columns, so `SELECT(all_columns(job_runs))` asks for
every column by name. Hive's `SELECT *` would ask for whatever the table holds on the day it
runs, so a column added later would quietly change your result; a list of names doesn't.

>>> every_column = statement(
...     SELECT(all_columns(job_runs)),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-23")),
... )
>>> text = show_hive(every_column)
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.status,
  job_runs.duration_mins,
  job_runs.avg_retry_secs,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-23';
>>> run(every_column, send=example_database.send)
   run_id  job_id   status  duration_mins  avg_retry_secs          dt
0      95       1  SUCCESS             12             2.0  2026-09-23
1      96       2  SUCCESS             18             0.0  2026-09-23
2      97       3   FAILED             30             8.0  2026-09-23
3      98       2     None             15             NaN  2026-09-23
4      99       1     TEST              5             0.0  2026-09-23

Run 98 is still running, so its status and its avg_retry_secs are missing: NULL. pandas shows
a missing number as NaN, and missing text as None.

### Build a SELECT from a list of column names

Each column of a Table reference is one of its attributes, such as `job_runs.status`. When the
names you want come as text, from a list in your settings or from another table's columns, the
built-in Python function `getattr` takes the attribute by its name, so the list of names
becomes a list of columns:

>>> wanted = ["run_id", "status", "duration_mins"]
>>> columns = [getattr(job_runs, name) for name in wanted]
>>> columns
[job_runs.run_id, job_runs.status, job_runs.duration_mins]
>>> chosen = statement(
...     SELECT(columns),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-23")),
... )
>>> text = show_hive(chosen)
SELECT
  job_runs.run_id,
  job_runs.status,
  job_runs.duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-23';

A name that isn't one of the table's columns stops the list at once: see Common mistakes.

## Check it worked

The three Table reference files are in the folder your notebook runs in:

>>> from pathlib import Path
>>> [Path(name).exists() for name in ["job_runs.py", "jobs.py", "run_alerts.py"]]
[True, True, True]

Once you've filled in a file's TODOs, both checks pass for its table:

>>> check_table_reference(job_runs, send=example_database.send)
ops.job_runs matches its Table reference.
>>> check_key(job_runs, send=example_database.send)
ops.job_runs: the key (run_id) holds on 2026-09-24.

## Common mistakes

### A column name the table doesn't have

A Table reference is there so you never type a column's name as text. A misspelt column stops
the line it is on, and lists the columns the table has:

>>> job_runs.stauts
Traceback (most recent call last):
...
AttributeError: job_runs has no column 'stauts'. Did you mean 'status'? Its columns are: run_id, job_id, status, duration_mins, avg_retry_secs, dt.

A name in a list you pass to `getattr` is checked the same way:

>>> columns = [getattr(job_runs, name) for name in ["run_id", "duration"]]
Traceback (most recent call last):
...
AttributeError: job_runs has no column 'duration'. Did you mean 'duration_mins'? Its columns are: run_id, job_id, status, duration_mins, avg_retry_secs, dt.

Copy the name from the list the message gives, here `"duration_mins"`.

### Adding up a column that doesn't add up

With `job_runs.avg_retry_secs` listed in `does_not_add_up=`, a total of it stops as you build
it, before anything runs:

>>> total_wait = statement(
...     SELECT(AS(sum_of(job_runs.avg_retry_secs), "wait")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  sum_of(job_runs.avg_retry_secs) adds up job_runs.avg_retry_secs, which is listed in does_not_add_up in its Table reference.
...

`GuardRefused` is how a Guard stops: a check the Toolbox runs as you build a Statement, which
refuses one that would quietly give a wrong number. If you leave `does_not_add_up=[]` empty,
nothing stops it, and the total means nothing.

### Writing a Table reference that is already there

`write_table_reference` never overwrites a file: once written, the file is yours, and
rewriting it would lose the key and the notes you added. Run a second time for the same table,
it stops:

>>> write_table_reference("ops.job_runs", send=example_database.send)
Traceback (most recent call last):
...
FileExistsError:
  What happened:  job_runs.py already exists in the folder you're working in, so nothing was written.
...

Edit the file instead, and run `check_table_reference` to see what has changed in the table
since.

### A key that doesn't pick out one row

The table ops.run_alerts has a run_id column too, and a run can raise several alerts. A key
of `["run_id"]`
looks right, but `check_key` shows the run_ids that repeat:

>>> wrong_key = Table(
...     "ops.run_alerts",
...     columns={"alert_id": "bigint", "run_id": "bigint", "severity": "string",
...              "dt": "string"},
...     date_partition="dt",
...     key=["run_id"],
... )
>>> check_key(wrong_key, send=example_database.send)
ops.run_alerts: the key (run_id) repeats on 2026-09-24. Keys with more than one row:
 run_id  copies
    101       3
    103       2

Its key is `["alert_id"]`: one row per alert.

## Next

- Describe a Saved table that doesn't exist yet, by hand:
  [Describe a table by hand](#describe_a_table_by_hand).
- Build your first Statement on the table and paste its Hive into another program:
  [Build a first Statement and paste its Hive](#build_a_first_statement).
- When a table gains or changes a column after you wrote its file:
  [Keep a Table reference true over time](#keep_a_table_reference_true_over_time).
- A table whose days are written like 20260924, or which is split by a second column too:
  [A day written another way, and a second partition](#a_day_written_another_way).
- Each function here has a Worked example in the gallery:
  [`write_table_reference`](examples.html#write_table_reference),
  [`check_table_reference`](examples.html#check_table_reference),
  [`check_key`](examples.html#check_key), [`first_look`](examples.html#first_look) and
  [`all_columns`](examples.html#all_columns).
"""
