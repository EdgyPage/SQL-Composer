## Q1

**Map**

- **Sources:**
  - `jobs`, from `<database>.jobs`, read for job_id and team.
  - `job_runs`, from `<database>.job_runs`, read for job_id and duration_mins.
- **Steps:**
  - `job_runs`. Its team column is a formula, `=XLOOKUP(job_id, jobs[job_id], jobs[team])`, and the teams summary reads it, so it is a step: a CTE that reads the source and joins jobs for team.
- **Finals:**
  - `teams`, with the columns team, runs, total_duration_mins. Its only typed column, team, is what its COUNTIFS and SUMIFS match on, so it is a summary: a GROUP BY of job_runs. Nothing reads it, so it is a final.
  - The three teams typed in the Teams sheet (data, finance, web) are the rows it holds. They are written as the list in the query and left joined to the totals, so web keeps its row with 0 runs and 0 minutes, as Excel gives 0 where nothing matches. In the sample, web has no runs.
- **Parameters and Keys:** none. Both are empty.
- **Typed over a formula:** none. No Keys row is needed.

**Marks**

- Teams' COUNTIFS becomes COUNT(*) and its SUMIFS becomes SUM, each wrapped in COALESCE(..., 0).
- The XLOOKUP becomes a LEFT JOIN to jobs on job_id. The `_xlfn.` prefix is only Excel's, so it is dropped.
- Run 99 (status TEST) and run 98 (blank status) stay in the counts, since the formulas don't filter them. Run 98's blank avg_retry_secs is read by no formula, so no mark.
- The dt column holds dates as text. No formula reads it, so no mark.

**Refused:** none.

**Left alone, and named:** the notes outside Tables, on the Steps sheet, Parameters D1, Keys D1, Jobs A1 and F2, Runs A1 and I2, and Teams E1.

**To fill in:** `<database>`, which is `ops` in your case, so the tables are ops.job_runs and ops.jobs.

**Hive for teams**

```sql
WITH job_runs AS (
  SELECT r.duration_mins, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
),
team_totals AS (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
)
SELECT t.team,
  COALESCE(s.runs, 0) AS runs,
  COALESCE(s.total_duration_mins, 0) AS total_duration_mins
FROM (
  SELECT 'data' AS team
  UNION ALL SELECT 'finance'
  UNION ALL SELECT 'web'
) t
LEFT JOIN team_totals s ON t.team = s.team
```

**Next steps**

- Fill in `<database>` as ops.
- You asked for the file to be saved as team_report.hql. Each final's query is meant to be saved as a .hql file named for its Table, which here is teams. If the convert Workflow asks for teams.hql, rename it. Then run the convert Workflow on it as one batch, with DEV filled in (file 13).
- I have not written the Toolbox code for this final. Ask if you want it next, from the same map.
