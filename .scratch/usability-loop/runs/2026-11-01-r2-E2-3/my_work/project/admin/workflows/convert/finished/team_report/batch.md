# Batch team_report

1 script, kept as given in scripts/: team_report.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- mart_dev.team_report, from its query: tables/mart_dev__team_report/, its checklist tables/mart_dev__team_report/conversion/checklist.md

## Each statement, in the order they run

1. team_report.hql line 1, `WITH job_runs AS ( SELECT r.job_id, r.duration_mins, j.team FROM ops.job_runs...`: mart_dev.team_report, written by its notebook
