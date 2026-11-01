date: 2026-10-31
arm: C
model: haiku
files: 72f183d3

## T33

You are at step 2 of convert, answering the table's open Decisions. Step 1 (the convert call) has already run, so it is left out. Run these cells in order. The decisions cell holds your two answers, dt as string and the folder as given; its shape follows the notebook's own DECISIONS template, which this file does not show.

```python
# Names cell (convert notebook)
NAME = "daily_fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
STAGING = None
```

```python
# Decisions cell: your answers for mart_dev.daily_fails_mart
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "dt": "string",
        "location": "/data/team/mart_dev.db/daily_fails",
    },
}
```

```python
# Step 3: write each answer into its table's Table reference
project.write_decisions(DECISIONS)
```

```python
# Step 4: create each table in dev
for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)
```

```python
# Step 5: seed each table that reads itself, once, from its original
run_execute(hive_settings("dynamic_partitions"), execute)
for table in project.batch_tables(NAME, seeded=True):
    run_execute(project.load(table).seed(), execute)
```

```python
# Step 6: write each table in dev
project.run_tables(tables=project.batch_tables(NAME), execute=execute)
```

```python
# Step 7: compare each table with its original
project.compare_batch(NAME, query=query)
```
