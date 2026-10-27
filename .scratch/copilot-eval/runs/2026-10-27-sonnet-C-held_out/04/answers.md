date: 2026-10-27
arm: C
model: sonnet
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
        equals(run_alerts.severity, "high"),
        equals(run_alerts.dt, "2026-09-24"),
        equals(job_runs.dt, "2026-09-24"),
    ),
)
```

This starts from the alerts and joins each one to its run on the run's Key (run_id), then to the run's job on the job's Key (job_id), so no row matches many. ops.run_alerts and ops.job_runs are both partitioned by dt, so each has its own bound on 2026-09-24 in WHERE. ops.jobs has no partitions and needs none. I used "high" as the severity value; change it if your data spells it differently. The job_runs bound assumes a run is stored under the same day as its alert. If a run can sit in an earlier partition, widen that bound with `between(...)` or `is_in(...)`.
