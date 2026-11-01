date: 2026-11-01
arm: C
model: haiku
files: 18-r5

## X01

### Map
- Sources: `job_runs` (typed columns run_id, job_id, duration_mins, dt)
- Steps: none
- Finals: `job_runs` (run_id, job_id, duration_mins, dt, duration_hours)
- Typed over a formula: none
- Marks: none
- Refusals: none
- Left alone: Parameters and Keys (both empty; no formula uses a fixed value, and no value is typed over a formula, so Keys needs no row); the Steps sheet and the D1 notes on Parameters and Keys (cells outside a Table)
- To fill in: `<database>`

### Hive
```sql
SELECT run_id, job_id, duration_mins, dt, duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X02

### Map
- Sources: `job_runs` (typed columns run_id, job_id, status, duration_mins)
- Steps: none
- Finals: `job_runs` (run_id, job_id, status, duration_mins, slow_job1, flag)
- Typed over a formula: none
- Marks: none
- Refusals: none
- Left alone: Parameters and Keys (both empty; no typed-over value, so Keys needs no row); the Steps sheet and the D1 notes on Parameters and Keys (cells outside a Table); the blank status on row 98 is kept as it is, as no formula reads status
- To fill in: `<database>`

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
- Sources: `job_runs` (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt)
- Steps: none
- Finals: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs)
- Typed over a formula: none
- Marks:
  - blank: `status` is blank on row 98, and score reads it; written as COALESCE(status, '') inside score
  - blank: `avg_retry_secs` is blank on row 98, and mins_per_retry and total_secs read it; written as COALESCE(avg_retry_secs, 0) inside both
- Refusals: none
- Left alone: Parameters and Keys (both empty; no typed-over value, so Keys needs no row); the Steps sheet and the D1 notes on Parameters and Keys (cells outside a Table)
- To fill in: `<database>`

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
- Sources: `jobs` (typed columns job_id, job_name, team, region)
- Steps: none
- Finals: `jobs` (job_id, job_name, team, region, code, name_length, third, odd)
- Typed over a formula: none
- Marks: none
- Refusals: none
- Left alone: Parameters and Keys (both empty; no typed-over value, so Keys needs no row); the Steps sheet and the D1 notes on Parameters and Keys (cells outside a Table)
- To fill in: `<database>`

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
- Sources: `job_runs` (typed columns run_id, dt); `region_costs` (typed columns job_id, cost_cents, region, dt)
- Steps: none
- Finals: `job_runs` (run_id, dt, month, days_since); `region_costs` (job_id, cost_cents, region, dt, day)
- Typed over a formula: none
- Marks:
  - date held as text: `region_costs` dt holds 20260911 as text, and day reads it; written as CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2))
- Refusals: none
- Left alone: Parameters and Keys (both empty; no typed-over value, so Keys needs no row); the Steps sheet and the D1 notes on Parameters and Keys (cells outside a Table); the blank cost_cents on row 29 of region_costs is kept as it is, as no formula reads cost_cents
- To fill in: `<database>`

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

**1. Map**

- Sources: `jobs` (its typed columns: job_id, job_name, team, region); `job_runs` (its typed columns: run_id, job_id, duration_mins).
- Steps: none.
- Finals: `job_runs` (run_id, job_id, duration_mins, job_name, runs_of_job). No other Table's formula or query reads job_runs, so it is a final, and its own formulas don't count.
- Typed over a formula: none. Keys and Parameters are empty, so no Keys row is needed.
- Marks: none. job_name, the XLOOKUP, is a LEFT JOIN to jobs. runs_of_job, the COUNTIFS over job_runs' own Table, is a COUNT(*) window with COALESCE to 0.
- Refusals: none.
- Left alone: `Parameters` and `Keys`, both empty. No formula reads them, and they are never a source, step or final.
- To fill in: `<database>`, in both reads.

**2. Hive**

### Final job_runs

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

**3. Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X07

**1. Map**

- Sources: `jobs` (its typed columns: job_id, job_name, team, region); `job_runs` (its typed columns: run_id, job_id, status).
- Steps: none.
- Finals: `job_runs` (run_id, job_id, status, team, region). No other Table's formula or query reads job_runs, so it is a final.
- Typed over a formula: none. Keys and Parameters are empty.
- Marks: none. team (VLOOKUP) and region (INDEX/MATCH) are both exact matches on job_id, so both come from one LEFT JOIN to jobs. The blank status in run 98 is read by no formula, so it stays NULL with no mark.
- Refusals: none.
- Left alone: `Parameters` and `Keys`, both empty; never a source, step or final.
- To fill in: `<database>`, in both reads.

**2. Hive**

### Final job_runs

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

**3. Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X08

**1. Map**

- Sources: `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: `by_job`, a summary (columns job_id, total_mins, avg_retry, longest). Its only typed column is job_id, which its SUMIFS, AVERAGEIFS and MAXIFS match on, so its typed job_ids 1, 2 and 3 are its groups, typed in, and its final query is a GROUP BY of job_runs.
- Typed over a formula: none. Keys and Parameters are empty.
- Marks: none. The blank avg_retry_secs in run 98 is inside AVERAGEIFS, an -IFS form, so it is written as it is.
- Refusals: none.
- Left alone: `Parameters` and `Keys`, both empty; never a source, step or final.
- To fill in: `<database>`, in the read of job_runs.

