## Q1

### Map

**Sources**
- `<database>.job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): Excel Table `job_runs` holds only typed columns and no query loads it, so it is a source. Its sheet note says the copy is from ops.job_runs; if so, fill `<database>` with `ops`.

**Steps**
- `CleanRuns` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): the query `CleanRuns` and the Table it loads are one step, a CTE named `CleanRuns`, because the formulas of `daily_runs` read the Table. The CTE reads `<database>.job_runs` and keeps the rows with a status that is not blank and not TEST. Row 98 (blank status) is dropped.

**Finals**
- `daily_runs` (dt, runs, total_duration_mins): this is the daily_runs final, a summary, because its only typed column, dt, is what its COUNTIFS and SUMIFS match on. It is the first block under Hive below.
- `daily_runs (Total Row)` (runs, total_duration_mins): its Total Row, a final of its own. The label "Total" gets no column. It is the second block under Hive below.

**Left out**
- `Parameters` and `Keys`: both are empty, no formula uses a fixed value and none is typed over, so they are never a source, step or final.

**Values written in**
- Summary groups in `daily_runs`, column dt: `'2026-09-23'` and `'2026-09-24'`, typed in. A later day won't be in the table, so add a row for each new day to the summary's groups.

**Values typed over a formula**
- None. Keys holds no row.

**Marks**
- Summary groups typed in: see Values written in above.
- The Power Query `CleanRuns` is not saved in the file, so the Hive is written from its M, not from the typed rows of the Table `CleanRuns`. On this sample the M gives the seven rows that the Table holds (runs 95, 96, 97, 101, 102, 103, 104). Add the query in Excel as the Power Query sheet says, if you want the workbook itself to match.
- Null handling: the M's `[status] <> null` drops the blank status, and the Hive writes `status IS NOT NULL AND status <> 'TEST'` to keep the same rows.

**Refusals**
- None.

**Left alone**
- The sheet notes (the Power Query sheet's A1 and the note in E1 of daily_runs) are not converted.
- Nothing in charts, PivotTables or cells outside a Table.

**`<...>` to fill in**
- `<database>` in the CTE `CleanRuns`, in both blocks. Use `ops` if the copy is ops.job_runs, as the sheet says.

### Hive

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(s.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (SELECT dt, COUNT(*) AS runs FROM CleanRuns GROUP BY dt) c ON d.dt = c.dt
LEFT JOIN (SELECT dt, SUM(duration_mins) AS total_duration_mins FROM CleanRuns GROUP BY dt) s ON d.dt = s.dt
```

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
),
daily_runs AS (
  SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(s.total_duration_mins, 0) AS total_duration_mins
  FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
  LEFT JOIN (SELECT dt, COUNT(*) AS runs FROM CleanRuns GROUP BY dt) c ON d.dt = c.dt
  LEFT JOIN (SELECT dt, SUM(duration_mins) AS total_duration_mins FROM CleanRuns GROUP BY dt) s ON d.dt = s.dt
)
SELECT SUM(runs) AS runs, SUM(total_duration_mins) AS total_duration_mins
FROM daily_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
