date: 2026-10-27
arm: C
model: haiku
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

This builds the Statement in `s` for the jobs whose runs from 2026-09-23 to 2026-09-24 average more than 15 minutes. The job_runs table is partitioned by dt, so the WHERE bounds it with `between` on that column. Each job_id is grouped, and the average is named `avg_minutes`. To run it, call `run_query(s, query)` after `from warehouse import query`.
