## Q1

### Map

Sources (read as `<database>.<table>`, never from the sample rows):
- `<database>.jobs`: job_id, job_name, team, region (Table jobs' typed columns; jobs is a source only)
- `<database>.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt (Table job_runs' typed columns)

Steps:
- job_runs, a CTE in teams' query: run_id, job_id, status, duration_mins, avg_retry_secs, dt, team. Its formula column team (`XLOOKUP([@job_id],jobs[job_id],jobs[team])`) is a LEFT JOIN to `<database>.jobs` on job_id, taking team. Table teams' formulas read it, so it is a step.

Finals:
- teams (team, runs, total_duration_mins): a summary, since its only typed column, team, is the one its COUNTIFS and SUMIFS match on. Its final query is a GROUP BY of job_runs. runs is COUNTIFS on team, written as COUNT(*), and total_duration_mins is SUMIFS of duration_mins, written as SUM; each has COALESCE to 0, as Excel gives 0 where nothing matches.

Left alone:
- Parameters: an empty Table, and no formula reads it. Not a source, step or final.
- Keys: an empty Table. No value is typed over a formula, so no Keys row is needed. Not a source, step or final.

Values written in:
- teams' typed groups: 'data', 'finance', 'web'. A team that appears in job_runs later won't show in teams until its name is typed in here.

Values typed over a formula: none.

Marks: none.

Refusals: none.

Blanks: job_runs' row for run 98 has a blank status and a blank avg_retry_secs. No formula reads either column, so no COALESCE is written and the NULLs come through as they are.

To fill in: `<database>` in the two reads inside the job_runs step, `<database>.job_runs` and `<database>.jobs`. The notes say ops, so write ops there.

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
) c ON t.team = c.team
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
