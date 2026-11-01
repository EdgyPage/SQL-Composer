date: 2026-11-01
arm: C
model: haiku
files: 18-r3

## X01

### Map
- **Sources:** job_runs (run_id, job_id, duration_mins, dt), read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, duration_mins, dt, duration_hours).
- **Parameters and Keys:** empty Tables, neither a source, step nor final; no value read, none typed over.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, job_id, duration_mins, dt,
  duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X02

### Map
- **Sources:** job_runs (run_id, job_id, status, duration_mins), read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, slow_job1, flag).
- **Parameters and Keys:** empty Tables, neither a source, step nor final; no value read, none typed over.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF(duration_mins > 25 OR job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X03

### Map
- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs).
- **Parameters and Keys:** empty Tables, neither a source, step nor final; no value read, none typed over.
- **Values typed over a formula:** none.
- **Marks:**
  - blank: status in row 98 is blank and score reads it, so it is written `COALESCE(status, '')`.
  - blank: avg_retry_secs in row 98 is blank and mins_per_retry and total_secs read it, so it is written `COALESCE(avg_retry_secs, 0)`.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X04

### Map
- **Sources:** jobs (job_id, job_name, team, region), read as `<database>.jobs`.
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, team, region, code, name_length, third, odd).
- **Parameters and Keys:** empty Tables, neither a source, step nor final; no value read, none typed over.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT job_id, job_name, team, region,
  CONCAT(CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-'), region) AS code,
  LENGTH(job_name) AS name_length,
  ROUND(job_id / 3, 2) AS third,
  PMOD(job_id, 2) AS odd
FROM <database>.jobs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X05

### Map
- **Sources:**
  - job_runs (run_id, dt), read as `<database>.job_runs`.
  - region_costs (job_id, cost_cents, region, dt), read as `<database>.region_costs`.
- **Steps:** none.
- **Finals:**
  - job_runs (run_id, dt, month, days_since).
  - region_costs (job_id, cost_cents, region, dt, day).
- **Parameters and Keys:** empty Tables, neither a source, step nor final; no value read, none typed over.
- **Values typed over a formula:** none.
- **Marks:**
  - date held as text: region_costs dt holds values such as 20260911, which day reads, so day is written `CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2))` and gives a text date. Check dt's Hive type.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- **To fill in:** `<database>`.

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

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X06

### Map

- Sources: jobs (job_id, job_name, team, region), read as `<database>.jobs`. All typed, no formula.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job). It holds formula columns, and only its own columns read it, so nothing else makes it a step.
- Settings, read by step 4, not a source, step or final: Parameters (empty, no formula uses a fixed value) and Keys (empty, no value typed over a formula).
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`, in the job_runs query.

### Hive

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  j.job_name AS job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X07

### Map

- Sources: jobs (job_id, job_name, team, region), read as `<database>.jobs`. All typed, no formula.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, team, region). Its formula columns read jobs only, and nothing else reads job_runs, so it is a final.
- Settings, read by step 4, not a source, step or final: Parameters (empty, no formula uses a fixed value) and Keys (empty, no value typed over a formula).
- Values typed over a formula: none.
- Marks: none. The blank status on the run_id 98 row is in a column no formula reads, so it stays as it is.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`, in the job_runs query.

### Hive

```sql
SELECT r.run_id, r.job_id, r.status,
  j.team AS team,
  j.region AS region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X08

### Map

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`. All typed, and no Table's formula is read by it except by_job's, which is a final reading a source.
- Steps: none.
- Finals: by_job (job_id, total_mins, avg_retry, longest), a summary: its only typed column, job_id, is the column its SUMIFS, AVERAGEIFS and MAXIFS match on. Its typed job_ids 1, 2 and 3 are typed in as its groups, and job_runs is read. No Total Row.
- Settings, read by step 4, not a source, step or final: Parameters (empty) and Keys (empty, no value typed over a formula).
- Values typed over a formula: none.
- Marks: none. The blank avg_retry_secs on the run_id 98 row is read by AVERAGEIFS, an -IFS form, so the column is written as it is and the blank is skipped, as AVG does.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`, in the by_job query.

### Hive

```sql
SELECT j.job_id,
  COALESCE(c.total_mins, 0) AS total_mins,
  c.avg_retry AS avg_retry,
  COALESCE(c.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id,
    SUM(duration_mins) AS total_mins,
    AVG(avg_retry_secs) AS avg_retry,
    MAX(duration_mins) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
) c
  ON j.job_id = c.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X09

