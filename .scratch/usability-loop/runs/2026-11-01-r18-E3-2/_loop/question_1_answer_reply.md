## Q1

### Map

- **Sources**: `<database>.job_runs`, read by the job_runs step, with its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt.
- **Steps**: Table job_runs. Its formula column kept is read by daily_runs' formulas, so it is a step, a CTE in daily_runs' block. Columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt, kept.
- **Finals**: Table daily_runs, a summary: its only typed column, dt, is what its COUNTIFS and SUMIFS match on, so its final is a GROUP BY of job_runs with its typed rows kept. Columns: dt, runs, total_duration_mins. Each COUNTIFS becomes COUNT(*) and each SUMIFS becomes SUM, each with COALESCE(..., 0), as Excel gives 0 where nothing matches.
- **Parameters**: empty, so it is neither a source, a step nor a final; no value is read from it.
- **Keys**: empty, so it is neither a source, a step nor a final, and it names no Table.
- **Typed over a formula**: none.
- **Marks**:
  - blank: job_runs' status is blank in run 98, and kept reads it, so the Hive writes COALESCE(status, ''). Excel reads the blank as "", so kept is 0 for run 98; the COALESCE keeps that result.
- **Refusals**:
  - daily_runs' row `Total` is typed as a row of its own, so it is one more row of data, not a Total Row. Its runs `=SUBTOTAL(109,daily_runs[runs])` and total_duration_mins `=SUBTOTAL(109,daily_runs[total_duration_mins])` read their own column, a circular formula, so both are NULL in that row. The two dated rows keep their COUNTIFS and SUMIFS.
- **Left alone**: the Steps sheet; the note "Copied from ops.job_runs in our warehouse." above job_runs, a cell outside a Table; the D1 notes on Parameters and Keys. The workbook holds no charts or PivotTables.
- **To fill in**: `<database>`, once, in the FROM of the job_runs step. Also take out the `Total` row before you run the Workflow, and turn on Table Design > Total Row instead, so its total is a Total Row final.

### Hive

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
UNION ALL
SELECT 'Total' AS dt, NULL AS runs, NULL AS total_duration_mins
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
