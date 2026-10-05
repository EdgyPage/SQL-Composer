"""The latest row per key, and the top N per group

For: Getting started

## Goal

Keep one whole row per key, such as each job's newest run, or the top N rows of each group,
such as each job's two longest runs. `row_number` numbers the rows of each group in the order
you choose, inside a Derived table, and the Statement that reads it keeps number 1, or numbers
1 to N.

## When you'd use it

- The latest row per key: each job's newest run, each customer's last order, each table's
  newest snapshot.
- The top N per group: each job's two longest runs, each team's three busiest days.
- Whenever you are tempted to take `max_of` of several columns to get "the newest row": each
  `max_of` picks its own row, so the columns can come from different rows. The first step
  shows it happen.

## Steps

### Import the Toolbox and name the table

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs

### See why max_of isn't the latest row

The question: what was each job's newest run, and how did it end? Run ids grow as runs start,
so the newest run is the one with the largest `job_runs.run_id`. The first thing most people
write takes the largest of each column:

>>> careless = statement(
...     SELECT(job_runs.job_id, AS(max_of(job_runs.run_id), "run_id"),
...            AS(max_of(job_runs.status), "status")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
>>> text = show_hive(careless)
SELECT
  job_runs.job_id,
  MAX(job_runs.run_id) AS run_id,
  MAX(job_runs.status) AS status
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.job_id;
>>> run(careless, send=example_database.send)
   job_id  run_id   status
0       1     104     TEST
1       2     102  SUCCESS
2       3     103  SUCCESS

It runs, and it is wrong. Job 2's newest run, 102, FAILED, but `max_of(job_runs.status)` takes
the largest status in alphabetical order from any of job 2's runs, SUCCESS. Job 1 shows TEST,
from run 99, though run 104 succeeded. Each `max_of` picks its own row.

### Number each job's runs, newest first

`row_number` numbers the rows of each group from 1:

- `PARTITION_BY=` names the column whose values make the groups, here each job. The word is
  SQL's; it has nothing to do with a table's Date partition.
- `ORDER_BY=` says the order to number them in. `descending` makes the largest come first, so
  each job's newest run gets 1.

The number is a calculation, so it needs a name with `AS`, and it goes in a Derived table,
for the next Statement to read:

>>> numbered = derived("numbered", statement(
...     SELECT(job_runs.job_id, job_runs.run_id, job_runs.status,
...            AS(row_number(PARTITION_BY=job_runs.job_id,
...                          ORDER_BY=descending(job_runs.run_id)), "newest_first")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... ))

[sqlglot_composer only]
sqlglot Composer's Example database runs only part of Hive, and not `row_number`. Pasted into
your own notebook with sqlglot Composer, running a Statement that reads `numbered`, here and in
the steps below, stops with this message:

>>> run(statement(SELECT(all_columns(numbered)), FROM(numbered)), send=example_database.send)
Traceback (most recent call last):
...
RuntimeError:
  What happened:  The Example database can't run this Hive: its executor has no window functions such as row_number.
...

So the results below that read `numbered`, or `ranked` and `oldest_first` like it, are what
Hive gives at work, worked out in pandas for this page, as their label says. The Hive is the
Hive your warehouse runs.
[end]

Check the numbering alone first, with a Statement that reads every column of it:

>>> numbering = statement(SELECT(all_columns(numbered)), FROM(numbered))
>>> text = show_hive(numbering)
WITH numbered AS (
  SELECT
    job_runs.job_id,
    job_runs.run_id,
    job_runs.status,
    ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id DESC) AS newest_first
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
)
SELECT
  numbered.job_id,
  numbered.run_id,
  numbered.status,
  numbered.newest_first
FROM numbered;
>>> run(numbering, send=example_database.send)
   job_id  run_id   status  newest_first
0       1      95  SUCCESS             4
1       1      99     TEST             3
2       1     101  SUCCESS             2
3       1     104  SUCCESS             1
4       2      96  SUCCESS             3
5       2      98     None             2
6       2     102   FAILED             1
7       3      97   FAILED             2
8       3     103  SUCCESS             1

Each job's runs are numbered 1, 2, 3, ... from its newest.

### Keep number 1

The Statement that reads `numbered` keeps the rows numbered 1: one whole row per job.

>>> latest = statement(
...     SELECT(numbered.job_id, numbered.run_id, numbered.status),
...     FROM(numbered),
...     WHERE(equals(numbered.newest_first, 1)),
... )
>>> text = show_hive(latest)
WITH numbered AS (
  SELECT
    job_runs.job_id,
    job_runs.run_id,
    job_runs.status,
    ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id DESC) AS newest_first
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
)
SELECT
  numbered.job_id,
  numbered.run_id,
  numbered.status
FROM numbered
WHERE
  numbered.newest_first = 1;
>>> run(latest, send=example_database.send)
   job_id  run_id   status
0       1     104  SUCCESS
1       2     102   FAILED
2       3     103  SUCCESS

Job 2's newest run is 102, and it FAILED, as it should be: the status comes from the same row
as the run.

### Keep the top N of each group

Keep numbers 1 to N instead, with `at_most`. Here, each job's two longest runs: number them
from the longest. Two runs of job 3 took 30 minutes each, so `ORDER_BY=` takes a list, and a
second column breaks the tie, the newest of the two first. Without one, which of two tied rows
gets the lower number can change from one run to the next.

>>> ranked = derived("ranked", statement(
...     SELECT(job_runs.job_id, job_runs.run_id, job_runs.duration_mins,
...            AS(row_number(PARTITION_BY=job_runs.job_id,
...                          ORDER_BY=[descending(job_runs.duration_mins),
...                                    descending(job_runs.run_id)]), "longest_first")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... ))
>>> top_two = statement(
...     SELECT(ranked.job_id, ranked.run_id, ranked.duration_mins),
...     FROM(ranked),
...     WHERE(at_most(ranked.longest_first, 2)),
... )
>>> text = show_hive(top_two)
WITH ranked AS (
  SELECT
    job_runs.job_id,
    job_runs.run_id,
    job_runs.duration_mins,
    ROW_NUMBER() OVER (
      PARTITION BY job_runs.job_id
      ORDER BY job_runs.duration_mins DESC, job_runs.run_id DESC
    ) AS longest_first
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
)
SELECT
  ranked.job_id,
  ranked.run_id,
  ranked.duration_mins
FROM ranked
WHERE
  ranked.longest_first <= 2;
>>> run(top_two, send=example_database.send)
   job_id  run_id  duration_mins
0       1      95             12
1       1     104             40
2       2      96             18
3       2     102             20
4       3      97             30
5       3     103             30

Two rows per job, or fewer for a job with fewer runs. `ORDER_BY` with `LIMIT`, as in
[Count and add up per group](#count_and_add_up_per_group), keeps the top N rows of the whole
result; `row_number` keeps the top N of each group.

## Check it worked

Check that each job comes back once: one row per job, as many rows as jobs that ran.
[sqlglot_composer only]
On the Example database this run stops, as above; `newest` here is the pandas result. At work
the Statement runs, and the check is the same.
[end]

>>> newest = run(latest, send=example_database.send)
>>> newest["job_id"].is_unique
True

And check each job's run against the largest run id worked out another way, with `max_of`,
which is right for one column on its own. Each side becomes a dict, from each job to its run,
so the order the rows came back in doesn't matter:

>>> newest_ids = statement(
...     SELECT(job_runs.job_id, AS(max_of(job_runs.run_id), "run_id")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
>>> text = show_hive(newest_ids)
SELECT
  job_runs.job_id,
  MAX(job_runs.run_id) AS run_id
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.job_id;
>>> largest = run(newest_ids, send=example_database.send)
>>> dict(zip(largest["job_id"], largest["run_id"])) == dict(zip(newest["job_id"], newest["run_id"]))
True

## Common mistakes

### Testing the row number in the same Statement

A row's number is given last, after the rows are picked, so Hive can't test it in the `WHERE`
of the Statement that makes it:

>>> in_one_go = statement(
...     SELECT(job_runs.job_id, job_runs.run_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           equals(row_number(PARTITION_BY=job_runs.job_id,
...                             ORDER_BY=descending(job_runs.run_id)), 1)),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  WHERE has ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id DESC) = 1, which numbers rows.
...

Number the rows in a Derived table, then keep number 1 in the Statement that reads it, as the
steps do.

### Numbering from the wrong end

Without `descending`, `ORDER_BY=` numbers from the smallest, so number 1 is each job's oldest
run, not its newest. Nothing stops it:

>>> oldest_first = derived("oldest_first", statement(
...     SELECT(job_runs.job_id, job_runs.run_id, job_runs.status,
...            AS(row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id),
...               "position")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... ))
>>> first_runs = statement(
...     SELECT(oldest_first.job_id, oldest_first.run_id, oldest_first.status),
...     FROM(oldest_first),
...     WHERE(equals(oldest_first.position, 1)),
... )
>>> run(first_runs, send=example_database.send)
   job_id  run_id   status
0       1      95  SUCCESS
1       2      96  SUCCESS
2       3      97   FAILED

Each job's first run of the two days. Its Hive numbers with `ORDER BY job_runs.run_id ASC`, where
numbering newest first says DESC.

### A row number without a name

>>> unnamed = derived("unnamed", statement(
...     SELECT(job_runs.job_id, job_runs.run_id,
...            row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id))),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... ))
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  SELECT has a calculation with no name: ROW_NUMBER() OVER (PARTITION BY job_runs.job_id ORDER BY job_runs.run_id DESC).
...

Name it with `AS`, so the Statement that reads it can test it by that name.

## Next

- Keep the numbering step as a Building block every Statement can call:
  [Reusable Derived tables](#reusable_derived_tables).
- Each job's newest row from a table that keeps a full copy of itself every day:
  [Look things up as of a day](#look_things_up_as_of_a_day).
- A rank, the row before, or a rolling sum, which the Toolbox doesn't write as Hive:
  [Finish in pandas](#finish_in_pandas).
- The gallery's Worked examples of [`row_number`](examples.html#row_number) and
  [`descending`](examples.html#descending), and the careless and fixed Statements side by side:
  [latest and top N](examples.html#latest_and_top_n).
"""

