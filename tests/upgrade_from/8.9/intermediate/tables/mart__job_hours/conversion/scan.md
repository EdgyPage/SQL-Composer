# Conversion mart.job_hours

- 28 lines of Hive, one query reading ops.job_events and ops.job_owners.
- Found:
  - the query becomes your own Saved table's write, INSERT_OVERWRITE(...)
- Opt-out added, marked # CONVERSION: at its line: FROM(job_events, reads_all_partitions=True)
- Opt-out added, marked # CONVERSION: at its line: LEFT_JOIN(o, reads_all_partitions=True)
- Opt-out added, marked # CONVERSION: at its line: sum_of(run_hours.hours, adds_up=True)
- Its Hive and the original's: The Statement's Hive and the original are the same query, once both are written out the same way.
