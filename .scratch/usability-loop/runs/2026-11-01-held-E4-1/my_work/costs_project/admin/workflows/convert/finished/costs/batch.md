# Batch costs

2 scripts, kept as given in scripts/: job_costs.hql and team_runs.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- mart_dev.job_costs, from its query: tables/mart_dev__job_costs/, its checklist tables/mart_dev__job_costs/conversion/checklist.md
- mart_dev.team_runs, from its query: tables/mart_dev__team_runs/, its checklist tables/mart_dev__team_runs/conversion/checklist.md

## Each statement, in the order they run

1. job_costs.hql line 1, `WITH job_runs AS ( SELECT job_id, duration_mins FROM ops.job_runs ) SELECT c....`: mart_dev.job_costs, written by its notebook
2. team_runs.hql line 1, `WITH job_runs AS ( SELECT r.job_id, r.duration_mins, j.team FROM ops.job_runs...`: mart_dev.team_runs, written by its notebook
