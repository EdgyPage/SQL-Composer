# sqlglot Composer

This is version <!-- VERSION -->.

Write Hive SQL as Python. You put clause functions (`SELECT`, `FROM`, `WHERE`, ...) together in
SQL order, and the Toolbox writes the Hive string. It refuses a Statement that would silently
give a wrong number, or read or return too much, and says what to change.

This page is a tutorial: eight steps, from installing the Toolbox, through a Saved table written
every day and the Lineage of each of its columns, to a project of your own. Most steps point to the how-to that walks
through them in full, on `sqlglot_composer/how_to.html`, a page in the download to open in your
browser. What changed in each
version, and how to update from it, is in `CHANGES.md`.

## 1. Install

The Toolbox needs Python 3.11 or newer, pandas, numpy and sqlglot, and is tested on Python 3.12,
which `requirements.txt`'s pins are for. It is one folder, `sqlglot_composer`.

1. Download this branch as a zip and extract it.
2. Install what the Toolbox needs, at the versions it is tested on: run
   `pip install -r requirements.txt` in the download's top folder, or, from a notebook,
   `%pip install -r` followed by the path to that file.
   - On Python 3.11, numpy 2.5.4 can't install: change its line in `requirements.txt` to
     `numpy==2.4.6`, which pandas 3.0.6 runs on there, before you run pip.
   - A package your notebook already has, such as pandas, needn't be installed again: delete
     its line, so pip doesn't replace it. The Toolbox works with any sqlglot from 25.24.2 up to
     (not including) 31, whose Example database and a struct column in create_table need
     30.19.0 or newer.
3. Copy the whole `sqlglot_composer` folder into the folder that holds your notebooks and
   scripts. Keep your own scripts beside it, never inside it.

