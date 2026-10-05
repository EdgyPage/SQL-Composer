"""Finish in pandas

For: Intermediate

## Goal

Work out in pandas what the Toolbox doesn't write as Hive: each row's value from the row
before it (lag), a rank within each group (rank), and a rolling sum. Then put the results of
several Statements side by side with a merge.

## When you'd use it

When a step needs a window of rows around each row, written OVER (...) in SQL, which only
`row_number` writes for you. The Toolbox refuses the others, so let a Statement do the heavy
part on the warehouse, reading every row of the days you give it and handing back a small
result, and finish that result in pandas. And when the numbers you need come from Statements
on different tables, small enough to combine in your notebook.

## Steps

### Import the Toolbox and fetch the rows

>>> from sqlglot_composer import *
>>> import pandas as pd
>>> job_events = example_database.job_events
>>> region_costs = example_database.region_costs

Each finished run, with how many minutes it took, over the last week of the Example database:

>>> finished = statement(
...     SELECT(job_events.job_id, job_events.dt, job_events.minutes),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-18", "2026-09-24"),
...           equals(job_events.event_type, "finish")),
... )
>>> runs = run(finished, send=example_database.send)

`runs` is an ordinary pandas DataFrame, one row per finished run. Everything after this works
on it in your notebook, and nothing more runs on the warehouse.

### The run before: lag

How much faster or slower was each run than the job's run before it? SQL's lag gives that, but
it needs OVER (...), so `hive_function` refuses it, and its message gives the pandas line to
use instead:

>>> hive_function("lag", job_events.minutes, 1)
Traceback (most recent call last):
...
ValueError:
  What happened:  hive_function('lag', ...) calls lag, which works only over a window of rows, written LAG(...) OVER (...).
...

The message's pandas line is written with example names: df stands for your DataFrame, here
`runs`, and "runs" for the column to shift, here "minutes".

In pandas, sort each job's runs by day, then `.shift(1)` within each job gives each row the
value of the row before it, and NaN, pandas' empty value, for each job's first run. The tables
on this page show NaN, like None, as NULL:

>>> runs = runs.sort_values(["job_id", "dt"])
>>> runs["minutes_before"] = runs.groupby("job_id")["minutes"].shift(1)
>>> runs["change"] = runs["minutes"] - runs["minutes_before"]
>>> runs
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

### A rank within each group: rank

Which of each job's runs took longest? rank is refused for the same reason:

>>> hive_function("rank")
Traceback (most recent call last):
...
ValueError:
  What happened:  hive_function('rank', ...) calls rank, which works only over a window of rows, written RANK(...) OVER (...).
...

In pandas, `.rank` within each job, longest first. `method="min"` gives two runs that tie the
same rank, and the next one the rank after both, as SQL's rank does; `.astype(int)` shows the
ranks as whole numbers:

>>> runs["longest_first"] = (runs.groupby("job_id")["minutes"]
...                          .rank(method="min", ascending=False).astype(int))
>>> runs[["job_id", "dt", "minutes", "longest_first"]]
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

To keep the newest row per key, or the top rows per group, use `row_number` instead, which
the Toolbox writes as Hive with its OVER (...): see [The latest row per key, and the top N per
group](#latest_row_per_key).

### A rolling sum

The minutes of each job's last three runs, added up. `sum_of` adds up a whole group into one
row, and so does sum through `hive_function`. Nothing refuses it, since sum is not only a
window function, but it writes plain SUM, with no OVER (...):

>>> hive_function("sum", job_events.minutes)
SUM(job_events.minutes)

The Toolbox writes no OVER (...) for a rolling sum, so work it out in pandas:
`.rolling(3, min_periods=1)` looks at each row and the two before it, or fewer at the start,
and `.transform` does it within each job, keeping one value per row:

>>> runs["last_3_runs"] = (runs.groupby("job_id")["minutes"]
...                        .transform(lambda minutes: minutes.rolling(3, min_periods=1).sum()))
>>> runs[["job_id", "dt", "minutes", "last_3_runs"]]
    job_id          dt  minutes  last_3_runs
0        1  2026-09-18       14         14.0
1        1  2026-09-19       11         25.0
2        1  2026-09-20       12         37.0
3        1  2026-09-21       13         36.0
4        1  2026-09-22       10         35.0
5        1  2026-09-23       12         35.0
6        1  2026-09-24       10         32.0
7        2  2026-09-18       22         22.0
8        2  2026-09-21       21         43.0
9        2  2026-09-22       18         61.0
10       2  2026-09-23       18         57.0
11       3  2026-09-21       33         33.0

It counts runs, not days: invoice_sync, job 2, doesn't run at weekends, so its first three
runs, up to 2026-09-22, span 2026-09-18 to 22, five days, and add up to 61 minutes.

### Merge the results of several Statements

The cost of each minute a job ran comes from two tables: its minutes from `ops.job_events`, and
its cost from `ops.region_costs`. Add up each per job, with a Statement each:

>>> minutes_per_job = statement(
...     SELECT(job_events.job_id, AS(count_rows(), "runs"),
...            AS(sum_of(job_events.minutes), "minutes")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-18", "2026-09-24"),
...           equals(job_events.event_type, "finish")),
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

Only each job's first run has no run before it, so of three jobs, three rows have NaN. And the
merge kept one row per job:

>>> int(runs["minutes_before"].isna().sum())
3
>>> per_job["job_id"].is_unique
True

## Common mistakes

### Shifting rows that aren't in order

`.shift(1)` takes the row above, whatever order the rows are in. The Example database gives rows
in a fixed order, but your warehouse gives them in no fixed order, as here, newest first:

>>> newest_first = runs[["job_id", "dt", "minutes"]].iloc[::-1].copy()
>>> newest_first["minutes_before"] = newest_first.groupby("job_id")["minutes"].shift(1)
>>> newest_first[newest_first["job_id"] == 2]
    job_id          dt  minutes  minutes_before
10       2  2026-09-23       18             NaN
9        2  2026-09-22       18            18.0
8        2  2026-09-21       21            18.0
7        2  2026-09-18       22            21.0

Each "minutes_before" is the run after it, and nothing stops it. Sort by the key and the day
first, with `.sort_values(["job_id", "dt"])`, as the step The run before: lag does.

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

Add up per job first, as `cost_per_job` does, then merge.

## Next

- [Test your own Statements](#test_your_own_statements): check that a Statement, and what you
  do in pandas after it, give the numbers you meant.
- [Call other Hive functions](#call_other_hive_functions): what `hive_function` writes, and the
  functions it refuses.
- The gallery's [`row_number`](examples.html#row_number) and
  [`derived`](examples.html#derived) entries, for what the warehouse can do before pandas.
"""