### Map

- Sources: jobs (job_id, job_name, team, region), read as `<database>.jobs`. All typed, no formula.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost). Only its own formulas read it, and no other Table or query does, so it is a final.
- Settings, read by step 4, not a source, step or final: Parameters (rate, 0.5), read in as 0.5 where cost reads it; Keys (job_runs, run_id).
- Values typed over a formula: cost where run_id is 97, typed as 100. Matched on run_id, the Keys row's column.
- Marks: blank. avg_retry_secs is blank on the run_id 98 row, and cost reads it in arithmetic, so it is written as COALESCE(avg_retry_secs, 0).
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`, in the job_runs query.

### Hive

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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X10

### Map

- Sources: none.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample). Its formula columns read only its own columns, and nothing else reads it, so it is a final.
- Settings, read by step 4, not a source, step or final: Parameters (empty) and Keys (empty). No Keys row names job_runs, so the typed-over value is matched on every typed column of its row: run_id, job_id, duration_mins and dt.
- Values typed over a formula: hours where run_id is 103, typed as 9.
- Marks: none.
- Refusals: sample, from `=RAND()`. NULL AS sample, as RAND gives a new random value on every calculation, so no Hive gives the same values.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`, in the job_runs query.

### Hive

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24' THEN 9
    ELSE duration_mins / 60
  END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X11

### Map

- **Sources:** none.
- **Steps:** none.
- **Finals:** `job_runs` (run_id, duration_mins, pick, scaled). It has formula columns and nothing reads it, so it is a final.
- **Values typed over a formula:** none. Parameters and Keys are empty.
- **Marks:** none.
- **Refusals:**
  - `pick`: `INDIRECT`, which has no Hive here. `NULL AS pick`.
  - `scaled`: reads `Summary!$C$2`, a cell outside a Table that is not a defined name. `NULL AS scaled`.
- **Left alone:** the bar chart on `Summary`; the cell `Summary!C2` (a cell outside a Table); the Steps sheet (the guide, not a Table); Parameters and Keys, empty settings Tables, never a source, step or final.
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
- **Finals:** `job_runs` (run_id, duration_mins, running, loop, with_tax). It has formula columns and nothing reads it, so it is a final.
- **Values typed over a formula:** none. Parameters and Keys are empty.
- **Marks:**
  - `with_tax`: reads the defined name `tax_rate`, which is `Summary!$B$3` holding 0.2. Written as its value, `0.2`. Move `tax_rate` into Parameters (name `tax_rate`, value `0.2`).
- **Refusals:**
  - `running`: `OFFSET`, and `ROW()`, which hangs on the order of the sheet's rows. `NULL AS running`.
  - `loop`: reads its own column, so it is circular. `NULL AS loop`.
- **Left alone:** the cell `Summary!B3` (a cell outside a Table, its value written in through `tax_rate`); the Steps sheet (the guide, not a Table); Parameters and Keys, empty settings Tables.
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

- **Sources:** `jobs` (job_id, job_name, team, region). It has only typed columns and job_runs reads it, so it is a source, read as `<database>.jobs`.
- **Steps:** none.
- **Finals:** `job_runs` (run_id, job_id, name, doubled). It has formula columns and nothing reads it, so it is a final.
- **Values typed over a formula:** none. Parameters and Keys are empty.
- **Marks:**
  - `name`: `VLOOKUP(..., TRUE)` is an approximate match. Written as the exact match on `job_id`, with column 2 (`job_name`). Named as a mark.
- **Refusals:**
  - `doubled`: `DOUBLE` is a defined name holding a LAMBDA, which is refused. `NULL AS doubled`.
- **Left alone:** the Steps sheet (the guide, not a Table); Parameters and Keys, empty settings Tables.
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
- **Steps:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt, hours). `by_job`'s formula reads its `hours` column, so it is a step. It is a CTE in the final that reads it, read as `<database>.job_runs`.
- **Finals:** `by_job` (job_id, total_hours), a summary. Its only typed column, job_id, is the one its SUMIFS matches on. Its typed job_ids 1, 2 and 3 are typed in as the groups, and `job_runs` is read.
- **Values typed over a formula:** none. Parameters and Keys are empty.
- **Marks:** none. The blanks in status and avg_retry_secs on row 98 feed no formula, so no COALESCE is written for them.
- **Refusals:** none.
- **Left alone:** the PivotTable on sheet `Pivot`, from job_runs; the Steps sheet (the guide, not a Table); Parameters and Keys, empty settings Tables.
- **To fill in:** `<database>`.

