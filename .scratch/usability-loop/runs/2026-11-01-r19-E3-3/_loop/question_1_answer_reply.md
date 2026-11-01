## Q1

### Map

**Sources**
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed columns only, no formula. Read as `<database>.job_runs`, the database table of its name, never its nine sample rows.

**Steps**
- `CleanRuns` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): the Table the Power Query CleanRuns loads, and Daily's formulas read it, so it is a step. Its CTE is that query's M (Power Query sheet, A4 to A10), reading `<database>.job_runs`. Its typed rows are a copy of the query's output, so they are not read.

**Finals**
- `Daily` (dt, runs, total_duration_mins): this is the final. Its only typed column, dt, is what its COUNTIFS and SUMIFS match on, so it is a summary: its typed dt groups are kept, and its query groups the step CleanRuns.
- `Daily (Total Row)` (runs, total_duration_mins): the Total Row's own final. Each of its two cells holds a SUBTOTAL(109), so each gets a column; the "Total" label in its dt cell gets none.

**Settings, never converted**
- `Parameters`: empty, and no formula reads a fixed value from it.
- `Keys`: empty. No value is typed over a formula, so no Keys row is needed.

**Values typed over a formula**: none.

**Marks**
- `CleanRuns`: the query is not loaded in the workbook as attached, so the Table has only typed columns. The Hive uses the M on the Power Query sheet instead, as the step above. To handle it: you can run the Hive as written, since it does not need Excel. Before you hand the workbook over, add the query in Excel as the Power Query sheet says (Data > From Table/Range on job_runs, paste the M, Close & Load To > Table at A1 of CleanRuns), which leaves the Hive the same. Do not paste CleanRuns' typed rows into a query, and never read `<database>.CleanRuns`, which is not a database table.
- Null status: M's `[status] <> null` drops a null status, but its `<> "TEST"` keeps one, as M does and Hive does not. So the Hive writes the test as `(status <> 'TEST' OR status IS NULL)`, as file 12 says.

**Refusals**: none.

**Left alone**: the Steps sheet (all text), Parameters D1, Keys D1, job_runs A1 and H2, CleanRuns H1, the Power Query sheet's A1 to A3 and A10 notes (A4 to A9 are read as the step's M), and Daily E1. Titles and notes can stay.

**To fill in**: `<database>` in each read of job_runs. The A1 note on job_runs says the table comes from ops.job_runs, so `<database>` is probably `ops`. Table names are plain (letters only), so none needs brackets.

### Hive

```sql
-- Final: Daily
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
-- Final: Daily (Total Row)
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
),
Daily AS (
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
FROM Daily
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
