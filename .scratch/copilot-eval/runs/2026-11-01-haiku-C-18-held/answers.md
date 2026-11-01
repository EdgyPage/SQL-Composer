date: 2026-11-01
arm: C
model: haiku
files: 18-held

## T03

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, equals, run_query, statement
from references.ops__run_alerts import run_alerts
from warehouse import query, execute

s = statement(
    SELECT(run_alerts.severity, AS(count_rows(), "alerts")),
    FROM(run_alerts),
    WHERE(equals(run_alerts.dt, "2026-09-24")),
    GROUP_BY(run_alerts.severity),
)
rows = run_query(s, query)
```

Notes: This counts the alerts in ops.run_alerts for 2026-09-24 and gives one row per severity, with the columns severity and alerts. The equals on run_alerts.dt bounds the read to that partition, as the partitioned table requires, and it sits in WHERE because the table is read in FROM. There is no opt-out. run_query(s, query) runs the read and returns the rows as a DataFrame.

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

Notes: This Table reference describes the new Saved table mart.team_alerts with its four columns and their Hive types. dt is the partition column, listed last in columns and in partitioned_by. The Key is team and dt, and the Toolbox will use it to trust joins and writes. high_share is a share of a day's alerts, so does_not_add_up keeps the Toolbox from adding it up. The location is the stored path you gave. Save this as references/mart__team_alerts.py, with the variable named team_alerts if you import it, or use the Project actions to write the file for you.

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

This gives each job's `job_id` and its average run time in minutes, `avg_minutes`, for runs dated 2026-09-23 and 2026-09-24, keeping only the jobs whose average is more than 15 minutes. The `between` on `job_runs.dt` bounds the read to those two partitions of the partitioned table. No opt-out is used.

## T12

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
        equals(job_runs.dt, "2026-09-24"),
        equals(run_alerts.severity, "high"),
    ),
)
```

Notes: This gives alert_id and job_name for each high-severity alert dated 2026-09-24 whose run has a row in ops.job_runs, with the job's name taken from ops.jobs. Both partitioned tables, run_alerts and job_runs, are bounded to 2026-09-24 in WHERE. jobs has no partitions, so it needs no bound. Each join is on the joined table's Key (run_id, then job_id). The severity value "high" is taken as written; if the column stores it differently, change that string. No opt-outs are used.

## T15

Code:

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

Notes: The window groups the rows by job_id and orders each group by run_id, so lag takes the duration of the run before each row within the same job. The first run of each job has no earlier run, so its minutes_before is empty (NULL). The WHERE bounds the read of the partitioned table to dt from 2026-09-23 to 2026-09-24.

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

INSERT_INTO adds these rows to what mart.job_day_runs already holds, so the existing rows stay. The WHERE bounds the read of ops.job_runs to the one day, and GROUP_BY over job_id and dt gives one row per Key (job_id, dt). A rerun for the same day would add the rows a second time, so run it once.

## T21

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, all_of, equals, mapped, statement
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

j = AS(jobs, "j")
r = AS(job_runs, "r")

# CASE j.team WHEN 'data' ... ELSE 'Other' END AS team_name
TEAM_NAMES = {"data": "Data", "web": "Web"}

s = statement(
    SELECT(
        j.job_name,
        AS(mapped(j.team, TEAM_NAMES, otherwise="Other"), "team_name"),
        r.run_id,
    ),
    FROM(j),
    # ops.job_runs is partitioned by dt, so its dt bound stays in ON=, with the join condition
    LEFT_JOIN(
        r,
        ON=all_of(equals(r.job_id, j.job_id), equals(r.dt, "2026-09-24")),
    ),
)
```

Parts kept as Hive: none. Every part has its code above: the FROM, the LEFT JOIN with its ON conditions and dt bound, the CASE as `mapped`, and the three columns.

## T24

```python
from sqlglot_composer import between, check_key
from references.ops__job_owners import job_owners
from warehouse import query

