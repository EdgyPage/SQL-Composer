"""Convert someone else's Hive

For: Getting started

## Goal

Turn scripts of Hive someone else wrote, with their temporary tables, their FROMs with several
INSERTs, their incremental INSERTs and their Script tags, into your own code. Hive is the SQL
your warehouse runs. You end with a Saved table, a real table your own Statements write, in your
Dev Database for each table the scripts write; your Dev Database is the database where you may
create and write tables of your own. Each Saved table's notebook builds the same query from the
Toolbox's functions, is compared with the table it copies, its original, and is then promoted to
your Prod Database, the database others read your finished tables from. That is a Conversion,
and the convert Workflow, an ordered list of steps in a notebook of its own, takes you through
it, step by step. What no Toolbox function writes yet stays Hive, at the smallest size it can,
so you get the rest converted rather than none of it.

## When you'd use it

- If you inherit Hive that works but that you can't maintain, such as a nightly job another
  team wrote or a folder of scripts that has grown for years, convert it as the steps below
  do. Converted, the Guards check it, Lineage traces it, and you change it in one place, dev,
  before promoting it.
- If one script writes a table another reads, convert both in one batch, as step 3 does.
- If a Script tag stands for a day that changes each run, such as the latest day a table
  holds, answer it with a Run value, the value a function of yours gives at each write, as
  step 8 does.
- If a table that reads itself has years of rows you don't need, limit its seed, the one copy
  of the original's rows, by Partition, as step 6 does.
- If several tables share an answer, such as the folder their files go under, give it once
  under "all_tables", as step 6 does.
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
>>> from sqlglot_composer import example_database, project, run_execute, hive_settings, show_hive
>>> from warehouse import query, execute

Done when `from warehouse import query, execute` runs without an error. Then step 2.

### 2. Save the scripts

Goal: the scripts where the convert Workflow reads them. Save each script as it is, a .hql
file beside the convert Workflow's notebook, in admin/workflows/convert/. Here the ops team's
two: the nightly one keeps the day's failed runs in a temporary table, then counts the day's
alerts two ways from one FROM; the weekly one adds each failed job to a history the job reads
itself. The nightly one holds a Script tag, `<PARM="RUN_DAY"/>`: the scheduler that runs the
script puts the day in its place before Hive reads it. Its author tagged only that one day; the
others are typed in, and the converted code keeps them as they are:

The file `admin/workflows/convert/daily.hql`, after you save it:

    SET hive.exec.parallel=true;
    DROP TABLE IF EXISTS ops_reports.failed_runs;
    CREATE TEMPORARY TABLE ops_reports.failed_runs AS
    SELECT r.run_id, r.job_id, r.dt
    FROM ops.job_runs r
    WHERE r.dt = '2026-09-24' AND r.status = 'FAILED';
    FROM ops.run_alerts a
    INSERT OVERWRITE TABLE ops_reports.alerts_by_severity PARTITION (dt='2026-09-24')
      SELECT a.severity, COUNT(*) AS alerts WHERE a.dt = <PARM="RUN_DAY"/> GROUP BY a.severity
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
settings of the writes after it: a Session setting is a Hive SET sent before a Statement. The
Script tag is read past, as if a day stood there: alerts_by_severity's WHERE becomes
WHERE(equals(a.dt, script_tag(TAGS["RUN_DAY"]))), and TAGS, in its Table reference, says
<PARM="RUN_DAY"/> until you answer it.
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
which copies the original's rows into it once, before its first write. Which of the original's
Partitions it copies is SEED, in its Table reference: every one, `SEED = {}`, until you answer
its "seed" Decision in step 6.

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

Each Script tag is a Decision of the table it ends up in, named RUN_DAY, as the tag is.
project.check() says where it stands and how to answer it. A tag that stands alone, as
`= <PARM="RUN_DAY"/>` does here, is a bare tag, answered with the value's own quotes:

>>> said = repr(project.check())  # -> str
>>> print(next(line.strip() for line in said.splitlines() if "tags:" in line))
mart.alerts_by_severity_ops_reports: tags: RUN_DAY, bare at daily.hql, line 9: the value with its own quotes, such as "'2026-10-31'", or a number, such as "5"

Done when you have the list of each table's open Decisions. Then step 6.

### 6. Answer each Decision in the decisions cell

Goal: an answer for each open Decision. Write each answer in the convert Workflow notebook's
decisions cell, DECISIONS, by each table's name as project.check() writes it. The convert step's
report and project.check() print a whole DECISIONS to paste there, each answer not given yet
shown as "<FILL IN>": paste it, and fill each in. The tag's line of it reads:

>>> print(next(line.strip() for line in said.splitlines() if '"RUN_DAY":' in line))
"RUN_DAY": "<FILL IN>",  # bare at daily.hql, line 9: the value with its own quotes, such as "'2026-10-31'", or a number, such as "5"

You open no Table reference, and tick nothing. This page stands in for the decisions cell,
where you paste the DECISIONS project.check() printed and fill it in:

>>> DECISIONS = {
...     "all_tables": {"location_root": "/data"},
...     "mart.alerts_by_severity_ops_reports": {"types": {"dt": "string"},
...                                             "tags": {"RUN_DAY": "'2026-09-24'"}},
...     "mart.alerted_runs_ops_reports": {"types": {"dt": "string"}},
...     "mart.fail_history": {"key": None, "seed": {"dt": {"from": "2026-09-01"}}},
... }

Each answer, by its kind:

- "all_tables" answers for every table of the batch at once, and a table's own answer
  overwrites it. Its "location_root" gives each table with no location of its own a folder
  under it, `<root>/<database>.db/<table>`: here /data/mart.db/fail_history and the like.
- "key": None says no columns name one row. fail_history's write reads its own table, so no
  Key could be worked out of it: its Key is open. A Key project.convert could work out of a
  table's query, as GROUP BY a.severity gives one, is proposed in its Table reference already,
  marked # proposed, and its checklist says so: answer "key" only where one is open or wrong.
- "types": two tables write the Partition dt from a query that doesn't say its type, so each
  one's dt is a guessed type, "string": keep it, or give its type. Here it is kept, the day as
  text. A Partition is a slice of a table: the rows that share one value of each column it is
  partitioned by.
- "tags": the Script tag's answer is the Hive the scheduler put in its place. A bare tag's
  answer is the day with its own quotes, "'2026-09-24'", the day of the run whose rows the
  original holds.
- "seed": fail_history reads itself, so step 12 seeds it, copying the original's rows into it
  once. With no "seed", it copies every Partition the original holds, years of them perhaps;
  here it copies only those from 2026-09-01 on. **A single value means that value or later**,
  not that one alone: for one Partition alone, give a list of one, `{"dt": ["2026-09-24"]}`.

A TODO line left, such as does_not_add_up=, waits on nothing.

Done when DECISIONS holds a location_root, a key for mart.fail_history, a dt type for the other
two, RUN_DAY's day and fail_history's seed. Then step 7.

### 7. Write each answer into its Table reference

Goal: each Decision made in the table's files. Run the Workflow's next step, which writes each
answer into the table's Table reference. Its cell gives the batch's tables, which "all_tables"
answers for:

>>> print(project.write_decisions(DECISIONS, tables=project.batch_tables("ops_reports")))
Wrote 3 answers into references/mart__alerts_by_severity_ops_reports.py.
mart.alerts_by_severity_ops_reports: 2 TODO lines left in references/mart__alerts_by_severity_ops_reports.py, which wait
on nothing: fill each in when you like.
  line 1: mart.alerts_by_severity_ops_reports - TODO: say in one line what one row is.
  line 14: does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
Each Decision of mart.alerts_by_severity_ops_reports is made.
Wrote 2 answers into references/mart__alerted_runs_ops_reports.py.
mart.alerted_runs_ops_reports: 2 TODO lines left in references/mart__alerted_runs_ops_reports.py, which wait
on nothing: fill each in when you like.
  line 1: mart.alerted_runs_ops_reports - TODO: say in one line what one row is.
  line 14: does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
Each Decision of mart.alerted_runs_ops_reports is made.
Wrote 3 answers into references/mart__fail_history.py.
mart.fail_history: 2 TODO lines left in references/mart__fail_history.py, which wait
on nothing: fill each in when you like.
  line 1: mart.fail_history - TODO: say in one line what one row is.
  line 14: does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
Each Decision of mart.fail_history is made.
all_tables: location_root "/data": written into mart.alerts_by_severity_ops_reports, mart.alerted_runs_ops_reports and mart.fail_history, each in its own folder under it.

Done when each table says `Each Decision of ... is made.` Then step 8.

### 8. Answer RUN_DAY with a Run value

Goal: RUN_DAY worked out each time the table is written, rather than typed in once. A day
answered in the decisions cell is the day the table is written for, every night after, until
you answer it again, whereas the scheduler put a new day there each night. A Run value is the
value a function of yours gives each time a table's write is built: the Toolbox calls the
function and writes what it gives into the Hive as plain text, a date as '2026-09-24', quotes
and all. Write the function in your Project, in building_blocks/run_values.py: here the latest
day ops.run_alerts holds, which `latest_partition` reads from the warehouse's list of
Partitions, reading no row. It imports `query` from warehouse.py itself, as every notebook does:

The file `building_blocks/run_values.py`, after you save it:

    \"\"\"Run values: what a Script tag stands for, worked out each time a table is written.\"\"\"

    import datetime

    from sqlglot_composer import latest_partition
    from references.ops__run_alerts import run_alerts
    from warehouse import query


    def run_day() -> datetime.date:
        \"\"\"The latest day ops.run_alerts holds.\"\"\"
        return latest_partition(run_alerts.dt, query)

It imports the Table reference of ops.run_alerts, which step 3 added, as it adds one for each
table the scripts read. A Run value that reads a table no script reads needs that table's
Table reference first, from the references Workflow.

Then answer RUN_DAY with it, in place of the day: import the function at the top of the
decisions cell, and give its name, with no brackets, so the Toolbox calls it at each write.
Under "all_tables", it answers RUN_DAY in each table that holds it, and passes over the others;
a table's own "tags" would overwrite it. Run the notebook's step 3 cell again, as in step 7 of
this page: it writes the import and the function's name into the table's TAGS, and says what
changed:

>>> from building_blocks.run_values import run_day
>>> DECISIONS["all_tables"]["tags"] = {"RUN_DAY": run_day}
>>> del DECISIONS["mart.alerts_by_severity_ops_reports"]["tags"]
>>> said = repr(project.write_decisions(DECISIONS, tables=project.batch_tables("ops_reports")))
>>> print(next(line for line in said.splitlines() if "in place of" in line))
mart.alerts_by_severity_ops_reports: tags: RUN_DAY is run_day now, in place of '2026-09-24': if the table is written already, write it and compare it again.

The rest of its report says each other answer is kept as written the first time. The table's
Table reference now imports the function, and its TAGS names it:

>>> reference = Path("references/mart__alerts_by_severity_ops_reports.py")
>>> for line in reference.read_text(encoding="utf-8").splitlines():
...     if "run_day" in line:
...         print(line.split("  #")[0])
from building_blocks.run_values import run_day
    "RUN_DAY": run_day,

Only the tag follows run_day. The script's PARTITION (dt='2026-09-24') was typed in, so its
write still goes to that day's Partition: the author tagged only the WHERE's day, and the
converted code keeps what was typed. A nightly script whose Partition changes with the day
tags it, PARTITION (dt=<PARM="RUN_DAY"/>), and that tag is one of the table's Script tags,
like any other: its write() names the Partition with
partition={"dt": script_tag(TAGS["RUN_DAY"])}, so each write goes to the day run_day gives,
and the table's Lineage page shows run_day feeding dt.

Done when RUN_DAY's line in TAGS names run_day. Then step 9.

### 9. Register the file

Goal: the Project's registry, its list of the files Project actions made, holds
building_blocks/run_values.py. You wrote the file by hand, so `project.check()` names it, with
the call that registers it. Run that call in admin/check_project.ipynb, whose last cell holds
`project.register(...)`, given the file's name:

>>> print(project.check())
Not registered, made by hand. Adopt each with the call beside it:
  building_blocks/run_values.py: project.register("run_values")
The next step of each Workflow you have started; project.do_next() runs the steps it can for you:
  admin/workflows/convert/convert.ipynb, ops_reports: 4. Create each table in dev. ...
>>> print(project.register("run_values"))
Registered building_blocks/run_values.py.

Done when `project.register` says it registered the file. Then step 10.

### 10. See the Hive before you send it

Goal: the day a Run value gives, seen before anything is sent. Open the table's Table notebook,
tables/mart__alerts_by_severity_ops_reports/mart__alerts_by_severity_ops_reports.ipynb, and run
its "Try it" cell, which shows the Hive of each step with `show_hive`, sending nothing. Each
time the Hive is built, the Toolbox calls run_day() and writes the day it gives where the tag
stood:

>>> text = show_hive(project.load("mart.alerts_by_severity_ops_reports").write())  # -> str
INSERT OVERWRITE TABLE mart.alerts_by_severity_ops_reports PARTITION(dt = '2026-09-24')
SELECT
  a.severity,
  COUNT(*) AS alerts
FROM ops.run_alerts AS a
WHERE
  a.dt = '2026-09-24'
GROUP BY
  a.severity;

A dry run, a run cell of the notebook with `dry_run=True` added, calls it the same way. If the
function fails, say with no connection, the Hive holds a placeholder in its place and a
Warning says why; nothing holding it is sent. Common mistakes, below, shows it.

Done when the Hive shows the day RUN_DAY stands for, here '2026-09-24'. Then step 11.

### 11. Create each table in dev

Goal: each Saved table made in your Dev Database. The notebook's steps 4 to 6 are calls to the
warehouse, yours to run, each a cell of the notebook. At work, its step 4 creates each
table in your Dev Database. Here execute is the Example database's, which prints the first line
of each Hive it is given and changes nothing:

>>> for table in project.batch_tables("ops_reports"):
...     run_execute(project.load(table).create(), execute)
execute: ...

Done when execute has been given each table's create. Then step 12.

### 12. Seed the table that reads itself

Goal: mart.fail_history starts from the original's rows. The notebook's step 5 sends the
Session settings for dynamic Partitions, the SET lines that let one write fill several
Partitions from its rows, then seeds mart.fail_history from the original, once,
copying only the Partitions its "seed" answer names:

>>> run_execute(hive_settings("dynamic_partitions"), execute)
execute: ...
>>> for table in project.batch_tables("ops_reports", seeded=True):  # those that read themselves
...     run_execute(project.load(table).seed(), execute)
execute: INSERT OVERWRITE TABLE mart.fail_history PARTITION (dt) SELECT * FROM ops_reports.fail_history WHERE dt >= '2026-09-01'

Done when execute has been given the seed. Then step 13.

### 13. Write each table in dev

Goal: each Saved table's rows in dev. The notebook's step 6 writes each table, in the order
they read each other. It sends each table's SET lines, the original's, before its write: here
hive.exec.parallel, which makes Hive faster and changes no row:

>>> print(project.run_tables(tables=project.batch_tables("ops_reports"), execute=execute))
execute: SET hive.exec.parallel=true
execute: INSERT OVERWRITE TABLE mart.alerts_by_severity_ops_reports PARTITION(dt = '2026-09-24')
1 of 3: mart.alerts_by_severity_ops_reports  worked
...
3 of 3: mart.fail_history                    worked
Wrote 3 tables, in order.

Done when it prints `Wrote 3 tables, in order.` Then step 14.

### 14. Compare each with its original

Goal: proof that each dev table gives its original's rows. The notebook's step 7 compares each
dev table's rows with the table it copies, on the latest Partition both hold, and writes each
result in its conversion/compare.md. The Example database holds no Dev Database, so here each
says it couldn't read its dev table; at work, once every table passes, the batch is finished:

>>> print(project.compare_batch("ops_reports", query=query))
mart.alerted_runs_ops_reports: failed, couldn't compare: The Example database has no table 'mart.alerted_runs_ops_reports'.
mart.alerts_by_severity_ops_reports: failed, couldn't compare: The Example database has no table 'mart.alerts_by_severity_ops_reports'.
mart.fail_history: failed, couldn't compare: The Example database has no table 'mart.fail_history'.

Done when each table's line says it passed, at work. Then step 15.

### 15. Promote them

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

A prod copy keeps its dev table's TAGS, its Run values among them. Its seed is its own: it
copies every Partition of the original until you answer "seed" for it in the promote
notebook's decisions cell, as step 6 did here, since prod often needs more of the original's
history than a dev compare did.

Done when the promote Workflow names its next step for the three tables, at work. Then check
it worked, below.

### Run values, in full

What the steps used, and the cases they didn't meet:

- **What it may give:** a `datetime.date` is written as '2026-09-24', in quotes; a datetime
  with its time; a number as it is; True or False as TRUE or FALSE; and text as Hive, as a
  typed-in answer is, so a day given as text needs its own quotes, "'2026-09-24'". Anything
  else is refused, naming the function.
- **When it runs:** each time a Statement holding it is built, such as the table's write(),
  preview() or seed(), for each table on its own. If two tables are answered with one
  function, the Toolbox calls it once for each, and they may get two days if the warehouse
  changed between the calls. A tag's function is called with no arguments.
- **Where it lives:** a file of your Project, such as building_blocks/run_values.py, so a
  Table reference can import it. One made in a notebook, a lambda or one inside another
  function is left unwritten by the notebook's step 3, which names it.
- **Its own day:** today() is today's date in UTC, and today(utc_offset_hours=-6) six hours
  behind it; today() - datetime.timedelta(days=1) is yesterday. `latest_partition` gives a
  date when every Partition's value is one, a number when every one is digits, and otherwise
  the last in the order of their text, passing over Hive's Partition for rows with no value.
- **A tag inside quotes**, as '<PARM="RUN_MONTH"/>', reads tag_text(TAGS["RUN_MONTH"]) in the
  converted logic. It gives text as it is. A date a function gives is written with no quotes
  of its own, 2026-09-24, because the original's quotes stand around it already. Lineage draws
  no box for it: it is part of a string.
- **In a Statement of your own**, run_value(function, ...) puts what any function gives where
  a value goes, called each time the Statement is built, with the arguments you give it. A
  partition column held to it is bounded, as by a plain day. Here run_day() is called with
  brackets, since its day is an argument to days_before; a tag's answer never has them:

>>> import datetime
>>> from sqlglot_composer import (FROM, SELECT, WHERE, at_least, latest_partition, run_value,
...                               statement, to_hive)
>>> from references.ops__job_runs import job_runs
>>> def days_before(day: datetime.date, days: int) -> datetime.date:
...     return day - datetime.timedelta(days=days)
>>> print(to_hive(statement(SELECT(job_runs.run_id), FROM(job_runs),
...                         WHERE(at_least(job_runs.dt, run_value(days_before, run_day(), 1))))))
SELECT
  job_runs.run_id
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt >= '2026-09-23'

### A Run value that runs a query of its own

A function may send a Statement of its own through `run_query`, to find a day no Partition
names, such as the latest day a run succeeded. Build it as any Statement, bounding each
partitioned table it reads, and give back what it read as a value. The table's lineage draws
an arrow into the Run value from each table its Statement read. Here it is, as you would add it
to building_blocks/run_values.py, called on its own to show what it gives; its file imports
what it uses, as run_day's does, `query` from warehouse.py among them:

>>> from sqlglot_composer import AS, equals, max_of, run_query
>>> def last_good_day() -> datetime.date:
...     \"\"\"The latest day a run succeeded, of the last 30 days ops.job_runs holds.\"\"\"
...     newest = latest_partition(job_runs.dt, query)  # -> datetime.date
...     first = str(newest - datetime.timedelta(days=30))  # -> str, such as "2026-08-25"
...     rows = run_query(statement(SELECT(AS(max_of(job_runs.dt), "day")), FROM(job_runs),
...                                WHERE(at_least(job_runs.dt, first),
...                                      equals(job_runs.status, "SUCCESS"))), query)
...     return datetime.date.fromisoformat(rows["day"][0])
>>> last_good_day()
datetime.date(2026, 9, 24)

### When a Run value fails

If the function raises, say with no connection to the warehouse, the Hive still builds, with a
placeholder in the value's place, `<RUN_DAY failed>` for a tag's function and the function's
name for run_value's, and a Warning saying what it raised, so a dry run and
`show_hive` still show the rest. Nothing holding the placeholder is sent: run_query and
run_execute refuse it, before sending. Fix the function, or what it reads, and run the step
again:

>>> def no_day() -> datetime.date:
...     raise ConnectionError("no connection to the warehouse")
>>> broken = statement(SELECT(job_runs.run_id), FROM(job_runs),
...                    WHERE(at_least(job_runs.dt, run_value(no_day))))
>>> print(to_hive(broken))
SELECT
  job_runs.run_id
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt >= `<no_day() failed>`
>>> try:
...     run_query(broken, query)
... except ValueError as refused:
...     print(str(refused).strip().splitlines()[0])
What happened:  Nothing was sent: the Statement holds a Run value that failed, ...

### all_tables, in full

- It loads first, then each table's own answer overwrites it, kind by kind and, for "tags", tag
  by tag: `{"all_tables": {"tags": {"RUN_DAY": run_day, "TEAM": "'ops'"}},
  "mart_dev.web_fails": {"tags": {"TEAM": "'web'"}}}` answers mart_dev.web_fails's RUN_DAY
  with run_day and its TEAM with 'web', and each other table's with run_day and 'ops'.
- It takes "location_root", "tags" and "seed". A Key or a type is each table's own: under
  "all_tables" it is refused, naming the tables to answer it for.
- A tag no table holds is refused; a table without it is passed over, and the report says so.
- "location_root" fills only a location still open: one written already is kept, and the report
  says so.
- It needs the notebook's tables, which each Workflow's step 3 cell gives with `tables=`.

### Seed limits, in full

"seed" limits the Partitions the seed copies, by partition column, each column on its own:

- a value, **that value or later**, never that one alone: `{"dt": "2026-09-01"}`;
- a range, either end left out as you like: `{"dt": {"from": "2026-01-01", "to": "2026-06-30"}}`;
- a list, those values alone, one value alone as a list of one: `{"region": ["US", "CA"]}`.

It works the same on any partition column, not only days: `{"dt": {"from": "2026-01-01"},
"region": ["US", "CA"], "batch_no": 400}` copies the Partitions from 2026-01-01 on, of the US
and Canada, from batch 400 on. Each value is written as the column's type says: a number as it
is, text and dates in quotes. Any value may be a Run value's function, called as the seed is
built. A partition column it leaves out is copied whole, and there is no top end unless "to"
gives one. A limit on a column that isn't one of the table's partition columns is refused, as
is one for a table that doesn't read itself. Under "all_tables", a limit applies only to the
tables with that partition column; the notebook's step 3 report and the seed's line say
what was sent.

The seed copies once, and each write after it reads what its own WHERE says. If a write
reads a window of days, such as the day before RUN_DAY through RUN_DAY, and the seed starts
at RUN_DAY's day, the first write fills the day before too, as the original's write did: the
copy then holds that day as the original does, and its compare passes. There is nothing to
do; start the seed earlier only if you want the copy to hold more days.

## Check it worked

Before you go on, check that:

- RUN_DAY's line in TAGS, in references/mart__alerts_by_severity_ops_reports.py, names
  run_day, and the Hive `show_hive` shows holds the day it gave;
- the seed's line ends with the WHERE its "seed" answer gave, here `WHERE dt >= '2026-09-01'`;
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
table's folder or a Script tag's value. Answer each one project.check() names in the decisions
cell: paste the DECISIONS it prints, and fill in each "<FILL IN>".

### Expecting a copy to keep its table's name

A table's copy in dev is named <table>_<the original's database>,
mart.fail_history_ops_reports, so two databases' tables of one name stay apart. To keep the
table's own name, give it before converting, the name alone: in the convert notebook's names
cell, RENAME = {"ops_reports.fail_history": "fail_history"}, which step 3 passes as rename=,
makes mart.fail_history.

### Answering a bare Script tag without its quotes

A bare tag's answer is put exactly where the tag stood, so a date needs its own quotes,
"'2026-09-24'": written 2026-09-24, Hive reads it as a subtraction, 2026 - 9 - 24.
project.write_decisions names that answer and writes nothing for it. A tag inside quotes,
'<PARM="NAME"/>', is answered with no quotes.

### Answering a nightly tag with one day

A day answered in the decisions cell is the day the table is written for, every night after,
until you answer it again. For a day that changes each run, answer it with a Run value's
function, as step 8 does: the Hive sent holds the day itself. If your warehouse lets you send
Hive variables, "'${hivevar:run_day}'" works too, with a line that sets it, SET
hivevar:run_day=..., kept at the top of the script you convert: the table's
session_settings() keeps it, project.run_tables sends it before each write, and
project.write_decisions says whether a line sets it.

### Writing the function's name with brackets

Answer a tag with the function itself, `run_day`, never `run_day()`: with brackets, Python
calls it once, as the decisions cell runs, and the answer is that one day. The Workflow's step
3 leaves a date given so unwritten, naming it in its report, and the tag stays open: answer
with the name alone.

### Working on a table converted before 8.4

A table converted before 8.4 keeps its seed() as it was, copying every Partition, with no SEED
for a "seed" answer to fill: the 8.4 Upgrade marks it so. Its tags in strings the Upgrade
writes through tag_text, as 8.4 writes them, so a Run value's function may answer them. To
limit its seed, convert its scripts again as a new batch, with a new name for each table in
RENAME, and remove the old one once the new one's compare passes, with `project.remove_table`
in admin/remove.ipynb.

### Promoting before comparing

promote refuses a table whose compare hasn't passed, so prod never gets rows that differ from
the original's. Compare each table, and fix it in dev until its compare passes, then promote.

## Next

- [Follow a Workflow](#follow_a_workflow): every Workflow's steps, drawn and listed.
- [Hand-written Hive with your Table references](#hand_written_hive_with_your_table_references):
  the Unchecked pieces a Conversion leaves, and how to replace them.
"""  # noqa: E501 - the Hive it converts and the files it shows, line for line
