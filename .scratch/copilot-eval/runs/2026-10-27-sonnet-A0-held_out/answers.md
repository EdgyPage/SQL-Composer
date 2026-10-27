date: 2026-10-27
arm: A0
model: sonnet
files: none

## T03

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, COUNT, equals, alias
from references import ops
from warehouse import query, execute

run_alerts = ops.run_alerts

s = statement(
    SELECT(run_alerts.severity, alias(COUNT(run_alerts.alert_id), "alerts")),
    FROM(run_alerts),
    WHERE(equals(run_alerts.dt, "2026-09-24")),
    GROUP_BY(run_alerts.severity),
)

result = query(s)
```

## T06

```python
from sqlglot_composer import Table
from warehouse import query, execute

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
    non_additive=["high_share"],  # a share of a day's alerts: never summed
)
```

## T09

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, HAVING, AVG, between, greater_than, alias
from references import ops
from warehouse import query, execute

job_runs = ops.job_runs

s = statement(
    SELECT(job_runs.job_id, alias(AVG(job_runs.duration_mins), "avg_minutes")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(job_runs.job_id),
    HAVING(greater_than(AVG(job_runs.duration_mins), 15)),
)
```

## T12

```python
from sqlglot_composer import statement, SELECT, FROM, JOIN, WHERE, equals, alias
from references import ops
from warehouse import query, execute

run_alerts = ops.run_alerts
job_runs = ops.job_runs
jobs = ops.jobs

s = statement(
    SELECT(run_alerts.alert_id, jobs.job_name),
    FROM(run_alerts),
    JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    WHERE(
        equals(run_alerts.dt, "2026-09-24"),
        equals(run_alerts.severity, "high"),
        equals(job_runs.dt, "2026-09-24"),
    ),
)
```

## T15

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, LAG, between, alias
from references import ops
from warehouse import query, execute

job_runs = ops.job_runs

s = statement(
    SELECT(
        job_runs.run_id,
        job_runs.job_id,
        job_runs.duration_mins,
        alias(
            LAG(job_runs.duration_mins, partition_by=[job_runs.job_id], order_by=[job_runs.run_id]),
            "minutes_before",
        ),
    ),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
)
```

## T18

```python
from sqlglot_composer import statement, INSERT_INTO, SELECT, FROM, WHERE, GROUP_BY, COUNT, equals, alias
from references import ops
from references.mart__job_day_runs import job_day_runs
from warehouse import query, execute

job_runs = ops.job_runs

# INSERT INTO (not OVERWRITE) so what the table already holds is kept.
s = statement(
    INSERT_INTO(job_day_runs),
    SELECT(
        job_runs.job_id,
        alias(COUNT(job_runs.run_id), "runs"),
        alias("2026-09-23", "dt"),
    ),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-23")),
    GROUP_BY(job_runs.job_id),
)

execute(s)
```

## T21

```python
from sqlglot_composer import statement, SELECT, FROM, LEFT_JOIN, CASE, WHEN, ELSE, equals, AND, alias
from references import ops
from warehouse import query, execute

jobs = ops.jobs
job_runs = ops.job_runs

s = statement(
    SELECT(
        jobs.job_name,
        alias(
            CASE(
                jobs.team,
                WHEN("data", "Data"),
                WHEN("web", "Web"),
                ELSE("Other"),
            ),
            "team_name",
        ),
        job_runs.run_id,
    ),
    FROM(jobs),
    LEFT_JOIN(
        job_runs,
        ON=AND(
            equals(job_runs.job_id, jobs.job_id),
            equals(job_runs.dt, "2026-09-24"),
        ),
    ),
)
```

## T24

```python
from sqlglot_composer import check_key
from references import ops
from warehouse import query, execute

# Looks for duplicate (job_id, dt) rows across the five days, using my query.
v = check_key(ops.job_owners, query, dt_from="2026-09-20", dt_to="2026-09-24")
```

## T27

```python
from sqlglot_composer import statement, SELECT, FROM, LEFT_JOIN, AND, equals
from references import ops
from warehouse import query, execute

jobs = ops.jobs
job_runs = ops.job_runs

# The dt condition moves into the join's ON, so a job with no run on
# 2026-09-24 is still kept once (with run_id NULL).
s = statement(
    SELECT(jobs.job_id, job_runs.run_id),
    FROM(jobs),
    LEFT_JOIN(
        job_runs,
        ON=AND(
            equals(job_runs.job_id, jobs.job_id),
            equals(job_runs.dt, "2026-09-24"),
        ),
    ),
)
```

## T30

```python
from sqlglot_composer import statement, SELECT, FROM, WHERE, CASE, WHEN, ELSE, equals, greater_than, alias
from references import ops
from warehouse import query, execute

job_runs = ops.job_runs

s = statement(
    SELECT(
        job_runs.run_id,
        alias(
            CASE(
                WHEN(equals(job_runs.status, "FAILED"), "failed"),
                WHEN(greater_than(job_runs.duration_mins, 25), "slow"),
                ELSE("ok"),
            ),
            "label",
        ),
    ),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
```
