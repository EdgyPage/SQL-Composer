date: 2026-11-01
arm: C
model: haiku
files: 8a631c94

## T31

Workflow: convert (batch daily_ops). The user is at step 1, converting the scripts into the Dev Database. Run the names cell, then the step 1 cell.

```python
# names cell
NAME = "daily_ops"
FILES = ["daily_fails.hql", "daily_alerts.hql"]
HIVE = None
DATABASE = "mart_dev"
STAGING = None

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                staging=STAGING)
```

## T32

Workflow: convert (batch fails). The user is at step 1, converting the Hive text into the Dev Database, with ops_reports.failed_runs folded. Run the names cell, then the step 1 cell.

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
DATABASE = "mart_dev"
STAGING = {"ops_reports.failed_runs": "fold"}

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                staging=STAGING)
```
