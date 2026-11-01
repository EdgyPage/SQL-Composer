"""Convert someone else's Hive

For: Getting started

## Goal

Turn scripts of Hive someone else wrote, with their temporary tables, their FROMs with several
INSERTs and their incremental INSERTs, into your own code. Hive is the SQL your warehouse runs.
You end with a Saved table, a real table your own Statements write, in your Dev Database for
each table the scripts write; your Dev Database is the database where you may create and write
tables of your own. Each Saved table's notebook builds the same query from the Toolbox's
functions, is compared with the table it copies, its original, and is then promoted to your
Prod Database, the database others read your finished tables from. That is a Conversion, and
the convert Workflow, an ordered list of steps in a notebook of its own, takes you through it,
step by step. What no Toolbox function writes yet stays Hive, at the smallest size it can, so
you get the rest converted rather than none of it.

## When you'd use it

- If you inherit Hive that works but that you can't maintain, such as a nightly job another
  team wrote or a folder of scripts that has grown for years, convert it as the steps below
  do. Converted, the Guards check it, Lineage traces it, and you change it in one place, dev,
  before promoting it.
- If one script writes a table another reads, convert both in one batch, as step 3 does.
- If you have no Project yet, do [Start a Project](#start_a_project) first.
- If you have not yet written a Saved table of your own, read [Save a table](#save_a_table)
  first.

## Steps

### 1. Start from the Project the story leaves

Goal: a Project to convert into. A Project is your folder of scripts at work, in the Toolbox's
fixed layout. Work in your own Project. This page uses a copy of the Starter Example project,
the one the how-tos before this one build, whose Dev Database, DEV in admin/databases.py, is
mart (yours is any database you own, such as mart_dev):

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "starter", ".", dirs_exist_ok=True)
>>> from sqlglot_composer import example_database, project, run_execute, hive_settings
>>> from warehouse import query, execute

Done when `from warehouse import query, execute` runs without an error. Then step 2.

### 2. Save the scripts

Goal: the scripts where the convert Workflow reads them. Save each script as it is, a .hql
file beside the convert Workflow's notebook, in admin/workflows/convert/. Here the ops team's
two: the nightly one keeps the day's failed runs in a temporary table, then counts the day's
alerts two ways from one FROM; the weekly one adds each failed job to a history the job reads
itself:

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

Done when both .hql files are in admin/workflows/convert/. Then step 3.

### 3. Convert them

Goal: your own code for each table the scripts write. Open
admin/workflows/convert/convert.ipynb and fill in its names cell: the batch's name as NAME, a
plain lowercase one, the scripts as FILES, and DATABASE, the database of a table the Hive names
without one. A batch is the scripts converted together by one Conversion. Save the cell, and
run the first step's cell, which is this call, from the notebook's folder. `rename=` gives a
table a name of your own in dev; left out, ops_reports.fail_history would be
mart.fail_history_ops_reports, its database at the end:

>>> import os
>>> os.chdir("admin/workflows/convert")  # where the notebook runs: this page stands in
>>> print(project.convert("ops_reports", files=["daily.hql", "weekly.hql"], query=query,
...                       database="ops", rename={"ops_reports.fail_history": "fail_history"}))
Converted ops_reports: ...
>>> os.chdir("../../..")  # back to the Project's folder, where the rest of this page runs

Done when `project.convert` prints `Converted ops_reports: ...`. Then step 4.

### 4. Read what each statement became

Goal: know what the Conversion made of each statement. The scripts' order doesn't matter: the
batch orders each statement by what reads what. Each table the scripts write is a Saved table
in mart, with its Table folder, the folder that holds everything about one Saved table, its
Table reference, the file that describes the table's columns, Partitions and Key, and its
Decisions to answer. The one exception is the temporary table: a Staging table, a table a
script writes only so a statement after it can read it. The weekly script reads it, so it is
folded into fail_history, its query a Derived table there, a named query that lives only
inside the Statement that reads it, and never made a table of its own. To keep it a table
instead, give staging={"ops_reports.failed_runs": "keep"}. The FROM with two INSERTs gives each
target a Saved table of its own. The DROP becomes nothing, and the SET line becomes the Session
settings of the writes after it: a Session setting is a Hive SET sent before a Statement.
admin/workflows/convert/ops_reports/batch.md lists what each statement became:

>>> print(Path("admin/workflows/convert/ops_reports/batch.md").read_text(encoding="utf-8"))
# Batch ops_reports
...

Open tables/mart__alerted_runs_ops_reports/mart__alerted_runs_ops_reports.ipynb. Its logic
cell holds your code: the query's clauses, and create(), preview() and write().
mart.fail_history's stays Hive, whole, an Unchecked statement, Hive text run through the
Toolbox that no Guard looks inside: its WHERE holds a query, NOT IN (SELECT ...), which no
Toolbox function writes yet, as its conversion/scan.md says. Its write reads its own table, as
an incremental INSERT does, so in dev it would start from nothing: its notebook has seed() too,
which copies the original's rows into it once, before its first write.

Done when batch.md starts `# Batch ops_reports` and you have read what each statement became.
Then step 5.

### 5. Read each table's open Decisions

Goal: know what only you can decide. What only you can decide of a table is a Decision: here
each table's location=, the folder its files go in, which your platform team names, and its
Key, the columns whose values name one row. Each table's conversion/checklist.md lists its
open Decisions, and project.check() names each one:

>>> checklist = Path("tables/mart__fail_history/conversion/checklist.md")
>>> text = checklist.read_text(encoding="utf-8")  # -> str
>>> print(text.split("Open Decisions")[1].split("## Notes")[0].strip())
- key: the columns whose values name one row, or None when none do, in
  references/mart__fail_history.py
- location: the folder its files go in, in references/mart__fail_history.py

Done when you have the list of each table's open Decisions. Then step 6.

### 6. Answer each Decision in the decisions cell

Goal: an answer for each open Decision. Write each answer in the convert Workflow notebook's
decisions cell, DECISIONS, by each table's name as project.check() writes it. You open no Table
reference, and tick nothing. "key": None says no columns name one row. A Key project.convert
could work out of a table's query, as GROUP BY a.severity gives one, is proposed in its Table
reference already, marked # proposed, and its checklist says so: answer "key" only where one is
open or wrong. A TODO line left, such as does_not_add_up=, waits on nothing. This page stands in
for the decisions cell:

>>> DECISIONS = {table: {"location": f"/data/mart.db/{table.split('.')[1]}"}
...              for table in project.batch_tables("ops_reports")}

fail_history's write reads its own table, so no Key could be worked out of it: its Key is
open. Here the answer is that no columns name one row of it.

>>> DECISIONS["mart.fail_history"]["key"] = None

Two tables write the Partition dt from a query that doesn't say its type, so each one's dt is
a guessed type to answer too: the day as text, "string". A Partition is a slice of a table: the
rows that share one value of each column it is partitioned by.

>>> for table in ["mart.alerts_by_severity_ops_reports", "mart.alerted_runs_ops_reports"]:
...     DECISIONS[table]["types"] = {"dt": "string"}

Done when DECISIONS holds a location for each table, a key for mart.fail_history, and a dt
type for the other two. Then step 7.

### 7. Write each answer into its Table reference

Goal: each Decision made in the table's files. Run the Workflow's next step, which writes each
answer into the table's Table reference:

>>> print(project.write_decisions(DECISIONS))
Wrote 2 answers into references/mart__alerts_by_severity_ops_reports.py.
mart.alerts_by_severity_ops_reports: 2 TODO lines left in references/mart__alerts_by_severity_ops_reports.py, which wait
on nothing: fill each in when you like.
Each Decision of mart.alerts_by_severity_ops_reports is made.
Wrote 2 answers into references/mart__alerted_runs_ops_reports.py.
mart.alerted_runs_ops_reports: 2 TODO lines left in references/mart__alerted_runs_ops_reports.py, which wait
on nothing: fill each in when you like.
Each Decision of mart.alerted_runs_ops_reports is made.
Wrote 2 answers into references/mart__fail_history.py.
mart.fail_history: 2 TODO lines left in references/mart__fail_history.py, which wait
on nothing: fill each in when you like.
Each Decision of mart.fail_history is made.

`project.check()` names the batch's next step in the Workflow, the first call to the
warehouse:

>>> print(project.check())
The next step of each Workflow you have started; project.do_next() runs the steps it can for you:
  admin/workflows/convert/convert.ipynb, ops_reports: 4. Create each table in dev. ...

Done when each table says `Each Decision of ... is made.` and `project.check()` names
`4. Create each table in dev`. Then step 8.

### 8. Create each table in dev

Goal: each Saved table made in your Dev Database. The Workflow's steps 4 to 6 are calls to the
warehouse, yours to run, each a cell of the Workflow's notebook. At work, step 4 creates each
table in your Dev Database. Here execute is the Example database's, which prints the first line
of each Hive it is given and changes nothing:

>>> for table in project.batch_tables("ops_reports"):
...     run_execute(project.load(table).create(), execute)
execute: ...

Done when execute has been given each table's create. Then step 9.

### 9. Seed the table that reads itself

Goal: mart.fail_history starts from the original's rows. The Workflow's step 5 sends the
Session settings for dynamic Partitions, then seeds mart.fail_history from the original, once:

>>> run_execute(hive_settings("dynamic_partitions"), execute)
execute: ...
>>> for table in project.batch_tables("ops_reports", seeded=True):
...     run_execute(project.load(table).seed(), execute)
execute: ...

Done when execute has been given the seed. Then step 10.

### 10. Write each table in dev

Goal: each Saved table's rows in dev. The Workflow's step 6 writes each table, in the order
they read each other. It sends each table's SET lines, the original's, before its write: here
hive.exec.parallel, which makes Hive faster and changes no row:

>>> print(project.run_tables(tables=project.batch_tables("ops_reports"), execute=execute))
execute: SET hive.exec.parallel=true
execute: INSERT OVERWRITE TABLE mart.alerts_by_severity_ops_reports PARTITION(dt = '2026-09-24')
1 of 3: mart.alerts_by_severity_ops_reports  worked
...
3 of 3: mart.fail_history                    worked
Wrote 3 tables, in order.

Done when it prints `Wrote 3 tables, in order.` Then step 11.

### 11. Compare each with its original

Goal: proof that each dev table gives its original's rows. The Workflow's step 7 compares each
dev table's rows with the table it copies, on the latest Partition both hold, and writes each
result in its conversion/compare.md. The Example database holds no Dev Database, so here each
says it couldn't read its dev table; at work, once every table passes, the batch is finished:

>>> print(project.compare_batch("ops_reports", query=query))
mart.alerted_runs_ops_reports: failed, couldn't compare: The Example database has no table 'mart.alerted_runs_ops_reports'.
mart.alerts_by_severity_ops_reports: failed, couldn't compare: The Example database has no table 'mart.alerts_by_severity_ops_reports'.
mart.fail_history: failed, couldn't compare: The Example database has no table 'mart.fail_history'.

Done when each table's line says it passed, at work. Then step 12.

### 12. Promote them

Goal: each table's code in your Prod Database. Once each table has passed, `project.promote`
copies their code to your Prod Database, PROD in admin/databases.py, each notebook reading the
others' prod copies. Fill PROD in, as this page stands in for your edit. Before each compare
has passed, promote refuses, naming each table:

>>> databases = Path("admin/databases.py")
>>> _ = databases.write_text(databases.read_text(encoding="utf-8").replace(
...     '"<PROD_DATABASE>"', '"mart_prod"'), encoding="utf-8")
>>> try:
...     project.promote(project.batch_tables("ops_reports"))
... except ValueError as refused:
...     print(str(refused).strip().splitlines()[0])
What happened:  project.promote([...]) can't promote yet: mart.alerts_by_severity_ops_reports: its compare hasn't passed; ...

At work, in admin/workflows/promote/promote.ipynb, name the dev tables and run its cells:

    project.promote(["mart.fail_history", "mart.alerts_by_severity_ops_reports",
                     "mart.alerted_runs_ops_reports"])

Done when the promote Workflow names its next step for the three tables, at work. Then check
it worked, below.

## Check it worked

Before you go on, check that:

- each result in each table's conversion/compare.md says "Passed:";
- `project.check()` names no step of the batch;
- the batch is in admin/workflows/convert/finished/;
- the promote Workflow has written each table in prod.

## Common mistakes

### Converting one script at a time

A table one script writes and another reads is made once, and read in dev, only when both are
in one batch. Give the scripts together, with `files=`.

### Leaving a Decision open

The Workflow waits on each table's open Decisions, each one only you can make, such as a
table's folder. Answer each one project.check() names in the decisions cell.

### Promoting before comparing

promote refuses a table whose compare hasn't passed, so prod never gets rows that differ from
the original's. Compare each table, and fix it in dev until its compare passes, then promote.

## Next

- [Follow a Workflow](#follow_a_workflow): every Workflow's steps, drawn and listed.
- [Hand-written Hive with your Table references](#hand_written_hive_with_your_table_references):
  the Unchecked pieces a Conversion leaves, and how to replace them.
"""  # noqa: E501 - the Hive it converts and the files it shows, line for line
