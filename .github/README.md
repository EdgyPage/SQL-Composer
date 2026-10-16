<!-- sqlglot Composer and Spark Composer 5.0, exported 2026-10-16 09:20 - generated from dev, do not edit -->
# sqlglot Composer and Spark Composer

This is version 5.0, exported 2026-10-16 09:20.

Write Hive SQL as Python. You put clause functions (`SELECT`, `FROM`, `WHERE`, ...) together in
SQL order, and the Toolbox writes the Hive string. It refuses a Statement that would silently
give a wrong number, or read or return too much, and says what to change.

## Which folders to copy

The Toolbox comes in two Editions, with the same functions and the same version. Whichever
you use, copy two folders, each whole: `composer_core`, the code both Editions share, and the
one Edition's own folder:

- **`sqlglot_composer`, sqlglot Composer**, writes its Hive with the sqlglot package. Copy it
  when your notebook sends Hive to the warehouse through a query API of its own.
- **`spark_composer`, Spark Composer**, writes the same Hive itself and needs no sqlglot. Copy it
  when your notebook runs Spark, with a `spark` session that reads the warehouse's tables.

Both write the same Hive, except in the few places listed under [Where the two Editions' Hive
differs](#where-the-two-editions-hive-differs). Three of them, dividing, a Python float and a
Saved table's Key in CREATE TABLE, are for Spark. So if your query API runs Hive, sqlglot
Composer's Hive is right for it. If it runs Spark, and you can install pyspark, Spark Composer's
Hive fits it better, and works with any `send`. The fourth, a hive_function call, comes from the
sqlglot library, which only sqlglot Composer uses. Use one Edition per notebook: importing both in one Python stops.

This page writes `sqlglot_composer`. With Spark Composer, write `spark_composer` wherever this
page writes `sqlglot_composer`: in your imports, and in `sqlglot_composer.VERSION`.

## Install

Each Edition needs Python 3.11 or newer, with pandas and numpy, and:

- sqlglot Composer: the sqlglot library, 25.24.2 or newer, below 31. sqlglot Composer's
  Example database runs queries on sqlglot 30.19.0 or newer, and so does a struct column in
  create_table, so install that:
  `%pip install "sqlglot>=30.19.0,<31"`.
- Spark Composer: pyspark 3.5.0 or newer, below 4.1: `%pip install "pyspark>=3.5.0,<4.1"`. Its
  Example database starts a Spark of its own, in a second Python in the background, so your
  `spark` is never touched. That Spark needs Java 17 to 21: set JAVA_HOME to it, or have `java`
  on the PATH.

1. Download this branch as a zip and extract it.
2. Copy the whole `composer_core` folder, and the whole `sqlglot_composer` folder or the whole
   `spark_composer` folder, side by side into the folder that holds your notebooks and scripts.

The download's two other folders, `example_projects` and `templates`, are for reading and
copying from, and the Toolbox doesn't need them: see [Example projects](#example-projects) and
[Templates](#templates).

Keep your own scripts beside the two folders, never inside them, and import from the
Edition's folder, at its top level:

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, equals, to_hive, run
```

## Update

Updating from 4.x? Copy the folders in as below, then see [Update from 4.x](#update-from-4x).
Updating from 3.x, SQL Composer or Spark Composer, with no `composer_core` folder? See
[Update from 3.x](#update-from-3x) instead, then [Update from 4.x](#update-from-4x) too.

1. Delete both folders: `composer_core` and your Edition's.
2. From the new download, copy in both whole folders of the same names.
3. Restart the kernel, which still holds the old code.

Keep your own files beside the folders, never inside them, so deleting them is safe. When they
are imported, the two folders check themselves. If a file is missing, extra, from another
version or another download, or from another Toolbox folder (`composer_core` or the other
Edition's), or if this Python or the library it needs won't work with it, the import stops and
says what happened, why it matters and the usual fix. `sqlglot_composer.VERSION` says which
copy you have, and `composer_core/CHANGES.md` says what changed in each version.

## Update from 4.x

5.0 checks more before it writes, so a notebook that ran on 4.x may need these changes. The
5.0 section of `composer_core/CHANGES.md` says more about each.

1. **A write into a Saved table with a Key may be refused.** Before 5.0, two rows with the same
   Key were saved without a word, since Hive never checks a Key. Now an `INSERT_OVERWRITE` or
   `INSERT_INTO` into a Saved table whose Table reference has `key=[...]` is refused unless
   the Toolbox can see that each row it writes has a Key of its own. The message says why its
   rows may repeat a Key, such as which join repeats them. Fix the write, or, if the rows are
   one per Key for a reason the Toolbox can't see, write
   `INSERT_OVERWRITE(t, unproven_key=True)` or `INSERT_INTO(t, unproven_key=True)`.
2. **Give each of your Saved tables' Table references a `location=`**: the folder your Saved
   tables go in, such as `location="/data/your_team/tables"`. create_table and the admin
   module refuse a Table reference without one. create_table now writes `CREATE EXTERNAL
   TABLE` with a `LOCATION` of `location=` followed by the table's own folder, such as
   `/data/your_team/tables/mart/daily_runs`. Writes don't need `location=`, so your writes
   work as before. A table made before 5.0 may be in a folder the warehouse chose, or share a
   folder with another table: once its reference has `location=`,
   `check_table_reference(t, send=...)` says so, and `admin.move_to_own_folder(t, send=...)`
   moves it when you choose to. A table you only read needs no `location=`.
3. **`drop_table` is now `admin.drop_table`.** Add `from sqlglot_composer import admin` below
   your star import, and write `admin.drop_table(t)` where you wrote `drop_table(t)`. Like the
   rest of the admin module, it needs the `location=` of step 2.
4. **The star import brings 26 new names.** If a variable of your own, set before the star
   import, has one of these names, give it another: `ANTI_JOIN`, `EXCEPT`, `FULL_JOIN`,
   `INTERSECT`, `RIGHT_JOIN`, `SEMI_JOIN`, `UNION`, `UNION_ALL`, `compute_statistics`, `cube`,
   `dense_rank`, `explain`, `first_value`, `grouping_sets`, `hive_settings`, `is_total`, `lag`,
   `last_value`, `lead`, `ntile`, `rank`, `repair_partitions`, `rollup`, `set_admin_log`,
   `unchecked_hive` and `window`.

## Update from 3.x

Before 4.0, each Edition was one folder you copied on its own, with no `composer_core`, and
sqlglot Composer was named SQL Composer, in a folder named `sql_composer`. These steps are the
same from 3.0, 3.1 or 3.2. To update from SQL Composer:

1. Delete the `sql_composer` folder.
2. From the new download, copy in the whole `composer_core` folder and the whole
   `sqlglot_composer` folder.
3. In your notebooks and scripts, change every `sql_composer` to `sqlglot_composer`: change
   `from sql_composer import` to `from sqlglot_composer import`, and `sql_composer.VERSION` to
   `sqlglot_composer.VERSION`. That includes each Table reference file `write_table_reference`
   wrote for you: each has the line `from sql_composer import Table` below its docstring.
4. Restart the kernel.

With Spark Composer, delete your `spark_composer` folder, then copy in the new one and the
`composer_core` folder beside it, and restart the kernel. Your `from spark_composer import`
lines stay as they are.

With either Edition, import every name from the Edition's folder itself, never from a file
inside it: the files inside moved to `composer_core`, so `from sql_composer.refusals import
GuardRefused` becomes `from sqlglot_composer import GuardRefused`. Importing both Editions in
one Python, which 3.x advised against, now stops: use one per notebook.

Two new refusals can stop code that ran on 3.x. `run` refuses a read whose `send` gives back
something other than a pandas DataFrame: if yours gives back a list of rows, end it with
`return pd.DataFrame(rows)`. And a comparison of two tables' days written different ways, such
as 20260925 and 2026-09-25, is refused. The 4.0 section of `composer_core/CHANGES.md`, where
the change notes now are, lists these and everything else that changed.

## A first Statement

The Example database ships inside the Toolbox: seven made-up tables, and a `send` that runs
Statements on them, so you can practise without touching the warehouse.

```python
>>> from sqlglot_composer import statement, SELECT, FROM, WHERE, equals, to_hive, example_database
>>> job_runs = example_database.job_runs
>>> first = statement(
...     SELECT(job_runs.run_id, job_runs.status),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
... )
>>> print(to_hive(first))
SELECT
  job_runs.run_id,
  job_runs.status
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24'
```

`run(first, send=...)` sends the Hive through a `send`: a function that takes a Hive string and
returns a pandas DataFrame. On the Example database, its own `send` runs it:

```python
>>> from sqlglot_composer import run
>>> run(first, send=example_database.send)
   run_id   status
0     101  SUCCESS
1     102   FAILED
2     103  SUCCESS
3     104  SUCCESS
```

At work, `send` is your own, and a Statement reads your own tables: `write_table_reference`
writes the Table reference for one. With sqlglot Composer, `send` is whatever sends a Hive
string to your query API and gives back a pandas DataFrame, such as
`send=lambda hive: pd.DataFrame(my_api.query(hive))`. With Spark Composer, it is usually this,
with your notebook's own `spark` session:

```python
result = run(first, send=lambda hive: spark.sql(hive).toPandas())
```

Every function and class in the cheat sheet has a Worked example like this in its docstring:
`help(to_hive)` shows the one for `to_hive`. The examples use every Toolbox name and the Example
database's `jobs` and `job_runs`, so run this first to paste one into a notebook:

```python
>>> from sqlglot_composer import *
>>> jobs, job_runs = example_database.jobs, example_database.job_runs
```

The examples take today as 2026-09-25, the day after the Example database's last day.
`last_n_days(...)` counts back from your own today, so in a pasted example that uses it, write
`between(...)` with the days the example's Hive shows in its place, such as
`between(job_runs.dt, "2026-09-23", "2026-09-24")`, to get the rows it shows. `first_look(...)`
reads your own yesterday too, so pasted, its Hive shows another day, and no rows.

## The Example gallery

Each Edition's folder holds its own Example gallery: every Worked example on one page, its Python
and, for each Statement it builds, the Hive and any result. Open it in your browser. It needs
nothing else: a box at the top keeps only the examples holding every word you type, and Ctrl+F
searches it too. Besides each docstring's example, it holds the Worked examples that stand on
their own: common jobs built in steps that each say why, such as building a Saved table or
finding rows with no match, and Statements that give a wrong number shown beside their fix.

- `sqlglot_composer/examples.html` shows each result from sqlglot Composer's Example database
  or, where that can't run it, computed in pandas.
- `spark_composer/examples.html` shows each result from Spark Composer's Example database,
  which runs Spark, and marks the places where Spark Composer's Hive differs.

## How-tos

New to the Toolbox? After [A first Statement](#a-first-statement), start here. Beside each
Example gallery, each Edition's folder holds a how-to page, `sqlglot_composer/how_to.html` and
`spark_composer/how_to.html`, to open in your browser. A how-to walks through one job from
start to finish, in steps you paste into one notebook, in order: its goal, its steps, each run
on the Example database with what it shows, how to check it worked, and the mistakes people
make first.

The Getting started how-tos take you from your first notebook to a daily pipeline and its
Lineage. The Intermediate ones are for work over many days and many tables: days written
another way, week and month totals, rows that come in late, pipelines of Saved tables, quality
checks, testing, how a Saved table is stored and its Key, more joins, looking across rows,
reconciling two tables, subtotals, and keeping reads fast.

Getting started, how-tos 1 to 18:

1. Start a notebook
2. Import a table's column names programmatically
3. Describe a table by hand
4. Build a first Statement and paste its Hive
5. Filter rows
6. Count and add up per group
7. Join tables safely
8. Reusable Derived tables (WITH ... AS in the Hive)
9. The latest row per key, and the top N per group
10. Save a table
11. Backfill a range of days
12. Run a daily pipeline
13. Lineage of one Statement
14. Lineage of a pipeline across Saved tables
15. Keep queries small with Load limits
16. Guards, Warnings and opt-outs
17. Generate Statements in a loop
18. Keep a Table reference true over time

Intermediate, how-tos 19 to 37:

19. A day written another way, and a second partition
20. Look things up as of a day
21. Week and month rollups
22. Incremental loads and late data
23. A pipeline of Saved tables
24. Share Building blocks between Statements
25. Check data quality with Statements
26. Generate Table references and Statements from settings
27. Call other Hive functions, and see where the Editions differ
28. Look across rows, then finish in pandas
29. Review a change with Lineage
30. Test your own Statements
31. Choose how a Saved table is stored
32. Keys, checked before each write
33. Semi-, anti- and full joins
34. Move a Saved table to its own folder
35. Reconcile two tables
36. Subtotals and grand totals
37. Keep reads and joins fast

## Your Saved tables: Keys and storage

A Saved table is one your own Statements write, a day at a time, or whole for a table with no
days (`date_partition=None`). Its Table reference says two things 5.0 relies on.

**Its Key**, `key=[...]`: the columns that tell its rows apart, such as
`key=["job_id", "dt"]` for one row per job per day. Hive never checks a Key, so the Toolbox
does, before each write: it refuses a write unless it can see that each row has a Key of its
own. It sees that from a GROUP_BY over the Key's columns, a SELECT_DISTINCT, a
`row_number(...)` kept at 1 in the Statement that reads its Derived table, or a FROM table
whose own Key gives one row per Key written, when each join matches the whole Key of the table
it joins. `unproven_key=True` on the write lets it through when you know better. The how-to
"Keys, checked before each write" shows each.

**Where it is stored**, `location=`: the folder your Saved tables go in. The Toolbox adds the
table's own folder to it, so each Saved table is an external table in a folder of its own, which
no other table reads or overwrites. `purge=True`, on the Table reference, has dropping the table
delete its files too; without it, the files stay behind. The Table reference can also give the
file format, Partitions inside each day and Buckets: the how-to "Choose how a Saved table is
stored" walks through them, and through why there are no indexes. Hive 3 has none: what makes a
read fast is reading only the days it needs, few large files, and statistics (see [Keep reads
and joins fast](#keep-reads-and-joins-fast)).

Hive can't change single rows of an external table, so the Toolbox has no `UPDATE`,
`DELETE`, `MERGE` or `TRUNCATE`: write a day again with `INSERT_OVERWRITE`, which replaces it,
or drop old days with `admin.drop_days`, which is Hive's: Spark refuses it, so if Spark runs
your tables, ask whoever looks after them how old days are dropped. A table with no days is written whole again with
`INSERT_OVERWRITE`, which replaces all its rows.

## Session settings, Hive by hand, and the admin module

A Session setting is a `SET` line Hive keeps for the rest of a session. `hive_settings(...)`
gives the lines of a named set, and `run(hive_settings(...), send=...)` sends them, one line
at a time: run it first, then your Statements. The Toolbox ships four sets, each explained in
`help(hive_settings)`: `"dynamic_partitions"`, `"map_joins"`, `"statistics_on_write"` and
`"merge_small_files"`. Keep your own in a settings.py of yours, and pass them to
`hive_settings` as `sets=`.

```python
>>> print(to_hive(hive_settings("map_joins")))
SET hive.auto.convert.join=true
SET hive.auto.convert.join.noconditionaltask=true
SET hive.ignore.mapjoin.hint=false
```

They hold only while your `send` keeps one session across its calls, as `spark.sql` does in
one notebook. If each call of your `send` opens a new session, as some query APIs do, each
`SET` is gone before your Statement runs: ask whoever looks after your query API.

For the one statement you need that no clause function writes yet, `unchecked_hive("...")`
runs Hive you write by hand. No Guard, Warning or Load limit looks inside it, and `show_hive`
says so.

The admin module changes your own Saved tables, with its checks: `admin.drop_table(t)`,
`admin.drop_days(t, before=...)`, `admin.add_columns(t, send=...)`,
`admin.set_properties(t)` and `admin.move_to_own_folder(t, send=...)`. The star import leaves
it out, so a notebook that changes a table says so at its top:

```python
from sqlglot_composer import admin
```

Each refuses a table that isn't one of your Saved tables, and `show_hive` prints what it changes
and what can't be undone before its Hive. Each `run` of one, or of an `unchecked_hive(...)`,
adds an entry to the Admin log, a file named admin_log.md in the folder of the notebook or
script that runs it: when, the call, the Hive sent, and whether it worked. `set_admin_log(path)`
keeps it elsewhere.

## Joins, Windows, Stacks and subtotals

Beside `JOIN`, `LEFT_JOIN` and `CROSS_JOIN`:

- `SEMI_JOIN(t, ON=...)` keeps each row that has a match in t, once; `ANTI_JOIN(t, ON=...)`
  keeps each row that has none; `FULL_JOIN(t, ON=...)` keeps the rows of both sides, matched or
  not, to compare two records of the same things. `RIGHT_JOIN` is refused: swap the tables and
  write `LEFT_JOIN`. `broadcast=True` asks Hive to copy a small joined table to every worker,
  which Hive heeds once the Session setting `"map_joins"` is sent. The how-to "Semi-, anti- and
  full joins" walks through them.
- A Window, `window(PARTITION_BY=..., ORDER_BY=..., rows=...)`, passed as `over=` to `sum_of`,
  `average_of`, `count_rows`, `min_of`, `max_of`, `rank`, `lag`, `lead` and the like, gives each
  row a value worked out across the rows near it: a running total, a moving average, a rank, or
  the value of the row before. The how-to "Look across rows, then finish in pandas" shows them.
- `UNION_ALL`, `UNION`, `INTERSECT` and `EXCEPT` stack whole Statements' rows, their columns
  matched by name (how-to "Reconcile two tables"), and `GROUP_BY(rollup(...))`, `cube(...)` and
  `grouping_sets(...)` add subtotal and grand total rows (how-to "Subtotals and grand totals").

sqlglot Composer's Example database can't run a semi join, a Window or subtotals, and says so;
Spark Composer's runs them all. The how-tos show each result either way.

## Keep reads and joins fast

What makes a Statement fast is reading only the days it needs, which every Load limit already
insists on, few large files, and statistics, from which Hive picks how to join.
`compute_statistics(t, day)` counts a day of a Saved table, `explain(s)` gives Hive's plan for a
Statement, and `repair_partitions(t)` adds the day folders it finds that the warehouse doesn't
list. The how-to "Keep reads and joins fast" puts them beside the Session settings that help.

## Example projects

An Example project is a folder of scripts laid out the way a project at work should be: Table
references, Building blocks, Statements, and a `run_pipeline.py` that runs them in order, all
written for the Example database's tables. Each Edition has two Example projects of its own,
written for it: `example_projects/sqlglot_composer/` and `example_projects/spark_composer/`
each hold

- `starter/`, on `ops.jobs`, `ops.job_runs` and `ops.run_alerts`. Examples 1 and 2 each save
  one day's numbers in a Saved table, and example 3 reads both to give each team's day.
- `intermediate/`, which builds on the starter project, on `ops.job_events`, `ops.job_owners`
  and `ops.region_costs`. Each run writes the last 3 days again, since rows can come in late.
  Example 1 saves each job's cost per day; example 2 saves each job's daily row beside the team
  that owned the job on that day; example 3 combines them into each team's days and weeks. It
  also has quality checks made from a few settings, and compares the Lineage before and after
  editing a Building block.

Each project's `README.md` says what each file is and how to run it. The Example database can
be read but not written, so running a project's `run_pipeline.py` prints the Hive of every
step, in order, without sending anything (a dry run). Python must find the Toolbox's two
folders, three folders up from a project's folder, so in that folder run, in bash:

```
PYTHONPATH=../../.. python run_pipeline.py
```

In PowerShell, run `$env:PYTHONPATH = "..\..\.."` first, and in the Windows command prompt
`set PYTHONPATH=..\..\..`, then `python run_pipeline.py`.

To start a project of your own, copy one out of the download, put `composer_core` and your
Edition's folder beside its `run_pipeline.py`, then replace its tables and Statements with
yours, or write its scripts from the Templates below.

## Templates

A Template is the empty shape of one of your own scripts, to copy into your project and fill
in. Each placeholder, a word in angle brackets such as `<TABLE>`, is for you to replace,
brackets and all, with your own; Python stops at a placeholder left in, so a Template can't run
half filled in. Each Template's docstring says where in your project to copy it, lists its
placeholders under "Fill in:", with an example of each, and names the Example project file it
mirrors.

`templates/sqlglot_composer/` and `templates/spark_composer/` each hold a starter set and an
intermediate set, and a `README.md` saying what each Template needs first. Below, the starter
set is listed in the order to use it.

In `starter/`:

- `starter/notebook_start.py` - A notebook's first cells: your send, a first Table reference, a first Statement.
- `starter/keep_table_references_true.py` - Writes the Table references of new tables, and compares those you keep with their tables.
- `starter/building_block.py` - A Building block: one row per group and day.
- `starter/saved_table_reference.py` - A Saved table's Table reference, by hand.
- `starter/saved_table.py` - A Saved table's steps: create, preview, write a day, backfill.
- `starter/daily_pipeline.py` - Every step for one day, in order.
- `starter/per_group_statement.py` - A Statement counting per group, keeping the groups that pass a test.

In `intermediate/`:

- `intermediate/incremental_load.py` - A Saved table whose every run writes the last few days again.
- `intermediate/incremental_pipeline.py` - Every step of a run, in order, for incremental loads.
- `intermediate/weekly_rollup.py` - Weekly totals, added up from a Saved table's days.
- `intermediate/as_of_lookup.py` - Rows counted by what a snapshot table said on their own day.
- `intermediate/building_blocks.py` - Building blocks built from other Building blocks: the keys missing on a day.
- `intermediate/quality_statements.py` - Repeated keys, NULL counts and rows per day, for one table.
- `intermediate/settings_driven.py` - The same Statements for many tables, made from settings.

## Before you use Spark Composer at work

Check one setting once, by hand, in your notebook's Spark:
`spark.conf.get("spark.sql.parser.escapedStringLiterals")` should be `"false"`, Spark's default.
Set to `"true"`, Spark reads a backslash in a value as itself, so a value with a backslash in
it, and the `%` or `_` that `contains` and `starts_with` match as themselves, would come out
wrong. If it is `"true"`, ask whoever looks after your Spark whether it can be `"false"`, or run
`spark.conf.set("spark.sql.parser.escapedStringLiterals", "false")` in your notebook first.

Two other settings may be either:

- `spark.sql.ansi.enabled`: with it on, Spark 4's default, Spark stops a query that divides by
  0, and Spark Composer writes a division so it gives NULL instead, as Hive does.
- `spark.sql.ansi.enforceReservedKeywords`: Spark Composer puts every word Spark reserves in
  backticks.

Before you read or write a Saved table, check it isn't a Hive ACID table: one Hive keeps its
own way, so that single rows can be changed. Spark can't read or write those as it reads other
tables. `spark.sql("SHOW TBLPROPERTIES mart.daily_runs").toPandas()` lists a table's properties,
and an ACID table has `transactional` set to `true`. A table `create_table` makes is never
one, since Hive makes only its own managed tables ACID, and `create_table` makes external
ones. If a table you read is one, ask whoever looks after the warehouse for a table Spark can
read, one with `transactional` set to `false`.

## Where the two Editions' Hive differs

Both Editions write the same Hive for a Statement, except in these places, each on purpose:

- **Dividing by something that could be 0.** With ANSI mode on (Spark's setting for following the SQL standard strictly), Spark 4's default, Spark stops the whole query with an error when it divides by 0, where Hive gives NULL. So Spark Composer writes x / y as x / NULLIF(y, 0): NULLIF(y, 0) is NULL when y is 0, so that row gets NULL, as in Hive. A divisor that is a number other than 0 is written as it is. sqlglot Composer writes `SUM(job_runs.duration_mins) / COUNT(*)` where Spark Composer writes `SUM(job_runs.duration_mins) / NULLIF(COUNT(*), 0)`.
- **A Python float.** Spark reads a number such as 0.5 as a DECIMAL, an exact decimal that pandas gets as a Decimal, where Hive reads a DOUBLE, SQL's float. So Spark Composer writes a Python float, such as 0.5, as 0.5D: the D marks a DOUBLE, and doesn't mean days. A very small or very large float, which the Toolbox writes with an e, such as 1e-05, is a DOUBLE already. sqlglot Composer writes `COALESCE(job_runs.avg_retry_secs, 0.1)` where Spark Composer writes `COALESCE(job_runs.avg_retry_secs, 0.1D)`.
- **A hive_function call.** sqlglot Composer writes a hive_function call as sqlglot reads it back: sometimes by another name that does the same, such as COALESCE for nvl, and sometimes with an argument changed, such as a date_format pattern 'YYYY-MM' written 'yyyy-MM'. Spark Composer writes the call as you gave it, its name in capitals. So write 'yyyy' for the year in a date_format pattern: YYYY is the year a week belongs to, which Spark refuses in a pattern. And hive_function counts the arguments of the functions on its own list in both Editions; for any other function, sqlglot Composer refuses a call sqlglot can't build, and Spark Composer writes it, for Spark to refuse when it runs, as it does nvl2 with 1 argument, or to run, as it does unix_timestamp with none. sqlglot Composer writes `COALESCE(job_runs.status, 'none')` where Spark Composer writes `NVL(job_runs.status, 'none')`.
- **A Saved table's Key in CREATE TABLE.** sqlglot Composer's create_table writes a Table reference's Key into the table as PRIMARY KEY (...) DISABLE NOVALIDATE, which Hive keeps for whoever reads the table and never checks. Spark refuses a PRIMARY KEY in CREATE TABLE, so Spark Composer leaves it out. Either way the Toolbox checks the Key itself, before each write. sqlglot Composer writes `runs BIGINT,
  PRIMARY KEY (job_id) DISABLE NOVALIDATE
)` where Spark Composer writes `runs BIGINT
)`.

## Cheat sheet

Everything the Toolbox offers, one line each, grouped by the file it lives in: the two constants
are in your Edition's folder, and every other name in a file of `composer_core`. Import every
name from your Edition's folder itself, `sqlglot_composer` or `spark_composer`: never from
`composer_core`, or from a file inside either folder. Arithmetic isn't in it: a calculation uses
Python's own `+ - * /` on columns, as in `job_runs.duration_mins / 60`. The star import brings
the 89 names listed here before the admin module. The admin module's
functions, which change your own Saved tables, come last: the star import leaves them out, so
import the module by name, `from sqlglot_composer import admin`, and call `admin.drop_table(t)`.

### `__init__.py`

Write Hive SQL as Python, one clause function per SQL clause.

- `TOOLBOX_VERSION` = `'5.0'` - the feature number, raised only when a big feature lands.
- `VERSION` = `'sqlglot Composer 5.0, exported 2026-10-16 09:20'` - the full text, which also says when this copy was exported.

### `tables.py`

Table references: Table, and the functions that read, write and check one.

- `Table` - A Table reference: a table's columns, the day column it's split by, and its key.
- `write_table_reference` - Write a table's Table reference as `<table>.py` in the folder you're working in.
- `first_look` - A first look at a table: all its columns, and 20 of yesterday's rows.
- `check_key` - Check on the newest day that no two rows share the Table reference's key.
- `check_table_reference` - Compare a Table reference with its table as it is now, and list what differs.
- `create_table` - The CREATE EXTERNAL TABLE Statement for a Saved table, in a folder of its own.
- `all_columns` - Every column of a Table reference, in its order, for SELECT instead of `*`.

### `clauses.py`

Clause functions: SELECT, FROM, JOIN, WHERE and the rest, assembled by statement(...).

- `SELECT` - The columns and named calculations a Statement returns; takes a list too.
- `SELECT_DISTINCT` - Like SELECT, but each different row comes back once.
- `AS` - Name a calculation, as AS(count_rows(), "runs"), or give a table a second name.
- `FROM` - The table a Statement reads; WHERE must bound its Date partition at both ends.
- `JOIN` - Add a second table's columns to the rows its ON= condition matches.
- `LEFT_JOIN` - Like JOIN, but rows with no match are kept, with NULL in the joined columns.
- `CROSS_JOIN` - Pair every row with every row of another table, with no ON=.
- `SEMI_JOIN` - Keep each row another table matches, once, adding none of that table's columns.
- `ANTI_JOIN` - Keep each row with no match in another table, such as the jobs that never ran.
- `FULL_JOIN` - Pair two tables' matching rows, and keep each table's rows with no match.
- `RIGHT_JOIN` - Refused: write LEFT_JOIN with the two tables swapped, which keeps the same rows.
- `WHERE` - Keep only the rows where every condition holds (they are joined with AND).
- `GROUP_BY` - Group rows that share these values, one output row per group.
- `HAVING` - Keep only the groups where every condition holds, tested after GROUP_BY.
- `ORDER_BY` - Sort the result; it needs a LIMIT, as sorting every row is slow, or use pandas.
- `LIMIT` - Return at most n rows.
- `INSERT_OVERWRITE` - Write rows into a Saved table, replacing one day, or the whole table.
- `INSERT_INTO` - Add rows to a Saved table's day, or to the table; sent twice, it adds twice.
- `statement` - Assemble clause functions, in SQL order, into a Statement.
- `derived` - Name a Statement so another Statement can read it like a table.

### `stacking.py`

Stacks and subtotals: UNION_ALL and the rest, rollup, cube, grouping_sets and is_total.

- `UNION_ALL` - Stack the rows of Statements one after another, keeping every row.
- `UNION` - Stack the rows of Statements, each different row once.
- `INTERSECT` - Keep the rows every Statement returns, each different row once.
- `EXCEPT` - Keep the first Statement's rows that no other Statement returns, each once.
- `rollup` - Subtotals for GROUP_BY: dropping its columns from the right, to a grand total.
- `cube` - Subtotals for GROUP_BY over every mix of the columns, and a grand total.
- `grouping_sets` - Subtotals for GROUP_BY: the groups of each listed set of columns, in one result.
- `is_total` - A condition true on a subtotal row that totals over every value of the column.

### `conditions.py`

Conditions: the tests that go in WHERE, HAVING and JOIN's ON=.

- `equals` - Rows where the column equals the value.
- `not_equals` - Rows where the column differs from the value; rows where it is NULL drop out.
- `is_null` - Rows where the column has no value (NULL).
- `is_not_null` - Rows where the column has a value (is not NULL).
- `at_least` - Rows where the column is greater than or equal to the value (>=).
- `at_most` - Rows where the column is less than or equal to the value (<=).
- `more_than` - Rows where the column is strictly greater than the value (>).
- `less_than` - Rows where the column is strictly less than the value (<).
- `between` - Rows where the column is from low to high, both ends included.
- `last_n_days` - Rows from the n days before today; today itself isn't included.
- `is_in` - Rows where the column is one of the values in a list.
- `is_not_in` - Rows where the column is none of the values; rows where it is NULL drop out.
- `contains` - Rows where the column contains your text, a % or _ in it matched as % or _.
- `starts_with` - Rows where the column starts with your text, a % or _ in it matched as % or _.
- `any_of` - Rows where at least one of the conditions holds (OR); takes a list too.
- `all_of` - Rows where every one of the conditions holds (AND), for use inside any_of.

### `calculations.py`

Calculations: counts and sums, row-level functions, and dates grouped into weeks and months.

- `count_rows` - The number of rows, or of the rows where a condition holds.
- `count_distinct` - The number of different values in a column, leaving out NULL.
- `sum_of` - The total of a column, or of its rows where a condition holds.
- `average_of` - The average of a column that isn't a division, an average or a distinct count.
- `min_of` - The smallest value in a column.
- `max_of` - The largest value in a column.
- `if_else` - One value where a condition holds and another where it doesn't (CASE WHEN).
- `fill_null` - The column, with a value put in where it is NULL (COALESCE).
- `week_start` - The Monday that starts each date's week, to group days into weeks.
- `month_start` - The first day of each date's month, to group days into months.
- `descending` - Sort by a column from largest to smallest, in ORDER_BY or a Window's ORDER_BY.
- `hive_function` - Call a Hive function the Toolbox doesn't wrap, with your text quoted for you.

### `windows.py`

Windows: a calculation over the rows around each row, such as a running total or a rank.

- `window` - The rows a calculation looks across for each row, passed to it as over=.
- `row_number` - Number the rows of each group from 1, in ORDER_BY's order.
- `rank` - Rank each row in its group from 1; rows that tie share a rank.
- `dense_rank` - Rank each row in its group from 1; ties share a rank, and the next follows on.
- `ntile` - Which of N nearly equal parts of its group each row falls in, 1 to N, in order.
- `lag` - The column's value on the row before each row in its group, in ORDER_BY's order.
- `lead` - The column's value on the row after each row in its group, in ORDER_BY's order.
- `first_value` - The column's value on the first row of each row's group, in ORDER_BY's order.
- `last_value` - The column's value on the last row of each row's group, in ORDER_BY's order.

### `running.py`

Running: turn a Statement into Hive, send it, split it by day, and set the load limits.

- `to_hive` - The Hive string for a Statement, ready to send.
- `show_hive` - Print the Hive that runs, ready to paste into another program, and return it.
- `run` - Send a Statement's Hive through your `send` function and return what comes back.
- `by_day` - Split a Statement into one Statement per day its FROM table reads, oldest first.
- `set_load_limits` - Switch on an automatic LIMIT and a cap on days per Statement; both start off.

### `refusals.py`

Guards and Load limits stop a Statement; a Warning shows at the join it's about.

- `GuardRefused` - A Guard stopped a Statement that would silently give a wrong answer.
- `LoadRefused` - A Load limit stopped a Statement that would read or return too much.

### `lineage.py`

Lineage: draw where each column comes from, as an HTML page and as Markdown.

- `export_lineage` - Write where each column comes from, as an HTML page and a Markdown twin.

### `unchecked.py`

Session settings, Unchecked statements and the Admin log: Hive sent as you chose it.

- `hive_settings` - The SET lines of Session settings, by name, to send before your Statements.
- `unchecked_hive` - Hive you write by hand, for run to send when no clause function writes it yet.
- `set_admin_log` - Set where the Admin log is written, such as ADMIN_LOG from your own settings.py.

### `upkeep.py`

Keeping reads and joins fast: repair_partitions, compute_statistics and explain.

- `repair_partitions` - The MSCK REPAIR TABLE Statement, which lists the days in a Saved table's folder.
- `compute_statistics` - The ANALYZE TABLE Statement, which counts a Saved table's rows for one day.
- `explain` - The EXPLAIN Statement: Hive's plan for running a Statement, without running it.

### `example_database.py`

- `example_database` - The Example database: seven made-up tables, and a send to run Statements on.

### `admin.py`

The admin module: changes to your own Saved tables, written and checked for you.

- `admin.drop_table` - Drop one of your Saved tables: the DROP TABLE IF EXISTS Statement.
- `admin.drop_days` - Drop a Saved table's days before a given day: an ALTER TABLE Statement.
- `admin.add_columns` - Add the new columns of a Saved table's Table reference to the table itself.
- `admin.set_properties` - Set a Saved table's properties as its Table reference gives them.
- `admin.move_to_own_folder` - Move a Saved table to a folder of its own: a list of Statements to run.
