date: 2026-11-01
arm: C
model: haiku
files: 19-dev

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

The jobs table has no partition columns, so it needs no bound. The read runs with `run_query`, which returns a DataFrame of each job's name and team.

## T02

```python
from sqlglot_composer import FROM, SELECT, WHERE, equals, statement
from references import ops

s = statement(
    SELECT(ops.job_runs.run_id, ops.job_runs.status),
    FROM(ops.job_runs),
    WHERE(equals(ops.job_runs.dt, "2026-09-24")),
)
```

The job_runs table is partitioned by dt, so the WHERE clause bounds the read to 2026-09-24. This cell only builds the Statement; to read the rows, run it with `run_query(s, query)` after importing `query` from `warehouse`.

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

Notes: This is the Table reference of the new Saved table mart.job_day_runs. The partition column dt is listed last in `columns` and in `partitioned_by`, the Key is job_id and dt, and the location is where its files go. To keep it in references/mart__job_day_runs.py, name the variable job_day_runs in that file, so the notebook can import it by name; here it is assigned to `t` as you asked.

## T05

```python
from sqlglot_composer import check_key, equals
from references.ops__job_runs import job_runs
from warehouse import query

v = check_key(job_runs, query=query, where=equals(job_runs.dt, "2026-09-24"))
```

Notes: ops.job_runs is partitioned by dt, so the check is bounded to 2026-09-24 with `where=`, and it counts whether run_id tells each row apart on that day. Run `print(v)` to see whether the Key holds; `if v:` is true when it does.

## T07

**Code**

```python
from sqlglot_composer import FROM, SELECT, WHERE, between, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(
        between(job_runs.dt, "2026-09-23", "2026-09-24"),
        equals(job_runs.status, "FAILED"),
    ),
)
```

**Notes**

This gives the run_id, job_id and duration_mins of each FAILED run in ops.job_runs on 2026-09-23 and 2026-09-24. The `between` on dt bounds the read to those two partitions, as a partitioned table requires. No opt-out is used.

## T08

**Code**

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, statement, sum_of
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
    # Opt-out: the user asked for every day ops.job_runs holds, so the read
    # takes all partitions of dt instead of a bounded range.
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

**Notes**

This gives job_id and minutes, the total of duration_mins for each job across every day in ops.job_runs. The opt-out `reads_all_partitions=True` is on FROM because you asked for all days the table holds; without it, the read needs a dt bound. The sum is grouped by job_id, which is the only column not added up.

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

This gives each run that ops.job_runs holds on 2026-09-24, beside the name of its job from ops.jobs. A JOIN keeps only runs with a matching job. ops.job_runs is partitioned by dt, so its bound sits in WHERE with a value. ops.jobs is not partitioned, so it needs no bound. ON= matches on jobs' whole Key, job_id. No opt-out is used.

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

**Notes**

This gives every job in ops.jobs, with how many of its runs in ops.job_runs fell on 2026-09-24. A LEFT_JOIN keeps every job, and count_distinct gives 0 for a job with no run that day. ops.job_runs is partitioned by dt, so its bound sits in ON= with a value, which keeps the jobs with no run that day in the result. ops.jobs is not partitioned, so it needs no bound. job_name is in GROUP_BY beside job_id, so Hive accepts it in the select list. No opt-out is used.

## T13

**Code**

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

**Notes**

The Derived table numbers each job's runs from the longest down, with the smaller run_id ahead on a tie, so row 1 of each job is its longest run. The outer Statement keeps only row 1, which gives one row per job. The window value is tested in the Statement that reads the Derived table, not in its own WHERE, and the 2026-09-23 to 2026-09-24 bound sits in the WHERE of the Statement that reads ops.job_runs.

## T14

