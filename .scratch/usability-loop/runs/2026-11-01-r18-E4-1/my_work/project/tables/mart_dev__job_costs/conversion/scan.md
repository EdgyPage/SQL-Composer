# Conversion mart_dev.job_costs

- 10 lines of Hive, one query reading ops.job_runs and ops.jobs.
- Found:
  - the query becomes your own Saved table's write, INSERT_OVERWRITE(...)
  - the sub-query j, rows typed in, stays Hive, in unchecked_derived(...), which the Toolbox writes at the top, as WITH j AS (...): no Statement lists rows typed in, and its Key is the one its rows show
  - the sub-query c becomes a Derived table, which the Toolbox writes at the top, as WITH c AS (...)
- Opt-out added, marked # CONVERSION: at its line: LEFT_JOIN(j, many_matches=True)
- Opt-out added, marked # CONVERSION: at its line: FROM(r, reads_all_partitions=True)
- Its Hive and the original's: The Statement's Hive and the original differ, once both are written out the same way: line 1 differs.
  - line 1, in the Statement: WITH j AS (
  - line 1, in the original:  WITH job_runs AS (
