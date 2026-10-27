date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

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
