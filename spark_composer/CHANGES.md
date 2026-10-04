<!-- Spark Composer 3.2, exported 2026-10-04 00:28 - generated from dev, do not edit -->
# Changes

What changed in each Toolbox version, in plain words. The newest version comes first.

## 3.2

- **hive_function("date_sub", ...) goes back by the whole day count.** With sqlglot older than
  version 30, hive_function("date_sub", job_runs.dt, job_runs.duration_mins + 1) moved the day
  forward by duration_mins - 1, not back by duration_mins + 1: the Hive left the count
  unbracketed. The Edition that prints its own Hive always wrote it right.
- **The Example database reads a table's name whatever its case**, as Hive and Spark do:
  OPS.jobs is ops.jobs.
- **write_table_reference points to the other partition columns** when the first holds no day
  it can bound, as for a table partitioned by region, then dt.
- **LEFT_JOIN lets through a WHERE that keeps the rows with no match**, such as
  any_of(is_null(job_runs.run_id), equals(job_runs.status, "FAILED")): jobs that never ran, or
  whose run failed. Before, only a bare is_null was let through, and the fix offered, moving
  the condition into ON=, changed the answer.
- **A join still sees its key when ON= puts it inside a saved condition**: if ON=all_of(...)
  holds a Building block that has the equals(...) on the key, the join no longer warns with a
  RepeatedRowsWarning.
- **The Example database refuses a query it can't run the same way in both Editions**,
  saying what went wrong and the tables to choose from. In the Edition that writes its Hive
  with sqlglot, a column or table name spelt wrong gave sqlglot's own error, and some queries
  it couldn't run gave a garbled message ("... has no what this needs").
- **The Example database has tables only in ops**: DESCRIBE mart.jobs and SELECT ... FROM
  mart.jobs are refused for the table. Before, DESCRIBE described ops.jobs, and in the Edition
  that writes its Hive with sqlglot the SELECT blamed a column.
- **example_database.send takes only Hive text**: given a Statement, it says to use run(...)
  or to_hive(...), where it gave a raw Python error.
- **With too old a sqlglot, the Example database's refusal says which version to install.**
- **A Saved table with no days yet matches its Table reference.** check_table_reference
  reported a Problem, "the newest dt, None, isn't written like ...", and said to set
  date_partition=None, which would stop every Statement's days being checked; now it notes
  that the date_format can be checked once the table has a day. write_table_reference names
  its Date partition, with a TODO to run check_table_reference once it has a day.
- **check_table_reference says a table matches when it finds only notes**, not problems.
- **A send that gives back nothing usable is refused**, saying what happened, why it
  matters and the usual fix, and a DESCRIBE that lists no columns is reported:
  write_table_reference, check_key and check_table_reference raised a raw Python error for an
  answer of None or an empty table, and check_table_reference said to delete every line.
- **check_table_reference reports a newest day written another way** than the date_format
  writes it, such as 2026-9-24, which Hive wouldn't match. It said the table matched, and
  write_table_reference named it the Date partition; now it writes date_partition=None, with
  a TODO saying why.
- **check_key on a day written another way** says so, and to run check_table_reference,
  where it used to stop with an error about a call inside the Toolbox.
- **first_look and all_columns refuse a table's name as text**, and Table refuses a Python
  type, such as int, as a column's type, saying what to write. Each raised a raw Python
  error.
- **write_table_reference never names a file like a module**: a table called calendar or
  pandas, or anything else Python can import, gets t_calendar.py, so Python's own calendar
  module isn't replaced by your file on the next import.
- **check_table_reference's report when SHOW PARTITIONS fails** is one readable line.
- **The GROUP BY Guard checks every column a grouped Statement shows, tests or sorts by.** It
  missed a column inside a grouped calculation, a column beside a count or a sum in one
  output, and the columns in HAVING and ORDER_BY, which Hive then refused.
- **A count or a sum is refused in ON= and GROUP_BY, and a row number in WHERE, HAVING, ON=
  and GROUP_BY**, as a count already was in WHERE. Each fix says where it goes instead. A
  count, a sum or a row number inside a count, a sum or a function such as collect_set is
  refused when it is made.
- **ORDER_BY's names are checked**, as GROUP_BY's are: a name SELECT doesn't have is refused.
- **row_number sorts by columns only.** Its ORDER_BY= refuses an empty list, and a name,
  which Hive can't see inside row_number. Before, the empty list gave a raw error.
