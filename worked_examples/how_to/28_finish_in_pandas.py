"""Look across rows, then finish in pandas

For: Intermediate

## Goal

Work out on the warehouse what looks across the rows around each row: each row's value from
the row before it (lag), a rank within each group (rank), a rolling sum, and a group's total
beside each row, each over a `window`. Keep only some of those rows through a Derived table,
and write a day of a Saved table that looks back on earlier days. Then finish in pandas: put the
results of several Statements side by side with a merge.

## When you'd use it

When a step needs the rows around each row, written OVER (...) in SQL: how a run compares with
the one before it, a running or moving total, a rank. A `window` says which rows: the rows of
each group, in an order, and with `rows=` only those near each row. The warehouse does that
work, reading every row of the days you give it, and hands back the result. And when the
numbers you need come from Statements on different tables, small enough to combine in your
notebook, pandas finishes the job.

## Steps

### Import the Toolbox and name the Window

>>> from sqlglot_composer import *
>>> import pandas as pd
>>> job_events = example_database.job_events
>>> region_costs = example_database.region_costs

A Window names the rows each row looks across. `PARTITION_BY=` makes the groups, here each
job: the word is SQL's, and has nothing to do with a table's Date partition. `ORDER_BY=` puts
each group's rows in order, here by day. Each job finishes at most once a day in the Example
database, so ordering by day gives each job's runs one clear order.

>>> each_jobs_runs = window(PARTITION_BY=job_events.job_id, ORDER_BY=job_events.dt)

And the rows to read, the same in every step: the finished runs of the last week of the
Example database.

>>> week_finished = [between(job_events.dt, "2026-09-18", "2026-09-24"),
...                  equals(job_events.event_type, "finish")]

The Example database runs only part of Hive, and no windows. Pasted into your own notebook,
running a Statement with a Window stops with this message:

>>> run(statement(SELECT(job_events.job_id, AS(lag(job_events.minutes, over=each_jobs_runs),
...                                            "minutes_before")),
...               FROM(job_events), WHERE(*week_finished)), send=example_database.send)
Traceback (most recent call last):
...
RuntimeError:
  What happened:  The Example database can't run this Hive: its executor has no window functions such as row_number.
...

So the results of the Statements below with a Window are what Hive gives at work, worked out
in pandas for this page, as their label says. The Hive is the Hive your warehouse runs.

### The run before: lag

How much faster or slower was each run than the job's run before it? `lag` gives each row the
value of the row before it in its Window's order, and NULL to the first row of each job.
pandas holds a missing number as NaN, and so shows that column with decimals; the tables on
this page show NaN as NULL:

>>> with_before = statement(
...     SELECT(job_events.job_id, job_events.dt, job_events.minutes,
...            AS(lag(job_events.minutes, over=each_jobs_runs), "minutes_before"),
...            AS(job_events.minutes - lag(job_events.minutes, over=each_jobs_runs), "change")),
...     FROM(job_events),
...     WHERE(*week_finished),
... )
>>> text = show_hive(with_before)
SELECT
  job_events.job_id,
  job_events.dt,
  job_events.minutes,
  LAG(job_events.minutes, 1) OVER (PARTITION BY job_events.job_id ORDER BY job_events.dt ASC) AS minutes_before,
  job_events.minutes - LAG(job_events.minutes, 1) OVER (PARTITION BY job_events.job_id ORDER BY job_events.dt ASC) AS change
FROM ops.job_events AS job_events
WHERE
  job_events.dt BETWEEN '2026-09-18' AND '2026-09-24'
  AND job_events.event_type = 'finish';
>>> run(with_before, send=example_database.send)
    job_id          dt  minutes  minutes_before  change
0        1  2026-09-18       14             NaN     NaN
1        1  2026-09-19       11            14.0    -3.0
2        1  2026-09-20       12            11.0     1.0
3        1  2026-09-21       13            12.0     1.0
4        1  2026-09-22       10            13.0    -3.0
5        1  2026-09-23       12            10.0     2.0
6        1  2026-09-24       10            12.0    -2.0
7        2  2026-09-18       22             NaN     NaN
8        2  2026-09-21       21            22.0    -1.0
9        2  2026-09-22       18            21.0    -3.0
10       2  2026-09-23       18            18.0     0.0
11       3  2026-09-21       33             NaN     NaN

The Window sees only the rows the Statement reads: job 1 ran on 2026-09-17 too, but WHERE
starts on 2026-09-18, so its run on 2026-09-18 has no run before it.

### A rank within each group: rank

Which of each job's runs took longest? `rank` numbers each job's runs in its Window's order,
here the longest first, with `descending`. Two runs that tie get the same rank, and the next
run the rank after both, as job 1's two runs of 12 minutes do: both 3, then 5 for its run of
11 minutes:

>>> longest_first = window(PARTITION_BY=job_events.job_id,
...                        ORDER_BY=descending(job_events.minutes))
>>> ranked = statement(
...     SELECT(job_events.job_id, job_events.dt, job_events.minutes,
...            AS(rank(over=longest_first), "longest_first")),
...     FROM(job_events),
...     WHERE(*week_finished),
... )
>>> run(ranked, send=example_database.send)
    job_id          dt  minutes  longest_first
0        1  2026-09-18       14              1
1        1  2026-09-19       11              5
2        1  2026-09-20       12              3
3        1  2026-09-21       13              2
4        1  2026-09-22       10              6
5        1  2026-09-23       12              3
6        1  2026-09-24       10              6
7        2  2026-09-18       22              1
8        2  2026-09-21       21              2
9        2  2026-09-22       18              3
10       2  2026-09-23       18              3
11       3  2026-09-21       33              1

`dense_rank` gives a tie the same rank too, but the next rank follows straight on: 3, 3,
then 4. To keep each
job's one newest run, or its top N, use `row_number`, which never ties: see [The latest row
per key, and the top N per group](#latest_row_per_key).

### A rolling sum, and a group's total beside each row

The minutes of each job's last three runs, added up, beside the job's minutes for the week.
`sum_of(..., over=...)` adds up each row's Window, and gives each row its own total.
`rows=(-2, 0)` keeps only the two rows before each row and the row itself; with no `ORDER_BY`
and no `rows=`, the Window is the whole job:

>>> last_three = statement(
...     SELECT(job_events.job_id, job_events.dt, job_events.minutes,
...            AS(sum_of(job_events.minutes, over=window(
...                PARTITION_BY=job_events.job_id, ORDER_BY=job_events.dt, rows=(-2, 0))),
...               "last_3_runs"),
...            AS(sum_of(job_events.minutes, over=window(PARTITION_BY=job_events.job_id)),
...               "week_minutes")),
...     FROM(job_events),
...     WHERE(*week_finished),
... )
>>> text = show_hive(last_three)
SELECT
...
>>> run(last_three, send=example_database.send)
    job_id          dt  minutes  last_3_runs  week_minutes
0        1  2026-09-18       14           14            82
1        1  2026-09-19       11           25            82
2        1  2026-09-20       12           37            82
3        1  2026-09-21       13           36            82
4        1  2026-09-22       10           35            82
5        1  2026-09-23       12           35            82
6        1  2026-09-24       10           32            82
7        2  2026-09-18       22           22            79
8        2  2026-09-21       21           43            79
9        2  2026-09-22       18           61            79
10       2  2026-09-23       18           57            79
11       3  2026-09-21       33           33            33

It counts runs, not days: invoice_sync, job 2, doesn't run at weekends, so its first three
runs, up to 2026-09-22, span 2026-09-18 to 22, five days, and add up to 61 minutes.

### Keep only some rows: through a Derived table

Which runs were slower than the job's run before? Hive works a Window out after it picks the
rows, so a test on `"change"` can't go in the WHERE of the Statement that works it out (see
Common mistakes). Name that Statement with `derived`, and test it in the Statement that reads
it:

>>> changes = derived("changes", with_before)
>>> slower = statement(
...     SELECT(changes.job_id, changes.dt, changes.change),
...     FROM(changes),
...     WHERE(more_than(changes.change, 0)),
... )
>>> run(slower, send=example_database.send)
   job_id          dt  change
0       1  2026-09-20       1
1       1  2026-09-21       1
2       1  2026-09-23       2

### Write a day that looks back on earlier days

To keep each run's change in a Saved table, day by day, each day's write needs the runs before
it, which may be on earlier days. A write fills one day, so read the earlier days too in a
Derived table that keeps the day column, and keep only the day written in the Statement that
writes, with `WHERE(equals(week.dt, day))`: the Toolbox writes the day that Statement keeps.
Only a write with a Window may read several days like this; any other write must read only the
day it writes. Here a job's run before may be up to 6 days back, so read the day and the 6 before it:

>>> import datetime
>>> run_changes = Table("mart.run_changes", date_partition="dt", key=["event_id", "dt"],
...                     columns={"event_id": "bigint", "job_id": "bigint", "minutes": "int",
...                              "minutes_before": "int", "dt": "string"},
...                     location="/data/your_team/tables", purge=True)
>>> def changes_on(day):
...     week_before = (datetime.date.fromisoformat(day) - datetime.timedelta(days=6)).isoformat()
...     week = derived("week", statement(
...         SELECT(job_events.event_id, job_events.job_id, job_events.dt, job_events.minutes,
...                AS(lag(job_events.minutes, over=each_jobs_runs), "minutes_before")),
...         FROM(job_events),
...         WHERE(between(job_events.dt, week_before, day),
...               equals(job_events.event_type, "finish")),
...     ))
...     return statement(
...         INSERT_OVERWRITE(run_changes),
...         SELECT(week.event_id, week.job_id, week.minutes, week.minutes_before),
...         FROM(week),
...         WHERE(equals(week.dt, day)),
...     )
>>> text = show_hive(changes_on("2026-09-24"))
WITH week AS (
...

The Example database can't be written to, so the write stops here. At work, a function sends
one such Statement for each day, oldest first, through your own send:

    def write_changes(days, send):
        for day in days:
            run(changes_on(day), send=send)

`by_day` can't split a Statement whose Window looks across days: see Common mistakes.

### Merge the results of several Statements

The cost of each minute a job ran comes from two tables: its minutes from `ops.job_events`, and
its cost from `ops.region_costs`. Add up each per job, with a Statement each:

>>> minutes_per_job = statement(
...     SELECT(job_events.job_id, AS(count_rows(), "runs"),
...            AS(sum_of(job_events.minutes), "minutes")),
...     FROM(job_events),
...     WHERE(*week_finished),
...     GROUP_BY(job_events.job_id),
... )
>>> cost_per_job = statement(
...     SELECT(region_costs.job_id, AS(sum_of(region_costs.cost_cents), "cost_cents")),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, "20260918", "20260924")),
...     GROUP_BY(region_costs.job_id),
... )
>>> minutes = run(minutes_per_job, send=example_database.send)
>>> costs = run(cost_per_job, send=example_database.send)

`.merge` puts the two side by side, matching rows on `"job_id"`. `how="outer"` keeps a job that
only one of them has, and `validate="one_to_one"` stops the merge if `"job_id"` repeats on
either side, which would repeat rows:

>>> per_job = minutes.merge(costs, on="job_id", how="outer", validate="one_to_one")
>>> per_job["cents_per_minute"] = (per_job["cost_cents"] / per_job["minutes"]).round(2)
>>> per_job
   job_id  runs  minutes  cost_cents  cents_per_minute
0       1     7       82         820             10.00
1       2     4       79         790             10.00
2       3     1       33         450             13.64

report_build, job 3, costs most per minute: it finished once this week, but its run that
failed on 2026-09-18 was billed too.

The Toolbox could join the two as Derived tables in one Statement, and on big results that is
the way: the warehouse does the work. For two small results you already have, a merge in pandas
is quicker to write and to change.

## Check it worked

Only each job's first run of the week has no run before it, so of three jobs, three rows have
NaN. And the merge kept one row per job:

>>> runs = run(with_before, send=example_database.send)
>>> int(runs["minutes_before"].isna().sum())
3
>>> per_job["job_id"].is_unique
True

## Common mistakes

### Testing a Window's result in the same Statement

A Window is worked out after the rows are picked, so Hive can't test it in the `WHERE` of the
Statement that works it out:

>>> in_one_go = statement(
...     SELECT(job_events.job_id, job_events.dt),
...     FROM(job_events),
...     WHERE(*week_finished,
...           more_than(job_events.minutes - lag(job_events.minutes, over=each_jobs_runs), 0)),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  WHERE has ...
...

Test it in the Statement that reads it as a Derived table, as the step Keep only some rows
does.

### A running total with ORDER_BY and no rows=

>>> sum_of(job_events.minutes, over=each_jobs_runs)
Traceback (most recent call last):
...
ValueError:
  What happened:  sum_of(job_events.minutes) is given a Window with ORDER_BY and no rows=.
...

With `ORDER_BY` and no `rows=`, Hive would add up the rows up to each row and every row tied
with it, which is seldom what's meant. Say which rows: `rows=(None, 0)` for every row up to each
one, `rows=(-2, 0)` for the last three, or leave `ORDER_BY` out for the whole group.

### Splitting a Window that looks across days with by_day

`by_day` sends one Statement per day, and each would see only its own day, so the run before
the day's first would be lost. It refuses:

>>> by_day(with_before)
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  by_day can't split this Statement: it works out lag(...) over a Window whose PARTITION_BY leaves out the Date partition job_events.dt, so it looks across days.
...

Read the earlier days and keep the day written, as the step Write a day that looks back on
earlier days does. A Window that looks only within each day, with the day among its
`PARTITION_BY=` columns, splits by day.

### Merging a result per day into one per job

Merge each job's week of minutes with its cost on each day, and each job's minutes repeat once
per day, so adding them up gives far too much:

>>> daily_cost = statement(
...     SELECT(region_costs.job_id, region_costs.dt, region_costs.cost_cents),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, "20260918", "20260924")),
... )
>>> daily_costs = run(daily_cost, send=example_database.send)
>>> repeated = minutes.merge(daily_costs, on="job_id")
>>> int(repeated["minutes"].sum()), int(minutes["minutes"].sum())
(1035, 194)

`validate="one_to_one"` stops such a merge rather than let it through:

>>> minutes.merge(daily_costs, on="job_id", validate="one_to_one")
Traceback (most recent call last):
...
pandas.errors.MergeError: Merge keys are not unique in right dataset; not a one-to-one merge
...

Add up per job first, as `cost_per_job` does, then merge.

## Next

- [Test your own Statements](#test_your_own_statements): check that a Statement, and what you
  do in pandas after it, give the numbers you meant.
- [Keys, checked before each write](#keys): a Window keeps every row, so a Statement's Key is
  its FROM table's; a `row_number` kept at 1 gives one row per group.
- The gallery's [`window`](examples.html#window), [`lag`](examples.html#lag) and
  [`row_number`](examples.html#row_number) entries.
"""

