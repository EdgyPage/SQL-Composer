"""Rewrite some partitions

For: Intermediate

## Goal

Rewrite some of a Saved table's Partitions, and leave the rest as they are: a range of days of
a table partitioned by its day, in one write that fills each Partition from its rows, or in a
loop of writes that each name their Partition with `partition={...}`; the last few days again
on every run, for rows that come in late; a table partitioned by region, written a region at a
time; and a table whose source writes its days another way. Then write several Saved tables in
order with `project.run_tables`.

## When you'd use it

- When a Saved table is new, and the Partitions it should already hold are empty: a backfill.
- After fixing a mistake in a write, since every Partition it wrote holds the mistake.
- When rows can come in late, such as a bill a day or two after its day, so the last few days
  of a table that counts them must be written again on each run.
- When one region's numbers changed, and the other regions' Partitions should stay as they
  are.

The Example database can't be written to, so on this page each write shows its Hive, and is
sent through the Project's execute, which here prints the first line of what it would send
and changes nothing. The rows a write would save are checked with a plain SELECT first, which
the Example database does run.

It needs the Getting started how-tos [Share Building blocks](#share_building_blocks) and [Save
a table](#save_a_table).

## Steps

### Start from the Intermediate Example project

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

Then import the Toolbox, the `project` module, and your query and execute:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from warehouse import query, execute

### Load a Table notebook's logic

mart.job_day_facts holds each job's events, runs and minutes per day, beside the team that
owned the job that day. It is partitioned by its day, dt. Its Table notebook,
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

`events_per_job`, a Building block, counts each job's day of `ops.job_events`, and keeps the
day, dt, in its GROUP_BY and its SELECT, so each day's numbers stay apart. `owner_on_day`
joins each row to the team that owned the job that day.

### Write a range of days in one write

`write_days` builds one write over a whole range of days. `INSERT_OVERWRITE` with no
`partition=` fills the table's partition column, dt, from each row's own day, and replaces only
the days the rows hold: any other day of the table keeps what it held. The partition column may
go anywhere in SELECT: the Toolbox puts it last, where Hive takes it from. Here, the 14 days
the Example database holds:

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
above the write: the Session setting "dynamic_partitions".

### Check the rows first

`facts.preview()` is the same rows as a plain SELECT, for the days `write()` writes, which
the Example database runs:

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

### Send it

`run_execute` sends a write through your execute. It doesn't send the SET lines with it: send
the Session setting first, `hive_settings("dynamic_partitions")`, which holds for as long as
your execute keeps one session:

>>> run_execute(hive_settings("dynamic_partitions"), execute)
execute: SET hive.exec.dynamic.partition=true
execute: SET hive.exec.dynamic.partition.mode=nonstrict
>>> run_execute(backfill, execute)
execute: WITH events_per_job AS (

The write is an INSERT OVERWRITE, which replaces the days it writes. So if it fails, say on a
network error, send it again: a day written twice holds the same rows, not twice as many.

### Rewrite the last few days on every run, for rows that come in late

An event can reach the warehouse a day or two after its day: say a run finished at 23:50 on
2026-09-24, and its `"finish"` row arrives at 00:30 the next morning, after the run that wrote
2026-09-24. The row lands in 2026-09-24's Partition of `ops.job_events`, a day a write of only
the newest day would never look at again.

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

### Write a range a Partition at a time, in a loop

At work a backfill can cover months, more than one Statement should read at once. Then write it
a Partition at a time: `one_day` below builds one write, which names its Partition with
`partition={"dt": day}` and leaves dt out of SELECT, and a Python loop over the days. The
Building blocks make the rows, as in the notebook, and `WHERE` keeps only the day the write
names, so the Toolbox can see each row's day is that one, and each job has one row in it, as
the table's Key, job_id and dt, needs:

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

Python's `datetime` makes the list of days:

>>> import datetime
>>> first = datetime.date(2026, 9, 1)
>>> september = [str(first + datetime.timedelta(days=n)) for n in range(30)]  # -> list[str]
>>> september[:3]
['2026-09-01', '2026-09-02', '2026-09-03']
>>> writes = [one_day(day) for day in september]  # -> list[Statement]

`insert_line` picks out the line of a write's Hive that says where it writes, after the
Building block's WITH:

>>> def insert_line(write: Statement) -> str:
...     return next(line for line in to_hive(write).splitlines() if line.startswith("INSERT"))
>>> for write in writes[:3]:
...     print(insert_line(write))
INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt = '2026-09-01')
INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt = '2026-09-02')
INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt = '2026-09-03')

Each names its Partition, so it needs no Session setting. `show_hive(writes)` prints them all,
each headed by its place in the list; a loop sends them, oldest first:

>>> from collections.abc import Callable
>>> def send_each(writes: list[Statement], execute: Callable[[str], None]) -> None:
...     for write in writes:
...         run_execute(write, execute)
>>> send_each(writes[:2], execute=execute)
execute: WITH events_per_job AS (
execute: WITH events_per_job AS (

A day the tables it reads hold no rows of is written with no rows. If the loop stops halfway,
send it again from the day that failed, or from the start.

### A table partitioned by region, a region at a time

Partitions are any columns, not only days. mart.budget_overruns holds each job's budget in a
region and the days its cost went over it, and is partitioned by region. Its `write()` gives a
list, a write per region, each naming its Partition, so a write replaces that region's
Partition alone:

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

`overruns.preview()` is eu's rows. To rewrite eu alone, send its write alone; the us
Partition keeps what it held:

>>> run_execute(by_region[0], execute)
execute: INSERT OVERWRITE TABLE mart.budget_overruns PARTITION(region = 'eu')

### A source that writes its days another way

mart.job_day_costs holds each job's cost per day, all regions added up, from `ops.region_costs`,
which writes its days like 20260924, where the Project's other tables write 2026-09-24. The
Toolbox compares a day exactly as it is written, so the Building block
building_blocks/costs_per_job.py writes the days it is asked for the table's way, and the day
each row holds back the Project's way, so mart.job_day_costs saves its days like 2026-09-24:

>>> from building_blocks.costs_per_job import as_written_here
>>> as_written_here("2026-09-24")  # -> str
'20260924'
>>> costs = project.load("mart.job_day_costs")  # -> the notebook's functions
>>> hive = to_hive(costs.write())  # -> str
>>> [line for line in hive.splitlines() if "BETWEEN" in line]
["    region_costs.dt BETWEEN '20260922' AND '20260924'"]

Its write is the last 3 days too, read as `ops.region_costs` writes them, and written into
Partitions named like 2026-09-24.

### Write several Saved tables in order

mart.team_days reads both mart.job_day_facts and mart.job_day_costs, so it must be written
after them, the same days. `project.run_tables` loads each table's `write()` and sends them in
the order Lineage draws them, every table before the tables that read it, with the Session
setting "dynamic_partitions" first, since some fill their Partitions from their rows:

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
Toolbox refuses it as you build it:

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

### Handing run_execute a whole list

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
