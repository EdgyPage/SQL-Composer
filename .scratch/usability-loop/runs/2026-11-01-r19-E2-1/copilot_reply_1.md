
### Map

- Read: five Excel Tables, Parameters, Keys, jobs, job_runs and teams. No defined name, no Power Query, no Total Row.
- Sources
  - `<database>.job_runs`: the typed columns of job_runs: run_id, job_id, status, duration_mins, avg_retry_secs, dt.
  - `<database>.jobs`: the Table jobs, all typed: job_id, job_name, team, region. jobs is a source only.
- Steps
  - job_runs, a CTE in the teams block: run_id, job_id, status, duration_mins, avg_retry_secs, dt, team. Its formula column team is the XLOOKUP on jobs, read by job_id. It is a step, not a final, because teams' COUNTIFS and SUMIFS read job_runs[team] and job_runs[duration_mins].
- Finals
  - teams (a summary): team, runs, total_duration_mins. Its only typed column, team, is the one its COUNTIFS and SUMIFS match on, so its typed groups data, finance and web are typed in, and job_runs is read. runs is COUNT(*) and total_duration_mins is SUM(duration_mins), each with COALESCE(.., 0).
- Value typed over a formula: none. Keys holds no row, so no CASE is needed.
- Marks: none. The blank status and avg_retry_secs on run 98 are read by no formula.
- Refusals: none.
- Left alone: the Steps sheet, A1 of Jobs and Runs, E1 of Teams, and D1 of Parameters and Keys, all cells outside a Table.
- Parameters and Keys: both empty, so no fixed value is read and no typed-over value needs a row. Neither is a source, step or final.
- `<...>` to fill in: `<database>` in `<database>.job_runs` and `<database>.jobs`. The notes on Jobs and Runs say ops.

### Hive

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
) c
  ON t.team = c.team
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
