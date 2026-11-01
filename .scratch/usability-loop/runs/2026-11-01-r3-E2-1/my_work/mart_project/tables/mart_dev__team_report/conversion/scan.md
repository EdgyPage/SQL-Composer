# Conversion mart_dev.team_report

- 19 lines of Hive, one query reading ops.job_runs and ops.jobs.
- Found:
  - the query becomes your own Saved table's write, INSERT_OVERWRITE(...)
  - the whole query stays an Unchecked statement, unchecked_hive(...): a SELECT with no FROM, which statement(...) needs
- Not compared: the whole query stays Hive, as an Unchecked statement, so its Hive is the original's, as written.
