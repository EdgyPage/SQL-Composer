# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 01:35:11, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 01:35:58, Project action

- Call: `project.add_references(["ops.jobs", "ops.job_runs"], query=...)`
- Tables named: ops.jobs, ops.job_runs
- Files: created references/ops__jobs.py; created references/ops__job_runs.py; wrote references/ops.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 01:35:58, Project action

- Call: `project.write_decisions(...)`
- Files: none changed
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 01:36:32, Project action

- Call: `project.write_decisions(...)`
- Tables named: ops.jobs, ops.job_runs
- Files: wrote references/ops__jobs.py; wrote references/ops__job_runs.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 01:40:41, Project action

- Call: `project.convert("team_report", ...)`
- Tables named: mart_dev.team_report
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/team_report/
- Script: cell 5, at commit nogit
- Result: worked

## 2026-11-01 01:41:03, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.team_report
- Files: wrote references/mart_dev__team_report.py
- Script: cell 8, at commit nogit
- Result: worked

## 2026-11-01 01:41:18, Statement with an Unchecked derived table

- Call: `unchecked_derived("team_keys", ...)`
- Tables named: ops.job_runs, ops.jobs, mart_dev.team_report
- Script: cell 14, at commit nogit
- Result: worked

```sql
WITH team_keys AS (
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
)
INSERT OVERWRITE TABLE mart_dev.team_report
SELECT
  k.team,
  COUNT(jr.run_id) AS runs,
  COALESCE(SUM(jr.duration_mins), 0) AS total_duration_mins
FROM team_keys AS k
LEFT JOIN job_runs AS jr
  ON jr.team = k.team
GROUP BY
  k.team
```

## 2026-11-01 01:41:23, Project action

- Call: `project.compare_batch("team_report")`
- Tables named: mart_dev.team_report
- Files: wrote tables/mart_dev__team_report/conversion/compare.md; moved admin/workflows/convert/team_report/ to admin/workflows/convert/finished/team_report/
- Script: cell 16, at commit nogit
- Result: worked

## 2026-11-01 01:41:29, Project action

- Call: `project.compare_batch("team_report")`
- Tables named: mart_dev.team_report
- Files: wrote tables/mart_dev__team_report/conversion/compare.md
- Script: a notebook, at commit nogit
- Result: worked
