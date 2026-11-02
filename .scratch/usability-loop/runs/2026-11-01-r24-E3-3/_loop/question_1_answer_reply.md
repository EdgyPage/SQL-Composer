## Q1

### 1. Map

**Sources**
- `ops.job_runs`, read for the Table `job_runs` (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt). The Table's rows are a sample, so the Hive reads the table, not the sample.

**Steps**
- `CleanRuns`: Power Query "CleanRuns" and the Excel Table "CleanRuns" it loads, as one CTE of the same name, since the Table holds the query's rows. Columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. It reads `ops.job_runs` and keeps rows whose status is not blank and not 'TEST'. It is a step, not a final, because daily's formulas read it.

**Finals**
- `daily` (dt, runs, total_duration_mins): a summary, because its only typed column, dt, is the one its COUNTIFS and SUMIFS match on. Its query is a GROUP BY of CleanRuns, with its typed dt groups kept.

**Values written in**
- daily's dt groups, 2026-09-23 and 2026-09-24, typed in as the summary's groups. A later day won't appear in the table until a row is added to the groups.
- Parameters: empty, and no formula reads it, so no value is written in from it.
- CleanRuns's typed rows: not read; the query gives the rows.

**Values typed over a formula**
- None. Keys is empty, so no Keys row is needed.

**Marks**
- The summary's groups are written into the Hive, as above.

**Refusals**
- None.

**Left alone**
- daily's Total Row: left out, as you said it is not needed, so there is no block for it.
- Parameters and Keys: empty tables, never a source, step or final.
- The Power Query's M is not saved in the file, as the Power Query sheet says. The Hive follows the M the workbook shows, not the typed-in rows of CleanRuns.

**To fill in**
- Nothing. The database is `ops`, as you said.

### 2. Hive

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM ops.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT d.dt,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (
  SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM CleanRuns
  GROUP BY dt
) c
  ON d.dt = c.dt
```

### 3. Next

Take out what you don't want, fill in each `<...>` (none here), save the query as `daily.hql`, and run the convert Workflow on it as one batch (file 13). It writes and checks the Toolbox code.
