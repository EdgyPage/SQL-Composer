date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

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

This reads job_name and team from ops.jobs and runs the read with your `query`. The jobs table has no partition columns, so it needs no bound.

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

This builds the Statement for run_id and status from ops.job_runs on 2026-09-24. The `dt` partition column is bounded in WHERE with `equals`. To run it, call `run_query(s, query)` after importing `query` from warehouse.

## T04

This is a new Saved table, so the Table reference gives it a `location=`, a Key of `job_id` and `dt`, and `partitioned_by=["dt"]` with `dt` listed in `columns` as well. Save it as `references/mart__job_day_runs.py`, which is the file name that matches `mart.job_day_runs`. The variable is `t`, as you asked; the file's own convention would name it `job_day_runs`.

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

## T05

This reads ops.job_runs with your `query`, so the check takes `query=query`. ops.job_runs is partitioned by `dt`, so the check is bounded with `where=equals(job_runs.dt, "2026-09-24")` to read only that day. The Key is `run_id`, which the check counts on that day's partition.

```python
from references.ops__job_runs import job_runs
from sqlglot_composer import check_key, equals
from warehouse import query

v = check_key(job_runs, query=query, where=equals(job_runs.dt, "2026-09-24"))
```

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

This reads the three columns you asked for from `ops.job_runs`. The `between` on `dt` bounds the read to the two days, since the table is partitioned by `dt`, and WHERE keeps only the rows where both conditions hold. Run it with `run_query(s, query)` after `from warehouse import query, execute`.

## T08

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, statement, sum_of
from references.ops__job_runs import job_runs

# Every day the table holds, so this read is deliberately not bounded on dt.
s = statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

This adds up `duration_mins` for each `job_id` across all partitions. The `reads_all_partitions=True` opt-out is there because you asked for every day, and it reads the whole table, so it can be slow on a large one. Run it with `run_query(s, query)` after `from warehouse import query, execute`.

## T10

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

This joins each run to its job on job_id, which is the Key of ops.jobs, so each run matches at most one job. JOIN keeps only the runs that have a matching job. The job_runs table is partitioned by dt, so its bound is the equals on job_runs.dt in WHERE. ops.jobs is not partitioned and needs no bound. Use run_query(s, query) to read it.

## T11

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

LEFT_JOIN keeps every job, and a job with no run that day gets NULL for run_id, which count_distinct counts as 0. The date bound on job_runs.dt sits inside ON= rather than WHERE, because job_runs is partitioned and the join is a LEFT_JOIN. count_distinct counts runs rather than joined rows. job_name is in GROUP_BY because it is selected next to the aggregate. Run it with run_query(s, query).

## T13

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, between, derived, descending, equals,
                              row_number, statement)
from references.ops__job_runs import job_runs

ranked = derived("ranked", statement(
    SELECT(job_runs.job_id, job_runs.run_id, job_runs.duration_mins,
           AS(row_number(PARTITION_BY=job_runs.job_id,
                         ORDER_BY=[descending(job_runs.duration_mins), job_runs.run_id]),
              "longest")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
))
s = statement(
    SELECT(ranked.job_id, ranked.run_id, ranked.duration_mins),
    FROM(ranked),
    WHERE(equals(ranked.longest, 1)),
)
```

The row_number numbers each job's runs from the longest down, with the smallest run_id second so a tie has one order. The Derived table reads only the two days, and the outer Statement keeps the row numbered 1, so each job gives one row. The window's value is tested in the outer Statement, not in the one that computes it.

## T14

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

The rollup adds one row per day and a total row for both days. On the total row, dt is empty (NULL), so that row is the one with no day. The WHERE bounds the read of the partitioned table on dt.

## T16

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, count_rows,
                              equals, statement)
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

This builds one Statement, `s`, that replaces the 2026-09-24 Partition of mart.job_day_runs. The WHERE bounds the read of ops.job_runs to that day, and GROUP_BY over job_id and dt gives one row per Key. Because the rows fill their Partition from the dt column, send it with `run_execute(hive_settings("dynamic_partitions"), execute)` first, then `run_execute(s, execute)`, after `from warehouse import query, execute`.

## T17

```python
# logic
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause,
                              Statement, count_rows, create_table, equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

DAY = "2026-09-24"


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

Paste this into the logic cell of the mart.job_day_runs Table notebook. The next cell can run `show_hive([create(), write()])` to see the Hive, and `run_query(preview(), query)` to read the rows before writing. The write replaces DAY's Partition, and project.run_tables sends it with its Session settings first.

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

Nothing is kept as Hive. The `dt` partition is bounded in WHERE by `equals(r.dt, "2026-09-24")`, as the Hive bounded it.

## T20

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, between, derived, equals,
                              if_else, statement, sum_of)
