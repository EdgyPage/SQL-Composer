date: 2026-11-01
arm: C
model: haiku
files: 18-r4


## X01

**Map**

- Sources: none.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours). It holds a formula column, and no query or other Table reads it.
- Left out: Parameters and Keys, both empty settings Tables that no formula reads.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: nothing.
- To fill in: `<database>`.

### Hive

```sql
-- job_runs
SELECT run_id, job_id, duration_mins, dt, duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X02

**Map**

- Sources: none.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag). It holds formula columns, and no query or other Table reads it.
- Left out: Parameters and Keys, both empty settings Tables that no formula reads.
- Values typed over a formula: none.
- Marks: none. The blank status on run 98 is read by no formula, so it stays NULL as typed.
- Refusals: none.
- Left alone: nothing.
- To fill in: `<database>`.

### Hive

```sql
-- job_runs
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF(duration_mins > 25 OR job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X03

**Map**

- Sources: none.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs). It holds formula columns, and no query or other Table reads it.
- Left out: Parameters and Keys, both empty settings Tables that no formula reads.
- Values typed over a formula: none.
- Marks, blank:
  - Run 98 has a blank status, which score reads. score reads COALESCE(status, '') there.
  - Run 98 has a blank avg_retry_secs, which mins_per_retry and total_secs read. Both read COALESCE(avg_retry_secs, 0) there.
- Refusals: none.
- Left alone: nothing.
- To fill in: `<database>`.

### Hive

```sql
-- job_runs
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X04

**Map**

- Sources: none.
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd). It holds formula columns, and no query or other Table reads it.
- Left out: Parameters and Keys, both empty settings Tables that no formula reads.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: nothing.
- To fill in: `<database>`.

### Hive

```sql
-- jobs
SELECT job_id, job_name, team, region,
  CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-', region) AS code,
  LENGTH(job_name) AS name_length,
  ROUND(job_id / 3, 2) AS third,
  PMOD(job_id, 2) AS odd
FROM <database>.jobs
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X05

**Map**

- Sources: none.
- Steps: none.
- Finals:
  - job_runs (run_id, dt, month, days_since). It holds formula columns, and no query or other Table reads it.
  - region_costs (job_id, cost_cents, region, dt, day). It holds a formula column, and no query or other Table reads it.
- Left out: Parameters and Keys, both empty settings Tables that no formula reads.
- Values typed over a formula: none.
- Marks:
  - region_costs day: dt is a date held as text (20260911), so day is CONCAT of its parts, not DATE, and gives 'yyyy-mm-dd' text.
  - Blank: cost_cents on row 29 is blank, but no formula reads it, so it stays NULL as typed.
- Refusals: none.
- Left alone: nothing.
- To fill in: `<database>`.

### Hive

```sql
-- job_runs
SELECT run_id, dt, MONTH(dt) AS month, DATEDIFF(dt, '2026-09-01') AS days_since
FROM <database>.job_runs
```

```sql
-- region_costs
SELECT job_id, cost_cents, region, dt,
  CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS day
FROM <database>.region_costs
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X06

### Map

- Sources: `jobs` (job_id, job_name, team, region). It holds typed columns only and no query loads it. The job_name formula in job_runs reads it.
- Steps: none.
- Finals: `job_runs` (run_id, job_id, duration_mins, job_name, runs_of_job). It holds formula columns, and no other Table's formula or query reads it, so it is a final. job_name is a LEFT JOIN to jobs on job_id. runs_of_job is COUNT(*) over its own job_id, with COALESCE, as Excel's COUNTIFS gives 0 where nothing matches.
- Value typed over a formula: none. Keys is empty, so no Keys row is needed.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys (both empty; no formula reads Parameters). No Total Row on job_runs or jobs. No queries and no defined names are listed.
- To fill in: `<database>` in the FROM and JOIN lines.

### Hive

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X07

### Map

- Sources: `jobs` (job_id, job_name, team, region). It holds typed columns only and no query loads it. The job_runs formulas read it.
- Steps: none.
- Finals: `job_runs` (run_id, job_id, status, team, region). Nothing else reads it, so it is a final. team (VLOOKUP with FALSE, column 3) and region (INDEX/MATCH with 0) are both exact matches on job_id, so one LEFT JOIN to jobs serves both.
- Value typed over a formula: none. Keys is empty, so no Keys row is needed.
- Marks: none. The blank status on run 98 stays NULL, as no formula reads status.
- Refusals: none.
- Left alone: Parameters and Keys (both empty). No Total Row on either Table. No queries and no defined names are listed.
- To fill in: `<database>` in the FROM and JOIN lines.

### Hive

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X08

### Map

- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). It holds typed columns only and no query loads it. The by_job formulas read it.
- Steps: none.
- Finals: `by_job` (job_id, total_mins, avg_retry, longest). It is a summary: its only typed column, job_id, is the one its SUMIFS, AVERAGEIFS and MAXIFS match on. Its typed groups 1, 2 and 3 are typed in, and job_runs is read.
  - total_mins: SUM over job_runs by job_id, with COALESCE.
  - avg_retry: AVG over job_runs by job_id, left NULL where nothing matches.
  - longest: MAX over job_runs by job_id, with COALESCE.
- Total Row: none.
- Value typed over a formula: none. Keys is empty, so no Keys row is needed.
- Marks: none. The blank avg_retry_secs on run 98 is skipped by AVG, as AVERAGEIFS skips a blank, so it is written as it is.
- Refusals: none.
- Left alone: Parameters and Keys (both empty). The dt column is read by no formula, so it stays as typed.
- To fill in: `<database>` in the FROM line of the summary's subquery.

### Hive

```sql
SELECT j.job_id, COALESCE(c.total_mins, 0) AS total_mins, c.avg_retry, COALESCE(c.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total_mins, AVG(avg_retry_secs) AS avg_retry, MAX(duration_mins) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
) c ON j.job_id = c.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X09

