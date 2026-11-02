## Q1

### Map

- **Sources**
  - `ops.jobs`: Table jobs, typed columns job_id, job_name, team, region. Read by the LEFT JOIN in the job_runs step.
  - `ops.job_runs`: Table job_runs' typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read by the job_runs step.
- **Steps**
  - Table job_runs, a CTE `job_runs` in the teams final. Its formula column team (`XLOOKUP([@job_id],jobs[job_id],jobs[team])`) is read by teams' formulas, so it is a step, not a final. Columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt, team.
- **Finals**
  - Table teams (team, runs, total_duration_mins). It is a summary: its only typed column, team, is the one its COUNTIFS and SUMIFS match on, so its query is a GROUP BY of job_runs, with its typed groups kept. It has no Total Row.
- **Left out**
  - Parameters and Keys: both are empty Tables, never a source, step or final. No formula reads Parameters, and no value is typed over a formula, so Keys needs no row.
  - Sheet "Steps": the shipped steps of the empty workbook, not a Table or a query.
- **Values written in**
  - The summary's groups data, finance and web, typed into teams' Hive. A team added later won't appear in the result until it is added to this query.
- **Values typed over a formula**
  - None. Keys is empty.
- **Marks**
  - None from files 11 and 12. XLOOKUP is written as a LEFT JOIN on job_id. Where a job_id has no row in jobs, Excel shows #N/A and Hive gives NULL.
  - Run 98's blank status and avg_retry_secs are read by no formula, so they pass through as NULL with no mark.
- **Refusals**
  - None. XLOOKUP, COUNTIFS and SUMIFS are all in file 11.
- **Left alone**
  - Cell notes outside a Table: A1 on jobs and A1 on job_runs, E1 on teams, and D1 on Parameters and Keys.
- **To fill in**
  - None. `<database>` is written as `ops`, as you asked.

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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
