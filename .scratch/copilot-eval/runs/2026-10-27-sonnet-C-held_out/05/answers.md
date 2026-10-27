date: 2026-10-27
arm: C
model: sonnet
files: 95fbcd5

## T15

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, between, lag, statement, window
from references.ops__job_runs import job_runs

# Each job's runs in run_id order; lag looks at the run just before.
each_job = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id)

s = statement(
    SELECT(
        job_runs.run_id,
        job_runs.job_id,
        job_runs.duration_mins,
        AS(lag(job_runs.duration_mins, over=each_job), "minutes_before"),
    ),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
)
```

This takes the minutes of the previous run of the same job, in run_id order, and the read is bounded on `dt` from 2026-09-23 to 2026-09-24. `minutes_before` is empty (NULL) for a job's first run in that range. The previous run is looked for only inside those two days, so a job's first run on 2026-09-23 doesn't see a run from 2026-09-22. If you want those filled, widen the `dt` bound to start earlier. Then keep only the two days in a Statement that reads this one as a Derived table.
