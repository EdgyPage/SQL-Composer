date: 2026-10-27
arm: A0
model: haiku
files: none

## T03

Count the alerts per severity on 2026-09-24, filtered in WHERE and grouped by severity, then run it with your query.

```python
from references.ops__run_alerts import run_alerts
from references import ops
from warehouse import query, execute
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, COUNT, equals

s = statement(
    SELECT(ops.run_alerts.severity, COUNT(ops.run_alerts.alert_id).AS("alerts")),
    FROM(ops.run_alerts),
    WHERE(equals(ops.run_alerts.dt, "2026-09-24")),
    GROUP_BY(ops.run_alerts.severity),
)

query(s)
```

## T06

Here is the Table reference for mart.team_alerts. I am not certain of the exact keyword for the rule that high_share is never added up, so I used `not_summed`. Check that name against the Table docs before you rely on it.

```python
from sqlglot_composer import Table

t = Table(
    "mart.team_alerts",
    columns={"team": "string", "alerts": "bigint", "high_share": "double", "dt": "string"},
    partitioned_by=["dt"],
    key=["team", "dt"],
    location="/data/your_team/mart.db/team_alerts",
    not_summed=["high_share"],
)
```

## T09

Average the run durations per job over 2026-09-23 to 2026-09-24, then keep the jobs above 15 minutes with HAVING.

```python
from references.ops__job_runs import job_runs
from references import ops
from warehouse import query, execute
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, HAVING, AVG, between, greater_than

s = statement(
    SELECT(ops.job_runs.job_id, AVG(ops.job_runs.duration_mins).AS("avg_minutes")),
    FROM(ops.job_runs),
    WHERE(between(ops.job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(ops.job_runs.job_id),
    HAVING(greater_than(AVG(ops.job_runs.duration_mins), 15)),
)
```

## T12

Join the alerts to their run, then to the job, and keep the high-severity alerts on 2026-09-24. I assumed the severity value is written `high` in lowercase.

```python
from references.ops__run_alerts import run_alerts
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references import ops
from warehouse import query, execute
from sqlglot_composer import statement, SELECT, FROM, JOIN, WHERE, and_, equals

s = statement(
    SELECT(ops.run_alerts.alert_id, ops.jobs.job_name),
    FROM(ops.run_alerts),
    JOIN(ops.job_runs, ON=equals(ops.job_runs.run_id, ops.run_alerts.run_id)),
    JOIN(ops.jobs, ON=equals(ops.jobs.job_id, ops.job_runs.job_id)),
    WHERE(and_(equals(ops.run_alerts.severity, "high"), equals(ops.run_alerts.dt, "2026-09-24"))),
)
```

## T15

The previous run of the same job can fall before 2026-09-23, so the window is computed over the whole table in a subquery and the date filter is applied after it. The first run of each job has no earlier run, so its minutes_before is empty.

```python
from references.ops__job_runs import job_runs
from references import ops
from warehouse import query, execute
from sqlglot_composer import statement, SELECT, FROM, WHERE, LAG, PARTITION_BY, ORDER_BY, between

runs = statement(
    SELECT(
        ops.job_runs.run_id,
        ops.job_runs.job_id,
        ops.job_runs.duration_mins,
        ops.job_runs.dt,
        LAG(ops.job_runs.duration_mins).OVER(
            PARTITION_BY(ops.job_runs.job_id),
            ORDER_BY(ops.job_runs.run_id),
        ).AS("minutes_before"),
    ),
    FROM(ops.job_runs),
)

s = statement(
    SELECT(runs.run_id, runs.job_id, runs.duration_mins, runs.minutes_before),
    FROM(runs),
    WHERE(between(runs.dt, "2026-09-23", "2026-09-24")),
)
```

## T18

INSERT_INTO appends the new rows and keeps what mart.job_day_runs already holds. The count is grouped by job and dt for 2026-09-23.

```python
from references.ops__job_runs import job_runs
from references.mart__job_day_runs import job_day_runs
from references import ops
from warehouse import query, execute
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, INSERT_INTO, COUNT, equals

s = statement(
    INSERT_INTO(job_day_runs),
    SELECT(ops.job_runs.job_id, COUNT(ops.job_runs.run_id).AS("runs"), ops.job_runs.dt),
    FROM(ops.job_runs),
    WHERE(equals(ops.job_runs.dt, "2026-09-23")),
    GROUP_BY(ops.job_runs.job_id, ops.job_runs.dt),
)

execute(s)
```

## T21

The Hive's LEFT JOIN keeps its date filter inside the ON clause, so the Toolbox version does the same. The simple CASE on j.team becomes a searched CASE with equals.

```python
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs
from references import ops
from warehouse import query, execute
from sqlglot_composer import statement, SELECT, FROM, LEFT_JOIN, CASE, WHEN, ELSE, and_, equals

s = statement(
    SELECT(
        ops.jobs.job_name,
        CASE(
            WHEN(equals(ops.jobs.team, "data"), "Data"),
            WHEN(equals(ops.jobs.team, "web"), "Web"),
            ELSE("Other"),
        ).AS("team_name"),
        ops.job_runs.run_id,
    ),
    FROM(ops.jobs),
    LEFT_JOIN(
        ops.job_runs,
        ON=and_(
            equals(ops.job_runs.job_id, ops.jobs.job_id),
            equals(ops.job_runs.dt, "2026-09-24"),
        ),
    ),
)
```

## T24

Group the owners by job_id and dt over 2026-09-20 to 2026-09-24 and count them. The Key holds if no group has more than one row, so an empty result means it holds.

```python
from references.ops__job_owners import job_owners
from references import ops
from warehouse import query, execute
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, HAVING, COUNT, between, greater_than

s = statement(
    SELECT(ops.job_owners.job_id, ops.job_owners.dt, COUNT(ops.job_owners.job_id).AS("n")),
    FROM(ops.job_owners),
    WHERE(between(ops.job_owners.dt, "2026-09-20", "2026-09-24")),
    GROUP_BY(ops.job_owners.job_id, ops.job_owners.dt),
    HAVING(greater_than(COUNT(ops.job_owners.job_id), 1)),
)

v = query(s)
```

## T27

The condition on job_runs.dt moves out of WHERE and into the LEFT_JOIN's ON, next to the join condition, so a job with no run on 2026-09-24 is still kept once.

```python
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs
from references import ops
from warehouse import query, execute
from sqlglot_composer import statement, SELECT, FROM, LEFT_JOIN, and_, equals

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

Each run gets one label, checked in order: FAILED first, then slow above 25 minutes, otherwise ok.

```python
from references.ops__job_runs import job_runs
from references import ops
from warehouse import query, execute
from sqlglot_composer import statement, SELECT, FROM, WHERE, CASE, WHEN, ELSE, equals, greater_than

s = statement(
    SELECT(
        ops.job_runs.run_id,
        CASE(
            WHEN(equals(ops.job_runs.status, "FAILED"), "failed"),
            WHEN(greater_than(ops.job_runs.duration_mins, 25), "slow"),
            ELSE("ok"),
        ).AS("label"),
    ),
    FROM(ops.job_runs),
    WHERE(equals(ops.job_runs.dt, "2026-09-24")),
)
```
