## Q1

### Map

- **Sources**: `job_runs`, read as `<database>.job_runs`, with its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. Its sample is not read. Its sheet's A1 note says "Copied from ops.job_runs", so `<database>` is probably `ops`.
- **Steps**: none.
- **Finals**: `run_report` (job_id, runs, failed_runs, avg_duration_mins). Its only typed column, job_id, is the one its COUNTIFS match on, so it is a summary: a GROUP BY of job_runs, with its typed job_ids 1, 2 and 3 typed in as groups. No other Table or query reads it.
- **Settings, never a source, step or final**: `Parameters` and `Keys` are empty Tables. No formula reads Parameters, so no value is read from it. Keys needs no row, as no value is typed over a formula.
- **Typed over a formula**: none. Every run_report row holds its formula.
- **Marks**: none. The blank status in one sample row (run 98) is read inside a -IFS form, so it is written as it is, with no COALESCE.
- **Refusals**: none.
- **Left alone**: the Steps sheet (text, not a Table) and the notes outside the Tables: job_runs A1, run_report F1, Parameters D1 and Keys D1. The workbook has no Power Query, defined name, chart or PivotTable.
- **To fill in**: `<database>`, in the final's block below.

### Hive

**run_report** (a summary)

```sql
SELECT g.job_id,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(f.failed_runs, 0) AS failed_runs,
  a.avg_duration_mins
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) g
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
  ON g.job_id = c.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS failed_runs FROM <database>.job_runs WHERE status = 'FAILED' GROUP BY job_id) f
  ON g.job_id = f.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_duration_mins FROM <database>.job_runs GROUP BY job_id) a
  ON g.job_id = a.job_id
```

### Next

"Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code."
