## Q1

### Map

- **Sources**: `job_runs`, with columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. It holds typed columns only, and no query loads it. Its nine rows are a sample; the Hive reads the table `<database>.job_runs`, never the sample.
- **Steps**: none.
- **Finals**: `run_report`, with columns job_id, runs, failed_runs, avg_duration_mins. It is a summary: its only typed column, job_id, is the key its three formulas match on, so its final query groups job_runs with its typed job_ids (1, 2, 3) kept. Nothing reads it and no query loads it. It has no Total Row.
- **Settings, never a source, step or final**: `Parameters` (name, value) and `Keys` (table, key_columns). Both are empty, so no fixed value is read from Parameters and no Keys row is needed.
- **Values typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet, and the notes outside any Table (Runs A1, Parameters D1, Keys D1, Report F1).
- **To fill in**: `<database>` in the query, the database that holds job_runs. The note in Runs A1 says "Copied from ops.job_runs", so ops is the likely value.

### Hive

```sql
SELECT j.job_id,
  COALESCE(r.runs, 0) AS runs,
  COALESCE(f.failed_runs, 0) AS failed_runs,
  a.avg_duration_mins
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