from references.ops__job_events import job_events

e = AS(job_events, "e")
events_in_range = statement(
    SELECT(e.job_id, e.event_type),
    FROM(e),
    WHERE(between(e.dt, "2026-09-20", "2026-09-24")),
)

ev = derived("ev", events_in_range)
s = statement(
    SELECT(ev.job_id, AS(sum_of(if_else(equals(ev.event_type, "finish"), 1, 0)), "finishes")),
    FROM(ev),
    GROUP_BY(ev.job_id),
)
```

Nothing is kept as Hive. The CTE `ev` is a Derived table named with `derived`, and the `dt` partition is bounded inside it in WHERE by `between(e.dt, "2026-09-20", "2026-09-24")`, as the Hive bounded it.

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

This reads your Statement and your team's Hive through your `query`, on the one partition dt = 2026-09-24, and counts the rows that are in one result and not the other. The columns are run_id and status in the same order on both sides, so the comparison can run. The Verdict holds (`if v:` is true) when no rows differ in either direction. It does not hold when any row appears in one result and not the other, and `print(v)` says what it found.

## T23

```python
from sqlglot_composer import FROM, SELECT, compare_hive, statement
from references.ops__jobs import jobs

HIVE = "select r.job_id, r.job_name from ops.jobs r -- every job"

s0 = statement(SELECT(jobs.job_id, jobs.job_name), FROM(jobs))
v = compare_hive(s0, HIVE)
print(v)
```

This compares the text only. It runs nothing and sends nothing, so `query` and `execute` are not needed. The Verdict holds when the two texts agree once spacing, case, comments and short table names are set aside. A different condition would make it not hold. Your Hive has no WHERE, and ops.jobs has no partition column, so no partition bound is needed. The comment "-- every job" is ignored. The alias `r` on ops.jobs is the kind of difference the check is meant to skip, but I can't be sure from the description alone whether it counts as a short table name, so read what `print(v)` says.

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

The `==` on `job_runs.status` is now `equals(job_runs.status, "FAILED")`, and the day is kept as a partition bound, `equals(job_runs.dt, "2026-09-24")`, in the same WHERE, because a read of the partitioned table needs one.

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

`LIMIT(3)` is added after ORDER_BY, which gives the top 3 longest runs, longest first, and it is the fix the refusal names for a top N; the descending sort and the 2026-09-24 bound are kept. `descending` is not among the names this file lists, so if the import fails, check it against your Toolbox before going on.

## T28

```python
from sqlglot_composer import AS, FROM, SELECT, mapped, statement
from references.ops__jobs import jobs

TEAM_LABEL = {"data": "Data platform", "finance": "Finance"}

s = statement(
    SELECT(jobs.job_id,
           AS(mapped(jobs.team, TEAM_LABEL, otherwise="Other"), "team_label")),
    FROM(jobs),
)
```

This builds one row per job with its team label. The lookup is a single-column mapped, so any team not in the dict, such as one not named data or finance, gets "Other". The dict is a constant at the top. ops.jobs has no partitions named here, so it needs no partition bound.

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

This uses Hive's upper through hive_function, since the Toolbox doesn't wrap it, and names the result name_upper with AS. Nothing here is hand-written Hive.

