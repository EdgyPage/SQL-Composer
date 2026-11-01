## Q1

**Map**

- Sources: `job_runs`, read as `ops.job_runs`. Its typed columns (run_id, job_id, status, duration_mins, avg_retry_secs, dt) are not loaded by a query, so it is a source. The note above the Table, "Copied from ops.job_runs in our warehouse.", names the database table.
- Steps: none. No query feeds another, and no formula Table is read by another Table.
- Finals: `run_report` (job_id, runs, failed_runs, avg_duration_mins). Nothing reads it, so it is one query. Its only typed column, job_id, is what its COUNTIFS and AVERAGEIFS match on, so it is a summary: a GROUP BY of job_runs by job_id.
- Parameters: empty, none. Keys: empty, none.
- Typed over a formula: none. No Keys row is needed.
- Total Rows: none in this workbook.

**Marks: converted, and said so**

- COUNTIFS with no condition is COUNT(*), and COUNTIFS with `job_runs[status],"FAILED"` is COUNT(CASE WHEN ... THEN 1 END), which counts the FAILED rows. Each is wrapped in COALESCE(..., 0), as Excel gives 0 where nothing matches.
- AVERAGEIFS is AVG, left NULL (no COALESCE), as the file asks.
- Blank cells: run 98 has a blank status and a blank avg_retry_secs. The blank status is read by failed_runs, but inside a COUNTIFS form, which skips a blank, so it is not wrapped. avg_retry_secs is read by no final, so the query leaves it out.
- The workbook types job_id 1, 2 and 3 as the rows of run_report. The query groups every job_id in ops.job_runs. In this sample those are the same three jobs.
- Partitions: the formulas have no date filter, so the query reads every day in the table. If ops.job_runs is partitioned by dt, as the example Table reference in the first message shows, the Toolbox code will need `reads_all_partitions=True` with a comment, since this workbook asks for every day.

**Refused:** none.

**Left alone, and named:** the note in F1 of the Report sheet ("One row per job: its runs, how many failed, its average minutes."), and the note in A1 of the Runs sheet ("Copied from ops.job_runs in our warehouse."). Both are cells outside a Table.

**To fill in:** nothing. ops.job_runs is written in full.

```sql
SELECT r.job_id,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(COUNT(CASE WHEN r.status = 'FAILED' THEN 1 END), 0) AS failed_runs,
  AVG(r.duration_mins) AS avg_duration_mins
FROM ops.job_runs r
GROUP BY r.job_id
```

Next steps: save this query as run_report.hql, then load file 13 in a new chat to run the convert Workflow on it as one batch, with DEV filled in. Ask in the same chat if you also want the Toolbox code, which files 03, 04 and 05 cover.
