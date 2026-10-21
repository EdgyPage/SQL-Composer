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

## Steps

### Import the Toolbox and name the tables

`ops.jobs` holds each job's team as it is today. `ops.job_owners` keeps each job's team on each
day. On a day when nothing has changed since, the two should agree.

>>> from sqlglot_composer import *
>>> jobs = example_database.jobs
>>> job_owners = example_database.job_owners

### Say what should agree

Write one Statement for each table, returning the columns that should agree, under the same
names. The Toolbox matches the two Statements' columns by name, not by their place in
`SELECT`, so `"job_id"` is compared with `"job_id"` and `"team"` with `"team"`:

>>> teams_today = statement(
...     SELECT(jobs.job_id, jobs.team),
...     FROM(jobs),
... )
>>> def teams_on(day):
...     return statement(
...         SELECT(job_owners.job_id, job_owners.team),
...         FROM(job_owners),
...         WHERE(equals(job_owners.dt, day)),
...     )

### The rows only the first table has

`EXCEPT` keeps the rows of the first Statement it is given that the second doesn't return. Two
rows count as the same when every column is alike:

>>> only_in_jobs = EXCEPT(teams_today, teams_on("2026-09-17"))
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
>>> run(only_in_jobs, send=example_database.send)
   job_id     team
0       3  finance

### The rows only the second table has

The same two Statements the other way round give what `ops.job_owners` held that `ops.jobs`
doesn't:

>>> only_in_owners = EXCEPT(teams_on("2026-09-17"), teams_today)
>>> run(only_in_owners, send=example_database.send)
   job_id  team
0       3  data

Together they say the two disagree on one job, job 3, report_build: `ops.jobs` says finance and
`ops.job_owners` said data on 2026-09-17. report_build moved from data to finance on
2026-09-18, and `ops.jobs` knows only today's team. Run only one direction, and you would see
only half of that.

### Count the rows of each

`EXCEPT` ignores how many times a row appears: a row held twice in one table and once in the
other counts as matching. So count each Statement's rows too:

>>> def rows_of(s):
...     counted = derived("counted", s)
...     return run(statement(SELECT(AS(count_rows(), "rows")), FROM(counted)),
...                send=example_database.send)
>>> rows_of(teams_today)
   rows
0     4
>>> rows_of(teams_on("2026-09-17"))
   rows
0     4

## Check it worked

On 2026-09-24, after report_build's move, `ops.job_owners` agrees with `ops.jobs`: both ways
come back empty.

>>> run(EXCEPT(teams_today, teams_on("2026-09-24")), send=example_database.send)
Empty DataFrame
Columns: [job_id, team]
Index: []
>>> run(EXCEPT(teams_on("2026-09-24"), teams_today), send=example_database.send)
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
  What happened:  EXCEPT(...)'s 2nd Statement doesn't return team, which the 1st returns, and returns owner_team, which the 1st doesn't.
...

Name the column alike in both with `AS`, as its fix says. A column of a different kind in
each, such as a number in one and text in the other, is refused the same way.

### Comparing a column with no value

`EXCEPT` counts two NULLs as alike, so a job with no owner in both tables agrees. `equals`
doesn't: in SQL nothing equals NULL. This is one place `EXCEPT` is the easier tool for
comparing tables, row by row.

### Reading every day of a big table

Each Statement passed to `EXCEPT` is checked like any other: its Date partition must be bounded
at both ends, as `teams_on` bounds `ops.job_owners` to one day. Reconcile a day at a time,
or a few days, and loop over the days in Python.

## Next

- [Keys, checked before each write](#keys): the columns that pick out exactly one row of a
  Saved table, which a reconciliation often checks too.
- [Check data quality](#check_data_quality): counts and checks on one table.
- The gallery's [`EXCEPT`](examples.html#EXCEPT), [`INTERSECT`](examples.html#INTERSECT),
  [`UNION`](examples.html#UNION) and [`UNION_ALL`](examples.html#UNION_ALL).
"""
