date: 2026-11-01
arm: C
model: haiku
files: 19-held

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

Notes: This counts the alerts in ops.run_alerts on 2026-09-24 for each severity, as the columns severity and alerts, and run_query sends it with your query and returns a DataFrame of the rows. The equals on run_alerts.dt bounds the read to that one partition, so no opt-out is used.

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

This Table reference describes the new Saved table mart.team_alerts with its four columns in order, each with its Hive type. The partition column dt is listed last in both columns and partitioned_by. The Key is team and dt, and high_share is named in does_not_add_up so the Toolbox refuses to add it up. The location is given because the table is written by your notebook. The file's self-check names the variable after the table, so when you save this as references/mart__team_alerts.py, rename `t` to `team_alerts`.

## T09

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, HAVING, SELECT, WHERE, average_of, between,
                              more_than, statement)
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_minutes")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(job_runs.job_id),
    HAVING(more_than(average_of(job_runs.duration_mins), 15)),
)
```

Notes: This gives each job_id with its average run length in minutes, named avg_minutes, over the runs dated 2026-09-23 through 2026-09-24, for only the jobs whose average is more than 15 minutes. The job_runs table is partitioned by dt, so the WHERE bounds it to those two days. No opt-out is used.

## T12

**Code**

```python
from sqlglot_composer import FROM, JOIN, SELECT, WHERE, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

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

**Notes**

This gives one row per high-severity alert raised on 2026-09-24, with its alert_id and the name of the job whose run raised it. The joins go on each table's Key (run_id for ops.job_runs, job_id for ops.jobs), so no alert repeats. Both run_alerts and job_runs are partitioned by dt, so each has its own bound in WHERE with the value 2026-09-24; ops.jobs is not partitioned and needs none. The severity value "high" is my reading of "high-severity"; change it if the warehouse writes it differently. No opt-out is used, and there is no ORDER_BY, so no LIMIT is needed. An alert whose run has no row in ops.job_runs would be dropped by the JOIN; say so if those alerts should stay.

## T15

**Code**

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, between, lag, statement, window
from references.ops__job_runs import job_runs

each_job = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins,
           AS(lag(job_runs.duration_mins, over=each_job), "minutes_before")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
)
```

**Notes**

Each run from 2026-09-23 to 2026-09-24 comes with the duration of the same job's run just before it, in run_id order, shown as minutes_before. The window orders each job's runs by run_id, and lag reads the row before within that order. The WHERE keeps only the two days, so the window sees only those rows: a job's first run on 2026-09-23 gets an empty minutes_before even if the job ran on 2026-09-22, because that day is not read. If that earlier run should count, the Statement needs a Derived table that reads from an earlier date, bounded on dt, with the two days kept in the outer Statement.

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

INSERT_INTO adds the day's rows to mart.job_day_runs and keeps what the table already holds. GROUP_BY over job_id and dt gives one row per Key, so no unproven_key is needed. The WHERE bounds the read of ops.job_runs to dt 2026-09-23. Send it with `run_execute(s, execute)` after `from warehouse import execute`, and run it once, since a rerun adds the rows twice. The write fills the dt Partition from its SELECT, so a Session setting, `hive_settings("dynamic_partitions")`, may be needed first.

## T21

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, all_of, equals, mapped, statement
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

# Hive's aliases: j for ops.jobs, r for ops.job_runs
j = AS(jobs, "j")
r = AS(job_runs, "r")

s = statement(
    SELECT(
        j.job_name,
        # CASE j.team WHEN 'data' THEN 'Data' WHEN 'web' THEN 'Web' ELSE 'Other' END AS team_name
        AS(mapped(j.team, {"data": "Data", "web": "Web"}, otherwise="Other"), "team_name"),
        r.run_id,
    ),
    FROM(j),
    # ON r.job_id = j.job_id AND r.dt = '2026-09-24'; job_runs is partitioned by dt,
    # so its bound stays inside ON=
    LEFT_JOIN(r, ON=all_of(equals(r.job_id, j.job_id), equals(r.dt, "2026-09-24"))),
)
```

No part is kept as Hive: every part of this query is Toolbox code.

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

When `v` holds, job_id and dt together tell each row apart on every day from 2026-09-20 to 2026-09-24, so no job has two rows for the same job_id on the same day. When it doesn't hold, the Key repeats on at least one of those days, and the printed Verdict says what it found; fix those rows before relying on the Key.

## T27

