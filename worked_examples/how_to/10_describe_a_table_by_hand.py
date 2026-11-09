"""Describe a table by hand

For: Intermediate

## Goal

Write a Table reference yourself, one argument at a time, for a table
`project.add_references` can't ask about, and keep it in the Project's references/ folder. A
Table reference is the file that describes one table: its columns and their types, its
Partitions and its Key. Here the table is mart.job_day, a table that doesn't exist yet, with one
row per job per day. Along the way you see what each argument of `Table` is for: the columns
and their types, `partitioned_by=`, `key=`, `does_not_add_up=` and `location=`, and how to
describe a table partitioned by two columns, whose days are written another way.

## When you'd use it

- If a table doesn't exist yet, such as one your own Python will write, or one another team is
  about to make, write its Table reference by hand: there is nothing to DESCRIBE, so you write
  what it will hold.
- If you fill in the Table reference `project.new_table` writes for a Saved table, write it by
  hand in the same way, as [Save a table](#save_a_table) shows.
- If you know a table better than the warehouse does, fill in what DESCRIBE never holds, its
  Key and the columns that don't add up, even in a Table reference `project.add_references`
  writes, as [Add your tables' references](#add_your_tables_references) shows.
- If you have not yet done the Getting started how-tos, do
  [Start a Project](#start_a_project) and
  [Add your tables' references](#add_your_tables_references) first.

## Steps

### 1. Copy the Intermediate Example project

Goal: a Project to work in. A Project is your folder of scripts at work, in the Toolbox's fixed
layout, and an Example project is one made for the Example database's tables, to read and copy
from. Work in a copy of the Intermediate Example project, at its top: copy
`example_projects/intermediate/` from the download to a folder of your own, copy the
`sqlglot_composer` folder into it, as a Project holds it, and open a notebook there. This page
makes the same copy in its first step, from the download the Toolbox came in, and runs its
steps there:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

Done when the folder holds the Intermediate Example project's files. Then step 2.

### 2. Import the Toolbox and your query

Goal: every name the steps call. Import the Toolbox, the `project` module, the Project's `ops`
Database and your query. A Database is a named group of tables, the first part of a table's
name, `ops` in `ops.jobs`:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from references import ops
>>> from warehouse import connect, query, execute
>>> connect(example_database)

Done when the four imports run without an error. Then step 3.

### 3. Decide what one row is

Goal: the sentence that decides the columns and the Key. Before you write anything, say in one
sentence what one row of the table is. For mart.job_day it is "one job on one day": how many
times the job ran that day, how many of those runs failed, their minutes in all, and the
average minutes of a run. Each of those becomes a column, and the sentence decides the Key, the
columns whose values name exactly one row.

Done when you have the sentence, and the columns it names. Then step 4.

### 4. Write the Table reference in a file

Goal: one Table reference every notebook of the Project imports. A Table reference is one call
to `Table`, kept in the Project's references/ folder, in a file named after its database and
table joined by two underscores:

The file `references/mart__job_day.py`, after you write it:

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

What each argument says:

- `"mart.job_day"` is the table's name as the warehouse knows it: the database, a dot, then the
  table.
- `columns=` maps each column's name to its Hive type, spelled as DESCRIBE prints it:
  `"bigint"` for whole numbers, `"string"` for text, `"double"` for numbers with a decimal
  point, `"decimal(10,2)"` for exact amounts such as money. The Toolbox checks the values you
  compare a typed column with, so comparing `job_day.runs` with `"3"` stops, since `"3"` is
  text.
- `partitioned_by=["dt"]` lists the columns the table is split into Partitions by, in the
  order Hive partitions by them: here one, the day. A Partition is a slice of the table: the
  rows that share one value of each of those columns. Each is a column in `columns=` too. The
  warehouse stores a Partition at a time, and every Statement that reads the table must filter
  at least one of them. A table that isn't partitioned, such as `ops.team_notes`, leaves it
  out.
- `key=["job_id", "dt"]` lists the columns that pick out one row of the table. A job has a row
  on every day, so `job_day.job_id` alone repeats; the job and the day together pick out one
  row. JOIN reads the Key to warn you when a join could repeat rows. A table with no Key,
  such as `ops.team_notes`, says `key=None`, and nothing is checked against one.
- `does_not_add_up=["avg_minutes"]` lists the columns that are averages, ratios or counts of
  different values. Adding up two days' averages gives a number that means nothing, so the
  Toolbox refuses to add these up.
- `location="/data/your_team/mart.db/job_day"` is the table's own folder, used exactly as you
  write it: the Toolbox adds nothing to it. Only a table you create yourself has one, and no
  two of your Saved tables may name one folder. A Saved table is a real table your own
  Statements write. A table someone else owns, such as `ops.job_events`, leaves it out.

Done when references/mart__job_day.py holds the call to `Table` above. Then step 5.

### 5. Register it

Goal: the Project knows the file. A file you write by hand isn't in the Project's Registry yet,
the Project's list of every file a Project action made. `project.check()` lists it as made by
hand, with the call that adopts it. Its last lines say a batch of Hive the Example project
converted earlier is done, which needs nothing from you (how-to 29 says more):

>>> project.check()  # -> a report, printed
Not registered, made by hand. Adopt each with the call beside it:
  references/mart__job_day.py: project.register("mart.job_day")
Done: each convert batch below.
  admin/workflows/convert/convert.ipynb, team_failures: every table the batch wrote passed its
    compare, and its folder is admin/workflows/convert/finished/team_failures/.
>>> project.register("mart.job_day")  # -> a report, printed
Registered references/mart__job_day.py.
Wrote references/mart.py: from references import mart gives mart.budget_overruns, mart.job_day,
    mart.job_day_costs, mart.job_day_facts, mart.job_events_checks, mart.job_notes,
    mart.team_days and mart.team_failures.
Restart the kernel of a notebook that imported references, to see a table added since.

Done when `project.register` prints `Registered references/mart__job_day.py.` Then step 6.

### 6. Import it from its Database

Goal: the table as an attribute of `mart`. `project.register` also writes references/mart.py
again, the `mart` Database, so the table is one of its attributes:

>>> from references import mart
>>> job_day = mart.job_day  # -> Table
>>> job_day
Table('mart.job_day', columns: job_id, runs, failed_runs, minutes, avg_minutes, dt)

Done when `job_day` shows its six columns. Then step 7.

### 7. Read it in a Statement

Goal: a Statement, one query, that reads your table. A hand-written Table reference works
exactly like one `project.add_references` wrote. Its columns are its attributes, and a
Statement reads it with `FROM`:

>>> long_days = statement(  # -> Statement
...     SELECT(job_day.job_id, job_day.dt, job_day.minutes),
...     FROM(job_day),
...     WHERE(between(job_day.dt, "2026-09-23", "2026-09-24"), at_least(job_day.minutes, 30)),
... )
>>> text = show_hive(long_days)  # -> str
SELECT
  job_day.job_id,
  job_day.dt,
  job_day.minutes
FROM mart.job_day AS job_day
WHERE
  job_day.dt BETWEEN '2026-09-23' AND '2026-09-24' AND job_day.minutes >= 30;

The table mart.job_day isn't on the Example database, so this how-to shows its Hive but can't
run it. At work, once the table exists and holds some days, `run_query(long_days, query)` runs
it.

Done when the Hive reads `FROM mart.job_day AS job_day`. Then step 8.

### 8. Read a table partitioned by two columns

Goal: a Statement on a table whose days are written another way. The Project's
`ops.region_costs`, each job's cost in cents per region per day, is partitioned by two columns:
the region, then the day. Its Key is the job, the region and the day. It writes its days like
20260924 rather than 2026-09-24. `project.add_references` wrote its Table reference,
references/ops__region_costs.py, from its DESCRIBE, both partition columns among it, and its
Key was filled in by hand:

    partitioned_by=["region", "dt"],
    key=["job_id", "region", "dt"],  # filled in by hand

The Toolbox compares a value with a column exactly as you write it, so write each day the
table's way:

>>> region_costs = ops.region_costs  # -> Table
>>> costs = statement(  # -> Statement
...     SELECT(region_costs.job_id, region_costs.cost_cents),
...     FROM(region_costs),
...     WHERE(equals(region_costs.dt, "20260923")),
... )
>>> run_query(costs, query)  # -> DataFrame
   job_id  cost_cents
0       1         120
1       2         180

Filtering either partition column is enough for the Load limit, the check that refuses a
Statement that would read too much: the step above filters the day alone, and one that filters
the region alone, or both, is let through too.

Done when the result holds jobs 1 and 2. Then step 9.

### 9. Keep a range of days written another way

Goal: several days from the same table. Days written year first, as both 20260924 and
2026-09-24 are, sort in date order as text, so `between` works on them as on dates:

>>> two_days = statement(  # -> Statement
...     SELECT(region_costs.job_id, region_costs.cost_cents),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, "20260923", "20260924")),
... )
>>> text = show_hive(two_days)  # -> str
SELECT
  region_costs.job_id,
  region_costs.cost_cents
FROM ops.region_costs AS region_costs
WHERE
  region_costs.dt BETWEEN '20260923' AND '20260924';

Done when the Hive's WHERE reads `BETWEEN '20260923' AND '20260924'`. Then check it worked,
below.

## Check it worked

Compare a table that already exists with its Table reference:

>>> check_table_reference(region_costs, query=query)  # -> Verdict
ops.region_costs matches its Table reference.

It matches, both partition columns in their order included.

The table mart.job_day doesn't exist yet. `create_table` writes the Hive that makes it from your
Table reference: read it to check the columns, their types and the partition are what you
meant.

>>> text = show_hive(create_table(job_day))  # -> str
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

The partition column, dt, goes under PARTITIONED BY rather than among the other columns: that
is how Hive splits a table into Partitions. LOCATION is the folder you wrote, as you wrote it.
STORED AS ORC says how Hive keeps the table's files: ORC, a compact format Hive reads quickly.
EXTERNAL and LOCATION say the files are yours, in the table's own folder.

At work, once `run_execute(create_table(job_day), execute)` has made the table,
`check_table_reference(job_day, query=query)` compares it with your file, as above. And the
Project knows the file:

>>> project.check()  # -> a report, printed
Every Table folder, Table reference and Building block is registered, and each one registered is
    there.
Done: each convert batch below.
  admin/workflows/convert/convert.ipynb, team_failures: every table the batch wrote passed its
    compare, and its folder is admin/workflows/convert/finished/team_failures/.

Before you go on, check that:

- `check_table_reference` says the table matches its Table reference;
- the Hive of `create_table(job_day)` holds dt under PARTITIONED BY and your LOCATION;
- `project.check()` says every Table reference is registered.

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
  What happened:  Table('mart.job_day'): partitioned_by names 'dt', which isn't one of its
                  columns.
...

Add `"dt": "string"` to `columns=`.

### A Key that names a column the table doesn't have

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

Name in `key=`, `partitioned_by=` and `does_not_add_up=` only columns from `columns=`,
spelled the same way.

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
  What happened:  sum_of(job_day.avg_minutes) adds up job_day.avg_minutes, which is listed in
                  does_not_add_up in its Table reference.
...
  Opt-out:        sum_of(job_day.avg_minutes, adds_up=True)

The Toolbox stops it with a Guard, a check that refuses a Statement that would give a wrong
result. Each day's average is right for its day, but a week's average isn't the sum of the
days', nor their average when the days had different numbers of runs. The table keeps
`job_day.minutes` and `job_day.runs`, which add up: total those over the week, and work the
average out from the totals. Keep the Opt-out for the rare call where a total really is what
you mean.

### A day written the other way

The Toolbox doesn't know how a table writes its days: it compares the value as you wrote it. A
day written like 2026-09-23, on a table that writes 20260923, matches no row, and nothing
stops it:

>>> wrong_day = statement(  # -> Statement
...     SELECT(region_costs.job_id),
...     FROM(region_costs),
...     WHERE(equals(region_costs.dt, "2026-09-23")),
... )
>>> run_query(wrong_day, query)  # -> DataFrame
Empty DataFrame
Columns: [job_id]
Index: []

When a result comes back empty, look at how the table writes the column: `first_look` shows a
few of its rows. Then write the day the table's way.

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
  What happened:  Table('ops.region_costs') was given date_partition=, which Toolbox 7.0
                  replaced.
...
  Usual fix:      Write partitioned_by=["dt"] where it said date_partition="dt", leave it out
                  where it said date_partition=None, and remove date_format=. CHANGES.md, under
                  7.0, says more.
...

Write the Table reference as the Usual fix says.

## Next

- Create a Saved table from a Table reference and write rows into it, from its own Table
  notebook: [Save a table](#save_a_table).
- Join your table to another without repeating rows, which is what `key=` is for:
  [Count, join and stay safe](#count_join_and_stay_safe).
- Rewrite some of a partitioned table's Partitions, the days or the regions it holds:
  [Rewrite some partitions](#rewrite_some_partitions).
- The gallery's Worked examples of [`Table`](examples.html#Table) and
  [`create_table`](examples.html#create_table), and a Saved table built and written step by
  step: [Worked example of a Saved table](examples.html#saved_table).
"""  # noqa: E501 - a file it writes, shown byte for byte as the Project writes it