The download's two other folders, `example_projects` and `templates`, are for reading and
copying from, and the Toolbox doesn't need them: see [Example projects](#example-projects) and
[Templates](#templates).

## 2. Start a notebook

Import from `sqlglot_composer`, at its top level, never from a file inside it:

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, equals, to_hive, run
```

The Toolbox never connects to anything itself: it writes Hive as text, and `run` hands that text
to a function of yours, `send`, which runs it and gives back a pandas DataFrame. From a query
API, `send` is such as `lambda hive: pd.DataFrame(my_api.query(hive))`; from a notebook with a
`spark` session that reads the warehouse's tables, it is `lambda hive: spark.sql(hive).toPandas()`
(see [If your send runs the Hive on Spark](#if-your-send-runs-the-hive-on-spark)).

The how-to [Start a notebook](../sqlglot_composer/how_to.html#start_a_notebook) walks through the
first cells, your send among them, and the mistakes people make first.

## 3. A first Statement

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

`run(first, send=...)` sends the Hive through a `send`. On the Example database, its own `send`
runs it:

```python
>>> from sqlglot_composer import run
>>> run(first, send=example_database.send)
   run_id   status
0     101  SUCCESS
1     102   FAILED
2     103  SUCCESS
3     104  SUCCESS
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

How-to: [Build a first Statement and paste its Hive](../sqlglot_composer/how_to.html#build_a_first_statement).

## 4. Your own tables

A Statement reads your tables through their Table references: each table's columns, their
types, its Date partition (the date column it is stored by, a day at a time) and its Key (the
columns that name one row). `write_table_reference("your_db.your_table", send=...)`
asks the table for its columns and writes the file for you; you fill in what it can't know.

How-tos: [Import a table's column names programmatically](../sqlglot_composer/how_to.html#import_column_names),
then [Describe a table by hand](../sqlglot_composer/how_to.html#describe_a_table_by_hand) for a
table you can't read yet.

## 5. Filter, count and join

How-tos: [Filter rows](../sqlglot_composer/how_to.html#filter_rows),
[Count and add up per group](../sqlglot_composer/how_to.html#count_and_add_up_per_group) and
[Join tables safely](../sqlglot_composer/how_to.html#join_tables_safely). Each shows the Guard
(a refusal) or Warning that stops or flags a Statement that would give a wrong number, and why;
[Guards, Warnings and opt-outs](../sqlglot_composer/how_to.html#guards_warnings_and_opt_outs)
covers them all.

## 6. Save a table, every day

A Saved table is a table of yours that a Statement writes, a day at a time, so a number worked
out once a day is read by everyone after. Hive can't change single rows of such a table, so the
Toolbox has no `UPDATE`, `DELETE`, `MERGE` or `TRUNCATE`: a day is written again, whole, with
`INSERT_OVERWRITE`, which replaces it, and old days go with `admin.drop_days`.

How-tos: [Save a table](../sqlglot_composer/how_to.html#save_a_table),
[Backfill a range of days](../sqlglot_composer/how_to.html#backfill_a_range_of_days) and
[Run a daily pipeline](../sqlglot_composer/how_to.html#run_a_daily_pipeline).

## 7. Where each column comes from

`export_lineage(...)` writes an HTML page and a Markdown twin that follow each output column
back to the table columns it reads, across the Saved tables of a whole pipeline.

How-tos: [Lineage of one Statement](../sqlglot_composer/how_to.html#lineage_of_one_statement) and
[Lineage of a pipeline across Saved tables](../sqlglot_composer/how_to.html#lineage_of_a_pipeline_across_saved_tables).

## 8. Lay out a project

Your own scripts sit in three Levels, each importing only from those below it: Table
references, Building blocks (pieces several Statements share) and Statements, with a script
that runs the Statements in order. The [Example projects](#example-projects) show the
layout filled in, and the [Templates](#templates) are its empty shapes, to copy.

## The how-tos

Every how-to walks through one job from start to finish, in steps you paste into one notebook,
in order: its goal, its steps, each run on the Example database with what it shows, how to check
it worked, and the mistakes people make first. The Getting started how-tos take you from your
first notebook to a daily pipeline and its Lineage; the Intermediate ones are for work over many
days and many tables: days written another way, week and month totals, rows that come in late,
pipelines of Saved tables, quality checks, testing, how a Saved table is stored and its Key,
Session settings and the admin module, more joins, looking across rows, reconciling two tables,
subtotals, and keeping reads fast.

<!-- HOW-TOS -->

## The Example gallery

`sqlglot_composer/examples.html` is the Example gallery: every Worked example on one page, its
Python and, for each Statement it builds, the Hive and any result. Open it in your browser. It
needs nothing else: a box at the top keeps only the examples holding every word you type, and
Ctrl+F searches it too. Besides each docstring's example, it holds the Worked examples that
stand on their own: common jobs built in steps that each say why, such as building a Saved table
or finding rows with no match, and Statements that give a wrong number shown beside their fix.
Each result comes from the Example database or, where that can't run it, is computed in pandas.

## Example projects

An Example project is a folder of scripts laid out the way a project at work should be: Table
references, Building blocks, Statements, and a `run_pipeline.py` that runs them in order, all
written for the Example database's tables. `example_projects/` holds two:

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
step, in order, without sending anything (a dry run). Python must find the Toolbox's folder,
two folders up from a project's folder, so in that folder run, in bash:

```
PYTHONPATH=../.. python run_pipeline.py
```

In PowerShell, run `$env:PYTHONPATH = "..\.."` first, and in the Windows command prompt
`set PYTHONPATH=..\..`, then `python run_pipeline.py`.

To start a project of your own, copy one out of the download, put `sqlglot_composer` beside
its `run_pipeline.py`, then replace its tables and Statements with yours, or write its scripts
from the Templates below.

## Templates

A Template is the empty shape of one of your own scripts, to copy into your project and fill
in. Each placeholder, a word in angle brackets such as `<TABLE>`, is for you to replace,
brackets and all, with your own; Python stops at a placeholder left in, so a Template can't run
half filled in. Each Template's docstring says where in your project to copy it, lists its
placeholders under "Fill in:", with an example of each, and names the Example project file it
mirrors.

`templates/` holds a starter set and an intermediate set, and a `README.md` saying what each
Template needs first. Below, the starter set is listed in the order to use it.

<!-- TEMPLATES -->

## If your send runs the Hive on Spark

The Toolbox writes Hive. Spark runs nearly all of it as Hive does, but not quite all:

- With `spark.sql.ansi.enabled` on, Spark 4's default, Spark stops a whole query that divides by
  0, where Hive gives NULL. Where a divisor could be 0, run the Statement on Spark once before
  you rely on it.
- Spark reads a number such as 0.5 as an exact DECIMAL, where Hive reads a DOUBLE.
- A Saved table's Key in `CREATE TABLE`, `PRIMARY KEY (...) DISABLE NOVALIDATE`, is refused by
  Spark. Create your Saved tables where Hive runs, or ask whoever looks after the warehouse.
- `admin.drop_days`, which drops a range of old days at once, is Hive's: Spark refuses it, so
  ask whoever looks after your tables how old days are dropped there.

Check one setting once, by hand, in your notebook's Spark:
`spark.conf.get("spark.sql.parser.escapedStringLiterals")` should be `"false"`, Spark's default.
Set to `"true"`, Spark reads a backslash in a value as itself, so a value with a backslash in
it, and the `%` or `_` that `contains` and `starts_with` match as themselves, would come out
wrong. If it is `"true"`, ask whoever looks after your Spark whether it can be `"false"`, or run
`spark.conf.set("spark.sql.parser.escapedStringLiterals", "false")` in your notebook first.

Before you read or write a Saved table, check it isn't a Hive ACID table: one Hive keeps its
own way, so that single rows can be changed. Spark can't read or write those as it reads other
tables. `spark.sql("SHOW TBLPROPERTIES mart.daily_runs").toPandas()` lists a table's properties,
and an ACID table has `transactional` set to `true`. A table `create_table` makes is never
one, since Hive makes only its own managed tables ACID, and `create_table` makes external
ones. If a table you read is one, ask whoever looks after the warehouse for a table Spark can
read, one with `transactional` set to `false`.

## Update

1. Note which version you have: `sqlglot_composer.VERSION` says, such as
   `'sqlglot Composer 5.1, exported ...'`.
2. Delete the `sqlglot_composer` folder, and any `composer_core` folder beside it, left over from
   before 6.0. Using Spark Composer? Delete `spark_composer` too, and install sqlglot, as Install
   says.
3. From the new download, copy in the whole `sqlglot_composer` folder.
4. Restart the kernel, which still holds the old code.
5. In `CHANGES.md`, at the top of the download, read the "To update" part of every version newer
   than yours: the newest comes first, so start at your version's next and read up the page. From
   4.x to 6.0, that is 5.0's "To update from 4.x", then 6.0's "To update from 5.x". Each says what
   to change in your notebooks and files.

When it is imported, the folder checks itself. If a file is missing, extra, from another
version or another download, or from another Toolbox folder, or if this Python or the library
it needs won't work with it, the import stops and says what happened, why it matters and the
usual fix.

## License

The Toolbox, its Example projects and its Templates are under the MIT No Attribution license,
in `LICENSE`: use them, change them, share them or sell them, at work or anywhere else, with
no need to say where they came from, so you needn't copy `LICENSE` along with the folder.
They come as they are, with no warranty.

## Cheat sheet

Everything the Toolbox offers, one line each, grouped by the file of `sqlglot_composer` it
lives in. Import every name from `sqlglot_composer` itself, never from a file inside it.
Arithmetic isn't in it: a calculation uses Python's own `+ - * /` on columns, as in
`job_runs.duration_mins / 60`. The star import brings the 89 names listed here before the admin
module. The admin module's functions, which change your own Saved tables, come last: the star
import leaves them out, so import the module by name, `from sqlglot_composer import admin`, and
call `admin.drop_table(t)`.

<!-- CHEAT SHEET -->
