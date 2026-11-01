date: 2026-11-01
arm: C
model: haiku
files: 18-r2

## X01

**Map**

- Sources: job_runs (run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours). No query loads job_runs and no other Table reads it, so it is a final.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Parameters and Keys Tables (settings, never a source, step or final; both empty), and the Steps sheet's cells outside a Table.
- To fill in: `<database>`.

### Hive

```sql
SELECT run_id, job_id, duration_mins, dt, duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X02

**Map**

- Sources: job_runs (run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag). No query loads job_runs and no other Table reads it, so it is a final.
- Values typed over a formula: none.
- Marks: none. The blank status in row 98 is not read by any formula, so it needs no COALESCE.
- Refusals: none.
- Left alone: the Parameters and Keys Tables (settings, never a source, step or final; both empty), and the Steps sheet's cells outside a Table.
- To fill in: `<database>`.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF(duration_mins > 25 OR job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X03

**Map**

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs). No query loads job_runs and no other Table reads it, so it is a final.
- Values typed over a formula: none.
- Marks: blank. Row 98 has a blank status and a blank avg_retry_secs, and formulas read both. The status is read as COALESCE(status, '') in score; avg_retry_secs is read as COALESCE(avg_retry_secs, 0) in mins_per_retry and total_secs.
- Refusals: none.
- Left alone: the Parameters and Keys Tables (settings, never a source, step or final; both empty), and the Steps sheet's cells outside a Table.
- To fill in: `<database>`.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X04

**Map**

- Sources: jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd). No query loads jobs and no other Table reads it, so it is a final.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Parameters and Keys Tables (settings, never a source, step or final; both empty), and the Steps sheet's cells outside a Table.
- To fill in: `<database>`.

### Hive

```sql
SELECT job_id, job_name, team, region,
  CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-', region) AS code,
  LENGTH(job_name) AS name_length,
  ROUND(job_id / 3, 2) AS third,
  PMOD(job_id, 2) AS odd
FROM <database>.jobs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X05

**Map**

- Sources: job_runs (run_id, dt); region_costs (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month, days_since), each formula reading its own row, and region_costs (job_id, cost_cents, region, dt, day). Neither Table is loaded by a query or read by another Table's formula, so both are finals.
- Values typed over a formula: none.
- Marks: date held as text. region_costs dt holds 20260911 as text, so day is written as CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)), which gives the same date as DATE(LEFT, MID, RIGHT) but as text in yyyy-mm-dd.
- Refusals: none.
- Left alone: the Parameters and Keys Tables (settings, never a source, step or final; both empty), and the Steps sheet's cells outside a Table.
- To fill in: `<database>` in each final.

### Hive

```sql
SELECT run_id, dt, MONTH(dt) AS month, DATEDIFF(dt, '2026-09-01') AS days_since
FROM <database>.job_runs
```

```sql
SELECT job_id, cost_cents, region, dt,
  CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS day
FROM <database>.region_costs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X06

**Map**
- Sources: jobs (job_id, job_name, team, region). Typed only, and no query loads it.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job). job_name is the XLOOKUP into jobs; runs_of_job is the COUNTIFS over its own job_id column.
- Value typed over a formula: none. Keys is empty, so it needs no row.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table. Parameters and Keys are settings Tables, both empty, and are never a source, step or final.
- To fill in: `<database>`, in both reads of the query.

**Hive**

### job_runs

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X07

**Map**
- Sources: jobs (job_id, job_name, team, region). Typed only, and no query loads it.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, team, region). team is the VLOOKUP into jobs column 3 (team); region is the INDEX and MATCH into jobs[region].
- Value typed over a formula: none. Keys is empty, so it needs no row.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table. Parameters and Keys are settings Tables, both empty, and are never a source, step or final.
- To fill in: `<database>`, in both reads of the query.

**Hive**

### job_runs

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X08

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Typed only, and read by by_job's formulas.
- Steps: none.
- Finals: by_job (job_id, total_mins, avg_retry, longest), a summary. Its typed job_id rows (1, 2, 3) are kept, and its final query is a GROUP BY of job_runs. total_mins is SUMIFS, longest is MAXIFS, and avg_retry is AVERAGEIFS.
- Value typed over a formula: none. Keys is empty, so it needs no row.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table. Parameters and Keys are settings Tables, both empty, and are never a source, step or final.
- To fill in: `<database>`, in the read of job_runs.

**Hive**

### by_job

```sql
SELECT j.job_id,
  COALESCE(c.total_mins, 0) AS total_mins,
  c.avg_retry AS avg_retry,
  COALESCE(c.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total_mins,
    AVG(avg_retry_secs) AS avg_retry, MAX(duration_mins) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
) c ON j.job_id = c.job_id
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X09

**Map**
- Sources: jobs (job_id, job_name, team, region). Typed only, and read by job_runs' team formula.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost). team is the XLOOKUP into jobs[team]; team_mins is the SUMIFS over its own team column; cost reads rate from Parameters.
- Parameters: rate is 0.5, typed into cost as its value. Keys: job_runs with run_id.
- Value typed over a formula: cost where run_id is 97 (typed 100). Matched on run_id, as Keys names it, in a CASE.
- Marks: blank. avg_retry_secs is blank in run 98, and cost reads it, so cost writes COALESCE(avg_retry_secs, 0).
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table. Parameters and Keys are settings Tables, never a source, step or final.
- To fill in: `<database>`, in both reads of the query.

