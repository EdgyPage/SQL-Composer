# mart_dev.job_fails_counted against mart.job_fails_counted

Below, the Statement is mart_dev.job_fails_counted's rows, and the original mart.job_fails_counted's.

## dt = '2026-09-23'

Passed: compared on dt = '2026-09-23', the Partition you gave.
Compared at 2026-11-01 23:10:42.

The Statement and the original give the same rows where dt = '2026-09-23': 1 row each.
mart_dev.job_fails_counted: the key (job_id, dt) holds where job_fails_counted.dt = '2026-09-23'.


## dt = '2026-09-24'

Passed: compared on dt = '2026-09-24', the latest Partition both hold; 1 other Partition both tables hold was not compared: to compare one, give compare_batch partition={"dt": "..."}.
Compared at 2026-11-01 23:10:36.

The Statement and the original give the same rows where dt = '2026-09-24': 1 row each.
mart_dev.job_fails_counted: the key (job_id, dt) holds where job_fails_counted.dt = '2026-09-24'.
