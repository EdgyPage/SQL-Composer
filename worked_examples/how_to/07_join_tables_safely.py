"""Join tables safely

For: Getting started

## Goal

Put two tables' columns side by side with `JOIN`, without counting any row twice. You join on
a table's key where you can, read the repeated-rows Warning when you can't, add the other
table up first so it has one row per value you join on, and use `LEFT_JOIN` to keep the rows
with no match, or to find them.

## When you'd use it

Whenever the numbers you want live in more than one table: each run's team, which is in
`ops.jobs`; each run's alerts, which are in `ops.run_alerts`; the jobs that never ran. A join
that repeats rows still runs and still gives numbers. They are just too big, so it is worth
knowing why it happens before it happens to you.

## Steps

### Import the Toolbox and name the tables

>>> from sqlglot_composer import *
>>> jobs = example_database.jobs
>>> job_runs = example_database.job_runs
>>> run_alerts = example_database.run_alerts

### Know each table's key

A table's key is the columns that pick out one of its rows, as its Table reference says:

- `jobs` has one row per job: its key is `jobs.job_id`;
- `job_runs` has one row per run: its key is `job_runs.run_id`, and each run names its job in
  `job_runs.job_id`;
- `run_alerts` has one row per alert: its key is `run_alerts.alert_id`, and each alert names
  its run in `run_alerts.run_id`. A run can raise several alerts, or none.

`check_key` checks a key holds on the table itself:

>>> check_key(jobs, send=example_database.send)
ops.jobs: the key (job_id) holds.

### Join on the other table's key

`JOIN` adds another table's columns to each row, matched by its `ON=` condition. Each run
names one job, and `jobs.job_id` is the key of `jobs`, so each run meets exactly one row of
`jobs`: nothing is repeated.

>>> runs_with_team = statement(
...     SELECT(job_runs.run_id, job_runs.job_id, jobs.team, job_runs.duration_mins),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> text = show_hive(runs_with_team)
SELECT
  job_runs.run_id,
  job_runs.job_id,
  jobs.team,
  job_runs.duration_mins
FROM ops.job_runs AS job_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = job_runs.job_id
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24';
>>> run(runs_with_team, send=example_database.send)
   run_id  job_id     team  duration_mins
0      95       1     data             12
1      96       2  finance             18
2      97       3  finance             30
3      98       2  finance             15
4      99       1     data              5
5     101       1     data             10
6     102       2  finance             20
7     103       3  finance             30
8     104       1     data             40

Nine runs in, nine rows out. Counting per team after this join is safe:

>>> per_team = statement(
...     SELECT(jobs.team, AS(count_rows(), "runs"), AS(sum_of(job_runs.duration_mins), "minutes")),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(jobs.team),
... )
>>> run(per_team, send=example_database.send)
      team  runs  minutes
0     data     4       67
1  finance     5      113

### See the repeated-rows Warning

Now each run's alerts. `run_alerts.run_id` isn't the key of `run_alerts`: a run with two
alerts matches two rows, so the run comes out twice. The Toolbox lets the Statement through,
since sometimes that is what you want, but warns at the JOIN:

>>> runs_with_alerts = statement(
...     SELECT(job_runs.run_id, job_runs.duration_mins, run_alerts.alert_id),
...     FROM(job_runs),
...     JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id)),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           between(run_alerts.dt, "2026-09-23", "2026-09-24")),
... )
>>> text = show_hive(runs_with_alerts)
SELECT
  job_runs.run_id,
  job_runs.duration_mins,
  run_alerts.alert_id
FROM ops.job_runs AS job_runs
JOIN ops.run_alerts AS run_alerts
  ON run_alerts.run_id = job_runs.run_id
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  AND run_alerts.dt BETWEEN '2026-09-23' AND '2026-09-24';
>>> run(runs_with_alerts, send=example_database.send)
   run_id  duration_mins  alert_id
0      97             30         1
1      97             30         2
2     101             10         3
3     101             10         4
4     101             10         5
5     102             20         6
6     103             30         7
7     103             30         8
8     104             40         9

Run 101 is there three times, with its 10 minutes each time, and the runs with no alert, such
as 95, are gone, because `JOIN` keeps only rows that match. `run_alerts` has a Date partition
too, so it gets its own days in `WHERE`.

### Watch a total come out too big

Add up the minutes over that join, and the repeated runs are added again:

>>> careless_total = statement(
...     SELECT(AS(sum_of(job_runs.duration_mins), "minutes"), AS(count_rows(), "alerts")),
...     FROM(job_runs),
...     JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id)),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           between(run_alerts.dt, "2026-09-23", "2026-09-24")),
... )
>>> text = show_hive(careless_total)
SELECT
  SUM(job_runs.duration_mins) AS minutes,
  COUNT(*) AS alerts
FROM ops.job_runs AS job_runs
JOIN ops.run_alerts AS run_alerts
  ON run_alerts.run_id = job_runs.run_id
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  AND run_alerts.dt BETWEEN '2026-09-23' AND '2026-09-24';
>>> run(careless_total, send=example_database.send)
   minutes  alerts
0      210       9

The nine runs took 180 minutes in all, as `per_team` shows (67 + 113). Here the minutes come out
as 210. Runs 97 and 103 are added twice (30 more minutes each), run 101 three times (20 more),
and the four runs with no alert, 95, 96, 98 and 99, not at all (50 fewer):
180 + 30 + 30 + 20 - 50 = 210.

### Add up first, with derived

The fix is to give `run_alerts` one row per run before joining it. `derived` gives a Statement
a name, so that another Statement can read it like a table: a Derived table.
[Reusable Derived tables](#reusable_derived_tables) covers them fully. This one groups the
alerts by run, so it has one row per run, and the Toolbox takes its GROUP_BY column,
`alerts_per_run.run_id`, as its key. The alerts' days are in its own `WHERE` now:

>>> alerts_per_run = derived("alerts_per_run", statement(
...     SELECT(run_alerts.run_id, AS(count_rows(), "alerts")),
...     FROM(run_alerts),
...     WHERE(between(run_alerts.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(run_alerts.run_id),
... ))

### Keep every run with LEFT_JOIN

Now join it. `LEFT_JOIN` keeps every run, also those with no alert, and gives them NULL in the
joined columns; `fill_null` turns that NULL into 0, written COALESCE in the Hive. The
Statement's `WHERE` gives only the runs' days: the alerts' days are inside `alerts_per_run`.

>>> runs_and_alerts = statement(
...     SELECT(job_runs.run_id, job_runs.duration_mins,
...            AS(fill_null(alerts_per_run.alerts, 0), "alerts")),
...     FROM(job_runs),
...     LEFT_JOIN(alerts_per_run, ON=equals(alerts_per_run.run_id, job_runs.run_id)),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> text = show_hive(runs_and_alerts)
WITH alerts_per_run AS (
  SELECT
    run_alerts.run_id,
    COUNT(*) AS alerts
  FROM ops.run_alerts AS run_alerts
  WHERE
    run_alerts.dt BETWEEN '2026-09-23' AND '2026-09-24'
  GROUP BY
    run_alerts.run_id
)
SELECT
  job_runs.run_id,
  job_runs.duration_mins,
  COALESCE(alerts_per_run.alerts, 0) AS alerts
FROM ops.job_runs AS job_runs
LEFT JOIN alerts_per_run
  ON alerts_per_run.run_id = job_runs.run_id
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24';
>>> run(runs_and_alerts, send=example_database.send)
   run_id  duration_mins  alerts
0      95             12       0
1      96             18       0
2      97             30       2
3      98             15       0
4      99              5       0
5     101             10       3
6     102             20       1
7     103             30       2
8     104             40       1

One row per run, and no Warning. The Derived table is written at the top of the Hive, as
`WITH alerts_per_run AS (...)`. A SUM of nothing but NULL is NULL, so `fill_null` around the
`sum_of` makes the total read 0 even if no run had an alert. The totals now come out right:

>>> fixed_total = statement(
...     SELECT(AS(sum_of(job_runs.duration_mins), "minutes"),
...            AS(fill_null(sum_of(alerts_per_run.alerts), 0), "alerts")),
...     FROM(job_runs),
...     LEFT_JOIN(alerts_per_run, ON=equals(alerts_per_run.run_id, job_runs.run_id)),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> text = show_hive(fixed_total)
WITH alerts_per_run AS (
  SELECT
    run_alerts.run_id,
    COUNT(*) AS alerts
  FROM ops.run_alerts AS run_alerts
  WHERE
    run_alerts.dt BETWEEN '2026-09-23' AND '2026-09-24'
  GROUP BY
    run_alerts.run_id
)
SELECT
  SUM(job_runs.duration_mins) AS minutes,
  COALESCE(SUM(alerts_per_run.alerts), 0) AS alerts
FROM ops.job_runs AS job_runs
LEFT JOIN alerts_per_run
  ON alerts_per_run.run_id = job_runs.run_id
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24';
>>> run(fixed_total, send=example_database.send)
   minutes  alerts
0      180       9

### Keep the rows with no match

`LEFT_JOIN` keeps every row of the table in `FROM`. Here every job, with its runs counted
first so each job meets at most one row; `ops.jobs` has a job that never ran, cache_warm:

>>> runs_per_job = derived("runs_per_job", statement(
...     SELECT(job_runs.job_id, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... ))
>>> every_job = statement(
...     SELECT(jobs.job_id, jobs.job_name, AS(fill_null(runs_per_job.runs, 0), "runs")),
...     FROM(jobs),
...     LEFT_JOIN(runs_per_job, ON=equals(runs_per_job.job_id, jobs.job_id)),
... )
>>> text = show_hive(every_job)
WITH runs_per_job AS (
  SELECT
    job_runs.job_id,
    COUNT(*) AS runs
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  GROUP BY
    job_runs.job_id
)
SELECT
  jobs.job_id,
  jobs.job_name,
  COALESCE(runs_per_job.runs, 0) AS runs
FROM ops.jobs AS jobs
LEFT JOIN runs_per_job
  ON runs_per_job.job_id = jobs.job_id;
>>> run(every_job, send=example_database.send)
   job_id      job_name  runs
0       1  nightly_load     4
1       2  invoice_sync     3
2       3  report_build     2
3       4    cache_warm     0

A plain `JOIN` would have left cache_warm out, with nothing to say it was missing.

### Find the rows with no match

A row with no match has NULL in every joined column, so `is_null` on one of them keeps just
those rows. Here, the jobs that never ran on the two days, with the same `runs_per_job`:

>>> never_ran = statement(
...     SELECT(jobs.job_id, jobs.job_name),
...     FROM(jobs),
...     LEFT_JOIN(runs_per_job, ON=equals(runs_per_job.job_id, jobs.job_id)),
...     WHERE(is_null(runs_per_job.job_id)),
... )
>>> text = show_hive(never_ran)
WITH runs_per_job AS (
  SELECT
    job_runs.job_id,
    COUNT(*) AS runs
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  GROUP BY
    job_runs.job_id
)
SELECT
  jobs.job_id,
  jobs.job_name
FROM ops.jobs AS jobs
LEFT JOIN runs_per_job
  ON runs_per_job.job_id = jobs.job_id
WHERE
  runs_per_job.job_id IS NULL;
>>> run(never_ran, send=example_database.send)
   job_id    job_name
0       4  cache_warm

## Check it worked

A join that doesn't repeat rows gives as many rows as the table in `FROM` has, and the same
totals. Count the runs of the two days on their own, then after the join:

>>> runs_alone = statement(
...     SELECT(AS(count_rows(), "runs"), AS(sum_of(job_runs.duration_mins), "minutes")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> run(runs_alone, send=example_database.send)
   runs  minutes
0     9      180
>>> len(run(runs_and_alerts, send=example_database.send))
9

Nine runs and 180 minutes alone, and nine rows after the fixed join, whose total,
`fixed_total`, is 180 too. Of the Statements here, only `runs_with_alerts` and
`careless_total`, built to show the Warning, gave one.

## Common mistakes

### Silencing the Warning instead of fixing the join

The Warning's Opt-out, `many_matches=True`, says the repeated rows are what you mean. Pasted to
make the Warning go away, it leaves the total just as wrong, and now nothing says so:

>>> silenced = statement(
...     SELECT(AS(sum_of(job_runs.duration_mins), "minutes")),
...     FROM(job_runs),
...     JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id), many_matches=True),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           between(run_alerts.dt, "2026-09-23", "2026-09-24")),
... )
>>> run(silenced, send=example_database.send)
   minutes
0      210

Use the Opt-out when one row per match is the point, such as a list of every alert with its
run's minutes, and nothing over it is added up. To add up, add up before you join.
[Guards, Warnings and opt-outs](#guards_warnings_and_opt_outs) says when each opt-out is right.

### A JOIN with no ON=

>>> no_on = statement(
...     SELECT(job_runs.run_id, jobs.team),
...     FROM(job_runs),
...     JOIN(jobs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  JOIN(jobs) has no ON=.
...

Without `ON=`, every run would be paired with every job: 9 runs times 4 jobs, 36 rows.

### A condition on the LEFT_JOIN's table in WHERE

`WHERE` runs after the join. A row `LEFT_JOIN` kept for having no match has NULL in the
joined columns, so a condition on them in `WHERE` throws it away again, and the LEFT_JOIN
becomes a plain JOIN. (`many_matches=True` is there because a job has many runs: it says the
repeated rows are meant, so that only the mistake shown here stops.)

>>> runs_of_every_job = statement(
...     SELECT(jobs.job_id, job_runs.run_id),
...     FROM(jobs),
...     LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id), many_matches=True),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  WHERE has job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24', a condition on job_runs, which LEFT_JOIN brought in.
...

Move it into `ON=`, next to the join condition, as the message's Usual fix says; `all_of`
joins the two conditions:
`ON=all_of(equals(job_runs.job_id, jobs.job_id), between(job_runs.dt, "2026-09-23",
"2026-09-24"))`. A condition on the joined table belongs in `WHERE` only when it keeps the rows
with no match: `is_null`, as in the step Find the rows with no match, or an `any_of` with such
an `is_null` among its conditions.

### Forgetting the joined table's days

Each table with a Date partition needs its own days, the joined one too. (Here too,
`many_matches=True` says that a run's several alerts are meant, so only the missing days
stop.) The message says "bounds": to bound a Date partition is to give its first and last
day.

>>> alerts_any_day = statement(
...     SELECT(job_runs.run_id, run_alerts.alert_id),
...     FROM(job_runs),
...     JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id), many_matches=True),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
Traceback (most recent call last):
...
composer_core.refusals.LoadRefused:
  What happened:  JOIN(run_alerts, ON=...) reads ops.run_alerts, but nothing bounds its Date partition dt at both ends.
...

## Next

- Keep a step such as `alerts_per_run` as a function, and use it in every Statement that
  needs it: [Reusable Derived tables](#reusable_derived_tables).
- Keep one whole row per key, such as each job's newest run:
  [The latest row per key](#latest_row_per_key).
- Every Guard, Warning and opt-out, and when an opt-out is right:
  [Guards, Warnings and opt-outs](#guards_warnings_and_opt_outs).
- The gallery's Worked examples of [`JOIN`](examples.html#JOIN) and
  [`LEFT_JOIN`](examples.html#LEFT_JOIN), and the traps beside their fixes:
  [repeated rows](examples.html#repeated_rows),
  [a LEFT_JOIN then WHERE](examples.html#left_join_then_where) and
  [jobs that never ran](examples.html#jobs_that_never_ran).
"""