**Hive**

### job_runs

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs,
  j.team,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.team), 0) AS team_mins,
  CASE WHEN r.run_id = 97 THEN 100
    ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5
  END AS cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X10

**Map**
- Sources: none. The only Table, job_runs, has formula columns and is a final.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample).
- Value typed over a formula: hours where run_id is 103 (typed 9). No Keys row names job_runs, so the CASE matches every typed column of that row: run_id, job_id, duration_mins and dt.
- Marks: none.
- Refusals: sample, `=RAND()`, is NULL AS sample. RAND gives a new random number on each calculation, so no Hive gives the same values.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table. Parameters and Keys are settings Tables, both empty, and are never a source, step or final.
- To fill in: `<database>`, in the read of job_runs.

**Hive**

### job_runs

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24'
    THEN 9 ELSE duration_mins / 60
  END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X11

### Map
- **Sources:** job_runs (run_id, duration_mins), read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, duration_mins, pick, scaled). No Total Row.
- **Values typed over a formula:** none. Keys is empty, so there is no Keys row.
- **Marks:** none.
- **Refusals:**
  - pick: `NULL AS pick`. Its formula uses INDIRECT, and ROW(), which hangs on the order of the sheet's rows.
  - scaled: `NULL AS scaled`. Its formula reads Summary!C2, a cell outside a Table that is not a defined name.
- **Left alone:** the bar chart on Summary; Summary!C2 (value 3), a cell outside a Table; the Steps sheet's text.
- **Settings:** Parameters and Keys are empty Tables, so neither is a source, step or final, and no value is read in.
- **To fill in:** `<database>`.

### Hive
#### job_runs
```sql
SELECT run_id, duration_mins, NULL AS pick, NULL AS scaled
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X12

### Map
- **Sources:** job_runs (run_id, duration_mins), read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, duration_mins, running, loop, with_tax). No Total Row.
- **Values typed over a formula:** none. Keys is empty, so there is no Keys row.
- **Marks:**
  - with_tax: tax_rate is a defined name for Summary!B3, a cell outside a Table, holding 0.2. Its value is written in place of the name (`* 0.2`). Move tax_rate into Parameters (name tax_rate, value 0.2) and read it there.
- **Refusals:**
  - running: `NULL AS running`. Its formula uses OFFSET, and ROW(), which hangs on the order of the sheet's rows.
  - loop: `NULL AS loop`. Its formula reads its own column (circular).
- **Left alone:** Summary!B3, the cell tax_rate names, left where it is; the Steps sheet's text.
- **Settings:** Parameters and Keys are empty Tables, so neither is a source, step or final.
- **To fill in:** `<database>`.

### Hive
#### job_runs
```sql
SELECT run_id, duration_mins, NULL AS running, NULL AS loop, duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X13

### Map
- **Sources:** job_runs (run_id, job_id), read as `<database>.job_runs`; jobs (job_id, job_name, team, region), read as `<database>.jobs`. jobs is a source only.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, name, doubled). No Total Row.
- **Values typed over a formula:** none. Keys is empty, so there is no Keys row.
- **Marks:**
  - name: `VLOOKUP(..., jobs, 2, TRUE)` is an approximate match. It is written as the exact match, `LEFT JOIN jobs ON job_id = jobs.job_id`, taking job_name.
- **Refusals:**
  - doubled: `NULL AS doubled`. Its formula calls DOUBLE, a defined name holding a LAMBDA.
- **Left alone:** the Steps sheet's text.
- **Settings:** Parameters and Keys are empty Tables, so neither is a source, step or final.
- **To fill in:** `<database>`.

### Hive
#### job_runs
```sql
SELECT r.run_id, r.job_id, j.job_name AS name, NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X14

### Map
- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
- **Steps:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, hours), where hours is `duration_mins / 60`. The by_job formula reads its hours column, so it is a CTE inside by_job's block.
- **Finals:** by_job (job_id, total_hours), a summary: its only typed column, job_id, is the one its SUMIFS matches on. Its typed rows (1, 2, 3) are kept. No Total Row.
- **Values typed over a formula:** none. Keys is empty, so there is no Keys row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the PivotTable on sheet Pivot (rows job_id, values Sum of duration_mins), and the Pivot sheet; the Steps sheet's text.
- **Settings:** Parameters and Keys are empty Tables, so neither is a source, step or final.
- **To fill in:** `<database>`.

### Hive
#### by_job
```sql
WITH job_runs AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt, duration_mins / 60 AS hours
  FROM <database>.job_runs
)
SELECT j.job_id, COALESCE(c.total_hours, 0) AS total_hours
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, SUM(hours) AS total_hours FROM job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X15

