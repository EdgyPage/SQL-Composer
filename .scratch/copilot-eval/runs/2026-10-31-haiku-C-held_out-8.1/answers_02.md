date: 2026-10-31
arm: C
model: haiku
files: c8c63aed

## T06

```python
from sqlglot_composer import Table

t = Table(
    "mart.team_alerts",
    columns={"team": "string", "alerts": "bigint", "high_share": "double", "dt": "string"},
    partitioned_by=["dt"],
    key=["team", "dt"],
    does_not_add_up=["high_share"],
    location="/data/your_team/mart.db/team_alerts",
)
```

This is the Table reference for the new Saved table mart.team_alerts, assigned to `t` as you asked. The partition column dt is listed in both columns (last) and partitioned_by. The Key is team and dt, as you said. high_share is in does_not_add_up, so the Toolbox refuses to add it up. The location is set because the table is Saved and its files go there. In the Project, the file references/mart__team_alerts.py takes the name after the table, so the Table in it is usually named team_alerts rather than t.
