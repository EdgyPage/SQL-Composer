date: 2026-10-27
arm: C
model: sonnet
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

This counts the rows of ops.run_alerts for each severity, giving the columns severity and alerts. The WHERE bounds the read on the partition column dt, and `run_query(s, query)` runs it with your query and returns a DataFrame in `rows`.


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

The WHERE bounds the partitioned table on `dt` to the two days. The Statement groups the runs by job and averages `duration_mins`, and HAVING keeps only the jobs whose average is over 15. Run it with `run_query(s, query)` after `from warehouse import query`.


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
        equals(run_alerts.severity, "high"),
        equals(run_alerts.dt, "2026-09-24"),
        equals(job_runs.dt, "2026-09-24"),
    ),
)
```

This starts from the alerts and joins each one to its run on the run's Key (run_id), then to the run's job on the job's Key (job_id), so no row matches many. ops.run_alerts and ops.job_runs are both partitioned by dt, so each has its own bound on 2026-09-24 in WHERE. ops.jobs has no partitions and needs none. I used "high" as the severity value; change it if your data spells it differently. The job_runs bound assumes a run is stored under the same day as its alert. If a run can sit in an earlier partition, widen that bound with `between(...)` or `is_in(...)`.


## T15

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, between, lag, statement, window
from references.ops__job_runs import job_runs

# Each job's runs in run_id order; lag looks at the run just before.
each_job = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id)

s = statement(
    SELECT(
        job_runs.run_id,
        job_runs.job_id,
        job_runs.duration_mins,
        AS(lag(job_runs.duration_mins, over=each_job), "minutes_before"),
    ),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
)
```

This takes the minutes of the previous run of the same job, in run_id order, and the read is bounded on `dt` from 2026-09-23 to 2026-09-24. `minutes_before` is empty (NULL) for a job's first run in that range. The previous run is looked for only inside those two days, so a job's first run on 2026-09-23 doesn't see a run from 2026-09-22. If you want those filled, widen the `dt` bound to start earlier. Then keep only the two days in a Statement that reads this one as a Derived table.


## T18

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_INTO, SELECT, WHERE,
                              count_rows, equals, statement)
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

This adds one row per job for 2026-09-23 to mart.job_day_runs and keeps what the table already holds, because INSERT_INTO adds rows instead of replacing a Partition. The SELECT gives the Saved table's columns in its order (job_id, runs, dt) with the partition column last. GROUP_BY over job_id and dt proves the Key, and the `equals` on `job_runs.dt` bounds the read of the partitioned ops.job_runs. Running it twice for the same day would add the rows twice. When you send it, use `run_execute(s, execute)`. A write whose rows fill their Partitions needs the "dynamic_partitions" Session setting first, so send `run_execute(hive_settings("dynamic_partitions"), execute)` before it. File 06 covers that.


## T21

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, all_of, equals, mapped,
                              statement)
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

TEAM_NAMES = {"data": "Data", "web": "Web"}

j = AS(jobs, "j")
r = AS(job_runs, "r")

s = statement(
    SELECT(
        j.job_name,
        AS(mapped(j.team, TEAM_NAMES, otherwise="Other"), "team_name"),
        r.run_id,
    ),
    FROM(j),
    LEFT_JOIN(r, ON=all_of(equals(r.job_id, j.job_id), equals(r.dt, "2026-09-24"))),
)
```

Nothing was kept as Hive. The `CASE j.team WHEN ...` becomes `mapped(...)` with `otherwise="Other"`. `ops.job_runs` is partitioned by `dt`, so the `r.dt = '2026-09-24'` condition stays inside the join's `ON=`, as the Hive had it. `ops.jobs` has no partitions, so it needs no bound.


## T24

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

This reads ops.job_owners through your `query` only, bounded to the partitions from 2026-09-20 to 2026-09-24, and checks whether the Key (job_id, dt) tells each row apart in that range. If the Verdict holds (`if v:` is true), no two rows in those days share a job_id and dt. If it doesn't hold, `print(v)` says what it found, so you can see which Key values repeat. It says nothing about days outside the range.


## T27

```python
from sqlglot_composer import FROM, LEFT_JOIN, SELECT, all_of, equals, statement
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

s = statement(
    SELECT(jobs.job_id, job_runs.run_id),
    FROM(jobs),
    LEFT_JOIN(
        job_runs,
        ON=all_of(
            equals(job_runs.job_id, jobs.job_id),
            equals(job_runs.dt, "2026-09-24"),
        ),
        # You asked for every job with all of its runs, so a job repeating once per run is wanted.
        many_matches=True,
    ),
)
```

I moved the `job_runs.dt` bound out of WHERE and into the `LEFT_JOIN`'s `ON=`, next to the join condition. That way it only decides which runs match, so a job with no runs on 2026-09-24 stays in the result once (with an empty run_id) instead of being dropped by the WHERE. `ON=` is also where the partition bound has to go for a LEFT_JOIN. I added `many_matches=True` because you want each job with all its runs, so a job showing once per run is what you asked for. Otherwise the join on `job_id`, which isn't job_runs' Key (`run_id`), would raise a RepeatedRowsWarning.


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

This uses `first_match` for the chain, so the first condition that holds gives the label: "failed" for a FAILED status, else "slow" when `duration_mins` is more than 25, else "ok". The `label` column is named with AS. The WHERE bounds the read to the `2026-09-24` partition of `dt`. The statement is a read, so you would run it with `run_query(s, query)`. Nothing in it is hand-written Hive.

