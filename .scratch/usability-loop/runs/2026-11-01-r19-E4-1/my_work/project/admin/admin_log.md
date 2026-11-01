# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 15:56:04, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: start.py, at commit nogit
- Result: worked

## 2026-11-01 15:59:35, Project action

- Call: `project.convert("costs", ...)`
- Tables named: mart_dev.job_costs, mart_dev.team_runs
- Files: converted 2 scripts into 2 Saved tables; wrote admin/workflows/convert/costs/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 15:59:51, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.job_costs, mart_dev.team_runs
- Files: wrote references/mart_dev__job_costs.py; wrote references/mart_dev__team_runs.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 16:00:05, Statement with an Unchecked derived table

- Call: `unchecked_derived("k", ...)`
- Tables named: ops.job_runs, ops.jobs, mart_dev.job_costs
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH k AS (
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
    r.job_id,
    r.duration_mins,
    jb.team
  FROM ops.job_runs AS r
  LEFT JOIN ops.jobs AS jb
    ON r.job_id = jb.job_id
), c AS (
  SELECT
    job_runs.job_id,
    SUM(job_runs.duration_mins) AS total
  FROM job_runs
  GROUP BY
    job_runs.job_id
)
INSERT OVERWRITE TABLE mart_dev.job_costs
SELECT
  k.job_id,
  CASE WHEN k.job_id = 3 THEN 1000 ELSE COALESCE(c.total, 0) * 50 END AS cost_cents
FROM k
LEFT JOIN c
  ON k.job_id = c.job_id
```

## 2026-11-01 16:00:05, Statement with an Unchecked derived table

- Call: `unchecked_derived("k", ...)`
- Tables named: ops.job_runs, ops.jobs, mart_dev.team_runs
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH k AS (
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
    r.job_id,
    r.duration_mins,
    jb.team
  FROM ops.job_runs AS r
  LEFT JOIN ops.jobs AS jb
    ON r.job_id = jb.job_id
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
  k.team,
  COALESCE(c.runs, 0) AS runs
FROM k
LEFT JOIN c
  ON k.team = c.team
```

## 2026-11-01 16:00:07, Project action

- Call: `project.compare_batch("costs")`
- Tables named: mart_dev.job_costs, mart_dev.team_runs
- Files: wrote tables/mart_dev__job_costs/conversion/compare.md; wrote tables/mart_dev__team_runs/conversion/compare.md; moved admin/workflows/convert/costs/ to admin/workflows/convert/finished/costs/
- Script: a notebook, at commit nogit
- Result: worked
