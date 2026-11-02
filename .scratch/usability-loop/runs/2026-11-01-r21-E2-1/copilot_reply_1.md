## Q1

### Map

**Sources**
- `jobs` (typed columns job_id, job_name, team, region), read as `<database>.jobs`. No query loads it and no formula is its own, so it is a source only.
- `job_runs` (its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.

**Steps**
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt, team): it has a formula column, team, and the `teams` Table's formulas read it, so it is a step. It is not a final. It becomes a CTE named job_runs in the teams block. Its team formula, `XLOOKUP([@job_id],jobs[job_id],jobs[team])`, becomes a LEFT JOIN to `<database>.jobs` on job_id, then jobs.team.

**Finals**
- `teams` (team, runs, total_duration_mins): nothing else reads it, and it has formula columns, so it is a final. Its only typed column, team, is the one its COUNTIFS and SUMIFS match on, so it is a summary. Its typed groups, data, finance and web, are typed in. Its runs and total_duration_mins read job_runs, another Table, so each is a LEFT JOIN with COALESCE(..., 0), since Excel gives 0 where nothing matches (web has no runs).

**Values typed over a formula:** none. Keys has no row, and no formula column holds a typed value.

**Marks:** none. No formula reads a blank cell in the sample. The blank status and avg_retry_secs cells are read by no formula.

**Refusals:** none.

**Left alone:** Parameters and Keys. Both are empty settings Tables that no formula reads, so they are never a source, step or final. The workbook has no Total Row, no Power Query and no defined name.

**To fill in:** `<database>` in each read of `jobs` and `job_runs`. The sheets say they were copied from ops.jobs and ops.job_runs, so `<database>` may be `ops`.

### Hive

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT t.team,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(s.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (SELECT team, COUNT(*) AS runs FROM job_runs GROUP BY team) c
  ON t.team = c.team
LEFT JOIN (SELECT team, SUM(duration_mins) AS total_duration_mins FROM job_runs GROUP BY team) s
  ON t.team = s.team
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
