# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 10:20:34, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: start.py, at commit nogit
- Result: worked

## 2026-11-01 10:20:59, Project action

- Call: `project.add_references(["ops.job_runs", "ops.job_owners"], query=...)`
- Tables named: ops.job_runs, ops.job_owners
- Files: created references/ops__job_runs.py; created references/ops__job_owners.py; wrote references/ops.py
- Script: step_refs.py, at commit nogit
- Result: worked

## 2026-11-01 10:21:59, Project action

- Call: `project.convert("weekly", ...)`
- Tables named: mart_dev.team_fails, mart_dev.job_runs_counted, mart_dev.job_fails_counted
- Files: converted 1 script into 3 Saved tables; wrote admin/workflows/convert/weekly/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 10:22:21, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.team_fails, mart_dev.job_runs_counted, mart_dev.job_fails_counted
- Files: wrote references/mart_dev__team_fails.py; wrote references/mart_dev__job_runs_counted.py; wrote references/mart_dev__job_fails_counted.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 10:22:45, Project action

- Call: `project.compare_batch("weekly")`
- Tables named: mart_dev.job_fails_counted, mart_dev.job_runs_counted, mart_dev.team_fails
- Files: wrote tables/mart_dev__job_fails_counted/conversion/compare.md; wrote tables/mart_dev__job_runs_counted/conversion/compare.md; wrote tables/mart_dev__team_fails/conversion/compare.md; moved admin/workflows/convert/weekly/ to admin/workflows/convert/finished/weekly/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 10:23:26, Project action

- Call: `project.promote(['mart_dev.team_fails', 'mart_dev.job_runs_counted', 'mart_dev.job_fails_counted'])`
- Tables named: team_prod.team_fails, team_prod.job_runs_counted, team_prod.job_fails_counted
- Files: wrote tables/team_prod__team_fails/ and references/team_prod__team_fails.py; wrote tables/team_prod__job_runs_counted/ and references/team_prod__job_runs_counted.py; wrote tables/team_prod__job_fails_counted/ and references/team_prod__job_fails_counted.py
- Script: a notebook, at commit nogit
- Result: worked
