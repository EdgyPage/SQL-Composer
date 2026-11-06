# Batch failed_runs

1 script, each read where it is: admin/workflows/convert/failed_runs.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- mart_dev.failed_runs, from its query: tables/mart_dev__failed_runs/, its checklist tables/mart_dev__failed_runs/conversion/checklist.md
  - # CONVERSION: FROM(r, reads_all_partitions=True), a note on its checklist

## Each statement, in the order they run

1. failed_runs.hql line 1, `SELECT r.job_id, COUNT(*) AS fails FROM ops.job_runs r WHERE r.status = 'FAIL...`: mart_dev.failed_runs, written by its notebook
