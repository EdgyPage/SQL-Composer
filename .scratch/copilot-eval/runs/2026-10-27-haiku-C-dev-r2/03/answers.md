date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T07

```python
from sqlglot_composer import FROM, SELECT, WHERE, between, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(
        equals(job_runs.status, "FAILED"),
        between(job_runs.dt, "2026-09-23", "2026-09-24"),
    ),
)
```

This reads the three columns you asked for from `ops.job_runs`. The `between` on `dt` bounds the read to the two days, since the table is partitioned by `dt`, and WHERE keeps only the rows where both conditions hold. Run it with `run_query(s, query)` after `from warehouse import query, execute`.

## T08

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, statement, sum_of
from references.ops__job_runs import job_runs

# Every day the table holds, so this read is deliberately not bounded on dt.
s = statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

This adds up `duration_mins` for each `job_id` across all partitions. The `reads_all_partitions=True` opt-out is there because you asked for every day, and it reads the whole table, so it can be slow on a large one. Run it with `run_query(s, query)` after `from warehouse import query, execute`.
