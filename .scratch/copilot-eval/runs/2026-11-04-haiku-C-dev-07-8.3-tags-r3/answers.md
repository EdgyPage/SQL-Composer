date: 2026-11-04
arm: C
model: haiku
files: 9ef648f

## T19

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, equals, is_in,
                              statement)
from references.ops__job_runs import job_runs

STATUS_VALUES = ["FAILED", "SUCCESS", "RETRY", "TEST"]

r = AS(job_runs, "r")
s = statement(
    SELECT(r.job_id, AS(count_rows(), "runs")),
    FROM(r),
    WHERE(equals(r.dt, "2026-09-24"), is_in(r.status, STATUS_VALUES)),
    GROUP_BY(r.job_id),
)
```

Kept as Hive: none.

## T20

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, between, derived, equals,
                              if_else, statement, sum_of)
from references.ops__job_events import job_events

e = AS(job_events, "e")
ev = derived(
    "ev",
    statement(
        SELECT(e.job_id, e.event_type),
        FROM(e),
        WHERE(between(e.dt, "2026-09-20", "2026-09-24")),
    ),
)

s = statement(
    SELECT(ev.job_id, AS(sum_of(if_else(equals(ev.event_type, "finish"), 1, 0)), "finishes")),
    FROM(ev),
    GROUP_BY(ev.job_id),
)
```

Kept as Hive: none.

## T43

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, equals, more_than, script_tag, statement
from references.ops__job_runs import job_runs

TAGS = {"RUN_DAY": "'2026-09-24'"}

r = AS(job_runs, "r")
s = statement(
    SELECT(r.run_id, r.status),
    FROM(r),
    WHERE(equals(r.dt, script_tag(TAGS["RUN_DAY"])), more_than(r.duration_mins, 30)),
)
```

Kept as Hive: none.
