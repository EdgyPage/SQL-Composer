## Q1

### Map

- **Sources**
  - `job_runs` (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt). Read as `<database>.job_runs`, the warehouse table, never the 9-row sample. Fill `<database>` with `ops`, since the sample is a copy of ops.job_runs.
- **Steps**
  - `CleanRuns`: the Power Query "CleanRuns" loads Table CleanRuns, and daily's formulas read that Table, so it is a step. It is read from the query's M, not from the seven typed rows in the Table, because the Power Query sheet says the query could not be saved and those rows are only what it gave. The M reads job_runs and keeps rows where status is not null and not "TEST". M's `<> "TEST"` keeps a null, so the filter is `status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)`. The step is a CTE, `WITH CleanRuns AS (...)`, in each final that reads it. Its columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt.
- **Finals**
  - `daily`, for mart_dev.daily_runs. It is a summary: its only typed column, dt, is the one COUNTIFS and SUMIFS match on. Its two typed groups, '2026-09-23' and '2026-09-24', are typed in, and CleanRuns is read. Columns: dt, runs, total_duration_mins. Each formula figure gets COALESCE(.., 0), as Excel gives 0 where nothing matches.
  - `daily (Total Row)`: the Total Row is a final of its own. It has a column for runs and one for total_duration_mins, each a SUM, and no column for the "Total" label. It reads the daily query as a CTE. Keep it or take it out: it is a separate query from the daily_runs one.
- **Parameters and Keys**: both are empty, so nothing is typed over a formula, and neither is a source, step or final.
- **Values typed over a formula**: none.
- **Marks**
  - Blank: run 98 has no status in the sample. The M's null test drops it, as the query does, so no COALESCE is needed there. avg_retry_secs is blank on run 98, but no formula reads it.
- **Refusals**: none.
- **Left alone**: the notes in A1 of job_runs, H1 of CleanRuns, E1 of daily and the Steps sheet, as titles and notes. No charts or PivotTables.
- **`<...>` to fill in**
  - `<database>` in the job_runs read: ops.
  - The Total Row's table name, as it is not mart_dev.daily_runs: name it when you save it.

### Hive

**daily, for mart_dev.daily_runs**

```sql
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

**daily (Total Row)**

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
),
daily AS (
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
FROM daily
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final (daily_runs.hql for daily, daily_total_row.hql for the Total Row), and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
