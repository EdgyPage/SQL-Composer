date: 2026-11-01
arm: C
model: haiku
files: 24-dev

## T31

Workflow: convert. The user's step: step 1, converting the scripts, not yet run.

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

Left to you, in words:
- Decisions: none yet. project.check() names any that convert opens, and you answer each in the decisions cell (step 2).
- Step 3: write each answer into its table's Table reference with project.write_decisions(DECISIONS); project.do_next() runs it for you.
- Step 4: create each table in dev, for each table of the batch daily_ops.
- Step 5: seed each table that reads itself, once, from its original. Neither table reads itself, so this step seeds nothing.
- Step 6: write each table in dev.
- Step 7: compare each table with its original.

With RENAME left as {}, the tables land as mart_dev.daily_fails_mart and mart_dev.daily_alerts_mart.

## T32

Workflow: convert. The user's step: step 1, converting the scripts, not yet run.

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

Left to you, in words:
- Decisions: none yet. project.check() names any that convert opens, and you answer each in the decisions cell (step 2).
- Step 3: write each answer into its table's Table reference with project.write_decisions(DECISIONS); project.do_next() runs it for you.
- Step 4: create each table in dev, for each table of the batch fails.
- Step 5: seed each table that reads itself, once, from its original. Check the convert report for this; the folded staging table is not made, so it cannot be seeded.
- Step 6: write each table in dev.
- Step 7: compare each table with its original.

ops_reports.failed_runs is folded: its query goes inside mart_dev.fails_per_job_mart, the table that reads it, and no table is made for it.

## T33

Workflow: convert. The user's step: step 2, answering the Decisions in the decisions cell.

You asked for only the decisions cell and the cell that writes the answers, so the names cell is left out; NAME = "fails" stays as it is.

```python
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "types": {"dt": "string"},
    },
}

project.write_decisions(DECISIONS)
```

Left to you, in words: no Decision is left. project.check() named two, the types of dt and the location, and both are answered above.

Later steps, in words:
- Step 4: create each table in dev, for each table of the batch fails.
- Step 5: seed each table that reads itself, once, from its original. mart_dev.daily_fails_mart reads ops.job_runs, not itself, so this step seeds nothing.
- Step 6: write each table in dev.
- Step 7: compare each table with its original.

## T37

Workflow: convert. The user's step: step 1, converting the query, not yet run.

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

Left to you, in words:
- Decisions: none yet. The query only SELECTs, so it makes one Saved table, named runs_per_job. project.check() names any Decision that convert opens, and you answer each in the decisions cell (step 2).
- Step 3: write each answer into its table's Table reference with project.write_decisions(DECISIONS); project.do_next() runs it for you.
- Step 4: create each table in dev, for each table of the batch runs_per_job.
- Step 5: seed each table that reads itself, once, from its original. Check convert's report for any; the query reads ops.job_runs, not itself, so this step seeds nothing.
- Step 6: write each table in dev.
- Step 7: compare each table with its original.

## T40

```python
# Names cell
TABLES = ["mart_dev.daily_fails_mart"]

# Step 1: promote each table
project.promote(TABLES)
```

## T41

```python
# Names cell
TABLES = ["mart_dev.daily_fails_mart"]

# Step 1: promote each table
project.promote(TABLES)

# Step 2: answer each prod table's open Decisions (none open for this prod copy)
DECISIONS = {}

# Step 3: write each answer into its prod table's Table reference
project.write_decisions(DECISIONS)

# Step 4: create each table in prod
for table in project.promoted_tables(TABLES):
    run_execute(project.load(table).create(), execute)

# Step 5: seed each prod table that reads itself, once, from its original
to_seed = project.promoted_tables(TABLES, seeded=True)
if not to_seed:
    print("Seeded nothing: no prod copy reads itself.")
else:
    run_execute(hive_settings("dynamic_partitions"), execute)
    for table in to_seed:
        run_execute(project.load(table).seed(), execute)

# Step 6: write each table in prod
project.run_tables(tables=project.promoted_tables(TABLES), execute=execute)

# Step 7: refresh the Reference sheet and the Database modules
project.refresh_reference_sheet(project.promoted_tables(TABLES))
```
