# mart_dev.run_log against mart.run_log

Below, the Statement is mart_dev.run_log's rows, and the original mart.run_log's.

## dt = '2026-09-23'

Passed: compared on dt = '2026-09-23', the Partition you gave.
Compared at 2026-11-06 01:32:03.

The Statement and the original give the same rows where dt = '2026-09-23': 5 rows each.
mart_dev.run_log: the key (run_id) holds where run_log.dt = '2026-09-23'.


## dt = '2026-09-24'

Passed: compared on dt = '2026-09-24', the latest Partition both hold.
Compared at 2026-11-06 01:32:03.

The Statement and the original give the same rows where dt = '2026-09-24': 4 rows each.
mart_dev.run_log: the key (run_id) holds where run_log.dt = '2026-09-24'.
