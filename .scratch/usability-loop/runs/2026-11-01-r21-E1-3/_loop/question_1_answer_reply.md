Message file: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E1-3\_loop\question_1_answer.md
Answers file: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E1-3\_loop\question_1_answer_reply.md

## Q1

### Map

- **Sources:** `<database>.job_runs`, read for job_runs' typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt. The rows on the sheet are a sample of that table, so the Hive reads the table, never the sample. The job_runs sheet's A1 note names ops.job_runs; if ops is your database, put `ops` in place of `<database>`.
- **Steps:** none. No query in the workbook loads or reads another piece.
- **Finals:** job_report, a summary: its formulas are COUNTIFS and AVERAGEIFS over job_runs, grouped by job_id. Its columns, in the Table's order, are job_id, runs, failed_runs, avg_duration_mins. Its typed job_ids 1, 2 and 3 are typed in as its groups. It has no Total Row.
- **Settings, neither a source, step nor final:** Parameters (name, value), empty, and no formula reads it; Keys (table, key_columns), empty, so no value is typed over a formula.
- **Values typed over a formula:** none.
- **Marks:** none. Row 98's blank status is read inside a COUNTIFS condition, so it is written as it is and matches no FAILED.
- **Refusals:** none.
- **Left alone:** the notes outside a Table: job_runs A1, Report F1, and the D1 instructions on Parameters and Keys. The workbook has no charts or PivotTables.
- **To fill in:** `<database>`, in each read of job_runs.

### Hive

```sql
SELECT j.job_id,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(f.failed_runs, 0) AS failed_runs,
  a.avg_duration_mins
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS failed_runs FROM <database>.job_runs WHERE status = 'FAILED' GROUP BY job_id) f
  ON j.job_id = f.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_duration_mins FROM <database>.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
