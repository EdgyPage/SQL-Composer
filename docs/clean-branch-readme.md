# sqlglot Composer

This is version <!-- VERSION -->.

Write Hive SQL as Python. You put clause functions (`SELECT`, `FROM`, `WHERE`, ...) together in
SQL order, and the Toolbox writes the Hive string. It refuses a Statement that would silently
give a wrong number, or read or return too much, and says what to change.

This page is a tutorial in eight steps, one story through one Project: you start it, add your
tables' Table references, build Statements on them, share Building blocks, save tables of your
own, follow their Lineage and keep the Project in order. The Starter Example project shows a
Project much like the one the story leaves, filled in. Each step
is a short summary of the Getting started how-to of the same name, which walks through it in
full on `sqlglot_composer/how_to.html`, a page in the download to open in your browser. Every
example here runs on the Example database, nine made-up tables that ship inside the Toolbox.
What changed in each version, and how to update from it, is in `CHANGES.md`.

## 1. Start a Project

The Toolbox needs Python 3.11 or newer, pandas, numpy and sqlglot, and is tested on Python 3.12,
which `requirements.txt`'s pins are for. It is one folder, `sqlglot_composer`.

1. Download this branch as a zip and extract it.
2. Install what the Toolbox needs, at the versions it is tested on: run
   `pip install -r requirements.txt` in the download's top folder, or, from a notebook,
   `%pip install -r` followed by the path to that file.
   - On Python 3.11, numpy 2.5.4 can't install: change its line in `requirements.txt` to
     `numpy==2.4.6`, which pandas 3.0.6 runs on there, before you run pip.
   - A package your notebook already has, such as pandas, needn't be installed again: delete
     its line, so pip doesn't replace it.
   - The Toolbox works with any sqlglot from 30.19.0 up to (not including) 31.
     `import sqlglot; print(sqlglot.__version__)` in a notebook shows which you have: keep
     sqlglot's line, so pip installs the one the Toolbox is tested on, unless yours is in that
     range.
3. Make an empty folder for your Project, and copy the whole `sqlglot_composer` folder into
   it. Keep your own files beside it, never inside it.
4. Open a notebook in the Project's folder, such as start.ipynb, and lay the folder out with
   one call:

```python
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py.
Next: write your two functions, query and execute, in warehouse.py.
```

Import from `sqlglot_composer`, at its top level, never from a file inside it.

### Every file of a Project

You make three things by hand: the Project's folder, the copied `sqlglot_composer` folder and
the notebook you run `project.start()` from. Every other file is made by a call of the
`project` module, a Project action, never by hand in your file explorer: each is logged in the
Admin log, and the registry lists what it made, so `project.check()` can tell what is missing
or made by hand.

