"""Keep queries small with Load limits

For: Getting started

## Goal

Stop a Statement before it reads, or brings back, more than the cluster or your notebook can
take. You switch on the two Load limits that are off until you switch them on, a LIMIT added
to every query and a cap on the days one Statement reads, with `set_load_limits`; you read
what each refusal says; and you learn when its opt-out is the right answer.

## When you'd use it

In the first cell of every notebook at work, after the import and your send. A Load limit
protects the cluster everyone shares, and your notebook's memory: a query that reads a year of
a big table, or brings back millions of rows, can stall both. It matters most when you explore
a table you don't know yet, or share a notebook with someone new to the warehouse.

Load limits aren't Guards. A Guard stops a Statement that would give a wrong answer; a Load
limit stops one that would cost too much, and its answer would have been right.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs

### Know the Load limits that are always on

Two Load limits need no switching on:

- Every table with a Date partition must have its days bounded at both ends, or the Statement
  is refused as you build it, as [Start a notebook](#start_a_notebook) shows.
- `ORDER_BY` without a `LIMIT` is refused, since the warehouse would sort every row before
  sending any back: sort in pandas instead. Common mistakes, below, shows it.

The other two are off until you switch them on, since only you know how much your cluster
and notebook can take.

### Switch on the other two

`set_load_limits` takes two numbers:

- `rows=`: a LIMIT added to every query that has none of its own, and a refusal when a result
  fills it, since it was then probably cut short;
- `dates=`: the most days one Statement may read from one table.

At work, `set_load_limits(rows=100000, dates=31)` is a good start. The Example database is
tiny, so this page sets small numbers, to see each limit at work:

>>> set_load_limits(rows=5, dates=7)
{'rows': 5, 'dates': 7}

It gives back the limits now in force. Call it in your own notebook, never inside the
Toolbox's folders, which you replace with each update.

### See the automatic LIMIT

Every query without a LIMIT of its own now gets one, at the end of its Hive:

>>> all_runs = statement(
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> text = show_hive(all_runs)
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.status
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
LIMIT 5;

A write, such as INSERT OVERWRITE, never gets one: its rows go into a table, not into your
notebook, and a LIMIT would quietly drop some of them.

### Read what a refusal says

The two days hold 9 runs. With the LIMIT, the warehouse sends back 5, exactly the limit, so
the result was probably cut short. `run` refuses it, rather than hand you 5 of 9 rows as if
they were all:

>>> run(all_runs, send=example_database.send)
Traceback (most recent call last):
...
composer_core.refusals.LoadRefused:
  What happened:  run(...) got back 5 rows, exactly the automatic LIMIT set by set_load_limits(rows=...).
...

Like every refusal, its message has four parts: what happened, why it matters, the usual fix
and the opt-out. The usual fix comes first: ask for fewer rows, with fewer days or more
conditions in WHERE. A result under the limit comes back as usual:

>>> failed = statement(
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           equals(job_runs.status, "FAILED")),
... )
>>> run(failed, send=example_database.send)
   run_id  job_id  status
0      97       3  FAILED
1     102       2  FAILED

### Bring back every row when you mean to

The opt-out, `returns_all_rows=True`, goes on `statement(...)`. It sends the query without the
automatic LIMIT, and never refuses its result:

>>> all_runs_whole = statement(
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     returns_all_rows=True,
... )
>>> run(all_runs_whole, send=example_database.send)
   run_id  job_id  status
0      95       1  SUCCESS
1      96       2  SUCCESS
2      97       3   FAILED
3      98       2     None
4      99       1     TEST
5     101       1  SUCCESS
6     102       2   FAILED
7     103       3  SUCCESS
8     104       1  SUCCESS

It is right when you know how big the result is, and that your notebook can hold it, such as
one row per job, or a result you will save straight to a file. It is wrong as a way to make the
refusal go away from a result whose size you don't know.

### Cap the days one Statement reads

`ops.job_events`, another of the Example database's tables, holds 14 days of each job's
events: when it started, finished, retried or failed. A Statement counting its events over ten
days reads more than the 7 set. It is refused as soon as its Hive is written, by `show_hive`,
`to_hive` or `run`, before anything is sent:

>>> job_events = example_database.job_events
>>> ten_days = statement(
...     SELECT(job_events.dt, AS(count_rows(), "events")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-15", "2026-09-24")),
...     GROUP_BY(job_events.dt),
... )
>>> text = show_hive(ten_days)
Traceback (most recent call last):
...
composer_core.refusals.LoadRefused:
  What happened:  FROM(job_events) reads 10 days of ops.job_events, more than the 7 set by set_load_limits(dates=...).
...

Its usual fix is to send one day at a time. `by_day` cuts the Statement into 10, each reading
one day, which the cap lets through:

>>> days = by_day(ten_days)
>>> len(days)
10
>>> print(to_hive(days[0]))
SELECT
  job_events.dt,
  COUNT(*) AS events
FROM ops.job_events AS job_events
WHERE
  job_events.dt = '2026-09-15'
GROUP BY
  job_events.dt
LIMIT 5

Each day's query keeps the automatic `LIMIT 5`, but gives one row, well under it. Run them one
after another, and put their results together in pandas with `pd.concat`:

>>> import pandas as pd
>>> results = [run(day, send=example_database.send) for day in days]
>>> pd.concat(results, ignore_index=True)
           dt  events
0  2026-09-15       4
1  2026-09-16       5
2  2026-09-17       4
3  2026-09-18       6
4  2026-09-19       2
5  2026-09-20       2
6  2026-09-21       6
7  2026-09-22       4
8  2026-09-23       4
9  2026-09-24       3

The opt-out, `reads_all_partitions=True` on `FROM`, reads the days without a cap. It is right
for a small table you truly need whole, not for a big one.

### Switch them off

`set_load_limits()` with nothing in it switches both off again:

>>> set_load_limits()
{'rows': None, 'dates': None}

## Check it worked

Set the limits you use at work, and check that a query's Hive ends with the LIMIT:

>>> set_load_limits(rows=100000, dates=31)
{'rows': 100000, 'dates': 31}
>>> print(to_hive(all_runs).splitlines()[-1])
LIMIT 100000

A Statement that reads more than 31 days is now refused, and one with a LIMIT of its own keeps
it.

## Common mistakes

### A limit written as text

A limit is a whole number of rows or days, 1 or more. Anything else is refused at once, so a
typo can't quietly switch a limit off:

>>> set_load_limits(rows="100000")
Traceback (most recent call last):
...
ValueError:
  What happened:  set_load_limits(rows='100000'): a limit must be a whole number, 1 or more, or None for no limit.
...

### A LIMIT of your own to make the refusal go away

A LIMIT you write yourself is never refused: the Toolbox takes it that you want only that many
rows. So `LIMIT(5)` brings back 5 of the 9 runs, and nothing says the rest are missing:

>>> first_five = statement(
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     LIMIT(5),
... )
>>> run(first_five, send=example_database.send)
   run_id  job_id   status
0      95       1  SUCCESS
1      96       2  SUCCESS
2      97       3   FAILED
3      98       2     None
4      99       1     TEST

Use your own LIMIT for a top N, after `ORDER_BY`, not to hush the row limit. Which rows a LIMIT
without `ORDER_BY` keeps is up to the warehouse.

### ORDER_BY without a LIMIT

Sorting is refused unless a LIMIT keeps only the first rows:

>>> statement(
...     SELECT(job_runs.run_id, job_runs.duration_mins),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     ORDER_BY(job_runs.duration_mins),
... )
Traceback (most recent call last):
...
composer_core.refusals.LoadRefused:
  What happened:  ORDER_BY has no LIMIT.
...

Sort the rows in pandas once they are back, with sort_values, or add a LIMIT for a top N. The
message's opt-out, `sorts_everything=True` on `ORDER_BY`, is right only for a result you know
is small.

### A joined table over the cap

The cap counts the days of every table a Statement reads, a joined one too. `by_day` splits only
the days of the table in `FROM`, so for a joined table the message says to narrow its days
instead:

>>> run_alerts = example_database.run_alerts
>>> text = show_hive(statement(
...     SELECT(run_alerts.alert_id, job_runs.status),
...     FROM(run_alerts),
...     JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
...     WHERE(equals(run_alerts.dt, "2026-09-24"),
...           between(job_runs.dt, "2026-08-01", "2026-09-24")),
... ))
Traceback (most recent call last):
...
composer_core.refusals.LoadRefused:
  What happened:  JOIN(job_runs, ON=...) reads 55 days of ops.job_runs, more than the 31 set by set_load_limits(dates=...).
...

An alert's run happened on the alert's day or just before it, so a day or two of `job_runs` is
enough: `between(job_runs.dt, "2026-09-23", "2026-09-24")`.

## Next

- Cut a long range into days, and send them in order:
  [Backfill a range of days](#backfill_a_range_of_days).
- Guards and Warnings, which protect the answer rather than the cluster:
  [Guards, Warnings and opt-outs](#guards_warnings_and_opt_outs).
- The gallery's [`set_load_limits`](examples.html#set_load_limits) and
  [`LoadRefused`](examples.html#LoadRefused) entries.
"""
