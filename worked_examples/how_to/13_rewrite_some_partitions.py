"""Rewrite some partitions

For: Intermediate

## Goal

Rewrite some of a Saved table's Partitions, and leave the rest as they are. A Saved table is a
real table in the warehouse that your own Statements write; a Partition is a slice of a table,
the rows that share one value of each column it is partitioned by. You write a range of days of
a table partitioned by its day, in one write that fills each Partition from its rows, or in a
loop of writes that each name their Partition with `partition={...}`; the last few days again
on every run, for rows that come in late; a table partitioned by region, written a region at a
time; and a table whose source writes its days another way. Then you write several Saved
tables in order with `project.run_tables`.

## When you'd use it

- If a Saved table is new, and the Partitions it should already hold are empty, write the
  range in one backfill, as steps 4 to 7 do.
- If you fixed a mistake in a write, rewrite every Partition it wrote, since each holds the
  mistake.
- If rows can come in late, such as a bill a day or two after its day, rewrite the last few
  days of the table that counts them on each run, as step 8 shows.
- If a backfill covers more days than one Statement should read at once, write it a Partition
  at a time, in a loop, as steps 9 to 12 do.
- If one region's numbers changed, rewrite that region's Partition alone, and the other regions'
  Partitions stay as they are, as steps 13 and 14 do.
- If several Saved tables read one another, write them in order with `project.run_tables`, as
  step 16 does.
- If you have not yet done the Getting started how-tos, do
  [Share Building blocks](#share_building_blocks) and [Save a table](#save_a_table) first.

The Example database can't be written to, so on this page each write shows its Hive, and is
sent through the Project's execute, which here prints the first line of what it would send
and changes nothing. The rows a write would save are checked with a plain SELECT first, which
the Example database does run.

## Steps

### 1. Copy the Intermediate Example project

Goal: a Project to work in. A Project is your folder of scripts at work, in the Toolbox's fixed
layout, and an Example project is one made for the Example database's tables, to read and copy
from. Work in a copy of the Intermediate Example project, at its top: copy
`example_projects/intermediate/` from the download to a folder of your own, copy the
`sqlglot_composer` folder into it, as a Project holds it, and open a notebook there. This page
makes the same copy in its first step, from the download the Toolbox came in, and runs its
steps there:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

Done when the folder holds the Intermediate Example project's files. Then step 2.

### 2. Import the Toolbox, project, query and execute

Goal: every name the steps call. Import the Toolbox, the `project` module, and your query and
execute:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from warehouse import connect, query, execute
>>> connect(example_database)

Done when the three imports run without an error. Then step 3.

### 3. Load a Table notebook's logic

Goal: the table's functions, in your notebook. mart.job_day_facts holds each job's events, runs
and minutes per day, beside the team that owned the job that day. It is partitioned by its day,
dt. Its Table notebook, the notebook whose cells create and write the table,
tables/mart__job_day_facts/mart__job_day_facts.ipynb, defines its steps as functions in its
logic cell, and `project.load` gives them, from any notebook of the Project:

>>> facts = project.load("mart.job_day_facts")  # -> the notebook's functions
>>> facts
The logic of mart.job_day_facts: create, rows, preview, write_days, write.

These are the functions of its logic cell this how-to uses, as the notebook has them:

    from sqlglot_composer import FROM, INSERT_OVERWRITE, SELECT, Clause, Statement, statement
    from building_blocks.days_rewritten import first_day_written
    from building_blocks.events_per_job import events_per_job
    from building_blocks.owner_on_day import owner_on_day
    from references.mart__job_day_facts import job_day_facts
    from references.ops__job_owners import job_owners

    DAY = "2026-09-24"  # the last day write() writes, the Example database's last day


    def rows(first_day: str, last_day: str) -> list[Clause]:
        events = events_per_job(first_day, last_day)
        return [
            SELECT(events.job_id, job_owners.team, events.events, events.runs, events.minutes,
                   events.dt),
            FROM(events),
            owner_on_day(events.job_id, events.dt, first_day=first_day, last_day=last_day),
        ]


    def write_days(first_day: str, last_day: str) -> Statement:
        return statement(INSERT_OVERWRITE(job_day_facts), *rows(first_day, last_day))


    def write() -> Statement:
        return write_days(first_day_written(DAY), DAY)

`events_per_job`, a Building block, a piece of your own code reused across notebooks, counts
each job's day of `ops.job_events`, and keeps the day, dt, in its GROUP_BY and its SELECT, so
each day's numbers stay apart. `owner_on_day` joins each row to the team that owned the job
that day.

Done when `facts` lists create, rows, preview, write_days and write. Then step 4.

### 4. Build a write over a range of days

Goal: one write that fills each day's Partition from its rows. `write_days` builds one write
over a whole range of days. `INSERT_OVERWRITE` with no `partition=` fills the table's partition
column, dt, from each row's own day, and replaces only the days the rows hold: any other day of
the table keeps what it held. The partition column may go anywhere in SELECT: the Toolbox puts
it last, where Hive takes it from. Here, the 14 days the Example database holds:

>>> backfill = facts.write_days("2026-09-11", "2026-09-24")  # -> Statement
>>> text = show_hive(backfill)  # -> str
-- The Session setting "dynamic_partitions": this write fills dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
WITH events_per_job AS (
...
)
INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt)
SELECT
  events_per_job.job_id,
  job_owners.team,
  events_per_job.events,
  events_per_job.runs,
  events_per_job.minutes,
  events_per_job.dt
FROM events_per_job
LEFT JOIN ops.job_owners AS job_owners
  ON job_owners.job_id = events_per_job.job_id
  AND job_owners.dt = events_per_job.dt
  AND job_owners.dt BETWEEN '2026-09-11' AND '2026-09-24';

PARTITION(dt) names no day: Hive takes each row's day from its last column. Filling
Partitions from the rows needs Hive's dynamic partitioning switched on, the two SET lines
above the write: the Session setting "dynamic_partitions". A Session setting is a Hive SET
sent before a Statement, which holds for the rest of the session.

Done when the Hive reads `INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt)`. Then
step 5.

### 5. Check the rows first

Goal: see the rows a write would save, before it saves them. `facts.preview()` is the same
rows as a plain SELECT, for the days `write()` writes, which the Example database runs:

>>> run_query(facts.preview(), query)  # -> DataFrame
   job_id     team  events  runs  minutes          dt
0       1     data       2     1       10  2026-09-22
1       1     data       2     1       10  2026-09-24
2       1     data       2     1       12  2026-09-23
3       2  finance       1     1        0  2026-09-24
4       2  finance       2     1       18  2026-09-22
5       2  finance       2     1       18  2026-09-23

Job 2, invoice_sync, is still running on 2026-09-24: its day has a start and no finish yet,
so 0 minutes.

Done when the rows are what you expect for each day. Then step 6.

### 6. Send the Session setting

Goal: dynamic partitioning switched on in your session. `run_execute` sends a write through
your execute, without its SET lines. So send the Session setting first,
`hive_settings("dynamic_partitions")`, which holds for as long as your execute keeps one
session:

>>> run_execute(hive_settings("dynamic_partitions"), execute)
execute: SET hive.exec.dynamic.partition=true
execute: SET hive.exec.dynamic.partition.mode=nonstrict

Done when execute has been given both SET lines. Then step 7.

### 7. Send the write

Goal: the days written. Send the write through your execute:

>>> run_execute(backfill, execute)
execute: WITH events_per_job AS (

The write is an INSERT OVERWRITE, which replaces the days it writes. So if it fails, say on a
network error, send it again: a day written twice holds the same rows, not twice as many.

Done when execute has been given the write. Then step 8.

### 8. Rewrite the last few days on every run, for rows that come in late

Goal: a write that picks up late rows. An event can reach the warehouse a day or two after its
day: say a run finished at 23:50 on 2026-09-24, and its `"finish"` row arrives at 00:30 the
next morning, after the run that wrote 2026-09-24. The row lands in 2026-09-24's Partition of
`ops.job_events`, a day a write of only the newest day would never look at again.

So `write()` writes the last 3 days, ending on `DAY`, on every run. The 3 is written once, in
the Building block building_blocks/days_rewritten.py, which every table of the Project that
counts or adds up rows per day reads:

>>> from building_blocks.days_rewritten import DAYS_REWRITTEN, first_day_written
>>> DAYS_REWRITTEN  # -> int
3
>>> first_day_written("2026-09-24")  # -> str
'2026-09-22'
>>> print(to_hive(facts.write()).splitlines()[-1])
  AND job_owners.dt BETWEEN '2026-09-22' AND '2026-09-24'

Tomorrow's run, with `DAY` one day on, writes 2026-09-24 again, now with any event of that day
that came in overnight, writes 2026-09-23 again with the same rows it already held, and writes
2026-09-25 for the first time. 2026-09-22, outside the window, keeps what it held. A day
already right comes out the same, and a day that changed comes out new, so the same write can
go out any number of times. A day whose rows all went away is the one exception: the write has
no row for it, so it fills nothing there, and the day keeps its old rows.

Rewrite as many days as late rows can take to arrive, plus one: rows up to two days late need
the last three. A row later than that needs a one-off backfill of its day, with `write_days`.

Done when `write()`'s Hive reads the days 2026-09-22 to 2026-09-24. Then step 9.

### 9. Build one write per day

Goal: a function that writes one named Partition. At work a backfill can cover months, more
than one Statement should read at once. Then write it a Partition at a time: `one_day` below
builds one write, which names its Partition with `partition={"dt": day}` and leaves dt out of
SELECT. The Building blocks make the rows, as in the notebook, and `WHERE` keeps only the day
the write names, so the Toolbox can see each row's day is that one, and each job has one row in
it, as the table's Key, job_id and dt, needs. A Key is the columns whose values name exactly one
row:

>>> from building_blocks.events_per_job import events_per_job
>>> from building_blocks.owner_on_day import owner_on_day
>>> from references.mart__job_day_facts import job_day_facts
>>> from references.ops__job_owners import job_owners
>>> def one_day(day: str) -> Statement:
...     events = events_per_job(day, day)
...     return statement(
...         INSERT_OVERWRITE(job_day_facts, partition={"dt": day}),
...         SELECT(events.job_id, job_owners.team, events.events, events.runs,
...                events.minutes),
...         FROM(events),
...         owner_on_day(events.job_id, events.dt, first_day=day, last_day=day),
...         WHERE(equals(events.dt, day)),
...     )

Done when `one_day` is defined. Then step 10.

### 10. Build a write for each day of the range

Goal: one write per day, in a list. Python's `datetime` makes the list of days:

>>> import datetime
>>> first = datetime.date(2026, 9, 1)
>>> september = [str(first + datetime.timedelta(days=n)) for n in range(30)]  # -> list[str]
>>> september[:3]
['2026-09-01', '2026-09-02', '2026-09-03']
>>> writes = [one_day(day) for day in september]  # -> list[Statement]

Done when `september` starts with 2026-09-01, 2026-09-02 and 2026-09-03. Then step 11.

### 11. Read where each write writes

Goal: see that each write names its own day. `insert_line` picks out the line of a write's Hive
that says where it writes, after the Building block's WITH:

>>> def insert_line(write: Statement) -> str:
...     return next(line for line in to_hive(write).splitlines() if line.startswith("INSERT"))
>>> for write in writes[:3]:
...     print(insert_line(write))
INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt = '2026-09-01')
INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt = '2026-09-02')
INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt = '2026-09-03')

Done when each line names its own day. Then step 12.

### 12. Send the writes in a loop

Goal: each day written, oldest first. Each write names its Partition, so it needs no Session
setting. `show_hive(writes)` prints them all, each headed by its place in the list; a loop
sends them, oldest first:

>>> from collections.abc import Callable
>>> def send_each(writes: list[Statement], execute: Callable[[str], None]) -> None:
...     for write in writes:
...         run_execute(write, execute)
>>> send_each(writes[:2], execute=execute)
execute: WITH events_per_job AS (
execute: WITH events_per_job AS (

A day the tables it reads hold no rows of is written with no rows. If the loop stops halfway,
send it again from the day that failed, or from the start.

Done when execute has been given one write per day sent. Then step 13.

### 13. Build a write per region

Goal: writes for a table partitioned by region. Partitions are any columns, not only days.
mart.budget_overruns holds each job's budget in a region and the days its cost went over it,
and is partitioned by region. Its `write()` gives a list, a write per region, each naming its
Partition, so a write replaces that region's Partition alone:

>>> overruns = project.load("mart.budget_overruns")  # -> the notebook's functions
>>> by_region = overruns.write()  # -> list[Statement]
>>> for write in by_region:
...     print(to_hive(write).splitlines()[0])
INSERT OVERWRITE TABLE mart.budget_overruns PARTITION(region = 'eu')
INSERT OVERWRITE TABLE mart.budget_overruns PARTITION(region = 'us')
>>> run_query(overruns.preview(), query)  # -> DataFrame
   job_id  budget_cents  days  days_over
0       1           150    14          1
1       2           200    10          2

Done when there is one write for eu and one for us. Then step 14.

### 14. Send one region's write

Goal: eu rewritten, us left as it is. `overruns.preview()` is eu's rows. To rewrite eu alone,
send its write alone; the us Partition keeps what it held:

>>> run_execute(by_region[0], execute)
execute: INSERT OVERWRITE TABLE mart.budget_overruns PARTITION(region = 'eu')

Done when execute has been given eu's write alone. Then step 15.

### 15. Read a source that writes its days another way

Goal: a write whose source writes days like 20260924. mart.job_day_costs holds each job's cost
per day, all regions added up, from `ops.region_costs`, which writes its days like 20260924,
where the Project's other tables write 2026-09-24. The Toolbox compares a day exactly as it is
written, so the Building block building_blocks/costs_per_job.py writes the days it is asked for
the table's way, and the day each row holds back the Project's way, so mart.job_day_costs saves
its days like 2026-09-24:

>>> from building_blocks.costs_per_job import as_written_here
>>> as_written_here("2026-09-24")  # -> str
'20260924'
>>> costs = project.load("mart.job_day_costs")  # -> the notebook's functions
>>> hive = to_hive(costs.write())  # -> str
>>> [line for line in hive.splitlines() if "BETWEEN" in line]
["    region_costs.dt BETWEEN '20260922' AND '20260924'"]

Its write is the last 3 days too, read as `ops.region_costs` writes them, and written into
Partitions named like 2026-09-24.

Done when the write reads `BETWEEN '20260922' AND '20260924'`. Then step 16.

### 16. Write several Saved tables in order

Goal: every table written after the tables it reads. mart.team_days reads both
mart.job_day_facts and mart.job_day_costs, so it must be written after them, the same days.
`project.run_tables` loads each table's `write()` and sends them in the order Lineage draws
them, every table before the tables that read it, with the Session setting
"dynamic_partitions" first, since some fill their Partitions from their rows. Lineage is the
record of which table columns feed each column a Statement gives:

>>> project.run_tables(execute=execute,  # -> a report, printed
...                    tables=["mart.team_days", "mart.job_day_costs", "mart.job_day_facts"])
execute: SET hive.exec.dynamic.partition=true
execute: SET hive.exec.dynamic.partition.mode=nonstrict
execute: WITH costs_per_job AS (
1 of 3: mart.job_day_costs  worked
execute: WITH events_per_job AS (
2 of 3: mart.job_day_facts  worked
execute: INSERT OVERWRITE TABLE mart.team_days PARTITION(dt)
3 of 3: mart.team_days      worked
Wrote 3 tables, in order.

Left out, `tables=` is every Table folder of the Project, and with no execute,
`project.run_tables()` prints each write's Hive in that order and sends nothing. If a write
fails, it stops there, and the tables after it aren't written, so a team's day is never written
from facts that weren't.

Done when it prints `Wrote 3 tables, in order.` with mart.team_days last. Then check it worked,
below.

## Check it worked

A write that fills Partitions from its rows replaces the Partitions its rows fill, and no
other, so the days `write()` rewrites are the days `facts.preview()` gives, the last three:

>>> sorted(set(run_query(facts.preview(), query)["dt"]))  # -> list[str]
['2026-09-22', '2026-09-23', '2026-09-24']

The day-at-a-time writes come oldest first, with none missing:

>>> for write in writes[-2:]:
...     print(insert_line(write))
INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt = '2026-09-29')
INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt = '2026-09-30')

At work, after a rewrite, read the Saved table's days back with `run_query`, and compare them
with `facts.preview()`'s rows.

Before you go on, check that:

- `facts.preview()` gives the days 2026-09-22, 2026-09-23 and 2026-09-24;
- the last two day-at-a-time writes name 2026-09-29 and 2026-09-30;
- `project.run_tables` printed `Wrote 3 tables, in order.`

## Common mistakes

### Leaving the partition column out of a write that fills it from its rows

A write with no `partition=` takes each row's Partition from its own partition column, so its
SELECT must give it. Leave it out, and the write is refused as you build it:

>>> events = events_per_job("2026-09-22", "2026-09-24")  # -> Table
>>> statement(
...     INSERT_OVERWRITE(job_day_facts),
...     SELECT(events.job_id, job_owners.team, events.events, events.runs, events.minutes),
...     FROM(events),
...     owner_on_day(events.job_id, events.dt, first_day="2026-09-22",
...                  last_day="2026-09-24"),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(job_day_facts): it leaves out dt.
...

Add `events.dt` to SELECT, as the notebook's `rows` does, or name the Partition with
`partition={"dt": ...}`, as `one_day` does.

### Naming one Partition in partition= while reading three days

`partition={"dt": "2026-09-24"}` names the Partition every row goes to, whatever day it was
read from. With the Building block reading three days, each job would have three rows in
2026-09-24, one from each day read, so the table's Key, job_id and dt, would repeat. The
Toolbox refuses it as you build it, with a Guard, a check that refuses a Statement that would
give a wrong result:

>>> statement(
...     INSERT_OVERWRITE(job_day_facts, partition={"dt": "2026-09-24"}),
...     SELECT(events.job_id, job_owners.team, events.events, events.runs, events.minutes),
...     FROM(events),
...     owner_on_day(events.job_id, events.dt, first_day="2026-09-22",
...                  last_day="2026-09-24"),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(job_day_facts) can't show that each row it writes has a Key
                  (job_id, dt) of its own: events_per_job's rows are told apart by job_id, dt,
                  and SELECT leaves out events_per_job.dt, so nothing makes its rows one for
                  each job_id.
...

`partition=` says where the rows go, and the reads which rows: keep them the same, with
`WHERE(equals(events.dt, day))` as `one_day` does, or leave `partition=` out and let each
row's own day say, as `write_days` does. A table with no Key isn't checked, so there nothing
would stop it: each day's Partition would hold the counts of three days.

### Using INSERT_INTO for a window of days

No message stops you here. `INSERT_INTO` adds rows to a Partition and keeps what it held. Its
Hive starts `INSERT INTO` where the steps' starts `INSERT OVERWRITE TABLE`:

>>> added = statement(INSERT_INTO(job_day_facts), *facts.rows("2026-09-22", "2026-09-24"))
>>> insert_line(added)  # -> str
'INSERT INTO mart.job_day_facts PARTITION(dt)'

Nothing refuses it, since adding rows is sometimes what you want. But in a window of three
days each day is written on three runs in a row, so each would hold its rows three times over,
and every count read from it would come out three times too big. Use `INSERT_OVERWRITE` for
any Partition you may write again.

### A range written back to front

`between` takes the earlier day first. With the days swapped, no day is inside the range, and
the Toolbox stops at once rather than write nothing:

>>> facts.write_days("2026-09-24", "2026-09-11")
Traceback (most recent call last):
...
ValueError:
  What happened:  between(job_events.dt, '2026-09-24', '2026-09-11') starts after it ends.
...

Give the earlier day first: `facts.write_days("2026-09-11", "2026-09-24")`.

### Writing a day the usual way, on a table that writes it another way

The Toolbox compares a day exactly as you write it, so a day written with dashes matches no
row of `ops.region_costs`, and a Statement that reads it gives nothing:

>>> from references import ops
>>> with_dashes = statement(  # -> Statement
...     SELECT(ops.region_costs.job_id, ops.region_costs.cost_cents),
...     FROM(ops.region_costs),
...     WHERE(between(ops.region_costs.dt, "2026-09-22", "2026-09-24")),
... )
>>> run_query(with_dashes, query)  # -> DataFrame
Empty DataFrame
Columns: [job_id, cost_cents]
Index: []

A write from it would write no rows, and nothing would say so. Write each day the table's way,
as `as_written_here` does.

### Giving run_execute a whole list

`run_execute` sends one Statement, and refuses a list, such as a `write()` that gives a write
per region:

>>> run_execute(by_region, execute)
Traceback (most recent call last):
...
TypeError:
  What happened:  run_execute was given [...], which isn't a Statement.
...

Send each in turn, with a loop, as `send_each` does, or let `project.run_tables` send them.

## Next

- Roll the days up into weeks and months, from a Saved table's days:
  [Rollups and subtotals](#rollups_and_subtotals).
- Look things up as of each day in a table that keeps a copy of itself every day, as
  `owner_on_day` does: [Look things up as of a day](#look_things_up_as_of_a_day).
- See where each column of mart.team_days comes from, through the tables it reads:
  [Follow lineage](#follow_lineage).
- Choose how a Saved table is stored, its Buckets and its compression: [Choose how a Saved
  table is stored](#choose_how_a_saved_table_is_stored).
- The gallery's [Saved table Worked example](examples.html#saved_table), and its Worked
  examples of [`INSERT_OVERWRITE`](examples.html#INSERT_OVERWRITE) and
  [`hive_settings`](examples.html#hive_settings).
"""
