date: 2026-10-27
arm: C
model: sonnet
files: 95fbcd5

## T06

```python
from sqlglot_composer import Table

t = Table(
    "mart.team_alerts",
    columns={
        "team": "string",
        "alerts": "bigint",
        "high_share": "double",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["team", "dt"],
    does_not_add_up=["high_share"],
    location="/data/your_team/mart.db/team_alerts",
)
```

This is the Table reference for the new Saved table `mart.team_alerts`. It would live in `references/mart__team_alerts.py`. File 02 says to name the variable after the table (`team_alerts`), but you asked for `t`, so I used `t`. Other code imports the variable by the name it has in that file. `dt` is in both `columns` and `partitioned_by`, and it comes last in `columns`. The Key is `team` and `dt`, as you said. `does_not_add_up=["high_share"]` makes the Toolbox refuse to sum that share. `location` is set because a Saved table needs one.