### Map

- Sources: `jobs` (job_id, job_name, team, region). It holds typed columns only and no query loads it. The team formula in job_runs reads it.
- Steps: none.
- Finals: `job_runs` (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost). Nothing else reads it, so it is a final.
  - team: the jobs team, a LEFT JOIN on job_id.
  - team_mins: SUM of its own duration_mins over its own team, with COALESCE.
  - cost: (duration_mins * 60 + avg_retry_secs) * rate, with rate read in from Parameters as its value, 0.5.
- Value typed over a formula: cost on run 97 is typed 100. Keys names job_runs with run_id, so the CASE matches on run_id.
- Marks: blank. avg_retry_secs is blank on run 98, and cost reads it, so it is written COALESCE(avg_retry_secs, 0).
- Refusals: none.
- Left alone: Parameters is read, not left alone. The `_xlfn.` prefixes are read past.
- To fill in: `<database>` in the FROM and JOIN lines.

### Hive

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs, j.team,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.team), 0) AS team_mins,
  CASE WHEN r.run_id = 97 THEN 100
    ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5 END AS cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X10

### Map

- Sources: none. No Table holds typed columns only; Parameters and Keys are empty and are never sources.
- Steps: none.
- Finals: `job_runs` (run_id, job_id, duration_mins, dt, hours, sample). It holds formula columns, and nothing else reads it, so it is a final.
  - hours: duration_mins / 60.
  - sample: refused, as `=RAND()` in every row is refused. `NULL AS sample`.
- Value typed over a formula: hours on run 103 is typed 9. No Keys row names job_runs (Keys is empty), so there is no Keys row. The CASE matches every typed column of that row: run_id, job_id, duration_mins and dt.
- Marks: none.
- Refusals: sample (RAND, in every row), NULL in its place.
- Left alone: Parameters and Keys (both empty). No Total Row on job_runs. No queries and no defined names are listed.
- To fill in: `<database>` in the FROM line.

### Hive

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24' THEN 9
    ELSE duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X11

### Map

- **Sources:** job_runs (run_id, duration_mins), typed columns read from `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, duration_mins, pick, scaled). Nothing else reads it, so it is a final.
- **Typed over a formula:** none. The Keys Table is empty.
- **Marks:** none.
- **Refusals:**
  - pick: `NULL AS pick`. It uses INDIRECT, and ROW(), which hangs on the order of the rows.
  - scaled: `NULL AS scaled`. It reads Summary!C2, a cell outside a Table that is not a defined name.
- **Left alone:** the Steps sheet; the empty Parameters and Keys Tables (no formula reads Parameters, and nothing is typed over a formula); the Summary sheet, its C2 cell (3) and its bar chart.
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

- **Sources:** job_runs (run_id, duration_mins), typed columns read from `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, duration_mins, running, loop, with_tax). Nothing else reads it, so it is a final.
- **Typed over a formula:** none. The Keys Table is empty.
- **Marks:**
  - with_tax reads tax_rate, a defined name for Summary!B3, a cell outside a Table. It is written as its value, 0.2. Move it into Parameters (name tax_rate, value 0.2).
- **Refusals:**
  - running: `NULL AS running`. It uses OFFSET, and ROW(), which hangs on the order of the rows.
  - loop: `NULL AS loop`. Its formula reads its own column, so it is circular.
- **Left alone:** the Steps sheet; the empty Parameters and Keys Tables (tax_rate is not in Parameters yet); the Summary sheet, whose B3 cell is read only through tax_rate.
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

