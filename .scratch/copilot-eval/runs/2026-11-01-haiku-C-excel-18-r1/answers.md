date: 2026-11-01
arm: C
model: haiku
files: 18-r1

## X01

**1. Map**

- Sources: job_runs (run_id, job_id, duration_mins, dt), read from `<database>.job_runs`.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours). It has a formula column and nothing reads it, so it is a final.
- Values typed over a formula: none. Keys holds no row.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables (no formula reads a fixed value, and no value is typed over a formula); the Steps sheet's cells outside a Table.
- To fill in: `<database>`.

**2. Hive**

Final job_runs:

```sql
SELECT run_id, job_id, duration_mins, dt, duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

**3. Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X02

**1. Map**

- Sources: job_runs (run_id, job_id, status, duration_mins), read from `<database>.job_runs`.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag). Nothing reads it, so it is a final.
- Values typed over a formula: none. Keys holds no row.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables; the Steps sheet's cells outside a Table.
- To fill in: `<database>`.

**2. Hive**

Final job_runs:

```sql
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF(duration_mins > 25 OR job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs
```

**3. Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X03

**1. Map**

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read from `<database>.job_runs`.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs). Nothing reads it, so it is a final.
- Values typed over a formula: none. Keys holds no row.
- Marks:
  - blank: status is blank at run 98, and score reads it, so it is written as COALESCE(status, '').
  - blank: avg_retry_secs is blank at run 98, and mins_per_retry and total_secs read it, so it is written as COALESCE(avg_retry_secs, 0).
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables; the Steps sheet's cells outside a Table.
- To fill in: `<database>`.

**2. Hive**

Final job_runs:

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

**3. Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X04

**1. Map**

- Sources: jobs (job_id, job_name, team, region), read from `<database>.jobs`.
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd). No query loads it and nothing reads it, so it is a final.
- Values typed over a formula: none. Keys holds no row.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables; the Steps sheet's cells outside a Table.
- To fill in: `<database>`.

**2. Hive**

Final jobs:

```sql
SELECT job_id, job_name, team, region,
  CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-', region) AS code,
  LENGTH(job_name) AS name_length,
  ROUND(job_id / 3, 2) AS third,
  PMOD(job_id, 2) AS odd
FROM <database>.jobs
```

**3. Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X05

**1. Map**

- Sources: job_runs (run_id, dt), read from `<database>.job_runs`; region_costs (job_id, cost_cents, region, dt), read from `<database>.region_costs`.
- Steps: none.
- Finals:
  - job_runs (run_id, dt, month, days_since). Nothing reads it, so it is a final.
  - region_costs (job_id, cost_cents, region, dt, day). Nothing reads it, so it is a final.
- Values typed over a formula: none. Keys holds no row.
- Marks:
  - date held as text: region_costs dt holds text such as 20260911, and day reads it as CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)). The result is text as yyyy-mm-dd, not a date.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables; the Steps sheet's cells outside a Table.
- To fill in: `<database>`.

**2. Hive**

Final job_runs:

```sql
SELECT run_id, dt, MONTH(dt) AS month,
  DATEDIFF(dt, '2026-09-01') AS days_since
FROM <database>.job_runs
```

Final region_costs:

```sql
SELECT job_id, cost_cents, region, dt,
  CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS day
FROM <database>.region_costs
```

**3. Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X06

**Map**

- **Sources**: `jobs` (job_id, job_name, team, region), typed, a source only: no formula of its own. `job_runs` (run_id, job_id, duration_mins), its typed columns, read as `<database>.job_runs`.
- **Steps**: none.
- **Finals**: `job_runs` (run_id, job_id, duration_mins, job_name, runs_of_job). job_name reads `jobs` by job_id; runs_of_job counts the rows of `job_runs` that share this row's job_id. Nothing else reads `job_runs`, so it is a final.
- **Value typed over a formula**: none. Keys is empty, so there is no Keys row.
- **Parameters**: empty; no formula uses a fixed value.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet, the D1 notes on Parameters and Keys, and cells outside a Table.
- **To fill in**: `<database>`, in both sources of the final's query.

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

- **Sources**: `jobs` (job_id, job_name, team, region), typed, a source only. `job_runs` (run_id, job_id, status), its typed columns, read as `<database>.job_runs`.
- **Steps**: none.
- **Finals**: `job_runs` (run_id, job_id, status, team, region). team is the jobs row's team for the job_id (VLOOKUP column 3, exact match); region is jobs' region for the job_id (INDEX and MATCH, exact). Nothing else reads `job_runs`, so it is a final.
- **Value typed over a formula**: none. Keys is empty, so there is no Keys row.
- **Parameters**: empty; no formula uses a fixed value.
- **Marks**: none. The blank status on run 98 is kept as NULL, as no formula reads status.
- **Refusals**: none.
- **Left alone**: the Steps sheet, the D1 notes on Parameters and Keys, and cells outside a Table.
- **To fill in**: `<database>`, in both sources of the final's query.

**Hive**

### job_runs

```sql
SELECT r.run_id, r.job_id, r.status, j.team AS team, j.region AS region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X08

**Map**

- **Sources**: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), typed, read as `<database>.job_runs`. Its typed columns only, so a source and never a final on its own; by_job's formulas read it.
- **Steps**: none.
- **Finals**: `by_job` (job_id, total_mins, avg_retry, longest), a summary: its only typed column, job_id, is the one its SUMIFS, AVERAGEIFS and MAXIFS match on. Its final query is a GROUP BY of `job_runs`, its typed rows (job_id 1, 2 and 3) kept. Nothing reads `by_job`, so it is a final.
- **Value typed over a formula**: none. Keys is empty, so there is no Keys row.
- **Parameters**: empty; no formula uses a fixed value.
- **Marks**: none. avg_retry is AVG with no COALESCE, so a job with no match is NULL. The blank avg_retry_secs on run 98 is skipped by AVG, as Excel's AVERAGEIFS skips it, so the column is written as it is.
- **Refusals**: none. The `_xlfn.` prefix on MAXIFS is read past.
- **Left alone**: the Steps sheet, the D1 notes on Parameters and Keys, and cells outside a Table.
- **To fill in**: `<database>`, in the final's query.

