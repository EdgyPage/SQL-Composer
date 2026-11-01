# Batch daily_runs

1 script, kept as given in scripts/: daily.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- default.daily_runs: mart_dev.daily_runs, tables/mart_dev__daily_runs/, its checklist tables/mart_dev__daily_runs/conversion/checklist.md
  - # CONVERSION: FROM(job_runs, reads_all_partitions=True), a note on its checklist

## Each statement, in the order they run

1. daily.hql line 1, `WITH CleanRuns AS ( SELECT dt, duration_mins FROM ops.job_runs WHERE status I...`: mart_dev.daily_runs, written by its notebook
