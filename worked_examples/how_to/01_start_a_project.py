"""Start a Project

For: Getting started

## Goal

Get a Project ready: one folder that holds the Toolbox, warehouse.py, where your own two
functions, `query` and `execute`, run Hive SQL on your warehouse, and, as you add them, your tables' Table references, the Building blocks
your notebooks share and a notebook per Saved table. `project.start()` lays the folder out the
same way every time. Then you try a first Statement on the Example database, the made-up tables
that ship inside the Toolbox, so you see each piece work before you touch a real table.

## When you'd use it

Once, when you start writing Hive with the Toolbox for your team's tables. Every notebook after
it lives in the Project, finds the Toolbox and your query and execute through it, and makes and removes its
folders and files through the Project's admin notebooks, which log each change.

## Steps

### Make the Project's folder and put the Toolbox in it

Make an empty folder for the Project, such as my_project. The Toolbox is one folder,
`sqlglot_composer`: copy it whole from the Toolbox you downloaded into the Project's folder.
Keep your own files beside it, never inside it: to update the Toolbox, you delete the folder
and copy it in again.

Then open a notebook in the Project's folder for the steps here. Jupyter runs a notebook in the
folder it is in, so the notebook finds `sqlglot_composer` beside it.

### Import the Toolbox

One line imports every Toolbox name: `statement`, the clause functions such as `SELECT`,
`FROM` and `WHERE`, `to_hive`, `show_hive`, `run`, `example_database`, and the rest. A second
imports the `project` module, which makes and keeps the Project's folders: like the admin
module, which later how-tos use, it is imported by its name, since the first line leaves it
out.

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project

If the import stops instead, its message says what happened, why it matters and the usual fix.
Most often a file is missing, or files from different downloads were mixed in one folder.

### Start the Project

`project.start()` makes the Project's folders and files in the folder your notebook runs in:

>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py. Next: write your query and execute in warehouse.py.

This is the Project, beside the Toolbox you copied in, and what each part is for:

- warehouse.py: your query and execute, written once, which every notebook imports from
  here;
- `admin/`: a notebook per Project action, which you run to make or remove a folder or file,
  such as new_table.ipynb; admin_log.md, the Admin log, every Project action, oldest
  first; registry.csv, every Table folder and Table reference made, and when; and
  `templates/`, the Templates a new Table notebook is made from;
- `references/`: a Table reference per table you read or write, and the Reference sheet;
- `building_blocks/`: the pieces several notebooks share;
- `tables/`: a Table folder per Saved table, holding its notebook and `lineage/`, its Lineage,
  a pair of files each time you export it.

`references/`, `building_blocks/` and `tables/` are empty for now:
[Add your tables' references](#add_your_tables_references) fills the first, and
[Add a Saved table](#add_a_saved_table) the last. Make and remove Table folders and Table
references with the `project` module's calls, such as `project.new_table(...)`, never by hand
in your file explorer. Each admin notebook holds one such call, ready to fill in, and calling
it from any notebook of the Project does just the same: it refuses a folder or file that is
already there, so nothing of yours is written over, lists what it made in the registry, and
logs what it did in the Admin log. `Path`, from Python's own `pathlib`, reads a file; the
log's first entry is the one after its heading:

>>> from pathlib import Path
>>> print(Path("admin/admin_log.md").read_text(encoding="utf-8").split("## ")[1])
2026-09-25 09:00:00, Project action
<BLANKLINE>
- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: a notebook, at commit 1a2b3c4
- Result: worked
<BLANKLINE>
<BLANKLINE>

The Script line names the git commit your Project's folder is at, when you keep it in git,
and nogit when you don't; this page shows a made-up one, 1a2b3c4.

### Write your query and execute

The Toolbox never connects to anything itself. It writes Hive as text, and `run` hands that
text to a function of yours, which runs it. Your team's API most likely runs Hive with two
calls: one that gives back rows, as a SELECT does, and one that gives back nothing, as a
statement that changes a table does, such as a write or a CREATE TABLE. So you write two
functions, one over each call:

- `query` runs Hive and gives back its rows as a pandas DataFrame;
- `execute` runs Hive and gives back nothing.

The Toolbox picks which one each Statement goes to: a read goes to your `query`, and a write, a
CREATE TABLE or anything else that changes a table goes to your `execute`. How you connect,
retry or save files stays in the two functions, so the Toolbox works with whatever your
notebooks use to reach the warehouse.

`project.start()` wrote warehouse.py with a query and an execute that run Hive on the Example
database, for you to replace:

>>> print(Path("warehouse.py").read_text(encoding="utf-8"))
\"\"\"warehouse - your two calls to the warehouse, query and execute.
...
def query(hive: str) -> pd.DataFrame:
    \"\"\"Run a Hive string that gives back rows, and give them back as a pandas DataFrame.\"\"\"
    return example_database.query(hive)  # at work: your warehouse's query call
<BLANKLINE>
<BLANKLINE>
def execute(hive: str) -> None:
    \"\"\"Run a Hive string that changes something, such as a write, and give back nothing.\"\"\"
    example_database.execute(hive)  # at work: your warehouse's execute call
<BLANKLINE>

Open warehouse.py in your editor and write your own two. Each calls your team's API, whatever
it uses to run a Hive string: `query` its call that gives back rows, turning them into a pandas
DataFrame, each column named, and `execute` its call that gives back nothing:

    import pandas as pd

    def query(hive: str) -> pd.DataFrame:
        rows = my_api.query(hive)  # your team's own call that gives back rows goes here
        return pd.DataFrame(rows)

    def execute(hive: str) -> None:
        my_api.execute(hive)  # your team's own call that gives back nothing goes here

`hive: str`, `-> pd.DataFrame` and `-> None` are type hints: they say a Hive string goes in,
and that a DataFrame comes out of `query` and nothing out of `execute`. Python doesn't check
them. A function of yours that takes your query hints it as a function that takes one `str`
and gives back a DataFrame, `Callable[[str], pd.DataFrame]`, and one that takes your execute as
a function that takes one `str` and gives back nothing, `Callable[[str], None]`, as later
how-tos do:

    from collections.abc import Callable

    def run_today(query: Callable[[str], pd.DataFrame],
                  execute: Callable[[str], None]) -> None:
        ...

This works when your API gives each row as a dict, such as `{"run_id": 97, "job_id": 3}`:
`pd.DataFrame(rows)` takes the column names from its keys. If it gives each row as a tuple, it
gives the column names apart too, as a database cursor does in `cursor.description`. Pass those
names on; don't type them yourself, since each Statement has its own columns:

    def query(hive: str) -> pd.DataFrame:
        cursor.execute(hive)  # your team's own cursor, from its database library
        names = [column[0] for column in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=names)

    def execute(hive: str) -> None:
        cursor.execute(hive)  # the same cursor: nothing comes back to read

Both use one cursor, so they share one session: a Session setting sent through `execute` holds
for what is sent after it on that session, through either function. And let each raise when
the warehouse reports a failure. If your API gives back an error rather than raising one,
raise it yourself, such as `raise RuntimeError(answer.error)`: the Toolbox knows a step failed
only when your function raises, and otherwise logs it as one that worked.

Every notebook of the Project then imports them with `from warehouse import query, execute`,
or only the one it uses. There is no warehouse on this page, so the next steps use the Example
database's own two: `example_database.query`, which runs Hive on the Example database's seven
made-up tables, and `example_database.execute`, which prints the first line of the Hive and
changes nothing, since the Example database can't be written to. At work you give `run` your
own `query` and `execute` in their place.

### See how a notebook deeper in the Project finds the Toolbox

Python looks for what a notebook imports in the folder the notebook runs in. A notebook in the
Project's folder finds `sqlglot_composer` and warehouse.py there. A Table notebook sits two
folders down, in `tables/<db>__<table>/`, so its first cell starts with three lines: two
imports, and one that puts the Project's folder on Python's list of places to look:

    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import *
    from warehouse import query, execute

`pathlib.Path.cwd()` is the folder the notebook runs in, and `.parents[1]` the folder two above
it: the Project's. After them, the notebook imports the Toolbox, your query and execute, and
your tables'
Table references and Building blocks by their folders, as in
`from references.ops__job_runs import job_runs`. A Table notebook is written with these lines
already in it, as [Add a Saved table](#add_a_saved_table) shows.

### Build a first Statement on the Example database

The Example database's first three tables are `ops.jobs`, one row per job; `ops.job_runs`, one
row per run of a job, on two days, 2026-09-23 and 2026-09-24; and `ops.run_alerts`, the alerts
a run raised. A fourth, `ops.scheduler_runs`, is the scheduler's own record of the two days'
runs, and three more, which the Intermediate how-tos use, hold 14 days each. Each table's
Table reference, which says what columns it has, comes with the Toolbox. Give the one you need
a short name:

>>> job_runs = example_database.job_runs

A Statement is one query, built from clause functions written in SQL's order: `SELECT` the
columns you want, `FROM` a table, and keep only some rows with `WHERE`. `WHERE` keeps a row
only if every condition in it holds. This Statement finds the runs that failed.

`job_runs.dt` is the table's Date partition: the day each row belongs to. The warehouse stores
such a table a day at a time, so every Statement must give the first and the last day it
reads, here with `between`: a Load limit refuses one that doesn't.

>>> failed = statement(
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
...     FROM(job_runs),
...     WHERE(equals(job_runs.status, "FAILED"),
...           between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )

Nothing has run yet: `failed` holds the Statement, ready to become Hive.

### See its Hive

`to_hive` gives the Hive as text: exactly what `run` sends. In it, `FROM ops.job_runs AS
job_runs` reads the table and calls it `job_runs`, the name the other lines use.

>>> print(to_hive(failed))
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.status = 'FAILED' AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'

`show_hive` prints the same Hive with a `;` at the end, ready to paste into another program,
such as Hue, Beeline or DBeaver. It gives the text back too, so `text` keeps it to save or
use again:

>>> text = show_hive(failed)
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.status = 'FAILED' AND job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24';

In a notebook you can also write `show_hive(failed)` on a line of its own: it prints the Hive
once, and the text it gives back isn't shown a second time. After you build each Statement,
call `show_hive` on it to read what will run.

### Run it

`run` turns the Statement into Hive, hands it to your `query` function, since it reads rows,
and gives back the DataFrame `query` returns. Here the Example database's query runs it:

>>> run(failed, query=example_database.query)
   run_id  job_id          dt
0      97       3  2026-09-23
1     102       2  2026-09-24

At work it is the same call with your own query, `run(failed, query=query)`, after
`from warehouse import query`, and a Statement that reads your own tables. A Statement that
writes a table goes to your execute instead, and `run` gives back nothing for it, as
[Save a table](#save_a_table) shows.

## Check it worked

The Project's folders are there, and `project.check()` finds nothing wrong with them: every
Table folder and Table reference the registry lists is there, and none is there that it doesn't
list.

>>> sorted(path.name for path in Path(".").iterdir() if path.is_dir())
['admin', 'building_blocks', 'references', 'tables']

In your own Project the list holds `sqlglot_composer` too, the Toolbox you copied in; this
page's folder has none.

>>> project.check()
Every Table folder and Table reference is registered, and each one registered is there.

Keep what `run` gives back, and check that it is a pandas DataFrame holding the two failed
runs:

>>> import pandas as pd
>>> result = run(failed, query=example_database.query)
>>> isinstance(result, pd.DataFrame)
True
>>> len(result)
2

At work, try your own query on its own, with Hive that reads no table, such as
`query("SELECT 1 AS one")`. A working query gives back a pandas DataFrame with one column,
named `"one"`. The Example database's query shows what to expect:

>>> example_database.query("SELECT 1 AS one")
   one
0    1

## Common mistakes

### Starting a Project inside another

`project.start()` refuses a folder inside a Project, the Project's own folder among them, so a
second run never writes over the first's files:

>>> project.start()
Traceback (most recent call last):
...
FileExistsError:
  What happened:  project.start() was run inside a Project: ...
...

Run it once, in the Project's folder. To work on the Project, open a notebook in it: there is
nothing to start again.

### A query that gives back the wrong thing

Many APIs give each row as a tuple, without the column names. A query that hands those rows to
`pd.DataFrame` without the names gives back a DataFrame whose columns are numbered 0, 1 and 2.
This page has no API, so a stand-in plays yours here, giving each row as a tuple:

>>> def query_api(hive: str) -> list[tuple[object, ...]]:
...     answer = example_database.query(hive)
...     return [tuple(row) for row in answer.itertuples(index=False)]
>>> query_without_column_names = lambda hive: pd.DataFrame(query_api(hive))
>>> run(failed, query=query_without_column_names)
     0  1           2
0   97  3  2026-09-23
1  102  2  2026-09-24

Nothing stops it, but no column has its name: reading one by name, such as `"run_id"`, stops
with a `KeyError`. Check that `query("SELECT 1 AS one")` gives back a column named `"one"`. If
it doesn't, pass `pd.DataFrame` the column names your API gives, as the step Write your query
and execute shows.

A query that gives back the rows just as the API gives them, a plain list, without
`pd.DataFrame`, stops when `run` gets them back:

>>> query_without_a_dataframe = lambda hive: query_api(hive)
>>> run(failed, query=query_without_a_dataframe)
Traceback (most recent call last):
...
TypeError:
  What happened:  Your query gave back a list, where a pandas DataFrame goes.
...

The fix is the message's: end your query with `return pd.DataFrame(rows)`, with the column
names when each row is a tuple, as the step Write your query and execute shows. Your execute
needs no such care: `run` never reads what it gives back.

### A Statement that doesn't give the days it reads

A table with a Date partition is stored a day at a time, and a Statement that doesn't give the
first and last day to read would read every day the table holds. The Toolbox refuses it as you
build it, before anything runs:

>>> every_failed_run = statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(equals(job_runs.status, "FAILED")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.LoadRefused:
  What happened:  FROM(job_runs) reads ops.job_runs, but nothing bounds its Date partition dt at both ends.
...
  Opt-out:        FROM(job_runs, reads_all_partitions=True)

Give the days as the message says, with `between` or `last_n_days` in `WHERE`, as `failed`
does. The message's Opt-out, `reads_all_partitions=True`, reads every day: use it only for a
small table you truly need whole.

## Next

- Write the Table references of the tables you read, many at once:
  [Add your tables' references](#add_your_tables_references).
- Build a Statement a clause at a time, then paste its Hive into another program:
  [Build a first Statement and paste its Hive](#build_a_first_statement).
- Give a Saved table its own Table folder and notebook: [Add a Saved table](#add_a_saved_table).
- Build Statements of your own from the [Example gallery](examples.html), which has a Worked
  example for every Toolbox name, such as [`statement`](examples.html#statement),
  [`run`](examples.html#run) and [`show_hive`](examples.html#show_hive).
"""
