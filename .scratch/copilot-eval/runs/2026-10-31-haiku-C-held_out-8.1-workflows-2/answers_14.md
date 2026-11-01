date: 2026-10-31
arm: C
model: haiku
files: de6bc5fc

## T36

You are in the new_table Workflow, at its first step: making the Table folder for mart_dev.ok_runs from ok_runs.hql. Run the names cell, then the first step's cell.

```python
# Names cell (admin/workflows/new_table/new_table.ipynb)
TABLES = ["mart_dev.ok_runs"]
QUERIES = {"ok_runs": "ok_runs.hql"}

# Step 1 cell: makes the Table folder from the query (it changes only files)
project.new_table(TABLES, queries=QUERIES)
```
