date: 2026-11-04
arm: C
model: haiku
files: 22aa474

## T31

Workflow: convert (Hive into Saved tables in dev). Your step: 1, convert the scripts.

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

After this run, the rest is yours in order: step 2 answers each table's open Decisions in the decisions cell (only you can give those answers), step 3 writes them into the Table references, step 4 creates each table in dev, step 5 seeds any table that reads itself, step 6 writes each table in dev, and step 7 compares each with its original.

## T32

Workflow: convert (Hive into Saved tables in dev). Your step: 1, convert the scripts.

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
GROUP BY f.job_id;"""
DATABASE = "default"
RENAME = {}
STAGING = {"ops_reports.failed_runs": "fold"}

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

After this run, the rest is yours in order: step 2 answers each table's open Decisions in the decisions cell, step 3 writes them into the Table references, step 4 creates each table in dev, step 5 seeds any table that reads itself, step 6 writes each table in dev, and step 7 compares each with its original. The staging table ops_reports.failed_runs is folded into mart_dev.fails_per_job and is never made as its own table.

## T33

Workflow: convert (Hive into Saved tables in dev). Your step: 2, answer the Decisions, then step 3, write them.

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
    },
}

# write cell
project.write_decisions(DECISIONS)
```

No Decision is left open for this table. Once you have run the write cell, the steps after it are yours in order: step 4 creates each table in dev, step 5 seeds any table that reads itself, step 6 writes each table in dev, and step 7 compares each with its original.

## T37

Workflow: convert (Hive into Saved tables in dev). Your step: 1, convert the query.

```python
# names cell
NAME = "runs_per_job"
FILES = []
HIVE = """SELECT r.job_id, COUNT(*) AS runs
FROM job_runs r
WHERE r.dt = '2026-09-24'
GROUP BY r.job_id"""
DATABASE = "ops"
RENAME = {}
STAGING = {}

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

The query only SELECTs, so it makes a Saved table named runs_per_job. Its tables with no database name, such as job_runs, are read from ops. No rename was given, so the default rename applies. After this run, the rest is yours in order: step 2 answers the Decisions, step 3 writes them, and steps 4 to 7 create, seed, write and compare the table.

## T45

Workflow: convert (Hive into Saved tables in dev). Your step: 2, answer the Decisions, which is open on RUN_DAY.

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
        "tags": {"RUN_DAY": "<FILL IN>"},
    },
}

# write cell
project.write_decisions(DECISIONS)
```

Left for you: the RUN_DAY tag. Its value changes each run, so it is not a literal I can guess. Choose one of two answers. Either the scheduler sets the day through a SET hivevar line kept in daily_fails.hql, and the answer is "'${hivevar:run_day}'" (the script then needs that SET line), or you want the literal day for this run only, "'2026-09-24'". Replace "<FILL IN>" with your choice before running the write cell. The location and dt type are answered above.

After the write cell, the steps after it are yours in order: step 4 creates each table in dev, step 5 seeds any table that reads itself, step 6 writes each table in dev, and step 7 compares each with its original.
