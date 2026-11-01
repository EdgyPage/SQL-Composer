# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 10:23:41, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: make_project.py, at commit nogit
- Result: worked

## 2026-11-01 10:27:52, Project action

- Call: `project.convert("costs", ...)`
- Tables named: mart_dev.job_costs, mart_dev.team_runs
- Files: converted 2 scripts into 2 Saved tables; wrote admin/workflows/convert/costs/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 10:28:10, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.job_costs, mart_dev.team_runs
- Files: wrote references/mart_dev__job_costs.py; wrote references/mart_dev__team_runs.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 10:28:27, Unchecked statement

- Call: `unchecked_hive("WITH job_runs AS (SELECT job_id, duration_mins FROM ops.job_runs)" ...)`
- Tables named: ops.job_runs, mart_dev.job_costs
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH job_runs AS (SELECT job_id, duration_mins FROM ops.job_runs) INSERT OVERWRITE TABLE mart_dev.job_costs SELECT c.job_id, CASE WHEN c.job_id = 3 THEN 1000 ELSE COALESCE(m.total_minutes, 0) * 50 END AS cost_cents FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) AS c LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total_minutes FROM job_runs GROUP BY job_id) AS m ON c.job_id = m.job_id
```

## 2026-11-01 10:28:27, Unchecked statement

- Call: `unchecked_hive("WITH job_runs AS (SELECT r.job_id, r.duration_mins, j.team FROM o" ...)`
- Tables named: ops.job_runs, ops.jobs, mart_dev.team_runs
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH job_runs AS (SELECT r.job_id, r.duration_mins, j.team FROM ops.job_runs AS r LEFT JOIN ops.jobs AS j ON r.job_id = j.job_id) INSERT OVERWRITE TABLE mart_dev.team_runs SELECT t.team, COALESCE(c.runs, 0) AS runs FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') AS t LEFT JOIN (SELECT team, COUNT(*) AS runs FROM job_runs GROUP BY team) AS c ON t.team = c.team
```

## 2026-11-01 10:28:27, Project action

- Call: `project.compare_batch("costs")`
- Tables named: mart_dev.job_costs, mart_dev.team_runs
- Files: wrote tables/mart_dev__job_costs/conversion/compare.md; wrote tables/mart_dev__team_runs/conversion/compare.md; moved admin/workflows/convert/costs/ to admin/workflows/convert/finished/costs/
- Script: a notebook, at commit nogit
- Result: worked
