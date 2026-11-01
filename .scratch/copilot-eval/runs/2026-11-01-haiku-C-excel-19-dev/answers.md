date: 2026-11-01
arm: C
model: haiku
files: 19-dev

## X01

### Map

- **Sources:** job_runs (run_id, job_id, duration_mins, dt), its typed columns.
- **Steps:** none.
- **Finals:** Table job_runs (run_id, job_id, duration_mins, dt, duration_hours). It has a formula column, no query loads it, and nothing else reads it.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables (no fixed value is read, no value is typed over a formula); the Steps sheet's cells outside a Table.
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

- **Sources:** job_runs (run_id, job_id, status, duration_mins), its typed columns.
- **Steps:** none.
- **Finals:** Table job_runs (run_id, job_id, status, duration_mins, slow_job1, flag). It has formula columns, no query loads it, and nothing else reads it.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables; the Steps sheet's cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins,
  duration_mins > 10 AND job_id = 1 AS slow_job1,
  IF((duration_mins > 25 OR job_id = 3), 'check', 'ok') AS flag
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X03

### Map

- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), its typed columns.
- **Steps:** none.
- **Finals:** Table job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs). It has formula columns, no query loads it, and nothing else reads it.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:**
  - blank: status on run 98 is read by score, so it is COALESCE(status, '').
  - blank: avg_retry_secs on run 98 is read by mins_per_retry and total_secs, so it is COALESCE(avg_retry_secs, 0).
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables; the Steps sheet's cells outside a Table.
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

- **Sources:** jobs (job_id, job_name, team, region), its typed columns.
- **Steps:** none.
- **Finals:** Table jobs (job_id, job_name, team, region, code, name_length, third, odd). It has formula columns, no query loads it, and nothing else reads it.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables; the Steps sheet's cells outside a Table.
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

- **Sources:** job_runs (run_id, dt) and region_costs (job_id, cost_cents, region, dt), their typed columns.
- **Steps:** none.
- **Finals:**
  - Table job_runs (run_id, dt, month, days_since). Its formula columns are read by nothing else, and no query loads it.
  - Table region_costs (job_id, cost_cents, region, dt, day). Its formula column is read by nothing else, and no query loads it.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:**
  - date held as text: region_costs' dt (such as 20260911) is read by day, so day is CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)), giving 'yyyy-mm-dd' text.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables; the Steps sheet's cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, dt,
  MONTH(dt) AS month,
  DATEDIFF(dt, '2026-09-01') AS days_since
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

- **Sources:** `jobs`, typed only (job_id, job_name, team, region), read as `<database>.jobs`.
- **Steps:** none.
- **Finals:** `job_runs` (run_id, job_id, duration_mins, job_name, runs_of_job). Nothing else reads it, and its formula columns read its own rows and `jobs`.
- **Typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables (no formula reads Parameters, and no value is typed over a formula, so Keys needs no row); the Steps sheet and the D1 notes, which are text outside a Table.
- **To fill in:** `<database>`, in each read of the final's query.

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

- **Sources:** `jobs`, typed only (job_id, job_name, team, region), read as `<database>.jobs`.
- **Steps:** none.
- **Finals:** `job_runs` (run_id, job_id, status, team, region). Nothing else reads it; its formula columns read `jobs` only.
- **Typed over a formula:** none.
- **Marks:** none. The VLOOKUP and MATCH both use FALSE and 0, so each is an exact match. The blank status in run 98 is not read by any formula, so it is kept as it is.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables; the Steps sheet and the D1 notes, which are text outside a Table.
- **To fill in:** `<database>`, in each read of the final's query.

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

