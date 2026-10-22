"""Describe a table by hand

For: Getting started

## Goal

Write a Table reference yourself, one argument at a time, for a table `write_table_reference`
can't ask about. Here it is mart.job_day, a Saved table you are about to create (a table of
your own, which your Statements write into), with one row per job per day. Along the way you see what each argument of `Table` is for: the columns and
their types, `partitioned_by=`, `key=`, `does_not_add_up=` and `location=`, and how a table
partitioned by two columns, whose days are written another way, is described.

## When you'd use it

- Before you create a Saved table. It doesn't exist yet, so there is nothing to ask:
  `create_table` makes the table from the Table reference you write here.
- When you know a table better than the warehouse does: its key and the columns that don't add
  up are never in its description, so even a generated Table reference needs your hand, as
  [Add your tables' references](#add_your_tables_references) shows.

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
...     partitioned_by=["dt"],
...     key=["job_id", "dt"],
...     does_not_add_up=["avg_minutes"],
...     location="/data/your_team/mart.db/job_day",
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
- `partitioned_by=["dt"]` lists the columns the table is split into Partitions by, in the
  order Hive partitions by them: here one, the day. Each is a column in `columns=` too. The
  warehouse stores a Partition at a time, and every Statement that reads the table must filter
  at least one of them. A table that isn't partitioned, such as `ops.jobs`, leaves it out.
- `key=["job_id", "dt"]` lists the columns that pick out one row. A table with no Key leaves it
  out, and nothing is checked against one. A job has a row on every day,
  so `job_day.job_id` alone repeats; the job and the day together pick out one row. JOIN reads
  the key to warn you when a join could repeat rows.
- `does_not_add_up=["avg_minutes"]` lists the columns that are averages, ratios or counts of
  different values. Adding up two days' averages gives a number that means nothing, so the
  Toolbox refuses to add these up.
- `location="/data/your_team/mart.db/job_day"` is the table's own folder, used exactly as you
  write it: the Toolbox adds nothing to it. Only a table you create yourself has one, and no
  two of your Saved tables may share a folder or nest one inside the other. A table someone
  else owns, such as `ops.jobs`, leaves it out.

### Keep it in a file

Save the Table reference as mart__job_day.py in your Project's references/ folder, named
after its database and table joined by two underscores, so every notebook of the Project that
reads the table imports the same one:

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
        partitioned_by=["dt"],
        key=["job_id", "dt"],
        does_not_add_up=["avg_minutes"],
        location="/data/your_team/mart.db/job_day",
    )

Then, in a notebook of the Project:

    from references.mart__job_day import job_day

A file you write by hand isn't in the Project's registry yet: `project.check()` lists it as
made by hand, and `project.register("mart.job_day")` adds it. For a Saved table the Project
makes, [Add a Saved table](#add_a_saved_table) writes this file for you to fill in, and
registers it.

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
run it. At work, once the table exists and holds some days, `run` runs it with your own query.

### A table partitioned by two columns, its days written another way

The Example database's `ops.region_costs`, each job's cost in cents per region per day, is
partitioned by two columns: the region, then the day. Its key is the job, the region and the
day. It writes its days like 20260924 rather than 2026-09-24:

>>> region_costs = Table(
...     "ops.region_costs",
...     columns={"job_id": "bigint", "cost_cents": "bigint", "region": "string",
...              "dt": "string"},
...     partitioned_by=["region", "dt"],
...     key=["job_id", "region", "dt"],
... )

The Toolbox compares a value with a column exactly as you write it, so write each day the
table's way:

>>> costs = statement(
...     SELECT(region_costs.job_id, region_costs.cost_cents),
...     FROM(region_costs),
...     WHERE(equals(region_costs.dt, "20260923")),
... )
>>> run(costs, query=example_database.query)
   job_id  cost_cents
0       1         120
1       2         180

Filtering either partition column is enough for the Load limit: the step above filters the
day alone, and one that filters the region alone, or both, is let through too.

Days written year first, as both 20260924 and 2026-09-24 are, sort in date order as text, so
`between` works on them as on dates:

>>> two_days = statement(
...     SELECT(region_costs.job_id, region_costs.cost_cents),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, "20260923", "20260924")),
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

>>> check_table_reference(region_costs, query=example_database.query)
ops.region_costs matches its Table reference.

It matches, both partition columns in their order included.
[A day written another way, and a second partition](#a_day_written_another_way) covers such a
table further.

The table mart.job_day doesn't exist yet. `create_table` writes the Hive that makes it from your
Table reference: read it to check the columns, their types and the partition are what you meant.

>>> text = show_hive(create_table(job_day))
CREATE EXTERNAL TABLE mart.job_day (
  job_id BIGINT,
  runs BIGINT,
  failed_runs BIGINT,
  minutes BIGINT,
  avg_minutes DOUBLE...
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/mart.db/job_day';

The partition column, dt, goes under PARTITIONED BY rather than among the other columns: that is
how Hive splits a table into Partitions. LOCATION is the folder you wrote, as you wrote it.
STORED AS ORC says how Hive keeps the table's files: ORC, a compact format Hive reads quickly.
EXTERNAL and LOCATION say the files are yours, in the table's own folder.

At work, once `run` has sent `create_table(job_day)` through your own execute and made the table,
`check_table_reference` compares it with your file, as above.

## Common mistakes

### A partition column left out of columns

A partition column is a column of the table too, so it goes in `columns=` as well as in
`partitioned_by=`. One that is only in `partitioned_by=` stops:

>>> job_day_no_dt = Table(
...     "mart.job_day",
...     columns={"job_id": "bigint", "runs": "bigint"},
...     partitioned_by=["dt"],
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  Table('mart.job_day'): partitioned_by names 'dt', which isn't one of its columns.
...

Add `"dt": "string"` to `columns=`.

### A key that names a column the table doesn't have

>>> job_day_typo = Table(
...     "mart.job_day",
...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
...     partitioned_by=["dt"],
...     key=["job_id", "day"],
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  Table('mart.job_day'): key names 'day', which isn't one of its columns.
...

`key=`, `partitioned_by=` and `does_not_add_up=` each name columns from `columns=`, spelled
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
sqlglot_composer.refusals.GuardRefused:
  What happened:  sum_of(job_day.avg_minutes) adds up job_day.avg_minutes, which is listed in does_not_add_up in its Table reference.
...
  Opt-out:        sum_of(job_day.avg_minutes, adds_up=True)

Each day's average is right for its day, but a week's average isn't the sum of the days', nor
their average when the days had different numbers of runs. The table keeps `job_day.minutes` and
`job_day.runs`, which add up: total those over the week, and work the average out from the
totals. The Opt-out is for the rare call where a total really is what you mean.

### A day written the other way

The Toolbox doesn't know how a table writes its days: it compares the value as you wrote it. A
day written like 2026-09-23, on a table that writes 20260923, matches no row, and nothing
stops it:

>>> wrong_day = statement(
...     SELECT(region_costs.job_id),
...     FROM(region_costs),
...     WHERE(equals(region_costs.dt, "2026-09-23")),
... )
>>> run(wrong_day, query=example_database.query)
Empty DataFrame
Columns: [job_id]
Index: []

When a result comes back empty, look at how the table writes the column: `first_look` shows a
few of its rows.

### date_partition= from an older Toolbox

A Table reference written for Toolbox 6 said `date_partition=` and, for days written another
way, `date_format=`. Both stop, saying what to write instead:

>>> old_reference = Table(
...     "ops.region_costs",
...     columns={"job_id": "bigint", "cost_cents": "bigint", "region": "string",
...              "dt": "string"},
...     date_partition="dt",
... )
Traceback (most recent call last):
...
TypeError:
  What happened:  Table('ops.region_costs') was given date_partition=, which Toolbox 7.0 replaced.
...
  Usual fix:      Write partitioned_by=["dt"] where it said date_partition="dt", leave it out where it said date_partition=None, and remove date_format=. CHANGES.md, under 7.0, says more.
...

## Next

- Build a Statement on your table and paste its Hive into another program:
  [Build a first Statement and paste its Hive](#build_a_first_statement).
- Join your table to another without repeating rows, which is what `key=` is for:
  [Join tables safely](#join_tables_safely).
- Create a Saved table and write rows into it: [Save a table](#save_a_table).
- The gallery's Worked examples of [`Table`](examples.html#Table) and
  [`create_table`](examples.html#create_table), and a Saved table built and written step by
  step: [Worked example of a Saved table](examples.html#saved_table).
"""
