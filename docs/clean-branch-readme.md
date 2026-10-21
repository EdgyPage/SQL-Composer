# sqlglot Composer

This is version <!-- VERSION -->.

Write Hive SQL as Python. You put clause functions (`SELECT`, `FROM`, `WHERE`, ...) together in
SQL order, and the Toolbox writes the Hive string. It refuses a Statement that would silently
give a wrong number, or read or return too much, and says what to change.

## Which folder to copy

Copy one folder, whole: `sqlglot_composer`, which writes its Hive with the sqlglot package and is
the folder you import.
Your notebook sends that Hive to the warehouse through a `send` of its own: a query API, or a
`spark` session (see [If your send runs the Hive on Spark](#if-your-send-runs-the-hive-on-spark)).

## Install

The Toolbox needs Python 3.11 or newer, pandas, numpy and sqlglot. It is tested on Python 3.12,
which `requirements.txt`'s pins are for.

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
   scripts.

The download's two other folders, `example_projects` and `templates`, are for reading and
copying from, and the Toolbox doesn't need them: see [Example projects](#example-projects) and
[Templates](#templates).

Keep your own scripts beside the folder, never inside it, and import from `sqlglot_composer`,
at its top level:

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, equals, to_hive, run
```

## Update

Updating from 5.x or 4.x, with a `composer_core` folder beside `sqlglot_composer`? Since 6.0
the Toolbox is one folder: in step 1 below, delete `composer_core` as well, and afterwards read
the 6.0 section of `CHANGES.md`, at the top of the download, for what else changed, such as
pandas 3 showing a missing text value as NaN. From 4.x, see [Update from 4.x](#update-from-4x) too. Updating from 3.x or SQL
Composer? See [Update from 3.x](#update-from-3x) instead, then [Update from 4.x](#update-from-4x)
too. Using Spark Composer? It was dropped in 6.0. Install sqlglot, as Install says, delete
`spark_composer` and `composer_core`, copy in `sqlglot_composer`, change each
`from spark_composer import` to `from sqlglot_composer import`, restart the kernel, and see
[If your send runs the Hive on Spark](#if-your-send-runs-the-hive-on-spark).

1. Delete the `sqlglot_composer` folder.
2. From the new download, copy in the whole `sqlglot_composer` folder.
3. Restart the kernel, which still holds the old code.

Keep your own files beside the folder, never inside it, so deleting it is safe. When it is
imported, the folder checks itself. If a file is missing, extra, from another version or another
download, or from another Toolbox folder, or if this Python or the library it needs won't work
with it, the import stops and says what happened, why it matters and the usual fix.
`sqlglot_composer.VERSION` says which copy you have, and `CHANGES.md` says what changed in each
version.

## Update from 4.x

5.0 checks more before it writes, so a notebook that ran on 4.x may need these changes. The
5.0 section of `CHANGES.md` says more about each.

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

Before 4.0, sqlglot Composer was one folder you copied on its own, with no `composer_core`, and
sqlglot Composer was named SQL Composer, in a folder named `sql_composer`. These steps are the
same from 3.0, 3.1 or 3.2. To update from SQL Composer:

1. Delete the `sql_composer` folder.
2. From the new download, copy in the whole `sqlglot_composer` folder.
3. In your notebooks and scripts, change every `sql_composer` to `sqlglot_composer`: change
   `from sql_composer import` to `from sqlglot_composer import`, and `sql_composer.VERSION` to
   `sqlglot_composer.VERSION`. That includes each Table reference file `write_table_reference`
   wrote for you: each has the line `from sql_composer import Table` below its docstring.
4. Restart the kernel.

Import every name from `sqlglot_composer` itself, never from a file inside it, so
`from sql_composer.refusals import GuardRefused` becomes `from sqlglot_composer import
GuardRefused`.

Two new refusals can stop code that ran on 3.x. `run` refuses a read whose `send` gives back
something other than a pandas DataFrame: if yours gives back a list of rows, end it with
`return pd.DataFrame(rows)`. And a comparison of two tables' days written different ways, such
as 20260925 and 2026-09-25, is refused. The 4.0 section of `CHANGES.md` lists these and
everything else that changed.

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
writes the Table reference for one. `send` is whatever sends a Hive string to your query API and
gives back a pandas DataFrame, such as `send=lambda hive: pd.DataFrame(my_api.query(hive))`.
Where your notebook has a `spark` session that reads the warehouse's tables, it is this:

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

`sqlglot_composer/examples.html` is the Example gallery: every Worked example on one page, its Python
and, for each Statement it builds, the Hive and any result. Open it in your browser. It needs
nothing else: a box at the top keeps only the examples holding every word you type, and Ctrl+F
searches it too. Besides each docstring's example, it holds the Worked examples that stand on
their own: common jobs built in steps that each say why, such as building a Saved table or
finding rows with no match, and Statements that give a wrong number shown beside their fix.
Each result comes from the Example database or, where that can't run it, is computed in pandas.

## How-tos

New to the Toolbox? After [A first Statement](#a-first-statement), start here. Beside each
Example gallery, `sqlglot_composer/how_to.html` is the how-to page, to open in your browser. A how-to walks through one job from
start to finish, in steps you paste into one notebook, in order: its goal, its steps, each run
on the Example database with what it shows, how to check it worked, and the mistakes people
make first.

The Getting started how-tos take you from your first notebook to a daily pipeline and its
Lineage. The Intermediate ones are for work over many days and many tables: days written
another way, week and month totals, rows that come in late, pipelines of Saved tables, quality
checks, testing, how a Saved table is stored and its Key, more joins, looking across rows,
reconciling two tables, subtotals, and keeping reads fast.

<!-- HOW-TOS -->

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

The Example database can't run a semi join, a Window or subtotals, and says so; the how-tos
show each result, computed in pandas.

## Keep reads and joins fast

What makes a Statement fast is reading only the days it needs, which every Load limit already
insists on, few large files, and statistics, from which Hive picks how to join.
`compute_statistics(t, day)` counts a day of a Saved table, `explain(s)` gives Hive's plan for a
Statement, and `repair_partitions(t)` adds the day folders it finds that the warehouse doesn't
list. The how-to "Keep reads and joins fast" puts them beside the Session settings that help.

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

## License

The Toolbox, its Example projects and its Templates are under the MIT No Attribution license,
in `LICENSE`: use them, change them, share them or sell them, at work or anywhere else, with
no need to say where they came from, so you needn't copy `LICENSE` along with the folder.
They come as they are, with no warranty.

## Cheat sheet

Everything the Toolbox offers, one line each, grouped by the file of `sqlglot_composer` it
lives in. Import every name from `sqlglot_composer` itself, never from a file inside it. Arithmetic isn't in it: a calculation uses
Python's own `+ - * /` on columns, as in `job_runs.duration_mins / 60`. The star import brings
the 89 names listed here before the admin module. The admin module's
functions, which change your own Saved tables, come last: the star import leaves them out, so
import the module by name, `from sqlglot_composer import admin`, and call `admin.drop_table(t)`.

<!-- CHEAT SHEET -->
