# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-01 09:22:04, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 09:22:34, Project action

- Call: `project.add_references(["ops.job_runs"], query=...)`
- Tables named: ops.job_runs
- Files: created references/ops__job_runs.py; wrote references/ops.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 09:22:52, Project action

- Call: `project.new_table("mart_dev.runs_per_day")`
- Tables named: mart_dev.runs_per_day
- Files: created tables/mart_dev__runs_per_day/ (mart_dev__runs_per_day.ipynb, lineage/); created references/mart_dev__runs_per_day.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 09:23:11, Project action

- Call: `project.reference_from_logic("mart_dev.runs_per_day")`
- Tables named: mart_dev.runs_per_day
- Files: wrote references/mart_dev__runs_per_day.py from its logic
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 09:23:31, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.runs_per_day
- Files: wrote references/mart_dev__runs_per_day.py
- Script: a notebook, at commit nogit
- Result: worked
