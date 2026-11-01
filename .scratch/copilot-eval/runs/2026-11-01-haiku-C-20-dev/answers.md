date: 2026-11-01
arm: C
model: haiku
files: 20-dev

## T01

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

Notes: This reads each job's name and team from ops.jobs, with no WHERE, since the request asks for every job. The jobs table has no partition columns, so it needs no bound and no opt-out. run_query sends the Statement through the query call from warehouse.py and returns the rows as a pandas DataFrame.

## T02

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

Notes: ops.job_runs is partitioned by dt, so the WHERE bounds the read to 2026-09-24 with equals on that partition column, and no opt-out is used. run_query sends the Statement through the query call from warehouse.py and returns run_id and status for each run as a pandas DataFrame.

## T04

```python
from sqlglot_composer import Table

t = Table(
    "mart.job_day_runs",
    columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    partitioned_by=["dt"],
    key=["job_id", "dt"],
    location="/data/your_team/mart.db/job_day_runs",
)
```

Notes: This is the Table reference for the new Saved table mart.job_day_runs. Its three columns are typed in Hive, dt is the partition column and is listed both in `columns` and in `partitioned_by`, and the Key is job_id and dt. Because it is a Saved table it has a `location=`. Save it as references/mart__job_day_runs.py, since the file and the variable are named after the table. Nothing here reads the warehouse, so the file needs no `query` or `execute` import.

## T05

```python
from sqlglot_composer import check_key, equals
from references.ops__job_runs import job_runs
from warehouse import query

v = check_key(job_runs, query=query, where=equals(job_runs.dt, "2026-09-24"))
```

Notes: This counts whether ops.job_runs's Key, run_id, tells each row apart on 2026-09-24. Its table is partitioned by dt, so the check is bounded with `where=equals(job_runs.dt, "2026-09-24")`, and it passes `query=query` to read the warehouse. Run `print(v)` to see whether the Key holds; `if v:` is true when it does.

## T07

**Code**

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

**Notes**

This gives each FAILED run in ops.job_runs for 2026-09-23 and 2026-09-24, with its run_id, job_id and duration_mins. The partitioned dt column is bounded by a between in WHERE, so the read stays within those two days. No opt-out is used.

## T08

**Code**

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, statement, sum_of
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
    # The user asked for every day ops.job_runs holds, so this read is not bounded by dt.
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

**Notes**

This gives each job_id with the sum of its duration_mins as minutes, grouped by job_id. It reads every day ops.job_runs holds, which is what the user asked for. The one opt-out is reads_all_partitions=True on FROM, and the comment in the code says why.

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

**Notes**

This gives each run in ops.job_runs on 2026-09-24 with its job's name from ops.jobs. JOIN keeps only runs whose job has a match in ops.jobs. The partition bound on job_runs.dt sits in WHERE, and ops.jobs is joined on its whole Key, job_id. ops.jobs is not partitioned, so it needs no bound. There are no opt-outs.

## T11

**Code**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, all_of, count_distinct,
                              equals, statement)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, AS(count_distinct(job_runs.run_id), "runs")),
    FROM(jobs),
    LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
                                  equals(job_runs.dt, "2026-09-24"))),
    GROUP_BY(jobs.job_id, jobs.job_name),
)
```

**Notes**

This gives every job in ops.jobs, with how many runs it had on 2026-09-24. A job with no run that day stays, with 0 in runs, because count_distinct(job_runs.run_id) counts only matched rows, where count_rows() would give 1. The partition bound on job_runs.dt sits in ON=, not WHERE, so a job with no runs that day is not thrown away. The join is on job_id, which is less than job_runs' Key run_id, so one job can match many runs; counting distinct run_id keeps the count right. There are no opt-outs.

## T13

**Code**

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, between, derived, descending,
                              equals, row_number, statement)
from references.ops__job_runs import job_runs

longest = derived("longest", statement(
    SELECT(job_runs.job_id, job_runs.run_id, job_runs.duration_mins,
           AS(row_number(PARTITION_BY=job_runs.job_id,
                         ORDER_BY=[descending(job_runs.duration_mins), job_runs.run_id]),
              "longest_first")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
))
s = statement(
    SELECT(longest.job_id, longest.run_id, longest.duration_mins),
    FROM(longest),
    WHERE(equals(longest.longest_first, 1)),
)
```

**Notes**

The inner Derived table numbers each job's runs from the longest down, with the smallest run_id first on a tie, and it is bounded to 2026-09-23 and 2026-09-24 in its own WHERE. The outer Statement keeps row 1 of each job, so it gives one row per job with job_id, run_id and duration_mins. The window's value is tested only in the Statement that reads the Derived table, not in its own WHERE.

## T14

