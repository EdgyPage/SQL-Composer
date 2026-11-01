# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-09-25 06:00:00, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-09-25 06:00:00, Project action

- Call: `project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"], query=...)`
- Tables named: ops.jobs, ops.job_runs, ops.run_alerts
- Files: created references/ops__jobs.py; created references/ops__job_runs.py; created references/ops__run_alerts.py; wrote references/ops.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-09-25 06:00:00, Project action

- Call: `project.new_block("runs_per_job")`
- Files: created building_blocks/runs_per_job.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-09-25 06:00:00, Project action

- Call: `project.new_table("mart.alerts_per_severity")`
- Tables named: mart.alerts_per_severity
- Files: created tables/mart__alerts_per_severity/ (mart__alerts_per_severity.ipynb, lineage/); created references/mart__alerts_per_severity.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-09-25 06:00:00, Project action

- Call: `project.new_table("mart.daily_job_runs")`
- Tables named: mart.daily_job_runs
- Files: created tables/mart__daily_job_runs/ (mart__daily_job_runs.ipynb, lineage/); created references/mart__daily_job_runs.py; wrote references/mart.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-09-25 06:00:00, Project action

- Call: `project.new_table("mart.alerts_per_job")`
- Tables named: mart.alerts_per_job
- Files: created tables/mart__alerts_per_job/ (mart__alerts_per_job.ipynb, lineage/); created references/mart__alerts_per_job.py; wrote references/mart.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-09-25 06:00:00, Project action

- Call: `project.new_table("mart.team_day")`
- Tables named: mart.team_day
- Files: created tables/mart__team_day/ (mart__team_day.ipynb, lineage/); created references/mart__team_day.py; wrote references/mart.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 13:52:21, Project action

- Call: `project.upgrade()`
- Files: rewrote admin/workflows/convert/convert.ipynb; rewrote admin/workflows/promote/promote.ipynb; rewrote admin/workflows/new_table/new_table.ipynb; rewrote admin/workflows/references/references.ipynb; rewrote admin/workflows/upgrade/upgrade.ipynb; rewrote admin/workflows/change_a_saved_table/change_a_saved_table.ipynb; rewrote admin/templates/saved_table.py; rewrote admin/templates/quality_checks.py; rewrote admin/templates/saved_table_reference.py; wrote admin/upgrade_8.1.md; wrote admin/project_version.txt: 8.1
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-01 13:52:21, Project action

- Call: `project.upgrade()`
- Files: added a cell writing its Hive, export_hive(), after the lineage cell of tables/mart__alerts_per_job/mart__alerts_per_job.ipynb: run it to write mart__alerts_per_job.hql beside it; added a cell writing its Hive, export_hive(), after the lineage cell of tables/mart__alerts_per_severity/mart__alerts_per_severity.ipynb: run it to write mart__alerts_per_severity.hql beside it; added a cell writing its Hive, export_hive(), after the lineage cell of tables/mart__daily_job_runs/mart__daily_job_runs.ipynb: run it to write mart__daily_job_runs.hql beside it; added a cell writing its Hive, export_hive(), after the lineage cell of tables/mart__team_day/mart__team_day.ipynb: run it to write mart__team_day.hql beside it; rewrote admin/workflows/convert/convert.ipynb; rewrote admin/workflows/promote/promote.ipynb; rewrote admin/workflows/new_table/new_table.ipynb; rewrote admin/workflows/references/references.ipynb; rewrote admin/workflows/upgrade/upgrade.ipynb; rewrote admin/workflows/change_a_saved_table/change_a_saved_table.ipynb; wrote admin/upgrade_8.2.md; wrote admin/project_version.txt: 8.2
- Script: a notebook, at commit nogit
- Result: worked
