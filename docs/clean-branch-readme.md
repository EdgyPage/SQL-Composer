# SQL Composer and Spark Composer

This is version <!-- VERSION -->.

Write Hive SQL as Python. You put clause functions (`SELECT`, `FROM`, `WHERE`, ...) together in
SQL order, and the Toolbox writes the Hive string. It refuses a Statement that would silently
give a wrong number, or read or return too much, and says what to change.

## Which folder to copy

The Toolbox comes in two Editions, two folders with the same functions, the same refusals and
the same version. Copy one, the whole folder:

- **`sql_composer`, SQL Composer**, writes its Hive with the sqlglot package. Copy it when your
  notebook sends Hive to the warehouse through a query API of its own.
- **`spark_composer`, Spark Composer**, writes the same Hive itself and needs no sqlglot. Copy it
  when your notebook runs Spark, with a `spark` session that reads the warehouse's tables.

Both write the same Hive, but in the few places listed under
[Where the two Editions' Hive differs](#where-the-two-editions-hive-differs). Pick one per
notebook: the two folders' objects don't mix.

This page writes `sql_composer`. With Spark Composer, write `spark_composer` wherever this page
writes `sql_composer`: in your imports, and in `sql_composer.VERSION`.

## Install

Each Edition needs Python 3.11 or newer, with pandas and numpy, and:

- SQL Composer: sqlglot 25.24.2 or newer, below 31. Its Example database runs queries on
  sqlglot 30.19.0 or newer.
- Spark Composer: pyspark 3.5.0 or newer, below 4.1. Its Example database starts a Spark of its
  own, apart from yours, which needs Java 17 to 21: set JAVA_HOME to it, or have `java` on the
  PATH.

1. Download this branch as a zip and extract it.
2. Copy the whole `sql_composer` folder, or the whole `spark_composer` folder, into the folder
   that holds your notebooks and scripts.

Keep your own scripts beside the folder, never inside it, and import from the folder's top
level:

```python
from sql_composer import statement, SELECT, FROM, WHERE, equals, to_hive, run
```

## Update

1. Delete the folder.
2. Copy in the new one, the whole folder, from the same folder of the download.
3. Restart the kernel, which still holds the old code.

Keep your own files beside the folder, never inside it, so deleting it is safe. When it is
imported, the folder checks itself. If a file is missing, extra, from another version or
export, or from the other folder, or if this Python or the library it needs won't work with it,
it stops and says what happened, why it matters and the usual fix. `sql_composer.VERSION` says
which copy you have, and `sql_composer/CHANGES.md` says what changed in each version.

## A first Statement

The Example database ships inside the Toolbox: three made-up tables, and a `send` that runs
Statements on them, so you can practise without touching the warehouse.

```python
>>> from sql_composer import statement, SELECT, FROM, WHERE, equals, to_hive, example_database
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
>>> from sql_composer import run
>>> run(first, send=example_database.send)
   run_id   status
0     101  SUCCESS
1     102   FAILED
2     103  SUCCESS
3     104  SUCCESS
```

At work, `send` is your own. With SQL Composer, it is whatever sends a Hive string to your query
API and gives back a DataFrame. With Spark Composer, it is usually this, with your notebook's
own `spark` session:

```python
result = run(first, send=lambda hive: spark.sql(hive).toPandas())
```

Every function and class in the cheat sheet has a Worked example like this in its docstring:
`help(to_hive)` shows the one for `to_hive`. The examples use every Toolbox name and the Example
database's `jobs` and `job_runs`, so run this first to paste one into a notebook:

```python
>>> from sql_composer import *
>>> jobs, job_runs = example_database.jobs, example_database.job_runs
```

## The Example gallery

Each folder holds its own Example gallery: every Worked example on one page, its Python and,
for each Statement it builds, the Hive and any result. Open it in your browser. It
needs nothing else: a box at the top keeps only the examples holding every word you type, and
Ctrl+F searches it too. It holds the docstrings' examples and the Worked examples on their own:
common jobs built in steps that each say why, such as building a Saved table or finding rows
with no match, and Statements that give a wrong number shown beside their fix.

- `sql_composer/examples.html` shows each result from SQL Composer's Example database or, where
  that can't run it, computed in pandas.
- `spark_composer/examples.html` shows each result from Spark Composer's Example database,
  which runs Spark, and marks the places where Spark Composer's Hive differs.

## Before you use Spark Composer at work

Check these once, by hand, in your notebook's Spark: Spark Composer's Hive relies on them.

- `spark.conf.get("spark.sql.parser.escapedStringLiterals")` is `"false"`, Spark's default.
  Set to `"true"`, Spark reads a backslash in a value as itself, so a value holding one, and
  the `%` or `_` that `contains` and `starts_with` match as themselves, would come out wrong.
- `spark.sql.ansi.enabled` may be either. With it on, Spark 4's default, Spark stops a query
  that divides by 0, and Spark Composer writes a division so it gives NULL instead, as Hive
  does.
- `spark.sql.ansi.enforceReservedKeywords` may be either: Spark Composer puts every word Spark
  reserves in backticks.
- Before writing a Saved table, check it isn't a Hive ACID table: Spark can't write those.
  `spark.sql("SHOW TBLPROPERTIES mart.daily_runs").toPandas()` lists a table's properties, and
  an ACID table has `transactional` set to `true`. Hive 3 can make every new table one, so
  check a table `create_table` made too.

## Where the two Editions' Hive differs

Both Editions write the same Hive for a Statement but in these places, each on purpose:

<!-- DIFFERENCES -->

## Cheat sheet

Everything the Toolbox offers, one line each, grouped by the file it lives in. Import every name
from the folder itself, `sql_composer` or `spark_composer`, never from one of its files.

<!-- CHEAT SHEET -->
