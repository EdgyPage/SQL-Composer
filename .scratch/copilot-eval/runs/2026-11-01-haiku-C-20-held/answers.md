date: 2026-11-01
arm: C
model: haiku
files: 20-held

## T03

**Code**

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

**Notes**

This gives one row per severity for 2026-09-24, with the columns severity and alerts, as a DataFrame from your query. The partition column dt is bounded in WHERE, because ops.run_alerts is partitioned by dt, so no opt-out is needed.

## T06

**Code**

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

**Notes**

This Table reference describes the new Saved table mart.team_alerts with its four columns and their Hive types, partitioned by dt, which is listed last in the columns as the partition rule requires. The Key is team and dt, so the Toolbox can trust a join or a write on them. The high_share column is listed in does_not_add_up, so the Toolbox refuses to add it up, since it is a share of a day's alerts. Because this is a Saved table, it has a location of /data/your_team/mart.db/team_alerts. The file would normally be saved as references/mart__team_alerts.py, named after the table, and the variable there would be team_alerts; the code above assigns it to t as you asked.

## T09

**Code**

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

**Notes**

This gives each job_id with its average run duration in minutes (avg_minutes), over the runs dated 2026-09-23 through 2026-09-24, keeping only the jobs whose average is more than 15 minutes. The WHERE on job_runs.dt bounds the read of the partitioned table, so no opt-out is used. The query has no ORDER_BY, so no LIMIT is needed.

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

This gives the alert_id and job_name of each high-severity alert raised on 2026-09-24, one row per alert. Both joins are inner JOINs, so an alert whose run or job has no match drops out, and each join is on the joined table's whole Key. Both partitioned tables, run_alerts and job_runs, are bounded to 2026-09-24 in WHERE, and jobs is not partitioned so it needs no bound. No opt-out is used.

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

The window groups the rows of each job and orders them by run_id, so lag reads the duration of the run just before each one, shown as minutes_before. The between Condition on dt bounds the read to 2026-09-23 and 2026-09-24. Because the WHERE runs before the window, lag sees only those two days: the first run of each job in the range shows no earlier run, so its minutes_before is NULL, even when the job ran on 2026-09-22. To see that earlier run, widen the between to start on 2026-09-22 and keep the rows you need from the range in a Derived table.

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

The write is INSERT_INTO, so the rows are added to what mart.job_day_runs already holds. The WHERE bounds the read of ops.job_runs, which is partitioned by dt, to 2026-09-23. The GROUP_BY over job_id and dt gives one row per Key, so the write is not refused. A rerun of the same write adds the rows twice.

Send it with `from warehouse import query, execute` and then `run_execute(s, execute)`. Because the write fills the dt Partitions from its rows, run `run_execute(hive_settings("dynamic_partitions"), execute)` before it.

## T21

Piece by piece, by hand:

- `FROM ops.jobs j` becomes `j = AS(jobs, "j")`, read as `j.job_name` and `j.team`.
- `FROM ops.job_runs r` becomes `r = AS(job_runs, "r")`, read as `r.run_id`, `r.job_id`, `r.dt`.
- The CASE on `j.team` becomes `mapped(j.team, {...}, otherwise="Other")`, named `team_name` with AS.
- The LEFT JOIN's ON keeps both conditions, the job match and `r.dt = '2026-09-24'`, inside `ON=` with `all_of`, which bounds the partitioned read of ops.job_runs.

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, all_of, equals, mapped,
                              statement)
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
        ON=all_of(
            equals(r.job_id, j.job_id),
            equals(r.dt, "2026-09-24"),  # the Hive's r.dt condition, kept in ON=; bounds the partitioned read
        ),
    ),
)
```

Kept as Hive: none. Every part of this query has a Toolbox form.

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

The `where=` bounds the read to the five days from 2026-09-20 to 2026-09-24, so the table's partition column is bounded and the check reads through your `query`. When the Verdict holds, the Key (job_id, dt) tells each row apart across those days, so no two rows share both values. When it doesn't hold, some job_id and dt pair appears on more than one row in that range, and the printed Verdict says so.

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
    ),
)
```

