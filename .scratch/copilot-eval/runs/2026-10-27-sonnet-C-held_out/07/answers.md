date: 2026-10-27
arm: C
model: sonnet
files: 95fbcd5

## T21

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, all_of, equals, mapped,
                              statement)
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

TEAM_NAMES = {"data": "Data", "web": "Web"}

j = AS(jobs, "j")
r = AS(job_runs, "r")

s = statement(
    SELECT(
        j.job_name,
        AS(mapped(j.team, TEAM_NAMES, otherwise="Other"), "team_name"),
        r.run_id,
    ),
    FROM(j),
    LEFT_JOIN(r, ON=all_of(equals(r.job_id, j.job_id), equals(r.dt, "2026-09-24"))),
)
```

Nothing was kept as Hive. The `CASE j.team WHEN ...` becomes `mapped(...)` with `otherwise="Other"`. `ops.job_runs` is partitioned by `dt`, so the `r.dt = '2026-09-24'` condition stays inside the join's `ON=`, as the Hive had it. `ops.jobs` has no partitions, so it needs no bound.
