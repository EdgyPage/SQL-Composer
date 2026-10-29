date: 2026-10-29
arm: C
model: sonnet
files: fac0fd8

## X39

**Map**
- Sources: job_runs, jobs.
- Steps: none (the query ok_runs is read by nothing, so it gives the final's rows).
- Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise).
- Parameters and Keys are empty, so they are none. No value is typed over a formula (every formula cell is a formula), so there is no Keys row to mention.
- Query ok_runs: job_runs where status is SUCCESS, columns run_id, job_id, duration_mins. A blank status simply fails the test, so nothing is wrapped.
- job_name is an XLOOKUP, so a LEFT JOIN to jobs. share is duration_mins divided by a SUMIFS over its own Table by job_id, so a window `SUM(...) OVER (PARTITION BY job_id)`, with COALESCE(.., 0) as Excel gives 0 where nothing matches.
- Refused: noise `=RAND()`, so `NULL AS noise`.
- Left alone: nothing else.
- Fill in: `<database>`.

```sql
WITH ok_runs_q AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT q.run_id, q.job_id, q.duration_mins, j.job_name,
  q.duration_mins / COALESCE(SUM(q.duration_mins) OVER (PARTITION BY q.job_id), 0) AS share,
  NULL AS noise
FROM ok_runs_q q
LEFT JOIN <database>.jobs j ON q.job_id = j.job_id
```

Toolbox code, with `<database>` as ops. The refused `noise` column has no Toolbox name in files 03 to 05, so it is left out of the Python; the Hive above keeps it as NULL.

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, WHERE, derived, equals,
                              fill_null, statement, sum_of, window)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

ok_runs_q = derived("ok_runs_q", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
))
by_job = window(PARTITION_BY=ok_runs_q.job_id)
s = statement(
    SELECT(ok_runs_q.run_id, ok_runs_q.job_id, ok_runs_q.duration_mins, jobs.job_name,
           AS(ok_runs_q.duration_mins / fill_null(sum_of(ok_runs_q.duration_mins, over=by_job), 0),
              "share")),
    FROM(ok_runs_q),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, ok_runs_q.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X40

**Map**
- Sources: Runs (typed Run, Job, Mins), jobs, run_alerts. Parameters holds rate = 2, used by value.
- Steps: Runs (it has formulas and two other Tables read it), so a CTE `runs_step` over the Runs source.
- Finals: Teams (Team, `<total_cost>`) and run_alerts (alert_id, run_id, severity, dt, `<run_mins>`).
- Teams is a summary: its only typed column, Team, is what its SUMIFS matches on, so it is a GROUP BY of Runs. Its Total Row is not in this workbook.
- Runs: Team is an XLOOKUP, so a LEFT JOIN to jobs. Cost is Mins * XLOOKUP("rate", Parameters...), which is its value, 2. Move the rate into Parameters if you want it to stay a parameter.
- Teams.Total Cost is a SUMIFS over another Table with COALESCE(.., 0). run_alerts.Run Mins is an XLOOKUP into Runs, so a LEFT JOIN to the step.
- Names: the headers `Total Cost` and `Run Mins` are not plain names, so they are `<total_cost>` and `<run_mins>`. Fill in each.
- Typed over: none. Blank: none in the columns the formulas read. There is no Keys row, which matters only if a value was typed over a formula (none was).
- Refused: none.
- Left alone: the PivotTable on sheet "Pivot" (rows Team, sum of Cost).
- Fill in: `<database>`, `<total_cost>`, `<run_mins>`.

```sql
WITH runs_step AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT Team, COALESCE(SUM(Cost), 0) AS <total_cost>
FROM runs_step
GROUP BY Team
```

```sql
WITH runs_step AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt, rs.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN runs_step rs ON a.run_id = rs.Run
```

Toolbox code, with `<database>` as ops (match the Table reference names to the ones your Project made, file 02):

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals,
                              fill_null, statement, sum_of)
from references.ops__runs import Runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

runs_step = derived("runs_step", statement(
    SELECT(Runs.Run, Runs.Job, Runs.Mins, AS(jobs.team, "Team"), AS(Runs.Mins * 2, "Cost")),
    FROM(Runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, Runs.Job), reads_all_partitions=True),
))

teams = statement(
    SELECT(runs_step.Team, AS(fill_null(sum_of(runs_step.Cost), 0), "total_cost")),  # fill in the name
    FROM(runs_step),
    GROUP_BY(runs_step.Team),
)

