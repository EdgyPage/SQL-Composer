# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 17:13:58, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 17:14:51, Project action

- Call: `project.add_references(["ops.jobs", "ops.job_runs"], query=...)`
- Tables named: ops.jobs, ops.job_runs
- Files: created references/ops__jobs.py; created references/ops__job_runs.py; wrote references/ops.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 17:15:24, Project action

- Call: `project.write_decisions(...)`
- Files: none changed
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 17:18:44, Project action

- Call: `project.convert("team_report", ...)`
- Tables named: mart_dev.team_report
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/team_report/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 17:18:56, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.team_report
- Files: wrote references/mart_dev__team_report.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 17:19:16, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.team_report
- Files: none changed
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 17:19:16, Statement with an Unchecked derived table

- Call: `unchecked_derived("t", ...)`
- Tables named: ops.job_runs, ops.jobs, mart_dev.team_report
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH t AS (
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
    COUNT(*) AS runs,
    SUM(job_runs.duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY
    job_runs.team
)
INSERT OVERWRITE TABLE mart_dev.team_report
SELECT
  t.team,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM t
LEFT JOIN c
  ON t.team = c.team
```

## 2026-11-01 17:19:16, Project action

- Call: `project.compare_batch("team_report")`
- Tables named: mart_dev.team_report
- Files: wrote tables/mart_dev__team_report/conversion/compare.md; moved admin/workflows/convert/team_report/ to admin/workflows/convert/finished/team_report/
- Script: a notebook, at commit nogit
- Result: worked
