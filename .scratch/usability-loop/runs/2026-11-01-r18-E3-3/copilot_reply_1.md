
### Map

- **Sources**: `job_runs`, read as `<database>.job_runs`, with its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt. The table is read, never the sample.
- **Steps**: none.
- **Finals**:
  - `daily` (dt, runs, total_duration_mins): a summary, since its only typed column, dt, is the one its COUNTIFS and SUMIFS match on. Its typed groups, 2026-09-23 and 2026-09-24, are typed in, and job_runs is read.
  - `daily (Total Row)` (runs, total_duration_mins): one row, a SUM of each column's total, from SUBTOTAL(109). The "Total" label gets no column.
- **Settings, never a source, step or final**:
  - `Parameters` (name test_status, value TEST): its value is typed in as 'TEST' in both formulas.
  - `Keys`: holds no row (None | None), so no Keys match is needed.
- **Power Query**: none. **Defined names**: none listed.
- **Value typed over a formula**: none. Both rows of each formula column hold formulas.
- **Marks**:
  - The bare criterion "<>" on status, in COUNTIFS and SUMIFS, is written as `status IS NOT NULL`, as Excel counts only the non-blank cells there. File 11 gives no rule for a bare "<>", so check this one.
  - Run 98 has a blank status and a blank avg_retry_secs in the sample. Status sits in the -IFS form, which skips a blank, so it is written as it is, with no COALESCE. No formula reads avg_retry_secs.
- **Refusals**: none. COUNTIFS, SUMIFS, XLOOKUP (its value typed in) and SUBTOTAL(109) each have Hive here.
- **Left alone**: the Steps sheet's text, which holds no Table, and the notes on the job_runs, Parameters, Keys and daily sheets.
- **`<...>` to fill in**: `<database>`, in both blocks below. The job_runs sheet's note says the data was copied from ops.job_runs, so it is likely `ops`.

### Hive

```sql
SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (
  SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
  GROUP BY dt
) c
  ON d.dt = c.dt
```

```sql
WITH daily AS (
  SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
  FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
  LEFT JOIN (
    SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
    FROM <database>.job_runs
    WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
    GROUP BY dt
  ) c
    ON d.dt = c.dt
)
SELECT SUM(runs) AS runs, SUM(total_duration_mins) AS total_duration_mins
FROM daily
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
