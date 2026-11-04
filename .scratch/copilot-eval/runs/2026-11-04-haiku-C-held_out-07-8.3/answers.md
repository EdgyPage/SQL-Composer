date: 2026-11-04
arm: C
model: haiku
files: 3c096cf

## T21

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, all_of, equals, mapped, statement
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
    # job_runs is partitioned by dt, so its read is bounded inside ON=;
    # matching r.job_id to j.job_id bounds nothing on its own.
    LEFT_JOIN(r, ON=all_of(equals(r.job_id, j.job_id), equals(r.dt, "2026-09-24"))),
)
```

No part is kept as Hive: the CASE, the LEFT JOIN and its ON condition, including `r.dt = '2026-09-24'`, are all converted.
