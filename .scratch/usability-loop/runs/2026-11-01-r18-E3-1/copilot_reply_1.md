
### Map

- **Sources**: `<database>.job_runs`, the typed columns of Table job_runs: run_id, job_id, status, duration_mins, avg_retry_secs, dt.
- **Steps**: Table job_runs, columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, kept. Table daily_runs' formulas read it, so it is a step: a CTE `job_runs` in each final that reads it, namely daily_runs and daily_runs (Total Row).
- **Finals**:
  - Table daily_runs, a summary. Its only typed column, dt, is what its COUNTIFS and SUMIFS match on, so its final is a GROUP BY of job_runs, with its dt groups typed in from the sample (2026-09-23, 2026-09-24). Columns: dt, runs, total_duration_mins.
  - daily_runs (Total Row): columns runs and total_duration_mins. The Total label under dt is left out.
- **Parameters**: a settings Table (name, value). Never a source, step or final. Its value TEST (excluded_status) is read into kept, as XLOOKUP's value typed in.
- **Keys**: a settings Table. Never a source, step or final. Its one row is the empty placeholder (None | None) and names no Table.
- **Values typed over a formula**: none. Every kept and runs/total_duration_mins cell holds its formula, so there is no CASE and no Keys row is needed.
- **Marks**:
  - blank: run 98 has a blank status (shown as None). kept reads status, so it is COALESCE(status, '') in kept. Run 98's avg_retry_secs is also blank, but no formula reads it, so it is read as it is.
- **Refusals**: none.
- **Left alone**: the note in Raw A1 (Copied from ops.job_runs), which sits outside the Table; the text on the Steps sheet and in Parameters D1 and Keys D1.
- **To fill in**:
  - `<database>` in both blocks. The Raw A1 note says ops.job_runs, so it may be ops.
  - Check daily_runs' dt groups. Only the two dates in the sample are typed in; add any other date the table holds.

### Hive

```sql
-- daily_runs
WITH job_runs AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
    IF(AND(COALESCE(status, '') <> '', COALESCE(status, '') <> 'TEST'), 1, 0) AS kept
  FROM <database>.job_runs
)
SELECT d.dt, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (
  SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  WHERE kept = 1
  GROUP BY dt
) c ON d.dt = c.dt
```

```sql
-- daily_runs (Total Row)
WITH job_runs AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
    IF(AND(COALESCE(status, '') <> '', COALESCE(status, '') <> 'TEST'), 1, 0) AS kept
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
  ) c ON d.dt = c.dt
)
SELECT SUM(runs) AS runs, SUM(total_duration_mins) AS total_duration_mins
FROM daily_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
