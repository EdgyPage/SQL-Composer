# mart_dev.daily_runs against its query, in conversion/statement.hql

Below, the Statement is mart_dev.daily_runs's rows, and the original its query's.

Failed: every row: it has no Partitions.
Compared at 2026-11-01 07:35:03.

The Statement and the original give different rows.
  The Statement gives 2 rows, and the original 3.
  0 rows are in the Statement and not in the original, and 1 row is in the original and not in the Statement.
The rows that differ, at most 5 from each, with how many times each gives them:
  dt  runs  total_duration_mins  in_statement  in_original
None     7                  160             0            1
