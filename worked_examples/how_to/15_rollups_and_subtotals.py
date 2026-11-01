"""Rollups and subtotals

For: Intermediate

## Goal

Turn days of rows into one row per week, or per month, with `week_start` and `month_start`;
count the different jobs that ran each week without adding up each day's count; and count runs
for each team and job with, in the same result, each team's subtotal and the grand total, with
`GROUP_BY(rollup(...))`, labelling the subtotal rows with `is_total`. A Subtotal row is a row
the grouping adds, totalling the rows of several groups, such as one per team over all its
jobs, or the grand total, one over every row.

## When you'd use it

- If a daily table is too fine to read and the question is about weeks or months, such as runs
  per week, the different jobs seen each month, or a week's total against the week before,
  group by `week_start` or `month_start` (steps 3 to 6).
- If a report shows the parts and their totals together, such as runs per job with each team's
  total, or any table a spreadsheet would end with a "Total" row, group with `rollup` (steps 7
  to 11).
- If you haven't done the Getting started how-tos
  [Count, join and stay safe](#count_join_and_stay_safe) and
  [Share Building blocks](#share_building_blocks), do them first.

## Steps

### 1. Copy the Intermediate Example project

Goal: a Project to work in, its Table references and Building blocks written. A Project is your
folder of scripts at work, in the Toolbox's fixed layout.

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

Done when the folder you work in holds `references/`, `building_blocks/` and `warehouse.py`.
Then step 2.

### 2. Import the Toolbox and the table

Goal: the table the steps count. Import the Toolbox, the `project` module, the Project's `ops`
Database, the named group of tables whose names start `ops.`, its Alias `ends_a_run`, a
condition its Table reference names, and your query. `ops.job_events` holds what each job's
runs did over 14 days, 2026-09-11 to 2026-09-24. Each run has one `"start"` row, so counting
the `"start"` rows counts the runs.

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from references import ops
>>> from references.ops__job_events import ends_a_run
>>> from warehouse import query, execute
>>> job_events = ops.job_events  # -> Table

Done when the imports run without an error. Then step 3.

### 3. Count each job's runs per week

Goal: one row per week and job. `week_start(job_events.dt)` gives the Monday that starts each
day's week, as text like
`2026-09-14`. Name it in `SELECT` with `AS`, then group by that name in `GROUP_BY`, with any
other column you group by:

>>> starts_per_week = statement(  # -> Statement
...     SELECT(AS(week_start(job_events.dt), "week"), job_events.job_id,
...            AS(count_rows(), "starts")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY("week", job_events.job_id),
... )
>>> text = show_hive(starts_per_week)  # -> str
SELECT
  CAST(NEXT_DAY(DATE_ADD(job_events.dt, 7 * -1), 'MO') AS STRING) AS week,
  job_events.job_id,
  COUNT(*) AS starts
FROM ops.job_events AS job_events
WHERE
  job_events.event_type = 'start'
  AND job_events.dt BETWEEN '2026-09-11' AND '2026-09-24'
GROUP BY
  CAST(NEXT_DAY(DATE_ADD(job_events.dt, 7 * -1), 'MO') AS STRING),
  job_events.job_id;
>>> run_query(starts_per_week, query)  # -> DataFrame
         week  job_id  starts
0  2026-09-07       1       3
1  2026-09-07       2       1
2  2026-09-07       3       1
3  2026-09-14       1       7
4  2026-09-14       2       5
5  2026-09-14       3       2
6  2026-09-21       1       4
7  2026-09-21       2       4
8  2026-09-21       3       1

Pasted into your own notebook, this `run_query`, and each `run_query` of a week or a month
below, stops with a RuntimeError saying the Example database can't run this Hive: the Example
database runs Hive with sqlglot, which has no NEXT_DAY or TRUNC. The week and month results
were worked out in pandas from the same rows, to show what the Hive gives. The subtotals below
run on the Example database as they are. Your warehouse runs the Hive as it is, and Check it
worked below runs on the Example database too.

The Hive works the Monday out from the day: DATE_ADD(job_events.dt, 7 * -1) adds -7 days, so
it is the day a week earlier, and NEXT_DAY(..., 'MO') is the first Monday after that. For
Thursday 2026-09-24, a week earlier is 2026-09-17, and the first Monday after it is
2026-09-21; for Monday 2026-09-14, a week earlier is 2026-09-07, and the first Monday after it
is 2026-09-14 itself. In `GROUP_BY`, Hive needs the calculation written out again, so the
Toolbox writes it for you; you give only the name.

The 14 days start on a Friday, so they fall in three weeks: Friday to Sunday of the week of
2026-09-07, all of the week of 2026-09-14, and Monday to Thursday of the week of 2026-09-21.

Done when the result holds the weeks of 2026-09-07, 2026-09-14 and 2026-09-21. Then step 4.

### 4. Count each job's runs per month

Goal: one row per month and job. `month_start` gives the first day of each day's month, and
works the same way. All 14 days are in September, so there is one month:

>>> starts_per_month = statement(  # -> Statement
...     SELECT(AS(month_start(job_events.dt), "month"), job_events.job_id,
...            AS(count_rows(), "starts")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY("month", job_events.job_id),
... )
>>> text = show_hive(starts_per_month)  # -> str
SELECT
  CAST(TRUNC(job_events.dt, 'MM') AS STRING) AS month,
  job_events.job_id,
  COUNT(*) AS starts
FROM ops.job_events AS job_events
WHERE
  job_events.event_type = 'start'
  AND job_events.dt BETWEEN '2026-09-11' AND '2026-09-24'
GROUP BY
  CAST(TRUNC(job_events.dt, 'MM') AS STRING),
  job_events.job_id;
>>> run_query(starts_per_month, query)  # -> DataFrame
        month  job_id  starts
0  2026-09-01       1      14
1  2026-09-01       2      10
2  2026-09-01       3       4

Done when every row's month is 2026-09-01. Then step 5.

### 5. Count the different jobs that ran each week

Goal: each job counted once per week. A count of different values, `count_distinct`, counts
each value once in its group. Count from the rows themselves, grouped by week, so a job that
ran on five days of a week counts once in that week:

>>> jobs_per_week = statement(  # -> Statement
...     SELECT(AS(week_start(job_events.dt), "week"),
...            AS(count_distinct(job_events.job_id), "jobs_that_ran")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY("week"),
... )
>>> run_query(jobs_per_week, query)  # -> DataFrame
         week  jobs_that_ran
0  2026-09-07              3
1  2026-09-14              3
2  2026-09-21              3

Three different jobs ran in each week. The first mistake below shows the count that adds up
each day's count instead, and what the Toolbox says.

Done when each week shows 3 jobs that ran. Then step 6.

### 6. Roll a Saved table's days up into weeks

Goal: weeks read from days already saved. A Saved table is a real table in the warehouse that
your own Statements write. One that holds a row per day can be rolled up the same way, reading
its saved days rather than counting them again. mart.team_days, a Saved table of the Project,
holds each team's day, and its notebook's logic cell defines `week_totals`, which adds its days
up into weeks; `project.load` gives it:

>>> team_days = project.load("mart.team_days")  # -> the notebook's functions
>>> week_totals = team_days.week_totals("2026-09-14", "2026-09-20")  # -> Statement
>>> text = show_hive(week_totals)  # -> str
SELECT
  CAST(NEXT_DAY(DATE_ADD(team_days.dt, 7 * -1), 'MO') AS STRING) AS week,
  team_days.team,
  SUM(team_days.events) AS events,
  SUM(team_days.runs) AS runs,
  SUM(team_days.minutes) AS minutes,
  SUM(team_days.cost_cents) AS cost_cents
FROM mart.team_days AS team_days
WHERE
  team_days.dt BETWEEN '2026-09-14' AND '2026-09-20'
GROUP BY
  CAST(NEXT_DAY(DATE_ADD(team_days.dt, 7 * -1), 'MO') AS STRING),
  team_days.team;

Events, runs, minutes and costs add up, so a week's are its days' added together. A count of
different values doesn't, as the first mistake shows.

Done when the Hive reads `mart.team_days` and groups by its week and team. Then step 7.

### 7. Count per team and job, with subtotals

Goal: each team's jobs, each team's subtotal and the grand total, in one result. Which team
owned a job changes from day to day, so the team comes from the Project's Building block
`owner_on_day`, a piece of the Project's code reused across notebooks, which joins each event
to its job's team that day, as [Look things up as
of a day](#look_things_up_as_of_a_day) shows. `rollup(job_owners.team, job_events.job_id)` in
`GROUP_BY` groups by both, as `GROUP_BY(job_owners.team, job_events.job_id)` does, then adds a
subtotal row for each team, over all its jobs, and one for every row, the grand total:

>>> from building_blocks.owner_on_day import owner_on_day
>>> job_owners = ops.job_owners  # -> Table
>>> runs_per_job = statement(  # -> Statement
...     SELECT(job_owners.team, job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "runs"),
...            AS(sum_of(job_events.minutes, where=ends_a_run), "minutes")),
...     FROM(job_events),
...     owner_on_day(job_events.job_id, job_events.dt, first_day="2026-09-18",
...                  last_day="2026-09-24"),
...     WHERE(between(job_events.dt, "2026-09-18", "2026-09-24")),
...     GROUP_BY(rollup(job_owners.team, job_events.job_id)),
... )
>>> text = show_hive(runs_per_job)  # -> str
SELECT
  job_owners.team,
  job_events.job_id,
  COUNT(CASE WHEN job_events.event_type = 'start' THEN 1 END) AS runs,
  SUM(
    CASE WHEN job_events.event_type IN ('finish', 'fail') THEN job_events.minutes END
  ) AS minutes
FROM ops.job_events AS job_events
LEFT JOIN ops.job_owners AS job_owners
  ON job_owners.job_id = job_events.job_id
  AND job_owners.dt = job_events.dt
  AND job_owners.dt BETWEEN '2026-09-18' AND '2026-09-24'
WHERE
  job_events.dt BETWEEN '2026-09-18' AND '2026-09-24'
GROUP BY
  job_owners.team,
  job_events.job_id
  GROUPING SETS (
    (job_owners.team, job_events.job_id),
    job_owners.team,
    ()
  );
>>> run_query(runs_per_job, query)  # -> DataFrame
      team  job_id  runs  minutes
0      NaN     NaN    14      206
1     data     NaN     7       82
2     data     1.0     7       82
3  finance     NaN     7      124
4  finance     2.0     5       79
5  finance     3.0     2       45

The Hive spells out each set of rows in `GROUPING SETS`: each team and job, each team, and
`()`, nothing, for one row over all of them. In a subtotal row the columns it totals over are
empty, NULL, which pandas shows as NaN: the job in a team's subtotal, and the team too in
the grand total. report_build, job 3, counts for finance: its team from 2026-09-18 on.

pandas keeps NaN only among fractions, so a column of whole numbers with a NaN in it shows its
numbers as 1.0, 2.0 and so on: job_id here. A column that is NULL in every row has no numbers
to go by, so pandas shows each NULL as None, as in step 10's job_id.

Done when the result holds one row per team and job, one per team, and the grand total, 14
runs. Then step 8.

### 8. Tell a subtotal row from a real NULL

Goal: know which empty value is a subtotal. A column can be empty in a real row too. Nobody
owns cache_warm, job 4, so its owner is NULL, and a rollup of `job_owners.owner` over
2026-09-24's snapshot has two rows with NaN:

>>> jobs_per_owner = statement(  # -> Statement
...     SELECT(job_owners.owner, AS(if_else(is_total(job_owners.owner), 1, 0), "subtotal"),
...            AS(count_rows(), "jobs")),
...     FROM(job_owners),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
...     GROUP_BY(rollup(job_owners.owner)),
... )
>>> run_query(jobs_per_owner, query)  # -> DataFrame
   owner  subtotal  jobs
0    NaN         0     1
1    NaN         1     4
2    ana         0     1
3    ben         0     1
4  chloe         0     1

`is_total(job_owners.owner)` holds on a subtotal row that totals over every owner, and nowhere
else, so the first row is cache_warm, which nobody owns, and the second the grand total of all
four jobs.

Done when the subtotal column is 1 on the grand total's row alone. Then step 9.

### 9. Label the subtotal rows

Goal: a word of your own on each subtotal row. `if_else(is_total(...), ...)` puts a word in
place of the empty column. Its two
answers should be of one type, so the job's number is written as text first, with Hive's
string function: `hive_function("string", job_events.job_id)`, which the Hive writes as
`CAST(job_events.job_id AS STRING)`:

>>> labelled = statement(  # -> Statement
...     SELECT(AS(if_else(is_total(job_owners.team), "every team", job_owners.team), "team"),
...            AS(if_else(is_total(job_events.job_id), "every job",
...                       hive_function("string", job_events.job_id)), "job"),
...            AS(count_rows(where=equals(job_events.event_type, "start")), "runs")),
...     FROM(job_events),
...     owner_on_day(job_events.job_id, job_events.dt, first_day="2026-09-18",
...                  last_day="2026-09-24"),
...     WHERE(between(job_events.dt, "2026-09-18", "2026-09-24")),
...     GROUP_BY(rollup(job_owners.team, job_events.job_id)),
... )
>>> run_query(labelled, query)  # -> DataFrame
         team        job  runs
0        data          1     7
1        data  every job     7
2  every team  every job    14
3     finance          2     5
4     finance          3     2
5     finance  every job     7

The rows come sorted by their first column, as the Example database sorts them, which puts
"every team" between "data" and "finance". At work rows come in no fixed order: sort them with
`ORDER_BY`, or in pandas.

Done when the subtotal rows say "every job" and "every team". Then step 10.

### 10. Keep only the subtotals

Goal: each team's total and the grand total, and no other row. `is_total` in `HAVING` keeps or
leaves out subtotal rows, since `HAVING` tests the rows `GROUP_BY` made, subtotals included.
Put the column it tests, `job_events.job_id`, in `SELECT` too: without it, a subtotal row looks
like the rows it totals, so the Toolbox refuses it.

>>> team_totals = statement(  # -> Statement
...     SELECT(job_owners.team, job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "runs")),
...     FROM(job_events),
...     owner_on_day(job_events.job_id, job_events.dt, first_day="2026-09-18",
...                  last_day="2026-09-24"),
...     WHERE(between(job_events.dt, "2026-09-18", "2026-09-24")),
...     GROUP_BY(rollup(job_owners.team, job_events.job_id)),
...     HAVING(is_total(job_events.job_id)),
... )
>>> run_query(team_totals, query)  # -> DataFrame
      team job_id  runs
0      NaN   None    14
1     data   None     7
2  finance   None     7

Done when the result holds three rows: data's, finance's and the grand total. Then step 11.

### 11. Choose other sets of subtotals

Goal: the subtotals your report needs, when a rollup's aren't them. `rollup` drops its columns
from the right, first the job, then the team: each team over its jobs, never each job over its
teams.

- If you want every mix, write `cube(job_owners.team, job_owners.owner)`: each team over every
  owner, each owner over every team, and the grand total.
- If you want to pick the sets yourself, list them with `grouping_sets([job_owners.team],
  [job_owners.owner], [])`.
- If you want a total within each value of a column, put that plain column beside the rollup:
  it is in every set, so `GROUP_BY(job_events.dt, rollup(job_owners.team))` totals each day's
  teams, and never adds days together.

Done when your `GROUP_BY` names the sets of subtotal rows you want. Then check it worked, below.

## Check it worked

Each week's runs are its days' runs added up, and the weeks' runs add up to the 28 runs over
the 14 days. Check both from a count per day, which the Example database runs, with each day's
Monday worked out in pandas: `days.dt.weekday` is 0 on a Monday and 6 on a Sunday, so taking
that many days off a day gives its Monday.

>>> import pandas as pd
>>> starts_per_day = statement(  # -> Statement
...     SELECT(job_events.dt, AS(count_rows(), "starts")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_events.dt),
... )
>>> per_day = run_query(starts_per_day, query)  # -> DataFrame
>>> days = pd.to_datetime(per_day["dt"])
>>> per_day["week"] = (days - pd.to_timedelta(days.dt.weekday, unit="D")).dt.strftime(
...     "%Y-%m-%d")
>>> per_day.groupby("week")["starts"].sum()
week
2026-09-07     5
2026-09-14    14
2026-09-21     9
Name: starts, dtype: int64
>>> int(per_day["starts"].sum())
28

These are `starts_per_week`'s rows added up per week: 3 + 1 + 1, 7 + 5 + 2 and 4 + 4 + 1.

And each team's subtotal is its jobs' runs added up. A plain `GROUP_BY`, which the Example
database runs, counts the same:

>>> runs_per_team = statement(  # -> Statement
...     SELECT(job_owners.team,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "runs")),
...     FROM(job_events),
...     owner_on_day(job_events.job_id, job_events.dt, first_day="2026-09-18",
...                  last_day="2026-09-24"),
...     WHERE(between(job_events.dt, "2026-09-18", "2026-09-24")),
...     GROUP_BY(job_owners.team),
... )
>>> run_query(runs_per_team, query)  # -> DataFrame
      team  runs
0     data     7
1  finance     7

7 and 7 are the team subtotals above, and they add up to the grand total, 14.

Before you go on, check that:

- the weeks' starts worked out from the days, 5, 14 and 9, are `starts_per_week`'s rows added
  up per week, and add up to 28;
- `runs_per_team` gives data 7 and finance 7, the team subtotals of `runs_per_job`;
- those subtotals add up to the grand total, 14.

## Common mistakes

### Adding up each day's count of different jobs

Say a count of the different jobs on each day is already there. Adding up its days looks like
the quick way to a week, but a job that ran on five days is in five days' counts, so the week
would count it five times. The Toolbox refuses it as you build the Statement, with a Guard, a
check that refuses a Statement that would give a wrong result:

>>> jobs_per_day = derived("jobs_per_day", statement(  # -> Table
...     SELECT(job_events.dt, AS(count_distinct(job_events.job_id), "jobs_that_ran")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_events.dt),
... ))
>>> statement(
...     SELECT(AS(week_start(jobs_per_day.dt), "week"),
...            AS(sum_of(jobs_per_day.jobs_that_ran), "jobs_that_ran")),
...     FROM(jobs_per_day),
...     GROUP_BY("week"),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  sum_of(jobs_per_day.jobs_that_ran) adds up jobs_per_day.jobs_that_ran, which
                  is a distinct count.
...

Count again from the rows, as `jobs_per_week` does. A plain count, such as runs, does add up:
a week's runs are its days' runs added together. The gallery's
[re-grouping Worked example](examples.html#regrouping) shows the wrong number the opt-out
gives.

### Leaving the week out of GROUP_BY

Without `GROUP_BY`, the Statement has no groups for the count to count in:

>>> statement(
...     SELECT(AS(week_start(job_events.dt), "week"), AS(count_rows(), "starts")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  SELECT has the calculation "week" (from job_events.dt), but the Statement
                  counts or adds up rows and has no GROUP_BY.
...

Its fix groups by the name you gave the week, `GROUP_BY("week")`: one row per week.
`GROUP_BY(job_events.dt)`, the column inside `week_start`, would give one row per day instead.

### Reading weeks your days only partly cover

The days you read decide which days each week holds. Counting the days in each week shows it:

>>> days_per_week = statement(  # -> Statement
...     SELECT(AS(week_start(job_events.dt), "week"),
...            AS(count_distinct(job_events.dt), "days")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY("week"),
... )
>>> run_query(days_per_week, query)  # -> DataFrame
         week  days
0  2026-09-07     3
1  2026-09-14     7
2  2026-09-21     4

The first and last weeks hold 3 and 4 days, so their runs look low next to the middle week's,
though nothing ran less. To compare weeks, read whole weeks, from a Monday to a Sunday, as
`week_totals` above does; for months, from the 1st to the month's last day.

### Adding up a column of subtotals

Each run is counted in its job's row, its team's subtotal and the grand total, so adding up the
whole `"runs"` column in pandas counts every run three times:

>>> int(run_query(runs_per_job, query)["runs"].sum())
42

Add up only the rows `is_total` says are real rows, or read the grand total's own row.

### Writing subtotals into a Saved table

A Saved table holds one row for each Key, and subtotal rows repeat the rows they total: a sum
over the table would count each row twice. mart.job_events_checks, a Saved table of the
Project, holds the row count of each day of `ops.job_events`; a write that adds a grand total
row to it is refused:

>>> from references import mart
>>> statement(
...     INSERT_OVERWRITE(mart.job_events_checks),
...     SELECT(AS(count_rows(), "row_count"), job_events.dt),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-18", "2026-09-24")),
...     GROUP_BY(rollup(job_events.dt)),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  INSERT_OVERWRITE(job_events_checks) writes rows made by
                  GROUP_BY(rollup(job_events.dt)).
...

Write the plain `GROUP_BY(job_events.dt)`, as the table's notebook does, and add the subtotals
in the Statement that reads the Saved table.

### is_total in WHERE

`WHERE` picks the rows before `GROUP_BY` makes any subtotal, so there is none to test there:

>>> statement(
...     SELECT(job_owners.team, AS(count_rows(), "jobs")),
...     FROM(job_owners),
...     WHERE(equals(job_owners.dt, "2026-09-24"), is_total(job_owners.team)),
...     GROUP_BY(rollup(job_owners.team)),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  WHERE has is_total(job_owners.team).
...

Test it in `HAVING`, as `team_totals` does.

## Next

- Save each day once, and rewrite the last few as rows come in late, so the weeks read from
  saved days: [Rewrite some partitions](#rewrite_some_partitions).
- Count, join and add up per group, without subtotals:
  [Count, join and stay safe](#count_join_and_stay_safe).
- The gallery's Worked examples of [`week_start`](examples.html#week_start),
  [`month_start`](examples.html#month_start), [`count_distinct`](examples.html#count_distinct),
  [`rollup`](examples.html#rollup), [`cube`](examples.html#cube),
  [`grouping_sets`](examples.html#grouping_sets) and [`is_total`](examples.html#is_total).
"""

