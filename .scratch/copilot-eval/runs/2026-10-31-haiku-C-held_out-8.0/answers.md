date: 2026-10-31
arm: C
model: haiku
files: ea80a87

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

The Statement counts the rows of ops.run_alerts for each severity, returned as the columns severity and alerts. Because ops.run_alerts is partitioned by dt, the WHERE clause bounds the read to 2026-09-24. The last line runs the read with your query and gives a pandas DataFrame in rows.

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

Here `dt` is listed in both `columns` and `partitioned_by`, last, and `high_share` is in `does_not_add_up`, so the Toolbox refuses to add it up. Saved tables need a `location`, which this has. To follow the references convention, save this as `references/mart__team_alerts.py` and name the variable `team_alerts` instead of `t`, so other code can write `from references.mart__team_alerts import team_alerts`.

## T18

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_INTO, SELECT, WHERE, count_rows,
                              equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

# job_runs is partitioned by dt, so the read is bounded to 2026-09-23.
# INSERT_INTO adds these rows and keeps what mart.job_day_runs already holds.
# GROUP_BY over the Key (job_id, dt) gives one row per Key.
s = statement(
    INSERT_INTO(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-23")),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
```

The statement is an INSERT_INTO, so existing rows stay. The SELECT gives job_id, runs and dt in the table's column order, with the partition column dt last. Grouping by job_id and dt covers the Key, so the write is not refused. To send it, run `run_execute(hive_settings("dynamic_partitions"), execute)` first, because the rows fill their Partition, then `run_execute(s, execute)`, with `from warehouse import query, execute` in the notebook.

## T21

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, all_of, equals, mapped, statement
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

j = AS(jobs, "j")
r = AS(job_runs, "r")
s = statement(
    SELECT(
        j.job_name,
        AS(mapped(j.team, {"data": "Data", "web": "Web"}, otherwise="Other"), "team_name"),
        r.run_id,
    ),
    FROM(j),
    LEFT_JOIN(
        r,
        ON=all_of(equals(r.job_id, j.job_id), equals(r.dt, "2026-09-24")),
    ),
)
```

Kept as Hive: none. The CASE becomes `mapped(...)` with its ELSE as `otherwise="Other"`, and the `r.dt` bound stays inside `ON=` because ops.job_runs is partitioned by dt and it is a LEFT JOIN.

