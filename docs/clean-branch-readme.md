# sqlglot Composer

This is version <!-- VERSION -->.

Write Hive SQL as Python. You put clause functions (`SELECT`, `FROM`, `WHERE`, ...) together in
SQL order, and the Toolbox writes the Hive string. It refuses a Statement that would silently
give a wrong number, or read or return too much, and says what to change.

This page is a tutorial: eight steps, from installing the Toolbox and starting a Project,
through your tables' references, a Saved table of your own and the Lineage of each of its
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

A Project is the folder your work lives in: the Toolbox, your query and execute, your tables'
Table references, the Building blocks your notebooks share, and a folder per Saved table. Open a
notebook in the Project's folder, and lay it out with one call:

```python
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
```

Import from `sqlglot_composer`, at its top level, never from a file inside it. The Toolbox
never connects to anything itself: it writes Hive as text, and `run` hands that text to one of
two functions of yours, in `warehouse.py`: `query`, which runs Hive that gives back rows, such as
a SELECT, and gives them back as a pandas DataFrame, and `execute`, which runs Hive that changes
something, such as a write, and gives back nothing. The Toolbox picks which one each Statement
goes to. Write them once, in place of the Example database's calls `project.start()` put there:
for example, through your team's query API,

```python
import pandas as pd

import my_api  # your team's query API


def query(hive: str) -> pd.DataFrame:
    return pd.DataFrame(my_api.query(hive))


def execute(hive: str) -> None:
    my_api.execute(hive)
```

A notebook imports the ones it uses, as in `from warehouse import query, execute`.

Make and remove Table folders and Table references with the `project` module's Project
actions, such as `project.new_table(...)`, never by hand in your file explorer: each is
logged in `admin/admin_log.md`, and listed in the registry, `admin/registry.csv`. `admin/`
holds a notebook per Project action, such as `new_table.ipynb`, ready to fill in; calling one
from any notebook of the Project does just the same.

The how-to [Start a Project](../sqlglot_composer/how_to.html#start_a_project) walks through what
each folder is for, your query and execute, the lines a notebook deeper in the Project starts
with, and the mistakes people make first. A later how-to that starts a Project of its own, since
its page has none, says so: in yours, leave `project.start()` out.

## 3. A first Statement

The Example database ships inside the Toolbox: nine made-up tables, a `query` that runs
Statements on them, and an `execute` that prints what it is given and changes nothing, so you
can practise without touching the warehouse.

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

`run(first, query=...)` sends the Hive through a `query`, since `first` reads rows. On the
Example database, its own `query` runs it:

```python
>>> from sqlglot_composer import run
>>> run(first, query=example_database.query)
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
`between(job_runs.dt, "2026-09-23", "2026-09-24")`, to get the rows it shows.

How-to: [Build a first Statement and paste its Hive](../sqlglot_composer/how_to.html#build_a_first_statement).

## 4. Your own tables

A Statement reads your tables through their Table references: each table's columns, their
types, its Partitions (the columns it is stored by, such as a day or a region) and its Key (the
columns that name one row), where it has them. `project.add_references(["your_db.your_table", ...], query=query)`
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

## 6. Save a table

A Saved table is a table of yours that a Statement writes, in a folder of its own, so a number
worked out once is read by everyone after. Hive can't change single rows of such a table, so the
Toolbox has no `UPDATE`, `DELETE`, `MERGE` or `TRUNCATE`: `INSERT_OVERWRITE` writes the
Partitions its rows fill again, whole, replacing them, or the whole table when it has none, and
old Partitions go with `admin.drop_partitions`.

In a Project, `project.new_table("mart.your_table")` gives each Saved table a Table folder in
`tables/`, holding its notebook, made from a Template, and writes its Table reference for you
to fill in. The notebook's logic defines `write()`, which takes nothing and gives the Statement
that writes the table. `project.run_tables(query=query, execute=execute)` then writes every
table, each after the tables it reads.

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
and `warehouse.py`, then the Building blocks, then each Table notebook's logic.
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

An Example project is a Project made for the Example database's tables, laid out as yours is:
made by the `project` module's Project actions, then filled in by hand, with its Building
blocks written by hand. `example_projects/` holds two:

- `starter/`, on `ops.jobs`, `ops.job_runs` and `ops.run_alerts`: two Saved tables
  partitioned by day, and a third, each team's day, read from both, through a Building block
  and Aliases, each made from the `saved_table` Template.
- `intermediate/`, on `ops.job_events`, `ops.job_owners`, `ops.region_costs`,
  `ops.region_budgets` and `ops.team_notes`, which builds on the starter project: six Saved
  tables, among them an incremental load, an as-of lookup, a weekly rollup, quality checks
  from the `quality_checks` Template, a table partitioned by region and written a region at a
  time, and one with no partitions and no Key.

Each project's `README.md` says what each folder holds, how each file was made, and how to run
it. Copy the `sqlglot_composer` folder into a project's folder first, as a Project holds it,
then open its notebooks. The Example database can be read but not written, so a Table notebook's cell 3
prints each write's Hive and runs only what reads the ops tables, and
`admin/run_tables.ipynb`, with no execute, prints every write in order, writers first, and
sends nothing (a dry run).

To start a Project of your own, start it with `project.start()` rather than copying one: an
Example project is for reading, and copying it would bring its tables and its Admin log.

## Templates

A Template is the empty shape of one of your notebooks or files, to make a new one from. They
ship inside the Toolbox, and `project.start()` copies them into your Project's
`admin/templates`, where they are yours to edit, or to add your own beside.
`project.new_table("mart.your_table")` makes a Table folder's notebook from the `saved_table`
Template, and `template=` names another, filling in the table's database and name. Every other
placeholder, a word in angle brackets such as `<SOURCE_TABLE>`, is yours to replace, brackets
and all; Python stops at one left in, so a notebook can't run half filled in. Each Template's
first lines list its placeholders, with an example of each.

The Table notebook Templates, each a notebook of the same five code cells around its own logic:

- `saved_table`: a Saved table worked out from a table it reads, with `create`, `rows`,
  `preview` and `write`, partitioned however its Table reference says, or not at all.
- `quality_checks`: the row count of each Partition of a table you read, saved, and checks for
  repeated keys and NULLs.

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
`job_runs.duration_mins / 60`. The star import brings the 99 names listed here before the admin
module. Two modules' functions come last: the admin module's, which change your own Saved
tables, and the project module's, which make and archive a Project's folders and files. The star
import leaves both out, so import each by name, as `from sqlglot_composer import admin, project`,
and call `admin.drop_table(t)` or `project.new_table("mart.daily_job_runs")`.

<!-- CHEAT SHEET -->
