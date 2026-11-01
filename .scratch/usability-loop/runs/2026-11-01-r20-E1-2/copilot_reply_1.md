## Q1

### Map

- **Sources**: `job_runs`, with its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt. Read it as `<database>.job_runs`, never its nine sample rows.
- **Steps**: none.
- **Finals**: `run_report`, a summary, since its only typed column, job_id, is the one its COUNTIFS match on. Its columns: job_id (typed in as the groups 1, 2 and 3), runs, failed_runs and avg_duration_mins. It has no Total Row.
- **Parameters and Keys**: both are empty Tables, so neither is a source, step or final. Parameters holds no fixed values, and Keys has no row because nothing was typed over.
- **Values typed over a formula**: none.
- **Marks**: none. Record 98 has a blank status and a blank avg_retry_secs. The COUNTIFS on status skip a blank as Excel does, so the blank needs no COALESCE and no mark. avg_retry_secs is read by no formula.
- **Refusals**: none. Every formula (COUNTIFS and AVERAGEIFS) has its Hive here.
- **Left alone**: the text on the Steps sheet, the note in A1 of Runs ("Copied from ops.job_runs"), the notes in D1 of Parameters and of Keys, and the note in F1 of Report. There are no charts, PivotTables, Power Query or defined names.
- **To fill in**: `<database>` in each of the three reads of job_runs. The note in Runs says the table was copied from ops.job_runs, so the database is probably ops; check it.

### Hive

```sql
SELECT j.job_id,
  COALESCE(r.runs, 0) AS runs,
  COALESCE(f.failed_runs, 0) AS failed_runs,
  a.avg_duration_mins AS avg_duration_mins
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
  ON j.job_id = r.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS failed_runs FROM <database>.job_runs WHERE status = 'FAILED' GROUP BY job_id) f
  ON j.job_id = f.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_duration_mins FROM <database>.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