- **Sources:** `job_runs`, typed only (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`. Nothing in it is a formula, and by_job reads it.
- **Steps:** none.
- **Finals:** `by_job`, a summary. Its only typed column, job_id, is the one its SUMIFS, AVERAGEIFS and MAXIFS match on, so its final is a GROUP BY of job_runs, with its job_id groups (1, 2, 3) typed in. Columns: job_id, total_mins, avg_retry, longest. Nothing else reads it.
- **Typed over a formula:** none.
- **Marks:** none. The blank avg_retry_secs in run 98 is read by AVERAGEIFS, an -IFS form, so it is written as it is; AVG skips it as Excel's AVERAGEIFS does, and no COALESCE is needed. The MAXIFS prefix `_xlfn.` is read past.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables; the Steps sheet and the D1 notes, which are text outside a Table.
- **To fill in:** `<database>`, in the read of job_runs.

### Hive

```sql
SELECT j.job_id,
  COALESCE(c.total_mins, 0) AS total_mins,
  c.avg_retry AS avg_retry,
  COALESCE(c.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total_mins, AVG(avg_retry_secs) AS avg_retry,
    MAX(duration_mins) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
) c ON j.job_id = c.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X09

### Map

- **Sources:** `jobs`, typed only (job_id, job_name, team, region), read as `<database>.jobs`.
- **Steps:** none.
- **Finals:** `job_runs` (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost). Nothing else reads it.
- **Typed over a formula:** `cost` in run 97, typed as 100 where the formula gives the value. Keys has a row for job_runs with run_id, so the CASE matches on run_id = 97.
- **Marks:** "blank": avg_retry_secs is blank in run 98, and cost reads it in arithmetic, so cost writes COALESCE(avg_retry_secs, 0).
- **Refusals:** none.
- **Read in:** Parameters' rate, 0.5, is typed into cost as its value.
- **Left alone:** Keys, a settings Table read only for the match; Parameters, a settings Table read only for its value; the Steps sheet and the D1 notes, which are text outside a Table.
- **To fill in:** `<database>`, in the read of job_runs and of jobs.

### Hive

```sql
SELECT run_id, job_id, duration_mins, avg_retry_secs, team,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY team), 0) AS team_mins,
  CASE WHEN run_id = 97 THEN 100
    ELSE (duration_mins * 60 + COALESCE(avg_retry_secs, 0)) * 0.5 END AS cost
FROM (
  SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
) t
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X10

### Map

- **Sources:** none. The workbook's only data Table, job_runs, holds a formula column, and nothing else reads it.
- **Steps:** none.
- **Finals:** `job_runs` (run_id, job_id, duration_mins, dt, hours, sample), read as `<database>.job_runs`.
- **Typed over a formula:** `hours` in run 103, typed as 9. There is no Keys row for job_runs, so the CASE matches on every typed column of that row: run_id, job_id, duration_mins and dt.
- **Marks:** none.
- **Refusals:** `sample` (`=RAND()` in every row): RAND gives a new random number each time, so no Hive gives the same values. It is `NULL AS sample`.
- **Left alone:** Parameters and Keys, both empty settings Tables; the Steps sheet and the D1 notes, which are text outside a Table.
- **To fill in:** `<database>`, in the read of job_runs.

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

**Map**

- Sources: job_runs (its typed columns run_id, duration_mins), read as `<database>.job_runs`.
- Steps: none.
- Finals: job_runs (run_id, duration_mins, pick, scaled). No query loads it and no other formula reads it, so it is a final. Its typed columns are also its source.
- Refusals (NULL in the place of the column, with why):
  - pick: `INDIRECT("B"&ROW())` uses INDIRECT and ROW(), which hang on the sheet's row order. Written as `NULL AS pick`.
  - scaled: reads Summary C2, a cell outside a Table that is not a defined name. Written as `NULL AS scaled`.
- Marks: none. No value is typed over a formula, so Keys needs no row.
- Left alone: the bar chart on the Summary sheet; the Summary sheet's cell C2 (read only by the refused scaled column).
- Left out: Parameters and Keys, the two empty settings Tables (never a source, step or final). The Steps sheet is the guide and is left alone.
- To fill in: `<database>`.

### Hive

```sql
SELECT run_id, duration_mins, NULL AS pick, NULL AS scaled
FROM <database>.job_runs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X12

**Map**

- Sources: job_runs (its typed columns run_id, duration_mins), read as `<database>.job_runs`.
- Steps: none.
- Finals: job_runs (run_id, duration_mins, running, loop, with_tax). No query loads it and no other formula reads it, so it is a final.
- Refusals (NULL in the place of the column, with why):
  - running: `SUM(OFFSET(...))` uses OFFSET and ROW(), which hang on the sheet's row order. Written as `NULL AS running`.
  - loop: reads its own column on its own row, so it is circular. Written as `NULL AS loop`.
- Marks:
  - with_tax reads the defined name tax_rate, which is Summary B3 holding 0.2. Written as the value: `duration_mins * 0.2`. Move tax_rate into Parameters (name tax_rate, value 0.2) and read it from there.
- Typed over a formula: none. Keys needs no row.
- Left alone: the Summary sheet's cell B3, which is read only through its defined name.
- Left out: Parameters and Keys, the two empty settings Tables (never a source, step or final). The Steps sheet is the guide and is left alone.
- To fill in: `<database>`.

### Hive

```sql
SELECT run_id, duration_mins, NULL AS running, NULL AS loop, duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X13

**Map**

- Sources:
  - job_runs (its typed columns run_id, job_id), read as `<database>.job_runs`.
  - jobs (its typed columns job_id, job_name, team, region), read as `<database>.jobs`. It has only typed columns and no query loads it, so it is a source only.
- Steps: none.
- Finals: job_runs (run_id, job_id, name, doubled). No query loads it and no other formula reads it, so it is a final.
- Marks:
  - name: `VLOOKUP(..., jobs, 2, TRUE)` is an approximate match. Written as the exact match: a LEFT JOIN of jobs on job_id, taking job_name. Check that the approximate match gave the same rows as the exact one.
- Refusals (NULL in the place of the column, with why):
  - doubled: `DOUBLE` is a defined name holding a LAMBDA. Written as `NULL AS doubled`.
- Typed over a formula: none. Keys needs no row.
- Left out: Parameters and Keys, the two empty settings Tables (never a source, step or final). The Steps sheet is the guide and is left alone.
- To fill in: `<database>`.

### Hive

```sql
SELECT r.run_id, r.job_id, j.job_name AS name, NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X14

**Map**

- Sources: job_runs (its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
- Steps: job_runs (its typed columns, plus hours = duration_mins / 60). by_job's formula reads job_runs[hours] and job_runs[job_id], so job_runs is a step, a CTE in by_job's final, and not a final of its own.
- Finals: by_job (job_id, total_hours). Its only typed column is job_id, the one its SUMIFS matches on, so it is a summary: its typed job_ids (1, 2, 3) are typed in, and its total is a GROUP BY of job_runs.
- Marks: none. The blank cells in status and avg_retry_secs (row 98) are read as they are, as no formula reads them.
- Refusals: none.
- Typed over a formula: none. Keys needs no row.
- Left alone: the PivotTable on the sheet "Pivot", from job_runs.
- Left out: Parameters and Keys, the two empty settings Tables (never a source, step or final). The Steps sheet is the guide and is left alone.
- To fill in: `<database>`.

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

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X15

**Map**

- Sources: tblRuns (its typed columns Run ID, Job ID, Duration (mins)), read as `<database>.tblRuns`. The Table name is plain, so it stays as it is.
- Steps: none.
- Finals: tblRuns (Run ID, Job ID, Duration (mins), Hours). No query loads it and no other formula reads it, so it is a final.
- Marks:
  - The headers with a space or brackets are written in snake case inside `<...>` for you to fill in: Run ID as `<run_id>`, Job ID as `<job_id>`, Duration (mins) as `<duration_mins>`. Hours is plain, so it stays `hours`.
- Refusals: none.
- Typed over a formula: none. Keys needs no row.
- Left out: Parameters and Keys, the two empty settings Tables (never a source, step or final). The Steps sheet is the guide and is left alone.
- To fill in: `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`.

### Hive

```sql
SELECT <run_id>, <job_id>, <duration_mins>, <duration_mins> / 60 AS hours
FROM <database>.tblRuns
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X16

### Map

- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`. It has typed columns only and no query loads it.
- Steps: none.
- Finals: Table `long_runs` (run_id, job_id, minutes, hours), loaded by query `long_runs`. No formula reads it. Query `long_runs`'s steps Source, Kept, Long, Hours and Renamed all go into its one SELECT and WHERE.
- Not a source, step or final: Parameters and Keys, both empty settings Tables.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the notes in D1 of Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`.

### Hive

```sql
SELECT run_id, job_id, duration_mins AS minutes, duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X17

### Map

- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`. It has typed columns only and no query loads it.
- Steps: query `ok_runs`. Query `ok_by_job` names it as its Source, so it is a CTE in that final's block. It is connection only, but it is read, so it is not left out.
- Finals: Table `ok_by_job` (job_id, runs, total_mins), loaded by query `ok_by_job`. No formula reads it.
- Not a source, step or final: Parameters and Keys, both empty settings Tables.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the notes in D1 of Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`.

### Hive

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

- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and `jobs` (job_id, job_name, team, region), each read as `<database>.<table>`. Both have typed columns only and no query loads them.
- Steps: none. Query `top_runs`'s steps Joined, Expanded, Sorted, Top and Kept all go into its one SELECT.
- Finals: Table `top_runs` (run_id, job_name, duration_mins), loaded by query `top_runs`. No formula reads it.
- Not a source, step or final: Parameters and Keys, both empty settings Tables.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the notes in D1 of Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>` in each of the two reads.

### Hive

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

- Sources:
  - `scheduler_runs` (run_id, job_id, dt), read as `<database>.scheduler_runs`. It has typed columns only and no query loads it.
  - `job_runs` (run_id, job_id, dt, the three columns query `all_runs` keeps), read as `<database>.job_runs`. It is the table `Sql.Database("dwh01", "ops")` names, outside the workbook.
- Steps: none.
- Finals: Table `all_runs` (run_id, job_id, dt), loaded by query `all_runs`. Its Table.Combine stacks the two sources, so UNION ALL. No formula reads it.
- Not a source, step or final: Parameters and Keys, both empty settings Tables.
- Left out: query `holidays`. It is connection only, loads nothing and nothing reads it. Its Web.Contents reads a web address, so it is refused and left out.
- Values typed over a formula: none.
- Marks: `job_runs` is read from `Sql.Database("dwh01", "ops")`, outside the workbook. It is read as the table it names, for you to check.
- Refusals: query `holidays`, for Web.Contents, left out.
- Left alone: the Steps sheet and the notes in D1 of Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>` in each of the two reads.

### Hive

```sql
SELECT run_id, job_id, dt FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X20

### Map

- Sources: `run_alerts` (alert_id, run_id, severity, dt), read as `<database>.run_alerts`. It has typed columns only and no query loads it.
- Steps: none. Query `alert_pivot`'s count column n, added as 1 on every row, is folded into THEN 1 in the pivot columns.
- Finals: Table `alert_pivot` (run_id, high, low), loaded by query `alert_pivot`. No formula reads it.
- Not a source, step or final: Parameters and Keys, both empty settings Tables.
- Values typed over a formula: none.
- Marks: Table.Pivot. Each value in the sample gets a column, `SUM(CASE WHEN severity = '...' THEN 1 END)`, for high and low, NULL where none, as M leaves it. The pivot's columns are now fixed as high and low; a new severity value needs a new column.
- Refusals: none.
- Left alone: the Steps sheet and the notes in D1 of Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`.

### Hive

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
- **Sources**: job_runs, its typed columns run_id, job_id, status, duration_mins, read from `<database>.job_runs`.
- **Steps**: none.
- **Finals**: job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). Its formula columns are longest_first, shortest_ok and job_total. No other Table's formula and no query reads it, so it is a final; its own formulas don't count.
- **Settings, never a source, step or final**: Parameters and Keys, both empty. No formula reads a Parameters value, and no value is typed over a formula, so Keys needs no row.
- **Typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet's cells, which sit outside any Table.
- **To fill in**: `<database>`.

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
- **Sources**: job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read from `<database>.job_runs`; jobs, its typed columns job_id and job_name, read from `<database>.jobs`.
- **Steps**: none.
- **Finals**: jobs (job_id, job_name, runs, avg_mins, id_order). Its formula columns are runs, avg_mins and id_order. No other Table's formula and no query reads it, so it is a final. Its typed columns are not a summary, as job_name is not one of the COUNTIF's match columns.
- **Settings, never a source, step or final**: Parameters and Keys, both empty. No formula reads a Parameters value, and no value is typed over a formula, so Keys needs no row.
- **Typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet's cells, which sit outside any Table.
- **To fill in**: `<database>`.

### Hive
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

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X43

### Map
- **Sources**: job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read from `<database>.job_runs`; jobs, its typed columns job_id, job_name, team, region, read from `<database>.jobs`.
- **Steps**: none.
- **Finals**:
  - busy_teams (team, runs, shortest, avg_mins). Loaded by query busy_teams, which reads job_runs and jobs and groups them by team; no Table formula reads it, so its rows are the query's.
  - statuses (job_id, status). Loaded by query statuses, which reads job_runs; no Table formula reads it, so its rows are the query's.
- **Settings, never a source, step or final**: Parameters and Keys, both empty. No formula reads a Parameters value, and no value is typed over a formula, so Keys needs no row.
- **Typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet's cells, which sit outside any Table.
- **To fill in**: `<database>`.

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
- **Sources**: job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read from `<database>.job_runs`; jobs, its typed columns job_id, job_name, team, region, read from `<database>.jobs`; scheduler_runs, its typed columns run_id, job_id, dt, read from `<database>.scheduler_runs`.
- **Steps**: none.
- **Finals**:
  - jobs_with_runs (run_id, job_name). Loaded by query jobs_with_runs, which reads job_runs and jobs in a right outer join; no Table formula reads it, so its rows are the query's.
  - never_scheduled (job_id, job_name, team). Loaded by query never_scheduled, which reads jobs and scheduler_runs in a left anti join; no Table formula reads it, so its rows are the query's.
- **Settings, never a source, step or final**: Parameters and Keys, both empty. No formula reads a Parameters value, and no value is typed over a formula, so Keys needs no row.
- **Typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet's cells, which sit outside any Table.
- **To fill in**: `<database>`.

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
- **Sources**: job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read from `<database>.job_runs`; scheduler_runs, its typed columns run_id, job_id, dt, read from `<database>.scheduler_runs`.
- **Steps**: none.
- **Finals**:
  - run_days (run_id, dt). Loaded by query run_days, which stacks the run_id and dt of job_runs and scheduler_runs, distinct; no Table formula reads it, so its rows are the query's.
  - matched (run_id, job_id, dt, status). Loaded by query matched, which full outer joins scheduler_runs with job_runs on run_id; no Table formula reads it, so its rows are the query's.
- **Settings, never a source, step or final**: Parameters and Keys, both empty. No formula reads a Parameters value, and no value is typed over a formula, so Keys needs no row.
- **Typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet's cells, which sit outside any Table.
- **To fill in**: `<database>`.

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

- **Sources:** `job_runs`, its typed columns (run_id, job_id, status, duration_mins, dt), read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** `job_runs`, with columns run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins. Nothing but its own formulas reads it, and those don't count, so it is a final.
- **Values typed over a formula:** none. Keys holds no row.
- **Marks:**
  - `not_ok`: Excel counts a blank status (row 98) as not SUCCESS, so the condition is `(status <> 'SUCCESS' OR status IS NULL)`.
  - `failed_in_job`: the wildcard "*ail*" matches without case, so it is `LOWER(status) LIKE '%ail%'`.
- **Blank:** status is blank in row 98. Only -IFS forms read it, which skip a blank, so it is written as it is, not COALESCEd.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables (no formula reads Parameters, no value is typed over a formula); never a source, step or final. The Steps sheet, the workbook's instructions.
- **To fill in:** `<database>`, the database name.

### Hive

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

- **Sources:** `job_runs`, its typed columns (run_id, job_id, duration_mins), read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:**
  - `job_runs`, with columns run_id, job_id, duration_mins, share, vs_avg, rank_in_job.
  - `job_runs (Total Row)`, with columns duration_mins (SUBTOTAL 109, a SUM) and share (SUBTOTAL 109, a SUM). The "Total" label and the empty cells get no column.
- **Values typed over a formula:** none. Keys holds no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables; never a source, step or final. The Steps sheet, the workbook's instructions.
- **To fill in:** `<database>`, the database name.

### Hive

```sql
SELECT run_id, job_id, duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

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

- **Sources:** `job_runs`, its typed columns (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`. It is a source only: its typed columns and no formula of its own.
- **Steps:** none.
- **Finals:**
  - `by_job`, a summary (its only typed column, job_id, is what its SUMIFS and COUNTIFS match on). Its groups are typed in: job_id 1, 2, 3. Columns job_id, total_mins, runs, longest.
  - `by_job (Total Row)`, with columns total_mins (SUM), runs (SUM) and longest (MAX, SUBTOTAL 104). The "Total" label gets no column.
- **Values typed over a formula:** none. Keys holds no row.
- **Marks:** none.
- **Refusals:** none.
- **Left out:** job_runs' status, avg_retry_secs and dt, since no formula reads them. Their blanks (status and avg_retry_secs, row 98) are therefore not read, so no blank mark applies.
- **Left alone:** Parameters and Keys, both empty settings Tables; never a source, step or final. The Steps sheet, the workbook's instructions.
- **To fill in:** `<database>`, the database name.

### Hive

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

- **Sources:** `job_runs`, its typed columns (run_id, dt), read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** `job_runs`, with columns run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label. Nothing but its own formulas reads it, so it is a final.
- **Values typed over a formula:** none. Keys holds no row.
- **Marks:**
  - `a_month_on`: EDATE is ADD_MONTHS, marked: a month's end stays one.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables; never a source, step or final. The Steps sheet, the workbook's instructions.
- **To fill in:** `<database>`, the database name.

### Hive

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

- **Sources:** `jobs`, its typed columns (job_id, job_name, team, region), read as `<database>.jobs`.
- **Steps:** none.
- **Finals:** `jobs`, with columns job_id, job_name, team, region, title, tag, code, has_sync, tens. Its formulas read its own row, which doesn't count, so nothing else reads it and it is a final. It is both a source and a final.
- **Values typed over a formula:** none. Keys holds no row.
- **Marks:** none. The sample has no blank in a column a formula reads. The names hold only letters and underscores, so INITCAP gives PROPER's result.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables; never a source, step or final. The Steps sheet, the workbook's instructions.
- **To fill in:** `<database>`, the database name.

### Hive

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

- **Sources:** `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs); `scheduler_runs` (run_id, job_id, dt).
- **Steps:** none.
- **Finals:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on). No Total Row.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** `weighted` ("blank"): avg_retry_secs is blank in row 98, so it is written as COALESCE(avg_retry_secs, 0), as Excel's SUMPRODUCT counts that blank as 0. `no_status` reads status as it is, as ISBLANK skips a blank (no mark).
- **Refusals:** none.
- **Left alone:** `Parameters` and `Keys`, both empty (no formula uses a Parameters value; no value is typed over a formula); the Steps sheet and the D1 notes on Parameters and Keys (cells outside a Table).
- **To fill in:** `<database>`, in both sources.

### Hive

```sql
-- job_runs
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

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (job_id, job_name, team, region).
- **Steps:** none.
- **Finals:** `picked` (run_id, job_id, status, avg_retry_secs, status_lc), loaded by Power Query "picked"; `ran_jobs` (job_id, job_name, team, region), loaded by Power Query "ran_jobs".
- **Values typed over a formula:** none.
- **Marks:** `picked` ("blank"): avg_retry_secs is blank in job_runs row 98, so it is written as COALESCE(avg_retry_secs, 0), as Table.ReplaceValue does.
- **Refusals:** none.
- **Left alone:** `Parameters` and `Keys`, both empty; the Steps sheet and the D1 notes on Parameters and Keys (cells outside a Table).
- **To fill in:** `<database>`, in both sources.

### Hive

```sql
-- picked
SELECT run_id, job_id, status, COALESCE(avg_retry_secs, 0) AS avg_retry_secs, LOWER(status) AS status_lc
FROM <database>.job_runs
WHERE job_id IN (1, 2) AND (status IS NULL OR status LIKE 'S%')
```

```sql
-- ran_jobs
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r ON r.job_id = j.job_id
WHERE j.job_name LIKE '%a%'
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X58

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (job_id, job_name, team, region); `scheduler_runs` (run_id, job_id, dt); `region_budgets` (job_id, budget_cents, region).
- **Steps:** none.
- **Finals:** `job_regions` (job_id, region), loaded by Power Query "job_regions"; `numbered` (run_id, dt, duration_mins, n), loaded by Power Query "numbered"; `days_per_job` (job_id, days), loaded by Power Query "days_per_job"; `unrun` (run_id, job_id), loaded by Power Query "unrun"; `measures` (run_id, measure, amount), loaded by Power Query "measures". No Total Row.
- **Values typed over a formula:** none.
- **Marks:** `measures` ("blank"): avg_retry_secs is blank in job_runs row 98, so that run's avg row is dropped, as M drops a null there. `days_per_job`: the Table.Sort by days has no FirstN or index after it, so no ORDER BY is written and the order is dropped.
- **Refusals:** none.
- **Left alone:** `Parameters` and `Keys`, both empty; the Steps sheet and the D1 notes on Parameters and Keys (cells outside a Table).
- **To fill in:** `<database>`, in the four sources.

### Hive

```sql
-- job_regions
WITH regions AS (
  SELECT DISTINCT region FROM <database>.region_budgets
)
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN regions r
```

```sql
-- numbered
SELECT run_id, dt, duration_mins,
  ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC) AS n
