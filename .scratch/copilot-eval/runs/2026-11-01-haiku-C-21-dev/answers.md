date: 2026-11-01
arm: C
model: haiku
files: 21-dev

## T01

**Code**

```python
from sqlglot_composer import FROM, SELECT, run_query, statement
from references.ops__jobs import jobs
from warehouse import query

s = statement(
    SELECT(jobs.job_name, jobs.team),
    FROM(jobs),
)
rows = run_query(s, query)
```

**Notes**

This Statement reads each job's name and team from ops.jobs, and run_query sends it with your `query` and returns a DataFrame with the job_name and team columns. The jobs table has no partitions, so it needs no partition bound and no opt-out. There is no ORDER_BY, so no LIMIT is needed.

## T02

**Code**

```python
from sqlglot_composer import FROM, SELECT, WHERE, equals, run_query, statement
from references import ops
from warehouse import query

s = statement(
    SELECT(ops.job_runs.run_id, ops.job_runs.status),
    FROM(ops.job_runs),
    WHERE(equals(ops.job_runs.dt, "2026-09-24")),
)
rows = run_query(s, query)
```

**Notes**

This Statement lists the run_id and status of each run in ops.job_runs on 2026-09-24, and run_query returns them as a DataFrame. The WHERE clause bounds the read on dt, the table's partition column, so the read covers that one day. No opt-out is used. The `from references import ops` import reaches job_runs through your Database module, as the rules ask.

## T04

```python
from sqlglot_composer import Table

job_day_runs = Table(
    "mart.job_day_runs",
    columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    partitioned_by=["dt"],
    key=["job_id", "dt"],
    location="/data/your_team/mart.db/job_day_runs",
)
t = job_day_runs
```

Notes: This is the Table reference for the new Saved table mart.job_day_runs, to save as references/mart__job_day_runs.py. Its columns are job_id, runs and dt, each with a Hive type, with dt last because it is the partition column in partitioned_by. The Key is job_id and dt, and location gives where the table's files go. The variable t is the name you asked for, set to the same Table as job_day_runs, which follows the file's naming rule.

## T05

```python
from sqlglot_composer import check_key, equals
from references.ops__job_runs import job_runs
from warehouse import query

v = check_key(job_runs, query=query, where=equals(job_runs.dt, "2026-09-24"))
```

Notes: This checks whether the Key run_id tells each row of ops.job_runs apart on 2026-09-24. The where= condition bounds the read to that one partition, and query=query sends the check's reads through your query call. The result is a Verdict in v: print(v) says whether the Key holds, and if v: is true when it does. The execute import is left out because this check only reads.

## T07

```python
from sqlglot_composer import FROM, SELECT, WHERE, between, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(
        equals(job_runs.status, "FAILED"),
        between(job_runs.dt, "2026-09-23", "2026-09-24"),
    ),
)
```

**Notes:** This gives the run_id, job_id and duration_mins of each FAILED run in ops.job_runs from 2026-09-23 through 2026-09-24. The between condition on dt is the partition bound, so the read covers only those two days. No opt-out is used.

## T08

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, statement, sum_of
from references.ops__job_runs import job_runs

# The user asked for every day ops.job_runs holds, so this read is not bounded by dt.
s = statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

**Notes:** This gives each job's total duration_mins, as minutes, over every day ops.job_runs holds. The reads_all_partitions=True opt-out is there because you asked for all days, with no date bound; the comment in the code says why. There is no ORDER_BY, so no LIMIT is needed.

## T10

**Code**

```python
from sqlglot_composer import FROM, JOIN, SELECT, WHERE, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, jobs.job_name, job_runs.status),
    FROM(job_runs),
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
```

**Notes**: This is an inner JOIN, so only runs whose job has a row in ops.jobs stay, with the job's name beside each run. ops.job_runs is partitioned by dt, so its day is bound in WHERE with `equals(job_runs.dt, "2026-09-24")`. ops.jobs has no partitions, so it needs no bound. No opt-outs are used.

## T11

