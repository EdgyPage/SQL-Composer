date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T15

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, between, derived, lag, statement, window
from references.ops__job_runs import job_runs

each_job = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id)
prior = derived("prior", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(lag(job_runs.duration_mins, over=each_job), "minutes_before")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-22", "2026-09-24")),
))
s = statement(
    SELECT(prior.run_id, prior.job_id, prior.duration_mins, prior.minutes_before),
    FROM(prior),
    WHERE(between(prior.dt, "2026-09-23", "2026-09-24")),
)
```

The Derived table reads 2026-09-22 through 2026-09-24, so the first run of 2026-09-23 can see the run before it, which is the same job's run with the next lower run_id. The outer Statement then keeps only the runs from 2026-09-23 to 2026-09-24. A run whose earlier run falls before 2026-09-22 shows an empty minutes_before, because that day isn't read; widen the between in the Derived table if those earlier runs should count.
