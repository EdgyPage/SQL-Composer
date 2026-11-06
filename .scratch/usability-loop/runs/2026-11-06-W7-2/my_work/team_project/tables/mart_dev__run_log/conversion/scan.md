# Conversion mart_dev.run_log

- 5 lines of Hive, one query reading ops.job_runs and mart_dev.run_log.
- Found:
  - line 1: its SET line is the Session settings HIVE_SETTINGS, which session_settings() gives
  - line 2: its INSERT INTO mart_dev.run_log PARTITION(dt) becomes your own Saved table's write, INSERT_INTO(...), with the same partitions
  - line 2: the whole query stays an Unchecked statement, unchecked_hive(...): no condition function writes IN (SELECT ...): SEMI_JOIN(...) writes it as a join; and an Unchecked expression can't hold it, as it reads a table of its own
  - run_log.hql, line 6: <PARM="PERIOD_END"/>, a Script tag, bare. Answer it under "tags" in the decisions cell of admin/workflows/convert/convert.ipynb: project.write_decisions writes it into TAGS, in the table's Table reference, and until then the table isn't created.
  - run_log.hql, line 6: <PARM="PERIOD_END"/>, a Script tag, bare. Answer it under "tags" in the decisions cell of admin/workflows/convert/convert.ipynb: project.write_decisions writes it into TAGS, in the table's Table reference, and until then the table isn't created.
- Not compared: the whole query stays Hive, as an Unchecked statement, so its Hive is the original's, as written.
