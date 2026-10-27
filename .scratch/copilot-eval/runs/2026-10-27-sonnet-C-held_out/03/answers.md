date: 2026-10-27
arm: C
model: sonnet
files: 95fbcd5

## T09

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, HAVING, SELECT, WHERE, average_of,
                              between, more_than, statement)
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_minutes")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(job_runs.job_id),
    HAVING(more_than(average_of(job_runs.duration_mins), 15)),
)
```

The WHERE bounds the partitioned table on `dt` to the two days. The Statement groups the runs by job and averages `duration_mins`, and HAVING keeps only the jobs whose average is over 15. Run it with `run_query(s, query)` after `from warehouse import query`.
