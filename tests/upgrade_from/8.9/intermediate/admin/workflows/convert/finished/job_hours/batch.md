# Batch job_hours

admin/workflows/convert/job_hours.xlsx, a workbook read where it is, its final kept as its Hive in scripts/: job_hours.hql. Each table they write is a Saved table in the Dev Database, mart; one they only create has its Table reference alone.

## Tables

- mart.job_hours, from its query: tables/mart__job_hours/, its checklist tables/mart__job_hours/conversion/checklist.md
  - # CONVERSION: FROM(job_events, reads_all_partitions=True), a note on its checklist
  - # CONVERSION: LEFT_JOIN(o, reads_all_partitions=True), a note on its checklist
  - # CONVERSION: sum_of(run_hours.hours, adds_up=True), a note on its checklist

## The Workbook check of job_hours.xlsx

It ran the Hive of each table the workbook gave, on this computer, over the workbook's own Tables, and compared its rows with the values the workbook shows, as last saved. A difference means the Hive doesn't give what the workbook's formula, query or PivotTable gave on the same rows: look at each one, though none stops anything. The workbook's rows are an old sample, so the warehouse's rows will differ from them: this compares the Hive with the workbook alone, never with the warehouse.

- mart.job_hours, from PivotTable "PivotTable1": every cell matches the workbook, 2 cells compared.

## Each statement, in the order they run

1. job_hours.hql line 1, `WITH job_events AS ( SELECT job_id, event_type, dt, minutes / 60 AS hours FRO...`: mart.job_hours, written by its notebook
