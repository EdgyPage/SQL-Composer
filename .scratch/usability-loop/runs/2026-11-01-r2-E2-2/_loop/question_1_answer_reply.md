## Q1

**Map**

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt, typed, from `<database>.job_runs`, as its note says "Copied from ops.job_runs") and `jobs` (job_id, job_name, team, region, typed, from `<database>.jobs`).
- **Steps:** `job_runs` is also a step. Its team column is a formula (an XLOOKUP into jobs), and the Table `teams` reads it, so it becomes a CTE inside the final's query.
- **Finals:** `teams` (columns team, runs, total_duration_mins). Its only typed column is `team`, the column its COUNTIFS and SUMIFS match on, so it is a summary: a GROUP BY of `job_runs`. Nothing reads `teams`, so it is a final. One query.
- No Table has a Total Row. Parameters and Keys are empty, so no value is typed over a formula.

**Marks and refusals**

- `web` has no run in the sample, so a GROUP BY alone would drop it. The query takes the three team names typed in `teams`, joins the sums to them with LEFT JOIN and wraps each in COALESCE(.., 0), as Excel gives 0. On the sample: data 4 runs and 67 minutes, finance 5 runs and 113 minutes, web 0 and 0.
- The team lookup has no if-not-found value, so a job_id missing from `jobs` gives NULL in Hive where Excel shows #N/A. The lookup is a LEFT JOIN, so every run stays.
- Run 98 has a blank status and a blank avg_retry_secs. No formula reads either one for `teams`, so nothing is wrapped. Run 99 has status TEST; the formulas count it, so the query does too.
- The workbook does not say whether `ops.job_runs` is partitioned by dt. The query reads every row, as the sample does. If that table is partitioned by dt, the Toolbox will ask for a bound on dt when the code is written.
- Left alone: the Steps, Parameters and Keys sheets, and the notes in A1, I2, F2 and E1. Titles and notes can stay.

**Fill in:** `<database>`, the database name in both `<database>.job_runs` and `<database>.jobs`.

```sql
WITH job_runs AS (
  SELECT r.duration_mins, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
),
listed AS (
  SELECT 'data' AS team
  UNION ALL SELECT 'finance'
  UNION ALL SELECT 'web'
),
summary AS (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
)
SELECT l.team,
  COALESCE(s.runs, 0) AS runs,
  COALESCE(s.total_duration_mins, 0) AS total_duration_mins
FROM listed l
LEFT JOIN summary s ON l.team = s.team
```

**Next steps:** take out anything you don't want converted, fill in `<database>`, save this query as `teams.hql`, and run the convert Workflow on it (file 13) with DEV filled in. Ask for the Toolbox code with files 03, 04 and 05 if you want it.
