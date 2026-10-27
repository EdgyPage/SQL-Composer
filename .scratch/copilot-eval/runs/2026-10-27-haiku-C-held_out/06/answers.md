date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T18

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_INTO, SELECT, WHERE, count_rows,
                              equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

s = statement(
    INSERT_INTO(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-23")),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
```

INSERT_INTO adds these rows to what mart.job_day_runs already holds, so the existing rows stay. The WHERE bounds the read to the 2026-09-23 partition of ops.job_runs. GROUP_BY over job_id and dt gives one row per Key, which is what the Saved table's Key (job_id, dt) needs. dt is the partition column, so it comes last in SELECT and no partition argument is given, because the rows fill their own Partition. To send it, run `from warehouse import query, execute`, then `run_execute(hive_settings("dynamic_partitions"), execute)` and `run_execute(s, execute)`. Running it again for the same day adds these rows a second time, so send it once.
