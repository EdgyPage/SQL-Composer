date: 2026-10-27
arm: C
model: sonnet
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

This uses `first_match` for the chain, so the first condition that holds gives the label: "failed" for a FAILED status, else "slow" when `duration_mins` is more than 25, else "ok". The `label` column is named with AS. The WHERE bounds the read to the `2026-09-24` partition of `dt`. The statement is a read, so you would run it with `run_query(s, query)`. Nothing in it is hand-written Hive.
