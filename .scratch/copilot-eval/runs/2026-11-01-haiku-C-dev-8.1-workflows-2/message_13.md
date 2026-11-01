You are standing in for Microsoft Copilot in a web chat. Use no tools: answer from what is written here and what you already know.

Before asking anything, the user pasted this as their first message:

<<<
# Copilot file 13: the Workflows, Hive to prod (sqlglot Composer 8.1)

Objective: take the user through converting Hive and promoting it to prod, step by step,
from each Workflow's notebook. Load this file when the user asks how to turn Hive into their
own tables end to end, or carry dev tables to prod. You write the steps for sqlglot Composer 8.1, a
Toolbox that writes Hive: the steps left, each its cell, in order. For a new table of their
own, Table references, an upgrade or a change to a Saved table, the user loads file 14; for
the Python inside a step, that step's file.

## Names for this objective, with their arguments

- project.check()
- project.run_workflow(workflow, *, query=None, execute=None, dry_run=False, change=None)
- project.convert(name, hive=None, *, file=None, files=None, query=None, database='default', rename=None, overwrite=False, staging=None)
- project.compare_batch(name, *, query=None, tables=None, partition=None)
- project.promote(tables, *, rename=None)

## How a Workflow runs

Each job has a notebook, admin/workflows/<name>/<name>.ipynb. The user fills in its names
cell (NAME, TABLES: the names in capitals) and its decisions cell, DECISIONS, and saves it.
DECISIONS holds each answer by the table's name as project.check() writes it, each by its
kind: `{"mart_dev.weekly": {"location": "/data/team/mart_dev.db/weekly", "key": ["job_id"],
"types": {"fails": "bigint"}}}`; a later step, `project.write_decisions(DECISIONS)`,
writes them in.
Each step's cell runs that step; the last cell, `project.run_workflow(...)`, runs every step
left, up to the first only the user can do, and `dry_run=True` sends nothing.
`project.check()` names the next step. A Decision is the user's: never answer it for them.
DEV and PROD, the Dev and Prod Databases, are set once in admin/databases.py.

## convert: someone else's Hive into Saved tables in dev

For any Hive, one query or many scripts. NAME is the batch's name; FILES the .hql files,
saved beside the notebook, in admin/workflows/convert/, where it reads them, or [] with HIVE
the Hive as text. STAGING is a dict: of each staging table, one a statement makes that a later
one reads, "fold" (into the tables that read it) or "keep", such as
{"ops_reports.failed": "fold"}; one left out is folded if temporary or DROPped, else kept.

1. Convert the scripts: each table they write a Saved table in dev (it is a call to the
   warehouse, yours to run).

       project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                       staging=STAGING)

2. Answer each table's open Decisions in the decisions cell (it is a decision, yours to make).
3. Write each answer into its table's Table reference (it changes only files, so
   project.do_next() runs it for you).

       project.write_decisions(DECISIONS)

4. Create each table in dev (it is a call to the warehouse, yours to run).

       for table in project.batch_tables(NAME):
           run_execute(project.load(table).create(), execute)

5. Seed each table that reads itself, once, from its original (it is a call to the warehouse,
   yours to run).

       run_execute(hive_settings("dynamic_partitions"), execute)
       for table in project.batch_tables(NAME, seeded=True):
           run_execute(project.load(table).seed(), execute)

6. Write each table in dev (it is a call to the warehouse, yours to run).

       project.run_tables(tables=project.batch_tables(NAME), execute=execute)

7. Compare each table with its original (it is a call to the warehouse, yours to run).

       project.compare_batch(NAME, query=query)


## promote: dev tables to prod

TABLES are the dev tables, such as ["mart_dev.daily_job_runs"].

1. Promote each table: a prod copy of its folder and Table reference (it changes only files, so
   project.do_next() runs it for you).

       project.promote(TABLES)

2. Answer each prod table's open Decisions in the decisions cell (it is a decision, yours to
   make).
3. Write each answer into its prod table's Table reference (it changes only files, so
   project.do_next() runs it for you).

       project.write_decisions(DECISIONS)

4. Create each table in prod (it is a call to the warehouse, yours to run).

       for table in project.promoted_tables(TABLES):
           run_execute(project.load(table).create(), execute)

