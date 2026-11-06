# mart_dev.run_log against mart.run_log

Below, the Statement is mart_dev.run_log's rows, and the original mart.run_log's.

## dt = '2026-09-24'

Passed: compared on dt = '2026-09-24', the latest Partition both hold; 1 other Partition both tables hold was not compared: to compare one, set PARTITION = {"dt": "..."} in the convert notebook's names cell, run it, and run step 7 again.
Compared at 2026-11-05 19:14:58.

The Statement and the original give the same rows where dt = '2026-09-24': 4 rows each.
mart_dev.run_log: the key (run_id) holds where run_log.dt = '2026-09-24'.
