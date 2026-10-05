"""Incremental loads and late data

For: Intermediate

## Goal

Keep a Saved table up to date by rewriting only its last few days on every run, so rows that
reach the warehouse a day or two late still land in the right day. You build one Statement over
a sliding window of days, split it into one write per day with `by_day`, and see why
`INSERT_OVERWRITE` lets you send the same days again safely.

## When you'd use it

For any Saved table filled from a table whose recent days can still change: events that arrive
late, a run that finishes after midnight, a bill that comes in the next day. Rewriting
yesterday as well as today costs a little more each run, and saves finding and fixing a short
day by hand later.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> job_events = example_database.job_events

### Describe the Saved table

mart.job_day will hold one row per job per day: how many runs started and how many finished.
It doesn't exist until you create it, so its Table reference is written by hand. At work it
goes in a file of its own, table_references/job_day.py:

>>> job_day = Table(
...     "mart.job_day",
...     columns={
...         "job_id": "bigint",
...         "starts": "bigint",
...         "finishes": "bigint",
...         "dt": "string",  # the day the runs started
...     },
...     date_partition="dt",
...     key=["job_id", "dt"],
... )

Create it once, with `may_exist=True`, so sending it again on later runs does nothing:

>>> print(to_hive(create_table(job_day, may_exist=True)))
CREATE TABLE IF NOT EXISTS mart.job_day (
  job_id BIGINT,
  starts BIGINT,
  finishes BIGINT
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC

### Preview the rows for the last three days

Before writing anything, run the same counts as a plain SELECT, to see what each day will
hold. `count_rows(where=...)` counts only the rows that meet its condition, so one pass counts
starts and finishes side by side. `last_n_days(job_events.dt, 3)` reads the three days before
today: here 2026-09-22 to 2026-09-24.

>>> preview = statement(
...     SELECT(job_events.dt, job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...            AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes")),
...     FROM(job_events),
...     WHERE(last_n_days(job_events.dt, 3)),
...     GROUP_BY(job_events.dt, job_events.job_id),
... )
>>> run(preview, send=example_database.send)
           dt  job_id  starts  finishes
0  2026-09-22       1       1         1
1  2026-09-22       2       1         1
2  2026-09-23       1       1         1
3  2026-09-23       2       1         1
4  2026-09-24       1       1         1
5  2026-09-24       2       1         0

Job 2, invoice_sync, started on 2026-09-24 and hasn't finished. When its `"finish"` row arrives,
it lands in 2026-09-24's partition, a day that a run writing only today would never look at
again.

### Write the last three days, one day at a time

A write fills one day of a Saved table. So build the write over the whole window, then
`by_day` splits it into one write per day, oldest first. Each selects the Saved table's columns
by name, apart from its Date partition, which the Toolbox fills from the day read. dt stays in
`GROUP_BY`, so each day's counts stay apart:

>>> def rewrite_last_days(n):
...     return by_day(statement(
...         INSERT_OVERWRITE(job_day),
...         SELECT(job_events.job_id,
...                AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...                AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes")),
...         FROM(job_events),
...         WHERE(last_n_days(job_events.dt, n)),
...         GROUP_BY(job_events.dt, job_events.job_id),
...     ))
>>> days = rewrite_last_days(3)
>>> text = show_hive(days)
-- 1 of 3: days[0]
INSERT OVERWRITE TABLE mart.job_day PARTITION(dt = '2026-09-22')
SELECT
  job_events.job_id,
  COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END) AS starts,
  COUNT(CASE WHEN job_events.event_type = 'finish' THEN 1 END) AS finishes
FROM ops.job_events AS job_events
WHERE
  job_events.dt = '2026-09-22'
GROUP BY
  job_events.dt,
  job_events.job_id;
<BLANKLINE>
-- 2 of 3: days[1]
INSERT OVERWRITE TABLE mart.job_day PARTITION(dt = '2026-09-23')
SELECT
  job_events.job_id,
  COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END) AS starts,
  COUNT(CASE WHEN job_events.event_type = 'finish' THEN 1 END) AS finishes
FROM ops.job_events AS job_events
WHERE
  job_events.dt = '2026-09-23'
GROUP BY
  job_events.dt,
  job_events.job_id;
<BLANKLINE>
-- 3 of 3: days[2]
INSERT OVERWRITE TABLE mart.job_day PARTITION(dt = '2026-09-24')
SELECT
  job_events.job_id,
  COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END) AS starts,
  COUNT(CASE WHEN job_events.event_type = 'finish' THEN 1 END) AS finishes
FROM ops.job_events AS job_events
WHERE
  job_events.dt = '2026-09-24'
GROUP BY
  job_events.dt,
  job_events.job_id;

The Example database can't be written to, so the writes stop here. At work, a function sends
them in order through your own send, and you call it once a day, `load_last_days(send)`:

    def load_last_days(send):
        for day in rewrite_last_days(3):
            run(day, send=send)

### Why sending a day again is safe

`INSERT OVERWRITE ... PARTITION(dt = '2026-09-24')` replaces everything that day held. Today's
run writes 2026-09-24 with invoice_sync's start and no finish. Tomorrow's run reads
2026-09-23 to 2026-09-25: it writes 2026-09-24 again, now with the finish that arrived
overnight, writes 2026-09-23 again with the same rows it already held, and writes 2026-09-25
for the first time.

A day already right comes out the same, and a day that changed comes out new, so the same
writes can go out any number of times: after a failed run, twice by mistake, or for a whole
month again with a wider window.

### Choose how many days

Rewrite as many days as late rows can take to arrive, plus one. If rows can come in up to two
days late, rewrite the last three. A day outside the window is never read again, so a row
arriving later than that needs a one-off backfill of its day: `by_day` over a `between` of the
days to fix, the same Statement with other days.

## Check it worked

The window holds one write per day, each for its own day:

>>> for day in days:
...     print(to_hive(day).splitlines()[0])
INSERT OVERWRITE TABLE mart.job_day PARTITION(dt = '2026-09-22')
INSERT OVERWRITE TABLE mart.job_day PARTITION(dt = '2026-09-23')
INSERT OVERWRITE TABLE mart.job_day PARTITION(dt = '2026-09-24')

At work, after a run, read the Saved table's last three days back through `job_day` with
`run`, and compare them with `preview`'s rows.

## Common mistakes

### Sending the window as one write

A write fills one day, so a write that reads three days is refused when it becomes Hive,
before anything is sent:

>>> whole_window = statement(
...     INSERT_OVERWRITE(job_day),
...     SELECT(job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...            AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes")),
...     FROM(job_events),
...     WHERE(last_n_days(job_events.dt, 3)),
...     GROUP_BY(job_events.dt, job_events.job_id),
... )
>>> to_hive(whole_window)
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(job_day) covers 3 days.
...

Split it with `by_day`, as `rewrite_last_days` does.

### Leaving dt out of GROUP_BY

Without the day in `GROUP_BY`, each job's counts would run across all three days, and each
day's write couldn't hold just its own day. `by_day` refuses to split it:

>>> by_day(statement(
...     INSERT_OVERWRITE(job_day),
...     SELECT(job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...            AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes")),
...     FROM(job_events),
...     WHERE(last_n_days(job_events.dt, 3)),
...     GROUP_BY(job_events.job_id),
... ))
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  by_day can't split this Statement: it groups rows without keeping the Date partition job_events.dt.
...

### Using INSERT_INTO for the window

`INSERT_INTO` adds rows to a day and keeps what it held. Its Hive differs from the steps' in
one word:

>>> print(to_hive(statement(
...     INSERT_INTO(job_day),
...     SELECT(job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...            AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes")),
...     FROM(job_events),
...     WHERE(equals(job_events.dt, "2026-09-24")),
...     GROUP_BY(job_events.dt, job_events.job_id),
... )).splitlines()[0])
INSERT INTO mart.job_day PARTITION(dt = '2026-09-24')

Nothing refuses it, since adding rows to a day is sometimes what you want. But in a sliding
window each day is written on three runs in a row, so each would hold its rows three times over,
and every count read from it would come out three times too big. Use `INSERT_OVERWRITE` for any
day you may write again.

## Next

- Chain Saved tables into layers, each read by the next: [A layered
  pipeline](#a_layered_pipeline).
- Roll the days up into weeks and months: [Week and month rollups](#week_and_month_rollups).
- The gallery's [Saved table Worked example](examples.html#saved_table), which creates, writes,
  adds to, backfills and rebuilds one, and its Worked example of
  [`by_day`](examples.html#by_day).
"""
