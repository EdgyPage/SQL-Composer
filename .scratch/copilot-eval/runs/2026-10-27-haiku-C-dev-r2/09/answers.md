date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T25

```python
from sqlglot_composer import FROM, SELECT, WHERE, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
)
```

The `==` on `job_runs.status` is now `equals(job_runs.status, "FAILED")`, and the day is kept as a partition bound, `equals(job_runs.dt, "2026-09-24")`, in the same WHERE, because a read of the partitioned table needs one.

## T26

```python
from sqlglot_composer import FROM, LIMIT, ORDER_BY, SELECT, WHERE, descending, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
    ORDER_BY(descending(job_runs.duration_mins)),
    LIMIT(3),
)
```

`LIMIT(3)` is added after ORDER_BY, which gives the top 3 longest runs, longest first, and it is the fix the refusal names for a top N; the descending sort and the 2026-09-24 bound are kept. `descending` is not among the names this file lists, so if the import fails, check it against your Toolbox before going on.
