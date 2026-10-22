"""Backfill a range of days

For: Getting started

## Goal

Write many past days of a Saved table at once. You build the write once, over the whole range
of days, with the day last in its SELECT: each row then goes to its own day's Partition, filled
from the rows, in one write. For a range too long to read at once, a loop writes it a day at a
time instead, each write naming its day with `partition=`.

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
...     partitioned_by=["dt"],
...     key=["job_id", "dt"],
...     location="/data/your_team/mart.db/daily_job_runs",
... )

### Build the write over the whole range

Write the Statement once, as a function of the first and the last day. It reads every day from
`first_day` to `last_day`, and counts per job and per day:

>>> def daily_counts(first_day: str, last_day: str) -> Statement:
...     return statement(
...         INSERT_OVERWRITE(daily_job_runs),
...         SELECT(
...             job_runs.job_id,
...             AS(count_rows(), "runs"),
...             AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...             job_runs.dt,
...         ),
...         FROM(job_runs),
...         WHERE(between(job_runs.dt, first_day, last_day)),
...         GROUP_BY(job_runs.job_id, job_runs.dt),
...     )
>>> backfill = daily_counts("2026-09-23", "2026-09-24")

`GROUP_BY(job_runs.job_id, job_runs.dt)` makes one row per job and day, and `count_rows()`
counts the runs in each; `count_rows(where=...)` counts only those that meet its condition,
which the Hive writes as `COUNT(CASE WHEN ... THEN 1 END)`. See
[`GROUP_BY`](examples.html#GROUP_BY) and [`count_rows`](examples.html#count_rows), or
[Count and add up per group](#count_and_add_up_per_group) from the start.

`job_runs.dt` is in `GROUP_BY`, which keeps each day's counts apart, and last in `SELECT`,
which says which day's Partition each row goes to. `INSERT_OVERWRITE` with no `partition=`
fills the table's partition column from the rows, and replaces only the days the rows hold:
any other day of the table keeps what it held.

### Check the rows first

The same counts as a plain SELECT, run on the Example database. These are the rows the
backfill would save, one per job and day:

>>> preview = statement(
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
>>> run(preview, query=example_database.query)
           dt  job_id  runs  failed_runs
0  2026-09-23       1     2            0
1  2026-09-23       2     2            0
2  2026-09-23       3     1            1
3  2026-09-24       1     2            0
4  2026-09-24       2     1            1
5  2026-09-24       3     1            0

### Print it, ready to paste

`show_hive` prints the write's Hive, ending with a `;`, ready for a program such as Hue,
Beeline or DBeaver. Filling Partitions from the rows needs Hive's dynamic partitioning switched
on, so it prints the two SET lines that do it first:

>>> text = show_hive(backfill)
-- The Session setting "dynamic_partitions": this write fills dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt)
SELECT
  job_runs.job_id,
  COUNT(*) AS runs,
  COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.job_id,
  job_runs.dt;

`text` keeps the same Hive as one string, to save in a file or paste elsewhere.

### Send it

From a notebook, `run` sends the write through your execute, as in
[Start a Project](#start_a_project). It doesn't send the SET lines with it: send the Session
setting first, `hive_settings("dynamic_partitions")`, which holds for as long as your execute's
connection lasts. On this page the Example database's execute stands in for yours: it prints
the first line of each and changes nothing:

>>> run(hive_settings("dynamic_partitions"), execute=example_database.execute)
execute: SET hive.exec.dynamic.partition=true
execute: SET hive.exec.dynamic.partition.mode=nonstrict
>>> run(backfill, execute=example_database.execute)
execute: INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt)

The write is an INSERT OVERWRITE, which replaces the days it writes. So if it fails, say on a
network error, send it again: a day written twice holds the same rows, not twice as many.
Don't backfill with `INSERT_INTO`, which adds rows each time it is sent.

### Backfill a longer range, a day at a time

At work a backfill can cover months, more than one Statement should read at once. Then write
it a day at a time: a function of one day, whose write names its day with
`partition={"dt": day}` and leaves dt out of SELECT, and a Python loop over the days. Python's
`datetime` makes the list of days:

>>> import datetime
>>> def one_day(day: str) -> Statement:
...     return statement(
...         INSERT_OVERWRITE(daily_job_runs, partition={"dt": day}),
...         SELECT(
...             job_runs.job_id,
...             AS(count_rows(), "runs"),
...             AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...         ),
...         FROM(job_runs),
...         WHERE(equals(job_runs.dt, day)),
...         GROUP_BY(job_runs.job_id),
...     )
>>> first = datetime.date(2026, 9, 1)
>>> september = [str(first + datetime.timedelta(days=n)) for n in range(30)]
>>> september[:3]
['2026-09-01', '2026-09-02', '2026-09-03']
>>> writes = [one_day(day) for day in september]
>>> len(writes)
30
>>> for write in writes[:3]:
...     print(to_hive(write).splitlines()[0])
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-01')
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-02')
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-03')

Each names every partition column, so it needs no Session setting. `show_hive(writes)` prints
them all, each headed by its place in the list; a loop sends them, oldest first:

>>> from collections.abc import Callable
>>> def send_backfill(writes: list[Statement], execute: Callable[[str], None]) -> None:
...     for write in writes:
...         run(write, execute=execute)
>>> send_backfill(writes[:2], execute=example_database.execute)
execute: INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-01')
execute: INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-02')

A day the table it reads holds no rows of is written with no rows. If the loop stops halfway,
send it again from the day that failed, or from the start.

## Check it worked

The range write fills dt from its rows, and the day-at-a-time writes come oldest first, with
none missing:

>>> to_hive(backfill).splitlines()[0]
'INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt)'
>>> for write in writes[-2:]:
...     print(to_hive(write).splitlines()[0])
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-29')
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-30')

At work, after the backfill, count the Saved table's rows and runs per day, and compare them
with the same counts from `ops.job_runs`, which the Example database can show here: 5 runs on
2026-09-23 and 4 on 2026-09-24.

>>> runs_per_day = statement(
...     SELECT(job_runs.dt, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.dt),
... )
>>> run(runs_per_day, query=example_database.query)
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

### Leaving the day out of SELECT

A write with no `partition=` takes each row's day from its last column, so one whose SELECT
leaves dt out is refused as you build it:

>>> statement(
...     INSERT_OVERWRITE(daily_job_runs),
...     SELECT(
...         job_runs.job_id,
...         AS(count_rows(), "runs"),
...         AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...     ),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id, job_runs.dt),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(daily_job_runs): it leaves out dt.
...

Add `job_runs.dt` at the end of SELECT, as `daily_counts` does, or name the day with
`partition={"dt": ...}`, as `one_day` does.

### Leaving the day out of GROUP_BY

Group by the job alone, and each row would be one job's total over the whole range, with no
single day to go to. The Toolbox refuses it, as Hive would:

>>> statement(
...     INSERT_OVERWRITE(daily_job_runs),
...     SELECT(
...         job_runs.job_id,
...         AS(count_rows(), "runs"),
...         AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...         job_runs.dt,
...     ),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  SELECT has job_runs.dt, which GROUP_BY leaves out.
...

Add `job_runs.dt` to `GROUP_BY`, as `daily_counts` does. A write of a single day, read with
`equals`, needn't group by the day, as `one_day` shows.

### A range written back to front

`between` takes the earlier day first. With the days swapped, no day is inside the range, and
the Toolbox stops at once rather than write nothing:

>>> daily_counts("2026-09-30", "2026-09-01")
Traceback (most recent call last):
...
ValueError:
  What happened:  between(job_runs.dt, '2026-09-30', '2026-09-01') starts after it ends.
...

## Next

- Write the Project's tables in order: [Run a daily pipeline](#run_a_daily_pipeline).
- Rewrite only the last few days each morning, for rows that arrive late:
  [Incremental loads and late data](#incremental_loads_and_late_data).
- Keep each Statement's reads small:
  [Keep queries small with Load limits](#keep_queries_small_with_load_limits).
- Each name's own entry in the gallery: [`INSERT_OVERWRITE`](examples.html#INSERT_OVERWRITE),
  [`hive_settings`](examples.html#hive_settings) and [`show_hive`](examples.html#show_hive),
  and the [Saved table example](examples.html#saved_table).
"""