- **Sources:**
  - job_runs (run_id, job_id), typed columns read from `<database>.job_runs`.
  - jobs (job_id, job_name, team, region), typed only, read from `<database>.jobs`. Nothing loads it; job_runs' name formula reads it.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, name, doubled). Nothing else reads it, so it is a final.
- **Typed over a formula:** none. The Keys Table is empty.
- **Marks:**
  - name is a VLOOKUP with TRUE, an approximate match. It is written as the exact match on job_id (a LEFT JOIN to jobs), and named here for the user to check.
- **Refusals:**
  - doubled: `NULL AS doubled`. DOUBLE is a defined name holding a LAMBDA.
- **Left alone:** the Steps sheet; the empty Parameters and Keys Tables.
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

- **Sources:** none. The typed columns of job_runs are read inside its step.
- **Steps:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, hours). Its hours formula is read by by_job's SUMIFS, so job_runs is a step, not a final. It is a CTE in by_job's final, reading `<database>.job_runs`.
- **Finals:** by_job (job_id, total_hours), a summary: its only typed column, job_id, is the one its SUMIFS matches on. Its typed job_ids 1, 2 and 3 are its groups, typed in. It has no Total Row.
- **Typed over a formula:** none. The Keys Table is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the PivotTable on sheet "Pivot", from job_runs; the Steps sheet; the empty Parameters and Keys Tables; the blank status and avg_retry_secs on job 98 (run 98), which no formula reads.
- **To fill in:** `<database>`.

### Hive

```sql
WITH job_runs AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
    duration_mins / 60 AS hours
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

- **Sources:** tblRuns (Run ID, Job ID, Duration (mins)), typed columns read from `<database>.tblRuns`.
- **Steps:** none.
- **Finals:** tblRuns (Run ID, Job ID, Duration (mins), Hours). Hours reads only its own row and nothing else reads the Table, so it is a final.
- **Typed over a formula:** none. The Keys Table is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet; the empty Parameters and Keys Tables.
- **To fill in:** `<database>`, and the headers in snake case: `<run_id>` (Run ID), `<job_id>` (Job ID), `<duration_mins>` (Duration (mins)). The Table name tblRuns is plain and stays as it is.

### Hive

```sql
SELECT <run_id>, <job_id>, <duration_mins>, <duration_mins> / 60 AS hours
FROM <database>.tblRuns
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X16

### Map

- **Sources**
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed columns only, and no query loads it. Read as `<database>.job_runs`.
- **Steps**: none.
- **Finals**
  - `long_runs` (run_id, job_id, minutes, hours): Table long_runs, loaded by query long_runs. No Table's formula reads long_runs, so it is a final, its rows the query's. The query's Kept, Long, Hours and Renamed steps are one SELECT.
- **Parameters and Keys**: both empty, read as settings, never a source, step or final. No value is typed over a formula, so no Keys row is needed.
- **Values typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet and the D1 notes, which are cells outside a Table.
- **To fill in**: `<database>`.

### Hive: long_runs

