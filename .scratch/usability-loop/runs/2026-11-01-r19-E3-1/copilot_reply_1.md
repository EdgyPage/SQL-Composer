
### Map

- **Sources:** `job_runs`, a Table of typed columns (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`. Its typed rows are a sample of that database table, so the Hive reads the table, never the sample.
- **Steps:** Table `CleanRuns`, which query `CleanRuns` loads. The query reads `job_runs` and keeps each row whose status is not blank and not `TEST`. Table `CleanRuns` is a step because daily_runs' formulas read it. Columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Its CTE is the query's logic, not its typed rows.
- **Finals:**
  - Table `daily_runs`: a summary, since its only typed column, dt, is the one its COUNTIFS and SUMIFS match on. Columns: dt, runs, total_duration_mins. Its typed groups, 2026-09-23 and 2026-09-24, are typed in; `CleanRuns` is read.
  - Table `daily_runs (Total Row)`: columns runs and total_duration_mins, each SUBTOTAL(109, ...) as SUM. The "Total" label in dt is left out.
- **Settings, not converted:** `Parameters` and `Keys` are empty Tables. Neither is a source, step or final. No formula reads a Parameters value, and no value is typed over a formula, so Keys needs no row.
- **Typed over a formula:** none.
- **Marks:**
  - Query `CleanRuns`: M's `[status] <> "TEST"` keeps a blank status, and Hive's `<>` doesn't. So it is written `(status <> 'TEST' OR status IS NULL)`, and `[status] <> null` as `status IS NOT NULL`.
  - Table `CleanRuns`' typed rows: the tool typed in the rows the query gives, since it couldn't save the query. The Hive reads the query, not those rows. The seven typed rows match the query's output.
  - Blank cells: run 98 has a blank status and a blank avg_retry_secs in `job_runs`. The query's filter drops run 98, so no COALESCE is needed.
- **Refusals:** none.
- **Left alone:** the notes and titles outside Tables: job_runs A1, daily_runs E1, Parameters D1, Keys D1, and the text of the Steps and Power Query sheets.
- **To fill in:** `<database>`, in each read of `job_runs` (the two blocks below).

### Hive

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
)
SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (
  SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM CleanRuns
  GROUP BY dt
) c ON d.dt = c.dt
```

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
),
daily_runs AS (
  SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
  FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
  LEFT JOIN (
    SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
    FROM CleanRuns
    GROUP BY dt
  ) c ON d.dt = c.dt
)
SELECT SUM(runs) AS runs, SUM(total_duration_mins) AS total_duration_mins
FROM daily_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
