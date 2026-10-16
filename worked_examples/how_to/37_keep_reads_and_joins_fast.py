"""Keep reads and joins fast

For: Intermediate

## Goal

Keep Statements on big tables fast: read only the days you need, keep a Saved table's files few
and large, give Hive the statistics it plans joins from, let it copy a small table to every
worker, and see with `explain` what Hive will do before you run a Statement. Along the way,
let the warehouse find a Saved table's days again with `repair_partitions`. Each of these is
safe to send again.

## When you'd use it

When a Statement or a pipeline gets slow, or a Saved table grows to millions of rows a day.
Hive has no indexes to add: [Choose how a Saved table is stored](#choose_how_a_saved_table_is_stored)
says why, under "Why there are no indexes", and shows how to give a big table Partitions and
Buckets. This how-to is what to do once the table exists.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> job_runs, jobs = example_database.job_runs, example_database.jobs

mart.daily_runs, each job's runs per day, is one of your Saved tables:

>>> daily_runs = Table(
...     "mart.daily_runs",
...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
...     date_partition="dt",
...     key=["job_id"],
...     location="/data/your_team/tables",
... )

### Read only the days you need

A table's Partitions are folders, one per day, and a Statement that bounds the Date partition
opens only those days' folders. Every Statement already bounds it, as the Load limits insist,
so the first rule of a fast read is one you keep anyway: bound it as tightly as the job
allows, a day rather than a week. A Statement that bounds a Partition inside the day, such as
region, opens fewer folders still.

### Keep files few and large

Every file costs Hive a little to open, so a day held in a thousand small files reads far more
slowly than the same rows in a few large ones. Small files come from writes that many workers
share. The Session setting "merge_small_files" has each write merge its files before it
finishes; "statistics_on_write" has each write count the day it writes, for the next step.
Send them before your writes, once per session:

>>> print(to_hive(hive_settings("merge_small_files", "statistics_on_write")))
SET hive.merge.mapfiles=true
SET hive.merge.mapredfiles=true
SET hive.merge.tezfiles=true
SET hive.stats.autogather=true
SET hive.stats.column.autogather=true
>>> run(hive_settings("merge_small_files", "statistics_on_write"), send=example_database.send)

`run` sends each SET line as a call of its own and gives back nothing. They hold only while
your send keeps one session across its calls.

### Give Hive the statistics it plans joins from

Hive picks how to join two tables from their statistics: how many rows and bytes each day
holds. Without them it guesses, and may sort two big tables to join them where copying a small
one would do. A day written with "statistics_on_write" is counted as it is written; count a day
written without that setting with `compute_statistics`, and add `columns=True` to count each
column's values too, which Hive reads to order several joins:

>>> print(to_hive(compute_statistics(daily_runs, "2026-09-24")))
ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24') COMPUTE STATISTICS
>>> print(to_hive(compute_statistics(daily_runs, "2026-09-24", columns=True)))
ANALYZE TABLE mart.daily_runs PARTITION(dt = '2026-09-24') COMPUTE STATISTICS FOR COLUMNS job_id, runs

It counts one day, as each write fills one. At work, a function counts the days you wrote
before, one by one, through your own send; sending a day again counts it again, which does no
harm:

    def count_days(send):
        for day in ["2026-09-22", "2026-09-23", "2026-09-24"]:
            run(compute_statistics(daily_runs, day), send=send)

`columns=[daily_runs.job_id]` counts only the columns you name, such as those you join or
filter on, which reads less. Where
your send runs on Spark rather than Hive, Spark counts columns over the whole table, whatever
the day, so name only those few.

### Let Hive copy a small table to every worker

Joining a big table to a small one, such as job_runs to jobs, is fastest when Hive copies the
small table to every worker, which then joins its share of the big one without sorting it: a
map join, or broadcast join. The Session setting "map_joins" lets Hive choose one by itself,
from the tables' statistics, so it works best once both tables have them. Send it before
your Statements, as the settings above:

>>> print(to_hive(hive_settings("map_joins")))
SET hive.auto.convert.join=true
SET hive.auto.convert.join.noconditionaltask=true
>>> run(hive_settings("map_joins"), send=example_database.send)

Nothing in the Statement changes: Hive decides when it plans it. The next step shows how to see
what it decided.

Where Hive still sorts both sides, `JOIN(jobs, ON=..., broadcast=True)` asks it by name to
copy jobs to every worker; [Semi-, anti- and full joins](#semi_anti_and_full_joins) shows how,
and the Session setting Hive needs before it heeds the request.

### Use Buckets only for big joins

Where two big tables are joined on the same column every day, Buckets spread each day's rows
into a fixed number of files by that column, so the join pairs file with file. They pay off
only on tables of tens of millions of rows a day, and changing them means writing the table
again: [Choose how a Saved table is stored](#choose_how_a_saved_table_is_stored) shows how.

### See Hive's plan with explain

`explain` writes EXPLAIN before exactly the Hive `run` would send, and `run` gives back Hive's
plan for it as text, without running the Statement:

>>> runs_per_team = statement(
...     SELECT(jobs.team, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
...     GROUP_BY(jobs.team),
... )
>>> print(to_hive(explain(runs_per_team)))
EXPLAIN SELECT
  jobs.team,
  COUNT(*) AS runs
FROM ops.job_runs AS job_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = job_runs.job_id
WHERE
  job_runs.dt = '2026-09-24'
GROUP BY
  jobs.team

At work, print the plan your own send gives back:

    def show_plan(send):
        print(run(explain(runs_per_team), send=send))

Hive's plan is a tree of steps, each reading what the steps below it give. Look for:

- "TableScan", once for each table read, with the filter it reads it with;
- "Map Join Operator" where Hive copies the small table to every worker, or "Merge Join
  Operator" where it sorts both sides first;
- each step's "Statistics:" line, the rows Hive expects, and "Basic stats: NONE" or "Column
  stats: NONE" where it has none to go by: count that table's days with `compute_statistics`.

[spark_composer only]
The Example database runs on Spark, so it gives Spark's own plan, which reads differently from
Hive's and starts with its heading:

>>> plan = run(explain(runs_per_team), send=example_database.send)
>>> print(plan.splitlines()[0])
== Physical Plan ==

Spark calls a map join a BroadcastHashJoin.
[end]

[sqlglot_composer only]
The Example database can't give a plan: it runs Hive on sqlglot's own small executor, which
makes none. `to_hive(explain(...))` still shows what you would send at work.
[end]

### Find the days a Saved table lost

The warehouse keeps a list of each table's days, and reads only the day folders on it. When a
table is made again where its old files stayed, since it was dropped without `purge=True`, or
when files are copied into its folder, their days are missing from the list until
`repair_partitions` finds them:

>>> print(to_hive(repair_partitions(daily_runs)))
MSCK REPAIR TABLE mart.daily_runs

It only adds days; it deletes no file, so it is safe to send again. Neither Example database
can run it or `compute_statistics`: their tables are made up and fixed.

## Check it worked

`explain` explains exactly the Hive `run` sends, so the plan is of the Statement you run:

>>> to_hive(explain(runs_per_team)) == "EXPLAIN " + to_hive(runs_per_team)
True

The Statement itself still gives its rows:

>>> run(runs_per_team, send=example_database.send)
      team  runs
0     data     2
1  finance     2

At work, compare the plan before and after a change: send `compute_statistics` for a table,
then explain the same Statement again, and the "Statistics:" lines of its TableScan should
say "Basic stats: COMPLETE" where they said NONE; send "map_joins" first, and a join to a
small table should be a "Map Join Operator". Then time the
Statement itself.

## Common mistakes

### Counting a table you only read

`compute_statistics` and `repair_partitions` change what the warehouse keeps about a table, so
they take only your own Saved tables, Table references with `location=`. A table another team
owns is refused:

>>> compute_statistics(job_runs, "2026-09-24")
Traceback (most recent call last):
...
ValueError:
  What happened:  compute_statistics(...) was given ops.job_runs, which isn't one of your Saved tables: its Table reference has no location=.
...

Ask the team that owns it to keep its statistics.

### Counting every day at once

`compute_statistics` counts one day of a table with a Date partition: leaving the day out
would read the whole table, so it is refused:

>>> compute_statistics(daily_runs)
Traceback (most recent call last):
...
TypeError:
  What happened:  compute_statistics(daily_runs) needs the day to count.
...

Pass the day, or loop over the days, as above.

### Sending Session settings to a send that forgets them

A Session setting holds for the rest of a session. If your send opens a new session for each
call, each SET is gone before your Statement runs, and the plan shows no change. Send the
settings and the Statements through one send that keeps its session, as `spark.sql` does in
one notebook.

## Next

- Give a big table Partitions inside each day, or Buckets:
  [Choose how a Saved table is stored](#choose_how_a_saved_table_is_stored).
- Ask for a map join on one join, with `broadcast=True`:
  [Semi-, anti- and full joins](#semi_anti_and_full_joins).
- Keep each Statement's reads bounded:
  [Keep queries small with load limits](#keep_queries_small_with_load_limits).
- Every option in one place: the gallery's [`explain`](examples.html#explain),
  [`compute_statistics`](examples.html#compute_statistics) and
  [`repair_partitions`](examples.html#repair_partitions) entries.
"""
