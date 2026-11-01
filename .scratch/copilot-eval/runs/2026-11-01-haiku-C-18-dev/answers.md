date: 2026-11-01
arm: C
model: haiku
files: 18-dev

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

This reads each job's name and team from ops.jobs through the Table reference `jobs`, and `run_query(s, query)` runs it and returns the rows as a DataFrame. The table has no partition columns, so it needs no bound and no opt-out.

## T02

**Code**

```python
from sqlglot_composer import FROM, SELECT, WHERE, equals, statement
from references import ops

s = statement(
    SELECT(ops.job_runs.run_id, ops.job_runs.status),
    FROM(ops.job_runs),
    WHERE(equals(ops.job_runs.dt, "2026-09-24")),
)
```

**Notes**

This builds the Statement that lists the run_id and status of each run in ops.job_runs on 2026-09-24. The table is partitioned by dt, so the WHERE clause bounds it on that partition column; no opt-out is used. To get the rows, add `from warehouse import query` and `rows = run_query(s, query)`, with `run_query` imported from sqlglot_composer.

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

Notes: This is the Table reference for the new Saved table mart.job_day_runs, with its three columns in order and each in Hive types. dt is the partition column, so it sits last in columns and in partitioned_by. The Key job_id and dt goes in key=, and location= sets where the table's files go, since the notebook writes this table. Save it as references/mart__job_day_runs.py.

## T05

```python
from sqlglot_composer import check_key, equals
from references.ops__job_runs import job_runs
from warehouse import query

v = check_key(job_runs, query=query, where=equals(job_runs.dt, "2026-09-24"))
```

Notes: This checks whether run_id tells each row of ops.job_runs apart on 2026-09-24. The where= condition bounds the read, since the table is partitioned by dt. Print v to see whether the Key holds; `if v:` is true when it does.

## T07

**Code**

```python
from sqlglot_composer import FROM, SELECT, WHERE, between, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(equals(job_runs.status, "FAILED"), between(job_runs.dt, "2026-09-23", "2026-09-24")),
)
```

**Notes**

This Statement lists the run_id, job_id and duration_mins of every ops.job_runs row with status FAILED, dated 2026-09-23 through 2026-09-24. The dt partition is bounded with `between` in WHERE, so no opt-out is needed. Run it with `run_query(s, query)` after `from warehouse import query, execute`.

## T08

**Code**

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, statement, sum_of
from references.ops__job_runs import job_runs

# The user asked for every day ops.job_runs holds, so this read opts out of the dt partition bound.
s = statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

**Notes**

This Statement gives each job_id with its total duration_mins, named minutes, summed over all partitions of ops.job_runs. The opt-out is `reads_all_partitions=True` on FROM, because the request covers every day the table holds and no single dt bound would give that. Run it with `run_query(s, query)` after `from warehouse import query, execute`.

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

This gives each run in ops.job_runs on 2026-09-24 with its job's name from ops.jobs, and only runs whose job is in ops.jobs stay, since it is a plain JOIN. The join is on jobs' whole Key, job_id. The day is bound in WHERE because job_runs is partitioned by dt; ops.jobs has no partitions, so it needs no bound. No opt-outs are used.

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

This gives every job in ops.jobs with its count of runs on 2026-09-24, and 0 for a job with no runs, since LEFT_JOIN keeps every job row. The count is count_distinct(job_runs.run_id), because count_rows() would give 1 for a job with no match. job_runs is partitioned by dt, so the day is bound inside ON= (not WHERE, which would drop the jobs with no runs). job_name is in GROUP_BY with job_id so that the grouped query is valid in Hive. No opt-outs are used.

## T13

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, between, derived, descending, equals,
                              row_number, statement)
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

**Notes:** The inner Statement numbers each job's runs from longest to shortest, with the smallest run_id first on a tie, and its WHERE bounds ops.job_runs to 2026-09-23 and 2026-09-24. The outer Statement keeps row 1 of each job, so you get one row per job with job_id, run_id and duration_mins.

## T14

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

**Notes:** The Statement counts the rows of ops.job_runs for each dt from 2026-09-23 to 2026-09-24. The rollup adds one total row across both days, and that row's dt is blank (NULL).

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

INSERT_OVERWRITE replaces the 2026-09-24 Partition of mart.job_day_runs rather than adding to it. The GROUP_BY over job_id and dt gives one row per Key, as the table requires. The equals Condition bounds the read of ops.job_runs to that day. To send it, add `from warehouse import query, execute` and run `run_execute(s, execute)`.

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