FROM <database>.job_runs
```

```sql
-- days_per_job
SELECT job_id, COUNT(DISTINCT dt) AS days
FROM <database>.job_runs
GROUP BY job_id
```

```sql
-- unrun
SELECT run_id, job_id FROM <database>.scheduler_runs
EXCEPT
SELECT run_id, job_id FROM <database>.job_runs
```

```sql
-- measures
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

- **Sources:** `jobs` (job_id, job_name, team, region); `run_alerts` (alert_id, run_id, severity, dt).
- **Steps:** `job_runs` (run_id, job_id, duration_mins, dt, team, alerts, running_mins). It has formula columns and is read by by_team's formulas and by Power Query "noisy_runs", so it is a CTE in each final that reads it. Its typed columns are read from `<database>.job_runs`.
- **Finals:**
  - `by_team` (team, total_mins, alerted_runs): a summary. Its typed groups, data and finance, are typed in, and job_runs is read in a GROUP BY.
  - `by_team (Total Row)` (total_mins, alerted_runs): the Total Row's "Total" label gets no column, and the Table's runs are the Total Row's only two totals.
  - `noisy_runs` (run_id, team, alerts, running_mins), loaded by Power Query "noisy_runs".
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** `Parameters` and `Keys`, both empty; the Steps sheet.
- **To fill in:** `<database>`, in the three sources (job_runs, jobs, run_alerts).