run_alerts_s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(runs_step.Mins, "run_mins")),  # fill in the name
    FROM(run_alerts, reads_all_partitions=True),
    LEFT_JOIN(runs_step, ON=equals(runs_step.Run, run_alerts.run_id)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X46

**Map**
- Sources: jobs (typed job_id, job_name, team), job_runs.
- Steps: none. Finals: jobs (job_id, job_name, team, shortest, runs, busiest).
- jobs is not a summary: job_name and team are typed and matched by nothing.
- shortest is a MINIFS over another Table, so a LEFT JOIN of a grouped MIN with COALESCE(.., 0). Job 4 has no runs, so it gets 0, as Excel gives. runs is a COUNTIF, so COUNT(*) with COALESCE. busiest is RANK.EQ of runs, so `RANK() OVER (ORDER BY runs DESC)`, written in a second step because it ranks a calculated column.
- Typed over: none. Blank: none in the columns read. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
WITH base AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(a.shortest, 0) AS shortest,
    COALESCE(a.runs, 0) AS runs
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, MIN(duration_mins) AS shortest, COUNT(*) AS runs
    FROM <database>.job_runs
    GROUP BY job_id
  ) a ON j.job_id = a.job_id
)
SELECT job_id, job_name, team, shortest, runs,
  RANK() OVER (ORDER BY runs DESC) AS busiest
FROM base
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              descending, equals, fill_null, min_of, rank, statement, window)
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

agg = derived("agg", statement(
    SELECT(job_runs.job_id, AS(min_of(job_runs.duration_mins), "shortest"),
           AS(count_rows(), "runs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
base = derived("base", statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(fill_null(agg.shortest, 0), "shortest"), AS(fill_null(agg.runs, 0), "runs")),
    FROM(jobs, reads_all_partitions=True),
    LEFT_JOIN(agg, ON=equals(agg.job_id, jobs.job_id)),
))
s = statement(
    SELECT(base.job_id, base.job_name, base.team, base.shortest, base.runs,
           AS(rank(over=window(ORDER_BY=descending(base.runs))), "busiest")),
    FROM(base),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X47

**Map**
- Sources: region_budgets. Steps: none. Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg).
- cheapest_first: RANK.EQ with 1 as third argument, so ASC. region_total: SUMIF over its own Table, so a window `SUM(..) OVER (PARTITION BY region)` with COALESCE(.., 0). region_avg: AVERAGEIF, `AVG(..) OVER (PARTITION BY region)`, left NULL.
- Typed over: none. Blank: none. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, SELECT, average_of, fill_null, rank, statement,
                              sum_of, window)
from references.ops__region_budgets import region_budgets

everyone = window(ORDER_BY=region_budgets.budget_cents)
by_region = window(PARTITION_BY=region_budgets.region)
s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(rank(over=everyone), "cheapest_first"),
           AS(fill_null(sum_of(region_budgets.budget_cents, over=by_region), 0), "region_total"),
           AS(average_of(region_budgets.budget_cents, over=by_region), "region_avg")),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's formula reads every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X48

**Map**
- Sources: job_runs, jobs, run_alerts. Steps: none.
- Finals: quiet_runs (run_id, job_id, status) and slow_regions (region, avg_mins, fastest). Both are queries loaded into Tables nothing reads.
- quiet_runs: a LeftAnti NestedJoin of job_runs and run_alerts on run_id, so `LEFT JOIN .. WHERE a.run_id IS NULL`, job_runs' columns only.
- slow_regions: Inner join to jobs, GROUP BY region, then the filter after the group is a HAVING that repeats the aggregate.
- Typed over: none. Blank: none read by a formula (the Tables have no formulas). Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

```sql
SELECT j.region, AVG(r.duration_mins) AS avg_mins, MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (ANTI_JOIN, AS, FROM, GROUP_BY, HAVING, JOIN, SELECT, at_least,
                              average_of, equals, min_of, statement)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

quiet_runs = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    ANTI_JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id),
              reads_all_partitions=True),
)

slow_regions = statement(
    SELECT(jobs.region, AS(average_of(job_runs.duration_mins), "avg_mins"),
           AS(min_of(job_runs.duration_mins), "fastest")),
    FROM(job_runs, reads_all_partitions=True),
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
    GROUP_BY(jobs.region),
    HAVING(at_least(average_of(job_runs.duration_mins), 20)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X49

**Map**
- Sources: job_runs, jobs, run_alerts, scheduler_runs, job_owners. Steps: none.
- Finals: alert_status (alert_id, severity, status), run_check (run_id, status, scheduled_run), teams (team). All three are queries loaded into Tables nothing reads.
- alert_status: a RightOuter join of run_alerts to job_runs, so a LEFT JOIN with the two tables swapped (every run kept, NULL alert where none).
- run_check: a FullOuter join, so FULL OUTER JOIN; the expanded run_id is renamed scheduled_run with AS.
- teams: Table.Distinct over a Table.Combine, so UNION (it drops repeats).
- Typed over: none. Blank: no formulas, so none. Refused: none. Left alone: nothing. No ORDER BY is needed, as no query sorts.
- Fill in: `<database>`.

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
```

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, FULL_JOIN, LEFT_JOIN, SELECT, UNION, equals, statement)
from references.ops__job_runs import job_runs
from references.ops__run_alerts import run_alerts
from references.ops__scheduler_runs import scheduler_runs
from references.ops__jobs import jobs
from references.ops__job_owners import job_owners

