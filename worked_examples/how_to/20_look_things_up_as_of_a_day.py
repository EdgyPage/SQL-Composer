"""Look things up as of a day

For: Intermediate

## Goal

Find what was true on each day from a table that keeps a full copy of itself every day, a daily
snapshot: here, the team each job belonged to on the day it ran. You join on the day as well
as the job, count each team's runs as they were owned at the time, and pick each job's newest
row with `row_number`.

## When you'd use it

When a table holds one row per thing per day, such as each job's owner, each product's price or
each customer's plan, and another table's rows need the value from their own day, not today's.
A job that changed teams last week should count for its old team before the change and its new
team after it.

## Steps

### Import the Toolbox and name the tables

`ops.job_events` holds what each job's runs did over 14 days, 2026-09-11 to 2026-09-24: a
`"start"` row when a run starts, then `"finish"`, `"retry"` or `"fail"`. `ops.job_owners` is the
snapshot: every job's team and owner, once per day.

>>> from sqlglot_composer import *
>>> job_events = example_database.job_events
>>> job_owners = example_database.job_owners
>>> jobs = example_database.jobs

### Look at the snapshot

Each day holds one row per job, so its key is the job and the day together: job_id and dt.
Job 3, report_build, moved from the data team to finance on 2026-09-18:

>>> report_build_owners = statement(
...     SELECT(job_owners.dt, job_owners.team, job_owners.owner),
...     FROM(job_owners),
...     WHERE(equals(job_owners.job_id, 3),
...           between(job_owners.dt, "2026-09-16", "2026-09-19")),
... )
>>> run(report_build_owners, send=example_database.send)
           dt     team  owner
0  2026-09-16     data    ana
1  2026-09-17     data    ana
2  2026-09-18  finance  chloe
3  2026-09-19  finance  chloe

### Join each run to its own day's row

A run is a `"start"` row of job_events. Join the snapshot on both parts of its key: the same
job, and the same day. Each run then meets exactly one row, its job's row on the day it ran.
[Join tables safely](#join_tables_safely) shows why a join on only part of a key repeats rows.

The snapshot is a table with days too, so it needs its own bound in `WHERE`: the Toolbox checks
each table's days separately, and `equals(job_owners.dt, job_events.dt)` in `ON=` matches the
two tables' days without saying which days to read.

>>> report_build_runs = statement(
...     SELECT(job_events.dt, job_owners.team),
...     FROM(job_events),
...     JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_events.job_id),
...                                equals(job_owners.dt, job_events.dt))),
...     WHERE(equals(job_events.job_id, 3),
...           equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24"),
...           between(job_owners.dt, "2026-09-11", "2026-09-24")),
... )
>>> text = show_hive(report_build_runs)
SELECT
  job_events.dt,
  job_owners.team
FROM ops.job_events AS job_events
JOIN ops.job_owners AS job_owners
  ON job_owners.job_id = job_events.job_id AND job_owners.dt = job_events.dt
WHERE
  job_events.job_id = 3
  AND job_events.event_type = 'start'
  AND job_events.dt BETWEEN '2026-09-11' AND '2026-09-24'
  AND job_owners.dt BETWEEN '2026-09-11' AND '2026-09-24';
>>> run(report_build_runs, send=example_database.send)
           dt     team
0  2026-09-11     data
1  2026-09-14     data
2  2026-09-18  finance
3  2026-09-21  finance

report_build ran four times: twice for data, then twice for finance.

### Count each team's runs as of their day

The same join, for every job, grouped by team:

>>> runs_per_team = statement(
...     SELECT(job_owners.team, AS(count_rows(), "runs")),
...     FROM(job_events),
...     JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_events.job_id),
...                                equals(job_owners.dt, job_events.dt))),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24"),
...           between(job_owners.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_owners.team),
... )
>>> run(runs_per_team, send=example_database.send)
      team  runs
0     data    16
1  finance    12

data has nightly_load's 14 runs and report_build's 2 before the move; finance has
invoice_sync's 10 and report_build's 2 after it.

### Pick each job's newest row

To know who owns each job now, take each job's newest row of the snapshot. `row_number` numbers
each job's rows from the newest day down; the Statement that reads them keeps number 1. Its
`PARTITION_BY=` is SQL's word for the groups to number within, here each job, not the table's
partitions. Hive can't keep a row by its number in the same SELECT that numbers it, so the
numbering goes in a Derived table, a Statement given a name for the next one to read, which the
Hive writes at its top as `WITH numbered AS (...)`. [Reusable Derived
tables](#reusable_derived_tables) and [The latest row per key](#latest_row_per_key) start with
both:

>>> numbered = derived("numbered", statement(
...     SELECT(job_owners.job_id, job_owners.team, job_owners.owner, job_owners.dt,
...            AS(row_number(PARTITION_BY=job_owners.job_id,
...                          ORDER_BY=descending(job_owners.dt)), "newest_first")),
...     FROM(job_owners),
...     WHERE(between(job_owners.dt, "2026-09-11", "2026-09-24")),
... ))
>>> newest_owner = statement(
...     SELECT(numbered.job_id, numbered.team, numbered.owner, numbered.dt),
...     FROM(numbered),
...     WHERE(equals(numbered.newest_first, 1)),
... )
>>> text = show_hive(newest_owner)
WITH numbered AS (
  SELECT
    job_owners.job_id,
    job_owners.team,
    job_owners.owner,
    job_owners.dt,
    ROW_NUMBER() OVER (PARTITION BY job_owners.job_id ORDER BY job_owners.dt DESC) AS newest_first
  FROM ops.job_owners AS job_owners
  WHERE
    job_owners.dt BETWEEN '2026-09-11' AND '2026-09-24'
)
SELECT
  numbered.job_id,
  numbered.team,
  numbered.owner,
  numbered.dt
FROM numbered
WHERE
  numbered.newest_first = 1;
>>> run(newest_owner, send=example_database.send)
   job_id     team  owner          dt
0       1     data    ana  2026-09-24
1       2  finance    ben  2026-09-24
2       3  finance  chloe  2026-09-24
3       4      web   None  2026-09-24

[sqlglot_composer only]
Pasted into your own notebook, this `run` stops with a RuntimeError saying the Example database
can't run this Hive: sqlglot Composer's Example database runs Hive with sqlglot, which has no
`row_number`. The result above was worked out in pandas from the same rows, to show what the
Hive gives. Your warehouse runs the Hive above as it is.
[end]

Here every job is in every day's copy, so each newest row is from 2026-09-24, and reading that
one day would give the same. At work a row can drop out of a snapshot, such as a job that was
deleted, and then `row_number` still finds its last row, from whichever day that was. Nobody
owns cache_warm, so its owner is NULL (pandas shows it as None).

## Check it worked

Each run should meet exactly one row of the snapshot, so the teams' runs add up to every run
over the 14 days:

>>> every_run = statement(
...     SELECT(AS(count_rows(), "runs")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
... )
>>> run(every_run, send=example_database.send)
   runs
0    28
>>> int(run(runs_per_team, send=example_database.send)["runs"].sum())
28

## Common mistakes

### Joining the snapshot on the job alone

Without the day in `ON=`, each run meets its job's row on every day of the snapshot. The Toolbox
warns at the `JOIN`, since a job_owners row is unique only by job and day:

>>> runs_per_team_repeated = statement(
...     SELECT(job_owners.team, AS(count_rows(), "runs")),
...     FROM(job_events),
...     JOIN(job_owners, ON=equals(job_owners.job_id, job_events.job_id)),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24"),
...           between(job_owners.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_owners.team),
... )
>>> run(runs_per_team_repeated, send=example_database.send)
      team  runs
0     data   224
1  finance   168

Each run counted 14 times, once per day of the snapshot. The Warning's fix names the part of
the key left out, the day: add `equals(job_owners.dt, job_events.dt)` to `ON=`, as
`report_build_runs` does.

### Taking the team from today's table

No message stops you here. `ops.jobs` holds each job's team as it is today, so joining it
gives every run today's team:

>>> runs_per_team_today = statement(
...     SELECT(jobs.team, AS(count_rows(), "runs")),
...     FROM(job_events),
...     JOIN(jobs, ON=equals(jobs.job_id, job_events.job_id)),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(jobs.team),
... )
>>> run(runs_per_team_today, send=example_database.send)
      team  runs
0     data    14
1  finance    14

The total is still 28, but report_build's two runs before 2026-09-18 count for finance, a
team that didn't own it then. Use today's table only for what you want as
it is today.

### Leaving the snapshot's days unbounded

The day in `ON=` matches the two tables' days, but it doesn't bound job_owners' days, so the
Toolbox refuses as you build the Statement:

>>> statement(
...     SELECT(job_owners.team, AS(count_rows(), "runs")),
...     FROM(job_events),
...     JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_events.job_id),
...                                equals(job_owners.dt, job_events.dt))),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_owners.team),
... )
Traceback (most recent call last):
...
composer_core.refusals.LoadRefused:
  What happened:  JOIN(job_owners, ON=...) reads ops.job_owners, but nothing bounds its Date partition dt at both ends.
...

Bound it with the same days as the table it is joined to, in `WHERE` as the steps do. A bound
in `ON=`, such as `between(job_owners.dt, "2026-09-11", "2026-09-24")` inside the `all_of`,
counts too.

## Next

- Roll the days up into weeks and months: [Week and month rollups](#week_and_month_rollups).
- Save each team's day, as of its day, in a pipeline of Saved tables:
  [A pipeline of Saved tables](#a_pipeline_of_saved_tables).
- The gallery's [latest run per job](examples.html#latest_and_top_n), which shows why `max_of`
  on each column can mix values from different rows, and its Worked example of
  [`row_number`](examples.html#row_number).
"""

from sqlglot_composer import (
    FROM, SELECT, WHERE, all_columns, between, example_database, run, statement,
)

job_owners = example_database.job_owners


def newest_owner_in_pandas():
    """newest_owner's result, computed in pandas, not by running this Hive."""
    every_day = run(
        statement(SELECT(all_columns(job_owners)), FROM(job_owners),
                  WHERE(between(job_owners.dt, "2026-09-11", "2026-09-24"))),
        send=example_database.send,
    )
    newest_first = every_day.sort_values("dt", ascending=False, kind="stable")
    newest = newest_first.groupby("job_id").head(1)
    return newest[["job_id", "team", "owner", "dt"]].sort_values("job_id").reset_index(drop=True)