**Hive**

### by_job

```sql
SELECT j.job_id,
  COALESCE(s.total_mins, 0) AS total_mins,
  s.avg_retry AS avg_retry,
  COALESCE(s.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total_mins, AVG(avg_retry_secs) AS avg_retry, MAX(duration_mins) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
) s ON j.job_id = s.job_id
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X09

**Map**

- **Sources**: `job_runs` (run_id, job_id, duration_mins, avg_retry_secs), its typed columns, read as `<database>.job_runs`. `jobs` (job_id, job_name, team, region), typed, a source only.
- **Steps**: none.
- **Finals**: `job_runs` (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost). team is jobs' team for the job_id; team_mins is the SUMIFS of duration_mins over this Table's own team; cost is (duration_mins * 60 + avg_retry_secs) * rate. Nothing else reads `job_runs`, so it is a final.
- **Parameters**: `rate` is 0.5, read in as 0.5 in cost.
- **Keys**: `job_runs`, with run_id.
- **Value typed over a formula**: cost where run_id is 97 is typed as 100; written as a CASE on run_id, the Keys row's column.
- **Marks**: blank. The blank avg_retry_secs on run 98 is in cost, which reads it, so it is written as COALESCE(avg_retry_secs, 0) inside cost.
- **Refusals**: none.
- **Left alone**: the Steps sheet, the D1 notes on Parameters and Keys, and cells outside a Table.
- **To fill in**: `<database>`, in both sources of the final's query.

**Hive**

### job_runs

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs,
  j.team AS team,
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

- **Sources**: `job_runs` (run_id, job_id, duration_mins, dt), its typed columns, read as `<database>.job_runs`.
- **Steps**: none.
- **Finals**: `job_runs` (run_id, job_id, duration_mins, dt, hours, sample). hours is duration_mins / 60; sample is refused. Nothing else reads `job_runs`, so it is a final.
- **Value typed over a formula**: hours where run_id is 103 is typed as 9. There is no Keys row (Keys is empty), so the CASE matches the row on every typed column: run_id, job_id, duration_mins and dt.
- **Parameters**: empty; no formula uses a fixed value.
- **Marks**: none.
- **Refusals**: sample, which is RAND() on every row, is refused: `NULL AS sample`, as RAND has no Hive here.
- **Left alone**: the Steps sheet, the D1 notes on Parameters and Keys, and cells outside a Table.
- **To fill in**: `<database>`, in the final's query.

**Hive**

### job_runs

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
  CASE WHEN r.run_id = 103 AND r.job_id = 3 AND r.duration_mins = 30 AND r.dt = '2026-09-24' THEN 9
    ELSE r.duration_mins / 60
  END AS hours,
  NULL AS sample
FROM <database>.job_runs r
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X11

### Map

- **Sources:** none.
- **Steps:** none.
- **Finals:** job_runs (run_id, duration_mins, pick, scaled). No Total Row, no summary.
- **Settings, read by step 4 (never a source, step or final):** Parameters and Keys, both empty, so no formula reads them.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:**
  - pick, `=INDIRECT("B"&ROW())`: INDIRECT is refused, and ROW() hangs on the order of the sheet's rows. NULL AS pick.
  - scaled, `=...*Summary!$C$2`: reads C2 on Summary, a cell outside a Table that isn't a defined name. NULL AS scaled.
- **Left alone:** C2 on Summary (value 3, outside a Table) and the bar chart on Summary.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, duration_mins, NULL AS pick, NULL AS scaled
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X12

### Map

- **Sources:** none.
- **Steps:** none.
- **Finals:** job_runs (run_id, duration_mins, running, loop, with_tax). No Total Row, no summary.
- **Settings, read by step 4 (never a source, step or final):** Parameters and Keys, both empty.
- **Values typed over a formula:** none.
- **Marks:**
  - with_tax reads the defined name tax_rate, which is Summary!$B$3. A defined name for a cell outside a Table: its value 0.2 is written in. Move tax_rate into Parameters.
- **Refusals:**
  - running, `=SUM(OFFSET(...,ROW()-1,1))`: OFFSET is refused, and ROW() hangs on the order of the sheet's rows. NULL AS running.
  - loop, `=job_runs[[#This Row],[loop]]+1`: reads its own column, which is circular. NULL AS loop.
- **Left alone:** B3 on Summary (the 0.2 cell, outside a Table; its value is written in by the mark above).
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, duration_mins, NULL AS running, NULL AS loop, duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X13

### Map

- **Sources:** jobs (job_id, job_name, team, region). Typed columns only, and no query loads it.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, name, doubled). No Total Row, no summary.
- **Settings, read by step 4 (never a source, step or final):** Parameters and Keys, both empty.
- **Values typed over a formula:** none.
- **Marks:**
  - name, `=VLOOKUP(...,jobs,2,TRUE)`: TRUE makes the match approximate. Written as the exact match on job_id.
- **Refusals:**
  - doubled, `=DOUBLE(...)`: DOUBLE is a defined name holding a LAMBDA (`_xlfn.LAMBDA(x,x*2)`), which is refused. NULL AS doubled.
- **Left alone:** none.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT r.run_id, r.job_id, j.job_name AS name, NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X14

### Map

- **Sources:** none.
- **Steps:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, hours). It has a formula column, and by_job's SUMIFS reads job_runs[hours] and job_runs[job_id], so it is a step: a CTE in by_job's query.
- **Finals:** by_job (job_id, total_hours). It is a summary: its only typed column, job_id, is the one its SUMIFS matches on, so its final is a GROUP BY of job_runs, with its typed rows (1, 2, 3) kept. No Total Row.
- **Settings, read by step 4 (never a source, step or final):** Parameters and Keys, both empty.
- **Values typed over a formula:** none.
- **Marks:** none. The blanks on run 98 (status, avg_retry_secs) are read by no formula, so they stay NULL with no mark.
- **Refusals:** none.
- **Left alone:** the PivotTable on sheet "Pivot" (from job_runs, rows job_id, values Sum of duration_mins), which is not converted.
- **To fill in:** `<database>`.

