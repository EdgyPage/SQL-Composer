date: 2026-11-04
arm: C
model: haiku
files: 3c096cf

## T38

Workflow: convert, step 1 (convert the scripts).

```python
NAME = "alerts"
FILES = ["alerts.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {"default.high_alerts": "keep"}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

## T39

Workflow: convert, step 1 (convert the scripts).

```python
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}
PARTITION = {"dt": "2026-09-24"}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)

# Step 2: the Key is still open; fill in the "<FILL IN>" before step 3.
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "key": "<FILL IN>",
    }
}

project.write_decisions(DECISIONS)

for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)

to_seed = project.batch_tables(NAME, seeded=True)
if not to_seed:
    print("Seeded nothing: no table of the batch reads itself.")
else:
    run_execute(hive_settings("dynamic_partitions"), execute)
    for table in to_seed:
        run_execute(project.load(table).seed(), execute)

project.run_tables(tables=project.batch_tables(NAME), execute=execute)

project.compare_batch(NAME, query=query, partition=PARTITION)
```

The Decision left to you is the Key of mart_dev.daily_fails_mart, which the scripts do not name. Answer it in the decisions cell before running the write step.
