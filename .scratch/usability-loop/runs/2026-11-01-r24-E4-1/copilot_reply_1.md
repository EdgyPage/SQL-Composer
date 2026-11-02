## Q1

### Map

**Sources** (each read as `<database>.<table>`):
- `jobs` (job_id, job_name, team, region): typed only, and no query loads it. Read `<database>.jobs`; its typed rows are a sample.
- `job_runs`, its typed columns (run_id, job_id, status, duration_mins, avg_retry_secs, dt): read from `<database>.job_runs`.

**Steps** (a CTE named `job_runs` in each final that reads it):
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt, team): its formula column `team` (`XLOOKUP([@job_id],jobs[job_id],jobs[team])`) reads `jobs`, and the formulas of job_costs and team_runs read `job_runs`, so it is a step, not a final.

**Finals**:
- `job_costs` (job_id, cost_cents): a summary, since its only typed column, job_id, is what its SUMIFS matches on. Its groups are typed in. It reads the `job_runs` step.
- `team_runs` (team, runs): a summary, since its only typed column, team, is what its COUNTIFS matches on. Its groups are typed in. It reads the `job_runs` step.
- Neither Table has a Total Row, so neither has a Total Row final.

**Settings, never a source, step or final**: Parameters and Keys. Parameters is read in by value; Keys matches the value typed over a formula.

**Values written in**:
- `cents_a_minute` = 50 (from Parameters), written into job_costs' cost_cents. Change it in Parameters and the table won't follow, so the Hive needs the new value too.
- job_costs' groups, job_id 1, 2, 3 and 4, typed in. A later job won't be in the table.
- team_runs' groups, team data, finance and web, typed in. A later team won't be in the table.

**Value typed over a formula**:
- job_costs, cost_cents where job_id is 3: 1000, typed over the formula. It is matched on job_costs' Keys row, job_id: `CASE WHEN job_id = 3 THEN 1000 ELSE ... END`.

**Marks**:
- The rate written in and the summary groups typed in, both above.
- Blank cells: none to convert. The blank status and avg_retry_secs in run 98 are not read by any formula, so no COALESCE is written.

**Refusals**: none. Every formula is an XLOOKUP, SUMIFS or COUNTIFS, each covered by file 11.

**Left alone**: the notes in D1 on each sheet and in A1 on jobs and job_runs (cells outside a Table), and the Steps sheet. The workbook has no Power Query and no Total Row, so file 12's parts don't apply.

**To fill in**: `<database>`, in `<database>.jobs` and `<database>.job_runs`.

### Hive

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT g.job_id,
  CASE WHEN g.job_id = 3 THEN 1000
    ELSE COALESCE(s.total, 0) * 50
  END AS cost_cents
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) g
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM job_runs GROUP BY job_id) s
  ON g.job_id = s.job_id
```

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT g.team, COALESCE(c.runs, 0) AS runs
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') g
LEFT JOIN (SELECT team, COUNT(*) AS runs FROM job_runs GROUP BY team) c
  ON g.team = c.team
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