### Hive

```sql
WITH job_runs AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt, duration_mins / 60 AS hours
  FROM <database>.job_runs
)
SELECT b.job_id, COALESCE(s.total_hours, 0) AS total_hours
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) b
LEFT JOIN (SELECT job_id, SUM(hours) AS total_hours FROM job_runs GROUP BY job_id) s
  ON b.job_id = s.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X15

### Map

- **Sources:** none.
- **Steps:** none.
- **Finals:** tblRuns (Run ID, Job ID, Duration (mins), Hours), written as `<run_id>`, `<job_id>`, `<duration_mins>` and `hours`. No Total Row, no summary.
- **Settings, read by step 4 (never a source, step or final):** Parameters and Keys, both empty.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>`, `<run_id>`, `<job_id>` and `<duration_mins>`, the headers Run ID, Job ID and Duration (mins), which are not plain names.

### Hive

```sql
SELECT <run_id>, <job_id>, <duration_mins>, <duration_mins> / 60 AS hours
FROM <database>.tblRuns
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X16

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Typed only; read by Power Query `long_runs`.
- **Steps:** none.
- **Finals:** Table `long_runs` (run_id, job_id, minutes, hours). It is loaded by Power Query `long_runs`, and no formula reads it, so it is a final whose rows are that query's.
- **Power Query `long_runs`:** the query behind final `long_runs`. Its steps are the final's Hive below; it is not a final or a step of its own.
- **Typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** none. Parameters and Keys are empty, so they have no role and need no rows.
- **To fill in:** `<database>`.

### Hive

```sql
-- long_runs
SELECT run_id, job_id, duration_mins AS minutes, duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X17

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Typed only.
- **Steps:** Power Query `ok_runs` (connection only), which keeps job_runs' rows with status = 'SUCCESS'. Query `ok_by_job` reads it, so it is a CTE in the query of final `ok_by_job`.
- **Finals:** Table `ok_by_job` (job_id, runs, total_mins). It is loaded by Power Query `ok_by_job`, and no formula reads it, so it is a final whose rows are that query's.
- **Typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** none. Parameters and Keys are empty, so they have no role and need no rows.
- **To fill in:** `<database>`.

