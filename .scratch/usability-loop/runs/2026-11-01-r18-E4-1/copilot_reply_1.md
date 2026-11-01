
### Map

- **Sources** (copied from ops.jobs and ops.job_runs, read as `<database>.jobs` and `<database>.job_runs`, with the database written `<database>` for you to fill in):
  - `<database>.jobs`: job_id, job_name, team, region. Table jobs has only typed columns and no query loads it, so it is a source only.
  - `<database>.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt. These are Table job_runs' typed columns.
- **Steps**:
  - Table job_runs: its team column is a formula, and Tables job_costs and team_runs read it, so it is a step, a CTE in each final that reads it. Columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt, team. team is `XLOOKUP` on job_id into jobs, written as a LEFT JOIN to `<database>.jobs`.
- **Finals**:
  - Table job_costs (job_id, cost_cents): a summary. Its only typed column, job_id, is the one its SUMIFS matches on, so its query is a GROUP BY of job_runs, with typed job_ids 1, 2, 3 and 4 kept.
  - Table team_runs (team, runs): a summary. Its only typed column, team, is the one its COUNTIFS matches on, so its query is a GROUP BY of job_runs by team, with typed groups data, finance and web kept.
  - Neither Table has a Total Row.
- **Value typed over a formula**: job_costs, cost_cents where job_id is 3, typed as 1000 in place of the formula. Matched on job_id, per the Keys row job_costs | job_id.
- **Read as a value**: Parameters' cents_a_minute is 50, so both SUMIFS formulas multiply by 50. Parameters and Keys are never a source, step or final.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet's text, and the notes outside any Table: A1 on jobs and job_runs, and D1 on Parameters, Keys, job_costs and team_runs.
- **Blanks**: job_runs run 98 has a blank status and avg_retry_secs. No formula reads either, so they stay NULL with no COALESCE, and they are not a mark.
- **To fill in**: `<database>` in the two sources.

### Hive

```sql
-- final: job_costs
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT j.job_id,
  CASE WHEN j.job_id = 3 THEN 1000 ELSE COALESCE(c.total, 0) * 50 END AS cost_cents
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) j
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
```
```sql
-- final: team_runs
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT t.team, COALESCE(c.runs, 0) AS runs
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (SELECT team, COUNT(*) AS runs FROM job_runs GROUP BY team) c
  ON t.team = c.team
```

### Next

"Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code."
