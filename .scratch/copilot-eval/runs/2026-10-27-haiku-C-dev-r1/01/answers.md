date: 2026-10-27
arm: C
model: haiku
files: 353cbeeb

## T01

Read each job's name and team from the one-table reference `jobs`. The table has no partitions, so it needs no bound. The Statement is run with `run_query(s, query)`, which gives a DataFrame.

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

The two columns come from the Table reference, so `jobs.job_name` and `jobs.team` are read as `table.column`. The last line runs the read with your `query` function and returns the rows.

## T02

Using the Database module, `ops.job_runs` is partitioned by `dt`, so the read is bounded on `dt` in WHERE. The Statement lists `run_id` and `status` for 2026-09-24 and is assigned to `s`. Add `run_query(s, query)` after it if you want the rows.

```python
from sqlglot_composer import FROM, SELECT, WHERE, equals, statement
from references import ops

s = statement(
    SELECT(ops.job_runs.run_id, ops.job_runs.status),
    FROM(ops.job_runs),
    WHERE(equals(ops.job_runs.dt, "2026-09-24")),
)
```
