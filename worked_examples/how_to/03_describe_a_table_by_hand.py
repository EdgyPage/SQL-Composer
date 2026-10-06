"""Describe a table by hand

For: Getting started

## Goal

Write a Table reference yourself, one argument at a time, for a table `write_table_reference`
can't ask about. Here it is mart.job_day, a Saved table you are about to create (a table of
your own, which your Statements write into), with one row per job per day. Along the way you see what each argument of `Table` is for: the columns and
their types, `date_partition=`, `key=`, `does_not_add_up=`, and `date_format=` for a table whose
days are written another way.

## When you'd use it

- Before you create a Saved table. It doesn't exist yet, so there is nothing to ask:
  `create_table` makes the table from the Table reference you write here.
- When you know a table better than the warehouse does: its key and the columns that don't add
  up are never in its description, so even a generated Table reference needs your hand, as
  [Import a table's column names programmatically](#import_column_names) shows.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *

### Decide what one row is

Before you write anything, say in one sentence what one row of the table is. For mart.job_day it
is "one job on one day": how many times the job ran that day, how many of those runs
failed, their minutes in all, and the average minutes of a run. Each of those becomes a
column, and the sentence decides the key.

### Write the Table reference

A Table reference is one call to `Table`:

>>> job_day = Table(
...     "mart.job_day",
...     columns={
...         "job_id": "bigint",
...         "runs": "bigint",
...         "failed_runs": "bigint",
...         "minutes": "bigint",
...         "avg_minutes": "double",  # minutes / runs: the average run that day
...         "dt": "string",  # the day of the runs, as 2026-09-24
...     },
...     date_partition="dt",
...     key=["job_id", "dt"],
...     does_not_add_up=["avg_minutes"],
... )
>>> job_day
Table('mart.job_day', columns: job_id, runs, failed_runs, minutes, avg_minutes, dt)

What each argument says:

- `"mart.job_day"` is the table's name as the warehouse knows it: the database, a dot, then the
  table.
- `columns=` maps each column's name to its Hive type, spelled as DESCRIBE prints it: `"bigint"`
  for whole numbers, `"string"` for text, `"double"` for numbers with a decimal point,
  `"decimal(10,2)"` for exact amounts such as money. The Toolbox checks the values you compare a
  typed column with, so `equals(job_day.runs, "3")` stops, since `"3"` is text.
- `date_partition="dt"` names the one column the table is split into days by. The warehouse
  stores a day at a time, and every Statement that reads the table must give its first and last
  day. A table with no days, such as `ops.jobs`, says `date_partition=None`. Unlike `key=`,
  `does_not_add_up=` and `date_format=`, it has no default, so you can't leave it out.
- `key=["job_id", "dt"]` lists the columns that pick out one row. A job has a row on every day,
  so `job_day.job_id` alone repeats; the job and the day together pick out one row. JOIN reads
  the key to warn you when a join could repeat rows.
- `does_not_add_up=["avg_minutes"]` lists the columns that are averages, ratios or counts of
  different values. Adding up two days' averages gives a number that means nothing, so the
  Toolbox refuses to add these up.
- There is no `date_format=`: its days are written like 2026-09-24, the usual way. The step
  A table whose days are written another way, below, shows one that needs it.

### Keep it in a file

Save the Table reference as job_day.py, beside your notebook, so every notebook and script
that reads the table imports the same one:

    \"\"\"mart.job_day - one row per job and day: runs, failed runs, minutes and the average.\"\"\"
    from sqlglot_composer import Table

    job_day = Table(
        "mart.job_day",
        columns={
            "job_id": "bigint",
            "runs": "bigint",
            "failed_runs": "bigint",
            "minutes": "bigint",
            "avg_minutes": "double",  # minutes / runs: the average run that day
            "dt": "string",  # the day of the runs, as 2026-09-24
        },
        date_partition="dt",
        key=["job_id", "dt"],
        does_not_add_up=["avg_minutes"],
    )

Then, in a notebook:

    from job_day import job_day

### Read it in a Statement

A hand-written Table reference works exactly like a generated one. Its columns are its
attributes, and a Statement reads it with `FROM`:

>>> long_days = statement(
...     SELECT(job_day.job_id, job_day.dt, job_day.minutes),
...     FROM(job_day),
...     WHERE(between(job_day.dt, "2026-09-23", "2026-09-24"), at_least(job_day.minutes, 30)),
... )
>>> text = show_hive(long_days)
SELECT
  job_day.job_id,
  job_day.dt,
  job_day.minutes
FROM mart.job_day AS job_day
WHERE
  job_day.dt BETWEEN '2026-09-23' AND '2026-09-24' AND job_day.minutes >= 30;

The table mart.job_day isn't on the Example database, so this how-to shows its Hive but can't
run it. At work, once the table exists and holds some days, `run` runs it with your own send.

### A table whose days are written another way

The Toolbox expects a Date partition's days written like 2026-09-24. Some tables write them
like 20260924 instead. The Example database's `ops.region_costs`, each job's cost in cents per
region per day, is one, so its key is the job, the region and the day. Its Table reference
says how its days are written, with `date_format=`:

>>> region_costs = Table(
...     "ops.region_costs",
...     columns={"job_id": "bigint", "cost_cents": "bigint", "region": "string",
...              "dt": "string"},
...     date_partition="dt",
...     date_format="%Y%m%d",
...     key=["job_id", "region", "dt"],
... )

`"%Y%m%d"` uses the codes of Python's own `datetime.strftime`: `"%Y"` is the year, `"%m"` the
month and `"%d"` the day, with nothing between them. The pattern must put the year first, then
the month, then the day: Hive compares the days as text, and only days written year first sort
in date order.

You then write each day the table's way:

>>> costs = statement(
...     SELECT(region_costs.job_id, region_costs.cost_cents),
...     FROM(region_costs),
...     WHERE(equals(region_costs.dt, "20260923")),
... )
>>> run(costs, send=example_database.send)
   job_id  cost_cents
0       1         120
1       2         180

Or pass a `datetime.date`, which the Toolbox writes the table's way for you, so the same
Python works on tables that write their days differently:

>>> import datetime
>>> two_days = statement(
...     SELECT(region_costs.job_id, region_costs.cost_cents),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, datetime.date(2026, 9, 23),
...                   datetime.date(2026, 9, 24))),
... )
>>> text = show_hive(two_days)
SELECT
  region_costs.job_id,
  region_costs.cost_cents
FROM ops.region_costs AS region_costs
WHERE
  region_costs.dt BETWEEN '20260923' AND '20260924';

## Check it worked

A table that already exists can be compared with your Table reference:

>>> check_table_reference(region_costs, send=example_database.send)
ops.region_costs matches its Table reference.
Notes:
  - the table is also partitioned by region, which a Statement may bound too.

It matches. The note is about a second partition, `region_costs.region`: a Statement may give
the regions it reads too, but doesn't have to.
[A day written another way, and a second partition](#a_day_written_another_way) covers it.

The table mart.job_day doesn't exist yet. `create_table` writes the Hive that makes it from your
Table reference: read it to check the columns, their types and the partition are what you meant.

>>> text = show_hive(create_table(job_day))
CREATE TABLE mart.job_day (
  job_id BIGINT,
  runs BIGINT,
  failed_runs BIGINT,
  minutes BIGINT,
  avg_minutes DOUBLE
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC;

The Date partition, dt, goes under PARTITIONED BY rather than among the other columns: that is
how Hive splits a table into days. STORED AS ORC says how Hive keeps the table's files: ORC, a
compact format Hive reads quickly.

At work, once `run` has sent `create_table(job_day)` through your own send and made the table,
`check_table_reference` compares it with your file, as above.

## Common mistakes

### Leaving out date_partition

`date_partition=` has no default, so that a table you forgot to describe the days of can't
quietly be read whole. Leaving it out stops with Python's own message:

>>> jobs = Table(
...     "ops.jobs",
...     columns={"job_id": "bigint", "job_name": "string", "team": "string",
...              "region": "string"},
...     key=["job_id"],
... )
Traceback (most recent call last):
...
TypeError: Table.__init__() missing 1 required positional argument: 'date_partition'

For a table with no days, write `date_partition=None`.

### A key that names a column the table doesn't have

>>> job_day_typo = Table(
...     "mart.job_day",
...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
...     date_partition="dt",
...     key=["job_id", "day"],
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  Table('mart.job_day'): key names 'day', which isn't one of its columns.
...

`key=`, `date_partition=` and `does_not_add_up=` each name columns from `columns=`, spelled
the same way.

### Adding up a column that doesn't add up

>>> week = statement(
...     SELECT(job_day.job_id, AS(sum_of(job_day.avg_minutes), "avg_minutes")),
...     FROM(job_day),
...     WHERE(between(job_day.dt, "2026-09-21", "2026-09-24")),
...     GROUP_BY(job_day.job_id),
... )
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  sum_of(job_day.avg_minutes) adds up job_day.avg_minutes, which is listed in does_not_add_up in its Table reference.
...
  Opt-out:        sum_of(job_day.avg_minutes, adds_up=True)

Each day's average is right for its day, but a week's average isn't the sum of the days', nor
their average when the days had different numbers of runs. The table keeps `job_day.minutes` and
`job_day.runs`, which add up: total those over the week, and work the average out from the
totals. The Opt-out is for the rare call where a total really is what you mean.

### A day written the other way

With `date_format="%Y%m%d"`, a day written like 2026-09-23 would match no day of the table, so
it stops:

>>> wrong_day = statement(
...     SELECT(region_costs.job_id),
...     FROM(region_costs),
...     WHERE(equals(region_costs.dt, "2026-09-23")),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  equals(region_costs.dt, ...) compares the Date partition region_costs.dt with '2026-09-23', but its Table reference writes days like '20260923'.
...

### A date_format that doesn't put the year first

>>> costs_by_hand = Table(
...     "ops.region_costs",
...     columns={"job_id": "bigint", "cost_cents": "bigint", "region": "string",
...              "dt": "string"},
...     date_partition="dt",
...     date_format="%d%m%Y",
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  date_format='%d%m%Y' doesn't write the year first, then the month, then the day.
...

If a table's days really are written day first, its message says what to do instead.

## Next

- Build a Statement on your table and paste its Hive into another program:
  [Build a first Statement and paste its Hive](#build_a_first_statement).
- Join your table to another without repeating rows, which is what `key=` is for:
  [Join tables safely](#join_tables_safely).
- Create a Saved table and write a day's rows into it: [Save a table](#save_a_table).
- The gallery's Worked examples of [`Table`](examples.html#Table) and
  [`create_table`](examples.html#create_table), and a Saved table built and written step by
  step: [Worked example of a Saved table](examples.html#saved_table).
"""
