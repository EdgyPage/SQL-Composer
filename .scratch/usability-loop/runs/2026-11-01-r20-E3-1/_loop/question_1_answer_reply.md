## Q1

### Map

- **Sources**: `job_runs` (Table: run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `ops.job_runs`. Its typed rows are a sample of that table, so the table is read, never the sample.
- **Steps**: `CleanRuns`, the Table that Power Query `CleanRuns` loads. Its M keeps the rows where status is not null and not TEST. Columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. The formulas of `daily_runs` read it, so it is a CTE.
- **Finals**: `daily_runs` (dt, runs, total_duration_mins). It is a summary: its only typed column, dt, is the one its COUNTIFS and SUMIFS match on. Its typed dt values are its groups, typed in, and `CleanRuns` is read for the counts and totals.
- **Values typed over a formula**: none. Keys is empty.
- **Marks**: none. Run 98 has a blank status; the query drops it, as M does, so no COALESCE is needed on status.
- **Refusals**: none.
- **Left alone**: the `daily_runs` Total Row (`SUBTOTAL(109, ...)` for runs and total_duration_mins), left out, as you wanted only the daily_runs Table kept as a table. Parameters and Keys are empty Tables, so they are never a source, step or final. Notes outside Tables (job_runs A1, the D1 notes on Parameters and Keys) are left alone.
- **`<...>` to fill in**: none. The database is `ops`, as you wrote it.

### Hive

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM ops.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (
  SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM CleanRuns
  GROUP BY dt
) c
  ON d.dt = c.dt
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