### Hive

```sql
-- by_team
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
-- by_team (Total Row)
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
-- noisy_runs
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

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (job_id, job_name, team, region); `region_budgets` (job_id, budget_cents, region).
- **Steps:** `base` (run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name, region), the connection-only query "base". It loads nothing, but Power Query "by_region" and "top_runs" both read it, so it is a CTE in each final that reads it.
- **Finals:**
  - `by_region` (region, total_mins, runs, share), loaded by Power Query "by_region". Its share is total_mins over the Table's own total.
  - `by_region (Total Row)` (total_mins): the Total Row's "Total" label gets no column, and its runs and share cells are empty, so only total_mins has a column.
  - `top_runs` (run_id, job_name, region), loaded by Power Query "top_runs".
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** `Parameters` and `Keys`, both empty; the Steps sheet.
- **To fill in:** `<database>`, in the three sources (job_runs, jobs, region_budgets).

### Hive

```sql
-- by_region
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  INNER JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
grouped AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT region, total_mins, runs, total_mins / SUM(total_mins) OVER () AS share
FROM grouped
```

```sql
-- by_region (Total Row)
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  INNER JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
grouped AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
),
by_region AS (
  SELECT region, total_mins, runs, total_mins / SUM(total_mins) OVER () AS share
  FROM grouped
)
SELECT SUM(total_mins) AS total_mins
FROM by_region
```

```sql
-- top_runs
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