**Code**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, all_of, count_distinct,
                              equals, statement)
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, AS(count_distinct(job_runs.run_id), "runs")),
    FROM(jobs),
    LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
                                  equals(job_runs.dt, "2026-09-24"))),
    GROUP_BY(jobs.job_id, jobs.job_name),
)
```

**Notes**: LEFT_JOIN keeps every job in ops.jobs, and a job with no runs that day gets 0. The day bound on ops.job_runs sits inside ON= rather than in WHERE, because a WHERE on a LEFT_JOIN's table would throw away the jobs with no match. count_distinct(job_runs.run_id) counts each run once and gives 0 for a job with no match, where count_rows() would give 1. GROUP_BY holds job_name as well as job_id, since the name is selected. No opt-outs are used.

## T13

**Code**

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, between, derived, descending, equals,
                              row_number, statement)
from references.ops__job_runs import job_runs

ranked = derived("ranked", statement(
    SELECT(job_runs.job_id, job_runs.run_id, job_runs.duration_mins,
           AS(row_number(PARTITION_BY=job_runs.job_id,
                         ORDER_BY=[descending(job_runs.duration_mins), job_runs.run_id]),
              "longest_first")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
))
s = statement(
    SELECT(ranked.job_id, ranked.run_id, ranked.duration_mins),
    FROM(ranked),
    WHERE(equals(ranked.longest_first, 1)),
)
```

**Notes**

The Derived table numbers each job's runs from 2026-09-23 to 2026-09-24, longest first, and the outer Statement keeps only row 1 of each job, so each job appears once with its longest run. The run_id in the second ORDER_BY column is ascending, so on a tie in duration_mins the smallest run_id wins. The WHERE on job_runs.dt bounds the read to the two days, since ops.job_runs is partitioned by dt.

## T14

**Code**

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows, rollup, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.dt, AS(count_rows(), "runs")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(rollup(job_runs.dt)),
)
```

**Notes**

The count gives one row per day with its runs. The rollup on dt adds one more row that counts both days together, and on that total row dt is empty (NULL). The WHERE on job_runs.dt bounds the read to the two days, since ops.job_runs is partitioned by dt.

## T16

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE,
                              count_rows, equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

DAY = "2026-09-24"

s = statement(
    INSERT_OVERWRITE(job_day_runs, partition={"dt": DAY}),
    SELECT(job_runs.job_id, AS(count_rows(), "runs")),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, DAY)),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
```

The WHERE bounds the read of ops.job_runs to 2026-09-24, and GROUP_BY over job_id and dt gives one row per Key. INSERT_OVERWRITE with `partition={"dt": DAY}` replaces only that day's Partition, so dt is left out of the SELECT. Send it with `run_execute(s, execute)` after `from warehouse import query, execute`.

## T17

```python
# logic
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause,
                              Statement, count_rows, create_table, equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

DAY = "2026-09-24"
PARTITIONED_BY = ["dt"]


def create() -> Statement:
    return create_table(job_day_runs, may_exist=True)


def rows(day: str) -> list[Clause]:
    return [
        SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, day)),
        GROUP_BY(job_runs.job_id, job_runs.dt),
    ]


def preview() -> Statement:
    return statement(*rows(DAY))


def write() -> Statement:
    return statement(
        INSERT_OVERWRITE(job_day_runs, partition={"dt": DAY}),
        *rows(DAY),
    )
```

The logic cell holds only imports, constants and functions, and calls no run_query or run_execute. rows(day) bounds the read of ops.job_runs to that day in WHERE, and groups by job_id and dt, the table's Key. write() replaces DAY's Partition with INSERT_OVERWRITE, so its SELECT leaves out dt and gives job_id and runs in order. The next cell can run `show_hive([create(), write()])` and `run_query(preview(), query)` to check it, and `project.run_tables(execute=execute)` sends it.

## T19

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, equals, is_in,
                              statement)
from references.ops__job_runs import job_runs

STATUS_VALUES = ["FAILED", "SUCCESS", "RETRY", "TEST"]

r = AS(job_runs, "r")
s = statement(
    SELECT(r.job_id, AS(count_rows(), "runs")),
    FROM(r),
    WHERE(equals(r.dt, "2026-09-24"), is_in(r.status, STATUS_VALUES)),
    GROUP_BY(r.job_id),
)
```

Parts kept as Hive: none.

## T20

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, between, derived, equals,
                              if_else, statement, sum_of)
from references.ops__job_events import job_events

e = AS(job_events, "e")
ev = derived(
    "ev",
    statement(
        SELECT(e.job_id, e.event_type),
        FROM(e),
        WHERE(between(e.dt, "2026-09-20", "2026-09-24")),
    ),
)
s = statement(
    SELECT(ev.job_id, AS(sum_of(if_else(equals(ev.event_type, "finish"), 1, 0)), "finishes")),
    FROM(ev),
    GROUP_BY(ev.job_id),
)
```

