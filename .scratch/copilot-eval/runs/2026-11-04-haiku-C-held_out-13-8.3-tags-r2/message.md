You are standing in for Microsoft Copilot in a web chat. Use no tools: answer from what is written here and what you already know.

Before asking anything, the user pasted this as their first message:

<<<
# Copilot file 13: the convert Workflow, Hive into dev (sqlglot Composer 8.3)

**Follow the steps below in order, as written. Add no step or call; reply as Output says.**

Objective: take the user through converting Hive into Saved tables in their Dev Database,
with sqlglot Composer 8.3, a Toolbox that writes Hive: the steps left, each its cell of the convert
Workflow's notebook, in order. Load this file when the user asks how to turn Hive into their
own tables end to end. File 16 is for promoting dev tables to prod; file 14 for new tables,
Table references, upgrades and changes to a Saved table; a step's own file, for the Python
inside it.

## Terms

- **Workflow**: ordered steps to one end goal; each step is a cell of its notebook,
  admin/workflows/<name>/<name>.ipynb. Its **names cell** holds its inputs in capitals.
- **Decision**: one thing about one table only the user decides, such as its location, Key
  or a column type, answered in the **decisions cell**, DECISIONS.
- **Saved table**: a table the user's own code writes; its **Table reference** is the file
  of its columns, partitions, Key and location.
- **DEV**, **PROD**: the Dev Database, where tables are built and compared, and the Prod
  Database, where others read them; set once in admin/databases.py.
- **query**, **execute**: the user's warehouse calls, from warehouse.py; a Workflow
  notebook's first cell imports them with the Toolbox's names.

## Names for this objective, with their arguments

- project.check()
- project.run_workflow(workflow, *, query=None, execute=None, dry_run=False, change=None)
- project.convert(name, hive=None, *, file=None, files=None, query=None, database='default', rename=None, overwrite=False, staging=None)
- project.compare_batch(name, *, query=None, tables=None, partition=None)
- project.write_decisions(answers)

## Steps

1. **Place the user.** Name the Workflow and the step the user is at; `project.check()`
   names the next step. Then step 2.
2. **Write the names cell**, each input below given the user's value. Then step 3.
3. **Write the cells asked**, by the Decision rules, each as listed, with the user's names.
   Then step 4.
4. **Name the rest**: each Decision left to the user, and each later step, in words. Then
   step 5.
5. **Check** the Self-check; fix what it finds, then reply.

## Decision rules

- If the user asks for particular cells, give those: a step's cell runs only once the steps
  before it are done.
- If the user asks for every step's cell, give each one as listed, in order.
- If the user gives a Decision's answer, write it in DECISIONS. If not, say what it asks, for
  the user to answer: a Decision is the user's, never yours.
- If the user names no rename, staging table or database, write `RENAME = {}`,
  `STAGING = {}` or `DATABASE = "default"`. If no Decision is open, write `DECISIONS = {}`.
- If the user asks to promote the tables to prod, name file 16 for it, once each compare
  has passed.

## Output

