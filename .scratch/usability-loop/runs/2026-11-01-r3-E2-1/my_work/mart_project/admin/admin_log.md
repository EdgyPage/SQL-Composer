# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 10:10:46, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 10:13:58, Project action

- Call: `project.convert("team_report", ...)`
- Tables named: mart_dev.team_report
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/team_report/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 10:14:10, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.team_report
- Files: wrote references/mart_dev__team_report.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 10:14:23, Unchecked statement

- Call: `unchecked_hive("WITH job_runs AS (SELECT r.duration_mins, j.team FROM ops.job_run" ...)`
- Tables named: ops.job_runs, ops.jobs, mart_dev.team_report
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH job_runs AS (SELECT r.duration_mins, j.team FROM ops.job_runs AS r LEFT JOIN ops.jobs AS j ON r.job_id = j.job_id), team_totals AS (SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins FROM job_runs GROUP BY team) INSERT OVERWRITE TABLE mart_dev.team_report SELECT t.team, COALESCE(s.runs, 0) AS runs, COALESCE(s.total_duration_mins, 0) AS total_duration_mins FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') AS t LEFT JOIN team_totals AS s ON t.team = s.team
```

## 2026-11-01 10:14:29, Project action

- Call: `project.compare_batch("team_report")`
- Tables named: mart_dev.team_report
- Files: wrote tables/mart_dev__team_report/conversion/compare.md; moved admin/workflows/convert/team_report/ to admin/workflows/convert/finished/team_report/
- Script: a notebook, at commit nogit
- Result: worked
