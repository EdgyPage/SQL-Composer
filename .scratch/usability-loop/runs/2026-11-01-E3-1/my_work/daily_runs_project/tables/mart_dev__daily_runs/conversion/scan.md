# Conversion mart_dev.daily_runs

- 1 line of Hive, one query reading ops.job_runs.
- Found:
  - line 1: its INSERT OVERWRITE mart_dev.daily_runs becomes your own Saved table's write, INSERT_OVERWRITE(...), with the same partitions
  - line 1: GROUP BY dt WITH ROLLUP becomes GROUP_BY(rollup(cleanruns.dt)), which the Toolbox writes as the GROUPING SETS it stands for
- Opt-out added, marked # CONVERSION: at its line: FROM(job_runs, reads_all_partitions=True)
- Its Hive and the original's: The Statement's Hive and the original differ, once both are written out the same way: lines 1 to 15 match, and line 16 differs.
  - line 14, in both:          GROUP BY
  - line 15, in both:          dt
  - line 16, in the Statement: GROUPING SETS (
  - line 16, in the original:  WITH ROLLUP