- **GROUP_BY() with nothing to group by is refused**, as ORDER_BY() is. It was dropped.
- **fill_null with a count or a sum in it is checked by the GROUP BY Guard.**
- **When a Derived table deeper down drops the Date partition**, by_day names it, and says to
  keep the Date partition in every Derived table that reads from it.
- **by_day refuses a LIMIT**, in your Statement or in a Derived table it reads through FROM.
  LIMIT keeps rows of the whole Statement: split by day, a top 10 over a week became the top
  10 of each day, 70 rows.
- **by_day follows the Date partition itself, not its name.** It checked only the name dt, so
  grouping by any column called dt passed, and each day got part of a total; a dt renamed
  with AS in a Derived table was refused. Now it follows job_runs.dt itself, whatever it's
  called.
- **A FROM table with no Date partition is named plainly** when by_day or a write needs its
  days. by_day's fix named a column the table doesn't have.
- **export_lineage shows a write over several days even with set_load_limits(dates=...)**,
  using the first day's Hive, as it does without it. Before, set_load_limits(dates=...)
  refused it.
- **set_load_limits(dates=...)'s fix for a joined table** says to narrow that table's own
  days. It said to use by_day, which splits only the table in FROM.
- **A Date partition's day must be written exactly as its date_format writes it.** Before,
  `equals(job_runs.dt, "2026-9-24")` was taken as 2026-09-24, but Hive compared the text
  '2026-9-24', which matches no day, so the answer was empty. Now it is refused.
- **date_format must put the year first, then the month, then the day**, and hold no other
  letter. Hive compares a Date partition's days as text, so with the day first, BETWEEN,
  last_n_days and check_key's newest day read the wrong days. A table whose days are
  written another way can still be read with date_partition=None.
- **by_day skips a day not_equals or is_not_in leaves out.** Before, it dropped the condition
  and read or wrote that day anyway. set_load_limits(dates=...) doesn't count that day
  either. by_day now refuses a WHERE that leaves no day to read, where it gave back an empty
  list.
- **by_day reads only the days an any_of lets through.** Before,
  `any_of(equals(job_runs.dt, "2026-09-01"), between(job_runs.dt, "2026-09-23", "2026-09-24"))`
  counted every day from the first to the last: by_day gave 24 Statements, most reading no
  rows, and set_load_limits(dates=...) counted 24 days. Now both count 3. Split by day, an
  INSERT_OVERWRITE wrote each day between with no rows, which replaced what it held.

## 3.1

- The first lines of some docstrings, which the README's cheat sheet shows, say more
  plainly what a function does, such as where `write_table_reference` writes its file.
- With a sqlglot that writes a struct without the colons Hive needs, as 25.24.2 does, the
  Edition that writes its Hive with sqlglot refuses a struct column in `create_table`, and
  says which sqlglot to install. Before, it wrote `STRUCT<name STRING>`, which Hive refuses,
  where Hive reads `STRUCT<name: STRING>`.

## 3.0

- **Two Editions.** The Toolbox now comes as two folders, with the same functions and
  version: one writes its Hive with the sqlglot package, as before, and the other writes the
  same Hive itself, for a notebook that runs Spark, and runs its Example database on a Spark of
  its own. Copy one, the whole folder. The README says which to copy, what each needs, and the
  few places their Hive differs.
- **week_start and month_start give text on Spark too**. Their Hive is now
  `CAST(NEXT_DAY(...) AS STRING)` and `CAST(TRUNC(...) AS STRING)`: Spark's NEXT_DAY and TRUNC
  give a date, and the CAST makes it text, a day like "2026-09-21", as Hive gives it. On Hive
  the result is the same as before. On Spark, give a Saved table's column for either the type
  "string", not "date": Spark won't write text into a date column.
- **The words Spark reserves go in backticks too**, such as any, except, minus,
  semi and current_user, as column, table and Derived table names. Before, some of them made
  to_hive fail, and others were written plain, which Spark refuses.
- **create_table takes only the column types Hive and Spark share**, written as
  DESCRIBE prints them: string, bigint, int, smallint, tinyint, double, float, boolean, date,
  timestamp and binary; decimal, varchar and char with their sizes, such as decimal(10,2); and
  arrays, maps and structs of them. Before, it took any type sqlglot knew, such as json or uuid,
  which neither has, and wrote integer, real or numeric under other names, so the table didn't
  match its Table reference. For a type people often write, such as integer, the refusal says
  what to write instead.
