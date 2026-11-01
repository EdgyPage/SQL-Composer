# Conversion mart_dev.job_run_report

- 6 lines of Hive, one query reading ops.job_runs.
- Found:
  - the query becomes your own Saved table's write, INSERT_OVERWRITE(...)
- Opt-out added, marked # CONVERSION: at its line: FROM(r, reads_all_partitions=True)
- Its Hive and the original's: The Statement's Hive and the original differ, once both are written out the same way: lines 1 to 3 match, and line 4 differs.
  - line 2, in both:          job_id,
  - line 3, in both:          COALESCE(COUNT(*), 0) AS runs,
  - line 4, in the Statement: COALESCE(COUNT(CASE WHEN status = 'FAILED' THEN 1 ELSE NULL END), 0) AS failed_runs,
  - line 4, in the original:  COALESCE(COUNT(CASE WHEN status = 'FAILED' THEN 1 END), 0) AS failed_runs,
