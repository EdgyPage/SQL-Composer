## Q1

### Map

- **Sources**: `job_runs`, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read as `<database>.job_runs`. Its nine rows are a sample of the database table, so the Hive reads the table, never the sample.
- **Steps**: none.
- **Finals**: `job_report`, columns job_id, runs, failed_runs, avg_duration_mins. It is a summary: its only typed column, job_id, is what its COUNTIFS match on, so its typed job_ids 1, 2 and 3 are the groups, typed in, and job_runs is read.
- **Typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: `Parameters` and `Keys`, both empty settings Tables, never a source, step or final; no fixed value is used and no value is typed over a formula, so no row is needed. The notes outside any Table on the Steps, Runs and Report sheets are left alone.
- **To fill in**: `<database>`, in the Hive below. The Runs sheet's note says "Copied from ops.job_runs", so it is probably `ops`.

### Hive

```sql
SELECT j.job_id,
  COALESCE(r.runs, 0) AS runs,
  COALESCE(r.failed_runs, 0) AS failed_runs,
  r.avg_duration_mins AS avg_duration_mins
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id,
    COUNT(*) AS runs,
    COUNT(CASE WHEN status = 'FAILED' THEN 1 END) AS failed_runs,
    AVG(duration_mins) AS avg_duration_mins
  FROM <database>.job_runs
  GROUP BY job_id
) r ON j.job_id = r.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
