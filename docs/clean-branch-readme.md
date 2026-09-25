# SQL Composer

This is <!-- VERSION -->.

Write Hive SQL as Python. You put clause functions (`SELECT`, `FROM`, `WHERE`, ...) together in
SQL order, and the Toolbox writes the Hive string. It refuses a Statement that would silently
give a wrong number, or read or return too much, and says what to change.

## Install

You need Python 3.11 or newer, with pandas, numpy and sqlglot 25.24.2 or newer (below 31).

1. Download this branch as a zip and extract it.
2. Copy the `sql_composer` folder into the folder that holds your notebooks and scripts.

Keep your own scripts beside the `sql_composer` folder, never inside it, and import from the
folder's top level:

```python
from sql_composer import statement, SELECT, FROM, WHERE, equals, to_hive, run
```

## Update

1. Delete the `sql_composer` folder.
2. Copy in the new one.
3. Restart the kernel, which still holds the old code.

None of your own files are inside the folder, so deleting it is safe. When it is imported, the
folder checks itself, and stops with a plain message if a file is missing, extra, or from
another version. `sql_composer.VERSION` says which copy you have, and `sql_composer/CHANGES.md`
says what changed in each version.

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

At work, `run(first, send=...)` sends the Hive through your own `send`: a function that takes a
Hive string and returns a DataFrame. On the Example database, its own `send` runs it (this needs
sqlglot 30.19.0 or newer):

```python
>>> from sql_composer import run
>>> run(first, send=example_database.send)
   run_id   status
0     101  SUCCESS
1     102   FAILED
2     103  SUCCESS
3     104  SUCCESS
```

Every name in the cheat sheet has a Worked example like this in its docstring, which
`help(to_hive)` shows.

## Cheat sheet

Everything the Toolbox offers, one line each, grouped by the file it lives in. Import every name
from `sql_composer` itself, never from one of its files.

<!-- CHEAT SHEET -->