alert_status = statement(
    SELECT(run_alerts.alert_id, run_alerts.severity, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id),
              reads_all_partitions=True),
)

run_check = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(scheduler_runs.run_id, "scheduled_run")),
    FROM(job_runs, reads_all_partitions=True),
    FULL_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id),
              reads_all_partitions=True),
)

teams = UNION(
    statement(SELECT(jobs.team), FROM(jobs, reads_all_partitions=True)),
    statement(SELECT(job_owners.team), FROM(job_owners, reads_all_partitions=True)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X50

**Map**
- Sources: job_owners, jobs. Steps: none (the query owners is read by nothing).
- Finals: owners (job_id, owner, job_name, newest_first), the query's rows plus two formulas.
- Query owners: job_id and owner from job_owners, Table.Distinct with no column list, so SELECT DISTINCT.
- job_name: XLOOKUP, so a LEFT JOIN to jobs. newest_first: RANK.EQ of job_id in its own column, so `RANK() OVER (ORDER BY job_id DESC)`.
- Typed over: none. Blank: owner is blank for job 4, but no formula reads owner. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
WITH owners_q AS (
  SELECT DISTINCT job_id, owner
  FROM <database>.job_owners
)
SELECT q.job_id, q.owner, j.job_name,
  RANK() OVER (ORDER BY q.job_id DESC) AS newest_first
FROM owners_q q
LEFT JOIN <database>.jobs j ON q.job_id = j.job_id
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, SELECT_DISTINCT, derived,
                              descending, equals, rank, statement, window)
from references.ops__job_owners import job_owners
from references.ops__jobs import jobs

owners_q = derived("owners_q", statement(
    SELECT_DISTINCT(job_owners.job_id, job_owners.owner),
    FROM(job_owners, reads_all_partitions=True),  # a workbook's query reads every row
))
s = statement(
    SELECT(owners_q.job_id, owners_q.owner, jobs.job_name,
           AS(rank(over=window(ORDER_BY=descending(owners_q.job_id))), "newest_first")),
    FROM(owners_q),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, owners_q.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X59

**Map**
- Sources: jobs (typed job_id, job_name), job_runs, run_alerts (typed alert_id, run_id, severity, dt). Steps: none.
- Finals: jobs (job_id, job_name, long_runs, failed_mins, not_test) and run_alerts (alert_id, run_id, severity, dt, alerts_so_far).
- jobs: three formulas over another Table, each a LEFT JOIN of a grouped subquery with COALESCE(.., 0). long_runs: COUNTIFS with ">=20". failed_mins: SUMIFS with "f*", a wildcard, so `LOWER(status) LIKE 'f%'` as Excel ignores case. not_test: COUNTIFS with "<>TEST", so `(status <> 'TEST' OR status IS NULL)` as Excel counts the blank status there.
- Blank: status is blank for run 98 and is read, but only inside -IFS forms, which skip it, so nothing is wrapped.
- run_alerts.alerts_so_far: COUNTIFS(run_id, "<="&this run_id) over its own Table is a running count with ties included: `COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`.
- Typed over: none. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(l.long_runs, 0) AS long_runs,
  COALESCE(f.failed_mins, 0) AS failed_mins,
  COALESCE(n.not_test, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS long_runs
  FROM <database>.job_runs
  WHERE duration_mins >= 20
  GROUP BY job_id
) l ON j.job_id = l.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS failed_mins
  FROM <database>.job_runs
  WHERE LOWER(status) LIKE 'f%'
  GROUP BY job_id
) f ON j.job_id = f.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS not_test
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) n ON j.job_id = n.job_id
```

```sql
SELECT alert_id, run_id, severity, dt,
  COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts
