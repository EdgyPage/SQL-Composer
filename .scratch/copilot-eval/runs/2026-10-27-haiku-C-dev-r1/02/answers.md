date: 2026-10-27
arm: C
model: haiku
files: 353cbeeb

## T04

This Table reference names the table, gives each column its Hive type, marks `dt` as the partition column in both `columns` and `partitioned_by`, sets the Key to `job_id` and `dt`, and sets the `location` a Saved table needs. The variable is `t`, as you asked.

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

Save it as `references/mart__job_day_runs.py` so the file name matches the table name. Other code can then import it with `from references.mart__job_day_runs import t`.

## T05

This runs the Key check on `ops.job_runs` for the one partition 2026-09-24, using your `query`. The table is partitioned by `dt`, so the check is bounded on `dt` with `where=`. The result is a Verdict in `v`, and `print(v)` says whether the Key `run_id` holds.

```python
from sqlglot_composer import check_key, equals
from references.ops__job_runs import job_runs
from warehouse import query

v = check_key(job_runs, query=query, where=equals(job_runs.dt, "2026-09-24"))
print(v)
```
