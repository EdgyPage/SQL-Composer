date: 2026-11-04
arm: C
model: haiku
files: 3c096cf

## T31

Workflow: convert, step 1 (convert the scripts).

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

Workflow: convert, step 1 (convert the scripts).

```python
NAME = "fails"
FILES = []
HIVE = """
CREATE TABLE ops_reports.failed_runs AS
SELECT r.job_id
FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status = 'FAILED';

INSERT OVERWRITE TABLE mart.fails_per_job PARTITION (dt = '2026-09-24')
SELECT f.job_id, COUNT(*) AS fails
FROM ops_reports.failed_runs f
GROUP BY f.job_id;
"""
DATABASE = "default"
RENAME = {}
STAGING = {"ops_reports.failed_runs": "fold"}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

## T33

Workflow: convert, step 2 (answer the Decisions). The decisions cell and the cell that writes them, as asked; the steps after them are yours to run.

```python
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "types": {"dt": "string"},
    },
}
```

```python
project.write_decisions(DECISIONS)
```

Left to you: step 4 (create each table in dev), step 5 (seed any table that reads itself, if the batch has one), step 6 (write each table in dev), and step 7 (compare each table with its original).

## T37

Workflow: convert, step 1 (convert the scripts).

```python
NAME = "runs_per_job"
FILES = []
HIVE = """
SELECT r.job_id, COUNT(*) AS runs
FROM job_runs r
WHERE r.dt = '2026-09-24'
GROUP BY r.job_id
"""
DATABASE = "ops"
RENAME = {}
STAGING = {}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```
