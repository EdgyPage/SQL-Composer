date: 2026-10-27
arm: C
model: haiku
files: 353cbeeb

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

The Python `==` on status became `equals(job_runs.status, "FAILED")`, and I added the partition bound `equals(job_runs.dt, "2026-09-24")` because ops.job_runs is partitioned by dt and FROM needs a bound on it to read that day.

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

I added `LIMIT(3)` after ORDER_BY, since ORDER_BY needs a LIMIT and a top 3 is what LIMIT(n) is for, and kept your dt bound and descending sort. `descending` is your name and is not among the names in this file, so check that it exists in the Toolbox before running.
