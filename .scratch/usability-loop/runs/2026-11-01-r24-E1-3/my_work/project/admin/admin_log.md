# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 23:18:00, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 23:18:40, Project action

- Call: `project.convert("job_run_report", ...)`
- Tables named: mart_dev.job_run_report
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/job_run_report/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 23:18:56, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.job_run_report
- Files: wrote references/mart_dev__job_run_report.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 23:19:31, Statement with an Unchecked derived table

- Call: `unchecked_derived("j", ...)`
- Tables named: ops.job_runs, mart_dev.job_run_report
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH j AS (
  SELECT
    1 AS job_id
  UNION ALL
  SELECT
    2
  UNION ALL
  SELECT
    3
), c AS (
  SELECT
    job_runs.job_id,
    COUNT(*) AS runs
  FROM ops.job_runs AS job_runs
  GROUP BY
    job_runs.job_id
), f AS (
  SELECT
    job_runs.job_id,
    COUNT(*) AS failed_runs
  FROM ops.job_runs AS job_runs
  WHERE
    job_runs.status = 'FAILED'
  GROUP BY
    job_runs.job_id
), a AS (
  SELECT
    job_runs.job_id,
    AVG(job_runs.duration_mins) AS avg_duration_mins
  FROM ops.job_runs AS job_runs
  GROUP BY
    job_runs.job_id
)
INSERT OVERWRITE TABLE mart_dev.job_run_report
SELECT
  j.job_id,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(f.failed_runs, 0) AS failed_runs,
  a.avg_duration_mins
FROM j
LEFT JOIN c
  ON j.job_id = c.job_id
LEFT JOIN f
  ON j.job_id = f.job_id
LEFT JOIN a
  ON j.job_id = a.job_id
```

## 2026-11-01 23:19:40, Project action

- Call: `project.compare_batch("job_run_report")`
- Tables named: mart_dev.job_run_report
- Files: wrote tables/mart_dev__job_run_report/conversion/compare.md; moved admin/workflows/convert/job_run_report/ to admin/workflows/convert/finished/job_run_report/
- Script: a notebook, at commit nogit
- Result: worked