### Map
- **Sources:** tblRuns (Run ID, Job ID, Duration (mins)), read as `<database>.tblRuns`.
- **Steps:** none.
- **Finals:** tblRuns (Run ID, Job ID, Duration (mins), Hours). No Total Row.
- **Values typed over a formula:** none. Keys is empty, so there is no Keys row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet's text.
- **Settings:** Parameters and Keys are empty Tables, so neither is a source, step or final.
- **To fill in:** `<database>`; `<run_id>` (Run ID); `<job_id>` (Job ID); `<duration_mins>` (Duration (mins)).

### Hive
#### tblRuns
```sql
SELECT <run_id>, <job_id>, <duration_mins>, <duration_mins> / 60 AS Hours
FROM <database>.tblRuns
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X16

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). All typed, no formula column; no query loads it.
- Steps: none.
- Finals: long_runs (run_id, job_id, minutes, hours), loaded by query long_runs. No other Table's formula or query reads it, so its rows are the query's.
- Values typed over a formula: none. Keys is empty.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the notes in D1 of Parameters and Keys, which sit outside any Table. Parameters and Keys are both empty, so nothing reads them.
- To fill in: `<database>`, in the query below.

**Hive**

```sql
SELECT run_id, job_id, duration_mins AS minutes, duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X17

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). All typed, no formula column; read by query ok_runs.
- Steps: query ok_runs (connection only: job_runs' rows with status = 'SUCCESS'). Query ok_by_job reads it, so it is a CTE in that final's block.
- Finals: ok_by_job (job_id, runs, total_mins), loaded by query ok_by_job, which groups ok_runs by job_id. Its rows are the query's.
- Values typed over a formula: none. Keys is empty.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the notes in D1 of Parameters and Keys, which sit outside any Table. Parameters and Keys are both empty.
- To fill in: `<database>`, in the query below.

**Hive**

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X18

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (job_id, job_name, team, region). Both all typed, no formula column; no query loads either, and query top_runs reads both.
- Steps: none.
- Finals: top_runs (run_id, job_name, duration_mins), loaded by query top_runs. Its rows are the query's: job_runs left-joined to jobs, sorted by duration_mins descending, first 3.
- Values typed over a formula: none. Keys is empty.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the notes in D1 of Parameters and Keys, which sit outside any Table. Parameters and Keys are both empty.
- To fill in: `<database>`, in the query below.

**Hive**

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC
LIMIT 3
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X19

**Map**
- Sources: scheduler_runs (run_id, job_id, dt). All typed, no formula column; no query loads it, and query all_runs reads it.
- Outside the workbook: job_runs, read by query all_runs from Sql.Database("dwh01", "ops") (schema ops, table job_runs). Read as `<database>.job_runs`; check that it is the table you mean.
- Steps: none.
- Finals: all_runs (run_id, job_id, dt), loaded by query all_runs: scheduler_runs stacked on job_runs with UNION ALL. Its rows are the query's.
- Values typed over a formula: none. Keys is empty.
- Marks: job_runs is read from the Sql.Database source outside the workbook, named above for you to check.
- Refusals: query holidays (connection only) is left out. It reads a web source, Web.Contents("https://calendar.example.com/holidays.csv"), which has no Hive here, and nothing reads it.
- Left alone: the Steps sheet and the notes in D1 of Parameters and Keys, which sit outside any Table. Parameters and Keys are both empty.
- To fill in: `<database>`, in both reads below.

**Hive**

```sql
SELECT run_id, job_id, dt FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt FROM <database>.job_runs
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X20

**Map**
- Sources: run_alerts (alert_id, run_id, severity, dt). All typed, no formula column; no query loads it, and query alert_pivot reads it.
- Steps: none.
- Finals: alert_pivot (run_id, high, low), loaded by query alert_pivot: the run_alerts rows of runs 97 and 101, counted and pivoted by severity. Its rows are the query's.
- Values typed over a formula: none. Keys is empty.
- Marks: Table.Pivot. Its columns are now fixed at high and low, the severities in the sample, so a new severity gets no column. A run with no alert of a severity is NULL in that column, as M leaves it.
- Refusals: none.
- Left alone: the Steps sheet and the notes in D1 of Parameters and Keys, which sit outside any Table. Parameters and Keys are both empty.
- To fill in: `<database>`, in the query below.

**Hive**

```sql
SELECT run_id,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
WHERE run_id = 97 OR run_id = 101
GROUP BY run_id
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X41

**Map**

- Sources: none.
- Steps: none.
- Finals: Table job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). Its typed rows are read from `<database>.job_runs`. It has formula columns, no query loads it and nothing else reads it, so it is a final.
- Settings: Parameters and Keys, both empty here, so no fixed value is read and no Keys row is needed. Neither is a source, step or final.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet, and the D1 notes on the Parameters and Keys sheets.
- To fill in: `<database>` in the Hive below.

**Hive**

### job_runs

