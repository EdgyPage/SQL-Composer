
### Map

- **Sources**: `job_runs`, a Table of typed columns only, read as `<database>.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt.
- **Steps**: Table `CleanRuns`, whose rows come from query CleanRuns (it loads the Table). daily's formulas read the Table, so it is a step, read as a CTE. Columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. The query reads job_runs and keeps rows whose status is not blank and not 'TEST'.
- **Finals**:
  - Table `daily` (dt, runs, total_duration_mins). It is a summary: its only typed column, dt, is what COUNTIFS and SUMIFS match on, so its two typed dates are typed in and CleanRuns is read. Save as `daily.hql`.
  - Table `daily (Total Row)` (runs, total_duration_mins). Per file 15, the Total Row is a final of its own; its two SUBTOTAL(109) cells are sums, and the "Total" label is not a column. Save as `daily_total_row.hql`. Take it out if you only want the daily block.
- **Values typed over a formula**: none, so no Keys row is needed. Parameters and Keys are empty Tables and are not converted.
- **Marks**: none. Row 98 has a blank status and is dropped by CleanRuns' filter, as the query drops it. No formula reads a blank in the sample.
- **Refusals**: none. COUNTIFS, SUMIFS and SUBTOTAL(109) are all converted.
- **Left alone**: Parameters and Keys (empty Tables); the Steps sheet; the text cells outside a Table (job_runs' A1 note, daily's E1 note, and the notes above the Power Query text).
- **To fill in**: `<database>`, in the job_runs read in each block. The job_runs note in A1 says it was copied from ops.job_runs, so check whether that database is the one to use.

### Hive

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins FROM CleanRuns GROUP BY dt) c
  ON d.dt = c.dt
```

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
),
daily AS (
  SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
  FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
  LEFT JOIN (SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins FROM CleanRuns GROUP BY dt) c
    ON d.dt = c.dt
)
SELECT SUM(runs) AS runs, SUM(total_duration_mins) AS total_duration_mins
FROM daily
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
