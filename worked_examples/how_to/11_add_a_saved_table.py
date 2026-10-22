"""Add a Saved table

For: Getting started

## Goal

Give a Saved table its own place in your Project: a Table folder holding its notebook, and a
Table reference in references/. `project.new_table` makes both from a Template and registers
them. You fill in the Table reference and the notebook's `<...>`, try its steps, and from then
on `project.run_tables` writes it with the Project's other Saved tables, each after the tables
it reads.

## When you'd use it

Each time you start a new Saved table in a Project, such as a day's counts that several people
read. [Save a table](#save_a_table) shows the Statements that create and write one; this
how-to puts them where the Project keeps them, so every table is laid out the same way, and
written in the right order.

## Steps

### Start a Project, with the table it reads

These steps run in a Project, as [Start a Project](#start_a_project) makes one, holding the
Table reference of each table the Saved table reads, as
[Add your tables' references](#add_your_tables_references) writes them. In your own Project, which is started already, leave out `project.start()`: it refuses a
folder that is a Project. This page has none, so it starts one,
and writes the one table it reads, `ops.job_runs`:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
>>> project.add_references(["ops.job_runs"], query=example_database.query)
Wrote references/ops__job_runs.py: fill in its TODO lines.
Wrote references/ops.py: from references import ops gives ops.job_runs.

### Make its Table folder

`project.new_table` takes the Saved table's name. The admin notebook admin/new_table.ipynb
holds this call, ready to fill in; calling it from any notebook of the Project does the same:

>>> project.new_table("mart.daily_job_runs")
Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.

It made four things, and listed two of them, the Table folder and the Table reference, in the
registry:

- tables/mart__daily_job_runs/, the table's Table folder, named after the database and the
  table joined by two underscores, as its Table reference is;
- mart__daily_job_runs.ipynb in it, the Table notebook, from the Template saved_table, a
  Saved table worked out from a table it reads. `template=` picks another:
  `"quality_checks"`, which saves a table's row counts and checks its rows. The notebook's
  text cell starts with what each `<...>` in it is for;
- lineage/ beside it, empty until you export the table's Lineage;
- references/mart__daily_job_runs.py, its Table reference, shown above, with `<...>` and TODO
  lines to fill in: a Saved table doesn't exist until you create it, so nothing can be asked of
  it.

The notebook has five code cells, run top to bottom:

1. the path lines and imports from [Start a Project](#start_a_project), and your query;
2. the logic, whose first line is `# logic`: imports, `READS`, the rows `write()` reads, and
   functions, each giving a Statement and running nothing: create, rows, preview and write;
3. try it: each step's Hive, then the day's rows;
4. its Lineage, as [Lineage across your tables](#lineage_across_your_tables) shows;
5. its rows in the Reference sheet, as [The Reference sheet](#the_reference_sheet) shows.

### Fill in its Table reference

Open references/mart__daily_job_runs.py in your editor and fill it in: what one row is, the
columns `write()` saves with their types, then its partition column, the key, and the table's
own folder, as [Describe a table by hand](#describe_a_table_by_hand) explains. Its key is
`["job_id", "dt"]`: the table has a row per job every day, so a job's rows are told apart by
the day. This page has no editor, so this step writes the file filled in:

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
...     partitioned_by=["dt"],
...     key=["job_id", "dt"],
...     location="/data/your_team/mart.db/daily_job_runs",
... )
... ''', encoding="utf-8")

### Fill in its notebook

Open the notebook in Jupyter and type over each `<...>` in its code cells: the table it reads,
by its file in references/ and its variable, the rows `write()` reads, as a condition on its
partition column, the column each row is for, the name of the count, and the partition column
that fills this table's own. A name Python reads, such as the table's variable, goes in bare; a
value, such as the count's name, goes in quotes, as the notebook's text cell says. This page has no Jupyter, so these lines do the same.
A notebook is a JSON file, and each cell keeps its lines in its `"source"`:

>>> import json
>>> path = Path("tables/mart__daily_job_runs/mart__daily_job_runs.ipynb")
>>> notebook = json.loads(path.read_text(encoding="utf-8"))
>>> filled_in = {"<SOURCE_NAME>": "ops__job_runs", "<SOURCE_TABLE>": "job_runs",
...              "<READS>": 'equals(job_runs.dt, "2026-09-24")', "<GROUP_COLUMN>": "job_id",
...              "<COUNT_NAME>": '"runs"', "<PARTITION_COLUMN>": "dt"}
>>> for cell in notebook["cells"]:
...     if cell["cell_type"] == "code":
...         for placeholder, value in filled_in.items():
...             cell["source"] = [line.replace(placeholder, value) for line in cell["source"]]
>>> size = path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")

Its logic cell now imports its own Table reference and `ops.job_runs`', and counts each job's
runs a day:

    from references.mart__daily_job_runs import daily_job_runs
    from references.ops__job_runs import job_runs


    READS = equals(job_runs.dt, "2026-09-24")


    def rows() -> list[Clause]:
        return [
            SELECT(
                job_runs.job_id,  # what each row is for
                AS(count_rows(), "runs"),
                job_runs.dt,  # this table's partition column, last
            ),
            FROM(job_runs),
            WHERE(READS),
            GROUP_BY(
                job_runs.job_id,
                job_runs.dt,  # kept, so each Partition's rows stay apart
            ),
        ]


    def write() -> Statement:
        return statement(INSERT_OVERWRITE(daily_job_runs), *rows())

`READS` picks the rows `write()` reads: here one day's Partition of `ops.job_runs`. The table
is partitioned by dt, so a read must filter it; one that isn't partitioned can be read whole,
as the notebook's text cell says.

### Try its steps

In Jupyter, run the notebook's cells top to bottom. Here, `project.load` runs its logic cell
and gives back what it defines, as any notebook or admin notebook of the Project can:

>>> logic = project.load("mart.daily_job_runs")
>>> logic
The logic of mart.daily_job_runs: create, rows, preview, write.

Cell 3 prints the Hive of the steps that create the table and write the rows `READS` picks,
then runs the preview, the rows the write would save:

>>> text = show_hive([logic.create(), logic.write()])
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
LOCATION '/data/your_team/mart.db/daily_job_runs';
<BLANKLINE>
-- 2 of 2
-- The Session setting "dynamic_partitions": this write fills dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt)
SELECT
  job_runs.job_id,
  COUNT(*) AS runs,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24'
GROUP BY
  job_runs.job_id,
  job_runs.dt;
>>> run(logic.preview(), query=example_database.query)
   job_id  runs          dt
0       1     2  2026-09-24
1       2     1  2026-09-24
2       3     1  2026-09-24

The write fills the day's Partition from the rows' own dt, so Hive's dynamic partitioning must
be switched on first: show_hive prints the two SET lines that do it ahead of the write. At
work, send them once on your connection, `run(hive_settings("dynamic_partitions"),
execute=execute)`, before the first such write.

The CREATE writes the Key, `PRIMARY KEY (job_id, dt) DISABLE NOVALIDATE`, for whoever reads the
table's description: Hive keeps it but never checks it, and the Toolbox checks it as you build
each Statement instead. dt is in it though it sits under `PARTITIONED BY`: a partition column
is a column of every row all the same.

At work, send the create step once, `run(logic.create(), execute=...)` with your execute, before the
first write. The Example database can be read but not written, so this page sends neither.

### Write it with the Project's other tables

`project.run_tables` loads every Table notebook's logic and sends each table's `write()`, a
table before any table that reads it: it finds which tables each write reads from its Hive. With no execute, it prints each write's Hive in that order
and sends nothing, a dry run to read first:

>>> project.run_tables()
-- 1 of 1: mart.daily_job_runs
-- The Session setting "dynamic_partitions": this write fills dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt)
SELECT
  job_runs.job_id,
  COUNT(*) AS runs,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24'
GROUP BY
  job_runs.job_id,
  job_runs.dt;
Printed 1 write in order, and sent nothing. Pass execute= to run them.

At work, you run the admin notebook admin/run_tables.ipynb, or your team's scheduler does: it
does this, then sends them with your query and execute,
`project.run_tables(query=query, execute=execute)`, printing a line as each table is written.
Each `write()` writes the rows its notebook's `READS` picks: change `READS` to write others.

## Check it worked

The Table folder holds its notebook and lineage/, and the registry lists the folder and both
Table references:

>>> sorted(path.name for path in Path("tables/mart__daily_job_runs").iterdir())
['lineage', 'mart__daily_job_runs.ipynb']
>>> project.check()
Every Table folder and Table reference is registered, and each one registered is there.

With no `<...>` left in it, the notebook's logic runs, and its `write()` writes the table:

>>> to_hive(logic.write()).splitlines()[0]
'INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt)'

## Common mistakes

### Loading a notebook with a <...> left

A second Saved table, made and not yet filled in, still has every `<...>` of its Template.
`project.load`, and so `project.run_tables`, refuses its logic cell, naming the first line to
fill in:

>>> project.new_table("mart.alerts_per_job")
Made tables/mart__alerts_per_job/: mart__alerts_per_job.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__alerts_per_job.py: fill in its <...> and TODO lines.
Wrote references/mart.py: from references import mart gives mart.daily_job_runs.
>>> project.load("mart.alerts_per_job")
Traceback (most recent call last):
...
ValueError:
  What happened:  project.load("mart.alerts_per_job"): the logic cell of tables/mart__alerts_per_job/mart__alerts_per_job.ipynb isn't Python yet, at its line 9: from references.<SOURCE_NAME> import <SOURCE_TABLE>
...

Fill in every `<...>`, run the notebook's cells to check them, then load it again. Until then,
`project.run_tables(tables=["mart.daily_job_runs"])` writes only the tables you name.

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

- Write a range of past days of a table:
  [Backfill a range of days](#backfill_a_range_of_days).
- Follow each of its columns back to the tables it reads, across the Project's notebooks:
  [Lineage across your tables](#lineage_across_your_tables).
- List its columns beside every other table's: [The Reference sheet](#the_reference_sheet).
- What each step's Statement does, and how a Saved table is stored:
  [Save a table](#save_a_table).
- The gallery's [`create_table`](examples.html#create_table) and
  [`INSERT_OVERWRITE`](examples.html#INSERT_OVERWRITE) entries.
"""