```sql
SELECT run_id, job_id, duration_mins AS minutes, duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X17

### Map

- **Sources**
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed columns only, read by query ok_runs. Read as `<database>.job_runs`.
- **Steps**
  - `ok_runs` (query, connection only): the job_runs rows whose status is SUCCESS, all six columns. Query ok_by_job names it, so it is a step: a CTE in ok_by_job's final.
- **Finals**
  - `ok_by_job` (job_id, runs, total_mins): Table ok_by_job, loaded by query ok_by_job, which groups ok_runs by job_id. No Table's formula reads ok_by_job, so it is a final, its rows the query's.
- **Parameters and Keys**: both empty, read as settings, never a source, step or final. No value is typed over a formula, so no Keys row is needed.
- **Values typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet and the D1 notes, which are cells outside a Table.
- **To fill in**: `<database>`.

### Hive: ok_by_job

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

- **Sources**
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed columns only, read by query top_runs. Read as `<database>.job_runs`.
  - `jobs` (job_id, job_name, team, region): typed columns only, read by query top_runs. Read as `<database>.jobs`.
- **Steps**: none. Query top_runs reads both Tables directly, so each is a source, not a CTE.
- **Finals**
  - `top_runs` (run_id, job_name, duration_mins): Table top_runs, loaded by query top_runs, which joins job_runs to jobs for job_name, sorts by duration_mins from longest, and keeps the first 3. No Table's formula reads top_runs, so it is a final, its rows the query's.
- **Parameters and Keys**: both empty, read as settings, never a source, step or final. No value is typed over a formula, so no Keys row is needed.
- **Values typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet and the D1 notes, which are cells outside a Table.
- **To fill in**: `<database>`.

### Hive: top_runs

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

- **Sources**
  - `scheduler_runs` (run_id, job_id, dt): typed columns only, read by query all_runs. Read as `<database>.scheduler_runs`.
  - `job_runs` (run_id, job_id, dt, read from the warehouse): query all_runs reads it from `Sql.Database("dwh01", "ops")`, item job_runs, which is outside the workbook. Read as `<database>.job_runs`, and named as a mark below.
- **Steps**: none.
- **Finals**
  - `all_runs` (run_id, job_id, dt): Table all_runs, loaded by query all_runs, which stacks the scheduler_runs rows on the warehouse job_runs rows, each kept to run_id, job_id and dt (Table.Combine, so UNION ALL). No Table's formula reads all_runs, so it is a final, its rows the query's.
- **Left out, named**
  - Query `holidays` (connection only): it loads nothing and nothing reads it, so it is left out. It is also refused: it reads a web source, `Web.Contents("https://calendar.example.com/holidays.csv")`, which no Hive here reads.
- **Refusals**: the query `holidays`, left out as above.
- **Marks**
  - `job_runs` comes from outside the workbook: the Sql.Database read of server dwh01, schema ops, item job_runs. It is read as `<database>.job_runs`, the table the Hive names. The server and schema are not in the Hive. Check that this table is the one in the user's Database.
- **Parameters and Keys**: both empty, read as settings, never a source, step or final. No value is typed over a formula, so no Keys row is needed.
- **Values typed over a formula**: none.
- **Left alone**: the Steps sheet and the D1 notes, which are cells outside a Table.
- **To fill in**: `<database>`.

### Hive: all_runs

```sql
SELECT run_id, job_id, dt FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X20

### Map

- **Sources**
  - `run_alerts` (alert_id, run_id, severity, dt): typed columns only, read by query alert_pivot. Read as `<database>.run_alerts`.
- **Steps**: none.
- **Finals**
  - `alert_pivot` (run_id, high, low): Table alert_pivot, loaded by query alert_pivot. It keeps the run_alerts rows whose run_id is 97 or 101, counts them by severity, and pivots severity into one column each. No Table's formula reads alert_pivot, so it is a final, its rows the query's.
- **Parameters and Keys**: both empty, read as settings, never a source, step or final. No value is typed over a formula, so no Keys row is needed.
- **Values typed over a formula**: none.
- **Marks**
  - The pivot's columns `high` and `low` are fixed as the sample has them. A severity that is not in the sample would be left out until the pivot's columns are changed.
  - Where a run has none of a severity, the count is NULL, as M leaves it.
- **Refusals**: none.
- **Left alone**: the Steps sheet and the D1 notes, which are cells outside a Table.
- **To fill in**: `<database>`.

### Hive: alert_pivot

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

- **Sources:** none.
- **Steps:** none.
- **Finals:** Table `job_runs` (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). No query loads it and no other Table's formula reads it, so it is a final. Its own formula columns reading its own row don't count. It is not a summary, as status and duration_mins are typed columns that no SUMIFS or COUNTIFS matches on.
- **Left out or settings:** `Parameters` and `Keys` are empty settings Tables, never a source, step or final. No value is typed over a formula, so `Keys` needs no row.
- **Values typed over a formula:** none.
- **Marks:** none. The blank status in row 98 sits inside MINIFS's criteria, so it is written as it is.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the notes in D1 of each sheet (cells outside a Table).
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins,
  RANK() OVER (ORDER BY duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN status = 'SUCCESS' THEN duration_mins END) OVER (PARTITION BY job_id), 0) AS shortest_ok,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0) AS job_total
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X42

### Map

- **Sources:** Table `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Typed only, and no query loads it.
- **Steps:** none.
- **Finals:** Table `jobs` (job_id, job_name, runs, avg_mins, id_order). Nothing else reads it, so it is a final. It is not a summary, as job_name is a typed column that no COUNTIF or AVERAGEIF matches on.
- **Left out or settings:** `Parameters` and `Keys` are empty settings Tables, never a source, step or final. No value is typed over a formula, so `Keys` needs no row.
- **Values typed over a formula:** none.
- **Marks:** none. The blank avg_retry_secs in row 98 is read by no formula.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the notes in D1 of each sheet (cells outside a Table).
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

- **Sources:**
  - Table `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Typed only. Power Query `busy_teams` and `statuses` read it, but no query loads it.
  - Table `jobs` (job_id, job_name, team, region). Typed only. Power Query `busy_teams` reads it.
- **Steps:** none.
- **Finals:**
  - Table `busy_teams` (team, runs, shortest, avg_mins), loaded by Power Query `busy_teams`. No other Table's formula reads it, so its rows are the query's.
  - Table `statuses` (job_id, status), loaded by Power Query `statuses`. No other Table's formula reads it, so its rows are the query's.