**2. Hive**

### Final by_job (summary)

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

**3. Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X09

**1. Map**

- Sources: `jobs` (its typed columns: job_id, job_name, team, region; the final reads job_id and team); `job_runs` (its typed columns: run_id, job_id, duration_mins, avg_retry_secs).
- Steps: none.
- Finals: `job_runs` (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost). No other Table's formula or query reads job_runs, so it is a final.
- Typed over a formula: cost in run 97 is typed as 100. Keys has job_runs with run_id, so the value is matched on run_id.
- Parameters: `rate` is read in as its value, 0.5.
- Marks: "blank". avg_retry_secs is blank in run 98, and cost reads it outside an -IFS form, so it is COALESCE(avg_retry_secs, 0).
- Refusals: none.
- Left alone: none. Parameters (rate) and Keys are read as above, never as sources.
- To fill in: `<database>`, in both reads.

**2. Hive**

### Final job_runs

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

**3. Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X10

**1. Map**

- Sources: `job_runs` (its typed columns: run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: `job_runs` (run_id, job_id, duration_mins, dt, hours, sample). No other Table's formula or query reads job_runs, so it is a final.
- Typed over a formula: hours in run 103 is typed as 9. There is no Keys row (Keys is empty), so no Keys row names job_runs. The value is matched on every typed column of its row: run_id 103, job_id 3, duration_mins 30, dt 2026-09-24.
- Marks: none.
- Refusals: `sample`, a formula =RAND() in every row. RAND is refused, as Hive has no value to give for it, so the column is NULL AS sample.
- Left alone: `Parameters` and `Keys`, both empty; never a source, step or final.
- To fill in: `<database>`.

**2. Hive**

### Final job_runs

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24'
    THEN 9 ELSE duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

**3. Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X11

### Map

- Sources: job_runs, its typed columns run_id and duration_mins, read from `<database>.job_runs`.
- Steps: none.
- Finals: job_runs (run_id, duration_mins, pick, scaled).
- Typed over a formula: none; the Keys Table is empty.
- Marks: none.
- Refusals:
  - pick, `=INDIRECT("B"&ROW())`: INDIRECT and ROW() hang on the order of the sheet's rows, so `NULL AS pick`.
  - scaled, `=job_runs[[#This Row],[duration_mins]]*Summary!$C$2`: C2 on Summary is a cell outside a Table and not a defined name, so `NULL AS scaled`.
- Left alone: the bar chart on Summary; the Parameters and Keys Tables, which are empty and read nothing.
- To fill in: `<database>`.

### Hive

```sql
SELECT run_id, duration_mins, NULL AS pick, NULL AS scaled
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X12

### Map

- Sources: job_runs, its typed columns run_id and duration_mins, read from `<database>.job_runs`.
- Steps: none.
- Finals: job_runs (run_id, duration_mins, running, loop, with_tax).
- Typed over a formula: none; the Keys Table is empty.
- Marks:
  - with_tax reads the defined name tax_rate, which is Summary!$B$3, a cell outside a Table. It is written as its value, 0.2: `duration_mins * 0.2`. Move tax_rate into Parameters (name tax_rate, value 0.2).
- Refusals:
  - running, `=SUM(OFFSET(...,ROW()-1,1))`: OFFSET and ROW() hang on the order of the sheet's rows, so `NULL AS running`.
  - loop, `=job_runs[[#This Row],[loop]]+1`: it reads its own column, which is circular, so `NULL AS loop`.
- Left alone: the Parameters and Keys Tables, which are empty and read nothing. Summary B3 is read only as the value written for tax_rate above.
- To fill in: `<database>`.

### Hive

```sql
SELECT run_id, duration_mins, NULL AS running, NULL AS loop, duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X13

### Map

- Sources:
  - jobs, its typed columns job_id, job_name, team and region, read from `<database>.jobs`. It is a source only.
  - job_runs, its typed columns run_id and job_id, read from `<database>.job_runs`.
- Steps: none.
- Finals: job_runs (run_id, job_id, name, doubled).
- Typed over a formula: none; the Keys Table is empty.
- Marks:
  - name, `=VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)`: VLOOKUP with TRUE is approximate, so it is written as the exact match, a LEFT JOIN of jobs on job_id, taking job_name (column 2).
- Refusals:
  - doubled, `=DOUBLE(job_runs[[#This Row],[job_id]])`: DOUBLE is a defined name holding a LAMBDA (`_xlfn.LAMBDA(x,x*2)`), so `NULL AS doubled`.
- Left alone: the Parameters and Keys Tables, which are empty and read nothing.
- To fill in: `<database>`.

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

- Sources: job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read from `<database>.job_runs` inside the step below.
- Steps: job_runs, which holds the formula column hours. by_job's formula reads job_runs[hours], so job_runs is a step, a CTE inside by_job's block.
- Finals: by_job (job_id, total_hours), a summary. Its typed job_ids 1, 2 and 3 are typed in as its groups, and job_runs is read as a GROUP BY. It has no Total Row.
- Typed over a formula: none; the Keys Table is empty.
- Marks: none.
- Refusals: none.
- Left alone: the PivotTable on sheet Pivot, from job_runs, as PivotTables are left alone; the Parameters and Keys Tables, which are empty and read nothing.
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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X15

### Map

- Sources: tblRuns, its typed columns Run ID, Job ID and Duration (mins), read from `<database>.tblRuns`.
- Steps: none.
- Finals: tblRuns (Run ID, Job ID, Duration (mins), Hours).
- Typed over a formula: none; the Keys Table is empty.
- Marks: none.
- Refusals: none.
- Left alone: the Parameters and Keys Tables, which are empty and read nothing.
- To fill in: `<database>`, and the headers in snake case in brackets: `<run_id>` for Run ID, `<job_id>` for Job ID, `<duration_mins>` for Duration (mins).

### Hive

```sql
SELECT <run_id>, <job_id>, <duration_mins>, <duration_mins> / 60 AS hours
FROM <database>.tblRuns
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X16

### Map

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), its typed columns, read from `<database>.job_runs`, not the sample's rows. No query loads it, so it is a source.
- Steps: none.
- Finals: long_runs (run_id, job_id, minutes, hours), the Table loaded by Power Query long_runs. No other Table's formula reads it, so it is a final, its rows the query's.
- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables that no formula reads, so neither is a source, step or final. The Steps sheet's text (cells outside a Table).
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

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), its typed columns, read from `<database>.job_runs`, not the sample's rows. No query loads it, so it is a source.
- Steps: ok_runs, the connection-only query that ok_by_job's M names. It keeps job_runs' SUCCESS rows and becomes a CTE in ok_by_job's final.
- Finals: ok_by_job (job_id, runs, total_mins), the Table loaded by Power Query ok_by_job. No other Table's formula reads it, so it is a final, its rows the query's.
- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables that no formula reads, so neither is a source, step or final. The Steps sheet's text (cells outside a Table).
- To fill in: `<database>`.

### Hive

```sql
WITH ok_runs AS (
  SELECT job_id, duration_mins FROM <database>.job_runs WHERE status = 'SUCCESS'
)
SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X18

### Map

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), its typed columns, read from `<database>.job_runs`, not the sample's rows. jobs (job_id, job_name, team, region), its typed columns, read from `<database>.jobs`. No query loads either Table, so both are sources.
- Steps: none.
- Finals: top_runs (run_id, job_name, duration_mins), the Table loaded by Power Query top_runs. No other Table's formula reads it, so it is a final, its rows the query's: a LEFT JOIN of job_runs to jobs, sorted by duration_mins descending, the top 3.
- Typed over a formula: none.
- Marks: runs 97 and 103 both have 30 minutes, so their order within the top 3 may come out the other way from the sample, as Hive does not keep a tie's order. The set of three rows is the same.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables that no formula reads, so neither is a source, step or final. The Steps sheet's text (cells outside a Table).
- To fill in: `<database>`.

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

- Sources: scheduler_runs (run_id, job_id, dt), its typed columns, read from `<database>.scheduler_runs`, not the sample's rows. No query loads it as a Table of its own, so it is a source.
- Steps: none.
- Finals: all_runs (run_id, job_id, dt), the Table loaded by Power Query all_runs. No other Table's formula reads it, so it is a final, its rows the query's: scheduler_runs stacked on the job_runs rows, with UNION ALL.
- Typed over a formula: none.
- Marks: all_runs reads job_runs from `Sql.Database("dwh01", "ops")`, a source outside the workbook. Its job_runs table is read as `<database>.job_runs`, for you to check it is the table you mean.
- Refusals: Power Query holidays is left out. It reads a web address through Web.Contents, a web source, which is refused. It loads nothing and nothing reads it.
- Left alone: Parameters and Keys, both empty settings Tables that no formula reads, so neither is a source, step or final. The Steps sheet's text (cells outside a Table).
- To fill in: `<database>`.

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

- Sources: run_alerts (alert_id, run_id, severity, dt), its typed columns, read from `<database>.run_alerts`, not the sample's rows. No query loads it as a Table of its own, so it is a source.
- Steps: none.
- Finals: alert_pivot (run_id, high, low), the Table loaded by Power Query alert_pivot. No other Table's formula reads it, so it is a final, its rows the query's: the alerts of runs 97 and 101, pivoted by severity with a count.
- Typed over a formula: none.
- Marks: Table.Pivot. The columns high and low are fixed as the severities in the sample, so a new severity needs a column of its own. A run with no alert of a severity gives NULL there, as M does.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables that no formula reads, so neither is a source, step or final. The Steps sheet's text (cells outside a Table).
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

**Map**

- **Sources:** `job_runs` (its typed columns: run_id, job_id, status, duration_mins).
- **Steps:** none.
- **Finals:** `job_runs` (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). It holds formula columns and nothing else reads it, so it is a final, not a step.
- **Values typed over a formula:** none.
- **Marks:** none. The blank status on run 98 sits inside shortest_ok's condition, so it is written as it is.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the D1 notes on the Parameters and Keys sheets (cells outside a Table).
- **Parameters and Keys:** empty settings that no formula reads, so neither is a source, step or final.
- **To fill in:** `<database>`.

### Hive

```sql
-- final: job_runs
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

- **Sources:** `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (its typed columns: job_id, job_name).
- **Steps:** none.
- **Finals:** `jobs` (job_id, job_name, runs, avg_mins, id_order). Its formula columns read job_runs and its own columns, and nothing else reads jobs, so it is a final. Its typed columns are read from `<database>.jobs`.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the D1 notes on the Parameters and Keys sheets (cells outside a Table).
- **Parameters and Keys:** empty settings that no formula reads, so neither is a source, step or final.
- **To fill in:** `<database>`.

### Hive

```sql
-- final: jobs
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

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X43

**Map**

- **Sources:** `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (its typed columns: job_id, job_name, team, region).
- **Steps:** none.
- **Finals:**
  - `busy_teams` (team, runs, shortest, avg_mins): the Table loaded by query busy_teams, its rows the query's.
  - `statuses` (job_id, status): the Table loaded by query statuses, its rows the query's.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the D1 notes on the Parameters and Keys sheets (cells outside a Table).
- **Parameters and Keys:** empty settings, so neither is a source, step or final.
- **To fill in:** `<database>`.

### Hive

```sql
-- final: busy_teams
SELECT j.team, COUNT(*) AS runs, MIN(r.duration_mins) AS shortest, AVG(r.duration_mins) AS avg_mins
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.team
HAVING COUNT(*) > 4
```

```sql
-- final: statuses
SELECT DISTINCT job_id, status FROM <database>.job_runs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X44

**Map**

- **Sources:** `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (its typed columns: job_id, job_name, team, region); `scheduler_runs` (its typed columns: run_id, job_id, dt).
- **Steps:** none.
- **Finals:**
  - `jobs_with_runs` (run_id, job_name): the Table loaded by query jobs_with_runs, its rows the query's.
  - `never_scheduled` (job_id, job_name, team): the Table loaded by query never_scheduled, its rows the query's.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the D1 notes on the Parameters and Keys sheets (cells outside a Table).
- **Parameters and Keys:** empty settings, so neither is a source, step or final.
- **To fill in:** `<database>`.

### Hive

```sql
-- final: jobs_with_runs
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON j.job_id = r.job_id
```

```sql
-- final: never_scheduled
SELECT j.job_id, j.job_name, j.team
FROM <database>.jobs j
LEFT JOIN <database>.scheduler_runs s ON j.job_id = s.job_id
WHERE s.job_id IS NULL
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X45

**Map**

- **Sources:** `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt); `scheduler_runs` (its typed columns: run_id, job_id, dt).
- **Steps:** none.
- **Finals:**
  - `run_days` (run_id, dt): the Table loaded by query run_days, its rows the query's.
  - `matched` (run_id, job_id, dt, status): the Table loaded by query matched, its rows the query's.
- **Values typed over a formula:** none.
- **Marks:** none. The matched query's full outer join gives NULL for run_id, job_id and dt on a row only job_runs has (run 99), as the sample's first row shows.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the D1 notes on the Parameters and Keys sheets (cells outside a Table).
- **Parameters and Keys:** empty settings, so neither is a source, step or final.
- **To fill in:** `<database>`.

### Hive

```sql
-- final: run_days
SELECT run_id, dt FROM <database>.job_runs
UNION
SELECT run_id, dt FROM <database>.scheduler_runs
```

```sql
-- final: matched
SELECT s.run_id, s.job_id, s.dt, r.status
FROM <database>.scheduler_runs s
FULL OUTER JOIN <database>.job_runs r ON s.run_id = r.run_id
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X51

### Map
- **Sources:** job_runs (its typed columns: run_id, job_id, status, duration_mins, dt).
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins). It has formula columns, no query loads it, and nothing else reads it, so it is a final.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty, so no fixed value is read and no Keys row is needed. Blank status of run 98 is read as it is: not_ok counts it, as Excel's "<>SUCCESS" does, and failed_in_job does not match it.
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
- **Sources:** job_runs (its typed columns: run_id, job_id, duration_mins).
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job); job_runs (Total Row) (duration_mins, share). The Total Row's label "Total" and its empty cells get no column.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty.
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
- **Sources:** job_runs (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt). Read as it is; no final reads status or avg_retry_secs, so the blanks of run 98 need no mark.
- **Steps:** none.
- **Finals:**
  - by_job (job_id, total_mins, runs, longest), a summary: its only typed column, job_id, is the one its SUMIFS and COUNTIFS match on, so its final is a GROUP BY of job_runs. Its typed job_ids (1, 2, 3) are typed in as the groups; job_runs is read.
  - by_job (Total Row) (total_mins, runs, longest). The "Total" label gets no column; SUBTOTAL(104) is a MAX.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT j.job_id, COALESCE(s.total_mins, 0) AS total_mins, COALESCE(s.runs, 0) AS runs, COALESCE(s.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total_mins, COUNT(*) AS runs, MAX(duration_mins) AS longest FROM <database>.job_runs GROUP BY job_id) s
  ON j.job_id = s.job_id
```

```sql
WITH by_job AS (
  SELECT j.job_id, COALESCE(s.total_mins, 0) AS total_mins, COALESCE(s.runs, 0) AS runs, COALESCE(s.longest, 0) AS longest
  FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total_mins, COUNT(*) AS runs, MAX(duration_mins) AS longest FROM <database>.job_runs GROUP BY job_id) s
    ON j.job_id = s.job_id
)
SELECT SUM(total_mins) AS total_mins, SUM(runs) AS runs, MAX(longest) AS longest
FROM by_job
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X54

### Map
- **Sources:** job_runs (its typed columns: run_id, dt).
- **Steps:** none.
- **Finals:** job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label). It has formula columns, no query loads it, and nothing else reads it, so it is a final.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** a_month_on: EDATE is written as ADD_MONTHS, marked, as a month's end stays one.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty.
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
- **Sources:** jobs (its typed columns: job_id, job_name, team, region).
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens). It has formula columns, no query loads it, and nothing else reads it, so it is a final. It has no Total Row.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty.
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

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs); `scheduler_runs` (run_id, job_id, dt), read by scheduled_on's lookup.
- **Steps:** none.
- **Finals:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on). It has formula columns, no query loads it, and no other Table reads it.
- **Values typed over a formula:** none. Keys needs no row.
- **Marks:** `weighted` (SUMPRODUCT) reads avg_retry_secs, which is blank in run 98, so it reads COALESCE(avg_retry_secs, 0): blank.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty (no formula reads Parameters, and no value is typed over a formula); the Steps sheet's text, which is cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT jr.run_id, jr.job_id, jr.status, jr.duration_mins, jr.avg_retry_secs,
  jr.status IS NULL AS no_status,
  FLOOR(jr.duration_mins / 7) AS weeks,
  GREATEST(jr.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(jr.duration_mins) OVER () AS spread,
  SUM(jr.duration_mins * COALESCE(jr.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(s.dt, 'unscheduled') AS scheduled_on
FROM <database>.job_runs jr
LEFT JOIN <database>.scheduler_runs s ON jr.run_id = s.run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X57

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (job_id, job_name, team, region).
- **Steps:** none.
- **Finals:** `picked` (run_id, job_id, status, avg_retry_secs, status_lc), the rows of query `picked`, which loads it. `ran_jobs` (job_id, job_name, team, region), the rows of query `ran_jobs`, which loads it.
- **Values typed over a formula:** none. Keys needs no row.
- **Marks:** none. Query `picked` fills avg_retry_secs's blank with 0 as its Table.ReplaceValue says, written COALESCE(avg_retry_secs, 0). status_lc keeps run 98's blank as NULL, as M's Text.Lower does.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty; the Steps sheet's text, which is cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, job_id, status, COALESCE(avg_retry_secs, 0) AS avg_retry_secs, LOWER(status) AS status_lc
FROM <database>.job_runs
WHERE job_id IN (1, 2) AND (status IS NULL OR status LIKE 'S%')
```

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r ON j.job_id = r.job_id
WHERE j.job_name LIKE '%a%'
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X58

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (job_id, job_name, team, region); `scheduler_runs` (run_id, job_id, dt); `region_budgets` (job_id, budget_cents, region).
- **Steps:** none. Query `job_regions` has a Regions step of its own, a CTE `regions` inside that final.
- **Finals:**
  - `job_regions` (job_id, region), the rows of query `job_regions`, which loads it.
  - `numbered` (run_id, dt, duration_mins, n), the rows of query `numbered`, which loads it.
  - `days_per_job` (job_id, days), the rows of query `days_per_job`, which loads it.
  - `unrun` (run_id, job_id), the rows of query `unrun`, which loads it.
  - `measures` (run_id, measure, amount), the rows of query `measures`, which loads it.
- **Values typed over a formula:** none. There are no formulas in this workbook. Keys needs no row.
- **Marks:**
  - `measures` drops run 98's blank avg_retry_secs, as M's unpivot does, so run 98 has no avg_retry_secs row.
  - `days_per_job`'s sort is dropped, as no FirstN or index follows it, so its row order is not kept.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty; the Steps sheet's text, which is cells outside a Table.
- **To fill in:** `<database>`.

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

- **Sources:** `jobs` (job_id, job_name, team, region); `run_alerts` (alert_id, run_id, severity, dt); `job_runs` (run_id, job_id, duration_mins, dt), its typed columns.
- **Steps:** `job_runs`, a Table whose formula columns (team, alerts, running_mins) are read by `by_team` and query `noisy_runs`. It is a CTE `job_runs` in each final that reads it.
- **Finals:**
  - `by_team` (team, total_mins, alerted_runs), a summary: its only typed column, team, is what its SUMIFS and COUNTIFS match on, so its typed groups data and finance are typed in and its totals are a GROUP BY of `job_runs`.
  - `by_team (Total Row)` (total_mins, alerted_runs). The Total cell under team is a label, so it has no column.
  - `noisy_runs` (run_id, team, alerts, running_mins), the rows of query `noisy_runs`, which reads `job_runs`.
- **Values typed over a formula:** none. Keys needs no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty; the Steps sheet's text, which is cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt, j.team,
    COALESCE(a.n_alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS n_alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
)
SELECT t.team, COALESCE(s.total_mins, 0) AS total_mins, COALESCE(c.alerted_runs, 0) AS alerted_runs
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance') t
LEFT JOIN (SELECT team, SUM(duration_mins) AS total_mins FROM job_runs GROUP BY team) s
  ON t.team = s.team
LEFT JOIN (SELECT team, COUNT(*) AS alerted_runs FROM job_runs WHERE alerts > 0 GROUP BY team) c
  ON t.team = c.team
```

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt, j.team,
    COALESCE(a.n_alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS n_alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
), by_team AS (
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
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt, j.team,
    COALESCE(a.n_alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS n_alerts FROM <database>.run_alerts GROUP BY run_id) a
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
- **Steps:** `base`, query base (connection only, but read by two queries, so it is a step and not left out), with columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name, region. It is a CTE `base` in each final that reads it.
- **Finals:**
  - `by_region` (region, total_mins, runs, share), the rows of query `by_region`, which loads it. Its share is total_mins over SUM(total_mins) of its own rows.
  - `by_region (Total Row)` (total_mins). Its runs and share cells are empty, and the Total cell under region is a label, so only total_mins gets a column.
  - `top_runs` (run_id, job_name, region), the rows of query `top_runs`, which loads it.
- **Values typed over a formula:** none. Keys needs no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty; the Steps sheet's text, which is cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT region, total_mins, runs, total_mins / SUM(total_mins) OVER () AS share
FROM (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) g
```

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
), by_region AS (
  SELECT region, total_mins, runs, total_mins / SUM(total_mins) OVER () AS share
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
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
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

**Sources**
- `<database>.job_runs`: typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. Only typed columns, and no query loads it.

**Steps**
- Query `ok_runs` (run_id, job_id, duration_mins): the M of query `ok_by_job` names it (`Table.Group(ok_runs, ...)`), so it is a CTE in the final that reads it. It is not the Table `ok_runs`.

**Finals**
- Table `ok_runs` (run_id, job_id, duration_mins, hours): loaded by query `ok_runs`, so its rows are that query's. No other Table's formula reads it. `hours` is `duration_mins / 60`.
- Table `ok_by_job` (job_id, total_mins): loaded by query `ok_by_job`, so its rows are that query's. No formula reads it. Its rows are the sum of duration_mins per job_id, over the step `ok_runs`.

**Settings, never a source, step or final**
- Parameters: empty, so no value is read.
- Keys: empty, and no value is typed over a formula, so no Keys row is needed.

**Typed over a formula**: none.

**Marks**: none.

**Refusals**: none.

**Left alone**: the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table.

**To fill in**: `<database>`, the database that holds `job_runs`.

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
- `<database>.job_runs`: typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt.
- `<database>.jobs`: typed columns job_id, job_name, team. These are read by the step `jobs` below.

**Steps**
- Table `jobs` (job_id, job_name, team, runs, total): its formula columns are read by Table `by_team`'s formula and by query `busy_jobs` (through `Excel.CurrentWorkbook` "jobs"), so it is a step, a CTE in each final that reads it.
  - `runs` is `COUNTIF(job_runs[job_id], ...)`: over another Table, a LEFT JOIN to the count of job_runs per job_id, with COALESCE(.., 0).
  - `total` is `SUMIF(job_runs[job_id], ..., job_runs[duration_mins])`: a LEFT JOIN to the sum of duration_mins per job_id, with COALESCE(.., 0).

**Finals**
- Table `by_team` (team, team_total): no other Table's formula or query reads it, and its only typed column, team, is the one its SUMIFS matches on, so it is a summary. Its groups `data`, `finance` and `web` are typed in, and its final is a GROUP BY of the step `jobs`. `team_total` is SUMIFS(jobs[total], jobs[team], team), with COALESCE(.., 0).
- Table `busy_jobs` (job_id, job_name, runs): loaded by query `busy_jobs`, so its rows are that query's: the rows of `jobs` with runs >= 3, reading the step `jobs`.

**Settings, never a source, step or final**
- Parameters: empty, so no value is read.
- Keys: empty, and no value is typed over a formula, so no Keys row is needed.

**Typed over a formula**: none.

**Marks**: none.

**Refusals**: none.

**Left alone**: the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table.

**To fill in**: `<database>`, the database that holds `job_runs` and `jobs`.

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
SELECT job_id, job_name, runs FROM jobs WHERE runs >= 3
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X75

### Map

**Sources**
- `<database>.job_runs`: typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. Only typed columns, and no query loads it.

**Steps**
- Query `long_runs` (run_id, dt, duration_mins): the M of query `long_per_day` names it (`Table.Group(long_runs, ...)`), so it is a CTE in the final that reads it. It is not the Table `long_runs`.

**Finals**
- Table `long_runs` (run_id, dt, duration_mins, over): loaded by query `long_runs`, so its rows are that query's. No other Table's formula reads it. `over` is `duration_mins - 15`.
- Table `long_per_day` (dt, runs): loaded by query `long_per_day`, so its rows are that query's. `runs` is the count of the step `long_runs` per dt.
- Note: `over` is a SQL keyword. It is kept as its header, as file 11 keeps a plain name as it is. If Hive refuses it, quote it in backticks.

**Settings, never a source, step or final**
- Parameters: empty, so no value is read.
- Keys: empty, and no value is typed over a formula, so no Keys row is needed.

**Typed over a formula**: none.

**Marks**: none.

**Refusals**: none.

**Left alone**: the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table.

**To fill in**: `<database>`, the database that holds `job_runs`.

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

**Sources**
- `<database>.jobs`: typed columns job_id, job_name, team, region. Only typed columns, and no query loads it.
- `<database>.job_runs`: typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. Only typed columns, and no query loads it.

**Steps**
- Query `finance_jobs` (job_id, job_name): the M of query `finance_runs` names it (`Table.NestedJoin(..., finance_jobs, ...)`), so it is a CTE in the final that reads it. It is not the Table `finance_jobs`.

**Finals**
- Table `finance_jobs` (job_id, job_name, label): loaded by query `finance_jobs`, so its rows are that query's. No other Table's formula reads it. `label` is `UPPER(job_name)`.
- Table `finance_runs` (run_id, job_name, duration_mins): loaded by query `finance_runs`, so its rows are that query's: job_runs inner-joined to the step `finance_jobs`, with job_name from it.

**Settings, never a source, step or final**
- Parameters: empty, so no value is read.
- Keys: empty, and no value is typed over a formula, so no Keys row is needed.

**Typed over a formula**: none.

**Marks**: none.

**Refusals**: none.

**Left alone**: the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table.

**To fill in**: `<database>`, the database that holds `jobs` and `job_runs`.

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