```

Toolbox code, with `<database>` as ops. Two limits: `starts_with` keeps case, so "F" below matches FAILED but not "failed" (the Hive above ignores case); and the running count is built from a count per run_id, so ties are included as Excel's.

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, JOIN, LEFT_JOIN, SELECT, WHERE, all_of,
                              any_of, at_least, count_rows, derived, equals, fill_null,
                              is_null, not_equals, starts_with, statement, sum_of, window)
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs
from references.ops__run_alerts import run_alerts

long_runs = derived("long_runs", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "long_runs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formula reads every row
    WHERE(at_least(job_runs.duration_mins, 20)),
    GROUP_BY(job_runs.job_id),
))
failed_mins = derived("failed_mins", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "failed_mins")),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(starts_with(job_runs.status, "F")),  # case kept; the Hive ignores case
    GROUP_BY(job_runs.job_id),
))
not_test = derived("not_test", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "not_test")),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
    GROUP_BY(job_runs.job_id),
))
jobs_s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(fill_null(long_runs.long_runs, 0), "long_runs"),
           AS(fill_null(failed_mins.failed_mins, 0), "failed_mins"),
           AS(fill_null(not_test.not_test, 0), "not_test")),
    FROM(jobs, reads_all_partitions=True),
    LEFT_JOIN(long_runs, ON=equals(long_runs.job_id, jobs.job_id)),
    LEFT_JOIN(failed_mins, ON=equals(failed_mins.job_id, jobs.job_id)),
    LEFT_JOIN(not_test, ON=equals(not_test.job_id, jobs.job_id)),
)

# run_alerts: a count per run_id, a running total of it, joined back
per_run = derived("per_run", statement(
    SELECT(run_alerts.run_id, AS(count_rows(), "n")),
    FROM(run_alerts, reads_all_partitions=True),
    GROUP_BY(run_alerts.run_id),
))
running = derived("running", statement(
    SELECT(per_run.run_id,
           AS(sum_of(per_run.n, over=window(ORDER_BY=per_run.run_id, rows=(None, 0))),
              "alerts_so_far")),
    FROM(per_run),
))
run_alerts_s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           running.alerts_so_far),
    FROM(run_alerts, reads_all_partitions=True),
    JOIN(running, ON=equals(running.run_id, run_alerts.run_id)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X60

**Map**
- Sources: region_budgets. Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region), and `region_budgets (Total Row)` (job_id, budget_cents), a query of its own because region_budgets is not a summary (job_id and budget_cents are typed and matched by nothing).
- share: a whole-column SUM, so `SUM(..) OVER ()`. above_avg: against `AVG(..) OVER ()`, a TRUE/FALSE value. rank_in_region: COUNTIFS(region, same, budget, "<"&this)+1 is `RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC)`.
- Total Row: SUBTOTAL(103) is a COUNT, SUBTOTAL(101) an AVG; one row, a column per total, in order. The label "Total" is dropped (no label).
- Typed over: none. Blank: none. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

```sql
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

Toolbox code, with `<database>` as ops. The TRUE/FALSE above_avg is built with if_else; check it against the Hive.

```python
from sqlglot_composer import (AS, FROM, SELECT, average_of, count_rows, if_else, more_than,
                              rank, statement, sum_of, window)
from references.ops__region_budgets import region_budgets

whole = window()
by_region = window(PARTITION_BY=region_budgets.region, ORDER_BY=region_budgets.budget_cents)
s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(region_budgets.budget_cents / sum_of(region_budgets.budget_cents, over=whole), "share"),
           AS(if_else(more_than(region_budgets.budget_cents,
                                average_of(region_budgets.budget_cents, over=whole)),
                      True, False), "above_avg"),
           AS(rank(over=by_region), "rank_in_region")),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's formula reads every row
)

total_row = statement(
    SELECT(AS(count_rows(), "job_id"), AS(average_of(region_budgets.budget_cents), "budget_cents")),
    FROM(region_budgets, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X61

**Map**
- Sources: region_costs. Steps: none.
- Finals: by_region (region, total_cents, entries, priciest).
- by_region is a summary: its only typed column, region, is what its SUMIFS, COUNTIFS and MAXIFS match on, so it is a GROUP BY of region_costs. Each formula keeps COALESCE(.., 0).
- Total Row: SUBTOTAL(109) over SUMs, 109 over a COUNT, 104 (MAX) over a MAX, so it needs no query of its own: the query ends `GROUP BY region WITH ROLLUP`, which adds the total as one more row with region NULL (a Subtotal row).
- Blank: cost_cents is blank for job 2 on 20260924, but it is read only inside -IFS forms, which skip it, so nothing is wrapped (COUNTIFS still counts that row).
- dt is held as text (20260911), but no formula reads it, so it is left as is.
- Typed over: none. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(*), 0) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, count_rows, fill_null, max_of,
                              rollup, statement, sum_of)
from references.ops__region_costs import region_costs

s = statement(
    SELECT(region_costs.region,
           AS(fill_null(sum_of(region_costs.cost_cents), 0), "total_cents"),
           AS(fill_null(count_rows(), 0), "entries"),
           AS(fill_null(max_of(region_costs.cost_cents), 0), "priciest")),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's formula reads every row
    GROUP_BY(rollup(region_costs.region)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X62

**Map**
- Sources: team_notes. Steps: none. Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short).
- week_of: d - WEEKDAY(d, 2) + 1 as week_start writes it. month_end: EOMONTH(d, 0) is LAST_DAY. month_of: EOMONTH(d, -1) + 1 as month_start writes it. months_in: DATEDIF "m" is FLOOR(MONTHS_BETWEEN(b, a)). three_before: d - 3 is DATE_SUB. who: PROPER is INITCAP. short: TEXTJOIN is CONCAT_WS, with LEFT as SUBSTR.
- Typed over: none. Blank: none. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT team, note, written_on,
  CAST(NEXT_DAY(DATE_ADD(written_on, 7 * -1), 'MO') AS STRING) AS week_of,
  LAST_DAY(written_on) AS month_end,
  CAST(TRUNC(written_on, 'MM') AS STRING) AS month_of,
  FLOOR(MONTHS_BETWEEN(written_on, '2026-01-01')) AS months_in,
  DATE_SUB(written_on, 3) AS three_before,
  INITCAP(team) AS who,
  CONCAT_WS(': ', team, SUBSTR(note, 1, 5)) AS short
FROM <database>.team_notes
```