- **Left out or settings:** `Parameters` and `Keys` are empty settings Tables, never a source, step or final. No value is typed over a formula, so `Keys` needs no row.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the notes in D1 of each sheet (cells outside a Table).
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
SELECT DISTINCT job_id, status FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X44

### Map

- **Sources:**
  - Table `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Typed only. Power Query `jobs_with_runs` reads it, but no query loads it.
  - Table `jobs` (job_id, job_name, team, region). Typed only. Power Query `jobs_with_runs` and `never_scheduled` read it.
  - Table `scheduler_runs` (run_id, job_id, dt). Typed only. Power Query `never_scheduled` reads it.
- **Steps:** none.
- **Finals:**
  - Table `jobs_with_runs` (run_id, job_name), loaded by Power Query `jobs_with_runs`. Its rows are the query's.
  - Table `never_scheduled` (job_id, job_name, team), loaded by Power Query `never_scheduled`. Its rows are the query's.
- **Left out or settings:** `Parameters` and `Keys` are empty settings Tables, never a source, step or final. No value is typed over a formula, so `Keys` needs no row.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the notes in D1 of each sheet (cells outside a Table).
- **To fill in:** `<database>`.

### Hive

```sql
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON j.job_id = r.job_id
```

```sql
SELECT t.job_id, t.job_name, t.team
FROM <database>.jobs t
LEFT JOIN <database>.scheduler_runs s ON t.job_id = s.job_id
WHERE s.job_id IS NULL
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X45

### Map

- **Sources:**
  - Table `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Typed only. Power Query `run_days` and `matched` read it, but no query loads it.
  - Table `scheduler_runs` (run_id, job_id, dt). Typed only. Power Query `run_days` and `matched` read it, but no query loads it.
- **Steps:** none.
- **Finals:**
  - Table `run_days` (run_id, dt), loaded by Power Query `run_days`. Its rows are the query's.
  - Table `matched` (run_id, job_id, dt, status), loaded by Power Query `matched`. Its rows are the query's.
- **Left out or settings:** `Parameters` and `Keys` are empty settings Tables, never a source, step or final. No value is typed over a formula, so `Keys` needs no row.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the notes in D1 of each sheet (cells outside a Table).
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

- Sources: job_runs (run_id, job_id, status, duration_mins, dt), read from `<database>.job_runs`.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins). No query loads it and no other Table's formula reads it, so it is a final; its own formulas reading its own rows don't count. It is not a summary (run_id is typed but not matched on) and has no Total Row.
- Values typed over a formula: none. Every formula cell holds its formula, so Keys needs no row.
- Marks: none. The blank status on run 98 is read only inside COUNTIFS conditions, so it is written as it is; not_ok counts it as Excel does, with `(status <> 'SUCCESS' OR status IS NULL)`.
- Refusals: none.
- Left alone: Parameters and Keys, the two settings Tables, both empty. Never a source, step or final.
- To fill in: `<database>`, in the FROM of the job_runs final.

### Hive

```sql
-- job_runs
SELECT run_id, job_id, status, duration_mins, dt,
  COALESCE(COUNT(CASE WHEN duration_mins > 15 THEN 1 END) OVER (PARTITION BY job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (status <> 'SUCCESS' OR status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY job_id), 0) AS failed_in_job,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X52

### Map

- Sources: job_runs (run_id, job_id, duration_mins), read from `<database>.job_runs`.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job). No query loads it and no other Table's formula reads it, so it is a final. It is not a summary (run_id is typed but not matched on).
- Finals: job_runs (Total Row), a final of its own with columns duration_mins and share, the only Total Row cells that hold a total. The "Total" label and the blank cells get no column.
- Values typed over a formula: none. Keys needs no row.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys, the two settings Tables, both empty.
- To fill in: `<database>`, in the FROM of the job_runs final.

### Hive

```sql
-- job_runs
SELECT run_id, job_id, duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

```sql
-- job_runs (Total Row)
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

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X53

### Map

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read from `<database>.job_runs`. It has only typed columns and no query loads it, so it is a source only, never a final. No formula reads its blank status or avg_retry_secs on run 98.
- Steps: none.
- Finals: by_job (job_id, total_mins, runs, longest). No query loads it and nothing else reads it, so it is a final. It is a summary: its only typed column, job_id, is what its SUMIFS and COUNTIFS match on. Its final is a GROUP BY of job_runs, with its typed job_ids 1, 2 and 3 typed in as the groups.
- Finals: by_job (Total Row), a final of its own with columns total_mins, runs and longest, the only Total Row cells that hold a total. The "Total" label gets no column.
- Values typed over a formula: none. Keys needs no row.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys, the two settings Tables, both empty.
- To fill in: `<database>`, in the FROM of the by_job final.

