"""Lineage of one Statement

For: Getting started

## Goal

See where each column of a Statement's result comes from: the table columns that feed it,
the conditions that decide which rows count towards it, and the Hive that ran.
`export_lineage` writes this Lineage as two files: an HTML page to explore in your browser,
and a Markdown file to read anywhere, even where no script runs.

## When you'd use it

- Before you hand someone a number, so you can answer "where does this come from?" by
  pointing at the files.
- When a number looks wrong: the Markdown file lists every condition that decides which rows
  count towards it, from every step, in one place.
- When you review a Statement someone else wrote, or one you wrote months ago.
- To keep beside your scripts, so a reviewer sees what each column is made of without reading
  the Python.

## Steps

### Import the Toolbox and build a Statement

The Statement here counts each team's runs, and their failed runs, over two days. It reads two
tables, `ops.job_runs` and `ops.jobs`, and works out two columns:

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs
>>> jobs = example_database.jobs
>>> team_runs = statement(
...     SELECT(
...         jobs.team,
...         AS(count_rows(), "runs"),
...         AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...     ),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(jobs.team),
... )
>>> run(team_runs, send=example_database.send)
      team  runs  failed_runs
0     data     4            0
1  finance     5            2

### Export its Lineage

`export_lineage` takes the Statement itself, not its Hive or its result. It writes the two
files and gives back their paths, the HTML page first:

>>> html_file, markdown_file = export_lineage(team_runs)

Nothing is sent to the warehouse: the Lineage is worked out from the Statement alone, so it
works the same on the Example database and at work.

The files go in a folder named lineage, beside your notebook or script; here, in the folder
this how-to runs in. Each file's name says when it was written, from which commit of your
scripts, by which notebook, and for which Statement:

>>> markdown_file.name
'..._lineage_notebook_team_runs.md'

- First the time, `20260925-090000` for 09:00:00 on 2026-09-25.
- Then your scripts' git commit, so you know which version of them it describes. Outside a git
  repository, it is `"nogit"`.
- Then the notebook's name. In JupyterLab, it is your notebook's own name; here, where the
  steps don't run in a saved notebook, it is `"notebook"`.
- Last, the name of the variable that holds the Statement, `team_runs`. So put a Statement in
  a variable with a meaningful name before you export it: passed straight in, as
  `export_lineage(statement(...))`, its files would be named `"statement"`.

Each export without `to=` gets a new name, so the files of earlier exports stay as they were.

### Read the Markdown file

The Markdown file is shown in full above. Read it from the top, one heading at a time.

The title names the Statement, and a short paragraph under it says what the chart's arrows
mean.

Graph is a chart written in Mermaid, a text format for charts. JupyterLab, GitHub and many
editors draw it; on this page it shows as text. Each table read is a group, a subgraph in Mermaid,
holding only the columns the Statement uses: `ops.jobs` and `ops.job_runs`. The group
team_runs holds the Statement's three output columns, each with what it is made of, and the
group of filters holds its WHERE and its JOIN's `ON=`. A solid arrow, `-->`, carries a value,
such as `ops.jobs.team` into `"team"`. A dotted arrow, `-.->`, carries a column into a
condition, or a condition to the rows it decides.

team_runs, the Statement's own section, starts with Calculated columns: each column that is
worked out rather than copied, here `"runs"` and `"failed_runs"`. For each, it says the Toolbox
call and the Hive it becomes, then three things:

- A small tree from the column down to the table columns it reads: `"failed_runs"` reads
  `ops.job_runs.status`, and `"runs"` reads no column, since it counts rows.
- Rows that count: every condition that decides which rows are counted, here the two days in
  WHERE and the match between the two tables in JOIN's `ON=`. When a number looks wrong, look
  here first.
- One value for each different `jobs.team`: what one row of the result stands for, from
  `GROUP_BY`.

Copied columns is a table of the columns copied as they are: `"team"` comes from
`ops.jobs.team`.

Hive as submitted is the Hive `run` sends, exactly as `to_hive` gives it.

The last line says when the file was made, from which commit, and with which Toolbox version.

### Open the HTML page

The HTML file is shown above by name; open it in your browser, from the lineage folder. It
draws the same Lineage as boxes and arrows, from the table columns on the left to the
Statement's columns on the right, with each condition as a dashed box. Click a box to light up
its whole path: every column it comes from and every condition that decides its rows. Its
controls expand, collapse or hide each table, and switch to a flowchart grouped by table. Below
the drawing, it holds the same sections as the Markdown file. The page needs no internet: all
it needs is inside the one file.

### Give the files a fixed name with to=

`to=` names the HTML file instead, and the Markdown file goes beside it, with the same name
ending in .md:

    export_lineage(team_runs, to="lineage/team_runs.html")

That writes lineage/team_runs.html and lineage/team_runs.md, and each export replaces the
last. Use a fixed name for the Lineage you keep with your scripts in git: one pair of files per
Statement, whose changes show up beside the change to the Statement. Leave `to=` out to keep
every export side by side, as when you compare a Statement before and after a change.

## Check it worked

Both files were written, in the lineage folder:

>>> html_file.exists(), markdown_file.exists()
(True, True)
>>> markdown_file.parent.name
'lineage'

Every column the Statement works out has a heading of its own under Calculated columns:

>>> text = markdown_file.read_text(encoding="utf-8")
>>> [line for line in text.splitlines() if line.startswith("#### ")]
['#### `runs`', '#### `failed_runs`']

## Common mistakes

### Passing the Hive, or the result, instead of the Statement

`export_lineage` works out the Lineage from the Statement, and refuses anything else, such as
the text `to_hive` gives:

>>> export_lineage(to_hive(team_runs))
Traceback (most recent call last):
...
TypeError:
  What happened:  export_lineage was given "SELECT...", which isn't a Statement that reads a table.
...

Pass the Statement: `export_lineage(team_runs)`.

### A to= that doesn't end in .html

`to=` names the HTML page. The Markdown file's name is made from it, so `to=` can't name the
Markdown file:

>>> export_lineage(team_runs, to="lineage/team_runs.md")
Traceback (most recent call last):
...
ValueError:
  What happened:  export_lineage(..., to='lineage/team_runs.md'): to= must name an .html file.
...

## Next

- Follow a column through several Statements and the Saved tables between them:
  [Lineage of a pipeline across Saved tables](#lineage_of_a_pipeline_across_saved_tables).
- See what a change to a Building block does, by its Lineage before and after:
  [Review a change with Lineage](#review_a_change_with_lineage).
- Build a Statement from named steps, which its Lineage names too:
  [Reusable Derived tables](#reusable_derived_tables).
- The gallery's [`export_lineage`](examples.html#export_lineage) entry, and its
  [Worked example of a job in steps](examples.html#step_by_step), whose Statement reads
  Derived tables.
"""
