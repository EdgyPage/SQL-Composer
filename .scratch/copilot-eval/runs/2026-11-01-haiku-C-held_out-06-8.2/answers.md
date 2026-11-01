date: 2026-11-01
arm: C
model: haiku
files: 0db74777

## T18

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_INTO, SELECT, WHERE, count_rows,
                              equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

# ops.job_runs is partitioned by dt, so the read is bounded to 2026-09-23 in WHERE.
# INSERT_INTO adds these rows and keeps what mart.job_day_runs already holds.
# GROUP_BY over the Key (job_id, dt) gives one row per Key.
s = statement(
    INSERT_INTO(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-23")),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
```

The SELECT gives job_id, runs and dt, the Saved table's columns in order with the partition column last. The table already exists, so no create is needed. To send it, add `from warehouse import query, execute` and `hive_settings` to the imports, then run `run_execute(hive_settings("dynamic_partitions"), execute)` followed by `run_execute(s, execute)`, because the rows fill their dt Partition. Running it a second time adds the day's rows again, since INSERT_INTO does not replace anything.
