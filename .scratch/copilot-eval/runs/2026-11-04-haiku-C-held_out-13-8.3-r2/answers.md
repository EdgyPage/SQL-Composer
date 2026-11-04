date: 2026-11-04
arm: C
model: haiku
files: 22aa474

## T38

Workflow: convert (batch `alerts`), step 1: convert the scripts.

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

Left to you after this step: step 2 is answering each table's open Decisions in the decisions cell (convert's step 1 prints a DECISIONS to paste, with each answer still `"<FILL IN>"`; fill in the ones for `mart_dev.high_alerts_per_run` and `default.high_alerts`, such as location or Key). Step 3 writes those answers into the Table references with `project.write_decisions(DECISIONS)`. Step 4 creates each table in dev, step 5 seeds any table that reads itself, step 6 writes each table in dev with `project.run_tables`, and step 7 compares each table with its original with `project.compare_batch(NAME, query=query, partition=PARTITION)`.

## T39

Workflow: convert (batch `fails`), step 1: convert the scripts. Every step's cell is below, in order; the Decision answer for the location is filled in, and the other Decisions are yours to answer in the decisions cell.

```python
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}
PARTITION = None

# Step 1: convert the scripts
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)

# Step 2: decisions cell (the location is answered; any other open Decision for
# mart_dev.daily_fails_mart is yours to fill in here)
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
    },
}

# Step 3: write each answer into its table's Table reference
project.write_decisions(DECISIONS)

# Step 4: create each table in dev
for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)

# Step 5: seed each table that reads itself, once, from its original
to_seed = project.batch_tables(NAME, seeded=True)
if not to_seed:
    print("Seeded nothing: no table of the batch reads itself.")
else:
    run_execute(hive_settings("dynamic_partitions"), execute)
    for table in to_seed:
        run_execute(project.load(table).seed(), execute)

# Step 6: write each table in dev
project.run_tables(tables=project.batch_tables(NAME), execute=execute)

# Step 7: compare each table with its original
project.compare_batch(NAME, query=query, partition=PARTITION)
```
