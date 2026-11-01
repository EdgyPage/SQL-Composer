# Conversion mart_dev.job_run_report

- 17 lines of Hive, one query reading ops.job_runs.
- Found:
  - the query becomes your own Saved table's write, INSERT_OVERWRITE(...)
- Opt-out added, marked # CONVERSION: at its line: FROM(job_runs, reads_all_partitions=True)
- Opt-out added, marked # CONVERSION: at its line: FROM(job_runs, reads_all_partitions=True)
- Its Hive and the original's: The Statement's Hive and the original are the same query, once both are written out the same way.
