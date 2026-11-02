## Q1

### Map

- **Sources:** `<database>.job_runs`, read in full, never the 9 sample rows (run_id, job_id, status, duration_mins, avg_retry_secs, dt). The sheet's note says it was copied from ops.job_runs, so `<database>` is probably `ops`.
- **Steps:** none.
- **Finals:** run_report (job_id, runs, failed_runs, avg_duration_mins). It is a summary: its only typed column, job_id, is the one its COUNTIFS match on, so its query is a GROUP BY of job_runs with its typed rows kept.
- **Left out:** Parameters and Keys are empty settings, so neither is a source, step or final. No formula reads a fixed value, and no value is typed over a formula, so neither needs a row.
- **Values written in:** the summary's groups, job_id 1, 2 and 3, typed into the Hive from run_report's typed rows. A job added later won't appear in this table until its group is added.
- **Values typed over a formula:** none.
- **Marks:** none. The blank status in row 98 is read only inside the "FAILED" condition of COUNTIFS, which skips a blank, so it is written as it is, with no COALESCE.
- **Refusals:** none.
- **Left alone:** nothing. There are no charts, PivotTables or cells outside a Table.
- **To fill in:** `<database>` in the three reads of job_runs.

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

"Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code."
