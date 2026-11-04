date: 2026-11-04
arm: C
model: haiku
files: 22aa474

## T21

Each part is converted; none is kept as Hive. The CASE becomes a `mapped` column named `team_name`, and the LEFT JOIN keeps its `dt` bound inside `ON=`.

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

## T44

Parts kept as Hive: none. The two Script tags stay as `script_tag` and `TAGS` lookups, and the scheduler fills them in at run time. The `TAGS` name must be imported from the Table reference that holds your values, which you did not list, so add that import before running.

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, equals, script_tag, statement
from references.ops__job_runs import job_runs
# TAGS: import it from your Table reference that holds the values (RUN_DAY, STATUS); it is not in the references listed above.
from references import ops  # noqa: F401  (kept for the ops tables by name)

r = AS(job_runs, "r")

s = statement(
    SELECT(r.job_id, AS(count_rows(), "runs")),
    FROM(r),
    WHERE(equals(r.dt, script_tag(TAGS["RUN_DAY"])), equals(r.status, TAGS["STATUS"])),
    GROUP_BY(r.job_id),
)
```
