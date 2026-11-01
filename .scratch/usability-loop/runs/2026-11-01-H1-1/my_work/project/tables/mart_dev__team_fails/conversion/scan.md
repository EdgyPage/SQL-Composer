# Conversion mart_dev.team_fails

- 2 lines of Hive, one query reading ops.job_runs and ops.job_owners.
- Found:
  - line 1: its SET line is the Session settings HIVE_SETTINGS, which session_settings() gives
  - line 2: its INSERT OVERWRITE mart_dev.team_fails PARTITION(dt) becomes your own Saved table's write, INSERT_OVERWRITE(...), with the same partitions
- Opt-out added, marked # CONVERSION: at its line: FROM(r, reads_all_partitions=True)
- Opt-out added, marked # CONVERSION: at its line: FROM(o, reads_all_partitions=True)
- Opt-out added, marked # CONVERSION: at its line: JOIN(w, many_matches=True)
- Its Hive and the original's: The Statement's Hive and the original are the same query, once both are written out the same way.
