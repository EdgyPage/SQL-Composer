## Q2

Here is daily_runs split into its two finals, as file 12 says: the Table's own final with its two dated rows only, and a separate final for its Total Row. First take the typed `Total` row out of daily_runs. Then turn on Table Design > Total Row and pick Sum for runs and total_duration_mins, so Excel's Total Row is read as a Total Row and not as one more row of data.

### Map

- **Sources**: `<database>.job_runs`, read by the job_runs step, as before.
- **Steps**: Table job_runs, a CTE in each of the two finals' blocks, as before.
- **Finals**:
  - daily_runs: a summary, with its two dated rows (2026-09-23 and 2026-09-24). Columns: dt, runs, total_duration_mins.
  - daily_runs (Total Row): one row, a column for each cell that holds a total: runs and total_duration_mins. The label `Total` in dt is a label, so it gets no column. Each SUBTOTAL(109, ...) becomes a SUM over the daily_runs final, read as a CTE.
- **Marks**: blank, as before: COALESCE(status, '') in kept.
- **To fill in**: `<database>`, once in each final's job_runs step.

### Hive: daily_runs

```sql
WITH job_runs AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
    IF(COALESCE(status, '') <> '' AND COALESCE(status, '') <> 'TEST', 1, 0) AS kept
  FROM <database>.job_runs
)
SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (
  SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  WHERE kept = 1
  GROUP BY dt
) c
  ON d.dt = c.dt
```

### Hive: daily_runs (Total Row)

```sql
WITH job_runs AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
    IF(COALESCE(status, '') <> '' AND COALESCE(status, '') <> 'TEST', 1, 0) AS kept
  FROM <database>.job_runs
),
daily_runs AS (
  SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
  FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
  LEFT JOIN (
    SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
    FROM job_runs
    WHERE kept = 1
    GROUP BY dt
  ) c
    ON d.dt = c.dt
)
SELECT SUM(runs) AS runs, SUM(total_duration_mins) AS total_duration_mins
FROM daily_runs
```

### Next

Save the first query as a .hql file named daily_runs.hql and the second as daily_runs_total_row.hql, fill in each `<database>`, and run the convert Workflow on both as one batch (file 13). It writes and checks the Toolbox code. The Total Row's file is its own final, so it repeats the job_runs step, as each final is written on its own.
