# sqlglot Composer

This is version <!-- VERSION -->.

Write Hive SQL as Python. You put clause functions (`SELECT`, `FROM`, `WHERE`, ...) together in
SQL order, and the Toolbox writes the Hive string. **It refuses a Statement that would silently
give a wrong number, or read or return too much, and says what to change.**

### How to read this page

- Steps 1 to 9 are a tutorial in nine steps, one story through one Project: you start it, add
  your tables' Table references, build Statements on them, share Building blocks, save tables
  of your own, follow their Lineage, keep the Project in order, and convert someone else's Hive
  into your own code. Do them in order: each closes with what to check before the next.
- Each step is a short summary of the Getting started how-to of the same name, which walks
  through it in full on `sqlglot_composer/how_to.html`, a page in the download to open in your
  browser.
- Every example here runs on the Example database, so you can follow the page before you
  connect your own warehouse.
- The Starter Example project shows a Project much like the one the story leaves, filled in.
- The sections after step 9 are reference: the Workflows, the how-tos, the Example gallery, the
  Example projects, the Templates, Copilot, updating, the license and the cheat sheet.
- What changed in each version, and how to update from it, is in `CHANGES.md`.

### Terms

Each word below is the Toolbox's own; the steps define the rest where they first use them.

- **Toolbox**: the one folder, `sqlglot_composer`, whose Python functions write Hive. You copy
  it into each Project.
- **Warehouse**: where your tables are and your Hive runs at work. The Toolbox reaches it only
  through two functions of yours, `query` and `execute`, in `warehouse.py`.
- **Example database**: nine made-up tables that ship inside the Toolbox and stand in for your
  warehouse in every example.
- **Statement**: one query, built from clause functions, that the Toolbox checks and writes as
  one Hive string.
- **Project**: your folder at work holding the Toolbox and your own files in one fixed layout.
- **Project action**: a call of the `project` module, such as `project.start()`, that makes or
  changes a Project's files, never the warehouse, and is logged in the Admin log.
- **Workflow**: the steps of one job of a Project, from what you start with to its end goal: a
  notebook in `admin/workflows/`. Fill in its names cell and save it, and `project.check()`
  names its next step, while `project.do_next()` runs each step that only writes files, such
  as making a Table folder, and stops at the first that calls the warehouse or needs your
  decision. The Workflows section below draws each one.
- **Decision**: one thing about one table that only you decide, such as its folder: you answer
  it in a Workflow's decisions cell, and a step writes your answer in.
- **Dev Database** and **Prod Database**: the database where you create and write your own
  tables first, and the one others read your finished tables from. You name both in
  `admin/databases.py`.

## 1. Start a Project

Goal: a Project folder laid out by the Toolbox, its warehouse.py connected.

The Toolbox needs Python 3.11 or newer, pandas, numpy and sqlglot, and is tested on Python 3.13,
which `requirements.txt`'s pins are for, as they are for 3.12. It is one folder,
`sqlglot_composer`. The Toolbox works with any sqlglot from 30.19.0 up to (not including) 31.

1. **Get the download.** Goal: the Toolbox on your computer. Action: download this branch as a
   zip and extract it. Done when the extracted folder holds `sqlglot_composer` and
   `requirements.txt`; then step 2.
2. **Install what the Toolbox needs.** Goal: its libraries, at the versions it is tested on.
   Action: change `requirements.txt` by the rules below, then run
   `pip install -r requirements.txt` in the download's top folder, or, from a notebook,
   `%pip install -r` followed by the path to that file. Done when pip finishes with no error;
   then step 3.
   - If you are on Python 3.11, change numpy's line in `requirements.txt` to `numpy==2.4.6`,
     which pandas 3.0.6 runs on there, before you run pip: numpy 2.5.4 can't install on 3.11.
   - If your notebook already has a package, such as pandas, delete its line, so pip keeps
     the one you have.
   - If your notebook's sqlglot is in the range above, delete sqlglot's line too. If it is
     not, keep the line, so pip installs the one the Toolbox is tested on.
     `import sqlglot; print(sqlglot.__version__)` in a notebook shows which you have.
3. **Make the Project's folder.** Goal: a folder holding the Toolbox. Action: make an empty
   folder for your Project, wherever you keep your work, such as `team_project` in your
   documents, and copy the whole `sqlglot_composer` folder into it. Any folder name will do,
   and the download's folder can stay where it is. Keep your own files beside the
   Toolbox, never inside it. Done when your folder holds `sqlglot_composer` alone; then step 4.
4. **Lay the folder out.** Goal: every folder and file a Project starts with. Action: open a
   notebook in the Project's folder, such as start.ipynb, and run `project.start()`, as below.
   Done when it prints "Started a Project in the folder you're working in"; then step 5.

```python
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py.
Next: set conn, your connection, in warehouse.py.
```

5. **Connect your warehouse.** Goal: the Toolbox's Hive reaching your tables. Action:
   `project.start()` set `conn` to the Example database; at work, set it to yours, once, in
   `warehouse.py`, as below. Done when `conn` in `warehouse.py` is your connection, or is still
   the Example database while you follow this page; then go on to section 2, "Add your
   tables' references".

```python
import my_api  # your team's library

# Your connection: its query(sql) gives back a DataFrame, its execute(sql) runs a change.
conn = my_api.connect()
```

If your team keeps its connection in a file outside the Project, such as a file
team_connection.py, then write these lines in `warehouse.py`, in place of
`conn = example_database`: they put that file's folder on Python's path, then import it.

```python
import sys

sys.path.append("C:/work/connections")  # the folder team_connection.py is in
from team_connection import conn
```

Two rules hold for every call on this page:

- Import every name from `sqlglot_composer`, at its top level, never from a file inside it.
- Each Project action, such as `project.start()`, returns its report, which a notebook shows
  under the cell. From a plain Python script, run `print(project.start())` to see it.

### Your query and execute

- The Toolbox never connects to anything itself: it writes Hive as text, and hands that text
  to one of two functions in `warehouse.py`, which pass it to your connection, `conn`.
- `query` runs Hive that gives back rows, such as a SELECT, and gives them back as a pandas
  DataFrame.
- `execute` runs Hive that changes something, such as a write, and gives back nothing.
- You pick which one sends a Statement, by calling `run_query(s, query)` or
  `run_execute(s, execute)`.

### Every file of a Project

You make three things by hand: the Project's folder, the copied `sqlglot_composer` folder and
the notebook you run `project.start()` from. A Project action makes every other file, so make
each with its call of the `project` module, not by hand in your file explorer: each is logged
in the Admin log, and the registry lists what it made, so `project.check()` can tell what is
missing or made by hand. Each line below names a path, what makes it, and what you fill in.

- **Made by you:**
  - your Project's folder, such as my_project: made by you, in your file explorer; you fill
    in nothing.
  - `sqlglot_composer/`: copied in by you from the download; you fill in nothing: never edit a
    file inside it.
  - `sqlglot_composer/version.txt`, the Toolbox's version and its list of files: from the
    download; you fill in nothing: the import checks the folder against it.
  - `start.ipynb`, or any name you like, the notebook you run `project.start()` from: made by
    you, in Jupyter; you fill in nothing: keep it for trying things out, or delete it.
- **At the Project's top:**
  - `warehouse.py`: made by `project.start()`; you fill in `conn`, your connection.
