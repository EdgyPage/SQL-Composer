date: 2026-10-27
arm: A0
model: haiku
files: none

## T01

Builds the job names and teams from ops.jobs; run it with `query(s)`.

```python
from references.ops__jobs import jobs
from sqlglot_composer import statement, SELECT, FROM

s = statement(SELECT(jobs.job_name, jobs.team), FROM(jobs))
# df = query(s)
```

## T02

Lists run_id and status for ops.job_runs on 2026-09-24, through the Database module.

```python
from references import ops
from sqlglot_composer import statement, SELECT, FROM, WHERE, equals

s = statement(
    SELECT(ops.job_runs.run_id, ops.job_runs.status),
    FROM(ops.job_runs),
    WHERE(equals(ops.job_runs.dt, "2026-09-24")),
)
```

## T04

The Table reference for mart.job_day_runs, with its columns, partition, Key and location.

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

Counts the run_id values that appear more than once on 2026-09-24. The Key holds when the result is empty.

```python
from references.ops__job_runs import job_runs
from warehouse import query
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, HAVING, COUNT, alias, equals, greater_than

dupes = statement(
    SELECT(job_runs.run_id, alias(COUNT(job_runs.run_id), "n")),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
    GROUP_BY(job_runs.run_id),
    HAVING(greater_than(COUNT(job_runs.run_id), 1)),
)
v = query(dupes).empty  # True means the Key holds
```

## T07

Failed runs from 2026-09-23 to 2026-09-24, with run_id, job_id and duration_mins.

```python
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, WHERE, AND, equals, between

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(AND(
        equals(job_runs.status, "FAILED"),
        between(job_runs.dt, "2026-09-23", "2026-09-24"),
    )),
)
```

## T08

Total minutes per job over every day in ops.job_runs.

```python
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, GROUP_BY, SUM, alias

s = statement(
    SELECT(job_runs.job_id, alias(SUM(job_runs.duration_mins), "minutes")),
    FROM(job_runs),
    GROUP_BY(job_runs.job_id),
)
```

## T10

Each run on 2026-09-24 joined to its job's name from ops.jobs.

```python
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from sqlglot_composer import statement, SELECT, FROM, JOIN, WHERE, equals

s = statement(
    SELECT(job_runs.run_id, jobs.job_name, job_runs.status),
    FROM(job_runs),
    JOIN(jobs, equals(job_runs.job_id, jobs.job_id)),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
```

## T11

Every job, with its run count on 2026-09-24. The day filter sits in the join condition so jobs with no runs keep a row, and COUNT of run_id gives 0 for them.

```python
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, LEFT_JOIN, GROUP_BY, COUNT, AND, equals, alias

s = statement(
    SELECT(jobs.job_id, jobs.job_name, alias(COUNT(job_runs.run_id), "runs")),
    FROM(jobs),
    LEFT_JOIN(job_runs, AND(
        equals(job_runs.job_id, jobs.job_id),
        equals(job_runs.dt, "2026-09-24"),
    )),
    GROUP_BY(jobs.job_id, jobs.job_name),
)
```

## T13

Each job's longest run from 2026-09-23 to 2026-09-24. ORDER_BY with no LIMIT is refused, so the Statement only selects the rows and the pandas step picks one per job, with the smallest run_id on a tie.

```python
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, WHERE, between

s = statement(
    SELECT(job_runs.job_id, job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
)
# Then, in pandas:
# df = query(s)
# df = df.sort_values(["job_id", "duration_mins", "run_id"], ascending=[True, False, True])
# longest = df.drop_duplicates("job_id")
```

## T14

Runs per day from 2026-09-23 to 2026-09-24. The total row is added in pandas after the query.

```python
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, COUNT, alias, between

s = statement(
    SELECT(job_runs.dt, alias(COUNT(job_runs.run_id), "runs")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(job_runs.dt),
)
# df = query(s)
# df.loc[len(df)] = ["total", df["runs"].sum()]
```

## T16

Replaces the 2026-09-24 partition of mart.job_day_runs with each job's run count for that day.

```python
from references import ops
from references.mart__job_day_runs import job_day_runs
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, COUNT, INSERT_OVERWRITE, PARTITION, alias, equals

s = statement(
    INSERT_OVERWRITE(job_day_runs, PARTITION(job_day_runs.dt, "2026-09-24")),
    SELECT(ops.job_runs.job_id, alias(COUNT(ops.job_runs.run_id), "runs"), alias("2026-09-24", "dt")),
    FROM(ops.job_runs),
    WHERE(equals(ops.job_runs.dt, "2026-09-24")),
    GROUP_BY(ops.job_runs.job_id),
)
```

## T17

The logic cell for the mart.job_day_runs notebook. create() makes the table, rows(day) holds the clauses that count each job's runs on that day, preview() reads them for DAY, and write() replaces DAY's rows.

