date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T04

This is a new Saved table, so the Table reference gives it a `location=`, a Key of `job_id` and `dt`, and `partitioned_by=["dt"]` with `dt` listed in `columns` as well. Save it as `references/mart__job_day_runs.py`, which is the file name that matches `mart.job_day_runs`. The variable is `t`, as you asked; the file's own convention would name it `job_day_runs`.

```python
from sqlglot_composer import Table

t = Table(
    "mart.job_day_runs",
    columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    partitioned_by=["dt"],
    key=["job_id", "dt"],
    location="/data/your_team/mart.db/job_day_runs",
)
```

## T05

This reads ops.job_runs with your `query`, so the check takes `query=query`. ops.job_runs is partitioned by `dt`, so the check is bounded with `where=equals(job_runs.dt, "2026-09-24")` to read only that day. The Key is `run_id`, which the check counts on that day's partition.

```python
from references.ops__job_runs import job_runs
from sqlglot_composer import check_key, equals
from warehouse import query

v = check_key(job_runs, query=query, where=equals(job_runs.dt, "2026-09-24"))
```