Toolbox code, with `<database>` as ops. Only week_start and month_start are named in the files loaded here. LAST_DAY, FLOOR(MONTHS_BETWEEN), DATE_SUB, INITCAP and CONCAT_WS are Hive functions (file 10, in a new chat), so the Python below keeps the columns it can and the rest comes from running `project.convert` on the Hive above.

```python
from sqlglot_composer import AS, FROM, SELECT, month_start, statement, week_start
from references.ops__team_notes import team_notes

s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on,
           AS(week_start(team_notes.written_on), "week_of"),
           # month_end, months_in, three_before, who and short: from project.convert on the Hive
           AS(month_start(team_notes.written_on), "month_of")),
    FROM(team_notes, reads_all_partitions=True),  # a workbook's formula reads every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X63

**Map**
- Sources: job_runs, scheduler_runs. Steps: none. Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded).
- no_retry: ISBLANK is `avg_retry_secs IS NULL`. quarters: INT is FLOOR. capped: MIN of one row's cells is LEAST. variance: VAR.S of the whole column is `VAR_SAMP(..) OVER ()`. weighted: SUMPRODUCT is `SUM(a * b) OVER ()`. scheduled_job: XLOOKUP with -1 as the fourth argument is a LEFT JOIN to scheduler_runs with COALESCE(.., -1). label: CONCATENATE is CONCAT. succeeded: ISNUMBER(SEARCH(..)) is `INSTR(LOWER(x), LOWER(a)) > 0`.
- Blank: status is blank for run 98 and SEARCH reads it, so it is wrapped, COALESCE(status, ''). avg_retry_secs is blank for run 98 but read only by ISBLANK, which is not wrapped.
- Typed over: none. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  r.avg_retry_secs IS NULL AS no_retry,
  FLOOR(r.duration_mins / 4) AS quarters,
  LEAST(r.duration_mins, 25) AS capped,
  VAR_SAMP(r.duration_mins) OVER () AS variance,
  SUM(r.duration_mins * r.job_id) OVER () AS weighted,
  COALESCE(s.job_id, -1) AS scheduled_job,
  CONCAT('run ', r.run_id) AS label,
  INSTR(LOWER(COALESCE(r.status, '')), LOWER('cess')) > 0 AS succeeded
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

Toolbox code, with `<database>` as ops. quarters (FLOOR), variance (VAR_SAMP), label (CONCAT) and succeeded (LOWER, INSTR) have no name in files 03 to 05 (they are Hive functions, file 10 in a new chat), so they are left to `project.convert` on the Hive.

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, if_else,
                              is_null, less_than, statement, sum_of, window)
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

whole = window()
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs,
           AS(if_else(is_null(job_runs.avg_retry_secs), True, False), "no_retry"),
           # quarters, variance, label, succeeded: from project.convert on the Hive
           AS(if_else(less_than(job_runs.duration_mins, 25), job_runs.duration_mins, 25), "capped"),
           AS(sum_of(job_runs.duration_mins * job_runs.job_id, over=whole), "weighted"),
           AS(fill_null(scheduler_runs.job_id, -1), "scheduled_job")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formula reads every row
    LEFT_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id),
              reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X64

**Map**
- Sources: jobs, region_costs. Steps: none.
- Finals: picked_costs (job_id, cost_cents, region, size), costed_jobs (job_id, job_name, team, region), costs_filled (job_id, cost_cents, dt, day). All three are queries loaded into Tables nothing reads.
- picked_costs: `<> null` is IS NOT NULL; List.Contains({1, 3}, job_id) is IN (1, 3); Text.Upper is UPPER; the added column is IF.
- costed_jobs: List.Contains(Costs[job_id], job_id) is a row whose job_id is in another table, so `LEFT SEMI JOIN`; `not Text.StartsWith` is NOT LIKE 'n%', case kept as M keeps it.
- costs_filled: ReplaceValue null with 0 is COALESCE(cost_cents, 0); Text.End([dt], 2) is SUBSTR(dt, -2). dt is held as text (20260911), which is what Text.End reads, so it is kept as is.
- Typed over: none. Blank: cost_cents is blank for job 2 on 20260924; picked_costs filters it out and costs_filled replaces it with 0, as the queries say. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

```sql
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt, SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

Toolbox code, with `<database>` as ops. UPPER and SUBSTR are Hive functions (file 10, new chat), and files 03 to 05 name no NOT for starts_with, so those three pieces are left to `project.convert` on the Hive.

