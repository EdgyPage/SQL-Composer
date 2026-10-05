"""Start a notebook

For: Getting started

## Goal

Get a notebook ready to write Hive SQL with the Toolbox. You import the Toolbox, write `send`,
your own function that runs Hive SQL on your warehouse, and try a first Statement on the
Example database, the made-up tables that ship inside the Toolbox, so you see each piece work
before you touch a real table.

## When you'd use it

At the top of every notebook, or script, that writes Hive with the Toolbox. Its first cell
imports the Toolbox and writes `send`; every cell after it builds Statements and runs them.

## Steps

### Put the two folders beside your notebook

The Toolbox is two folders: `composer_core`, the code both Editions share, and
`sqlglot_composer`, this Edition's own. Copy both from the Toolbox you downloaded, each whole,
into the folder that holds your notebook, so they sit side by side. Keep your own files beside
the two folders, never inside them: to update the Toolbox, you delete both folders and copy
them in again.

### Import the Toolbox

One line imports every Toolbox name: `statement`, the clause functions such as `SELECT`,
`FROM` and `WHERE`, `to_hive`, `show_hive`, `run`, `example_database`, and the rest.

>>> from sqlglot_composer import *

If the import stops instead, its message says what happened, why it matters and the usual fix.
Most often a file or a folder is missing, or the two folders come from different downloads.

### Write your send

The Toolbox never connects to anything itself. It writes Hive as text, and `run` hands that
text to a function of yours, `send`, which runs it and gives back a pandas DataFrame. How you
connect, retry or save files stays in your `send`, so the Toolbox works with whatever your
notebook uses to reach the warehouse.

[sqlglot_composer only]
With sqlglot Composer, `send` calls your query API, whatever your team uses to run a Hive
string, and turns the rows that come back into a pandas DataFrame, each column named. Write it
once, in your first cell:

    import pandas as pd

    def send(hive):
        rows = my_api.query(hive)  # your team's own call that runs Hive text goes here
        return pd.DataFrame(rows)

This works when your API gives each row as a dict, such as `{"run_id": 97, "job_id": 3}`:
`pd.DataFrame(rows)` takes the column names from its keys. If it gives each row as a tuple, it
gives the column names apart too, as a database cursor does in `cursor.description`. Pass those
names on; don't type them yourself, since each Statement has its own columns:

    def send(hive):
        cursor.execute(hive)  # your team's own cursor, from its database library
        names = [column[0] for column in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=names)

If your notebook has a Spark session, `spark`, that reads the warehouse's tables, use Spark
Composer instead. Its `send` runs the Hive on your `spark`, and where Spark would read a piece
of Hive differently, it writes that piece so Spark gives what Hive gives; the README lists each
place. Its folder, `spark_composer`, has its own copy of this page.
[end]
[spark_composer only]
With Spark Composer, `send` runs the Hive on your notebook's own `spark` session, and turns
Spark's DataFrame into a pandas one. Write it once, in your first cell:

    send = lambda hive: spark.sql(hive).toPandas()

`lambda hive: ...` is a function on one line: it takes the Hive text as `hive` and gives back
what follows the colon. `spark.sql(hive)` runs the Hive on Spark, and `.toPandas()` fetches
the rows into a pandas DataFrame.

The Example database runs on Spark too: its own Spark, apart from yours, which needs Java 17
to 21 on your computer. The first query a notebook sends it prints a Note saying it is starting
that Spark, and takes about 15 seconds; later queries take about a second.
[end]

There is no warehouse on this page, so the next steps use the Example database's own send,
`example_database.send`, which runs Hive on the Example database's six made-up tables. At work
you give `run` your own `send` in its place.

### Build a first Statement on the Example database

The Example database's first three tables are `ops.jobs`, one row per job; `ops.job_runs`, one
row per run of a job, on two days, 2026-09-23 and 2026-09-24; and `ops.run_alerts`, the alerts
a run raised. Three more, which the Intermediate how-tos use, hold 14 days each. Each table's
Table reference, which says what columns it has, comes with the Toolbox. Give the one you need
a short name:

>>> job_runs = example_database.job_runs

A Statement is one query, built from clause functions written in SQL's order: `SELECT` the
columns you want, `FROM` a table, and keep only some rows with `WHERE`. `WHERE` keeps a row
only if every condition in it holds. This Statement finds the runs that failed.

`job_runs.dt` is the table's Date partition: the day each row belongs to. The warehouse stores
such a table a day at a time, so the Toolbox has a rule: every Statement gives the first and
the last day it reads, here with `between`.

>>> failed = statement(
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
...     FROM(job_runs),
...     WHERE(equals(job_runs.status, "FAILED"),
...           between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )

Nothing has run yet: `failed` holds the Statement, ready to become Hive.

### See its Hive

`to_hive` gives the Hive as text: exactly what `run` sends. In it, `FROM ops.job_runs AS
job_runs` reads the table and calls it `job_runs`, the name the other lines use.

>>> print(to_hive(failed))
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.status = 'FAILED' AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'

`show_hive` prints the same Hive with a `;` at the end, ready to paste into another program,
such as Hue, DBeaver or spark-sql. It gives the text back too, so `text` keeps it to save or
use again:

>>> text = show_hive(failed)
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.status = 'FAILED' AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24';

In a notebook you can also write `show_hive(failed)` on a line of its own: it prints the Hive
once, and the text it gives back isn't shown a second time. After you build each Statement,
call `show_hive` on it to read what will run.

### Run it

`run` turns the Statement into Hive, hands it to a send, and gives back the DataFrame the send
returns. Here the Example database's send runs it:

>>> run(failed, send=example_database.send)
   run_id  job_id          dt
0      97       3  2026-09-23
1     102       2  2026-09-24

At work it is the same call with your own send, `run(failed, send=send)`, and a Statement that
reads your own tables.

## Check it worked

The import ran without stopping. Keep what `run` gives back, and check that it is a pandas
DataFrame holding the two failed runs:

>>> import pandas as pd
>>> result = run(failed, send=example_database.send)
>>> isinstance(result, pd.DataFrame)
True
>>> len(result)
2

At work, try your own send on its own, with a query that reads no table, such as
`send("SELECT 1 AS one")`. A working send gives back a pandas DataFrame with one column, named
`"one"`. The Example database's send shows what to expect:

>>> example_database.send("SELECT 1 AS one")
   one
0    1

## Common mistakes

### A send that gives back the wrong thing

[sqlglot_composer only]
Many query APIs give each row as a tuple, without the column names. A send that hands those
rows to `pd.DataFrame` without the names gives back a DataFrame whose columns are numbered 0, 1
and 2. This page has no query API, so a stand-in plays yours here, giving each row as a tuple:

>>> def query_api(hive):
...     answer = example_database.send(hive)
...     return [tuple(row) for row in answer.itertuples(index=False)]
>>> send_without_column_names = lambda hive: pd.DataFrame(query_api(hive))
>>> run(failed, send=send_without_column_names)
     0  1           2
0   97  3  2026-09-23
1  102  2  2026-09-24

Nothing stops it, but no column has its name: reading one by name, such as `"run_id"`, stops
with a `KeyError`. Check that `send("SELECT 1 AS one")` gives back a column named `"one"`. If
it doesn't, pass `pd.DataFrame` the column names your API gives, as the step Write your send
shows.
[end]
[spark_composer only]
`spark.sql(hive)` gives back Spark's own DataFrame, which hasn't fetched its rows yet. A send
that leaves out `.toPandas()` hands that to `run`, which stops: there are no rows yet to count
or read. Your own `spark` isn't in this notebook, so a stand-in plays its DataFrame here; like
Spark's, it has a `toPandas` method, which is how `run` knows it is Spark's:

>>> class SparkDataFrame:
...     def toPandas(self):
...         return pd.DataFrame()
>>> send_without_to_pandas = lambda hive: SparkDataFrame()
>>> run(failed, send=send_without_to_pandas)
Traceback (most recent call last):
...
TypeError:
  What happened:  Your send gave back a Spark DataFrame, where a pandas DataFrame goes.
...

The fix is the message's: end your send with `.toPandas()`.
[end]

### A Statement that doesn't give the days it reads

A table with a Date partition is stored a day at a time, and a Statement that doesn't give the
first and last day to read would read every day the table holds. The Toolbox refuses it as you
build it, before anything runs:

>>> every_failed_run = statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(equals(job_runs.status, "FAILED")),
... )
Traceback (most recent call last):
...
composer_core.refusals.LoadRefused:
  What happened:  FROM(job_runs) reads ops.job_runs, but nothing bounds its Date partition dt at both ends.
...
  Opt-out:        FROM(job_runs, reads_all_partitions=True)

Give the days as the message says, with `between` or `last_n_days` in `WHERE`, as `failed`
does. The message's Opt-out, `reads_all_partitions=True`, reads every day: use it only for a
small table you truly need whole.

### Importing both Editions

[sqlglot_composer only]
Use one Edition in a notebook. After `from sqlglot_composer import *`, a second import line
`from spark_composer import *` stops with a message: the two Editions share `composer_core`,
which writes the Hive for one Edition at a time. Keep one import line, in your notebook and in
any of your own .py files it imports, then restart the notebook's kernel.
[end]
[spark_composer only]
Use one Edition in a notebook. After `from spark_composer import *`, a second import line
`from sqlglot_composer import *` stops with a message: the two Editions share `composer_core`,
which writes the Hive for one Edition at a time. Keep one import line, in your notebook and in
any of your own .py files it imports, then restart the notebook's kernel.
[end]

## Next

- Read one of your own tables: [`write_table_reference`](examples.html#write_table_reference)
  reads a table's columns through your send and writes its Table reference for you.
- Build Statements of your own from the [Example gallery](examples.html), which has a Worked
  example for every Toolbox name, such as [`statement`](examples.html#statement),
  [`run`](examples.html#run) and [`show_hive`](examples.html#show_hive).
- See a job built step by step, each step's Hive shown, in the gallery's
  [Worked example of a job in steps](examples.html#step_by_step).
"""