The logic cell holds only imports, constants and functions, and calls no run_query or run_execute. The equals Condition bounds the read of ops.job_runs to DAY's Partition. write() starts with INSERT_OVERWRITE, so DAY's rows in mart.job_day_runs are replaced. Save the notebook, then run_tables sends it.

## T19

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, equals, is_in, statement
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

Kept as Hive: none.

## T20

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, between, derived, equals, if_else,
                              statement, sum_of)
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

Kept as Hive: none.

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

The check reads both your Statement and your team's Hive through your `query`, on the one Partition 2026-09-24, and counts the rows that are in one and not the other. If it holds, no row differs, so the two give the same rows that day. If it doesn't hold, the Verdict shows the rows counted in one and not the other, and the two need a look before the Hive is replaced. The Hive's columns are run_id and status, the same names and order as the Statement's.

## T23

```python
from sqlglot_composer import FROM, SELECT, compare_hive, statement
from references.ops__jobs import jobs

HIVE = "select r.job_id, r.job_name from ops.jobs r -- every job"

s0 = statement(SELECT(jobs.job_id, jobs.job_name), FROM(jobs))
v = compare_hive(s0, HIVE)
print(v)
```

This check compares the text only and sends nothing, so no query runs. If it holds, the Statement is the same query as your team's Hive: the difference in spacing, case, the comment and the short table name r doesn't count. If it doesn't hold, the Statement differs from the Hive in a column, table or condition, and the Verdict says so. The ops.jobs table has no partitions, so it needs no bound.

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

The `==` on `job_runs.status` became `equals(job_runs.status, "FAILED")`, the Condition function the refusal's Usual fix names. I also added `equals(job_runs.dt, "2026-09-24")` to WHERE, because ops.job_runs is partitioned by dt and every read of it needs a bound; it is the day you asked for.

## T26

```python
from sqlglot_composer import FROM, SELECT, WHERE, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
    # Longest first is ORDER_BY on job_runs.duration_mins, descending. This file does
    # not name the descending sort, so it is not written here: load file 03 (building a
    # Statement) in a new chat to write it. The top 3 then needs LIMIT(3) right after
    # that ORDER_BY. Without the ORDER_BY and LIMIT(3), this reads every run on the day.
)
```

The refusal is "ORDER_BY has no LIMIT.", and its Usual fix for a top N is `LIMIT(3)` after the ORDER_BY. The bound on `dt` for 2026-09-24 is kept, so the read stays on the one partition. I did not write the descending sort, because this file doesn't name a function for it and I won't guess one; file 03 covers it, so load that file in a new chat to finish the longest-first ORDER_BY and add LIMIT(3) after it.

## T28

```python
from sqlglot_composer import AS, FROM, SELECT, mapped, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id,
           AS(mapped(jobs.team,
                     {"data": "Data platform", "finance": "Finance"},
                     otherwise="Other"),
              "team_label")),
    FROM(jobs),
)
```

No hand-written Hive here: `mapped` looks up the one column `team`, and any team other than data or finance gets "Other".

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

No hand-written Hive here: `upper` has no Toolbox name, so `hive_function` calls Hive's own upper on `job_name`.

## T31

Workflow: convert, your step 1 (convert the two scripts into your Dev Database as the batch daily_ops).

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

Decisions left to you: none are answered yet. Run `project.check()` after step 1; it names each table's open Decisions, such as its location, Key or a column type. Those answers are yours to give in the decisions cell (step 2).

Later steps, in words:
- Step 2: answer each table's open Decisions in the decisions cell.
- Step 3: write each answer into its table's Table reference. This changes only files, so `project.do_next()` runs it for you.
- Step 4: create each table in Dev, one at a time, in the batch (a call to the warehouse, yours to run).
- Step 5: seed each table that reads itself, once, from its original. Neither script reads the table it writes, so expect nothing to seed.
- Step 6: write each table in Dev (a call to the warehouse, yours to run).
- Step 7: compare each table with its original (a call to the warehouse, yours to run). A table is promoted only after its compare has passed.

## T32

Workflow: convert, your step 1 (convert this Hive into your Dev Database as the batch fails, folding the staging table).

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

Folded: ops_reports.failed_runs is never made. Its query goes inside the statement that reads it, the fails_per_job table.

Decisions left to you: none are answered yet. Run `project.check()` after step 1; it names the open Decisions of the table this batch writes, which you answer in the decisions cell (step 2).

