"""The latest row of each group, and the top N

For: Intermediate

## Goal

Keep one whole row of each group, such as each job's last run, or the top N rows of each
group, such as each job's three longest runs. `row_number` numbers the rows of each group in
the order you choose, inside a Derived table, and the Statement that reads it keeps number 1,
or numbers 1 to N.

## When you'd use it

- The latest row of each group: each job's last run, each customer's last order, each
  product's newest price.
- The top N of each group: each job's three longest runs, each team's busiest days.
- Whenever you are tempted to take `max_of` of several columns to get "the newest row": each
  `max_of` picks its own row, so the columns can come from different rows. The first step
  shows it happen.

It needs the Getting started how-tos [Build and run a first
Statement](#build_and_run_a_first_statement), [Count, join and stay
safe](#count_join_and_stay_safe) and [Share Building blocks](#share_building_blocks), which
starts with Derived tables.

## Steps

### Start from the Intermediate Example project

Work in a copy of the Intermediate Example project, at its top: copy
`example_projects/intermediate/` from the download to a folder of your own, copy the
`sqlglot_composer` folder into it, as a Project holds it, and open a notebook there. This page
makes the same copy in its first step, from the download the Toolbox came in, and runs its
steps there:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

Then import the Toolbox, the Project's `ops` Database and your query. `ops.job_events` holds
what each job's runs did: a `"start"` row when a run starts, then `"retry"`, `"finish"` or
`"fail"`, with the minutes since the run started. Its Table reference ends with an Alias,
`ends_a_run`, the events that end a run, imported beside the table it is about:

>>> from sqlglot_composer import *
>>> from references import ops
>>> from references.ops__job_events import ends_a_run
>>> from warehouse import query
>>> job_events = ops.job_events  # -> Table
>>> ends_a_run  # -> Condition
job_events.event_type IN ('finish', 'fail')

A run's minutes are on the row that ends it, and event ids grow as events come in, so the
last run of each job is its run-ending row with the largest `job_events.event_id`. This
how-to reads the last week of the Example database, 2026-09-18 to 2026-09-24:

>>> week_ends = [between(job_events.dt, "2026-09-18", "2026-09-24"), ends_a_run]

### See why max_of isn't the latest row

The question: how long did each job's last run take? The first thing most people write takes
the largest of each column:

>>> careless = statement(  # -> Statement
...     SELECT(job_events.job_id, AS(max_of(job_events.event_id), "event_id"),
...            AS(max_of(job_events.minutes), "minutes")),
...     FROM(job_events),
...     WHERE(*week_ends),
...     GROUP_BY(job_events.job_id),
... )
>>> text = show_hive(careless)  # -> str
SELECT
  job_events.job_id,
  MAX(job_events.event_id) AS event_id,
  MAX(job_events.minutes) AS minutes
FROM ops.job_events AS job_events
WHERE
  job_events.dt BETWEEN '2026-09-18' AND '2026-09-24'
  AND job_events.event_type IN ('finish', 'fail')
GROUP BY
  job_events.job_id;
>>> run(careless, query=query)  # -> DataFrame
   job_id  event_id  minutes
0       1        56       14
1       2        54       22
2       3        46       33

It runs, and it is wrong. Job 1's last run, event 56, took 10 minutes, but
`max_of(job_events.minutes)` takes the largest minutes from any of job 1's runs, 14. Each
`max_of` picks its own row.

### Number each job's runs, last first

`row_number` numbers the rows of each group from 1:

- `PARTITION_BY=` names the column whose values make the groups, here each job. The word is
  SQL's; it has nothing to do with a table's Partitions.
- `ORDER_BY=` says the order to number them in. `descending` makes the largest come first, so
  each job's last run gets 1.

The two may also go inside a `window`, passed as `over=`, the way every other calculation over
the rows around each row takes them, such as `lag` and `rank`: `row_number(over=window(
PARTITION_BY=..., ORDER_BY=...))` writes the same Hive.

The number is a calculation, so it needs a name with `AS`, and it goes in a Derived table, for
the next Statement to read:

>>> numbered = derived("numbered", statement(  # -> Table
...     SELECT(job_events.job_id, job_events.event_id, job_events.minutes,
...            AS(row_number(PARTITION_BY=job_events.job_id,
...                          ORDER_BY=descending(job_events.event_id)), "last_first")),
...     FROM(job_events),
...     WHERE(*week_ends),
... ))

The Example database runs only part of Hive, and not `row_number`. Pasted into your own
notebook, running a Statement that reads `numbered`, here and in the steps below, stops with
this message:

>>> run(statement(SELECT(all_columns(numbered)), FROM(numbered)), query=query)
Traceback (most recent call last):
...
RuntimeError:
  What happened:  The Example database can't run this Hive: its executor has no window functions such as row_number.
...

So the results below that read `numbered`, or `ranked` and `first_first` like it, are what
Hive gives at work, worked out in pandas for this page, as their label says. The Hive is the
Hive your warehouse runs.

Check the numbering alone first, with a Statement that reads every column of it:

>>> numbering = statement(SELECT(all_columns(numbered)), FROM(numbered))  # -> Statement
>>> text = show_hive(numbering)  # -> str
WITH numbered AS (
  SELECT
    job_events.job_id,
    job_events.event_id,
    job_events.minutes,
    ROW_NUMBER() OVER (PARTITION BY job_events.job_id ORDER BY job_events.event_id DESC) AS last_first
  FROM ops.job_events AS job_events
  WHERE
    job_events.dt BETWEEN '2026-09-18' AND '2026-09-24'
    AND job_events.event_type IN ('finish', 'fail')
)
SELECT
  numbered.job_id,
  numbered.event_id,
  numbered.minutes,
  numbered.last_first
FROM numbered;
>>> run(numbering, query=query)  # -> DataFrame
    job_id  event_id  minutes  last_first
0        1        32       14           7
1        1        38       11           6
2        1        40       12           5
3        1        42       13           4
4        1        48       10           3
5        1        52       12           2
6        1        56       10           1
7        2        34       22           4
8        2        44       21           3
9        2        50       18           2
10       2        54       18           1
11       3        36       12           2
12       3        46       33           1

Each job's runs are numbered 1, 2, 3, ... from its last.

### Keep number 1

The Statement that reads `numbered` keeps the rows numbered 1: one whole row per job.

>>> latest = statement(  # -> Statement
...     SELECT(numbered.job_id, numbered.event_id, numbered.minutes),
...     FROM(numbered),
...     WHERE(equals(numbered.last_first, 1)),
... )
>>> text = show_hive(latest)  # -> str
WITH numbered AS (
...
)
SELECT
  numbered.job_id,
  numbered.event_id,
  numbered.minutes
FROM numbered
WHERE
  numbered.last_first = 1;
>>> run(latest, query=query)  # -> DataFrame
   job_id  event_id  minutes
0       1        56       10
1       2        54       18
2       3        46       33

Job 1's last run took 10 minutes, as it should: the minutes come from the same row as the
event.

### Keep the top N of each group

Keep numbers 1 to N instead, with `at_most`. Here, each job's three longest runs: number them
from the longest. Two of job 1's runs took 12 minutes, so `ORDER_BY=` takes a list, and a
second column breaks the tie, the later of the two first. Without one, which of two tied rows
gets the lower number can change from one run to the next.

>>> ranked = derived("ranked", statement(  # -> Table
...     SELECT(job_events.job_id, job_events.event_id, job_events.minutes,
...            AS(row_number(PARTITION_BY=job_events.job_id,
...                          ORDER_BY=[descending(job_events.minutes),
...                                    descending(job_events.event_id)]), "longest_first")),
...     FROM(job_events),
...     WHERE(*week_ends),
... ))
>>> top_three = statement(  # -> Statement
...     SELECT(ranked.job_id, ranked.event_id, ranked.minutes),
...     FROM(ranked),
...     WHERE(at_most(ranked.longest_first, 3)),
... )
>>> text = show_hive(top_three)  # -> str
WITH ranked AS (
  SELECT
    job_events.job_id,
    job_events.event_id,
    job_events.minutes,
    ROW_NUMBER() OVER (
      PARTITION BY job_events.job_id
      ORDER BY job_events.minutes DESC, job_events.event_id DESC
    ) AS longest_first
  FROM ops.job_events AS job_events
  WHERE
    job_events.dt BETWEEN '2026-09-18' AND '2026-09-24'
    AND job_events.event_type IN ('finish', 'fail')
)
SELECT
  ranked.job_id,
  ranked.event_id,
  ranked.minutes
FROM ranked
WHERE
  ranked.longest_first <= 3;
>>> run(top_three, query=query)  # -> DataFrame
   job_id  event_id  minutes
0       1        32       14
1       1        42       13
2       1        52       12
3       2        34       22
4       2        44       21
5       2        54       18
6       3        36       12
7       3        46       33

Three rows per job, or fewer for a job with fewer runs, as job 3 has two. Of job 1's two runs
of 12 minutes, the later, event 52, is kept. `ORDER_BY` with `LIMIT` keeps the top N rows of
the whole result; `row_number` keeps the top N of each group.

## Check it worked

Check that each job comes back once: one row per job, as many rows as jobs that ran. On the
Example database this run stops, as above; `last_runs` here is the pandas result. At work the
Statement runs, and the check is the same.

>>> last_runs = run(latest, query=query)  # -> DataFrame
>>> last_runs["job_id"].is_unique
True

And check each job's last run against the largest event id worked out another way, with
`max_of`, which is right for one column on its own. Each side becomes a dict, from each job to
its event, so the order the rows came back in doesn't matter:

>>> largest_ids = statement(  # -> Statement
...     SELECT(job_events.job_id, AS(max_of(job_events.event_id), "event_id")),
...     FROM(job_events),
...     WHERE(*week_ends),
...     GROUP_BY(job_events.job_id),
... )
>>> largest = run(largest_ids, query=query)  # -> DataFrame
>>> dict(zip(largest["job_id"], largest["event_id"])) == dict(
...     zip(last_runs["job_id"], last_runs["event_id"]))
True

## Common mistakes

### Testing the row number in the same Statement

A row's number is given last, after the rows are picked, so Hive can't test it in the `WHERE`
of the Statement that makes it:

>>> in_one_go = statement(
...     SELECT(job_events.job_id, job_events.event_id, job_events.minutes),
...     FROM(job_events),
...     WHERE(*week_ends,
...           equals(row_number(PARTITION_BY=job_events.job_id,
...                             ORDER_BY=descending(job_events.event_id)), 1)),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  WHERE has ROW_NUMBER() OVER (PARTITION BY job_events.job_id ORDER BY job_events.event_id DESC) = 1, which numbers rows.
...

Number the rows in a Derived table, then keep number 1 in the Statement that reads it, as the
steps do.

### Numbering from the wrong end

Without `descending`, `ORDER_BY=` numbers from the smallest, so number 1 is each job's first
run of the week, not its last. Nothing stops it:

>>> first_first = derived("first_first", statement(  # -> Table
...     SELECT(job_events.job_id, job_events.event_id, job_events.minutes,
...            AS(row_number(PARTITION_BY=job_events.job_id, ORDER_BY=job_events.event_id),
...               "position")),
...     FROM(job_events),
...     WHERE(*week_ends),
... ))
>>> first_runs = statement(  # -> Statement
...     SELECT(first_first.job_id, first_first.event_id, first_first.minutes),
...     FROM(first_first),
...     WHERE(equals(first_first.position, 1)),
... )
>>> run(first_runs, query=query)  # -> DataFrame
   job_id  event_id  minutes
0       1        32       14
1       2        34       22
2       3        36       12

Each job's first run of the week. Its Hive numbers with `ORDER BY job_events.event_id ASC`,
where numbering last first says DESC.

### A row number without a name

>>> unnamed = derived("unnamed", statement(
...     SELECT(job_events.job_id, job_events.event_id,
...            row_number(PARTITION_BY=job_events.job_id,
...                       ORDER_BY=descending(job_events.event_id))),
...     FROM(job_events),
...     WHERE(*week_ends),
... ))
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  SELECT has a calculation with no name: ROW_NUMBER() OVER (PARTITION BY job_events.job_id ORDER BY job_events.event_id DESC).
...

Name it with `AS`, so the Statement that reads it can test it by that name.

## Next

- Keep the numbering step as a Building block every Statement can call:
  [Share Building blocks](#share_building_blocks).
- Each job's row as it was on a given day, from a table that keeps a copy of itself every day:
  [Look things up as of a day](#look_things_up_as_of_a_day).
- A rank, the row before, or a rolling sum, each over a Window:
  [Look across rows](#look_across_rows).
- The gallery's Worked examples of [`row_number`](examples.html#row_number) and
  [`descending`](examples.html#descending), and the careless and fixed Statements side by side:
  [latest and top N](examples.html#latest_and_top_n).
"""

