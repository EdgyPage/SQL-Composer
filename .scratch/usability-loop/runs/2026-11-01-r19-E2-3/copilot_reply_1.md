
**Map**

Sources (each typed column read from `<database>.<table>`):
- `jobs`: job_id, job_name, team, region
- `job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt

Steps:
- `job_runs`: its typed columns, plus `team`, which is `=_xlfn.XLOOKUP(job_id, jobs[job_id], jobs[team])` and reads as a LEFT JOIN to `<database>.jobs`. It is a step, not a final: the `teams` formulas read it and no query loads it. Columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt, team.

Finals:
- `teams`: a summary, since its only typed column, team, is what its COUNTIFS and SUMIFS match on. Its typed groups are data, finance and web. Columns: team, runs, total_duration_mins. web has no runs, so it reads 0 in both figures, as Excel does.

Values typed over a formula: none. Keys holds no row.

Marks: none.

Refusals: none.

Left alone: the notes in cells outside a Table, which are the Steps sheet, Jobs A1, Runs A1, Teams E1, Parameters D1 and Keys D1. Parameters and Keys are empty Tables, so they are never a source, step or final. No formula uses a fixed value, so Parameters stays empty.

To fill in: `<database>`, the database name in each read of `job_runs` and `jobs`.

**Hive**

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team AS team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT t.team, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
) c ON t.team = c.team
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
