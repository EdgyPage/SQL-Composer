"""The latest row of each group, and the top N

For: Intermediate

## Goal

Keep one whole row of each group, such as each job's last run, or the top N rows of each
group, such as each job's three longest runs. `row_number` numbers the rows of each group in
the order you choose, inside a Derived table: a Statement given a name so another Statement
can read from it, never stored. A Statement is one query, made of the Toolbox's Clause
functions. The Statement that reads the Derived table keeps number 1, or numbers 1 to N.

## When you'd use it

- If you want the latest row of each group, such as each job's last run, each customer's last
  order or each product's newest price, keep number 1, as steps 5 to 7 do.
- If you want the top N of each group, such as each job's three longest runs or each team's
  busiest days, keep numbers 1 to N, as steps 8 and 9 do.
- If you are about to take `max_of` of several columns to get "the newest row", number the
  rows instead: each `max_of` picks its own row, so the columns can come from different rows.
  Step 4 shows it happen.
- If you have not yet done the Getting started how-tos, do
  [Build and run a first statement](#build_and_run_a_first_statement),
  [Count, join and stay safe](#count_join_and_stay_safe) and
  [Share Building blocks](#share_building_blocks), which starts with Derived tables, first.

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

### 2. Import the Toolbox, the table and its Alias

Goal: the table and the Condition the steps read. Import the Toolbox, the Project's `ops`
Database and your query. `ops.job_events` holds what each job's runs did: a `"start"` row when
a run starts, then `"retry"`, `"finish"` or `"fail"`, with the minutes since the run started.
Its Table reference, the file that describes the table, ends with an Alias, a name you give by
hand to a condition on that table alone: `ends_a_run`, the events that end a run, imported
beside the table it is about:

>>> from sqlglot_composer import *
>>> from references import ops
>>> from references.ops__job_events import ends_a_run
>>> from warehouse import query, execute
>>> job_events = ops.job_events  # -> Table
>>> ends_a_run  # -> Condition
job_events.event_type IN ('finish', 'fail')

Done when `ends_a_run` shows `job_events.event_type IN ('finish', 'fail')`. Then step 3.

### 3. Keep the week's run-ending rows

Goal: the filter every Statement below reads. A run's minutes are on the row that ends it, and
event ids grow as events come in, so the last run of each job is its run-ending row with the
largest `job_events.event_id`. This how-to reads the last week of the Example database,
2026-09-18 to 2026-09-24:

>>> week_ends = [between(job_events.dt, "2026-09-18", "2026-09-24"), ends_a_run]

Done when `week_ends` holds the two Conditions. Then step 4.

### 4. See why max_of isn't the latest row

Goal: see the wrong answer before the right one. The question: how long did each job's last run
take? The first thing most people write takes the largest of each column:

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
>>> run_query(careless, query)  # -> DataFrame
   job_id  event_id  minutes
0       1        56       14
1       2        54       22
2       3        46       33

It runs, and it is wrong. Job 1's last run, event 56, took 10 minutes, but
`max_of(job_events.minutes)` takes the largest minutes from any of job 1's runs, 14. Each
`max_of` picks its own row.

Done when you see job 1's minutes, 14, come from a run other than event 56. Then step 5.

### 5. Number each job's runs, last first

Goal: a number on each row, 1 for each job's last run. `row_number` numbers the rows of each
group from 1:

- `PARTITION_BY=` names the column whose values make the groups, here each job. The word is
  SQL's; it has nothing to do with a table's Partitions.
- `ORDER_BY=` says the order to number them in. `descending` makes the largest come first, so
  each job's last run gets 1.

The two may also go inside a `window`, passed as `over=`, the way every other calculation over
the rows around each row takes them, such as `lag` and `rank`: `row_number(over=window(
PARTITION_BY=..., ORDER_BY=...))` writes the same Hive.

The number is a calculation, so name it with `AS`, and put it in a Derived table, for the next
Statement to read:

>>> numbered = derived("numbered", statement(  # -> Table
...     SELECT(job_events.job_id, job_events.event_id, job_events.minutes,
...            AS(row_number(PARTITION_BY=job_events.job_id,
...                          ORDER_BY=descending(job_events.event_id)), "last_first")),
...     FROM(job_events),
...     WHERE(*week_ends),
... ))

Done when `numbered` is made without an error. Then step 6.

### 6. Check the numbering alone

Goal: see each row's number before you keep any. Read every column of the Derived table with a
Statement of its own:

>>> numbering = statement(SELECT(all_columns(numbered)), FROM(numbered))  # -> Statement
>>> text = show_hive(numbering)  # -> str
WITH numbered AS (
  SELECT
    job_events.job_id,
    job_events.event_id,
    job_events.minutes,
    ROW_NUMBER() OVER (PARTITION BY job_events.job_id ORDER BY job_events.event_id DESC) AS
        last_first
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
>>> run_query(numbering, query)  # -> DataFrame
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

Each job's runs are numbered 1, 2, 3, ... from its last. The table lists them by job and
event id, as the Example database gives rows when nothing orders them, so each job's numbers
count down.

Done when each job's largest event id has last_first 1. Then step 7.

### 7. Keep number 1

Goal: one whole row per job. The Statement that reads `numbered` keeps the rows numbered 1:

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
>>> run_query(latest, query)  # -> DataFrame
   job_id  event_id  minutes
0       1        56       10
1       2        54       18
2       3        46       33

Job 1's last run took 10 minutes, as it should: the minutes come from the same row as the
event.

Done when job 1's row is event 56, 10 minutes. Then step 8.

### 8. Number each job's runs, longest first

Goal: a number on each row, 1 for each job's longest run. Number the runs from the longest.
Two of job 1's runs took 12 minutes, so `ORDER_BY=` takes a list, and a second column breaks the
tie, the later of the two first. Give every numbering a column that breaks ties: without one,
which of two tied rows gets the lower number can change from one run to the next.

>>> ranked = derived("ranked", statement(  # -> Table
...     SELECT(job_events.job_id, job_events.event_id, job_events.minutes,
...            AS(row_number(PARTITION_BY=job_events.job_id,
...                          ORDER_BY=[descending(job_events.minutes),
...                                    descending(job_events.event_id)]), "longest_first")),
...     FROM(job_events),
...     WHERE(*week_ends),
... ))

Done when `ranked` is made without an error. Then step 9.

### 9. Keep the top N of each group

Goal: each job's three longest runs. Keep numbers 1 to N, with `at_most`:

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
>>> run_query(top_three, query)  # -> DataFrame
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

Done when jobs 1 and 2 have three rows each and job 3 two. Then check it worked, below.

## Check it worked

Check that each job comes back once: one row per job, as many rows as jobs that ran.

>>> last_runs = run_query(latest, query)  # -> DataFrame
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
>>> largest = run_query(largest_ids, query)  # -> DataFrame
>>> dict(zip(largest["job_id"], largest["event_id"])) == dict(
...     zip(last_runs["job_id"], last_runs["event_id"]))
True

Before you go on, check that:

- `last_runs["job_id"].is_unique` shows `True`;
- the comparison with `max_of` above shows `True`;
- each row of `latest` takes its minutes from its own event, as job 1's 10 minutes do.

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
  What happened:  WHERE has ROW_NUMBER() OVER (PARTITION BY job_events.job_id ORDER BY
                  job_events.event_id DESC) = 1, which numbers rows.
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
>>> run_query(first_runs, query)  # -> DataFrame
   job_id  event_id  minutes
0       1        32       14
1       2        34       22
2       3        36       12

Each job's first run of the week. Its Hive numbers with `ORDER BY job_events.event_id ASC`,
where numbering last first says DESC. To number from the last, wrap the column in
`descending`.

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
  What happened:  SELECT has a calculation with no name: ROW_NUMBER() OVER (PARTITION BY
                  job_events.job_id ORDER BY job_events.event_id DESC).
...

The Toolbox stops it with a Guard, a check that refuses a Statement that would give a wrong
result. Name it with `AS`, so the Statement that reads it can test it by that name.

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
