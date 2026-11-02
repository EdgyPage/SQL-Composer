## Q1

**Map**

Sources
- `job_runs`: a typed Table with run_id, job_id, status, duration_mins, avg_retry_secs and dt. Read it from `<database>.job_runs`, never its sample.

Steps
- Power Query `CleanRuns`, which loads Table `CleanRuns`: the job_runs rows whose status is not blank and not TEST. Table `CleanRuns` is read by daily's formulas, so it is a step too. Both are one CTE named `CleanRuns` in each final that reads it. Columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt.

Finals
- Table `daily` (a summary, since its typed dt is the one its COUNTIFS and SUMIFS match on): dt, runs, total_duration_mins. Its typed rows, dt 2026-09-23 and 2026-09-24, are its groups, typed in. runs is COUNTIFS, so COUNT(*); total_duration_mins is SUMIFS, so SUM(duration_mins); each has COALESCE to 0.
- `daily (Total Row)`: runs and total_duration_mins. Its "Total" label in the dt column gets no column.

Settings, with no role
- Parameters: empty, and no formula reads it.
- Keys: empty, and no value is typed over a formula.
- Neither is ever a source, step or final.

Typed over a formula: none.

Marks: none. The sample's blank cells (row 98's status and avg_retry_secs) are removed by the query's filter, and no formula reads a blank, so no blank COALESCE is needed.

Refusals: none.

Left alone, and named:
- The Clean sheet's typed-in rows for CleanRuns are not read; the query's M, as listed, is the logic. The Power Query sheet's note says the query is not live in this file.
- Sheet "Steps", the workbook's own steps.
- Notes in cells outside a Table: Parameters D1, Keys D1, job_runs A1, Clean H1, Daily E1 and the Power Query sheet's A1.

To fill in: `<database>`, in both blocks below (the database of job_runs).

### Hive

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
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

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
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

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
