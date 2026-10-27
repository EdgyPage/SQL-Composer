date: 2026-10-27
arm: A1
model: sonnet
files: none

## T03

The page shows only part of the function list, so the names for counting and aliasing below (`count_rows`, `alias`, `GROUP_BY`) are my best guess at the Toolbox's style. Check them against your version.

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, equals, count_rows, run_query
from references.ops__run_alerts import run_alerts
from warehouse import query, execute

s = statement(
    SELECT(run_alerts.severity, count_rows().alias("alerts")),
    FROM(run_alerts),
    WHERE(equals(run_alerts.dt, "2026-09-24")),
    GROUP_BY(run_alerts.severity),
)

df = run_query(s, query)
```

## T06

`non_additive` is my guess at the Table argument that marks a column as never to be summed. Use the name your version's Table takes for this.

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
    location="/data/your_team/mart.db/team_alerts",
    non_additive=["high_share"],
)
```

## T09

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, HAVING, between, greater_than, avg
from references.ops__job_runs import job_runs
from warehouse import query, execute

avg_minutes = avg(job_runs.duration_mins)

s = statement(
    SELECT(job_runs.job_id, avg_minutes.alias("avg_minutes")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(job_runs.job_id),
    HAVING(greater_than(avg_minutes, 15)),
)
```

## T12

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, JOIN, equals, and_
from references.ops__run_alerts import run_alerts
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from warehouse import query, execute

s = statement(
    SELECT(run_alerts.alert_id, jobs.job_name),
    FROM(run_alerts),
    JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    WHERE(and_(
        equals(run_alerts.dt, "2026-09-24"),
        equals(run_alerts.severity, "high"),
    )),
)
```

## T15

The window runs only over the rows from 2026-09-23 to 2026-09-24. So the first run of each job in that range gets a NULL `minutes_before`, even if the job had an earlier run on 2026-09-22 or before. To reach back further, widen the dt range and filter afterwards.

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, between, lag
from references.ops__job_runs import job_runs
from warehouse import query, execute

s = statement(
    SELECT(
        job_runs.run_id,
        job_runs.job_id,
        job_runs.duration_mins,
        lag(job_runs.duration_mins)
            .over(partition_by=[job_runs.job_id], order_by=[job_runs.run_id])
            .alias("minutes_before"),
    ),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
)
```

## T18

This appends one row per job, with dt set to the day counted, and leaves the rows already in the Saved table alone. Because the Key is job_id and dt, running it twice for the same day would repeat keys.

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, INSERT_INTO, equals, count_rows, lit, run_execute
from references.ops__job_runs import job_runs
from references.mart__job_day_runs import job_day_runs
from warehouse import query, execute

s = statement(
    INSERT_INTO(job_day_runs),
    SELECT(
        job_runs.job_id,
        count_rows().alias("runs"),
        lit("2026-09-23").alias("dt"),
    ),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-23")),
    GROUP_BY(job_runs.job_id),
)

run_execute(s, execute)
```

## T21

```python
from sqlglot_composer import statement, SELECT, FROM, LEFT_JOIN, CASE, equals, and_
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs
from warehouse import query, execute

team_name = (
    CASE(jobs.team)
    .WHEN("data", "Data")
    .WHEN("web", "Web")
    .ELSE("Other")
    .alias("team_name")
)

s = statement(
    SELECT(jobs.job_name, team_name, job_runs.run_id),
    FROM(jobs),
    LEFT_JOIN(
        job_runs,
        ON=and_(
            equals(job_runs.job_id, jobs.job_id),
            equals(job_runs.dt, "2026-09-24"),
        ),
    ),
)
```

## T24

`check_key` is my guess at the Toolbox's name for the Key check. Use the name your version has.

```python
from sqlglot_composer import check_key
from references.ops__job_owners import job_owners
from warehouse import query, execute

v = check_key(job_owners, dt_from="2026-09-20", dt_to="2026-09-24", query=query)
```

## T27

The refusal's fix is to move the dt condition from WHERE into the join's ON, joined to the key condition with `and_`. That way it only decides which runs match, and a job with no runs on that day stays once, with a NULL `run_id`.

```python
from sqlglot_composer import statement, SELECT, FROM, LEFT_JOIN, equals, and_
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs
from warehouse import query, execute

s = statement(
    SELECT(jobs.job_id, job_runs.run_id),
    FROM(jobs),
    LEFT_JOIN(
        job_runs,
        ON=and_(
            equals(job_runs.job_id, jobs.job_id),
            equals(job_runs.dt, "2026-09-24"),
        ),
    ),
)
```

## T30

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, CASE, equals, greater_than
from references.ops__job_runs import job_runs
from warehouse import query, execute

label = (
    CASE()
    .WHEN(equals(job_runs.status, "FAILED"), "failed")
    .WHEN(greater_than(job_runs.duration_mins, 25), "slow")
    .ELSE("ok")
    .alias("label")
)

s = statement(
    SELECT(job_runs.run_id, label),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
```