1. The Workflow and the user's step, in one line.
2. Each cell asked for in a ```python block, the names cell first.
3. Each Decision left to the user, then each later step, in words.

## How a Workflow runs

- DECISIONS holds each answer by the table's name as `project.check()` writes it, each by
  its kind: `{"mart_dev.weekly": {"location": "/data/team/mart_dev.db/weekly", "key":
  ["job_id"], "types": {"fails": "bigint"}, "tags": {"PERIOD_END": "'2026-10-31'"}}}`;
  `project.write_decisions(DECISIONS)` writes each into its table's Table reference.
- `project.check()`, and convert's step 1, print a whole DECISIONS to paste, each answer
  still to give `"<FILL IN>"`, which is no answer until filled in.
- A Script tag, `<PARM="NAME"/>` in the Hive, filled in by the program that ran it, is a
  Decision of its table under "tags": a bare one is answered with the value's own quotes,
  `"'2026-10-31'"`, one inside quotes with none, `"failed"`. Answer it with the value the
  user gives; only if they ask for one changing each run, `"'${hivevar:run_day}'"`, a SET
  hivevar line kept in the script. If they give none, never guess: ask.
- Leave convert's `PARTITION = None` unless the user asks to compare a Partition by name:
  then `PARTITION = {"dt": "2026-09-23"}`, and step 7 compares it too.
- The last cell, `project.run_workflow(...)`, runs every step left, up to the first only the
  user can do; `dry_run=True` sends nothing.

## convert: someone else's Hive into Saved tables in dev

Its inputs:

- NAME: the batch's name. For the `project.run_workflow(...)` cell, which runs every step
  left, it may be a list of batches converted already.
- FILES: the .hql files, saved in admin/workflows/convert/; or `FILES = []` and HIVE the
  Hive as text. A query that only SELECTs makes a Saved table too, named for its file or
  NAME.
- DATABASE: the database of a table the Hive names without one, such as "ops".
- RENAME: a dev copy's own name, by the table's full name (DATABASE when the scripts give
  none), the new name without a database: `{"mart.team_fails": "team_fails"}` makes
  mart_dev.team_fails. Left `{}`, it is <table>_<its database>: mart_dev.team_fails_mart.
- STAGING: a staging table is one a statement makes and a later one reads; convert's report
  names each. Folded, its query goes inside each table that reads it, and it is never made;
  kept, it is a Saved table: `{"ops_reports.failed": "fold"}` or "keep". Each one not named,
  convert folds if temporary or DROPped, and keeps if not.

1. Convert the scripts: each table they write a Saved table in dev (it is a call to the
   warehouse, yours to run).

       project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                       rename=RENAME, staging=STAGING)

2. Answer each table's open Decisions in the decisions cell (it is a decision, yours to make).
3. Write each answer into its table's Table reference (it changes only files, so
   project.do_next() runs it for you).

       project.write_decisions(DECISIONS)

4. Create each table in dev (it is a call to the warehouse, yours to run).

       for table in project.batch_tables(NAME):
           run_execute(project.load(table).create(), execute)

5. Seed each table that reads itself, once, from its original (it is a call to the warehouse,
   yours to run).

       to_seed = project.batch_tables(NAME, seeded=True)
       if not to_seed:
           print("Seeded nothing: no table of the batch reads itself.")
       else:
           run_execute(hive_settings("dynamic_partitions"), execute)
           for table in to_seed:
               run_execute(project.load(table).seed(), execute)

6. Write each table in dev (it is a call to the warehouse, yours to run).

       project.run_tables(tables=project.batch_tables(NAME), execute=execute)

7. Compare each table with its original (it is a call to the warehouse, yours to run).

       project.compare_batch(NAME, query=query, partition=PARTITION)


## Example

The user: "I have daily.hql and weekly.hql from the ops team; DEV is filled in." The
convert notebook's names cell, then its first step's cell:

```python
NAME = "ops_reports"
FILES = ["daily.hql", "weekly.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

## Self-check

- The reply names the Workflow and the user's step.
- Each cell is one listed here, with the user's names in it.
- Each later step is named in words, unless every cell was asked for.
- Each Decision answered is in DECISIONS by the table's name; each other is named.
- Promoting is named as file 16's, never given here.

>>>

Each task below is a separate request the user sends next. Answer each as you would in that chat: reply with its `## T..` heading, then your answer, with the code in a ```python block.

## T38

I work in a sqlglot Composer 8.3 Project. Its references:
- `from references.ops__run_alerts import run_alerts` gives ops.run_alerts: alert_id bigint, run_id bigint, severity string, dt string; partitioned by dt; Key alert_id.
- `from references import ops` gives each ops table above by its name, as ops.job_runs.
- admin/databases.py has DEV = 'mart_dev' and PROD = 'mart'.
- admin/workflows/convert/alerts.hql holds:

CREATE TEMPORARY TABLE high_alerts AS
SELECT a.run_id
FROM ops.run_alerts a
WHERE a.dt = '2026-09-24' AND a.severity = 'high';

INSERT OVERWRITE TABLE mart.high_alerts_per_run PARTITION (dt = '2026-09-24')
SELECT h.run_id, COUNT(*) AS alerts
FROM high_alerts h
GROUP BY h.run_id;

- `from warehouse import query, execute` gives my two calls to the warehouse.

I have alerts.hql from the ops team, saved in admin/workflows/convert/. Its first statement makes a temporary table, high_alerts, which I want kept as a table of its own rather than folded. Convert it into my Dev Database as a batch named alerts: give the convert notebook's names cell and its first step's cell.

Answer with one Python code block: the Workflow notebook's cells to run, in order, its names cell first, filled in.

## T39

I work in a sqlglot Composer 8.3 Project. Its references:
- `from references.ops__job_runs import job_runs` gives ops.job_runs: run_id bigint, job_id bigint, status string, duration_mins int, avg_retry_secs double, dt string; partitioned by dt; Key run_id.
- `from references import ops` gives each ops table above by its name, as ops.job_runs.
- admin/databases.py has DEV = 'mart_dev' and PROD = 'mart'.
- admin/workflows/convert/daily_fails.hql holds:

CREATE TABLE IF NOT EXISTS mart.daily_fails (job_id BIGINT, fails BIGINT)
PARTITIONED BY (dt STRING);

INSERT OVERWRITE TABLE mart.daily_fails PARTITION (dt = '2026-09-24')
SELECT r.job_id, COUNT(*) AS fails
FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status = 'FAILED'
GROUP BY r.job_id;

- `from warehouse import query, execute` gives my two calls to the warehouse.

I have daily_fails.hql from the ops team, saved in admin/workflows/convert/, and their job has run it, so mart.daily_fails holds its rows. Convert it into my Dev Database as a batch named fails and take it all the way through the compare: give every step's cell, in order. convert will name the table mart_dev.daily_fails_mart, and its folder is /data/team/mart_dev.db/daily_fails.

Answer with one Python code block: the Workflow notebook's cells to run, in order, its names cell first, filled in.

## T46

I work in a sqlglot Composer 8.3 Project. Its references:
- `from references.ops__job_runs import job_runs` gives ops.job_runs: run_id bigint, job_id bigint, status string, duration_mins int, avg_retry_secs double, dt string; partitioned by dt; Key run_id.
- `from references import ops` gives each ops table above by its name, as ops.job_runs.
- admin/databases.py has DEV = 'mart_dev' and PROD = 'mart'.
- admin/workflows/convert/daily_fails.hql holds:

CREATE TABLE IF NOT EXISTS mart.daily_fails (job_id BIGINT, fails BIGINT)
PARTITIONED BY (dt STRING);

INSERT OVERWRITE TABLE mart.daily_fails PARTITION (dt = '2026-09-24')
SELECT r.job_id, COUNT(*) AS fails
FROM ops.job_runs r
WHERE r.dt = <PARM="RUN_DAY"/> AND r.status = '<PARM="STATUS"/>'
GROUP BY r.job_id;

- `from warehouse import query, execute` gives my two calls to the warehouse.

I have daily_fails.hql from the ops team, saved in admin/workflows/convert/. Their scheduler fills in each <PARM="NAME"/> in it before Hive reads it: this run, RUN_DAY with '2026-09-24' and STATUS with FAILED, and the job has run, so mart.daily_fails holds its rows. Convert it into my Dev Database as a batch named fails and take it all the way through the compare: give every step's cell, in order. convert will name the table mart_dev.daily_fails_mart, and its folder is /data/team/mart_dev.db/daily_fails.

Answer with one Python code block: the Workflow notebook's cells to run, in order, its names cell first, filled in.
