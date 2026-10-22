"""Count, join and stay safe

For: Getting started

## Goal

Answer "how many, and how much, per something", such as runs per job or minutes per team, and
put two tables' columns side by side without counting any row twice. `GROUP_BY` makes one row
per group, `count_rows` and `sum_of` work out its numbers, `HAVING` keeps some groups, and
`ORDER_BY` with `LIMIT` keeps the top N. `JOIN` and `LEFT_JOIN` bring in another table. On the
way you meet the three ways the Toolbox stops a Statement, or warns about it, as you build it:
a Guard, a Warning and a Load limit, and when each one's opt-out is right.

## When you'd use it

Whenever the answer is a table of totals rather than a list of rows: a daily count for a
dashboard, the busiest jobs, each team's minutes. The warehouse does the counting, so only the
totals come back to your notebook. And whenever a Statement stops with a message, or builds
with a Warning: read it before you change anything.

## Steps

### Where the last how-to left the Project

[Build and run a first statement](#build_and_run_a_first_statement) built its Statements on
the Project as [Add your tables' references](#add_your_tables_references) left it: three Table
references filled in, and Aliases in two of them. This page has no Project, so it makes one
with the same three files; in your own, leave these steps out:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py.
Next: write your two functions, query and execute, in warehouse.py.
>>> from warehouse import query, execute
>>> project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"], query=query)
Wrote references/ops__jobs.py, references/ops__job_runs.py and references/ops__run_alerts.py: fill in their TODO lines.
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs and ops.run_alerts.
Restart the kernel of a notebook that imported references, to see a table added since.

The file `references/ops__job_runs.py`, after you fill it in:

    \"\"\"ops.job_runs - one row per run of a job, on the day it ran.\"\"\"
    from sqlglot_composer import Table, equals

    job_runs = Table(
        "ops.job_runs",
        columns={
            "run_id": "bigint",
            "job_id": "bigint",
            "status": "string",
            "duration_mins": "int",
            "avg_retry_secs": "double",
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=["run_id"],
        does_not_add_up=["avg_retry_secs"],
        descriptions={
            "status": "SUCCESS / FAILED / TEST, NULL while running",
        },
    )

    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from references.ops__job_runs import job_runs, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
    # gives back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = job_runs.status
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(job_runs.status, <value>)

    minutes = job_runs.duration_mins
    failed = equals(job_runs.status, "FAILED")

The file `references/ops__jobs.py`, after you fill it in:

    \"\"\"ops.jobs - one row per job: its name, the team that owns it and its region.\"\"\"
    from sqlglot_composer import Table

    jobs = Table(
        "ops.jobs",
        columns={
            "job_id": "bigint",
            "job_name": "string",
            "team": "string",
            "region": "string",
        },
        key=["job_id"],
        does_not_add_up=[],
    )

    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from references.ops__jobs import jobs, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
    # gives back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = jobs.job_name
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(jobs.job_name, <value>)

The file `references/ops__run_alerts.py`, after you fill it in:

    \"\"\"ops.run_alerts - one row per alert a run raised.\"\"\"
    from sqlglot_composer import Table, equals

    run_alerts = Table(
        "ops.run_alerts",
        columns={
            "alert_id": "bigint",
            "run_id": "bigint",
            "severity": "string",
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=["alert_id"],
        does_not_add_up=[],
        descriptions={
            "severity": "low / high",
        },
    )

    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from references.ops__run_alerts import run_alerts, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
    # gives back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = run_alerts.severity
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(run_alerts.severity, <value>)

    high = equals(run_alerts.severity, "high")

### Add the two tables this how-to also reads

Two more of the Example database's tables show how the Toolbox keeps a Statement safe:
ops.region_budgets, each job's budget for a day, in the region it is billed in, partitioned by
that region; and ops.team_notes, the notes each team wrote about its jobs, not partitioned at
all. Add their Table references, before any notebook imports references:

>>> project.add_references(["ops.region_budgets", "ops.team_notes"], query=query)
Wrote references/ops__region_budgets.py and references/ops__team_notes.py: fill in their TODO lines.
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs, ops.region_budgets, ops.run_alerts and ops.team_notes.
Restart the kernel of a notebook that imported references, to see a table added since.

A job has one budget in each region it is billed in, so the Key of ops.region_budgets is the
job and the region together:

The file `references/ops__region_budgets.py`, after you fill it in:

    \"\"\"ops.region_budgets - one row per job and region: its budget for a day there.\"\"\"
    from sqlglot_composer import Table

    region_budgets = Table(
        "ops.region_budgets",
        columns={
            "job_id": "bigint",
            "budget_cents": "bigint",
            "region": "string",
        },
        partitioned_by=["region"],
        key=["job_id", "region"],
        does_not_add_up=[],
        descriptions={
            "budget_cents": "the most a day of the job should cost there",
        },
    )

    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from references.ops__region_budgets import region_budgets, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
    # gives back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = region_budgets.job_id
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(region_budgets.job_id, <value>)

Nothing names one note of ops.team_notes: a team may write two on one day. So it has no Key,
and `key=None` is the right answer; only its TODO comment goes:

The file `references/ops__team_notes.py`, after you fill it in:

    \"\"\"ops.team_notes - one row per note a team wrote about its jobs.\"\"\"
    from sqlglot_composer import Table

    team_notes = Table(
        "ops.team_notes",
        columns={
            "team": "string",
            "note": "string",
            "written_on": "string",
        },
        key=None,
        does_not_add_up=[],
        descriptions={
            "written_on": "the day the note was written, as yyyy-MM-dd",
        },
    )

    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from references.ops__team_notes import team_notes, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
    # gives back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = team_notes.team
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(team_notes.team, <value>)

### Name the tables

`from references import ops` gives every table, and the Aliases `failed` and `minutes` come
from their table's own file. Short names keep the Statements below easy to read:

>>> from references import ops
>>> from references.ops__job_runs import failed, minutes
>>> jobs = ops.jobs  # -> Table
>>> job_runs = ops.job_runs  # -> Table
>>> run_alerts = ops.run_alerts  # -> Table

### Count every row

`count_rows()` counts rows, and `sum_of` adds up a Column, here `minutes`, the Alias of
`job_runs.duration_mins`. Each gives a Column, a calculation, and every calculation in
`SELECT` needs a name for its column in the result, which `AS` gives:

>>> all_runs = statement(  # -> Statement
...     SELECT(AS(count_rows(), "runs"), AS(sum_of(minutes), "minutes")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> text = show_hive(all_runs)
SELECT
  COUNT(*) AS runs,
  SUM(job_runs.duration_mins) AS minutes
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24';
>>> run(all_runs, query=query)
   runs  minutes
0     9      180

Without `GROUP_BY`, all the rows read are one group: one row comes back.

### One row per job

`GROUP_BY(job_runs.job_id)` makes one group per job. `SELECT` then holds the columns you group
by, and calculations over each group, such as `min_of` and `max_of`. `count_rows` takes
`where=`, a Condition, to count only the rows where it holds while the group keeps every row:
here the Alias `failed`:

>>> per_job = statement(  # -> Statement
...     SELECT(
...         job_runs.job_id,
...         AS(count_rows(), "runs"),
...         AS(count_rows(where=failed), "failed_runs"),
...         AS(sum_of(minutes), "minutes"),
...         AS(max_of(minutes), "longest"),
...     ),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
>>> text = show_hive(per_job)
SELECT
  job_runs.job_id,
  COUNT(*) AS runs,
  COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs,
  SUM(job_runs.duration_mins) AS minutes,
  MAX(job_runs.duration_mins) AS longest
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.job_id;
>>> run(per_job, query=query)
   job_id  runs  failed_runs  minutes  longest
0       1     4            0       67       40
1       2     3            1       53       20
2       3     2            1       60       30

`COUNT(CASE WHEN ... THEN 1 END)` counts the rows where the Condition holds. Putting `failed`
in `WHERE` instead would drop the other runs before counting, so `"runs"` would count only
failed runs too.

### Keep some groups, or the top N

`WHERE` picks rows before they are counted, so it can't test a count. `HAVING` tests each
group after `GROUP_BY` has counted it, and repeats the calculation itself, `count_rows()`:
SQL works `HAVING` out before `SELECT` has named anything. Here, the jobs with 3 runs or more:

>>> busy_jobs = statement(  # -> Statement
...     SELECT(job_runs.job_id, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
...     HAVING(at_least(count_rows(), 3)),
... )
>>> run(busy_jobs, query=query)
   job_id  runs
0       1     4
1       2     3

`ORDER_BY` sorts the result, smallest first, or largest first with `descending`, and `LIMIT`
keeps the first rows. `ORDER_BY` is worked out after `SELECT`, so it sorts by the name. Here,
the two jobs with the most minutes:

>>> top_two = statement(  # -> Statement
...     SELECT(job_runs.job_id, AS(sum_of(minutes), "minutes")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
...     ORDER_BY(descending("minutes")),
...     LIMIT(2),
... )
>>> run(top_two, query=query)
   job_id  minutes
0       1       67
1       3       60

### Join on the other table's Key

`JOIN` adds another table's columns to each row, matched by its `ON=` Condition. Each run names
one job, and `jobs.job_id` is the Key of ops.jobs, so each run meets exactly one row of it:
nothing is repeated, and counting per team after the join is safe:

>>> per_team = statement(  # -> Statement
...     SELECT(jobs.team, AS(count_rows(), "runs"), AS(sum_of(minutes), "minutes")),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(jobs.team),
... )
>>> text = show_hive(per_team)
SELECT
  jobs.team,
  COUNT(*) AS runs,
  SUM(job_runs.duration_mins) AS minutes
FROM ops.job_runs AS job_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = job_runs.job_id
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  jobs.team;
>>> run(per_team, query=query)
      team  runs  minutes
0     data     4       67
1  finance     5      113

Nine runs, and 180 minutes, as before the join.

### Read the repeated-rows Warning

Now the runs' alerts. `run_alerts.run_id` isn't the Key of ops.run_alerts: a run with two
alerts matches two rows, so the run comes out twice, and its minutes are added twice. The
Toolbox builds the Statement, since sometimes one row per match is what you want, but warns at
the JOIN. `run_alerts` is partitioned too, so it gets its own filter on `run_alerts.dt`:

>>> careless_total = statement(  # -> Statement
...     SELECT(AS(sum_of(minutes), "minutes"), AS(count_rows(), "alerts")),
...     FROM(job_runs),
...     JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id)),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           between(run_alerts.dt, "2026-09-23", "2026-09-24")),
... )
>>> run(careless_total, query=query)
   minutes  alerts
0      210       9

The Statement builds, with the repeated-rows Warning. In a notebook it shows under the cell, at
your own line, and on this page under the step that builds it; it doesn't stop anything. It
says:

- What happened: JOIN(run_alerts) matches on run_id, but a run_alerts row is told apart only
  by its Key (alert_id).
- Why it matters: Each row before the join is repeated once per matching run_alerts row, so
  sums and counts over it may come out too big.
- Usual fix: Group run_alerts first so it has one row per value you join on, and join that.
- Opt-out: `JOIN(run_alerts, ON=..., many_matches=True)`

And so it is: the nine runs took 180 minutes, but here they come out as 210. Runs 97 and 103
are added twice, run 101 three times, and the four runs with no alert not at all, since `JOIN`
keeps only rows that match.

### Add up first, with a Derived table

The Warning's usual fix: give ops.run_alerts one row per run before joining it. `derived` gives
a Statement a name, so another Statement can read it like a table: a Derived table, which is a
Table too. This one groups the alerts by run, and the Toolbox takes its GROUP_BY column as its
Key. `LEFT_JOIN` keeps every run, those with no alert too, with NULL in the joined columns, and
`fill_null` turns that NULL into 0:

>>> alerts_per_run = derived("alerts_per_run", statement(  # -> Table
...     SELECT(run_alerts.run_id, AS(count_rows(), "alerts")),
...     FROM(run_alerts),
...     WHERE(between(run_alerts.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(run_alerts.run_id),
... ))
>>> fixed_total = statement(  # -> Statement
...     SELECT(AS(sum_of(minutes), "minutes"),
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
>>> run(fixed_total, query=query)
   minutes  alerts
0      180       9

No Warning, and the totals are right. The Derived table is written at the top of the Hive, as
`WITH alerts_per_run AS (...)`. [Share Building blocks](#share_building_blocks) keeps one in a
file of its own, for every notebook that needs it.

### Find the rows with no match

A row `LEFT_JOIN` keeps for having no match has NULL in every joined column, so `is_null` on
one of them keeps just those rows. Here, the jobs that never ran on the two days, from the runs
counted per job first, so each job meets at most one row:

>>> runs_per_job = derived("runs_per_job", statement(  # -> Table
...     SELECT(job_runs.job_id, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... ))
>>> never_ran = statement(  # -> Statement
...     SELECT(jobs.job_id, jobs.job_name),
...     FROM(jobs),
...     LEFT_JOIN(runs_per_job, ON=equals(runs_per_job.job_id, jobs.job_id)),
...     WHERE(is_null(runs_per_job.job_id)),
... )
>>> run(never_ran, query=query)
   job_id    job_name
0       4  cache_warm

A plain `JOIN` would have left cache_warm out, with nothing to say it was missing.

### Know the three ways the Toolbox stops or warns

You have met two already. The three kinds, each checked as you build a Statement:

- a Guard refuses a Statement that would silently give a wrong answer, such as a sum that
  counts some rows twice. It stops with a `GuardRefused`;
- a Warning lets the Statement through, but says why a number may come out wrong, where the
  risky Statement is often the one you meant, as the repeated-rows Warning above;
- a Load limit refuses a Statement that would cost the cluster or your notebook too much,
  though its answer would have been right. It stops with a `LoadRefused`.

Every message has the same four parts: what happened, why it matters, the usual fix, and the
opt-out, a keyword to add to one of your calls, or "none" when there is no way around it. Each
of the next three steps meets one on the two tables added above.

### A Load limit: read only the Partitions you need

ops.region_budgets is partitioned by region, so a Statement that names no region would read
every Partition:

>>> statement(
...     SELECT(ops.region_budgets.job_id, ops.region_budgets.budget_cents),
...     FROM(ops.region_budgets),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.LoadRefused:
  What happened:  FROM(region_budgets) reads ops.region_budgets, but filters none of its partition columns: region.
...

The usual fix is the right one: name the regions to read, here both, with `is_in`. A region
isn't a day: a partition column can be any column, and a Statement filters it as it filters
any other:

>>> budgets = ops.region_budgets  # -> Table
>>> every_budget = statement(  # -> Statement
...     SELECT(budgets.job_id, budgets.region, budgets.budget_cents),
...     FROM(budgets),
...     WHERE(is_in(budgets.region, ["eu", "us"])),
... )
>>> run(every_budget, query=query)
   job_id region  budget_cents
0       1     eu           150
1       2     eu           200
2       3     us           350
3       4     eu            50

The opt-out, `reads_all_partitions=True` on `FROM`, is right only for a small table you truly
need whole.

### A Guard: a condition on the LEFT_JOIN's table goes in ON=

Every job, with its budget in eu, keeping the jobs that have none there. `WHERE` runs after the
join, and a job with no eu budget has NULL in every column `LEFT_JOIN` brought in, so a
Condition on them in `WHERE` would throw that job away again, and the `LEFT_JOIN` would quietly
act as a `JOIN`. A Guard stops it:

>>> statement(
...     SELECT(jobs.job_name, budgets.budget_cents),
...     FROM(jobs),
...     LEFT_JOIN(budgets, ON=equals(budgets.job_id, jobs.job_id)),
...     WHERE(equals(budgets.region, "eu")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  WHERE has region_budgets.region = 'eu', a condition on region_budgets, which LEFT_JOIN brought in.
...

It warns at the `LEFT_JOIN` too: matched on `budgets.job_id` alone, a job meets its budget in every
region, and the region is the other column of the Key. The Guard's usual fix mends both: move
the Condition into `ON=`, beside the join's own, with `all_of`. It filters the partition column
there too, and the join now matches on the whole Key:

>>> eu_budgets = statement(  # -> Statement
...     SELECT(jobs.job_name, budgets.budget_cents),
...     FROM(jobs),
...     LEFT_JOIN(budgets, ON=all_of(equals(budgets.job_id, jobs.job_id),
...                                  equals(budgets.region, "eu"))),
... )
>>> run(eu_budgets, query=query)
       job_name  budget_cents
0    cache_warm          50.0
1  invoice_sync         200.0
2  nightly_load         150.0
3  report_build           NaN

report_build is billed in us, so it has no eu budget, and is kept, with NaN. The opt-out,
`keeps_only_matches=True`, is almost never right: if you want only the jobs that have a match,
`JOIN` says so plainly.

### A Warning: a table with no Key

ops.team_notes has no Key, so the Toolbox can't know how many notes a team has, and warns at
any join onto it. Each job, beside its team's notes:

>>> notes = ops.team_notes  # -> Table
>>> job_notes = statement(  # -> Statement
...     SELECT(jobs.job_name, notes.note),
...     FROM(jobs),
...     JOIN(notes, ON=equals(notes.team, jobs.team)),
... )
>>> run(job_notes, query=query)
       job_name                                          note
0    cache_warm            cache_warm is paused until October
1  invoice_sync       invoice_sync's bill comes in a day late
2  invoice_sync        report_build came over from data today
3  nightly_load          ask ana before changing nightly_load
4  nightly_load  nightly_load runs long at the end of a month
5  report_build       invoice_sync's bill comes in a day late
6  report_build        report_build came over from data today

This time one row per matching note is the point, and nothing is added up over it, so the
Warning's opt-out is right. `many_matches=True`, on the call the message names, says so to the
Toolbox and to the next reader, and the Warning goes:

>>> job_notes = statement(  # -> Statement
...     SELECT(jobs.job_name, notes.note),
...     FROM(jobs),
...     JOIN(notes, ON=equals(notes.team, jobs.team), many_matches=True),
... )

### Switch on the row limit

Two Load limits are always on: a partitioned table must have a partition column filtered, and
`ORDER_BY` needs a `LIMIT`, as Common mistakes shows. A third is off until you switch it on,
since only you know how much your notebook can take. `set_load_limits(rows=...)` adds a LIMIT
to every query that has none of its own, and refuses a result that fills it, since it was then
probably cut short. At work, `set_load_limits(rows=100000)`, in the first cell of a notebook,
is a good start. The Example database is tiny, so this page sets 5:

>>> set_load_limits(rows=5)  # -> dict[str, int | None]
{'rows': 5}
>>> run(statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... ), query=query)
Traceback (most recent call last):
...
sqlglot_composer.refusals.LoadRefused:
  What happened:  run(...) got back 5 rows, exactly the automatic LIMIT set by set_load_limits(rows=...).
...

The usual fix is to ask for fewer rows. Its opt-out, `returns_all_rows=True` on
`statement(...)`, is right when you know the result fits in your notebook. `set_load_limits()`
with nothing in it switches the limit off again:

>>> set_load_limits()  # -> dict[str, int | None]
{'rows': None}

### Know when an opt-out is right

Each opt-out says "I know, and I mean it". Add one only when the message's "why it matters"
doesn't apply to what you want:

- `many_matches=True` on a `JOIN` or `LEFT_JOIN`: when one row per match is the point, such as
  listing each note beside its job, and nothing over it is added up.
- `reads_all_partitions=True` on `FROM` or a join: for a small partitioned table you truly need
  every Partition of.
- `returns_all_rows=True` on `statement(...)`: when you know the result fits in your notebook.
- `adds_up=True` on a sum: when a column the Toolbox takes for one that doesn't add up really
  does. For a column a Table reference lists in `does_not_add_up=[...]`, fix the list instead.
- `sorts_everything=True` on `ORDER_BY`: for a result you know is small.
- `keeps_only_matches=True` on `LEFT_JOIN`: almost never; write `JOIN`.

When the opt-out would hide a mistake, make the fix instead.

## Check it worked

A join that doesn't repeat rows keeps the totals of the table in `FROM`: the runs and minutes
per team add up to those of every run, and `fixed_total` has them too:

>>> totals = run(all_runs, query=query)  # -> DataFrame
>>> teams = run(per_team, query=query)  # -> DataFrame
>>> int(teams["runs"].sum()) == int(totals["runs"][0])
True
>>> int(teams["minutes"].sum()) == int(run(fixed_total, query=query)["minutes"][0]) == 180
True

And the warehouse's counts per job match the same counts made in pandas from the rows:

>>> every_run = run(statement(  # -> DataFrame
...     SELECT(job_runs.job_id, job_runs.duration_mins),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... ), query=query)
>>> from_hive = run(per_job, query=query)  # -> DataFrame
>>> every_run.groupby("job_id")["duration_mins"].sum().to_dict() == dict(
...     zip(from_hive["job_id"], from_hive["minutes"]))
True

## Common mistakes

### A column that isn't grouped

Each row of the result is one group, so every column in `SELECT` must be in `GROUP_BY` or
inside a calculation. Here `job_runs.status` is neither, and one job's runs have several
statuses:

>>> statement(
...     SELECT(job_runs.job_id, job_runs.status, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  SELECT has job_runs.status, which GROUP_BY leaves out.
...

Add it to `GROUP_BY` for one row per job and status. A calculation with no `AS` stops the same
way: name it, as in `AS(count_rows(), "runs")`.

### Adding up a column that doesn't add up

`job_runs.avg_retry_secs` is listed in `does_not_add_up=` in its Table reference, so a total
of it stops as you build it:

>>> statement(
...     SELECT(AS(sum_of(job_runs.avg_retry_secs), "wait")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  sum_of(job_runs.avg_retry_secs) adds up job_runs.avg_retry_secs, which is listed in does_not_add_up in its Table reference.
...

If you leave `does_not_add_up=[]` empty, nothing stops it, and the total means nothing.

### Sorting without a LIMIT

Sorting a whole result makes the warehouse put every row in order before any comes back, which
is slow on a big table. A Load limit stops a sort with no `LIMIT`:

>>> statement(
...     SELECT(job_runs.job_id, AS(sum_of(minutes), "minutes")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
...     ORDER_BY(descending("minutes")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.LoadRefused:
  What happened:  ORDER_BY has no LIMIT.
...

For a top N, add `LIMIT`. To sort every row, sort in pandas once the result is back, with
`.sort_values(...)`.

### Silencing the Warning instead of fixing the join

`many_matches=True`, pasted to make the repeated-rows Warning go away, leaves the total just as
wrong, and now nothing says so:

>>> silenced = statement(
...     SELECT(AS(sum_of(minutes), "minutes")),
...     FROM(job_runs),
...     JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id), many_matches=True),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           between(run_alerts.dt, "2026-09-23", "2026-09-24")),
... )
>>> run(silenced, query=query)
   minutes
0      210

To add up, add up before you join, as `fixed_total` does.

### Forgetting the joined table's partition filter

Each partitioned table a Statement reads needs a filter on one of its own partition columns,
the joined one too:

>>> statement(
...     SELECT(job_runs.run_id, run_alerts.alert_id),
...     FROM(job_runs),
...     JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id), many_matches=True),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.LoadRefused:
  What happened:  JOIN(run_alerts, ON=...) reads ops.run_alerts, but filters none of its partition columns: dt.
...

### The opt-out on the wrong call

An opt-out goes on the call the message names, such as `JOIN(notes, ON=..., many_matches=True)`.
On another call, Python itself refuses the keyword, and the Warning stays:

>>> statement(
...     SELECT(jobs.job_name, notes.note),
...     FROM(jobs),
...     JOIN(notes, ON=equals(notes.team, jobs.team)),
...     many_matches=True,
... )
Traceback (most recent call last):
...
TypeError: statement() got an unexpected keyword argument 'many_matches'

Copy the opt-out from the message as it is written.

## Next

- Keep a Derived table such as `alerts_per_run` in a file of its own, and use it in every
  notebook that needs it: [Share Building blocks](#share_building_blocks).
- Save a count like `per_job` as a table of your own, a Partition at a time:
  [Save a table](#save_a_table).
- More joins, such as rows of one table with no match in another:
  [Semi-, anti- and full joins](#semi_anti_and_full_joins).
- The gallery's Worked examples of [`GROUP_BY`](examples.html#GROUP_BY),
  [`HAVING`](examples.html#HAVING), [`JOIN`](examples.html#JOIN),
  [`LEFT_JOIN`](examples.html#LEFT_JOIN) and [`set_load_limits`](examples.html#set_load_limits),
  and the traps beside their fixes: [repeated rows](examples.html#repeated_rows),
  [a LEFT_JOIN then WHERE](examples.html#left_join_then_where) and
  [jobs that never ran](examples.html#jobs_that_never_ran).
"""
