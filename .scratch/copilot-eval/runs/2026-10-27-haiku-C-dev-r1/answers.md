date: 2026-10-27
arm: C
model: haiku
files: 353cbeeb

## T01

Read each job's name and team from the one-table reference `jobs`. The table has no partitions, so it needs no bound. The Statement is run with `run_query(s, query)`, which gives a DataFrame.

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

The two columns come from the Table reference, so `jobs.job_name` and `jobs.team` are read as `table.column`. The last line runs the read with your `query` function and returns the rows.

## T02

Using the Database module, `ops.job_runs` is partitioned by `dt`, so the read is bounded on `dt` in WHERE. The Statement lists `run_id` and `status` for 2026-09-24 and is assigned to `s`. Add `run_query(s, query)` after it if you want the rows.

```python
from sqlglot_composer import FROM, SELECT, WHERE, equals, statement
from references import ops

s = statement(
    SELECT(ops.job_runs.run_id, ops.job_runs.status),
    FROM(ops.job_runs),
    WHERE(equals(ops.job_runs.dt, "2026-09-24")),
)
```

## T04

This Table reference names the table, gives each column its Hive type, marks `dt` as the partition column in both `columns` and `partitioned_by`, sets the Key to `job_id` and `dt`, and sets the `location` a Saved table needs. The variable is `t`, as you asked.

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

Save it as `references/mart__job_day_runs.py` so the file name matches the table name. Other code can then import it with `from references.mart__job_day_runs import t`.

## T05

This runs the Key check on `ops.job_runs` for the one partition 2026-09-24, using your `query`. The table is partitioned by `dt`, so the check is bounded on `dt` with `where=`. The result is a Verdict in `v`, and `print(v)` says whether the Key `run_id` holds.

```python
from sqlglot_composer import check_key, equals
from references.ops__job_runs import job_runs
from warehouse import query

v = check_key(job_runs, query=query, where=equals(job_runs.dt, "2026-09-24"))
print(v)
```

## T07

The failed runs are the rows where status is "FAILED" and dt falls between the two days. The bound on dt sits in WHERE, as the partitioned table needs, and the three columns are plain, so they need no AS.

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

Run it with `run_query(s, query)` after `from warehouse import query, execute`.

## T08

The total minutes per job need every day the table holds, so the read opts out of the partition bound with `reads_all_partitions=True`, with a comment saying why. The total is `sum_of` with an AS name, and job_id goes in GROUP_BY because it is not added up.

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, statement, sum_of
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
    # The user asked for every day ops.job_runs holds, so the read is not bounded on dt.
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

Run it with `run_query(s, query)` after `from warehouse import query, execute`.

## T10

Each run on 2026-09-24 with its job's name. The FROM table is partitioned by dt, so it gets its bound in WHERE. The jobs table is not partitioned, so it needs no bound.

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

This is an inner join, so a run whose job is missing from ops.jobs is left out. The statement is assigned to `s`. Run it with `run_query(s, query)` after `from warehouse import query, execute`.

## T11

Every job with its run count on 2026-09-24, with 0 for jobs that had no runs. The LEFT_JOIN keeps every job. Its partition bound on job_runs.dt goes inside ON=, not WHERE, so it does not throw away the jobs with no match. The count uses count_distinct on job_runs.run_id, which gives 0 for a job with no match where count_rows() would give 1. GROUP_BY names job_name as well as job_id, since job_name is selected too.

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

The statement is assigned to `s`. Run it with `run_query(s, query)` after `from warehouse import query, execute`.

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

The row_number in the Derived table numbers each job's runs from the longest down, with the smallest run_id first on a tie. The Statement then keeps the row numbered 1 for each job. The Derived table is bounded on dt, since ops.job_runs is partitioned by dt. To read it, run `run_query(s, query)` after `from warehouse import query, execute`.

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

The rollup in GROUP_BY adds one total row for both days together, where dt is empty. The WHERE bounds the read on dt, the partition column. To read it, run `run_query(s, query)` after `from warehouse import query, execute`.

## T16

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE,
                              count_rows, equals, statement)
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

DAY = "2026-09-24"

s = statement(
    INSERT_OVERWRITE(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, DAY)),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
