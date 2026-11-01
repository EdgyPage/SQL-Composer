date: 2026-10-31
arm: C
model: haiku
files: de6bc5fc

## T33

Workflow: convert, batch daily_fails. You are at step 2 (answer the Decisions). Step 1, the convert, has already run, so its cell is not repeated. The decisions cell holds your two answers under the name project.check() wrote. The .hql writes mart.daily_fails, but check() names mart_dev.daily_fails_mart, so confirm that name is the one you mean before you run the write cell. The last cell of the notebook, project.run_workflow(...), runs the steps left; its arguments are not in the file, so they are not written here.

```python
# Names cell (admin/workflows/convert/daily_fails.ipynb)
NAME = "daily_fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
STAGING = None
query = None  # the batch is one .hql file, so no query text

# Decisions cell (step 2: your answers, as project.check() wrote them)
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "types": {"dt": "string"},
    },
}

# Write cell (step 3: writes the answers into the Table reference)
project.write_decisions(DECISIONS)

# Step 4: create each table in dev
for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)

# Step 5: seed each table that reads itself, once (none here: daily_fails reads ops.job_runs)
run_execute(hive_settings("dynamic_partitions"), execute)
for table in project.batch_tables(NAME, seeded=True):
    run_execute(project.load(table).seed(), execute)

# Step 6: write each table in dev
project.run_tables(tables=project.batch_tables(NAME), execute=execute)

# Step 7: compare each table with its original
project.compare_batch(NAME, query=query)
```

## T36

You are in the new_table Workflow, at its first step: making the Table folder for mart_dev.ok_runs from ok_runs.hql. Run the names cell, then the first step's cell.

```python
# Names cell (admin/workflows/new_table/new_table.ipynb)
TABLES = ["mart_dev.ok_runs"]
QUERIES = {"ok_runs": "ok_runs.hql"}

# Step 1 cell: makes the Table folder from the query (it changes only files)
project.new_table(TABLES, queries=QUERIES)
```