```sql
SELECT run_id, job_id, status, duration_mins,
  RANK() OVER (ORDER BY duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN status = 'SUCCESS' THEN duration_mins END) OVER (PARTITION BY job_id), 0) AS shortest_ok,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0) AS job_total
FROM <database>.job_runs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X42

**Map**

- Sources: Table job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Typed only, and no query loads it. Read as `<database>.job_runs`.
- Steps: none.
- Finals: Table jobs (job_id, job_name, runs, avg_mins, id_order). Its typed rows are read from `<database>.jobs`. It has formula columns and nothing reads it, so it is a final. It is not a summary, as job_name is typed and not matched on.
- Settings: Parameters and Keys, both empty here, so no fixed value is read and no Keys row is needed. Neither is a source, step or final.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet, and the D1 notes on the Parameters and Keys sheets.
- To fill in: `<database>` in the Hive below.

**Hive**

### jobs

```sql
SELECT j.job_id, j.job_name,
  COALESCE(r.runs, 0) AS runs,
  COALESCE(r.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS runs, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) r ON j.job_id = r.job_id
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X43

**Map**

- Sources: Table job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and Table jobs (job_id, job_name, team, region). Both typed only, and no query loads either. Read as `<database>.job_runs` and `<database>.jobs`.
- Steps: none. Query busy_teams and query statuses are each read by no query, so neither is a step.
- Finals:
  - Table busy_teams (team, runs, shortest, avg_mins), its rows the query busy_teams' rows. No formula reads it.
  - Table statuses (job_id, status), its rows the query statuses' rows. No formula reads it.
- Settings: Parameters and Keys, both empty here. Neither is a source, step or final.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet, and the D1 notes on the Parameters and Keys sheets.
- To fill in: `<database>` in the Hive below.

**Hive**

### busy_teams

```sql
SELECT j.team, COUNT(*) AS runs, MIN(r.duration_mins) AS shortest, AVG(r.duration_mins) AS avg_mins
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.team
HAVING COUNT(*) > 4
```

### statuses

```sql
SELECT DISTINCT job_id, status
FROM <database>.job_runs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X44

**Map**

- Sources: Table job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), Table jobs (job_id, job_name, team, region) and Table scheduler_runs (run_id, job_id, dt). All typed only, and no query loads any of them. Read as `<database>.job_runs`, `<database>.jobs` and `<database>.scheduler_runs`.
- Steps: none. Query jobs_with_runs and query never_scheduled are each read by no query, so neither is a step.
- Finals:
  - Table jobs_with_runs (run_id, job_name), its rows the query jobs_with_runs' rows. No formula reads it.
  - Table never_scheduled (job_id, job_name, team), its rows the query never_scheduled' rows. No formula reads it.
- Settings: Parameters and Keys, both empty here. Neither is a source, step or final.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet, and the D1 notes on the Parameters and Keys sheets.
- To fill in: `<database>` in the Hive below.

**Hive**

### jobs_with_runs

```sql
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON j.job_id = r.job_id
```

### never_scheduled

```sql
SELECT t.job_id, t.job_name, t.team
FROM <database>.jobs t
LEFT JOIN <database>.scheduler_runs u ON t.job_id = u.job_id
WHERE u.job_id IS NULL
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X45

**Map**

- Sources: Table job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and Table scheduler_runs (run_id, job_id, dt). Both typed only, and no query loads either. Read as `<database>.job_runs` and `<database>.scheduler_runs`.
- Steps: none. Query run_days and query matched are each read by no query, so neither is a step.
- Finals:
  - Table run_days (run_id, dt), its rows the query run_days' rows. No formula reads it.
  - Table matched (run_id, job_id, dt, status), its rows the query matched' rows. No formula reads it.
- Settings: Parameters and Keys, both empty here. Neither is a source, step or final.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet, and the D1 notes on the Parameters and Keys sheets.
- To fill in: `<database>` in the Hive below.

**Hive**

### run_days

```sql
SELECT run_id, dt FROM <database>.job_runs
UNION
SELECT run_id, dt FROM <database>.scheduler_runs
```

### matched

```sql
SELECT s.run_id, s.job_id, s.dt, r.status
FROM <database>.scheduler_runs s
FULL OUTER JOIN <database>.job_runs r ON s.run_id = r.run_id
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X51

### Map

- **Sources:** none. job_runs has formula columns, so it is not a source.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins).
- **Parameters and Keys:** both empty, so nothing is read from them. They are never a source, step or final.
- **Values typed over a formula:** none, as Keys is empty.
- **Marks:** none. The blank status in run_id 98 is read only inside the COUNTIFS and SUMIFS forms, so it is written as it is. not_ok counts it, as Excel does.
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>`, the database name in the one query.

### Hive

```sql
-- final: job_runs
SELECT run_id, job_id, status, duration_mins, dt,
  COALESCE(COUNT(CASE WHEN duration_mins > 15 THEN 1 END) OVER (PARTITION BY job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (status <> 'SUCCESS' OR status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY job_id), 0) AS failed_in_job,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X52

### Map

- **Sources:** none. job_runs has formula columns, so it is not a source.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job); job_runs (Total Row) (duration_mins, share).
- **Parameters and Keys:** both empty, so nothing is read from them. They are never a source, step or final.
- **Values typed over a formula:** none, as Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>`, the database name in both queries.

### Hive