**Code**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows, rollup,
                              statement)
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.dt, AS(count_rows(), "runs")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(rollup(job_runs.dt)),
)
```

**Notes**

The Statement counts the runs of each day from 2026-09-23 to 2026-09-24, and rollup adds one total row that counts both days together. On that total row dt is empty (NULL), so it is the row with no day in its dt column. The bound on dt in WHERE covers the table's partition, as the rule requires.

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

The WHERE bounds the read of ops.job_runs to its 2026-09-24 Partition, and INSERT_OVERWRITE replaces that day's rows in mart.job_day_runs. GROUP_BY over job_id and dt gives one row per Key, so the write is not refused. Send it with `run_execute(s, execute)` after `from warehouse import query, execute`.

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

The logic cell imports only what it uses and calls no run_query or run_execute. Its read of ops.job_runs is bounded to DAY's Partition, and write() replaces that day's rows, with the dt column last in SELECT to match the table's columns, job_id, runs and dt. GROUP_BY over job_id and dt proves the Key.

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

Kept as Hive: none. Every part is Toolbox code.

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

Kept as Hive: none. The CTE becomes `ev = derived("ev", ...)`, and its read of ops.job_events stays bounded by `between(e.dt, ...)` in its WHERE.

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

When the Verdict holds, your Statement and your team's Hive return the same rows on 2026-09-24. When it doesn't, the check has counted rows in one and not in the other on that day, and the printed Verdict says what it found. The check reads both through your `query` on that one Partition, so `ops.job_runs` is bounded by the day and nothing else is read.

## T23

```python
from sqlglot_composer import FROM, SELECT, compare_hive, statement
from references.ops__jobs import jobs

HIVE = "select r.job_id, r.job_name from ops.jobs r -- every job"

s0 = statement(SELECT(jobs.job_id, jobs.job_name), FROM(jobs))
v = compare_hive(s0, HIVE)
print(v)
```

Nothing is run here: `compare_hive` compares the text of your Statement's Hive with the string you gave, and sends nothing to the warehouse. When the Verdict holds, the two are the same query by text, since spacing, case, comments and short table names don't count. When it doesn't, the texts differ, even if they would return the same rows. Your team's Hive reads from `ops.jobs` with the alias `r` and prefixes its columns with `r.`, while the Statement has no alias, so look at what the printed Verdict says about that difference before deciding the two match. `ops.jobs` has no Partitions, so no bound is needed.

## T25

```python
from sqlglot_composer import FROM, SELECT, WHERE, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id),
    FROM(job_runs),
    WHERE(equals(job_runs.status, "FAILED"), equals(job_runs.dt, "2026-09-24")),
)
```

The `==` on job_runs.status became `equals(job_runs.status, "FAILED")`, and WHERE also gets `equals(job_runs.dt, "2026-09-24")`, because ops.job_runs is partitioned by dt and a read of it needs a bound on a partition column; the same bound limits the read to 2026-09-24.

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

`LIMIT(3)` after the ORDER_BY gives the top 3 longest runs on 2026-09-24, longest first, so the sort and the cut both happen in the warehouse; the dt bound and the descending sort are unchanged.

## T28

```python
from sqlglot_composer import AS, FROM, SELECT, equals, first_match, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id,
           AS(first_match([(equals(jobs.team, "data"), "Data platform"),
                           (equals(jobs.team, "finance"), "Finance")],
                          otherwise="Other"), "team_label")),
    FROM(jobs),
)
```

This is a three-value label, so it uses first_match, the first condition that holds winning, rather than nested if_else calls. I took the team values as the lowercase "data" and "finance", as the request writes them; if the column holds other spellings, change the two strings in equals.

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

hive_function("upper", ...) is the Toolbox's way to call a Hive function it has no name for, so no hand-written Hive is used here.

## T31

Workflow convert, step 1: convert the two ops scripts into your Dev Database as the batch daily_ops.

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

Decisions left to you: the ones project.check() names for the two dev tables after the convert (such as location, Key or a column type), each to answer in the decisions cell.

Later steps, in words:
2. Answer each table's open Decisions in the decisions cell.
3. Write the answers into each table's Table reference with project.write_decisions(DECISIONS); project.do_next() runs it.
4. Create each table in dev with run_execute(project.load(table).create(), execute), over project.batch_tables(NAME).
5. Seed each table that reads itself, once, from its original.
6. Write each table in dev with project.run_tables.
7. Compare each table with its original with project.compare_batch(NAME, query=query).

## T32

Workflow convert, step 1: convert the Hive into your Dev Database as the batch fails, with the staging table ops_reports.failed_runs folded into the table that reads it.

```python
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

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

The folded staging table is never made: its query goes inside the table that reads it, so only the one dev table is a Saved table here.

Decisions left to you: the ones project.check() names for that one dev table after the convert (such as location, Key or a column type), each to answer in the decisions cell.