- **In admin/:**
  - `admin/`, a notebook for each job on the whole Project, such as check_project.ipynb,
    run_tables.ipynb and remove.ipynb: made by `project.start()`; you fill in the names some
    ask for in their names cell, such as the tables to remove.
  - `admin/workflows/`, a folder per Workflow, such as new_table/ and convert/, each holding
    its notebook: made by `project.start()`; you fill in what the Workflow works on, in its
    notebook's names cell, such as the tables, then save it. Then run each step's cell in turn,
    or `project.do_next()`, which runs the steps it can for you, those that change only files,
    up to the first it can't; `project.check()` names the next step.
  - `admin/databases.py`, the names of your Dev Database and Prod Database: made by
    `project.start()`; you fill in `DEV` and `PROD`.
  - `admin/sent.csv`, a row for each change a notebook of the Project sends to the warehouse:
    made by `project.start()`, then each `run_execute` and `project.run_tables`; you fill in
    nothing.
  - `admin/admin_log.md`, the Admin log: made by `project.start()`, then each Project action
    adds an entry; you fill in nothing.
  - `admin/project_version.txt`, the Toolbox version that last wrote the Project: made by
    `project.start()`, then `project.upgrade()`; you fill in nothing.
  - `admin/workflows/convert/<name>/`, a Conversion folder per batch of someone else's Hive you
    convert: its scripts as given, and what each statement became. Made by
    `project.convert(...)`, from `admin/workflows/convert/convert.ipynb`, as
    [Convert someone else's Hive](../sqlglot_composer/how_to.html#convert_someone_elses_hive)
    shows; it makes each table the Hive writes a Saved table in your Dev Database. You fill in
    each table's Decisions, in the notebook's decisions cell.
  - an Upgrade's checklist in admin/, named for the version it upgraded to, such as
    upgrade_7.3.md: what it did and a box for each change it left you. Made by
    `project.upgrade()`; you make the changes it lists, each marked `# UPGRADE <version>:` at
    its line.
  - `admin/registry.csv`, the registry: made by `project.start()`, then each Project action
    that makes or archives a Table folder, a Table reference, a Building block or a Conversion
    folder adds a row; you fill in nothing.
  - `admin/templates/`, the Templates: made by `project.start()`; you fill in nothing, unless
    you want your team's own shape.
  - admin/removed/, what you archive: made by `project.remove_table(...)`,
    `project.remove_reference(...)`, `project.remove_block(...)` and
    `project.remove_conversion(...)`, and by `project.upgrade()` and
    `project.convert(..., overwrite=True)`, which keep each file as it was before they change
    it; you fill in nothing.
- **In references/:**
  - `references/<db>__<table>.py`, a Table reference per table: made by
    `project.add_references([...], query=query)` for a table in the warehouse, or by
    `project.new_table(...)` for a Saved table of your own; you fill in its TODO lines, and
    your own Aliases.
  - `references/<db>.py`, a Database module per Database, such as `references/ops.py`: made by
    each Project action that adds or archives a Table reference; you fill in nothing: never
    edit it.
  - `references/reference_sheet.csv`, the Reference sheet: made by
    `project.refresh_reference_sheet()`; you fill in nothing.
- **In building_blocks/:**
  - `building_blocks/<name>.py`, a Building block: made by `project.new_block("<name>")`; you
    fill in its `<...>` and TODO lines.
- **In tables/:**
  - `tables/<db>__<table>/<db>__<table>.ipynb`, a Table notebook per Saved table: made by
    `project.new_table("<db>.<table>")`; you fill in its `<...>` lines.
  - `tables/<db>__<table>/lineage/`, the table's Lineage: made by its notebook's lineage cell;
    you fill in nothing.
  - `tables/<db>__<table>/<db>__<table>.hql`, the Hive the table's logic sends, to read at a
    glance and to commit: written by its notebook's Hive cell, `export_hive()`, again each time
    it runs. It is generated, so never edit it: edit the notebook's logic, save the notebook,
    and run its `export_hive()` cell again.
- **Anywhere else:**
  - a `.hql` file of Hive you write or are given, such as `daily.hql`: your input, not
    generated. Saved by you, in `admin/workflows/convert/` for the convert Workflow's `FILES`,
    or in `admin/workflows/new_table/` for the new_table Workflow's `QUERIES`; you write all of
    it: it is yours, and nothing writes over it.
  - `lineage/`, beside the notebook you run it from, the Lineage of a Statement exported outside
    a Table notebook: made by `export_lineage(...)`; you fill in nothing.

How-to: [Start a Project](../sqlglot_composer/how_to.html#start_a_project), with what to do when
your API gives rows without their column names, and the lines a notebook deeper in the Project
starts with.

Before you go on, check:

- `project.start()` printed "Started a Project", and the folder holds admin/, references/,
  building_blocks/, tables/ and warehouse.py beside `sqlglot_composer`.
- `conn` in `warehouse.py` is the connection you mean to use.

## 2. Add your tables' references

Goal: a Table reference for each table your Statements read.

A Statement reads a table through its **Table reference**: a small file in `references/` holding
the table's columns and their types, its **Partitions** (the columns it is stored by, such as a
day or a region) and its **Key** (the columns that name one row), where it has them. Each
**Database**, the first part of a table's name (`ops` in `ops.jobs`), has a **Database module**,
such as `references/ops.py`, that gives each of its tables at a dot. The references Workflow,
`admin/workflows/references/references.ipynb`, takes you through it.

1. **Name the tables.** Goal: the Workflow knows which tables to read. Action: name the tables
   in the references Workflow's names cell, and save the notebook. Done when the names cell
   lists each table you read; then step 2.
2. **Write their files.** Goal: a Table reference per table. Action: run its first step,
   `project.add_references`, which asks each table for its columns, through your query, and
   writes its file, and the Database module of its Database, as below. Done when it names each
   file it wrote; then step 3.

```python
>>> from warehouse import query, execute
>>> project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"], query=query)
Wrote references/ops__jobs.py, references/ops__job_runs.py and references/ops__run_alerts.py: fill in their TODO lines.
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs and ops.run_alerts.
Restart the kernel of a notebook that imported references, to see a table added since.
```

3. **Fill in what the table can't say.** Goal: each file complete. Action: fill in each file's
   TODO lines: what one row is, its Key, and which columns don't add up, such as averages.
   Below it, you may add **Aliases**, your own names for its columns and conditions. Done when
   no TODO line is left. A `does_not_add_up=` line is filled in by naming its columns, or, when
   no column is one, by deleting its TODO; then step 4.
4. **Import the Database.** Goal: every table of the Database from one import. Action: run
   `from references import ops`; each column is at a dot after its table, as below. Done when
   `ops.job_runs.status` shows `job_runs.status`; then step 5.

```python
>>> from references import ops
>>> ops.job_runs.status  # -> Column
job_runs.status
```

5. **Check each file.** Goal: each file true to its table. Action: run
   `check_table_reference(ops.job_runs, query=query)`, which checks the file against its table,
   and `check_key`, which checks the Key you wrote. If the table is partitioned, then give
   `check_key` one Partition to check with `where=`, such as `check_key(ops.job_runs,
   query=query, where=equals(ops.job_runs.dt, "2026-09-24"))`; `query("SHOW PARTITIONS
   ops.job_runs")` lists the Partitions it holds. `admin/check_references.ipynb` runs both
   checks on every table, each partitioned one on its latest Partition. Done when each check's
   `ok` is true; then go on to section 3, "Build and run a first statement".

How-to: [Add your tables' references](../sqlglot_composer/how_to.html#add_your_tables_references).

Before you go on, check:

- `references/` holds a file for each table you read, with no TODO line left, and a Database
  module for each Database.
- `from references import ops` gives each table at a dot, and each column at a dot after it.

## 3. Build and run a first statement

Goal: one Statement built, its Hive read, and its rows back in pandas.

A Statement is built along a chain of types, each made by a call on the one before:

- `ops.jobs`, a Table reference, gives a `Table`: a table, its columns, its Partitions and its
  Key.
- `ops.jobs.job_id` gives a `Column`: one of its columns.
- a test, such as `equals(...)`, gives a `Condition`: a test of each row, for WHERE or ON.
- `SELECT(...)`, `FROM(...)`, `WHERE(...)` and the others give a `Clause`: one part of a query.
- `statement(...)` gives a `Statement`: its Clauses, checked together as one query.
- `to_hive(...)` gives a `str`: the Hive, the query's text, ready to paste.
- `run_query(..., query)` gives a `DataFrame`: the rows your query gives back, in pandas.

The example finds the runs that failed on 2026-09-23 and 2026-09-24. ops.job_runs is
partitioned by dt, so a Statement on it must filter dt.

1. **Build the Statement.** Goal: the failed runs as one query. Action: give `statement(...)`
   its Clause functions in SQL order, `SELECT`, `FROM`, then `WHERE` with a test of status and
   of dt. Done when `statement(...)` gives back a Statement; then step 2.
2. **Read its Hive.** Goal: the query's text. Action: run `print(to_hive(failed))`. Done when
   it prints the SELECT below; then step 3.
3. **Run it.** Goal: its rows. Action: run `run_query(failed, query)`. Done when it gives back
   the two runs below; then step 4.

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

4. **Run a Worked example.** Goal: any function's example in your own notebook. Action: find
   it, `help(to_hive)` shows the one for `to_hive`, then run the lines below first and paste
   the example after them. Done when the example shows the rows its docstring shows; then go
   on to section 4, "Count, join and stay safe".

```python
from sqlglot_composer import *
jobs, job_runs = example_database.jobs, example_database.job_runs
```

What the Worked examples hold:

- Every function and class in the cheat sheet has a Worked example in its docstring.
- The examples use every Toolbox name and the Example database's `jobs` and `job_runs`: its own
  Table references of `ops.jobs` and `ops.job_runs`, the same tables as your Project's
  `ops.jobs` and `ops.job_runs`, which ship inside the Toolbox so an example runs with no
  Project.
- The examples take today as 2026-09-25, the day after the Example database's last day.
- If a pasted example uses `last_n_days(...)`, which counts back from your own today, write
  `between(...)` with the days the example's Hive shows in its place, such as
  `between(job_runs.dt, "2026-09-23", "2026-09-24")`, to get the rows it shows.

How-to: [Build and run a first statement](../sqlglot_composer/how_to.html#build_and_run_a_first_statement),
with every Condition `WHERE` takes, `AS`, `all_columns` and `first_look`.

Before you go on, check:

- `print(to_hive(failed))` prints a WHERE that filters dt.
- `run_query(failed, query)` gives back runs 97 and 102.

## 4. Count, join and stay safe

Goal: numbers per group, other tables joined in, and each refusal read.

1. **Count per group.** Goal: each job's runs and failed runs. Action: give `GROUP_BY` the
   column to group by, which makes one row per group, and let `count_rows` and `sum_of` work
   out its numbers, as below. Done when it gives back one row per job; then step 2.

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

2. **Join another table.** Goal: its columns beside yours. Action: add `JOIN` or `LEFT_JOIN`,
   which brings in another table, matched on its Key. Done when the Statement builds; then
   step 3.
3. **Read each refusal.** Goal: a Statement that gives the right number. Action: as you build a
   Statement, the Toolbox checks it three ways, below; follow the message of any check that
   stops it. Done when the Statement builds, each Warning read; then go on to section 5,
   "Share Building blocks".

The three checks:

- A **Guard** refuses a Statement that would silently give a wrong number, such as a join that
  counts a row twice.
- A **Warning** lets one through but says why a number may come out wrong.
- A **Load limit** refuses one that would cost the cluster or your notebook too much, such as a
  read that filters none of a table's partition columns.

Each message says what happened, why it matters, the usual fix and the opt-out, a keyword for
when you truly mean it:

- If the usual fix gives what you want, make it.
- If you truly mean what it refused, pass its opt-out.

How-to: [Count, join and stay safe](../sqlglot_composer/how_to.html#count_join_and_stay_safe),
with `HAVING`, the top N, Derived tables, the rows with no match, and when each opt-out is
right.

Before you go on, check:

- `run_query(per_job, query)` gives one row per job, with runs and failed_runs.
- For each refusal you met, you can name its check, Guard or Load limit, and its usual fix.

## 5. Share Building blocks

Goal: a piece several Statements need, written once.

A **Derived table** is a Statement given a name with `derived`, which another Statement reads
like a table. Wrapped in a function, kept in a file of its own in `building_blocks/`, it is a
**Building block**, which every notebook of the Project imports.

1. **Make its file.** Goal: the Building block's file. Action: run `project.new_block`, which
   makes its file from the Project's `building_block` Template, as below. Done when it names the
   file it wrote; then step 2.

```python
>>> project.new_block("runs_per_job")
Wrote building_blocks/runs_per_job.py, from admin/templates/building_block.py:
fill in its <...> and TODO lines.
```

2. **Fill it in.** Goal: the piece's logic. Action: fill in its `<...>` and TODO lines. The
   Starter Example project's `building_blocks/runs_per_job.py` is this file filled in: each
   job's runs, failed runs and minutes, for the rows a Condition it is given picks. Done when
   no `<...>` or TODO line is left; then go on to section 6, "Save a table".

How-to: [Share Building blocks](../sqlglot_composer/how_to.html#share_building_blocks).

Before you go on, check:

- `building_blocks/runs_per_job.py` holds no `<...>` or TODO line.

## 6. Save a table

Goal: a table of yours written in dev, read by everyone after.

A **Saved table** is a table of yours that a Statement writes, so a number worked out once is
read by everyone after. Each has a **Table folder** in tables/, holding its **Table notebook**,
whose cells create, preview and write it. The new_table Workflow,
`admin/workflows/new_table/new_table.ipynb`, takes you from its name to the table written in
dev.

1. **Add what it reads.** Goal: a Table reference for each table the new table reads, from its
   query or from logic you write. Action: add them with the references Workflow,
   `admin/workflows/references/references.ipynb`, before you run the new_table Workflow. Done
   when each has its file in `references/`; then step 2.
2. **Name the table.** Goal: the Workflow knows what to make. Action: name the table in the
   new_table Workflow's names cell, by the rules below, and save the notebook. Done when the
   names cell holds it; then step 3.
   - If you have its query already, give it in the names cell's
     `QUERIES = {"alerts_per_severity": "alerts_per_severity.hql"}`, the table named in your Dev
     Database: its logic is written for you from the query, then compared with it.
   - If you have no query, you write its logic in step 4.
3. **Make its Table folder.** Goal: the table's notebook and a stand-in Table reference.
   Action: run its first step, `project.new_table`, which makes its Table folder, holding a
   Table notebook made from the `saved_table` Template, and a Table reference that stands in
   until a later step writes it, as below. Done when it names the folder it made; then step 4.

```python
>>> project.new_table("mart.alerts_per_severity")
Made tables/mart__alerts_per_severity/: mart__alerts_per_severity.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__alerts_per_severity.py: project.reference_from_logic writes it.
```

4. **Write its logic.** Goal: what the table holds. Action: in the notebook's logic, set
   `READS`, the rows its write reads, and define `create()`, `rows()`, `preview()` and
   `write()`, each giving a Statement and running nothing. Save the notebook. Done when
   `preview()` gives the rows you expect; then step 5.
5. **Write its Table reference.** Goal: the stand-in replaced. Action: run the step
   `project.reference_from_logic`, which writes it from the logic you wrote: its columns and
   types from `preview()`, its partition columns from the logic's `PARTITIONED_BY`, and its
   Key. Done when its file in `references/` lists those columns; then step 6.
6. **Write it.** Goal: its rows in the warehouse. Action: run
   `project.run_tables(execute=execute)`, which writes every Saved table, each after the tables
   it reads, sending the Session setting below first. With no execute, it prints each write's
   Hive in order and sends nothing. Done when it has sent each write; then step 7.
7. **Write its Hive file.** Goal: the table's Hive to read at a glance. Action: run its
   notebook's Hive cell, `export_hive()`, which writes it into `<db>__<table>.hql` beside the
   notebook: `create()`, then `write()`, in the order they are sent. Done when the file is
   there; then go on to section 7, "Follow lineage".

How a write works:

- `write()` gives an `INSERT_OVERWRITE`, which replaces whatever the Partitions its rows fill
  held, or the whole table when it has none, so sending it twice leaves the same rows, not
  twice as many.
- A write that fills its Partitions from its rows needs the **Session setting**
  "dynamic_partitions", which `show_hive` prints ahead of it.
- The Python stays the table's definition, so the `.hql` file is generated, to read and to
  commit, never edited.

To change a table's Hive file:

1. **Edit the logic.** Action: edit the logic cell of the Table notebook, such as
   `tables/mart__alerts_per_severity/mart__alerts_per_severity.ipynb`. Done when it holds your
   change; then step 2.
2. **Save the notebook.** Action: save it, since `export_hive()` reads it as last saved. Done
   when it is saved; then step 3.
3. **Write the file again.** Action: run its `export_hive()` cell, which writes
   `mart__alerts_per_severity.hql` again. Done when the file shows your change.

Which `.hql` file is which:

- If `export_hive()` wrote it, it is in the Table folder, generated: read it and commit it.
- If you wrote it yourself or were given it, such as `alerts_per_severity.hql` above, it is
  yours: save it in `admin/workflows/new_table/` for the new_table Workflow's `QUERIES`, or in
  `admin/workflows/convert/` for the convert Workflow's `FILES`, never in a Table folder.

How-to: [Save a table](../sqlglot_composer/how_to.html#save_a_table), with the Starter Example
project's `mart.alerts_per_severity` notebook filled in beside its Table reference.

Before you go on, check:

- `tables/mart__alerts_per_severity/` holds its notebook, `lineage/` and, once its Hive cell has
  run, its `.hql` file.
- Its Table reference lists the columns `preview()` gives.

## 7. Follow lineage

Goal: each output column followed back to the table columns it reads.

1. **Export the Lineage.** Goal: the Lineage of a Statement: an HTML page and a Markdown twin
   that follow each output column back to the table columns it reads, and list every condition
   that decides which rows count. Action: run `export_lineage(...)`; from a Table notebook, run
   its lineage cell, which writes them into its Table folder's `lineage/`, named by the time
   and the table, so each export joins the table's history. Done when the new pages are in
   `lineage/`; then step 2.
2. **Follow it past what it reads.** Goal: Lineage that goes back to where the rows start.
   Action: by the rules below. Done when the HTML page traces each output column to a table
   column; then go on to section 8, "Keep the Project in order".
   - If the table reads another Saved table, pass that table's write too, from
     `project.load("mart.daily_job_runs").write()`, so its Lineage goes on back to the tables
     they start from.
   - If a change is made in pandas, declare it with `python_step`, a **Python step**, so the
     Lineage doesn't stop at it.

How-to: [Follow lineage](../sqlglot_composer/how_to.html#follow_lineage).

Before you go on, check:

- The table's `lineage/` holds the HTML page and its Markdown twin from your last export.

## 8. Keep the Project in order

Goal: every file the registry lists is there, and every file there is registered.

1. **Check the Project.** Goal: what is missing or made by hand. Action: run `project.check()`,
   which compares the registry with the Project's files, and changes nothing. Done when it
   prints the line below; then step 2.
   - If it names a file made by hand, run the `project.register(...)` call it gives, which
     adopts it.
   - It also names any file deleted by hand.

```python
>>> project.check()
Every Table folder, Table reference and Building block is registered, and each one registered is there.
```

2. **Refresh the Reference sheet.** Goal: every column of every table in one CSV file, the
   Reference sheet. Action: run `project.refresh_reference_sheet()`. Done when
   references/reference_sheet.csv lists them; then step 3.
3. **Check the Table references.** Goal: each Table reference true to its table. Action: run
   `admin/check_references.ipynb`, which checks each against its table. Done when it finds
   nothing wrong; then step 4.
4. **Archive what you no longer need.** Action: run `project.remove_table(...)`,
   `project.remove_reference(...)` or `project.remove_block(...)`, which archive it in
   admin/removed/, deleting nothing. Done when `project.check()` prints the line above again;
   then go on to section 9, "Convert someone else's Hive".

How a Project stays in order:

- Your files sit in three **Levels**, each importing only from the Toolbox and the Levels below
  it: the Table references and `warehouse.py`, then the Building blocks, then each Table
  notebook's logic.
- `project.check()` also names the next step of each Workflow you have started, and
  `project.do_next()` runs the steps it can for you, up to the first it can't.

How-to: [Keep the Project in order](../sqlglot_composer/how_to.html#keep_the_project_in_order).

Before you go on, check:

- `project.check()` prints that every Table folder, Table reference and Building block is
  registered.

## 9. Convert someone else's Hive

Goal: Hive someone else wrote, one query or a folder of scripts, as your own code, each table
it writes a Saved table in dev, then in prod.

The convert Workflow, `admin/workflows/convert/convert.ipynb`, makes a **Conversion** of a
**batch**, one or more scripts converted together. The scripts' order doesn't matter: a FROM
with several INSERTs and an INSERT that reads its own table each come out as Saved tables, and
a temporary table another statement reads, a **staging table**, is folded into the tables that
read it. A **Script tag**, a `<PARM="NAME"/>` the program that ran the scripts filled in before
Hive read it, such as `WHERE dt <= <PARM="PERIOD_END"/>`, is converted as a value standing
there, and left for you to answer, once for each table it ends up in, since it may stand for a different
value in each.

1. **Save the scripts.** Goal: the Workflow can read them. Action: save them beside it, in
   `admin/workflows/convert/`, where it reads them. Done when each script is there; then
   step 2.
2. **Name the batch.** Goal: the Workflow knows what to convert, and what each table it makes
   is called. Action: name the batch and its scripts in its names cell, `NAME` and `FILES`,
   fill in DEV, your Dev Database, in `admin/databases.py`, and save the notebook. Each table
   the batch makes in dev is named by the rules below; you may give one a name of your own
   in the names cell's `RENAME`. Done when both are filled in; then step 3.
   - If a script writes a table, such as `INSERT OVERWRITE TABLE mart.team_fails`, its copy in
     dev is named for that table, then the original's database: `mart_dev.team_fails_mart`,
     so two databases' tables of one name stay apart in your Dev Database. If you want
     the copy to keep the original's name, give it in `RENAME`, the name alone, without a
     database: `RENAME = {"mart.team_fails": "team_fails"}` makes `mart_dev.team_fails`.
   - If the batch is one file holding a query alone, one that writes no table, its table is
     named for the batch, whatever the file is called: `NAME = "failed_runs"` with
     `FILES = ["from_your_team.hql"]` makes `mart_dev.failed_runs`.
   - If the batch is several files, each holding a query alone is named for its file:
     `sales.hql` makes `mart_dev.sales`.
3. **Convert them.** Goal: a Saved table for each table the scripts write. Action: run its
   first step, below, which makes each table the scripts write a Saved table in your Dev
   Database, with its Table folder, its Table reference and a checklist. Done when it names each
   table it made; then step 4.

```python
project.convert("ops_reports", files=["daily.hql", "weekly.hql"], query=query)
```

4. **Answer each Decision.** Goal: what only you can decide. Action: answer each table's
   Decisions, such as its folder and each Script tag's value, in the notebook's decisions cell,
   and save it: the convert step and `project.check()` print a whole `DECISIONS = {...}` to
   paste there, each answer not given yet shown as `"<FILL IN>"`. Done when each table's
   Decisions are answered; then step 5. Each answer, by the rules below:
   - If a tag stands alone, bare, answer it with the value's own quotes,
     `{"tags": {"PERIOD_END": "'2026-10-31'"}}`; if it stands inside quotes,
     `'<PARM="STATUS"/>'`, with none, `{"tags": {"STATUS": "failed"}}`.
   - If a tag stands for a day that changes each run, answer it with a **Run value**, the
     value a function of yours gives each time the table is written. Write the function in
     your Project, such as `period_end` in building_blocks/run_values.py, which gives the
     latest day a table holds with `latest_partition(job_runs.dt, query)`. Import it at the
     top of the decisions cell and give its name, with no brackets:
     `{"tags": {"PERIOD_END": period_end}}`. The Hive sent holds the day itself, a date as
     `'2026-10-31'`; `show_hive`, in the Table notebook's "Try it" cell, shows it first.
   - If you wrote a Run value's file, register it once: `project.check()` names it as made by
     hand, with the call to run in the `project.register(...)` cell of
     `admin/check_project.ipynb`, `project.register("run_values")`.
   - If several tables share an answer, give it once under `"all_tables"`, and a table's own
     answer overwrites it: `{"all_tables": {"location_root": "/data/team", "tags":
     {"PERIOD_END": period_end}}}` gives each table with no location its own folder under
     `/data/team`, and each table holding PERIOD_END that function.
   - If a table reads itself, its seed copies every Partition of its original unless you
     limit it, by partition column: `{"seed": {"dt": {"from": "2026-01-01"}}}` copies those
     from 2026-01-01 on; a list, `{"region": ["US", "CA"]}`, those values alone. A single
     value, `{"dt": "2026-01-01"}`, means **that value or later**.
   - If an answer was wrong, answer it again, then run the notebook's steps 3, 6 and 7 again:
     write the answers in, write each table, and compare each. Each table is made and seeded
     already, so steps 4 and 5 stay done.
5. **Build each table in dev.** Goal: each table written in dev and compared. Action: run the
   Workflow's next steps: they write your answers in, create each table in dev, seed each whose
   write reads its own table (copy its **original**'s rows in once, the original being the
   table the script writes, so its first write doesn't start from nothing, each Partition or
   those its `"seed"` answer names), write each, and
   compare each with the table it copies, `project.compare_batch`. A partitioned table is
   compared on the latest Partition both tables hold. If you want another Partition compared
   too, once your dev table holds it, then set `PARTITION` in the names cell, such as
   `PARTITION = {"dt": "2026-09-23"}`, and run the compare step again: its
   `conversion/compare.md` keeps each Partition's result. Done when every result of each table
   has passed; then step 6.
6. **Promote them.** Goal: the tables in your Prod Database. Action: run the promote Workflow,
   which carries them to your Prod Database, PROD, `project.promote`, each keeping its name
   unless `rename=` gives it another. Done when each is written in prod.

Dev stays the source: to change a promoted table, change it in dev and promote it again.

How-to: [Convert someone else's Hive](../sqlglot_composer/how_to.html#convert_someone_elses_hive).

Before you go on, check:

- Each table of the batch passed `project.compare_batch` before you promoted it.
- Each change you make to a promoted table is made in dev.

## The Workflows

Each job a Project goes through has a Workflow: a notebook in `admin/workflows/`, whose steps
take you from what you start with to the end goal. What only you can decide of a table, a
Decision such as its folder, you answer in its decisions cell,
`DECISIONS = {"mart_dev.weekly": {"location": "/data/team/mart_dev.db/weekly"}}`, and a step
writes each answer in for you.

**Run a Workflow notebook's cells one at a time, never all at once (Run All), since a step after
a decision would write before you make it.**

1. **Name what it works on.** Action: fill in the names cell, and save the notebook. Done when
   it is saved; then step 2.
2. **Run up to the first decision.** Action: run each step's cell in turn, down to the first
   step that is a decision: the line under its heading says "It is a decision, yours to make".
   Done when you reach it; then step 3.
3. **Make the decision.** Action: make it where that step says, such as the decisions cell for
   each table's open Decisions, or the step's own cell for change_a_saved_table's change, and
   save the notebook. Done when it is saved; then step 4.
4. **Run the rest.** Action: by the rules below. Done when the notebook's last step has run.
   - If you want each step in turn, run each cell after it in turn, and go back to step 3 at
     the next decision.
   - If you want every step left at once, run, in their place, the notebook's last cell,
     `project.run_workflow(...)`, which runs every step left, the calls to the warehouse too,
     up to the first only you can do, and says where it stopped.
   - If you want to see what it would send first, give `run_workflow` `dry_run=True`: it sends
     nothing through your execute and says the Hive each step would send.

`project.check()` names each Workflow's next step, and `project.do_next()` runs only the steps
that write files. Each chart below is drawn from the steps its notebook runs, beside the same
steps as a list. In each chart:

- a plain box is a step that changes only files, or only prints;
- a box with double edges is a call to the warehouse, yours to run;
- a diamond is a decision, yours to make;
- a box with round corners is something a step needs or makes.

### How the Toolbox runs

The path every Statement takes, from a Table reference to the warehouse:

<!-- chart: program_flow -->
```mermaid
flowchart TD
    reference("Table reference: references/db__table.py")
    clauses["Clause functions: SELECT, FROM, WHERE, JOIN_ON and the rest"]
    statement["statement(...): a Statement"]
    guards{"Guards and Load limits check it as it is built"}
    refusal("a refusal: what happened, why, the usual fix, the opt-out")
    hive["to_hive(s) or show_hive(s): its Hive"]
    read[["run_query(s, query): its rows, through warehouse.py"]]
    change[["run_execute(s, execute): a change, through warehouse.py"]]
    conversion["project.convert: someone else's Hive"]
    notebook["a Saved table's notebook: create() and write()"]
    tables[["project.run_tables: each write(), in order"]]
    reference --> clauses --> statement --> guards
    guards -->|"refused"| refusal
    guards --> hive
    hive --> read
    hive --> change
    conversion --> notebook --> statement
    notebook --> tables --> change
```

1. A Table reference describes a table you read or write.

       references/db__table.py

2. Clause functions build a Statement, in the order SQL writes them.

       statement(SELECT(...), FROM(...), WHERE(...))

3. Guards and Load limits check it as it is built; a refusal says what happened, why, the usual
   fix and the opt-out.
4. to_hive or show_hive gives its Hive.

       show_hive(s)

5. run_query sends a read through your query, run_execute a change through your execute, both in
   warehouse.py.

       run_query(s, query)
       run_execute(s, execute)

6. A Saved table's notebook builds its create() and write() the same way; project.convert writes
   one from someone else's Hive, and project.run_tables runs each write() in order.

       project.run_tables(execute=execute)

<!-- /chart -->

### convert

<!-- chart: convert -->
```mermaid
flowchart TD
    s0[["1. Convert the scripts: each table they write a Saved table in dev"]]:::warehouse_call
    s1{"2. Answer each table's open Decisions in the decisions cell"}:::your_decision
    s2["3. Write each answer into its table's Table reference"]:::files_only
    s3[["4. Create each table in dev"]]:::warehouse_call
    s4[["5. Seed each table that reads itself, once, from its original"]]:::warehouse_call
    s5[["6. Write each table in dev"]]:::warehouse_call
    s6[["7. Compare each table with its original"]]:::warehouse_call
    t0("Hive scripts"):::thing
    t1("your Dev Database's name"):::thing
    t2("read access to the sources"):::thing
    t3("a dev Table folder per table the scripts write"):::thing
    t4("a Table reference per table, each Script tag in its TAGS"):::thing
    t5("each answer in the decisions cell"):::thing
    t6("each answer written in"):::thing
    t7("each made in dev"):::thing
    t8("each seeded"):::thing
    t9("each written in dev"):::thing
    t10("each compared with its original"):::thing
    t0 --> s0
    t1 --> s0
    t2 --> s0
    s0 --> t3
    s0 --> t4
    t4 --> s1
    s1 --> t5
    t5 --> s2
    s2 --> t6
    t6 --> s3
    s3 --> t7
    t7 --> s4
    s4 --> t8
    t8 --> s5
    s5 --> t9
    t9 --> s6
    s6 --> t10
    classDef files_only fill:#e3f2e1,stroke:#4a8a3f
    classDef warehouse_call fill:#e1ecf7,stroke:#3f6a9a
    classDef your_decision fill:#fbf1d6,stroke:#a8842a
    classDef thing fill:#ffffff,stroke:#888888
```

1. Convert the scripts: each table they write a Saved table in dev (it is a call to the
   warehouse, yours to run).

       project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                       rename=RENAME, staging=STAGING)

2. Answer each table's open Decisions in the decisions cell (it is a decision, yours to make).
3. Write each answer into its table's Table reference (it changes only files, so
   project.do_next() runs it for you).

       project.write_decisions(DECISIONS, tables=project.batch_tables(NAME))

4. Create each table in dev (it is a call to the warehouse, yours to run).

       for table in project.batch_tables(NAME):
           run_execute(project.load(table).create(), execute)

5. Seed each table that reads itself, once, from its original (it is a call to the warehouse,
   yours to run).

       to_seed = project.batch_tables(NAME, seeded=True)
       if not to_seed:
           print("Seeded nothing: no table of the batch reads itself.")
       else:
           run_execute(hive_settings("dynamic_partitions"), execute)
           for table in to_seed:
               run_execute(project.load(table).seed(), execute)

6. Write each table in dev (it is a call to the warehouse, yours to run).

       project.run_tables(tables=project.batch_tables(NAME), execute=execute)

7. Compare each table with its original (it is a call to the warehouse, yours to run).

       project.compare_batch(NAME, query=query, partition=PARTITION)

<!-- /chart -->

### promote

<!-- chart: promote -->
```mermaid
flowchart TD
    s0["1. Promote each table: a prod copy of its folder and Table reference"]:::files_only
    s1{"2. Answer each prod table's open Decisions in the decisions cell"}:::your_decision
    s2["3. Write each answer into its prod table's Table reference"]:::files_only
    s3[["4. Create each table in prod"]]:::warehouse_call
    s4[["5. Seed each prod table that reads itself, once, from its original"]]:::warehouse_call
    s5[["6. Write each table in prod"]]:::warehouse_call
    s6["7. Refresh the Reference sheet and the Database modules"]:::files_only
    t0("dev Table folders, each Decision made and compared"):::thing
    t1("your Prod Database's name"):::thing
    t2("prod Table folders"):::thing
    t3("prod Table references"):::thing
    t4("each answer in the decisions cell"):::thing
    t5("each with its location="):::thing
    t6("each made in prod"):::thing
    t7("each seeded in prod"):::thing
    t8("each written in prod"):::thing
    t9("each in the Reference sheet"):::thing
    t0 --> s0
    t1 --> s0
    s0 --> t2
    s0 --> t3
    t3 --> s1
    s1 --> t4
    t4 --> s2
    s2 --> t5
    t5 --> s3
    s3 --> t6
    t6 --> s4
    s4 --> t7
    t7 --> s5
    s5 --> t8
    t8 --> s6
    s6 --> t9
    classDef files_only fill:#e3f2e1,stroke:#4a8a3f
    classDef warehouse_call fill:#e1ecf7,stroke:#3f6a9a
    classDef your_decision fill:#fbf1d6,stroke:#a8842a
    classDef thing fill:#ffffff,stroke:#888888
```

1. Promote each table: a prod copy of its folder and Table reference (it changes only files, so
   project.do_next() runs it for you).

       project.promote(TABLES)

2. Answer each prod table's open Decisions in the decisions cell (it is a decision, yours to
   make).
3. Write each answer into its prod table's Table reference (it changes only files, so
   project.do_next() runs it for you).

       project.write_decisions(DECISIONS, tables=project.promoted_tables(TABLES))

4. Create each table in prod (it is a call to the warehouse, yours to run).

       for table in project.promoted_tables(TABLES):
           run_execute(project.load(table).create(), execute)

5. Seed each prod table that reads itself, once, from its original (it is a call to the
   warehouse, yours to run).

       to_seed = project.promoted_tables(TABLES, seeded=True)
       if not to_seed:
           print("Seeded nothing: no prod copy reads itself.")
       else:
           run_execute(hive_settings("dynamic_partitions"), execute)
           for table in to_seed:
               run_execute(project.load(table).seed(), execute)

6. Write each table in prod (it is a call to the warehouse, yours to run).

       project.run_tables(tables=project.promoted_tables(TABLES), execute=execute)

7. Refresh the Reference sheet and the Database modules (it changes only files, so
   project.do_next() runs it for you).

       project.refresh_reference_sheet(project.promoted_tables(TABLES))

<!-- /chart -->

### new_table

<!-- chart: new_table -->
```mermaid
flowchart TD
    s0["1. Make each Table folder, converting each table's query QUERIES gives"]:::files_only
    s1{"2. Write each table's logic in its Table notebook, and save it"}:::your_decision
    s2["3. Write each Table reference from its logic"]:::files_only
    s3{"4. Answer each table's open Decisions in the decisions cell"}:::your_decision
    s4["5. Write each answer into its table's Table reference"]:::files_only
    s5[["6. Check each table's rows with preview(), which writes nothing"]]:::warehouse_call
    s6[["7. Create and write each in dev"]]:::warehouse_call
    s7[["8. Compare each table made from a query with its query"]]:::warehouse_call
    t0("the tables' names"):::thing
    t1("a Table folder"):::thing
    t2("what each table should hold"):::thing
    t3("its logic"):::thing
    t4("its Table reference"):::thing
    t5("each answer in the decisions cell"):::thing
    t6("a dev Table folder whose logic loads"):::thing
    t7("its rows, checked"):::thing
    t8("written in dev"):::thing
    t9("each from a query compared with it"):::thing
    t0 --> s0
    s0 --> t1
    t1 --> s1
    t2 --> s1
    s1 --> t3
    t3 --> s2
    s2 --> t4
    t4 --> s3
    s3 --> t5
    t5 --> s4
    s4 --> t6
    t6 --> s5
    s5 --> t7
    t7 --> s6
    t4 --> s6
    s6 --> t8
    t8 --> s7
    s7 --> t9
    classDef files_only fill:#e3f2e1,stroke:#4a8a3f
    classDef warehouse_call fill:#e1ecf7,stroke:#3f6a9a
    classDef your_decision fill:#fbf1d6,stroke:#a8842a
    classDef thing fill:#ffffff,stroke:#888888
```

1. Make each Table folder, converting each table's query QUERIES gives (it changes only files,
   so project.do_next() runs it for you).

       project.new_table(TABLES, queries=QUERIES)

2. Write each table's logic in its Table notebook, and save it (it is a decision, yours to
   make).

       for table in TABLES:
           project.load(table).preview()  # says what stops it, if anything does

3. Write each Table reference from its logic (it changes only files, so project.do_next() runs
   it for you).

       project.reference_from_logic(TABLES)

4. Answer each table's open Decisions in the decisions cell (it is a decision, yours to make).
5. Write each answer into its table's Table reference (it changes only files, so
   project.do_next() runs it for you).

       project.write_decisions(DECISIONS, tables=TABLES)

6. Check each table's rows with preview(), which writes nothing (it is a call to the warehouse,
   yours to run).

       for table in TABLES:
           print(run_query(project.load(table).preview(), query))

7. Create and write each in dev (it is a call to the warehouse, yours to run).

       for table in TABLES:
           run_execute(project.load(table).create(), execute)
       project.run_tables(tables=TABLES, execute=execute)

8. Compare each table made from a query with its query (it is a call to the warehouse, yours to
   run).

       for name in QUERIES:
           print(project.compare_batch(name, query=query))

<!-- /chart -->

### references

<!-- chart: references -->
```mermaid
flowchart TD
    s0[["1. Write the Table references from DESCRIBE"]]:::warehouse_call
    s1{"2. Answer each table's open Decisions in the decisions cell"}:::your_decision
    s2["3. Write each answer into its table's Table reference"]:::files_only
    s3["4. Refresh the Reference sheet and the Database modules"]:::files_only
    t0("table names your query can DESCRIBE"):::thing
    t1("Table references with TODO lines"):::thing
    t2("each answer in the decisions cell"):::thing
    t3("filled-in Table references"):::thing
    t4("the Reference sheet"):::thing
    t5("the Database modules"):::thing
    t0 --> s0
    s0 --> t1
    t1 --> s1
    s1 --> t2
    t2 --> s2
    s2 --> t3
    t3 --> s3
    s3 --> t4
    s3 --> t5
    classDef files_only fill:#e3f2e1,stroke:#4a8a3f
    classDef warehouse_call fill:#e1ecf7,stroke:#3f6a9a
    classDef your_decision fill:#fbf1d6,stroke:#a8842a
    classDef thing fill:#ffffff,stroke:#888888
```

1. Write the Table references from DESCRIBE (it is a call to the warehouse, yours to run).

       project.add_references(TABLES, query=query)

2. Answer each table's open Decisions in the decisions cell (it is a decision, yours to make).
3. Write each answer into its table's Table reference (it changes only files, so
   project.do_next() runs it for you).

       project.write_decisions(DECISIONS, tables=TABLES)

