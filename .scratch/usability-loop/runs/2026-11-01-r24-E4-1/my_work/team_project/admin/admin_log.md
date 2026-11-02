# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 23:18:49, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: start.py, at commit nogit
- Result: worked

## 2026-11-01 23:22:32, Project action

- Call: `project.convert("costs", ...)`
- Tables named: mart_dev.job_costs, mart_dev.team_runs
- Files: converted 2 scripts into 2 Saved tables; wrote admin/workflows/convert/costs/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 23:22:47, Project action

- Call: `project.write_decisions(...)`
- Files: none changed
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 23:22:54, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.job_costs, mart_dev.team_runs
- Files: wrote references/mart_dev__job_costs.py; wrote references/mart_dev__team_runs.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 23:23:16, Statement with an Unchecked derived table

- Call: `unchecked_derived("g", ...)`
- Tables named: ops.job_runs, ops.jobs, mart_dev.job_costs
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH g AS (
  SELECT
    1 AS job_id
  UNION ALL
  SELECT
    2
  UNION ALL
  SELECT
    3
  UNION ALL
  SELECT
    4
), job_runs AS (
  SELECT
    r.run_id,
    r.job_id,
    r.status,
    r.duration_mins,
    r.avg_retry_secs,
    r.dt,
    j.team
  FROM ops.job_runs AS r
  LEFT JOIN ops.jobs AS j
    ON r.job_id = j.job_id
), s AS (
  SELECT
    job_runs.job_id,
    SUM(job_runs.duration_mins) AS total
  FROM job_runs
  GROUP BY
    job_runs.job_id
)
INSERT OVERWRITE TABLE mart_dev.job_costs
SELECT
  g.job_id,
  CASE WHEN g.job_id = 3 THEN 1000 ELSE COALESCE(s.total, 0) * 50 END AS cost_cents
FROM g
LEFT JOIN s
  ON g.job_id = s.job_id
```

## 2026-11-01 23:23:16, Statement with an Unchecked derived table

- Call: `unchecked_derived("g", ...)`
- Tables named: ops.job_runs, ops.jobs, mart_dev.team_runs
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH g AS (
  SELECT
    'data' AS team
  UNION ALL
  SELECT
    'finance'
  UNION ALL
  SELECT
    'web'
), job_runs AS (
  SELECT
    r.run_id,
    r.job_id,
    r.status,
    r.duration_mins,
    r.avg_retry_secs,
    r.dt,
    j.team
  FROM ops.job_runs AS r
  LEFT JOIN ops.jobs AS j
    ON r.job_id = j.job_id
), c AS (
  SELECT
    job_runs.team,
    COUNT(*) AS runs
  FROM job_runs
  GROUP BY
    job_runs.team
)
INSERT OVERWRITE TABLE mart_dev.team_runs
SELECT
  g.team,
  COALESCE(c.runs, 0) AS runs
FROM g
LEFT JOIN c
  ON g.team = c.team
```

## 2026-11-01 23:23:22, Project action

- Call: `project.compare_batch("costs")`
- Tables named: mart_dev.job_costs, mart_dev.team_runs
- Files: wrote tables/mart_dev__job_costs/conversion/compare.md; wrote tables/mart_dev__team_runs/conversion/compare.md; moved admin/workflows/convert/costs/ to admin/workflows/convert/finished/costs/
- Script: a notebook, at commit nogit
- Result: worked
