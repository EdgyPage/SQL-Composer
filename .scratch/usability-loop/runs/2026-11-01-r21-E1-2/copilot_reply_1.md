## Q1

### Map

- **Sources**: `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read as `<database>.job_runs`. No query loads it, so it is a source, never a final.
- **Steps**: none. No query loads a Table, and no formula reads another Table as a step.
- **Finals**: `job_report` (job_id, runs, failed_runs, avg_duration_mins), a summary: its only typed column, job_id, is the one its COUNTIFS and AVERAGEIFS match on. Its typed job_ids 1, 2 and 3 are the groups, typed in.
- **Left out**: `Parameters` and `Keys`, which are empty Tables. Parameters and Keys are never a source, step or final. No formula reads a Parameters value, and no value is typed over a formula, so Keys needs no row.
- **Typed over a formula**: none.
- **Marks**: none. The blank status in the job_id 2 row of job_runs sits inside the COUNTIFS for failed_runs, a -IFS form, so it is written as it is and skipped, as Excel skips it.
- **Refusals**: none.
- **Left alone**: the notes outside a Table, in D1 of Parameters, D1 of Keys, A1 of Runs and F1 of Report. The A1 note on Runs reads "Copied from ops.job_runs in our warehouse", so `<database>` is probably `ops`; check it.
- **To fill in**: `<database>`.

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