4. Refresh the Reference sheet and the Database modules (it changes only files, so
   project.do_next() runs it for you).

       project.refresh_reference_sheet(TABLES)

<!-- /chart -->

### upgrade

<!-- chart: upgrade -->
```mermaid
flowchart TD
    s0["1. Upgrade the Project's files"]:::files_only
    s1{"2. Make each change an UPGRADE mark asks for, and delete the mark"}:::your_decision
    t0("a Project at an older version"):::thing
    t1("the new Toolbox copied in"):::thing
    t2("the Project at the new version"):::thing
    t3("UPGRADE marks"):::thing
    t4("every UPGRADE mark dealt with"):::thing
    t0 --> s0
    t1 --> s0
    s0 --> t2
    s0 --> t3
    t3 --> s1
    s1 --> t4
    classDef files_only fill:#e3f2e1,stroke:#4a8a3f
    classDef your_decision fill:#fbf1d6,stroke:#a8842a
    classDef thing fill:#ffffff,stroke:#888888
```

1. Upgrade the Project's files (it changes only files, or only prints: run its cell).

       project.upgrade()

2. Make each change an UPGRADE mark asks for, and delete the mark (it is a decision, yours to
   make).
<!-- /chart -->

### change_a_saved_table

<!-- chart: change_a_saved_table -->
```mermaid
flowchart TD
    s0{"1. Write the Admin statement for the change"}:::your_decision
    s1[["2. Print its Hive, and run the check its Check first line names"]]:::warehouse_call
    s2[["3. Send it, then any check after it, such as admin.check_the_copy"]]:::warehouse_call
    t0("a Saved table"):::thing
    t1("the change wanted"):::thing
    t2("an Admin statement"):::thing
    t3("its Hive, read and checked"):::thing
    t4("the change sent"):::thing
    t5("the change logged"):::thing
    t0 --> s0
    t1 --> s0
    s0 --> t2
    t2 --> s1
    s1 --> t3
    t3 --> s2
    s2 --> t4
    s2 --> t5
    classDef warehouse_call fill:#e1ecf7,stroke:#3f6a9a
    classDef your_decision fill:#fbf1d6,stroke:#a8842a
    classDef thing fill:#ffffff,stroke:#888888
```

