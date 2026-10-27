date: 2026-10-27
arm: C
model: haiku
files: 353cbeeb

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