import pandas as pd

from sqlglot_composer import (
    FROM, SELECT, WHERE, all_columns, between, example_database, is_in, run, statement,
)

# The Example database can't run row_number, so the page and the doctest get each Statement's
# result from these, worked out in pandas from every run-ending event of the week.


def every_run_end() -> pd.DataFrame:
    """Every event that ended a run in the week, read with a Statement the Example database
    can run."""
    job_events = example_database.job_events
    return run(statement(SELECT(all_columns(job_events)), FROM(job_events),
                         WHERE(between(job_events.dt, "2026-09-18", "2026-09-24"),
                               is_in(job_events.event_type, ["finish", "fail"]))),
               query=example_database.query)


def numbered_runs(by: list[str], largest_first: bool) -> pd.DataFrame:
    """Every run end, numbered within its job in the order of the columns `by`, from 1."""
    runs = every_run_end().sort_values(by, ascending=not largest_first, kind="stable")
    return runs.assign(number=runs.groupby("job_id").cumcount() + 1)


def in_order(rows: pd.DataFrame) -> pd.DataFrame:
    """The rows as the Example database gives them: by the first column, then the next, ..."""
    return rows.sort_values(list(rows.columns)).reset_index(drop=True)


def numbering_in_pandas() -> pd.DataFrame:
    rows = numbered_runs(["event_id"], largest_first=True).rename(
        columns={"number": "last_first"})
    return in_order(rows[["job_id", "event_id", "minutes", "last_first"]])


def latest_in_pandas() -> pd.DataFrame:
    rows = numbered_runs(["event_id"], largest_first=True)
    return in_order(rows[rows["number"] == 1][["job_id", "event_id", "minutes"]])


def top_three_in_pandas() -> pd.DataFrame:
    rows = numbered_runs(["minutes", "event_id"], largest_first=True)
    return in_order(rows[rows["number"] <= 3][["job_id", "event_id", "minutes"]])


def first_runs_in_pandas() -> pd.DataFrame:
    rows = numbered_runs(["event_id"], largest_first=False)
    return in_order(rows[rows["number"] == 1][["job_id", "event_id", "minutes"]])