### Hive

```sql
-- ok_by_job
WITH ok_runs AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X18

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and `jobs` (job_id, job_name, team, region). Both typed only; both read by Power Query `top_runs`.
- **Steps:** none.
- **Finals:** Table `top_runs` (run_id, job_name, duration_mins). It is loaded by Power Query `top_runs`, and no formula reads it, so it is a final whose rows are that query's.
- **Typed over a formula:** none.
- **Marks:** none. The two runs at 30 minutes both fall inside the top 3, so the tie does not cut a row.
- **Refusals:** none.
- **Left alone:** none. Parameters and Keys are empty, so they have no role and need no rows.
- **To fill in:** `<database>`.

### Hive

```sql
-- top_runs
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC
LIMIT 3
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X19

### Map

- **Sources:** `scheduler_runs` (run_id, job_id, dt), typed only. And `job_runs` (run_id, job_id, dt), read by Power Query `all_runs` from the Sql.Database named under Marks.
- **Steps:** none.
- **Finals:** Table `all_runs` (run_id, job_id, dt). It is loaded by Power Query `all_runs`, and no formula reads it, so it is a final whose rows are that query's: scheduler_runs' rows, then job_runs' rows, stacked.
- **Typed over a formula:** none.
- **Marks:** Power Query `all_runs` reads `Sql.Database("dwh01", "ops")`, table `job_runs`, written as `<database>.job_runs`. Check it is the table you mean.
- **Refusals:** Power Query `holidays` reads Web.Contents, so it is left out. It loads nothing and nothing reads it.
- **Left alone:** none. Parameters and Keys are empty, so they have no role and need no rows.
- **To fill in:** `<database>`.

### Hive

```sql
-- all_runs
SELECT run_id, job_id, dt FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X20

### Map

- **Sources:** `run_alerts` (alert_id, run_id, severity, dt). Typed only; read by Power Query `alert_pivot`.
- **Steps:** none.
- **Finals:** Table `alert_pivot` (run_id, high, low). It is loaded by Power Query `alert_pivot`, and no formula reads it, so it is a final whose rows are that query's, one per run_id.
- **Typed over a formula:** none.
- **Marks:** Table.Pivot. Its columns `high` and `low` are fixed from the sample; a severity not in the sample gets no column. Each count is written as THEN 1.
- **Refusals:** none.
- **Left alone:** none. Parameters and Keys are empty, so they have no role and need no rows.
- **To fill in:** `<database>`.

### Hive

```sql
-- alert_pivot
SELECT run_id,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
WHERE run_id = 97 OR run_id = 101
GROUP BY run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X41

**Map**

- Sources: job_runs (run_id, job_id, status, duration_mins), read as `<database>.job_runs`.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). It has formula columns, and no query or other Table reads it, so it is a final.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, as cells outside a Table. Parameters and Keys are empty and have no role; no formula uses a fixed value, and no Keys row is needed.
- To fill in: `<database>`.

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

- Sources: jobs (job_id, job_name), read as `<database>.jobs`; job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
- Steps: none.
- Finals: jobs (job_id, job_name, runs, avg_mins, id_order). Its formula columns read job_runs, and nothing reads jobs, so it is a final.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, as cells outside a Table. Parameters and Keys are empty and have no role; no Keys row is needed.
- To fill in: `<database>`.

**Hive**

### jobs