- **Sources:** job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read from `<database>.job_runs`.
- **Steps:** query ok_runs (run_id, job_id, duration_mins), read by ok_by_job's final as a CTE. Its Table ok_runs is a final of its own, not a step.
- **Finals:**
  - Table ok_runs: run_id, job_id, duration_mins, hours.
  - Table ok_by_job: job_id, total_mins.
- **Typed over a formula:** none. The Keys Table has no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Parameters and Keys Tables, empty and read by no formula (never a source, step or final); the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- **To fill in:** `<database>` in each query, the database that holds job_runs.

### Hive

```sql
-- Final: Table ok_runs
SELECT run_id, job_id, duration_mins, duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE status = 'SUCCESS'
```
```sql
-- Final: Table ok_by_job
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins FROM <database>.job_runs WHERE status = 'SUCCESS'
)
SELECT job_id, SUM(duration_mins) AS total_mins FROM ok_runs GROUP BY job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X72

### Map

- **Sources:** jobs, its typed columns job_id, job_name and team, read from `<database>.jobs`; job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read from `<database>.job_runs`.
- **Steps:** Table jobs (job_id, job_name, team, runs, total). It is read by query busy_jobs and by by_team's formula, so it is a CTE in each of those two finals. Its runs is COUNTIF over job_runs by job_id, and its total is SUMIF of duration_mins by job_id, each with COALESCE to 0.
- **Finals:**
  - Table busy_jobs: job_id, job_name, runs (the rows of query busy_jobs).
  - Table by_team, a summary: team, team_total. Its typed teams data, finance and web are typed in; jobs is read, as a GROUP BY of the step.
- **Typed over a formula:** none. The Keys Table has no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Parameters and Keys Tables, empty and read by no formula (never a source, step or final); the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- **To fill in:** `<database>` in each query, the database that holds jobs and job_runs.

### Hive

```sql
-- Final: Table busy_jobs
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(r.runs, 0) AS runs,
    COALESCE(s.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
    ON j.job_id = r.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) s
    ON j.job_id = s.job_id
)
SELECT job_id, job_name, runs FROM jobs WHERE runs >= 3
```
```sql
-- Final: Table by_team (summary)
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(r.runs, 0) AS runs,
    COALESCE(s.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
    ON j.job_id = r.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) s
    ON j.job_id = s.job_id
)
SELECT g.team, COALESCE(c.team_total, 0) AS team_total
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') g
LEFT JOIN (SELECT team, SUM(total) AS team_total FROM jobs GROUP BY team) c
  ON g.team = c.team
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X75

