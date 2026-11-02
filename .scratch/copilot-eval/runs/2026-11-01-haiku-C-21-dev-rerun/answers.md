date: 2026-11-01
arm: C
model: haiku
files: 21-dev-rerun

## T16

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, count_rows,
                              equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

s = statement(
    INSERT_OVERWRITE(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
```

The WHERE bounds the read of ops.job_runs to 2026-09-24, and GROUP_BY over job_id and dt gives one row per Key of mart.job_day_runs. INSERT_OVERWRITE replaces that day's Partition, and dt is the last column of SELECT. To send it, add `from warehouse import query, execute` and run `run_execute(s, execute)`.

## T17

```python
# logic
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause,
                              Statement, count_rows, create_table, equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

DAY = "2026-09-24"
PARTITIONED_BY = ["dt"]


def create() -> Statement:
    return create_table(job_day_runs, may_exist=True)


def rows(day: str) -> list[Clause]:
    return [
        SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, day)),
        GROUP_BY(job_runs.job_id, job_runs.dt),
    ]


def preview() -> Statement:
    return statement(*rows(DAY))


def write() -> Statement:
    return statement(INSERT_OVERWRITE(job_day_runs), *rows(DAY))
```

The logic cell holds only imports, constants and functions, and runs no Hive. Its read of ops.job_runs is bounded to the day by equals on dt, and write() replaces DAY's Partition of mart.job_day_runs. Next, the Table notebook's run_tables cell sends the writes, and the export_hive cell writes the .hql file once the notebook is saved.

## T31

Workflow: convert (someone else's Hive into Saved tables in dev), at step 1, convert the scripts.

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

Decisions left to you: the open Decisions for the two tables are not known until `project.check()` runs after the convert. Answer each one in the decisions cell; they are yours to make.

Later steps, in words:
- Step 2: answer each table's open Decisions in the decisions cell.
- Step 3: write each answer into its table's Table reference with `project.write_decisions(DECISIONS)`.
- Step 4: create each table in dev, one at a time, for every table in the batch.
- Step 5: seed each table that reads itself, once, from its original, if convert names one; the dynamic partitions setting goes first.
- Step 6: write each table in dev with `project.run_tables`.
- Step 7: compare each table with its original with `project.compare_batch`. A table is promoted only once its compare has passed.

## T32

Workflow: convert (someone else's Hive into Saved tables in dev), at step 1, convert the scripts, with the staging table ops_reports.failed_runs folded.

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

Decisions left to you: the open Decisions are not known until `project.check()` runs after the convert; answer each one in the decisions cell. Folded, ops_reports.failed_runs is never made; its query goes inside mart_dev's fails_per_job table.

Later steps, in words:
- Step 2: answer each table's open Decisions in the decisions cell.
- Step 3: write each answer into its table's Table reference with `project.write_decisions(DECISIONS)`.
- Step 4: create each table in dev, one at a time, for every table in the batch.
- Step 5: seed each table that reads itself, once, from its original, if convert names one; the dynamic partitions setting goes first.
- Step 6: write each table in dev with `project.run_tables`.
- Step 7: compare each table with its original with `project.compare_batch`. A table is promoted only once its compare has passed.

## T33

Workflow: convert (the batch fails), at step 2, answer the open Decisions; step 3 writes them into the Table reference.

```python
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}

DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "types": {"dt": "string"},
    },
}

project.write_decisions(DECISIONS)
```

Decisions left to you: none. Both open Decisions for mart_dev.daily_fails_mart are answered above: its location and dt's type as string.

Later steps, in words, which you run yourself:
- Step 4: create each table in dev, one at a time, for every table in the batch.
- Step 5: seed each table that reads itself, once, from its original, if convert names one; the dynamic partitions setting goes first.
- Step 6: write each table in dev with `project.run_tables`.
- Step 7: compare each table with its original with `project.compare_batch`. The table is promoted only once its compare has passed.

## T37

Workflow: convert (someone else's Hive into Saved tables in dev), at step 1, convert the query.

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

Decisions left to you: the open Decisions are not known until `project.check()` runs after the convert; answer each one in the decisions cell.

Later steps, in words:
- Step 2: answer each table's open Decisions in the decisions cell.
- Step 3: write each answer into its table's Table reference with `project.write_decisions(DECISIONS)`.
- Step 4: create each table in dev, one at a time, for every table in the batch.
- Step 5: seed each table that reads itself, once, from its original, if convert names one; the dynamic partitions setting goes first.
- Step 6: write each table in dev with `project.run_tables`.
- Step 7: compare each table with its original with `project.compare_batch`. A table is promoted only once its compare has passed.
