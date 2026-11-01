date: 2026-11-01
arm: C
model: haiku
files: 20-dev

## X01

### Map
- **Sources:** job_runs, its typed columns run_id, job_id, duration_mins and dt, read from `<database>.job_runs`.
- **Steps:** none. The workbook lists no Power Query.
- **Finals:** job_runs (run_id, job_id, duration_mins, dt, duration_hours). Its formula column duration_hours (`=[@duration_mins]/60`) reads its own row only, no query loads the Table, and nothing else reads it, so it is a final.
- **Values typed over a formula:** none. Every row holds the same formula.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables, so never a source, step or final. No charts, PivotTables, cells outside a Table, or Total Row.
- **To fill in:** `<database>` in the FROM.

### Hive
```sql
SELECT run_id, job_id, duration_mins, dt, duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X02

### Map
- **Sources:** job_runs, its typed columns run_id, job_id, status and duration_mins, read from `<database>.job_runs`.
- **Steps:** none. The workbook lists no Power Query.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, slow_job1, flag). Its formula columns read its own row only, and nothing else reads the Table, so it is a final.
- **Values typed over a formula:** none. Every row holds the same formula in each column.
- **Marks:** none. The blank status in row 98 is kept as NULL; no formula reads status, so no COALESCE is needed.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables. No charts, PivotTables, cells outside a Table, or Total Row.
- **To fill in:** `<database>` in the FROM.

### Hive
```sql
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF((duration_mins > 25 OR job_id = 3), 'check', 'ok') AS flag
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X03

### Map
- **Sources:** job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read from `<database>.job_runs`.
- **Steps:** none. The workbook lists no Power Query.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs). Its formula columns read its own row only, and nothing else reads the Table, so it is a final.
- **Values typed over a formula:** none.
- **Marks:**
  - "blank": status is blank in row 98, and score's SWITCH reads status. Written as `COALESCE(status, '')`.
  - "blank": avg_retry_secs is blank in row 98, and mins_per_retry and total_secs read it. Written as `COALESCE(avg_retry_secs, 0)`.
- **Converted, not marks:** `_xlfn.SWITCH` read past its prefix as a CASE; IFERROR(a / b, 0) as COALESCE(a / b, 0).
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables. No charts, PivotTables, cells outside a Table, or Total Row.
- **To fill in:** `<database>` in the FROM.

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
- **Sources:** jobs, its typed columns job_id, job_name, team and region, read from `<database>.jobs`.
- **Steps:** none. The workbook lists no Power Query.
- **Finals:** jobs (job_id, job_name, team, region, code, name_length, third, odd). Its formula columns read its own row only, and nothing else reads the Table, so it is a final.
- **Values typed over a formula:** none.
- **Marks:** none. Every cell the formulas read is filled in.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables. No charts, PivotTables, cells outside a Table, or Total Row.
- **To fill in:** `<database>` in the FROM.

### Hive
```sql
SELECT job_id, job_name, team, region,
  CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-', region) AS code,
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
  - job_runs, its typed columns run_id and dt, read from `<database>.job_runs`.
  - region_costs, its typed columns job_id, cost_cents, region and dt, read from `<database>.region_costs`.
- **Steps:** none. The workbook lists no Power Query.
- **Finals:**
  - job_runs (run_id, dt, month, days_since). Its formula columns read its own row only, and nothing else reads the Table.
  - region_costs (job_id, cost_cents, region, dt, day). Its formula column reads its own row only, and nothing else reads the Table.
- **Values typed over a formula:** none. Every row holds the same formula in each column.
- **Marks:**
  - "date held as text": region_costs dt holds dates as text such as 20260911, and the day column reads it. Written as `CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2))`, so day comes out as text 'yyyy-mm-dd', not a date.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables. No charts, PivotTables, cells outside a Table, or Total Row. The blank cost_cents in region_costs row 29 is kept as NULL; no formula reads cost_cents, so it is not a mark.
- **To fill in:** `<database>` in each FROM.

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

- Sources: `<database>.jobs` (job_id, job_name, team, region), read only for the lookup in job_name. `<database>.job_runs` (run_id, job_id, duration_mins), its typed columns.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job). No formula reads job_runs from another Table, so it is a final as well as a source.
- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys, both empty. No formula uses a fixed value and no value is typed over a formula, so there is no Keys row. Neither is a source, step or final.
- To fill in: `<database>` in each read.

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

- Sources: `<database>.jobs` (job_id, job_name, team, region), read for the lookups in team and region. `<database>.job_runs` (run_id, job_id, status), its typed columns.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, team, region). No formula reads job_runs from another Table, so it is a final as well as a source.
- Typed over a formula: none.
- Marks: none. The blank status at run 98 is kept as it is, as no formula reads status.
- Refusals: none.
- Left alone: Parameters and Keys, both empty. Neither is a source, step or final.
- To fill in: `<database>` in each read.

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

- Sources: `<database>.job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), its typed columns only, so a source and never a final.
- Steps: none.
- Finals: by_job, a summary, as its only typed column (job_id) is the one its SUMIFS, AVERAGEIFS and MAXIFS match on. Its groups are job_id 1, 2 and 3, typed in. Columns: job_id, total_mins, avg_retry, longest. Its final query is a GROUP BY of job_runs.
- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the blank avg_retry_secs at run 98 is left as it is. AVG skips it, as AVERAGEIFS does in Excel, so no COALESCE is written there. Parameters and Keys, both empty, are neither a source, step nor final.
- To fill in: `<database>` in the read.

