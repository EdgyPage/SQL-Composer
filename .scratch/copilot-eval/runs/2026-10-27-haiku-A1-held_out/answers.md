date: 2026-10-27
arm: A1
model: haiku
files: none

## T03

```python
from warehouse import query, execute
from references.ops__run_alerts import run_alerts
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, run_query

s = statement(
    SELECT(run_alerts.severity, COUNT(run_alerts.alert_id).as_("alerts")),
    FROM(run_alerts),
    WHERE(equals(run_alerts.dt, "2026-09-24")),
    GROUP_BY(run_alerts.severity),
)

df = run_query(s, query)
```

## T06

```python
from sqlglot_composer import Table

t = Table(
    "mart.team_alerts",
    columns={"team": "string", "alerts": "bigint", "high_share": "double", "dt": "string"},
    partitioned_by=["dt"],
    key=["team", "dt"],
    location="/data/your_team/mart.db/team_alerts",
    never_sum=["high_share"],
)
```

Note: the name `never_sum` for keeping high_share out of sums is my guess; check the Table reference how-to for the exact argument.

## T09

```python
from warehouse import query, execute
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, HAVING, AVG, between, greater_than

s = statement(
    SELECT(job_runs.job_id, AVG(job_runs.duration_mins).as_("avg_minutes")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(job_runs.job_id),
    HAVING(greater_than(AVG(job_runs.duration_mins), 15)),
)
```

## T12

```python
from warehouse import query, execute
from references.ops__run_alerts import run_alerts
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from sqlglot_composer import statement, SELECT, FROM, INNER_JOIN, WHERE, AND, equals

s = statement(
    SELECT(run_alerts.alert_id, jobs.job_name),
    FROM(run_alerts),
    INNER_JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
    INNER_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    WHERE(AND(
        equals(run_alerts.dt, "2026-09-24"),
        equals(run_alerts.severity, "high"),
        equals(job_runs.dt, "2026-09-24"),
    )),
)
```

## T15

```python
from warehouse import query, execute
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, WHERE, LAG, between

s = statement(
    SELECT(
        job_runs.run_id,
        job_runs.job_id,
        job_runs.duration_mins,
        LAG(job_runs.duration_mins).over(
            partition_by=[job_runs.job_id],
            order_by=[job_runs.run_id],
        ).as_("minutes_before"),
    ),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
)
```

Note: a run on 2026-09-23 whose previous run is on an earlier day gets no value here, because the window only sees the filtered rows. Reaching back past the range needs a wider window first, which I have not written out.

## T18

```python
from warehouse import query, execute
from references import ops
from references.ops__job_runs import job_runs
from references.mart__job_day_runs import job_day_runs
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, COUNT, INSERT_INTO, equals, run_execute

s = statement(
    INSERT_INTO(job_day_runs),
    SELECT(
        job_runs.job_id,
        COUNT(job_runs.run_id).as_("runs"),
        job_runs.dt,
    ),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-23")),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)

run_execute(s, execute)
```

## T21

```python
from warehouse import query, execute
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, LEFT_JOIN, CASE, WHEN, AND, equals

s = statement(
    SELECT(
        jobs.job_name,
        CASE(
            WHEN(equals(jobs.team, "data"), "Data"),
            WHEN(equals(jobs.team, "web"), "Web"),
            ELSE="Other",
        ).as_("team_name"),
        job_runs.run_id,
    ),
    FROM(jobs),
    LEFT_JOIN(job_runs, ON=AND(
        equals(job_runs.job_id, jobs.job_id),
        equals(job_runs.dt, "2026-09-24"),
    )),
)
```

## T24

```python
from warehouse import query, execute
from references.ops__job_owners import job_owners
from sqlglot_composer import check_key

v = check_key(job_owners, query=query, dt_from="2026-09-20", dt_to="2026-09-24")
```

Note: `check_key` and its arguments are my guess at the Key check's name; the message does not name it.

## T27

```python
from warehouse import query, execute
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, LEFT_JOIN, AND, equals

s = statement(
    SELECT(jobs.job_id, job_runs.run_id),
    FROM(jobs),
    LEFT_JOIN(job_runs, ON=AND(
        equals(job_runs.job_id, jobs.job_id),
        equals(job_runs.dt, "2026-09-24"),
    )),
)
```

## T30

```python
from warehouse import query, execute
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, WHERE, CASE, WHEN, equals, greater_than

s = statement(
    SELECT(
        job_runs.run_id,
        CASE(
            WHEN(equals(job_runs.status, "FAILED"), "failed"),
            WHEN(greater_than(job_runs.duration_mins, 25), "slow"),
            ELSE="ok",
        ).as_("label"),
    ),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
```
