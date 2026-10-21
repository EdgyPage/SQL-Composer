# Changes

What changed in each Toolbox version, in plain words. The newest version comes first.

## 6.0

6.0 is sqlglot Composer alone, tested on Python 3.12, pandas 3 and numpy 2.5.

### To update from 5.x

- **The README is a tutorial**: eight steps, from installing the Toolbox to a project of your
  own, each pointing to the how-tos that walk through it. What it said about one version,
  such as updating from 4.x or 3.x, is in these notes, under that version's "To update".
- **The Toolbox is one folder, `sqlglot_composer`.** Delete both old folders, `composer_core`
  and `sqlglot_composer`, copy in the new `sqlglot_composer`, and restart the kernel. Imports
  `from sqlglot_composer import ...` stay as they are; one that named `composer_core`, such as
  `from composer_core.refusals import GuardRefused`, becomes `from sqlglot_composer import
  GuardRefused`. A traceback names a Toolbox error by its new home, such as
  `sqlglot_composer.refusals.GuardRefused`, where it said `composer_core.refusals.GuardRefused`.
  These change notes, `CHANGES.md`, are now at the top of the download, beside the README, and
  the Example projects and the Templates sit in `example_projects/` and `templates/` themselves,
  not in a folder named `sqlglot_composer` inside each.
- **Spark Composer is dropped.** If you used it: install sqlglot (`pip install -r
  requirements.txt`), delete the `spark_composer` and `composer_core` folders, copy in
  `sqlglot_composer`, change each `from spark_composer import` to `from
  sqlglot_composer import`, and restart the kernel.
- **The Toolbox writes Hive, and says nothing of Spark.** The README's "If your send runs the
  Hive on Spark" is gone, and so are the Toolbox's two refusals made only for Spark: of a send
  that gives back a Spark DataFrame, which is now refused as any send that gives back something
  other than a pandas DataFrame, and of a Saved table's `properties=` naming `comment`, `owner`,
  `provider`, `location` or `is_managed_location`. If a warehouse of yours runs the Hive on
  Spark, ask whoever looks after it where Spark reads Hive its own way.
- **`requirements.txt` is one list, pinned for Python 3.12**: pandas 3.0.6, numpy 2.5.4 and
  sqlglot 30.23.0, with what they need in turn, and pytz, which pandas 3 no longer needs but is
  kept for code of yours that imports it. On Python 3.11, change numpy's line to
  `numpy==2.4.6`, as the README's Install says. The Toolbox itself still runs on Python 3.11 or
  newer.
- **pandas 3 shows a missing text value as NaN**, where pandas 2 showed None: a run's result
  with a NULL in a text column reads NaN there. Test for it with `isna()`, never `== None`.
- **`write_table_reference` names its file for the database and the table**, such as
  `ops__job_runs.py` for `ops.job_runs`, so `from ops__job_runs import job_runs` imports it;
  `folder="references"` writes it into that folder. A column's DESCRIBE comment now goes in
  `Table`'s new `descriptions={...}`, not a `#` comment, and an Aliases heading below the Table
  reference shows how to add your own names for its columns and conditions. A table named
  like a Python word, such as class, still gets t_ in front of its variable, but a table named
  like a module, such as calendar, no longer does, since its file's name starts with its
  database. A name with no database, such as `"jobs"`, is refused: write `"ops.jobs"`. Files
  written before 6.0 keep their names: nothing to change.