```sql
-- final: job_runs
SELECT run_id, job_id, duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

```sql
-- final: job_runs (Total Row)
WITH job_runs AS (
  SELECT run_id, job_id, duration_mins,
    duration_mins / SUM(duration_mins) OVER () AS share,
    duration_mins - AVG(duration_mins) OVER () AS vs_avg,
    RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
  FROM <database>.job_runs
)
SELECT SUM(duration_mins) AS duration_mins, SUM(share) AS share FROM job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X53

### Map

- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). It has only typed columns and no query loads it.
- **Steps:** none.
- **Finals:** by_job (job_id, total_mins, runs, longest), a summary: its typed rows are kept and its final query is a GROUP BY of job_runs; by_job (Total Row) (total_mins, runs, longest).
- **Parameters and Keys:** both empty, so nothing is read from them. They are never a source, step or final.
- **Values typed over a formula:** none, as Keys is empty.
- **Marks:** none. The blank status and avg_retry_secs in run_id 98 are read by no formula, so nothing changes for them.
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>`, the database name in every query that reads job_runs.

### Hive

```sql
-- final: by_job
SELECT j.job_id,
  COALESCE(s.total_mins, 0) AS total_mins,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(m.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total_mins FROM <database>.job_runs GROUP BY job_id) s
  ON j.job_id = s.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
LEFT JOIN (SELECT job_id, MAX(duration_mins) AS longest FROM <database>.job_runs GROUP BY job_id) m
  ON j.job_id = m.job_id
```

```sql
-- final: by_job (Total Row)
WITH by_job AS (
  SELECT j.job_id,
    COALESCE(s.total_mins, 0) AS total_mins,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(m.longest, 0) AS longest
  FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total_mins FROM <database>.job_runs GROUP BY job_id) s
    ON j.job_id = s.job_id
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
    ON j.job_id = c.job_id
  LEFT JOIN (SELECT job_id, MAX(duration_mins) AS longest FROM <database>.job_runs GROUP BY job_id) m
    ON j.job_id = m.job_id
)
SELECT SUM(total_mins) AS total_mins, SUM(runs) AS runs, MAX(longest) AS longest FROM by_job
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X54

### Map

- **Sources:** none. job_runs has formula columns, so it is not a source.
- **Steps:** none.
- **Finals:** job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label).
- **Parameters and Keys:** both empty, so nothing is read from them. They are never a source, step or final.
- **Values typed over a formula:** none, as Keys is empty.
- **Marks:** a_month_on, EDATE written as ADD_MONTHS, marked: a month's end stays one.
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>`, the database name in the one query.

### Hive

```sql
-- final: job_runs
SELECT run_id, dt,
  LAST_DAY(dt) AS month_end,
  ADD_MONTHS(dt, 1) AS a_month_on,
  DATE_ADD(dt, 7) AS due,
  CAST(NEXT_DAY(DATE_ADD(dt, 7 * -1), 'MO') AS STRING) AS week_of,
  CAST(TRUNC(dt, 'MM') AS STRING) AS month_of,
  DAYOFWEEK(dt) AS weekday,
  DATE_FORMAT(dt, 'yyyy-MM') AS label
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X55

### Map