Parts kept as Hive: none.

## T22

```python
from sqlglot_composer import FROM, SELECT, WHERE, compare_with_original, equals, statement
from references.ops__job_runs import job_runs
from warehouse import query

HIVE = "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-24'"

s0 = statement(
    SELECT(job_runs.run_id, job_runs.status),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
v = compare_with_original(s0, HIVE, query=query, partition={"dt": "2026-09-24"})
print(v)
```

If the Verdict holds, your Statement and the team's Hive return the same rows for 2026-09-24. If it doesn't, the output counts the rows found in one and not in the other on that day, so look at the condition and the columns for that day. The check reads both sides through your `query` and only that one Partition.

## T23

```python
from sqlglot_composer import FROM, SELECT, compare_hive, statement
from references.ops__jobs import jobs

HIVE = "select r.job_id, r.job_name from ops.jobs r -- every job"

s0 = statement(SELECT(jobs.job_id, jobs.job_name), FROM(jobs))
v = compare_hive(s0, HIVE)
print(v)
```

If the Verdict holds, the Hive and the Statement are the same query by text, ignoring spacing, case, comments and short table names. If it doesn't, the texts differ in something that counts, such as a different condition or column. Nothing is run: `compare_hive` sends nothing, and it compares text, not rows, so a query with the same rows but a different condition would not match.

## T25

```python
from sqlglot_composer import FROM, SELECT, WHERE, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
)
```

The `==` on status became `equals(job_runs.status, "FAILED")`, and the WHERE also keeps the partition bound `equals(job_runs.dt, "2026-09-24")` that a read of a partitioned table needs, so the run_id column and the 2026-09-24 day are kept as asked.

## T26

```python
from sqlglot_composer import FROM, LIMIT, ORDER_BY, SELECT, WHERE, descending, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
    ORDER_BY(descending(job_runs.duration_mins)),
    LIMIT(3),
)
```

`LIMIT(3)` now follows the ORDER_BY, so the statement returns the 3 longest runs on 2026-09-24, longest first, which clears the refusal for a sort with no LIMIT while keeping the columns and the day.

## T28

```python
from sqlglot_composer import AS, FROM, SELECT, mapped, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id,
           AS(mapped(jobs.team, {"data": "Data platform", "finance": "Finance"}, otherwise="Other"), "team_label")),
    FROM(jobs),
)
```

This is a one-column lookup on `team`, so `mapped` is used with `otherwise="Other"` for any other team. The label carries its AS name, `team_label`. There is no hand-written Hive in this answer.

## T29

```python
from sqlglot_composer import AS, FROM, SELECT, hive_function, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id,
           AS(hive_function("upper", jobs.job_name), "name_upper")),
    FROM(jobs),
)
```

`hive_function("upper", ...)` calls Hive's upper by name, so it is a function call and not hand-written Hive. There is no hand-written Hive in this answer.

## T31

Workflow: convert (batch daily_ops), step 1: convert the two scripts into your Dev Database.

```python
NAME = "daily_ops"
FILES = ["daily_fails.hql", "daily_alerts.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

Decisions: none are known yet. After the convert, project.check() names any Decision it leaves, and each one is yours to answer in the decisions cell (step 2).

Later steps, in words:
- Step 3: write each answer into its table's Table reference (project.write_decisions(DECISIONS)).
- Step 4: create each table in dev.
- Step 5: seed each table that reads itself, once, from its original.
- Step 6: write each table in dev.
- Step 7: compare each table with its original (project.compare_batch(NAME, query=query)). A table is promoted only once its compare has passed.

## T32

Workflow: convert (batch fails), step 1: convert the Hive into your Dev Database, folding the staging table ops_reports.failed_runs.

```python
NAME = "fails"
FILES = []
HIVE = """
CREATE TABLE ops_reports.failed_runs AS
SELECT r.job_id
FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status = 'FAILED';

INSERT OVERWRITE TABLE mart.fails_per_job PARTITION (dt = '2026-09-24')
SELECT f.job_id, COUNT(*) AS fails
FROM ops_reports.failed_runs f
GROUP BY f.job_id;
"""
DATABASE = "default"
RENAME = {}
STAGING = {"ops_reports.failed_runs": "fold"}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

