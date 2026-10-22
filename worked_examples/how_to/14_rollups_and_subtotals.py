"""Rollups and subtotals

For: Intermediate

## Goal

Turn days of rows into one row per week, or per month, with `week_start` and `month_start`;
count the different jobs that ran each week without adding up each day's count; and count runs
for each team and job with, in the same result, each team's subtotal and the grand total, with
`GROUP_BY(rollup(...))`, labelling the subtotal rows with `is_total`.

## When you'd use it

- When a daily table is too fine to read, and the question is about weeks or months: runs per
  week, the different jobs seen each month, a week's total against the week before.
- For a report that shows the parts and their totals together: runs per job with each team's
  total, any table a spreadsheet would end with a "Total" row.

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

Then import the Toolbox, the `project` module, the Project's `ops` Database, its Alias
`ends_a_run`, and your query. `ops.job_events` holds what each job's runs did over 14 days,
2026-09-11 to 2026-09-24. Each run has one `"start"` row, so counting the `"start"` rows
counts the runs.

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from references import ops
>>> from references.ops__job_events import ends_a_run
>>> from warehouse import query
>>> job_events = ops.job_events  # -> Table

### Count each job's runs per week

`week_start(job_events.dt)` gives the Monday that starts each day's week, as text like
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
>>> run(starts_per_week, query=query)  # -> DataFrame
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

Pasted into your own notebook, this `run`, and each `run` of a week, a month or subtotals
below, stops with a RuntimeError saying the Example database can't run this Hive: the Example
database runs Hive with sqlglot, which has no NEXT_DAY or TRUNC, and makes no subtotals. The
results here were worked out in pandas from the same rows, to show what the Hive gives. Your
warehouse runs the Hive as it is, and Check it worked below runs on the Example database too.

The Hive works the Monday out from the day: DATE_ADD(job_events.dt, 7 * -1) adds -7 days, so
it is the day a week earlier, and NEXT_DAY(..., 'MO') is the first Monday after that. For
Thursday 2026-09-24, a week earlier is 2026-09-17, and the first Monday after it is
2026-09-21; for Monday 2026-09-14, a week earlier is 2026-09-07, and the first Monday after it
is 2026-09-14 itself. In `GROUP_BY`, Hive needs the calculation written out again, so the
Toolbox writes it for you; you give only the name.

The 14 days start on a Friday, so they fall in three weeks: Friday to Sunday of the week of
2026-09-07, all of the week of 2026-09-14, and Monday to Thursday of the week of 2026-09-21.

### Count each job's runs per month

`month_start` gives the first day of each day's month, and works the same way. All 14 days are
in September, so there is one month:

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
>>> run(starts_per_month, query=query)  # -> DataFrame
        month  job_id  starts
0  2026-09-01       1      14
1  2026-09-01       2      10
2  2026-09-01       3       4

### Count the different jobs that ran each week

A count of different values, `count_distinct`, counts each value once in its group. Count from
the rows themselves, grouped by week, so a job that ran on five days of a week counts once in
that week:

>>> jobs_per_week = statement(  # -> Statement
...     SELECT(AS(week_start(job_events.dt), "week"),
...            AS(count_distinct(job_events.job_id), "jobs_that_ran")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY("week"),
... )
>>> run(jobs_per_week, query=query)  # -> DataFrame
         week  jobs_that_ran
0  2026-09-07              3
1  2026-09-14              3
2  2026-09-21              3

Three different jobs ran in each week. The first mistake below shows the count that adds up
each day's count instead, and what the Toolbox says.

### Roll a Saved table's days up into weeks

A Saved table that holds a row per day can be rolled up the same way, reading its saved days
rather than counting them again. mart.team_days, a Saved table of the Project, holds each
team's day, and its notebook's logic cell defines `week_totals`, which adds its days up into
weeks; `project.load` gives it:

>>> team_days = project.load("mart.team_days")  # -> TableLogic
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

### Count per team and job, with subtotals

Which team owned a job changes from day to day, so the team comes from the Project's Building
block `owner_on_day`, which joins each event to its job's team that day, as [Look things up as
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
>>> run(runs_per_job, query=query)  # -> DataFrame
      team  job_id  runs  minutes
0      NaN    <NA>    14      206
1     data    <NA>     7       82
2     data       1     7       82
3  finance    <NA>     7      124
4  finance       2     5       79
5  finance       3     2       45

The Hive spells out each set of rows in `GROUPING SETS`: each team and job, each team, and
`()`, nothing, for one row over all of them. In a subtotal row the columns it totals over are
empty, NULL, which pandas shows as NaN in a column of text and as `<NA>` in a column of whole
numbers, and the tables on this page as NULL: the job in a team's subtotal, and the team too in
the grand total. report_build, job 3, counts for finance: its team from 2026-09-18 on.

### Tell a subtotal row from a real NULL

A column can be empty in a real row too. Nobody owns cache_warm, job 4, so its owner is NULL,
and a rollup of `job_owners.owner` over 2026-09-24's snapshot has two rows with NaN:

>>> jobs_per_owner = statement(  # -> Statement
...     SELECT(job_owners.owner, AS(if_else(is_total(job_owners.owner), 1, 0), "subtotal"),
...            AS(count_rows(), "jobs")),
...     FROM(job_owners),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
...     GROUP_BY(rollup(job_owners.owner)),
... )
>>> run(jobs_per_owner, query=query)  # -> DataFrame
   owner  subtotal  jobs
0    NaN         0     1
1    NaN         1     4
2    ana         0     1
3    ben         0     1
4  chloe         0     1

`is_total(job_owners.owner)` holds on a subtotal row that totals over every owner, and nowhere
else, so the first row is cache_warm, which nobody owns, and the second the grand total of all
four jobs.

### Label the subtotal rows

`if_else(is_total(...), ...)` puts a word of your own in place of the empty column. Its two
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
>>> run(labelled, query=query)  # -> DataFrame
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

### Keep only the subtotals

`is_total` in `HAVING` keeps or leaves out subtotal rows, since `HAVING` tests the rows
`GROUP_BY` made, subtotals included. Here only each team's total and the grand total. The
column it tests, `job_events.job_id`, must be in `SELECT` too: without it, a subtotal row
looks like the rows it totals, so the Toolbox refuses it.

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
>>> run(team_totals, query=query)  # -> DataFrame
      team  job_id  runs
0      NaN    <NA>    14
1     data    <NA>     7
2  finance    <NA>     7

### Other sets of subtotals

`rollup` drops its columns from the right, first the job, then the team: each team over its
jobs, never each job over its teams. For every mix, use `cube(job_owners.team,
job_owners.owner)`: each team over every owner, each owner over every team, and the grand
total. To pick the sets yourself, list them with `grouping_sets([job_owners.team],
[job_owners.owner], [])`. A plain column beside a rollup is in every set, so
`GROUP_BY(job_events.dt, rollup(job_owners.team))` totals each day's teams, and never adds days
together.

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
>>> per_day = run(starts_per_day, query=query)  # -> DataFrame
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
>>> run(runs_per_team, query=query)  # -> DataFrame
      team  runs
0     data     7
1  finance     7

7 and 7 are the team subtotals above, and they add up to the grand total, 14.

## Common mistakes

### Adding up each day's count of different jobs

Say a count of the different jobs on each day is already there. Adding up its days looks like
the quick way to a week, but a job that ran on five days is in five days' counts, so the week
would count it five times. The Toolbox refuses it as you build the Statement:

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
  What happened:  sum_of(jobs_per_day.jobs_that_ran) adds up jobs_per_day.jobs_that_ran, which is a distinct count.
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
  What happened:  SELECT has the calculation "week" (from job_events.dt), but the Statement counts or adds up rows and has no GROUP_BY.
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
>>> run(days_per_week, query=query)  # -> DataFrame
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

>>> int(run(runs_per_job, query=query)["runs"].sum())
42

Add up only the rows that aren't subtotals, or read the grand total's own row.

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
  What happened:  INSERT_OVERWRITE(job_events_checks) writes rows made by GROUP_BY(rollup(job_events.dt)).
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

Test it in `HAVING`, as Keep only the subtotals does.

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
    FROM, LEFT_JOIN, SELECT, WHERE, all_columns, all_of, between, equals, example_database,
    run, statement,
)

job_events = example_database.job_events
job_owners = example_database.job_owners

# The Example database can't run week_start, month_start or a rollup, so the page and the
# doctest get each such Statement's result from these, worked out in pandas from rows read
# with Statements it can run.


def every_event() -> pd.DataFrame:
    """Every event over the 14 days, each with its week and month, as week_start and
    month_start give them."""
    events = run(
        statement(SELECT(all_columns(job_events)), FROM(job_events),
                  WHERE(between(job_events.dt, "2026-09-11", "2026-09-24"))),
        query=example_database.query,
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


def week_events() -> pd.DataFrame:
    """Every event of the week from 2026-09-18, with its job's team that day, read with a
    Statement the Example database can run, and a 1 in "start" on a run's start, and its
    minutes in "ended" on the event that ends a run."""
    events = run(
        statement(SELECT(job_events.job_id, job_events.event_type, job_events.minutes,
                         job_owners.team),
                  FROM(job_events),
                  LEFT_JOIN(job_owners, ON=all_of(
                      equals(job_owners.job_id, job_events.job_id),
                      equals(job_owners.dt, job_events.dt),
                      between(job_owners.dt, "2026-09-18", "2026-09-24"))),
                  WHERE(between(job_events.dt, "2026-09-18", "2026-09-24"))),
        query=example_database.query,
    )
    ends = events.event_type.isin(["finish", "fail"])
    return events.assign(start=(events.event_type == "start").astype("int64"),
                         ended=events.minutes.where(ends))


def team_rollup() -> pd.DataFrame:
    """The rows of rollup(team, job_id) over the week: each team and job, each team, and the
    grand total, with the job, and then the team too, NULL in a subtotal row."""
    events = week_events()
    found = []
    for columns in (["team", "job_id"], ["team"], []):
        grouped = (events.assign(every=0).groupby(columns + ["every"], as_index=False)
                   .agg(runs=("start", "sum"), minutes=("ended", "sum")))
        found.append(grouped.drop(columns="every"))
    rows = pd.concat(found, ignore_index=True)
    rows["team"] = rows["team"].astype("str")
    rows["job_id"] = rows["job_id"].astype("Int64")
    rows["minutes"] = rows["minutes"].astype("int64")
    return rows[["team", "job_id", "runs", "minutes"]]


def _sorted(frame: pd.DataFrame) -> pd.DataFrame:
    """The rows as the Example database gives them: sorted by every column, NULL first."""
    keys = [frame[column].map(lambda value: (not pd.isna(value), value))
            for column in frame.columns]
    order = sorted(range(len(frame)), key=lambda i: tuple(key.iloc[i] for key in keys))
    return frame.iloc[order].reset_index(drop=True)


def runs_per_job_in_pandas() -> pd.DataFrame:
    """runs_per_job's result, computed in pandas, not by running this Hive."""
    return _sorted(team_rollup())


