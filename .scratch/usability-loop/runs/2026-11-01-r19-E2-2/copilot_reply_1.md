
### Map

- **Sources**
  - `jobs`: job_id, job_name, team, region. Typed columns only, and no query loads it, so it is a source. Read as `<database>.jobs`.
  - `job_runs`, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read as `<database>.job_runs` inside the step below.
- **Steps**
  - `job_runs`, all seven columns, team last. Its team formula is an XLOOKUP into jobs, so it is a LEFT JOIN on job_id. The teams formulas read it, so it is a step: a CTE in teams' query.
- **Finals**
  - `teams`: team, runs, total_duration_mins. Its only typed column, team, is the one its COUNTIFS and SUMIFS match on, so it is a summary. Its final is a GROUP BY over job_runs, with its typed groups data, finance and web typed in. The web row gives 0 and 0, as Excel does. No Total Row.
- **Left out, settings**
  - `Parameters`: empty, and no formula uses a fixed value, so there is nothing to move into it. Never a source, step or final.
  - `Keys`: empty, and no value is typed over a formula, so it needs no row. Never a source, step or final.
- **Typed over a formula**: none. Every formula cell holds its formula in every row.
- **Marks**: none. Run 98 has a blank status and a blank avg_retry_secs. No formula reads either column, so both stay as they are, with no COALESCE.
- **Refusals**: none.
- **Left alone**: the Steps sheet's text; the A1 notes on the Jobs, Runs and Teams sheets; the D1 notes on the Parameters and Keys sheets. Each is a cell outside any Table.
- **To fill in**: `<database>` in the two sources and in the job_runs step. The A1 notes say ops.jobs and ops.job_runs, so fill in ops.

### Hive

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