**Code**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows,
                              rollup, statement)
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.dt, AS(count_rows(), "runs")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(rollup(job_runs.dt)),
)
```

**Notes**

The Statement counts the runs of each day from 2026-09-23 to 2026-09-24, and the rollup adds one total row for both days. On that total row dt is empty (NULL) and runs is the count for the two days together. The partition bound sits in WHERE, so only those two days are read.

## T16

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE,
                              count_rows, equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

s = statement(
    INSERT_OVERWRITE(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
```

The WHERE bounds the read of ops.job_runs to 2026-09-24, and GROUP_BY over job_id and dt gives one row per Key of mart.job_day_runs, so no unproven_key is needed. INSERT_OVERWRITE replaces the rows that day held, with dt last in SELECT to match the table's columns. To send it by hand, run `run_execute(create_table(job_day_runs, may_exist=True), execute)` and `run_execute(hive_settings("dynamic_partitions"), execute)` first, then `run_execute(s, execute)`, after `from warehouse import query, execute`.

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
        SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, day)),
        GROUP_BY(job_runs.job_id, job_runs.dt),
    ]


def preview() -> Statement:
    return statement(*rows(DAY))


def write() -> Statement:
    return statement(INSERT_OVERWRITE(job_day_runs), *rows(DAY))
```

The logic cell only imports, sets constants and defines functions, and calls no run_query or run_execute. rows(day) bounds each read of ops.job_runs by its dt, and write() replaces only the rows of DAY. Save the Table notebook, then run `project.run_tables(execute=execute)` to send the writes.

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

No part is kept as Hive.

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

No part is kept as Hive.

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

## T23

```python
from sqlglot_composer import FROM, SELECT, compare_hive, statement
from references.ops__jobs import jobs

HIVE = "select r.job_id, r.job_name from ops.jobs r -- every job"

s0 = statement(SELECT(jobs.job_id, jobs.job_name), FROM(jobs))
v = compare_hive(s0, HIVE)
print(v)
```

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

The `==` on `job_runs.status` became `equals(job_runs.status, "FAILED")`, as the refusal's Usual fix says, and I added `equals(job_runs.dt, "2026-09-24")` so the read is bounded to the one day you asked for, since ops.job_runs is partitioned by dt.

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

I added `LIMIT(3)` after the ORDER_BY, which gives the top 3 longest runs on 2026-09-24, longest first, as the refusal's top-N fix describes; the day bound was already in WHERE, so nothing else changed.

## T28

```python
from sqlglot_composer import AS, FROM, SELECT, mapped, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id,
           AS(mapped(jobs.team, {"data": "Data platform", "finance": "Finance"}, otherwise="Other"),
              "team_label")),
    FROM(jobs),
)
```

The label is a lookup on one column, so it uses `mapped`, with `otherwise="Other"` for any other team. No hand-written Hive is needed here.

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

Hive's `upper` has no Toolbox name, so `hive_function` calls it with the column `jobs.job_name`. No hand-written Hive is needed here.

## T31

Workflow: convert (batch daily_ops), at step 1: convert the two scripts into dev.

```python
# names cell
NAME = "daily_ops"
FILES = ["daily_fails.hql", "daily_alerts.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

With RENAME = {}, the two land in mart_dev as daily_fails_mart and daily_alerts_mart.

Decisions: none is answered here. After step 1, run project.check(); each Decision it names (a location, Key or column type for one table) is yours to answer in the decisions cell.

Later steps, in words:
- Step 3: write your answers into each table's Table reference with project.write_decisions(DECISIONS); project.do_next() runs it for you.
- Step 4: create each table in dev, for each table in project.batch_tables(NAME).
- Step 5: seed each table that reads itself, once, from its original. Neither script reads its own table, so this seeds nothing.
- Step 6: write each table in dev with project.run_tables(tables=project.batch_tables(NAME), execute=execute).
- Step 7: compare each table with its original with project.compare_batch(NAME, query=query). Promote a table only once its compare has passed.

## T32

Workflow: convert (batch fails), at step 1: convert the Hive into dev.

```python
# names cell
NAME = "fails"
FILES = []
HIVE = """CREATE TABLE ops_reports.failed_runs AS
SELECT r.job_id
FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status = 'FAILED';

INSERT OVERWRITE TABLE mart.fails_per_job PARTITION (dt = '2026-09-24')
SELECT f.job_id, COUNT(*) AS fails
FROM ops_reports.failed_runs f
GROUP BY f.job_id;"""
DATABASE = "default"
RENAME = {}
STAGING = {"ops_reports.failed_runs": "fold"}

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

Folded, ops_reports.failed_runs is never made: its query goes inside mart_dev.fails_per_job_mart, the table that reads it. With RENAME = {}, the output table is mart_dev.fails_per_job_mart.

Decisions: none is answered here. After step 1, run project.check(); each Decision it names is yours to answer in the decisions cell.

Later steps, in words:
- Step 3: write your answers into each table's Table reference with project.write_decisions(DECISIONS); project.do_next() runs it for you.
- Step 4: create each table in dev, for each table in project.batch_tables(NAME).
- Step 5: seed each table that reads itself, once, from its original. fails_per_job does not read its own table, so this seeds nothing.
- Step 6: write each table in dev with project.run_tables(tables=project.batch_tables(NAME), execute=execute).
- Step 7: compare each table with its original with project.compare_batch(NAME, query=query). Promote a table only once its compare has passed.

## T33

Workflow: convert (batch fails), at its decisions cell: both Decisions project.check() names for mart_dev.daily_fails_mart are answered below.

```python
# decisions cell
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "types": {"dt": "string"},
    },
}