```python
from sqlglot_composer import FROM, LEFT_JOIN, SELECT, all_of, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

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

The `job_runs.dt = '2026-09-24'` condition moved out of WHERE and into the LEFT_JOIN's ON= beside the join condition, so it decides only which runs match and a job with no run that day is still kept once.

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

The label is a chain, so it uses first_match: a FAILED status gives "failed", otherwise a run over 25 minutes gives "slow", and anything else gives "ok". The WHERE on job_runs.dt bounds the read to 2026-09-24, since ops.job_runs is partitioned by dt. Run it as a read with run_query(s, query) after from warehouse import query, execute.

There is no hand-written Hive in this answer; every piece is a Toolbox call.

## T38

Workflow: convert, batch alerts. The user is at step 1, converting the scripts into dev.

```python
# names cell
NAME = "alerts"
FILES = ["alerts.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {"default.high_alerts": "keep"}

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

Decisions left to you: convert's report names each table it makes in dev, including mart_dev.high_alerts_per_run_mart and the kept high_alerts, which is a Saved table of its own. project.check() then lists the open Decisions for each one, such as its location, Key or column types. You answer those in the decisions cell (DECISIONS); I have no answers for them.

Later steps, in words:
2. Answer each open Decision in the decisions cell (DECISIONS), as yours to make.
3. Write each answer into its Table reference with project.write_decisions(DECISIONS); project.do_next() runs it.
4. Create each table in dev with run_execute(project.load(table).create(), execute) for each table in project.batch_tables(NAME).
5. Seed each table that reads itself, once, from its original. None of these scripts reads its own table, so this seeds nothing here.
6. Write each table in dev with project.run_tables(tables=project.batch_tables(NAME), execute=execute).
7. Compare each table with its original with project.compare_batch(NAME, query=query).

The table is not promoted to prod in this request. A table is promoted only once its compare has passed.

## T39

Workflow: convert, batch fails. The user is at step 1, and every step's cell is given below, in order.

```python
# names cell
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)

# step 2 cell: the decisions cell
DECISIONS = {"mart_dev.daily_fails_mart": {"location": "/data/team/mart_dev.db/daily_fails"}}

# step 3 cell
project.write_decisions(DECISIONS)

# step 4 cell
for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)

# step 5 cell
run_execute(hive_settings("dynamic_partitions"), execute)
for table in project.batch_tables(NAME, seeded=True):
    run_execute(project.load(table).seed(), execute)

# step 6 cell
project.run_tables(tables=project.batch_tables(NAME), execute=execute)

# step 7 cell
project.compare_batch(NAME, query=query)
```

Decisions left to you: the location is answered in DECISIONS above. project.check() may still ask other Decisions for mart_dev.daily_fails_mart, such as its Key or a column type. Those are yours to answer; add each to the DECISIONS dict under the same table name before step 3 runs.

Step 5 seeds nothing for this batch, since daily_fails reads ops.job_runs and never its own table; it is given because every cell was asked for.

No later steps are left in words. The table is not promoted to prod in this request, and it is promoted only once its compare has passed.

## T36

Workflow: new_table, at step 1 (Make each Table folder), for the new table mart_dev.ok_runs made from ok_runs.hql.

```python
TABLES = ["mart_dev.ok_runs"]
QUERIES = {"ok_runs": "ok_runs.hql"}
DECISIONS = {}

# step 1: make each Table folder (project.do_next() runs it for you)
project.new_table(TABLES, queries=QUERIES)
```

Decision left to you: the table's location, and any other Decision that project.check() names once the Table reference exists, such as its Key or a column type. Answer them yourself in the decisions cell at step 4; DECISIONS stays empty until you do.

Later steps, in order:
- Step 2: write ok_runs's logic in its Table notebook, and save it. This is your decision.
- Step 3: write its Table reference from that logic with project.reference_from_logic(TABLES). It is written from the logic, never by hand, and project.do_next() runs it for you.
- Step 4: answer its open Decisions in the decisions cell. This is your decision.
- Step 5: write those answers into its Table reference with project.write_decisions(DECISIONS), which project.do_next() runs for you.
- Step 6: check its rows with preview() through run_query. It writes nothing, and you run it.
- Step 7: create and write it in dev with run_execute(project.load(table).create(), execute), then project.run_tables(tables=TABLES, execute=execute). You run both.
- Step 8: compare it with ok_runs.hql using project.compare_batch. You run it.

The last cell, project.run_workflow("new_table", query=query, execute=execute), runs every step left, up to the first one only you can do.

