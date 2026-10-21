"""Lineage across your tables

For: Getting started

## Goal

Follow each column of a Saved table back through the other Saved tables of your Project that
it reads, to the tables they start from, and keep each export in the table's own history. From
a Table notebook, `project.load` gives the logic of the notebooks it reads, so one
`export_lineage` call draws them together; the files go in the Table folder's lineage/, named
by the time and the table, beside the ones before.

## When you'd use it

Whenever a table's logic changes, and whenever someone asks where one of its numbers comes
from. [Lineage of a pipeline across Saved tables](#lineage_of_a_pipeline_across_saved_tables)
draws writes made in one notebook; in a Project, each Saved table's writes sit in its own
notebook, and this is how one notebook draws another's.

## Steps

### Make two Saved tables, one reading the other

These steps need a Project with two filled-in Table notebooks: mart.daily_job_runs, each job's
runs a day, read from `ops.job_runs`, and mart.jobs_by_runs, read from it, how many jobs ran
once, twice and so on each day. [Add a Saved table](#add_a_saved_table) makes one, step by
step; this page does its steps for both in one function, `add_table`, so the steps below start
from two notebooks ready to run:

>>> import json
>>> from pathlib import Path
>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and send.py. Next: write your send in send.py.
>>> project.add_references(["ops.job_runs"], send=example_database.send)
Wrote references/ops__job_runs.py: fill in its TODO lines.
>>> def add_table(name, columns, key, filled_in):
...     project.new_table(name)
...     stem = name.replace(".", "__")
...     variable = name.split(".")[1]
...     Path(f"references/{stem}.py").write_text(
...         "from sqlglot_composer import Table\\n\\n"
...         f"{variable} = Table({name!r}, columns={columns!r}, date_partition='dt',\\n"
...         f"    key={key!r}, location='/data/your_team/tables')\\n", encoding="utf-8")
...     path = Path(f"tables/{stem}/{stem}.ipynb")
...     notebook = json.loads(path.read_text(encoding="utf-8"))
...     for cell in notebook["cells"]:
...         if cell["cell_type"] == "code":
...             for placeholder, value in filled_in.items():
...                 cell["source"] = [line.replace(placeholder, value)
...                                   for line in cell["source"]]
...     path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
>>> add_table("mart.daily_job_runs", {"job_id": "bigint", "runs": "bigint", "dt": "string"},
...           ["job_id", "dt"],
...           {"<SOURCE_NAME>": "ops__job_runs", "<SOURCE_TABLE>": "job_runs",
...            "<DATE_PARTITION>": "dt", "<KEY_COLUMN>": "job_id", "<COUNT_NAME>": '"runs"',
...            "<DAY>": '"2026-09-24"'})
>>> add_table("mart.jobs_by_runs", {"runs": "bigint", "jobs": "bigint", "dt": "string"},
...           ["runs", "dt"],
...           {"<SOURCE_NAME>": "mart__daily_job_runs", "<SOURCE_TABLE>": "daily_job_runs",
...            "<DATE_PARTITION>": "dt", "<KEY_COLUMN>": "runs", "<COUNT_NAME>": '"jobs"',
...            "<DAY>": '"2026-09-24"'})

### Export one table's Lineage

Cell 4 of a Table notebook exports its table's Lineage. Here, `project.load` gives
mart.daily_job_runs' logic, as the notebook's own cell 2 does when it runs. Put the write in a
variable with a meaningful name first: the Lineage names each Statement after the variable
that holds it, and one passed straight in is named statement_1.

>>> daily_job_runs_logic = project.load("mart.daily_job_runs")
>>> write_daily_job_runs = daily_job_runs_logic.write_day("2026-09-24")
>>> html_file, markdown_file = export_lineage(write_daily_job_runs)
>>> markdown_file.relative_to(Path.cwd()).as_posix()
'tables/mart__daily_job_runs/lineage/20260925-090000-mart__daily_job_runs.md'

The write fills a table that has a Table folder, so its two files go in that folder's
lineage/, named by the time, `20260925-090000` for 09:00:00 on 2026-09-25, and the table. Each
export gets a new pair, so lineage/ keeps every one before: the table's history, oldest first,
to compare when its logic changes.

### Draw a table with the tables it reads

mart.jobs_by_runs reads mart.daily_job_runs, so its Lineage alone would stop there, with
nothing behind it. Its notebook draws both: cell 4 loads the logic of the table it reads, and
passes both writes, the writer's first. Jupyter runs a notebook in its own folder, so this page
moves there first, as opening the notebook would:

>>> import os
>>> os.chdir("tables/mart__jobs_by_runs")
>>> jobs_by_runs_logic = project.load("mart.jobs_by_runs")
>>> write_jobs_by_runs = jobs_by_runs_logic.write_day("2026-09-24")
>>> html_file, markdown_file = export_lineage(write_daily_job_runs, write_jobs_by_runs)
>>> markdown_file.name
'20260925-090000-mart__jobs_by_runs.md'

The files go in this Table folder's lineage/, named for its own table, mart.jobs_by_runs: one
of the writes fills it, and the notebook works in its folder. The Markdown file, shown above,
has a section for each write. The second's first line says it reads mart.daily_job_runs,
written by write_daily_job_runs above, so the tree of its `"jobs"` count goes on through the
Saved table, back to `ops.job_runs`.

In the notebook itself, cell 1 has already set DAY and cell 2 defined the table's own
write_day, so cell 4 only loads the tables it reads. The starter Example project's
mart.team_day notebook draws three tables this way.

`project.load` works from any notebook of the Project: it finds the Project's folder by
looking up from the folder you're working in, and runs the named notebook's logic cell there.

## Check it worked

Each Table folder's lineage/ holds its pair:

>>> sorted(path.name for path in Path("lineage").iterdir())
['20260925-090000-mart__jobs_by_runs.html', '20260925-090000-mart__jobs_by_runs.md']
>>> sorted(path.name for path in Path("../mart__daily_job_runs/lineage").iterdir())
['20260925-090000-mart__daily_job_runs.html', '20260925-090000-mart__daily_job_runs.md']

The reading table's Lineage reaches back through the Saved table it reads:

>>> text = markdown_file.read_text(encoding="utf-8")
>>> [line for line in text.splitlines() if line.startswith("## ")]
['## Graph', '## write_daily_job_runs', '## write_jobs_by_runs']
>>> "written by write_daily_job_runs above" in text
True
>>> "ops.job_runs" in text
True

## Common mistakes

### Exporting two tables from the Project's folder

Exported from the Project's own folder, two writes of two different tables belong to no one
Table folder, so the files go in a lineage/ folder where you are, named as
[Lineage of one Statement](#lineage_of_one_statement) describes:

>>> os.chdir("../..")
>>> html_file, markdown_file = export_lineage(write_daily_job_runs, write_jobs_by_runs)
>>> markdown_file.relative_to(Path.cwd()).as_posix()
'lineage/20260925-090000_1a2b3c4_lineage_notebook_write_daily_job_runs__write_jobs_by_runs.md'

Export from the notebook of the table that reads the others, so its history stays in its own
Table folder.

### Loading a table that has no Table folder

`project.load` runs the notebook in a table's Table folder. A table the Project has no Table
folder for, such as one of the tables it only reads, is refused:

>>> project.load("ops.job_runs")
Traceback (most recent call last):
...
FileNotFoundError:
  What happened:  project.load("ops.job_runs"): there is no tables/ops__job_runs/ops__job_runs.ipynb.
...

Load only the Project's Saved tables, by the names `project.new_table` made them with. A table
the Project only reads has no write to draw: its columns show as the start of each tree.

## Next

- Each section of a Lineage, step by step: [Lineage of one Statement](#lineage_of_one_statement).
- Draw several writes made in one notebook:
  [Lineage of a pipeline across Saved tables](#lineage_of_a_pipeline_across_saved_tables).
- Compare a table's Lineage before and after a change:
  [Review a change with Lineage](#review_a_change_with_lineage).
- Write every table's day in that same order: [Add a Saved table](#add_a_saved_table).
- The gallery's [`export_lineage`](examples.html#export_lineage) entry.
"""
