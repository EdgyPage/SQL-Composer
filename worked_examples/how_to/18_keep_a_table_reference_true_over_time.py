"""Keep a Table reference true over time

For: Getting started

## Goal

Notice when a table at work changes under its Table reference, a column added, removed or
given a new type, or its days written another way, and bring the Table reference back in line
before a Statement gives a wrong answer or fails at the warehouse. `check_table_reference`
compares the two and says which line of the Table reference to change.

## When you'd use it

- On a schedule, say every Monday, for every Table reference your notebooks use.
- When the team that owns a table says it has changed it.
- When a Statement that used to run fails at the warehouse, naming a column it can't find.
- Before you rely on a Table reference written long ago, or by someone else.

A Table reference is written once, from the table as it was that day, and the table goes on
changing without it. The Toolbox checks every Statement against the Table reference, so a
Table reference that is out of date lets through Statements the warehouse then refuses, or
reads a column as the wrong type.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> import pandas as pd

### Check a Table reference against its table

`check_table_reference` takes a Table reference and your send. It sends two queries that read
the table's description, never its rows: DESCRIBE, which lists the columns and their types,
and SHOW PARTITIONS, which lists the days the table holds. Then it compares them with the
Table reference:

>>> check_table_reference(example_database.job_runs, send=example_database.send)
ops.job_runs matches its Table reference.

This is what the warehouse's DESCRIBE answers, here from the Example database: the columns
and their types, then the partition columns again, under a heading of their own:

>>> described = example_database.send("DESCRIBE ops.job_runs")
>>> described[["col_name", "data_type"]]
                  col_name  data_type
0                   run_id     bigint
1                   job_id     bigint
2                   status     string
3            duration_mins        int
4           avg_retry_secs     double
5                       dt     string
6                                None
7  # Partition Information       None
8               # col_name  data_type
9                       dt     string

### Your Table reference, as it was written

At work, a Table reference lives in its own file, written months ago, perhaps by
`write_table_reference`. This one is the same as the Example database's:

>>> job_runs = Table(
...     "ops.job_runs",
...     columns={
...         "run_id": "bigint",
...         "job_id": "bigint",
...         "status": "string",  # SUCCESS / FAILED / TEST, NULL while running
...         "duration_mins": "int",
...         "avg_retry_secs": "double",
...         "dt": "string",
...     },
...     date_partition="dt",
...     key=["run_id"],
...     does_not_add_up=["avg_retry_secs"],
... )

`does_not_add_up=[...]` lists the columns a sum would make meaningless, such as an average: the
Toolbox refuses `sum_of` on them. `job_runs.avg_retry_secs` is an average per run, so it is listed.

### The table changes

Say the team that owns `ops.job_runs` replaces `"avg_retry_secs"` with `"retries"`, the number of
times each run was retried, and makes `"duration_mins"` a `"bigint"`, since some runs got very
long. The Example database's tables never change, so a stand-in send plays the warehouse after
that change: it answers DESCRIBE with the new columns, and passes every other query on to the
Example database's send.

>>> after_the_change = pd.DataFrame(
...     [("run_id", "bigint", ""),
...      ("job_id", "bigint", ""),
...      ("status", "string", "SUCCESS / FAILED / TEST, NULL while running"),
...      ("duration_mins", "bigint", ""),
...      ("retries", "int", "times the run was retried"),
...      ("dt", "string", ""),
...      ("", None, None),
...      ("# Partition Information", None, None),
...      ("# col_name", "data_type", "comment"),
...      ("dt", "string", "")],
...     columns=["col_name", "data_type", "comment"],
... )
>>> def send_after_the_change(hive):
...     if hive.startswith("DESCRIBE"):
...         return after_the_change
...     return example_database.send(hive)

### Check it again

The same check, against the changed table, now lists what differs:

>>> check_table_reference(job_runs, send=send_after_the_change)
ops.job_runs differs from its Table reference.
Problems:
  - duration_mins is bigint in the table: change its line to "duration_mins": "bigint",
  - avg_retry_secs isn't in the table: remove its line, or correct its name.
Notes:
  - retries is in the table but not in the Table reference: add "retries": "int", if you want it.

It sorts what it finds in two:

- Problems make Statements wrong, or make the warehouse refuse them: a column the table no
  longer has, or one whose type changed. Fix every one.
- Notes may not matter: a new column the Table reference doesn't list is simply not
  available to your Statements. Add it if you want to use it.

Each line ends with the line to write in the Table reference file. The check never edits the
file itself: the Table reference is yours, with your key and comments in it. Copy each line
as it is, comma included: it is a line of the `columns={...}` dict.

### Update the Table reference

Make each change it lists. `"avg_retry_secs"` goes from `columns={...}`, and from
`does_not_add_up=[...]` too, and `"retries"` comes in:

>>> job_runs = Table(
...     "ops.job_runs",
...     columns={
...         "run_id": "bigint",
...         "job_id": "bigint",
...         "status": "string",  # SUCCESS / FAILED / TEST, NULL while running
...         "duration_mins": "bigint",
...         "retries": "int",  # times the run was retried
...         "dt": "string",
...     },
...     date_partition="dt",
...     key=["run_id"],
... )
>>> check_table_reference(job_runs, send=send_after_the_change)
ops.job_runs matches its Table reference.

### Let the Toolbox find the Statements to change

With the Table reference up to date, every Statement that still reads
`job_runs.avg_retry_secs` stops as it is built, at its own line, naming the columns the table
has now:

>>> statement(
...     SELECT(job_runs.run_id, job_runs.avg_retry_secs),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
... )
Traceback (most recent call last):
...
AttributeError: job_runs has no column 'avg_retry_secs'. Its columns are: run_id, job_id, status, duration_mins, retries, dt.

Run your notebooks and scripts once after the update, and each stop shows a Statement to
change. Without the update, the same Statement would be sent, and the warehouse would refuse
it, in the middle of a run.

### When the days are written another way

A Table reference can say how its days are written with `date_format=...`; left out, as in
every Table reference so far, it is `"%Y-%m-%d"`, as in 2026-09-25. The check also reads the
newest day SHOW PARTITIONS lists, and checks it is written that way. Say the team starts
writing new days as 20260925 rather than 2026-09-25. Another stand-in send plays that, answering SHOW PARTITIONS with the new day:

>>> def send_with_a_new_day(hive):
...     if hive.startswith("SHOW PARTITIONS"):
...         return pd.DataFrame({"partition": ["dt=2026-09-23", "dt=2026-09-24", "dt=20260925"]})
...     return example_database.send(hive)
>>> check_table_reference(example_database.job_runs, send=send_with_a_new_day)
ops.job_runs differs from its Table reference.
Problems:
  - the newest dt, '20260925', isn't written like date_format='%Y-%m-%d', the usual one: change the line to date_format="%Y%m%d",

That is a Problem: a Statement bounding the days as 2026-09-25 would find none of the new
days. The fix is the line it gives. If the older days stay written the old way, one
`date_format=...` can't bound both, so ask the table's owners whether they will write the
older days again the new way.

### Check every Table reference at once

A loop checks every table your notebooks read. At work, it is one cell of a notebook you run
every week, with your own send and your own Table references. A notebook shows what a cell's
last line gives, but inside a loop nothing is shown unless you `print` it:

>>> for table in [example_database.jobs, example_database.job_runs, example_database.run_alerts]:
...     print(check_table_reference(table, send=example_database.send))
ops.jobs matches its Table reference.
ops.job_runs matches its Table reference.
ops.run_alerts matches its Table reference.

## Check it worked

The updated Table reference matches the changed table, and its key still holds: no two rows
of the newest day share a `"run_id"`. `check_table_reference` doesn't look at the key, so check
it with `check_key`, which counts rows per key on the newest day:

>>> check_table_reference(job_runs, send=send_after_the_change)
ops.job_runs matches its Table reference.
>>> check_key(job_runs, send=send_after_the_change)
ops.job_runs: the key (run_id) holds on 2026-09-24.

## Common mistakes

### Passing the table's name as text

`check_table_reference` checks a Table reference, so it takes the Table reference itself, not
the table's name:

>>> check_table_reference("ops.job_runs", send=example_database.send)
Traceback (most recent call last):
...
TypeError:
  What happened:  check_table_reference(...) was given 'ops.job_runs'.
...

Pass `job_runs`, imported from its file. To write a Table reference from a table's name, use
`write_table_reference` instead.

### Removing a column but leaving it in does_not_add_up

A column the check says to remove may be named elsewhere in the Table reference too. Remove it
from `columns={...}` only, and the Table reference itself stops, naming the line left over:

>>> Table(
...     "ops.job_runs",
...     columns={"run_id": "bigint", "job_id": "bigint", "status": "string",
...              "duration_mins": "bigint", "retries": "int", "dt": "string"},
...     date_partition="dt",
...     key=["run_id"],
...     does_not_add_up=["avg_retry_secs"],
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  Table('ops.job_runs'): does_not_add_up names 'avg_retry_secs', which isn't one of its columns.
...

### Reading a failed check as a changed table

When the send itself fails, say the warehouse can't be reached, the check doesn't stop with
an error: it says so, and compares nothing. A stand-in send that fails plays that here:

>>> def send_that_fails(hive):
...     raise ConnectionError("the warehouse can't be reached")
>>> check_table_reference(job_runs, send=send_that_fails)
ops.job_runs: DESCRIBE failed, so nothing was compared. Check the table's name, and that send works. It said:
    ConnectionError:
    the warehouse can't be reached

Nothing about the table is known from this: fix the send, or the table's name, and check again.

## Next

- Write a Table reference from a table's columns, then check it: the gallery's
  [`write_table_reference`](examples.html#write_table_reference) and
  [`check_table_reference`](examples.html#check_table_reference) entries, and
  [`check_key`](examples.html#check_key).
- After a Saved table's columns change, rebuild it: [Save a table](#save_a_table).
- Write a table's Table reference in the first place:
  [Import a table's column names programmatically](#import_column_names).
- A table whose days are written like 20260924, or which is split by a second column too:
  [A day written another way, and a second partition](#a_day_written_another_way).
- Build many Statements, or check many tables, in a loop:
  [Generate Statements in a loop](#generate_statements_in_a_loop).
"""
