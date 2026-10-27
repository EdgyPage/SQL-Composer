date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T30

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, equals, first_match, more_than, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id,
           AS(first_match([(equals(job_runs.status, "FAILED"), "failed"),
                           (more_than(job_runs.duration_mins, 25), "slow")],
                          otherwise="ok"), "label")),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
```

This builds the Statement for ops.job_runs on 2026-09-24, with the run_id and a label. The WHERE on dt bounds the read to that one partition, since job_runs is partitioned by dt. first_match checks the conditions in order, so a FAILED run gets "failed" even if it also took more than 25 minutes, and a run that is not failed but took more than 25 minutes gets "slow". Every other run gets "ok". To run it, pass s to run_query with your query call, after `from warehouse import query, execute`.
