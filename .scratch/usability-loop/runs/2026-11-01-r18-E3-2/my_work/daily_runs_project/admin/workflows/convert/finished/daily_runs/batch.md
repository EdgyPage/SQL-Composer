# Batch daily_runs

1 script, kept as given in scripts/: daily_runs.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- mart_dev.daily_runs, from its query: tables/mart_dev__daily_runs/, its checklist tables/mart_dev__daily_runs/conversion/checklist.md
  - # CONVERSION: FROM(job_runs, reads_all_partitions=True), a note on its checklist

## Each statement, in the order they run

1. daily_runs.hql line 1, `WITH job_runs AS ( SELECT run_id, job_id, status, duration_mins, avg_retry_se...`: mart_dev.daily_runs, written by its notebook
