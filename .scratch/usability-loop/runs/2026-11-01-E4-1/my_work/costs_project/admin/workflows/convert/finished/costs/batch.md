# Batch costs

2 scripts, kept as given in scripts/: job_costs.hql and team_runs.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- default.job_costs: mart_dev.job_costs, tables/mart_dev__job_costs/, its checklist tables/mart_dev__job_costs/conversion/checklist.md
  - # CONVERSION: FROM(r, reads_all_partitions=True), a note on its checklist
- default.team_runs: mart_dev.team_runs, tables/mart_dev__team_runs/, its checklist tables/mart_dev__team_runs/conversion/checklist.md
  - # CONVERSION: LEFT_JOIN(j, many_matches=True), a note on its checklist
  - # CONVERSION: FROM(r, reads_all_partitions=True), a note on its checklist

## Each statement, in the order they run

1. job_costs.hql line 1, `WITH runs AS ( SELECT r.job_id, r.duration_mins FROM ops.job_runs r ), run_to...`: mart_dev.job_costs, written by its notebook
2. team_runs.hql line 1, `WITH runs AS ( SELECT r.job_id, r.duration_mins, j.team FROM ops.job_runs r L...`: mart_dev.team_runs, written by its notebook
