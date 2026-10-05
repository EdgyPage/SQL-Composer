"""Filter rows

For: Getting started

## Goal

Keep only the rows you want, with the condition functions `WHERE` takes: the days to read,
an exact value, a number above or below a line, one of a list, a piece of text, one condition
or another, and missing values (NULL). Each step shows the condition's Hive and the rows it
keeps on the Example database, so you can see each one work.

## When you'd use it

In nearly every Statement. Every Statement on a table with a Date partition gives the days it
reads, and most keep only some rows of those days: the failed runs, the jobs of one team, the
runs that took too long.

## Steps

### Import the Toolbox and name the tables

>>> from sqlglot_composer import *
>>> jobs = example_database.jobs
>>> job_runs = example_database.job_runs

`ops.job_runs` holds nine runs, five on 2026-09-23 and four on 2026-09-24. Run 98 is still
running, so its status is missing: NULL, which pandas shows as None.

### Give the days to read

Each Statement on `job_runs` gives the first and the last day it reads, through its Date
partition, `job_runs.dt`. There are three ways to write them:

- `equals(job_runs.dt, "2026-09-24")` reads one day;
- `between(job_runs.dt, "2026-09-23", "2026-09-24")` reads from the first day to the last, both
  included;
- `last_n_days(job_runs.dt, 7)` reads the 7 days before today, today itself left out.

>>> two_days = statement(
...     SELECT(job_runs.run_id, job_runs.status, job_runs.duration_mins, job_runs.dt),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> run(two_days, send=example_database.send)
   run_id   status  duration_mins          dt
0      95  SUCCESS             12  2026-09-23
1      96  SUCCESS             18  2026-09-23
2      97   FAILED             30  2026-09-23
3      98     None             15  2026-09-23
4      99     TEST              5  2026-09-23
5     101  SUCCESS             10  2026-09-24
6     102   FAILED             20  2026-09-24
7     103  SUCCESS             30  2026-09-24
8     104  SUCCESS             40  2026-09-24

`last_n_days` writes its days into the Hive as dates, counted back from the day you build the
Statement. These steps ran as if today were 2026-09-25, so it gives the same two days:

>>> recent = statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(last_n_days(job_runs.dt, 2)),
... )
>>> text = show_hive(recent)
SELECT
  job_runs.run_id
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24';

In your own notebook today is your real today, so on the Example database write `between` with
the dates instead.

### Keep one value

`equals` keeps the rows where a column holds one value. `WHERE` keeps a row only if every
condition in it holds, so the days and the status go side by side:

>>> failed = statement(
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           equals(job_runs.status, "FAILED")),
... )
>>> run(failed, send=example_database.send)
   run_id  job_id          dt
0      97       3  2026-09-23
1     102       2  2026-09-24

### Keep numbers above or below a line

`at_least` (>=), `at_most` (<=), `more_than` (>) and `less_than` (<) compare a column with a
number. Two of them make a range:

>>> middling = statement(
...     SELECT(job_runs.run_id, job_runs.duration_mins),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           at_least(job_runs.duration_mins, 15), less_than(job_runs.duration_mins, 30)),
... )
>>> text = show_hive(middling)
SELECT
  job_runs.run_id,
  job_runs.duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  AND job_runs.duration_mins >= 15
  AND job_runs.duration_mins < 30;
>>> run(middling, send=example_database.send)
   run_id  duration_mins
0      96             18
1      98             15
2     102             20

### Keep one of a list

`is_in` keeps the rows whose value is in a Python list, and `is_not_in` those whose value
isn't. Here, the runs of jobs 1 and 3:

>>> some_jobs = statement(
...     SELECT(job_runs.run_id, job_runs.job_id),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"), is_in(job_runs.job_id, [1, 3])),
... )
>>> text = show_hive(some_jobs)
SELECT
  job_runs.run_id,
  job_runs.job_id
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24' AND job_runs.job_id IN (1, 3);
>>> run(some_jobs, send=example_database.send)
   run_id  job_id
0      95       1
1      97       3
2      99       1
3     101       1
4     103       3
5     104       1

The list can come from anywhere in your notebook, such as a column of another result. Here,
every run of the jobs that failed at least once, with the job_ids from the result of
`failed`, above:

>>> failed_jobs = run(failed, send=example_database.send)["job_id"].tolist()
>>> failed_jobs
[3, 2]
>>> runs_of_failed_jobs = statement(
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           is_in(job_runs.job_id, failed_jobs)),
... )
>>> run(runs_of_failed_jobs, send=example_database.send)
   run_id  job_id   status
0      96       2  SUCCESS
1      97       3   FAILED
2      98       2     None
3     102       2   FAILED
4     103       3  SUCCESS

`.tolist()` turns the pandas column into a plain Python list.

### Keep text that contains or starts with a word

`contains` keeps the rows whose text holds a piece of text anywhere, and `starts_with` those
whose text begins with it. `ops.jobs` has no days, so it needs no Date partition bound:

>>> named = statement(
...     SELECT(jobs.job_id, jobs.job_name),
...     FROM(jobs),
...     WHERE(contains(jobs.job_name, "sync")),
... )
>>> text = show_hive(named)
SELECT
  jobs.job_id,
  jobs.job_name
FROM ops.jobs AS jobs
WHERE
  jobs.job_name LIKE '%sync%';
>>> run(named, send=example_database.send)
   job_id      job_name
0       2  invoice_sync

In the Hive, `LIKE '%sync%'` means "sync, with anything before and after it". Both functions
match the text exactly as you give it, capitals and all.

### Keep one condition or another

`any_of` keeps a row where at least one of its conditions holds: SQL's OR. Here, the runs
that failed or took 30 minutes or more:

>>> to_check = statement(
...     SELECT(job_runs.run_id, job_runs.status, job_runs.duration_mins),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           any_of(equals(job_runs.status, "FAILED"), at_least(job_runs.duration_mins, 30))),
... )
>>> text = show_hive(to_check)
SELECT
  job_runs.run_id,
  job_runs.status,
  job_runs.duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  AND (
    job_runs.status = 'FAILED' OR job_runs.duration_mins >= 30
  );
>>> run(to_check, send=example_database.send)
   run_id   status  duration_mins
0      97   FAILED             30
1     102   FAILED             20
2     103  SUCCESS             30
3     104  SUCCESS             40

The Hive puts brackets around the OR, so the days still hold for every row kept.

`all_of` groups conditions that must all hold, for use inside `any_of`. Here: job 1's runs of
30 minutes or more, or any run that failed:

>>> slow_or_failed = statement(
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           any_of(all_of(equals(job_runs.job_id, 1), at_least(job_runs.duration_mins, 30)),
...                  equals(job_runs.status, "FAILED"))),
... )
>>> text = show_hive(slow_or_failed)
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.status,
  job_runs.duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  AND (
    (
      job_runs.job_id = 1 AND job_runs.duration_mins >= 30
    )
    OR job_runs.status = 'FAILED'
  );
>>> run(slow_or_failed, send=example_database.send)
   run_id  job_id   status  duration_mins
0      97       3   FAILED             30
1     102       2   FAILED             20
2     104       1  SUCCESS             40

### Find missing values

A missing value is NULL. `is_null` keeps the rows where a column is NULL, and `is_not_null`
the rows where it holds a value. Run 98 has no status yet:

>>> still_running = statement(
...     SELECT(job_runs.run_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"), is_null(job_runs.status)),
... )
>>> text = show_hive(still_running)
SELECT
  job_runs.run_id,
  job_runs.status
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24' AND job_runs.status IS NULL;
>>> run(still_running, send=example_database.send)
   run_id status
0      98   None

## Check it worked

Check a Statement's rows against the same condition worked out in pandas, on every row of the
days it reads. Here, `to_check`: the runs that failed or took 30 minutes or more.

>>> kept = run(to_check, send=example_database.send)
>>> every_run = run(two_days, send=example_database.send)
>>> in_pandas = every_run[(every_run["status"] == "FAILED") | (every_run["duration_mins"] >= 30)]
>>> list(in_pandas["run_id"]) == list(kept["run_id"])
True

The same rows, worked out twice. At work, do this on a day small enough to look at, and look
at a few of the rows left out too.

## Common mistakes

### Comparing with None

`equals(job_runs.status, None)` looks like the way to find run 98, but in SQL nothing equals
NULL, not even NULL, so it would keep no rows at all. The Toolbox stops it:

>>> no_status = statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"), equals(job_runs.status, None)),
... )
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  equals(job_runs.status, None) compares with None.
...

Use `is_null(job_runs.status)`, as the step Find missing values does. A None in a list given
to `is_in` stops the same way.

### Expecting not_equals to keep NULL

pandas' `!=` keeps a row whose value is missing; SQL's `<>`, which `not_equals` writes, drops
it. Leaving out the TEST runs on 2026-09-23 also leaves out run 98, still running:

>>> not_test = statement(
...     SELECT(job_runs.run_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-23"), not_equals(job_runs.status, "TEST")),
... )
>>> run(not_test, send=example_database.send)
   run_id   status
0      95  SUCCESS
1      96  SUCCESS
2      97   FAILED

Nothing stops this, since the Toolbox can't know which columns may be NULL. To keep run 98,
ask for the NULL rows too:

>>> not_test = statement(
...     SELECT(job_runs.run_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-23"),
...           any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
... )
>>> run(not_test, send=example_database.send)
   run_id   status
0      95  SUCCESS
1      96  SUCCESS
2      97   FAILED
3      98     None

`is_not_in` drops NULL rows the same way.

### Two conditions on one column in WHERE

`WHERE` keeps a row only if every condition holds, and no run is both FAILED and TEST, so this
keeps nothing, without any message:

>>> failed_and_test = statement(
...     SELECT(job_runs.run_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           equals(job_runs.status, "FAILED"), equals(job_runs.status, "TEST")),
... )
>>> run(failed_and_test, send=example_database.send)
Empty DataFrame
Columns: [run_id, status]
Index: []

For one value or another, use `is_in(job_runs.status, ["FAILED", "TEST"])`, or `any_of`.

### A value of the wrong type

`job_runs.job_id` holds numbers. Comparing it with text, as if `"3"` were 3, would leave the
warehouse to convert one into the other, which can quietly match nothing. The Toolbox stops it:

>>> job_3 = statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"), equals(job_runs.job_id, "3")),
... )
Traceback (most recent call last):
...
TypeError:
  What happened:  equals(job_runs.job_id, ...) compares job_runs.job_id, a bigint column, with '3'.
...

Write `equals(job_runs.job_id, 3)`.

### The days the wrong way round

>>> backwards = statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-24", "2026-09-23")),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  between(job_runs.dt, '2026-09-24', '2026-09-23') starts after it ends.
...

## Next

- Count and add up the rows you kept, per job or per day:
  [Count and add up per group](#count_and_add_up_per_group).
- Keep conditions you use again and again in one place:
  [Reusable Derived tables](#reusable_derived_tables).
- The gallery's Worked examples of each condition, such as
  [`between`](examples.html#between), [`is_in`](examples.html#is_in) and
  [`any_of`](examples.html#any_of), and the traps side by side with their fixes:
  [`not_equals` drops NULL](examples.html#not_equals_drops_null),
  [None in `equals`](examples.html#none_in_equals) and
  [lists and text](examples.html#lists_and_text).
"""
