date: 2026-11-01
arm: C
model: haiku
files: 21-held

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

Notes: This gives one row per severity, with the alert count in a column named alerts, for the 2026-09-24 partition of ops.run_alerts. The equals on dt bounds the read to that one partition, since the table is partitioned by dt. There is no ORDER_BY, so no LIMIT is needed. rows is a pandas DataFrame.

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

Notes: This is the Table reference for the new Saved table mart.team_alerts. Its Key is team and dt, dt is the partition column and sits last in `columns`, and `location=` is set because the table is written. high_share is listed in `does_not_add_up` so the Toolbox refuses to add it up. Save it as references/mart__team_alerts.py. Your request asked for the name `t`, but the file's rule names the variable after the table, so you may rename `t` to `team_alerts` when you save it.

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

This gives each job_id from ops.job_runs with its average run time in minutes, as avg_minutes, for runs dated 2026-09-23 through 2026-09-24, keeping only the jobs whose average is more than 15 minutes. The WHERE bounds the read on the partition column dt, as the table is partitioned by dt. There are no opt-outs, and no ORDER_BY, so no LIMIT is needed. To run it, pass `s` to `run_query(s, query)` after `from warehouse import query`.

## T12

**Code**

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

**Notes**

This gives each high-severity alert on 2026-09-24 once, as its alert_id with the name of the job whose run raised it. Both joins are on each joined table's whole Key (run_id, then job_id), so no row repeats. The JOIN keeps only alerts whose run and job both match. Both partitioned tables, run_alerts and job_runs, are bounded to 2026-09-24 in WHERE, and jobs has no partitions so it needs no bound. No opt-out is used. The severity value "high" is an assumption about how the table stores it; change that string if the stored text differs.

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

The window sits over each job's runs in run_id order, and lag gives the duration of the job's run just before each row, as minutes_before. The WHERE keeps only the two days, and the window reads just those kept rows, so a job's first run in the range shows no value when its previous run falls on 2026-09-22 or earlier. If that earlier run should count, the range needs to be widened to read it.

## T18

