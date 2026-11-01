date: 2026-10-31
arm: C
model: haiku
files: c8c63aed

## T21

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, all_of, equals, mapped, statement
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

j = AS(jobs, "j")
r = AS(job_runs, "r")

s = statement(
    SELECT(
        j.job_name,
        AS(mapped(j.team, {"data": "Data", "web": "Web"}, otherwise="Other"), "team_name"),
        r.run_id,
    ),
    FROM(j),
    LEFT_JOIN(r, ON=all_of(equals(r.job_id, j.job_id), equals(r.dt, "2026-09-24"))),
)
```

Nothing is kept as Hive. The CASE becomes `mapped(...)`, named `team_name` with AS. The `r.dt = '2026-09-24'` condition stays inside `ON=` with `all_of`, which bounds the partitioned `ops.job_runs` read as the Hive did. `ops.jobs` has no partitions, so it needs no bound.