| Path | Made by | What you fill in |
|---|---|---|
| your Project's folder, such as my_project | you, in your file explorer | nothing |
| `sqlglot_composer/` | you: copied in from the download | nothing: never edit a file inside it |
| `sqlglot_composer/version.txt`, the Toolbox's version and its list of files | the download | nothing: the import checks the folder against it |
| `start.ipynb`, or any name you like | you, in Jupyter: the notebook you run `project.start()` from | nothing: keep it for trying things out, or delete it |
| `warehouse.py` | `project.start()` | your query and execute |
| `admin/`, a notebook per Project action, such as new_table.ipynb and run_tables.ipynb | `project.start()` | the call each holds, such as the table's name; the same call from any notebook of the Project does just the same |
| `admin/admin_log.md`, the Admin log | `project.start()`, then each Project action adds an entry | nothing |
| `admin/project_version.txt`, the Toolbox version that last wrote the Project | `project.start()`, then `project.upgrade()` | nothing |
| admin/conversions/, a Conversion folder per query of someone else's Hive you convert, until you finish it | `project.convert(...)`, from `admin/convert.ipynb`, as [Convert someone else's Hive](../sqlglot_composer/how_to.html#convert_someone_elses_hive) shows | the checks its notebook asks for, then `project.finish_conversion(...)` |
| an Upgrade's checklist in admin/, named for the version it upgraded to, such as upgrade_7.3.md: what it did and a box for each change it left you | `project.upgrade()` | the changes it lists, each marked `# UPGRADE <version>:` at its line |
| `admin/registry.csv`, the registry | `project.start()`, then each Project action that makes or archives a Table folder, a Table reference, a Building block or a Conversion folder adds a row | nothing |
| `admin/templates/`, the Templates | `project.start()` | nothing, unless you want your team's own shape |
| `references/<db>__<table>.py`, a Table reference per table | `project.add_references([...], query=query)` for a table in the warehouse, or `project.new_table(...)` for a Saved table of your own | its TODO lines, and your own Aliases |
| `references/<db>.py`, a Database module per Database, such as `references/ops.py` | each Project action that adds or archives a Table reference | nothing: never edit it |
| `references/reference_sheet.csv`, the Reference sheet | `project.refresh_reference_sheet()` | nothing |
| `building_blocks/<name>.py`, a Building block | `project.new_block("<name>")` | its `<...>` and TODO lines |
| `tables/<db>__<table>/<db>__<table>.ipynb`, a Table notebook per Saved table | `project.new_table("<db>.<table>")` | its `<...>` lines |
| `tables/<db>__<table>/lineage/`, the table's Lineage | its notebook's lineage cell | nothing |
| `lineage/`, beside the notebook you run it from: the Lineage of a Statement exported outside a Table notebook | `export_lineage(...)` | nothing |
| admin/removed/, what you archive | `project.remove_table(...)`, `project.remove_reference(...)`, `project.remove_block(...)`, `project.finish_conversion(...)` and `project.remove_conversion(...)`, and `project.upgrade()`, which keeps each file as it was before it changed it | nothing |

### Your query and execute

The Toolbox never connects to anything itself: it writes Hive as text, and hands that text to
one of two functions of yours, in `warehouse.py`. `query` runs Hive that gives back rows, such
as a SELECT, and gives them back as a pandas DataFrame; `execute` runs Hive that changes
something, such as a write, and gives back nothing. You pick which one sends a Statement, by
calling `run_query(s, query)` or `run_execute(s, execute)`. `project.start()` wrote them to run
on the Example database; at work, write them over your team's API, once:

```python
import pandas as pd

import my_api  # your team's query API


def query(hive: str) -> pd.DataFrame:
    return pd.DataFrame(my_api.query(hive))


def execute(hive: str) -> None:
    my_api.execute(hive)
```

How-to: [Start a Project](../sqlglot_composer/how_to.html#start_a_project), with what to do when
your API gives rows without their column names, and the lines a notebook deeper in the Project
starts with.

## 2. Add your tables' references

A Statement reads a table through its Table reference: a small file in `references/` holding
the table's columns and their types, its Partitions (the columns it is stored by, such as a day
or a region) and its Key (the columns that name one row), where it has them.
`project.add_references` asks each table for its columns, through your query, and writes its
file, and the Database module of its Database:

```python
>>> from warehouse import query, execute
>>> project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"], query=query)
Wrote references/ops__jobs.py, references/ops__job_runs.py and references/ops__run_alerts.py: fill in their TODO lines.
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs and ops.run_alerts.
Restart the kernel of a notebook that imported references, to see a table added since.
```

You fill in what the table can't say: what one row is, its Key, and which columns don't add up,
such as averages. Below it, you may add Aliases, your own names for its columns and conditions.
Then one import gives every table of the Database, and each column at a dot after its table:

```python
>>> from references import ops
>>> ops.job_runs.status  # -> Column
job_runs.status
```

`check_table_reference(ops.job_runs, query=query)` checks the file against its table, and
`check_key` checks the Key you wrote.

How-to: [Add your tables' references](../sqlglot_composer/how_to.html#add_your_tables_references).

## 3. Build and run a first statement

A Statement is built along a chain of types, each made by a call on the one before:

| You write | It gives | Which is |
|---|---|---|
| `ops.jobs`, a Table reference | `Table` | a table: its columns, its Partitions and its Key |
| `ops.jobs.job_id` | `Column` | one of its columns |
| a test, such as `equals(...)` | `Condition` | a test of each row, for WHERE or ON |
| `SELECT(...)`, `FROM(...)`, `WHERE(...)` and the others | `Clause` | one part of a query |
| `statement(...)` | `Statement` | its Clauses, checked together as one query |
| `to_hive(...)` | `str` | the Hive: the query's text, ready to paste |
| `run_query(..., query)` | `DataFrame` | the rows your query gives back, in pandas |

The runs that failed on 2026-09-23 and 2026-09-24. ops.job_runs is partitioned by dt, so a
Statement on it must filter dt:

```python
>>> from sqlglot_composer import *
>>> job_runs = ops.job_runs  # -> Table
>>> failed = statement(  # -> Statement
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
...     FROM(job_runs),
...     WHERE(equals(job_runs.status, "FAILED"),
...           between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> print(to_hive(failed))
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.status = 'FAILED' AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
>>> run_query(failed, query)  # -> DataFrame
   run_id  job_id          dt
0      97       3  2026-09-23
1     102       2  2026-09-24
```

`show_hive(failed)` prints the same Hive with a `;` at the end, ready to paste into Hue,
Beeline or DBeaver.

Every function and class in the cheat sheet has a Worked example in its docstring:
`help(to_hive)` shows the one for `to_hive`. The examples use every Toolbox name and the Example
database's `jobs` and `job_runs`: its own Table references of `ops.jobs` and `ops.job_runs`,
the same tables as your Project's `ops.jobs` and `ops.job_runs`, which ship inside the Toolbox
so an example runs with no Project. Run this first to paste one into a notebook:

```python
from sqlglot_composer import *
jobs, job_runs = example_database.jobs, example_database.job_runs
```

The examples take today as 2026-09-25, the day after the Example database's last day.
`last_n_days(...)` counts back from your own today, so in a pasted example that uses it, write
`between(...)` with the days the example's Hive shows in its place, such as
`between(job_runs.dt, "2026-09-23", "2026-09-24")`, to get the rows it shows.

How-to: [Build and run a first statement](../sqlglot_composer/how_to.html#build_and_run_a_first_statement),
with every Condition `WHERE` takes, `AS`, `all_columns` and `first_look`.

## 4. Count, join and stay safe

`GROUP_BY` makes one row per group, and `count_rows` and `sum_of` work out its numbers:

```python
>>> per_job = statement(  # -> Statement
...     SELECT(job_runs.job_id,
...            AS(count_rows(), "runs"),
...            AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
>>> run_query(per_job, query)  # -> DataFrame
   job_id  runs  failed_runs
0       1     4            0
1       2     3            1
2       3     2            1
```

`JOIN` and `LEFT_JOIN` bring in another table, matched on its Key. As you build a Statement,
the Toolbox checks it three ways: a Guard refuses one that would silently give a wrong number,
such as a join that counts a row twice; a Warning lets one through but says why a number may
come out wrong; and a Load limit refuses one that would cost the cluster or your notebook too
much, such as a read that filters none of a table's partition columns. Each message says what
happened, why it matters, the usual fix and the opt-out, a keyword for when you truly mean it.

How-to: [Count, join and stay safe](../sqlglot_composer/how_to.html#count_join_and_stay_safe),
with `HAVING`, the top N, Derived tables, the rows with no match, and when each opt-out is
right.

## 5. Share Building blocks

A Derived table is a Statement given a name with `derived`, which another Statement reads like a
table. Wrapped in a function, kept in a file of its own in `building_blocks/`, it is a Building
block, which every notebook of the Project imports, so a piece several Statements need is
written once. `project.new_block` makes its file from the Project's `building_block` Template,
for you to fill in:

```python
>>> project.new_block("runs_per_job")
Wrote building_blocks/runs_per_job.py, from admin/templates/building_block.py:
fill in its <...> and TODO lines.
```

The Starter Example project's `building_blocks/runs_per_job.py` is this file filled in: each
job's runs, failed runs and minutes, for the rows a Condition it is given picks.

How-to: [Share Building blocks](../sqlglot_composer/how_to.html#share_building_blocks).

## 6. Save a table

A Saved table is a table of yours that a Statement writes, so a number worked out once is read
by everyone after. `project.new_table` makes its Table folder, holding a Table notebook made
from the `saved_table` Template, and its Table reference, for you to fill in:

```python
>>> project.new_table("mart.alerts_per_severity")
Made tables/mart__alerts_per_severity/: mart__alerts_per_severity.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__alerts_per_severity.py: fill in its <...> and TODO lines.
```

The notebook's logic sets `READS`, the rows its write reads, and defines `create()`, `rows()`,
`preview()` and `write()`, each giving a Statement and running nothing. `write()` gives an
`INSERT_OVERWRITE`, which replaces whatever the Partitions its rows fill held, or the whole
table when it has none, so sending it twice leaves the same rows, not twice as many. A write
that fills its Partitions from its rows needs the Session setting "dynamic_partitions", which
`show_hive` prints ahead of it. `project.run_tables(execute=execute)` then writes
every Saved table, each after the tables it reads, sending that setting first; with no execute,
it prints each write's Hive in order and sends nothing.

How-to: [Save a table](../sqlglot_composer/how_to.html#save_a_table), with the Starter Example
project's `mart.alerts_per_severity` notebook filled in beside its Table reference.

## 7. Follow lineage

`export_lineage(...)` writes the Lineage of a Statement: an HTML page and a Markdown twin that
follow each output column back to the table columns it reads, and list every condition that
decides which rows count. From a Table notebook, its lineage cell writes them into its Table
folder's `lineage/`, named by the time and the table, so each export joins the table's history.
A table that reads another Saved table passes that table's write too, from
`project.load("mart.daily_job_runs").write()`, so its Lineage goes on back to the tables they
start from. A change made in pandas is declared with `python_step`, so the Lineage doesn't stop
at it.

How-to: [Follow lineage](../sqlglot_composer/how_to.html#follow_lineage).

## 8. Keep the Project in order

`project.check()` compares the registry with the Project's files, and changes nothing:

```python
>>> project.check()
Every Table folder, Table reference and Building block is registered, and each one registered is there.
```

It names any file made by hand, with the `project.register(...)` call that adopts it, and any
file deleted by hand. `project.refresh_reference_sheet()` lists every column of every table in
one CSV file, and `admin/check_references.ipynb` checks each Table reference against its table.
`project.remove_table(...)`, `project.remove_reference(...)` and `project.remove_block(...)`
archive what you no longer need in admin/removed/, deleting nothing. And your files sit in
three Levels, each importing only from the Toolbox and the Levels below it: the Table
references and `warehouse.py`, then the Building blocks, then each Table notebook's logic.

How-to: [Keep the Project in order](../sqlglot_composer/how_to.html#keep_the_project_in_order).

## The how-tos

Every how-to walks through one job from start to finish, in steps you paste into one notebook,
in order: its goal, its steps, each run on the Example database with what it shows, how to check
it worked, and the mistakes people make first.

- Getting started: one story through one Project, a how-to for each of the README's steps: a
  Project, its Table references, Statements, Building blocks, Saved tables, their Lineage and
  the Project's upkeep.
- Intermediate: a menu, each starting from the Intermediate Example project: one job each,
  such as rewriting some partitions, rollups, Keys, quality checks and testing. Each says
  which Getting started how-tos it needs.

<!-- HOW-TOS -->

## The Example gallery

The [Example gallery](../sqlglot_composer/examples.html), `sqlglot_composer/examples.html`,
holds every Worked example on one page: its Python and, for each Statement it builds, the Hive
and any result. Open it in your browser. It needs nothing else: a box at the top keeps only the
examples holding every word you type, and Ctrl+F searches it too. Besides each docstring's
example, it holds the Worked examples that stand on their own: common jobs built in steps that
each say why, such as building a Saved table or finding rows with no match, and Statements that
give a wrong number shown beside their fix. Each result comes from the Example database or,
where that can't run it, is computed in pandas.

## Example projects

An Example project is a Project made for the Example database's tables, laid out as yours is:
made by the `project` module's Project actions, then filled in by hand. `example_projects/`
holds two, and each one's `README.md` shows the file map of step 1 filled in, how each file was
made, and how to run it:

- `starter/`, on `ops.jobs`, `ops.job_runs` and `ops.run_alerts`: four Saved tables, each
  made from the `saved_table` Template. `mart.alerts_per_severity` is the Template filled in
  and nothing else; `mart.daily_job_runs` takes its rows from the Building block
  `runs_per_job`; `mart.alerts_per_job` joins each alert to its run; and `mart.team_day` adds
  up each team's day from `mart.daily_job_runs` alone among the Saved tables, with each job's
  team from `ops.jobs`, so it is written after it. It is much like the Project the Getting
  started how-tos leave, but not the same: it also holds `mart.alerts_per_job`, which no
  how-to makes, and it lacks what the how-tos add to show one thing each: the Table references
  of `ops.region_budgets` and `ops.team_notes`, from Count, join and stay safe,
  `mart.run_speed`, from Follow lineage, and `ops.scheduler_runs`, from Keep the Project in
  order.
- `intermediate/`, where the Intermediate how-tos start, on `ops.job_events`, `ops.job_owners`,
  `ops.region_costs`, `ops.region_budgets` and `ops.team_notes`: seven Saved tables, among them
  an incremental load, an as-of lookup, a weekly rollup, quality checks from the
  `quality_checks` Template, a table partitioned by region and written a region at a time, one
  with no partitions and no Key, and a finished Conversion, with the Hive it replaced.

Copy the `sqlglot_composer` folder into a project's folder first, as a Project holds it, then
open its notebooks. The Example database can be read but not written, so a Table notebook
prints each write's Hive and runs only what reads the ops tables, and `admin/run_tables.ipynb`,
with no execute, prints every write in order, writers first, and sends nothing (a dry run).

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
- `building_block`: a Derived table several notebooks read, which `new_block` writes into
  `building_blocks`, to fill in.

## Have Copilot write it

`copilot/`, in the download's top folder beside `sqlglot_composer`, holds the Copilot files:
plain text that teaches Microsoft Copilot the Toolbox, so
you can ask it in plain words for a Statement, a Table reference, a Table notebook's logic
cell or a Conversion. Open a new chat, paste the one file for what you want to do as your
first message, then ask, giving the import line and columns of each table to read.
`copilot/00_start_here.txt` says which file fits. Each file fits the 8,000 characters Copilot
takes at once, spaces and line breaks included; `copilot/count_characters.py` counts a
copy you edit. Run what Copilot gives you as you would your own code: the Toolbox still
refuses what would give a wrong number.

To hand over an Excel workbook's calculations, one chat holds five files:

1. Copy `copilot/formula_workbook.xlsx` and follow its Steps sheet to move the data and
   formulas in.
2. In a new chat, attach `copilot/03_build_a_statement.txt`, `04_joins.txt`,
   `05_windows_and_subtotals.txt`, `11_excel_formula_workbooks.txt` and
   `12_excel_power_query.txt` (or paste each as a message of its own), then attach your
   workbook and send "Convert this workbook".
3. Copilot answers with a map: which Tables are sources, the samples of your database's
   tables, and which are finals, each becoming a query. Check every Table you expected is
   there.
4. Each query writes `<...>` for a name it can't know, such as `<database>.<sales_data>`.
   Fill each in with your database's own names: your Project's `references/` folder has
   them, `ops__job_runs.py` for `ops.job_runs`, or ask whoever owns the data.
5. In `admin/convert.ipynb`, give each filled-in query to a Conversion:
   `project.convert("sales_summary", HIVE, query=query)`, with the query pasted as
   `HIVE = """..."""`. Its code is checked; Copilot's Python after the Hive is only for
   reading, and the Conversion's code wins where the two differ.

## Update

1. Note which version you have: `sqlglot_composer.VERSION` says, such as
   `'sqlglot Composer 5.1, exported ...'`, and, if the import stops, the first line of
   `sqlglot_composer/version.txt` does.
2. Delete the `sqlglot_composer` folder, and any `composer_core` folder beside it, left over from
   before 6.0.
3. From the new download, copy in the whole `sqlglot_composer` folder.
4. Restart the kernel, which still holds the old code.
5. If your Project was made by Toolbox 7.1 or newer, upgrade it: run `project.upgrade()` in a
   new cell of `admin/check_project.ipynb`, which imports `project` already, or of
   `admin/upgrade.ipynb` once your Project has one (its first Upgrade adds it). Updating is
   copying in the new folder; an Upgrade carries your Project's files to the new version, one
   version at a time: it makes each change that needs no judgement, keeping the file as it was in the
   folder admin/removed/, and marks each one it leaves for you with an `# UPGRADE <version>:` comment
   at the line. Work through the boxes in the checklist it writes in admin/, named for the
   version, such as upgrade_7.3.md;
   `project.check()` lists the marks left. It never touches the warehouse. How-to:
   [Upgrade your Project to a new Toolbox version](../sqlglot_composer/how_to.html#upgrade_your_project_to_a_new_toolbox_version).
6. If your Project was made before 7.1, bring it to 7.1 by hand first, then upgrade it as in
   step 5: in `CHANGES.md`, at the top of the download, read the "To update" part of every
   version newer than yours, up to 7.1's: the newest comes first, so start at your version's
   next and read up the page. From 4.x to 6.0, that is 5.0's "To update from 4.x", then 6.0's
   "To update from 5.x". Each says what to change in your notebooks and files. A Project 7.0
   made looks like one 7.1 made to `project.upgrade()`, so do 7.1's "To update from 7.0" first.

When it is imported, the folder checks itself against its `version.txt`, the one file that
names its version and lists each of its files. If a file is missing or extra, if `version.txt`
is missing or unreadable, or if this Python or the library it needs won't work with it, the
import stops and says what happened, why it matters and the usual fix. A file that differs from
the download, edited by hand or pasted from another download, only warns, naming it.

## License

The Toolbox, its Example projects and its Templates are under the MIT No Attribution license,
in `LICENSE`: use them, change them, share them or sell them, at work or anywhere else, with
no need to say where they came from, so you needn't copy `LICENSE` along with the folder.
They come as they are, with no warranty.

## Cheat sheet

Everything the Toolbox offers, one line each, grouped by the file of `sqlglot_composer` it
lives in. Import every name from `sqlglot_composer` itself, never from a file inside it.
Arithmetic isn't in it: a calculation uses Python's own `+ - * /` on columns, as in
`job_runs.duration_mins / 60`. The star import brings the 109 names listed here before the admin
module. Two modules' functions come last: the admin module's, which change your own Saved
tables, and the project module's, which make and archive a Project's folders and files. The star
import leaves both out, so import each by name, as `from sqlglot_composer import admin, project`,
and call `admin.drop_table(t)` or `project.new_table("mart.daily_job_runs")`.

<!-- CHEAT SHEET -->