### Map

- **Sources:** job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read from `<database>.job_runs`.
- **Steps:** query long_runs (run_id, dt, duration_mins), read by long_per_day's final as a CTE. Its Table long_runs is a final of its own, not a step.
- **Finals:**
  - Table long_runs: run_id, dt, duration_mins, over.
  - Table long_per_day: dt, runs.
- **Typed over a formula:** none. The Keys Table has no row.
- **Marks:** the header `over` is a Hive keyword, so the final writes it in backticks. Its values are unchanged.
- **Refusals:** none.
- **Left alone:** the Parameters and Keys Tables, empty and read by no formula (never a source, step or final); the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- **To fill in:** `<database>` in each query, the database that holds job_runs.

### Hive

```sql
-- Final: Table long_runs
SELECT run_id, dt, duration_mins, duration_mins - 15 AS `over`
FROM <database>.job_runs
WHERE duration_mins >= 15
```
```sql
-- Final: Table long_per_day
WITH long_runs AS (
  SELECT run_id, dt, duration_mins FROM <database>.job_runs WHERE duration_mins >= 15
)
SELECT dt, COUNT(*) AS runs FROM long_runs GROUP BY dt
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X76

### Map

- **Sources:** jobs, its typed columns job_id, job_name, team and region, read from `<database>.jobs`; job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read from `<database>.job_runs`.
- **Steps:** query finance_jobs (job_id, job_name), read by finance_runs' final as a CTE. Its Table finance_jobs is a final of its own, not a step.
- **Finals:**
  - Table finance_jobs: job_id, job_name, label.
  - Table finance_runs: run_id, job_name, duration_mins.
- **Typed over a formula:** none. The Keys Table has no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Parameters and Keys Tables, empty and read by no formula (never a source, step or final); the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- **To fill in:** `<database>` in each query, the database that holds jobs and job_runs.

### Hive

```sql
-- Final: Table finance_jobs
SELECT job_id, job_name, UPPER(job_name) AS label
FROM <database>.jobs
WHERE team = 'finance'
```
```sql
-- Final: Table finance_runs
WITH finance_jobs AS (
  SELECT job_id, job_name FROM <database>.jobs WHERE team = 'finance'
)
SELECT r.run_id, f.job_name, r.duration_mins
FROM <database>.job_runs r
JOIN finance_jobs f ON r.job_id = f.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X79

