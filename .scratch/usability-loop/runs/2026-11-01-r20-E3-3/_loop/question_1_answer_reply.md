## Q1

### Map

- **Sources**: `job_runs`, the Raw sheet's Table, with its typed columns only (run_id, job_id, status, duration_mins, avg_retry_secs, dt). No query loads it, so it is read as `<database>.job_runs`. The note in Raw A1 says ops.job_runs; the database is written as `<database>` for you to fill in.
- **Steps**: `CleanRuns`, the Clean sheet's Table (columns run_id, job_id, status, duration_mins, avg_retry_secs, dt), loaded by Power Query `CleanRuns`, whose M is on the Power Query sheet. Daily_runs' formulas read it, so it is a step: a CTE in each final that reads it, never a read of `<database>.CleanRuns` and never its typed rows. The CTE is the query's M: it reads `<database>.job_runs` and keeps rows whose status is not blank and not 'TEST'. Row 98 has a blank status; the filter drops it in M and in Hive alike, so it is not a mark.
- **Finals**:
  - `daily_runs` (dt, runs, total_duration_mins): a summary, since its only typed column, dt, is what its COUNTIFS and SUMIFS match on. Its dt groups are typed in from the sample (2026-09-23 and 2026-09-24); check them against the dates in the database. runs and total_duration_mins become a LEFT JOIN to a GROUP BY of CleanRuns, each with COALESCE(.., 0).
  - `daily_runs (Total Row)` (runs, total_duration_mins): the two Total Row cells that hold SUBTOTAL(109, ...), each a SUM over daily_runs. The "Total" label in dt is not a total, so it has no column.
- **Left out, neither a source, step nor final**: `Parameters` and `Keys`, both empty.
- **Typed over a formula**: none. Keys is empty, so no row is needed.
- **Marks**: none. Each formula converts as it is.
- **Refusals**: none.
- **Left alone**: cells outside a Table: the Steps sheet's text, the note in Raw A1, the label "Query CleanRuns:" on the Power Query sheet (its M is read, not left alone), and the notes in Parameters D1 and Keys D1. No charts or PivotTables.
- **To fill in**: `<database>`, in both blocks.

### Hive

```sql
-- daily_runs
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
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

```sql
-- daily_runs (Total Row)
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
),
daily_runs AS (
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
)
SELECT SUM(runs) AS runs, SUM(total_duration_mins) AS total_duration_mins
FROM daily_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
