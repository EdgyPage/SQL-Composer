date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T21

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, all_of, equals, mapped, statement
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

j = AS(jobs, "j")
r = AS(job_runs, "r")

TEAM_NAMES = {"data": "Data", "web": "Web"}

s = statement(
    SELECT(
        j.job_name,
        AS(mapped(j.team, TEAM_NAMES, otherwise="Other"), "team_name"),
        r.run_id,
    ),
    FROM(j),
    LEFT_JOIN(
        r,
        ON=all_of(
            equals(r.job_id, j.job_id),
            equals(r.dt, "2026-09-24"),
        ),
    ),
)
```

ops.job_runs is partitioned by dt, so its read is bounded by `equals(r.dt, "2026-09-24")` inside ON=, as the Hive's ON bounded it. ops.jobs has no partitions, so it needs no bound. The CASE became `mapped(...)` with a constant dict, named `team_name`. The columns come out in the Hive's order: job_name, team_name, run_id.

No part is kept as Hive.
