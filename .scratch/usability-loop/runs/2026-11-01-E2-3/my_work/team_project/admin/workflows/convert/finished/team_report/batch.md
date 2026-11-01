# Batch team_report

1 script, kept as given in scripts/: team_report.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- ops.team_report: mart_dev.team_report, tables/mart_dev__team_report/, its checklist tables/mart_dev__team_report/conversion/checklist.md

## Each statement, in the order they run

1. team_report.hql line 1, `WITH job_runs AS ( SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.av...`: mart_dev.team_report, written by its notebook
