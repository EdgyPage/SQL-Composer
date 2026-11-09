"""Start a Project

For: Getting started

## Goal

Get a Project ready. A Project is your folder at work that holds the Toolbox and your own
scripts in one fixed layout: warehouse.py, where your own two functions, `query` and `execute`,
run Hive SQL on your warehouse, and, as you add them, your tables' Table references (a file
describing one table), the Building blocks your notebooks share (pieces of code reused across
notebooks) and a notebook per Saved table (a table your own Statements write). You install what
the Toolbox needs, copy it into the folder, let `project.start()` lay the folder out, learn
which call makes each file of a Project and what you fill in, and set your connection.

## When you'd use it

- If you are about to write Hive with the Toolbox for your team's tables, start a Project once,
  as the steps below do: every notebook after it lives in the Project and finds the Toolbox and
  your query and execute there.
- If you have done this how-to, go on with the Getting started how-tos after it: each works in
  the Project this one makes, one step at a time.
- If you want to see a Project filled in, read the Starter Example project, much like the one
  those how-tos leave.

## Steps

### 1. Install what the Toolbox needs

Goal: the packages the Toolbox runs on. The Toolbox needs Python 3.11 or newer, pandas, numpy
and sqlglot. Download the Toolbox and extract it; in its top folder, requirements.txt pins each
package to the version it is tested on. Install them from a terminal in that folder, with
`pip install -r requirements.txt`, or from a notebook, with `%pip install -r` followed by the
path to that file.

A package your notebooks already have, such as pandas, needn't be installed again: delete its
line from requirements.txt first, so pip keeps the version you have.

Done when pip says each package is installed. Then step 2.

### 2. Make the Project's folder and copy the Toolbox in

Goal: a folder holding the Toolbox. Make an empty folder for the Project, such as my_project.
The Toolbox is one folder, `sqlglot_composer`: copy it whole from the download into the
Project's folder. Keep your own files beside it, never inside it: to update the Toolbox, you
delete the folder and copy the new one in.

Done when the Project's folder holds `sqlglot_composer`. Then step 3.

### 3. Open a notebook in the Project's folder

Goal: a notebook that finds the Toolbox. Open a notebook in the Project's folder, such as
start.ipynb, for the steps here. Jupyter runs a notebook in the folder it is in, so the
notebook finds `sqlglot_composer` beside it. The folder, the copied Toolbox and this notebook
are the only things of a Project you make by hand: the Toolbox makes the rest.

Done when start.ipynb is open beside `sqlglot_composer`. Then step 4.

### 4. Import the project module

Goal: the module that makes the Project's files. The `project` module makes and keeps the
Project's folders and files. Import it by its name:

>>> from sqlglot_composer import project

If the import stops instead, its message says what happened, why it matters and the usual fix.
Most often a file is missing, or files from different downloads were mixed in one folder.

Done when the import runs without a message. Then step 5.

### 5. Start the Project

Goal: the Project's layout. `project.start()` lays out the folder your notebook runs in:

>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/, scheduled_runs/ and warehouse.py.
Next: set conn, your connection, in warehouse.py.

Done when it says `Started a Project`. Then step 6.

### 6. Know every file of a Project

Goal: know which call makes each file, and what you fill in. Besides the three things you made
by hand, each file of a Project is made by a call of the `project` module, a Project action: a
one-time change to the Project's files, recorded in the Admin log. Make each file with its
Project action, never by hand in your file explorer. Here is every file, the call that makes
it, and what you fill in:

- `my_project/`, the Project's folder: made by you, in your file explorer.
- `sqlglot_composer/`: copied in by you. You fill in nothing: never edit a file inside it.
- start.ipynb, or any name you like, the notebook you run `project.start()` from: made by
  you, in Jupyter. Keep it for trying things out, or delete it.
- `warehouse.py`: `project.start()`. You set `conn`, your connection, in it, in step 8.
- `admin/`, a notebook for each job on the whole Project, such as check_project.ipynb,
  run_tables.ipynb and remove.ipynb: `project.start()`. You fill in the names some ask for in
  their names cell, such as the tables to remove, and run them. Calling the same Project
  action from any notebook of the Project does just the same.
- `admin/workflows/`, a folder per Workflow, an ordered list of steps that takes the Project to
  one end goal, such as new_table/, references/ and convert/, each holding its notebook:
  `project.start()`. You name what the Workflow works on in its notebook's names cell, such as
  the tables, and save it. Convert, promote, new_table and references open with four cells,
  run in order: the names cell, "Run up to your Decisions", the decisions cell, where you
  answer, and "Run the rest". Each step's own cell is below them, under Step by step, to run
  one step on purpose; in upgrade and change_a_saved_table, run each step's cell in turn.
  `project.do_next()` runs only the steps that change files, and `project.check()` names the
  next step.
- admin/databases.py, the Database settings of your Dev Database, where you create and write
  tables of your own, and your Prod Database, where others read your finished tables:
  `project.start()`. You fill in DEV and PROD, a dict each, such as
  `{"database": "mart_dev", "location_root": "/data/team/dev"}`: its name, and the folder its
  tables' files go under, each table with no folder of its own placed in
  `<location_root>/<database>.db/<table>`.
  [Set your Database settings](#set_your_database_settings) shows each setting.
- admin/sent.csv, a row for each change a notebook of the Project sends to the warehouse:
  `project.start()`, then each change you run on the warehouse. You fill in nothing.
- admin/admin_log.md, the Admin log, the record of each Project action and each change you
  run: `project.start()`, then each Project action adds an entry. You fill in nothing.
- admin/registry.csv, the registry, the list of what each Project action made:
  `project.start()`, then each Project action that makes or archives a Table folder, a Table
  reference, a Building block or a Conversion folder adds a row. You fill in nothing.
- admin/project_version.txt, the Toolbox version that last wrote the Project:
  `project.start()`, then `project.upgrade()`. You fill in nothing.
- admin/workflows/convert/<name>/, a Conversion folder per batch of someone else's Hive you
  convert, its batch.md naming where each script is, read where it is and never copied, and
  what each statement became: `project.convert(...)`, from
  admin/workflows/convert/convert.ipynb, which makes each table the Hive writes a Saved table
  in your Dev Database. You answer each of its tables' Decisions, the things only you decide,
  as [Convert someone else's Hive](#convert_someone_elses_hive) shows.
- an Upgrade's checklist in admin/, named for the version it upgraded to, such as
  upgrade_7.3.md: `project.upgrade()`, once you copy in a newer Toolbox. You make each change
  it lists, each marked `# UPGRADE <version>:` at its line.
- `admin/templates/`, the Templates a new notebook or Building block is made from:
  `project.start()`. Nothing, unless you want your team's own shape.
- `references/<db>__<table>.py`, a Table reference per table:
  `project.add_references([...], query=query)` for a table in the warehouse, or
  `project.new_table(...)` for a Saved table of your own. You accept or change what it
  proposed, such as its Key, and add your own names for its columns, as [Add your tables' references](#add_your_tables_references)
  shows.
- `references/<db>.py`, a Database module per Database, the group of tables a name such as
  `ops` in `ops.jobs` names, such as references/ops.py: written again by each Project action
  that adds or archives a Table reference. Leave it as the Project actions write it.
- references/reference_sheet.csv, the Reference sheet, every column of every table you have a
  Table reference for: `project.refresh_reference_sheet()`. You fill in nothing.
- `building_blocks/<name>.py`, a Building block: `project.new_block("<name>")`. You fill in its
  `<...>` and TODO lines, as [Share Building blocks](#share_building_blocks) shows.
- `building_blocks/prod/<name>.py`, the prod copy of a Building block a promoted table
  imports: `project.promote(...)`. You fill in nothing: change the dev block and promote it
  again.
- `tables/<db>__<table>/<db>__<table>.ipynb`, a Table notebook per Saved table, whose cells
  create, preview and write it: `project.new_table("<db>.<table>")`. You fill in its `<...>`
  lines, as [Save a table](#save_a_table) shows.
- `tables/<db>__<table>/lineage/`, the Lineage of that table, which table columns feed each of
  its columns: its notebook's lineage cell. You fill in nothing.
- `tables/<db>__<table>/<db>__<table>.hql`, the Hive that table's logic sends: its notebook's
  Hive cell, written again each time it runs, as [Save a table](#save_a_table) shows. You fill
  in nothing: edit the logic instead.
- `lineage/`, beside the notebook you run it from, such as start.ipynb: the Lineage of a
  Statement exported outside a Table notebook, by `export_lineage(...)`, as
  [Follow lineage](#follow_lineage) shows. You fill in nothing.
- `admin/removed/`, what you archive: `project.remove_table(...)`,
  `project.remove_reference(...)` and `project.remove_block(...)` move a file or folder here
  rather than delete it, as does `project.remove_conversion(...)` with a Conversion folder;
  `project.upgrade()` keeps here each file as it was before it changed it, and
  `project.convert(..., overwrite=True)` each file it writes over.

`references/`, `building_blocks/` and `tables/` are empty for now. Each Project action
writes over nothing of yours: most refuse a file or folder that is already there, and convert,
run again, writes a fresh copy of a file you changed into its batch's folder. Each logs what it
did in the Admin log. `Path`, from Python's own `pathlib`, reads a file; the log's first entry
is the one after its heading:

>>> from pathlib import Path
>>> print(Path("admin/admin_log.md").read_text(encoding="utf-8").split("## ")[1])
2026-09-25 09:00:00, Project action
<BLANKLINE>
- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, scheduled_runs/, warehouse.py
- Script: a notebook, at commit 1a2b3c4
- Result: worked
<BLANKLINE>
<BLANKLINE>

The Script line names the git commit your Project's folder is at, when you keep it in git,
and nogit when you don't; this page shows a made-up one, 1a2b3c4.

Done when the Admin log's first entry names `project.start()`. Then step 7.

### 7. Read the warehouse.py start wrote

Goal: know how the Toolbox reaches your warehouse. The Toolbox never connects to anything
itself. It writes Hive as text, and hands that text to a function in warehouse.py, which hands
it to your connection to the warehouse. Your team's library most likely gives you a connection
with two calls: one that gives back rows, as a SELECT does, and one that gives back nothing, as
a statement that changes a table does, such as a write or a CREATE TABLE. So warehouse.py holds
your connection, `conn`, set once, and two functions over it:

- `query` runs Hive through `conn.query`, and gives back its rows as a pandas DataFrame;
- `execute` runs Hive through `conn.execute`, and gives back nothing.

You pick which one sends each Statement, a query the Toolbox builds, by the Toolbox function
you call, as [Build and run a first statement](#build_and_run_a_first_statement) shows.
`project.start()` set `conn` to the Example database, the made-up tables that ship inside the
Toolbox, so every how-to runs before you touch a real table:

>>> print(Path("warehouse.py").read_text(encoding="utf-8"))
\"\"\"warehouse - your connection to the warehouse, conn, and its two calls.
...
conn = example_database
<BLANKLINE>
<BLANKLINE>
def query(hive: str) -> pd.DataFrame:
    \"\"\"Run a Hive string that gives back rows, and give them back as a pandas
        DataFrame.\"\"\"
    return conn.query(hive)
<BLANKLINE>
<BLANKLINE>
def execute(hive: str) -> None:
    \"\"\"Run a Hive string that changes something, such as a write, and give back
        nothing.\"\"\"
    conn.execute(hive)
<BLANKLINE>

Among the lines the `...` above leaves out, warehouse.py imports the Example database from the
Toolbox:

    from sqlglot_composer import example_database

`example_database.query` runs Hive on the Example database's nine tables, and
`example_database.execute` prints the first line of the Hive and changes nothing, since the
Example database can't be written to. The Getting started how-tos keep warehouse.py just so.

Done when warehouse.py shows `conn = example_database` and the two functions. Then step 8.

### 8. Set your connection

Goal: `query` and `execute` that reach your warehouse. At work, open warehouse.py in your
editor and set `conn` to your team's connection, once, in place of `example_database`. `conn`
can be anything with the two calls: a module, as `example_database` is, or the object your
team's library connects you with. Here `my_api` and its connect call are made-up names for
yours:

    import my_api  # your team's library

    conn = my_api.connect()  # its query gives back a DataFrame; its execute runs a change

If your team keeps its connection in a file outside the Project, such as
team_connection.py in a folder C:/work/connections, write these lines in warehouse.py in place
of `conn = example_database`: they put that folder on Python's path, then import it.

    import sys

    sys.path.append("C:/work/connections")  # the folder team_connection.py is in
    from team_connection import conn

That is all, when your connection's `query` gives back a pandas DataFrame whose columns are
named as the SELECT names them, and its `execute` runs Hive that changes something. Whatever
`conn.execute` gives back, `execute` drops it. `query` and `execute` below it pass each Hive
string on. In this page, `query` and `execute` are always the two functions in warehouse.py;
`conn.query` and `conn.execute` are your connection's.

If your connection gives rows some other way, as each row a dict or a tuple, change `query`
to turn them into a DataFrame. A dict, such as `{"run_id": 97, "job_id": 3}`, gives its column
names from its keys:

    def query(hive: str) -> pd.DataFrame:
        return pd.DataFrame(conn.query(hive))

A database cursor gives each row as a tuple, and the column names apart, in
`cursor.description`. Pass those names on, rather than typing them yourself, since each
Statement has its own columns:

    def query(hive: str) -> pd.DataFrame:
        cursor = conn.cursor()  # your connection's cursor, from its database library
        cursor.execute(hive)
        names = [column[0] for column in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=names)


    def execute(hive: str) -> None:
        conn.cursor().execute(hive)  # the same connection: nothing comes back to read

`hive: str`, `-> pd.DataFrame` and `-> None` are type hints: they say a Hive string goes in,
and that a DataFrame comes out of `query` and nothing out of `execute`. Python doesn't check
them.

Both functions use the one `conn`. Most connections keep one session, so a Session setting, a
Hive SET line that holds for the rest of the session, sent through `execute` holds for what is sent
after it, through either function; if yours opens a new session for each call, keep one open in
`conn` yourself. And let each raise when the warehouse reports a failure. If your connection
gives back an error rather than raising one, raise it yourself, such as
`raise RuntimeError(answer.error)`: the Toolbox knows a step failed only when your connection
raises.

Done when warehouse.py sets `conn` to your connection, and `query` gives back a DataFrame. Then
step 9.

### 9. Try your query

Goal: proof that `query` gives back rows. Every notebook of the Project imports the two from
warehouse.py:

>>> from warehouse import query, execute

Try it on Hive that reads no table. A working query gives back a pandas DataFrame, one column
for each name after SELECT:

>>> one = query("SELECT 1 AS one")  # -> DataFrame
>>> one
   one
0    1

From [Build and run a first statement](#build_and_run_a_first_statement) on, the Toolbox writes
the Hive for you, and `run_query` hands it to your query.

Done when `one` shows a column named one holding 1. Then step 10.

### 10. See how a notebook deeper in the Project finds the Toolbox

Goal: know why each notebook the Project actions make starts as it does. Python looks for what
a notebook imports in the folder the notebook runs in, so a notebook in the Project's folder
finds `sqlglot_composer`, warehouse.py and `references/` there. A Table notebook sits two
folders down, in `tables/<db>__<table>/`, so its first code cell, under a comment line, starts
with three lines, two imports and one that puts the Project's folder on Python's list of places
to look, before its own imports. This is the cell as the saved_table Template, the shape a new
Table notebook is made from, writes it:

    # 1. The Project and your query
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import export_lineage, project, run_query, show_hive
    from warehouse import query

`pathlib.Path.cwd()` is the folder the notebook runs in, and `.parents[1]` the folder two above
it: the Project's. An admin notebook, one folder down, starts with `.parent` in its place,
and a Workflow's, three down, with `.parents[2]`.
`project.new_table` and `project.start` write these lines into each notebook they make.

Done when you can say which line puts the Project's folder on Python's list. Then check it
worked, below.

## Check it worked

The Project's folders are there, and `project.check()` finds nothing wrong with them: every
Table folder, Table reference and Building block the registry lists is there, and none is there
that it doesn't list.

>>> sorted(path.name for path in Path(".").iterdir() if path.is_dir())
['admin', 'building_blocks', 'references', 'scheduled_runs', 'tables']

In your own Project the list holds `sqlglot_composer` too, the Toolbox you copied in, and
`__pycache__/`, where Python keeps warehouse.py ready to import once a notebook has imported it;
this page's folder has neither.

>>> project.check()
Every Table folder, Table reference and Building block is registered, and each one registered is
    there.

Your query gives back a pandas DataFrame, with the column named as the Hive names it:

>>> import pandas as pd
>>> isinstance(one, pd.DataFrame)
True
>>> list(one.columns)
['one']

Before you go on, check that:

- the Project's folder holds admin, building_blocks, references and tables;
- `project.check()` says every Table folder, Table reference and Building block is registered;
- `query("SELECT 1 AS one")` gives back a DataFrame whose one column is named one.

## Common mistakes

### A query that gives back the wrong thing

Many APIs give each row as a tuple, without the column names. A query that hands those rows to
`pd.DataFrame` without the names gives back a DataFrame whose columns are numbered 0, 1 and 2.
This page has no API, so a stand-in plays yours here, giving each row as a tuple:

>>> def query_api(hive: str) -> list[tuple[object, ...]]:
...     answer = query(hive)
...     return [tuple(row) for row in answer.itertuples(index=False)]
>>> def query_without_column_names(hive: str) -> pd.DataFrame:
...     return pd.DataFrame(query_api(hive))
>>> query_without_column_names("SELECT 1 AS one, 2 AS two, 3 AS three")
   0  1  2
0  1  2  3

Nothing stops it, but no column has its name: reading one by name, such as `"one"`, stops
with a `KeyError`. Pass `pd.DataFrame` the column names your connection gives, as step 8, Set
your connection, shows. A query that gives back the rows as a plain list, without
`pd.DataFrame`, is refused the first time `run_query` gets them back.

### Starting the Project again

`project.start()` run again in the Project's folder writes over nothing. It adds only what
start() makes and the Project lacks, such as an admin notebook deleted by mistake, and says so:

>>> project.start()
This folder is a Project already, and lacks nothing start() makes.

Run it in a folder inside the Project, such as `tables/`, and it refuses, so no Project is ever
started inside another. To work on the Project, open a notebook in it: there is nothing to
start again.

### Making a file by hand

A Table reference or Table folder you make in your file explorer isn't in the registry, so
nothing logs it, and `project.check()` reports it. Make each with its Project action, as the
file map in step 6 says; [Keep the Project in order](#keep_the_project_in_order) shows how to
adopt one made by hand.

## Next

- Write the Table references of the tables you read, many at once:
  [Add your tables' references](#add_your_tables_references).
- Build a Statement on one of them, read its Hive and run it:
  [Build and run a first statement](#build_and_run_a_first_statement).
- See a Project filled in: the Starter Example project, in the folder
  example_projects/starter, is much like the Project the Getting started how-tos build; its
  README says how the two differ.
"""  # noqa: E501 - the saved_table Template's first cell, quoted as the Template writes it
