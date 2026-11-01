date: 2026-11-01
arm: C
model: haiku
files: de6bc5fc

## T34

You are in the references Workflow, at its first step: write the Table references from DESCRIBE. Run the names cell, then the step cell.

```python
# Cell 1, names
NAME = "references"
TABLES = ["ops.jobs", "ops.run_alerts"]

# Cell 2, step 1: write the Table references from DESCRIBE (a call to the warehouse)
project.add_references(TABLES, query=query)
```

## T35

You are in the new_table Workflow, at its first step: make each Table folder. You have no query, so QUERIES stays empty and you write the logic yourself. Run the names cell, then the step cell.

```python
# Cell 1, names
NAME = "new_table"
TABLES = ["mart_dev.job_day_counts"]
QUERIES = {}

# Cell 2, step 1: make each Table folder (it changes only files, so project.do_next() runs it for you)
project.new_table(TABLES, queries=QUERIES)
```
