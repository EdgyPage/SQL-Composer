# Admin log

Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or Unchecked derived table, and Project action the Toolbox has run, oldest first. The Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived tables are the list of what the Toolbox should learn to write next.

## 2026-11-06 01:28:24, Project action

- Call: `project.start()`
- Files: created admin/, references/, building_blocks/, tables/, warehouse.py
- Script: start_project.py, at commit nogit
- Result: worked

## 2026-11-06 01:30:10, Project action

- Call: `project.add_references(["ops.job_runs"], query=...)`
- Tables named: ops.job_runs
- Files: created references/ops__job_runs.py; wrote references/ops.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-06 01:30:23, Project action

- Call: `project.write_decisions(...)`
- Tables named: ops.job_runs
- Files: wrote references/ops__job_runs.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-06 01:30:41, Project action

- Call: `project.convert("run_log", ...)`
- Tables named: mart_dev.run_log
- Files: converted 1 script into 1 Saved table; wrote admin/workflows/convert/run_log/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-06 01:31:28, Project action

- Call: `project.new_run_value("period_end", latest_partition="ops.job_runs.dt")`
- Tables named: ops.job_runs
- Files: created building_blocks/run_values.py; registered building_blocks/run_values.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-06 01:31:29, Project action

- Call: `project.write_decisions(...)`
- Tables named: mart_dev.run_log
- Files: wrote references/mart_dev__run_log.py
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-06 01:31:29, Unchecked statement

- Call: `unchecked_hive("INSERT OVERWRITE TABLE mart_dev.run_log PARTITION (dt) SELECT * F" ...)`
- Tables named: mart_dev.run_log, mart.run_log
- Script: a notebook, at commit nogit
- Result: worked

```sql
INSERT OVERWRITE TABLE mart_dev.run_log PARTITION (dt) SELECT * FROM mart.run_log WHERE dt >= '2026-09-24'
```

## 2026-11-06 01:31:29, Unchecked statement

- Call: `unchecked_hive("INSERT INTO mart_dev.run_log PARTITION(dt) SELECT r.run_id, r.job" ...)`
- Tables named: mart_dev.run_log, ops.job_runs
- Script: a notebook, at commit nogit
- Result: worked

```sql
INSERT INTO mart_dev.run_log PARTITION(dt) SELECT r.run_id, r.job_id, r.dt FROM ops.job_runs AS r WHERE r.dt BETWEEN DATE_ADD('2026-09-24', 1 * -1) AND '2026-09-24' AND NOT r.run_id IN (SELECT l.run_id FROM mart_dev.run_log AS l)
```

## 2026-11-06 01:31:29, Project action

- Call: `project.compare_batch("run_log")`
- Tables named: mart_dev.run_log
- Files: wrote tables/mart_dev__run_log/conversion/compare.md; moved admin/workflows/convert/run_log/ to admin/workflows/convert/finished/run_log/
- Script: a notebook, at commit nogit
- Result: worked

## 2026-11-06 01:32:03, Project action

- Call: `project.compare_batch("run_log")`
- Tables named: mart_dev.run_log
- Files: wrote tables/mart_dev__run_log/conversion/compare.md
- Script: a notebook, at commit nogit
- Result: worked
