date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T06

```python
from sqlglot_composer import Table

t = Table(
    "mart.team_alerts",
    columns={"team": "string", "alerts": "bigint", "high_share": "double", "dt": "string"},
    partitioned_by=["dt"],
    key=["team", "dt"],
    location="/data/your_team/mart.db/team_alerts",
    does_not_add_up=["high_share"],
)
```

Save this as `references/mart__team_alerts.py`, so the file name matches the table name. The `dt` column is listed in both `columns` and `partitioned_by`, and it is last in `columns`. The Key is `team` and `dt`, and `location` is set because mart.team_alerts is a Saved table that your notebook writes. `high_share` is in `does_not_add_up`, so the Toolbox refuses to add it up. You asked for the variable to be `t`; the usual style names it after the table, `team_alerts`, which makes it easier to import from other code.