Later steps, in words:
- Step 2: answer each table's open Decisions in the decisions cell.
- Step 3: write each answer into its table's Table reference. This changes only files, so `project.do_next()` runs it for you.
- Step 4: create each table in Dev (a call to the warehouse, yours to run).
- Step 5: seed each table that reads itself, once, from its original. fails_per_job does not read itself, so expect nothing to seed.
- Step 6: write each table in Dev (a call to the warehouse, yours to run).
- Step 7: compare each table with its original (a call to the warehouse, yours to run). A table is promoted only after its compare has passed.

## T33

Workflow: convert, your step 2 (answer the Decisions in the decisions cell); step 3 writes the answers in.

```python
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "types": {"dt": "string"},
    },
}

project.write_decisions(DECISIONS)
```

Decisions left to you: none. Both open Decisions that `project.check()` names are answered above: the location, and dt's type as string.

Later steps, in words, which you run yourself:
- Step 4: create each table in Dev (a call to the warehouse, yours to run).
- Step 5: seed each table that reads itself, once, from its original. daily_fails does not read itself, so expect nothing to seed.
- Step 6: write each table in Dev (a call to the warehouse, yours to run).
- Step 7: compare each table with its original (a call to the warehouse, yours to run). A table is promoted only after its compare has passed.

## T37

Workflow: convert, your step 1 (convert this query into your Dev Database as the batch runs_per_job).

```python
NAME = "runs_per_job"
FILES = []
HIVE = """
SELECT r.job_id, COUNT(*) AS runs
FROM job_runs r
WHERE r.dt = '2026-09-24'
GROUP BY r.job_id
"""
DATABASE = "ops"
RENAME = {}
STAGING = {}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

The text has no CREATE TABLE or INSERT, so it names no table for convert to write, and this batch would make no Saved table in Dev. I have not invented a target table name. Tell me which table the query should write (its database and name, and whether it is a CREATE TABLE or an INSERT OVERWRITE with a partition), and I will put that statement in the Hive text.

Decisions left to you: none are answered yet. Once the batch writes a table, `project.check()` names its open Decisions, and you answer them in the decisions cell (step 2).

Later steps, in words:
- Step 2: answer each table's open Decisions in the decisions cell.
- Step 3: write each answer into its table's Table reference. This changes only files, so `project.do_next()` runs it for you.
- Step 4: create each table in Dev (a call to the warehouse, yours to run).
- Step 5: seed each table that reads itself, once, from its original, if any does.
- Step 6: write each table in Dev (a call to the warehouse, yours to run).
- Step 7: compare each table with its original (a call to the warehouse, yours to run). A table is promoted only after its compare has passed.

## T34

The references Workflow, step 1: write the Table references for ops.jobs and ops.run_alerts from DESCRIBE.

```python
# Names cell
TABLES = ["ops.jobs", "ops.run_alerts"]

# Step 1 cell
project.add_references(TABLES, query=query)
```

Left to you, and the later steps in words:
- Step 2 (yours to decide): answer each table's open Decisions in the decisions cell, DECISIONS, such as its location, its Key or a column type. I have not answered any of them.
- Step 3: write each answer into its table's Table reference with `project.write_decisions(DECISIONS)`; project.do_next() runs it for you.
- Step 4: refresh the Reference sheet and the Database modules with `project.refresh_reference_sheet(TABLES)`; project.do_next() runs it for you.

## T35

The new_table Workflow, step 1: make the Table folder for mart_dev.job_day_counts. You write its logic yourself, so there is no query and QUERIES is empty.

```python
# Names cell
TABLES = ["mart_dev.job_day_counts"]
QUERIES = {}

# Step 1 cell
project.new_table(TABLES, queries=QUERIES)
```

Left to you, and the later steps in words:
- Step 2 (yours to write): write the table's logic in its Table notebook and save it. Then check it with `project.load("mart_dev.job_day_counts").preview()`, which says what stops it, if anything does.
- Step 3: write the Table reference from its logic with `project.reference_from_logic(TABLES)`; project.do_next() runs it for you.
- Step 4 (yours to decide): answer its open Decisions in the decisions cell, DECISIONS, such as its location, its Key or a column type. I have not answered any of them.
- Step 5: write each answer into its Table reference with `project.write_decisions(DECISIONS)`; project.do_next() runs it for you.
- Step 6: check its rows with `run_query(project.load("mart_dev.job_day_counts").preview(), query)`, a call to the warehouse, yours to run.
- Step 7: create and write it in dev with `run_execute(project.load("mart_dev.job_day_counts").create(), execute)` and `project.run_tables(tables=TABLES, execute=execute)`, calls to the warehouse, yours to run.
- Step 8: compare with its query. This applies only to a table made from a query, and QUERIES is empty, so there is nothing to compare.

