## Q1

### Map

1. **Sources**
   - `jobs` (Table jobs, typed columns): read from `<database>.jobs`; columns job_id, job_name, team, region.
   - `job_runs` (Table job_runs, typed columns): read from `<database>.job_runs`; columns run_id, job_id, status, duration_mins, avg_retry_secs, dt.
2. **Steps**
   - `job_runs` (Table job_runs, with its formula column team): read by teams' formulas (COUNTIFS and SUMIFS both read job_runs), so it is a CTE in teams' query, not a final. Columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, team.
3. **Finals**
   - `teams` (Table teams): a summary, because its only typed column, team, is what its COUNTIFS and SUMIFS match on. Its typed groups, data, finance and web, are typed in. Columns team, runs, total_duration_mins. No Total Row, so no `(Total Row)` block.
4. **Typed over a formula**: none; Keys is empty.
5. **Marks**: none.
6. **Refusals**: none.
7. **Left alone**: the text on the Steps sheet, the D1 notes on Parameters and Keys, and the "Copied from" lines in A1 of jobs and job_runs, all outside a Table. Parameters and Keys are empty, so neither is a source, a step or a final.
8. **To fill in**: `<database>` in each read. The Table references name it ops (ops.jobs, ops.job_runs).

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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