```sql
SELECT j.job_id, j.job_name,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS runs, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) c ON j.job_id = c.job_id
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X43

**Map**

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`; jobs (job_id, job_name, team, region), read as `<database>.jobs`.
- Steps: none. Power Query "busy_teams" and Power Query "statuses" are each read by no query or formula, and each loads a Table, so neither is a step.
- Finals: busy_teams (team, runs, shortest, avg_mins), its rows the rows of Power Query "busy_teams"; statuses (job_id, status), its rows the rows of Power Query "statuses".
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, as cells outside a Table. Parameters and Keys are empty and have no role.
- To fill in: `<database>`.

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

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`; jobs (job_id, job_name, team, region), read as `<database>.jobs`; scheduler_runs (run_id, job_id, dt), read as `<database>.scheduler_runs`.
- Steps: none. Power Query "jobs_with_runs" and Power Query "never_scheduled" are each read by no query or formula, and each loads a Table, so neither is a step.
- Finals: jobs_with_runs (run_id, job_name), its rows the rows of Power Query "jobs_with_runs"; never_scheduled (job_id, job_name, team), its rows the rows of Power Query "never_scheduled".
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, as cells outside a Table. Parameters and Keys are empty and have no role.
- To fill in: `<database>`.

**Hive**

### jobs_with_runs

```sql
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON r.job_id = j.job_id
```

### never_scheduled

```sql
SELECT j.job_id, j.job_name, j.team
FROM <database>.jobs j
LEFT JOIN <database>.scheduler_runs s ON j.job_id = s.job_id
WHERE s.job_id IS NULL
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X45

**Map**

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`; scheduler_runs (run_id, job_id, dt), read as `<database>.scheduler_runs`.
- Steps: none. Power Query "run_days" and Power Query "matched" are each read by no query or formula, and each loads a Table, so neither is a step.
- Finals: run_days (run_id, dt), its rows the rows of Power Query "run_days"; matched (run_id, job_id, dt, status), its rows the rows of Power Query "matched".
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, as cells outside a Table. Parameters and Keys are empty and have no role.
- To fill in: `<database>`.

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

- **Sources:** job_runs (run_id, job_id, status, duration_mins, dt), typed, read from `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins). The formula columns are long_in_job, not_ok, failed_in_job and running_mins. No Total Row.
- **Typed over a formula:** none. Keys holds no row, and none is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table). Parameters and Keys are empty, no formula reads them, and they are never a source, step or final.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT
  run_id,
  job_id,
  status,
  duration_mins,
  dt,
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

- **Sources:** job_runs (run_id, job_id, duration_mins), typed, read from `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job); job_runs (Total Row) (duration_mins, share), the Total Row's two totals.
- **Typed over a formula:** none. Keys holds no row, and none is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table). Parameters and Keys are empty, no formula reads them, and they are never a source, step or final.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT
  run_id,
  job_id,
  duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

```sql
WITH job_runs AS (
  SELECT
    run_id,
    job_id,
    duration_mins,
    duration_mins / SUM(duration_mins) OVER () AS share,
    duration_mins - AVG(duration_mins) OVER () AS vs_avg,
    RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
  FROM <database>.job_runs
)
SELECT SUM(duration_mins) AS duration_mins, SUM(share) AS share
FROM job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X53

### Map

- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), typed, read from `<database>.job_runs`. Only job_id and duration_mins are read by a formula.
- **Steps:** none.
- **Finals:** by_job, a summary (job_id, total_mins, runs, longest), keeping its typed rows, its only typed column being the one its SUMIFS, COUNTIFS and MAXIFS match on; by_job (Total Row) (total_mins, runs, longest), the Total Row's three totals.
- **Typed over a formula:** none. Keys holds no row, and none is needed.
- **Marks:** none.
- **Refusals:** none. MAXIFS converts as MAX, with its `_xlfn.` prefix read past.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table). Parameters and Keys are empty, no formula reads them, and they are never a source, step or final.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT j.job_id, COALESCE(g.total_mins, 0) AS total_mins, COALESCE(g.runs, 0) AS runs, COALESCE(g.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total_mins, COUNT(*) AS runs, MAX(duration_mins) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
) g
  ON j.job_id = g.job_id
```

```sql
WITH by_job AS (
  SELECT j.job_id, COALESCE(g.total_mins, 0) AS total_mins, COALESCE(g.runs, 0) AS runs, COALESCE(g.longest, 0) AS longest
  FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
  LEFT JOIN (
    SELECT job_id, SUM(duration_mins) AS total_mins, COUNT(*) AS runs, MAX(duration_mins) AS longest
    FROM <database>.job_runs
    GROUP BY job_id
  ) g
    ON j.job_id = g.job_id
)
SELECT SUM(total_mins) AS total_mins, SUM(runs) AS runs, MAX(longest) AS longest
FROM by_job
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X54

### Map

