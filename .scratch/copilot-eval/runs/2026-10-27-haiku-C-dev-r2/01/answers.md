date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T01

```python
from sqlglot_composer import FROM, SELECT, run_query, statement
from references.ops__jobs import jobs
from warehouse import query

s = statement(
    SELECT(jobs.job_name, jobs.team),
    FROM(jobs),
)
rows = run_query(s, query)
```

This reads job_name and team from ops.jobs and runs the read with your `query`. The jobs table has no partition columns, so it needs no bound.

## T02

```python
from sqlglot_composer import FROM, SELECT, WHERE, equals, statement
from references import ops

s = statement(
    SELECT(ops.job_runs.run_id, ops.job_runs.status),
    FROM(ops.job_runs),
    WHERE(equals(ops.job_runs.dt, "2026-09-24")),
)
```

This builds the Statement for run_id and status from ops.job_runs on 2026-09-24. The `dt` partition column is bounded in WHERE with `equals`. To run it, call `run_query(s, query)` after importing `query` from warehouse.
