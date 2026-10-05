"""Generate Statements in a loop

For: Getting started

## Goal

Build many Statements from one function and a loop, instead of copying the same lines and
changing a word in each. You make one Statement per team, one per table, and one per entry of
a dict of settings; run them all, gather their results in one pandas DataFrame, and print
their Hive.

## When you'd use it

- When you would otherwise copy a Statement and change one value: a team, a status, a day.
- When the same question is asked of several tables.
- For a set of daily checks, where adding a check should be one more line of settings, not
  one more Statement to write.

A Statement is a Python value, built by Python functions, so a loop builds Statements as it
builds anything else. Check first that you need several: when only a value changes, one
Statement with `GROUP_BY` often answers for every value at once.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> import pandas as pd
>>> jobs = example_database.jobs
>>> job_runs = example_database.job_runs
>>> run_alerts = example_database.run_alerts
>>> job_events = example_database.job_events

### Check whether one Statement does it

How many runs failed per team? One Statement, grouped by team, answers for every team at once,
in one query:

>>> failed_per_team = statement(
...     SELECT(jobs.team, AS(count_rows(), "failed_runs")),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           equals(job_runs.status, "FAILED")),
...     GROUP_BY(jobs.team),
... )
>>> run(failed_per_team, send=example_database.send)
      team  failed_runs
0  finance            2

Teams with no failed run don't appear: only finance had one.

A loop is for when each Statement must be its own: its own result to send somewhere, its own
table, or its own columns and conditions.

### One Statement per team

Each team wants its own list of failed runs, in a file of its own. Write the Statement once, as
a function of the team:

>>> def team_failures(team):
...     return statement(
...         SELECT(job_runs.run_id, jobs.job_name, job_runs.dt),
...         FROM(job_runs),
...         JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...         WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...               equals(job_runs.status, "FAILED"),
...               equals(jobs.team, team)),
...     )

Then loop over the three teams in `ops.jobs`, keeping each team's Statement in a dict, by
team:

>>> per_team = {}
>>> for team in ["data", "finance", "web"]:
...     per_team[team] = team_failures(team)
>>> run(per_team["finance"], send=example_database.send)
   run_id      job_name          dt
0      97  report_build  2026-09-23
1     102  invoice_sync  2026-09-24

Run each, and save each team's result in its own CSV file:

>>> for team in per_team:
...     result = run(per_team[team], send=example_database.send)
...     result.to_csv(f"failed_runs_{team}.csv", index=False)

A team with no failed runs gets a file with only the column names, so every team gets a file
each day.

### Print every Statement's Hive

Put the Statements in a list, and `show_hive` prints them all, each headed by its place in
the list, ready to paste into another program:

>>> team_statements = list(per_team.values())
>>> text = show_hive(team_statements)
-- 1 of 3: team_statements[0]
SELECT
  job_runs.run_id,
  jobs.job_name,
  job_runs.dt
FROM ops.job_runs AS job_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = job_runs.job_id
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  AND job_runs.status = 'FAILED'
  AND jobs.team = 'data';
<BLANKLINE>
-- 2 of 3: team_statements[1]
SELECT
  job_runs.run_id,
  jobs.job_name,
  job_runs.dt
FROM ops.job_runs AS job_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = job_runs.job_id
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  AND job_runs.status = 'FAILED'
  AND jobs.team = 'finance';
<BLANKLINE>
-- 3 of 3: team_statements[2]
SELECT
  job_runs.run_id,
  jobs.job_name,
  job_runs.dt
FROM ops.job_runs AS job_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = job_runs.job_id
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  AND job_runs.status = 'FAILED'
  AND jobs.team = 'web';

The three differ only in their last line, the team.

### One Statement per table

How many rows does each table hold per day? The question is the same for every table whose
Date partition is dt, so the function takes the table itself, a Table reference, as an
argument:

>>> def rows_per_day(table, first_day, last_day):
...     return statement(
...         SELECT(table.dt, AS(count_rows(), "row_count")),
...         FROM(table),
...         WHERE(between(table.dt, first_day, last_day)),
...         GROUP_BY(table.dt),
...     )

Loop over a dict of the tables, by name, and add each table's name to its result with
`result.insert`, so the results can go in one DataFrame:

>>> tables = {"ops.job_runs": job_runs, "ops.run_alerts": run_alerts,
...           "ops.job_events": job_events}
>>> results = []
>>> for name, table in tables.items():
...     result = run(rows_per_day(table, "2026-09-23", "2026-09-24"),
...                  send=example_database.send)
...     result.insert(0, "table", name)
...     results.append(result)
>>> pd.concat(results, ignore_index=True)
            table          dt  row_count
0    ops.job_runs  2026-09-23          5
1    ops.job_runs  2026-09-24          4
2  ops.run_alerts  2026-09-23          2
3  ops.run_alerts  2026-09-24          7
4  ops.job_events  2026-09-23          4
5  ops.job_events  2026-09-24          3

`pd.concat` stacks the DataFrames one under another, and `ignore_index=True` numbers the rows
again from 0.

### One Statement per entry of a dict of settings

A set of daily checks counts, on one day, the rows of a table whose column holds a given
value. Each check is a few settings, so each is an entry of a dict: its name, then its table,
its column and its value.

>>> CHECKS = {
...     "failed_runs": {"table": job_runs, "column": "status", "value": "FAILED"},
...     "high_alerts": {"table": run_alerts, "column": "severity", "value": "high"},
...     "retries": {"table": job_events, "column": "event_type", "value": "retry"},
... }

The function names the column as text, so it reads it from the Table reference with Python's
`getattr`: `getattr(job_runs, "status")` is `job_runs.status`.

>>> def matching_rows(table, column, value, day):
...     return statement(
...         SELECT(AS(count_rows(), "matching")),
...         FROM(table),
...         WHERE(equals(table.dt, day), equals(getattr(table, column), value)),
...     )

The loop builds and runs each check, and gathers one row per check:

>>> found = []
>>> for name, setting in CHECKS.items():
...     check = matching_rows(setting["table"], setting["column"], setting["value"],
...                           "2026-09-24")
...     result = run(check, send=example_database.send)
...     found.append({"check": name, "matching": result["matching"][0]})
>>> pd.DataFrame(found)
         check  matching
0  failed_runs         1
1  high_alerts         2
2      retries         0

To add a check, add one line to `CHECKS`; the function and the loop stay as they are. At work,
the settings can come from a file your team keeps, such as a JSON file read with Python's
json module, with each table's name looked up in a dict like `tables` above.

## Check it worked

The per-team Statements together find the same failed runs as the one grouped Statement: two.

>>> sum(len(run(team_statement, send=example_database.send))
...     for team_statement in per_team.values())
2

And the loops made one Statement per team, per table and per check:

>>> len(per_team), len(results), len(found)
(3, 3, 3)

## Common mistakes

### A setting that names a column the table doesn't have

A typo in a setting is caught when the Statement is built, with the column's likely name and
the table's columns:

>>> matching_rows(job_runs, "statsu", "FAILED", "2026-09-24")
Traceback (most recent call last):
...
AttributeError: job_runs has no column 'statsu'. Did you mean 'status'? Its columns are: run_id, job_id, status, duration_mins, avg_retry_secs, dt.

### A table without a Date partition in the loop

`rows_per_day` reads each table's `table.dt`, so a table with no days, such as `ops.jobs`, stops the
loop at that table:

>>> rows_per_day(jobs, "2026-09-23", "2026-09-24")
Traceback (most recent call last):
...
AttributeError: jobs has no column 'dt'. Its columns are: job_id, job_name, team, region.

Loop only over the tables the question fits, or give each table its own settings.

### A setting that looks for a missing value

A check for runs with no status can't use `equals` with None: in SQL nothing equals a missing
value, so it would always count 0. A Guard stops it, and with it the loop:

>>> matching_rows(job_runs, "status", None, "2026-09-24")
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  equals(job_runs.status, None) compares with None.
...

Use `is_null` for such a check: give it a function of its own, or a setting that says which
condition to build.

## Next

- Catch a refusal inside a loop, note it and go on, and when an opt-out is right:
  [Guards, Warnings and opt-outs](#guards_warnings_and_opt_outs).
- Write one Saved table's days in a loop: [Backfill a range of days](#backfill_a_range_of_days).
- The gallery's [`all_columns`](examples.html#all_columns) entry, which gives a Table
  reference's columns as a list to loop over.
"""
