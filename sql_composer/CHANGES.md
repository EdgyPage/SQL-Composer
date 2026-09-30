# Changes

What changed in each Toolbox version, in plain words. The newest version comes first.

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
- A value holding a bell, a form feed or a vertical tab is now refused, and so is a
  `date_format` holding one. In a Python string these are what `\a`, `\f` and `\v` give, as
  in a Windows path like `'D:\logs\alerts'`. The Hive would write them as `\a`, `\f` and
  `\v`, which Hive reads back as the plain letters a, f and v, so the value would quietly be
  a different one. Write such a path with r before the quotes: `r'D:\logs\alerts'`.
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
- A table Spark describes with a "# Partitioning" section, such as a Delta or Iceberg table,
  now has its partition column read from it. Before, `check_table_reference` said to change
  its line to `date_partition="Part 0",` and `write_table_reference` wrote
  `date_partition=None,`: if you have either line, put the Date partition back.
- The Example database gives a Statement's rows in the same order every time. When the
  Statement has no `ORDER_BY`, they are sorted by its first column, then its second, and so on,
  with None first. At work, rows still come back in no fixed order.
- A `hive_function(...)` call is now compared by the function you name, whatever its case, and
  by its arguments, so it no longer counts as the same calculation as another one that writes
  the same Hive: `hive_function("nvl", x, 0)` and `fill_null(x, 0)` both write COALESCE, for
  example. It matters in one place: a `derived(...)` table that SELECTs one and groups by the
  other no longer knows its key, so a JOIN to it warns. Group by the calculation you SELECT.
- Refusals and docstrings that described Hive alone now say what holds on Spark as well, such
  as why a sort needs a LIMIT: sorting a whole big result is slow, wherever it runs.

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