Decisions: none are known yet. After the convert, project.check() names any Decision it leaves, and each one is yours to answer in the decisions cell (step 2).

Later steps, in words:
- Step 3: write each answer into its table's Table reference (project.write_decisions(DECISIONS)).
- Step 4: create each table in dev.
- Step 5: seed each table that reads itself, once, from its original.
- Step 6: write each table in dev.
- Step 7: compare each table with its original (project.compare_batch(NAME, query=query)). A table is promoted only once its compare has passed.

## T33

Workflow: convert (batch fails), step 2: answer the Decisions in the decisions cell, then step 3 writes the answers into the Table reference.

```python
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "types": {"dt": "string"},
    },
}

project.write_decisions(DECISIONS)
```

The names cell is not repeated, as you asked for the decisions cell and the write cell only. NAME = "fails" stays as it is in your names cell. Both Decisions project.check() named are answered above, so none is left for you.

Later steps, in words (you run these yourself):
- Step 4: create each table in dev.
- Step 5: seed each table that reads itself, once, from its original.
- Step 6: write each table in dev.
- Step 7: compare each table with its original (project.compare_batch(NAME, query=query)). A table is promoted only once its compare has passed.

## T37

Workflow: convert (batch runs_per_job), step 1: convert the query into your Dev Database. Its tables are in the ops database, so DATABASE is "ops".

```python
NAME = "runs_per_job"
FILES = []
HIVE = None
DATABASE = "ops"
RENAME = {}
STAGING = {}
query = """
SELECT r.job_id, COUNT(*) AS runs
FROM job_runs r
WHERE r.dt = '2026-09-24'
GROUP BY r.job_id
"""

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

The query names no staging table, so STAGING is empty. Its query is defined in the names cell so the convert call can read it.

Decisions: none are known yet. After the convert, project.check() names any Decision it leaves, and each one is yours to answer in the decisions cell (step 2).

Later steps, in words:
- Step 3: write each answer into its table's Table reference (project.write_decisions(DECISIONS)).
- Step 4: create each table in dev.
- Step 5: seed each table that reads itself, once, from its original.
- Step 6: write each table in dev.
- Step 7: compare each table with its original (project.compare_batch(NAME, query=query)). A table is promoted only once its compare has passed.

## T34

The references Workflow, at its first step: writing the Table references for ops.jobs and ops.run_alerts from DESCRIBE.

```python
# names cell
TABLES = ["ops.jobs", "ops.run_alerts"]
DECISIONS = {}

# step 1's cell
project.add_references(TABLES, query=query)
```

Decisions left to you: once step 1 writes the references, each open Decision for ops.jobs and ops.run_alerts (such as its location, Key or a column type) is yours to answer in the decisions cell, DECISIONS. You have given no answers yet, so DECISIONS is empty.

Later steps, in words:
- Step 2: answer each table's open Decisions in the decisions cell (yours to make).
- Step 3: write each answer into its table's Table reference with project.write_decisions(DECISIONS), which project.do_next() runs for you.
- Step 4: refresh the Reference sheet and the Database modules with project.refresh_reference_sheet(TABLES), which project.do_next() runs for you.

## T35

The new_table Workflow, at its first step: making the Table folder for mart_dev.job_day_counts.

```python
# names cell
TABLES = ["mart_dev.job_day_counts"]
QUERIES = {}

# step 1's cell
project.new_table(TABLES, queries=QUERIES)
```

Decisions left to you: step 2 is writing the table's logic in its Table notebook and saving it, since you will write it yourself. Then project.load(table).preview() says what stops it, if anything does. Any Decision the Table reference raises (such as its location, Key or a column type) is yours to answer in DECISIONS.

Later steps, in words:
- Step 3: project.reference_from_logic(TABLES) writes the Table reference from your logic, never by hand; project.do_next() runs it for you.
- Step 4: answer each table's open Decisions in the decisions cell (yours to make).
- Step 5: project.write_decisions(DECISIONS) writes each answer into its Table reference; project.do_next() runs it for you.
- Step 6: check each table's rows with preview(), a call to the warehouse you run with run_query.
- Step 7: create and write each table in dev with run_execute and project.run_tables(tables=TABLES, execute=execute), a call to the warehouse you run.
- Step 8 does not apply: it compares a table made from a query with that query, and QUERIES is empty here.
