"""Incremental loads and late data

For: Intermediate

## Goal

Keep a Saved table up to date by rewriting only its last few days on every run, so rows that
reach the warehouse a day or two late still land in the right day. You build one write over a
sliding window of days, which fills each day's Partition from its rows, and see why
`INSERT_OVERWRITE` lets you send the same days again safely.

## When you'd use it

For any Saved table filled from a table whose recent days can still change: events that reach
the warehouse a day or two after the day they happened, a cost left NULL until its bill comes
in. Rewriting the days before yesterday as well as yesterday costs a little more each run, and
saves finding and fixing a short day by hand later. [Save a table](#save_a_table) and
[Backfill a range of days](#backfill_a_range_of_days) start with writing one day, and many.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> job_events = example_database.job_events

### Describe the Saved table

mart.job_day will hold one row per job per day: how many runs started and how many finished.
It is partitioned by dt, one Partition per day. It doesn't exist until you create it, so its
Table reference is written by hand. At work it goes in a file of its own in your Project,
references/mart__job_day.py:

>>> job_day = Table(
...     "mart.job_day",
...     columns={
...         "job_id": "bigint",
...         "starts": "bigint",
...         "finishes": "bigint",
...         "dt": "string",  # the day the events happened
...     },
...     partitioned_by=["dt"],
...     key=["job_id", "dt"],
...     location="/data/your_team/mart.db/job_day",
... )

`location=` is the table's own folder, written exactly as the Hive should name it. Create the
table once, with `may_exist=True`, so sending it again on later runs does nothing:

>>> print(to_hive(create_table(job_day, may_exist=True)))
CREATE EXTERNAL TABLE IF NOT EXISTS mart.job_day (
  job_id BIGINT,
  starts BIGINT,
  finishes BIGINT...
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/mart.db/job_day'

### Preview the rows for the last three days

Before writing anything, run the same counts as a plain SELECT, to see what each day will
hold. `count_rows(where=...)` counts only the rows that meet its condition, so one pass counts
starts and finishes side by side. `last_n_days(job_events.dt, 3)` reads the three days before
today: here 2026-09-22 to 2026-09-24, since this page was run as if today were 2026-09-25. In
your own notebook today is your real today, so on the Example database it finds no rows: write
`between(job_events.dt, "2026-09-22", "2026-09-24")` there instead.

>>> preview = statement(
...     SELECT(job_events.dt, job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...            AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes")),
...     FROM(job_events),
...     WHERE(last_n_days(job_events.dt, 3)),
...     GROUP_BY(job_events.dt, job_events.job_id),
... )
>>> run(preview, query=example_database.query)
           dt  job_id  starts  finishes
0  2026-09-22       1       1         1
1  2026-09-22       2       1         1
2  2026-09-23       1       1         1
3  2026-09-23       2       1         1
4  2026-09-24       1       1         1
5  2026-09-24       2       1         0

Job 2, invoice_sync, is still running on 2026-09-24, so that day has its start and no finish.

Each event lands in the partition of the day it happened, but it can reach the warehouse late.
Say a run finished at 23:50 on 2026-09-24 and its `"finish"` row arrives at 00:30 the next
morning, after the run just after midnight wrote 2026-09-24: the row lands in 2026-09-24's
partition, a day that a run writing only its newest day would never look at again.

### Write the last three days in one write

`INSERT_OVERWRITE(job_day)` into a partitioned table puts each row in the Partition its own
dt names, and replaces only the Partitions its rows fill. So one write over the window rewrites
each of its three days. The write's `SELECT` lists every column of mart.job_day, dt included,
and dt stays in `GROUP_BY`, so each day's counts stay apart:

>>> def rewrite_last_days(n: int) -> Statement:
...     return statement(
...         INSERT_OVERWRITE(job_day),
...         SELECT(job_events.job_id,
...                AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...                AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes"),
...                job_events.dt),
...         FROM(job_events),
...         WHERE(last_n_days(job_events.dt, n)),
...         GROUP_BY(job_events.dt, job_events.job_id),
...     )
>>> last_days = rewrite_last_days(3)
>>> text = show_hive(last_days)
-- The Session setting "dynamic_partitions": this write fills dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.job_day PARTITION(dt)
SELECT
  job_events.job_id,
  COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END) AS starts,
  COUNT(CASE WHEN job_events.event_type = 'finish' THEN 1 END) AS finishes,
  job_events.dt
FROM ops.job_events AS job_events
WHERE
  job_events.dt BETWEEN '2026-09-22' AND '2026-09-24'
GROUP BY
  job_events.dt,
  job_events.job_id;

PARTITION(dt) in the Hive names no day: Hive takes each row's day from the last column the `SELECT`
gives, which the Toolbox puts last. Filling Partitions from the rows needs Hive's dynamic
partitioning switched on, the two SET lines above the write, which `run` doesn't send with it.

The Example database can't be written to, so the write stops here. At work, a function sends
the settings, then the write, through your own execute, and you call it once a day,
`load_last_days(execute)`, as [Run a daily pipeline](#run_a_daily_pipeline) does for one day:

    from collections.abc import Callable

    def load_last_days(execute: Callable[[str], None]) -> None:
        run(hive_settings("dynamic_partitions"), execute=execute)
        run(rewrite_last_days(3), execute=execute)

### Why sending a day again is safe

`INSERT OVERWRITE` replaces everything each Partition it fills held. Today's run writes
2026-09-24 with the events that have arrived so far. Tomorrow's run reads 2026-09-23 to
2026-09-25: it writes 2026-09-24 again, now with any event of that day that arrived overnight,
writes 2026-09-23 again with the same rows it already held, and writes 2026-09-25 for the
first time. 2026-09-22, outside the window, keeps what it held.

A day already right comes out the same, and a day that changed comes out new, so the same
write can go out any number of times: after a failed run, twice by mistake, or for a whole
month again with a wider window. A day whose rows all went away is the one exception: the
write has no row for it, so it fills nothing there, and the day keeps its old rows.

### Choose how many days

Rewrite as many days as late rows can take to arrive, plus one. If rows can come in up to two
days late, rewrite the last three. A day outside the window is never read again, so a row
arriving later than that needs a one-off backfill of its day: the same write with a `between`
of the days to fix, as [Backfill a range of days](#backfill_a_range_of_days) shows.

## Check it worked

The write replaces the Partitions its rows fill, and no other, so the days it rewrites are the
days `preview`'s rows hold, the three of the window:

>>> sorted(set(run(preview, query=example_database.query)["dt"]))
['2026-09-22', '2026-09-23', '2026-09-24']

At work, after a run, read the Saved table's last three days back through `job_day` with
`run`, and compare them with `preview`'s rows.

## Common mistakes

### Leaving dt out of SELECT

A write that fills Partitions from its rows takes each row's day from its own dt, so the
`SELECT` must give it. Leave it out, and the write is refused as you build it:

>>> statement(
...     INSERT_OVERWRITE(job_day),
...     SELECT(job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...            AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes")),
...     FROM(job_events),
...     WHERE(last_n_days(job_events.dt, 3)),
...     GROUP_BY(job_events.dt, job_events.job_id),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(job_day): it leaves out dt.
...

### Naming one day in partition= while reading three

No message stops you here. `partition={"dt": "2026-09-24"}` names the day every row goes to,
whatever day it was read from. With `WHERE` still reading three days, each job's three days of
counts go into 2026-09-24 as one:

>>> print(to_hive(statement(
...     INSERT_OVERWRITE(job_day, partition={"dt": "2026-09-24"}),
...     SELECT(job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...            AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes")),
...     FROM(job_events),
...     WHERE(last_n_days(job_events.dt, 3)),
...     GROUP_BY(job_events.job_id),
... )))
INSERT OVERWRITE TABLE mart.job_day PARTITION(dt = '2026-09-24')
SELECT
  job_events.job_id,
  COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END) AS starts,
  COUNT(CASE WHEN job_events.event_type = 'finish' THEN 1 END) AS finishes
FROM ops.job_events AS job_events
WHERE
  job_events.dt BETWEEN '2026-09-22' AND '2026-09-24'
GROUP BY
  job_events.job_id

`partition=` says where the rows go, and `WHERE` which rows are read: keep them the same, or
leave `partition=` out and let each row's own dt say, as `rewrite_last_days` does.

### Using INSERT_INTO for the window

No message stops you here. `INSERT_INTO` adds rows to a day and keeps what it held. Its Hive
starts `INSERT INTO` where the steps' starts `INSERT OVERWRITE TABLE`:

>>> print(to_hive(statement(
...     INSERT_INTO(job_day),
...     SELECT(job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...            AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes"),
...            job_events.dt),
...     FROM(job_events),
...     WHERE(last_n_days(job_events.dt, 3)),
...     GROUP_BY(job_events.dt, job_events.job_id),
... )).splitlines()[0])
INSERT INTO mart.job_day PARTITION(dt)

Nothing refuses it, since adding rows to a day is sometimes what you want. But in a sliding
window each day is written on three runs in a row, so each would hold its rows three times over,
and every count read from it would come out three times too big. Use `INSERT_OVERWRITE` for any
day you may write again.

## Next

- Chain Saved tables, each read by the next: [A pipeline of Saved
  tables](#a_pipeline_of_saved_tables).
- Roll the days up into weeks and months: [Week and month rollups](#week_and_month_rollups).
- The gallery's [Saved table Worked example](examples.html#saved_table), which creates, writes,
  adds to, backfills and rebuilds one, and its Worked example of
  [`INSERT_OVERWRITE`](examples.html#INSERT_OVERWRITE).
"""