import pandas as pd

from sqlglot_composer import FROM, SELECT, WHERE, all_columns, between, example_database, run, statement

# The Example database can't run a window, so the page and the doctest get
# each Statement's result from these, worked out in pandas from every finished run of the
# week.


def finished_runs() -> pd.DataFrame:
    """Every finished run of the week, read with a Statement the Example database can run."""
    job_events = example_database.job_events
    rows = run(statement(SELECT(all_columns(job_events)), FROM(job_events),
                         WHERE(between(job_events.dt, "2026-09-18", "2026-09-24"))),
               send=example_database.send)
    rows = rows[rows["event_type"] == "finish"]
    return rows.sort_values(["job_id", "dt"]).reset_index(drop=True)


def in_order(rows: pd.DataFrame) -> pd.DataFrame:
    """The rows as the Example database gives them: by the first column, then the next, ..."""
    return rows.sort_values(list(rows.columns)).reset_index(drop=True)


def with_before_in_pandas() -> pd.DataFrame:
    runs = finished_runs()
    runs["minutes_before"] = runs.groupby("job_id")["minutes"].shift(1)
    runs["change"] = runs["minutes"] - runs["minutes_before"]
    return in_order(runs[["job_id", "dt", "minutes", "minutes_before", "change"]])


def ranked_in_pandas() -> pd.DataFrame:
    runs = finished_runs()
    runs["longest_first"] = (runs.groupby("job_id")["minutes"]
                             .rank(method="min", ascending=False).astype("int32"))
    return in_order(runs[["job_id", "dt", "minutes", "longest_first"]])


def last_three_in_pandas() -> pd.DataFrame:
    runs = finished_runs()
    runs["last_3_runs"] = (runs.groupby("job_id")["minutes"]
                           .transform(lambda minutes: minutes.rolling(3, min_periods=1).sum())
                           .astype("int64"))
    runs["week_minutes"] = runs.groupby("job_id")["minutes"].transform("sum").astype("int64")
    return in_order(runs[["job_id", "dt", "minutes", "last_3_runs", "week_minutes"]])


def slower_in_pandas() -> pd.DataFrame:
    changes = with_before_in_pandas()
    slower = changes[changes["change"] > 0][["job_id", "dt", "change"]]
    # With no NULL left, Hive gives the change as whole numbers.
    return in_order(slower.astype({"change": "int64"}))
