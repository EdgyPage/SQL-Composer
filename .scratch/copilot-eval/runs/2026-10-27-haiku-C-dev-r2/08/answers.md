date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T22

```python
from sqlglot_composer import FROM, SELECT, WHERE, compare_with_original, equals, statement
from references.ops__job_runs import job_runs
from warehouse import query

HIVE = "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-24'"

s0 = statement(
    SELECT(job_runs.run_id, job_runs.status),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
v = compare_with_original(s0, HIVE, query=query, partition={"dt": "2026-09-24"})
print(v)
```

This reads your Statement and your team's Hive through your `query`, on the one partition dt = 2026-09-24, and counts the rows that are in one result and not the other. The columns are run_id and status in the same order on both sides, so the comparison can run. The Verdict holds (`if v:` is true) when no rows differ in either direction. It does not hold when any row appears in one result and not the other, and `print(v)` says what it found.

## T23

```python
from sqlglot_composer import FROM, SELECT, compare_hive, statement
from references.ops__jobs import jobs

HIVE = "select r.job_id, r.job_name from ops.jobs r -- every job"

s0 = statement(SELECT(jobs.job_id, jobs.job_name), FROM(jobs))
v = compare_hive(s0, HIVE)
print(v)
```

This compares the text only. It runs nothing and sends nothing, so `query` and `execute` are not needed. The Verdict holds when the two texts agree once spacing, case, comments and short table names are set aside. A different condition would make it not hold. Your Hive has no WHERE, and ops.jobs has no partition column, so no partition bound is needed. The comment "-- every job" is ignored. The alias `r` on ops.jobs is the kind of difference the check is meant to skip, but I can't be sure from the description alone whether it counts as a short table name, so read what `print(v)` says.