1. Write the Admin statement for the change (it is a decision, yours to make).

       from sqlglot_composer import between, equals  # where= takes a Condition
       table = project.table_reference(TABLE)
       # such as where=equals(table.dt, "2026-09-24"), or a range of days,
       # where=between(table.dt, "2026-09-01", "2026-09-30"), dt its partition column
       change = admin.drop_partitions(table, where=...)  # or another: help(admin)

2. Print its Hive, and run the check its Check first line names (it is a call to the warehouse,
   yours to run).

       show_hive(change)
       print(query("SHOW PARTITIONS " + TABLE))

3. Send it, then any check after it, such as admin.check_the_copy (it is a call to the
   warehouse, yours to run).

       run_execute(change, execute)

<!-- /chart -->

## The how-tos

Every how-to walks through one job from start to finish, in steps you paste into one notebook,
in order. Each holds:

- its goal;
- its steps, each run on the Example database with what it shows;
- how to check it worked;
- the mistakes people make first.

The how-tos come in two groups:

- Getting started: one story through one Project, a how-to for each of the README's steps: a
  Project, its Table references, Statements, Building blocks, Saved tables, their Lineage, the
  Project's upkeep and a Conversion of someone else's Hive.
- Intermediate: a menu, each starting from the Intermediate Example project: one job each,
  such as rewriting some partitions, rollups, Keys, quality checks and testing. Each says
  which Getting started how-tos it needs.

