"""Keep reads and joins fast

For: Intermediate

## Goal

Keep Statements, the queries you build with the Toolbox, fast on big tables: read only the
Partitions you need, keep each step of a Statement small, keep a Saved table's files few and
large, give Hive the Statistics it plans joins from, let it copy a small table to every worker,
and see with `explain` what Hive will do before you run a Statement. A Partition is a slice of
a table, the rows that share one value of each column it is partitioned by; a Saved table is a
real table your own Statements write; Statistics are what the warehouse has counted about a
table's Partitions. Along the way, let the warehouse find a Saved table's Partitions again with
`repair_partitions`. Each of these is safe to send again.

## When you'd use it

- If a Statement or a run of your tables gets slow, follow the steps below.
- If a Statement has no mistake in its logic but takes far longer than its rows should, check
  its steps against the rules in step 4.
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

Goal: a Project, your folder of scripts at work, holding a Saved table. Work in your own
Project, at its top. This page works in a copy of the Intermediate Example project, which the
download's Example projects page shows file by file: `example_project("intermediate")` makes
that copy in the folder the page runs in. It is a line of this page alone, not a Toolbox name,
as `conn` is this page's connection: in your own Project leave it out.

>>> example_project("intermediate")

Done when the folder you work in holds the Project's admin/, references/ and tables/ folders.
Then step 2.

### 2. Name the tables

Goal: the tables the steps read, by short names. mart.job_day_facts, each job's events, runs
and minutes per day beside its team, is one of the Project's Saved tables, partitioned by dt:

>>> from sqlglot_composer import *
>>> from warehouse import connect, query, execute
>>> connect(conn)
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

### 4. Keep each step small

Goal: Hive that does no more work than its rows need. A Derived table is written at the top of
the Hive as a CTE, `WITH name AS (...)`, and Hive keeps none of a CTE's rows: it works the CTE
out again each time the Statement reads it. So each step reads its table once, keeps only the
rows and columns the next step needs, and adds up before it joins. Here each team's events on
2026-09-24, counted per job first, so the join meets one row for each job rather than one for
each event:

>>> events_per_job = derived("events_per_job", statement(  # -> Table
...     SELECT(job_events.job_id, AS(count_rows(), "events")),
...     FROM(job_events),
...     WHERE(equals(job_events.dt, "2026-09-24")),
...     GROUP_BY(job_events.job_id),
... ))
>>> team_events = statement(  # -> Statement
...     SELECT(job_owners.team, AS(sum_of(events_per_job.events), "events")),
...     FROM(events_per_job),
...     JOIN(job_owners, ON=all_of(equals(job_owners.job_id, events_per_job.job_id),
...                                equals(job_owners.dt, "2026-09-24"))),
...     GROUP_BY(job_owners.team),
... )
>>> print(to_hive(team_events))
WITH events_per_job AS (
  SELECT
    job_events.job_id,
    COUNT(*) AS events
  FROM ops.job_events AS job_events
  WHERE
    job_events.dt = '2026-09-24'
  GROUP BY
    job_events.job_id
)
SELECT
  job_owners.team,
  SUM(events_per_job.events) AS events
FROM events_per_job
JOIN ops.job_owners AS job_owners
  ON job_owners.job_id = events_per_job.job_id
  AND job_owners.dt = '2026-09-24'
GROUP BY
  job_owners.team
>>> run_query(team_events, query)  # -> DataFrame
      team  events
0     data       2
1  finance       1

The rules for keeping each step small, each with its reason, from Hive's own documentation
where it has one. A step here is a Derived table, which the Hive holds as a CTE:

- **Read each Derived table once in a Statement.** Hive's setting
  hive.optimize.cte.materialize.threshold is -1, off, in Hive 2.x, 3.1 and 4.0, so a Derived
  table one Statement reads twice is worked out twice. From Hive 4.1 the setting is 3: a CTE
  with GROUP BY totals, read more than 3 times, is worked out once. Ask whoever looks after
  your warehouse which Hive it runs. Where one Statement needs a step's rows twice, save the
  step as a Saved table, written once: [Save a table](#save_a_table). A Building block that
  several Statements import is no second read: each Statement works out its own copy once.
- **Select in a Derived table only the columns read after it, and group it only by those.** A
  column it groups by makes a row for each of its values, rows that every step after it
  carries. A column it only carries costs little where Hive works the CTE out inside the
  Statement, as Hive drops what nothing reads, but every column counts where Hive saves the
  CTE's rows (from 4.1, above), and a short step is quicker to check when a number looks
  wrong. A Building block that several Statements share may carry more: each Statement reads
  its own columns of it.
- **Filter and add up before joining.** The WHERE, on a partition column first, goes in the
  step that reads the big table, and a total goes in a step before the join it feeds, as
  `events_per_job` does. Hive copies a join's small side to every worker only while it is under
  10 MB (hive.auto.convert.join.noconditionaltask.size); otherwise it sorts both sides, and
  holds every side but the last in memory.
- **Rename or add a column in the SELECT that reads a table or step**, never in a step of its
  own that copies every column to change one: each copy is one more step to read when a
  number looks wrong.
- **ORDER_BY only with LIMIT, and only in the Statement that gives the rows.** Hive sorts every
  row through one worker for an ORDER BY, and from Hive 3.0 drops one with no LIMIT inside a
  CTE or subquery (hive.remove.orderby.in.subquery), so it would sort nothing anyway.
- **Fix a join that repeats rows in the join itself**: match the whole Key, or add up the
  other side to one row for each key first. SELECT_DISTINCT afterwards makes every repeated
  row first, then sorts them all to drop the copies.

Done when the result is data 2 and finance 1, and the Hive names ops.job_events once, in
`events_per_job`. Then step 5.

### 5. Keep files few and large

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

Done when your execute has been given the five SET lines. Then step 6.

### 6. Give Hive the Statistics it plans joins from

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
sent. Then step 7.

### 7. Let Hive copy a small table to every worker

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

Nothing in the Statement changes: Hive decides when it plans it. Step 9 shows how to see what
it decided.

Where Hive still sorts both sides, `JOIN(job_owners, ON=..., broadcast=True)` asks it by name
to copy job_owners to every worker; [Semi-, anti- and full joins](#semi_anti_and_full_joins)
shows how. Hive heeds that request only after "map_joins", whose last line,
hive.ignore.mapjoin.hint=false, tells it to.

Done when your execute has been given the three SET lines of "map_joins". Then step 8.

### 8. Keep Buckets for big joins

Goal: Buckets only where they pay off. Where two big tables are joined on the same column on
every run, Buckets spread each Partition's rows into a fixed number of files by that column, so
the join pairs file with file. They pay off only on tables of tens of millions of rows a
Partition, and changing them means writing the table again: [Choose how a Saved table is
stored](#choose_how_a_saved_table_is_stored) shows how.

Done when you have decided, for each big join, whether its tables reach tens of millions of
rows a Partition. Then step 9.

### 9. See Hive's Plan with explain

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

Done when the Hive starts with `EXPLAIN SELECT`. Then step 10.

### 10. Find the Partitions a Saved table lost

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
