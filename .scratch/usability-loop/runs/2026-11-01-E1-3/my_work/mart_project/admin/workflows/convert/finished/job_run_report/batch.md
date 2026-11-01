# Batch job_run_report

1 script, kept as given in scripts/: job_run_report.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- default.job_run_report: mart_dev.job_run_report, tables/mart_dev__job_run_report/, its checklist tables/mart_dev__job_run_report/conversion/checklist.md

## Each statement, in the order they run

1. job_run_report.hql line 1, `SELECT job_id, COUNT(*) AS runs, COALESCE(SUM(CASE WHEN status = 'FAILED' THE...`: mart_dev.job_run_report, written by its notebook
