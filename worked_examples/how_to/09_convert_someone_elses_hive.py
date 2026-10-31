"""Convert someone else's Hive

For: Getting started

## Goal

Turn scripts of Hive someone else wrote, with their temporary tables, their FROMs with several
INSERTs and their incremental INSERTs, into your own code: a Saved table in your Dev Database
for each table the scripts write, each notebook's logic building the same query from the
Toolbox's functions, compared with the table it copies and then promoted to your Prod
Database. That is a Conversion, and the convert Workflow takes you through it, step by step.
What no Toolbox function writes yet stays Hive, at the smallest size it can, so you get the rest
converted rather than none of it.

## When you'd use it

When you inherit Hive that works but that you can't maintain: a nightly job another team
wrote, a folder of scripts that has grown for years. Converted, the Guards check it, Lineage
traces it, and you change it in one place, dev, before promoting it.

It needs [Start a Project](#start_a_project) and [Save a table](#save_a_table).

## Steps

### Start from the Project the story leaves

Work in your own Project. This page uses a copy of the Starter Example project, the one the
how-tos before this one build, whose Dev Database, DEV in admin/databases.py, is mart:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "starter", ".", dirs_exist_ok=True)
>>> from sqlglot_composer import example_database, project, run_execute, hive_settings
>>> from warehouse import query, execute

### Save the scripts

Save each script as it is, a .hql file beside the convert Workflow's notebook, in
admin/workflows/convert/, where it reads them. Here the ops team's two: the
nightly one keeps the day's failed runs in a temporary table, then counts the day's alerts two
ways from one FROM; the weekly one adds each failed job to a history the job reads itself:

The file `admin/workflows/convert/daily.hql`, after you save it:

    SET hive.exec.parallel=true;
    DROP TABLE IF EXISTS ops_reports.failed_runs;
    CREATE TEMPORARY TABLE ops_reports.failed_runs AS
    SELECT r.run_id, r.job_id, r.dt
    FROM ops.job_runs r
    WHERE r.dt = '2026-09-24' AND r.status = 'FAILED';
    FROM ops.run_alerts a
    INSERT OVERWRITE TABLE ops_reports.alerts_by_severity PARTITION (dt='2026-09-24')
      SELECT a.severity, COUNT(*) AS alerts WHERE a.dt = '2026-09-24' GROUP BY a.severity
    INSERT OVERWRITE TABLE ops_reports.alerted_runs PARTITION (dt='2026-09-24')
      SELECT a.run_id, COUNT(*) AS alerts WHERE a.dt = '2026-09-24' GROUP BY a.run_id;

The file `admin/workflows/convert/weekly.hql`, after you save it:

    CREATE TABLE IF NOT EXISTS ops_reports.fail_history (job_id BIGINT, fails BIGINT)
    PARTITIONED BY (dt STRING) STORED AS ORC;
    INSERT INTO TABLE ops_reports.fail_history PARTITION (dt='2026-09-24')
    SELECT f.job_id, COUNT(*) AS fails
    FROM ops_reports.failed_runs f
    WHERE f.job_id NOT IN (SELECT h.job_id FROM ops_reports.fail_history h WHERE h.dt = '2026-09-24')
    GROUP BY f.job_id;

### Convert them

Open admin/workflows/convert/convert.ipynb and fill in its names cell: the batch's name as
NAME, a plain lowercase one, the scripts as FILES, and DATABASE, the database of a table the
Hive names without one. Save it, and run its first step's cell, which is this call, from the
notebook's folder. `rename=` gives a table a name of your own in dev; left out,
ops_reports.fail_history would be mart.fail_history_ops_reports, its database at the end:

>>> import os
>>> os.chdir("admin/workflows/convert")  # where the notebook runs: this page stands in
>>> print(project.convert("ops_reports", files=["daily.hql", "weekly.hql"], query=query,
...                       database="ops", rename={"ops_reports.fail_history": "fail_history"}))
Converted ops_reports: ...
>>> os.chdir("../../..")  # back to the Project's folder, where the rest of this page runs

The scripts' order doesn't matter: the batch orders each statement by what reads what. Each
table the scripts write is a Saved table in mart, with its Table folder, its Table reference and
a checklist: the temporary table too, which the weekly script reads, so it is made first. The
FROM with two INSERTs gives each target a Saved table of its own. The DROP and the SET line
become nothing and the Session settings of the writes after them.
admin/workflows/convert/ops_reports/batch.md lists what each statement became:

>>> print(Path("admin/workflows/convert/ops_reports/batch.md").read_text(encoding="utf-8"))
# Batch ops_reports
...

Open tables/mart__alerted_runs_ops_reports/mart__alerted_runs_ops_reports.ipynb. Its logic
cell holds your code: the query's clauses, and create(), preview() and write().
mart.fail_history's stays Hive, whole, an Unchecked statement: its WHERE holds a query, NOT IN
(SELECT ...), which no Toolbox function writes yet, as its conversion/scan.md says. Its write
reads its own table, as an incremental INSERT does, so in dev it would start from nothing: its
notebook has seed() too, which copies the original's rows into it once, before its first
write.

### Decide each box

Each table's conversion/checklist.md has a box for each decision only you can make:

>>> print(Path("tables/mart__fail_history/conversion/checklist.md").read_text(encoding="utf-8"))
# Checklist: mart.fail_history
...

Fill in each Table reference's location=, the folder its files go in, which your platform
team names, and its Key, then tick each box. Three tables' checklists ask you to send the
original's SET line, hive.exec.parallel, before their write: it makes Hive faster and changes
no row, so tick it, and send it at work if you want it, as its box says. This page stands in
for your edits:

>>> for path in Path("references").glob("mart__*.py"):
...     text = path.read_text(encoding="utf-8")
...     if "location=None," in text:
...         _ = path.write_text(text.replace("location=None,", f'location="/data/mart.db/{path.stem}",'), encoding="utf-8")
>>> for path in Path("tables").glob("*/conversion/checklist.md"):
...     _ = path.write_text(path.read_text(encoding="utf-8").replace("- [ ] ", "- [x] "), encoding="utf-8")

`project.check()` names the batch's next step in the Workflow:

>>> print(project.check())
The next step ...

### Create, seed and write each table in dev

Steps 3 to 5 are calls to the warehouse, yours to run, each a cell of the Workflow's notebook.
At work they create each table in your Dev Database, seed mart.fail_history from the original,
and write each, in the order they read each other. Here execute is the Example database's,
which prints the first line of each and changes nothing:

>>> for table in project.batch_tables("ops_reports"):
...     run_execute(project.load(table).create(), execute)
execute: ...
>>> run_execute(hive_settings("dynamic_partitions"), execute)
execute: ...
>>> for table in project.batch_tables("ops_reports", seeded=True):
...     run_execute(project.load(table).seed(), execute)
execute: ...
>>> print(project.run_tables(tables=project.batch_tables("ops_reports"), execute=execute))
execute: INSERT OVERWRITE TABLE mart.failed_runs_ops_reports
1 of 4: mart.failed_runs_ops_reports         worked
...
4 of 4: mart.fail_history                    worked
Wrote 4 tables, in order.

### Compare each with its original

Step 6 compares each dev table's rows with the table it copies, on the latest Partition both
hold, and writes each result in its conversion/compare.md. The Example database holds no Dev
Database, so here each says it couldn't read its dev table; at work, once every table passes,
the batch is finished:

>>> print(project.compare_batch("ops_reports", query=query))
mart.alerted_runs_ops_reports: failed, couldn't compare: The Example database has no table 'mart.alerted_runs_ops_reports'.
mart.alerts_by_severity_ops_reports: failed, couldn't compare: The Example database has no table 'mart.alerts_by_severity_ops_reports'.
mart.fail_history: failed, couldn't compare: The Example database has no table 'mart.fail_history'.
mart.failed_runs_ops_reports: failed, couldn't compare: The Example database couldn't run this Hive: it has no table mart.failed_runs_ops_reports.

### Promote them

Once each table has passed, `project.promote` copies their code to your Prod Database, PROD in
admin/databases.py, each notebook reading the others' prod copies. Fill PROD in, as this page
stands in for your edit, and it refuses before each compare has passed, naming each table:

>>> databases = Path("admin/databases.py")
>>> _ = databases.write_text(databases.read_text(encoding="utf-8").replace(
...     '"<PROD_DATABASE>"', '"mart_prod"'), encoding="utf-8")
>>> try:
...     project.promote(project.batch_tables("ops_reports"))
... except ValueError as refused:
...     print(str(refused).strip().splitlines()[0])
What happened:  project.promote([...]) can't promote yet: mart.failed_runs_ops_reports: its compare hasn't passed; ...

At work, in admin/workflows/promote/promote.ipynb, name the dev tables and run its cells:

    project.promote(["mart.failed_runs_ops_reports", "mart.fail_history",
                     "mart.alerts_by_severity_ops_reports", "mart.alerted_runs_ops_reports"])

## Check it worked

Each table's conversion/compare.md starts "Passed:", `project.check()` names no step of the
batch, which is in admin/workflows/convert/finished/, and the promote Workflow writes each in
prod.

## Common mistakes

- **Converting one script at a time.** A table one script writes and another reads is made
  once, and read in dev, only when both are in one batch: give them together, with `files=`.
- **Leaving a box.** The Workflow waits on every box of every checklist: each is a decision
  only you can make, such as a table's folder or a seed.
- **Promoting before comparing.** promote refuses a table whose compare hasn't passed, so prod
  never gets rows that differ from the original's.

## Next

- [Follow a Workflow](#follow_a_workflow): every Workflow's steps, drawn and listed.
- [Hand-written Hive with your Table references](#hand_written_hive_with_your_table_references):
  the Unchecked pieces a Conversion leaves, and how to replace them.
"""  # noqa: E501 - the Hive it converts and the files it shows, line for line