```python
from sqlglot_composer import AS, FROM, GROUP_BY, INSERT_INTO, SELECT, WHERE, count_rows, equals, statement
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

This uses INSERT_INTO, not INSERT_OVERWRITE, because the rows are added to what mart.job_day_runs already holds. A rerun adds them twice, so send it once. The WHERE bounds the read of ops.job_runs to dt 2026-09-23, and GROUP_BY over job_id and dt gives one row per Key, so the write is not refused. Since the write fills a Partition by its dt column, send `run_execute(hive_settings("dynamic_partitions"), execute)` first, then `run_execute(s, execute)`, with `from warehouse import query, execute` in place.

## T21

This Hive is converted by hand, since the user asked for it piece by piece. Each part is kept in the code:

- `FROM ops.jobs j`: `j = AS(jobs, "j")`, then `FROM(j)`, `j.job_name`, `j.team`.
- `ops.job_runs r`: `r = AS(job_runs, "r")`, then `r.run_id`.
- `CASE j.team WHEN 'data' ... ELSE 'Other' END AS team_name`: `mapped(j.team, {...}, otherwise="Other")`, named with AS.
- `LEFT JOIN ... ON r.job_id = j.job_id AND r.dt = '2026-09-24'`: `LEFT_JOIN(r, ON=all_of(equals(r.job_id, j.job_id), equals(r.dt, "2026-09-24")))`. The partition bound stays inside ON=, since `ops.job_runs` is partitioned by dt.

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

Parts kept as Hive: none. Every part of this query has a Toolbox form above.

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

If the Verdict holds, the Key (job_id, dt) tells each row apart on every day from 2026-09-20 to 2026-09-24, so no job_id has two rows for the same day. If it doesn't hold, some job_id has more than one row on a day in that range, and the Verdict says where, so the Key needs a fix before the table is trusted.

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

The condition on `job_runs.dt` moved out of WHERE and into the LEFT_JOIN's `ON=`, beside the join condition, so the day only decides which runs match; a job with no runs on 2026-09-24 is still kept once, with no run_id.

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

No hand-written Hive is needed: `first_match` with `more_than` covers the label, and the `dt` condition in WHERE bounds the read of the partitioned table to 2026-09-24.

## T38

Workflow convert (the convert notebook), your step 1: convert the scripts into Saved tables in dev.

```python
# names cell
NAME = "alerts"
FILES = ["alerts.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {"default.high_alerts": "keep"}

# step 1: convert the scripts
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

Decision left to you: step 2, answer each table's open Decisions in the decisions cell. After the convert, project.check() names them, such as the location and Key of the kept high_alerts table and of mart_dev.high_alerts_per_run. I have written no DECISIONS, since you gave no answers.

Later steps, in words:
- Step 3: write each answer into its table's Table reference, with project.write_decisions(DECISIONS). It changes only files, so project.do_next() runs it for you.
- Step 4: create each table in dev with run_execute(project.load(table).create(), execute) for each table in project.batch_tables(NAME). This is a call to the warehouse.
- Step 5: seed each table that reads itself, once, from its original. Run the dynamic partitions setting first, then the seed for each table in project.batch_tables(NAME, seeded=True). This is a call to the warehouse.
- Step 6: write each table in dev with project.run_tables(tables=project.batch_tables(NAME), execute=execute). This is a call to the warehouse.
- Step 7: compare each table with its original with project.compare_batch(NAME, query=query).

Note: the STAGING key uses the full name default.high_alerts, because your script gives high_alerts no database and DATABASE is "default". Check it against the name convert's report gives the temporary table before you run the names cell.

## T39

Workflow convert (the convert notebook), your step 1: convert the scripts into Saved tables in dev. Every step's cell is below, in order. Step 2 is yours, and the decisions cell holds the location you gave.

```python
# names cell
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}

# step 1: convert the scripts
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)

# step 2: decisions cell (yours to complete; the Key is still open)
DECISIONS = {"mart_dev.daily_fails_mart": {"location": "/data/team/mart_dev.db/daily_fails"}}

# step 3: write each answer into its table's Table reference
project.write_decisions(DECISIONS)

# step 4: create each table in dev
for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)

# step 5: seed each table that reads itself, once, from its original
run_execute(hive_settings("dynamic_partitions"), execute)
for table in project.batch_tables(NAME, seeded=True):
    run_execute(project.load(table).seed(), execute)

# step 6: write each table in dev
project.run_tables(tables=project.batch_tables(NAME), execute=execute)

# step 7: compare each table with its original
project.compare_batch(NAME, query=query)
```

Decision left to you: step 2, the Key of mart_dev.daily_fails_mart. You gave the location, which is in DECISIONS above, but no Key. Add its Key to the decisions cell, as "key": [...], and check there are no other open Decisions that project.check() names, before step 3's cell runs. Steps 3 to 7 wait until step 2 is done.

Later steps, in words:
- Step 3: write each answer into the Table reference, with project.write_decisions(DECISIONS). project.do_next() runs it for you.
- Step 4: create the table in dev with run_execute(project.load(table).create(), execute). This is a call to the warehouse.
- Step 5: seed each table that reads itself, once, from its original. daily_fails reads ops.job_runs and not itself, so the seed loop finds nothing to seed; the cell is still run as listed. This is a call to the warehouse.
- Step 6: write the table in dev with project.run_tables. This is a call to the warehouse.
- Step 7: compare the table with its original, mart.daily_fails, with project.compare_batch(NAME, query=query). Promote to prod only once this compare has passed; promotion is not part of this request.

## T36

Workflow new_table, step 1: make the Table folder for mart_dev.ok_runs from ok_runs.hql.

```python
# names cell
TABLES = ["mart_dev.ok_runs"]
QUERIES = {"ok_runs": "ok_runs.hql"}
DECISIONS = {}

# step 1 cell (changes only files, so project.do_next() runs it for you)
project.new_table(TABLES, queries=QUERIES)
```

Decision left to you: the table's location, where mart_dev.ok_runs is stored (such as /data/team/mart_dev.db/ok_runs), and any other Decision project.check() lists for it, such as its Key or a column type. Answer them in DECISIONS once known; they are needed at step 4.

Later steps:

2. Write the table's logic in its Table notebook and save it (your decision). Then check what stops it with project.load("mart_dev.ok_runs").preview().
3. Write its Table reference from that logic with project.reference_from_logic(TABLES); project.do_next() runs it for you.
4. Answer its open Decisions in the decisions cell, DECISIONS (your decision).
5. Write each answer into its Table reference with project.write_decisions(DECISIONS); project.do_next() runs it for you.
6. Check its rows with preview(), which writes nothing: print(run_query(project.load("mart_dev.ok_runs").preview(), query)).
7. Create and write it in dev: run_execute(project.load("mart_dev.ok_runs").create(), execute), then project.run_tables(tables=TABLES, execute=execute).
8. Compare it with its query: print(project.compare_batch("ok_runs", query=query)).