### Hive

```sql
SELECT j.job_id,
  COALESCE(g.total_mins, 0) AS total_mins,
  g.avg_retry,
  COALESCE(g.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total_mins, AVG(avg_retry_secs) AS avg_retry,
    MAX(duration_mins) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
) g ON j.job_id = g.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X09

### Map

- Sources: `<database>.jobs` (job_id, job_name, team, region), read for the lookup in team. `<database>.job_runs` (run_id, job_id, duration_mins, avg_retry_secs), its typed columns.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost). No formula reads job_runs from another Table, so it is a final as well as a source.
- Typed over a formula: cost, where run_id is 97, is typed as 100. Keys holds job_runs with run_id, so the CASE matches on run_id.
- Marks: blank. avg_retry_secs is blank at run 98 and cost reads it in arithmetic, so it is written as COALESCE(avg_retry_secs, 0).
- Refusals: none.
- Left alone: Parameters is read in as its value: rate is 0.5, typed into cost. Keys is used only for the match above and is never a source, step or final.
- To fill in: `<database>` in each read.

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

- Sources: `<database>.job_runs` (run_id, job_id, duration_mins, dt), its typed columns.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample). No formula reads job_runs from another Table, so it is a final as well as a source.
- Typed over a formula: hours, where run_id is 103, is typed as 9. Keys is empty, so there is no Keys row. The CASE therefore matches every typed column of that row: run_id, job_id, duration_mins and dt.
- Marks: none.
- Refusals: sample, as `=RAND()` gives a new random value on each recalculation and has no fixed Hive value. Written as `NULL AS sample`.
- Left alone: Parameters, empty, is neither a source, step nor final.
- To fill in: `<database>` in the read.

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
- **Sources:** job_runs (run_id, duration_mins), its typed columns.
- **Steps:** none.
- **Finals:** job_runs (run_id, duration_mins, pick, scaled). No query loads it and no other Table's formula reads it, so it is a final; its own formula columns don't count.
- **Typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals (NULL in place):**
  - pick: `=INDIRECT("B"&ROW())` uses INDIRECT and ROW(), both refused. `NULL AS pick`.
  - scaled: `=job_runs[[#This Row],[duration_mins]]*Summary!$C$2` reads C2 on Summary, a cell outside a Table that is not a defined name (address Summary!C2). `NULL AS scaled`.
- **Left alone:** the Steps sheet (cells outside a Table); the Summary sheet's C2 (3) and its bar chart; Parameters and Keys, both empty, never a source, step or final.
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
- **Sources:** job_runs (run_id, duration_mins), its typed columns.
- **Steps:** none.
- **Finals:** job_runs (run_id, duration_mins, running, loop, with_tax). No query or other Table reads it, so it is a final.
- **Typed over a formula:** none. Keys is empty.
- **Marks:**
  - with_tax reads the defined name tax_rate, which is Summary!$B$3, a cell outside a Table. Written as its value, 0.2. Move tax_rate into Parameters.
- **Refusals (NULL in place):**
  - running: `=SUM(OFFSET(...,ROW()-1,1))` uses OFFSET and ROW(), which hang on the sheet's row order. `NULL AS running`.
  - loop: `=job_runs[[#This Row],[loop]]+1` reads its own column (circular). `NULL AS loop`.
- **Left alone:** the Steps sheet (cells outside a Table); Summary's B3, read only through tax_rate; Parameters and Keys, both empty.
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
- **Sources:** jobs (job_id, job_name, team, region), its typed columns only, so a source and never a final. job_runs (run_id, job_id), its typed columns.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, name, doubled). No formula of another Table reads it, so it is a final. jobs is a source only.
- **Typed over a formula:** none. Keys is empty.
- **Marks:**
  - name: `=VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)` is an approximate match (TRUE). Written as the exact match on job_id, through a LEFT JOIN to jobs; its column 2 is job_name.
- **Refusals (NULL in place):**
  - doubled: `=DOUBLE(job_runs[[#This Row],[job_id]])`. DOUBLE is a defined name holding `_xlfn.LAMBDA(x,x*2)`, a LAMBDA, refused. `NULL AS doubled`.
- **Left alone:** the Steps sheet (cells outside a Table); jobs' team and region, which no final reads; Parameters and Keys, both empty.
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
- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), its typed columns.
- **Steps:** job_runs (job_id, hours = `duration_mins / 60`). by_job's formula reads job_runs[hours], so job_runs is a step, a CTE in by_job's final, and not a final itself.
- **Finals:** by_job (job_id, total_hours), a summary. Its only typed column, job_id, is the one its SUMIFS matches on, so its typed job_ids (1, 2, 3) are typed in as its groups, and job_runs is read.
- **Typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the PivotTable on sheet "Pivot" (from job_runs: rows job_id, Sum of duration_mins); the blank status and avg_retry_secs cells on run 98, which no formula reads, so no COALESCE; Parameters and Keys, both empty; the Steps sheet (cells outside a Table).
- **To fill in:** `<database>`.

