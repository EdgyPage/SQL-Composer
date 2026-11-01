# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 09:30:43, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 09:34:36, Project action

- Call: `project.convert("team_report", ...)`
- Tables named: mart_dev.team_report
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/team_report/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 09:35:14, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.team_report
- Files: wrote references/mart_dev__team_report.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 09:35:31, Statement with an Unchecked derived table

- Call: `unchecked_derived("listed", ...)`
- Tables named: ops.job_runs, ops.jobs
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH listed AS (
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
    r.duration_mins,
    j.team
  FROM ops.job_runs AS r
  LEFT JOIN ops.jobs AS j
    ON r.job_id = j.job_id
), summary AS (
  SELECT
    job_runs.team,
    COUNT(*) AS runs,
    SUM(job_runs.duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY
    job_runs.team
)
SELECT
  l.team,
  COALESCE(s.runs, 0) AS runs,
  COALESCE(s.total_duration_mins, 0) AS total_duration_mins
FROM listed AS l
LEFT JOIN summary AS s
  ON l.team = s.team
```

## 2026-11-01 09:36:01, Statement with an Unchecked derived table

- Call: `unchecked_derived("listed", ...)`
- Tables named: ops.job_runs, ops.jobs, mart_dev.team_report
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH listed AS (
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
    r.duration_mins,
    j.team
  FROM ops.job_runs AS r
  LEFT JOIN ops.jobs AS j
    ON r.job_id = j.job_id
), summary AS (
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
  l.team,
  COALESCE(s.runs, 0) AS runs,
  COALESCE(s.total_duration_mins, 0) AS total_duration_mins
FROM listed AS l
LEFT JOIN summary AS s
  ON l.team = s.team
```

## 2026-11-01 09:36:09, Project action

- Call: `project.compare_batch("team_report")`
- Tables named: mart_dev.team_report
- Files: wrote tables/mart_dev__team_report/conversion/compare.md; moved admin/workflows/convert/team_report/ to admin/workflows/convert/finished/team_report/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 09:36:27, Project action

- Call: `project.promote(['mart_dev.team_report'])`
- Tables named: team_prod.team_report
- Files: wrote tables/team_prod__team_report/ and references/team_prod__team_report.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 09:36:45, Statement with an Unchecked derived table

- Call: `unchecked_derived("listed", ...)`
- Tables named: ops.job_runs, ops.jobs, team_prod.team_report
- Script: a notebook, at commit nogit
- Result: worked

```sql
WITH listed AS (
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
    r.duration_mins,
    j.team
  FROM ops.job_runs AS r
  LEFT JOIN ops.jobs AS j
    ON r.job_id = j.job_id
), summary AS (
  SELECT
    job_runs.team,
    COUNT(*) AS runs,
    SUM(job_runs.duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY
    job_runs.team
)
INSERT OVERWRITE TABLE team_prod.team_report
SELECT
  l.team,
  COALESCE(s.runs, 0) AS runs,
  COALESCE(s.total_duration_mins, 0) AS total_duration_mins
FROM listed AS l
LEFT JOIN summary AS s
  ON l.team = s.team
```
