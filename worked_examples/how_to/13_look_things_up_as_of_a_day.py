"""Look things up as of a day

For: Intermediate

## Goal

Find what was true on each day from a table that keeps a full copy of itself every day, a daily
snapshot: here, the team each job belonged to on the day it ran. You join on the day as well
as the job, count each team's runs as they were owned at the time, keep that join in a
Building block, and pick each job's newest row with `row_number`.

## When you'd use it

When a table holds one row per thing per day, such as each job's owner, each product's price
or each customer's plan, and another table's rows need the value from their own day, not
today's. A job that changed teams last week should count for its old team before the change
and its new team after it.

It needs the Getting started how-tos [Count, join and stay safe](#count_join_and_stay_safe)
and [Share Building blocks](#share_building_blocks).

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

Then import the Toolbox, the Project's `ops` Database and your query. `ops.job_events` holds
what each job's runs did over 14 days, 2026-09-11 to 2026-09-24: a `"start"` row when a run
starts, then `"finish"`, `"retry"` or `"fail"`. `ops.job_owners` is the snapshot: every job's
team and owner, once per day.

>>> from sqlglot_composer import *
>>> from references import ops
>>> from warehouse import query, execute
>>> job_events = ops.job_events  # -> Table
>>> job_owners = ops.job_owners  # -> Table

### Look at the snapshot

Each day holds one row per job, so its Key is the job and the day together: job_id and dt,
which its Table reference, references/ops__job_owners.py, says. Job 3, report_build, moved
from the data team to finance on 2026-09-18:

>>> report_build_owners = statement(  # -> Statement
...     SELECT(job_owners.dt, job_owners.team, job_owners.owner),
...     FROM(job_owners),
...     WHERE(equals(job_owners.job_id, 3),
...           between(job_owners.dt, "2026-09-16", "2026-09-19")),
... )
>>> run_query(report_build_owners, query)  # -> DataFrame
           dt     team  owner
0  2026-09-16     data    ana
1  2026-09-17     data    ana
2  2026-09-18  finance  chloe
3  2026-09-19  finance  chloe

### Join each run to its own day's row

A run is a `"start"` row of job_events. Join the snapshot on both parts of its Key: the same
job, and the same day. Each run then meets exactly one row, its job's row on the day it ran.

The snapshot is partitioned by dt too, so it needs its own filter on dt, in `WHERE` or in
`ON=`: the Toolbox checks each table's partition columns separately, and
`equals(job_owners.dt, job_events.dt)` in `ON=` matches the two tables' days without saying
which days to read.

>>> report_build_runs = statement(  # -> Statement
...     SELECT(job_events.dt, job_owners.team),
...     FROM(job_events),
...     JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_events.job_id),
...                                equals(job_owners.dt, job_events.dt))),
...     WHERE(equals(job_events.job_id, 3),
...           equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24"),
...           between(job_owners.dt, "2026-09-11", "2026-09-24")),
... )
>>> text = show_hive(report_build_runs)  # -> str
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
>>> run_query(report_build_runs, query)  # -> DataFrame
           dt     team
0  2026-09-11     data
1  2026-09-14     data
2  2026-09-18  finance
3  2026-09-21  finance

report_build ran four times: twice for data, then twice for finance.

### Count each team's runs as of their day

The same join, for every job, grouped by team:

>>> runs_per_team = statement(  # -> Statement
...     SELECT(job_owners.team, AS(count_rows(), "runs")),
...     FROM(job_events),
...     JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_events.job_id),
...                                equals(job_owners.dt, job_events.dt))),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24"),
...           between(job_owners.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_owners.team),
... )
>>> run_query(runs_per_team, query)  # -> DataFrame
      team  runs
0     data    16
1  finance    12

data has nightly_load's (job 1) 14 runs and report_build's (job 3) 2 before the move; finance
has invoice_sync's (job 2) 10 and report_build's 2 after it.

### Keep the lookup in a Building block

Every Statement of the Project that needs a job's team on a day makes the same join, so the
Project keeps it once, in the Building block building_blocks/owner_on_day.py:

    from sqlglot_composer import LEFT_JOIN, Clause, Column, all_of, between, equals
    from references.ops__job_owners import job_owners


    def owner_on_day(job_id_column: Column, day_column: Column, first_day: str,
                     last_day: str) -> Clause:
        return LEFT_JOIN(
            job_owners,
            ON=all_of(equals(job_owners.job_id, job_id_column),
                      equals(job_owners.dt, day_column),
                      between(job_owners.dt, first_day, last_day)),
        )

It filters the snapshot's days in `ON=`, and it is a `LEFT_JOIN`, so a run whose day has no
snapshot yet keeps its row, with a NULL team, rather than being dropped. A Statement calls it
where a JOIN goes:

>>> from building_blocks.owner_on_day import owner_on_day
>>> runs_per_team_then = statement(  # -> Statement
...     SELECT(job_owners.team, AS(count_rows(), "runs")),
...     FROM(job_events),
...     owner_on_day(job_events.job_id, job_events.dt, first_day="2026-09-11",
...                  last_day="2026-09-24"),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_owners.team),
... )
>>> run_query(runs_per_team_then, query)  # -> DataFrame
      team  runs
0     data    16
1  finance    12

The same counts: every run of the 14 days has a snapshot. mart.job_day_facts, a Saved table of
the Project, saves each job's day beside its team through this Building block, as [Rewrite some
partitions](#rewrite_some_partitions) shows.

### Pick each job's newest row

To know who owns each job now, take each job's newest row of the snapshot. `row_number` numbers
each job's rows from the newest day down; the Statement that reads them keeps number 1. Its
`PARTITION_BY=` is SQL's word for the groups to number within, here each job, not the table's
Partitions. Hive can't keep a row by its number in the same SELECT that numbers it, so the
numbering goes in a Derived table, which the Hive writes at its top as
`WITH numbered AS (...)`. [The latest row of each group](#latest_row_of_each_group) starts with it:

>>> numbered = derived("numbered", statement(  # -> Table
...     SELECT(job_owners.job_id, job_owners.team, job_owners.owner, job_owners.dt,
...            AS(row_number(PARTITION_BY=job_owners.job_id,
...                          ORDER_BY=descending(job_owners.dt)), "newest_first")),
...     FROM(job_owners),
...     WHERE(between(job_owners.dt, "2026-09-11", "2026-09-24")),
... ))
>>> newest_owner = statement(  # -> Statement
...     SELECT(numbered.job_id, numbered.team, numbered.owner, numbered.dt),
...     FROM(numbered),
...     WHERE(equals(numbered.newest_first, 1)),
... )
>>> text = show_hive(newest_owner)  # -> str
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
>>> run_query(newest_owner, query)  # -> DataFrame
   job_id     team  owner          dt
0       1     data    ana  2026-09-24
1       2  finance    ben  2026-09-24
2       3  finance  chloe  2026-09-24
3       4      web    NaN  2026-09-24

Pasted into your own notebook, this `run_query` stops with a RuntimeError saying the Example database
can't run this Hive: the Example database runs Hive with sqlglot, which has no `row_number`.
The result above was worked out in pandas from the same rows, to show what the Hive gives.
Your warehouse runs the Hive above as it is.

Here every job is in every day's copy, so each newest row is from 2026-09-24, and reading that
one day would give the same. At work a row can drop out of a snapshot, such as a job that was
deleted, and then `row_number` still finds its last row, from whichever day that was. Nobody
owns cache_warm (job 4), so its owner is NULL (pandas shows it as NaN).

## Check it worked

Each run should meet exactly one row of the snapshot, so the teams' runs add up to every run
over the 14 days:

>>> every_run = statement(  # -> Statement
...     SELECT(AS(count_rows(), "runs")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
... )
>>> run_query(every_run, query)  # -> DataFrame
   runs
0    28
>>> int(run_query(runs_per_team, query)["runs"].sum())
28

## Common mistakes

### Joining the snapshot on the job alone

Without the day in `ON=`, each run meets its job's row on every day of the snapshot. The
Toolbox warns at the `JOIN`, since a job_owners row is told apart only by the job and the day:

>>> runs_per_team_repeated = statement(  # -> Statement
...     SELECT(job_owners.team, AS(count_rows(), "runs")),
...     FROM(job_events),
...     JOIN(job_owners, ON=equals(job_owners.job_id, job_events.job_id)),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24"),
...           between(job_owners.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_owners.team),
... )
>>> run_query(runs_per_team_repeated, query)  # -> DataFrame
      team  runs
0     data   224
1  finance   168

Each run counted 14 times, once per day of the snapshot. The Warning's fix names the part of
the Key left out, the day: add `equals(job_owners.dt, job_events.dt)` to `ON=`, as
`report_build_runs` does.

### Taking every run's team from the newest day

No message stops you here. Joining every run to the snapshot of one day, the newest, gives
every run the team its job has now:

>>> runs_per_team_now = statement(  # -> Statement
...     SELECT(job_owners.team, AS(count_rows(), "runs")),
...     FROM(job_events),
...     JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_events.job_id),
...                                equals(job_owners.dt, "2026-09-24"))),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_owners.team),
... )
>>> run_query(runs_per_team_now, query)  # -> DataFrame
      team  runs
0     data    14
1  finance    14

The total is still 28, but report_build's two runs before 2026-09-18 count for finance, a team
that didn't own it then. Use one day's snapshot only for what you want as it is on that day.

### Leaving the snapshot's days unfiltered

The day in `ON=` matches the two tables' days, but it doesn't say which of job_owners' days to
read, so the Toolbox refuses as you build the Statement:

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
sqlglot_composer.refusals.LoadRefused:
  What happened:  JOIN(job_owners, ON=...) reads ops.job_owners, but filters none of its partition columns: dt.
...

Filter it with the same days as the table it is joined to, in `WHERE` as the steps do, or in
`ON=`, as `owner_on_day` does.

## Next

- Roll the days up into weeks and months: [Rollups and subtotals](#rollups_and_subtotals).
- Save each job's day beside its team then, and rewrite the last few days as rows come in late:
  [Rewrite some partitions](#rewrite_some_partitions).
- Each job's last row of a table, and the top N: [The latest row of each
  group](#latest_row_of_each_group).
- The gallery's [latest run per job](examples.html#latest_and_top_n), which shows why `max_of`
  on each column can mix values from different rows, and its Worked example of
  [`row_number`](examples.html#row_number).
"""

import pandas as pd

from sqlglot_composer import (
    FROM, SELECT, WHERE, all_columns, between, example_database, run_query, statement,
)

job_owners = example_database.job_owners


def newest_owner_in_pandas() -> pd.DataFrame:
    """newest_owner's result, computed in pandas, not by running this Hive."""
    every_day = run_query(
        statement(SELECT(all_columns(job_owners)), FROM(job_owners),
                  WHERE(between(job_owners.dt, "2026-09-11", "2026-09-24"))),
        example_database.query,
    )
    newest_first = every_day.sort_values("dt", ascending=False, kind="stable")
    newest = newest_first.groupby("job_id").head(1)
    newest = newest[["job_id", "team", "owner", "dt"]]
    return newest.sort_values("job_id").reset_index(drop=True)
