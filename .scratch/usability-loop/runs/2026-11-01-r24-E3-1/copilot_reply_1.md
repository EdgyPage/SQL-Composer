## Q1

**Map**

Sources
- job_runs (Raw sheet; typed columns only: run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`. Its rows are a sample, so the query reads the table, never the sample.

Steps
- CleanRuns: the query `CleanRuns` reads Excel Table job_runs and keeps the rows whose status is not blank and not 'TEST'. It loads the Table CleanRuns (run_id, job_id, status, duration_mins, avg_retry_secs, dt), which daily's formulas read. Both are one CTE named CleanRuns. The query's type change (Table.TransformColumnTypes) has no Hive.

Finals
- daily (Table daily): its only typed column, dt, is the one its COUNTIFS and SUMIFS match on, so it is a summary. Its final query is a GROUP BY of CleanRuns with its typed dt values kept. Columns: dt, runs, total_duration_mins. No formula or query reads daily, so it is a final.

Left alone
- The Total Row of daily (Total: SUBTOTAL(109) of runs and of total_duration_mins): left out, as you said it is not needed as a table. No block is written for it.
- Parameters (empty, and no formula uses it) and Keys (empty, and no value is typed over a formula): settings, never a source, step or final. No Keys row is needed.
- Raw row 98 has a blank status, so it drops out, as the query's filter drops it.

Written in
- The dt groups '2026-09-23' and '2026-09-24' are typed in as daily's groups. A later day won't be in the table until its group is added.
- No value is typed over a formula.

Marks and refusals
- None.

To fill in
- `<database>` in the one read of `<database>.job_runs`, in CleanRuns. The Raw sheet's A1 note says the rows were copied from ops.job_runs, so `<database>` is likely ops.
- The workbook names the Table daily. Save its query as daily_runs.hql, so the file matches the Saved table you want, mart_dev.daily_runs.

**Hive**

### daily (final), for mart_dev.daily_runs

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

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