### Hive
```sql
WITH job_runs AS (
  SELECT job_id, duration_mins / 60 AS hours
  FROM <database>.job_runs
)
SELECT j.job_id, COALESCE(s.total_hours, 0) AS total_hours
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, SUM(hours) AS total_hours FROM job_runs GROUP BY job_id) s
  ON j.job_id = s.job_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X15

### Map
- **Sources:** tblRuns (Run ID, Job ID, Duration (mins)), its typed columns, written `<run_id>`, `<job_id>`, `<duration_mins>`.
- **Steps:** none.
- **Finals:** tblRuns (Run ID, Job ID, Duration (mins), Hours). No query or other Table reads it, and Hours reads only its own row, so it is a final.
- **Typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet (cells outside a Table); Parameters and Keys, both empty.
- **To fill in:** `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`.

### Hive
```sql
SELECT <run_id>, <job_id>, <duration_mins>, <duration_mins> / 60 AS hours
FROM <database>.tblRuns
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X16

### Map
- **Sources:** job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** long_runs (run_id, job_id, minutes, hours). Query long_runs loads Table long_runs, and no formula reads that Table, so the Table is a final and its rows are the query's.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables, never a source, step or final.
- **To fill in:** `<database>`.

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
- **Sources:** job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read as `<database>.job_runs`.
- **Steps:** ok_runs, a connection-only query. Query ok_by_job's M names it (`Source = ok_runs`), so it is a CTE in ok_by_job's block. It keeps job_runs' rows with status SUCCESS and all six of job_runs' columns.
- **Finals:** ok_by_job (job_id, runs, total_mins). Query ok_by_job loads Table ok_by_job, and no formula reads that Table, so the Table is a final and its rows are the query's.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables, never a source, step or final.
- **To fill in:** `<database>`.

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
- **Sources:** job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read as `<database>.job_runs`; and jobs, its typed columns job_id, job_name, team, region, read as `<database>.jobs`. Neither Table is loaded by a query, so both are sources.
- **Steps:** none.
- **Finals:** top_runs (run_id, job_name, duration_mins). Query top_runs loads Table top_runs, and no formula reads that Table, so the Table is a final and its rows are the query's. The query joins jobs as a LEFT JOIN, sorts by duration_mins descending and keeps the first 3 rows.
- **Values typed over a formula:** none.
- **Marks:** the sort has a tie at 30 minutes, run 97 and run 103. Hive gives no fixed order between two tied rows, so their order may differ from the sample. The set of three rows is the same.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables, never a source, step or final.
- **To fill in:** `<database>`.

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
- **Sources:** scheduler_runs, its typed columns run_id, job_id, dt, read as `<database>.scheduler_runs`; and job_runs, read by query all_runs from `Sql.Database("dwh01", "ops")`, its table ops.job_runs, with columns run_id, job_id, dt, read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** all_runs (run_id, job_id, dt). Query all_runs loads Table all_runs, and no formula reads that Table, so the Table is a final and its rows are the query's. The query stacks the two sources with Table.Combine.
- **Values typed over a formula:** none.
- **Marks:** all_runs reads ops.job_runs from the dwh01 server, a source outside the workbook. It is read as `<database>.job_runs`; check that it is the table you mean. Table.Combine stacks the rows with UNION ALL, so duplicate rows are kept.
- **Refusals:** the query holidays (`Web.Contents`, a web source) is left out. It loads nothing and nothing reads it.
- **Left alone:** Parameters and Keys, both empty settings Tables, never a source, step or final.
- **To fill in:** `<database>`.

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
- **Sources:** run_alerts, its typed columns alert_id, run_id, severity, dt, read as `<database>.run_alerts`.
- **Steps:** none.
- **Finals:** alert_pivot (run_id, high, low). Query alert_pivot loads Table alert_pivot, and no formula reads that Table, so the Table is a final and its rows are the query's. The query keeps run_alerts' rows for runs 97 and 101, and pivots severity into one column per value.
- **Values typed over a formula:** none.
- **Marks:** Table.Pivot becomes a `SUM(CASE WHEN severity = '...' THEN 1 END)` column for each value in the sample, high and low, with NULL where a run has none, as M leaves it. The pivot's columns are now fixed to high and low, so a severity that appears later gets no column. The count column n is always 1, so the sum counts rows.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables, never a source, step or final.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
WHERE (run_id = 97 OR run_id = 101)
GROUP BY run_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X41

