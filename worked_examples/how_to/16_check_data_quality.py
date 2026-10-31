"""Check data quality with Statements

For: Intermediate

## Goal

Check a table's data before you trust a number built on it, with Statements you keep and run
again: Keys that repeat, NULLs in each column, the rows in each Partition, and two tables that
should agree. Then run them all at once and gather what they find in one pandas DataFrame, and
see where the Project keeps such checks: a Table notebook made from the quality_checks
Template.

## When you'd use it

Before you build on a table that is new to you, after a load that looked odd, or every morning
before the Project's Saved tables are written. A check that is a Statement runs on the
warehouse, so it reads every row of the Partitions you give it, and your notebook gets back
only the few rows that matter.

It needs the Getting started how-tos [Count, join and stay safe](#count_join_and_stay_safe)
and [Save a table](#save_a_table).

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

Then import the Toolbox, pandas, the `project` module, the Project's `ops` Database and your
query. This how-to reads three of its tables, each holding 14 days, 2026-09-11 to 2026-09-24:
`ops.job_owners`, which says each day who owns each job; `ops.job_events`, each run's start,
finish, retry or fail; and `ops.region_costs`, what each job cost per region and day, in
cents, which writes its days like 20260911, not 2026-09-11, so its days are written that way
below.

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> import pandas as pd
>>> from references import ops
>>> from warehouse import query, execute
>>> job_owners = ops.job_owners  # -> Table
>>> job_events = ops.job_events  # -> Table
>>> region_costs = ops.region_costs  # -> Table

### Find Keys that repeat

A Table reference's Key lists the columns that pick out one row of the table. For
`ops.job_owners` it is `job_owners.job_id` and `job_owners.dt`: one row per job per day. The
warehouse never enforces a Key, and JOIN relies on it to warn you about repeated rows, so
check it holds.

Write a check so that each row it gives back is a problem. Here, group the rows by the Key and
keep, with `HAVING`, only the groups holding more than one row:

>>> repeated_keys = statement(  # -> Statement
...     SELECT(job_owners.job_id, job_owners.dt, AS(count_rows(), "copies")),
...     FROM(job_owners),
...     WHERE(between(job_owners.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_owners.job_id, job_owners.dt),
...     HAVING(more_than(count_rows(), 1)),
... )
>>> run_query(repeated_keys, query)  # -> DataFrame
Empty DataFrame
Columns: [job_id, dt, copies]
Index: []

No rows: no Key repeats on any of the 14 days. The Toolbox's own
[`check_key`](examples.html#check_key) does the same for the rows its `where=` picks, and
says so in a sentence:

>>> check_key(job_owners, query=query,  # -> Verdict
...           where=between(job_owners.dt, "2026-09-11", "2026-09-24"))
ops.job_owners: the key (job_id, dt) holds where job_owners.dt BETWEEN '2026-09-11' AND
    '2026-09-24'.

### Count the NULLs in every column

[`all_columns`](examples.html#all_columns) gives every column of a Table reference, in a list,
so one short function writes a NULL count for each column of any table. A column's text is the
Hive that names it, such as `job_owners.owner`, and the part after the dot is its own name,
which names each count. Which rows to count is a condition on one of the table's partition
columns, since each table is partitioned its own way:

>>> def null_counts(t: Table, where: Condition) -> Statement:
...     counts = [AS(count_rows(where=is_null(column)), "null_" + str(column).split(".")[1])
...               for column in all_columns(t)]
...     return statement(
...         SELECT(AS(count_rows(), "total_rows"), counts),
...         FROM(t),
...         WHERE(where),
...     )

Here is the Hive it writes for `ops.job_owners`, one count per column:

>>> owner_nulls = null_counts(  # -> Statement
...     job_owners, between(job_owners.dt, "2026-09-11", "2026-09-24"))
>>> text = show_hive(owner_nulls)  # -> str
SELECT
  COUNT(*) AS total_rows,
  COUNT(CASE WHEN job_owners.job_id IS NULL THEN 1 END) AS null_job_id,
  COUNT(CASE WHEN job_owners.team IS NULL THEN 1 END) AS null_team,
  COUNT(CASE WHEN job_owners.owner IS NULL THEN 1 END) AS null_owner,
  COUNT(CASE WHEN job_owners.dt IS NULL THEN 1 END) AS null_dt
FROM ops.job_owners AS job_owners
WHERE
  job_owners.dt BETWEEN '2026-09-11' AND '2026-09-24';
>>> run_query(owner_nulls, query)  # -> DataFrame
   total_rows  null_job_id  null_team  null_owner  null_dt
0          56            0          0          14        0

14 of the 56 rows have no owner: cache_warm has had none on any of the 14 days. The same
function counts the NULLs in `ops.region_costs`, here its eu Partitions:

>>> run_query(null_counts(region_costs, equals(region_costs.region, "eu")), query)
   total_rows  null_job_id  null_cost_cents  null_region  null_dt
0          24            0                1            0        0

### Count the rows in each Partition

A Partition holding far fewer rows than the others often means a load that broke halfway.
Count the rows per day with `GROUP_BY`:

>>> events_per_day = statement(  # -> Statement
...     SELECT(job_events.dt, AS(count_rows(), "events")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_events.dt),
... )
>>> run_query(events_per_day, query)  # -> DataFrame
            dt  events
0   2026-09-11       6
1   2026-09-12       2
2   2026-09-13       2
3   2026-09-14       7
4   2026-09-15       4
5   2026-09-16       5
6   2026-09-17       4
7   2026-09-18       6
8   2026-09-19       2
9   2026-09-20       2
10  2026-09-21       6
11  2026-09-22       4
12  2026-09-23       4
13  2026-09-24       3

The weekends, 2026-09-12 and 13 and 2026-09-19 and 20, hold 2 events each: only
nightly_load runs then.

### Check that two tables agree

Every run that starts should get a bill. `ops.job_events` says how many runs started each day,
and `ops.region_costs` how many bills came in. Count each, per day, with one Statement each:

>>> starts_per_day = statement(  # -> Statement
...     SELECT(job_events.dt,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "starts")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-11", "2026-09-24")),
...     GROUP_BY(job_events.dt),
... )
>>> bills_per_day = statement(  # -> Statement
...     SELECT(region_costs.dt,
...            AS(count_rows(where=is_not_null(region_costs.cost_cents)), "bills")),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, "20260911", "20260924")),
...     GROUP_BY(region_costs.dt),
... )

The two tables write their days differently, so compare the two small results in pandas:
write `region_costs`'s days like `job_events`'s, then put the two side by side with
`starts.merge`. `how="outer"` keeps a day that only one of them has, with NaN, pandas' empty
value, for the other count, so that day shows up as a difference too:

>>> starts = run_query(starts_per_day, query)  # -> DataFrame
>>> bills = run_query(bills_per_day, query)  # -> DataFrame
>>> bills["dt"] = pd.to_datetime(bills["dt"], format="%Y%m%d").dt.strftime("%Y-%m-%d")
>>> both = starts.merge(bills, on="dt", how="outer")  # -> DataFrame
>>> both[both["starts"] != both["bills"]]
            dt  starts  bills
13  2026-09-24       2      1

On 2026-09-24 two runs started but only one was billed: invoice_sync is still running, and
its bill comes in when it finishes.

### Run every check and gather what they find

Two more checks, each giving the rows that are problems: jobs with no owner on the newest day,
and costs not billed yet:

>>> no_owner = statement(  # -> Statement
...     SELECT(job_owners.job_id, job_owners.dt),
...     FROM(job_owners),
...     WHERE(equals(job_owners.dt, "2026-09-24"), is_null(job_owners.owner)),
... )
>>> not_billed = statement(  # -> Statement
...     SELECT(region_costs.job_id, region_costs.region, region_costs.dt),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, "20260911", "20260924"),
...           is_null(region_costs.cost_cents)),
... )

Keep the checks in a dict, by name, and run each in a loop. Add the days on which the two
tables disagree, already in pandas, then count each check's problem rows:

>>> checks = {"repeated_keys": repeated_keys, "no_owner": no_owner,
...           "not_billed": not_billed}
>>> found = {name: run_query(check_statement, query)  # -> dict[str, DataFrame]
...          for name, check_statement in checks.items()}
>>> found["starts_not_billed"] = both[both["starts"] != both["bills"]]
>>> summary = pd.DataFrame({"check": list(found),  # -> DataFrame
...                         "problem_rows": [len(rows) for rows in found.values()]})
>>> summary
               check  problem_rows
0      repeated_keys             0
1           no_owner             1
2         not_billed             1
3  starts_not_billed             1

A check with 0 problem rows passed. For the others, `found` holds the rows to look at:

>>> found["not_billed"]
   job_id region        dt
0       2     eu  20260924

### Keep a table's checks in its own Table notebook

The Project keeps the checks it runs every day in a Table notebook made from the
quality_checks Template: `project.new_table("mart.job_events_checks",
template="quality_checks")` made tables/mart__job_events_checks/mart__job_events_checks.ipynb.
Its logic cell names the rows it checks once, as READS, the newest day of `ops.job_events`,
and defines a check of repeated Keys and a NULL count, as above, beside a `checks_logic.write()`
that saves each day's row count, so a day that came in short shows beside the days around it.
`project.load` gives its functions:

>>> checks_logic = project.load("mart.job_events_checks")  # -> the notebook's functions
>>> checks_logic
The logic of mart.job_events_checks: create, rows, preview, write, repeated_keys, column_name,
    null_counts.
>>> run_query(checks_logic.repeated_keys(), query)  # -> DataFrame
Empty DataFrame
Columns: [event_id, times_seen]
Index: []
>>> run_query(checks_logic.null_counts(), query)  # -> DataFrame
   null_event_id  null_job_id  null_event_type  null_minutes  null_dt
0              0            0                0             0        0

A check is of the rows in on the day it runs, so the notebook checks only the day its READS
names: a check written again later would hide what was missing then.

## Check it worked

Each check you expect to pass gives no rows, and each one that finds something names the rows
you can explain: `no_owner` names cache_warm, job 4, which has never had an owner, and
`not_billed` names invoice_sync, job 2, still running on 2026-09-24.

>>> found["no_owner"]
   job_id          dt
0       4  2026-09-24
>>> len(found["repeated_keys"])
0

## Common mistakes

### Looking for NULLs with equals

In SQL nothing equals NULL, not even NULL, so a condition owner = NULL matches no row, and
the count comes out 0 however many owners are missing. The Toolbox refuses it as you build it:

>>> count_rows(where=equals(job_owners.owner, None))
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  equals(job_owners.owner, None) compares with None.
...

Use `is_null(column)`, as `null_counts` does, or `is_not_null(column)`.

### Expecting a day with no rows to show 0

`GROUP_BY` makes one row per value it finds, so a day with no rows at all isn't in the result:
it doesn't show with 0. invoice_sync, job 2, runs on weekdays only, and its count per day
skips the weekends without a word:

>>> invoice_sync_per_day = statement(  # -> Statement
...     SELECT(job_events.dt, AS(count_rows(), "events")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-11", "2026-09-24"),
...           equals(job_events.job_id, 2)),
...     GROUP_BY(job_events.dt),
... )
>>> per_day = run_query(invoice_sync_per_day, query)  # -> DataFrame
>>> len(per_day)
10

To find the days that are missing, list every day you expected, with `pd.date_range`, and
keep those the result doesn't hold:

>>> every_day = pd.date_range("2026-09-11", "2026-09-24").strftime("%Y-%m-%d")
>>> [day for day in every_day if day not in set(per_day["dt"])]
['2026-09-12', '2026-09-13', '2026-09-19', '2026-09-20']

Here the four are weekends, as expected. A missing weekday would be a load to look into.

### A check that reads every Partition

A check of a partitioned table must filter one of its partition columns, as any read must. A
NULL count over all of `ops.region_costs` is refused, naming its partition columns:

>>> statement(SELECT(AS(count_rows(where=is_null(region_costs.cost_cents)), "nulls")),
...           FROM(region_costs))
Traceback (most recent call last):
...
sqlglot_composer.refusals.LoadRefused:
  What happened:  FROM(region_costs) reads ops.region_costs, but filters none of its partition
                  columns: region, dt.
...

Give each check the Partitions it checks, as `null_counts` takes them in `where`.

## Next

- Check that a Statement gives the numbers you meant, against pandas, and review a change
  before you make it: [Review and test a change](#review_and_test_a_change).
- Check a Saved table's Key before every write: [Keys](#keys).
- Put two tables' rows side by side, and find the ones that differ:
  [Reconcile two tables](#reconcile_two_tables).
- The gallery's [`check_table_reference`](examples.html#check_table_reference) checks that a
  Table reference still matches its table, and [`check_key`](examples.html#check_key) checks
  its Key on the rows you pick.
"""
