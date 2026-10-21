<!-- sqlglot Composer 6.0, exported 2026-10-21 07:24 - generated from dev, do not edit -->
# sqlglot Composer

This is version 6.0, exported 2026-10-21 07:24.

Write Hive SQL as Python. You put clause functions (`SELECT`, `FROM`, `WHERE`, ...) together in
SQL order, and the Toolbox writes the Hive string. It refuses a Statement that would silently
give a wrong number, or read or return too much, and says what to change.

This page is a tutorial: eight steps, from installing the Toolbox and starting a Project,
through your tables' references, a Saved table written every day and the Lineage of each of its
columns, to keeping the Project in order. Most steps point to the how-to that walks through them
in full, on `sqlglot_composer/how_to.html`, a page in the download to open in your browser. What
changed in each version, and how to update from it, is in `CHANGES.md`.

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
3. Make a folder for your Project, and copy the whole `sqlglot_composer` folder into it. Keep
   your own files beside it, never inside it.

The download's other folder, `example_projects`, is for reading and copying from, and the
Toolbox doesn't need it: see [Example projects](#example-projects). The
[Templates](#templates) ship inside the Toolbox.

## 2. Start a Project

A Project is the folder your work lives in: the Toolbox, your send, your tables' Table
references, the Building blocks your notebooks share, and a folder per Saved table. Open a
notebook in the Project's folder, and lay it out with one call:

```python
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and send.py. Next: write your send in send.py.
```

Import from `sqlglot_composer`, at its top level, never from a file inside it. The Toolbox
never connects to anything itself: it writes Hive as text, and `run` hands that text to a
function of yours, `send`, which runs it and gives back a pandas DataFrame. Write it once, in
`send.py`: for example, `def send(hive): return pd.DataFrame(my_api.query(hive))`, which runs
the Hive through your team's query API. Every notebook imports it with
`from send import send`.

Make and remove Table folders and Table references with the `project` module's Project
actions, such as `project.new_table(...)`, never by hand in your file explorer: each is
logged in `admin/admin_log.md`, and listed in the registry, `admin/registry.csv`. `admin/`
holds a notebook per Project action, such as `new_table.ipynb`, ready to fill in; calling one
from any notebook of the Project does just the same.

The how-to [Start a Project](../sqlglot_composer/how_to.html#start_a_project) walks through what
each folder is for, your send, the lines a notebook deeper in the Project starts with, and the
mistakes people make first. A later how-to that starts a Project of its own, since its page
has none, says so: in yours, leave `project.start()` out.

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
columns that name one row). `project.add_references(["your_db.your_table", ...], send=send)`
asks each table for its columns and writes its file into `references/`; you fill in what it
can't know, and add Aliases, your own names for its columns and conditions. A notebook then
imports one as `from references.your_db__your_table import your_table`.
`project.refresh_reference_sheet()` lists every column of every table in one CSV file.

How-tos: [Add your tables' references](../sqlglot_composer/how_to.html#add_your_tables_references),
[Describe a table by hand](../sqlglot_composer/how_to.html#describe_a_table_by_hand) for a
table you can't read yet, and [The Reference sheet](../sqlglot_composer/how_to.html#the_reference_sheet).

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

In a Project, `project.new_table("mart.your_table")` gives each Saved table a Table folder in
`tables/`, holding its notebook, made from a Template, and writes its Table reference for you
to fill in. `project.run_tables(day, send=send)` then writes a day of every table, each after
the tables it reads.

How-tos: [Save a table](../sqlglot_composer/how_to.html#save_a_table),
[Add a Saved table](../sqlglot_composer/how_to.html#add_a_saved_table),
[Backfill a range of days](../sqlglot_composer/how_to.html#backfill_a_range_of_days) and
[Run a daily pipeline](../sqlglot_composer/how_to.html#run_a_daily_pipeline).

## 7. Where each column comes from

`export_lineage(...)` writes an HTML page and a Markdown twin that follow each output column
back to the table columns it reads, across the Saved tables of a whole pipeline. From a Table
notebook, the files go in its Table folder's `lineage/`, named by the time and the table, so
each export joins the table's history, and `project.load("mart.other_table")` gives another
notebook's logic, to draw the tables it reads beside it.

How-tos: [Lineage of one Statement](../sqlglot_composer/how_to.html#lineage_of_one_statement),
[Lineage of a pipeline across Saved tables](../sqlglot_composer/how_to.html#lineage_of_a_pipeline_across_saved_tables) and
[Lineage across your tables](../sqlglot_composer/how_to.html#lineage_across_your_tables).

## 8. Keep the Project in order

Your files sit in three Levels, each importing only from those below it: the Table references
and `send.py`, then the Building blocks, then each Table notebook's logic.
`project.check()` reports any Table folder or Table reference the registry doesn't list, or
lists but isn't there; `project.remove_table(...)` archives a Table folder in
admin/removed/ rather than deleting it; and a notebook you run every week checks each Table
reference against its table, as how-to 21 shows. The [Example projects](#example-projects) show a Project filled
in, and the [Templates](#templates) are the shapes a new Table notebook is made from.

How-tos: [Keep a Table reference true over time](../sqlglot_composer/how_to.html#keep_a_table_reference_true_over_time)
and [Share Building blocks between Statements](../sqlglot_composer/how_to.html#share_building_blocks_between_statements).

## The how-tos

Every how-to walks through one job from start to finish, in steps you paste into one notebook,
in order: its goal, its steps, each run on the Example database with what it shows, how to check
it worked, and the mistakes people make first. The Getting started how-tos take you from
starting a Project to its Saved tables, their Lineage and the Reference sheet; the Intermediate
ones are for work over many days and many tables: days written another way, week and month
totals, rows that come in late, pipelines of Saved tables, quality checks, testing, how a Saved
table is stored and its Key, Session settings and the admin module, more joins, looking across
rows, reconciling two tables, subtotals, and keeping reads fast.

Getting started, how-tos 1 to 21:

1. [Start a Project](../sqlglot_composer/how_to.html#start_a_project)
2. [Add your tables' references](../sqlglot_composer/how_to.html#add_your_tables_references)
3. [Describe a table by hand](../sqlglot_composer/how_to.html#describe_a_table_by_hand)
4. [Build a first Statement and paste its Hive](../sqlglot_composer/how_to.html#build_a_first_statement)
5. [Filter rows](../sqlglot_composer/how_to.html#filter_rows)
6. [Count and add up per group](../sqlglot_composer/how_to.html#count_and_add_up_per_group)
7. [Join tables safely](../sqlglot_composer/how_to.html#join_tables_safely)
8. [Reusable Derived tables (WITH ... AS in the Hive)](../sqlglot_composer/how_to.html#reusable_derived_tables)
9. [The latest row per key, and the top N per group](../sqlglot_composer/how_to.html#latest_row_per_key)
10. [Save a table](../sqlglot_composer/how_to.html#save_a_table)
11. [Add a Saved table](../sqlglot_composer/how_to.html#add_a_saved_table)
12. [Backfill a range of days](../sqlglot_composer/how_to.html#backfill_a_range_of_days)
13. [Run a daily pipeline](../sqlglot_composer/how_to.html#run_a_daily_pipeline)
14. [Lineage of one Statement](../sqlglot_composer/how_to.html#lineage_of_one_statement)
15. [Lineage of a pipeline across Saved tables](../sqlglot_composer/how_to.html#lineage_of_a_pipeline_across_saved_tables)
16. [Lineage across your tables](../sqlglot_composer/how_to.html#lineage_across_your_tables)
17. [The Reference sheet](../sqlglot_composer/how_to.html#the_reference_sheet)
18. [Keep queries small with Load limits](../sqlglot_composer/how_to.html#keep_queries_small_with_load_limits)
19. [Guards, Warnings and opt-outs](../sqlglot_composer/how_to.html#guards_warnings_and_opt_outs)
20. [Generate Statements in a loop](../sqlglot_composer/how_to.html#generate_statements_in_a_loop)
21. [Keep a Table reference true over time](../sqlglot_composer/how_to.html#keep_a_table_reference_true_over_time)

Intermediate, how-tos 22 to 40:

22. [A day written another way, and a second partition](../sqlglot_composer/how_to.html#a_day_written_another_way)
23. [Look things up as of a day](../sqlglot_composer/how_to.html#look_things_up_as_of_a_day)
24. [Week and month rollups](../sqlglot_composer/how_to.html#week_and_month_rollups)
25. [Incremental loads and late data](../sqlglot_composer/how_to.html#incremental_loads_and_late_data)
26. [A pipeline of Saved tables](../sqlglot_composer/how_to.html#a_pipeline_of_saved_tables)
27. [Share Building blocks between Statements](../sqlglot_composer/how_to.html#share_building_blocks_between_statements)
28. [Check data quality with Statements](../sqlglot_composer/how_to.html#check_data_quality)
29. [Generate Table references and Statements from settings](../sqlglot_composer/how_to.html#generate_from_settings)
30. [Call other Hive functions](../sqlglot_composer/how_to.html#call_other_hive_functions)
31. [Look across rows, then finish in pandas](../sqlglot_composer/how_to.html#finish_in_pandas)
32. [Review a change with Lineage](../sqlglot_composer/how_to.html#review_a_change_with_lineage)
33. [Test your own Statements](../sqlglot_composer/how_to.html#test_your_own_statements)
34. [Choose how a Saved table is stored](../sqlglot_composer/how_to.html#choose_how_a_saved_table_is_stored)
35. [Keys, checked before each write](../sqlglot_composer/how_to.html#keys)
36. [Semi-, anti- and full joins](../sqlglot_composer/how_to.html#semi_anti_and_full_joins)
37. [Move a Saved table to its own folder](../sqlglot_composer/how_to.html#move_a_saved_table_to_its_own_folder)
38. [Reconcile two tables](../sqlglot_composer/how_to.html#reconcile_two_tables)
39. [Subtotals and grand totals](../sqlglot_composer/how_to.html#subtotals_and_grand_totals)
40. [Keep reads and joins fast](../sqlglot_composer/how_to.html#keep_reads_and_joins_fast)

## The Example gallery

`sqlglot_composer/examples.html` is the Example gallery: every Worked example on one page, its
Python and, for each Statement it builds, the Hive and any result. Open it in your browser. It
needs nothing else: a box at the top keeps only the examples holding every word you type, and
Ctrl+F searches it too. Besides each docstring's example, it holds the Worked examples that
stand on their own: common jobs built in steps that each say why, such as building a Saved table
or finding rows with no match, and Statements that give a wrong number shown beside their fix.
Each result comes from the Example database or, where that can't run it, is computed in pandas.

## Example projects

An Example project is a Project made for the Example database's tables, laid out as yours is:
everything in it was made by the `project` module's Project actions, then filled in by hand.
`example_projects/` holds two:

- `starter/`, on `ops.jobs`, `ops.job_runs` and `ops.run_alerts`: two Saved tables written a
  day at a time, and a third, each team's day, read from both, through a Building block and
  Aliases.
- `intermediate/`, on `ops.job_events`, `ops.job_owners` and `ops.region_costs`, which builds
  on the starter project: four Saved tables, one from each of the other Table notebook
  Templates. The three that count or add up rows write their last 3 days again on every run,
  since rows can come in late; the quality checks write only their day.

Each project's `README.md` says what each folder holds and how to run it. Copy the
`sqlglot_composer` folder into a project's folder first, as a Project holds it, then open its
notebooks. The Example database can be read but not written, so a Table notebook's cell 3
prints each write's Hive and runs only what reads the ops tables, and
`admin/run_tables.ipynb`, with no send, prints every write in order, writers first, and sends
nothing (a dry run).

To start a Project of your own, start it with `project.start()` rather than copying one: an
Example project is for reading, and copying it would bring its tables and its Admin log.

## Templates

A Template is the empty shape of one of your notebooks or files, to make a new one from. They
ship inside the Toolbox, and `project.start()` copies them into your Project's
`admin/templates`, where they are yours to edit, or to add your own beside.
`project.new_table("mart.your_table", template="daily_table")` makes a Table folder's notebook
from one, filling in the table's database and name. Every other placeholder, a word in angle
brackets such as `<SOURCE_TABLE>`, is yours to replace, brackets and all; Python stops at one
left in, so a notebook can't run half filled in. Each Template's first cell lists its
placeholders, with an example of each.

The Table notebook Templates, each a notebook of the same five code cells around its own logic:

- `daily_table`: a table written a day at a time, from a table it reads.
- `incremental_load`: each run writes its day and the few days before it again, for rows that
  come in late.
- `weekly_rollup`: a table written a day at a time and read a week at a time.
- `as_of_lookup`: each row looked up in a snapshot table as of its own day.
- `quality_checks`: a table's row count saved each day, and checks for repeated keys and NULLs.

And two more, for files beside the notebooks:

- `saved_table_reference`: the Table reference `new_table` writes for the table, in
  `references`, to fill in.
- `building_block`: a Derived table several notebooks read, copied by hand into
  `building_blocks`.

## Update

1. Note which version you have: `sqlglot_composer.VERSION` says, such as
   `'sqlglot Composer 5.1, exported ...'`.
2. Delete the `sqlglot_composer` folder, and any `composer_core` folder beside it, left over from
   before 6.0.
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
module. Two modules' functions come last: the admin module's, which change your own Saved
tables, and the project module's, which make and archive a Project's folders and files. The star
import leaves both out, so import each by name, as `from sqlglot_composer import admin, project`,
and call `admin.drop_table(t)` or `project.new_table("mart.daily_job_runs")`.

### `__init__.py`

Write Hive SQL as Python, one clause function per SQL clause.

- `TOOLBOX_VERSION` = `'6.0'` - the feature number, raised only when a big feature lands.
- `VERSION` = `'sqlglot Composer 6.0, exported 2026-10-21 07:24'` - the full text, which also says when this copy was exported.

### `tables.py`

Table references: Table, and the functions that read, write and check one.

- `Table` - A Table reference: a table's columns, the day column it's split by, and its key.
- `write_table_reference` - Write a table's Table reference as a file, such as ops__run_alerts.py.
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

### `project.py`

The project module: a Project's folders and files, made and archived for you, and logged.

- `project.start` - Make a Project in the folder you're working in, once, from a notebook there.
- `project.new_table` - Make a Table folder for a Saved table: its notebook, lineage/ and reference.
- `project.remove_table` - Move a Table folder into admin/removed/, named by the time, deleting nothing.
- `project.add_references` - Write a Table reference for each table into references/, skipping any it can't.
- `project.remove_reference` - Move a Table reference into admin/removed/, named by the time, deleting nothing.
- `project.register` - Adopt a Table folder or Table reference made by hand into the registry.
- `project.check` - Report each Table folder or Table reference that the registry gets wrong.
- `project.refresh_reference_sheet` - Rebuild the Reference sheet: a row per column of every Table reference.
- `project.load` - A Table notebook's logic, its functions by name, from anywhere in the Project.
- `project.run_tables` - Write a day of every table, each before the tables that read it.
