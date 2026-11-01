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

## T18

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_INTO, SELECT, WHERE, count_rows,
                              equals, hive_settings, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

# The write's rows fill the dt Partition, so this Session setting is sent first.
settings = hive_settings("dynamic_partitions")

# The read is bounded to one day of ops.job_runs by its partition column dt.
READS = equals(job_runs.dt, "2026-09-23")

# INSERT_INTO adds these rows to what mart.job_day_runs already holds.
s = statement(
    INSERT_INTO(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(READS),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
```

This adds each job's run count for 2026-09-23 to mart.job_day_runs with INSERT_INTO, so the rows it already holds stay. GROUP_BY over job_id and dt, the table's Key, gives one row per Key. Run it once, because a second run adds the same rows again. Send the setting first with `run_execute(settings, execute)`, then the write with `run_execute(s, execute)`, after `from warehouse import query, execute`.

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
    LEFT_JOIN(r, ON=all_of(equals(r.job_id, j.job_id), equals(r.dt, "2026-09-24"))),
)
```

Nothing is kept as Hive. The CASE becomes `mapped(...)`, named `team_name` with AS. The `r.dt = '2026-09-24'` condition stays inside `ON=` with `all_of`, which bounds the partitioned `ops.job_runs` read as the Hive did. `ops.jobs` has no partitions, so it needs no bound.
