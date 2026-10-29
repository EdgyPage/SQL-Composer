date: 2026-10-29
arm: C
model: haiku
files: 5df4678

## X46

**Map**
- Sources: job_runs, jobs (each has typed columns).
- Steps: none.
- Finals: jobs (job_id, job_name, team, shortest, runs, busiest). job_runs has no formula of its own, so it is a source only.
- Parameters and Keys: empty, none.
- Left alone: the Steps sheet, which holds no Table.

```sql
SELECT j.job_id, j.job_name, j.team,
  COALESCE(s.shortest, 0) AS shortest,
  COALESCE(c.runs, 0) AS runs,
  RANK() OVER (ORDER BY COALESCE(c.runs, 0) DESC) AS busiest
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, MIN(duration_mins) AS shortest
  FROM <database>.job_runs
  GROUP BY job_id
) s ON j.job_id = s.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS runs
  FROM <database>.job_runs
  GROUP BY job_id
) c ON j.job_id = c.job_id
```

**Marks:** none. No blank sits in duration_mins or job_id.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X47

**Map**
- Sources: region_budgets.
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg).
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

**Marks:** none. No blanks. region_avg is left NULL where nothing matches, as AVERAGEIF is left NULL.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X48

**Map**
- Sources: job_runs, jobs, run_alerts.
- Steps: none.
- Finals: quiet_runs (run_id, job_id, status), from query quiet_runs; slow_regions (region, avg_mins, fastest), from query slow_regions.
- Connection-only queries: none.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

quiet_runs, a LeftAnti join, which is a LEFT JOIN with WHERE IS NULL:

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

slow_regions, an Inner join, a GROUP BY, and HAVING for the Table.SelectRows after the Table.Group:

```sql
SELECT j.region,
  AVG(r.duration_mins) AS avg_mins,
  MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

**Marks:** none. The blank status on run 98 is read by no formula, so it passes through as NULL.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X49

**Map**
- Sources: job_runs, jobs, run_alerts, scheduler_runs, job_owners.
- Steps: none.
- Finals: alert_status (alert_id, severity, status), from query alert_status; run_check (run_id, status, scheduled_run), from query run_check; teams (team), from query teams.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

alert_status, a RightOuter join, which is a LEFT JOIN with the two tables swapped:

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON a.run_id = r.run_id
```

run_check, a FullOuter join:

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

teams, Table.Combine then Table.Distinct, which is UNION:

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

**Marks:** none needed. No formula reads a blank. Run 100, which is only in scheduler_runs, keeps run_id NULL, as the full outer join gives.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X50

**Map**
- Sources: job_owners, jobs.
- Steps: none.
- Finals: owners (job_id, owner, job_name, newest_first), from query owners.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

**Marks:** the blank owner for job 4 stays NULL. No formula reads owner, so nothing is wrapped.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X59

**Map**
- Sources: job_runs, jobs, run_alerts.
- Steps: none.
- Finals: jobs (job_id, job_name, long_runs, failed_mins, not_test); run_alerts (alert_id, run_id, severity, dt, alerts_so_far).
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(lr.n, 0) AS long_runs,
  COALESCE(fr.total, 0) AS failed_mins,
  COALESCE(nt.n, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS n
  FROM <database>.job_runs
  WHERE duration_mins >= 20
  GROUP BY job_id
) lr ON j.job_id = lr.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total
  FROM <database>.job_runs
  WHERE LOWER(status) LIKE 'f%'
  GROUP BY job_id
) fr ON j.job_id = fr.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS n
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) nt ON j.job_id = nt.job_id
```

```sql
WITH run_alerts AS (
  SELECT alert_id, run_id, severity, dt,
    COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts
)
SELECT alert_id, run_id, severity, dt, alerts_so_far
FROM run_alerts
```

Note: the second block is the run_alerts Table written as a single query. It needs no CTE, so the same SELECT without the WITH works too.

**Marks:**
- The blank status on run 98 is not wrapped. It sits in -IFS forms, which skip a blank, and "<>TEST" counts it as Excel does, through `OR status IS NULL`.
- The "f*" wildcard becomes `LOWER(status) LIKE 'f%'`, as Excel ignores case.
- alerts_so_far is a running count, ties included, so no COALESCE.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X60

**Map**
- Sources: region_budgets.
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region); region_budgets (Total Row), a query of its own, one row, with the label left out.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

Total Row, SUBTOTAL(103) as COUNT, SUBTOTAL(101) as AVG:

```sql
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

**Marks:**
- The Total Row's "Total" label is left out.
- rank_in_region is the COUNTIFS "<" plus 1 form, so it is RANK with ASC inside each region.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X61

