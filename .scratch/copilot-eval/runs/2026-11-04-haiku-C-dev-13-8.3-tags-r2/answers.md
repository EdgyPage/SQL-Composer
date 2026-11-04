date: 2026-11-04
arm: C
model: haiku
files: 1224d14

## T31

Workflow: convert, step 1 (convert the scripts), for daily_ops.

```python
# names cell
NAME = "daily_ops"
FILES = ["daily_fails.hql", "daily_alerts.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

Left to you: any Decision that project.convert reports, answered in the decisions cell (step 2).
Later steps: step 3 writes your answers into each table's Table reference; step 4 creates each
table in dev; step 5 seeds each table that reads itself, once, from its original; step 6 writes
each table in dev; step 7 compares each table with its original.

## T32

Workflow: convert, step 1 (convert the scripts), for fails.

```python
# names cell
NAME = "fails"
FILES = []
HIVE = """CREATE TABLE ops_reports.failed_runs AS
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

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

Left to you: any Decision that project.convert reports, answered in the decisions cell (step 2).
Later steps: step 3 writes your answers into each table's Table reference; step 4 creates each
table in dev; step 5 seeds each table that reads itself, once, from its original; step 6 writes
each table in dev; step 7 compares each table with its original.

## T33

Workflow: convert, step 2 (answer the Decisions), for fails.

```python
# names cell
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}

# decisions cell
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "types": {"dt": "string"},
    }
}

# step 3 cell
project.write_decisions(DECISIONS)
```

No Decision is left open. Later steps, which you run yourself: step 4 creates each table in dev;
step 5 seeds each table that reads itself, once, from its original; step 6 writes each table in
dev; step 7 compares each table with its original.

## T37

Workflow: convert, step 1 (convert the scripts), for runs_per_job.

```python
# names cell
NAME = "runs_per_job"
FILES = []
HIVE = """SELECT r.job_id, COUNT(*) AS runs
FROM job_runs r
WHERE r.dt = '2026-09-24'
GROUP BY r.job_id
"""
DATABASE = "ops"
RENAME = {}
STAGING = {}

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

Left to you: any Decision that project.convert reports, answered in the decisions cell (step 2).
Later steps: step 3 writes your answers into each table's Table reference; step 4 creates each
table in dev; step 5 seeds each table that reads itself, once, from its original; step 6 writes
each table in dev; step 7 compares each table with its original.

## T45

Workflow: convert, step 2 (answer the Decisions), for fails.

```python
# names cell
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}

# decisions cell
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "types": {"dt": "string"},
        "tags": {"RUN_DAY": "'2026-09-24'"},
    }
}

# step 3 cell
project.write_decisions(DECISIONS)
```

No Decision is left open. Later steps, which you run yourself: step 4 creates each table in dev;
step 5 seeds each table that reads itself, once, from its original; step 6 writes each table in
dev; step 7 compares each table with its original.