### Hive

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

- **Sources:** none.
- **Steps:** none.
- **Finals:** `tblRuns` (`<run_id>`, `<job_id>`, `<duration_mins>`, Hours). It has a formula column and nothing reads it, so it is a final. The headers Run ID, Job ID and Duration (mins) are not plain names, so they are written in snake case in brackets. `Hours` is plain and kept.
- **Values typed over a formula:** none. Parameters and Keys are empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet (the guide, not a Table); Parameters and Keys, empty settings Tables.
- **To fill in:** `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`.

### Hive

```sql
SELECT <run_id>, <job_id>, <duration_mins>, <duration_mins> / 60 AS Hours
FROM <database>.tblRuns
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X16

### Map

- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). A Table of typed columns only, and no query loads it.
- **Steps:** none.
- **Finals:** long_runs (run_id, job_id, minutes, hours), the Table long_runs. Power Query long_runs loads it, no other Table's formula or query reads it, so the Table is a final, its rows the query's.
- **Query long_runs:** it names no other query (only the Table job_runs), so it is the final's query, not a step.
- **Parameters and Keys:** both empty. No fixed value is read, no value is typed over a formula, and no Keys row is needed. Neither is a source, step or final.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet (cells outside a Table).
- **To fill in:** `<database>`.

### Hive

#### long_runs

```sql
SELECT run_id, job_id, duration_mins AS minutes, duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X17

### Map

- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). A Table of typed columns only.
- **Steps:** ok_runs, the Power Query with connection only. Query ok_by_job's M names it (`Source = ok_runs`), so it is a step, a CTE in ok_by_job's final, and not a final of its own.
- **Finals:** ok_by_job (job_id, runs, total_mins), the Table ok_by_job, loaded by Power Query ok_by_job. No other Table's formula or query reads it, so its rows are the query's.
- **Parameters and Keys:** both empty. Neither is a source, step or final.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet (cells outside a Table).
- **To fill in:** `<database>`.

### Hive

#### ok_by_job

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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X18

### Map

- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (job_id, job_name, team, region). Both are Tables of typed columns, and no query loads either.
- **Steps:** none.
- **Finals:** top_runs (run_id, job_name, duration_mins), the Table top_runs, loaded by Power Query top_runs. Its rows are the query's.
- **Parameters and Keys:** both empty. Neither is a source, step or final.
- **Values typed over a formula:** none.
- **Marks:** Table.Sort gives no tie-break. Runs 97 and 103 both have 30 minutes, so their order in Hive is not fixed and may differ from the sample. The set of three rows is the same.
- **Refusals:** none.
- **Left alone:** the Steps sheet (cells outside a Table).
- **To fill in:** `<database>`.

### Hive

#### top_runs

```sql
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

- **Sources:** scheduler_runs (run_id, job_id, dt), a Table of typed columns only. job_runs (run_id, job_id, dt after the select), read by Power Query all_runs from `Sql.Database("dwh01", "ops")`. It is outside this workbook, so it is read as `<database>.job_runs` and named below for you to check.
- **Steps:** none. The steps of Power Query all_runs are one query's steps.
- **Finals:** all_runs (run_id, job_id, dt), the Table all_runs, loaded by Power Query all_runs. Its rows are the query's.
- **Left out:** Power Query holidays, which has connection only and no query reads it. It reads `Web.Contents`, a web source, so it is refused and left out.
- **Parameters and Keys:** both empty. Neither is a source, step or final.
- **Values typed over a formula:** none.
- **Marks:** the `Sql.Database` read of job_runs is read as `<database>.job_runs`. Check that it is the same table as ops.job_runs on dwh01.
- **Refusals:** the holidays query, left out (`Web.Contents`, a web source).
- **Left alone:** the Steps sheet (cells outside a Table).
- **To fill in:** `<database>`.

### Hive

#### all_runs

```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X20

### Map