### Map

**Sources**
- `job_runs`: typed columns run_id, job_id, status, duration_mins, read as `<database>.job_runs`.

**Steps**
- None.

**Finals**
- `job_runs` (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). It has formula columns and nothing else reads it, so it is a final. Its formulas: longest_first is RANK.EQ on duration_mins, descending; shortest_ok is MINIFS of duration_mins where status is SUCCESS, per job_id, 0 where none; job_total is SUMIF of duration_mins per job_id.

**Typed over a formula**: none.

**Marks**: none. The blank status in row 98 sits inside the MINIFS condition, so it is written as it is.

**Refusals**: none.

**Left alone**: the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table.

**Settings**: Parameters and Keys are empty, so neither is a source, step or final. No formula reads a Parameters value, and no Keys row is needed.

**To fill in**: `<database>`.

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

**Sources**
- `job_runs`: typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read as `<database>.job_runs`. Only job_id and duration_mins are read by a formula.

**Steps**
- None.

**Finals**
- `jobs` (job_id, job_name, runs, avg_mins, id_order). It has formula columns and nothing else reads it, and its own formulas don't count, so it is a final. Its formulas: runs is COUNTIF of job_runs per job_id, a LEFT JOIN with COUNT(*) and 0 where none; avg_mins is IFERROR of AVERAGEIF over job_runs, a LEFT JOIN with AVG and 0 where none; id_order is RANK.EQ on job_id, ascending (the `_xlfn.` prefix is read past).

**Typed over a formula**: none.

**Marks**: none.

**Refusals**: none.

**Left alone**: the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table.

**Settings**: Parameters and Keys are empty, so neither is a source, step or final. No Keys row is needed.

**To fill in**: `<database>`.

### Hive

```sql
SELECT j.job_id, j.job_name,
  COALESCE(r.runs, 0) AS runs,
  COALESCE(a.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
  ON j.job_id = r.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins FROM <database>.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X43

### Map

**Sources**
- `job_runs`: typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read as `<database>.job_runs`.
- `jobs`: typed columns job_id, job_name, team, region, read as `<database>.jobs`.

**Steps**
- None.

**Finals**
- `busy_teams` (team, runs, shortest, avg_mins). This is the Table busy_teams, loaded by query busy_teams. No formula reads it, so its rows are the query's. The query joins job_runs to jobs on job_id, groups by team, and keeps teams with more than 4 runs.
- `statuses` (job_id, status). This is the Table statuses, loaded by query statuses. The query keeps job_id and status from job_runs and drops duplicate pairs.

**Typed over a formula**: none.

**Marks**: none.

**Refusals**: none.

**Left alone**: the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table.

**Settings**: Parameters and Keys are empty, so neither is a source, step or final.

**To fill in**: `<database>`.

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

**Sources**
- `job_runs`: typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read as `<database>.job_runs`.
- `jobs`: typed columns job_id, job_name, team, region, read as `<database>.jobs`.
- `scheduler_runs`: typed columns run_id, job_id, dt, read as `<database>.scheduler_runs`.

**Steps**
- None.

**Finals**
- `jobs_with_runs` (run_id, job_name). This is the Table jobs_with_runs, loaded by query jobs_with_runs. The query is a RightOuter join, so every job appears, and a job with no run keeps a NULL run_id (cache_warm, as the sample's blank row shows).
- `never_scheduled` (job_id, job_name, team). This is the Table never_scheduled, loaded by query never_scheduled. The query is a LeftAnti join, so it keeps the jobs with no scheduler_runs row.

**Typed over a formula**: none.

**Marks**: none.

**Refusals**: none.

**Left alone**: the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table.

**Settings**: Parameters and Keys are empty, so neither is a source, step or final.

**To fill in**: `<database>`.

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

**Sources**
- `job_runs`: typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read as `<database>.job_runs`.
- `scheduler_runs`: typed columns run_id, job_id, dt, read as `<database>.scheduler_runs`.

**Steps**
- None.

**Finals**
- `run_days` (run_id, dt). This is the Table run_days, loaded by query run_days. The query stacks run_id and dt from job_runs and scheduler_runs, then removes duplicates, so it is a UNION.
- `matched` (run_id, job_id, dt, status). This is the Table matched, loaded by query matched. The query is a FullOuter join of scheduler_runs with job_runs on run_id, keeping status from job_runs. A job_runs-only row, such as run 99, keeps NULL in run_id, job_id and dt, as the sample's TEST row shows.

**Typed over a formula**: none.

**Marks**: none.

**Refusals**: none.

**Left alone**: the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table.

**Settings**: Parameters and Keys are empty, so neither is a source, step or final.

**To fill in**: `<database>`.

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

- Sources: job_runs (its typed columns: run_id, job_id, status, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins). Nothing else reads it, and its COUNTIFS and SUMIFS are over its own rows, so it is a final, not a summary (run_id is typed but never matched on).
- Settings, neither a source, step nor final: Parameters (empty, so no value is read in) and Keys (empty, as no value is typed over a formula, so no Keys row).
- Values typed over a formula: none.
- Marks: none. The blank status on run 98 is read only inside -IFS conditions, so it is written as it is.
- Refusals: none.
- Left alone: the Steps sheet, and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).
- `<...>` to fill in: `<database>` in the FROM.

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

- Sources: job_runs (its typed columns: run_id, job_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job); job_runs (Total Row) (duration_mins, share), its Total Row's two cells that hold a total. The label "Total" and the empty cells are not columns.
- Settings, neither a source, step nor final: Parameters (empty) and Keys (empty; no value typed over a formula, so no Keys row).
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet, and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).
- `<...>` to fill in: `<database>` in each FROM.

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

- Sources: job_runs (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt). The finals read only job_id and duration_mins.
- Steps: none.
- Finals:
  - by_job (job_id, total_mins, runs, longest), a summary: its only typed column, job_id, is the one its SUMIFS, COUNTIFS and MAXIFS match on. Its typed job_ids 1, 2 and 3 are its groups, typed in; job_runs is read.
  - by_job (Total Row) (total_mins, runs, longest): SUBTOTAL(109) is SUM for total_mins and runs, SUBTOTAL(104) is MAX for longest.
- Settings, neither a source, step nor final: Parameters (empty) and Keys (empty; no value typed over a formula, so no Keys row).
- Values typed over a formula: none.
- Marks: none. The blanks in job_runs (status and avg_retry_secs on run 98) are not read by any formula.
- Refusals: none.
- Left alone: the Steps sheet, and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).
- `<...>` to fill in: `<database>` in each FROM.

### Hive

```sql
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
SELECT SUM(total_mins) AS total_mins, SUM(runs) AS runs, MAX(longest) AS longest
FROM by_job
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X54