### Map

- **Sources:** job_runs, its typed columns run_id, job_id, status and duration_mins, read from `<database>.job_runs`.
- **Steps:** none. No query loads or names a step, and no other Table reads job_runs.
- **Finals:** Table job_runs: run_id, job_id, status, duration_mins, kept, long_or_failed. Its formula columns read only its own row.
- **Typed over a formula:** none. The Keys Table has no row.
- **Marks:**
  - "blank": the sample has a blank status (run 98), and both formulas read status, so each reads COALESCE(status, '').
- **Refusals:** none.
- **Left alone:** the Parameters and Keys Tables, empty and read by no formula (never a source, step or final); the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- **To fill in:** `<database>`, the database that holds job_runs.

### Hive

```sql
-- Final: Table job_runs
SELECT run_id, job_id, status, duration_mins,
  IF(COALESCE(status, '') <> '' AND COALESCE(status, '') <> 'TEST', 1, 0) AS kept,
  IF((duration_mins > 25 OR COALESCE(status, '') = 'FAILED'), 'yes', 'no') AS long_or_failed
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X81

### Map

- **Sources:** `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. It holds only typed columns and no query loads it, so it is a source, read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** `by_job` (job_id, long_failed, mid_mins, failed_or_test), a summary. Its formulas match on its typed column job_id, so its typed job_ids 1, 2 and 3 are typed in as its groups, and job_runs is read. Each formula reads its own row's job_id, not another formula, so nothing else reads it.
- **Typed over a formula:** none, so no Keys row is needed.
- **Marks:** none. status's blank (row 98) sits only inside -IFS conditions, which skip it as written; `(status <> 'TEST' OR status IS NULL)` keeps it, as Excel does.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty, never a source, step or final; no formula reads Parameters. The Steps sheet and the D1 notes, which are cells outside a Table.
- **To fill in:** `<database>`, in each read of job_runs.