<!-- HOW-TOS -->

## The Example gallery

The [Example gallery](../sqlglot_composer/examples.html), `sqlglot_composer/examples.html`,
holds every Worked example on one page: its Python and, for each Statement it builds, the Hive
and any result. Open it in your browser.

- It needs nothing else: a box at the top keeps only the examples holding every word you type,
  and Ctrl+F searches it too.
- Besides each docstring's example, it holds the Worked examples that stand on their own: common
  jobs built in steps that each say why, such as building a Saved table or finding rows with no
  match, and Statements that give a wrong number shown beside their fix.
- Each result comes from the Example database or, where that can't run it, is computed in
  pandas.

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
  `mart.run_speed`, from Follow lineage, `ops.scheduler_runs`, from Keep the Project in order,
  and the four Saved tables of the ops_reports batch, from Convert someone else's Hive.
- `intermediate/`, where the Intermediate how-tos start, on `ops.job_events`, `ops.job_owners`,
  `ops.region_costs`, `ops.region_budgets` and `ops.team_notes`: seven Saved tables, among them
  an incremental load, an as-of lookup, a weekly rollup, quality checks from the
  `quality_checks` Template, a table partitioned by region and written a region at a time, one
  with no partitions and no Key, and a finished Conversion, with the Hive it replaced.

