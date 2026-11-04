date: 2026-11-04
arm: C
model: haiku
files: 1224d14

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
    LEFT_JOIN(
        r,
        ON=all_of(equals(r.job_id, j.job_id), equals(r.dt, "2026-09-24")),
    ),
)
```

Parts kept as Hive: none. Every part is converted; the `r.dt = '2026-09-24'` condition stays in the LEFT JOIN's ON= because job_runs is partitioned by dt.

## T44

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, equals, script_tag, statement
from references.ops__job_runs import job_runs

TAGS = {"RUN_DAY": "2026-09-24", "STATUS": "FAILED"}

r = AS(job_runs, "r")

s = statement(
    SELECT(r.job_id, AS(count_rows(), "runs")),
    FROM(r),
    WHERE(
        equals(r.dt, script_tag(TAGS["RUN_DAY"])),
        equals(r.status, TAGS["STATUS"]),
    ),
    GROUP_BY(r.job_id),
)
```

Parts kept as Hive: none. Both Script tags are converted: `<PARM="RUN_DAY"/>` becomes `script_tag(TAGS["RUN_DAY"])` and `'<PARM="STATUS"/>'` becomes `TAGS["STATUS"]`.
