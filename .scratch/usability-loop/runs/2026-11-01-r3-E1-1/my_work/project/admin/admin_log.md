# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 10:11:24, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 10:11:58, Project action

- Call: `project.convert("job_run_report", ...)`
- Tables named: mart_dev.job_run_report
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/job_run_report/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 10:12:34, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.job_run_report
- Files: wrote references/mart_dev__job_run_report.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 10:12:49, Project action

- Call: `project.compare_batch("job_run_report")`
- Tables named: mart_dev.job_run_report
- Files: wrote tables/mart_dev__job_run_report/conversion/compare.md; moved admin/workflows/convert/job_run_report/ to admin/workflows/convert/finished/job_run_report/
- Script: a notebook, at commit nogit
- Result: worked