To open one:

1. **Copy the Toolbox in.** Action: copy the `sqlglot_composer` folder into the project's
   folder first, as a Project holds it. Done when the folder holds `sqlglot_composer`; then
   step 2.
2. **Open its notebooks.** Action: open them and run their cells. The Example database can be
   read but not written, so a Table notebook prints each write's Hive and runs only what reads
   the ops tables, and `admin/run_tables.ipynb`, with no execute, prints every write in order,
   writers first, and sends nothing (a dry run). Done when its cells have run.

To start a Project of your own, start it with `project.start()` rather than copying one: an
Example project is for reading, and copying it would bring its tables and its Admin log.

## Templates

A Template is the empty shape of one of your notebooks or files, to make a new one from.

- They ship inside the Toolbox, and `project.start()` copies them into your Project's
  `admin/templates`, where they are yours to edit, or to add your own beside.
- `project.new_table("mart.your_table")` makes a Table folder's notebook from the `saved_table`
  Template, and `template=` names another, filling in the table's database and name.
- Every other placeholder, a word in angle brackets such as `<SOURCE_TABLE>`, is yours to
  replace, brackets and all. Python stops at one left in, so a notebook can't run half filled
  in.
- Each Template's first lines list its placeholders, with an example of each.

The Table notebook Templates, each a notebook of the same six code cells around its own logic:

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
plain text that teaches Microsoft Copilot the Toolbox, so you can ask it in plain words for a
Statement, a Table reference, a Table notebook's logic cell or a Conversion, or for a whole
job's steps: `copilot/13_workflows.txt` and `copilot/16_workflows_promote.txt` list convert's
and promote's, and file 14 the other Workflows', from the steps each notebook runs.