### Map

- Sources: job_runs (its typed columns: run_id, dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label). No formula reads it from another Table, so it is a final.
- Settings, neither a source, step nor final: Parameters (empty) and Keys (empty; no value typed over a formula, so no Keys row).
- Values typed over a formula: none.
- Marks: a_month_on, EDATE written as ADD_MONTHS, marked: a month's end stays one.
- Refusals: none.
- Left alone: the Steps sheet, and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).
- `<...>` to fill in: `<database>` in the FROM.

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

- Sources: jobs (its typed columns: job_id, job_name, team, region).
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens). Its formulas read only its own row, so it is a final.
- Settings, neither a source, step nor final: Parameters (empty) and Keys (empty; no value typed over a formula, so no Keys row).
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet, and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).
- `<...>` to fill in: `<database>` in the FROM.

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

**Map**
- Sources: scheduler_runs (run_id, job_id, dt). Typed columns only, and no query loads it. Read as `<database>.scheduler_runs`, for the XLOOKUP in scheduled_on.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on). No query loads it, and no other Table reads it.
- Values typed over a formula: none. Keys stays empty.
- Marks: blank, in weighted. avg_retry_secs is blank in run 98, so it is read as COALESCE(avg_retry_secs, 0). no_status reads status as it is, inside ISBLANK.
- Refusals: none.
- Left alone: Parameters and Keys (empty settings Tables, never a source, step or final); the Steps sheet (cells outside a Table).
- To fill in: `<database>`, in both reads (job_runs and scheduler_runs).

**Hive**

```sql
-- Final: job_runs
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
LEFT JOIN <database>.scheduler_runs s ON j.run_id = s.run_id
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X57

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (job_id, job_name, team, region). Typed columns only, and no query loads either. Read as `<database>.job_runs` and `<database>.jobs`.
- Steps: none. No query names another query.
- Finals:
  - picked (run_id, job_id, status, avg_retry_secs, status_lc), the Table loaded by query picked. No formula reads it.
  - ran_jobs (job_id, job_name, team, region), the Table loaded by query ran_jobs. No formula reads it.
- Values typed over a formula: none. Keys stays empty.
- Marks: blank, in picked. Run 98 has a blank avg_retry_secs, which the query's Table.ReplaceValue fills with 0, written as COALESCE(avg_retry_secs, 0).
- Refusals: none.
- Left alone: Parameters and Keys (empty settings Tables); the Steps sheet (cells outside a Table).
- To fill in: `<database>`, in each read.

**Hive**

```sql
-- Final: picked
SELECT run_id, job_id, status, COALESCE(avg_retry_secs, 0) AS avg_retry_secs, LOWER(status) AS status_lc
FROM <database>.job_runs
WHERE job_id IN (1, 2) AND (status IS NULL OR status LIKE 'S%')
```

```sql
-- Final: ran_jobs
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r ON j.job_id = r.job_id
WHERE j.job_name LIKE '%a%'
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X58

