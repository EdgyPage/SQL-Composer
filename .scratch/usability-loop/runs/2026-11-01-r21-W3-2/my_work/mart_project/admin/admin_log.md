# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 19:44:02, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: start_project.py, at commit nogit
- Result: worked

## 2026-11-01 19:45:35, Project action

- Call: `project.convert("failed_runs", ...)`
- Tables named: mart_dev.failed_runs
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/failed_runs/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 19:46:01, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.failed_runs
- Files: wrote references/mart_dev__failed_runs.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 19:47:36, Project action

- Call: `project.compare_batch("failed_runs")`
- Tables named: mart_dev.failed_runs
- Files: wrote tables/mart_dev__failed_runs/conversion/compare.md; moved admin/workflows/convert/failed_runs/ to admin/workflows/convert/finished/failed_runs/
- Script: a notebook, at commit nogit
- Result: worked
