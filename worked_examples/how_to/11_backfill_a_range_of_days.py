"""Backfill a range of days

For: Getting started

## Goal

Write many past days of a Saved table at once. You build the day's write once, over the whole
range of days, let `by_day` cut it into one write per day, oldest first, and print them all
with `show_hive`, ready to paste into another program or to send one after another.

## When you'd use it

To backfill is to write days that have already happened. You need it:

- when a Saved table is new, and its past days are empty;
- after fixing a mistake in a write, since every day it wrote holds the mistake;
- after rebuilding a Saved table whose columns changed, as in [Save a table](#save_a_table);
- when the daily run was missed for a few days.

The Example database can't be written to, so on this page the writes show their Hive, and the
rows they would save are checked with a plain SELECT, which the Example database does run.

## Steps

### Import the Toolbox and describe the Saved table

The Saved table, mart.daily_job_runs, holds one row per job and day: how many times the job
ran, and how many of those runs failed. Its Table reference is written by hand, as in
[Save a table](#save_a_table):

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs
>>> daily_job_runs = Table(
...     "mart.daily_job_runs",
...     columns={
...         "job_id": "bigint",
...         "runs": "bigint",
...         "failed_runs": "bigint",
...         "dt": "string",  # the day of the runs, as yyyy-MM-dd
...     },
...     date_partition="dt",
...     key=["job_id", "dt"],
... )

### Build the write over the whole range

Write the Statement once, as a function of the first and the last day. It reads every day from
`first_day` to `last_day`, and counts per job and per day:

>>> def daily_counts(first_day, last_day):
...     return statement(
...         INSERT_OVERWRITE(daily_job_runs),
...         SELECT(
...             job_runs.job_id,
...             AS(count_rows(), "runs"),
...             AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...         ),
...         FROM(job_runs),
...         WHERE(between(job_runs.dt, first_day, last_day)),
...         GROUP_BY(job_runs.job_id, job_runs.dt),
...     )
>>> backfill = daily_counts("2026-09-23", "2026-09-24")

`job_runs.dt` is in `GROUP_BY` but not in `SELECT`. In `GROUP_BY`, it keeps each day's counts
apart, so no day's runs are counted with another's. It stays out of `SELECT` because a write
never selects the Date partition: each day's write names its day in its first line instead.

`backfill` reads two days, and a write fills one day, so it can't be sent as it is. The next
steps check its rows, then split it.

### Check the rows first

The same counts as a plain SELECT, with the day shown, run on the Example database. These are
the rows the backfill would save, one per job and day:

>>> check = statement(
...     SELECT(
...         job_runs.dt,
...         job_runs.job_id,
...         AS(count_rows(), "runs"),
...         AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...     ),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.dt, job_runs.job_id),
... )
>>> run(check, send=example_database.send)
           dt  job_id  runs  failed_runs
0  2026-09-23       1     2            0
1  2026-09-23       2     2            0
2  2026-09-23       3     1            1
3  2026-09-24       1     2            0
4  2026-09-24       2     1            1
5  2026-09-24       3     1            0

### Split it into one write per day

`by_day` gives back a list: one Statement per day the range reads, oldest first, each the
same write with its WHERE bounded to its one day.

>>> days = by_day(backfill)
>>> len(days)
2

### Print them all, ready to paste

`show_hive` takes the whole list. It prints each write's Hive, headed by its place in the list
and its name, `days[0]` then `days[1]`, each ending with a `;`, so a program such as Hue,
Beeline or spark-sql runs them one after another, in this order:

>>> text = show_hive(days)
-- 1 of 2: days[0]
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-23')
SELECT
  job_runs.job_id,
  COUNT(*) AS runs,
  COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-23'
GROUP BY
  job_runs.job_id,
  job_runs.dt;
<BLANKLINE>
-- 2 of 2: days[1]
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-24')
SELECT
  job_runs.job_id,
  COUNT(*) AS runs,
  COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24'
GROUP BY
  job_runs.job_id,
  job_runs.dt;

`text` keeps the same Hive as one string, to save in a file or paste elsewhere.

### Send them in order

From a notebook, send each write in turn with `run`. At work, your own send goes where this
shows the Example database's, which would refuse the writes:

    for write in days:
        run(write, send=example_database.send)

Each write is an INSERT OVERWRITE, which replaces its day. So if the loop stops halfway, say
on a network error, send it again from the day that failed, or from the start: a day written
twice holds the same rows, not twice as many. Don't backfill with `INSERT_INTO`, which adds
rows each time it is sent.

### Backfill a longer range

At work a backfill covers weeks or months. The same function builds it, and `by_day` cuts a
month into 30 writes:

>>> september = by_day(daily_counts("2026-09-01", "2026-09-30"))
>>> len(september)
30
>>> for write in september[:3]:
...     print(to_hive(write).splitlines()[0])
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-01')
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-02')
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-03')

`by_day` cuts the range in WHERE into its days, whether or not the table holds rows on each:
a day with no runs is written with no rows. Sending one day at a time also keeps each
Statement small: a Load limit set with `set_load_limits(dates=7)` refuses a Statement that
reads more than 7 days, and each of these reads one. See
[Keep queries small with Load limits](#keep_queries_small_with_load_limits).

## Check it worked

Each write reads exactly one day, the day in its first line, and the days come oldest first,
with none missing:

>>> for write in days:
...     print(to_hive(write).splitlines()[0])
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-23')
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-24')

At work, after the backfill, count the Saved table's rows and runs per day, and compare them
with the same counts from `ops.job_runs`, which the Example database can show here: 5 runs on
2026-09-23 and 4 on 2026-09-24.

>>> runs_per_day = statement(
...     SELECT(job_runs.dt, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.dt),
... )
>>> run(runs_per_day, send=example_database.send)
           dt  runs
0  2026-09-23     5
1  2026-09-24     4

The Statement to run on the Saved table at work adds up `daily_job_runs.runs` per day;
each day's total should match:

>>> saved_per_day = statement(
...     SELECT(daily_job_runs.dt, AS(sum_of(daily_job_runs.runs), "runs")),
...     FROM(daily_job_runs),
...     WHERE(between(daily_job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(daily_job_runs.dt),
... )
>>> text = show_hive(saved_per_day)
SELECT
  daily_job_runs.dt,
  SUM(daily_job_runs.runs) AS runs
FROM mart.daily_job_runs AS daily_job_runs
WHERE
  daily_job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  daily_job_runs.dt;

## Common mistakes

### Sending the whole range as one write

A write fills one day, so the range write is refused as soon as its Hive is written, by
`show_hive`, `to_hive` or `run`. The message's fix is `by_day`:

>>> text = show_hive(backfill)
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(daily_job_runs) covers 2 days.
...

### Leaving the day out of GROUP_BY

Group by the job alone, and the range's counts would add up each job's runs across every day:
one total, not one per day. `by_day` refuses to split it, since each day's partial counts
couldn't always be added back up:

>>> per_job_only = statement(
...     INSERT_OVERWRITE(daily_job_runs),
...     SELECT(
...         job_runs.job_id,
...         AS(count_rows(), "runs"),
...         AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...     ),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
>>> by_day(per_job_only)
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  by_day can't split this Statement: it groups rows without keeping the Date partition job_runs.dt.
...

Add `job_runs.dt` to `GROUP_BY`, as `daily_counts` does.

### A range written back to front

`between` takes the earlier day first. With the days swapped, no day is inside the range, and
the Toolbox stops at once rather than write nothing:

>>> daily_counts("2026-09-30", "2026-09-01")
Traceback (most recent call last):
...
ValueError:
  What happened:  between(job_runs.dt, '2026-09-30', '2026-09-01') starts after it ends.
...

### A LIMIT in a Statement to split

`LIMIT 10` keeps 10 rows of the whole result. Split by day, each day would keep 10 rows of its
own, so `by_day` refuses a Statement with a LIMIT:

>>> some_runs = statement(
...     SELECT(job_runs.run_id, job_runs.dt),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     LIMIT(10),
... )
>>> by_day(some_runs)
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  by_day can't split this Statement: it has LIMIT 10.
...

## Next

- Run the day's writes every morning, in order: [Run a daily pipeline](#run_a_daily_pipeline).
- Cap how many days one Statement may read:
  [Keep queries small with Load limits](#keep_queries_small_with_load_limits).
- Each name's own entry in the gallery: [`by_day`](examples.html#by_day) and
  [`show_hive`](examples.html#show_hive), and the
  [Saved table example](examples.html#saved_table), whose `backfill` writes two Statements a
  day.
"""
