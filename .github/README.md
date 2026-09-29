<!-- SQL Composer 2.1, exported 2026-09-29 12:54 - generated from dev, do not edit -->
# SQL Composer

This is SQL Composer 2.1, exported 2026-09-29 12:54.

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

Keep your own files beside the folder, never inside it, so deleting it is safe. When it is
imported, the folder checks itself. If a file is missing, extra, or from another version or
export, or if this Python or its sqlglot won't work with it, it stops and says what happened,
why it matters and the usual fix. `sql_composer.VERSION` says which copy you have, and
`sql_composer/CHANGES.md` says what changed in each version.

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

Every function and class in the cheat sheet has a Worked example like this in its docstring:
`help(to_hive)` shows the one for `to_hive`. The examples use every Toolbox name and the Example
database's `jobs` and `job_runs`, so run this first to paste one into a notebook:

```python
>>> from sql_composer import *
>>> jobs, job_runs = example_database.jobs, example_database.job_runs
```

`sql_composer/examples.html` is the Example gallery: every Worked example on one page, its
Python and, for each Statement it builds, the Hive and any result, from the Example database
or, where the Example database can't run it, computed in pandas. It holds the docstrings'
examples and the Worked examples on their own: common jobs built in steps that each say why,
such as building a Saved table or finding rows with no match, and Statements that give a wrong
number shown beside their fix. Open it in your browser. It needs nothing else: a box at the top
keeps only the examples holding every word you type, and Ctrl+F searches it too.

## Cheat sheet

Everything the Toolbox offers, one line each, grouped by the file it lives in. Import every name
from `sql_composer` itself, never from one of its files.

### `__init__.py`

SQL Composer: write Hive SQL as Python, one clause function per SQL clause.

- `TOOLBOX_VERSION` = `'2.1'` - the feature number, raised only when a big feature lands.
- `VERSION` = `'SQL Composer 2.1, exported 2026-09-29 12:54'` - the full text, which also says when this copy was exported.

### `tables.py`

Table references: Table, and the functions that read, write and check one.

- `Table` - A Table reference: one table's columns and types, Date partition and key.
- `write_table_reference` - Write a new Table reference file for a table, from Hive's own description of it.
- `first_look` - A first look at a table: all its columns, and 20 of yesterday's rows.
- `check_key` - Check on the newest day that no two rows share the table's declared key.
- `check_table_reference` - Compare a Table reference with its table in Hive, and list what differs.
- `create_table` - The CREATE TABLE Statement for a Saved table, from its Table reference.
- `drop_table` - The DROP TABLE IF EXISTS Statement for a Saved table, from its Table reference.
- `all_columns` - Every column of a Table reference, in its order, for SELECT instead of `*`.

### `clauses.py`

Clause functions: SELECT, FROM, JOIN, WHERE and the rest, assembled by statement(...).

- `SELECT` - The columns and named calculations a Statement returns; takes a list too.
- `SELECT_DISTINCT` - Like SELECT, but each different row comes back once.
- `AS` - Give a calculation its name in the result, or a table a second name.
- `FROM` - The table a Statement reads; its Date partition must be bounded in WHERE.
- `JOIN` - Add a second table's columns to each row, matching rows by ON=.
- `LEFT_JOIN` - Like JOIN, but rows with no match are kept, with NULL in the joined columns.
- `CROSS_JOIN` - Pair every row with every row of another table, with no ON=.
- `WHERE` - Keep only the rows where every condition holds (they are joined with AND).
- `GROUP_BY` - Group rows that share these values, one output row per group.
- `HAVING` - Keep only the groups where every condition holds, tested after GROUP_BY.
- `ORDER_BY` - Sort the result; it needs a LIMIT, and sorting in pandas is usually better.
- `LIMIT` - Return at most n rows.
- `INSERT_OVERWRITE` - Write the Statement's rows into one day of a Saved table, replacing that day.
- `INSERT_INTO` - Add rows to a day of a Saved table, keeping its rows; sent twice, it adds twice.
- `statement` - Assemble clause functions, in SQL order, into a Statement.
- `derived` - Name a Statement so another Statement can read it like a table.

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
- `contains` - Rows where the column contains the text, with % and _ matched as themselves.
- `starts_with` - Rows where the column starts with the text, with % and _ matched as themselves.
- `any_of` - Rows where at least one of the conditions holds (OR); takes a list too.
- `all_of` - Rows where every one of the conditions holds (AND), for use inside any_of.

### `calculations.py`

Calculations: counts and sums, row-level functions, and dates grouped into weeks and months.

- `count_rows` - The number of rows, or of the rows where a condition holds.
- `count_distinct` - The number of different values in a column, leaving out NULL.
- `sum_of` - The total of a column, or of its rows where a condition holds.
- `average_of` - The average of a column; it refuses to average something that doesn't add up.
- `min_of` - The smallest value in a column.
- `max_of` - The largest value in a column.
- `if_else` - One value where a condition holds and another where it doesn't (CASE WHEN).
- `fill_null` - The column, with a value put in where it is NULL (COALESCE).
- `week_start` - The Monday that starts each date's week, to group days into weeks.
- `month_start` - The first day of each date's month, to group days into months.
- `row_number` - Number the rows within each group from 1, in the order you give.
- `descending` - Sort by a column from largest to smallest, in ORDER_BY or row_number.
- `hive_function` - Call a Hive function the Toolbox doesn't wrap, with its arguments escaped.

### `running.py`

Running: turn a Statement into Hive, send it, split it by day, and set the load limits.

- `to_hive` - The Hive string for a Statement, ready to send.
- `run` - Send a Statement's Hive through your `send` function and return what comes back.
- `by_day` - Split a Statement into one Statement per day of its date bound, oldest first.
- `set_load_limits` - Switch on an automatic LIMIT and a cap on days per Statement; both start off.

### `refusals.py`

Every Guard, Load limit and Warning in one file, with GuardRefused and LoadRefused.

- `GuardRefused` - A Guard stopped a Statement that would silently give a wrong answer.
- `LoadRefused` - A Load limit stopped a Statement that would read or return too much.

### `lineage.py`

Lineage: draw where each column comes from, as an HTML page and as Markdown.

- `export_lineage` - Write where each column comes from, as an HTML page and a Markdown twin.

### `example_database.py`

- `example_database` - The Example database: three made-up tables, and a send to run Statements on.
