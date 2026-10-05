"""Run a daily pipeline

For: Getting started

## Goal

Write a day of several Saved tables with one call, in an order that is always right: every
table is written before the Statements that read it. You put each step in a function of the
day, list the day's steps in order, print their Hive to check them, run the list, and re-run a
day safely when something went wrong.

## When you'd use it

When one Saved table is read by another. Here mart.daily_job_runs counts each job's runs per
day, from `ops.job_runs`, and mart.team_day adds those counts up per team, reading
mart.daily_job_runs and `ops.jobs`. Every morning, yesterday's day of both is written: the job
counts first, then the team counts, which read them.

The Example database can be read but not written to, so this page prints each step's Hive,
and runs the list with a stand-in send that only shows what it would send.

## Steps

### Import the Toolbox and describe the two Saved tables

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs
>>> jobs = example_database.jobs
>>> daily_job_runs = Table(
...     "mart.daily_job_runs",
...     columns={"job_id": "bigint", "runs": "bigint", "failed_runs": "bigint",
...              "dt": "string"},
...     date_partition="dt",
...     key=["job_id", "dt"],
... )
>>> team_day = Table(
...     "mart.team_day",
...     columns={"team": "string", "runs": "bigint", "failed_runs": "bigint", "dt": "string"},
...     date_partition="dt",
...     key=["team", "dt"],
... )

### Write each step as a function of the day

Each step takes the day it writes, so the same lines write any day: yesterday's every
morning, or a day from last week when it has to be written again.

>>> def write_job_day(day):
...     return statement(
...         INSERT_OVERWRITE(daily_job_runs),
...         SELECT(
...             job_runs.job_id,
...             AS(count_rows(), "runs"),
...             AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...         ),
...         FROM(job_runs),
...         WHERE(equals(job_runs.dt, day)),
...         GROUP_BY(job_runs.job_id),
...     )

It writes one day, bounded with `equals`, so it needn't group by the day: only a range cut
with `by_day` must, as [Backfill a range of days](#backfill_a_range_of_days) shows.

The team step reads the Saved table the job step writes, through its Table reference, like
any other table, and reads the same day of it:

>>> def write_team_day(day):
...     return statement(
...         INSERT_OVERWRITE(team_day),
...         SELECT(
...             jobs.team,
...             AS(sum_of(daily_job_runs.runs), "runs"),
...             AS(sum_of(daily_job_runs.failed_runs), "failed_runs"),
...         ),
...         FROM(daily_job_runs),
...         JOIN(jobs, ON=equals(jobs.job_id, daily_job_runs.job_id)),
...         WHERE(equals(daily_job_runs.dt, day)),
...         GROUP_BY(jobs.team),
...     )

Adding up the job counts per team is safe: a sum of counts is the count of all of them.

### List the day's steps in order

One function gives the day's steps as a list, in the order they are sent:

>>> def day_steps(day):
...     return [
...         create_table(daily_job_runs, may_exist=True),
...         create_table(team_day, may_exist=True),
...         write_job_day(day),  # writes mart.daily_job_runs
...         write_team_day(day),  # reads mart.daily_job_runs: after the step that writes it
...     ]

Two things decide the order:

- Creating comes first. With `may_exist=True`, a table that is already there is skipped, so
  the create steps can stay in the list every day, and a new Saved table needs no separate
  step.
- A step that writes a table comes before every step that reads it. Here the team step reads
  what the job step writes, so it comes after it. Swapped, the team step would read the job
  counts before they were written: an empty day the first time, the day as it was before
  every time after, and nothing would stop to say so.

### Print the day's Hive

`show_hive` takes the list, and prints every step in order, each headed by its place in it:

>>> steps = day_steps("2026-09-24")
>>> text = show_hive(steps)
-- 1 of 4: steps[0]
CREATE TABLE IF NOT EXISTS mart.daily_job_runs (
  job_id BIGINT,
  runs BIGINT,
  failed_runs BIGINT
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC;
<BLANKLINE>
-- 2 of 4: steps[1]
CREATE TABLE IF NOT EXISTS mart.team_day (
  team STRING,
  runs BIGINT,
  failed_runs BIGINT
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC;
<BLANKLINE>
-- 3 of 4: steps[2]
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-24')
SELECT
  job_runs.job_id,
  COUNT(*) AS runs,
  COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24'
GROUP BY
  job_runs.job_id;
<BLANKLINE>
-- 4 of 4: steps[3]
INSERT OVERWRITE TABLE mart.team_day PARTITION(dt = '2026-09-24')
SELECT
  jobs.team,
  SUM(daily_job_runs.runs) AS runs,
  SUM(daily_job_runs.failed_runs) AS failed_runs
FROM mart.daily_job_runs AS daily_job_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = daily_job_runs.job_id
WHERE
  daily_job_runs.dt = '2026-09-24'
GROUP BY
  jobs.team;

Pasted into Hue or spark-sql, this runs the whole day by hand, in the same order.

### Run the list

`run` sends one Statement, so a short function sends the day's steps one after another, with
whichever send it is given:

>>> def run_day(day, send):
...     for step in day_steps(day):
...         run(step, send=send)

Here no warehouse can be written to, so a stand-in send shows what `run_day` sends: it prints
the first line of each step's Hive and gives back an empty DataFrame, as a send usually does
for a write.

>>> import pandas as pd
>>> def print_first_line(hive):
...     print(hive.splitlines()[0])
...     return pd.DataFrame()
>>> run_day("2026-09-24", send=print_first_line)
CREATE TABLE IF NOT EXISTS mart.daily_job_runs (
CREATE TABLE IF NOT EXISTS mart.team_day (
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-24')
INSERT OVERWRITE TABLE mart.team_day PARTITION(dt = '2026-09-24')

At work it is the same call with your own send. If a step fails, `run` stops there with the
warehouse's message, and the steps after it aren't sent, so a team day is never written from
job counts that weren't.

### Run it every morning

The day to write each morning is yesterday's, worked out from today's date:

>>> import datetime
>>> def run_yesterday(send):
...     yesterday = datetime.date.today() - datetime.timedelta(days=1)
...     run_day(str(yesterday), send=send)

The last cell of a notebook you run every morning calls `run_yesterday`, giving it your own
send. Keep `day_steps`, `run_day` and `run_yesterday` in a .py file of their own beside your
notebook, and import them, so every notebook runs the same steps in the same order.

### Re-run a day safely

Every step can be sent again without harm. A create with `may_exist=True` skips a table that is
there, and INSERT OVERWRITE replaces the day, so sending a day twice leaves the same rows, not
twice as many. To write a day again, after fixing a step or after a morning that failed
halfway, run the whole day again:

>>> run_day("2026-09-23", send=print_first_line)
CREATE TABLE IF NOT EXISTS mart.daily_job_runs (
CREATE TABLE IF NOT EXISTS mart.team_day (
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-23')
INSERT OVERWRITE TABLE mart.team_day PARTITION(dt = '2026-09-23')

Run the whole day, not just the step you fixed: a fixed job count changes the team counts
that read it. For several days, run them oldest first, each day whole:

>>> for day in ["2026-09-23", "2026-09-24"]:
...     run_day(day, send=print_first_line)
CREATE TABLE IF NOT EXISTS mart.daily_job_runs (
CREATE TABLE IF NOT EXISTS mart.team_day (
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-23')
INSERT OVERWRITE TABLE mart.team_day PARTITION(dt = '2026-09-23')
CREATE TABLE IF NOT EXISTS mart.daily_job_runs (
CREATE TABLE IF NOT EXISTS mart.team_day (
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-24')
INSERT OVERWRITE TABLE mart.team_day PARTITION(dt = '2026-09-24')

## Check it worked

The Example database has no mart tables, but it can work out what mart.team_day should hold
for a day straight from `ops.job_runs` and `ops.jobs`, in one Statement: on 2026-09-24, the
data team's job ran twice, and the finance team's jobs ran twice, one run failing.

>>> team_runs = statement(
...     SELECT(
...         jobs.team,
...         AS(count_rows(), "runs"),
...         AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...     ),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
...     GROUP_BY(jobs.team),
... )
>>> run(team_runs, send=example_database.send)
      team  runs  failed_runs
0     data     2            0
1  finance     2            1

At work, after the morning's run, read the day back from mart.team_day and compare it with
this. The same numbers mean both steps ran, in the right order.

## Common mistakes

### Handing run the whole list

`run` sends one Statement, and refuses a list. The message names `to_hive`, which `run` calls
first to write the Hive, and which takes one Statement:

>>> run(steps, send=print_first_line)
Traceback (most recent call last):
...
TypeError:
  What happened:  to_hive was given [...], which isn't a Statement.
...

Send the list's steps one at a time, with a loop, as `run_day` does.

### Reading a Saved table without naming its day

A step that reads a Saved table must bound its days, like any table with a Date partition.
Leave out the WHERE, and the team step is refused as you build it:

>>> statement(
...     INSERT_OVERWRITE(team_day),
...     SELECT(jobs.team, AS(sum_of(daily_job_runs.runs), "runs"),
...            AS(sum_of(daily_job_runs.failed_runs), "failed_runs")),
...     FROM(daily_job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, daily_job_runs.job_id)),
...     GROUP_BY(jobs.team),
... )
Traceback (most recent call last):
...
composer_core.refusals.LoadRefused:
  What happened:  FROM(daily_job_runs) reads mart.daily_job_runs, but nothing bounds its Date partition dt at both ends.
...

Bound it to the day being written, `equals(daily_job_runs.dt, day)`, so each step of a day
reads that same day.

### A step that works out its own day

A step bounded with `last_n_days(job_runs.dt, 1)` reads yesterday, counted from the day it
runs, so it can't write any other day. On this page today is 2026-09-25, so it writes
2026-09-24:

>>> yesterday_only = statement(
...     INSERT_OVERWRITE(daily_job_runs),
...     SELECT(job_runs.job_id, AS(count_rows(), "runs"),
...            AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs")),
...     FROM(job_runs),
...     WHERE(last_n_days(job_runs.dt, 1)),
...     GROUP_BY(job_runs.job_id),
... )
>>> print(to_hive(yesterday_only).splitlines()[0])
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-24')

Run it a week later to redo 2026-09-24, and it writes a different day. Give every step the day
as an argument, as `write_job_day` does, and work out yesterday once, in `run_yesterday`.

### A create without may_exist in the daily list

`create_table(daily_job_runs)` writes a plain CREATE TABLE:

>>> print(to_hive(create_table(daily_job_runs)).splitlines()[0])
CREATE TABLE mart.daily_job_runs (

The first morning it creates the table. The second morning the warehouse refuses it, since the
table exists, and `run_day` stops before writing anything. In a list that runs every day, use
`may_exist=True`, which writes CREATE TABLE IF NOT EXISTS.

## Next

- See where each column of mart.team_day comes from, through mart.daily_job_runs:
  [Lineage of a pipeline across Saved tables](#lineage_of_a_pipeline_across_saved_tables).
- Write many past days of the first step at once:
  [Backfill a range of days](#backfill_a_range_of_days).
- The writes themselves, step by step: [Save a table](#save_a_table).
- The gallery's [`run`](examples.html#run), [`create_table`](examples.html#create_table) and
  [`show_hive`](examples.html#show_hive) entries.
"""
