date: 2026-10-31
arm: C
model: haiku
files: de6bc5fc

## T33

You are at step 2 of the convert Workflow, `admin/workflows/convert/fails/fails.ipynb`, after the convert call in step 1. The decisions cell answers the two open Decisions from `project.check()`, and the write cell puts them into the Table reference.

```python
NAME = "fails"
FILES = ["daily_fails.hql"]
DATABASE = "default"
STAGING = None

DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "types": {"dt": "string"},
    },
}

project.write_decisions(DECISIONS)
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