```python
from sqlglot_composer import (AS, FROM, SEMI_JOIN, SELECT, WHERE, at_least, equals, fill_null,
                              if_else, is_in, is_not_null, statement)
from references.ops__region_costs import region_costs
from references.ops__jobs import jobs

picked_costs = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents,
           region_costs.region,  # UPPER(region): from project.convert on the Hive
           AS(if_else(at_least(region_costs.cost_cents, 200), "big", "small"), "size")),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_not_null(region_costs.cost_cents), is_in(region_costs.job_id, [1, 3])),
)

costed_jobs = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs, reads_all_partitions=True),
    SEMI_JOIN(region_costs, ON=equals(region_costs.job_id, jobs.job_id),
              reads_all_partitions=True),
    # NOT job_name LIKE 'n%': from project.convert on the Hive
)

costs_filled = statement(
    SELECT(region_costs.job_id, AS(fill_null(region_costs.cost_cents, 0), "cost_cents"),
           region_costs.dt),  # day = SUBSTR(dt, -2): from project.convert on the Hive
    FROM(region_costs, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X65

**Map**
- Sources: jobs, region_budgets, job_owners, scheduler_runs, job_runs. Steps: none.
- Finals (all queries loaded into Tables nothing reads): team_regions (team, region), budget_places (job_id, budget_cents, region, place), jobs_per_team (team, jobs), ran_as_scheduled (run_id, dt), run_measures (run_id, job_id, measure, amount).
- team_regions: AddColumn of a table, then expanded, is a CROSS JOIN of the distinct teams and the distinct regions. The query sorts by team with no FirstN, so no ORDER BY: the order was dropped, as a Hive table holds no order.
- budget_places: Sort then AddIndexColumn is `ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place`; the sort is only for the number, so rows come out unordered.
- jobs_per_team: List.Count(List.Distinct(job_id)) is COUNT(DISTINCT job_id); job_id has no blank in the sample, so nothing differs.
- ran_as_scheduled: an Inner NestedJoin on every column, its new column removed, in Table.Distinct is INTERSECT.
- run_measures: Unpivot is one SELECT per column, stacked with UNION ALL, each with WHERE .. IS NOT NULL as M drops a null (run 98's avg_retry_secs).
- Typed over: none. Blank: no formulas. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
WITH teams AS (
  SELECT DISTINCT team FROM <database>.jobs
), regions AS (
  SELECT DISTINCT region FROM <database>.jobs
)
SELECT t.team, r.region
FROM teams t
CROSS JOIN regions r
```

```sql
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

```sql
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

```sql
SELECT run_id, dt FROM <database>.scheduler_runs
INTERSECT
SELECT run_id, dt FROM <database>.job_runs
```

```sql
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

Toolbox code, with `<database>` as ops. A constant column (`'duration_mins' AS measure`) is not shown in files 03 to 05, so check that line against `project.convert`.

```python
from sqlglot_composer import (AS, CROSS_JOIN, FROM, GROUP_BY, INTERSECT, SELECT, SELECT_DISTINCT,
                              UNION_ALL, WHERE, count_distinct, derived, descending,
                              is_not_null, row_number, statement)
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets
from references.ops__job_owners import job_owners
from references.ops__scheduler_runs import scheduler_runs
from references.ops__job_runs import job_runs

teams = derived("teams", statement(
    SELECT_DISTINCT(jobs.team), FROM(jobs, reads_all_partitions=True)))  # a workbook's query reads every row
regions = derived("regions", statement(
    SELECT_DISTINCT(jobs.region), FROM(jobs, reads_all_partitions=True)))
team_regions = statement(
    SELECT(teams.team, regions.region),
    FROM(teams),
    CROSS_JOIN(regions),
)

budget_places = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(row_number(ORDER_BY=descending(region_budgets.budget_cents)), "place")),
    FROM(region_budgets, reads_all_partitions=True),
)

jobs_per_team = statement(
    SELECT(job_owners.team, AS(count_distinct(job_owners.job_id), "jobs")),
    FROM(job_owners, reads_all_partitions=True),
    GROUP_BY(job_owners.team),
)

ran_as_scheduled = INTERSECT(
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt),
              FROM(scheduler_runs, reads_all_partitions=True)),
    statement(SELECT(job_runs.run_id, job_runs.dt),
              FROM(job_runs, reads_all_partitions=True)),
)

