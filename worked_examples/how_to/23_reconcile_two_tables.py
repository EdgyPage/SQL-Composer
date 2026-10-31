"""Reconcile two tables

For: Intermediate

## Goal

Find every row where two tables that should agree don't: `EXCEPT` gives the rows of one
Statement that another doesn't return, so running it both ways round lists what only the first
table has, then what only the second has. When both come back empty, the tables agree.

## When you'd use it

When two tables should hold the same rows: a Saved table and the table it was copied from, the
same table before and after a change to its Statement, or your team's table and another team's
record of the same thing.

It needs [Build and run a first statement](#build_and_run_a_first_statement) and [Share
Building blocks](#share_building_blocks), which starts with Derived tables.

## Steps

### Start from the Intermediate Example project

Work in a copy of the Intermediate Example project, at its top: copy
`example_projects/intermediate/` from the download to a folder of your own, copy the
`sqlglot_composer` folder into it, as a Project holds it, and open a notebook there. This page
makes the same copy in its first step, from the download the Toolbox came in, into the folder
it runs in, which Python's path holds already, as Jupyter's does for a notebook's own folder:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

`ops.job_owners`, which the Project reads already, keeps each job's team on each day.
`ops.jobs` holds each job's team as it is today: add its Table reference, as [Add your
tables' references](#add_your_tables_references) shows. Its TODO lines can wait, since
`EXCEPT` compares whole rows and reads no Key:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from warehouse import query, execute
>>> project.add_references(["ops.jobs"], query=query)
Wrote references/ops__jobs.py: fill in its TODO lines.
Wrote references/ops.py: from references import ops gives ops.job_events, ops.job_owners,
    ops.jobs, ops.region_budgets, ops.region_costs and ops.team_notes.
Restart the kernel of a notebook that imported references, to see a table added since.
>>> from references import ops
>>> jobs, job_owners = ops.jobs, ops.job_owners  # -> Table, Table

On a day when no job has changed teams since, the two should agree.

### Say what should agree

Write one Statement for each table, returning the columns that should agree, under the same
names. The Toolbox matches the two Statements' columns by name, not by their place in
`SELECT`, so `"job_id"` is compared with `"job_id"` and `"team"` with `"team"`:

>>> teams_today = statement(  # -> Statement
...     SELECT(jobs.job_id, jobs.team),
...     FROM(jobs),
... )
>>> def teams_on(day: str) -> Statement:
...     return statement(
...         SELECT(job_owners.job_id, job_owners.team),
...         FROM(job_owners),
...         WHERE(equals(job_owners.dt, day)),
...     )

### The rows only the first table has

`EXCEPT` keeps the rows of the first Statement it is given that the second doesn't return. Two
rows count as the same when every column is alike:

>>> only_in_jobs = EXCEPT(teams_today, teams_on("2026-09-17"))  # -> Statement
>>> text = show_hive(only_in_jobs)
SELECT
  jobs.job_id,
  jobs.team
FROM ops.jobs AS jobs
EXCEPT
SELECT
  job_owners.job_id,
  job_owners.team
FROM ops.job_owners AS job_owners
WHERE
  job_owners.dt = '2026-09-17';
>>> run_query(only_in_jobs, query)  # -> DataFrame
   job_id     team
0       3  finance

### The rows only the second table has

The same two Statements the other way round give what `ops.job_owners` held that `ops.jobs`
doesn't:

>>> only_in_owners = EXCEPT(teams_on("2026-09-17"), teams_today)  # -> Statement
>>> run_query(only_in_owners, query)
   job_id  team
0       3  data

Together they say the two disagree on one job, job 3, report_build: `ops.jobs` says finance and
`ops.job_owners` said data on 2026-09-17. report_build moved from data to finance on
2026-09-18, and `ops.jobs` knows only today's team. Run only one direction, and you would see
only half of that.

### Count the rows of each

`EXCEPT` ignores how many times a row appears: a row held twice in one table and once in the
other counts as matching. So count each Statement's rows too, reading it as a Derived table:

>>> import pandas as pd
>>> def rows_of(s: Statement) -> pd.DataFrame:
...     counted = derived("counted", s)
...     return run_query(statement(SELECT(AS(count_rows(), "rows")), FROM(counted)), query)
>>> rows_of(teams_today)
   rows
0     4
>>> rows_of(teams_on("2026-09-17"))
   rows
0     4

## Check it worked

On 2026-09-24, after report_build's move, `ops.job_owners` agrees with `ops.jobs`: both ways
come back empty.

>>> run_query(EXCEPT(teams_today, teams_on("2026-09-24")), query)
Empty DataFrame
Columns: [job_id, team]
Index: []
>>> run_query(EXCEPT(teams_on("2026-09-24"), teams_today), query)
Empty DataFrame
Columns: [job_id, team]
Index: []

## Common mistakes

### A column named differently in each

Say the second Statement names its team `"owner_team"`. The Toolbox matches columns by name, so
it refuses the pair as you build it, naming the column, where Hive, which matches them by their
place, would compare them without a word:

>>> EXCEPT(teams_today, statement(
...     SELECT(job_owners.job_id, AS(job_owners.team, "owner_team")),
...     FROM(job_owners),
...     WHERE(equals(job_owners.dt, "2026-09-17")),
... ))
Traceback (most recent call last):
...
ValueError:
  What happened:  EXCEPT(...)'s 2nd Statement doesn't return team, which the 1st returns, and
                  returns owner_team, which the 1st doesn't.
...

Name the column alike in both with `AS`, as its fix says. A column of a different kind in
each, such as a number in one and text in the other, is refused the same way.

### Comparing a column with no value

`EXCEPT` counts two NULLs as alike, so a job with no owner in both tables agrees. `equals`
doesn't: in SQL nothing equals NULL. This is one place `EXCEPT` is the easier tool for
comparing tables, row by row.

### Reading every partition of a big table

Each Statement passed to `EXCEPT` is checked like any other: a read of a partitioned table must
filter at least one of its partition columns, as `teams_on` filters `ops.job_owners` to one day.
Reconcile a few partitions at a time, and loop over them in Python.

## Next

- [Semi-, anti- and full joins](#semi_anti_and_full_joins): `FULL_JOIN`, which pairs the two
  records' rows and says which side each was found in.
- [Keys](#keys): the columns that name one row of a table, which a reconciliation often
  checks too.
- [Check data quality](#check_data_quality): counts and checks on one table.
- The gallery's [`EXCEPT`](examples.html#EXCEPT), [`INTERSECT`](examples.html#INTERSECT),
  [`UNION`](examples.html#UNION) and [`UNION_ALL`](examples.html#UNION_ALL).
"""
