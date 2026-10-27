date: 2026-10-27
arm: C
model: haiku
files: 353cbeeb

## T10

Each run on 2026-09-24 with its job's name. The FROM table is partitioned by dt, so it gets its bound in WHERE. The jobs table is not partitioned, so it needs no bound.

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

This is an inner join, so a run whose job is missing from ops.jobs is left out. The statement is assigned to `s`. Run it with `run_query(s, query)` after `from warehouse import query, execute`.

## T11

Every job with its run count on 2026-09-24, with 0 for jobs that had no runs. The LEFT_JOIN keeps every job. Its partition bound on job_runs.dt goes inside ON=, not WHERE, so it does not throw away the jobs with no match. The count uses count_distinct on job_runs.run_id, which gives 0 for a job with no match where count_rows() would give 1. GROUP_BY names job_name as well as job_id, since job_name is selected too.

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

The statement is assigned to `s`. Run it with `run_query(s, query)` after `from warehouse import query, execute`.
