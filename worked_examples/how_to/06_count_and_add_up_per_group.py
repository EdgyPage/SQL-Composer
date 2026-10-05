"""Count and add up per group

For: Getting started

## Goal

Answer "how many, and how much, per something": runs per job, minutes per day, failed runs per
job. `GROUP_BY` makes one output row per group, the calculation functions (`count_rows`,
`count_distinct`, `sum_of`, `min_of`, `max_of`) work out each group's numbers, `HAVING` keeps
only some groups, and `ORDER_BY` with `LIMIT` keeps the top N.

## When you'd use it

Whenever the answer is a table of totals rather than a list of rows: a daily count for a
dashboard, the busiest jobs of the week, the teams over a budget. The warehouse does the
counting, so only the totals come back to your notebook, however many rows they were counted
from.

## Steps

### Import the Toolbox and name the table

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs

### Count every row

`count_rows()` counts rows. Every calculation in `SELECT` needs a name for its column in the
result, which `AS` gives:

>>> all_runs = statement(
...     SELECT(AS(count_rows(), "runs"), AS(sum_of(job_runs.duration_mins), "minutes")),
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
>>> run(all_runs, send=example_database.send)
   runs  minutes
0     9      180

Without `GROUP_BY`, the whole of the two days is one group: one row comes back.

### One row per job

`GROUP_BY(job_runs.job_id)` makes one group per job. `SELECT` then holds the columns you group
by, and calculations over each group:

>>> per_job = statement(
...     SELECT(
...         job_runs.job_id,
...         AS(count_rows(), "runs"),
...         AS(sum_of(job_runs.duration_mins), "minutes"),
...         AS(min_of(job_runs.duration_mins), "shortest"),
...         AS(max_of(job_runs.duration_mins), "longest"),
...     ),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
>>> text = show_hive(per_job)
SELECT
  job_runs.job_id,
  COUNT(*) AS runs,
  SUM(job_runs.duration_mins) AS minutes,
  MIN(job_runs.duration_mins) AS shortest,
  MAX(job_runs.duration_mins) AS longest
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.job_id;
>>> run(per_job, send=example_database.send)
   job_id  runs  minutes  shortest  longest
0       1     4       67         5       40
1       2     3       53        15       20
2       3     2       60        30       30

### Count only some rows of each group

`count_rows` and `sum_of` take `where=`, a condition, to count or add up only the rows where it
holds, while the group keeps every row. Here, each job's runs and its failed runs side by side:

>>> failures = statement(
...     SELECT(
...         job_runs.job_id,
...         AS(count_rows(), "runs"),
...         AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...     ),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
>>> text = show_hive(failures)
SELECT
  job_runs.job_id,
  COUNT(*) AS runs,
  COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.job_id;
>>> run(failures, send=example_database.send)
   job_id  runs  failed_runs
0       1     4            0
1       2     3            1
2       3     2            1

In the Hive, `COUNT(CASE WHEN ... THEN 1 END)` counts the rows where the condition holds: CASE
gives 1 for those and NULL for the rest, and COUNT skips NULL. Putting
`equals(job_runs.status, "FAILED")` in `WHERE` instead would drop the other runs
before counting, so `"runs"` would count only failed runs too.

### Count different values

`count_distinct` counts the different values in a column, each once. Here, how many runs each
job had, and on how many different days:

>>> days_per_job = statement(
...     SELECT(
...         job_runs.job_id,
...         AS(count_rows(), "runs"),
...         AS(count_distinct(job_runs.dt), "days_with_runs"),
...     ),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
>>> text = show_hive(days_per_job)
SELECT
  job_runs.job_id,
  COUNT(*) AS runs,
  COUNT(DISTINCT job_runs.dt) AS days_with_runs
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.job_id;
>>> run(days_per_job, send=example_database.send)
   job_id  runs  days_with_runs
0       1     4               2
1       2     3               2
2       3     2               2

Job 1 ran 4 times, on 2 different days.

### Group by two columns

`GROUP_BY` takes several columns: one group per different pair. Here, each job on each day:

>>> per_job_day = statement(
...     SELECT(job_runs.job_id, job_runs.dt, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id, job_runs.dt),
... )
>>> text = show_hive(per_job_day)
SELECT
  job_runs.job_id,
  job_runs.dt,
  COUNT(*) AS runs
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.job_id,
  job_runs.dt;
>>> run(per_job_day, send=example_database.send)
   job_id          dt  runs
0       1  2026-09-23     2
1       1  2026-09-24     2
2       2  2026-09-23     2
3       2  2026-09-24     1
4       3  2026-09-23     1
5       3  2026-09-24     1

### Keep only some groups with HAVING

`WHERE` picks rows before they are counted, so it can't test a count. `HAVING` tests each
group after `GROUP_BY` has counted it. Here, the jobs with 3 runs or more:

>>> busy_jobs = statement(
...     SELECT(job_runs.job_id, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
...     HAVING(at_least(count_rows(), 3)),
... )
>>> text = show_hive(busy_jobs)
SELECT
  job_runs.job_id,
  COUNT(*) AS runs
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.job_id
HAVING
  COUNT(*) >= 3;
>>> run(busy_jobs, send=example_database.send)
   job_id  runs
0       1     4
1       2     3

`HAVING` repeats the calculation itself, `count_rows()`, rather than its name, `"runs"`: SQL
works `HAVING` out before `SELECT` has named anything. `ORDER_BY`, in the next step, is worked
out after `SELECT`, so it sorts by the name.

### Keep the top N

`ORDER_BY` sorts the result, and `LIMIT` keeps the first rows. `descending` sorts from largest
to smallest. A calculation is sorted by its name. Here, the two jobs with the most minutes:

>>> top_two = statement(
...     SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
...     ORDER_BY(descending("minutes")),
...     LIMIT(2),
... )
>>> text = show_hive(top_two)
SELECT
  job_runs.job_id,
  SUM(job_runs.duration_mins) AS minutes
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.job_id
ORDER BY
  minutes DESC
LIMIT 2;
>>> run(top_two, send=example_database.send)
   job_id  minutes
0       1       67
1       3       60

Job 2's 53 minutes didn't make the top two.

## Check it worked

Count the same groups in pandas from the rows themselves, and compare. `every_run` reads every
run of the two days. Each side becomes a dict, from each job to its minutes, so the order the
rows came back in doesn't matter: without `ORDER_BY`, the warehouse may give them in any
order.

>>> every_run = run(statement(
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... ), send=example_database.send)
>>> in_pandas = every_run.groupby("job_id")["duration_mins"].sum().to_dict()
>>> from_hive = run(per_job, send=example_database.send)
>>> in_pandas == dict(zip(from_hive["job_id"], from_hive["minutes"]))
True

The totals of every group also add up to the total of all rows, from `all_runs`:

>>> print(from_hive["minutes"].sum())
180

## Common mistakes

### A column that isn't grouped

Each output row is one group, so every column in `SELECT` must be in `GROUP_BY` or inside a
calculation. Here `job_runs.status` is neither, and one job's runs have several statuses:

>>> status_per_job = statement(
...     SELECT(job_runs.job_id, job_runs.status, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  SELECT has job_runs.status, which GROUP_BY leaves out.
...

Add it to `GROUP_BY` for one row per job and status. To keep one whole row per job, such as
each job's newest run, see [The latest row per key](#latest_row_per_key).

### A calculation without a name

>>> unnamed = statement(
...     SELECT(job_runs.job_id, count_rows()),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  SELECT has a calculation with no name: COUNT(*).
...

Name it: `AS(count_rows(), "runs")`.

### Testing a count in WHERE

>>> busy_in_where = statement(
...     SELECT(job_runs.job_id, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"), at_least(count_rows(), 3)),
...     GROUP_BY(job_runs.job_id),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  WHERE has COUNT(*) >= 3, which counts or adds up rows.
...

Move it to `HAVING`, as `busy_jobs` does.

### Testing a calculation's name in HAVING

`HAVING` takes conditions on columns and calculations, not on the names `AS` gives:

>>> busy_by_name = statement(
...     SELECT(job_runs.job_id, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
...     HAVING(at_least("runs", 3)),
... )
Traceback (most recent call last):
...
TypeError:
  What happened:  at_least("runs", ...) was given 'runs' where a column goes.
...

Write the calculation again: `HAVING(at_least(count_rows(), 3))`.

### Sorting without a LIMIT

Sorting a whole result makes the warehouse put every row in order before any comes back, which
is slow on a big table. The Toolbox stops a sort with no `LIMIT`:

>>> sorted_jobs = statement(
...     SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
...     ORDER_BY(descending("minutes")),
... )
Traceback (most recent call last):
...
composer_core.refusals.LoadRefused:
  What happened:  ORDER_BY has no LIMIT.
...

This stop is a `LoadRefused`, not a `GuardRefused`: a Load limit protects the cluster from a
query too big for it, where a Guard protects the answer from a wrong number. For a top N, add
`LIMIT(2)` or however many you want. To sort every row, sort in pandas once the
result is back:

>>> run(per_job, send=example_database.send).sort_values("minutes", ascending=False)
   job_id  runs  minutes  shortest  longest
0       1     4       67         5       40
2       3     2       60        30       30
1       2     3       53        15       20

## Next

- Count across two tables, such as runs per team, without counting a row twice:
  [Join tables safely](#join_tables_safely).
- Keep each job's newest run, or each job's top N runs, whole:
  [The latest row per key](#latest_row_per_key).
- The gallery's Worked examples of [`GROUP_BY`](examples.html#GROUP_BY),
  [`HAVING`](examples.html#HAVING) and [`count_distinct`](examples.html#count_distinct), the
  four shapes side by side in [groups and the top N](examples.html#groups_and_top_n), and why a
  sum of counts of different values is refused: [re-grouping](examples.html#regrouping).
"""
