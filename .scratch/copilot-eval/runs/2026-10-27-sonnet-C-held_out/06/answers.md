date: 2026-10-27
arm: C
model: sonnet
files: 95fbcd5

## T18

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_INTO, SELECT, WHERE,
                              count_rows, equals, statement)
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

This adds one row per job for 2026-09-23 to mart.job_day_runs and keeps what the table already holds, because INSERT_INTO adds rows instead of replacing a Partition. The SELECT gives the Saved table's columns in its order (job_id, runs, dt) with the partition column last. GROUP_BY over job_id and dt proves the Key, and the `equals` on `job_runs.dt` bounds the read of the partitioned ops.job_runs. Running it twice for the same day would add the rows twice. When you send it, use `run_execute(s, execute)`. A write whose rows fill their Partitions needs the "dynamic_partitions" Session setting first, so send `run_execute(hive_settings("dynamic_partitions"), execute)` before it. File 06 covers that.
