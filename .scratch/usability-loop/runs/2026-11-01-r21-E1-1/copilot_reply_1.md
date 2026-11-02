## Q1

### Map

- **Sources:** `<database>.job_runs`, read for its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt. Its sample holds 9 rows; the table is read, never the sample.
- **Steps:** none. No Power Query is listed, and no Table feeds another Table's formula.
- **Finals:** run_report, a summary. Its only typed column, job_id, is the one its COUNTIFS match on, so its final is a GROUP BY of job_runs. Its typed job_ids 1, 2 and 3 are typed in as its groups. Columns: job_id, runs, failed_runs, avg_duration_mins.
- **Total Rows:** none.
- **Left alone:** Parameters (empty; no formula uses it; never a source, step or final). Keys (empty; no value is typed over a formula, so no Keys row is needed). The Steps sheet (its text is not in the attachment, so nothing is read from it).
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **`<...>` to fill in:** `<database>`, in each of the three reads of job_runs. The job_runs sheet's note says it was copied from ops.job_runs; if ops is the database, write `ops` in its place.

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
