# Conversion mart_dev.team_report

- 20 lines of Hive, one query reading ops.job_runs and ops.jobs.
- Found:
  - the query becomes your own Saved table's write, INSERT_OVERWRITE(...)
  - the CTE listed stays Hive, in unchecked_derived(...): a SELECT with no FROM, which statement(...) needs
- Opt-out added, marked # CONVERSION: at its line: LEFT_JOIN(j, many_matches=True)
- Opt-out added, marked # CONVERSION: at its line: FROM(r, reads_all_partitions=True)
- Its Hive and the original's: The Statement's Hive and the original differ, once both are written out the same way: line 1 differs.
  - line 1, in the Statement: WITH listed AS (
  - line 1, in the original:  WITH job_runs AS (
