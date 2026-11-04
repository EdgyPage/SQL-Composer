date: 2026-11-04
arm: C
model: haiku
files: 1224d14

## T38

Workflow: convert, at step 1 (convert the scripts). The names cell and the first step's cell:

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

Workflow: convert, at step 1 (convert the scripts), taken through to step 7 (compare). Every step's cell, in order, with the names cell first:

```python
# Names cell
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}
PARTITION = None

# Step 1: convert
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)

# Step 2: decisions cell (the Key is still open, for you to answer)
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "key": "<FILL IN>",
    }
}

# Step 3: write each answer into its table's Table reference
project.write_decisions(DECISIONS)

# Step 4: create each table in dev
for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)

# Step 5: seed each table that reads itself, once
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

Decision left to you: the Key of mart_dev.daily_fails_mart (the table is written with job_id and fails by the script, and its Key is not given). Fill in the "<FILL IN>" in the decisions cell before step 3 runs. Later steps, in words: step 3 writes your answers into the Table reference, step 4 creates the table in dev, step 5 seeds nothing because no table of the batch reads itself, step 6 writes the table in dev, and step 7 compares it with mart.daily_fails.

## T46

Workflow: convert, at step 1 (convert the scripts), taken through to step 7 (compare). Every step's cell, in order, with the names cell first. The two Script tags are answered as Decisions under "tags": RUN_DAY is a bare tag, so its value keeps its own quotes, and STATUS sits inside quotes in the script, so its value has none:

```python
# Names cell
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}
PARTITION = None

# Step 1: convert
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)

# Step 2: decisions cell (the Key is still open, for you to answer)
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "key": "<FILL IN>",
        "tags": {
            "RUN_DAY": "'2026-09-24'",
            "STATUS": "FAILED",
        },
    }
}

# Step 3: write each answer into its table's Table reference
project.write_decisions(DECISIONS)

# Step 4: create each table in dev
for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)

# Step 5: seed each table that reads itself, once
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

Decision left to you: the Key of mart_dev.daily_fails_mart, which you have not given; fill in the "<FILL IN>" in the decisions cell before step 3 runs. Later steps, in words: step 3 writes your answers into the Table reference, step 4 creates the table in dev, step 5 seeds nothing because no table of the batch reads itself, step 6 writes the table in dev, and step 7 compares it with mart.daily_fails.