**Map**
- Sources: region_costs.
- Steps: none.
- Finals: by_region (region, total_cents, entries, priciest). It is a summary, since its only typed column is region, so it is a GROUP BY of region_costs.
- Total Row: its totals are SUM, SUM and MAX of MAXes, so it needs no query of its own. The GROUP BY ends WITH ROLLUP, and the NULL-region row it adds is the Total Row. Its "Total" label is left out.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
SELECT region,
  SUM(cost_cents) AS total_cents,
  COUNT(*) AS entries,
  MAX(cost_cents) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

**Marks:**
- The blank cost_cents on job 2, 20260924, stays NULL. SUM and MAX skip it, as the -IFS forms do, and COUNTIFS counts the row.
- dt is held as text, but no formula reads it, so no date conversion.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X62

**Map**
- Sources: team_notes.
- Steps: none.
- Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short).
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

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

**Marks:**
- written_on is a date, so no text-date conversion.
- week_of and month_of are cast to STRING, as file 11's rules write a week's and a month's start.
- No blanks.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X63

**Map**
- Sources: scheduler_runs (read by a formula, so a source only), job_runs.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded).
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

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

**Marks:**
- Blank status on run 98: wrapped as COALESCE(status, ''), because the SEARCH inside ISNUMBER reads it outside an -IFS form. Say blank.
- Blank avg_retry_secs on run 98: ISBLANK becomes `IS NULL`, not wrapped.
- scheduled_job: XLOOKUP's fourth argument, -1, becomes COALESCE(s.job_id, -1). Run 99 has no scheduler row, so it gets -1.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X64

**Map**
- Sources: jobs, region_costs.
- Steps: none.
- Finals: picked_costs (job_id, cost_cents, region, size), from query picked_costs; costed_jobs (job_id, job_name, team, region), from query costed_jobs; costs_filled (job_id, cost_cents, dt, day), from query costs_filled.
- Connection-only queries: none.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

picked_costs:

```sql
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

costed_jobs, a LEFT SEMI JOIN on region_costs:

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

costs_filled:

```sql
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt,
  SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

**Marks:**
- The blank cost on job 2, 20260924, is wrapped as COALESCE(cost_cents, 0) in costs_filled, as Table.ReplaceValue does. Say blank. picked_costs drops it with IS NOT NULL.
- dt is held as text. Text.End reads its last two characters, so day is SUBSTR(dt, -2) with no date conversion.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X65

**Map**
- Sources: jobs, region_budgets, job_owners, scheduler_runs, job_runs.
- Steps: none.
- Finals: team_regions (team, region); budget_places (job_id, budget_cents, region, place); jobs_per_team (team, jobs); ran_as_scheduled (run_id, dt); run_measures (run_id, job_id, measure, amount).
- Connection-only queries: none.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

team_regions, a cross join. The final Table.Sort has no FirstN or index after it, so its order is dropped:

```sql
SELECT t.team, r.region
FROM (SELECT DISTINCT team FROM <database>.jobs) t
CROSS JOIN (SELECT DISTINCT region FROM <database>.jobs) r
```

budget_places, Table.Sort then Table.AddIndexColumn:

```sql
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

jobs_per_team:

```sql
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

ran_as_scheduled, an inner join on both keys, then Table.Distinct:

```sql
SELECT DISTINCT s.run_id, s.dt
FROM <database>.scheduler_runs s
JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.dt = r.dt
```

run_measures, Table.Unpivot as one SELECT per column, stacked with UNION ALL:

