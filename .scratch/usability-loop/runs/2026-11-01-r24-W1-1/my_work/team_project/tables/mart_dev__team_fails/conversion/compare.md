# mart_dev.team_fails against mart.team_fails

Below, the Statement is mart_dev.team_fails's rows, and the original mart.team_fails's.

## dt = '2026-09-23'

Passed: compared on dt = '2026-09-23', the Partition you gave.
Compared at 2026-11-01 23:10:29.

The Statement and the original give the same rows where dt = '2026-09-23': 2 rows each.
mart_dev.team_fails: the key (team, dt) holds where team_fails.dt = '2026-09-23'.


## dt = '2026-09-24'

Passed: compared on dt = '2026-09-24', the latest Partition both hold; 1 other Partition both tables hold was not compared: to compare one, give compare_batch partition={"dt": "..."}.
Compared at 2026-11-01 23:10:12.

The Statement and the original give the same rows where dt = '2026-09-24': 1 row each.
mart_dev.team_fails: the key (team, dt) holds where team_fails.dt = '2026-09-24'.
