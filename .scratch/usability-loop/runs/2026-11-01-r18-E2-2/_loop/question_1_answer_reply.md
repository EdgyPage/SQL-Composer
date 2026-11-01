## Q1

**Map**

- Sources (typed columns, read as `<database>.<table>`):
  - `<database>.jobs`: job_id, job_name, team, region. Table jobs has only typed columns and no query loads it.
  - `<database>.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt. These are the typed columns of Table job_runs.
- Steps (a CTE named `job_runs` inside team_report):
  - Table job_runs, columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, team. Its team formula, the XLOOKUP on jobs, becomes a LEFT JOIN to `<database>.jobs`. Table teams reads job_runs in its formulas, so job_runs is a step, not a final.
- Finals:
  - team_report, from Table teams (renamed as you asked). It is a summary: its only typed column, team, is the one its COUNTIFS and SUMIFS match on. Columns: team, runs, total_duration_mins. The groups data, finance and web are typed in; job_runs is read as a GROUP BY.
- Values typed over a formula: none. Keys is empty, so no row is needed.
- Marks: none. Run 98 has blanks in status and avg_retry_secs, but no formula reads either column, so no blank mark applies.
- Refusals: none.
- Left alone, and named: the notes in job_runs A1, jobs A1 and teams E1; the notes in Parameters D1 and Keys D1; the Steps sheet. Parameters and Keys are empty, so neither is a source, step or final.
- `<...>` to fill in: `<database>`, in each read. The workbook's notes say ops.

### team_report

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
) c
  ON t.team = c.team
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final (team_report.hql), and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
