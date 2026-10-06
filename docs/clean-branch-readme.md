# sqlglot Composer and Spark Composer

This is version <!-- VERSION -->.

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
differs](#where-the-two-editions-hive-differs). Two of them, dividing and a Python float, are
for Spark. So if your query API runs Hive, sqlglot Composer's Hive is right for it. If it runs
Spark, and you can install pyspark, Spark Composer's Hive fits it better, and works with any
`send`. The third, a hive_function call, comes from the sqlglot library, which only sqlglot
Composer uses. Use one Edition per notebook: importing both in one Python stops.

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

Updating a copy from before 4.0, with a `sql_composer` folder or no `composer_core` folder?
See [Update from 3.x](#update-from-3x) instead.

1. Delete both folders: `composer_core` and your Edition's.
2. From the new download, copy in both whole folders of the same names.
3. Restart the kernel, which still holds the old code.

Keep your own files beside the folders, never inside them, so deleting them is safe. When they
are imported, the two folders check themselves. If a file is missing, extra, from another
version or another download, or from another Toolbox folder (`composer_core` or the other
Edition's), or if this Python or the library it needs won't work with it, the import stops and
says what happened, why it matters and the usual fix. `sqlglot_composer.VERSION` says which
copy you have, and `composer_core/CHANGES.md` says what changed in each version.

## Update from 3.x

Before 4.0, the Toolbox was one folder, with no `composer_core`, and sqlglot Composer was named
SQL Composer, in a folder named `sql_composer`. To update from it:

1. Delete the `sql_composer` folder.
2. From the new download, copy in the whole `composer_core` folder and the whole
   `sqlglot_composer` folder.
3. In your notebooks and scripts, the Table reference files `write_table_reference` wrote for
   you included, change every `sql_composer` to `sqlglot_composer`: change
   `from sql_composer import` to `from sqlglot_composer import`, and `sql_composer.VERSION` to
   `sqlglot_composer.VERSION`. Each Table reference file it wrote has the line
   `from sql_composer import Table` below its docstring.
4. Restart the kernel.

With Spark Composer, delete your `spark_composer` folder, then copy in the new one and the
`composer_core` folder beside it, and restart the kernel. Your imports stay as they are.

Before 4.0, the two Editions could be imported in one Python. Now that stops: use one per
notebook. The 4.0 section of `composer_core/CHANGES.md` lists what else changed, such as the
new how-to page and what `run` now refuses.

## A first Statement

The Example database ships inside the Toolbox: six made-up tables, and a `send` that runs
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
checks and testing.

<!-- HOW-TOS -->

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

<!-- TEMPLATES -->

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
and an ACID table has `transactional` set to `true`. Hive 3 can make every new table one, so
check a table `create_table` made too. If a table is one, ask whoever looks after the warehouse
for a table Spark can write, one with `transactional` set to `false`.

## Where the two Editions' Hive differs

Both Editions write the same Hive for a Statement, except in these places, each on purpose:

<!-- DIFFERENCES -->

## Cheat sheet

Everything the Toolbox offers, one line each, grouped by the file it lives in: the two constants
are in your Edition's folder, and every other name in a file of `composer_core`. Import every
name from your Edition's folder itself, `sqlglot_composer` or `spark_composer`: never from
`composer_core`, or from a file inside either folder. Arithmetic isn't in it: a calculation uses
Python's own `+ - * /` on columns, as in `job_runs.duration_mins / 60`.

<!-- CHEAT SHEET -->
