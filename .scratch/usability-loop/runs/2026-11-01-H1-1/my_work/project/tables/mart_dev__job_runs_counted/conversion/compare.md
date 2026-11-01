# mart_dev.job_runs_counted against mart.job_runs_counted

Below, the Statement is mart_dev.job_runs_counted's rows, and the original mart.job_runs_counted's.

Passed: compared on dt = '2026-09-24', the latest Partition both hold.
Compared at 2026-11-01 01:39:00.

The Statement and the original give the same rows where dt = '2026-09-24': 3 rows each.
mart_dev.job_runs_counted: the key (job_id, dt) holds where job_runs_counted.dt = '2026-09-24'.
