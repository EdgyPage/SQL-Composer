date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T12

```python
from sqlglot_composer import FROM, JOIN, SELECT, WHERE, equals, statement
from references.ops__run_alerts import run_alerts
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(run_alerts.alert_id, jobs.job_name),
    FROM(run_alerts),
    JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    WHERE(
        equals(run_alerts.dt, "2026-09-24"),
        equals(job_runs.dt, "2026-09-24"),
        equals(run_alerts.severity, "high"),
    ),
)
```

This joins each alert to its run on run_id, the whole Key of ops.job_runs, and then each run to its job on job_id, the whole Key of ops.jobs. Both partitioned tables, ops.run_alerts and ops.job_runs, are bounded to 2026-09-24 in WHERE with a value, and ops.jobs has no partitions, so it needs no bound. The severity filter assumes the stored value is "high"; if the column holds another spelling, change that string.