### Hive

```sql
-- by_job
SELECT j.job_id,
  COALESCE(a.total_mins, 0) AS total_mins,
  COALESCE(a.runs, 0) AS runs,
  COALESCE(a.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total_mins, COUNT(*) AS runs, MAX(duration_mins) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
) a
  ON j.job_id = a.job_id
```

```sql
-- by_job (Total Row)
WITH by_job AS (
  SELECT j.job_id,
    COALESCE(a.total_mins, 0) AS total_mins,
    COALESCE(a.runs, 0) AS runs,
    COALESCE(a.longest, 0) AS longest
  FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
  LEFT JOIN (
    SELECT job_id, SUM(duration_mins) AS total_mins, COUNT(*) AS runs, MAX(duration_mins) AS longest
    FROM <database>.job_runs
    GROUP BY job_id
  ) a
    ON j.job_id = a.job_id
)
SELECT SUM(total_mins) AS total_mins, SUM(runs) AS runs, MAX(longest) AS longest
FROM by_job
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X54

### Map

- Sources: job_runs (run_id, dt), read from `<database>.job_runs`.
- Steps: none.
- Finals: job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label). No query loads it and no other Table's formula reads it, so it is a final.
- Values typed over a formula: none. Keys needs no row.
- Marks: a_month_on, `EDATE(dt, 1)`, written as `ADD_MONTHS(dt, 1)`; marked, as a month's end stays the month's end.
- Refusals: none.
- Left alone: Parameters and Keys, the two settings Tables, both empty.
- To fill in: `<database>`, in the FROM of the job_runs final.

### Hive

```sql
-- job_runs
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

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X55

### Map

- Sources: jobs (job_id, job_name, team, region), read from `<database>.jobs`.
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens). No query loads it and nothing else reads it, so it is a final.
- Values typed over a formula: none. Keys needs no row.
- Marks: none. The team and region cells have no blanks in the sample, so tag needs no COALESCE.
- Refusals: none.
- Left alone: Parameters and Keys, the two settings Tables, both empty.
- To fill in: `<database>`, in the FROM of the jobs final.

### Hive

```sql
-- jobs
SELECT job_id, job_name, team, region,
  INITCAP(REPLACE(job_name, '_', ' ')) AS title,
  CONCAT_WS('/', team, region) AS tag,
  CONCAT(region, '-', job_id) AS code,
  INSTR(LOWER(job_name), LOWER('SYNC')) > 0 AS has_sync,
  CAST(CONCAT(job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X56

### Map

Sources
- scheduler_runs: run_id, job_id, dt. Typed only, and no query loads it. Read by job_runs' scheduled_on.

Steps: none.

Finals
- job_runs: run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on. Its typed columns are read from `<database>.job_runs`. Nothing else reads it, and its own formulas don't count.
  - no_status: ISBLANK, written as `status IS NULL`.
  - weeks: INT, as `FLOOR(duration_mins / 7)`.
  - at_least_20: MAX of one row's cells, as `GREATEST(duration_mins, 20)`.
  - spread: STDEV.S of the whole column, as `STDDEV_SAMP(duration_mins) OVER ()`.
  - weighted: SUMPRODUCT, as `SUM(duration_mins * COALESCE(avg_retry_secs, 0)) OVER ()`.
  - scheduled_on: XLOOKUP, as a LEFT JOIN of scheduler_runs on run_id, then `COALESCE(dt, 'unscheduled')`.

Values typed over a formula: none. Keys is empty, so it needs no row.

Marks
- blank: avg_retry_secs is blank in run 98, and weighted reads it. Written as `COALESCE(avg_retry_secs, 0)`.

Refusals: none.

Left alone: Parameters (empty, and no formula reads it), Keys (empty), and the Steps sheet.

`<...>` to fill in: `<database>`.

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

Sources
- job_runs: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Typed only, and no query loads it. Read by the query picked.
- jobs: job_id, job_name, team, region. Typed only, and no query loads it. Read by the query ran_jobs.

Steps: none.

Finals
- picked (loads Table picked): run_id, job_id, status, avg_retry_secs, status_lc. From `<database>.job_runs`, where job_id is in (1, 2) and status is blank or starts with S. avg_retry_secs is filled with 0, and status_lc is LOWER(status). No formula reads it.
- ran_jobs (loads Table ran_jobs): job_id, job_name, team, region. From `<database>.jobs`, kept where a job_runs row has its job_id (LEFT SEMI JOIN) and job_name contains "a".

Values typed over a formula: none. Keys is empty, so it needs no row.

Marks
- blank: avg_retry_secs is blank in run 98 in job_runs. The query's fill with 0 is written as `COALESCE(avg_retry_secs, 0)`.

Refusals: none.

Left alone: Parameters (empty, and no formula reads it), Keys (empty), and the Steps sheet.

`<...>` to fill in: `<database>`.

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

Sources
- jobs: job_id, job_name, team, region. Typed only. Read by the query job_regions.
- job_runs: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Typed only. Read by the queries numbered, days_per_job, unrun and measures.
- scheduler_runs: run_id, job_id, dt. Typed only. Read by the query unrun.
- region_budgets: job_id, budget_cents, region. Typed only. Read by the query job_regions.

Steps: none.

Finals
- job_regions (loads Table job_regions): job_id, region. Each job of jobs paired with each distinct region of region_budgets. The let step `Regions` is a CTE `regions`, and the pairing is a CROSS JOIN.
- numbered (loads Table numbered): run_id, dt, duration_mins, n. From job_runs, `n` is ROW_NUMBER() ordered by duration_mins descending, then run_id ascending.
- days_per_job (loads Table days_per_job): job_id, days. COUNT(DISTINCT dt) grouped by job_id.
- unrun (loads Table unrun): run_id, job_id. The scheduler_runs rows with no job_runs row on every column, which is EXCEPT.
- measures (loads Table measures): run_id, measure, amount. Each unpivoted column is one SELECT, stacked with UNION ALL, and each drops its nulls.

Values typed over a formula: none. Keys is empty, so it needs no row.

Marks
- order dropped: days_per_job's Table.Sort by days descending is dropped, as a Hive table holds no order.
- blank: job_runs' avg_retry_secs is blank in run 98. Its row is dropped from measures by the WHERE, as M drops it there.

Refusals: none.

Left alone: Parameters (empty, and no formula reads it), Keys (empty), and the Steps sheet.

`<...>` to fill in: `<database>`.

### Hive

```sql
WITH regions AS (
  SELECT DISTINCT region FROM <database>.region_budgets
)
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN regions r
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

