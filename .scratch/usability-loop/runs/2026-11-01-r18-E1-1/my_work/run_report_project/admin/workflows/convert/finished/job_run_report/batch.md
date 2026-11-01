# Batch job_run_report

1 script, kept as given in scripts/: report.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- mart_dev.job_run_report, from its query: tables/mart_dev__job_run_report/, its checklist tables/mart_dev__job_run_report/conversion/checklist.md
  - # CONVERSION: FROM(job_runs, reads_all_partitions=True), a note on its checklist
  - # CONVERSION: FROM(job_runs, reads_all_partitions=True), a note on its checklist
  - # CONVERSION: FROM(job_runs, reads_all_partitions=True), a note on its checklist

## Each statement, in the order they run

1. report.hql line 1, `SELECT g.job_id, COALESCE(r.runs, 0) AS runs, COALESCE(f.failed_runs, 0) AS f...`: mart_dev.job_run_report, written by its notebook
