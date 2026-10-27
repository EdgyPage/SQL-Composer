date: 2026-10-27
arm: R
model: haiku
files: 95fbcd5

## T03

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, equals,
                              run_query, statement)
from references.ops__run_alerts import run_alerts
from warehouse import query, execute

s = statement(
    SELECT(run_alerts.severity, AS(count_rows(), "alerts")),
    FROM(run_alerts),
    WHERE(equals(run_alerts.dt, "2026-09-24")),
    GROUP_BY(run_alerts.severity),
)

result = run_query(s, query)
```

This counts the rows of ops.run_alerts for 2026-09-24, one row per severity, with the columns severity and alerts. The WHERE clause bounds the read on dt, the table's partition column, so the table is not read whole. The result of `run_query(s, query)` is kept in `result`.
