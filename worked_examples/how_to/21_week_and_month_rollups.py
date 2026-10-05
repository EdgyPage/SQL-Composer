"""Week and month rollups

For: Intermediate

## Goal

Turn 14 days of rows into one row per week, or per month: count each job's runs per week with
`week_start`, per month with `month_start`, and count the different jobs that ran each week
without adding up each day's count, which counts a job once per day it ran.

## When you'd use it

When a daily table is too fine to read, and the question is about weeks or months: runs per
week, the different users seen each month, a week's total against the week before.

## Steps

### Import the Toolbox

`ops.job_events` holds what each job's runs did over 14 days, 2026-09-11 to 2026-09-24. Each run
has one `"start"` row, so counting the `"start"` rows counts the runs.

>>> from sqlglot_composer import *
>>> job_events = example_database.job_events

### Count each job's runs per week

`week_start(job_events.dt)` gives the Monday that starts each day's week, as text like
`2026-09-14`. Name it in `SELECT` with `AS`, then group by that name in `GROUP_BY`, with any
other column you group by, as [Count and add up per group](#count_and_add_up_per_group) does with
plain columns:

>>> starts_per_week = statement(
...     SELECT(AS(week_start(job_events.dt), "week"), job_events.job_id,
...            AS(count_rows(), "starts")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY("week", job_events.job_id),
... )
>>> text = show_hive(starts_per_week)
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
>>> run(starts_per_week, send=example_database.send)
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

[sqlglot_composer only]
Pasted into your own notebook, this `run`, and each `run` of a week or a month below, stops with
a RuntimeError saying the Example database can't run this Hive: sqlglot Composer's Example
database runs Hive with sqlglot, which has no NEXT_DAY or TRUNC. The results here were worked
out in pandas from the same rows, to show what the Hive gives. Your warehouse runs the Hive as
it is, and Check it worked below runs on the Example database too.
[end]

The Hive works the Monday out from the day: DATE_ADD(job_events.dt, 7 * -1) adds -7 days, so it
is the day a week earlier, and NEXT_DAY(..., 'MO') is the first Monday after that. In
`GROUP_BY`, Hive needs the calculation written out again, so the Toolbox writes it for you; you
give only the name.

The 14 days start on a Friday, so they fall in three weeks: Friday to Sunday of the week of
2026-09-07, all of the week of 2026-09-14, and Monday to Thursday of the week of 2026-09-21.

### Count each job's runs per month

`month_start` gives the first day of each day's month, and works the same way. All 14 days are
in September, so there is one month:

>>> starts_per_month = statement(
...     SELECT(AS(month_start(job_events.dt), "month"), job_events.job_id,
...            AS(count_rows(), "starts")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY("month", job_events.job_id),
... )
>>> text = show_hive(starts_per_month)
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
>>> run(starts_per_month, send=example_database.send)
        month  job_id  starts
0  2026-09-01       1      14
1  2026-09-01       2      10
2  2026-09-01       3       4

### Count the different jobs that ran each week

A count of different values, `count_distinct`, counts each value once in its group. Count from
the rows themselves, grouped by week, so a job that ran on five days of a week counts once in
that week:

>>> jobs_per_week = statement(
...     SELECT(AS(week_start(job_events.dt), "week"),
...            AS(count_distinct(job_events.job_id), "jobs_that_ran")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY("week"),
... )
>>> run(jobs_per_week, send=example_database.send)
         week  jobs_that_ran
0  2026-09-07              3
1  2026-09-14              3
2  2026-09-21              3

Three different jobs ran in each week. The first mistake below shows the count that adds up
each day's count instead, and what the Toolbox says.

## Check it worked

Each week's runs are its days' runs added up, and the weeks' runs add up to the 28 runs over the
14 days. Check both from a count per day, which the Example database runs in either Edition, with
each day's Monday worked out in pandas: `days.dt.weekday` is 0 on a Monday and 6 on a Sunday, so
taking that many days off a day gives its Monday.

>>> import pandas as pd
>>> starts_per_day = statement(
...     SELECT(job_events.dt, AS(count_rows(), "starts")),
...     FROM(job_events),
...     WHERE(equals(job_events.event_type, "start"),
...           between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_events.dt),
... )
>>> per_day = run(starts_per_day, send=example_database.send)
>>> days = pd.to_datetime(per_day["dt"])
>>> per_day["week"] = (days - pd.to_timedelta(days.dt.weekday, unit="D")).dt.strftime("%Y-%m-%d")
>>> per_day.groupby("week")["starts"].sum()
week
2026-09-07     5
2026-09-14    14
2026-09-21     9
Name: starts, dtype: int64
>>> int(per_day["starts"].sum())
28

These are `starts_per_week`'s rows added up per week: 3 + 1 + 1, 7 + 5 + 2 and 4 + 4 + 1.

## Common mistakes

### Adding up each day's count of different jobs

Say a count of the different jobs on each day is already there. Adding up its days looks like
the quick way to a week, but a job that ran on five days is in five days' counts, so the week
would count it five times. The Toolbox refuses it as you build the Statement:

>>> jobs_per_day = derived("jobs_per_day", statement(
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
composer_core.refusals.GuardRefused:
  What happened:  sum_of(jobs_per_day.jobs_that_ran) adds up jobs_per_day.jobs_that_ran, which is a distinct count.
...

Count again from the rows, as `jobs_per_week` does. A plain count, such as runs, does add up:
a week's runs are its days' runs added together. The gallery's
[re-grouping Worked example](examples.html#regrouping) shows the wrong number the opt-out gives.

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
composer_core.refusals.GuardRefused:
  What happened:  SELECT has job_events.dt, but the Statement counts or adds up rows and has no GROUP_BY.
...

The message names job_events.dt, the column inside `week_start`, and its fix offers
`GROUP_BY(job_events.dt)`, which would give one row per day. To get one row per week, group by
the name you gave the week instead: `GROUP_BY("week")`.

### Reading weeks your days only partly cover

The days you read decide which days each week holds. Counting the days in each week shows it:

>>> days_per_week = statement(
...     SELECT(AS(week_start(job_events.dt), "week"),
...            AS(count_distinct(job_events.dt), "days")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY("week"),
... )
>>> run(days_per_week, send=example_database.send)
         week  days
0  2026-09-07     3
1  2026-09-14     7
2  2026-09-21     4

The first and last weeks hold 3 and 4 days, so their runs look low next to the middle week's,
though nothing ran less. To compare weeks, read whole weeks, from a Monday to a Sunday, such as
`between(job_events.dt, "2026-09-14", "2026-09-20")`; for months, from the 1st to the month's
last day.

## Next

- Save each day once, and roll it up into weeks from the Saved table:
  [A pipeline of Saved tables](#a_pipeline_of_saved_tables).
- Keep a Saved table's last few days up to date: [Incremental loads and late
  data](#incremental_loads_and_late_data).
- The gallery's Worked examples of [`week_start`](examples.html#week_start),
  [`month_start`](examples.html#month_start) and
  [`count_distinct`](examples.html#count_distinct).
"""

