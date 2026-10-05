"""Build a first Statement and paste its Hive

For: Getting started

## Goal

Build a Statement a clause at a time, reading its Hive after each change, then run it, and
copy the finished Hive into another program, such as Hue, Beeline, DBeaver or spark-sql,
exactly as `run` sends it. Three functions do the work: `to_hive` gives the Hive as text,
`show_hive` prints it ready to paste, and `run` runs it through a send and gives back a pandas
DataFrame.

## When you'd use it

- Every time you write a new Statement: read its Hive before you run it.
- When someone who doesn't use Python needs the query: a colleague, a dashboard, a scheduled
  job, or your warehouse's own editor, where you can run it again by hand.
- When a result looks wrong: the Hive shows exactly what the warehouse was asked.

## Steps

### Import the Toolbox and name the table

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs

The question here is: which runs on 2026-09-24 took 20 minutes or more?

### Start with SELECT, FROM and the day

Start with the columns you want, the table, and the day to read. `equals(job_runs.dt,
"2026-09-24")` reads one day: it gives the first and the last day at once.

>>> runs_that_day = statement(
...     SELECT(job_runs.run_id, job_runs.status, job_runs.duration_mins),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
... )

`runs_that_day` is a Statement: Python's own object, which holds the clauses and hasn't run
anything. Shown on its own, it says what it reads, and how to see its Hive:

>>> runs_that_day
<Statement reading ops.job_runs - print(to_hive(s)) shows its Hive>

### Read its Hive

`to_hive` gives the Hive as text. `print` shows the text as it is, one clause per line:

>>> print(to_hive(runs_that_day))
SELECT
  job_runs.run_id,
  job_runs.status,
  job_runs.duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24'

`job_runs.dt = '2026-09-24'` is how the Hive reads one day. `FROM ops.job_runs AS job_runs`
reads the table and calls it job_runs, which is why every column in the Hive starts with
`job_runs.`, just as it does in your Python.

### Add a condition, and read the Hive again

`WHERE` takes any number of conditions, and keeps a row only if every one holds. Add a second
one: at least 20 minutes.

>>> long_runs = statement(
...     SELECT(job_runs.run_id, job_runs.status, job_runs.duration_mins),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24"), at_least(job_runs.duration_mins, 20)),
... )
>>> print(to_hive(long_runs))
SELECT
  job_runs.run_id,
  job_runs.status,
  job_runs.duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24' AND job_runs.duration_mins >= 20

The two conditions are joined with AND. Comparing the Hive before and after a change is the
quickest way to see what the change did.

### Name a column in the result

`AS` gives a column the name you want in the result, here `"minutes"` in place
of `"duration_mins"`:

>>> long_runs = statement(
...     SELECT(job_runs.run_id, job_runs.status, AS(job_runs.duration_mins, "minutes")),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24"), at_least(job_runs.duration_mins, 20)),
... )

`WHERE` still uses `job_runs.duration_mins`: the new name is the result's, and WHERE reads the
table.

### Print it ready to paste

`show_hive` prints the same Hive as `to_hive` with a `;` at the end, which Hue, Beeline,
DBeaver and spark-sql need to tell one Statement from the next:

>>> text = show_hive(long_runs)
SELECT
  job_runs.run_id,
  job_runs.status,
  job_runs.duration_mins AS minutes
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24' AND job_runs.duration_mins >= 20;

Copy what it prints, from `SELECT` to the `;`, and paste it into the other program. It gives
back the same text too, kept here as `text`.

### Print several at once

Give `show_hive` several Statements, and it prints them all, each headed by a comment line
starting `--`, which Hive skips. The comment gives its number and the name of the variable
it is in:

>>> text = show_hive(runs_that_day, long_runs)
-- 1 of 2: runs_that_day
SELECT
  job_runs.run_id,
  job_runs.status,
  job_runs.duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24';
<BLANKLINE>
-- 2 of 2: long_runs
SELECT
  job_runs.run_id,
  job_runs.status,
  job_runs.duration_mins AS minutes
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24' AND job_runs.duration_mins >= 20;

Paste the lot into a program that runs several Statements in a row, such as a Beeline script.

### Save it to a file

`text` is a plain Python string, so Python can write it to a file, for a program that reads
its SQL from a file, such as `beeline -f long_runs.sql`:

>>> from pathlib import Path
>>> Path("long_runs.sql").write_text(text)
362

`Path.write_text` gives back how many characters it wrote.

### Run it

`run` turns the Statement into Hive, exactly the text `to_hive` gave, without the `;`, hands
it to a send, and gives back the pandas DataFrame the send returns:

>>> result = run(long_runs, send=example_database.send)
>>> result
   run_id   status  minutes
0     102   FAILED       20
1     103  SUCCESS       30
2     104  SUCCESS       40

The column names are the Statement's: `"minutes"`, as `AS` named it. From here it is pandas:

>>> print(result["minutes"].sum())
90

At work, pass your own send in place of `example_database.send`, as
[Start a notebook](#start_a_notebook) shows.

## Check it worked

The file holds exactly the Hive `run` sends, `to_hive`'s text, with a `;` at the end:

>>> to_hive(long_runs) + ";" in Path("long_runs.sql").read_text()
True

The result holds the three runs of 20 minutes or more:

>>> list(result["run_id"])
[102, 103, 104]

## Common mistakes

### Showing the Hive without print

In a notebook, `to_hive(long_runs)` on its own line shows the text as Python writes a string,
with each line break written `\\n`:

>>> to_hive(long_runs)
"SELECT\\n  job_runs.run_id,\\n  job_runs.status,\\n  job_runs.duration_mins AS minutes\\nFROM ops.job_runs AS job_runs\\nWHERE\\n  job_runs.dt = '2026-09-24' AND job_runs.duration_mins >= 20"

Wrap it in `print(...)`, or use `show_hive`, which prints it for you.

### Giving run the Hive text

`run` takes the Statement and makes the Hive itself, so it can check it first. Given the text,
it stops:

>>> run(to_hive(long_runs), send=example_database.send)
Traceback (most recent call last):
...
TypeError:
  What happened:  to_hive was given "SELECT...", which isn't a Statement.
...

Pass the Statement itself: `run(long_runs, send=example_database.send)`.

### Giving a send the Statement

A send works the other way round: it takes Hive text, not a Statement. The Example database's
send stops:

>>> example_database.send(long_runs)
Traceback (most recent call last):
...
TypeError:
  What happened:  example_database.send was given <Statement reading ops.job_runs - print(to_hive(s)) shows its Hive>, which isn't Hive text.
...

`run(long_runs, send=example_database.send)` makes the text and hands it to the send for you.

### Pasting Hive that was built with last_n_days

The Hive is fixed text once the Statement is built. `last_n_days` counts back from the day you
build the Statement, and writes those days into the Hive as dates. These steps ran as if
today were 2026-09-25:

>>> last_two_days = statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(last_n_days(job_runs.dt, 2)),
... )
>>> text = show_hive(last_two_days)
SELECT
  job_runs.run_id
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24';

Pasted into a job that runs every day, this Hive reads 2026-09-23 and 2026-09-24 every day.
For a job that runs every day, build the Statement again on each day, in Python, and run it
with `run`.

## Next

- Keep only the rows you want, with every kind of condition: [Filter rows](#filter_rows).
- Count and add up per group: [Count and add up per group](#count_and_add_up_per_group).
- The gallery's Worked examples of [`to_hive`](examples.html#to_hive),
  [`show_hive`](examples.html#show_hive) and [`run`](examples.html#run), and a long Statement
  built in named steps: [Worked example of a job in steps](examples.html#step_by_step).
"""
