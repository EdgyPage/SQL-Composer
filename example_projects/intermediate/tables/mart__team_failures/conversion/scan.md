# Conversion mart.team_failures

- 1 line of Hive, one query reading ops.job_events and ops.job_owners.
- Found:
  - line 1: its INSERT OVERWRITE mart.team_failures PARTITION(dt) becomes your own Saved table's write, INSERT_OVERWRITE(...), with the same partitions
  - line 1: the IN list of 4 values is the constant EVENT_TYPE_VALUES
  - line 1: the CASE on p.team is the constant TEAM_NAME_BY_TEAM
- Opt-out added, marked # CONVERSION: at its line: JOIN(o, reads_all_partitions=True)
- Its Hive and the original's: The Statement's Hive and the original are the same query, once both are written out the same way.