import pandas as pd

from sqlglot_composer import (
    FROM, SELECT, WHERE, all_columns, between, example_database, run, statement,
)

job_events = example_database.job_events


def every_event():
    """Every event over the 14 days, read with a Statement the Example database can run, each
    with its week and month, as week_start and month_start give them."""
    events = run(
        statement(SELECT(all_columns(job_events)), FROM(job_events),
                  WHERE(between(job_events.dt, "2026-09-11", "2026-09-24"))),
        send=example_database.send,
    )
    days = pd.to_datetime(events.dt)
    monday = days - pd.to_timedelta(days.dt.weekday, unit="D")
    return events.assign(week=monday.dt.strftime("%Y-%m-%d"),
                         month=days.dt.strftime("%Y-%m-01"))


def every_start():
    events = every_event()
    return events[events.event_type == "start"]


def starts_per_week_in_pandas():
    """starts_per_week's result, computed in pandas, not by running this Hive."""
    return every_start().groupby(["week", "job_id"], as_index=False).size().rename(
        columns={"size": "starts"})


def starts_per_month_in_pandas():
    """starts_per_month's result, computed in pandas, not by running this Hive."""
    return every_start().groupby(["month", "job_id"], as_index=False).size().rename(
        columns={"size": "starts"})


def jobs_per_week_in_pandas():
    """jobs_per_week's result, computed in pandas, not by running this Hive."""
    return every_start().groupby("week", as_index=False).job_id.nunique().rename(
        columns={"job_id": "jobs_that_ran"})


def days_per_week_in_pandas():
    """days_per_week's result, computed in pandas, not by running this Hive."""
    return every_event().groupby("week", as_index=False).dt.nunique().rename(
        columns={"dt": "days"})
