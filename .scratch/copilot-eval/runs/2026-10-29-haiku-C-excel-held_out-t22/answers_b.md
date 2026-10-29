date: 2026-10-29
arm: C
model: haiku
files: 423bc80

## X46

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team).
- Steps: none.
- Finals: jobs (job_id, job_name, team, shortest, runs, busiest).
- Typed over a formula: none.
- Marks: none. No blank sits in a column a formula reads.
- Refused: none.
- Left alone: none. Parameters and Keys are empty, so none.
- Fill in: `<database>`.

```sql
WITH counted AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(s.shortest, 0) AS shortest,
    COALESCE(c.runs, 0) AS runs
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
)
SELECT job_id, job_name, team, shortest, runs,
  RANK() OVER (ORDER BY runs DESC) AS busiest
FROM counted
```

## X47

**Map**
- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg).
- Typed over a formula: none.
- Marks: region_avg is AVERAGEIF, so AVG, left NULL. region_total is SUMIF over its own Table, so a window with COALESCE.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

## X48

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region); run_alerts (alert_id, run_id, severity, dt).
- Steps: none.
- Finals: quiet_runs (run_id, job_id, status); slow_regions (region, avg_mins, fastest).
- Typed over a formula: none.
- Marks: none. No formula reads a blank.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final quiet_runs (Power Query LeftAnti, then select):

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

Final slow_regions (Power Query inner join, group, then the HAVING on the averaged value):

```sql
SELECT j.region,
  AVG(r.duration_mins) AS avg_mins,
  MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

## X49

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); run_alerts (alert_id, run_id, severity, dt); jobs (job_id, job_name, team, region); scheduler_runs (run_id, job_id, dt); job_owners (job_id, team, owner, dt).
- Steps: none. No query is read by another query or by a formula.
- Finals: alert_status (alert_id, severity, status); run_check (run_id, status, scheduled_run); teams (team).
- Typed over a formula: none.
- Marks: none. Blank status (run 98), blank owner and blank severity are kept as NULL; no formula reads them.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final alert_status (RightOuter, so the two tables swap to a LEFT JOIN from job_runs):

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
```

Final run_check (FullOuter):

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

Final teams (Table.Combine inside Table.Distinct, so UNION):

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

## X50

**Map**
- Sources: job_owners (job_id, team, owner, dt); jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: owners (job_id, owner, job_name, newest_first).
- Typed over a formula: none.
- Marks: none. The blank owner for job 4 stays NULL; no formula reads owner.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM (
  SELECT DISTINCT job_id, owner
  FROM <database>.job_owners
) o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

## X59

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name); run_alerts (alert_id, run_id, severity, dt).
- Steps: none.
- Finals: jobs (job_id, job_name, long_runs, failed_mins, not_test); run_alerts (alert_id, run_id, severity, dt, alerts_so_far).
- Typed over a formula: none.
- Marks: blank status (run 98) is not wrapped. not_test counts it, as Excel counts a blank under "<>TEST", and failed_mins skips it, as the "f*" match does. No COALESCE on status.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final jobs (COUNTIFS and SUMIFS over another Table, so LEFT JOINs to grouped subqueries):

```sql
SELECT j.job_id, j.job_name,
  COALESCE(lr.long_runs, 0) AS long_runs,
  COALESCE(fm.failed_mins, 0) AS failed_mins,
  COALESCE(nt.not_test, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS long_runs
  FROM <database>.job_runs
  WHERE duration_mins >= 20
  GROUP BY job_id
) lr ON j.job_id = lr.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS failed_mins
  FROM <database>.job_runs
  WHERE LOWER(status) LIKE 'f%'
  GROUP BY job_id
) fm ON j.job_id = fm.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS not_test
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) nt ON j.job_id = nt.job_id
```

Final run_alerts (running count over its own Table, ties included):

```sql
SELECT alert_id, run_id, severity, dt,
  COALESCE(COUNT(*) OVER (ORDER BY run_id
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
FROM <database>.run_alerts
```

