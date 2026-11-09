"""Look across rows, then finish in pandas

For: Intermediate

## Goal

Work out on the warehouse what looks across the rows around each row: each row's value from
the row before it (lag), a rank within each group (rank), a rolling sum, and a group's total
beside each row, each over a `window`. A Window is the rows a calculation looks across for each
row: the rows of that row's group, in an order, and sometimes only those near it. Keep only
some of those rows through a Derived table, a Statement given a name so another Statement can
read from it, and write a Partition of a Saved table, a real table your own Statements write,
that looks back on earlier Partitions. Then finish in pandas: put the results of several
Statements side by side with a merge.

## When you'd use it

- If a step needs the rows around each row, written OVER (...) in SQL, such as how a run
  compares with the one before it, a running or moving total, or a rank, write it over a
  `window` (steps 3 to 7). The warehouse does that work, reading every row of the Partitions
  you give it, and gives back the result.
- If you want only the rows a Window's result picks out, test it through a Derived table
  (step 8).
- If a Saved table's Partition needs rows from earlier days, write it as steps 9 to 11 do.
- If the numbers you need come from Statements on different tables, small enough to combine
  in your notebook, merge them in pandas (steps 12 and 13).
- If you haven't done the Getting started how-tos
  [Count, join and stay safe](#count_join_and_stay_safe),
  [Share Building blocks](#share_building_blocks), which starts with Derived tables, and
  [Save a table](#save_a_table), do them first.

## Steps

### 1. Copy the Intermediate Example project

Goal: a Project to work in, its Table references written. A Project is your folder of scripts
at work, in the Toolbox's fixed layout; a Table reference is the file that describes one table.

Work in a copy of the Intermediate Example project, at its top: copy
`example_projects/intermediate/` from the download to a folder of your own, copy the
`sqlglot_composer` folder into it, as a Project holds it, and open a notebook there. This page
makes the same copy in its first step, from the download the Toolbox came in, and runs its
steps there:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

Done when the folder you work in holds `references/` and `warehouse.py`. Then step 2.

### 2. Import the Toolbox and the tables

Goal: the two tables the steps read. Import the Toolbox, pandas, the `project` module, the
Project's `ops` Database, the named group of tables whose names start `ops.`, and your query
and execute:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> import pandas as pd
>>> from references import ops
>>> from warehouse import connect, query, execute
>>> connect(example_database)
>>> job_events = ops.job_events  # -> Table
>>> region_costs = ops.region_costs  # -> Table

Done when the imports run without an error. Then step 3.

### 3. Name the Window

Goal: the rows each row looks across, named once. `PARTITION_BY=` makes the groups, here each
job: the word is SQL's, and has nothing to do with a table's Partitions. `ORDER_BY=` puts
each group's rows in order, here by day. Each job finishes at most once a day in the Example
database, so ordering by day gives each job's runs one clear order.

>>> each_jobs_runs = window(  # -> Window
...     PARTITION_BY=job_events.job_id, ORDER_BY=job_events.dt)

Done when `each_jobs_runs` is made without an error. Then step 4.

### 4. Name the rows to read

Goal: the rows to read, the same in every step: the finished runs of the last week of the
Example database.

>>> week_finished = [  # -> list[Condition]
...     between(job_events.dt, "2026-09-18", "2026-09-24"),
...     equals(job_events.event_type, "finish"),
... ]

Done when `week_finished` holds its two Conditions. Then step 5.

### 5. Read the run before, with lag

Goal: how much faster or slower each run was than the job's run before it. `lag` gives each
row the
value of the row before it in its Window's order, and NULL to the first row of each job.
pandas holds a missing number as NaN, and so shows that column with decimals; the tables on
this page show NaN as NULL:

>>> with_before = statement(  # -> Statement
...     SELECT(job_events.job_id, job_events.dt, job_events.minutes,
...            AS(lag(job_events.minutes, over=each_jobs_runs), "minutes_before"),
...            AS(job_events.minutes - lag(job_events.minutes, over=each_jobs_runs), "change")),
...     FROM(job_events),
...     WHERE(*week_finished),
... )
>>> text = show_hive(with_before)  # -> str
SELECT
  job_events.job_id,
  job_events.dt,
  job_events.minutes,
  LAG(job_events.minutes, 1) OVER (PARTITION BY job_events.job_id ORDER BY job_events.dt ASC) AS
      minutes_before,
  job_events.minutes - LAG(job_events.minutes, 1) OVER (PARTITION BY job_events.job_id ORDER BY
      job_events.dt ASC) AS change
FROM ops.job_events AS job_events
WHERE
  job_events.dt BETWEEN '2026-09-18' AND '2026-09-24'
  AND job_events.event_type = 'finish';
>>> run_query(with_before, query)  # -> DataFrame
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

Done when each job's first run of the week shows NaN before it. Then step 6.

### 6. Rank within each group, with rank

Goal: which of each job's runs took longest. `rank` numbers each job's runs in its Window's
order,
here the longest first, with `descending`. Two runs that tie get the same rank, and the next
run the rank after both, as job 1's two runs of 12 minutes do: both 3, then 5 for its run of
11 minutes:

>>> longest_first = window(PARTITION_BY=job_events.job_id,  # -> Window
...                        ORDER_BY=descending(job_events.minutes))
>>> ranked = statement(  # -> Statement
...     SELECT(job_events.job_id, job_events.dt, job_events.minutes,
...            AS(rank(over=longest_first), "longest_first")),
...     FROM(job_events),
...     WHERE(*week_finished),
... )
>>> run_query(ranked, query)  # -> DataFrame
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
of each group, and the top N](#latest_row_of_each_group).

Done when job 1's two runs of 12 minutes both rank 3. Then step 7.

### 7. Add a rolling sum, and a group's total beside each row

Goal: the minutes of each job's last three runs, added up, beside the job's minutes for the
week.
`sum_of(..., over=...)` adds up each row's Window, and gives each row its own total.
`rows=(-2, 0)` keeps only the two rows before each row and the row itself; with no `ORDER_BY`
and no `rows=`, the Window is the whole job:

>>> last_three = statement(  # -> Statement
...     SELECT(job_events.job_id, job_events.dt, job_events.minutes,
...            AS(sum_of(job_events.minutes, over=window(
...                PARTITION_BY=job_events.job_id, ORDER_BY=job_events.dt, rows=(-2, 0))),
...               "last_3_runs"),
...            AS(sum_of(job_events.minutes, over=window(PARTITION_BY=job_events.job_id)),
...               "week_minutes")),
...     FROM(job_events),
...     WHERE(*week_finished),
... )
>>> text = show_hive(last_three)  # -> str
SELECT
...
>>> run_query(last_three, query)  # -> DataFrame
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

Done when job 2's `"last_3_runs"` on 2026-09-22 is 61. Then step 8.

### 8. Keep only some rows, through a Derived table

Goal: the runs that were slower than the job's run before. Hive works a Window out after it
picks the rows, so a test on `"change"` can't go in the WHERE of the Statement that works it
out (see Common mistakes). Name that Statement with `derived`, and test it in the Statement
that reads it:

>>> changes = derived("changes", with_before)  # -> Table
>>> slower = statement(  # -> Statement
...     SELECT(changes.job_id, changes.dt, changes.change),
...     FROM(changes),
...     WHERE(more_than(changes.change, 0)),
... )
>>> run_query(slower, query)  # -> DataFrame
   job_id          dt  change
0       1  2026-09-20       1
1       1  2026-09-21       1
2       1  2026-09-23       2

Done when the result holds the three runs whose change is more than 0. Then step 9.

### 9. Describe the Saved table

Goal: a Table reference for the Saved table that keeps each run's change. The Saved table,
mart.run_changes, has a Table reference of its own, written by hand as
[Describe a table by hand](#describe_a_table_by_hand) shows, and registered:

The file `references/mart__run_changes.py`, after you write it:

    \"\"\"mart.run_changes - each finished run beside the job's run before.\"\"\"
    from sqlglot_composer import Table

    run_changes = Table(
        "mart.run_changes",
        columns={
            "event_id": "bigint",
            "job_id": "bigint",
            "minutes": "int",
            "minutes_before": "int",  # the job's run before; NULL for its first
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=["event_id", "dt"],
        location="/data/your_team/mart.db/run_changes",
        purge=True,
    )

>>> _ = project.register("mart.run_changes")
>>> from references.mart__run_changes import run_changes

Done when `from references.mart__run_changes import run_changes` runs without an error. Then
step 10.

### 10. Write a Partition that looks back on earlier ones

Goal: each day's write, its Partition at a time, with the runs before it. Each day's write
needs the runs before it, which may be on earlier days. So read the earlier days too in a
Derived table that keeps the day column, and keep only the day written in the Statement that
writes, with `WHERE(equals(week.dt, day))`, naming its Partition with `partition={"dt": day}`.
Read only the day itself, and each job's first run that day would have no run before it.

Here a job's run before may be up to 6 days back, so each write reads its day and the 6
before it:

>>> import datetime
>>> def changes_on(day: str) -> Statement:
...     week_before = (datetime.date.fromisoformat(day)
...                    - datetime.timedelta(days=6)).isoformat()
...     week = derived("week", statement(
...         SELECT(job_events.event_id, job_events.job_id, job_events.dt, job_events.minutes,
...                AS(lag(job_events.minutes, over=each_jobs_runs), "minutes_before")),
...         FROM(job_events),
...         WHERE(between(job_events.dt, week_before, day),
...               equals(job_events.event_type, "finish")),
...     ))
...     return statement(
...         INSERT_OVERWRITE(run_changes, partition={"dt": day}),
...         SELECT(week.event_id, week.job_id, week.minutes, week.minutes_before),
...         FROM(week),
...         WHERE(equals(week.dt, day)),
...     )
>>> text = show_hive(changes_on("2026-09-24"))  # -> str
WITH week AS (
...

Done when the Hive starts `WITH week AS (`. Then step 11.

### 11. Send one write per day

Goal: each day's Partition written, oldest first. The Example database can't be written to,
so on this page the Project's execute prints the first line of each write and changes nothing.
A loop sends one such write for each day, oldest first:

>>> for day in ["2026-09-23", "2026-09-24"]:
...     run_execute(changes_on(day), execute)
execute: WITH week AS (
execute: WITH week AS (

In a Table notebook of its own, made with `project.new_table("mart.run_changes")`, its
write() would give that list of writes, one per day, for `project.run_tables` to send.

Done when execute shows one write per day. Then step 12.

### 12. Add up each table per job

Goal: two small results, one row per job each. The cost of each minute a job ran comes from
two tables: its minutes from `ops.job_events`, and its cost from `ops.region_costs`. Add up
each per job, with a Statement each:

>>> minutes_per_job = statement(  # -> Statement
...     SELECT(job_events.job_id, AS(count_rows(), "runs"),
...            AS(sum_of(job_events.minutes), "minutes")),
...     FROM(job_events),
...     WHERE(*week_finished),
...     GROUP_BY(job_events.job_id),
... )
>>> cost_per_job = statement(  # -> Statement
...     SELECT(region_costs.job_id, AS(sum_of(region_costs.cost_cents), "cost_cents")),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, "20260918", "20260924")),
...     GROUP_BY(region_costs.job_id),
... )
>>> minutes = run_query(minutes_per_job, query)  # -> DataFrame
>>> costs = run_query(cost_per_job, query)  # -> DataFrame

Done when `minutes` and `costs` each hold one row per job. Then step 13.

### 13. Merge the results

Goal: the two results side by side, one row per job. `.merge` puts the two side by side,
matching rows on `"job_id"`. `how="outer"` keeps a job that
only one of them has, and `validate="one_to_one"` stops the merge if `"job_id"` repeats on
either side, which would repeat rows:

>>> per_job = minutes.merge(  # -> DataFrame
...     costs, on="job_id", how="outer", validate="one_to_one")
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

Done when `per_job` holds jobs 1, 2 and 3, each with its `"cents_per_minute"`. Then check it
worked, below.

## Check it worked

Only each job's first run of the week has no run before it, so of three jobs, three rows have
NaN. And the merge kept one row per job:

>>> runs = run_query(with_before, query)  # -> DataFrame
>>> int(runs["minutes_before"].isna().sum())
3
>>> per_job["job_id"].is_unique
True

Before you go on, check that:

- `"minutes_before"` is NaN on 3 rows, one per job;
- `per_job["job_id"].is_unique` shows `True`;
- each write step 11 sends starts `WITH week AS (`.

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

Test it in the Statement that reads it as a Derived table, as step 8 does.

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

### Merging a result per day into one per job

Merge each job's week of minutes with its cost on each day, and each job's minutes repeat once
per day, so adding them up gives far too much:

>>> daily_cost = statement(  # -> Statement
...     SELECT(region_costs.job_id, region_costs.dt, region_costs.cost_cents),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, "20260918", "20260924")),
... )
>>> daily_costs = run_query(daily_cost, query)  # -> DataFrame
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

- Check that a Statement, and what you do in pandas after it, give the numbers you meant:
  [Review and test a change](#review_and_test_a_change).
- Each job's last row, or its top N, kept with `row_number`: [The latest row of each
  group](#latest_row_of_each_group).
- [Keys](#keys): a Window keeps every row, so a Statement's Key is
  its FROM table's; a `row_number` kept at 1 gives one row per group.
- The gallery's [`window`](examples.html#window), [`lag`](examples.html#lag) and
  [`row_number`](examples.html#row_number) entries.
"""