```sql
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

**Marks:**
- team_regions: the order was dropped, since a Hive table holds no order and the Table.Sort has nothing after it to keep it.
- The blank avg_retry_secs on run 98 gets no row in run_measures, as M drops a null there.
- jobs_per_team: COUNT(DISTINCT) counts job_id, which has no blank.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X66

**Map**
- Sources: job_runs.
- Steps: none.
- Finals: ok_runs (run_id, job_id, duration_mins, dt, running, share), from query ok_runs; ok_runs (Total Row), a query of its own, one row, with the label left out. ok_runs is not a summary, so the Total Row gets its own query.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

ok_runs:

```sql
WITH ok AS (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT run_id, job_id, duration_mins, dt,
  SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM ok
```

Total Row, SUBTOTAL(109) as SUM:

```sql
WITH ok AS (
  SELECT duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT SUM(duration_mins) AS duration_mins
FROM ok
```

**Marks:**
- The blank status on run 98 is dropped by `status IS NOT NULL`, as the query's <> null does.
- running is a running total by job, ties included, so it is RANGE UNBOUNDED PRECEDING to CURRENT ROW.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X69

**Map**
- Sources: region_costs, jobs, region_budgets. jobs and region_budgets are read by formulas, so they are sources only.
- Steps: none.
- Finals: region_costs (job_id, cost_cents, region, dt, job_name, budget, over_budget, running_cost).
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
WITH region_costs AS (
  SELECT job_id, cost_cents, region, dt,
    CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS dt_date
  FROM <database>.region_costs
)
SELECT c.job_id, c.cost_cents, c.region, c.dt,
  j.job_name,
  b.budget_cents AS budget,
  COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
  SUM(c.cost_cents) OVER (PARTITION BY c.job_id ORDER BY c.dt_date RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
FROM region_costs c
LEFT JOIN <database>.jobs j ON c.job_id = j.job_id
LEFT JOIN <database>.region_budgets b ON c.job_id = b.job_id
```

**Marks:**
- dt is held as text, so it is converted to a date string, dt_date, for the running order. Say the date is held as text.
- The blank cost on job 2, 20260924, is wrapped as COALESCE(cost_cents, 0) in over_budget, since that comparison is not an -IFS form. Say blank.
- In running_cost the blank is skipped, as SUMIFS skips it, so it is not wrapped.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X70

**Map**
- Sources: jobs, job_owners, job_runs.
- Steps:
  - staffed, a connection-only query that owner_load reads, so it is a CTE.
  - owner_load, a Table with a formula (avg_mins) that busiest_owner reads, so it is a step.
- Finals:
  - busiest_owner (owner, total_mins, runs), from query busiest_owner.
  - owner_load (Total Row), a query of its own, one row, with the label left out.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

busiest_owner:

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs,
    SUM(r.duration_mins) / COUNT(*) AS avg_mins
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs
FROM owner_load
ORDER BY runs DESC
LIMIT 1
```

owner_load (Total Row), SUBTOTAL(109) as SUM:

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs,
    SUM(r.duration_mins) / COUNT(*) AS avg_mins
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT SUM(runs) AS runs
FROM owner_load
```

**Marks:**
- Owner blank on job 4 is dropped by `owner IS NOT NULL`, as the query's <> null does.
- Table.RowCount becomes COUNT(*), and List.Sum becomes SUM.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X73

**Map**
- Sources: region_budgets, jobs.
- Steps: eu_budgets, a Table with a formula (dollars) that eu_count's query reads, so it is a CTE.
- Finals: eu_count (region, jobs, total_cents), from query eu_count.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name,
    b.budget_cents / 100 AS dollars
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT region, COUNT(*) AS jobs, SUM(budget_cents) AS total_cents
FROM eu_budgets
GROUP BY region
```

**Marks:** none. No blanks.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X74

**Map**
- Sources: run_alerts, job_runs.
- Steps: run_alerts, a Table with formulas (status, job_id, alerts_so_far) that by_status and late_alerts read, so it is a CTE in both.
- Finals:
  - by_status (status, alerts), a summary, since its only typed column is status, which COUNTIFS matches on. It is a GROUP BY of the run_alerts step.
  - late_alerts (alert_id, run_id, alerts_so_far), from query late_alerts.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

by_status:

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(r.status, '') AS status,
    r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT status, COUNT(*) AS alerts
FROM run_alerts
GROUP BY status
```

late_alerts:

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(r.status, '') AS status,
    r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM run_alerts
WHERE alerts_so_far > 5
```

**Marks:**
- The status lookup reads job_runs.status, which is blank on run 98. It is wrapped as COALESCE(status, ''). Say blank. No alert belongs to run 98, so the blank does not show in this sample.
- alerts_so_far is a running count, ties included. It is computed in the step, and late_alerts tests it in its WHERE.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X77

**Map**
- Sources: run_alerts.
- Steps: high_alerts, a Table with a formula (late_run) that high_per_day's query reads, so it is a CTE. late_run is in the step only and no final reads it.
- Finals: high_per_day (dt, alerts), from query high_per_day.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
WITH high_alerts AS (
  SELECT alert_id, run_id, dt, run_id > 100 AS late_run
  FROM <database>.run_alerts
  WHERE severity = 'high'
)
SELECT dt, COUNT(*) AS alerts
FROM high_alerts
GROUP BY dt
```

**Marks:** none. No blanks.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X78

**Map**
- Sources: region_costs.
- Steps: known_costs, a Table with a formula (dollars) that cost_per_job's query reads, so it is a CTE.
- Finals:
  - cost_per_job (job_id, total_cents), from query cost_per_job.
  - known_costs (Total Row), a query of its own, since known_costs is not a summary. One row, the label left out.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

cost_per_job:

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt, cost_cents / 100 AS dollars
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT job_id, SUM(cost_cents) AS total_cents
FROM known_costs
GROUP BY job_id
```

known_costs (Total Row), SUBTOTAL(109) as SUM:

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt, cost_cents / 100 AS dollars
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT SUM(cost_cents) AS cost_cents
FROM known_costs
```

**Marks:**
- The blank cost on job 2, 20260924, is dropped by `cost_cents IS NOT NULL`, as the query's <> null does.
- The Total Row's SUM skips NULL.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.