- **Sources:** run_alerts (alert_id, run_id, severity, dt), a Table of typed columns only, and no query loads it.
- **Steps:** none. The steps Two, Kept, Counted and Pivoted are all inside query alert_pivot.
- **Finals:** alert_pivot (run_id, high, low), the Table alert_pivot, loaded by Power Query alert_pivot. Its rows are the query's.
- **Parameters and Keys:** both empty. Neither is a source, step or final.
- **Values typed over a formula:** none.
- **Marks:** Table.Pivot. The columns high and low are fixed at the severities the sample holds (high and low, from the rows kept for runs 97 and 101). A severity added later gets no column. NULL where a run has no row of a severity, as M leaves it.
- **Refusals:** none.
- **Left alone:** the Steps sheet (cells outside a Table).
- **To fill in:** `<database>`.

### Hive

#### alert_pivot

```sql
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

### Map
- **Sources:** none. job_runs holds formula columns, so it is a final, not a source.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). Its typed columns are read from `<database>.job_runs`. Its three formula columns follow file 11.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty. No formula reads Parameters, and no value is typed over a formula, so Keys needs no row. Cells outside a Table: the Steps sheet and the D1 notes of Parameters and Keys.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT
  run_id,
  job_id,
  status,
  duration_mins,
  RANK() OVER (ORDER BY duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN status = 'SUCCESS' THEN duration_mins END) OVER (PARTITION BY job_id), 0) AS shortest_ok,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0) AS job_total
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X42

### Map
- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). It holds only typed columns and no query loads it, so it is a source. Its typed columns are read from `<database>.job_runs`.
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, runs, avg_mins, id_order). Its typed columns are read from `<database>.jobs`. runs is COUNTIF as a LEFT JOIN to a COUNT(*) grouped by job_id. avg_mins is AVERAGEIF inside IFERROR, so AVG left NULL under a COALESCE of 0. id_order is RANK.EQ ascending.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty. Cells outside a Table: the Steps sheet and the D1 notes of Parameters and Keys.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT j.job_id, j.job_name,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(a.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id) AS id_order
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins FROM <database>.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X43

### Map
- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (job_id, job_name, team, region). Both hold only typed columns and no query loads either, so both are sources.
- **Steps:** none.
- **Finals:**
  - busy_teams (team, runs, shortest, avg_mins), loaded by Power Query busy_teams. Its rows are the query's: an inner join of job_runs to jobs, grouped by team, with COUNT(*), MIN and AVG, kept where the count is above 4.
  - statuses (job_id, status), loaded by Power Query statuses. Its rows are the query's: the distinct job_id and status pairs of job_runs. The blank status comes out as NULL, as Table.Distinct keeps it.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty. Cells outside a Table: the Steps sheet and the D1 notes of Parameters and Keys.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT j.team, COUNT(*) AS runs, MIN(r.duration_mins) AS shortest, AVG(r.duration_mins) AS avg_mins
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.team
HAVING COUNT(*) > 4
```

```sql
SELECT DISTINCT job_id, status
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X44

### Map
- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), jobs (job_id, job_name, team, region), and scheduler_runs (run_id, job_id, dt). Each holds only typed columns and no query loads it, so each is a source.
- **Steps:** none.
- **Finals:**
  - jobs_with_runs (run_id, job_name), loaded by Power Query jobs_with_runs. The RightOuter join is written as jobs LEFT JOIN job_runs, so a job with no run, cache_warm, has a NULL run_id.
  - never_scheduled (job_id, job_name, team), loaded by Power Query never_scheduled. It is the LeftAnti join of jobs to scheduler_runs, keeping the jobs with no scheduler row.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty. Cells outside a Table: the Steps sheet and the D1 notes of Parameters and Keys.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON j.job_id = r.job_id
```

```sql
SELECT j.job_id, j.job_name, j.team
FROM <database>.jobs j
LEFT JOIN <database>.scheduler_runs s ON j.job_id = s.job_id
WHERE s.job_id IS NULL
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X45

### Map
- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and scheduler_runs (run_id, job_id, dt). Each holds only typed columns and no query loads it, so each is a source.
- **Steps:** none.
- **Finals:**
  - run_days (run_id, dt), loaded by Power Query run_days. Its rows are the distinct run_id and dt pairs from job_runs and scheduler_runs together, as Table.Distinct over Table.Combine is UNION.
  - matched (run_id, job_id, dt, status), loaded by Power Query matched. Its rows are a FULL OUTER JOIN of scheduler_runs to job_runs on run_id, with status from job_runs.
- **Values typed over a formula:** none.
- **Marks:**
  - matched: run 99 is in job_runs only. In the FULL OUTER join it comes out with run_id, job_id and dt NULL and status TEST, as the sample shows, because the scheduler's columns are the ones kept. Check this row.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty. Cells outside a Table: the Steps sheet and the D1 notes of Parameters and Keys.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, dt FROM <database>.job_runs
UNION
SELECT run_id, dt FROM <database>.scheduler_runs
```

