## Q1

**Map**

- Sources: ops.job_runs, read for Table job_runs. Its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. job_report reads job_id, status and duration_mins.
- Steps: none.
- Finals: Table job_report (job_id, runs, failed_runs, avg_duration_mins). Nothing reads it, and its only typed column, job_id, is the one its COUNTIFS match on, so it is a summary: its typed job_ids 1, 2 and 3 are typed in, and job_runs is read for the counts and the average.
- Values typed over a formula: none. Keys is empty, so no Keys row is needed.
- Marks: none.
- Refusals: none.
- Left alone: the notes outside any Table (job_runs A1, Report F1, and the notes on the Steps, Parameters and Keys sheets).
- `<...>` to fill in: none.

**Hive: job_report**

```sql
SELECT j.job_id,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(f.failed_runs, 0) AS failed_runs,
  a.avg_duration_mins AS avg_duration_mins
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM ops.job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS failed_runs FROM ops.job_runs WHERE status = 'FAILED' GROUP BY job_id) f
  ON j.job_id = f.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_duration_mins FROM ops.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
