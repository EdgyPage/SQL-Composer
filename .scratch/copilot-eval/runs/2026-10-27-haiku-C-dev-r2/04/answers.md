date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T10

```python
from sqlglot_composer import FROM, JOIN, SELECT, WHERE, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, jobs.job_name, job_runs.status),
    FROM(job_runs),
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
```

This joins each run to its job on job_id, which is the Key of ops.jobs, so each run matches at most one job. JOIN keeps only the runs that have a matching job. The job_runs table is partitioned by dt, so its bound is the equals on job_runs.dt in WHERE. ops.jobs is not partitioned and needs no bound. Use run_query(s, query) to read it.

## T11

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, all_of, count_distinct,
                              equals, statement)
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, AS(count_distinct(job_runs.run_id), "runs")),
    FROM(jobs),
    LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
                                  equals(job_runs.dt, "2026-09-24"))),
    GROUP_BY(jobs.job_id, jobs.job_name),
)
```

LEFT_JOIN keeps every job, and a job with no run that day gets NULL for run_id, which count_distinct counts as 0. The date bound on job_runs.dt sits inside ON= rather than WHERE, because job_runs is partitioned and the join is a LEFT_JOIN. count_distinct counts runs rather than joined rows. job_name is in GROUP_BY because it is selected next to the aggregate. Run it with run_query(s, query).
