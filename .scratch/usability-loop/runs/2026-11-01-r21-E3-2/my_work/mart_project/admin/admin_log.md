# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 19:58:06, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: start_project.py, at commit nogit
- Result: worked

## 2026-11-01 19:58:50, Project action

- Call: `project.convert("daily_runs", ...)`
- Tables named: mart_dev.daily_runs
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/daily_runs/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 19:59:13, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.daily_runs
- Files: wrote references/mart_dev__daily_runs.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 19:59:43, Statement with an Unchecked derived table

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
), cleanruns AS (
  SELECT
    job_runs.run_id,
    job_runs.job_id,
    job_runs.status,
    job_runs.duration_mins,
    job_runs.avg_retry_secs,
    job_runs.dt
  FROM ops.job_runs AS job_runs
  WHERE
    NOT job_runs.status IS NULL AND job_runs.status <> 'TEST'
), c AS (
  SELECT
    cleanruns.dt,
    COUNT(*) AS runs,
    SUM(cleanruns.duration_mins) AS total_duration_mins
  FROM cleanruns
  GROUP BY
    cleanruns.dt
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

## 2026-11-01 19:59:50, Project action

- Call: `project.compare_batch("daily_runs")`
- Tables named: mart_dev.daily_runs
- Files: wrote tables/mart_dev__daily_runs/conversion/compare.md; moved admin/workflows/convert/daily_runs/ to admin/workflows/convert/finished/daily_runs/
- Script: a notebook, at commit nogit
- Result: worked
