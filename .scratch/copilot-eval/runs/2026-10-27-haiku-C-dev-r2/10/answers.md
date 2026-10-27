date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T28

```python
from sqlglot_composer import AS, FROM, SELECT, mapped, statement
from references.ops__jobs import jobs

TEAM_LABEL = {"data": "Data platform", "finance": "Finance"}

s = statement(
    SELECT(jobs.job_id,
           AS(mapped(jobs.team, TEAM_LABEL, otherwise="Other"), "team_label")),
    FROM(jobs),
)
```

This builds one row per job with its team label. The lookup is a single-column mapped, so any team not in the dict, such as one not named data or finance, gets "Other". The dict is a constant at the top. ops.jobs has no partitions named here, so it needs no partition bound.

## T29

```python
from sqlglot_composer import AS, FROM, SELECT, hive_function, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id,
           AS(hive_function("upper", jobs.job_name), "name_upper")),
    FROM(jobs),
)
```

This uses Hive's upper through hive_function, since the Toolbox doesn't wrap it, and names the result name_upper with AS. Nothing here is hand-written Hive.
