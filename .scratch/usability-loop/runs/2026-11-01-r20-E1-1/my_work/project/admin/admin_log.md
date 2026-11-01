# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 17:10:03, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: start_project.py, at commit nogit
- Result: worked

## 2026-11-01 17:23:54, Project action

- Call: `project.convert("job_run_report", ...)`
- Tables named: mart_dev.job_run_report
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/job_run_report/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 17:24:06, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.job_run_report
- Files: wrote references/mart_dev__job_run_report.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 17:24:27, Statement with an Unchecked derived table

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
), r AS (
  SELECT
    job_runs.job_id,
    COUNT(*) AS runs,
    COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) AS failed_runs,
    AVG(job_runs.duration_mins) AS avg_duration_mins
  FROM ops.job_runs AS job_runs
  GROUP BY
    job_runs.job_id
)
INSERT OVERWRITE TABLE mart_dev.job_run_report
SELECT
  j.job_id,
  COALESCE(r.runs, 0) AS runs,
  COALESCE(r.failed_runs, 0) AS failed_runs,
  r.avg_duration_mins
FROM j
LEFT JOIN r
  ON j.job_id = r.job_id
```

## 2026-11-01 17:24:27, Project action

- Call: `project.compare_batch("job_run_report")`
- Tables named: mart_dev.job_run_report
- Files: wrote tables/mart_dev__job_run_report/conversion/compare.md; moved admin/workflows/convert/job_run_report/ to admin/workflows/convert/finished/job_run_report/
- Script: a notebook, at commit nogit
- Result: worked
