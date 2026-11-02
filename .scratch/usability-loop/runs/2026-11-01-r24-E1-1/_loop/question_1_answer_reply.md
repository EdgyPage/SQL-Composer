## Q1

### Map

- **Sources:** `<database>.job_runs`, read for its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt. Read the table, never the Runs sample, which holds nine rows of a larger table. The Runs note says it was copied from ops.job_runs.
- **Steps:** none.
- **Finals:** job_report (job_id, runs, failed_runs, avg_duration_mins), a summary. Its only typed column, job_id, is the one its COUNTIFS match on, so its final is a GROUP BY of job_runs with its typed job_ids kept. runs is COUNTIFS as COUNT(*) with COALESCE; failed_runs is COUNTIFS with status "FAILED" as a count with COALESCE; avg_duration_mins is AVERAGEIFS as AVG, left NULL where a job has no runs.
- **Left out:** Parameters and Keys, both empty. They are settings, never a source, step or final. No formula reads a Parameters value and no value is typed over a formula, so no Keys row is needed.
- **Values written in:** job_id 1, 2 and 3, the summary's groups. A job with a later id won't be in the table; add a line for it to the SELECT.
- **Values typed over a formula:** none.
- **Marks:** the typed groups above. No blank mark: job 2 has a blank status in one row, but that cell sits inside a COUNTIFS, which skips a blank as the Hive's `status = 'FAILED'` does, so that column is written as it is.
- **Refusals:** none.
- **Left alone:** avg_retry_secs, which no formula reads, so it is in the source's list only. The notes in D1 and F1, the Parameters and Keys instructions and the Runs note are not pieces.
- **`<...>` to fill in:** `<database>`, in each of the three reads of job_runs. The Runs note says ops.job_runs, so it may be ops; check it.

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
