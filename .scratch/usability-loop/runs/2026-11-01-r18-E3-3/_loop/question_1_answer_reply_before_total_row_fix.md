## Q1

### Map

- **Sources**: `<database>.job_runs`, read for its typed columns run_id, job_id, status, duration_mins and dt. daily's query reads dt, status and duration_mins. avg_retry_secs is read by no formula, so it is not in the Hive.
- **Steps**: none. No query loads a Table, and no other Table's formula reads daily.
- **Finals**: `daily`, with columns dt, runs, total_duration_mins. It is a summary: its only typed column, dt, is the one its COUNTIFS and SUMIFS match on. So its typed dt rows (2026-09-23, 2026-09-24, Total) are typed in, and job_runs is read.
- **Not converted, not a source, step or final**: Parameters, read by name. test_status is TEST, typed in as its value. Keys is empty, so it has no row. The Steps sheet's text is left alone.
- **Values typed over a formula**: none.
- **Marks**: none. The blank status in run 98 is skipped by the IFS form (`status IS NOT NULL`), so no COALESCE is needed.
- **Refusals**: daily's `Total` row, its runs and total_duration_mins cells, are NULL. The Total is typed as a row of its own, not a Total Row, so Copilot reads it as one more row of data (Steps, step 5). Its SUBTOTAL formulas read daily's own column, which is circular, so they are refused.
- **To fix in the workbook**: in daily, turn on Table Design > Total Row, delete the typed Total row, and attach the workbook again. Copilot then writes `daily (Total Row)` as its own final.
- **Left alone**: none. There are no charts or cells outside a Table.
- **To fill in**: `<database>`, the database that holds job_runs.

### Hive

```sql
SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (
  SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
  GROUP BY dt
) c ON d.dt = c.dt
UNION ALL
SELECT 'Total', NULL, NULL
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
