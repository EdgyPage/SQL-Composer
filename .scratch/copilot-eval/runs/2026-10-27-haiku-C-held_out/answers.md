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


## T09

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, HAVING, SELECT, WHERE, average_of,
                              between, more_than, statement)
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_minutes")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(job_runs.job_id),
    HAVING(more_than(average_of(job_runs.duration_mins), 15)),
)
```

This builds the Statement in `s` for the jobs whose runs from 2026-09-23 to 2026-09-24 average more than 15 minutes. The job_runs table is partitioned by dt, so the WHERE bounds it with `between` on that column. Each job_id is grouped, and the average is named `avg_minutes`. To run it, call `run_query(s, query)` after `from warehouse import query`.


## T12

```python
from sqlglot_composer import FROM, JOIN, SELECT, WHERE, equals, statement
from references.ops__run_alerts import run_alerts
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(run_alerts.alert_id, jobs.job_name),
    FROM(run_alerts),
    JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    WHERE(
        equals(run_alerts.dt, "2026-09-24"),
        equals(job_runs.dt, "2026-09-24"),
        equals(run_alerts.severity, "high"),
    ),
)
```

This joins each alert to its run on run_id, the whole Key of ops.job_runs, and then each run to its job on job_id, the whole Key of ops.jobs. Both partitioned tables, ops.run_alerts and ops.job_runs, are bounded to 2026-09-24 in WHERE with a value, and ops.jobs has no partitions, so it needs no bound. The severity filter assumes the stored value is "high"; if the column holds another spelling, change that string.


## T15

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, between, derived, lag, statement, window
from references.ops__job_runs import job_runs

each_job = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id)
prior = derived("prior", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(lag(job_runs.duration_mins, over=each_job), "minutes_before")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-22", "2026-09-24")),
))
s = statement(
    SELECT(prior.run_id, prior.job_id, prior.duration_mins, prior.minutes_before),
    FROM(prior),
    WHERE(between(prior.dt, "2026-09-23", "2026-09-24")),
)
```

The Derived table reads 2026-09-22 through 2026-09-24, so the first run of 2026-09-23 can see the run before it, which is the same job's run with the next lower run_id. The outer Statement then keeps only the runs from 2026-09-23 to 2026-09-24. A run whose earlier run falls before 2026-09-22 shows an empty minutes_before, because that day isn't read; widen the between in the Derived table if those earlier runs should count.


## T18

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_INTO, SELECT, WHERE, count_rows,
                              equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

s = statement(
    INSERT_INTO(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-23")),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
```

INSERT_INTO adds these rows to what mart.job_day_runs already holds, so the existing rows stay. The WHERE bounds the read to the 2026-09-23 partition of ops.job_runs. GROUP_BY over job_id and dt gives one row per Key, which is what the Saved table's Key (job_id, dt) needs. dt is the partition column, so it comes last in SELECT and no partition argument is given, because the rows fill their own Partition. To send it, run `from warehouse import query, execute`, then `run_execute(hive_settings("dynamic_partitions"), execute)` and `run_execute(s, execute)`. Running it again for the same day adds these rows a second time, so send it once.


## T21

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, all_of, equals, mapped, statement
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

j = AS(jobs, "j")
r = AS(job_runs, "r")

TEAM_NAMES = {"data": "Data", "web": "Web"}

s = statement(
    SELECT(
        j.job_name,
        AS(mapped(j.team, TEAM_NAMES, otherwise="Other"), "team_name"),
        r.run_id,
    ),
    FROM(j),
    LEFT_JOIN(
        r,
        ON=all_of(
            equals(r.job_id, j.job_id),
            equals(r.dt, "2026-09-24"),
        ),
    ),
)
```

ops.job_runs is partitioned by dt, so its read is bounded by `equals(r.dt, "2026-09-24")` inside ON=, as the Hive's ON bounded it. ops.jobs has no partitions, so it needs no bound. The CASE became `mapped(...)` with a constant dict, named `team_name`. The columns come out in the Hive's order: job_name, team_name, run_id.

No part is kept as Hive.


## T24

Here is the Key check for ops.job_owners, bounded to the five days with a `between` on its partition column `dt`, and run through your `query`.

```python
from sqlglot_composer import between, check_key
from references.ops__job_owners import job_owners
from warehouse import query

v = check_key(
    job_owners,
    query=query,
    where=between(job_owners.dt, "2026-09-20", "2026-09-24"),
)
print(v)
```

The Verdict is true when the Key (job_id, dt) tells every row apart across 2026-09-20 to 2026-09-24. If it is false, `print(v)` says what it found, which is the rows the Key fails to tell apart.


## T27

```python
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from sqlglot_composer import FROM, LEFT_JOIN, SELECT, all_of, equals, statement

s = statement(
    SELECT(jobs.job_id, job_runs.run_id),
    FROM(jobs),
    LEFT_JOIN(
        job_runs,
        ON=all_of(
            equals(job_runs.job_id, jobs.job_id),
            equals(job_runs.dt, "2026-09-24"),
        ),
    ),
)
```

The condition on `job_runs.dt` moved out of WHERE and into the LEFT_JOIN's `ON=`, joined with the job_id match by `all_of`, so it decides which runs match and a job with no run on 2026-09-24 is still kept once, with no run_id. The join on job_id can give a job one row per run that day, which is what you asked for; I did not add `many_matches=True`, since that is an opt-out you haven't asked for, so if the Toolbox warns with a RepeatedRowsWarning, tell me the repeats are wanted and I'll add it.


## T30

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, equals, first_match, more_than, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id,
           AS(first_match([(equals(job_runs.status, "FAILED"), "failed"),
                           (more_than(job_runs.duration_mins, 25), "slow")],
                          otherwise="ok"), "label")),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
```

This builds the Statement for ops.job_runs on 2026-09-24, with the run_id and a label. The WHERE on dt bounds the read to that one partition, since job_runs is partitioned by dt. first_match checks the conditions in order, so a FAILED run gets "failed" even if it also took more than 25 minutes, and a run that is not failed but took more than 25 minutes gets "slow". Every other run gets "ok". To run it, pass s to run_query with your query call, after `from warehouse import query, execute`.