The date condition moved out of WHERE and into the LEFT_JOIN's ON=, beside the join condition, so it only decides which runs match. Every job still appears, and a job with no run on 2026-09-24 is kept once with an empty run_id. The join matches several runs per job, so the Toolbox may warn with RepeatedRowsWarning; that is the one row per run you asked for, and if you want it kept, tell me and I will add `many_matches=True`.

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

## T38

Workflow: convert (batch alerts), at step 1: convert the scripts.

```python
# Names cell
NAME = "alerts"
FILES = ["alerts.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {"default.high_alerts": "keep"}

# Step 1: convert the scripts into Saved tables in dev
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

- Decisions left to you: none is answered in your message. Convert's report names each table's open Decisions (such as its location, Key or a column type). Answer each one in the decisions cell, DECISIONS, at step 2.
- Step 2: answer each table's open Decisions in the decisions cell (yours to make).
- Step 3: write each answer into its table's Table reference with `project.write_decisions(DECISIONS)`; `project.do_next()` runs it for you.
- Step 4: create each table in dev with `run_execute(project.load(table).create(), execute)` for each table in `project.batch_tables(NAME)`.
- Step 5: seed each table that reads itself, once, from its original (`hive_settings("dynamic_partitions")`, then `project.batch_tables(NAME, seeded=True)`).
- Step 6: write each table in dev with `project.run_tables(tables=project.batch_tables(NAME), execute=execute)`.
- Step 7: compare each table with its original with `project.compare_batch(NAME, query=query)`.

Your temporary table high_alerts is kept as a Saved table of its own: STAGING names it `default.high_alerts`, and DATABASE is "default" because you name no database for it.

## T39

Workflow: convert (batch fails), at step 1: convert the scripts. Every step's cell is below, in order, through the compare.

```python
# Names cell
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}

# Step 1: convert the scripts into Saved tables in dev
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)

# Step 2: the decisions cell, with the location you gave
DECISIONS = {
    "mart_dev.daily_fails_mart": {"location": "/data/team/mart_dev.db/daily_fails"},
}

# Step 3: write each answer into its table's Table reference
project.write_decisions(DECISIONS)

# Step 4: create each table in dev
for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)

# Step 5: seed each table that reads itself, once, from its original
run_execute(hive_settings("dynamic_partitions"), execute)
for table in project.batch_tables(NAME, seeded=True):
    run_execute(project.load(table).seed(), execute)

# Step 6: write each table in dev
project.run_tables(tables=project.batch_tables(NAME), execute=execute)

# Step 7: compare each table with its original
project.compare_batch(NAME, query=query)
```

- Decisions left to you: the location is the only one your message answers. If convert's report or `project.check()` names another open Decision, answer it in DECISIONS in the decisions cell.

## T36

The new_table Workflow, at its step 1: make the Table folder for mart_dev.ok_runs from ok_runs.hql.

```python
TABLES = ["mart_dev.ok_runs"]
QUERIES = {"ok_runs": "ok_runs.hql"}
DECISIONS = {}

# step 1: make the Table folder from the query
project.new_table(TABLES, queries=QUERIES)
```

Decisions left to you: none are answered yet, so DECISIONS is empty. Once ok_runs has its Table reference (step 3), its open Decisions are what it asks: its location (where its files sit, such as under /data/team/mart_dev.db/ok_runs), its Key, and any column type the Table reference can't settle. Answer them in the decisions cell, in DECISIONS, by the table's name.

Later steps, in order:

2. Write mart_dev.ok_runs's logic in its Table notebook and save it. Then run its preview() in the notebook, which writes nothing.
3. Write its Table reference from that logic with project.reference_from_logic(TABLES). This changes only files, so project.do_next() runs it for you.
4. Answer its open Decisions in the decisions cell, as above.
5. Write each answer into its Table reference with project.write_decisions(DECISIONS). This changes only files, so project.do_next() runs it for you.
6. Check its rows with run_query(project.load(table).preview(), query) for each table in TABLES. This calls the warehouse, so you run it.
7. Create and write it in dev with run_execute(project.load(table).create(), execute), then project.run_tables(tables=TABLES, execute=execute). This calls the warehouse, so you run it.
8. Compare it with its query, with print(project.compare_batch("ok_runs", query=query)). This calls the warehouse, so you run it.
