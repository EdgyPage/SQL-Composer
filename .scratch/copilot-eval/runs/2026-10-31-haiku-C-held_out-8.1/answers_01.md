date: 2026-10-31
arm: C
model: haiku
files: c8c63aed

## T03

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, equals, run_query, statement
from references.ops__run_alerts import run_alerts
from warehouse import query

s = statement(
    SELECT(run_alerts.severity, AS(count_rows(), "alerts")),
    FROM(run_alerts),
    WHERE(equals(run_alerts.dt, "2026-09-24")),
    GROUP_BY(run_alerts.severity),
)
rows = run_query(s, query)
```

The table is partitioned by dt, so the WHERE clause bounds the read to 2026-09-24. Each severity is a plain column, and the count gets its name from AS. The last line runs the Statement with your query and returns a DataFrame.
