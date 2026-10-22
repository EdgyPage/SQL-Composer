"""Share Building blocks

For: Getting started

## Goal

Write a piece several Statements need once, and use it in each of them. The piece is a Derived
table: a Statement given a name with `derived`, which another Statement reads like a table, and
which the Hive writes at its top as `WITH name AS (...)`. Wrapped in a function, kept in a file
of its own in building_blocks/, it is a Building block, which any notebook of the Project
imports. `project.new_block` makes the file, from the Project's building_block Template.

## When you'd use it

- When two Statements need the same numbers, such as each job's runs, failed runs and minutes:
  written once, they can't be worked out two different ways, and a fix reaches them all.
- When a Statement grows long: in named steps, it can be read and checked a step at a time.
- When you add up before a join, as [Count, join and stay safe](#count_join_and_stay_safe)
  does: the added-up table is a Derived table.

## Steps

### Where the last how-to left the Project

[Count, join and stay safe](#count_join_and_stay_safe) left the Starter Example project with
its Table references filled in, as [Add your tables' references](#add_your_tables_references)
fills them. This how-to reads two of them, `ops.job_runs`, with its Aliases minutes and
failed, and `ops.jobs`. In your own Project they are there already; here, the steps make
them again, their comments left out:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
>>> project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"],
...                        query=example_database.query)
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

The steps run in a notebook in the Project's folder. Jupyter puts that folder on Python's
path, so `from references import ops` finds the Project's references/:

>>> from references import ops

### Name one step with derived

`derived` gives a Statement a name, and gives back a Table: its columns are what its `SELECT`
makes, checked like a Table reference's. Here, each job's runs and minutes on 2026-09-24:

>>> job_runs = ops.job_runs  # -> Table
>>> job_totals = derived("job_totals", statement(  # -> Table
...     SELECT(job_runs.job_id, AS(count_rows(), "runs"),
...            AS(sum_of(job_runs.duration_mins), "minutes")),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... ))
>>> job_totals
derived('job_totals', columns: job_id, runs, minutes)

Another Statement reads it with `FROM` or `JOIN`, like any table. Here, the minutes per team.
It needs no filter on the day of its own: the day is inside `job_totals`, and `ops.jobs` isn't
partitioned.

>>> per_team = statement(  # -> Statement
...     SELECT(ops.jobs.team, AS(sum_of(job_totals.minutes), "minutes")),
...     FROM(job_totals),
...     JOIN(ops.jobs, ON=equals(ops.jobs.job_id, job_totals.job_id)),
...     GROUP_BY(ops.jobs.team),
... )
>>> text = show_hive(per_team)  # -> str
WITH job_totals AS (
  SELECT
    job_runs.job_id,
    COUNT(*) AS runs,
    SUM(job_runs.duration_mins) AS minutes
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt = '2026-09-24'
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
>>> run(per_team, query=example_database.query)  # -> DataFrame
      team  minutes
0     data       50
1  finance       50

The Hive starts with `WITH job_totals AS (...)`, the step's own Hive; then the Statement reads
`job_totals` by name. A Derived table lives only inside the Statement that reads it: nothing
is saved in the warehouse.

### Make a Building block with project.new_block

A Building block is a function that gives back the Derived table, so every Statement that
needs it calls the function. What changes from one Statement to the next, such as the rows it
reads, becomes its argument. `project.new_block` makes its file, building_blocks/<name>.py,
from admin/templates/building_block.py, and registers it. Run it from the admin notebook
admin/new_block.ipynb, or any notebook of the Project:

>>> project.new_block("runs_per_job")
Wrote building_blocks/runs_per_job.py, from admin/templates/building_block.py:
fill in its <...> and TODO lines.

The file's docstring says what each `<...>` is for. Fill them in, or write over its code with
your own piece, as here: each job's runs, failed runs and minutes, for each day of the rows it
reads.

The file `building_blocks/runs_per_job.py`, after you fill it in:

    \"\"\"runs_per_job - each job's runs, failed runs and minutes for each dt it reads.

    Why: mart.daily_job_runs saves these numbers, and mart.team_day's notebook checks a day
    from them too, and writing them once here means the two can never count them two
    different ways.

    Every run counts, TEST runs and runs still going among them, since each one takes the
    cluster's time: a team that wants TEST runs left out says so in its own Statement.
    \"\"\"

    from sqlglot_composer import (
        AS, FROM, GROUP_BY, SELECT, WHERE, Condition, Table, count_rows, derived, statement,
        sum_of,
    )
    from references.ops__job_runs import failed, job_runs, minutes  # failed, minutes: Aliases


    def runs_per_job(reads: Condition) -> Table:
        \"\"\"One row per job for each dt of the rows `reads` picks: its runs, failed runs and
        minutes.

        `reads` is a condition on ops.job_runs, such as equals(job_runs.dt, "2026-09-24"):
        the table is partitioned by dt, so it must filter dt. dt is kept in GROUP_BY, so the
        counts of each dt stay apart when `reads` picks several, and in SELECT, so a write
        that reads this fills each dt's Partition from it.
        \"\"\"
        return derived(
            "runs_per_job",
            statement(
                SELECT(
                    job_runs.job_id,
                    job_runs.dt,
                    AS(count_rows(), "runs"),
                    AS(count_rows(where=failed), "failed_runs"),
                    AS(sum_of(minutes), "minutes"),
                ),
                FROM(job_runs),
                WHERE(reads),
                GROUP_BY(job_runs.job_id, job_runs.dt),
            ),
        )

Three things to notice:

- It imports what it reads: the Toolbox's names, and the Table reference of `ops.job_runs`
  with its two Aliases, from references/. A Building block's file imports only these, never
  another Building block's file or a notebook: [Keep the Project in
  order](#keep_the_project_in_order) says why.
- Its function is named as its file is, and so is its Derived table, `"runs_per_job"`: the
  Hive and the Lineage of every Statement that reads it call it the same.
- Its argument is a Condition, the rows it reads. The Table notebooks of
  [Save a table](#save_a_table) hand it the condition they call READS.

### Import it, and check it alone

A notebook imports it by its file's name:

>>> from building_blocks.runs_per_job import runs_per_job
>>> last_day = runs_per_job(equals(ops.job_runs.dt, "2026-09-24"))  # -> Table

`run` runs a Statement, and a Derived table is a step inside one, so check a block alone in
the smallest Statement that reads it: every column, with `all_columns`. Check a block like this
before you build on it:

>>> check_last_day = statement(SELECT(all_columns(last_day)), FROM(last_day))  # -> Statement
>>> run(check_last_day, query=example_database.query)  # -> DataFrame
   job_id          dt  runs  failed_runs  minutes
0       1  2026-09-24     2            0       50
1       2  2026-09-24     1            1       20
2       3  2026-09-24     1            0       30

### Use the same block in another Statement

Any Statement that needs each job's runs calls the same function. Here, each team's failed
runs over two days: the block keeps each day apart, and the Statement adds the days up:

>>> two_days = runs_per_job(between(ops.job_runs.dt, "2026-09-23", "2026-09-24"))  # -> Table
>>> failed_per_team = statement(  # -> Statement
...     SELECT(ops.jobs.team, AS(sum_of(two_days.failed_runs), "failed_runs")),
...     FROM(two_days),
...     JOIN(ops.jobs, ON=equals(ops.jobs.job_id, two_days.job_id)),
...     GROUP_BY(ops.jobs.team),
... )
>>> text = show_hive(failed_per_team)  # -> str
WITH runs_per_job AS (
  SELECT
    job_runs.job_id,
    job_runs.dt,
    COUNT(*) AS runs,
    COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs,
    SUM(job_runs.duration_mins) AS minutes
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  GROUP BY
    job_runs.job_id,
    job_runs.dt
)
SELECT
  jobs.team,
  SUM(runs_per_job.failed_runs) AS failed_runs
FROM runs_per_job
JOIN ops.jobs AS jobs
  ON jobs.job_id = runs_per_job.job_id
GROUP BY
  jobs.team;
>>> run(failed_per_team, query=example_database.query)  # -> DataFrame
      team  failed_runs
0     data            0
1  finance            2

Its Hive starts with the same `WITH runs_per_job AS (...)` as the check's, reading the days
this Statement gave it. The Alias failed became `job_runs.status = 'FAILED'`: an Alias is a
name for you, and the Hive says what it stands for.

### Keep one Building block to a file

Each Building block is a file of its own in building_blocks/, named as it is, made by
`project.new_block`, so the registry lists it and `project.check()` can find it. A second
block that reads this one, such as the busy jobs among its rows, is made the same way, with
`project.new_block("busy_jobs")`, and takes the Derived table `runs_per_job` gives back as its
argument, rather than importing building_blocks/runs_per_job.py: the notebook that reads both
imports both, builds `runs_per_job` once and hands it in.

## Check it worked

The registry lists the block's file, and `project.check()` finds nothing amiss:

>>> project.check()
Every Table folder, Table reference and Building block is registered, and each one registered is there.

The block, checked alone over the two days, gives the failed runs the team Statement adds up:

>>> by_job = run(statement(SELECT(all_columns(two_days)), FROM(two_days)),
...              query=example_database.query)
>>> by_team = run(failed_per_team, query=example_database.query)
>>> print(by_job["failed_runs"].sum(), by_team["failed_runs"].sum())
2 2

## Common mistakes

### Running a Derived table itself

`run` takes a Statement. A Derived table is a step to read, so on its own it stops:

>>> run(last_day, query=example_database.query)
Traceback (most recent call last):
...
TypeError:
  What happened:  run was given derived('runs_per_job', columns: job_id, dt, runs, failed_runs, minutes), which isn't a Statement.
...

Wrap it in the smallest Statement that reads it, as Import it, and check it alone does.

### A column the block doesn't make

A Derived table's columns are checked like a Table reference's, so a name it doesn't have
stops at once, with the names it has:

>>> last_day.failed
Traceback (most recent call last):
...
AttributeError: runs_per_job has no column 'failed'. Did you mean 'failed_runs'? Its columns are: job_id, dt, runs, failed_runs, minutes.

failed is an Alias of `ops.job_runs`, for the block to count with; what the block gives back
is the count, `"failed_runs"`.

### Making a Building block whose name is taken

`project.new_block` never writes over a file of yours. Run again with the same name, it stops:

>>> project.new_block("runs_per_job")
Traceback (most recent call last):
...
FileExistsError:
  What happened:  project.new_block("runs_per_job"): building_blocks/runs_per_job.py is already there, so nothing was made.
...

Open the file that is there, or give the new block a name of its own.

## Next

- Save a Statement's rows in a Saved table, from a Table notebook that can read this block:
  [Save a table](#save_a_table).
- Follow a column through the block, and the Saved tables built on it:
  [Follow lineage](#follow_lineage).
- Which file may import which, and the registry: [Keep the Project in
  order](#keep_the_project_in_order).
- The gallery's Worked example of [`derived`](examples.html#derived), and a long Statement
  built in named steps: [Worked example of a job in steps](examples.html#step_by_step).
"""