# cell that writes the answers in
project.write_decisions(DECISIONS)
```

No Decision is left to you for this table: dt is answered as string, and the location as the folder you gave. The names cell is not repeated; NAME = "fails" stays as set in your notebook.

Later steps, in words, to run yourself after the write (it changes only files):
- Step 4: create each table in dev, for each table in project.batch_tables(NAME).
- Step 5: seed each table that reads itself, once, from its original. daily_fails does not read its own table, so this seeds nothing.
- Step 6: write each table in dev with project.run_tables(tables=project.batch_tables(NAME), execute=execute).
- Step 7: compare each table with its original with project.compare_batch(NAME, query=query). Promote a table only once its compare has passed.

## T37

Workflow: convert (batch runs_per_job), at step 1: convert the query into dev.

```python
# names cell
NAME = "runs_per_job"
FILES = []
HIVE = """SELECT r.job_id, COUNT(*) AS runs
FROM job_runs r
WHERE r.dt = '2026-09-24'
GROUP BY r.job_id"""
DATABASE = "ops"
RENAME = {}
STAGING = {}

# step 1 cell
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

The query only SELECTs, so it becomes a Saved table named for NAME, runs_per_job. DATABASE = "ops" is the database its job_runs table lives in.

Decisions: none is answered here. After step 1, run project.check(); each Decision it names is yours to answer in the decisions cell.

Later steps, in words:
- Step 3: write your answers into the Table reference with project.write_decisions(DECISIONS); project.do_next() runs it for you.
- Step 4: create each table in dev, for each table in project.batch_tables(NAME).
- Step 5: seed each table that reads itself, once, from its original. This query's table does not read itself, so this seeds nothing.
- Step 6: write each table in dev with project.run_tables(tables=project.batch_tables(NAME), execute=execute).
- Step 7: compare each table with its original with project.compare_batch(NAME, query=query). Promote a table only once its compare has passed.

## T34

Workflow: references, at step 1 (write the Table references from DESCRIBE for ops.jobs and ops.run_alerts).

```python
# names cell
TABLES = ["ops.jobs", "ops.run_alerts"]

# step 1's cell (a call to the warehouse, yours to run)
project.add_references(TABLES, query=query)
```

Left to you: each table's open Decisions that step 1 raises, such as its location, Key or a column type. Answer them in the decisions cell as DECISIONS, keyed by each table's name as project.check() writes it.

Later steps, in words:
- Step 2: answer each table's open Decisions in the decisions cell (yours to make).
- Step 3: write each answer into its Table reference with project.write_decisions(DECISIONS); project.do_next() runs it for you.
- Step 4: refresh the Reference sheet and the Database modules with project.refresh_reference_sheet(TABLES); project.do_next() runs it for you.

## T35

Workflow: new_table, at step 1 (make each Table folder for mart_dev.job_day_counts).

```python
# names cell
TABLES = ["mart_dev.job_day_counts"]
QUERIES = {}

# step 1's cell (changes only files, so project.do_next() runs it for you)
project.new_table(TABLES, queries=QUERIES)
```

Left to you: the logic of mart_dev.job_day_counts, written in its Table notebook (step 2), and any open Decisions for it, such as its location, Key or a column type, answered in the decisions cell once step 1 has raised them.

Later steps, in words:
- Step 2: write the logic in the Table notebook for mart_dev.job_day_counts and save it (yours to make), then preview it with project.load(table).preview(), which writes nothing and says what stops it, if anything does.
- Step 3: write its Table reference from its logic with project.reference_from_logic(TABLES), which is never written by hand; project.do_next() runs it for you.
- Step 4: answer its open Decisions in the decisions cell (yours to make).
- Step 5: write each answer into its Table reference with project.write_decisions(DECISIONS); project.do_next() runs it for you.
- Step 6: check its rows with run_query(project.load(table).preview(), query) (a call to the warehouse, yours to run).
- Step 7: create and write it in dev with run_execute(project.load(table).create(), execute) and project.run_tables(tables=TABLES, execute=execute) (a call to the warehouse, yours to run).
- Step 8: nothing to compare here, since no query is given (QUERIES is empty), so this step does not apply.

The Workflow's last cell, project.run_workflow(...), is not given because you asked for particular cells only; it would run the steps left, up to the first only you can do.
