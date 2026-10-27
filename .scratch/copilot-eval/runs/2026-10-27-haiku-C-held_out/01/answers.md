date: 2026-10-27
arm: C
model: haiku
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

This counts the alerts in ops.run_alerts for 2026-09-24 and groups them by severity. The `dt` condition bounds the read, since run_alerts is partitioned by dt. The count is named `alerts` with AS, and `run_query` sends the read through your `query` function and returns a DataFrame with the columns severity and alerts. For more on grouping and counting, such as how GROUP_BY and count_rows take their arguments, load Copilot file 03 (building a Statement) in a new chat.
