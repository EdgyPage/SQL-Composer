## Q1

### Map

- **Sources**
  - `jobs`: job_id, job_name, team, region (its typed columns). No query loads it and it has no formula, so it is a source only. Read as `<database>.jobs`.
  - `job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt (its typed columns). Read as `<database>.job_runs`.
- **Steps**
  - Table `job_runs`, with its formula column `team` (`XLOOKUP(job_id, jobs[job_id], jobs[team])`, as a LEFT JOIN of jobs on job_id). The Table `teams` formulas read it, so it is a step, not a final: a CTE in `teams`' block.
- **Finals**
  - Table `teams` (team, runs, total_duration_mins): a summary, as its only typed column, team, is the one its COUNTIFS and SUMIFS match on. Its typed groups data, finance and web are typed in, and job_runs is read.
    - runs: `COUNTIFS(job_runs[team], ...)` as COUNT(*), with COALESCE(.., 0).
    - total_duration_mins: `SUMIFS(job_runs[duration_mins], ...)` as SUM(duration_mins), with COALESCE(.., 0).
    - No Total Row on `teams`, so no second final.
- **Typed over a formula:** none. Keys is empty, so it needs no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters (an empty Table, name | value) and Keys (an empty Table, table | key_columns), which are never a source, step or final; the Steps sheet's text; the notes in A1 of Jobs and Runs, in E1 of Teams, and in D1 of Parameters and Keys.
- **To fill in:** `<database>` in the two reads, `<database>.jobs` and `<database>.job_runs`. The notes on Jobs and Runs say ops, so it is probably ops.

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

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final (teams.hql), and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
