## Q1

### 1. Map

- **Sources:** job_runs (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
- **Steps:** none. No query and no formula reads another Table.
- **Finals:** report (job_id, runs, failed_runs, avg_duration_mins). It is a summary: its only typed column, job_id, is what its COUNTIFS match on, so its typed job_ids 1, 2 and 3 are typed in, and job_runs is read for the counts and the average. Table report has no Total Row, so there is no Total Row final.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** avg_duration_mins: AVERAGEIFS as AVG, left NULL with no COALESCE, so a job with no run gives NULL where Excel shows #DIV/0!.
- **Not marks:** the blank status on run 98 in the sample is inside the -IFS condition `status = 'FAILED'`, so status is written as it is.
- **Refusals:** none. Every formula is one file 11 lists. There are no Power Query queries and no defined names in the workbook.
- **Left alone:** Parameters and Keys, both empty Tables, never a source, step or final. Also left alone: the Steps sheet, and the notes in job_runs A1, report F1, Parameters D1 and Keys D1, which sit outside any Table.
- **To fill in:** `<database>`, in each read of job_runs. The note in job_runs A1 says it was copied from ops.job_runs, so `ops` is likely the value.

### 2. Hive

#### report (a summary final)

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

### 3. Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