- **hive_function checks a call by one list**, for about 110 common functions,
  such as upper, substr, date_add or max: it refuses a call with the wrong number of arguments,
  and treats a function that turns many rows into one, such as collect_set or percentile, as
  count_rows() is treated. A function that works only over a window of rows, such as lag or
  rank, is refused, since hive_function can't write OVER, and the refusal says how pandas does
  it. Before, sqlglot checked the call, and let through some counts Hive and Spark refuse, such
  as length with 2 arguments. For a function the list doesn't hold, the Edition that writes its
  Hive with sqlglot still has sqlglot check the call; the other writes it as given, and Spark
  checks it when it runs.
- **An object from the other Edition's folder is refused plainly**. Given, say, a
  Table reference whose file imports the other folder, the Toolbox function you give it to
  says which folder made the object, and how to import from one folder only, whichever your
  notebook uses.
- **A file from the other folder stops the import**. A file copied in from the
  other folder by mistake, even `__init__.py`, is named with the folder it came from, and the
  fix says to copy this folder in again from its own folder of the download.
- **One more Worked example:** one count divided by another as a percent.
- A value holding a bell, a form feed or a vertical tab is now refused, and so is a
  `date_format` holding one. In a Python string these are what `\a`, `\f` and `\v` give, as
  in a Windows path like `'D:\logs\alerts'`. The Hive would write them as `\a`, `\f` and
  `\v`, which Hive and Spark read back as the plain letters a, f and v, so the value would
  quietly be a different one. Write such a path with r before the quotes:
  `r'D:\logs\alerts'`.
- `write_table_reference`, `check_table_reference` and `check_key` now read a day written
  like 2026/09/24, which SHOW PARTITIONS lists as `2026%2F09%2F24`. Before, for such a table,
  `check_table_reference` said to change its line to `date_partition=None,` and
  `write_table_reference` wrote that line: if you have it, put the Date partition back, with
  `date_format="%Y/%m/%d",`, and run `check_key` again.
- SHOW PARTITIONS lists the rows with no day under the name `__HIVE_DEFAULT_PARTITION__`,
  which sorts after every day, and the three used to take it for the newest day. On a table
  with such rows, `check_table_reference` said to change its line to `date_partition=None,`,
  `write_table_reference` wrote that line, and `check_key` counted those rows instead of the
  newest day's: if you have that line, put the Date partition back, and run `check_key` again.
- `write_table_reference`, `check_table_reference` and `check_key` now work on a table named
  with a word Hive keeps for itself, such as `ops.order`: they put the name in backticks in
  what they send. Your Table reference names the table as before, `Table("ops.order", ...)`.
- When DESCRIBE lists more after a table's partition columns, such as the columns' default
  values, that is no longer taken for more partition columns.
- A send that gives back a Spark DataFrame, as `send=spark.sql` does without `.toPandas()`,
  is now refused wherever its rows are read, saying to make it give back pandas:
  `send=lambda hive: spark.sql(hive).toPandas()`. Before, `run` gave such a frame back without
  its row limit, and `write_table_reference` and `check_key` stopped with Python's own error,
  which `check_table_reference` reported. A write's frame is still given back, since Spark
  has carried out the write by then.
- A table Spark describes with a "# Partitioning" section, such as a Delta or Iceberg table,
  now has its partition column read from it. Before, `check_table_reference` said to change
  its line to `date_partition="Part 0",` and `write_table_reference` wrote
  `date_partition=None,`: if you have either line, put the Date partition back.
- The Example database gives a Statement's rows in the same order every time. When the
  Statement has no `ORDER_BY`, they are sorted by its first column, then its second, and so on,
  with None first. At work, rows still come back in no fixed order.
- A `hive_function(...)` call is now compared by the function you name, whatever its case, and
  by its arguments, so it no longer counts as the same calculation as another one that writes
  the same Hive: `hive_function("coalesce", x, 0)` and `fill_null(x, 0)` both write COALESCE,
  for example. It matters in one place: a `derived(...)` table that SELECTs one and groups by the
  other no longer knows its key, so a JOIN to it warns. Group by the calculation you SELECT.
- Refusals and docstrings that described Hive alone now say what holds on Spark as well, and
  call where Statements run at work "the warehouse".
- A refusal shows a calculation inside a Toolbox call the way you wrote it, as the lineage
  does: `equals(fill_null(job_runs.status, "none"), None)` rather than
  `equals(COALESCE(job_runs.status, 'none'), None)`. So an opt-out it gives can be pasted back
  as it is.

