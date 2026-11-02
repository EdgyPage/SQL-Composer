## Q1

### Map

**Sources**
- `job_runs` (Excel Table, typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt): read as `<database>.job_runs`. Its rows are a sample of the database table, so the query reads the table, not the sample.

**Steps**
- `CleanRuns`: Table CleanRuns, loaded by Power Query CleanRuns, which reads job_runs. The Table is a step because daily's formulas read it, so it is a CTE, not a final. The query CleanRuns is that step's logic. Columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. Filter: status is not blank and is not TEST.

**Finals**
- `daily` (a summary: its typed column dt is what COUNTIFS and SUMIFS match on): columns dt, runs, total_duration_mins. Its typed groups '2026-09-23' and '2026-09-24' are typed in. A date that is not in the sample is not in the Hive.
- `daily (Total Row)`: columns runs, total_duration_mins, from SUBTOTAL(109, ...) as SUM. The label "Total" gets no column.

**Settings, never a source, step or final**
- `Parameters`: an empty Table. No formula reads it.
- `Keys`: an empty Table. No value is typed over a formula, so no Keys row is needed.

**Value typed over a formula**: none.

**Marks**: none. No formula reads a blank cell: the blank status (row 98) and blank avg_retry_secs are not read by any formula, and the query's filter drops the blank status as M does.

**Refusals**: none.

**Left alone**
- Cell notes outside Tables: the job_runs sheet's A1 note "Copied from ops.job_runs"; the CleanRuns sheet's H1 note, which says the query loads "from Raw". The workbook has no sheet named Raw. The query's M reads job_runs, and that is what is converted.
- The notes in Parameters D1, Keys D1 and daily E1, and the text of the Steps sheet.

**To fill in**
- `<database>` in the source read, `<database>.job_runs`. The A1 note names ops, which may be it.

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
) c
  ON d.dt = c.dt
```

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
),
daily AS (
  SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
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

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
