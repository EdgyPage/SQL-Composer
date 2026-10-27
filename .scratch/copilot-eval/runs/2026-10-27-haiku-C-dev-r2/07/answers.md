date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

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

Nothing is kept as Hive. The `dt` partition is bounded in WHERE by `equals(r.dt, "2026-09-24")`, as the Hive bounded it.

## T20

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, between, derived, equals,
                              if_else, statement, sum_of)
from references.ops__job_events import job_events

e = AS(job_events, "e")
events_in_range = statement(
    SELECT(e.job_id, e.event_type),
    FROM(e),
    WHERE(between(e.dt, "2026-09-20", "2026-09-24")),
)

ev = derived("ev", events_in_range)
s = statement(
    SELECT(ev.job_id, AS(sum_of(if_else(equals(ev.event_type, "finish"), 1, 0)), "finishes")),
    FROM(ev),
    GROUP_BY(ev.job_id),
)
```

Nothing is kept as Hive. The CTE `ev` is a Derived table named with `derived`, and the `dt` partition is bounded inside it in WHERE by `between(e.dt, "2026-09-20", "2026-09-24")`, as the Hive bounded it.
