# Conversion mart_dev.failed_runs

- 4 lines of Hive, one query reading ops.job_runs.
- Found:
  - the query becomes your own Saved table's write, INSERT_OVERWRITE(...)
- Opt-out added, marked # CONVERSION: at its line: FROM(r, reads_all_partitions=True)
- Its Hive and the original's: The Statement's Hive and the original are the same query, once both are written out the same way.
