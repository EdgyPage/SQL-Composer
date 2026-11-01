# Conversion mart_dev.job_costs

- 1 line of Hive, one query reading ops.job_runs and ops.jobs.
- Found:
  - line 1: its INSERT OVERWRITE mart_dev.job_costs becomes your own Saved table's write, INSERT_OVERWRITE(...), with the same partitions
- Opt-out added, marked # CONVERSION: at its line: FROM(r, reads_all_partitions=True)
- Its Hive and the original's: The Statement's Hive and the original are the same query, once both are written out the same way.
