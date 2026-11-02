## Q1

**Map**

- **Sources**
  - `ops.jobs`: job_id, job_name, team, region. This is the Excel Table "jobs", typed only, with no formula and no query loading it, so it is a source and never a final.
  - `ops.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt. These are the typed columns of the Excel Table "job_runs". The table is read from the database, not from the sample.
- **Steps**
  - job_runs, a CTE inside teams' block: run_id, job_id, status, duration_mins, avg_retry_secs, dt, team. Its formula column team is an XLOOKUP into jobs, and the Table "teams" reads it with COUNTIFS and SUMIFS while nothing else does, so it is a step.
- **Finals**
  - teams: team, runs, total_duration_mins. Its only typed column is team, the one its COUNTIFS match on, so it is a summary. Its query is a GROUP BY of job_runs, with its typed rows kept: data, finance and web. Those three groups are typed in from the sample, so check them against ops.job_runs in case the table holds other teams.
- **Typed over a formula**: none. The Keys Table is empty, so no Keys row is needed.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Parameters and Keys Tables, which are empty settings Tables and never a source, step or final. Also left alone are the notes in A1 of the Jobs, Runs and Teams sheets, the notes in D1 and E1, and the Total Row check: no Table has a Total Row.
- **`<...>` to fill in**: none. The database is `ops`, taken from the workbook notes, so every name in the query is filled in.

### Hive

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
)
SELECT t.team, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
) c ON t.team = c.team
```

**Next**

"Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code."

For this workbook that means saving the query above as teams.hql, since it is the only final, and there is no `<...>` left to fill in.
