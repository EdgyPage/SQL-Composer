# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 09:31:11, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: start.py, at commit nogit
- Result: worked

## 2026-11-01 09:31:59, Project action

- Call: `project.add_references(["ops.jobs", "ops.job_runs"], query=...)`
- Tables named: ops.jobs, ops.job_runs
- Files: created references/ops__jobs.py; created references/ops__job_runs.py; wrote references/ops.py
- Script: _add_refs_tmp.py, at commit nogit
- Result: worked

## 2026-11-01 09:35:29, Project action

- Call: `project.convert("team_report", ...)`
- Tables named: mart_dev.team_report
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/team_report/
- Script: convert_team.py, at commit nogit
- Result: worked

## 2026-11-01 09:35:51, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.team_report
- Files: wrote references/mart_dev__team_report.py
- Script: write_dec.py, at commit nogit
- Result: worked

## 2026-11-01 09:36:23, Statement with an Unchecked derived table

- Call: `unchecked_derived("team_names", ...)`
- Tables named: ops.job_runs, ops.jobs
- Script: preview_team.py, at commit nogit
- Result: worked

```sql
WITH team_names AS (
  SELECT
    'data' AS team
  UNION ALL
  SELECT
    'finance'
  UNION ALL
  SELECT
    'web'
), runs_with_team AS (
  SELECT
    r.job_id,
    r.duration_mins,
    j.team
  FROM ops.job_runs AS r
  LEFT JOIN ops.jobs AS j
    ON r.job_id = j.job_id
), totals AS (
  SELECT
    runs_with_team.team,
    COUNT(*) AS runs,
    SUM(runs_with_team.duration_mins) AS total_duration_mins
  FROM runs_with_team
  GROUP BY
    runs_with_team.team
)
SELECT
  n.team,
  COALESCE(t.runs, 0) AS runs,
  COALESCE(t.total_duration_mins, 0) AS total_duration_mins
FROM team_names AS n
LEFT JOIN totals AS t
  ON n.team = t.team
```

## 2026-11-01 09:36:37, Statement with an Unchecked derived table

- Call: `unchecked_derived("team_names", ...)`
- Tables named: ops.job_runs, ops.jobs, mart_dev.team_report
- Script: write_team.py, at commit nogit
- Result: worked

```sql
WITH team_names AS (
  SELECT
    'data' AS team
  UNION ALL
  SELECT
    'finance'
  UNION ALL
  SELECT
    'web'
), runs_with_team AS (
  SELECT
    r.job_id,
    r.duration_mins,
    j.team
  FROM ops.job_runs AS r
  LEFT JOIN ops.jobs AS j
    ON r.job_id = j.job_id
), totals AS (
  SELECT
    runs_with_team.team,
    COUNT(*) AS runs,
    SUM(runs_with_team.duration_mins) AS total_duration_mins
  FROM runs_with_team
  GROUP BY
    runs_with_team.team
)
INSERT OVERWRITE TABLE mart_dev.team_report
SELECT
  n.team,
  COALESCE(t.runs, 0) AS runs,
  COALESCE(t.total_duration_mins, 0) AS total_duration_mins
FROM team_names AS n
LEFT JOIN totals AS t
  ON n.team = t.team
```

## 2026-11-01 09:36:42, Project action

- Call: `project.compare_batch("team_report")`
- Tables named: mart_dev.team_report
- Files: wrote tables/mart_dev__team_report/conversion/compare.md; moved admin/workflows/convert/team_report/ to admin/workflows/convert/finished/team_report/
- Script: compare_team.py, at commit nogit
- Result: worked