- **New: the `project` module**, imported by name, as `from sqlglot_composer import project`.
  `project.start()`, run once from a notebook in a folder beside `sqlglot_composer`, lays out a
  Project: `admin/` (a notebook per Project action, the Templates, a registry and the Admin
  log), `references/`, `building_blocks/`, `tables/` and `send.py`, your send written once.
  `project.new_table("mart.daily_job_runs")` makes a Table folder, with a notebook made from a
  Template and a `lineage/` folder, and the table's Table reference to fill in;
  `project.add_references([...], send=send)` writes many tables' Table references at once,
  skipping any already there or that DESCRIBE can't read, and naming each skipped at the end;
  `project.refresh_reference_sheet()` writes `references/reference_sheet.csv`, a row per
  column of every Table reference, with its Aliases and description;
  `project.load("mart.daily_job_runs")` gives a Table notebook's logic, its functions such as
  `write_day`, from anywhere in the Project. `project.run_tables(day, send=send)` writes a day
  of every table, each before the tables that read it; with no `send`, it prints each Hive and
  sends nothing. `remove_table` and `remove_reference` move what they remove into
  `admin/removed/`, deleting nothing; `register` adopts what you made by hand, and `check()`
  reports what the registry doesn't know. Inside a Project, Admin statements log to
  `admin/admin_log.md` too, wherever the notebook that runs them is, and `export_lineage` of one
  write of a Saved table with a Table folder puts its files in that folder's `lineage/`, named
  by the time and the table, so each run adds to the table's past Lineage. Nothing to change
  in your notebooks: a folder that isn't a Project works as before.

## 5.1

Nothing to change in your notebooks or files: copy the two folders in over 5.0's.

