<!-- sqlglot Composer 7.2 - copy it, then edit your copy -->
# Conversion team_failures

- 21 lines of Hive, one query reading ops.job_events and ops.job_owners.
- Found:
  - line 6: the IN list of 4 values is the constant EVENT_TYPE_VALUES
  - line 15: its INSERT OVERWRITE ops_reports.team_failures PARTITION(dt) becomes your own Saved table's write, INSERT_OVERWRITE(...), with the same partitions
  - line 17: the CASE on p.team is the constant TEAM_NAME_BY_TEAM
- Opt-out added, marked # CONVERSION: at its line: JOIN(o, reads_all_partitions=True)
- Its Hive and the original's: The Statement's Hive and the original are the same query, once both are written out the same way.
