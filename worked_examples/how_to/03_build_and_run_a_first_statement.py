"""Build and run a first statement

For: Getting started

## Goal

Build a Statement from your Table references, read the Hive the Toolbox writes for it, run it
through your query, and get the rows back as a pandas DataFrame. A Statement is one query, made
of the Toolbox's Clause functions; a Table reference is the file that describes one table, its
columns, its Partitions and its Key; Hive is the SQL your warehouse runs. On the way you meet
the chain of types every Statement is built along, from a Table to a DataFrame, and the
Conditions `WHERE` takes to keep only the rows you want.

## When you'd use it

- If you have a question for a table, build a Statement for it, as the steps below do.
- If someone who doesn't use Python needs the query, print its Hive with `show_hive` (step 7)
  and paste it into another program, such as Hue, Beeline or DBeaver.
- If a result looks wrong, read the Statement's Hive (step 6): it shows exactly what the
  warehouse was asked.
- If the question counts per group or joins tables, do this how-to first, then
  [Count, join and stay safe](#count_join_and_stay_safe).

## Steps

### 1. Set up the Project the last how-to left

Goal: a Project whose Table references the steps below read. A Project is your folder of
scripts at work, in the Toolbox's fixed layout.

[Add your tables' references](#add_your_tables_references) left the Project with the Table
references of ops.jobs, ops.job_runs and ops.run_alerts. This page has no Project, so it makes
one with the same three; in your own Project, leave these calls out. Their TODO lines change no
Statement here, so this page leaves them as `project.add_references` writes them:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/, scheduled_runs/ and warehouse.py.
Next: at the top of each notebook, fill in connect(...) with your connection.
>>> from warehouse import connect, query, execute
>>> connect(example_database)
>>> project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"], query=query)
Wrote references/ops__jobs.py, references/ops__job_runs.py and references/ops__run_alerts.py:
    fill in their TODO lines.
...
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs and
    ops.run_alerts.
Restart the kernel of a notebook that imported references, to see a table added since.

Every notebook of the Project starts with three imports: every Toolbox name, your query and
execute, and the tables of the Database ops. A Database is a named group of tables, the first
part of a table's name, `ops` in `ops.jobs`:

>>> from references import ops

Done when `from references import ops` runs without an error. Then step 2.

### 2. Name the table and a column

Goal: the first two links of the chain of types. A Statement is built along a chain of types,
each made by a call on the one before:

- `ops.job_runs` is a Table: a table, its columns, its Partitions and its Key;
- `ops.job_runs.status` is a Column: one of its columns;
- `equals(...)`, and every test like it, gives a Condition: a test of each row;
- `SELECT(...)`, `FROM(...)`, `WHERE(...)` and the other Clause functions each give a Clause:
  one part of a query;
- `statement(...)` gives a Statement: its Clauses, checked together as one query;
- `to_hive(...)` gives a `str`: the Hive, the query's text;
- `run_query(..., query)` gives a DataFrame: the rows your query gives back, in pandas.

Each step below makes one, and its comment, such as `# -> Table`, says which. The question
the steps answer: which runs failed on 2026-09-23 and 2026-09-24? Give the table a short name
first, then read one of its Columns:

>>> job_runs = ops.job_runs  # -> Table
>>> job_runs.status  # -> Column
job_runs.status

Done when `job_runs.status` shows `job_runs.status`. Then step 3.

### 3. Make a Condition

Goal: a test that keeps the failed runs. A Condition tests a Column, row by row:

>>> is_failed = equals(job_runs.status, "FAILED")  # -> Condition
>>> is_failed
job_runs.status = 'FAILED'

Done when `is_failed` shows `job_runs.status = 'FAILED'`. Then step 4.

### 4. Make a WHERE Clause

Goal: a Clause that keeps only the rows you want. ops.job_runs is partitioned by dt: the
warehouse stores it a Partition at a time, one Partition for each value of dt. So every
Statement that reads it filters dt, here with `between`, which keeps the values from the first
to the last, both included. `WHERE` keeps a row only if every Condition in it holds:

>>> where = WHERE(is_failed, between(job_runs.dt, "2026-09-23", "2026-09-24"))  # -> Clause
>>> where
<WHERE clause - put it in statement(...)>

Done when `where` shows `<WHERE clause - put it in statement(...)>`. Then step 5.

### 5. Put the Clauses into a Statement

Goal: one query, checked as a whole. A Clause on its own is only a part. `statement` puts the
Clauses together in SQL's order, `SELECT` the columns you want, `FROM` a table, then `WHERE`,
and checks them as one query:

>>> failed = statement(  # -> Statement
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
...     FROM(job_runs),
...     where,
... )
>>> failed
<Statement reading ops.job_runs - print(to_hive(s)) shows its Hive>

Nothing has run yet: `failed` holds the Statement, ready to become Hive. Most of the time you
write the Clauses straight into `statement(...)`, as every Statement after this one does; it is
the same Statement.

Done when `failed` shows `<Statement reading ops.job_runs - ...>`. Then step 6.

### 6. Read its Hive

Goal: see exactly what the warehouse will be asked. `to_hive` gives the Hive as text, a `str`,
exactly what `run_query` sends. `print` shows it as it is, one clause to a line:

>>> hive = to_hive(failed)  # -> str
>>> print(hive)
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.status = 'FAILED' AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'

`FROM ops.job_runs AS job_runs` reads the table and calls it job_runs, which is why every
column in the Hive starts with `job_runs.`, just as it does in your Python. The two Conditions
are joined with AND.

Done when the Hive's WHERE holds both Conditions, joined with AND. Then step 7.

### 7. Print it ready to paste

Goal: Hive you can paste into Hue, Beeline or DBeaver. `show_hive` prints the same Hive with a
`;` at the end, which those programs need to tell one query from the next. It gives the text
back too, so `text` keeps it to save or use again:

>>> text = show_hive(failed)  # -> str
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.status = 'FAILED' AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24';

In a notebook you can also write `show_hive(failed)` on a line of its own: it prints the Hive
once, and the text it gives back isn't shown a second time. Given several Statements, it prints
them all, ready to paste as one script, each headed by a `--` comment line: its number, such
as `-- 1 of 2`, then the name of the variable it is in, when it is in one, such as
`-- 1 of 2: failed`.

Done when the printed Hive ends with `;`. Then step 8.

### 8. Run it

Goal: the rows, as a DataFrame. `run_query` turns the Statement into Hive, hands it to your
`query`, and gives back the DataFrame `query` returns. Call `run_query` for a Statement that
reads rows:

>>> result = run_query(failed, query)  # -> DataFrame
>>> result
   run_id  job_id          dt
0      97       3  2026-09-23
1     102       2  2026-09-24

The column names are the Statement's. From here it is pandas, such as `result["run_id"]`. A
Statement that writes a table goes to your execute instead, with `run_execute`, which gives
back nothing, as [Save a table](#save_a_table) shows.

Done when the result holds runs 97 and 102. Then step 9.

### 9. Keep only the rows you want

Goal: the Conditions for any question you ask. `WHERE` takes any number of Conditions. Each
function below makes one:

- `equals` and `not_equals` test one value;
- `at_least` (>=), `at_most` (<=), `more_than` (>) and `less_than` (<) compare with a number,
  and `between` keeps a range, both ends included;
- `is_in` and `is_not_in` test against a Python list;
- `contains` and `starts_with` test text;
- `is_null` and `is_not_null` find missing values, NULL;
- `any_of` keeps a row where at least one of its Conditions holds, SQL's OR, and `all_of`
  groups Conditions that must all hold, for use inside `any_of`.

The runs on 2026-09-24 of jobs 1 and 3 that took 20 minutes or more, each Condition on one
line:

>>> long_runs = statement(  # -> Statement
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24"),
...           is_in(job_runs.job_id, [1, 3]),
...           at_least(job_runs.duration_mins, 20)),
... )
>>> text = show_hive(long_runs)
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24'
  AND job_runs.job_id IN (1, 3)
  AND job_runs.duration_mins >= 20;
>>> run_query(long_runs, query)
   run_id  job_id  duration_mins
0     103       3             30
1     104       1             40

The runs that failed or took 30 minutes or more, with `any_of`. The Hive puts brackets around
the OR, so the filter on dt still holds for every row kept:

>>> to_check = statement(  # -> Statement
...     SELECT(job_runs.run_id, job_runs.status, job_runs.duration_mins),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           any_of(equals(job_runs.status, "FAILED"), at_least(job_runs.duration_mins, 30))),
... )
>>> text = show_hive(to_check)
SELECT
  job_runs.run_id,
  job_runs.status,
  job_runs.duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
  AND (
    job_runs.status = 'FAILED' OR job_runs.duration_mins >= 30
  );
>>> run_query(to_check, query)
   run_id   status  duration_mins
0      97   FAILED             30
1     102   FAILED             20
2     103  SUCCESS             30
3     104  SUCCESS             40

Run 98 is still running, so its status is missing: NULL in Hive, which pandas shows as NaN, or
as None in a column that holds nothing else. `is_null` finds it:

>>> still_running = statement(  # -> Statement
...     SELECT(job_runs.run_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"), is_null(job_runs.status)),
... )
>>> run_query(still_running, query)
   run_id status
0      98   None

ops.jobs isn't partitioned, so a Statement on it needs no filter at all. `contains` keeps the
jobs whose name holds a piece of text, matched exactly as you give it, capitals and all:

>>> sync_jobs = statement(  # -> Statement
...     SELECT(ops.jobs.job_id, ops.jobs.job_name),
...     FROM(ops.jobs),
...     WHERE(contains(ops.jobs.job_name, "sync")),
... )
>>> text = show_hive(sync_jobs)
SELECT
  jobs.job_id,
  jobs.job_name
FROM ops.jobs AS jobs
WHERE
  jobs.job_name LIKE '%sync%';
>>> run_query(sync_jobs, query)
   job_id      job_name
0       2  invoice_sync

Done when each Statement gives the rows shown under it. Then step 10.

### 10. Name a column in the result

Goal: a result column named as you want. `AS` gives a column the name you want in the result,
here `"minutes"` in place of `"duration_mins"`. `WHERE` still tests `job_runs.duration_mins`:
the new name is the result's, and `WHERE` reads the table.

>>> minutes_named = statement(  # -> Statement
...     SELECT(job_runs.run_id, AS(job_runs.duration_mins, "minutes")),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24"), at_least(job_runs.duration_mins, 30)),
... )
>>> run_query(minutes_named, query)
   run_id  minutes
0     103       30
1     104       40

Done when the result's second column is named minutes. Then step 11.

### 11. Select every column

Goal: every column of a table, named one by one. `all_columns` gives a Table's Columns as a
Python list, in the table's order, and `SELECT` takes a list as well as single Columns. Hive's
`SELECT *` would ask for whatever the table holds on the day it runs, so a column added later
would quietly change your result; a list of names keeps your result the same:

>>> every_column = all_columns(job_runs)  # -> list[Column]
>>> every_column
[job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
    job_runs.avg_retry_secs, job_runs.dt]

Done when `every_column` lists the table's six Columns. Then step 12.

### 12. Select columns by their names

Goal: Columns chosen by names you hold as text, from a list in your settings or another
table's columns. Python's own `getattr` takes each Column by its name:

>>> wanted = ["run_id", "status", "duration_mins"]
>>> chosen = [getattr(job_runs, name) for name in wanted]  # -> list[Column]
>>> chosen_runs = statement(  # -> Statement
...     SELECT(chosen),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-23")),
... )
>>> run_query(chosen_runs, query)
   run_id   status  duration_mins
0      95  SUCCESS             12
1      96  SUCCESS             18
2      97   FAILED             30
3      98      NaN             15
4      99     TEST              5

Done when the result's columns are run_id, status and duration_mins. Then step 13.

### 13. Take a first look at a table

Goal: a quick look at a big table. `first_look` builds a Statement that reads every column and
the first 20 rows the warehouse comes to: `LIMIT 20` stops the read early. Which 20 a big table
gives is up to the warehouse:

>>> text = show_hive(first_look(job_runs))
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.status,
  job_runs.duration_mins,
  job_runs.avg_retry_secs,
  job_runs.dt
FROM ops.job_runs AS job_runs
LIMIT 20;

Done when the Hive ends with `LIMIT 20;`. Then check it worked, below.

## Check it worked

Check a Statement's rows against the same Conditions worked out in pandas, on every row of the
Partitions it reads. Here, `to_check`: the runs that failed or took 30 minutes or more.

>>> every_run = run_query(statement(  # -> DataFrame
...     SELECT(all_columns(job_runs)),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... ), query)
>>> in_pandas = every_run[(every_run["status"] == "FAILED")
...                       | (every_run["duration_mins"] >= 30)]
>>> sorted(in_pandas["run_id"]) == sorted(run_query(to_check, query)["run_id"])
True

Both lists are sorted first: without `ORDER_BY`, the warehouse may give the rows in any order.
At work, run this check on a Partition small enough to look at, and look at a few of the rows
left out too. Before you go on, check that:

- `print(to_hive(failed))` shows a WHERE that filters dt;
- `run_query(failed, query)` gives runs 97 and 102;
- the comparison with pandas above shows `True`.

## Common mistakes

### A Statement that doesn't filter a partition column

A Statement that filters none of a partitioned table's partition columns would read every
Partition the table holds. The Toolbox refuses it as you build it, before anything runs:

>>> every_failed_run = statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(equals(job_runs.status, "FAILED")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.LoadRefused:
  What happened:  FROM(job_runs) reads ops.job_runs, but filters none of its partition columns:
                  dt.
...
  Opt-out:        FROM(job_runs, reads_all_partitions=True)

This is a Load limit: a check that protects the cluster, not the answer. Filter the partition
column as the message says, as `failed` does. The Opt-out, `reads_all_partitions=True`, reads
every Partition: keep it for a small table you truly need whole.
[Count, join and stay safe](#count_join_and_stay_safe) shows the other Load limits.

### Giving run_query the Hive text

`run_query` takes the Statement and makes the Hive itself, so it can check it first. Given the
text, it stops:

>>> run_query(hive, query)
Traceback (most recent call last):
...
TypeError:
  What happened:  run_query was given "SELECT...", which isn't a Statement.
...

Pass the Statement itself: `run_query(failed, query)`. Your query works the other way round:
it takes Hive text, a `str`.

### Comparing with None

`equals(job_runs.status, None)` looks like the way to find run 98, but in SQL nothing equals
NULL, not even NULL, so it would keep no rows at all. The Toolbox stops it with a Guard, a
check that refuses a Statement that would give a wrong result:

>>> equals(job_runs.status, None)
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  equals(job_runs.status, None) compares with None.
...

Write `is_null(job_runs.status)`, as `still_running` does. A None in a list given to `is_in`
stops the same way.

### Expecting not_equals to keep NULL

pandas' `!=` keeps a row whose value is missing; SQL's `<>`, which `not_equals` writes, drops
it. Leaving out the TEST runs on 2026-09-23 also leaves out run 98, still running:

>>> not_test = statement(
...     SELECT(job_runs.run_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-23"), not_equals(job_runs.status, "TEST")),
... )
>>> run_query(not_test, query)
   run_id   status
0      95  SUCCESS
1      96  SUCCESS
2      97   FAILED

Nothing stops this, since the Toolbox can't know which columns may be NULL. To keep run 98,
ask for the NULL rows too:
`any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))`.

### A value of the wrong type

`job_runs.job_id` holds numbers. Comparing it with text, as if `"3"` were 3, would leave the
warehouse to convert one into the other, which can quietly match nothing. The Toolbox stops it:

>>> equals(job_runs.job_id, "3")
Traceback (most recent call last):
...
TypeError:
  What happened:  equals(job_runs.job_id, ...) compares job_runs.job_id, a bigint column, with
                  '3'.
...

Write the value in the column's type: `equals(job_runs.job_id, 3)`.

## Next

- Count and add up per group, join tables without counting a row twice, and read what the
  Toolbox says when it stops a Statement:
  [Count, join and stay safe](#count_join_and_stay_safe).
- Write the rare Hive the Toolbox has no function for, with your Table references in it:
  [Hand-written Hive with your Table references](#hand_written_hive_with_your_table_references).
- The gallery's Worked examples of [`statement`](examples.html#statement),
  [`to_hive`](examples.html#to_hive), [`show_hive`](examples.html#show_hive),
  [`run_query`](examples.html#run_query) and each Condition, such as
  [`between`](examples.html#between), [`is_in`](examples.html#is_in) and
  [`any_of`](examples.html#any_of), and the traps beside their fixes:
  [`not_equals` drops NULL](examples.html#not_equals_drops_null) and
  [None in `equals`](examples.html#none_in_equals).
"""