- **Sources:** none. jobs has formula columns, so it is not a source.
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens).
- **Parameters and Keys:** both empty, so nothing is read from them. They are never a source, step or final.
- **Values typed over a formula:** none, as Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>`, the database name in the one query.

### Hive

```sql
-- final: jobs
SELECT job_id, job_name, team, region,
  INITCAP(REPLACE(job_name, '_', ' ')) AS title,
  CONCAT_WS('/', team, region) AS tag,
  CONCAT(region, '-', job_id) AS code,
  INSTR(LOWER(job_name), 'sync') > 0 AS has_sync,
  CAST(CONCAT(job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

Message file: C:\Users\myfir\AppData\Local\Temp\claude\C--Users-myfir-Code-and-Repos-SQL-Composer\adb999d6-d2cc-49aa-89d3-e71d06e18fba\scratchpad\excel\r2\msg_7.md
Answers file: C:\Users\myfir\AppData\Local\Temp\claude\C--Users-myfir-Code-and-Repos-SQL-Composer\adb999d6-d2cc-49aa-89d3-e71d06e18fba\scratchpad\excel\r2\ans_7.md

## X56

### Map

**Sources**
- job_runs: typed columns run_id, job_id, status, duration_mins, avg_retry_secs. Its formula columns are its own final's work, below.
- scheduler_runs: run_id, job_id, dt. Typed only, and no query loads it.

**Steps**
- None. No query reads job_runs, and no other Table's formula reads it.

**Finals**
- job_runs: run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on. Its formula columns read its own rows and its own typed columns, so it is a final.

**Values typed over a formula**
- None. The Keys Table is empty, so there is no Keys row.

**Marks**
- blank: weighted reads avg_retry_secs, which is blank in run 98, so it reads COALESCE(avg_retry_secs, 0).

**Refusals**
- None.

**Left alone**
- Parameters and Keys, both empty, read by no formula.

**To fill in**
- `<database>`, in the two FROM and JOIN lines. Every table and column name is plain, so no other `<...>`.

### Hive

```sql
SELECT
  j.run_id,
  j.job_id,
  j.status,
  j.duration_mins,
  j.avg_retry_secs,
  j.status IS NULL AS no_status,
  FLOOR(j.duration_mins / 7) AS weeks,
  GREATEST(j.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(j.duration_mins) OVER () AS spread,
  SUM(j.duration_mins * COALESCE(j.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(s.dt, 'unscheduled') AS scheduled_on
FROM <database>.job_runs j
LEFT JOIN <database>.scheduler_runs s
  ON j.run_id = s.run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X57

### Map

**Sources**
- job_runs: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Typed only; queries read it, but no query loads it.
- jobs: job_id, job_name, team, region. Typed only.

**Steps**
- None. Neither query is read by another query, and no Table's formula reads a Table here.

**Finals**
- picked: run_id, job_id, status, avg_retry_secs, status_lc. The Table picked is loaded by query picked; no formula or query reads it, so the Table is the final. The query and the Table are two things.
- ran_jobs: job_id, job_name, team, region. The Table ran_jobs is loaded by query ran_jobs; nothing reads it, so it is the final.

**Values typed over a formula**
- None. The Keys Table is empty.

**Marks**
- blank: query picked's Table.ReplaceValue turns the null avg_retry_secs in run 98 into 0, written COALESCE(avg_retry_secs, 0).

**Refusals**
- None.

**Left alone**
- Parameters and Keys, both empty, read by no formula.

**To fill in**
- `<database>`, in each FROM and JOIN line. Every table and column name is plain, so no other `<...>`.

### Hive

```sql
SELECT
  run_id,
  job_id,
  status,
  COALESCE(avg_retry_secs, 0) AS avg_retry_secs,
  LOWER(status) AS status_lc
FROM <database>.job_runs
WHERE job_id IN (1, 2)
  AND (status IS NULL OR status LIKE 'S%')
```

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r
  ON r.job_id = j.job_id
WHERE j.job_name LIKE '%a%'
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X58

### Map

**Sources**
- job_runs: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Typed only.
- jobs: job_id, job_name, team, region. Typed only.
- scheduler_runs: run_id, job_id, dt. Typed only.
- region_budgets: job_id, budget_cents, region. Typed only.

**Steps**
- None. No query is read by another query, and no Table has a formula.

**Finals**
- job_regions: job_id, region. Loaded by query job_regions; the query crosses the jobs with the distinct regions, as Table.AddColumn then Table.ExpandTableColumn does.
- numbered: run_id, dt, duration_mins, n. Loaded by query numbered; n is the index after the sort, as ROW_NUMBER.
- days_per_job: job_id, days. Loaded by query days_per_job; days is a count of distinct dt.
- unrun: run_id, job_id. Loaded by query unrun; the left-anti join on both columns, with Table.Distinct, is EXCEPT.
- measures: run_id, measure, amount. Loaded by query measures; the unpivot of duration_mins and avg_retry_secs is stacked with UNION ALL.

**Values typed over a formula**
- None. There are no formulas in this workbook, and the Keys Table is empty.

**Marks**
- Order dropped: query days_per_job sorts by days descending with no FirstN or index after it, so the Hive has no ORDER BY, and the order is dropped.
- blank: measures drops the null avg_retry_secs in run 98 with WHERE avg_retry_secs IS NOT NULL, as M drops a null there.

**Refusals**
- None.

**Left alone**
- Parameters and Keys, both empty, read by no formula.

**To fill in**
- `<database>`, in each FROM and JOIN line. Every table and column name is plain, so no other `<...>`.

### Hive

```sql
SELECT j.job_id, r.region
FROM (SELECT job_id FROM <database>.jobs) j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) r
```

```sql
SELECT
  run_id,
  dt,
  duration_mins,
  ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC) AS n
FROM <database>.job_runs
```

```sql
SELECT job_id, COUNT(DISTINCT dt) AS days
FROM <database>.job_runs
GROUP BY job_id
```

```sql
SELECT run_id, job_id FROM <database>.scheduler_runs
EXCEPT
SELECT run_id, job_id FROM <database>.job_runs
```

```sql
SELECT run_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X67

### Map

**Sources**
- jobs: job_id, job_name, team, region. Typed only.
- run_alerts: alert_id, run_id, severity, dt. Typed only.
- job_runs: typed columns run_id, job_id, duration_mins, dt.

**Steps**
- job_runs: run_id, job_id, duration_mins, dt, team, alerts, running_mins. Its formulas are team (XLOOKUP on jobs), alerts (COUNTIF on run_alerts) and running_mins (the running total of its own rows). It is a step because the formulas of by_team read it, and query noisy_runs reads it too. It is a CTE in each final below.

**Finals**
- by_team: team, total_mins, alerted_runs. Its only typed column, team, is what its SUMIFS and COUNTIFS match on, so it is a summary: a GROUP BY of job_runs with the typed rows data and finance kept.
- by_team (Total Row): total_mins, alerted_runs. Its Total Row label "Total" is dropped, and it reads by_team's final query as a CTE.
- noisy_runs: run_id, team, alerts, running_mins. Loaded by query noisy_runs; nothing reads it, so it is a final.

