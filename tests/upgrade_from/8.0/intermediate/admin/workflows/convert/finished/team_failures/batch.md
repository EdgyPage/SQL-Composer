# Batch team_failures

1 script, kept as given in scripts/: team_failures.hql. Each table they write is a Saved table in the Dev Database, mart; one they only create has its Table reference alone.

## Tables

- ops_reports.team_failures: mart.team_failures, tables/mart__team_failures/, its checklist tables/mart__team_failures/conversion/checklist.md
  - # CONVERSION: JOIN(o, reads_all_partitions=True), a box on its checklist

## Each statement, in the order they run

1. team_failures.hql line 2, `WITH ev AS ( SELECT e.job_id, e.dt, e.event_type FROM ops.job_events e WHERE ...`: mart.team_failures, written by its notebook