```python
from references import ops
from references.mart__job_day_runs import job_day_runs
from warehouse import query, execute
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, COUNT, INSERT_OVERWRITE, PARTITION, alias, equals, create_table

DAY = "2026-09-24"

def create():
    execute(create_table(job_day_runs))

def rows(day):
    return (
        SELECT(ops.job_runs.job_id, alias(COUNT(ops.job_runs.run_id), "runs"), alias(day, "dt")),
        FROM(ops.job_runs),
        WHERE(equals(ops.job_runs.dt, day)),
        GROUP_BY(ops.job_runs.job_id),
    )

def preview():
    return query(statement(*rows(DAY)))

def write():
    execute(statement(
        INSERT_OVERWRITE(job_day_runs, PARTITION(job_day_runs.dt, DAY)),
        *rows(DAY),
    ))
```

## T19

The Hive converted to a Statement. COUNT(*) is written as a count of run_id, which is never null because it is the Key.

```python
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, COUNT, IN, AND, equals, alias

s = statement(
    SELECT(job_runs.job_id, alias(COUNT(job_runs.run_id), "runs")),
    FROM(job_runs),
    WHERE(AND(
        equals(job_runs.dt, "2026-09-24"),
        IN(job_runs.status, ["FAILED", "SUCCESS", "RETRY", "TEST"]),
    )),
    GROUP_BY(job_runs.job_id),
)
```

## T20

The CTE becomes a Statement `ev` used as the FROM of the outer Statement. The message's import line names ops.job_runs for this table, but the events table is ops.job_events, so the code imports job_events from its own reference.

```python
from references.ops__job_events import job_events
from sqlglot_composer import statement, SELECT, FROM, WHERE, GROUP_BY, SUM, CASE, WHEN, ELSE, alias, equals, between

ev = statement(
    SELECT(job_events.job_id, job_events.event_type),
    FROM(job_events),
    WHERE(between(job_events.dt, "2026-09-20", "2026-09-24")),
)

s = statement(
    SELECT(ev.job_id, alias(SUM(CASE(WHEN(equals(ev.event_type, "finish"), 1), ELSE(0))), "finishes")),
    FROM(ev),
    GROUP_BY(ev.job_id),
)
```

## T22

Runs the Hive and the Statement with my query, sorts both, and compares them on 2026-09-24. If query takes only a Statement, the Hive string has to go through the warehouse's own call instead.

```python
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, WHERE, equals
from warehouse import query

s0 = statement(
    SELECT(job_runs.run_id, job_runs.status),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
hive = "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-24'"

a = query(s0).sort_values(["run_id", "status"]).reset_index(drop=True)
b = query(hive).sort_values(["run_id", "status"]).reset_index(drop=True)
v = a.equals(b)
```

## T23

Compares the Statement's Hive with the team's Hive without running anything. The two differ only by the `r.` alias and the trailing comment, so both are normalised before the comparison.

```python
import re
from references.ops__jobs import jobs
from sqlglot_composer import statement, SELECT, FROM

s0 = statement(SELECT(jobs.job_id, jobs.job_name), FROM(jobs))

hive = "select r.job_id, r.job_name from ops.jobs r -- every job"

def bare(text):
    text = re.sub(r"--.*", "", text)
    text = re.sub(r"\br\.", "", text)
    return " ".join(text.lower().split())

v = bare(hive) == bare(s0.to_hive())
```

## T25

Replaces `==` with equals(), and keeps the 2026-09-24 day filter that the request names.

```python
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, WHERE, AND, equals

s = statement(
    SELECT(job_runs.run_id),
    FROM(job_runs),
    WHERE(AND(
        equals(job_runs.status, "FAILED"),
        equals(job_runs.dt, "2026-09-24"),
    )),
)
```

## T26

Adds LIMIT(3) after ORDER_BY, which is the fix the error names for a top N.

```python
from references.ops__job_runs import job_runs
from sqlglot_composer import statement, SELECT, FROM, WHERE, ORDER_BY, LIMIT, descending, equals

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
    ORDER_BY(descending(job_runs.duration_mins)),
    LIMIT(3),
)
```

## T28

Each job with its team label, using a CASE on the team value.

```python
from references.ops__jobs import jobs
from sqlglot_composer import statement, SELECT, FROM, CASE, WHEN, ELSE, alias, equals

s = statement(
    SELECT(
        jobs.job_id,
        alias(
            CASE(
                WHEN(equals(jobs.team, "data"), "Data platform"),
                WHEN(equals(jobs.team, "finance"), "Finance"),
                ELSE("Other"),
            ),
            "team_label",
        ),
    ),
    FROM(jobs),
)
```

## T29

Each job with its name in capitals, using Hive's upper function as UPPER.

```python
from references.ops__jobs import jobs
from sqlglot_composer import statement, SELECT, FROM, UPPER, alias

s = statement(
    SELECT(jobs.job_id, alias(UPPER(jobs.job_name), "name_upper")),
    FROM(jobs),
)
```
