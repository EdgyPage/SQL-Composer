## Q1

### Map

**Sources**
- `ops.jobs` (job_id, job_name, team, region): Table jobs has only typed columns and no query loads it, so it is a source. Read in full, never the sample.
- `ops.job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): the typed columns of Table job_runs. Read in full, never the sample.

**Steps**
- Table job_runs: its formula column team (`=XLOOKUP([@job_id],jobs[job_id],jobs[team])`) is read by teams' formulas, so it is a step, not a final. It becomes a CTE named job_runs in teams' query, with columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, team (a LEFT JOIN of ops.jobs on job_id).

**Finals**
- Table teams (team, runs, total_duration_mins): a summary, because its only typed column, team, is the one its COUNTIFS and SUMIFS match on. Nothing reads teams and no query loads it, so it is a final. Its query is a GROUP BY of job_runs. It has no Total Row.

**Written in**
- teams' typed groups, data, finance and web, are written into the Hive. A later team won't be in the table unless it is added to these groups too.

**Typed over a formula**
- None. Keys has no row, because no value is typed over a formula.

**Marks**
- None. Row 98's blank status and avg_retry_secs are read by no formula, so no COALESCE is needed.

**Refusals**
- None. XLOOKUP, COUNTIFS and SUMIFS are all converted.

**Left alone**
- Parameters and Keys: empty Tables. No formula uses a Parameter and no value is typed over a formula, so neither is a piece.
- The D1 and E1 notes, the A1 "Copied from" notes and the Steps sheet: text, not pieces.

**To fill in**
- None. The database is ops, as you said, and every name is plain.

### Hive: teams
```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
)
SELECT t.team, COALESCE(c.runs, 0) AS runs, COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
) c
  ON t.team = c.team
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