run_measures = UNION_ALL(
    statement(SELECT(job_runs.run_id, job_runs.job_id,
                     AS("duration_mins", "measure"), AS(job_runs.duration_mins, "amount")),
              FROM(job_runs, reads_all_partitions=True),
              WHERE(is_not_null(job_runs.duration_mins))),
    statement(SELECT(job_runs.run_id, job_runs.job_id,
                     AS("avg_retry_secs", "measure"), AS(job_runs.avg_retry_secs, "amount")),
              FROM(job_runs, reads_all_partitions=True),
              WHERE(is_not_null(job_runs.avg_retry_secs))),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X66

**Map**
- Sources: job_runs. Steps: none.
- Finals: ok_runs (run_id, job_id, duration_mins, dt, running, share), and `ok_runs (Total Row)` (duration_mins), a query of its own because ok_runs is not a summary.
- Query ok_runs: `[status] <> null` is IS NOT NULL, Text.StartsWith is `LIKE 'SUCC%'`.
- running: SUMIFS(duration, job_id = this, dt "<="&this dt) over its own Table is a running total with ties included, `SUM(..) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`, with COALESCE(.., 0). share: whole-column SUM, `SUM(..) OVER ()`.
- Total Row: SUBTOTAL(109) is a SUM, one row, no label (the label "Total" is dropped).
- dt here is an ISO date (2026-09-23), so it needs no conversion.
- Typed over: none. Blank: none. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
WITH ok AS (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT run_id, job_id, duration_mins, dt,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM ok
```

```sql
SELECT SUM(duration_mins) AS duration_mins
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

Toolbox code, with `<database>` as ops. Note `rows=(None, 0)` counts rows, not ties: runs 101 and 104 of job 1 share a dt, so the Python's running for 101 is 22 where the Hive (and Excel) gives 62. The Hive is the exact one.

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, derived, fill_null, is_not_null,
                              starts_with, statement, sum_of, window)
from references.ops__job_runs import job_runs

ok = derived("ok", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_not_null(job_runs.status), starts_with(job_runs.status, "SUCC")),
))
per_job = window(PARTITION_BY=ok.job_id, ORDER_BY=ok.dt, rows=(None, 0))
whole = window()
s = statement(
    SELECT(ok.run_id, ok.job_id, ok.duration_mins, ok.dt,
           AS(fill_null(sum_of(ok.duration_mins, over=per_job), 0), "running"),
           AS(ok.duration_mins / sum_of(ok.duration_mins, over=whole), "share")),
    FROM(ok),
)