## 2.1

- **Adding to a day.** `INSERT_INTO(t)` adds a Statement's rows to one day of a Saved
  table and keeps the rows already there, for a day filled from more than one source. It
  follows every rule of `INSERT_OVERWRITE`, but sending it twice adds its rows twice, so
  the first write of a day is still `INSERT_OVERWRITE`.
- **Dropping a table.** `drop_table(t)` writes `DROP TABLE IF EXISTS` for a table, to
  send with `run`. It deletes every day of the table, and is for rebuilding a Saved table
  after changing its columns: drop it, create it again, and write its days again.
- **More Worked examples.** The Example gallery now starts with common jobs, each built in
  steps that say why: building a Saved table (create it, write a day, add to a day,
  backfill, drop and rebuild it), jobs with no runs, labels and counts by condition, counts
  per group with `HAVING` and the top N, filters by a list or by text, and a long Statement
  built from named steps. The Statements that give a wrong number beside their fix follow.
- A Statement with both `INSERT_OVERWRITE` and `INSERT_INTO`, or with both `SELECT` and
  `SELECT_DISTINCT`, is now refused.
- A write that reads a table with no Date partition now says so plainly.

## 2.0

The first version of the new Toolbox. Everything is new:

- **Table references.** `Table(...)` describes one table: its columns and their types, its
  Date partition, its key, and the columns that don't add up. `write_table_reference` writes one
  from Hive's own description, `check_table_reference` compares one with the table as it is now,
  and `check_key` checks a declared key on the newest day. `first_look(t)` shows a table's
  columns and 20 of yesterday's rows.
- **Statements.** Clause functions in SQL order (`SELECT`, `FROM`, `JOIN`, `WHERE`,
  `GROUP_BY`, ...) are assembled by `statement(...)` and written as Hive by `to_hive(...)`.
  `derived(name, statement)` names a Statement so another can read it. There is no `*`:
  `all_columns(t)` lists a table's columns instead.
- **Conditions and calculations** are named functions, such as `equals`, `between`,
  `count_rows` and `sum_of`. Arithmetic uses Python's `+ - * /`. `week_start` and
  `month_start` group days into weeks and months, `row_number` keeps the latest row or the top
  N per group, and `hive_function` calls any other Hive function.
- **Guards** refuse a Statement that would give a wrong number, and **Load limits** refuse one
  that would read or return too much. Each raises `GuardRefused` or `LoadRefused` and says
  what happened, why, the usual fix, and the keyword that lets it through where there is one.
  A join off the joined table's key gives a **Warning** instead.
- **Running.** `run(s, send=...)` sends a Statement through your own `send`, `by_day(s)` splits
  one into single days, and `set_load_limits(...)` switches on an automatic `LIMIT` and a cap
  on days per Statement, both off to start with.
- **Saved tables.** `INSERT_OVERWRITE(t)` writes one day of a Saved table, and
  `create_table(t)` creates it.
- **The folder checks itself.** On import, the Toolbox's folder stops if a file is missing or
  extra, or if its files come from different versions or different exports. It also stops on a
  Python older than 3.11, and on a sqlglot outside 25.24.2 up to (not including) 31 or one
  that behaves differently. Each stop says what happened, why it matters and the usual fix, in
  the same four parts as a refusal, and none of them can be switched off.
  `TOOLBOX_VERSION` is the feature number, and `VERSION` also says when this copy was exported.
- **Lineage.** `export_lineage(s)` writes where each column comes from, as an HTML page and
  a Markdown twin that needs no script, in a `lineage/` folder beside your script or
  notebook. Every step stays on screen, from the table columns through each Derived table to
  the outputs, with controls to expand, collapse or hide each table. Pass several Statements
  and the drawing follows each Saved table from the Statement that writes it to the ones that
  read it.
- **The Example database.** `example_database` holds three made-up tables and a `send` that
  runs Statements on them, to practise without touching the warehouse. What its small
  executor can't run, such as `row_number` or `week_start`, it says plainly.
- **The Example gallery.** `examples.html`, in the Toolbox's folder, holds every Worked example
  on one page: each docstring's example, and the Worked examples on their own, each showing a
  Statement that gives a wrong number beside its fix. Each shows its Python and, for each
  Statement it builds, the Hive and any result: from the Example database, or computed in pandas
  where the Example database can't run it. Open it in a browser; a box keeps only the entries
  holding every word you type, and Ctrl+F searches it without the box.