```

The WHERE bounds ops.job_runs on its partition column dt, and GROUP_BY over job_id and dt gives one row per Key of mart.job_day_runs. INSERT_OVERWRITE replaces only the partition the rows hold, which is 2026-09-24, so that day's old rows are replaced. Partitions filled from the rows need the Session setting first, so after `from warehouse import query, execute`, send it with `run_execute(hive_settings("dynamic_partitions"), execute)` and then write with `run_execute(s, execute)`.

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

The other cells of the notebook run it: `run_execute(create(), execute)` once, `run_query(preview(), query)` to look at the rows, then `run_execute(write(), execute)` after the dynamic_partitions Session setting. `show_hive(create(), write())` shows both without sending anything.

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

Nothing is kept as Hive. The partition bound on `r.dt` is in WHERE, and the status list is a constant list with `is_in`.

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

Nothing is kept as Hive. The CTE `ev` keeps its name through `derived`, and the partition bound on `e.dt` is in the CTE's WHERE with `between`. The outer query reads only `ev`, so it needs no partition bound.

## T22

This runs your query on the 2026-09-24 Partition of `ops.job_runs` and compares the rows from your Statement with the rows from the team's Hive. The Verdict holds when both return the same rows on that day, and it doesn't hold when a row appears in one and not the other.

```python
from sqlglot_composer import FROM, SELECT, WHERE, compare_with_original, equals, statement
from references.ops__job_runs import job_runs
from warehouse import query

HIVE = "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-24'"

s0 = statement(SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
               WHERE(equals(job_runs.dt, "2026-09-24")))

v = compare_with_original(s0, HIVE, query=query, partition={"dt": "2026-09-24"})
print(v)
```

The Hive's columns are run_id and status, in that order, the same as the Statement's, so the rows can be compared. Because `job_runs` is partitioned by dt, the check is bounded to one Partition with `partition=`.

## T23

This compares the text of your Statement with the team's Hive, and it sends nothing to the warehouse. The Verdict holds when the two are the same query once spacing, case, comments and short table names are set aside. The alias `r` and the trailing comment don't count, so the check holds. It doesn't hold when the conditions, columns or tables differ.

```python
from sqlglot_composer import FROM, SELECT, compare_hive, statement
from references.ops__jobs import jobs

HIVE = "select r.job_id, r.job_name from ops.jobs r -- every job"

s0 = statement(SELECT(jobs.job_id, jobs.job_name), FROM(jobs))

v = compare_hive(s0, HIVE)
print(v)
```

Because this check only reads the text, it doesn't need `query` or `execute`.

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

The Python `==` on status became `equals(job_runs.status, "FAILED")`, and I added the partition bound `equals(job_runs.dt, "2026-09-24")` because ops.job_runs is partitioned by dt and FROM needs a bound on it to read that day.

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

I added `LIMIT(3)` after ORDER_BY, since ORDER_BY needs a LIMIT and a top 3 is what LIMIT(n) is for, and kept your dt bound and descending sort. `descending` is your name and is not among the names in this file, so check that it exists in the Toolbox before running.

## T28

Each job gets its team label from a lookup. `team` can be NULL, and a NULL key isn't allowed in `mapped`, so the column is filled first. Any team not in the dict, including the filled value, gets "Other".

```python
from sqlglot_composer import AS, FROM, SELECT, fill_null, mapped, statement
from references.ops__jobs import jobs

TEAM_NAMES = {"data": "Data platform", "finance": "Finance"}

s = statement(
    SELECT(jobs.job_id,
           AS(mapped(fill_null(jobs.team, "Other"), TEAM_NAMES, otherwise="Other"), "team_label")),
    FROM(jobs),
)
```

The statement selects job_id and the team_label, and it stays a plain read with no partition bound because ops.jobs has no partitions.

## T29

Each job's name is passed through Hive's `upper` with `hive_function`, which the Toolbox doesn't wrap by name, and the result is named with AS.

```python
from sqlglot_composer import AS, FROM, SELECT, hive_function, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id,
           AS(hive_function("upper", jobs.job_name), "name_upper")),
    FROM(jobs),
)
```

Nothing here is hand-written Hive, and the statement is a read, so it would go to `run_query` when you run it.

