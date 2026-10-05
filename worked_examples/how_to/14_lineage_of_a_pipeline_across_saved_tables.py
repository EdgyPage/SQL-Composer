"""Lineage of a pipeline across Saved tables

For: Getting started

## Goal

Follow each column of a pipeline's last Saved table all the way back to the tables it starts
from, through every Saved table in between. You pass `export_lineage` every write of the
pipeline at once, and it draws them as one Lineage, joined at each Saved table one write fills
and the next one reads.

## When you'd use it

When a number comes from a Saved table that another Statement filled. The Lineage of the last
write alone stops at the Saved table it reads, which tells you nothing of how that table's
numbers were made. Exported together, the writes show the whole way, from `ops.job_runs` to
the team counts. Export it whenever the pipeline's steps change, and keep it beside them.

## Steps

### Import the Toolbox and describe the two Saved tables

The pipeline is the one from [Run a daily pipeline](#run_a_daily_pipeline): mart.daily_job_runs
counts each job's runs per day, and mart.team_day adds those counts up per team.

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs
>>> jobs = example_database.jobs
>>> daily_job_runs = Table(
...     "mart.daily_job_runs",
...     columns={"job_id": "bigint", "runs": "bigint", "failed_runs": "bigint",
...              "dt": "string"},
...     date_partition="dt",
...     key=["job_id", "dt"],
... )
>>> team_day = Table(
...     "mart.team_day",
...     columns={"team": "string", "runs": "bigint", "failed_runs": "bigint", "dt": "string"},
...     date_partition="dt",
...     key=["team", "dt"],
... )

### Put each write in a variable of its own

The Lineage names each Statement after the variable that holds it, so give each write a
variable with a meaningful name. These are one day's two writes:

>>> write_daily_job_runs = statement(
...     INSERT_OVERWRITE(daily_job_runs),
...     SELECT(
...         job_runs.job_id,
...         AS(count_rows(), "runs"),
...         AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
...     ),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
>>> write_team_day = statement(
...     INSERT_OVERWRITE(team_day),
...     SELECT(
...         jobs.team,
...         AS(sum_of(daily_job_runs.runs), "runs"),
...         AS(sum_of(daily_job_runs.failed_runs), "failed_runs"),
...     ),
...     FROM(daily_job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, daily_job_runs.job_id)),
...     WHERE(equals(daily_job_runs.dt, "2026-09-24")),
...     GROUP_BY(jobs.team),
... )

Both writes' Hive, each headed by its variable's name:

>>> text = show_hive(write_daily_job_runs, write_team_day)
-- 1 of 2: write_daily_job_runs
INSERT OVERWRITE TABLE mart.daily_job_runs PARTITION(dt = '2026-09-24')
SELECT
  job_runs.job_id,
  COUNT(*) AS runs,
  COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24'
GROUP BY
  job_runs.job_id;
<BLANKLINE>
-- 2 of 2: write_team_day
INSERT OVERWRITE TABLE mart.team_day PARTITION(dt = '2026-09-24')
SELECT
  jobs.team,
  SUM(daily_job_runs.runs) AS runs,
  SUM(daily_job_runs.failed_runs) AS failed_runs
FROM mart.daily_job_runs AS daily_job_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = daily_job_runs.job_id
WHERE
  daily_job_runs.dt = '2026-09-24'
GROUP BY
  jobs.team;

### Export them together

Pass every write of the pipeline, each as its own argument. `to=` gives the files a fixed name,
so each export replaces the last:

>>> html_file, markdown_file = export_lineage(write_daily_job_runs, write_team_day,
...                                           to="lineage/pipeline.html")

The order you pass them in doesn't matter: `export_lineage` puts each write before the
Statements that read the Saved table it fills, which is also the order to run them in.

### Read the Markdown file, section by section

The Markdown file is shown in full above. Read it one heading at a time.

The title names both writes, in the order they run.

Graph is the whole pipeline as one Mermaid chart, shown here as text. Drawn in JupyterLab or
GitHub, it runs from the columns of `ops.job_runs` the job write uses, through the Saved table
mart.daily_job_runs, which the job write's outputs flow into and the team write reads from,
with `ops.jobs` joined, to mart.team_day. In the text, each table is a subgraph of its own,
and an arrow labelled `|day written|` runs from each write's WHERE to the Date partition of the
table it writes: the day in WHERE is the day written.

write_daily_job_runs is the first write's section. It says which Saved table it writes, then
its Calculated columns, `"runs"` and `"failed_runs"`, each with its tree, its Rows that count
and what one row stands for, then its Copied columns and its Hive.

write_team_day is the second write's section. Its first line says it reads the Saved table
mart.daily_job_runs, written by write_daily_job_runs above. Each tree now goes on through the
Saved table: the team's `"failed_runs"` is a sum of the Saved table's column
`daily_job_runs.failed_runs`, which write_daily_job_runs counted from `ops.job_runs.status`. So
the file answers "what counts as a failed run here?" in one place: a run whose status is
FAILED.

Rows that count, under each of the team write's columns, lists the conditions that decide
which rows of the Saved table count: the team write's day, and its match on job_id with
`ops.jobs`. The job write's day isn't listed again: it is the day it writes, which the chart
shows as day written. Had the job write kept only some runs, say with a condition on their
status, that condition would be listed here too, since it decides which runs the team counts
add up.

Hive as submitted, in each section, is the Hive `run` sends for that write.

### Open the HTML page

Open lineage/pipeline.html in your browser. Click a column of mart.team_day, and the page
lights up its whole path: through mart.daily_job_runs, back to `ops.job_runs`, with every
condition on the way. Hide `ops.jobs` with its control to see only the counts' path.

## Check it worked

The Markdown file has a section for each write, in the order they run:

>>> text = markdown_file.read_text(encoding="utf-8")
>>> [line for line in text.splitlines() if line.startswith("## ")]
['## Graph', '## write_daily_job_runs', '## write_team_day']

The team write's section knows where its Saved table's numbers come from, and the file
reaches back to `ops.job_runs`:

>>> "written by write_daily_job_runs above" in text
True
>>> "ops.job_runs.status" in text
True

## Common mistakes

### Exporting the last write on its own

The team write alone draws mart.daily_job_runs as a table like any other, with nothing behind
it:

>>> team_only_html, team_only_markdown = export_lineage(write_team_day,
...                                                     to="lineage/team_only.html")
>>> "ops.job_runs" in team_only_markdown.read_text(encoding="utf-8")
False

Its trees stop at mart.daily_job_runs: nothing says how the job counts were made. Pass every
write of the pipeline, since `export_lineage` follows a Saved table only between the
Statements it is given.

### Passing the list of writes as one argument

`show_hive` takes a list, but `export_lineage` takes each Statement as its own argument, and
refuses a list:

>>> pipeline = [write_daily_job_runs, write_team_day]
>>> export_lineage(pipeline, to="lineage/pipeline.html")
Traceback (most recent call last):
...
TypeError:
  What happened:  export_lineage was given [...], which isn't a Statement that reads a table.
...

Name each write, as above, or put a `*` before the list, `export_lineage(*pipeline,
to="lineage/pipeline.html")`, which hands each Statement in it on as its own argument.

### Passing the create steps too

A day's list of steps from [Run a daily pipeline](#run_a_daily_pipeline) starts with
`create_table` Statements. They read no table, so they have no Lineage, and are refused. The
message shows the create Statement it was given as `<Statement - print(to_hive(s)) shows it>`:

>>> create_daily_job_runs = create_table(daily_job_runs, may_exist=True)
>>> export_lineage(create_daily_job_runs, write_daily_job_runs, write_team_day,
...                to="lineage/pipeline.html")
Traceback (most recent call last):
...
TypeError:
  What happened:  export_lineage was given <Statement - print(to_hive(s)) shows it>, which isn't a Statement that reads a table.
...

Pass only the writes.

## Next

- The sections of one Statement's Lineage, step by step:
  [Lineage of one Statement](#lineage_of_one_statement).
- Run the same two writes every day, in order: [Run a daily pipeline](#run_a_daily_pipeline).
- The gallery's [`export_lineage`](examples.html#export_lineage) entry.
"""