- **Sources:** job_runs (run_id, dt), typed, read from `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label). The formula columns are the last seven. No Total Row.
- **Typed over a formula:** none. Keys holds no row, and none is needed.
- **Marks:** a_month_on: EDATE is ADD_MONTHS, marked: a month's end stays one. No dt in the sample is a month's last day, so no row differs from Excel.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table). Parameters and Keys are empty, no formula reads them, and they are never a source, step or final.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT
  run_id,
  dt,
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

- **Sources:** jobs (job_id, job_name, team, region), typed, read from `<database>.jobs`.
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens). The formula columns are the last five. No Total Row.
- **Typed over a formula:** none. Keys holds no row, and none is needed.
- **Marks:** none.
- **Refusals:** none. The `_xlfn.` prefix on TEXTJOIN is read past.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table). Parameters and Keys are empty, no formula reads them, and they are never a source, step or final.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT
  job_id,
  job_name,
  team,
  region,
  INITCAP(REPLACE(job_name, '_', ' ')) AS title,
  CONCAT_WS('/', team, region) AS tag,
  CONCAT(region, '-', job_id) AS code,
  INSTR(LOWER(job_name), LOWER('SYNC')) > 0 AS has_sync,
  CAST(CONCAT(job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X56

### Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs), typed; scheduler_runs (run_id, job_id, dt), typed.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on). No query loads it and no other Table or query reads it.
- Values typed over a formula: none. Parameters and Keys are empty, and every row of job_runs holds its formulas.
- Marks:
  - blank: weighted reads avg_retry_secs, which is blank in run 98, so it is written COALESCE(avg_retry_secs, 0).
  - no_status reads status through ISBLANK, so status is written as it is, with no COALESCE.
  - text: scheduled_on takes the text 'unscheduled', so dt is cast to STRING.
- Refusals: none.
- Left alone: the Steps sheet's cells outside a Table; Parameters and Keys, which are empty and read by no formula.
- To fill in: `<database>`, in each read of job_runs and scheduler_runs.

### Hive
```sql
-- Final: job_runs
SELECT
  r.run_id,
  r.job_id,
  r.status,
  r.duration_mins,
  r.avg_retry_secs,
  (r.status IS NULL) AS no_status,
  FLOOR(r.duration_mins / 7) AS weeks,
  GREATEST(r.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(r.duration_mins) OVER () AS spread,
  SUM(r.duration_mins * COALESCE(r.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(CAST(s.dt AS STRING), 'unscheduled') AS scheduled_on
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs s
  ON r.run_id = s.run_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X57

### Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), typed; jobs (job_id, job_name, team, region), typed.
- Steps: none.
- Finals:
  - picked (run_id, job_id, status, avg_retry_secs, status_lc), loaded by query picked. No formula reads it, so its rows are the query's.
  - ran_jobs (job_id, job_name, team, region), loaded by query ran_jobs. No formula reads it, so its rows are the query's.
- Values typed over a formula: none. The workbook has no formula column; Parameters and Keys are empty.
- Marks:
  - blank: query picked replaces the blank avg_retry_secs (run 98) with 0 through Table.ReplaceValue, so it is written COALESCE(avg_retry_secs, 0). status stays blank as NULL, and status_lc follows it.
- Refusals: none.
- Left alone: the Steps sheet's cells outside a Table; Parameters and Keys, which are empty.
- To fill in: `<database>`, in each read of job_runs and jobs.

### Hive
```sql
-- Final: picked
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
-- Final: ran_jobs
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r
  ON j.job_id = r.job_id
WHERE j.job_name LIKE '%a%'
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X58

### Map
- Sources:
  - job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), typed.
  - jobs (job_id, job_name, team, region), typed.
  - scheduler_runs (run_id, job_id, dt), typed.
  - region_budgets (job_id, budget_cents, region), typed.
- Steps: none.
- Finals:
  - job_regions (job_id, region), loaded by query job_regions.
  - numbered (run_id, dt, duration_mins, n), loaded by query numbered.
  - days_per_job (job_id, days), loaded by query days_per_job.
  - unrun (run_id, job_id), loaded by query unrun.
  - measures (run_id, measure, amount), loaded by query measures.
  - No formula reads any of these Tables, so each one's rows are its query's.
- Values typed over a formula: none. The workbook has no formula column; Parameters and Keys are empty.
- Marks:
  - blank: measures drops run 98's blank avg_retry_secs, as M drops a null there, so no row for 98 in measures.
  - order: days_per_job sorts with no FirstN or index after it, so no ORDER BY is written, and the order is dropped.
  - numbered: n is ROW_NUMBER() over the sort of query numbered, ordered by duration_mins descending then run_id ascending, as the index follows the sort.
- Refusals: none.
- Left alone: the Steps sheet's cells outside a Table; Parameters and Keys, which are empty.
- To fill in: `<database>`, in each read of job_runs, jobs, scheduler_runs and region_budgets.

### Hive
```sql
-- Final: job_regions
SELECT j.job_id, d.region
FROM (SELECT job_id FROM <database>.jobs) j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) d
```
```sql
-- Final: numbered
SELECT
  run_id,
  dt,
  duration_mins,
  ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC) AS n
FROM <database>.job_runs
```
```sql
-- Final: days_per_job
SELECT job_id, COUNT(DISTINCT dt) AS days
FROM <database>.job_runs
GROUP BY job_id
```
```sql
-- Final: unrun
SELECT DISTINCT s.run_id, s.job_id
FROM <database>.scheduler_runs s
LEFT JOIN <database>.job_runs r
  ON s.run_id = r.run_id AND s.job_id = r.job_id
WHERE r.run_id IS NULL
```
```sql
-- Final: measures
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
- Sources:
  - job_runs (run_id, job_id, duration_mins, dt), typed; its formula columns are the Step below.
  - jobs (job_id, job_name, team, region), typed.
  - run_alerts (alert_id, run_id, severity, dt), typed.
- Steps:
  - job_runs (run_id, job_id, duration_mins, dt, team, alerts, running_mins). It is read by the formulas of by_team and by query noisy_runs, so it is a CTE in each final that reads it. team is the XLOOKUP of jobs, alerts is the COUNTIF of run_alerts, and running_mins is the SUMIFS running total over its own rows, ties included.
- Finals:
  - by_team (team, total_mins, alerted_runs), a summary: its only typed column is team, matched by its SUMIFS and COUNTIFS. Its final query is a GROUP BY of job_runs, with its typed rows kept (data, finance).
  - by_team (Total Row): one row, total_mins and alerted_runs, read from the by_team final.
  - noisy_runs (run_id, team, alerts, running_mins), loaded by query noisy_runs. No formula reads it, so its rows are the query's.
- Values typed over a formula: none. Every row of job_runs holds its formulas; Parameters and Keys are empty.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet's cells outside a Table; Parameters and Keys, which are empty.
- To fill in: `<database>`, in each read of job_runs, jobs and run_alerts.

### Hive
```sql
-- Final: by_team (summary)
WITH job_runs AS (
  SELECT
    r.run_id,
    r.job_id,
    r.duration_mins,
    r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j
    ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
)
SELECT t.team,
  COALESCE(s.total_mins, 0) AS total_mins,
  COALESCE(c.alerted_runs, 0) AS alerted_runs
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance') t
LEFT JOIN (SELECT team, SUM(duration_mins) AS total_mins FROM job_runs GROUP BY team) s
  ON t.team = s.team
LEFT JOIN (SELECT team, COUNT(*) AS alerted_runs FROM job_runs WHERE alerts > 0 GROUP BY team) c
  ON t.team = c.team
```
```sql
-- Final: by_team (Total Row)
WITH job_runs AS (
  SELECT
    r.run_id,
    r.job_id,
    r.duration_mins,
    r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j
    ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
),
by_team AS (
  SELECT t.team,
    COALESCE(s.total_mins, 0) AS total_mins,
    COALESCE(c.alerted_runs, 0) AS alerted_runs
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
-- Final: noisy_runs
WITH job_runs AS (
  SELECT
    r.run_id,
    r.job_id,
    r.duration_mins,
    r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_mins
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
- Sources:
  - job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), typed.
  - jobs (job_id, job_name, team, region), typed.
  - region_budgets (job_id, budget_cents, region), typed.
- Steps:
  - base (run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name, region), Power Query base, connection only. It is read by queries by_region and top_runs, so it is a CTE in each of them. job_name comes from jobs, an inner join; region comes from region_budgets, a left join.
- Finals:
  - by_region (region, total_mins, runs, share), loaded by query by_region. share is a formula column, total_mins / SUM(total_mins) OVER (), over the Table's rows only. No other formula or query reads the Table, so its rows are the query's.
  - by_region (Total Row): one row, total_mins only; the label Total and the blank runs and share cells are left out.
  - top_runs (run_id, job_name, region), loaded by query top_runs. No formula reads it, so its rows are the query's.
- Values typed over a formula: none. Parameters and Keys are empty.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet's cells outside a Table; Parameters and Keys, which are empty.
- To fill in: `<database>`, in each read of job_runs, jobs and region_budgets.

### Hive
```sql
-- Final: by_region
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
SELECT g.region, g.total_mins, g.runs,
  g.total_mins / SUM(g.total_mins) OVER () AS share
FROM (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) g
```
```sql
-- Final: by_region (Total Row)
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
by_region AS (
  SELECT g.region, g.total_mins, g.runs,
    g.total_mins / SUM(g.total_mins) OVER () AS share
  FROM (
    SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
    FROM base
    GROUP BY region
    HAVING COUNT(*) >= 2
  ) g
)
SELECT SUM(total_mins) AS total_mins
FROM by_region
```
```sql
-- Final: top_runs
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

**Sources**
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed columns only, and no query loads it.

**Steps**
- Power Query `ok_runs`: keeps job_runs' SUCCESS rows as run_id, job_id, duration_mins. Query `ok_by_job` reads it, so it is a CTE in that final's block.

**Finals**
- Table `ok_runs` (run_id, job_id, duration_mins, hours): its rows are query `ok_runs`' rows. `hours` is its formula column, `duration_mins / 60`. Its formula reads only its own row, and no other formula reads the Table, so it is a final.
- Table `ok_by_job` (job_id, total_mins): its rows are query `ok_by_job`'s, the SUM of duration_mins per job_id over step `ok_runs`.

**Values typed over a formula:** none.

**Marks:** none.

**Refusals:** none.

**Left alone:** Table `Parameters` and Table `Keys`, both empty. No formula uses a fixed value and no value is typed over a formula, so neither has a role.

**To fill in:** `<database>`, in each block.

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
SELECT job_id, SUM(duration_mins) AS total_mins FROM ok_runs GROUP BY job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X72

### Map

**Sources**
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed columns only, and no query loads it.

**Steps**
- Table `jobs` (job_id, job_name, team, runs, total): a formula column of Table `by_team` reads its `total`, and query `busy_jobs` reads it. Its typed rows are written inline in each block that reads it. `runs` is COUNTIF over `job_runs`, `total` is SUMIF over `job_runs`, each COALESCE to 0 as Excel gives 0 where nothing matches.

**Finals**
- Table `by_team` (team, team_total): a summary, since its only typed column, team, is the one its SUMIFS matches on. Its typed rows are kept (data, finance, web), and `team_total` is the SUM of step `jobs`' total for each team, COALESCE to 0.
- Table `busy_jobs` (job_id, job_name, runs): its rows are query `busy_jobs`' rows, the step `jobs` rows with runs of 3 or more, as job_id, job_name, runs. No formula reads it, so it is a final.

**Values typed over a formula:** none.

**Marks:** none.

**Refusals:** none.

**Left alone:** Table `Parameters` and Table `Keys`, both empty. No formula uses a fixed value and no value is typed over a formula, so neither has a role.

**To fill in:** `<database>`, in each block.

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
SELECT c.team, COALESCE(s.team_total, 0) AS team_total
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') c
LEFT JOIN (SELECT team, SUM(total) AS team_total FROM jobs GROUP BY team) s
  ON c.team = s.team
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

**Sources**
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed columns only, and no query loads it.

**Steps**
- Power Query `long_runs`: keeps job_runs' rows with duration_mins of 15 or more, as run_id, dt, duration_mins. Query `long_per_day` reads it, so it is a CTE in that final's block.

**Finals**
- Table `long_runs` (run_id, dt, duration_mins, over): its rows are query `long_runs`' rows. `over` is its formula column, `duration_mins - 15`. It reads only its own row, and no other formula reads the Table, so it is a final.
- Table `long_per_day` (dt, runs): its rows are query `long_per_day`'s, the COUNT of step `long_runs` per dt.

**Values typed over a formula:** none.

**Marks:** `over` is a reserved word in Hive, so its alias is in backticks. The header stays `over`.

**Refusals:** none.

**Left alone:** Table `Parameters` and Table `Keys`, both empty. No formula uses a fixed value and no value is typed over a formula, so neither has a role.

**To fill in:** `<database>`, in each block.

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
SELECT dt, COUNT(*) AS runs FROM long_runs GROUP BY dt
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X76

### Map

**Sources**
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed columns only, and no query loads it.
- `jobs` (job_id, job_name, team, region): typed columns only, and no query loads it. Query `finance_jobs` reads it.

**Steps**
- Power Query `finance_jobs`: keeps jobs' rows with team "finance", as job_id, job_name. Query `finance_runs` reads it in a join, so it is a CTE in that final's block.

**Finals**
- Table `finance_jobs` (job_id, job_name, label): its rows are query `finance_jobs`' rows. `label` is its formula column, `UPPER(job_name)`. It reads only its own row, and no other formula reads the Table, so it is a final.
- Table `finance_runs` (run_id, job_name, duration_mins): its rows are query `finance_runs`', job_runs inner-joined to step `finance_jobs` on job_id, keeping run_id, job_name, duration_mins.

**Values typed over a formula:** none.

**Marks:** none.

**Refusals:** none.

**Left alone:** Table `Parameters` and Table `Keys`, both empty. No formula uses a fixed value and no value is typed over a formula, so neither has a role.

**To fill in:** `<database>`, in each block.

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

