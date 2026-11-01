# Conversion mart_dev.team_runs

- 1 line of Hive, one query reading ops.job_runs and ops.jobs.
- Found:
  - line 1: its INSERT OVERWRITE mart_dev.team_runs becomes your own Saved table's write, INSERT_OVERWRITE(...), with the same partitions
- Opt-out added, marked # CONVERSION: at its line: LEFT_JOIN(j, many_matches=True)
- Opt-out added, marked # CONVERSION: at its line: FROM(r, reads_all_partitions=True)
- Its Hive and the original's: The Statement's Hive and the original differ, once both are written out the same way: line 1 differs.
  - line 1, in the Statement: WITH teams AS (
  - line 1, in the original:  WITH runs AS (
