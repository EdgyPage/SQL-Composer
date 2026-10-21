"""Add a Saved table

For: Getting started

## Goal

Give a Saved table its own place in your Project: a Table folder holding its notebook, and a
Table reference in references/. `project.new_table` makes both from a Template and registers
them. You fill in the Table reference and the notebook's `<...>`, try its steps, and from then
on `project.run_tables` writes it every day with the Project's other Saved tables, each after
the tables it reads.

## When you'd use it

Each time you start a new Saved table in a Project, such as a day's counts that several people
read. [Save a table](#save_a_table) shows the Statements that create and write one; this
how-to puts them where the Project keeps them, so every table is laid out the same way, and
written in the right order.

## Steps

### Start a Project, with the table it reads

These steps run in a Project, as [Start a Project](#start_a_project) makes one, holding the
Table reference of each table the Saved table reads, as
[Add your tables' references](#add_your_tables_references) writes them. This page starts a new
one, and writes the one it reads, `ops.job_runs`:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and send.py. Next: write your send in send.py.
>>> project.add_references(["ops.job_runs"], send=example_database.send)
Wrote references/ops__job_runs.py: fill in its TODO lines.

### Make its Table folder

`project.new_table` takes the Saved table's name. At work, run it from the admin notebook
admin/new_table.ipynb, where the Project keeps its one-time actions:

>>> project.new_table("mart.daily_job_runs")
Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
admin/templates/daily_table.py.
Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.

It made three things, and listed each in the registry:

- tables/mart__daily_job_runs/, the table's Table folder, named after the database and the
  table joined by two underscores, as its Table reference is;
- mart__daily_job_runs.ipynb in it, the Table notebook, from the Template daily_table, a table
  written a day at a time. `template=` picks another: `"incremental_load"`, which writes its
  last few days again on each run, `"weekly_rollup"`, `"as_of_lookup"` or `"quality_checks"`.
  The notebook's text cell says what each `<...>` in it is for;
- lineage/ beside it, empty until you export the table's Lineage;
- references/mart__daily_job_runs.py, its Table reference, shown above, with `<...>` and TODO
  lines to fill in: a Saved table doesn't exist until you create it, so nothing can be asked of
  it.

The notebook has five code cells, run top to bottom:

1. the path lines and imports from [Start a Project](#start_a_project), your send, and DAY, a
   day to try things on;
2. the logic, whose first line is `# logic`: only imports and functions, such as create,
   preview and write_day, each giving a Statement and running nothing;
3. try it: each step's Hive, then the day's rows;
4. its Lineage, as [Lineage across your tables](#lineage_across_your_tables) shows;
5. its rows in the Reference sheet, as [The Reference sheet](#the_reference_sheet) shows.

### Fill in its Table reference

Open references/mart__daily_job_runs.py in your editor and fill it in: what one row is, the
columns write_day saves with their types, then the day, the key, and the folder your Saved
tables go in, as [Describe a table by hand](#describe_a_table_by_hand) explains. This page has
no editor, so this step writes the file filled in:

>>> from pathlib import Path
>>> size = Path("references/mart__daily_job_runs.py").write_text('''\"\"\"mart.daily_job_runs - one row per job and day: its runs.\"\"\"
...
... from sqlglot_composer import Table
...
... daily_job_runs = Table(
...     "mart.daily_job_runs",
...     columns={
...         "job_id": "bigint",
...         "runs": "bigint",
...         "dt": "string",
...     },
...     date_partition="dt",
...     key=["job_id", "dt"],
...     location="/data/your_team/tables",
... )
... ''', encoding="utf-8")

### Fill in its notebook

Open the notebook in Jupyter and type over each `<...>` in its code cells: the table it reads,
by its file in references/ and its variable, its Date partition, the column each row is for,
the name of the count, and a day to try. This page has no Jupyter, so these lines do the same.
A notebook is a JSON file, and each cell keeps its lines in its `"source"`:

>>> import json
>>> path = Path("tables/mart__daily_job_runs/mart__daily_job_runs.ipynb")
>>> notebook = json.loads(path.read_text(encoding="utf-8"))
>>> filled_in = {"<SOURCE_NAME>": "ops__job_runs", "<SOURCE_TABLE>": "job_runs",
...              "<DATE_PARTITION>": "dt", "<KEY_COLUMN>": "job_id",
...              "<COUNT_NAME>": '"runs"', "<DAY>": '"2026-09-24"'}
>>> for cell in notebook["cells"]:
...     if cell["cell_type"] == "code":
...         for placeholder, value in filled_in.items():
...             cell["source"] = [line.replace(placeholder, value) for line in cell["source"]]
>>> size = path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")

Its logic cell now imports `ops.job_runs`' Table reference, and counts each job's runs a day:

    from references.ops__job_runs import job_runs


    def rows(first_day, last_day):
        return [
            SELECT(job_runs.job_id, AS(count_rows(), "runs")),
            FROM(job_runs),
            WHERE(between(job_runs.dt, first_day, last_day)),
            GROUP_BY(job_runs.dt, job_runs.job_id),
        ]

### Try its steps

In Jupyter, run the notebook's cells top to bottom. Here, `project.load` runs its logic cell
and gives back what it defines, as any notebook or admin notebook of the Project can:

>>> logic = project.load("mart.daily_job_runs")
>>> logic
The logic of mart.daily_job_runs: create, rows, preview, write_day, backfill.

Cell 3 prints the Hive of the steps that create the table and write a day, then runs the
preview, the rows the day's write would save:

>>> text = show_hive([logic.create(), logic.write_day("2026-09-24")])
-- 1 of 2
CREATE EXTERNAL TABLE IF NOT EXISTS mart.daily_job_runs (
  job_id BIGINT,
  runs BIGINT,
  PRIMARY KEY (job_id, dt) DISABLE NOVALIDATE
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/tables/mart/daily_job_runs';
<BLANKLINE>
-- 2 of 2
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-24')
SELECT
  job_runs.job_id,
  COUNT(*) AS runs
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-24' AND '2026-09-24'
GROUP BY
  job_runs.dt,
  job_runs.job_id;
>>> run(logic.preview("2026-09-24"), send=example_database.send)
   job_id  runs
0       1     2
1       2     1
2       3     1

At work, send the create step once, `run(logic.create(), send=...)` with your send, before the first write.
The Example database can be read but not written, so this page sends neither.

### Write it every day, with the Project's other tables

`project.run_tables` loads every Table notebook's logic and writes each table's day, a
table before any table that reads it. With no send, it prints each write's Hive in that order
and sends nothing, a dry run to read first:

>>> project.run_tables("2026-09-24")
-- 1 of 1: mart.daily_job_runs
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-24')
SELECT
  job_runs.job_id,
  COUNT(*) AS runs
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-24' AND '2026-09-24'
GROUP BY
  job_runs.dt,
  job_runs.job_id;
Printed 1 write in order, and sent nothing. Pass send= to run them.

At work, the admin notebook admin/run_tables.ipynb does this each day, then sends them with your
send, project.run_tables(DAY, send=send), printing a line as each table is written.

## Check it worked

The Table folder holds its notebook and lineage/, and the registry lists the folder and both
Table references:

>>> sorted(path.name for path in Path("tables/mart__daily_job_runs").iterdir())
['lineage', 'mart__daily_job_runs.ipynb']
>>> project.check()
Every Table folder and Table reference is registered, and each one registered is there.

`project.load` runs the notebook's logic without a `<...>` left, and its write_day writes the
day:

>>> to_hive(logic.write_day("2026-09-24")).splitlines()[0]
"INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-24')"

## Common mistakes

### Loading a notebook with a <...> left

A second Saved table, made and not yet filled in, still has every `<...>` of its Template.
`project.load`, and so `project.run_tables`, refuses its logic cell, naming the first line to
fill in:

>>> project.new_table("mart.alerts_per_job")
Made tables/mart__alerts_per_job/: mart__alerts_per_job.ipynb and lineage/, from
admin/templates/daily_table.py.
Wrote references/mart__alerts_per_job.py: fill in its <...> and TODO lines.
>>> project.load("mart.alerts_per_job")
Traceback (most recent call last):
...
ValueError:
  What happened:  project.load("mart.alerts_per_job"): the logic cell of tables/mart__alerts_per_job/mart__alerts_per_job.ipynb isn't Python yet, at its line 9: from references.<SOURCE_NAME> import <SOURCE_TABLE>
...

Fill in every `<...>`, run the notebook's cells to check them, then load it again. Until then,
`project.run_tables("2026-09-24", tables=["mart.daily_job_runs"])` writes only the tables you
name.

### Making a Table folder that is already there

`project.new_table` never writes over a Table folder: it holds your notebook and its Lineage.
Run again for the same table, it stops:

>>> project.new_table("mart.daily_job_runs")
Traceback (most recent call last):
...
FileExistsError:
  What happened:  project.new_table("mart.daily_job_runs"): tables/mart__daily_job_runs/ is already there, so nothing was made.
...

Open the notebook that is there instead. To start a table again, archive its folder first with
`project.remove_table("mart.daily_job_runs")`, from admin/remove_table.ipynb, which moves it
into admin/removed/ and logs it; never delete a Table folder by hand, or the registry lists a
folder that isn't there.

## Next

- Write a range of past days of the table, one day at a time:
  [Backfill a range of days](#backfill_a_range_of_days).
- Follow each of its columns back to the tables it reads, across the Project's notebooks:
  [Lineage across your tables](#lineage_across_your_tables).
- List its columns beside every other table's: [The Reference sheet](#the_reference_sheet).
- What each step's Statement does, and how a Saved table is stored:
  [Save a table](#save_a_table).
- The gallery's [`create_table`](examples.html#create_table) and
  [`INSERT_OVERWRITE`](examples.html#INSERT_OVERWRITE) entries.
"""