5. Seed each prod table that reads itself, once, from its original (it is a call to the
   warehouse, yours to run).

       run_execute(hive_settings("dynamic_partitions"), execute)
       for table in project.promoted_tables(TABLES, seeded=True):
           run_execute(project.load(table).seed(), execute)

6. Write each table in prod (it is a call to the warehouse, yours to run).

       project.run_tables(tables=project.promoted_tables(TABLES), execute=execute)

7. Refresh the Reference sheet and the Database modules (it changes only files, so
   project.do_next() runs it for you).

       project.refresh_reference_sheet(project.promoted_tables(TABLES))


## Worked example

The user: "I have daily.hql and weekly.hql from the ops team; DEV is filled in." The
convert notebook's names cell, then its first step's cell:

```python
NAME = "ops_reports"
FILES = ["daily.hql", "weekly.hql"]
project.convert(NAME, None, files=FILES, query=query, database="default",
                staging=None)
```

## Do and don't

- Do give each step's cell as listed, with the user's names in it.
- Don't skip a Decision, such as a table's location: say what it asks of the user, to answer in the decisions cell.
- Don't promote a table before its compare has passed.

## Before you answer

- Name the Workflow and the step the user is at; give each later step's cell as it is.
- Never invent a step or a call: only those listed here.

>>>

Each task below is a separate request the user sends next. Answer each as you would in that chat: reply with its `## T..` heading, then your answer, with the code in a ```python block.

## T31

I work in a sqlglot Composer 8.1 Project. Its references:
- `from references.ops__job_runs import job_runs` gives ops.job_runs: run_id bigint, job_id bigint, status string, duration_mins int, avg_retry_secs double, dt string; partitioned by dt; Key run_id.
- `from references.ops__run_alerts import run_alerts` gives ops.run_alerts: alert_id bigint, run_id bigint, severity string, dt string; partitioned by dt; Key alert_id.
- `from references import ops` gives each ops table above by its name, as ops.job_runs.
- admin/databases.py has DEV = 'mart_dev' and PROD = 'mart'.
- admin/workflows/convert/daily_fails.hql holds:

INSERT OVERWRITE TABLE mart.daily_fails PARTITION (dt = '2026-09-24')
SELECT r.job_id, COUNT(*) AS fails
FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status = 'FAILED'
GROUP BY r.job_id;

- admin/workflows/convert/daily_alerts.hql holds:

INSERT OVERWRITE TABLE mart.daily_alerts PARTITION (dt = '2026-09-24')
SELECT a.severity, COUNT(*) AS alerts
FROM ops.run_alerts a
WHERE a.dt = '2026-09-24'
GROUP BY a.severity;

- `from warehouse import query, execute` gives my two calls to the warehouse.

I have two scripts from the ops team, daily_fails.hql and daily_alerts.hql, saved in admin/workflows/convert/. Convert them into my Dev Database as one batch named daily_ops: give the convert notebook's names cell and its first step's cell.

Answer with one Python code block: the Workflow notebook's cells to run, in order, its names cell first, filled in.

## T32

I work in a sqlglot Composer 8.1 Project. Its references:
- `from references.ops__job_runs import job_runs` gives ops.job_runs: run_id bigint, job_id bigint, status string, duration_mins int, avg_retry_secs double, dt string; partitioned by dt; Key run_id.
- `from references import ops` gives each ops table above by its name, as ops.job_runs.
- admin/databases.py has DEV = 'mart_dev' and PROD = 'mart'.
- `from warehouse import query, execute` gives my two calls to the warehouse.

Convert this Hive into my Dev Database as a batch named fails, folding the staging table ops_reports.failed_runs into the table that reads it rather than keeping it: give the convert notebook's names cell and its first step's cell.

CREATE TABLE ops_reports.failed_runs AS
SELECT r.job_id
FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status = 'FAILED';

INSERT OVERWRITE TABLE mart.fails_per_job PARTITION (dt = '2026-09-24')
SELECT f.job_id, COUNT(*) AS fails
FROM ops_reports.failed_runs f
GROUP BY f.job_id;


Answer with one Python code block: the Workflow notebook's cells to run, in order, its names cell first, filled in.
