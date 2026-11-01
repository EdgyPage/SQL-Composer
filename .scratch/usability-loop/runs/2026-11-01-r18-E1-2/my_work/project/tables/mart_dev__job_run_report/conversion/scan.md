# Conversion mart_dev.job_run_report

- 13 lines of Hive, one query reading ops.job_runs.
- Found:
  - the query becomes your own Saved table's write, INSERT_OVERWRITE(...)
  - the sub-query j, rows typed in, stays Hive, in unchecked_derived(...), which the Toolbox writes at the top, as WITH j AS (...): no Statement lists rows typed in, and its Key is the one its rows show
  - the sub-query r becomes a Derived table, which the Toolbox writes at the top, as WITH r AS (...)
  - the sub-query f becomes a Derived table, which the Toolbox writes at the top, as WITH f AS (...)
  - the sub-query a becomes a Derived table, which the Toolbox writes at the top, as WITH a AS (...)
- Opt-out added, marked # CONVERSION: at its line: FROM(job_runs, reads_all_partitions=True)
- Opt-out added, marked # CONVERSION: at its line: FROM(job_runs, reads_all_partitions=True)
- Opt-out added, marked # CONVERSION: at its line: FROM(job_runs, reads_all_partitions=True)
- Its Hive and the original's: The Statement's Hive and the original are the same query, once both are written out the same way.
