# Conversion mart_dev.job_run_report

- 1 line of Hive, one query reading ops.job_runs.
- Found:
  - line 1: its INSERT OVERWRITE mart_dev.job_run_report becomes your own Saved table's write, INSERT_OVERWRITE(...), with the same partitions
- Stopped: a refusal it couldn't add an opt-out for, first line: sum_of(1) was given 1 where a column goes.
