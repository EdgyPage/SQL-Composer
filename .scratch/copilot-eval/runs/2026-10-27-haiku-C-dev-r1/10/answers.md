date: 2026-10-27
arm: C
model: haiku
files: 353cbeeb

## T28

Each job gets its team label from a lookup. `team` can be NULL, and a NULL key isn't allowed in `mapped`, so the column is filled first. Any team not in the dict, including the filled value, gets "Other".

```python
from sqlglot_composer import AS, FROM, SELECT, fill_null, mapped, statement
from references.ops__jobs import jobs

TEAM_NAMES = {"data": "Data platform", "finance": "Finance"}

s = statement(
    SELECT(jobs.job_id,
           AS(mapped(fill_null(jobs.team, "Other"), TEAM_NAMES, otherwise="Other"), "team_label")),
    FROM(jobs),
)
```

The statement selects job_id and the team_label, and it stays a plain read with no partition bound because ops.jobs has no partitions.

## T29

Each job's name is passed through Hive's `upper` with `hive_function`, which the Toolbox doesn't wrap by name, and the result is named with AS.

```python
from sqlglot_composer import AS, FROM, SELECT, hive_function, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id,
           AS(hive_function("upper", jobs.job_name), "name_upper")),
    FROM(jobs),
)
```

Nothing here is hand-written Hive, and the statement is a read, so it would go to `run_query` when you run it.
