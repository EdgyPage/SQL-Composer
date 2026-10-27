date: 2026-10-27
arm: C
model: haiku
files: 353cbeeb

## T07

The failed runs are the rows where status is "FAILED" and dt falls between the two days. The bound on dt sits in WHERE, as the partitioned table needs, and the three columns are plain, so they need no AS.

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

Run it with `run_query(s, query)` after `from warehouse import query, execute`.

## T08

The total minutes per job need every day the table holds, so the read opts out of the partition bound with `reads_all_partitions=True`, with a comment saying why. The total is `sum_of` with an AS name, and job_id goes in GROUP_BY because it is not added up.

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, statement, sum_of
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
    # The user asked for every day ops.job_runs holds, so the read is not bounded on dt.
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

Run it with `run_query(s, query)` after `from warehouse import query, execute`.
