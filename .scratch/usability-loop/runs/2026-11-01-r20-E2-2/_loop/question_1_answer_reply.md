## Q1

### Map

- **Sources**
  - `<database>.jobs`: job_id, job_name, team, region. Its typed columns, read by the join in the job_runs step.
  - `<database>.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Its typed columns, read by the job_runs step.
- **Steps**
  - Table job_runs is a step, not a final: the teams formulas read its team and duration_mins. Its columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt, team. It becomes the CTE `job_runs` in the teams block. Its team column (`_xlfn.XLOOKUP` on jobs) becomes a LEFT JOIN to jobs.
- **Finals**
  - Table teams is a summary: its only typed column, team, is the one its COUNTIFS and SUMIFS match on. Its columns: team, runs, total_duration_mins. Its groups data, finance and web are typed in; its counts and sums are read from job_runs. Table teams has no Total Row.
- **Left out**
  - Table Parameters: empty, so no fixed value is read and nothing needs filling in there.
  - Table Keys: empty, and no value is typed over a formula.
- **Values typed over a formula**: none. Every team cell in job_runs and every formula cell in teams is still a formula.
- **Marks**: none.
- **Refusals**: none.
- **Blanks**: job_runs row 98 has a blank status and avg_retry_secs. No formula reads either column, so no COALESCE is written for them.
- **Left alone**: the notes outside a Table, which are not calculations: Jobs A1, Runs A1, Teams E1, the Steps sheet, and the notes in Parameters D1 and Keys D1.
- **To fill in**: `<database>`, in the two sources as the Hive below shows.

### Hive: teams

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT t.team,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
) c ON t.team = c.team
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
