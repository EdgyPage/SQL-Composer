
### Map

- **Sources**
  - `jobs`: typed columns job_id, job_name, team, region; read as `<database>.jobs`.
  - `job_runs`: typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt; read as `<database>.job_runs`.
- **Steps**
  - `job_runs` (formula column team = XLOOKUP(job_id, jobs[job_id], jobs[team])): a Table that job_costs' and team_runs' formulas read, so it is a step, a CTE in each final. Its team reads the jobs source by a LEFT JOIN. The CTE carries job_id, duration_mins and team.
- **Finals**
  - `job_costs`, a summary, with columns job_id and cost_cents. Its only typed column, job_id, is what its SUMIFS matches on, so its typed job_ids 1, 2, 3 and 4 are typed in as groups, and job_runs is read.
  - `team_runs`, a summary, with columns team and runs. Its only typed column, team, is what its COUNTIFS matches on, so its typed teams data, finance and web are typed in as groups, and job_runs is read.
- **Settings, never a source, step or final**
  - `Parameters`: cents_per_minute, read in as its value 50 in cost_cents.
  - `Keys`: job_costs, matched on job_id.
- **Typed over a formula**: job_costs, cost_cents where job_id is 3, typed as 1000. It is a CASE on job_id, as the Keys row for job_costs says.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet; the notes outside Tables, at Jobs A1, Runs A1, Parameters D1, Keys D1, Job costs D1 and Team runs D1. There are no Total Rows, no Power Query and no defined names listed, and no chart or PivotTable.
- **`<...>` to fill in**: `<database>`, in each read. The notes at Jobs A1 and Runs A1 say the tables were copied from ops.

### Hive

```sql
-- final: job_costs
WITH job_runs AS (
  SELECT r.job_id, r.duration_mins, jb.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs jb ON r.job_id = jb.job_id
)
SELECT k.job_id,
  CASE WHEN k.job_id = 3 THEN 1000
    ELSE COALESCE(c.total, 0) * 50 END AS cost_cents
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) k
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM job_runs GROUP BY job_id) c
  ON k.job_id = c.job_id
```

```sql
-- final: team_runs
WITH job_runs AS (
  SELECT r.job_id, r.duration_mins, jb.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs jb ON r.job_id = jb.job_id
)
SELECT k.team, COALESCE(c.runs, 0) AS runs
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') k
LEFT JOIN (SELECT team, COUNT(*) AS runs FROM job_runs GROUP BY team) c
  ON k.team = c.team
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
