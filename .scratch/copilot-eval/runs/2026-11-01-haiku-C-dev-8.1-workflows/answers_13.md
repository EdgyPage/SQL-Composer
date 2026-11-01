date: 2026-11-01
arm: C
model: haiku
files: de6bc5fc

## T31

You are in the convert Workflow, at step 1 (convert the scripts). Set the names cell, then run the first step's cell.

```python
# names cell
NAME = "daily_ops"
FILES = ["daily_fails.hql", "daily_alerts.hql"]

# step 1 cell
project.convert(NAME, None, files=FILES, query=query, database="default",
                staging=None)
```

## T32

You are in the convert Workflow, at step 1 (convert the scripts). The staging table ops_reports.failed_runs is named in STAGING so it is folded into the table that reads it. Set the names cell, then run the first step's cell.

```python
# names cell
NAME = "fails"
FILES = None
HIVE = """CREATE TABLE ops_reports.failed_runs AS
SELECT r.job_id
FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status = 'FAILED';

INSERT OVERWRITE TABLE mart.fails_per_job PARTITION (dt = '2026-09-24')
SELECT f.job_id, COUNT(*) AS fails
FROM ops_reports.failed_runs f
GROUP BY f.job_id;
"""
STAGING = ["ops_reports.failed_runs"]

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database="default",
                staging=STAGING)
```
