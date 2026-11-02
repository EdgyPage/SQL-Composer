# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 19:44:13, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: start.py, at commit nogit
- Result: worked

## 2026-11-01 19:45:53, Project action

- Call: `project.convert("weekly_fails", ...)`
- Tables named: mart_dev.team_fails
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/weekly_fails/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 19:46:25, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.team_fails
- Files: wrote references/mart_dev__team_fails.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 19:47:05, Project action

- Call: `project.compare_batch("weekly_fails")`
- Tables named: mart_dev.team_fails
- Files: wrote tables/mart_dev__team_fails/conversion/compare.md; moved admin/workflows/convert/weekly_fails/ to admin/workflows/convert/finished/weekly_fails/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 19:47:45, Project action

- Call: `project.compare_batch("weekly_fails")`
- Tables named: mart_dev.team_fails
- Files: wrote tables/mart_dev__team_fails/conversion/compare.md
- Script: compare_other_partition.py, at commit nogit
- Result: worked
