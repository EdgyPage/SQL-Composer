date: 2026-10-31
arm: C
model: haiku
files: c8c63aed

## T18

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_INTO, SELECT, WHERE, count_rows,
                              equals, hive_settings, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

# The write's rows fill the dt Partition, so this Session setting is sent first.
settings = hive_settings("dynamic_partitions")

# The read is bounded to one day of ops.job_runs by its partition column dt.
READS = equals(job_runs.dt, "2026-09-23")

# INSERT_INTO adds these rows to what mart.job_day_runs already holds.
s = statement(
    INSERT_INTO(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(READS),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
```

This adds each job's run count for 2026-09-23 to mart.job_day_runs with INSERT_INTO, so the rows it already holds stay. GROUP_BY over job_id and dt, the table's Key, gives one row per Key. Run it once, because a second run adds the same rows again. Send the setting first with `run_execute(settings, execute)`, then the write with `run_execute(s, execute)`, after `from warehouse import query, execute`.
