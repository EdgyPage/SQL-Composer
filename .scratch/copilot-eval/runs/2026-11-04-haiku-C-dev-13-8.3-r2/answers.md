date: 2026-11-04
arm: C
model: haiku
files: 22aa474

## T31

Workflow: convert (batch daily_ops), step 1: convert the two scripts into dev.

```python
NAME = "daily_ops"
FILES = ["daily_fails.hql", "daily_alerts.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

## T32

Workflow: convert (batch fails), step 1: convert the Hive into dev, folding the staging table.

```python
NAME = "fails"
FILES = []
HIVE = """CREATE TABLE ops_reports.failed_runs AS
SELECT r.job_id
FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status = 'FAILED';

INSERT OVERWRITE TABLE mart.fails_per_job PARTITION (dt = '2026-09-24')
SELECT f.job_id, COUNT(*) AS fails
FROM ops_reports.failed_runs f
GROUP BY f.job_id;"""
DATABASE = "default"
RENAME = {}
STAGING = {"ops_reports.failed_runs": "fold"}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

## T33

Workflow: convert (batch fails), step 2: answer the open Decisions, then step 3: write them into the Table reference.

```python
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "types": {"dt": "string"},
    }
}

project.write_decisions(DECISIONS)
```

Later steps, left for you to run after these:
- Step 4: create each table in dev with `run_execute(project.load(table).create(), execute)` for each table in `project.batch_tables(NAME)`.
- Step 5: seed each table that reads itself, once, from its original (`project.batch_tables(NAME, seeded=True)`; it prints a note and seeds nothing if no table reads itself).
- Step 6: write each table in dev with `project.run_tables(tables=project.batch_tables(NAME), execute=execute)`.
- Step 7: compare each table with its original with `project.compare_batch(NAME, query=query, partition=PARTITION)`.

## T37

Workflow: convert (batch runs_per_job), step 1: convert the query into dev.

```python
NAME = "runs_per_job"
FILES = []
HIVE = """SELECT r.job_id, COUNT(*) AS runs
FROM job_runs r
WHERE r.dt = '2026-09-24'
GROUP BY r.job_id"""
DATABASE = "ops"
RENAME = {}
STAGING = {}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```
