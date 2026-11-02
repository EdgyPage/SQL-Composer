## Q1

**Map**

- **Sources**
  - `<database>.jobs`: job_id, job_name, team, region. Its typed columns. Only job_runs' team formula reads it, so it is a source and never a final.
  - `<database>.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt. The typed columns of Table job_runs, read by the job_runs step.
- **Steps**
  - Excel Table `job_runs`, a CTE in the teams final. Columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt, team. Its formula column team (XLOOKUP on job_id) becomes a LEFT JOIN to `<database>.jobs`. It is a step because teams' COUNTIFS and SUMIFS read it.
- **Finals**
  - Excel Table `teams`, a summary: team, runs, total_duration_mins. Its only typed column, team, is the one its COUNTIFS and SUMIFS match on, so its typed rows (data, finance, web) are typed in as groups. It has no Total Row.
- **Left out**
  - Parameters: empty, and never a source, step or final. No formula uses a fixed value.
  - Keys: empty, and never a source, step or final. No value is typed over a formula, so no Keys row is needed.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the cells outside a Table: the A1 notes on the jobs, job_runs and teams sheets, the D1 notes on Parameters and Keys, and the Steps sheet, which holds no Table or query. The attachment lists no charts or PivotTables.
- **To fill in:** `<database>` in `<database>.jobs` and `<database>.job_runs`. The A1 notes say the data was copied from ops.jobs and ops.job_runs, so the database may be `ops`; check it.

### Hive

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
) c
  ON t.team = c.team
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