```sql
SELECT s.run_id, s.job_id, s.dt, r.status
FROM <database>.scheduler_runs s
FULL OUTER JOIN <database>.job_runs r ON s.run_id = r.run_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X51

### Map
- **Sources:** job_runs (run_id, job_id, status, duration_mins, dt), read from `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins).
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty Tables that no formula reads. They are never a source, step or final.
- **To fill in:** `<database>`, in the block below.

### Hive
**job_runs**

```sql
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
- **Sources:** job_runs (run_id, job_id, duration_mins), read from `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job); job_runs (Total Row) (duration_mins, share).
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty Tables that no formula reads. They are never a source, step or final. The Total Row's "Total" label and its empty cells get no column.
- **To fill in:** `<database>`, in the blocks below.

### Hive
**job_runs**

```sql
SELECT run_id, job_id, duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

**job_runs (Total Row)**

```sql
WITH job_runs AS (
  SELECT run_id, job_id, duration_mins,
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
- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read from `<database>.job_runs`. Only job_id and duration_mins are read by a formula.
- **Steps:** none.
- **Finals:** by_job (job_id, total_mins, runs, longest), a summary of job_runs grouped by job_id, with its typed job_ids kept (1, 2, 3); by_job (Total Row) (total_mins, runs, longest).
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty Tables that no formula reads. They are never a source, step or final. The Total Row's "Total" label gets no column.
- **To fill in:** `<database>`, in the blocks below.

### Hive
**by_job**

```sql
SELECT j.job_id,
  COALESCE(c.total_mins, 0) AS total_mins,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total_mins, COUNT(*) AS runs, MAX(duration_mins) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
) c
  ON j.job_id = c.job_id
```

**by_job (Total Row)**

```sql
WITH by_job AS (
  SELECT j.job_id,
    COALESCE(c.total_mins, 0) AS total_mins,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(c.longest, 0) AS longest
  FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
  LEFT JOIN (
    SELECT job_id, SUM(duration_mins) AS total_mins, COUNT(*) AS runs, MAX(duration_mins) AS longest
    FROM <database>.job_runs
    GROUP BY job_id
  ) c
    ON j.job_id = c.job_id
)
SELECT SUM(total_mins) AS total_mins, SUM(runs) AS runs, MAX(longest) AS longest
FROM by_job
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X54

### Map
- **Sources:** job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label), read from `<database>.job_runs`. Only run_id and dt are typed; the rest are formulas.
- **Steps:** none.
- **Finals:** job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label).
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** a_month_on: EDATE as ADD_MONTHS, marked: a month's end stays one.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty Tables that no formula reads. They are never a source, step or final.
- **To fill in:** `<database>`, in the block below.

### Hive
**job_runs**

```sql
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
- **Sources:** jobs (job_id, job_name, team, region), read from `<database>.jobs`.
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens).
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty Tables that no formula reads. They are never a source, step or final.
- **To fill in:** `<database>`, in the block below.

### Hive
**jobs**

```sql
SELECT job_id, job_name, team, region,
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

- **Sources:** `scheduler_runs` (run_id, job_id, dt). It has only typed columns and no query loads it. The formula `scheduled_on` reads it.
- **Steps:** none.
- **Finals:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on). No Total Row. No other Table or query reads it, so it is a final.
- **Values typed over a formula:** none. Keys stays empty, as no Keys row is needed.
- **Marks:**
  - `weighted` (blank): `avg_retry_secs` is blank on run 98, and SUMPRODUCT reads it, so it is written as `COALESCE(avg_retry_secs, 0)`.
  - `scheduled_on`: XLOOKUP becomes a LEFT JOIN. A run_id held twice in `scheduler_runs` would repeat its row, where Excel takes the first match. The sample's run_ids are unique, so check the database table.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty and read by no formula.
- **To fill in:** `<database>` in the two table names.

### Hive

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  r.status IS NULL AS no_status,
  FLOOR(r.duration_mins / 7) AS weeks,
  GREATEST(r.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(r.duration_mins) OVER () AS spread,
  SUM(r.duration_mins * COALESCE(r.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(s.dt, 'unscheduled') AS scheduled_on
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X57

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read by query `picked` and query `ran_jobs`. `jobs` (job_id, job_name, team, region), read by query `ran_jobs`. Neither has a formula, and no query loads either.
- **Steps:** none. The query names in M are not read by another query.
- **Finals:**
  - `picked` (run_id, job_id, status, avg_retry_secs, status_lc). Query `picked` loads this Table, and no formula reads it.
  - `ran_jobs` (job_id, job_name, team, region). Query `ran_jobs` loads this Table, and no formula reads it.
- **Values typed over a formula:** none. Keys stays empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty and read by no formula.
- **To fill in:** `<database>` in each block.

### Hive

```sql
SELECT run_id, job_id, status, COALESCE(avg_retry_secs, 0) AS avg_retry_secs,
  LOWER(status) AS status_lc
