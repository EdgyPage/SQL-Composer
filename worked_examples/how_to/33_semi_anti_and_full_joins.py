"""Semi-, anti- and full joins

For: Intermediate

## Goal

Keep the rows that have a match in another table, each once, with `SEMI_JOIN`; keep the rows
that have none with `ANTI_JOIN`; and compare two records of the same things, row for row, with
`FULL_JOIN`. On the way, ask Hive to copy a small table to every worker with `broadcast=True`,
and see why `RIGHT_JOIN` is refused.

## When you'd use it

- **SEMI_JOIN**: the runs that raised an alert, the jobs that ran today. A plain `JOIN` gives
  a row for each match, so a run with three alerts comes out three times; `SEMI_JOIN` keeps it
  once, and adds none of the other table's columns.
- **ANTI_JOIN**: the runs with no alert, the jobs that never ran, the rows a copy is missing.
- **FULL_JOIN**: two systems that should agree, such as the runs `ops.job_runs` holds and the
  runs the scheduler says it started. Each run comes out once, whichever side has it.

## Steps

### Import the Toolbox and name the tables

`ops.scheduler_runs` is the scheduler's own record of the runs it started on the Example
database's two days. It should match `ops.job_runs`, run for run, but doesn't quite.

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs
>>> jobs = example_database.jobs
>>> run_alerts = example_database.run_alerts
>>> scheduler_runs = example_database.scheduler_runs

### See JOIN repeat the runs

Join the alerts to find the runs that raised one, and a run comes out once for each alert:

>>> repeated = statement(
...     SELECT(job_runs.run_id, job_runs.status),
...     FROM(job_runs),
...     JOIN(run_alerts, ON=all_of(equals(run_alerts.run_id, job_runs.run_id),
...                                between(run_alerts.dt, "2026-09-23", "2026-09-24")),
...          many_matches=True),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> run(repeated, send=example_database.send)
   run_id   status
0      97   FAILED
1      97   FAILED
2     101  SUCCESS
3     101  SUCCESS
4     101  SUCCESS
5     102   FAILED
6     103  SUCCESS
7     103  SUCCESS
8     104  SUCCESS

### Keep each run with an alert once, with SEMI_JOIN

`SEMI_JOIN` keeps each run that has a match, once, however many alerts match it, so it needs
no `many_matches=` and gives no repeated-rows Warning. It is written `LEFT SEMI JOIN`. The
alerts' days go inside its `ON=`, since only `ON=` may read its table's columns:

>>> with_an_alert = statement(
...     SELECT(job_runs.run_id, job_runs.status),
...     FROM(job_runs),
...     SEMI_JOIN(run_alerts, ON=all_of(equals(run_alerts.run_id, job_runs.run_id),
...                                     between(run_alerts.dt, "2026-09-23", "2026-09-24"))),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> text = show_hive(with_an_alert)
SELECT
  job_runs.run_id,
  job_runs.status
FROM ops.job_runs AS job_runs
LEFT SEMI JOIN ops.run_alerts AS run_alerts
  ON run_alerts.run_id = job_runs.run_id
  AND run_alerts.dt BETWEEN '2026-09-23' AND '2026-09-24'
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24';
>>> run(with_an_alert, send=example_database.send)
   run_id   status
0      97   FAILED
1     101  SUCCESS
2     102   FAILED
3     103  SUCCESS
4     104  SUCCESS

[sqlglot_composer only]
Pasted into your own notebook, this `run`, and the one of `with_an_alert` under Check it
worked, stops with a RuntimeError saying the Example database can't run a `LEFT SEMI JOIN`:
sqlglot's own small executor doesn't know it. The result above is worked out in pandas
instead. Hive at work runs it, and so does Spark Composer's Example database.
[end]

Since a semi join never repeats rows, the runs keep their Key, run_id: a write of these
rows into a Saved table keyed by run_id is let through, as [Keys, checked before each
write](#keys) explains.

### Keep each run with no alert, with ANTI_JOIN

`ANTI_JOIN` keeps the rows that have no match. Hive 3 has no anti join of its own, so the
Toolbox writes a `LEFT JOIN`, then a `WHERE` that keeps the rows where the column `ON=`
matched is NULL: a run with an alert has its run_id there.

>>> no_alert = statement(
...     SELECT(job_runs.run_id, job_runs.status),
...     FROM(job_runs),
...     ANTI_JOIN(run_alerts, ON=all_of(equals(run_alerts.run_id, job_runs.run_id),
...                                     between(run_alerts.dt, "2026-09-23", "2026-09-24"))),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> text = show_hive(no_alert)
SELECT
  job_runs.run_id,
  job_runs.status
FROM ops.job_runs AS job_runs
LEFT JOIN ops.run_alerts AS run_alerts
  ON run_alerts.run_id = job_runs.run_id
  AND run_alerts.dt BETWEEN '2026-09-23' AND '2026-09-24'
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24' AND run_alerts.run_id IS NULL;
>>> run(no_alert, send=example_database.send)
   run_id   status
0      95  SUCCESS
1      96  SUCCESS
2      98     None
3      99     TEST

The alerts' days are inside `ON=` here too: an alert outside them doesn't count as a match.

### Find the jobs that never ran

[Join tables safely](#join_tables_safely) found cache_warm with a Derived table, a
`LEFT_JOIN` and `is_null`. `ANTI_JOIN` says the same in one clause:

>>> never_ran = statement(
...     SELECT(jobs.job_id, jobs.job_name),
...     FROM(jobs),
...     ANTI_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
...                                   between(job_runs.dt, "2026-09-23", "2026-09-24"))),
... )
>>> text = show_hive(never_ran)
SELECT
  jobs.job_id,
  jobs.job_name
FROM ops.jobs AS jobs
LEFT JOIN ops.job_runs AS job_runs
  ON job_runs.job_id = jobs.job_id
  AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
WHERE
  job_runs.job_id IS NULL;
>>> run(never_ran, send=example_database.send)
   job_id    job_name
0       4  cache_warm

### Compare two records with FULL_JOIN

`FULL_JOIN` pairs the rows that match and keeps the rows of each side that have none, with
NULL in the other side's columns. Each side keeps all of its rows, so its days can't be
bounded in `WHERE`, which would throw away the other side's unmatched rows, nor in `ON=`,
which keeps every row anyway: each side reads its own days in a Derived table first.

>>> recorded = derived("recorded", statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... ))
>>> started = derived("started", statement(
...     SELECT(scheduler_runs.run_id),
...     FROM(scheduler_runs),
...     WHERE(between(scheduler_runs.dt, "2026-09-23", "2026-09-24")),
... ))

`fill_null` takes the run_id from whichever side has one, and `if_else` says where each run
was found:

>>> both_records = statement(
...     SELECT(AS(fill_null(recorded.run_id, started.run_id), "run_id"),
...            AS(if_else(is_null(started.run_id), "only in job_runs",
...                       if_else(is_null(recorded.run_id), "only in scheduler_runs",
...                               "in both")), "found")),
...     FROM(recorded),
...     FULL_JOIN(started, ON=equals(started.run_id, recorded.run_id)),
... )
>>> text = show_hive(both_records)
WITH recorded AS (
  SELECT
    job_runs.run_id
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
), started AS (
  SELECT
    scheduler_runs.run_id
  FROM ops.scheduler_runs AS scheduler_runs
  WHERE
    scheduler_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
)
SELECT
  COALESCE(recorded.run_id, started.run_id) AS run_id,
  CASE
    WHEN started.run_id IS NULL
    THEN 'only in job_runs'
    ELSE CASE WHEN recorded.run_id IS NULL THEN 'only in scheduler_runs' ELSE 'in both' END
  END AS found
FROM recorded
FULL JOIN started
  ON started.run_id = recorded.run_id;
>>> run(both_records, send=example_database.send)
   run_id                   found
0      95                 in both
1      96                 in both
2      97                 in both
3      98                 in both
4      99        only in job_runs
5     100  only in scheduler_runs
6     101                 in both
7     102                 in both
8     103                 in both
9     104                 in both

Run 99, a TEST run started by hand, never went through the scheduler; run 100 was started but
never reached `ops.job_runs`.

### Keep only the differences

A `WHERE` on either side's columns is refused after a `FULL_JOIN`, since it would throw away
rows the join kept, unless it is `is_null(...)`, which keeps a side's rows with no match. So
the runs only one side holds:

>>> differences = statement(
...     SELECT(AS(recorded.run_id, "in_job_runs"), AS(started.run_id, "in_scheduler_runs")),
...     FROM(recorded),
...     FULL_JOIN(started, ON=equals(started.run_id, recorded.run_id)),
...     WHERE(any_of(is_null(recorded.run_id), is_null(started.run_id))),
... )
>>> run(differences, send=example_database.send)
   in_job_runs  in_scheduler_runs
0          NaN              100.0
1         99.0                NaN

pandas shows a whole-number column with a missing value as decimals, with NaN for NULL.

A `FULL_JOIN`'s rows have no Key the Toolbox can see, since either side's run_id may be NULL:
to write them into a Saved table, group them by the run_id that `fill_null` makes, with
`GROUP_BY(fill_null(recorded.run_id, started.run_id))`, which gives them that Key.

### Ask Hive to copy a small table to every worker

`broadcast=True`, on `JOIN`, `LEFT_JOIN`, `SEMI_JOIN` or `ANTI_JOIN`, asks for a map join: the
small table, such as `ops.jobs`, is copied whole to every worker, so each worker matches the
big table's rows where they are, without first sorting them and sending them across the
cluster. The Toolbox writes it as a hint after `SELECT`: a comment, `/*+ ... */`, that Hive
reads as a request.

>>> per_team = statement(
...     SELECT(jobs.team, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), broadcast=True),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(jobs.team),
... )
>>> text = show_hive(per_team)
SELECT /*+ MAPJOIN(jobs) */
  jobs.team,
  COUNT(*) AS runs
FROM ops.job_runs AS job_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = job_runs.job_id
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  jobs.team;
>>> run(per_team, send=example_database.send)
      team  runs
0     data     4
1  finance     5

The rows are the same with it or without it: it only changes how the work is done. Usually
you don't need it. Hive makes map joins by itself, from the tables' sizes and statistics, once
the Session setting "map_joins" is sent with `run(hive_settings("map_joins"), send=...)`.
And Hive heeds the hint only once its setting hive.ignore.mapjoin.hint is false, which you
send as a set of your own:

>>> heed_hints = {"heed_hints": {"hive.ignore.mapjoin.hint": False}}
>>> run(hive_settings("heed_hints", sets=heed_hints), send=example_database.send)

Where your Hive runs on Spark, Spark heeds the hint always. Ask for it only for a table you know is small: copied to
every worker, a big table can run them out of memory.

## Check it worked

Every run either has an alert or hasn't, so the runs `SEMI_JOIN` keeps and the runs
`ANTI_JOIN` keeps add up to all the runs of the two days:

>>> every_run = statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> len(run(every_run, send=example_database.send))
9
>>> alerted = len(run(with_an_alert, send=example_database.send))
>>> not_alerted = len(run(no_alert, send=example_database.send))
>>> alerted + not_alerted
9

And the `FULL_JOIN` gave 10 rows: the 8 runs in both, and one only in each.

## Common mistakes

### Reading a SEMI_JOIN's table outside its ON=

`SEMI_JOIN` adds none of the joined table's columns, so asking for one is refused. To show
each alert's severity, `JOIN` the alerts, a row for each; to test it, put the test in `ON=`.

>>> severities = statement(
...     SELECT(job_runs.run_id, run_alerts.severity),
...     FROM(job_runs),
...     SEMI_JOIN(run_alerts, ON=all_of(equals(run_alerts.run_id, job_runs.run_id),
...                                     between(run_alerts.dt, "2026-09-23", "2026-09-24"))),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  SELECT reads run_alerts.severity, a column of run_alerts, which SEMI_JOIN only tests.
...

### Bounding an ANTI_JOIN's days in WHERE

Every column of an `ANTI_JOIN`'s table is NULL in the rows it keeps, so `WHERE` can't test
one, the days included. They go inside `ON=`, as in the steps:

>>> careless = statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     ANTI_JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id)),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           between(run_alerts.dt, "2026-09-23", "2026-09-24")),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  WHERE reads run_alerts.dt, a column of run_alerts, which ANTI_JOIN only tests.
...

### A WHERE on a FULL_JOIN's table

Testing a side's column in `WHERE` throws away the rows the other side has and it lacks, so
it is refused. Pick each side's rows in its own Derived table instead.

>>> only_job_1 = statement(
...     SELECT(recorded.run_id, AS(started.run_id, "started")),
...     FROM(recorded),
...     FULL_JOIN(started, ON=equals(started.run_id, recorded.run_id)),
...     WHERE(more_than(recorded.run_id, 100)),
... )
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  WHERE has recorded.run_id > 100, a condition on recorded, and FULL_JOIN(started) keeps the rows of both sides that have no match.
...

### Writing a RIGHT_JOIN

A RIGHT JOIN keeps every row of the table it joins. The Toolbox doesn't write one: swap the
two tables, putting the one whose every row you want in `FROM`, and `LEFT_JOIN` the other.

>>> RIGHT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id))
Traceback (most recent call last):
...
ValueError:
  What happened:  RIGHT_JOIN(jobs, ...): the Toolbox doesn't write a RIGHT JOIN.
...

## Next

- [Join tables safely](#join_tables_safely): `JOIN`, `LEFT_JOIN` and the repeated-rows Warning.
- [Keys, checked before each write](#keys): which joins keep a table's Key.
- The gallery's Worked examples of [`SEMI_JOIN`](examples.html#SEMI_JOIN),
  [`ANTI_JOIN`](examples.html#ANTI_JOIN), [`FULL_JOIN`](examples.html#FULL_JOIN) and
  [`RIGHT_JOIN`](examples.html#RIGHT_JOIN).
"""

import pandas as pd

from sqlglot_composer import (
    FROM, SELECT, WHERE, between, example_database, run, statement,
)


# sqlglot Composer's Example database can't run a LEFT SEMI JOIN, so the page and the doctest
# get with_an_alert's result from this, worked out in pandas from two Statements it can run.
# Spark Composer's runs the Hive itself, and its result must match.


def with_an_alert_in_pandas() -> pd.DataFrame:
    job_runs, run_alerts = example_database.job_runs, example_database.run_alerts
    runs = run(statement(SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
                         WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"))),
               send=example_database.send)
    alerted = run(statement(SELECT(run_alerts.run_id), FROM(run_alerts),
                            WHERE(between(run_alerts.dt, "2026-09-23", "2026-09-24"))),
                  send=example_database.send)
    kept = runs[runs["run_id"].isin(alerted["run_id"])]
    return kept.sort_values("run_id").reset_index(drop=True)