- **`requirements.txt`, at the top of the download, lists what the Toolbox needs** beyond
  Python's standard library: every package pinned to the version it is tested on, with the
  packages pandas and pyspark need in turn. It has a section for both Editions and one for each
  Edition: delete the section of the Edition you don't use, then `pip install -r
  requirements.txt`. Its pins are for Python 3.11; the README's Install says what to do on a
  newer Python, or where your notebook already has pandas or pyspark.
- **Spark Composer supports pyspark up to 4.2**: 3.5.0 or newer, below 4.3, where it was below
  4.1, and it is tested on pyspark 4.2.0.
- **A column or table named collations, current_path or current_schema is written in
  backticks**, in both Editions: Spark 4.2 reserves those words, and both Editions write the same
  Hive.
- **hive_function knows Spark 4.2's new aggregates**, such as approx_top_k, as functions that
  turn many rows into one, so a SELECT with one beside a plain column needs GROUP_BY, as with
  sum_of.
- **sqlglot Composer is tested on sqlglot 30.23.0**, still within 25.24.2 or newer, below 31.
  That sqlglot writes a few characters of a value (NUL and SUB) differently, so both Editions now
  write a value's characters by one table of their own: your Hive is what 5.0 wrote on sqlglot
  30.19.0, whichever sqlglot you have.

## 5.0

5.0 fills in the SQL the Toolbox left out: Keys checked before each write, how your Saved tables
are stored, Session settings, Hive written by hand, an admin module for changing your own Saved
tables, more joins, Windows, Stacks and subtotals, and the Statements that keep reads fast. It
refuses some writes 4.x let through, so read To update first.

### To update from 4.x

Copy both folders in as 4.x's README said, then change these in your notebooks and
files. Each is listed again, with more, under New or Refused now below.

- **A write into a Saved table whose Table reference declares a Key is refused unless the
  Toolbox can see that each row it writes has a Key of its own.** Hive never checks a Key, so
  before 5.0 two rows with the same Key were saved without a word. A write 4.1 let through may
  be refused now: its message says why its rows may repeat a Key, such as which join repeats
  them.
  Fix the write, or, when the rows are one per Key for a reason the Toolbox can't see, write
  `INSERT_OVERWRITE(t, unproven_key=True)` or `INSERT_INTO(t, unproven_key=True)`. The how-to
  "Keys, checked before each write" shows each.
- **Give each of your Saved tables' Table references a `location=`**, the folder your Saved
  tables go in, such as `location="/data/your_team/tables"`. create_table now refuses a Table
  reference without one, and writes `CREATE EXTERNAL TABLE ... LOCATION '<folder>/<database>/<table>'`:
  every Saved table is an external table in a folder of its own, which the Toolbox adds to
  `location=`. A table you only read needs none. A table create_table made before 5.0 is a
  managed table, in a folder the warehouse chose, and a table made by hand may share a folder
  with another: check_table_reference(t, send=...) now reports both, and
  admin.move_to_own_folder(t, send=...) copies such a table's days into a new table, which
  create_table makes at its own folder. Writes don't need `location=`: until it is moved,
  writing it works as in 4.x.
- **`drop_table` moved into the admin module.** `from sqlglot_composer import *` no longer
  brings it. Add `from sqlglot_composer import admin` below your star import, and write
  `admin.drop_table(t)` where you wrote `drop_table(t)`; a line that imports `drop_table` by
  name now stops with an ImportError. It now refuses a table that isn't one of your Saved
  tables, a Table reference with no `location=`, and each `run` of it adds an entry to the
  Admin log, `admin_log.md` beside your notebook.
- **The star import brings 26 new names**: `ANTI_JOIN`, `EXCEPT`, `FULL_JOIN`, `INTERSECT`,
  `RIGHT_JOIN`, `SEMI_JOIN`, `UNION`, `UNION_ALL`, `compute_statistics`, `cube`, `dense_rank`,
  `explain`, `first_value`, `grouping_sets`, `hive_settings`, `is_total`, `lag`, `last_value`,
  `lead`, `ntile`, `rank`, `repair_partitions`, `rollup`, `set_admin_log`, `unchecked_hive`
  and `window`. A variable of your own with one of these names, set before the star import,
  is replaced by the Toolbox's: give it another name.

### New

**Keys**

- **create_table writes a Table reference's Key into the table** in sqlglot Composer, as
  `PRIMARY KEY (...) DISABLE NOVALIDATE`, which Hive keeps for whoever reads the table and
  never checks. Spark refuses a PRIMARY KEY, so Spark Composer leaves it out. Either way, the
  Toolbox checks the Key before each write (To update, above).
- **A Derived table's Key reaches further**: through a join that matches its joined table's
  whole Key, through a row_number(...) kept at 1, and past a column whose value another
  column already fixes, as a run's run_id fixes its job_id. JOIN's repeated-rows Warning asks
  for `many_matches=` less often, and when a Derived table has no Key it says where its
  Statement lost one.
- **Lineage shows Keys**: each column that is part of a Key is marked "in the Key" in the
  chart, and the report lists each step's Key, or where it lost one, and whether a write's Key
  holds.

**How a Saved table is stored**

- **A Saved table's Table reference says how it is stored**, and create_table writes it:
  `location=` (above), `purge=True` (dropping it deletes its files too), `properties={...}`
  (other table properties), `stored_as="ORC"` or `"PARQUET"`, `compression=`,
  `partitioned_by=[...]` (Partitions inside each day, filled from each write's rows), and
  `bucketed_by=[...]` with `buckets=` and `sorted_by=[...]` (Buckets, for big tables joined
  on those columns). help(Table) lists them, and the how-to "Choose how a Saved table is
  stored" walks through them, and why there are no indexes.
- **check_table_reference compares a Saved table's storage** with what DESCRIBE FORMATTED
  says: that it is external, its folder, purge, its file format and compression, its
  properties, its Partitions and its Buckets, each difference with the line to change.
- **A Saved table with no days can be written.** Give its Table reference
  `date_partition=None`, and `INSERT_OVERWRITE(t)` writes the whole table, replacing every row
  it holds, as `INSERT OVERWRITE TABLE t SELECT ...` with no PARTITION; `INSERT_INTO(t)` adds
  rows to it. Before 5.0, both refused such a table. The Statement may read several days of a
  table with days, its days bounded in WHERE as in any read, and every other check of a write
  still applies, its Key too. The table must be one of your Saved tables, with `location=`,
  since INSERT_OVERWRITE replaces all of it. by_day refuses such a write, which is sent whole, and so
  does a write that keeps one day in a step above. (`admin.drop_days` and `repair_partitions`
  refuse a table with no days, as before.) The how-to "Save a table" has a section on it.
- **show_hive prints the Session setting a write needs first**: a write into a table with
  `partitioned_by=` fills those Partitions from its rows, which needs Hive's dynamic
  partitioning, so its SET lines are printed ahead of it. run sends the write alone: send
  the setting first with `run(hive_settings("dynamic_partitions"), send=...)`.

**Session settings, Hive written by hand, and the Admin log**

- **Session settings: `hive_settings("name")` gives the `SET` lines of a named set**, for
  `run` to send before your Statements, one line at a time, as Hive takes them. Four sets come
  with the Toolbox, each documented with why: `"dynamic_partitions"`, `"map_joins"`,
  `"statistics_on_write"` and `"merge_small_files"`. Keep your own in a settings.py of yours as
  `HIVE_SETTINGS = {"nightly": {"hive.exec.parallel": True}}` and pass them:
  `hive_settings("nightly", sets=HIVE_SETTINGS)`. They hold only while your send keeps one
  session across its calls. `show_hive` prints them, and `export_lineage`, passed them with
  your Statements, writes them at the foot of both its files.
- **`unchecked_hive("...")` runs Hive you write by hand**, for the one statement you need now
  that no clause function writes yet. No Guard, Warning or Load limit looks inside it.
  `show_hive` marks it, `export_lineage` draws it as one step it can't see inside, linked to
  the tables its text names, and text that starts `DROP`, `ALTER` or `TRUNCATE` gets a note
  naming the admin function that does the same job with its checks, where one does.
- **The Admin log.** Each `run` of an Unchecked statement or an Admin statement adds an
  entry to `admin_log.md`, beside the script or notebook that runs it: when, the call, the
  Hive sent, the script and its git commit, and whether it worked. The Toolbox only ever adds
  to it. To keep it elsewhere, keep its path in a settings.py of your own as `ADMIN_LOG`, and
  call `set_admin_log(ADMIN_LOG)` at the top of each notebook or pipeline.

**The admin module**

- **`from sqlglot_composer import admin`** gives the changes to your own Saved tables, written
  and checked for you. The star import leaves it out, so a notebook that changes a table says
  so. `admin.drop_table(t)`; `admin.drop_days(t, before=...)`, which drops a Saved table's
  days before a given day, the job TRUNCATE can't do on an external table;
  `admin.add_columns(t, send=...)`, which adds the columns its Table reference lists and the
  table lacks; `admin.set_properties(t)`, which sets purge, compression and properties as its
  Table reference gives them; and `admin.move_to_own_folder(t, send=...)`, the steps that move
  a Saved table to its own folder: a copy made there, each day copied, the rows compared, the
  old table dropped and the copy given its name. Each makes an ordinary Statement, which `run`
  sends and logs in the Admin log (the move gives a list of them, to run one at a time, in
  order), and `show_hive` prints what it
  changes, what can't be undone and what to check first before its Hive. Each refuses a table
  that isn't one of your Saved tables. The how-to "Move a Saved table to its own folder" walks
  a table out of a folder it shares.

**Joins**

- **Three more joins.** `SEMI_JOIN(t, ON=...)` keeps each row that has a match in t, once,
  written `LEFT SEMI JOIN`; `ANTI_JOIN(t, ON=...)` keeps each row that has none, written as a
  `LEFT JOIN` with a `WHERE` that keeps the rows whose matched column is NULL, since Hive 3 has
  no anti join. Neither repeats rows, so both keep the reading table's Key and give no
  repeated-rows Warning, and only their `ON=` may read t's columns. `FULL_JOIN(t, ON=...)`
  pairs the rows that match and keeps the rows of each side that have none, to compare two
  records of the same things. A `WHERE` on either side, other than `is_null(...)`, is refused
  (opt-out `FULL_JOIN(t, ON=..., keeps_only_matches=True)`), since it would throw away the rows the join keeps; bound
  each side's days in a Derived table of its own instead. Its rows have no Key until a
  GROUP_BY gives them one. `RIGHT_JOIN` is refused, saying to swap the tables and write
  `LEFT_JOIN`. Lineage names each join's `ON=` with what it keeps. The how-to "Semi-, anti-
  and full joins" walks through them.
- **`broadcast=True` on JOIN, LEFT_JOIN, SEMI_JOIN and ANTI_JOIN** asks for a map join: the
  joined table is copied to every worker, written as Hive's `/*+ MAPJOIN(t) */` hint. Hive
  heeds the hint once the Session setting "map_joins" is sent, which sets
  `hive.ignore.mapjoin.hint=false`. That setting also lets Hive make map joins by itself.
  Spark always heeds the hint.
- The Example database has a seventh table, `ops.scheduler_runs`: the scheduler's own record
  of the runs it started on 2026-09-23 and 2026-09-24, which lacks run 99 and holds a run 100
  that job_runs lacks, for FULL_JOIN to find. sqlglot Composer's Example database can't run a
  `LEFT SEMI JOIN`, and says so.

**Windows**

- **`window(PARTITION_BY=..., ORDER_BY=..., rows=(-6, 0))`** names the rows a calculation looks
  across for each row. Pass it as `over=` to `sum_of`, `average_of`, `count_rows`, `min_of`
  and `max_of` for a running total, a moving average or a group's total beside each row; and
  to the new `rank`, `dense_rank`, `ntile`, `lag`, `lead`, `first_value` and `last_value`,
  which always take one. `row_number(over=window(...))` numbers rows the same as
  `row_number(PARTITION_BY=..., ORDER_BY=...)`, which still works. A Window keeps every row,
  so a Statement's Key stays what it was. A value worked out over a Window doesn't add up
  again: sum_of refuses it unless you pass `adds_up=True`. Lineage lists each Window's groups
  and order under "Rows that count". The how-to once called "Finish in pandas", now "Look
  across rows, then finish in pandas", works out lag, rank and a rolling sum this way. sqlglot
  Composer's Example database can't run a Window; Spark Composer's can.
- **A write whose Window looks back may read earlier days and write one day**: read the day and
  the days before it in a Derived table that keeps the day column, and keep only the day
  written in the Statement that writes, with `WHERE(equals(the_derived_table.dt, day))`. The
  Toolbox writes the day that Statement keeps. Only a write with a Window may do this: any
  other write that reads several days is refused, as in 4.x.

**Stacks and subtotals**

- **Stacks: `UNION_ALL`, `UNION`, `INTERSECT` and `EXCEPT` put whole Statements' rows
  together**, one Statement after another, their columns matched by name, so a column is never
  stacked under one of another name. A Statement that lacks a column, or returns it as
  another kind of value, is refused, with the column named. A Stack is a Statement: run,
  show_hive and derived(...) take it, and by_day splits each Statement it stacks (a `UNION`,
  `INTERSECT` or `EXCEPT` only when each Statement returns the day). `UNION`, `INTERSECT` and
  `EXCEPT` keep each different row once, so their rows have a Key; `UNION_ALL` keeps every
  row, so its rows have none. Lineage feeds each column of a `UNION_ALL` or `UNION` from every
  Statement, and each of an `INTERSECT` or `EXCEPT` from its first, the others deciding which
  of its rows are kept. The how-to "Reconcile two tables" runs `EXCEPT` both ways.
- **Subtotals: `GROUP_BY(rollup(...))`, `cube(...)` and `grouping_sets(...)`** add subtotal
  rows to the groups' rows, written as Hive's `GROUPING SETS`, and `is_total(column)` tells a
  subtotal row from a row whose column is really NULL. The Toolbox refuses to write subtotals
  into a Saved table, as their rows repeat the rows they total: write the plain GROUP_BY, and
  add the subtotals when you read it. sqlglot Composer's Example database can't make subtotals
  and says so; Spark Composer's can. The how-to "Subtotals and grand totals" walks through
  them.

**Keeping reads and joins fast**

- **Three Statements that keep reads and joins fast**, each safe to send again:
  - `repair_partitions(t)` writes `MSCK REPAIR TABLE`, which adds to the warehouse's list of
    a Saved table's days each day folder it finds that the list lacks, as after creating a
    table again where its old files stayed.
  - `compute_statistics(t, day)` writes `ANALYZE TABLE ... PARTITION(...) COMPUTE
    STATISTICS`, which counts a day's rows for Hive to plan joins from; `columns=True`, or a
    list of columns, counts columns too (`FOR COLUMNS ...`).
  - `explain(s)` writes `EXPLAIN` before a Statement's Hive, and `run` gives back Hive's plan
    for it as text.

  The first two take only your own Saved tables, Table references with `location=`. The
  how-to "Keep reads and joins fast" puts them beside Partitions, file sizes, Buckets and the
  Session settings `"map_joins"`, `"statistics_on_write"` and `"merge_small_files"`.
  help(create_table) now says that `create_table(t, may_exist=True)` is safe to send again
  too.
- Spark Composer's Example database answers an `EXPLAIN` of a query with Spark's plan;
  sqlglot Composer's says its small executor has none to give. Both answer a `SET` line, as
  Spark does, with the setting and its value.

### Refused now

- **A write into a Saved table with a Key the Toolbox can't see each row keeps**: see To
  update, above. The Toolbox sees it from a GROUP_BY over the Key's columns, a
  SELECT_DISTINCT, a row_number(...) kept at 1 for each Key in a Derived table, or a FROM
  table whose own Key gives one row per Key written, when each join matches its joined table's
  whole Key. The day written counts as one value, so a Key such as `key=["job_id", "dt"]` needs one
  row for each job_id.
- **create_table refuses a Table reference with no `location=`**, and **each admin function
  refuses a table that isn't one of your Saved tables**, a Table reference with no
  `location=`, such as a table another team fills: `admin.drop_table`, which as `drop_table`
  took any Table reference, included. See To update, above.
- Table(...) refuses storage options on a table with no `location=`, a `location=` that isn't
  a whole path from the top folder, such as `/data/your_team/tables`, or already ends with the
  table's own folder, two Saved tables whose folders
  are one or sit one inside the other, and any option create_table couldn't write.
- **by_day refuses a Statement whose Window looks across days**: one whose `PARTITION_BY=`
  leaves out the day, such as each job's `lag(...)`: split by day, each day's Statement would
  stop at its own day's edge. In 4.x a `row_number(...)` there was refused as grouping across
  days; the message now says how the Window would be cut off, and how to write one day that
  reads the earlier days it needs.
- `hive_function("lag", ...)`, and `"lead"`, `"rank"`, `"dense_rank"`, `"ntile"` and
  `"row_number"`, are refused as before, and the message now names the Toolbox's own function,
  such as `lag(column, over=window(...))`, where it gave a pandas line.

### The license

- **The Toolbox, its Example projects and its Templates are under the MIT No Attribution
  license** (`LICENSE`, at the top of the download): use, change, share or sell them, privately
  or commercially, with no need to name where they came from, so you needn't copy `LICENSE`
  along with the folders. Before, the download had no license at all. Nothing to change in
  your notebooks or files.
## 4.1

Nothing to change in your notebooks or files: copy the two folders in over 4.0's.

- **Spark Composer's Example database can't reach anything off your computer.** The Spark it
  starts for its made-up tables runs in a Python of its own, which now refuses any connection,
  or lookup of a name, that would leave this computer, and stops with a RuntimeError naming
  what it refused, in that process's log. It still talks to your notebook's Python and to its
  own Java on 127.0.0.1, as before. Nothing changes in your own Python, where your send still
  reaches your warehouse, and sqlglot Composer is unchanged.
- **Every Python file and page in the download is checked for code that could reach a
  network** before it is exported: the Toolbox reaches nothing but your send, and the Example projects and Templates
  reach nothing at all.

## 4.0

### To update from 3.x

These are the same steps whether you have 3.0, 3.1 or 3.2.

- **The Toolbox is now two folders: `composer_core`, the Composer core, which holds the code
  both Editions share, and your Edition's own.** Before 4.0, each Edition was one folder you
  copied on its own. Copy both, each whole, side by side where your notebooks are. An
  Edition's folder imported without `composer_core` beside it stops, and says to copy it in.
  To update later, delete both folders and copy both in again from one download. These change
  notes moved too: they were in `sql_composer/CHANGES.md` and `spark_composer/CHANGES.md`, and
  are now in `composer_core/CHANGES.md`.
- **SQL Composer is now sqlglot Composer, in the folder `sqlglot_composer`.** Delete your
  `sql_composer` folder, and copy in `sqlglot_composer` and `composer_core`. Then, in your
  notebooks and scripts, change each `from sql_composer import` to
  `from sqlglot_composer import`, and each `sql_composer.VERSION` to
  `sqlglot_composer.VERSION`. That includes every Table reference file write_table_reference
  wrote for you: each has the line `from sql_composer import Table` below its docstring.
  Restart the kernel last.
- **With Spark Composer, your `from spark_composer import` lines stay as they are.** Delete
  your `spark_composer` folder, copy in the new one and `composer_core` beside it, and restart
  the kernel.
- **Import every name from your Edition's folder itself**, as the README says. The
  files inside it moved to `composer_core`, so a line such as
  `from sql_composer.refusals import GuardRefused` or `import spark_composer.example_database`
  now stops with a ModuleNotFoundError. Write `from sqlglot_composer import GuardRefused` or
  `from spark_composer import example_database` instead.
- **One Edition per Python, such as one notebook.** Before 4.0, the README advised using one
  Edition per notebook, but importing both in one Python worked. Now importing the second
  stops, and says to make every import line name the same Edition, then restart the kernel:
  the two share the code that builds your Statements, which writes the Hive for one Edition at
  a time.
- **A Guard's traceback names `composer_core.refusals.GuardRefused`**, since the Guards are
  in the Composer core. Before 4.0 it named the Edition's folder, as in
  `sql_composer.refusals.GuardRefused`. To catch it, import it from your Edition's folder, as
  before: `from sqlglot_composer import GuardRefused`.
- **Two new refusals can stop code that ran before 4.0**, each listed under Refused now below:
  run refuses a read whose send gives back something other than a pandas DataFrame, such as a
  list of rows, and a comparison of two tables' days written different ways is refused. If your
  send gives back a list of rows, end it with `return pd.DataFrame(rows)`.

### New

- **show_hive prints the Hive that runs, ready to paste into another program**, such as Hue,
  DBeaver or spark-sql, and returns it, so `text = show_hive(...)` keeps it. Each Statement's
  Hive is what to_hive gives and run sends, with a `;` at the end. Given several Statements, or
  a list such as by_day(...) gives, it heads each with its number and the name of its
  variable. It is the Toolbox's 64th name.
- **A how-to page, `how_to.html`, beside `examples.html` in each Edition's folder.** Open it in
  your browser. Each of its 30 how-tos walks through one job from start to finish, in steps you
  paste into one notebook, each run on the Example database. Getting started (1-18) goes from a
  first notebook to a daily pipeline and its Lineage. Intermediate (19-30) covers a table whose
  days are written like 20260911, or that is partitioned first by something other than its
  days; looking a value up as of a day; week and month totals; rows that come in late; a
  pipeline of Saved tables; sharing Building blocks; data-quality checks; Statements made from
  settings; hive_function; finishing in pandas; reviewing a change with Lineage; and testing
  your own Statements. As with `examples.html`, importing the folder stops if `how_to.html` is
  missing.
- **The Example database has three more tables**, `job_events`, `job_owners` and
  `region_costs`, with rows on 14 days, 2026-09-11 to 2026-09-24, so you can practise week
  totals, a job that moves to another team (report_build, on 2026-09-18), and a table
  partitioned by region, then by a day written like 20260911. Its refusal of a table it doesn't
  hold names all six.
- **The download holds Example projects and Templates**, in the folders `example_projects`
  and `templates`, each with a folder per Edition. They are for reading and copying from, and
  the Toolbox doesn't need them. An Example project is a folder laid out as a project at work
  should be: Table references, Building blocks, Statements, and a `run_pipeline.py` that runs
  them in order. There are two, `starter` and `intermediate`, which builds on it. A Template is
  the empty shape of one of your own scripts to copy and fill in, each placeholder listed in its
  docstring: a starter set and an intermediate set, with a README giving the order to use them
  in. Each file's first line says to copy it, then edit your copy.
- **The README has four new sections**: Update from 3.x, How-tos, Example projects and
  Templates. Its "Where the two Editions' Hive differs" now says what Spark's ANSI mode is.
- **write_table_reference's docstring says it looks for the Date partition in the first
  partition column only.** A table partitioned first by something else, such as region, gets
  `date_partition=None` and a TODO naming its partition columns, as it did in 3.2.

### Refused now

- **Comparing two tables' days written different ways is refused**, a new Guard with no
  opt-out. `equals(region_costs.dt, job_events.dt)`, where region_costs writes its days like
  20260925 and job_events like 2026-09-25, was built without a word and matched no rows: Hive
  compares days as text. Any comparison of the two is refused, in `ON=` or in `WHERE`, and so
  is one through a Derived table's column that passes a Date partition on unchanged. The
  message names both date_formats, and the fix points to the intermediate Example project,
  which saves one table's days written the other's way.
- **run refuses a send that gives back something other than a pandas DataFrame** for a read,
  such as the plain list of rows a query API gives, or None from a send with no `return`. The
  fix says to turn the rows into a DataFrame at the end of your send: on Spark,
  `spark.sql(hive).toPandas()`, and from a query API, `pd.DataFrame(rows)`, or
  `pd.DataFrame(rows, columns=names)` when each row is a tuple. Before, run gave back the list
  as it was. A write's send may still give back anything.
- **run, to_hive and show_hive refuse what isn't a Statement, in their own name.** For a
  Derived table, the fix wraps it in `statement(SELECT(all_columns(d)), FROM(d))`, and for a
  list, such as by_day(...) gives, it loops over its Statements.
- **A day written the wrong way is shown as the Table reference writes it**, using your own
  day where it can be read. A day written another table's way also offers that table's
  date_format.
- **A calculation's name in a comparison gets a clearer fix.** For `HAVING(at_least("runs",
  3))`, where "runs" is the name AS gave `count_rows()`, the fix says to write the calculation
  itself, since WHERE and HAVING are worked out before SELECT names anything.
- **A calculation GROUP_BY leaves out is named as itself.** For
  `AS(week_start(job_events.dt), "week")`, the fix is `GROUP_BY("week")`, not the column inside
  it.
- **The repeated-rows Warning on a table whose key holds its Date partition** says to match
  the day too, with `all_of`.
- **write_table_reference names the file it won't overwrite**, not its whole path, and its TODO
  for a table partitioned first by something else says "its last region value" and "name it in
  date_partition=", not "its newest region" and "name it".

### Fixed

- **A Warning always shows.** A RepeatedRowsWarning from a scope with no `__name__`, as some
  notebook tools and `exec` give, was dropped unseen, and under `python -c` it stopped with
  "'__main__' is not a built-in module".
- **export_lineage lists a LEFT_JOIN's conditions only under the columns read from its
  table.** A LEFT_JOIN keeps every row before it, so its own ON=, and what decided the joined
  table's rows (its WHERE, or the WHERE and JOIN of the Statement that wrote it), decide only
  the columns that come from it. Before 4.0 they were listed under every column's "Rows that
  count", in the Statement that joins and in every Statement downstream of the Saved table it
  writes, as if they had dropped rows. They are still listed under every column with
  many_matches=True, since each row can then count several times, and when another condition
  that can drop rows reads the joined table, as a `WHERE(is_null(...))` that keeps only the rows
  with no match does.
- **export_lineage lists a write's condition on a joined table's day with the day written.**
  A write that reads job_day for the day it writes and JOINs job_owners with
  `equals(job_owners.dt, job_day.dt)` in its ON= may also have
  `WHERE(equals(job_owners.dt, day))`. That condition only picks the day, as the day written
  does, so it is now listed only in the write's own section, beside the day written, not under
  the rows that count in the Statements that read the Saved table.
- **A join that compares a column with itself stops.** A JOIN or LEFT_JOIN whose ON= sets a
  column of the joined table equal to the same column of a table of the same name, as when one
  Statement reads one Building block twice, stops with a ValueError saying to give the second
  a name of its own. Before 4.0 it warned that the join "matches on nothing".
- **sqlglot Composer's Example database refuses a query it would answer wrong**: one that
  works out GROUP_BY or a count or a sum after a join, where sqlglot's executor, the small
  engine that runs sqlglot Composer's Example database, would read a joined table's column in
  place of a same-named column of a table before it (NULL after a LEFT_JOIN). It says "The Example database can't run this Hive" and how to rename the column.
  Spark Composer's Example database runs it right.

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