FROM <database>.job_runs
WHERE job_id IN (1, 2) AND (status IS NULL OR status LIKE 'S%')
```

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r ON r.job_id = j.job_id
WHERE j.job_name LIKE '%a%'
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X58

### Map

- **Sources:**
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read by queries `numbered`, `days_per_job`, `unrun` and `measures`.
  - `jobs` (job_id, job_name, team, region), read by query `job_regions`.
  - `scheduler_runs` (run_id, job_id, dt), read by query `unrun`.
  - `region_budgets` (job_id, budget_cents, region), read by query `job_regions`.
- **Steps:** none.
- **Finals:**
  - `job_regions` (job_id, region). Query `job_regions` loads it.
  - `numbered` (run_id, dt, duration_mins, n). Query `numbered` loads it.
  - `days_per_job` (job_id, days). Query `days_per_job` loads it.
  - `unrun` (run_id, job_id). Query `unrun` loads it.
  - `measures` (run_id, measure, amount). Query `measures` loads it.
- **Values typed over a formula:** none. Keys stays empty.
- **Marks:**
  - `days_per_job`: the Table.Sort by days, descending, has no FirstN or index after it, so the ORDER BY is dropped. A Hive table holds no order, so the sort is not written.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty and read by no formula.
- **To fill in:** `<database>` in each block.

### Hive

```sql
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) r
```

```sql
SELECT run_id, dt, duration_mins,
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

- **Sources:**
  - `jobs` (job_id, job_name, team, region), read by the formula `team`.
  - `run_alerts` (alert_id, run_id, severity, dt), read by the formula `alerts`.
- **Steps:**
  - `job_runs` (run_id, job_id, duration_mins, dt, team, alerts, running_mins). It has formula columns, no query loads it, and the formulas of `by_team` and query `noisy_runs` read it. It is a CTE in each block that reads it.
- **Finals:**
  - `by_team`, a summary (team, total_mins, alerted_runs). Its typed team values, data and finance, are typed in as its groups. Its only typed column is the one its SUMIFS and COUNTIFS match on.
  - `by_team (Total Row)` (total_mins, alerted_runs). Its Total Row cell for team is a label, so it gets no column.
  - `noisy_runs` (run_id, team, alerts, running_mins). Query `noisy_runs` loads it.
- **Values typed over a formula:** none. Keys stays empty.
- **Marks:**
  - `team` (XLOOKUP as a LEFT JOIN): Excel takes the first match, and a job_id held twice in `jobs` would repeat a row. The sample's job_ids are unique, so check the database table.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty and read by no formula.
- **To fill in:** `<database>` in each block.

### Hive

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
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
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
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
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
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

- **Sources:**
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read by query `base`.
  - `jobs` (job_id, job_name, team, region), read by query `base`.
  - `region_budgets` (job_id, budget_cents, region), read by query `base`.
- **Steps:**
  - `base` (run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name, region). It is a connection-only query, but two queries read it, so it is a step. It is a CTE in each block of `by_region` and `top_runs`.
- **Finals:**
  - `by_region` (region, total_mins, runs, share). Query `by_region` loads it. `share` is computed over the rows the query keeps, so the window sits over a subquery of those rows.
  - `by_region (Total Row)` (total_mins). Only the total_mins cell holds a total. The label and the empty cells get no column.
  - `top_runs` (run_id, job_name, region). Query `top_runs` loads it.
- **Values typed over a formula:** none. Keys stays empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty and read by no formula.
- **To fill in:** `<database>` in each block.