Sources
- jobs: job_id, job_name, team, region. Typed only. Read by job_runs' team formula.
- run_alerts: alert_id, run_id, severity, dt. Typed only. Read by job_runs' alerts formula.

Steps
- job_runs: run_id, job_id, duration_mins, dt, team, alerts, running_mins. Its typed columns are read from `<database>.job_runs`. It is read by the by_team formulas and by the query noisy_runs, so it is a step. It is a CTE `job_runs` in each final that reads it.
  - team: XLOOKUP, as a LEFT JOIN of jobs on job_id, then team.
  - alerts: COUNTIF, as a LEFT JOIN of a COUNT(*) grouped by run_id from run_alerts, then `COALESCE(alerts, 0)`.
  - running_mins: SUMIFS with "<=" on dt, as the running total `SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`.

Finals
- by_team (summary, typed team groups data and finance, with its SUMIFS and COUNTIFS): team, total_mins, alerted_runs. Its groups are typed in, and job_runs is read as the step.
  - total_mins: SUMIFS, as a LEFT JOIN of SUM(duration_mins) grouped by team, then `COALESCE(total_mins, 0)`.
  - alerted_runs: COUNTIFS with ">0", as a LEFT JOIN of COUNT(*) where alerts > 0 grouped by team, then `COALESCE(alerted_runs, 0)`.
- by_team (Total Row): total_mins, alerted_runs. Each SUBTOTAL(109) is a SUM. The "Total" label and the Total Row's team cell get no column. It reads by_team's final query as a CTE.
- noisy_runs (loads Table noisy_runs): run_id, team, alerts, running_mins. From job_runs, kept where alerts >= 2, with its columns selected.

Values typed over a formula: none. Keys is empty, so it needs no row.

Marks: none.

Refusals: none.

Left alone: Parameters (empty, and no formula reads it), Keys (empty), and the Steps sheet.

`<...>` to fill in: `<database>`.

### Hive

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt, j.team,
    COALESCE(a.alerts, 0) AS alerts,
    SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_mins
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
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt, j.team,
    COALESCE(a.alerts, 0) AS alerts,
    SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_mins
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
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt, j.team,
    COALESCE(a.alerts, 0) AS alerts,
    SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_mins
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

Sources
- job_runs: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Typed only. Read by the step base.
- jobs: job_id, job_name, team, region. Typed only. Read by the step base.
- region_budgets: job_id, budget_cents, region. Typed only. Read by the step base.

Steps
- base (a Power Query with connection only, which loads no Table and is read by by_region and top_runs): run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name, region. Inner join to jobs, left join to region_budgets. It is a CTE `base` in each final that reads it.

