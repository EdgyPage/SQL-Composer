<!-- SQL Composer and Spark Composer 3.1, exported 2026-09-30 20:19 - generated from dev, do not edit -->
# SQL Composer and Spark Composer

This is version 3.1, exported 2026-09-30 20:19.

Write Hive SQL as Python. You put clause functions (`SELECT`, `FROM`, `WHERE`, ...) together in
SQL order, and the Toolbox writes the Hive string. It refuses a Statement that would silently
give a wrong number, or read or return too much, and says what to change.

## Which folder to copy

The Toolbox comes in two Editions, two folders with the same functions and the same version.
Copy one, the whole folder:

- **`sql_composer`, SQL Composer**, writes its Hive with the sqlglot package. Copy it when your
  notebook sends Hive to the warehouse through a query API of its own.
- **`spark_composer`, Spark Composer**, writes the same Hive itself and needs no sqlglot. Copy it
  when your notebook runs Spark, with a `spark` session that reads the warehouse's tables.

Both write the same Hive, except in the few places listed under
[Where the two Editions' Hive differs](#where-the-two-editions-hive-differs). Two of them,
dividing and a Python float, are for Spark. So if your query API runs Hive, SQL Composer's Hive
is right for it. If it runs Spark, and you can install pyspark, Spark Composer's Hive fits it
better, and works with any `send`. The third, a hive_function call, comes from sqlglot, which
only SQL Composer uses. Pick one per notebook: the two folders' objects don't mix.

This page writes `sql_composer`. With Spark Composer, write `spark_composer` wherever this page
writes `sql_composer`: in your imports, in `sql_composer.VERSION`, and in paths such as
`sql_composer/CHANGES.md`.

## Install

Each Edition needs Python 3.11 or newer, with pandas and numpy, and:

- SQL Composer: sqlglot 25.24.2 or newer, below 31. Its Example database runs queries on
  sqlglot 30.19.0 or newer, and so does a struct column in create_table, so install that:
  `%pip install "sqlglot>=30.19.0,<31"`.
- Spark Composer: pyspark 3.5.0 or newer, below 4.1: `%pip install "pyspark>=3.5.0,<4.1"`. Its
  Example database starts a Spark of its own, in a second Python in the background, so your
  `spark` is never touched. That Spark needs Java 17 to 21: set JAVA_HOME to it, or have `java`
  on the PATH.

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
2. From the new download, copy in the whole folder of the same name.
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

At work, `send` is your own, and a Statement reads your own tables: `write_table_reference`
writes the Table reference for one. With SQL Composer, `send` is whatever sends a Hive string to
your query API and gives back a pandas DataFrame, such as
`send=lambda hive: pd.DataFrame(my_api.query(hive))`. With Spark Composer, it is usually this,
with your notebook's own `spark` session:

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

The examples take today as 2026-09-25, the day after the Example database's last day.
`last_n_days(...)` counts back from your own today, so in a pasted example that uses it, write
`between(...)` with the days the example's Hive shows in its place, such as
`between(job_runs.dt, "2026-09-23", "2026-09-24")`, to get the rows it shows. `first_look(...)`
reads your own yesterday too, so pasted, its Hive shows another day, and no rows.

## The Example gallery

Each folder holds its own Example gallery: every Worked example on one page, its Python and,
for each Statement it builds, the Hive and any result. Open it in your browser. It needs nothing
else: a box at the top keeps only the examples holding every word you type, and Ctrl+F searches
it too. Besides each docstring's example, it holds the Worked examples that stand on their own:
common jobs built in steps that each say why, such as building a Saved table or finding rows
with no match, and Statements that give a wrong number shown beside their fix.

- `sql_composer/examples.html` shows each result from SQL Composer's Example database or, where
  that can't run it, computed in pandas.
- `spark_composer/examples.html` shows each result from Spark Composer's Example database,
  which runs Spark, and marks the places where Spark Composer's Hive differs.

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

- **Dividing by something that could be 0.** With ANSI on, Spark 4's default, Spark stops the whole query with an error when it divides by 0, where Hive gives NULL. So Spark Composer writes x / y as x / NULLIF(y, 0): NULLIF(y, 0) is NULL when y is 0, so that row gets NULL, as in Hive. A divisor that is a number other than 0 is written as it is. SQL Composer writes `SUM(job_runs.duration_mins) / COUNT(*)` where Spark Composer writes `SUM(job_runs.duration_mins) / NULLIF(COUNT(*), 0)`.
- **A Python float.** Spark reads 0.5 as a DECIMAL, an exact decimal that pandas gets as a Decimal, where Hive reads a DOUBLE, SQL's float. So Spark Composer writes a Python float as 0.5D: the D marks a DOUBLE, and doesn't mean days. A very small or very large float, which the Toolbox writes with an e, such as 1e-05, is a DOUBLE already. SQL Composer writes `COALESCE(job_runs.avg_retry_secs, 0.1)` where Spark Composer writes `COALESCE(job_runs.avg_retry_secs, 0.1D)`.
- **A hive_function call.** SQL Composer writes a hive_function call as sqlglot reads it back: sometimes by another name that does the same, such as COALESCE for nvl, and sometimes with an argument changed, such as a date_format pattern 'YYYY-MM' written 'yyyy-MM'. Spark Composer writes the call as you gave it, its name in capitals. So write 'yyyy' for the year in a date_format pattern: YYYY is the year a week belongs to, which Spark refuses in a pattern. And hive_function counts the arguments of the functions on its own list in both Editions; for any other function, SQL Composer refuses a call sqlglot can't build, and Spark Composer writes it, for Spark to refuse when it runs, as it does nvl2 with 1 argument, or to run, as it does unix_timestamp with none. SQL Composer writes `COALESCE(job_runs.status, 'none')` where Spark Composer writes `NVL(job_runs.status, 'none')`.

## Cheat sheet

Everything the Toolbox offers, one line each, grouped by the file it lives in. Import every name
from the folder itself, `sql_composer` or `spark_composer`, never from one of its files.
Arithmetic isn't in it: a calculation uses Python's own `+ - * /` on columns, as in
`job_runs.duration_mins / 60`.

### `__init__.py`

Write Hive SQL as Python, one clause function per SQL clause.

- `TOOLBOX_VERSION` = `'3.1'` - the feature number, raised only when a big feature lands.
- `VERSION` = `'SQL Composer 3.1, exported 2026-09-30 20:19'` - the full text, which also says when this copy was exported.

### `tables.py`

Table references: Table, and the functions that read, write and check one.

- `Table` - A Table reference: a table's columns, the day column it's split by, and its key.
- `write_table_reference` - Write a table's Table reference as `<table>.py` in the folder you're working in.
- `first_look` - A first look at a table: all its columns, and 20 of yesterday's rows.
- `check_key` - Check on the newest day that no two rows share the Table reference's key.
- `check_table_reference` - Compare a Table reference with its table as it is now, and list what differs.
- `create_table` - The CREATE TABLE Statement for a Saved table, one your Statements write into.
- `drop_table` - The DROP TABLE IF EXISTS Statement for a Saved table, from its Table reference.
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
- `WHERE` - Keep only the rows where every condition holds (they are joined with AND).
- `GROUP_BY` - Group rows that share these values, one output row per group.
- `HAVING` - Keep only the groups where every condition holds, tested after GROUP_BY.
- `ORDER_BY` - Sort the result; it needs a LIMIT, as sorting every row is slow, or use pandas.
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
- `row_number` - Number the rows of each PARTITION_BY group from 1, in ORDER_BY's order.
- `descending` - Sort by a column from largest to smallest, in ORDER_BY or row_number.
- `hive_function` - Call a Hive function the Toolbox doesn't wrap, with your text quoted for you.

### `running.py`

Running: turn a Statement into Hive, send it, split it by day, and set the load limits.

- `to_hive` - The Hive string for a Statement, ready to send.
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

### `example_database.py`

- `example_database` - The Example database: three made-up tables, and a send to run Statements on.
