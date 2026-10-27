date: 2026-10-27
arm: C
model: haiku
files: 353cbeeb

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

Nothing is kept as Hive. The partition bound on `r.dt` is in WHERE, and the status list is a constant list with `is_in`.

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

Nothing is kept as Hive. The CTE `ev` keeps its name through `derived`, and the partition bound on `e.dt` is in the CTE's WHERE with `between`. The outer query reads only `ev`, so it needs no partition bound.
