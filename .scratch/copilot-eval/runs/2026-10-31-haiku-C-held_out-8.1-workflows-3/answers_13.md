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