### Hive

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  INNER JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
by_region AS (
  SELECT region, total_mins, runs,
    total_mins / SUM(total_mins) OVER () AS share
  FROM (SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
    FROM base GROUP BY region HAVING COUNT(*) >= 2) g
)
SELECT region, total_mins, runs, share
FROM by_region
```

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  INNER JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
by_region AS (
  SELECT region, total_mins, runs,
    total_mins / SUM(total_mins) OVER () AS share
  FROM (SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
    FROM base GROUP BY region HAVING COUNT(*) >= 2) g
)
SELECT SUM(total_mins) AS total_mins
FROM by_region
```

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  INNER JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
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

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
- **Steps:** query `ok_runs` (run_id, job_id, duration_mins), keeping the SUCCESS rows. It is a CTE in the `ok_by_job` final, since query `ok_by_job` names it.
- **Finals:**
  - Table `ok_runs` (run_id, job_id, duration_mins, hours). Its rows are query `ok_runs`'s rows; `hours` is `duration_mins / 60`.
  - Table `ok_by_job` (job_id, total_mins). Its rows are query `ok_by_job`'s rows: `SUM(duration_mins)` per job_id.
- **Values typed over a formula:** none. Keys has no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the empty Parameters and Keys Tables, which have no role; the Steps sheet and the D1 notes, which are cells outside a Table.
- **To fill in:** `<database>` in each final's query, the user's database name.

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

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
- **Steps:** Table `jobs` (job_id, job_name, team, runs, total). Its typed columns are read from `<database>.jobs`. `runs` is `COUNTIF` over job_runs and `total` is `SUMIF` over job_runs' duration_mins, each as a LEFT JOIN with COALESCE. It is a CTE in each final that reads it: `by_team` (through its SUMIFS) and `busy_jobs` (through query `busy_jobs`).
- **Finals:**
  - Table `by_team` (team, team_total), a summary. Its typed groups data, finance and web are typed in, and `team_total` is `SUMIFS` over the jobs step's total, with COALESCE.
  - Table `busy_jobs` (job_id, job_name, runs). Its rows are query `busy_jobs`'s rows: the jobs step's rows where runs >= 3.
- **Values typed over a formula:** none. Keys has no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the empty Parameters and Keys Tables, which have no role; the Steps sheet and the D1 notes, which are cells outside a Table.
- **To fill in:** `<database>` in each final's query, the user's database name.

### Hive

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(s.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
    ON j.job_id = c.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) s
    ON j.job_id = s.job_id
)
SELECT g.team, COALESCE(t.team_total, 0) AS team_total
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') g
LEFT JOIN (SELECT team, SUM(total) AS team_total FROM jobs GROUP BY team) t
  ON g.team = t.team
```

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(s.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
    ON j.job_id = c.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) s
    ON j.job_id = s.job_id
)
SELECT job_id, job_name, runs FROM jobs WHERE runs >= 3
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X75

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
- **Steps:** query `long_runs` (run_id, dt, duration_mins), keeping rows where duration_mins >= 15. It is a CTE in the `long_per_day` final, since query `long_per_day` names it.
- **Finals:**
  - Table `long_runs` (run_id, dt, duration_mins, over). Its rows are query `long_runs`'s rows; `over` is `duration_mins - 15`.
  - Table `long_per_day` (dt, runs). Its rows are query `long_per_day`'s rows: `COUNT(*)` per dt.
- **Values typed over a formula:** none. Keys has no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the empty Parameters and Keys Tables, which have no role; the Steps sheet and the D1 notes, which are cells outside a Table.
- **To fill in:** `<database>` in each final's query, the user's database name.

### Hive

```sql
SELECT run_id, dt, duration_mins, duration_mins - 15 AS over
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

- **Sources:** `jobs` (job_id, job_name, team, region) and `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), each read as `<database>.<table>`.
- **Steps:** query `finance_jobs` (job_id, job_name), keeping `team = 'finance'`. It is a CTE in the `finance_runs` final, since query `finance_runs` names it.
- **Finals:**
  - Table `finance_jobs` (job_id, job_name, label). Its rows are query `finance_jobs`'s rows; `label` is `UPPER(job_name)`.
  - Table `finance_runs` (run_id, job_name, duration_mins). Its rows are query `finance_runs`'s rows: job_runs joined inner on job_id to the finance_jobs step.
- **Values typed over a formula:** none. Keys has no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the empty Parameters and Keys Tables, which have no role; the Steps sheet and the D1 notes, which are cells outside a Table.
- **To fill in:** `<database>` in each final's query, the user's database name.

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