1. **Pick the file.** Action: read `copilot/00_start_here.txt`, which says which file fits what
   you want to do. Done when you have its name; then step 2.
2. **Give it to Copilot.** Action: open a new chat, and paste the one file for what you want to
   do as your first message. Done when it is sent; then step 3.
3. **Ask.** Action: ask in plain words, giving the import line and columns of each table to
   read. Done when Copilot answers; then step 4.
4. **Run its answer.** Action: run what Copilot gives you as you would your own code: the
   Toolbox still refuses what would give a wrong number. Done when it runs.

About the files:

- Each file fits the 8,000 characters Copilot takes at once, spaces and line breaks included;
  `copilot/count_characters.py` counts a copy you edit.
- `copilot/all_in_one/all_copilot_files.txt` holds every file in one document, for reading or
  searching them together, not for Copilot: it is many times the 8,000 characters, so in
  Copilot paste or attach the separate files.

The path from a workbook to prod:

<!-- chart: excel -->
```mermaid
flowchart TD
    workbook("a Formula workbook")
    copilot{{"Copilot, given files 15, 11 and 12: the workbook as Hive"}}
    scripts("its Hive, each name in angle brackets filled in, saved as .hql files")
    convert["the convert Workflow: project.convert(NAME, files=FILES), one batch"]
    dev[["each table created, seeded and written in dev"]]
    compare[["project.compare_batch: each against its query"]]
    promote["project.promote: each copied to prod"]
    prod[["each created and written in prod"]]
    workbook --> copilot --> scripts --> convert --> dev --> compare --> promote --> prod
```

1. Fill in a Formula workbook, laid out as copilot/formula_workbook.xlsx is.
2. Give Copilot files 15, 11 and 12 with the workbook: it writes the workbook as Hive, a query
   for each final Table.
3. Fill in each name it writes in angle brackets, save each query as a .hql file named for its
   final Table, and convert them as one batch in the convert Workflow, DEV filled in: each
   becomes a Saved table named for its file, or, when the batch is one file, for the batch.

       project.convert("budget", files=["sales.hql", "regions.hql"], query=query)