### Hive

```sql
SELECT j.job_id,
  COALESCE(c1.long_failed, 0) AS long_failed,
  COALESCE(c2.mid_mins, 0) AS mid_mins,
  COALESCE(c3.failed_or_test, 0) AS failed_or_test
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS long_failed
  FROM <database>.job_runs
  WHERE status = 'FAILED' AND duration_mins >= 20
  GROUP BY job_id
) c1 ON j.job_id = c1.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS mid_mins
  FROM <database>.job_runs
  WHERE duration_mins > 10 AND duration_mins <= 30 AND (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) c2 ON j.job_id = c2.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS failed_or_test
  FROM <database>.job_runs
  WHERE status IN ('FAILED', 'TEST')
  GROUP BY job_id
) c3 ON j.job_id = c3.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X82

### Map

- **Sources:** `job_runs`, its typed columns run_id, job_id, status, duration_mins, dt, read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** `job_runs` (run_id, job_id, status, duration_mins, dt, needs_look, failed_long_mins, failed_or_late). It has formula columns and no query loads it, and its formulas read its own columns, not another Table's formula or a query, so nothing else reads it: it is a final, not a step. It is not a summary, as it has no SUMIFS or COUNTIFS.
- **Typed over a formula:** none, so no Keys row is needed.
- **Marks:** blank. status is blank in row 98. needs_look is a plain IF, not an -IFS form, so it reads `COALESCE(status, '')`. The conditions in failed_long_mins and failed_or_late are written as they are, as they skip a blank as Excel does.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty, never a source, step or final. The Steps sheet and the D1 notes, which are cells outside a Table.
- **To fill in:** `<database>`, in the read of job_runs.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins, dt,
  IF((COALESCE(status, '') = 'FAILED' OR duration_mins > 25) AND NOT job_id = 1, 1, 0) AS needs_look,
  SUM(CASE WHEN status = 'FAILED' AND duration_mins > 15 THEN duration_mins ELSE 0 END) OVER () AS failed_long_mins,
  COUNT(CASE WHEN status = 'FAILED' OR dt = '2026-09-24' THEN 1 END) OVER () AS failed_or_late
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