Finals
- by_region (loads Table by_region): region, total_mins, runs, share. From base, grouped by region, kept where COUNT(*) >= 2 (HAVING).
  - share: the formula `=by_region[[#This Row],[total_mins]]/SUM(by_region[total_mins])`, as `total_mins / SUM(total_mins) OVER ()`.
- by_region (Total Row): total_mins. The SUBTOTAL(109) is a SUM. The "Total" label and the empty runs and share cells get no column. It reads by_region's rows as a CTE, without the share column.
- top_runs (loads Table top_runs): run_id, job_name, region. From base, sorted by duration_mins descending then run_id ascending, the top 2.

Values typed over a formula: none. Keys is empty, so it needs no row.

Marks: none.

Refusals: none.

Left alone: Parameters (empty, and no formula reads it), Keys (empty), and the Steps sheet.

`<...>` to fill in: `<database>`.

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
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT region, total_mins, runs,
  total_mins / SUM(total_mins) OVER () AS share
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
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
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

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). It has only typed columns and no query loads it.
- **Steps:** query `ok_runs`, read as a CTE by final `ok_by_job`. It is the query, not the Table of the same name. It keeps job_runs' SUCCESS rows (run_id, job_id, duration_mins).
- **Finals:**
  - Table `ok_runs` (run_id, job_id, duration_mins, hours). Its rows are query ok_runs' rows. `hours` is `duration_mins / 60`. No other Table's formula reads it.
  - Table `ok_by_job` (job_id, total_mins). Its rows are query ok_by_job's: duration_mins summed by job_id over the ok_runs step.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty and never a source, step or final. The Steps sheet.
- **To fill in:** `<database>`, in both finals.

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

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). It has only typed columns and no query loads it.
- **Steps:** Table `jobs` (job_id, job_name, team, runs, total), read as a CTE `jobs` by both finals. Its typed columns are read from `<database>.jobs`. Its `runs` and `total` are COUNTIF and SUMIF over job_runs, written as LEFT JOINs with COALESCE(.., 0). It is read by by_team's formula and by query busy_jobs, so it is a step.
- **Finals:**
  - Table `by_team` (team, team_total), a summary. Its only typed column, team, is the one its SUMIFS matches on, so its typed rows (data, finance, web) are typed in as groups. Its final is a GROUP BY of `jobs`. No other Table or query reads it.
  - Table `busy_jobs` (job_id, job_name, runs). Its rows are query busy_jobs' rows: jobs rows with runs of 3 or more.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty and never a source, step or final. The Steps sheet.
- **To fill in:** `<database>`, in all of the finals' blocks.

### Hive

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(r.runs, 0) AS runs,
    COALESCE(t.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
    ON j.job_id = r.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) t
    ON j.job_id = t.job_id
)
SELECT g.team, COALESCE(s.team_total, 0) AS team_total
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') g
LEFT JOIN (SELECT team, SUM(total) AS team_total FROM jobs GROUP BY team) s
  ON g.team = s.team
```

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(r.runs, 0) AS runs,
    COALESCE(t.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
    ON j.job_id = r.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) t
    ON j.job_id = t.job_id
)
SELECT job_id, job_name, runs FROM jobs WHERE runs >= 3
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X75

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). It has only typed columns and no query loads it.
- **Steps:** query `long_runs`, read as a CTE by final `long_per_day`. It is the query, not the Table of the same name. It keeps job_runs rows with duration_mins of 15 or more (run_id, dt, duration_mins).
- **Finals:**
  - Table `long_runs` (run_id, dt, duration_mins, over). Its rows are query long_runs' rows. `over` is `duration_mins - 15`. No other Table's formula reads it.
  - Table `long_per_day` (dt, runs). Its rows are query long_per_day's: the count of query long_runs' rows per dt.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty and never a source, step or final. The Steps sheet.
- **To fill in:** `<database>`, in both finals.

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

- **Sources:** `jobs` (job_id, job_name, team, region) and `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Each has only typed columns and no query loads it.
- **Steps:** query `finance_jobs`, read as a CTE by final Table `finance_runs`. It is the query, not the Table of the same name. It keeps jobs rows with team `finance` (job_id, job_name).
- **Finals:**
  - Table `finance_jobs` (job_id, job_name, label). Its rows are query finance_jobs' rows. `label` is `UPPER(job_name)`. No other Table's formula reads it.
  - Table `finance_runs` (run_id, job_name, duration_mins). Its rows are query finance_runs': job_runs joined on job_id to query finance_jobs, an inner join, so `job_name` comes from the step.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty and never a source, step or final. The Steps sheet.
- **To fill in:** `<database>`, in both finals.

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

