"""Reusable Derived tables (WITH ... AS in the Hive)

For: Getting started

## Goal

Write a step once, as a function, and use it in every Statement that needs it.

The step is a Derived table: a Statement given a name with `derived`, which another Statement
reads like a table. The Hive writes it at its top, as `WITH name AS (...)`.

The function that makes it is a Building block. It takes arguments, such as the days to read.
You check it alone with `run`, chain one onto another, and it keeps the same name in every
Statement.

## When you'd use it

- When two Statements need the same numbers, such as each job's runs and minutes: written
  once, they can't be worked out two different ways.
- When a Statement grows long: in named steps, it can be read and checked one step at a time.
- When you add up before a join, as [Join tables safely](#join_tables_safely) does: the
  added-up table is a Derived table.

## Steps

### Import the Toolbox and name the tables

>>> from sqlglot_composer import *
>>> jobs = example_database.jobs
>>> job_runs = example_database.job_runs

### Name one step with derived

`derived` gives a Statement a name. Here, each job's runs and minutes over two days:

>>> job_totals = derived("job_totals", statement(
...     SELECT(job_runs.job_id, AS(count_rows(), "runs"),
...            AS(sum_of(job_runs.duration_mins), "minutes")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... ))
>>> job_totals
derived('job_totals', columns: job_id, runs, minutes)

Its columns are what its `SELECT` makes, checked like a Table reference's. Another Statement
reads it with `FROM` or `JOIN`, like any table. Here, the minutes per team. `per_team` gives no
days of its own: the days are inside `job_totals`, and `ops.jobs` has no Date partition.

>>> per_team = statement(
...     SELECT(jobs.team, AS(sum_of(job_totals.minutes), "minutes")),
...     FROM(job_totals),
...     JOIN(jobs, ON=equals(jobs.job_id, job_totals.job_id)),
...     GROUP_BY(jobs.team),
... )
>>> text = show_hive(per_team)
WITH job_totals AS (
  SELECT
    job_runs.job_id,
    COUNT(*) AS runs,
    SUM(job_runs.duration_mins) AS minutes
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  GROUP BY
    job_runs.job_id
)
SELECT
  jobs.team,
  SUM(job_totals.minutes) AS minutes
FROM job_totals
JOIN ops.jobs AS jobs
  ON jobs.job_id = job_totals.job_id
GROUP BY
  jobs.team;
>>> run(per_team, send=example_database.send)
      team  minutes
0     data       67
1  finance      113

The Hive starts with `WITH job_totals AS (...)`, holding the step's own Hive; then the
Statement reads `job_totals` by name. A Derived table lives only inside the Statement that
reads it: nothing is saved in the warehouse.

### Make it a Building block

A Building block is a function that gives back the Derived table, so any Statement can call
it. The days become its arguments, and the name is written once, inside it:

>>> def runs_per_job(first_day, last_day):
...     \"\"\"One row per job: its runs, failed runs and minutes from first_day to last_day.\"\"\"
...     return derived("runs_per_job", statement(
...         SELECT(
...             job_runs.job_id,
...             AS(count_rows(), "runs"),
...             AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...             AS(sum_of(job_runs.duration_mins), "minutes"),
...         ),
...         FROM(job_runs),
...         WHERE(between(job_runs.dt, first_day, last_day)),
...         GROUP_BY(job_runs.job_id),
...     ))

Each call gives a Derived table for the days you ask:

>>> two_days = runs_per_job("2026-09-23", "2026-09-24")
>>> last_day = runs_per_job("2026-09-24", "2026-09-24")

### Check a block alone with run

`run` runs a Statement, and a Derived table is a step inside one, so wrap the block in the
smallest Statement that reads it: every column, with `all_columns`. Check a block like this
before you build on it:

>>> check_two_days = statement(SELECT(all_columns(two_days)), FROM(two_days))
>>> text = show_hive(check_two_days)
WITH runs_per_job AS (
  SELECT
    job_runs.job_id,
    COUNT(*) AS runs,
    COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs,
    SUM(job_runs.duration_mins) AS minutes
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  GROUP BY
    job_runs.job_id
)
SELECT
  runs_per_job.job_id,
  runs_per_job.runs,
  runs_per_job.failed_runs,
  runs_per_job.minutes
FROM runs_per_job;
>>> run(check_two_days, send=example_database.send)
   job_id  runs  failed_runs  minutes
0       1     4            0       67
1       2     3            1       53
2       3     2            1       60
>>> check_last_day = statement(SELECT(all_columns(last_day)), FROM(last_day))
>>> text = show_hive(check_last_day)
WITH runs_per_job AS (
  SELECT
    job_runs.job_id,
    COUNT(*) AS runs,
    COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs,
    SUM(job_runs.duration_mins) AS minutes
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-24' AND '2026-09-24'
  GROUP BY
    job_runs.job_id
)
SELECT
  runs_per_job.job_id,
  runs_per_job.runs,
  runs_per_job.failed_runs,
  runs_per_job.minutes
FROM runs_per_job;
>>> run(check_last_day, send=example_database.send)
   job_id  runs  failed_runs  minutes
0       1     2            0       50
1       2     1            1       20
2       3     1            0       30

### Chain a second step onto the first

A block can read another block. `busy_jobs` keeps the jobs with at least `min_runs` runs. It
reads the Derived table that `runs_per_job` gives back, passed in as its argument `per_job`;
the Statement after it adds each job's name.

`busy_jobs` takes the Derived table as an argument, rather than calling `runs_per_job` itself,
so the Statement picks the days once and every block reads the same ones; and one block's file
never imports another's (see Keep it in a file, below). The Statement builds `runs_per_job` and
hands it in:

>>> def busy_jobs(per_job, min_runs):
...     \"\"\"The jobs of per_job, from runs_per_job, with at least min_runs runs.\"\"\"
...     return derived("busy_jobs", statement(
...         SELECT(per_job.job_id, per_job.runs, per_job.minutes),
...         FROM(per_job),
...         WHERE(at_least(per_job.runs, min_runs)),
...     ))
>>> busy = busy_jobs(runs_per_job("2026-09-23", "2026-09-24"), min_runs=3)
>>> busy_with_names = statement(
...     SELECT(jobs.job_name, busy.runs, busy.minutes),
...     FROM(busy),
...     JOIN(jobs, ON=equals(jobs.job_id, busy.job_id)),
... )
>>> text = show_hive(busy_with_names)
WITH runs_per_job AS (
  SELECT
    job_runs.job_id,
    COUNT(*) AS runs,
    COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs,
    SUM(job_runs.duration_mins) AS minutes
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  GROUP BY
    job_runs.job_id
), busy_jobs AS (
  SELECT
    runs_per_job.job_id,
    runs_per_job.runs,
    runs_per_job.minutes
  FROM runs_per_job
  WHERE
    runs_per_job.runs >= 3
)
SELECT
  jobs.job_name,
  busy_jobs.runs,
  busy_jobs.minutes
FROM busy_jobs
JOIN ops.jobs AS jobs
  ON jobs.job_id = busy_jobs.job_id;
>>> run(busy_with_names, send=example_database.send)
       job_name  runs  minutes
0  invoice_sync     3       53
1  nightly_load     4       67

The Hive holds both steps, in order, each under its own name: `runs_per_job`, then `busy_jobs`
reading it. In `busy_jobs`, `per_job.runs` is a plain column, one number per row, so `WHERE`
can test it.

### Use the same block in another Statement

Any Statement that needs each job's runs calls the same function, and gets the same step under
the same name. Here, each team's failed runs:

>>> per_job = runs_per_job("2026-09-23", "2026-09-24")
>>> failed_per_team = statement(
...     SELECT(jobs.team, AS(sum_of(per_job.failed_runs), "failed_runs")),
...     FROM(per_job),
...     JOIN(jobs, ON=equals(jobs.job_id, per_job.job_id)),
...     GROUP_BY(jobs.team),
... )
>>> text = show_hive(failed_per_team)
WITH runs_per_job AS (
  SELECT
    job_runs.job_id,
    COUNT(*) AS runs,
    COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs,
    SUM(job_runs.duration_mins) AS minutes
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  GROUP BY
    job_runs.job_id
)
SELECT
  jobs.team,
  SUM(runs_per_job.failed_runs) AS failed_runs
FROM runs_per_job
JOIN ops.jobs AS jobs
  ON jobs.job_id = runs_per_job.job_id
GROUP BY
  jobs.team;
>>> run(failed_per_team, send=example_database.send)
      team  failed_runs
0     data            0
1  finance            2

Its Hive starts with the same `WITH runs_per_job AS (...)` as `busy_with_names`'s. Keep a
block's name the same in every Statement, and name it like its function: then its Hive reads
the same everywhere, a Lineage (the record of which table columns feed each output column, see
[Lineage of one Statement](#lineage_of_one_statement)) names it the same in every Statement,
and a change to the function reaches them all.

### Keep it in a file

Building blocks go in .py files in a folder of their own beside your notebook, one block to a
file, such as building_blocks/runs_per_job.py, or a few that belong together in one file, as
how-to 24 does. A block's file imports the
Toolbox and the Table references it reads, never another block's file or a Statement:

    \"\"\"Each job's runs, failed runs and minutes, as a Derived table to read.\"\"\"
    from sqlglot_composer import (
        AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows, derived, equals, statement,
        sum_of,
    )
    from table_references.job_runs import job_runs


    def runs_per_job(first_day, last_day):
        \"\"\"One row per job: its runs, failed runs and minutes from first_day to last_day.\"\"\"
        return derived("runs_per_job", statement(
            SELECT(
                job_runs.job_id,
                AS(count_rows(), "runs"),
                AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
                AS(sum_of(job_runs.duration_mins), "minutes"),
            ),
            FROM(job_runs),
            WHERE(between(job_runs.dt, first_day, last_day)),
            GROUP_BY(job_runs.job_id),
        ))

This file imports its Table reference from a folder table_references/, beside
building_blocks/: once you have many, Table references get a folder of their own too. In
[Import a table's column names programmatically](#import_column_names) the file sat beside the
notebook, so the line there was `from job_runs import job_runs`.

A notebook then imports the block with
`from building_blocks.runs_per_job import runs_per_job`. The starter Example project, in the
Toolbox download's example_projects folder, is laid out this way: Table references, Building
blocks, then Statements.

## Check it worked

The block, checked alone, and a Statement built on it give the same numbers. The failed runs
of the two days, from the block alone, add up to those per team:

>>> from_block = run(check_two_days, send=example_database.send)
>>> from_teams = run(failed_per_team, send=example_database.send)
>>> print(from_block["failed_runs"].sum(), from_teams["failed_runs"].sum())
2 2

## Common mistakes

### Running a Derived table itself

`run` takes a Statement. A Derived table is a step to read, so on its own it stops:

>>> run(two_days, send=example_database.send)
Traceback (most recent call last):
...
TypeError:
  What happened:  to_hive was given derived('runs_per_job', columns: job_id, runs, failed_runs, minutes), which isn't a Statement.
...

Wrap it in a Statement that reads it, as the step Check a block alone with run does.

### Two blocks with one name

A second block, copied from the first and changed, keeps the first one's name unless you change
it. Here a block of each job's long runs keeps the name `runs_per_job`. A Statement that reads
it beside `busy`, which reads the real `runs_per_job`, holds two different steps under one
name, and stops:

>>> def long_runs_per_job(first_day, last_day):
...     return derived("runs_per_job", statement(
...         SELECT(job_runs.job_id, AS(count_rows(), "long_runs")),
...         FROM(job_runs),
...         WHERE(between(job_runs.dt, first_day, last_day),
...               at_least(job_runs.duration_mins, 30)),
...         GROUP_BY(job_runs.job_id),
...     ))
>>> long_runs = long_runs_per_job("2026-09-23", "2026-09-24")
>>> busy_and_long = statement(
...     SELECT(busy.job_id, busy.runs, AS(fill_null(long_runs.long_runs, 0), "long_runs")),
...     FROM(busy),
...     LEFT_JOIN(long_runs, ON=equals(long_runs.job_id, busy.job_id)),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  statement(...) reads two different Derived tables called 'runs_per_job'.
...

Give each block's Derived table a name of its own, the same as its function's:
`derived("long_runs_per_job", ...)`.

### A column the block doesn't make

A Derived table's columns are checked like a Table reference's, so a name it doesn't have
stops at once, with the names it has:

>>> per_job.failed
Traceback (most recent call last):
...
AttributeError: runs_per_job has no column 'failed'. Did you mean 'failed_runs'? Its columns are: job_id, runs, failed_runs, minutes.

## Next

- Keep one whole row per key, numbering rows in a Derived table:
  [The latest row per key](#latest_row_per_key).
- A file of Building blocks built from other blocks, and how to test them:
  [Share Building blocks between Statements](#share_building_blocks_between_statements).
- The gallery's Worked example of [`derived`](examples.html#derived), and a long Statement
  built in named steps: [Worked example of a job in steps](examples.html#step_by_step).
"""
