# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 14:04:03, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: start_project.py, at commit nogit
- Result: worked

## 2026-11-01 14:05:07, Project action

- Call: `project.add_references(["ops.job_runs"], query=...)`
- Tables named: ops.job_runs
- Files: created references/ops__job_runs.py; wrote references/ops.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 14:05:51, Project action

- Call: `project.convert("daily_runs", ...)`
- Tables named: mart_dev.daily_runs
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/daily_runs/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 14:06:25, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.daily_runs
- Files: wrote references/mart_dev__daily_runs.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 14:06:44, Statement with an Unchecked derived table

- Call: `unchecked_derived("d", ...)`
- Tables named: ops.job_runs
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH d AS (
  SELECT
    '2026-09-23' AS dt
  UNION ALL
  SELECT
    '2026-09-24'
), job_runs AS (
  SELECT
    job_runs.run_id,
    job_runs.job_id,
    job_runs.status,
    job_runs.duration_mins,
    job_runs.avg_retry_secs,
    job_runs.dt,
    CASE
      WHEN COALESCE(job_runs.status, '') <> '' AND COALESCE(job_runs.status, '') <> 'TEST'
      THEN 1
      ELSE 0
    END AS kept
  FROM ops.job_runs AS job_runs
), c AS (
  SELECT
    job_runs.dt,
    COUNT(*) AS runs,
    SUM(job_runs.duration_mins) AS total_duration_mins
  FROM job_runs
  WHERE
    job_runs.kept = 1
  GROUP BY
    job_runs.dt
)
SELECT
  d.dt,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM d
LEFT JOIN c
  ON d.dt = c.dt
```

## 2026-11-01 14:06:51, Statement with an Unchecked derived table

- Call: `unchecked_derived("d", ...)`
- Tables named: ops.job_runs, mart_dev.daily_runs
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH d AS (
  SELECT
    '2026-09-23' AS dt
  UNION ALL
  SELECT
    '2026-09-24'
), job_runs AS (
  SELECT
    job_runs.run_id,
    job_runs.job_id,
    job_runs.status,
    job_runs.duration_mins,
    job_runs.avg_retry_secs,
    job_runs.dt,
    CASE
      WHEN COALESCE(job_runs.status, '') <> '' AND COALESCE(job_runs.status, '') <> 'TEST'
      THEN 1
      ELSE 0
    END AS kept
  FROM ops.job_runs AS job_runs
), c AS (
  SELECT
    job_runs.dt,
    COUNT(*) AS runs,
    SUM(job_runs.duration_mins) AS total_duration_mins
  FROM job_runs
  WHERE
    job_runs.kept = 1
  GROUP BY
    job_runs.dt
)
INSERT OVERWRITE TABLE mart_dev.daily_runs
SELECT
  d.dt,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM d
LEFT JOIN c
  ON d.dt = c.dt
```

## 2026-11-01 14:06:58, Project action

- Call: `project.compare_batch("daily_runs")`
- Tables named: mart_dev.daily_runs
- Files: wrote tables/mart_dev__daily_runs/conversion/compare.md; moved admin/workflows/convert/daily_runs/ to admin/workflows/convert/finished/daily_runs/
- Script: a notebook, at commit nogit
- Result: worked
