## Q1

**Map**

- **Sources**
  - `ops.jobs`: Table `jobs`, typed columns job_id, job_name, team, region. Read for job_id and team, the two columns the final uses.
  - `ops.job_runs`: Table `job_runs`, typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read for job_id and duration_mins.
- **Steps**
  - `job_runs` (a CTE in the final's query): its team column is a formula, `=XLOOKUP(job_id, jobs[job_id], jobs[team])`, and the Teams sheet reads it. So it is a step: `ops.job_runs` LEFT JOIN `ops.jobs` on job_id, with team taken from jobs.
- **Finals**
  - `mart_dev.team_report`, from Table `teams` on the Teams sheet, with the columns team, runs, total_duration_mins in that order. Its only typed column is team, which its COUNTIFS and SUMIFS match on, so it is a summary of job_runs grouped by team, with one row per typed team (data, finance, web).
- **Parameters and Keys**: both are empty, so there are none. No value is typed over a formula, so there is no Keys row to add.

**Marks (converted, and said so)**

- Team `web` has no runs in the sample, because no run has job_id 4. A plain GROUP BY would drop it, but the final must hold every row of its Table. So the query starts from the three typed team values, and a team with no runs gets 0 for runs and total_duration_mins, as Excel's COUNTIFS and SUMIFS give 0 where nothing matches (COALESCE).
- Run 99 has status TEST. COUNTIFS and SUMIFS count it, so the query counts it too. Nothing is filtered.

**Refusals**

- None.

**Left alone, and named**

- The notes outside Tables: Jobs A1, Runs A1, Teams E1, the text on the Steps sheet, and Parameters D1 and Keys D1.
- No charts, PivotTables or Power Query are in this workbook.

**To fill in**

- Nothing. Every database and table name is given, so there are no `<...>` in the query.

**Hive**

```sql
WITH job_runs AS (
  SELECT r.job_id, r.duration_mins, j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
),
totals AS (
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
LEFT JOIN totals s ON t.team = s.team
```

**Next steps**

- Take out anything you don't want converted. Nothing here needs taking out.
- Save the query as `team_report.hql`, named for its Table, and run the convert Workflow on it as a batch (file 13), with DEV filled in. Where the Workflow's checked code and this query differ, the checked code wins.
- The Toolbox code for this final (file 11, step 8) is not in this reply. The literal team rows are not a form that files 03, 04 or 05 name, so ask for it once you have the query checked.