4. Answer each table's Decisions, then create, seed and write each in dev, as the Workflow's
   steps say.
5. Compare each with its query, the Hive Copilot wrote.

       project.compare_batch("budget", query=query)

6. Promote them, and create and write each in prod, through the promote Workflow.

       project.promote([...])

<!-- /chart -->

To hand over an Excel workbook's calculations, one chat holds three Copilot files and the workbook:

1. **Fill in a Formula workbook.** Action: copy `copilot/formula_workbook.xlsx` and follow its
   Steps sheet to move the data and formulas in. `copilot/examples/` shows three filled in:
   formulas with a value typed over, a summary Table with a Total Row, and Power Query, whose
   queries you add by hand as its Power Query sheet says. The last sheet of each, Hive, is the
   conversion Copilot should give. Done when your data and formulas are in it; then step 2.
2. **Ask Copilot.** Goal: Copilot sees all of the workbook. Copilot may not see a Power
   Query's M inside an attached workbook; the workbook written as text shows it.
   - If you can run Python: in a terminal in the download's top folder, run
     `python copilot/workbook_text.py "C:/my work/costs.xlsx"`, with your workbook's path in
     quotes. It needs nothing but Python, and writes costs.txt beside the workbook: each
     Table and formula, each Power Query's M, from the workbook or its Power Query sheet, and
     the order each piece reads the others in. If it names a loop instead, it writes nothing:
     break the link it names in Excel, save, and run it again. Attach the .txt below.
   - If you can't: attach the workbook itself below. If it has a Power Query, keep each
     query's M on its Power Query sheet too, as the Steps sheet's step 7 lays it out.

   Action: in a new chat, attach `copilot/15_excel_workbook_steps.txt`,
   `11_excel_formula_workbooks.txt` and `12_excel_power_query.txt` (or paste each as a message
   of its own), then attach the .txt or the workbook, and send "Convert this workbook". Done
   when Copilot answers with a map, a Hive query for each final, and what to do next; then
   step 3.
3. **Check the map.** Action: read the map Copilot answers with: which Tables are sources, the
   samples of your database's tables, and which are finals, the Tables your work ends with,
   each becoming a query. Done when every Table you expected is there; then step 4.
4. **Fill in the names.** Action: each query writes `<...>` for a name it can't know, such as
   `<database>.<sales_data>`. Fill each in with your database's own names: your Project's
   `references/` folder has them, `ops__job_runs.py` for `ops.job_runs`, or ask whoever owns
   the data. Done when no `<...>` is left; then step 5.
5. **Save the queries.** Goal: the convert Workflow can read them. Action: leave out each
   final no one needs kept as a table, such as a Total Row whose total no one needs. Save each
   other filled-in query as a .hql file of its own in `admin/workflows/convert/`, beside
   `convert.ipynb`, named for its final Table, such as `by_job.hql`; a Total Row's query,
   titled `by_job (Total Row)`, as `by_job_total.hql`. Done when each final you keep has its
   file; then step 6.
6. **Convert them.** Goal: a Saved table in dev for each final. Action: in the convert
   notebook's names cell, name the batch and its files, such as `NAME = "sales_summary"` and
   `FILES = ["sales.hql", "regions.hql"]`, with DEV filled in, in `admin/databases.py`, then
   run its steps. Each query becomes a Saved table named for its file; with one file, the
   table is named for the batch, so name the batch for its final Table. A query here writes no
   table of its own, so its compare step checks each Saved table's rows against the rows the
   query gives. Done when each table has passed its compare.

Copilot answers with Hive alone: the Conversion writes the Toolbox code from it, and checks
it.

Before you go on, check:

- Each final you keep has its query saved as a .hql file, with no `<...>` left in it.
- Each table the batch made has passed its compare in the convert notebook.

## Update

Goal: the new Toolbox copied in, and your Project carried to its version.

1. **Note your version.** Action: read `sqlglot_composer.VERSION`, such as
   `'sqlglot Composer 5.1, exported ...'`, or, if the import stops, the first line of
   `sqlglot_composer/version.txt`. Done when you have it written down; then step 2.
2. **Delete the old folder.** Action: delete the `sqlglot_composer` folder, and any
   `composer_core` folder beside it, left over from before 6.0. Done when neither is there;
   then step 3.
3. **Copy in the new one.** Action: from the new download, copy in the whole `sqlglot_composer`
   folder. Done when it is there; then step 4.
4. **Restart the kernel.** Action: restart it, since it still holds the old code. Done when it
   has restarted; then step 5.
5. **Bring your Project to the new version.** Action: by the rules below. Done when
   `project.check()` lists no UPGRADE mark left.
   - If your Project was made by Toolbox 7.1 or newer, upgrade it: run step 1's cell,
     `project.upgrade()`, of `admin/workflows/upgrade/upgrade.ipynb` (`project.start()` writes
     it, and an Upgrade adds it to a Project made before 8.0). If your Project has none, as one
     made before 8.0 hasn't, run `project.upgrade()` from `admin/check_project.ipynb`, which
     imports `project` already. Then work through the boxes in each checklist it writes in
     admin/, one for each version it upgraded through, named for the version, such as
     upgrade_8.4.md: the upgrade's report ends by naming each, in order.
   - If you skipped versions, copy in the newest and upgrade once: it runs each version's step
     in turn. From 8.3 on, the Toolbox's tests upgrade each version's Example projects straight
     to the newest.
   - If your Project was made before 7.1, bring it to 7.1 by hand first, then upgrade it as
     above: in `CHANGES.md`, at the top of the download, read the "To update" part of every
     version newer than yours, up to 7.1's. The newest comes first, so start at your version's
     next and read up the page. From 4.x to 6.0, that is 5.0's "To update from 4.x", then
     6.0's "To update from 5.x". Each says what to change in your notebooks and files. A
     Project 7.0 made looks like one 7.1 made to `project.upgrade()`, so do 7.1's "To update
     from 7.0" first.
   - If a mark in `admin/databases.py` asks for your Dev and Prod Databases' names, fill in
     DEV and PROD in place of `<DEV_DATABASE>` and `<PROD_DATABASE>`. Naming them renames
     nothing: each Saved table you made before, such as `mart.daily_job_runs`, keeps its name
     and its folder, and new tables, conversions and promotions use the names you set.

What an Upgrade does:

- Updating is copying in the new folder; an **Upgrade** carries your Project's files to the new
  version, one version at a time.
- It makes each change that needs no judgement, keeping the file as it was in the folder
  admin/removed/, and marks each one it leaves for you with an `# UPGRADE <version>:` comment at
  the line.
- `project.check()` lists the marks left.
- It never touches the warehouse.

How-to:
[Upgrade your Project to a new Toolbox version](../sqlglot_composer/how_to.html#upgrade_your_project_to_a_new_toolbox_version).

When it is imported, the folder checks itself against its `version.txt`, the one file that
names its version and lists each of its files:

- If a file is missing or extra, if `version.txt` is missing or unreadable, or if this Python or
  the library it needs won't work with it, the import stops and says what happened, why it
  matters and the usual fix.
- If a file differs from the download, edited by hand or pasted from another download, the
  import only warns, naming it.

## License

- The Toolbox, its Example projects and its Templates are under the MIT No Attribution
  license, in `LICENSE`.
- Use them, change them, share them or sell them, at work or anywhere else, with no need to say
  where they came from, so you needn't copy `LICENSE` along with the folder.
- They come as they are, with no warranty.

## Cheat sheet

Everything the Toolbox offers, one line each, grouped by the file of `sqlglot_composer` it
lives in.

- Import every name from `sqlglot_composer` itself, never from a file inside it.
- Arithmetic isn't in it: a calculation uses Python's own `+ - * /` on columns, as in
  `job_runs.duration_mins / 60`.
- The star import brings the 117 names listed here before the admin module.
- Two modules' functions come last: the admin module's, which change your own Saved tables, and
  the project module's, which make and archive a Project's folders and files. The star import
  leaves both out, so import each by name, as `from sqlglot_composer import admin, project`,
  and call `admin.drop_table(t)` or `project.new_table("mart.daily_job_runs")`.

<!-- CHEAT SHEET -->
