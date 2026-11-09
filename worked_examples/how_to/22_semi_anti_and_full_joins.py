"""Semi-, anti- and full joins

For: Intermediate

## Goal

Keep the rows that have a match in another table, each once, with `SEMI_JOIN`; keep the rows
that have none with `ANTI_JOIN`; and compare two records of the same things, row for row, with
`FULL_JOIN`. On the way, ask Hive for a map join, a join that copies a small table to every
worker, with `broadcast=True`, and see why `RIGHT_JOIN` is refused.

## When you'd use it

- If you want the rows that have a match in another table, such as the jobs that had an event
  on a day or the runs that raised an alert, use `SEMI_JOIN`. A plain `JOIN` gives a row for
  each match, so a job with two events comes out twice; `SEMI_JOIN` keeps it once, and adds
  none of the other table's columns.
- If you want the rows with no match, such as the jobs with no event on a day or the rows a
  copy is missing, use `ANTI_JOIN`.
- If you have two records that should agree, such as the runs `ops.job_runs` holds and the
  runs the scheduler says it started, compare them with `FULL_JOIN`. Each run comes out once,
  whichever side has it.
- If you haven't yet, read [Build and run a first
  statement](#build_and_run_a_first_statement) and [Count, join and stay
  safe](#count_join_and_stay_safe) first, which shows `JOIN`, `LEFT_JOIN` and the
  repeated-rows Warning.

## Steps

### 1. Start from the Intermediate Example project

Goal: a Project to work in. An Example project is a Project made for the Example database's
tables, filled in, to read and copy from.

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

Done when the folder you work in holds the Project's admin/, references/ and tables/. Then
step 2.

### 2. Add the two records' Table references

Goal: Table references, the files that describe one table each, for the two records the full
join compares. The Project reads ops.job_events and ops.job_owners already. The full join
compares `ops.job_runs` with `ops.scheduler_runs`, the scheduler's own record of the runs it
started, which should match it run for run but doesn't quite. Add their Table references, as
[Add your tables' references](#add_your_tables_references) shows:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from warehouse import connect, query, execute
>>> connect(example_database)
>>> project.add_references(["ops.job_runs", "ops.scheduler_runs"], query=query)
Wrote references/ops__job_runs.py and references/ops__scheduler_runs.py: fill in their TODO
    lines.
...
Wrote references/ops.py: from references import ops gives ops.job_events, ops.job_owners,
    ops.job_runs, ops.region_budgets, ops.region_costs, ops.scheduler_runs and ops.team_notes.
Restart the kernel of a notebook that imported references, to see a table added since.

Done when references/ holds ops__job_runs.py and ops__scheduler_runs.py. Then step 3.

### 3. Fill in their TODO lines

Goal: each table's Key, the columns that name one of its rows. Each has a row per run, named
by its run_id:

The file `references/ops__job_runs.py`, after you fill it in:

    \"\"\"ops.job_runs - one row per run of a job.\"\"\"
    from sqlglot_composer import Table

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
    )

The file `references/ops__scheduler_runs.py`, after you fill it in:

    \"\"\"ops.scheduler_runs - one row per run the scheduler started.\"\"\"
    from sqlglot_composer import Table

    scheduler_runs = Table(
        "ops.scheduler_runs",
        columns={"run_id": "bigint", "job_id": "bigint", "dt": "string"},
        partitioned_by=["dt"],
        key=["run_id"],
    )

Done when both files say `key=["run_id"]`. Then step 4.

### 4. Import the tables

Goal: the four tables, by name, from the Database ops, a named group of tables:

>>> from references import ops
>>> job_events, job_owners = ops.job_events, ops.job_owners  # -> Table, Table
>>> job_runs, scheduler_runs = ops.job_runs, ops.scheduler_runs  # -> Table, Table

Done when the imports run without an error. Then step 5.

### 5. See JOIN repeat the jobs

Goal: see why a plain join is the wrong tool here. Which of the jobs ops.job_owners lists on
2026-09-24 had an event that day? Join the events, and a job comes out once for each event:

>>> repeated = statement(  # -> Statement
...     SELECT(job_owners.job_id, job_owners.team),
...     FROM(job_owners),
...     JOIN(job_events, ON=all_of(equals(job_events.job_id, job_owners.job_id),
...                                equals(job_events.dt, "2026-09-24")),
...          many_matches=True),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
... )
>>> run_query(repeated, query)  # -> DataFrame
   job_id     team
0       1     data
1       1     data
2       2  finance

Done when job 1 comes out twice. Then step 6.

### 6. Keep each job with an event once, with SEMI_JOIN

Goal: each job with an event, once. `SEMI_JOIN` keeps each row that has a match, once, however
many rows match it, so it needs no `many_matches=` and gives no repeated-rows Warning. It is
written `LEFT SEMI JOIN`. The events' day goes inside its `ON=`, since only `ON=` may read its
table's columns:

>>> with_an_event = statement(  # -> Statement
...     SELECT(job_owners.job_id, job_owners.team),
...     FROM(job_owners),
...     SEMI_JOIN(job_events, ON=all_of(equals(job_events.job_id, job_owners.job_id),
...                                     equals(job_events.dt, "2026-09-24"))),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
... )
>>> text = show_hive(with_an_event)
SELECT
  job_owners.job_id,
  job_owners.team
FROM ops.job_owners AS job_owners
LEFT SEMI JOIN ops.job_events AS job_events
  ON job_events.job_id = job_owners.job_id AND job_events.dt = '2026-09-24'
WHERE
  job_owners.dt = '2026-09-24';
>>> run_query(with_an_event, query)
   job_id     team
0       1     data
1       2  finance

Pasted into your own notebook, this `run_query`, and the one of `with_an_event` under Check it
worked, stops with a RuntimeError saying the Example database can't run a `LEFT SEMI JOIN`:
sqlglot's own small executor doesn't know it. The result above is worked out in pandas
instead. Hive at work runs it.

Since a semi join never repeats rows, the rows keep their Key, ops.job_owners' job and day:
a write of these rows into a Saved table with that Key is let through, as
[Keys](#keys) explains.

Done when jobs 1 and 2 each come out once. Then step 7.

### 7. Keep each job with no event, with ANTI_JOIN

Goal: each job with no event that day. `ANTI_JOIN` keeps the rows that have no match. Hive 3
has no anti join of its own, so the Toolbox writes a `LEFT JOIN`, then a `WHERE` that keeps the
rows where the column `ON=` matched is NULL: a job with an event has its job_id there.

>>> no_event = statement(  # -> Statement
...     SELECT(job_owners.job_id, job_owners.team),
...     FROM(job_owners),
...     ANTI_JOIN(job_events, ON=all_of(equals(job_events.job_id, job_owners.job_id),
...                                     equals(job_events.dt, "2026-09-24"))),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
... )
>>> text = show_hive(no_event)
SELECT
  job_owners.job_id,
  job_owners.team
FROM ops.job_owners AS job_owners
LEFT JOIN ops.job_events AS job_events
  ON job_events.job_id = job_owners.job_id AND job_events.dt = '2026-09-24'
WHERE
  job_owners.dt = '2026-09-24' AND job_events.job_id IS NULL;
>>> run_query(no_event, query)
   job_id     team
0       3  finance
1       4      web

The events' day is inside `ON=` here too: an event on another day doesn't count as a match.

Done when jobs 3 and 4 come out. Then step 8.

### 8. Read each record's days in a Derived table

Goal: each side of the full join, its Partitions already filtered. `FULL_JOIN` pairs the rows
that match and keeps the rows of each side that have none, with NULL in the other side's
columns. Each side keeps all of its rows, so its partitions can't be filtered in `WHERE`,
which would throw away the other side's unmatched rows, nor in `ON=`, which keeps every row
anyway: each side reads its own days in a Derived table first, a Statement named so another
Statement can read from it.

>>> recorded = derived("recorded", statement(  # -> Table
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... ))
>>> started = derived("started", statement(  # -> Table
...     SELECT(scheduler_runs.run_id),
...     FROM(scheduler_runs),
...     WHERE(between(scheduler_runs.dt, "2026-09-23", "2026-09-24")),
... ))

Done when `recorded` and `started` build without a refusal. Then step 9.

### 9. Compare the two records with FULL_JOIN

Goal: every run once, with where it was found. `fill_null` takes the run_id from whichever
side has one, and `if_else` says where each run was found:

>>> both_records = statement(  # -> Statement
...     SELECT(AS(fill_null(recorded.run_id, started.run_id), "run_id"),
...            AS(if_else(is_null(started.run_id), "only in job_runs",
...                       if_else(is_null(recorded.run_id), "only in scheduler_runs",
...                               "in both")), "found")),
...     FROM(recorded),
...     FULL_JOIN(started, ON=equals(started.run_id, recorded.run_id)),
... )
>>> text = show_hive(both_records)
WITH recorded AS (
  SELECT
    job_runs.run_id
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
), started AS (
  SELECT
    scheduler_runs.run_id
  FROM ops.scheduler_runs AS scheduler_runs
  WHERE
    scheduler_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
)
SELECT
  COALESCE(recorded.run_id, started.run_id) AS run_id,
  CASE
    WHEN started.run_id IS NULL
    THEN 'only in job_runs'
    ELSE CASE WHEN recorded.run_id IS NULL THEN 'only in scheduler_runs' ELSE 'in both' END
  END AS found
FROM recorded
FULL JOIN started
  ON started.run_id = recorded.run_id;
>>> run_query(both_records, query)
   run_id                   found
0      95                 in both
1      96                 in both
2      97                 in both
3      98                 in both
4      99        only in job_runs
5     100  only in scheduler_runs
6     101                 in both
7     102                 in both
8     103                 in both
9     104                 in both

Run 99, a TEST run started by hand, never went through the scheduler; run 100 was started but
never reached `ops.job_runs`.

Done when runs 99 and 100 are each found on one side only. Then step 10.

### 10. Keep only the differences

Goal: the runs only one side holds. A `WHERE` on either side's columns is refused after a
`FULL_JOIN`, since it would throw away rows the join kept, unless it is `is_null(...)`, which
keeps a side's rows with no match. So the runs only one side holds:

>>> differences = statement(  # -> Statement
...     SELECT(AS(recorded.run_id, "in_job_runs"), AS(started.run_id, "in_scheduler_runs")),
...     FROM(recorded),
...     FULL_JOIN(started, ON=equals(started.run_id, recorded.run_id)),
...     WHERE(any_of(is_null(recorded.run_id), is_null(started.run_id))),
... )
>>> run_query(differences, query)
   in_job_runs  in_scheduler_runs
0          NaN              100.0
1         99.0                NaN

pandas shows a whole-number column with a missing value as decimals, with NaN for NULL.

A `FULL_JOIN`'s rows have no Key the Toolbox can see, since either side's run_id may be NULL:
to write them into a Saved table, a real table your own Statements write, group them by the
run_id that `fill_null` makes, with `GROUP_BY(fill_null(recorded.run_id, started.run_id))`,
which gives them that Key.

Done when the result holds runs 100 and 99 alone. Then step 11.

### 11. Send the "map_joins" Session setting

Goal: Hive ready to read a map join's hint. `broadcast=True`, on `JOIN`, `LEFT_JOIN`,
`SEMI_JOIN` or `ANTI_JOIN`, asks for a map join: the small table, here one day of
ops.job_owners, is copied whole to every worker, so each worker matches the big table's rows
where they are, without first sorting them and sending them across the cluster. The Toolbox
writes it as a hint after `SELECT`: a comment, `/*+ ... */`, that Hive reads as a request.
Hive ignores the hint unless the Session setting "map_joins", a set of Hive SET lines that
hold for the rest of the session, is sent first, since one of its lines sets
hive.ignore.mapjoin.hint to false, so send it before the Statement:

>>> run_execute(hive_settings("map_joins"), execute)
execute: SET hive.auto.convert.join=true
execute: SET hive.auto.convert.join.noconditionaltask=true
execute: SET hive.ignore.mapjoin.hint=false

Done when execute shows the three SET lines. Then step 12.

### 12. Ask for a map join with broadcast=True

Goal: a join that copies the small table to every worker. Give the small table's join
`broadcast=True`:

>>> per_team = statement(  # -> Statement
...     SELECT(job_owners.team, AS(count_rows(), "events")),
...     FROM(job_events),
...     JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_events.job_id),
...                                equals(job_owners.dt, job_events.dt),
...                                equals(job_owners.dt, "2026-09-24")),
...          broadcast=True),
...     WHERE(equals(job_events.dt, "2026-09-24")),
...     GROUP_BY(job_owners.team),
... )
>>> text = show_hive(per_team)
SELECT /*+ MAPJOIN(job_owners) */
  job_owners.team,
  COUNT(*) AS events
FROM ops.job_events AS job_events
JOIN ops.job_owners AS job_owners
  ON job_owners.job_id = job_events.job_id
  AND job_owners.dt = job_events.dt
  AND job_owners.dt = '2026-09-24'
WHERE
  job_events.dt = '2026-09-24'
GROUP BY
  job_owners.team;
>>> run_query(per_team, query)
      team  events
0     data       2
1  finance       1

The rows are the same with it or without it: it only changes how the work is done. Usually
you don't need the hint, though: with "map_joins" sent, Hive makes map joins by itself, from
the tables' sizes and Statistics, what the warehouse has counted about them. Ask for it only
for a table you know is small: copied to every worker, a big table can run them out of
memory.

Done when the Hive starts `SELECT /*+ MAPJOIN(job_owners) */`. Then check it worked, below.

## Check it worked

Every job ops.job_owners lists on the day either had an event or hadn't, so the jobs
`SEMI_JOIN` keeps and the jobs `ANTI_JOIN` keeps add up to all of them:

>>> every_job = statement(
...     SELECT(job_owners.job_id),
...     FROM(job_owners),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
... )
>>> len(run_query(every_job, query))
4
>>> with_one = len(run_query(with_an_event, query))
>>> without = len(run_query(no_event, query))
>>> with_one + without
4

And the `FULL_JOIN` gave 10 rows: the 8 runs in both, and one only in each.

Before you go on, check that:

- the jobs `SEMI_JOIN` keeps and the jobs `ANTI_JOIN` keeps add up to 4, every job of the day;
- `both_records` gives 10 rows, one for each run;
- `differences` gives runs 99 and 100 alone.

## Common mistakes

### Reading a SEMI_JOIN's table outside its ON=

`SEMI_JOIN` adds none of the joined table's columns, so asking for one is refused. To show each
event's type, `JOIN` the events, a row for each; to test it, put the test in `ON=`.

>>> event_types = statement(
...     SELECT(job_owners.job_id, job_events.event_type),
...     FROM(job_owners),
...     SEMI_JOIN(job_events, ON=all_of(equals(job_events.job_id, job_owners.job_id),
...                                     equals(job_events.dt, "2026-09-24"))),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  SELECT reads job_events.event_type, a column of job_events, which SEMI_JOIN
                  only tests.
...

### Filtering an ANTI_JOIN's partitions in WHERE

Every column of an `ANTI_JOIN`'s table is NULL in the rows it keeps, so `WHERE` can't test
one, its partition columns included. They go inside `ON=`, as in the steps:

>>> careless = statement(
...     SELECT(job_owners.job_id),
...     FROM(job_owners),
...     ANTI_JOIN(job_events, ON=equals(job_events.job_id, job_owners.job_id)),
...     WHERE(equals(job_owners.dt, "2026-09-24"), equals(job_events.dt, "2026-09-24")),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  WHERE reads job_events.dt, a column of job_events, which ANTI_JOIN only tests.
...

### A WHERE on a FULL_JOIN's table

Testing a side's column in `WHERE` throws away the rows the other side has and it lacks, so
it is refused. Pick each side's rows in its own Derived table instead.

>>> only_late_runs = statement(
...     SELECT(recorded.run_id, AS(started.run_id, "started")),
...     FROM(recorded),
...     FULL_JOIN(started, ON=equals(started.run_id, recorded.run_id)),
...     WHERE(more_than(recorded.run_id, 100)),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  WHERE has recorded.run_id > 100, a condition on recorded, and
                  FULL_JOIN(started) keeps the rows of both sides that have no match.
...

### Writing a RIGHT_JOIN

A RIGHT JOIN keeps every row of the table it joins. The Toolbox writes none: swap the two
tables, putting the one whose every row you want in `FROM`, and `LEFT_JOIN` the other.

>>> RIGHT_JOIN(job_owners, ON=equals(job_owners.job_id, job_events.job_id))
Traceback (most recent call last):
...
ValueError:
  What happened:  RIGHT_JOIN(job_owners, ...): the Toolbox doesn't write a RIGHT JOIN.
...

## Next

- [Count, join and stay safe](#count_join_and_stay_safe): `JOIN`, `LEFT_JOIN` and the
  repeated-rows Warning.
- [Keys](#keys): which joins keep a table's Key.
- [Reconcile two tables](#reconcile_two_tables): `EXCEPT`, the other way to compare two
  records, row by row.
- The gallery's Worked examples of [`SEMI_JOIN`](examples.html#SEMI_JOIN),
  [`ANTI_JOIN`](examples.html#ANTI_JOIN), [`FULL_JOIN`](examples.html#FULL_JOIN) and
  [`RIGHT_JOIN`](examples.html#RIGHT_JOIN).
"""

import pandas as pd

from sqlglot_composer import FROM, SELECT, WHERE, equals, example_database, run_query, statement


# The Example database can't run a LEFT SEMI JOIN, so the page and the doctest get
# with_an_event's result from this, worked out in pandas from two Statements it can run.


def with_an_event_in_pandas() -> pd.DataFrame:
    job_owners, job_events = example_database.job_owners, example_database.job_events
    owners = run_query(statement(SELECT(job_owners.job_id, job_owners.team), FROM(job_owners),
                                 WHERE(equals(job_owners.dt, "2026-09-24"))),
                       example_database.query)
    events = run_query(statement(SELECT(job_events.job_id), FROM(job_events),
                                 WHERE(equals(job_events.dt, "2026-09-24"))),
                       example_database.query)
    kept = owners[owners["job_id"].isin(events["job_id"])]
    return kept.sort_values("job_id").reset_index(drop=True)