import pandas as pd

from sqlglot_composer import (
    FROM, SELECT, WHERE, all_columns, between, example_database, run_query, statement,
)

job_events = example_database.job_events
job_owners = example_database.job_owners

# The Example database can't run week_start or month_start, so the page and the doctest
# get each such Statement's result from these, worked out in pandas from rows read with
# Statements it can run.


def every_event() -> pd.DataFrame:
    """Every event over the 14 days, each with its week and month, as week_start and
    month_start give them."""
    events = run_query(
        statement(SELECT(all_columns(job_events)), FROM(job_events),
                  WHERE(between(job_events.dt, "2026-09-11", "2026-09-24"))),
        example_database.query,
    )
    days = pd.to_datetime(events.dt)
    monday = days - pd.to_timedelta(days.dt.weekday, unit="D")
    return events.assign(week=monday.dt.strftime("%Y-%m-%d"),
                         month=days.dt.strftime("%Y-%m-01"))


def every_start() -> pd.DataFrame:
    events = every_event()
    return events[events.event_type == "start"]


def starts_per_week_in_pandas() -> pd.DataFrame:
    """starts_per_week's result, computed in pandas, not by running this Hive."""
    return every_start().groupby(["week", "job_id"], as_index=False).size().rename(
        columns={"size": "starts"})


def starts_per_month_in_pandas() -> pd.DataFrame:
    """starts_per_month's result, computed in pandas, not by running this Hive."""
    return every_start().groupby(["month", "job_id"], as_index=False).size().rename(
        columns={"size": "starts"})


def jobs_per_week_in_pandas() -> pd.DataFrame:
    """jobs_per_week's result, computed in pandas, not by running this Hive."""
    return every_start().groupby("week", as_index=False).job_id.nunique().rename(
        columns={"job_id": "jobs_that_ran"})


def days_per_week_in_pandas() -> pd.DataFrame:
    """days_per_week's result, computed in pandas, not by running this Hive."""
    return every_event().groupby("week", as_index=False).dt.nunique().rename(
        columns={"dt": "days"})
