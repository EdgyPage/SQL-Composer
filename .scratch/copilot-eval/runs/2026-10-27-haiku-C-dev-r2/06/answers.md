date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T16

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, count_rows,
                              equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

s = statement(
    INSERT_OVERWRITE(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
```

This builds one Statement, `s`, that replaces the 2026-09-24 Partition of mart.job_day_runs. The WHERE bounds the read of ops.job_runs to that day, and GROUP_BY over job_id and dt gives one row per Key. Because the rows fill their Partition from the dt column, send it with `run_execute(hive_settings("dynamic_partitions"), execute)` first, then `run_execute(s, execute)`, after `from warehouse import query, execute`.

## T17

```python
# logic
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause,
                              Statement, count_rows, create_table, equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

DAY = "2026-09-24"


def create() -> Statement:
    return create_table(job_day_runs, may_exist=True)


def rows(day: str) -> list[Clause]:
    return [
        SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, day)),
        GROUP_BY(job_runs.job_id, job_runs.dt),
    ]


def preview() -> Statement:
    return statement(*rows(DAY))


def write() -> Statement:
    return statement(INSERT_OVERWRITE(job_day_runs), *rows(DAY))
```

Paste this into the logic cell of the mart.job_day_runs Table notebook. The next cell can run `show_hive([create(), write()])` to see the Hive, and `run_query(preview(), query)` to read the rows before writing. The write replaces DAY's Partition, and project.run_tables sends it with its Session settings first.
