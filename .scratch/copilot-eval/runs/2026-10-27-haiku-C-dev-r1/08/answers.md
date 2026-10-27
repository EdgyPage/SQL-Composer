date: 2026-10-27
arm: C
model: haiku
files: 353cbeeb

## T22

This runs your query on the 2026-09-24 Partition of `ops.job_runs` and compares the rows from your Statement with the rows from the team's Hive. The Verdict holds when both return the same rows on that day, and it doesn't hold when a row appears in one and not the other.

```python
from sqlglot_composer import FROM, SELECT, WHERE, compare_with_original, equals, statement
from references.ops__job_runs import job_runs
from warehouse import query

HIVE = "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-24'"

s0 = statement(SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
               WHERE(equals(job_runs.dt, "2026-09-24")))

v = compare_with_original(s0, HIVE, query=query, partition={"dt": "2026-09-24"})
print(v)
```

The Hive's columns are run_id and status, in that order, the same as the Statement's, so the rows can be compared. Because `job_runs` is partitioned by dt, the check is bounded to one Partition with `partition=`.

## T23

This compares the text of your Statement with the team's Hive, and it sends nothing to the warehouse. The Verdict holds when the two are the same query once spacing, case, comments and short table names are set aside. The alias `r` and the trailing comment don't count, so the check holds. It doesn't hold when the conditions, columns or tables differ.

```python
from sqlglot_composer import FROM, SELECT, compare_hive, statement
from references.ops__jobs import jobs

HIVE = "select r.job_id, r.job_name from ops.jobs r -- every job"

s0 = statement(SELECT(jobs.job_id, jobs.job_name), FROM(jobs))

v = compare_hive(s0, HIVE)
print(v)
```

Because this check only reads the text, it doesn't need `query` or `execute`.
