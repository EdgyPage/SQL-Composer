# Batch costs

2 scripts, kept as given in scripts/: job_costs.hql and team_runs.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- mart_dev.job_costs, from its query: tables/mart_dev__job_costs/, its checklist tables/mart_dev__job_costs/conversion/checklist.md
  - # CONVERSION: LEFT_JOIN(j, many_matches=True), a note on its checklist
  - # CONVERSION: FROM(r, reads_all_partitions=True), a note on its checklist
- mart_dev.team_runs, from its query: tables/mart_dev__team_runs/, its checklist tables/mart_dev__team_runs/conversion/checklist.md
  - # CONVERSION: LEFT_JOIN(j, many_matches=True), a note on its checklist
  - # CONVERSION: FROM(r, reads_all_partitions=True), a note on its checklist

## Each statement, in the order they run

1. job_costs.hql line 1, `WITH job_runs AS ( SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.av...`: mart_dev.job_costs, written by its notebook
2. team_runs.hql line 1, `WITH job_runs AS ( SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.av...`: mart_dev.team_runs, written by its notebook