import pandas as pd

from sqlglot_composer import (
    FROM, SELECT, WHERE, all_columns, between, example_database, run, statement,
)

# sqlglot Composer's Example database can't run row_number, so the page and the doctest get
# each Statement's result from these, worked out in pandas from every run of the two days.
# Spark Composer's runs the Hive itself, and its result must match.


def every_run() -> pd.DataFrame:
    """Every run of the two days, read with a Statement the Example database can run."""
    job_runs = example_database.job_runs
    return run(statement(SELECT(all_columns(job_runs)), FROM(job_runs),
                         WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"))),
               send=example_database.send)


def numbered_runs(by: list[str], largest_first: bool) -> pd.DataFrame:
    """Every run, numbered within its job in the order of the columns `by`, from 1."""
    runs = every_run().sort_values(by, ascending=not largest_first, kind="stable")
    return runs.assign(number=runs.groupby("job_id").cumcount() + 1)


def in_order(rows: pd.DataFrame) -> pd.DataFrame:
    """The rows as the Example database gives them: by the first column, then the next, ..."""
    return rows.sort_values(list(rows.columns)).reset_index(drop=True)


def numbering_in_pandas() -> pd.DataFrame:
    rows = numbered_runs(["run_id"], largest_first=True).rename(columns={"number": "newest_first"})
    return in_order(rows[["job_id", "run_id", "status", "newest_first"]])


def latest_in_pandas() -> pd.DataFrame:
    rows = numbered_runs(["run_id"], largest_first=True)
    return in_order(rows[rows["number"] == 1][["job_id", "run_id", "status"]])


def top_two_in_pandas() -> pd.DataFrame:
    rows = numbered_runs(["duration_mins", "run_id"], largest_first=True)
    return in_order(rows[rows["number"] <= 2][["job_id", "run_id", "duration_mins"]])


def first_runs_in_pandas() -> pd.DataFrame:
    rows = numbered_runs(["run_id"], largest_first=False)
    return in_order(rows[rows["number"] == 1][["job_id", "run_id", "status"]])