## X60

**Map**
- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region); region_budgets (Total Row) (one row: COUNT of job_id, AVG of budget_cents, no label).
- Typed over a formula: none.
- Marks: none. No blanks in the sample.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final region_budgets (SUM and AVERAGE over the whole column are windows; COUNTIFS "<" +1 is RANK ASC within region):

```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

Total Row region_budgets (Total Row):

```sql
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

## X61

**Map**
- Sources: region_costs (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: by_region (region, total_cents, entries, priciest). It is a summary of region_costs, since its only typed column is region.
- Total Row of by_region: folded into by_region's query by GROUP BY ... WITH ROLLUP. Its row is the one with region NULL (the Subtotal row). No separate query.
- Typed over a formula: none.
- Marks: blank cost_cents (job 2, 20260924) stays NULL. SUMIFS and MAXIFS skip it, and COUNTIFS counts the row, as Excel does. dt is held as text (20260911), but no formula reads it, so it is not converted.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final by_region (summary with the Total Row folded in):

```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(*), 0) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

## X62

**Map**
- Sources: team_notes (team, note, written_on).
- Steps: none.
- Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short).
- Typed over a formula: none.
- Marks: week_of and month_of are CAST to STRING, as file 11 writes the week and month starts.
- Refused: none.
- Left alone: none.
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

## X63

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs); scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded).
- Typed over a formula: none.
- Marks: blank status (run 98) is wrapped as COALESCE(status, '') in succeeded, because SEARCH on a blank is not a match in Excel. blank avg_retry_secs is not wrapped, since no_retry is ISBLANK and becomes IS NULL. Run 99 has no scheduler row, so scheduled_job is -1 by the XLOOKUP fourth argument.
- Refused: none.
- Left alone: none.
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

## X64

**Map**
- Sources: jobs (job_id, job_name, team, region); region_costs (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: picked_costs (job_id, cost_cents, region, size); costed_jobs (job_id, job_name, team, region); costs_filled (job_id, cost_cents, dt, day).
- Typed over a formula: none.
- Marks: in costs_filled, the blank cost_cents (job 2, 20260924) becomes 0 by COALESCE, as Table.ReplaceValue does. dt is held as text (20260911), so it is converted to 2026-09-11 with CONCAT(SUBSTR...). day reads the last two characters, as Text.End does.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final picked_costs:

```sql
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

Final costed_jobs (List.Contains on another Table is a LEFT SEMI JOIN; "and not" is NOT):

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

Final costs_filled:

```sql
SELECT job_id,
  COALESCE(cost_cents, 0) AS cost_cents,
  CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS dt,
  SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

## X65

**Map**
- Sources: jobs (job_id, job_name, team, region); region_budgets (job_id, budget_cents, region); job_owners (job_id, team, owner, dt); scheduler_runs (run_id, job_id, dt); job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: team_regions (team, region); budget_places (job_id, budget_cents, region, place); jobs_per_team (team, jobs); ran_as_scheduled (run_id, dt); run_measures (run_id, job_id, measure, amount).
- Typed over a formula: none.
- Marks: team_regions sorts by team with no FirstN and no index after it, so the order was dropped and there is no ORDER BY. run_measures drops run 98's blank avg_retry_secs, as Table.Unpivot drops a null. jobs_per_team counts COUNT(DISTINCT job_id); no job_id is blank.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final team_regions (AddColumn then expand is a CROSS JOIN):

```sql
SELECT t.team, u.region
FROM (SELECT DISTINCT team FROM <database>.jobs) t
CROSS JOIN (SELECT DISTINCT region FROM <database>.jobs) u
```

Final budget_places (Table.Sort then AddIndexColumn, so ROW_NUMBER with the sort's order):

```sql
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

Final jobs_per_team:

```sql
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

Final ran_as_scheduled (inner join on both keys, then distinct):

```sql
SELECT DISTINCT s.run_id, s.dt
FROM <database>.scheduler_runs s
JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.dt = r.dt
```

Final run_measures (Table.Unpivot as one SELECT per column, stacked, each with a NOT NULL filter):

```sql
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

## X66

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: ok_runs (run_id, job_id, duration_mins, dt, running, share); ok_runs (Total Row) (duration_mins, one column, no label).
- Typed over a formula: none.
- Marks: the blank status (run 98) is dropped by status IS NOT NULL, as the M does. Text.StartsWith is LIKE 'SUCC%', case kept. running is SUMIFS over its own Table with "<=", so a RANGE window that counts ties.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final ok_runs:

```sql
SELECT run_id, job_id, duration_mins, dt,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

Total Row ok_runs (Total Row):

```sql
WITH ok_runs AS (
  SELECT duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT SUM(duration_mins) AS duration_mins
FROM ok_runs
```

## X69

**Map**
- Sources: jobs (job_id, job_name, team, region); region_budgets (job_id, budget_cents, region).
- Steps: region_costs, a Table with formulas that job_totals and late_costs read. It is kept as the CTEs dated and costs inside each final's query.
- Finals: job_totals (job_id, total_cents, over_count), a summary of costs; late_costs (job_id, dt, running_cost).
- Typed over a formula: none.
- Marks: dt is held as text (20260911) and is converted with CONCAT(SUBSTR...) in dated, since the running total orders by it. Blank cost_cents (job 2, 20260924): over_budget uses COALESCE(cost_cents, 0), a comparison and not an -IFS form. running_cost and total_cents skip the blank, as SUMIFS does.
- Refused: none.
- Left alone: none.
- Total Row of job_totals: folded into its query by GROUP BY job_id WITH ROLLUP. Its row has job_id NULL.
- late_costs tests a window's value in the outer statement, reading the costs CTE.
- Fill in: `<database>`.

Final job_totals:

```sql
WITH dated AS (
  SELECT r.job_id, r.cost_cents, r.region,
    CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) AS dt,
    j.job_name,
    b.budget_cents AS budget
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
costs AS (
  SELECT job_id, cost_cents, region, dt, job_name, budget,
    COALESCE(cost_cents, 0) > budget AS over_budget,
    COALESCE(SUM(cost_cents) OVER (PARTITION BY job_id ORDER BY dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM dated
)
SELECT job_id,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(CASE WHEN over_budget = TRUE THEN 1 END), 0) AS over_count
FROM costs
GROUP BY job_id WITH ROLLUP
```

Final late_costs (the same dated and costs CTEs, then the filter):

```sql
WITH dated AS (
  SELECT r.job_id, r.cost_cents, r.region,
    CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) AS dt,
    j.job_name,
    b.budget_cents AS budget
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
costs AS (
  SELECT job_id, cost_cents, region, dt, job_name, budget,
    COALESCE(cost_cents, 0) > budget AS over_budget,
    COALESCE(SUM(cost_cents) OVER (PARTITION BY job_id ORDER BY dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM dated
)
SELECT job_id, dt, running_cost
FROM costs
WHERE running_cost > 1500
```

## X70

**Map**
- Sources: jobs (job_id, job_name, team, region); job_owners (job_id, team, owner, dt); job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: staffed, a connection-only query that owner_load's query reads, so it is kept as a CTE; and the owner_load query, which busiest_owner reads, kept as the CTE grouped.
- Finals: owner_load (owner, total_mins, runs, avg_mins); owner_load (Total Row) (runs, one column, no label); busiest_owner (owner, total_mins, runs).
- Typed over a formula: none.
- Marks: the blank owner for job 4 is dropped by owner IS NOT NULL, as the M's <> null does. avg_mins is total_mins / runs.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final owner_load:

```sql
WITH staffed AS (
  SELECT j.job_id, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
    ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
grouped AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs, total_mins / runs AS avg_mins
FROM grouped
```

Total Row owner_load (Total Row):

```sql
WITH staffed AS (
  SELECT j.job_id, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
    ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
grouped AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT SUM(runs) AS runs
FROM grouped
```

Final busiest_owner (Table.Sort then FirstN 1):

```sql
WITH staffed AS (
  SELECT j.job_id, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
    ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
grouped AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs
FROM grouped
ORDER BY runs DESC
LIMIT 1
```

## X73

**Map**
- Sources: region_budgets (job_id, budget_cents, region); jobs (job_id, job_name, team, region).
- Steps: eu_budgets, the query that eu_count's query reads, kept as the CTE eu_budgets.
- Finals: eu_budgets (job_id, budget_cents, region, job_name, dollars); eu_count (region, jobs, total_cents).
- Typed over a formula: none.
- Marks: none. No blanks in the sample.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final eu_budgets:

```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT job_id, budget_cents, region, job_name,
  budget_cents / 100 AS dollars
FROM eu_budgets
```

Final eu_count:

```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT region,
  COUNT(*) AS jobs,
  SUM(budget_cents) AS total_cents
FROM eu_budgets
GROUP BY region
```

## X74

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); run_alerts (alert_id, run_id, severity, dt).
- Steps: run_alerts, a Table with formulas (status, job_id, alerts_so_far) that by_status and late_alerts read. It is kept as the CTE alerts.
- Finals: by_status (status, alerts), a summary of the step since its only typed column is status; late_alerts (alert_id, run_id, alerts_so_far).
- Typed over a formula: none.
- Marks: none. The only blank status (run 98) is not an alert's run.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

The CTE used by both finals:

```sql
WITH alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    r.status, r.job_id,
    COALESCE(COUNT(*) OVER (ORDER BY a.run_id
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
```

Final by_status:

```sql
WITH alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    r.status, r.job_id,
    COALESCE(COUNT(*) OVER (ORDER BY a.run_id
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT status, COALESCE(COUNT(*), 0) AS alerts
FROM alerts
GROUP BY status
```

Final late_alerts (the window is computed in the CTE, then tested in the outer statement):

```sql
WITH alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    r.status, r.job_id,
    COALESCE(COUNT(*) OVER (ORDER BY a.run_id
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM alerts
WHERE alerts_so_far > 5
```

## X77

**Map**
- Sources: run_alerts (alert_id, run_id, severity, dt).
- Steps: the high_alerts query, which high_per_day's query reads, kept as the CTE high_alerts.
- Finals: high_alerts (alert_id, run_id, dt, late_run); high_per_day (dt, alerts).
- Typed over a formula: none.
- Marks: none.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final high_alerts:

```sql
WITH high_alerts AS (
  SELECT alert_id, run_id, dt
  FROM <database>.run_alerts
  WHERE severity = 'high'
)
SELECT alert_id, run_id, dt,
  run_id > 100 AS late_run
FROM high_alerts
```

Final high_per_day:

```sql
WITH high_alerts AS (
  SELECT alert_id, run_id, dt
  FROM <database>.run_alerts
  WHERE severity = 'high'
)
SELECT dt, COUNT(*) AS alerts
FROM high_alerts
GROUP BY dt
```

## X78

**Map**
- Sources: region_costs (job_id, cost_cents, region, dt).
- Steps: known_costs, the query that cost_per_job's query reads, kept as the CTE known_costs.
- Finals: known_costs (job_id, cost_cents, dt, dollars); known_costs (Total Row) (cost_cents, one column, no label); cost_per_job (job_id, total_cents).
- Typed over a formula: none.
- Marks: the blank cost_cents (job 2, 20260924) is dropped by cost_cents IS NOT NULL, as the M's <> null does. So known_costs has 27 rows, and job 2's total leaves that row out. dt is held as text, but no formula reads it, so it is not converted.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final known_costs:

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT job_id, cost_cents, dt,
  cost_cents / 100 AS dollars
FROM known_costs
```

Total Row known_costs (Total Row):

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT SUM(cost_cents) AS cost_cents
FROM known_costs
```

Final cost_per_job (Table.Group, List.Sum):

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT job_id, SUM(cost_cents) AS total_cents
FROM known_costs
GROUP BY job_id
```
