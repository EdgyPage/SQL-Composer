"""Keep reads and joins fast

For: Intermediate

## Goal

Keep Statements, the queries you build with the Toolbox, fast on big tables: read only the
Partitions you need, keep a Saved table's files few and large, give Hive the Statistics it
plans joins from, let it copy a small table to every worker, and see with `explain` what Hive
will do before you run a Statement. A Partition is a slice of a table, the rows that share one
value of each column it is partitioned by; a Saved table is a real table your own Statements
write; Statistics are what the warehouse has counted about a table's Partitions. Along the way,
let the warehouse find a Saved table's Partitions again with `repair_partitions`. Each of these
is safe to send again.

## When you'd use it

- If a Statement or a run of your tables gets slow, follow the steps below.
- If a Saved table grows to millions of rows a Partition, follow the steps below.
- If you want an index: Hive has none to add. [Choose how a Saved table is
  stored](#choose_how_a_saved_table_is_stored) says why, under "Why there are no indexes", and
  shows how to give a big table Partitions and Buckets; this how-to is what to do once the
  table exists.
- If you have not joined tables or saved a table yet, do
  [Count, join and stay safe](#count_join_and_stay_safe) and [Save a table](#save_a_table)
  first.

## Steps

### 1. Start from the Intermediate Example project

Goal: a Project, your folder of scripts at work, holding a Saved table. Work in a copy of the
Intermediate Example project, at its top: copy `example_projects/intermediate/` from the
download to a folder of your own, copy the `sqlglot_composer` folder into it, as a Project holds
it, and open a notebook there. This page makes the same copy in its first step, from the
download the Toolbox came in, into the folder it runs in, which Python's path holds already, as
Jupyter's does for a notebook's own folder:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

Done when the folder you work in holds the Project's admin/, references/ and tables/ folders.
Then step 2.

### 2. Name the tables

Goal: the tables the steps read, by short names. mart.job_day_facts, each job's events, runs
and minutes per day beside its team, is one of the Project's Saved tables, partitioned by dt:

>>> from sqlglot_composer import *
>>> from warehouse import connect, query, execute
>>> connect(example_database)
>>> from references import mart, ops
>>> job_day_facts = mart.job_day_facts  # -> Table
>>> job_events, job_owners = ops.job_events, ops.job_owners  # -> Table, Table

Done when `job_day_facts`, `job_events` and `job_owners` are set. Then step 3.

### 3. Read only the Partitions you need

Goal: each read opens as few folders as the job allows. A table's Partitions are folders, here
one per day, and a Statement that filters a partition column opens only the folders it picks.
Every Statement on a partitioned table already filters one, as the Load limits, the checks that
refuse a read too big for the cluster, insist. So the first rule of a fast read is one you keep
anyway: filter as tightly as the job allows, a day rather than a week. On a table partitioned
by two columns, such as ops.region_costs by region and then dt, a Statement that filters both
opens fewer folders still.

Done when each of your Statements filters its partition columns to the days the job needs.
Then step 4.

### 4. Keep files few and large

Goal: Partitions held in a few large files. Every file costs Hive a little to open, so a
Partition held in a thousand small files reads far more slowly than the same rows in a few
large ones. Small files come from writes that many workers share. A Session setting is a Hive
SET line that holds for the rest of the session. The Session setting "merge_small_files" has
each write merge its files before it finishes; "statistics_on_write" has each write count the
Partitions it writes, for the next step. Send them before your writes, once per session:

>>> settings = hive_settings("merge_small_files", "statistics_on_write")  # -> SessionSettings
>>> print(to_hive(settings))
SET hive.merge.mapfiles=true
SET hive.merge.mapredfiles=true
SET hive.merge.tezfiles=true
SET hive.stats.autogather=true
SET hive.stats.column.autogather=true
>>> run_execute(settings, execute)
execute: SET hive.merge.mapfiles=true
execute: SET hive.merge.mapredfiles=true
execute: SET hive.merge.tezfiles=true
execute: SET hive.stats.autogather=true
execute: SET hive.stats.column.autogather=true

`run_execute` sends each SET line through your execute, as a call of its own, and gives back
nothing; the Example database's execute prints each one. They hold only while your query and
execute keep one session across their calls.

Done when your execute has been given the five SET lines. Then step 5.

### 5. Give Hive the Statistics it plans joins from

Goal: Partitions Hive has counted. Hive picks how to join two tables from their Statistics: how
many rows and bytes each Partition holds. Without them it guesses, and may sort two big tables
to join them where copying a small one would do. A Partition written with
"statistics_on_write" is counted as it is written; count one written without that setting with
`compute_statistics`, and add `columns=True` to count each column's values too, which Hive
reads to order several joins:

>>> count_day = compute_statistics(job_day_facts,
...                                partition={"dt": "2026-09-24"})  # -> Statement
>>> print(to_hive(count_day))
ANALYZE TABLE mart.job_day_facts PARTITION(dt = '2026-09-24') COMPUTE STATISTICS
>>> print(to_hive(compute_statistics(job_day_facts, partition={"dt": "2026-09-24"},
...                                  columns=True)))
ANALYZE TABLE mart.job_day_facts PARTITION(dt = '2026-09-24') COMPUTE STATISTICS FOR COLUMNS
    job_id, team, events, runs, minutes

`columns=[job_day_facts.job_id, job_day_facts.team]` counts only the columns you name, such as
those you join or filter on, which reads less. `partition=` names the Partition to count. Left
out, it counts every Partition the table holds, which reads the whole table:

>>> print(to_hive(compute_statistics(job_day_facts)))
ANALYZE TABLE mart.job_day_facts PARTITION(dt) COMPUTE STATISTICS

At work, a function counts the Partitions you wrote before, one by one, through your own
execute; sending one again counts it again, which does no harm:

    def count_days(days: list[str]) -> None:
        for day in days:
            run_execute(compute_statistics(job_day_facts, partition={"dt": day}), execute)

Done when each Partition you wrote without "statistics_on_write" has had its ANALYZE TABLE
sent. Then step 6.

### 6. Let Hive copy a small table to every worker

Goal: map joins where a small table meets a big one. Joining a big table to a small one, such
as the events of a day to the owners of that day, is fastest when Hive copies the small table
to every worker, which then joins its share of the big one without sorting it: a Map join, or
broadcast join. The Session setting "map_joins" lets Hive choose one by itself, from the
tables' Statistics, so it works best once both tables have them. Send it before your
Statements, as the settings above:

>>> print(to_hive(hive_settings("map_joins")))
SET hive.auto.convert.join=true
SET hive.auto.convert.join.noconditionaltask=true
SET hive.ignore.mapjoin.hint=false
>>> run_execute(hive_settings("map_joins"), execute)
execute: SET hive.auto.convert.join=true
execute: SET hive.auto.convert.join.noconditionaltask=true
execute: SET hive.ignore.mapjoin.hint=false

Nothing in the Statement changes: Hive decides when it plans it. Step 8 shows how to see what
it decided.

Where Hive still sorts both sides, `JOIN(job_owners, ON=..., broadcast=True)` asks it by name
to copy job_owners to every worker; [Semi-, anti- and full joins](#semi_anti_and_full_joins)
shows how. Hive heeds that request only after "map_joins", whose last line,
hive.ignore.mapjoin.hint=false, tells it to.

Done when your execute has been given the three SET lines of "map_joins". Then step 7.

### 7. Keep Buckets for big joins

Goal: Buckets only where they pay off. Where two big tables are joined on the same column on
every run, Buckets spread each Partition's rows into a fixed number of files by that column, so
the join pairs file with file. They pay off only on tables of tens of millions of rows a
Partition, and changing them means writing the table again: [Choose how a Saved table is
stored](#choose_how_a_saved_table_is_stored) shows how.

Done when you have decided, for each big join, whether its tables reach tens of millions of
rows a Partition. Then step 8.

### 8. See Hive's Plan with explain

Goal: how Hive will run a Statement, before you run it. A Plan is that: which tables Hive reads,
with which filters, and how it joins them. `explain` writes EXPLAIN before exactly the Hive
`run_query` would send, and `run_query` gives back Hive's Plan for it as text, without running
the Statement. Here each team's events on 2026-09-24, each event joined to its job's owner that
day:

>>> events_per_team = statement(  # -> Statement
...     SELECT(job_owners.team, AS(count_rows(), "events")),
...     FROM(job_events),
...     JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_events.job_id),
...                                equals(job_owners.dt, job_events.dt),
...                                equals(job_owners.dt, "2026-09-24"))),
...     WHERE(equals(job_events.dt, "2026-09-24")),
...     GROUP_BY(job_owners.team),
... )
>>> plan = explain(events_per_team)  # -> Statement
>>> print(to_hive(plan))
EXPLAIN SELECT
  job_owners.team,
  COUNT(*) AS events
FROM ops.job_events AS job_events
JOIN ops.job_owners AS job_owners
  ON job_owners.job_id = job_events.job_id
  AND job_owners.dt = job_events.dt
  AND job_owners.dt = '2026-09-24'
WHERE
  job_events.dt = '2026-09-24'
GROUP BY
  job_owners.team

At work, print the Plan your query gives back, `print(run_query(plan, query))`. Hive's Plan is
a tree of steps, each reading what the steps below it give. Look for:

- "TableScan", once for each table read, with the filter it reads it with;
- "Map Join Operator" where Hive copies the small table to every worker, or "Merge Join
  Operator" where it sorts both sides first;
- each step's "Statistics:" line, the rows Hive expects, and "Basic stats: NONE" or "Column
  stats: NONE" where it has none to go by: count that table's Partitions with
  `compute_statistics`, if it is yours, or ask its owner.

The Example database can't give a Plan: it runs Hive on sqlglot's own small executor, which
makes none. `to_hive(explain(...))` still shows what you would send at work.

Done when the Hive starts with `EXPLAIN SELECT`. Then step 9.

### 9. Find the Partitions a Saved table lost

Goal: every Partition of a Saved table on the warehouse's list. The warehouse keeps a list of
each table's Partitions, and reads only the folders on it. When a table is made again where its
old files stayed, since it was dropped without `purge=True`, or when files are copied into its
folder, their Partitions are missing from the list until `repair_partitions` finds them:

>>> repair = repair_partitions(job_day_facts)  # -> Statement
>>> print(to_hive(repair))
MSCK REPAIR TABLE mart.job_day_facts
>>> run_execute(repair, execute)
execute: MSCK REPAIR TABLE mart.job_day_facts

It only adds Partitions; it deletes no file, so it is safe to send again. Like
`compute_statistics`, it goes to your execute; the Example database's execute only prints its
first line, since its tables are made up and fixed.

Done when your execute has been given `MSCK REPAIR TABLE mart.job_day_facts`. Then check it
worked, below.

## Check it worked

`explain` explains exactly the Hive `run_query` sends, so the Plan is of the Statement you run:

>>> to_hive(plan) == "EXPLAIN " + to_hive(events_per_team)
True

The Statement itself still gives its rows:

>>> run_query(events_per_team, query)  # -> DataFrame
      team  events
0     data       2
1  finance       1

At work, compare the Plan before and after a change: send `compute_statistics` for a table,
then explain the same Statement again, and the "Statistics:" lines of its TableScan should
say "Basic stats: COMPLETE" where they said NONE; send "map_joins" first, and a join to a
small table should be a "Map Join Operator". Then time the Statement itself.

Before you go on, check that:

- `to_hive(plan)` is "EXPLAIN " followed by the Statement's own Hive;
- `run_query(events_per_team, query)` gives data 2 and finance 1;
- at work, the Plan's TableScan lines say "Basic stats: COMPLETE" once you counted the table.

## Common mistakes

### Counting a table you only read

`compute_statistics` and `repair_partitions` change what the warehouse keeps about a table, so
they take only your own Saved tables, Table references with `location=`. A table another team
owns is refused:

>>> compute_statistics(job_events, partition={"dt": "2026-09-24"})
Traceback (most recent call last):
...
ValueError:
  What happened:  compute_statistics(...) was given ops.job_events, which isn't one of your
                  Saved tables: its Table reference has no location=.
...

Ask the team that owns it to keep its Statistics.

### Naming the Partition without partition=

`compute_statistics` names the Partitions to count by their partition columns, so the value
alone is refused:

>>> compute_statistics(job_day_facts, "2026-09-24")
Traceback (most recent call last):
...
TypeError:
  What happened:  compute_statistics(job_day_facts, partition="2026-09-24"): partition= is a
                  dict of partition columns and their values.
...

Write `partition={"dt": "2026-09-24"}`, as the steps do.

### Sending Session settings to an execute that forgets them

A Session setting holds for the rest of a session. If your execute opens a new session for each
call, each SET is gone before your Statement runs, and the Plan shows no change. A read goes
through your query and a SET through your execute, so make both use one connection that keeps
its session for every call.

## Next

- Give a big table a second partition column, or Buckets:
  [Choose how a Saved table is stored](#choose_how_a_saved_table_is_stored).
- Ask for a map join on one join, with `broadcast=True`:
  [Semi-, anti- and full joins](#semi_anti_and_full_joins).
- Keep each Statement's reads small, with Load limits:
  [Count, join and stay safe](#count_join_and_stay_safe).
- Every option in one place: the gallery's [`explain`](examples.html#explain),
  [`compute_statistics`](examples.html#compute_statistics) and
  [`repair_partitions`](examples.html#repair_partitions) entries.
"""
