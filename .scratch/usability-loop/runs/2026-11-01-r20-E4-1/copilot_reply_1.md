## Q1

### Map

**Sources**
- `<database>.jobs`: job_id, job_name, team, region (the typed columns of Table jobs)
- `<database>.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt (the typed columns of Table job_runs)

**Steps**
- job_runs: a step, not a final. Its team is a formula column, `=XLOOKUP(job_id, jobs[job_id], jobs[team])`, and job_costs and team_runs read job_runs through their formulas. It is a CTE in each of those two finals, with columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, team.

**Finals**
- Table job_costs, a summary: job_id, cost_cents. Its job_ids 1, 2, 3 and 4 are typed in as its groups. cost_cents is its SUMIFS of job_runs' duration_mins times the Parameters value cents_a_minute, which is 50 and read in as its value.
- Table team_runs, a summary: team, runs. Its teams data, finance and web are typed in as its groups. runs is its COUNTIFS of job_runs' team.
- No Table has a Total Row, so there is no `(Total Row)` final.
- jobs is a source only, and job_runs is a step.

**Value typed over a formula**
- job_costs, cost_cents where job_id is 3: 1000, typed over the formula. Its Keys row names job_costs, job_id, so the CASE matches on job_id.

**Marks**
- None. The blank status and avg_retry_secs in run 98 (shown as None) are read by no formula, so no mark is needed.

**Refusals**
- None. Every formula is one this file converts; `_xlfn.` is read past.

**Left alone**
- The Steps sheet, which is instructions and not a Table.
- The notes beside the Tables: A1 on Jobs and Runs, D1 on Job costs, Team runs, Parameters and Keys.
- Parameters and Keys: settings, read by step 4, never a source, step or final.

**To fill in**
- `<database>` in each read of a source or step. The notes name ops.jobs and ops.job_runs, so the database is probably ops; check it.

### Hive

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

### Next

"Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code."
