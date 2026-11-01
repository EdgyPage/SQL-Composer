## Q1

### Map

**Sources**
- `jobs`: job_id, job_name, team, region. A source only, read as `<database>.jobs`.
- `job_runs`, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read as `<database>.job_runs`.

**Steps**
- `job_runs` (the Table with its formula column team): run_id, job_id, status, duration_mins, avg_retry_secs, dt, team. Its team formula is an XLOOKUP into jobs by job_id, so it is a LEFT JOIN. It is a step because the teams formulas read it, so it is a CTE in team_report.

**Finals**
- `team_report` (the Table `teams`, renamed as you asked): a summary, with its typed groups data, finance and web kept and typed in. Columns: team, runs, total_duration_mins. Its formulas are COUNTIFS (runs) and SUMIFS (total_duration_mins) over job_runs, so each is a GROUP BY of job_runs with COALESCE to 0.

**Other parts**
- Parameters and Keys: both empty. Never a source, step or final.
- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet, and the notes outside a Table: Jobs A1 and F2, Runs A1 and I2, Teams E1, Parameters D1 and Keys D1.
- To fill in: `<database>`, in both reads in the job_runs step. The sheets' notes say both copies come from ops, so write ops there.

### Hive

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT g.team, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') g
LEFT JOIN (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
) c ON g.team = c.team
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