def team_totals_in_pandas() -> pd.DataFrame:
    """team_totals' result, computed in pandas, not by running this Hive."""
    found = runs_per_job_in_pandas()
    return found[found["job_id"].isna()][["team", "job_id", "runs"]].reset_index(drop=True)


def labelled_in_pandas() -> pd.DataFrame:
    """labelled's result, computed in pandas, not by running this Hive."""
    found = runs_per_job_in_pandas()
    team = found["team"].where(found["team"].notna(), "every team")
    job = found["job_id"].astype("str").where(found["job_id"].notna(), "every job")
    labelled = pd.DataFrame({"team": team, "job": job, "runs": found["runs"]})
    return _sorted(labelled)


def jobs_per_owner_in_pandas() -> pd.DataFrame:
    """jobs_per_owner's result, computed in pandas, not by running this Hive."""
    owners = run(statement(SELECT(job_owners.owner), FROM(job_owners),
                           WHERE(equals(job_owners.dt, "2026-09-24"))),
                 query=example_database.query)
    each = (owners.assign(every=0).groupby(["owner", "every"], dropna=False, as_index=False)
            .size().rename(columns={"size": "jobs"}).drop(columns="every"))
    each["subtotal"] = 0
    total = pd.DataFrame({"owner": [None], "subtotal": [1], "jobs": [len(owners)]})
    rows = pd.concat([each, total], ignore_index=True)
    rows["owner"] = rows["owner"].astype("str")
    return _sorted(rows[["owner", "subtotal", "jobs"]])
