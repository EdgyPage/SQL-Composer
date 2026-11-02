## Q1

**Map**

- Sources: `jobs` (job_id, job_name, team, region), typed. Read from `<database>.jobs`, never the sample rows.
- Steps: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt, team). Its typed columns are read from `<database>.job_runs`, and its formula column `team` (XLOOKUP on jobs) is a LEFT JOIN to `<database>.jobs`. It is a step because the formulas of job_costs and team_runs read it, so each final below reads it as a CTE.
- Finals:
  - `job_costs` (job_id, cost_cents): a summary, as its only typed column, job_id, is the one its SUMIFS matches on. cost_cents is SUMIFS over job_runs as a LEFT JOIN with COALESCE(..., 0), times the Parameters value 50.
  - `team_runs` (team, runs): a summary, as its only typed column, team, is the one its COUNTIFS matches on. runs is COUNTIFS over job_runs as a LEFT JOIN with COALESCE(..., 0).
  - Neither Table has a Total Row, so there is no Total Row final.
- Not a source, step or final: `Parameters` (name, value), read in as the value 50 where XLOOKUP("cents_a_minute", ...) stands. `Keys` (job_costs, key job_id), read in for the typed value below.
- Value typed over a formula: `job_costs`, cost_cents where job_id is 3, typed as 1000 in place of the formula. The Keys row names job_id, so that value is a CASE on job_id.
- Marks: none. The blank status and avg_retry_secs of run 98 are read by no formula, so no COALESCE is needed.
- Refusals: none.
- Left alone (cells outside a Table): the Steps sheet; the A1 notes on jobs, job_runs, job_costs and team_runs; the D1 notes on Parameters and Keys.
- To fill in: `<database>`, the database name, in each read of `<database>.jobs` and `<database>.job_runs`.

**Hive**

```sql
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

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
