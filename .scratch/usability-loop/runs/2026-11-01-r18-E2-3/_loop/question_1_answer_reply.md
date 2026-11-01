## Q1

### Map

**Sources**, each read as `<database>.<table>`, typed columns only:
- `jobs`: job_id, job_name, team, region. Copied from ops.jobs. Nothing loads it as a final or step, and job_runs' team formula reads it, so it is a source only.
- `job_runs`: its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. Copied from ops.job_runs.

**Steps**, each a CTE in each final that reads it:
- `job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt, team. It is a step, not a final, because the teams sheet's COUNTIFS and SUMIFS read it. Its formula column team, the XLOOKUP on jobs, is written as a LEFT JOIN on jobs.

**Finals**:
- `team_report`: the teams Table, renamed as you asked (save its query as team_report.hql). Columns team, runs, total_duration_mins. Its only typed column, team, is what its COUNTIFS and SUMIFS match on, so it is a summary: a GROUP BY of job_runs, with its typed groups data, finance and web kept. It has no Total Row.

**Typed over a formula**: none. Keys is empty, so no row is needed.

**Marks**: none. Row 98's blank status and avg_retry_secs are not read by any formula, so no blank mark is needed.

**Refusals**: none. `_xlfn.XLOOKUP` is read past its prefix.

**Left alone**: Parameters and Keys, both empty Tables, never a source, step or final; the Steps sheet's text, which is not a Table; the notes above the jobs and job_runs Tables, "Copied from ops.jobs" and "Copied from ops.job_runs", which name the database tables.

**To fill in**: `<database>`, the database name, such as ops, in each read.

### Hive

#### team_report

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT t.team, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
) c ON t.team = c.team
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
