date: 2026-10-27
arm: C
model: sonnet
files: 95fbcd5

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

This counts the rows of ops.run_alerts for each severity, giving the columns severity and alerts. The WHERE bounds the read on the partition column dt, and `run_query(s, query)` runs it with your query and returns a DataFrame in `rows`.