**Values typed over a formula**
- None. The Keys Table is empty.

**Marks**
- None.

**Refusals**
- None.

**Left alone**
- Parameters and Keys, both empty, read by no formula.

**To fill in**
- `<database>`, in each FROM and JOIN line. Every table and column name is plain, so no other `<...>`.

### Hive

```sql
WITH job_runs AS (
  SELECT
    r.run_id,
    r.job_id,
    r.duration_mins,
    r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j
    ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
),
by_team AS (
  SELECT t.team, COALESCE(s.total_mins, 0) AS total_mins, COALESCE(c.alerted_runs, 0) AS alerted_runs
  FROM (SELECT 'data' AS team UNION ALL SELECT 'finance') t
  LEFT JOIN (SELECT team, SUM(duration_mins) AS total_mins FROM job_runs GROUP BY team) s
    ON t.team = s.team
  LEFT JOIN (SELECT team, COUNT(*) AS alerted_runs FROM job_runs WHERE alerts > 0 GROUP BY team) c
    ON t.team = c.team
)
SELECT team, total_mins, alerted_runs
FROM by_team
```

```sql
WITH job_runs AS (
  SELECT
    r.run_id,
    r.job_id,
    r.duration_mins,
    r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j
    ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
),
by_team AS (
  SELECT t.team, COALESCE(s.total_mins, 0) AS total_mins, COALESCE(c.alerted_runs, 0) AS alerted_runs
  FROM (SELECT 'data' AS team UNION ALL SELECT 'finance') t
  LEFT JOIN (SELECT team, SUM(duration_mins) AS total_mins FROM job_runs GROUP BY team) s
    ON t.team = s.team
  LEFT JOIN (SELECT team, COUNT(*) AS alerted_runs FROM job_runs WHERE alerts > 0 GROUP BY team) c
    ON t.team = c.team
)
SELECT SUM(total_mins) AS total_mins, SUM(alerted_runs) AS alerted_runs
FROM by_team
```

```sql
WITH job_runs AS (
  SELECT
    r.run_id,
    r.job_id,
    r.duration_mins,
    r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j
    ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
)
SELECT run_id, team, alerts, running_mins
FROM job_runs
WHERE alerts >= 2
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X68

### Map

**Sources**
- job_runs: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Typed only.
- jobs: job_id, job_name, team, region. Typed only.
- region_budgets: job_id, budget_cents, region. Typed only.

**Steps**
- base: run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name, region. Query base is connection only: it loads nothing and is read by queries by_region and top_runs, so it is a step, a CTE in each of their blocks.

**Finals**
- by_region: region, total_mins, runs, share. Loaded by query by_region, which groups base by region and keeps the groups of two or more runs. Nothing reads it, so it is a final. Its formula column share is total_mins / SUM(total_mins) OVER () over its own rows.
- by_region (Total Row): total_mins. Its Total Row has a total only in total_mins, so it is the one column; the blank cells of runs and share are not totals. It reads by_region's final query as a CTE.
- top_runs: run_id, job_name, region. Loaded by query top_runs; nothing reads it, so it is a final.

**Values typed over a formula**
- None. The Keys Table is empty.

**Marks**
- None.

**Refusals**
- None.

**Left alone**
- Parameters and Keys, both empty, read by no formula.

**To fill in**
- `<database>`, in each FROM and JOIN line. Every table and column name is plain, so no other `<...>`.

### Hive

```sql
WITH base AS (
  SELECT
    r.run_id,
    r.job_id,
    r.status,
    r.duration_mins,
    r.avg_retry_secs,
    r.dt,
    j.job_name,
    b.region
  FROM <database>.job_runs r
  INNER JOIN <database>.jobs j
    ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b
    ON r.job_id = b.job_id
),
grouped AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT
  region,
  total_mins,
  runs,
  total_mins / SUM(total_mins) OVER () AS share
FROM grouped
```

```sql
WITH base AS (
  SELECT
    r.run_id,
    r.job_id,
    r.status,
    r.duration_mins,
    r.avg_retry_secs,
    r.dt,
    j.job_name,
    b.region
  FROM <database>.job_runs r
  INNER JOIN <database>.jobs j
    ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b
    ON r.job_id = b.job_id
),
grouped AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
),
by_region AS (
  SELECT
    region,
    total_mins,
    runs,
    total_mins / SUM(total_mins) OVER () AS share
  FROM grouped
)
SELECT SUM(total_mins) AS total_mins
FROM by_region
```

```sql
WITH base AS (
  SELECT
    r.run_id,
    r.job_id,
    r.status,
    r.duration_mins,
    r.avg_retry_secs,
    r.dt,
    j.job_name,
    b.region
  FROM <database>.job_runs r
  INNER JOIN <database>.jobs j
    ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b
    ON r.job_id = b.job_id
)
SELECT run_id, job_name, region
FROM base
ORDER BY duration_mins DESC, run_id ASC
LIMIT 2
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X71

### Map

- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: query `ok_runs` (run_id, job_id, duration_mins), read by query `ok_by_job`, so it is a CTE in that final.
- Finals:
  - Table `ok_runs` (run_id, job_id, duration_mins, hours), its rows the query `ok_runs`'s, with `hours` from the formula `[duration_mins]/60`.
  - Table `ok_by_job` (job_id, total_mins), its rows the query `ok_by_job`'s.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet, and the notes in Parameters D1 and Keys D1, which are cells outside a Table.
- Parameters and Keys are empty and no formula reads them, so neither is a source, step or final.
- To fill in: `<database>`, the database name, in each FROM.

### Hive

```sql
SELECT run_id, job_id, duration_mins, duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE status = 'SUCCESS'
```

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins FROM <database>.job_runs WHERE status = 'SUCCESS'
)
SELECT job_id, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X72

### Map

- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: Table `jobs` (job_id, job_name, team, runs, total). Its formulas `runs` and `total` read `job_runs`, Table `by_team`'s formula reads it, and query `busy_jobs` reads it, so it is a CTE in each final that reads it. Its typed rows are written in as literal rows.
- Finals:
  - Table `by_team` (team, team_total), a summary: its only typed column, team, is the one its SUMIFS matches on. Its typed rows are kept, and its final is a GROUP BY of `jobs`.
  - Table `busy_jobs` (job_id, job_name, runs), loaded by query `busy_jobs`, its rows the query's.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet, and the notes in Parameters D1 and Keys D1, which are cells outside a Table.
- Parameters and Keys are empty and no formula reads them, so neither is a source, step or final.
- To fill in: `<database>`, the database name, in each FROM.

### Hive

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(r.runs, 0) AS runs,
    COALESCE(t.total, 0) AS total
  FROM (
    SELECT 1 AS job_id, 'nightly_load' AS job_name, 'data' AS team
    UNION ALL SELECT 2, 'invoice_sync', 'finance'
    UNION ALL SELECT 3, 'report_build', 'finance'
    UNION ALL SELECT 4, 'cache_warm', 'web'
  ) j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
    ON j.job_id = r.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) t
    ON j.job_id = t.job_id
)
SELECT b.team, COALESCE(s.team_total, 0) AS team_total
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') b
LEFT JOIN (SELECT team, SUM(total) AS team_total FROM jobs GROUP BY team) s
  ON b.team = s.team
```

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(r.runs, 0) AS runs,
    COALESCE(t.total, 0) AS total
  FROM (
    SELECT 1 AS job_id, 'nightly_load' AS job_name, 'data' AS team
    UNION ALL SELECT 2, 'invoice_sync', 'finance'
    UNION ALL SELECT 3, 'report_build', 'finance'
    UNION ALL SELECT 4, 'cache_warm', 'web'
  ) j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
    ON j.job_id = r.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) t
    ON j.job_id = t.job_id
)
SELECT job_id, job_name, runs
FROM jobs
WHERE runs >= 3
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X75

### Map

- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: query `long_runs` (run_id, dt, duration_mins), read by query `long_per_day`, so it is a CTE in that final.
- Finals:
  - Table `long_runs` (run_id, dt, duration_mins, over), its rows the query `long_runs`'s, with `over` from the formula `[duration_mins]-15`.
  - Table `long_per_day` (dt, runs), its rows the query `long_per_day`'s.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet, and the notes in Parameters D1 and Keys D1, which are cells outside a Table.
- Parameters and Keys are empty and no formula reads them, so neither is a source, step or final.
- To fill in: `<database>`, the database name, in each FROM.

### Hive

```sql
SELECT run_id, dt, duration_mins, duration_mins - 15 AS `over`
FROM <database>.job_runs
WHERE duration_mins >= 15
```

```sql
WITH long_runs AS (
  SELECT run_id, dt, duration_mins FROM <database>.job_runs WHERE duration_mins >= 15
)
SELECT dt, COUNT(*) AS runs
FROM long_runs
GROUP BY dt
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X76

### Map

- Sources:
  - `jobs` (job_id, job_name, team, region).
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: query `finance_jobs` (job_id, job_name), read by query `finance_runs`, so it is a CTE in that final.
- Finals:
  - Table `finance_jobs` (job_id, job_name, label), its rows the query `finance_jobs`'s, with `label` from the formula `UPPER([job_name])`.
  - Table `finance_runs` (run_id, job_name, duration_mins), its rows the query `finance_runs`'s.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet, and the notes in Parameters D1 and Keys D1, which are cells outside a Table.
- Parameters and Keys are empty and no formula reads them, so neither is a source, step or final.
- To fill in: `<database>`, the database name, in each FROM.

### Hive

```sql
SELECT job_id, job_name, UPPER(job_name) AS label
FROM <database>.jobs
WHERE team = 'finance'
```

```sql
WITH finance_jobs AS (
  SELECT job_id, job_name FROM <database>.jobs WHERE team = 'finance'
)
SELECT r.run_id, f.job_name, r.duration_mins
FROM <database>.job_runs r
JOIN finance_jobs f ON r.job_id = f.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