total_row = statement(
    SELECT(AS(sum_of(job_runs.duration_mins), "duration_mins")),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(is_not_null(job_runs.status), starts_with(job_runs.status, "SUCC")),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X69

**Map**
- Sources: region_costs (typed job_id, cost_cents, region, dt), jobs, region_budgets.
- Steps: region_costs, a CTE `rc` over the source, since job_totals and late_costs read it and its formulas.
- Finals: job_totals (job_id, total_cents, over_count) and late_costs (job_id, dt, running_cost).
- rc: job_name is an XLOOKUP, a LEFT JOIN to jobs; budget is an XLOOKUP, a LEFT JOIN to region_budgets (budget_cents). over_budget is cost_cents > budget. running_cost is a SUMIFS on job_id and dt "<="&this dt over its own Table: a running total, ties included, with COALESCE(.., 0).
- Blank: cost_cents is blank for job 2 on 20260924. over_budget reads it outside an -IFS form, so it is wrapped, COALESCE(cost_cents, 0). running_cost and job_totals read it inside SUMIFS, which skips it.
- dt is held as text (20260911). It is only ordered and passed through, and fixed-width text sorts as the date does, so it is kept as is; late_costs shows it unchanged.
- job_totals is a summary: its only typed column, job_id, is what its SUMIFS and COUNTIFS match on, so it is a GROUP BY of rc. total_cents: SUMIFS with COALESCE(.., 0). over_count: COUNTIFS with over_budget TRUE, a count of rows where it holds, COALESCE(.., 0). Its Total Row only adds up SUMs and COUNTs, so it needs no query of its own: `GROUP BY job_id WITH ROLLUP` adds it as one more row, job_id NULL (a Subtotal row).
- late_costs: the query's filter on running_cost, then three columns. It reads the step.
- No Keys row, and no value is typed over a formula, so nothing depends on it. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
WITH rc AS (
  SELECT c.job_id, c.cost_cents, c.region, c.dt, j.job_name, b.budget_cents AS budget,
    COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(c.cost_cents) OVER (PARTITION BY c.job_id ORDER BY c.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs c
  LEFT JOIN <database>.jobs j ON c.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON c.job_id = b.job_id
)
SELECT job_id,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(CASE WHEN over_budget = TRUE THEN 1 END), 0) AS over_count
FROM rc
GROUP BY job_id WITH ROLLUP
```

```sql
WITH rc AS (
  SELECT c.job_id, c.cost_cents, c.region, c.dt, j.job_name, b.budget_cents AS budget,
    COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(c.cost_cents) OVER (PARTITION BY c.job_id ORDER BY c.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs c
  LEFT JOIN <database>.jobs j ON c.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON c.job_id = b.job_id
)
SELECT job_id, dt, running_cost
FROM rc
WHERE running_cost > 1500
```

Toolbox code, with `<database>` as ops. `rows=(None, 0)` counts rows, not ties; the sample has no repeated dt for a job, so it agrees here, but the Hive is the exact one if that changes.

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, count_rows, derived,
                              equals, fill_null, if_else, more_than, rollup, statement, sum_of,
                              window)
from references.ops__region_costs import region_costs
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets

per_job = window(PARTITION_BY=region_costs.job_id, ORDER_BY=region_costs.dt, rows=(None, 0))
rc = derived("rc", statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region, region_costs.dt,
           jobs.job_name, AS(region_budgets.budget_cents, "budget"),
           AS(if_else(more_than(fill_null(region_costs.cost_cents, 0), region_budgets.budget_cents),
                      True, False), "over_budget"),
           AS(fill_null(sum_of(region_costs.cost_cents, over=per_job), 0), "running_cost")),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, region_costs.job_id), reads_all_partitions=True),
    LEFT_JOIN(region_budgets, ON=equals(region_budgets.job_id, region_costs.job_id),
              reads_all_partitions=True),
))

job_totals = statement(
    SELECT(rc.job_id,
           AS(fill_null(sum_of(rc.cost_cents), 0), "total_cents"),
           AS(fill_null(count_rows(where=equals(rc.over_budget, True)), 0), "over_count")),
    FROM(rc),
    GROUP_BY(rollup(rc.job_id)),
)

late_costs = statement(
    SELECT(rc.job_id, rc.dt, rc.running_cost),
    FROM(rc),
    WHERE(more_than(rc.running_cost, 1500)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X70

**Map**
- Sources: jobs, job_owners, job_runs.
- Steps: staffed (a connection-only query that owner_load reads), and the query owner_load, which busiest_owner reads. Both are CTEs.
- Finals: owner_load (owner, total_mins, runs, avg_mins), the Table with its formula column; `owner_load (Total Row)` (runs); busiest_owner (owner, total_mins, runs). I treat the Table owner_load as a final because only the query owner_load, not the Table, is read by busiest_owner; if you treat it as a step only, drop its two blocks.
- staffed: jobs (job_id, job_name) Inner-joined to the distinct (job_id, owner) pairs, then `[owner] <> null` is `owner IS NOT NULL`.
- owner_load: staffed LeftOuter-joined to job_runs on job_id, grouped by owner: total_mins SUM, runs `Table.RowCount(_)` as COUNT(*). avg_mins: total_mins / runs.
- Total Row: SUBTOTAL(109) over runs is a SUM, a query of its own, one row, the label "Total" dropped, and only runs has a total.
- busiest_owner: Sort descending on runs, then FirstN 1, is ORDER BY .. DESC LIMIT 1. The order is kept because a LIMIT follows.
- Typed over: none. Blank: none read by a formula. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
), owner_load_q AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs, total_mins / runs AS avg_mins
FROM owner_load_q
```

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
), owner_load_q AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT SUM(runs) AS runs
FROM owner_load_q
```

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
), owner_load_q AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs
FROM owner_load_q
ORDER BY runs DESC
LIMIT 1
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, JOIN, LEFT_JOIN, LIMIT, ORDER_BY, SELECT,
                              SELECT_DISTINCT, WHERE, count_rows, derived, descending, equals,
                              is_not_null, statement, sum_of)
from references.ops__jobs import jobs
from references.ops__job_owners import job_owners
from references.ops__job_runs import job_runs

owners = derived("owners", statement(
    SELECT_DISTINCT(job_owners.job_id, job_owners.owner),
    FROM(job_owners, reads_all_partitions=True),  # a workbook's query reads every row
))
staffed = derived("staffed", statement(
    SELECT(jobs.job_id, jobs.job_name, owners.owner),
    FROM(jobs, reads_all_partitions=True),
    JOIN(owners, ON=equals(owners.job_id, jobs.job_id)),
    WHERE(is_not_null(owners.owner)),
))
owner_load_q = derived("owner_load_q", statement(
    SELECT(staffed.owner, AS(sum_of(job_runs.duration_mins), "total_mins"),
           AS(count_rows(), "runs")),
    FROM(staffed),
    LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, staffed.job_id), reads_all_partitions=True),
    GROUP_BY(staffed.owner),
))

owner_load = statement(
    SELECT(owner_load_q.owner, owner_load_q.total_mins, owner_load_q.runs,
           AS(owner_load_q.total_mins / owner_load_q.runs, "avg_mins")),
    FROM(owner_load_q),
)

owner_load_total_row = statement(
    SELECT(AS(sum_of(owner_load_q.runs), "runs")),
    FROM(owner_load_q),
)

busiest_owner = statement(
    SELECT(owner_load_q.owner, owner_load_q.total_mins, owner_load_q.runs),
    FROM(owner_load_q),
    ORDER_BY(descending(owner_load_q.runs)),
    LIMIT(1),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.
