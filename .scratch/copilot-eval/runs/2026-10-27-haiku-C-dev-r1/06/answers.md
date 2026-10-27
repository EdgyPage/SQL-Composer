date: 2026-10-27
arm: C
model: haiku
files: 353cbeeb

## T16

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE,
                              count_rows, equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

DAY = "2026-09-24"

s = statement(
    INSERT_OVERWRITE(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, DAY)),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
```

The WHERE bounds ops.job_runs on its partition column dt, and GROUP_BY over job_id and dt gives one row per Key of mart.job_day_runs. INSERT_OVERWRITE replaces only the partition the rows hold, which is 2026-09-24, so that day's old rows are replaced. Partitions filled from the rows need the Session setting first, so after `from warehouse import query, execute`, send it with `run_execute(hive_settings("dynamic_partitions"), execute)` and then write with `run_execute(s, execute)`.

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

The other cells of the notebook run it: `run_execute(create(), execute)` once, `run_query(preview(), query)` to look at the rows, then `run_execute(write(), execute)` after the dynamic_partitions Session setting. `show_hive(create(), write())` shows both without sending anything.