v = check_key(job_owners, query=query, where=between(job_owners.dt, "2026-09-20", "2026-09-24"))
print(v)
```

The check reads ops.job_owners through your `query` only, bounded to the days from 2026-09-20 to 2026-09-24 by its `dt` partition column. If the Verdict holds, job_id and dt together tell each row apart on every day in that range. If it doesn't, the printed Verdict names the rows that share a job_id and dt, so those rows need fixing before the Key can be trusted.

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

The `job_runs.dt = '2026-09-24'` condition moved out of WHERE and into the LEFT_JOIN's ON=, beside the join condition on job_id. It now decides which runs match, so every job is still kept, with its runs on that day, and a job with none appears once with empty run columns. The WHERE clause is gone, and the partition bound on job_runs now sits inside ON=, as the rule for LEFT_JOIN requires.

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

Workflow: convert, batch alerts; you are at step 1, Convert the scripts.

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

Decisions left to you: convert's report names the open Decisions for each table it makes, such as its Key or a column type. None is answered yet, and I have not answered any. The report lists them after step 1 runs. With RENAME left as {}, the kept high_alerts table is named mart_dev.high_alerts_default by the default rule; set RENAME if you want another name.

Later steps:
- Step 2: answer each table's open Decisions in the decisions cell, DECISIONS.
- Step 3: write each answer into its table's Table reference with project.write_decisions(DECISIONS); project.do_next() runs it for you.
- Step 4: create each table in dev, with run_execute(project.load(table).create(), execute) for each table in project.batch_tables(NAME).
- Step 5: seed each table that reads itself, once, from its original. None of these tables reads itself, so the seed loop has nothing to seed, but it is still run as listed.
- Step 6: write each table in dev, with project.run_tables(tables=project.batch_tables(NAME), execute=execute).
- Step 7: compare each table with its original, with project.compare_batch(NAME, query=query).

## T39

Workflow: convert, batch fails; you are at step 1, Convert the scripts.

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

# Step 2: the decisions cell, with the answer you gave
DECISIONS = {"mart_dev.daily_fails_mart": {"location": "/data/team/mart_dev.db/daily_fails"}}

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

Decisions left to you: you gave only the location for mart_dev.daily_fails_mart. Convert's report names any other open Decisions for it, such as its Key or a column type. Answer those yourself and add them to DECISIONS before step 3 runs.

Later steps: none are left in words, since you asked for every cell. Step 5 seeds nothing here, because daily_fails does not read itself, but it runs as listed. Promotion to prod is not part of this run. It is the promote Workflow, and you start it only once this compare has passed.

## T36

Workflow new_table, step 1: make the Table folder for mart_dev.ok_runs.

```python
# names cell
TABLES = ["mart_dev.ok_runs"]
QUERIES = {"ok_runs": "ok_runs.hql"}
DECISIONS = {}

# step 1 cell
project.new_table(TABLES, queries=QUERIES)
```

Left to you: the location of mart_dev.ok_runs is a Decision only you can answer. Once you know it, put it in DECISIONS by the table's name, for example {"mart_dev.ok_runs": {"location": "..."}}, and answer the other open Decisions in the decisions cell. DECISIONS is empty for now because you have given no answers yet.

Step 1 changes only files, so project.do_next() runs it for you.

Later steps, in words:
2. Write the table's logic in its Table notebook and save it (your decision).
3. Write its Table reference from that logic with project.reference_from_logic(TABLES).
4. Answer each open Decision in the decisions cell (your decision).
5. Write each answer into the Table reference with project.write_decisions(DECISIONS).
6. Check the rows with run_query(project.load(table).preview(), query) for each table. This calls the warehouse, so you run it.
7. Create and write the table in dev with run_execute(project.load(table).create(), execute) for each table, then project.run_tables(tables=TABLES, execute=execute). This calls the warehouse, so you run it.
8. Compare the table with its query using project.compare_batch(name, query=query) for each name in QUERIES. This calls the warehouse, so you run it.

