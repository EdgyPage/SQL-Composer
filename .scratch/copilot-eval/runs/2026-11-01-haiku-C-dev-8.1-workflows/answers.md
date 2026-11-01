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

## T34

You are in the references Workflow, at its first step: write the Table references from DESCRIBE. Run the names cell, then the step cell.

```python
# Cell 1, names
NAME = "references"
TABLES = ["ops.jobs", "ops.run_alerts"]

# Cell 2, step 1: write the Table references from DESCRIBE (a call to the warehouse)
project.add_references(TABLES, query=query)
```

## T35

You are in the new_table Workflow, at its first step: make each Table folder. You have no query, so QUERIES stays empty and you write the logic yourself. Run the names cell, then the step cell.

```python
# Cell 1, names
NAME = "new_table"
TABLES = ["mart_dev.job_day_counts"]
QUERIES = {}

# Cell 2, step 1: make each Table folder (it changes only files, so project.do_next() runs it for you)
project.new_table(TABLES, queries=QUERIES)
```
