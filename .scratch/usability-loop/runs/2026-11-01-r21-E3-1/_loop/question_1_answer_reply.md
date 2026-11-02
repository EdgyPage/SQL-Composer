## Q1

### Map

**Sources**
- `ops.job_runs` (Excel Table `job_runs`, typed columns only): run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read as `ops.job_runs`, as you said its sample is copied from there.

**Steps**
- `CleanRuns` (Power Query `CleanRuns`, which loads Excel Table `CleanRuns`): run_id, job_id, status, duration_mins, avg_retry_secs, dt. The Table is a step because daily_runs' formulas read it, so the query's logic is one CTE: `ops.job_runs` where status is not blank and not TEST. The typed-in rows on the CleanRuns sheet are a sample of that output; the Hive reads the query, not those rows.

**Finals**
- `daily_runs` (Daily summary): dt, runs, total_duration_mins. A summary, as dt is its only typed column and the one COUNTIFS and SUMIFS match on. Its typed days, 2026-09-23 and 2026-09-24, are typed in as its groups. runs is COUNTIFS over another Table, and total_duration_mins is SUMIFS over another Table: each a LEFT JOIN with COALESCE(..., 0), per file 11.

**Left out**
- `daily_runs (Total Row)`: left out, as you asked; no block for it.
- `Parameters`: an empty settings Table; no formula uses a fixed value, so nothing is read from it. Left alone.
- `Keys`: an empty settings Table; no value is typed over a formula, so no row is needed. Left alone.

**Values typed over a formula:** none.

**Marks:** none. The blank status on run 98 is dropped by the `IS NOT NULL` test, the same as the query drops it, so no COALESCE is needed. The blank avg_retry_secs on run 98 is read by no formula.

**Refusals:** none.

**`<...>` to fill in:** none; the database is written as `ops`, as you asked.

**Check:** on the sample's rows, daily_runs should give 2026-09-23: 3 runs, 60 minutes; 2026-09-24: 4 runs, 100 minutes.

### Hive

```sql
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM ops.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
