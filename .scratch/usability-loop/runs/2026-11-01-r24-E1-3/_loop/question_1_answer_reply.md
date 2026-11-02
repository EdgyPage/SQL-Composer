## Q1

**Map**

- Sources: `job_runs` (typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`. Its note says it is copied from ops.job_runs, so `<database>` is ops. The nine rows are a sample; the Hive reads the whole table.
- Steps: none.
- Finals: `run_report` (job_id, runs, failed_runs, avg_duration_mins), to become the Hive table job_run_report. Its only typed column, job_id, is the one its COUNTIFS match on, so it is a summary: its final is a GROUP BY of job_runs, its typed rows kept.
- Values written in: the summary's groups job_id 1, 2 and 3, from run_report's typed rows. A later job won't appear in this table until its id is added.
- Values typed over a formula: none, so no Keys row is needed.
- Marks: avg_duration_mins is AVERAGEIFS, written as AVG and left NULL with no COALESCE. A job with no runs gives NULL here where Excel gives #DIV/0!. All three jobs have runs in this sample.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables. Neither is a source, step or final, and no formula reads them. Run 98's blank status is left as it is: COUNTIFS skips it, and so does = in Hive, so the count is the same.
- Total Row: none on run_report.
- To fill in: `<database>` in the source's read, which is ops per the note.

**Hive**

### run_report, to become job_run_report

```sql
SELECT j.job_id,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(f.failed_runs, 0) AS failed_runs,
  a.avg_duration_mins AS avg_duration_mins
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS failed_runs FROM <database>.job_runs WHERE status = 'FAILED' GROUP BY job_id) f
  ON j.job_id = f.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_duration_mins FROM <database>.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

**Next**

Take out what you don't want, fill in each `<...>`, save the query as run_report.hql, and run the convert Workflow on it as one batch (file 13). It writes and checks the Toolbox code.
