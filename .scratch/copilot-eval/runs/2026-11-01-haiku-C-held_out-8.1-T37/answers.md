date: 2026-11-01
arm: C
model: haiku
files: 8a631c94

## T37

```python
# Workflow: convert, batch runs_per_job. Step 1 of 7 is the next step.

# Names cell
NAME = "runs_per_job"
FILES = []
HIVE = """SELECT r.job_id, COUNT(*) AS runs
FROM job_runs r
WHERE r.dt = '2026-09-24'
GROUP BY r.job_id"""
DATABASE = "ops"
STAGING = {}

# Step 1: convert the query into Saved tables in dev (a call to the warehouse, yours to run)
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE, staging=STAGING)

# Step 2 (yours, not Copilot's): answer each table's open Decisions here
DECISIONS = {}

# Step 3: write each answer into its table's Table reference (project.do_next() runs it)
project.write_decisions(DECISIONS)

# Step 4: create each table in dev (a call to the warehouse, yours to run)
for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)

# Step 5: seed each table that reads itself, once, from its original (yours to run)
run_execute(hive_settings("dynamic_partitions"), execute)
for table in project.batch_tables(NAME, seeded=True):
    run_execute(project.load(table).seed(), execute)

# Step 6: write each table in dev (a call to the warehouse, yours to run)
project.run_tables(tables=project.batch_tables(NAME), execute=execute)

# Step 7: compare each table with its original (a call to the warehouse, yours to run)
project.compare_batch(NAME, query=query)
```