**Map**
- Sources:
  - jobs (job_id, job_name, team, region)
  - job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt)
  - scheduler_runs (run_id, job_id, dt)
  - region_budgets (job_id, budget_cents, region)
  
  All typed columns only, and no query loads any of them. Each is read as `<database>.<table>`.
- Steps: none.
- Finals:
  - job_regions (job_id, region), loaded by query job_regions.
  - numbered (run_id, dt, duration_mins, n), loaded by query numbered. Its sort is kept as n, with ties in run_id ascending.
  - days_per_job (job_id, days), loaded by query days_per_job.
  - unrun (run_id, job_id), loaded by query unrun.
  - measures (run_id, measure, amount), loaded by query measures. The null avg_retry_secs of run 98 is left out, as the unpivot drops a null.
- Values typed over a formula: none. Keys stays empty.
- Marks:
  - days_per_job: the sort by days, descending, is dropped. No FirstN or index comes after it, so the Hive table holds no order.
- Refusals: none.
- Left alone: Parameters and Keys (empty settings Tables); the Steps sheet (cells outside a Table).
- To fill in: `<database>`, in each read.

**Hive**

```sql
-- Final: job_regions
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) r
```

```sql
-- Final: numbered
SELECT run_id, dt, duration_mins,
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
SELECT run_id, job_id FROM <database>.scheduler_runs
EXCEPT
SELECT run_id, job_id FROM <database>.job_runs
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

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X67

**Map**
- Sources:
  - jobs (job_id, job_name, team, region)
  - run_alerts (alert_id, run_id, severity, dt)
  
  Typed columns only. Read as `<database>.jobs` and `<database>.run_alerts`.
- Steps: job_runs (run_id, job_id, duration_mins, dt, team, alerts, running_mins). It holds formula columns, and by_team's formulas and query noisy_runs read it. It is a CTE in each final that reads it.
- Finals:
  - by_team (team, total_mins, alerted_runs), a summary. Its groups data and finance are typed in, and job_runs is read.
  - by_team (Total Row) (total_mins, alerted_runs). The label "Total" has no column. It is a final of its own, reading by_team as a CTE.
  - noisy_runs (run_id, team, alerts, running_mins), loaded by query noisy_runs. No other Table reads it.
- Values typed over a formula: none. Keys stays empty.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys (empty settings Tables); the Steps sheet (cells outside a Table).
- To fill in: `<database>`, in each read.

**Hive**

```sql
-- Final: by_team
WITH job_runs AS (
  SELECT j.run_id, j.job_id, j.duration_mins, j.dt,
    jb.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(j.duration_mins) OVER (
      PARTITION BY j.job_id ORDER BY j.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs j
  LEFT JOIN <database>.jobs jb ON j.job_id = jb.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON j.run_id = a.run_id
),
by_team AS (
  SELECT g.team,
    COALESCE(t.total_mins, 0) AS total_mins,
    COALESCE(c.alerted_runs, 0) AS alerted_runs
  FROM (SELECT 'data' AS team UNION ALL SELECT 'finance') g
  LEFT JOIN (SELECT team, SUM(duration_mins) AS total_mins FROM job_runs GROUP BY team) t
    ON g.team = t.team
  LEFT JOIN (SELECT team, COUNT(*) AS alerted_runs FROM job_runs WHERE alerts > 0 GROUP BY team) c
    ON g.team = c.team
)
SELECT team, total_mins, alerted_runs FROM by_team
```

```sql
-- Final: by_team (Total Row)
WITH job_runs AS (
  SELECT j.run_id, j.job_id, j.duration_mins, j.dt,
    jb.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(j.duration_mins) OVER (
      PARTITION BY j.job_id ORDER BY j.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs j
  LEFT JOIN <database>.jobs jb ON j.job_id = jb.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON j.run_id = a.run_id
),
by_team AS (
  SELECT g.team,
    COALESCE(t.total_mins, 0) AS total_mins,
    COALESCE(c.alerted_runs, 0) AS alerted_runs
  FROM (SELECT 'data' AS team UNION ALL SELECT 'finance') g
  LEFT JOIN (SELECT team, SUM(duration_mins) AS total_mins FROM job_runs GROUP BY team) t
    ON g.team = t.team
  LEFT JOIN (SELECT team, COUNT(*) AS alerted_runs FROM job_runs WHERE alerts > 0 GROUP BY team) c
    ON g.team = c.team
)
SELECT SUM(total_mins) AS total_mins, SUM(alerted_runs) AS alerted_runs FROM by_team
```

```sql
-- Final: noisy_runs
WITH job_runs AS (
  SELECT j.run_id, j.job_id, j.duration_mins, j.dt,
    jb.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(j.duration_mins) OVER (
      PARTITION BY j.job_id ORDER BY j.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs j
  LEFT JOIN <database>.jobs jb ON j.job_id = jb.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON j.run_id = a.run_id
)
SELECT run_id, team, alerts, running_mins
FROM job_runs
WHERE alerts >= 2
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X68

**Map**
- Sources:
  - job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt)
  - jobs (job_id, job_name, team, region)
  - region_budgets (job_id, budget_cents, region)
  
  Typed columns only, read by query base. Read as `<database>.job_runs`, `<database>.jobs` and `<database>.region_budgets`.
- Steps: base (run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name, region). It is the query with connection only, which loads no Table. It is read by by_region and top_runs, so it is a CTE in each of them.
- Finals:
  - by_region (region, total_mins, runs, share), loaded by query by_region. No other Table reads it. share is a formula over the Table's total_mins.
  - by_region (Total Row) (total_mins). The Total Row's only cell that holds a total is total_mins; the label and the blank cells have no column. It is a final of its own, reading by_region as a CTE.
  - top_runs (run_id, job_name, region), loaded by query top_runs. No formula reads it.
- Values typed over a formula: none. Keys stays empty.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys (empty settings Tables); the Steps sheet (cells outside a Table).
- To fill in: `<database>`, in each read.

**Hive**

```sql
-- Final: by_region
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
by_region AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT region, total_mins, runs, total_mins / SUM(total_mins) OVER () AS share
FROM by_region
```

```sql
-- Final: by_region (Total Row)
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
by_region AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT SUM(total_mins) AS total_mins FROM by_region
```

```sql
-- Final: top_runs
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT run_id, job_name, region
FROM base
ORDER BY duration_mins DESC, run_id ASC
LIMIT 2
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X71

### Map
- Sources: `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: Power Query `ok_runs` (run_id, job_id, duration_mins), a CTE in the final `ok_by_job`, since query ok_by_job's M names it.
- Finals:
  - Table `ok_runs` (run_id, job_id, duration_mins, hours), loaded by query ok_runs; no other Table's formula or query reads it, so its rows are the query's.
  - Table `ok_by_job` (job_id, total_mins), loaded by query ok_by_job.
- Values typed over a formula: none. No Keys row is needed.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys (empty settings Tables that no formula reads, so no role); the Steps sheet; the notes in D1 of Parameters and Keys (cells outside a Table).
- To fill in: `<database>`, the database that holds `job_runs`, in each read.

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
- Sources:
  - `jobs` (its typed columns: job_id, job_name, team).
  - `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: Table `jobs` with its formula columns runs and total. Both by_team's formula and query busy_jobs read it, so it is a CTE in each final: runs and total are its columns, computed from `job_runs` in the CTE.
- Finals:
  - Table `by_team` (team, team_total), a summary: its only typed column, team, is the one SUMIFS matches on, so its typed groups data, finance and web are typed in and `jobs` is read.
  - Table `busy_jobs` (job_id, job_name, runs), loaded by query busy_jobs, which reads `jobs`.
- Values typed over a formula: none. No Keys row is needed.
- Marks: none. The blank status in the sample's row 98 is in no formula's read, so it is not a mark here.
- Refusals: none.
- Left alone: Parameters and Keys (empty settings Tables); the Steps sheet; the notes in D1 of Parameters and Keys.
- To fill in: `<database>`, the database that holds `jobs` and `job_runs`, in each read.

### Hive

```sql
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
SELECT t.team, COALESCE(g.team_total, 0) AS team_total
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (SELECT team, SUM(total) AS team_total FROM jobs GROUP BY team) g
  ON t.team = g.team
```

```sql
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
SELECT job_id, job_name, runs
FROM jobs
WHERE runs >= 3
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X75

### Map
- Sources: `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: Power Query `long_runs` (run_id, dt, duration_mins), a CTE in the final `long_per_day`, since query long_per_day's M names it.
- Finals:
  - Table `long_runs` (run_id, dt, duration_mins, over), loaded by query long_runs; no other Table's formula or query reads it, so its rows are the query's.
  - Table `long_per_day` (dt, runs), loaded by query long_per_day.
- Values typed over a formula: none. No Keys row is needed.
- Marks: none.
- Refusals: none.
- Kept, to check: `over` is a reserved word in Hive. It is kept as the header, as file 11 keeps a plain name, so the convert batch may need it quoted or renamed.
- Left alone: Parameters and Keys (empty settings Tables); the Steps sheet; the notes in D1 of Parameters and Keys.
- To fill in: `<database>`, the database that holds `job_runs`, in each read.

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
- Sources:
  - `jobs` (its typed columns: job_id, job_name, team, region).
  - `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: Power Query `finance_jobs` (job_id, job_name), a CTE in the final `finance_runs`, since query finance_runs' M names it in its join.
- Finals:
  - Table `finance_jobs` (job_id, job_name, label), loaded by query finance_jobs; no other Table's formula or query reads it, so its rows are the query's.
  - Table `finance_runs` (run_id, job_name, duration_mins), loaded by query finance_runs.
- Values typed over a formula: none. No Keys row is needed.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys (empty settings Tables); the Steps sheet; the notes in D1 of Parameters and Keys.
- To fill in: `<database>`, the database that holds `jobs` and `job_runs`, in each read.

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

## X79

### Map
- Sources: `job_runs` (its typed columns: run_id, job_id, status, duration_mins).
- Steps: none.
- Finals:
  - Table `job_runs` (run_id, job_id, status, duration_mins, kept, long_or_failed). It has formula columns that nothing else reads (their own row doesn't count), so it is a final.
- Values typed over a formula: none. No Keys row is needed.
- Marks:
  - blank: `status` has a blank in the sample (row 98), and the formulas `kept` and `long_or_failed` read it, so `status` is written as COALESCE(status, '') in both. The IF and OR forms here are not an -IF(S) form or ISBLANK, so the rule for them does not apply.
- Converted, not marked: `kept` as IF(a AND b, 1, 0), and `long_or_failed` with OR bracketed as (a OR b).
- Refusals: none.
- Left alone: Parameters and Keys (empty settings Tables); the Steps sheet; the notes in D1 of Parameters and Keys.
- To fill in: `<database>`, the database that holds `job_runs`.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins,
  IF(COALESCE(status, '') <> '' AND COALESCE(status, '') <> 'TEST', 1, 0) AS kept,
  IF((duration_mins > 25 OR COALESCE(status, '') = 'FAILED'), 'yes', 'no') AS long_or_failed
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X81

**Map**

- Sources: job_runs, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. No query loads it and it holds no formula column.
- Steps: none.
- Finals: by_job, a summary (its only typed column, job_id, is the one its COUNTIFS match on). Its final is a GROUP BY of job_runs, with by_job's typed job_ids (1, 2, 3) typed in. Columns: job_id, long_failed, mid_mins, failed_or_test.
- Parameters and Keys: settings Tables, both empty. Not a source, step or final. No formula reads a fixed value, and no value is typed over a formula, so Keys needs no row.
- Values typed over a formula: none.
- Marks: none.
- Rewrite, named: failed_or_test adds two COUNTIFS on job_id that differ only in status ("FAILED", then "TEST"), so it is written as one count with status IN ('FAILED', 'TEST').
- Blank: status is blank in row 98 (job 2). The "<>TEST" condition in mid_mins keeps it, as Excel does, through `OR status IS NULL`.
- Refusals: none.
- Left alone: the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table).
- To fill in: `<database>`, in each read of job_runs.

### Hive

```sql
SELECT j.job_id,
  COALESCE(lf.long_failed, 0) AS long_failed,
  COALESCE(mm.mid_mins, 0) AS mid_mins,
  COALESCE(ft.failed_or_test, 0) AS failed_or_test
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, COUNT(*) AS long_failed FROM <database>.job_runs WHERE status = 'FAILED' AND duration_mins >= 20 GROUP BY job_id) lf
  ON j.job_id = lf.job_id
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS mid_mins FROM <database>.job_runs WHERE duration_mins > 10 AND duration_mins <= 30 AND (status <> 'TEST' OR status IS NULL) GROUP BY job_id) mm
  ON j.job_id = mm.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS failed_or_test FROM <database>.job_runs WHERE status IN ('FAILED', 'TEST') GROUP BY job_id) ft
  ON j.job_id = ft.job_id
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X82

**Map**

- Sources: job_runs, its typed columns: run_id, job_id, status, duration_mins, dt.
- Steps: none.
- Finals: job_runs, which is also its own source. No query loads it, and no other Table's formula or query reads it. Its own formula columns, reading its own rows and columns, don't count, so it is a final. It is not a summary, as it has typed columns that no COUNTIFS or SUMIFS matches on. Columns, in the Table's order: run_id, job_id, status, duration_mins, dt, needs_look, failed_long_mins, failed_or_late.
- Parameters and Keys: settings Tables, both empty. Not a source, step or final. No formula reads a fixed value, no value is typed over a formula, so Keys needs no row.
- Values typed over a formula: none.
- Converted, whole-column reads: failed_long_mins and failed_or_late read job_runs as a whole, so each is written with OVER () as every row shows the same total.
- Marks:
  - Blank: status is blank in row 98. needs_look, failed_long_mins and failed_or_late read status as plain comparisons, so each reads COALESCE(status, '').
  - Date held against text: failed_or_late compares dt with "2026-09-24". In Excel, = between a date and text is FALSE, so the workbook may count differently from the Hive. Check whether dt is held as a date or as text before the convert run.
- Refusals: none.
- Left alone: the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table).
- To fill in: `<database>`, in the read of job_runs.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins, dt,
  IF((COALESCE(status, '') = 'FAILED' OR duration_mins > 25) AND NOT job_id = 1, 1, 0) AS needs_look,
  SUM(CASE WHEN COALESCE(status, '') = 'FAILED' AND duration_mins > 15 THEN duration_mins ELSE 0 END) OVER () AS failed_long_mins,
  COUNT(CASE WHEN (COALESCE(status, '') = 'FAILED' OR dt = '2026-09-24') THEN 1 END) OVER () AS failed_or_late
FROM <database>.job_runs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
