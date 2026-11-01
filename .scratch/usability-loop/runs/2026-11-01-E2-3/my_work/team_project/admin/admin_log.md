# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 01:40:00, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: start.py, at commit nogit
- Result: worked

## 2026-11-01 01:43:48, Project action

- Call: `project.convert("team_report", ...)`
- Tables named: mart_dev.team_report
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/team_report/
- Script: run_convert.py, at commit nogit
- Result: worked

## 2026-11-01 01:44:05, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.team_report
- Files: wrote references/mart_dev__team_report.py
- Script: run_decisions.py, at commit nogit
- Result: worked

## 2026-11-01 01:44:14, Unchecked statement

- Call: `unchecked_hive("WITH job_runs AS (SELECT r.run_id, r.job_id, r.status, r.duration" ...)`
- Tables named: ops.job_runs, ops.jobs, mart_dev.team_report
- Script: run_steps.py, at commit nogit
- Result: worked

```sql
WITH job_runs AS (SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team FROM ops.job_runs AS r LEFT JOIN ops.jobs AS j ON r.job_id = j.job_id), per_team AS (SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins FROM job_runs GROUP BY team) INSERT OVERWRITE TABLE mart_dev.team_report SELECT t.team, COALESCE(p.runs, 0) AS runs, COALESCE(p.total_duration_mins, 0) AS total_duration_mins FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') AS t LEFT JOIN per_team AS p ON t.team = p.team
```

## 2026-11-01 01:44:15, Project action

- Call: `project.compare_batch("team_report")`
- Tables named: mart_dev.team_report
- Files: wrote tables/mart_dev__team_report/conversion/compare.md; moved admin/workflows/convert/team_report/ to admin/workflows/convert/finished/team_report/
- Script: run_steps.py, at commit nogit
- Result: worked
