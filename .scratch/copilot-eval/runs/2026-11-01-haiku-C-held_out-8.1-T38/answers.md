date: 2026-11-01
arm: C
model: haiku
files: e805b0a4

## T38

This is the convert Workflow, batch `alerts`, at its first step: converting the scripts into your Dev Database. Run the names cell, then the step 1 cell. Keeping `high_alerts` makes it a Saved table of its own, and the Decisions that come after this step are yours to answer in the decisions cell.

```python
# names cell
NAME = "alerts"
FILES = ["alerts.hql"]
HIVE = None
DATABASE = "default"
STAGING = {"default.high_alerts": "keep"}

# step 1 cell: convert the scripts into dev
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                staging=STAGING)
```
