date: 2026-10-31
arm: C
model: haiku
files: 72f183d3

## T36

You are at step 1 of the new_table Workflow: make the Table folder from your query. Names cell first, then step 1's cell.

```python
# Names cell (admin/workflows/new_table/new_table.ipynb)
TABLES = ["mart_dev.ok_runs"]
QUERIES = {"ok_runs": "ok_runs.hql"}

# Step 1 cell: make each Table folder, converting each table's query QUERIES gives
project.new_table(TABLES, queries=QUERIES)
```