Later steps, in words:
2. Answer each table's open Decisions in the decisions cell.
3. Write the answers into each table's Table reference with project.write_decisions(DECISIONS); project.do_next() runs it.
4. Create each table in dev with run_execute(project.load(table).create(), execute), over project.batch_tables(NAME).
5. Seed each table that reads itself, once, from its original (if the batch has none, this step has nothing to seed).
6. Write each table in dev with project.run_tables.
7. Compare each table with its original with project.compare_batch(NAME, query=query).

## T33

Workflow convert, step 2: answer its Decisions in the decisions cell, and step 3 writes the answers into the Table reference.

```python
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "types": {"dt": "string"},
    },
}

project.write_decisions(DECISIONS)
```

Decisions left to you: none. Both that project.check() asks for, dt's type and the table's location, are answered above.

Later steps, in words, for you to run:
4. Create each table in dev with run_execute(project.load(table).create(), execute), over project.batch_tables(NAME), with NAME = "fails".
5. Seed each table that reads itself, once, from its original.
6. Write each table in dev with project.run_tables.
7. Compare each table with its original with project.compare_batch(NAME, query=query). Promote only once that compare has passed.

## T37

Workflow convert, step 1: convert the query into your Dev Database as the batch runs_per_job, with its tables read from the ops database.

```python
NAME = "runs_per_job"
FILES = []
HIVE = """SELECT r.job_id, COUNT(*) AS runs
FROM job_runs r
WHERE r.dt = '2026-09-24'
GROUP BY r.job_id"""
DATABASE = "ops"
RENAME = {}
STAGING = {}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

Decisions left to you: the ones project.check() names for the dev table the query makes after the convert (such as location, Key or a column type), each to answer in the decisions cell.

Later steps, in words:
2. Answer each table's open Decisions in the decisions cell.
3. Write the answers into each table's Table reference with project.write_decisions(DECISIONS); project.do_next() runs it.
4. Create each table in dev with run_execute(project.load(table).create(), execute), over project.batch_tables(NAME).
5. Seed each table that reads itself, once, from its original.
6. Write each table in dev with project.run_tables.
7. Compare each table with its original with project.compare_batch(NAME, query=query).

## T34

Workflow references, at its first step: writing the Table references for ops.jobs and ops.run_alerts from DESCRIBE.

```python
# names cell
TABLES = ["ops.jobs", "ops.run_alerts"]
DECISIONS = {}

# first step's cell
project.add_references(TABLES, query=query)
```

- Left to you: each table's open Decisions, such as its location, Key or a column type, which the references step leaves for ops.jobs and ops.run_alerts. Answer each in the decisions cell, DECISIONS, by the table's name. None is answered yet, so DECISIONS stays empty.
- Step 2, yours to make: answer each table's open Decisions in the decisions cell.
- Step 3: write each answer into its table's Table reference with project.write_decisions(DECISIONS). It changes only files, so project.do_next() runs it for you.
- Step 4: refresh the Reference sheet and the Database modules with project.refresh_reference_sheet(TABLES). It changes only files, so project.do_next() runs it for you.

## T35

Workflow new_table, at its first step: making the Table folder for mart_dev.job_day_counts with project.new_table, with no query given.

```python
# names cell
TABLES = ["mart_dev.job_day_counts"]
QUERIES = {}
DECISIONS = {}

# first step's cell
project.new_table(TABLES, queries=QUERIES)
```

- Left to you: writing the table's logic in its Table notebook and saving it. It is a decision, yours to make, and the Table reference is never written by hand.
- Step 2: preview the logic with project.load(table).preview() for each table. It writes nothing, and says what stops it, if anything does.
- Step 3: write the Table reference from the logic with project.reference_from_logic(TABLES). It changes only files, so project.do_next() runs it for you.
- Step 4, yours to make: answer the table's open Decisions, such as its location, Key or column types, in the decisions cell, DECISIONS, by the table's name. None is answered yet.
- Step 5: write each answer into the Table reference with project.write_decisions(DECISIONS). It changes only files, so project.do_next() runs it for you.
- Step 6: check each table's rows with run_query(project.load(table).preview(), query). It is a call to the warehouse, yours to run.
- Step 7: create and write each table in dev with run_execute(project.load(table).create(), execute), then project.run_tables(tables=TABLES, execute=execute). It is a call to the warehouse, yours to run.
- Step 8: nothing to compare, since no query was given and QUERIES is empty. Skip it.

