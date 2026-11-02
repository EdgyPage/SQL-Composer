date: 2026-11-01
arm: C
model: haiku
files: 21-dev

## X01

### Map
- Sources: job_runs (its typed columns: run_id, job_id, duration_mins, dt).
- Steps: none. No query loads anything, and no formula reads another Table.
- Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours). It has a formula column, and nothing else reads it, so it is a final.
- Settings, not pieces: Parameters and Keys, both empty. Neither is a source, step or final. No formula reads Parameters, and no value is typed over a formula, so Keys has no row.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>` in the job_runs final's FROM.

### Hive
```sql
SELECT run_id, job_id, duration_mins, dt, duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X02

### Map
- Sources: job_runs (its typed columns: run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag). It has formula columns, and nothing else reads it, so it is a final.
- Settings, not pieces: Parameters and Keys, both empty. Neither is a source, step or final. Keys has no row, as no value is typed over a formula.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>` in the job_runs final's FROM.

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
- Sources: job_runs (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs). It has formula columns, and nothing else reads it, so it is a final.
- Settings, not pieces: Parameters and Keys, both empty. Neither is a source, step or final. Keys has no row, as no value is typed over a formula.
- Values typed over a formula: none.
- Marks:
  - blank: status is blank in the sample (run 98), and score reads it, so score reads COALESCE(status, '').
  - blank: avg_retry_secs is blank in the sample (run 98), and mins_per_retry and total_secs read it, so both read COALESCE(avg_retry_secs, 0).
- Refusals: none.
- Left alone: none.
- To fill in: `<database>` in the job_runs final's FROM.

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
- Sources: jobs (its typed columns: job_id, job_name, team, region).
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd). It has formula columns, and nothing else reads it, so it is a final.
- Settings, not pieces: Parameters and Keys, both empty. Neither is a source, step or final. Keys has no row, as no value is typed over a formula.
- Values typed over a formula: none.
- Marks: none. The columns the formulas read have no blanks in the sample.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>` in the jobs final's FROM.

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
- Sources: job_runs (its typed columns: run_id, dt); region_costs (its typed columns: job_id, cost_cents, region, dt).
- Steps: none. No query loads anything, and no formula reads another Table.
- Finals:
  - job_runs (run_id, dt, month, days_since). It has formula columns, and nothing else reads it, so it is a final.
  - region_costs (job_id, cost_cents, region, dt, day). It has a formula column, and nothing else reads it, so it is a final.
- Settings, not pieces: Parameters and Keys, both empty. Neither is a source, step or final. Keys has no row, as no value is typed over a formula.
- Values typed over a formula: none.
- Marks:
  - region_costs dt is held as text (20260911), so day builds 'yyyy-mm-dd' text from its digits, not a date type. The typed dt column is kept as it is.
  - None for job_runs dt, which is a date (2026-09-23) and is read by MONTH and DATEDIFF as it is.
  - None for the blank cost_cents in region_costs row 29, as no formula reads it.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>` in each final's FROM.

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
- Sources: `jobs` (job_id, job_name, team, region), read as `<database>.jobs`; `job_runs` (its typed columns run_id, job_id, duration_mins), read as `<database>.job_runs`.
- Steps: none.
- Finals: `job_runs` (run_id, job_id, duration_mins, job_name, runs_of_job). No query loads it and no other Table's formula reads it, so it is a final. Its formulas: job_name is XLOOKUP on jobs, written as a LEFT JOIN to jobs on job_id; runs_of_job is COUNTIFS over its own Table, written as COUNT(*) OVER (PARTITION BY job_id), with COALESCE.
- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: `Parameters` and `Keys`, the two settings Tables, both empty here and never a source, step or final; the D1 notes on the Parameters and Keys sheets and the Steps sheet, which are cells outside a Table.
- To fill in: `<database>`, in each read of the final.

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
- Sources: `job_runs` (its typed columns run_id, job_id, status), read as `<database>.job_runs`; `jobs` (job_id, job_name, team, region), read as `<database>.jobs`.
- Steps: none.
- Finals: `job_runs` (run_id, job_id, status, team, region). Its formulas: team is VLOOKUP on jobs' column 3 (team), exact; region is INDEX and MATCH on jobs' region, exact. Both are written as one LEFT JOIN to jobs on job_id.
- Typed over a formula: none.
- Marks: none. The blank status in row 98 is read by no formula, so it is written as it is, with no COALESCE.
- Refusals: none.
- Left alone: `Parameters` and `Keys`, the two settings Tables, both empty here and never a source, step or final; the D1 notes on the Parameters and Keys sheets and the Steps sheet, which are cells outside a Table.
- To fill in: `<database>`, in each read of the final.

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
- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), all typed, read as `<database>.job_runs`.
- Steps: none.
- Finals: `by_job` (job_id, total_mins, avg_retry, longest), a summary. Its only typed column, job_id, is the one its SUMIFS, AVERAGEIFS and MAXIFS match on, so its final is a GROUP BY of job_runs, and its typed job_ids 1, 2 and 3 are its groups, typed in. total_mins is SUMIFS over another Table, a LEFT JOIN to the grouped rows, with COALESCE; avg_retry is AVERAGEIFS, AVG left NULL; longest is MAXIFS, MAX with COALESCE.
- Typed over a formula: none.
- Marks: none. The blank avg_retry_secs in row 98 sits inside AVERAGEIFS, which skips a blank as AVG skips NULL, so it is written as it is.
- Refusals: none.
- Left alone: `Parameters` and `Keys`, the two settings Tables, both empty here and never a source, step or final; the D1 notes on the Parameters and Keys sheets and the Steps sheet. by_job has no Total Row.
- To fill in: `<database>`.

### Hive

```sql
SELECT j.job_id,
  COALESCE(s.total_mins, 0) AS total_mins,
  s.avg_retry,
  COALESCE(s.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total_mins,
    AVG(avg_retry_secs) AS avg_retry, MAX(duration_mins) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
) s ON j.job_id = s.job_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X09

### Map
- Sources: `jobs` (job_id, job_name, team, region), read as `<database>.jobs`; `job_runs` (its typed columns run_id, job_id, duration_mins, avg_retry_secs), read as `<database>.job_runs`.
- Steps: none.
- Finals: `job_runs` (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost). Its formulas: team is XLOOKUP on jobs, written as a LEFT JOIN to jobs on job_id, then jobs' team; team_mins is SUMIFS over its own Table on team, written as a window over the joined team, with COALESCE; cost is (duration_mins * 60 + avg_retry_secs) * rate.
- Parameters: `rate` is 0.5, typed into cost where it reads XLOOKUP("rate", Parameters[name], Parameters[value]). Parameters is never a source, step or final.
- Typed over a formula: cost at run_id 97 is 100, matched on the Keys row for job_runs, whose key column is run_id: `CASE WHEN run_id = 97 THEN 100 ELSE ... END`.
- Marks: blank. avg_retry_secs at run_id 98 is blank and cost reads it, so cost reads COALESCE(avg_retry_secs, 0) in its place.
- Refusals: none.
- Left alone: `Keys`, a settings Table, read only to match the typed value; the D1 notes on the Parameters and Keys sheets and the Steps sheet.
- To fill in: `<database>`, in each read of the final.

### Hive

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

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X10

### Map
- Sources: `job_runs` (its typed columns run_id, job_id, duration_mins, dt), read as `<database>.job_runs`.
- Steps: none.
- Finals: `job_runs` (run_id, job_id, duration_mins, dt, hours, sample). No query loads it and no other Table reads it, so it is a final. hours is duration_mins / 60; sample is refused.
- Typed over a formula: hours at run_id 103 is 9. The Keys sheet has no row for job_runs, so there is no Keys row, and the typed value is matched on every typed column of its row: run_id 103, job_id 3, duration_mins 30, dt 2026-09-24.
- Marks: none.
- Refusals: sample, `=RAND()`, is `NULL AS sample`. RAND is refused, as random values have no Hive form that gives the sample again.
- Left alone: `Parameters`, empty and read by no formula, and `Keys`, empty, both settings Tables and never a source, step or final; the D1 notes on the Parameters and Keys sheets and the Steps sheet.
- To fill in: `<database>`.

### Hive

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24'
    THEN 9 ELSE duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X11

### Map

- Sources: `<database>.job_runs`, its typed columns run_id and duration_mins.
- Steps: none.
- Finals: Table job_runs (run_id, duration_mins, pick, scaled). No query loads it and no other piece reads it, so it is a final.
- Typed over a formula: none. Every row of pick and scaled holds its formula, so Keys needs no row.
- Marks: none.
- Refusals:
  - pick, `=INDIRECT("B"&ROW())`: INDIRECT, and ROW(), which hangs on the order of the sheet's rows. Written as NULL AS pick.
  - scaled, `=job_runs[[#This Row],[duration_mins]]*Summary!$C$2`: reads Summary!C2, a cell outside a Table that isn't a defined name. Written as NULL AS scaled.
- Left alone: the bar chart on Summary; cells outside a Table (Summary C2, and the notes in column D of Parameters, Keys and Steps).
- Not pieces: Parameters and Keys. Both are empty, and no formula reads Parameters.
- To fill in: `<database>`.

### Hive

```sql
SELECT run_id, duration_mins,
  NULL AS pick,
  NULL AS scaled
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X12

### Map

- Sources: `<database>.job_runs`, its typed columns run_id and duration_mins.
- Steps: none.
- Finals: Table job_runs (run_id, duration_mins, running, loop, with_tax). No query loads it and no other piece reads it, so it is a final.
- Typed over a formula: none. Keys is empty.
- Marks:
  - with_tax reads the defined name tax_rate, which is Summary!B3. It is written as its value, 0.2. Move tax_rate into Parameters (name tax_rate, value 0.2) and read it there with XLOOKUP("tax_rate", Parameters[name], Parameters[value]).
- Refusals:
  - running, `=SUM(OFFSET(...))`: OFFSET, and ROW(), which hangs on the order of the sheet's rows. Written as NULL AS running.
  - loop, `=job_runs[[#This Row],[loop]]+1`: reads its own column, which is circular. Written as NULL AS loop.
- Left alone: Summary B3, a cell outside a Table, read only through tax_rate; cells outside a Table (the notes in column D of Parameters, Keys and Steps).
- Not pieces: Parameters and Keys. Both are empty.
- To fill in: `<database>`.

### Hive

```sql
SELECT run_id, duration_mins,
  NULL AS running,
  NULL AS loop,
  duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X13

### Map

- Sources:
  - `<database>.job_runs`, its typed columns run_id and job_id.
  - `<database>.jobs`, its typed columns job_id, job_name, team and region. jobs has no formula and no query loads it, so it is a source only.
- Steps: none.
- Finals: Table job_runs (run_id, job_id, name, doubled). No query loads it and no other piece reads it, so it is a final.
- Typed over a formula: none. Keys is empty.
- Marks:
  - name, `=VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)`: TRUE makes the match approximate. It is written as the exact match (FALSE) on jobs' job_id, reading job_name.
- Refusals:
  - doubled, `=DOUBLE(job_runs[[#This Row],[job_id]])`: DOUBLE is a defined name holding a LAMBDA. Written as NULL AS doubled.
- Left alone: cells outside a Table (the notes in column D of Parameters, Keys and Steps).
- Not pieces: Parameters and Keys. Both are empty.
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

- Sources: `<database>.job_runs`, read in full with its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt. The sample rows are not typed in.
- Steps:
  - Table job_runs, a step because by_job's SUMIFS reads its formula column hours. It is a CTE in by_job's block, with hours written as `duration_mins / 60`.
- Finals:
  - Table by_job (job_id, total_hours). It is a summary: its only typed column, job_id, is the one its SUMIFS matches on. Its typed groups are typed in: job_id 1, 2 and 3. Its SUMIFS reads another Table, so it is a LEFT JOIN on a GROUP BY, with COALESCE for a group with no match.
- Typed over a formula: none. Keys is empty.
- Marks:
  - The summary's groups 1, 2 and 3 are typed in from by_job's sample rows. A job_id in job_runs that is not among them gets no row.
- Refusals: none.
- Left alone:
  - the PivotTable on sheet Pivot, built from job_runs. It is not converted.
  - cells outside a Table (the notes in column D of Parameters and Keys).
- Blanks: the blank status and avg_retry_secs in row 98 are not read by any formula, so no blank mark.
- Not pieces: Parameters and Keys. Both are empty.
- To fill in: `<database>`.

### Hive

```sql
WITH job_runs AS (
  SELECT job_id, duration_mins / 60 AS hours
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

- Sources: `<database>.tblRuns`, its typed columns Run ID, Job ID and Duration (mins), read in full.
- Steps: none.
- Finals: Table tblRuns (Run ID, Job ID, Duration (mins), Hours). It has a formula column, no query loads it, and nothing else reads it, so it is a final.
- Typed over a formula: none. Keys is empty.
- Marks: none.
- Names: the headers Run ID, Job ID and Duration (mins) are not plain names, so they are written in snake case in brackets: `<run_id>`, `<job_id>`, `<duration_mins>`. Hours and the Table name tblRuns are plain names, so they stay as they are.
- Refusals: none.
- Left alone: cells outside a Table (the notes in column D of Parameters and Keys).
- Not pieces: Parameters and Keys. Both are empty.
- To fill in: `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`.

### Hive

```sql
SELECT <run_id>, <job_id>, <duration_mins>,
  <duration_mins> / 60 AS Hours
FROM <database>.tblRuns
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X16

### Map

**Sources:** job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read as `<database>.job_runs`.

**Steps:** none.

**Finals:** long_runs, the Excel Table long_runs (run_id, job_id, minutes, hours), loaded by Power Query long_runs. No formula reads that Table, so it is a final and its rows are the query's. The query long_runs is its query, not a step.

**Settings, never a source, step or final:** Parameters and Keys, both empty. No formula reads Parameters, and no value is typed over a formula.

**Values typed over a formula:** none. No Table here has a formula column.

**Marks:** none.

**Refusals:** none.

**Left alone:** none.

**To fill in:** `<database>`, in long_runs' FROM.

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

**Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.

**Steps:** ok_runs, the Power Query ok_runs (connection only), which reads job_runs and keeps `status = 'SUCCESS'`. Query ok_by_job reads it, so it is a CTE in ok_by_job's final, not a source.

**Finals:** ok_by_job, the Excel Table ok_by_job (job_id, runs, total_mins), loaded by Power Query ok_by_job. No formula reads that Table, so it is a final and its rows are the query's, grouped by job_id.

**Settings, never a source, step or final:** Parameters and Keys, both empty.

**Values typed over a formula:** none. No Table here has a formula column.

**Marks:** none.

**Refusals:** none.

**Left alone:** none.

**To fill in:** `<database>`, in ok_runs' FROM.

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

**Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`; and jobs (job_id, job_name, team, region), read as `<database>.jobs`. Neither is loaded or read by a formula, so each is a source.

**Steps:** none.

**Finals:** top_runs, the Excel Table top_runs (run_id, job_name, duration_mins), loaded by Power Query top_runs. No formula reads that Table, so it is a final and its rows are the query's: a left join of job_runs to jobs, sorted by duration_mins descending, the first 3 rows kept.

**Settings, never a source, step or final:** Parameters and Keys, both empty.

**Values typed over a formula:** none. No Table here has a formula column.

**Marks:** none.

**Refusals:** none.

**Left alone:** none.

**To fill in:** `<database>`, in both FROM and JOIN.

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

**Sources:** scheduler_runs (run_id, job_id, dt), its typed columns, read as `<database>.scheduler_runs`; and job_runs (run_id, job_id, dt), the table that Power Query all_runs names in `Sql.Database("dwh01", "ops")` as `Schema = "ops", Item = "job_runs"`, read as `<database>.job_runs`.

**Steps:** none.

**Finals:** all_runs, the Excel Table all_runs (run_id, job_id, dt), loaded by Power Query all_runs. No formula reads that Table, so it is a final and its rows are the query's: scheduler_runs stacked on job_runs with UNION ALL.

**Settings, never a source, step or final:** Parameters and Keys, both empty.

**Values typed over a formula:** none. No Table here has a formula column.

**Marks:** all_runs reads a source outside the workbook, the Sql.Database("dwh01", "ops") table job_runs. It is read as `<database>.job_runs`, for you to check that it is the table you mean.

**Refusals:** Power Query holidays reads a web source through Web.Contents, so it is refused. It is left out: nothing reads it, and it loads nothing.

**Left alone:** none.

**To fill in:** `<database>`, in both FROM clauses.

### Hive

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

**Sources:** run_alerts (alert_id, run_id, severity, dt), read as `<database>.run_alerts`.

**Steps:** none.

**Finals:** alert_pivot, the Excel Table alert_pivot (run_id, high, low), loaded by Power Query alert_pivot. No formula reads that Table, so it is a final and its rows are the query's: the alerts of runs 97 and 101, counted per severity by run_id.

**Settings, never a source, step or final:** Parameters and Keys, both empty.

**Values typed over a formula:** none. No Table here has a formula column.

**Marks:** Table.Pivot. The columns high and low are fixed as the severity values in the sample, and NULL where a run has none, as M leaves it. A severity that is new later gets no column.

**Refusals:** none.

**Left alone:** none.

**To fill in:** `<database>`, in the FROM.

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

**Sources**
- `job_runs`, its typed columns: run_id, job_id, status, duration_mins.

**Steps**
- None.

**Finals**
- Table `job_runs`: no query and no other Table reads it, and its formula columns read only its own rows, so it is a final. Columns: run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total.

**Each piece's role**
- Excel Table "job_runs": the final above, read from `<database>.job_runs`.
- Excel Table "Parameters": a settings Table, empty, never a source, step or final.
- Excel Table "Keys": a settings Table, empty, never a source, step or final. No value is typed over a formula, so it needs no row.

**Typed over a formula:** none.

**Marks:** none. The blank status on run 98 sits inside MINIFS's condition, so it is written as it is.

**Refusals:** none.

**Left alone:** the Parameters and Keys Tables; the Steps sheet and the D1 notes (cells outside a Table). No Total Rows or defined names.

**To fill in:** `<database>`, in the block below.

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
- `job_runs`, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt.
- `jobs`, its typed columns: job_id, job_name.

**Steps**
- None.

**Finals**
- Table `jobs`: its formulas read `job_runs`, and nothing reads `jobs`, so it is a final, not a step. Columns: job_id, job_name, runs, avg_mins, id_order.

**Each piece's role**
- Excel Table "job_runs": no formula and no query, so a source only, read from `<database>.job_runs`.
- Excel Table "jobs": the final above, its typed columns read from `<database>.jobs`.
- Excel Table "Parameters": a settings Table, empty, never a source, step or final.
- Excel Table "Keys": a settings Table, empty, never a source, step or final. No value is typed over a formula, so it needs no row.

**Typed over a formula:** none.

**Marks:** none.

**Refusals:** none.

**Left alone:** the Parameters and Keys Tables; the Steps sheet and the D1 notes (cells outside a Table). No Total Rows or defined names.

**To fill in:** `<database>`, in the block below.

### Hive

```sql
SELECT j.job_id, j.job_name,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(a.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
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

**Sources**
- `job_runs`, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt.
- `jobs`, its typed columns: job_id, job_name, team, region.

**Steps**
- None. Neither query names another query.

**Finals**, in the order of their blocks
- Table `busy_teams` (team, runs, shortest, avg_mins), loaded by Power Query "busy_teams", so its rows are that query's. The query reads `job_runs` and `jobs`, joins them inner, groups by team, and keeps teams with more than 4 runs. Its block is the final's query.
- Table `statuses` (job_id, status), loaded by Power Query "statuses", so its rows are that query's. The query reads `job_runs`, keeps job_id and status, and removes duplicates. Its block is the final's query.

**Each piece's role**
- Excel Table "job_runs": a source only (typed columns, no query loads it).
- Excel Table "jobs": a source only.
- Power Query "busy_teams": the query of final `busy_teams`.
- Power Query "statuses": the query of final `statuses`.
- Excel Table "Parameters": a settings Table, empty, never a source, step or final.
- Excel Table "Keys": a settings Table, empty, never a source, step or final.

**Typed over a formula:** none.

**Marks:** none.

**Refusals:** none.

**Left alone:** the Parameters and Keys Tables; the Steps sheet and the D1 notes (cells outside a Table). No Total Rows or defined names.

**To fill in:** `<database>`, in each block below.

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

**Sources**
- `job_runs`, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt.
- `jobs`, its typed columns: job_id, job_name, team, region.
- `scheduler_runs`, its typed columns: run_id, job_id, dt.

**Steps**
- None. Neither query names another query.

**Finals**, in the order of their blocks
- Table `jobs_with_runs` (run_id, job_name), loaded by Power Query "jobs_with_runs", so its rows are that query's. The query keeps every job (a right outer join, so jobs are the kept side), giving cache_warm a NULL run_id because it has no run.
- Table `never_scheduled` (job_id, job_name, team), loaded by Power Query "never_scheduled", so its rows are that query's. The query keeps the jobs with no scheduler run (a left anti join).

**Each piece's role**
- Excel Table "job_runs", "jobs", "scheduler_runs": sources only (typed columns, no query loads them).
- Power Query "jobs_with_runs": reads `job_runs` and `jobs`; the query of final `jobs_with_runs`.
- Power Query "never_scheduled": reads `jobs` and `scheduler_runs`; the query of final `never_scheduled`.
- Excel Table "Parameters": a settings Table, empty, never a source, step or final.
- Excel Table "Keys": a settings Table, empty, never a source, step or final.

**Typed over a formula:** none.

**Marks:** none.

**Refusals:** none.

**Left alone:** the Parameters and Keys Tables; the Steps sheet and the D1 notes (cells outside a Table). No Total Rows or defined names.

**To fill in:** `<database>`, in each block below.

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
- `job_runs`, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt.
- `scheduler_runs`, its typed columns: run_id, job_id, dt.

**Steps**
- None. Neither query names another query.

**Finals**, in the order of their blocks
- Table `run_days` (run_id, dt), loaded by Power Query "run_days", so its rows are that query's: the distinct (run_id, dt) pairs of `job_runs` and `scheduler_runs`.
- Table `matched` (run_id, job_id, dt, status), loaded by Power Query "matched", so its rows are that query's: `scheduler_runs` full outer joined to `job_runs` on run_id, with status taken from `job_runs`. Run 99 (TEST) has no scheduler row, so its run_id, job_id and dt come out NULL, as the query's expand takes them from `scheduler_runs`.

**Each piece's role**
- Excel Table "job_runs", "scheduler_runs": sources only (typed columns, no query loads them).
- Power Query "run_days": reads `job_runs` and `scheduler_runs`; the query of final `run_days`.
- Power Query "matched": reads `scheduler_runs` and `job_runs`; the query of final `matched`.
- Excel Table "Parameters": a settings Table, empty, never a source, step or final.
- Excel Table "Keys": a settings Table, empty, never a source, step or final.

**Typed over a formula:** none.

**Marks:** none.

**Refusals:** none.

**Left alone:** the Parameters and Keys Tables; the Steps sheet and the D1 notes (cells outside a Table). No Total Rows or defined names.

**To fill in:** `<database>`, in each block below.

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
- **Sources:** job_runs, its typed columns run_id, job_id, status, duration_mins and dt, read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins). Its formula columns read only its own typed columns, so it is a final.
- **Values typed over a formula:** none, so Keys needs no row.
- **Marks:** none. The blank status in row 98 is read only inside the COUNTIFS forms, so it is written as it is.
- **Refusals:** none.
- **Left alone:** Parameters (empty, read by no formula; a setting, never a source, step or final), Keys (empty; no value typed over a formula), and the Steps sheet (the Formula workbook's instructions, not a calculation).
- **To fill in:** `<database>`.

### Hive

```sql
-- Final: job_runs
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
- **Sources:** job_runs, its typed columns run_id, job_id and duration_mins, read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job); and job_runs (Total Row) (duration_mins, share), the Total Row being a final of its own with a column only for each of its two cells that holds a total.
- **Values typed over a formula:** none, so Keys needs no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters (empty, read by no formula; a setting, never a source, step or final), Keys (empty; no value typed over a formula), and the Steps sheet (the Formula workbook's instructions, not a calculation).
- **To fill in:** `<database>`.

### Hive

```sql
-- Final: job_runs
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
-- Final: job_runs (Total Row)
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
- **Sources:** job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read as `<database>.job_runs`. It has no formula and no query loads it, so it is a source only, never a final.
- **Steps:** none.
- **Finals:**
  - by_job (job_id, total_mins, runs, longest), a summary: its only typed column, job_id, is the one its SUMIFS, COUNTIFS and MAXIFS match on. Its typed groups 1, 2 and 3 are typed in, and its values are a GROUP BY of job_runs.
  - by_job (Total Row) (total_mins, runs, longest), with a column for each of its three cells that holds a total (SUBTOTAL 109, 109 and 104).
- **Values typed over a formula:** none, so Keys needs no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters (empty, read by no formula; a setting, never a source, step or final), Keys (empty; no value typed over a formula), and the Steps sheet (the Formula workbook's instructions, not a calculation).
- **To fill in:** `<database>`.

### Hive

```sql
-- Final: by_job
SELECT
  j.job_id,
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
-- Final: by_job (Total Row)
WITH by_job AS (
  SELECT
    j.job_id,
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
- **Sources:** job_runs, its typed columns run_id and dt, read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label).
- **Values typed over a formula:** none, so Keys needs no row.
- **Marks:** a_month_on, EDATE written as ADD_MONTHS(dt, 1), marked: a month's end stays one.
- **Refusals:** none.
- **Left alone:** Parameters (empty, read by no formula; a setting, never a source, step or final), Keys (empty; no value typed over a formula), and the Steps sheet (the Formula workbook's instructions, not a calculation).
- **To fill in:** `<database>`.

### Hive

```sql
-- Final: job_runs
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
- **Sources:** jobs, its typed columns job_id, job_name, team and region, read as `<database>.jobs`.
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens). It has formula columns and no query loads it, and nothing else reads it, so it is a final.
- **Values typed over a formula:** none, so Keys needs no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters (empty, read by no formula; a setting, never a source, step or final), Keys (empty; no value typed over a formula), and the Steps sheet (the Formula workbook's instructions, not a calculation).
- **To fill in:** `<database>`.

### Hive

```sql
-- Final: jobs
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
- Sources: `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs; `scheduler_runs`, its typed columns run_id, job_id, dt. Both are read as `<database>.<table>`.
- Steps: none.
- Finals: `job_runs`, with the columns run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on. Nothing else reads it, so it is a final, and its formula columns read its own rows and columns.
- Values typed over a formula: none. The Keys row is not needed.
- Marks: `weighted` (blank): the sample has a blank avg_retry_secs in run 98, so SUMPRODUCT reads `COALESCE(avg_retry_secs, 0)`. `no_status` (ISBLANK) is written as `status IS NULL`, with status as it is.
- Refusals: none.
- Left alone: `Parameters` and `Keys`, both empty; neither is a source, step or final.
- To fill in: `<database>`, the database both sources are in.

### Hive: job_runs
```sql
SELECT jr.run_id, jr.job_id, jr.status, jr.duration_mins, jr.avg_retry_secs,
  jr.status IS NULL AS no_status,
  FLOOR(jr.duration_mins / 7) AS weeks,
  GREATEST(jr.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(jr.duration_mins) OVER () AS spread,
  SUM(jr.duration_mins * COALESCE(jr.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(sr.dt, 'unscheduled') AS scheduled_on
FROM <database>.job_runs jr
LEFT JOIN <database>.scheduler_runs sr ON jr.run_id = sr.run_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X57

### Map
- Sources: `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt; `jobs`, its typed columns job_id, job_name, team, region. Both are read as `<database>.<table>`.
- Steps: none. Power Query `picked` and Power Query `ran_jobs` each load their Table, so each is that Table's final query.
- Finals:
  - `picked`, with the columns run_id, job_id, status, avg_retry_secs, status_lc, loaded by Power Query `picked`. Its rows are the query's: job_id in 1 or 2, and status blank or starting with S.
  - `ran_jobs`, with the columns job_id, job_name, team, region, loaded by Power Query `ran_jobs`. Its rows are the jobs with a run in job_runs and a job_name containing "a".
- Values typed over a formula: none. The Keys row is not needed.
- Marks: `picked` `avg_retry_secs` (blank): the Table.ReplaceValue step is `COALESCE(avg_retry_secs, 0)`, which sets the blank of run 98 to 0.
- Refusals: none.
- Left alone: `Parameters` and `Keys`, both empty; neither is a source, step or final.
- To fill in: `<database>`, the database both sources are in.

### Hive: picked
```sql
SELECT run_id, job_id, status, COALESCE(avg_retry_secs, 0) AS avg_retry_secs, LOWER(status) AS status_lc
FROM <database>.job_runs
WHERE job_id IN (1, 2) AND (status IS NULL OR status LIKE 'S%')
```

### Hive: ran_jobs
```sql
SELECT t.job_id, t.job_name, t.team, t.region
FROM <database>.jobs t
LEFT SEMI JOIN <database>.job_runs u ON u.job_id = t.job_id
WHERE t.job_name LIKE '%a%'
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X58

### Map
- Sources: `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt; `jobs`, its typed columns job_id, job_name, team, region; `scheduler_runs`, its typed columns run_id, job_id, dt; `region_budgets`, its typed columns job_id, budget_cents, region. All are read as `<database>.<table>`.
- Steps: none. No query's M names another query.
- Finals, each loaded by the Power Query of the same name:
  - `job_regions` (job_id, region)
  - `numbered` (run_id, dt, duration_mins, n)
  - `days_per_job` (job_id, days)
  - `unrun` (run_id, job_id)
  - `measures` (run_id, measure, amount)
- Values typed over a formula: none. The Keys row is not needed.
- Marks:
  - `days_per_job`: its Power Query sorts by days descending with no FirstN or index after the sort, so the order is dropped and no ORDER BY is written.
  - `measures`: the blank avg_retry_secs of run 98 has no row, as M's UnpivotOtherColumns drops the null, so each measure's SELECT has `WHERE ... IS NOT NULL`.
  - `numbered`: n is ROW_NUMBER() ordered by duration_mins descending, then run_id ascending, as the sort's ties were.
- Refusals: none.
- Left alone: `Parameters` and `Keys`, both empty; neither is a source, step or final.
- To fill in: `<database>`, the database all four sources are in.

### Hive: job_regions
```sql
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) r
```

### Hive: numbered
```sql
SELECT run_id, dt, duration_mins,
  ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC) AS n
FROM <database>.job_runs
```

### Hive: days_per_job
```sql
SELECT job_id, COUNT(DISTINCT dt) AS days
FROM <database>.job_runs
GROUP BY job_id
```

### Hive: unrun
```sql
SELECT run_id, job_id FROM <database>.scheduler_runs
EXCEPT
SELECT run_id, job_id FROM <database>.job_runs
```

### Hive: measures
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
- Sources: `jobs`, its typed columns job_id, job_name, team, region; `run_alerts`, its typed columns alert_id, run_id, severity, dt; `job_runs`, its typed columns run_id, job_id, duration_mins, dt. All are read as `<database>.<table>`.
- Steps: `job_runs`, with the columns run_id, job_id, duration_mins, dt, team, alerts, running_mins. Its formulas are team (XLOOKUP into jobs), alerts (COUNTIF into run_alerts) and running_mins (a running total over its own rows). Two other pieces read it, so it is a step: the `by_team` formulas and the `noisy_runs` query. It is a CTE in each final that reads it.
- Finals:
  - `by_team` (team, total_mins, alerted_runs): a summary, since its only typed column, team, is what its SUMIFS and COUNTIFS match on. Its typed groups `data` and `finance` are typed in, and its final query is a GROUP BY of `job_runs`.
  - `by_team (Total Row)` (total_mins, alerted_runs), reading `by_team`'s final query as a CTE. The label "Total" and the empty cells get no column.
  - `noisy_runs` (run_id, team, alerts, running_mins), loaded by Power Query `noisy_runs`.
- Values typed over a formula: none. The Keys row is not needed.
- Marks: none.
- Refusals: none.
- Left alone: `Parameters` and `Keys`, both empty; neither is a source, step or final.
- To fill in: `<database>`, the database all three sources are in.

### Hive: by_team
```sql
WITH job_runs AS (
  SELECT jr.run_id, jr.job_id, jr.duration_mins, jr.dt, j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(jr.duration_mins) OVER (PARTITION BY jr.job_id ORDER BY jr.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs jr
  LEFT JOIN <database>.jobs j ON jr.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON jr.run_id = a.run_id
)
SELECT g.team,
  COALESCE(s.total_mins, 0) AS total_mins,
  COALESCE(c.alerted_runs, 0) AS alerted_runs
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance') g
LEFT JOIN (SELECT team, SUM(duration_mins) AS total_mins FROM job_runs GROUP BY team) s
  ON g.team = s.team
LEFT JOIN (SELECT team, COUNT(*) AS alerted_runs FROM job_runs WHERE alerts > 0 GROUP BY team) c
  ON g.team = c.team
```

### Hive: by_team (Total Row)
```sql
WITH job_runs AS (
  SELECT jr.run_id, jr.job_id, jr.duration_mins, jr.dt, j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(jr.duration_mins) OVER (PARTITION BY jr.job_id ORDER BY jr.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs jr
  LEFT JOIN <database>.jobs j ON jr.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON jr.run_id = a.run_id
),
by_team AS (
  SELECT g.team,
    COALESCE(s.total_mins, 0) AS total_mins,
    COALESCE(c.alerted_runs, 0) AS alerted_runs
  FROM (SELECT 'data' AS team UNION ALL SELECT 'finance') g
  LEFT JOIN (SELECT team, SUM(duration_mins) AS total_mins FROM job_runs GROUP BY team) s
    ON g.team = s.team
  LEFT JOIN (SELECT team, COUNT(*) AS alerted_runs FROM job_runs WHERE alerts > 0 GROUP BY team) c
    ON g.team = c.team
)
SELECT SUM(total_mins) AS total_mins, SUM(alerted_runs) AS alerted_runs
FROM by_team
```

### Hive: noisy_runs
```sql
WITH job_runs AS (
  SELECT jr.run_id, jr.job_id, jr.duration_mins, jr.dt, j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(jr.duration_mins) OVER (PARTITION BY jr.job_id ORDER BY jr.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs jr
  LEFT JOIN <database>.jobs j ON jr.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON jr.run_id = a.run_id
)
SELECT run_id, team, alerts, running_mins
FROM job_runs
WHERE alerts >= 2
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X68

### Map
- Sources: `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt; `jobs`, its typed columns job_id, job_name, team, region; `region_budgets`, its typed columns job_id, budget_cents, region. All are read as `<database>.<table>`.
- Steps: `base`, Power Query with connection only, reading `job_runs`, `jobs` and `region_budgets`. Two queries read it, so it is a CTE in each final that reads it. Its columns are run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name, region.
- Finals:
  - `by_region` (region, total_mins, runs, share), loaded by Power Query `by_region`. Its share is total_mins over the SUM of by_region's own rows, written as a window over the grouped rows.
  - `by_region (Total Row)` (total_mins): the only Total Row cell that holds a total is total_mins. The label "Total" and the empty cells get no column.
  - `top_runs` (run_id, job_name, region), loaded by Power Query `top_runs`.
- Values typed over a formula: none. The Keys row is not needed.
- Marks: none.
- Refusals: none.
- Left alone: `Parameters` and `Keys`, both empty; neither is a source, step or final. In `base`, the blank status and blank avg_retry_secs of run 98 are carried through, and no final reads them, so no COALESCE is written for them.
- To fill in: `<database>`, the database all three sources are in.

### Hive: by_region
```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  INNER JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT g.region, g.total_mins, g.runs, g.total_mins / SUM(g.total_mins) OVER () AS share
FROM (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) g
```

### Hive: by_region (Total Row)
```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  INNER JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
by_region AS (
  SELECT g.region, g.total_mins, g.runs, g.total_mins / SUM(g.total_mins) OVER () AS share
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

### Hive: top_runs
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

- **Sources**: `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read as `<database>.job_runs`. No query loads it, and it has no formula column.
- **Steps**: Power Query `ok_runs` (keeps job_runs' SUCCESS rows, columns run_id, job_id, duration_mins). Query `ok_by_job` names it, so it is a CTE `ok_runs` in the `ok_by_job` block.
- **Finals**:
  - Excel Table `ok_runs` (run_id, job_id, duration_mins, hours). Loaded by query `ok_runs`, so its rows are that query's. No other Table's formula reads it, and its own hours formula reads its own row, so it is a final, not a step. hours is `duration_mins / 60`.
  - Excel Table `ok_by_job` (job_id, total_mins). Loaded by query `ok_by_job`, which reads step `ok_runs` and sums duration_mins per job_id. Nothing reads it, so it is a final.
- **Power Query `ok_by_job`**: the loader of final `ok_by_job`. No query names it, so it is not a step.
- **Left alone**: Excel Table `Parameters` (empty, as no formula uses a fixed value), Excel Table `Keys` (empty, as no value is typed over a formula), and the Steps sheet.
- **Values typed over a formula**: none, so no Keys row is needed.
- **Marks**: none.
- **Refusals**: none.
- **`<...>` to fill in**: `<database>`, the database name, in each FROM.

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

- **Sources**: `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read as `<database>.job_runs`. No query loads it, and it has no formula column.
- **Steps**: Excel Table `jobs`, typed job_id, job_name, team, with formula columns runs and total. Its typed columns are read as `<database>.jobs`, and its formulas read job_runs. It is read by the formulas of `by_team` and by query `busy_jobs`, so it is a CTE `jobs` in each of those two final blocks. runs is `COALESCE` of the count of job_runs per job_id; total is `COALESCE` of the sum of duration_mins per job_id.
- **Finals**:
  - Excel Table `by_team` (team, team_total). Its only typed column, team, is the one its SUMIFS matches on, so it is a summary. Its final query groups the step `jobs` by team, with the typed groups `data`, `finance` and `web` typed in. team_total is the SUM of jobs' total per team, COALESCE'd to 0. Nothing reads it, and no query loads it.
  - Excel Table `busy_jobs` (job_id, job_name, runs). Loaded by Power Query `busy_jobs`, which reads Table `jobs` and keeps runs of at least 3. Nothing reads it, so it is a final.
- **Power Query `busy_jobs`**: the loader of final `busy_jobs`. No query names it, so it is not a step.
- **Left alone**: Excel Table `Parameters` (empty, as no formula uses a fixed value), Excel Table `Keys` (empty, as no value is typed over a formula), and the Steps sheet.
- **Values typed over a formula**: none, so no Keys row is needed.
- **Marks**: none.
- **Refusals**: none.
- **`<...>` to fill in**: `<database>`, the database name, in each FROM and each join.

### Hive

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(n.runs, 0) AS runs,
    COALESCE(t.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) n
    ON j.job_id = n.job_id
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
    COALESCE(n.runs, 0) AS runs,
    COALESCE(t.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) n
    ON j.job_id = n.job_id
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

- **Sources**: `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read as `<database>.job_runs`. No query loads it, and it has no formula column.
- **Steps**: Power Query `long_runs` (keeps job_runs rows with duration_mins of at least 15, columns run_id, dt, duration_mins). Query `long_per_day` names it, so it is a CTE `long_runs` in the `long_per_day` block.
- **Finals**:
  - Excel Table `long_runs` (run_id, dt, duration_mins, over). Loaded by query `long_runs`, so its rows are that query's. No other Table's formula reads it, and its own formula reads its own row, so it is a final. over is `duration_mins - 15`.
  - Excel Table `long_per_day` (dt, runs). Loaded by query `long_per_day`, which reads step `long_runs` and counts rows per dt. Nothing reads it, so it is a final.
- **Power Query `long_per_day`**: the loader of final `long_per_day`. No query names it, so it is not a step.
- **Left alone**: Excel Table `Parameters` (empty, as no formula uses a fixed value), Excel Table `Keys` (empty, as no value is typed over a formula), and the Steps sheet.
- **Values typed over a formula**: none, so no Keys row is needed.
- **Marks**: none.
- **Refusals**: none.
- **`<...>` to fill in**: `<database>`, the database name, in each FROM.

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
SELECT dt, COUNT(*) AS runs
FROM long_runs
GROUP BY dt
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X76

### Map

- **Sources**:
  - `jobs`, its typed columns job_id, job_name, team, region, read as `<database>.jobs`. No query loads it as a Table, and it has no formula column.
  - `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read as `<database>.job_runs`.
- **Steps**: Power Query `finance_jobs` (keeps jobs rows with team 'finance', columns job_id, job_name). Query `finance_runs` names it, so it is a CTE `finance_jobs` in the `finance_runs` block.
- **Finals**:
  - Excel Table `finance_jobs` (job_id, job_name, label). Loaded by query `finance_jobs`, so its rows are that query's. No other Table's formula reads it, and its own label formula reads its own row, so it is a final. label is `UPPER(job_name)`.
  - Excel Table `finance_runs` (run_id, job_name, duration_mins). Loaded by Power Query `finance_runs`, which joins job_runs to step `finance_jobs` on job_id, inner. Nothing reads it, so it is a final.
- **Power Query `finance_runs`**: the loader of final `finance_runs`. No query names it, so it is not a step.
- **Left alone**: Excel Table `Parameters` (empty, as no formula uses a fixed value), Excel Table `Keys` (empty, as no value is typed over a formula), and the Steps sheet.
- **Values typed over a formula**: none, so no Keys row is needed.
- **Marks**: none.
- **Refusals**: none.
- **`<...>` to fill in**: `<database>`, the database name, in each FROM and each join.

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

- **Sources**: `job_runs`, its typed columns run_id, job_id, status, duration_mins, read as `<database>.job_runs`. No query loads it.
- **Steps**: none.
- **Finals**:
  - Excel Table `job_runs` (run_id, job_id, status, duration_mins, kept, long_or_failed). No query loads it and nothing else reads it, so it is a final. Its formula columns read its own row, which does not make it a step.
    - kept: `IF(COALESCE(status, '') <> '' AND COALESCE(status, '') <> 'TEST', 1, 0)`. The IF is kept as it is, and AND(a, b) is written `a AND b`.
    - long_or_failed: `IF((duration_mins > 25 OR COALESCE(status, '') = 'FAILED'), 'yes', 'no')`. OR(a, b) is written `(a OR b)`.
- **Left alone**: Excel Table `Parameters` (empty, as no formula uses a fixed value), Excel Table `Keys` (empty, as no value is typed over a formula), and the Steps sheet.
- **Values typed over a formula**: none, so no Keys row is needed.
- **Marks**:
  - blank, in kept and in long_or_failed: status is blank in the sample (run 98). Excel reads that blank as "", and Hive as NULL, so status is written as `COALESCE(status, '')` in both formulas.
- **Refusals**: none.
- **`<...>` to fill in**: `<database>`, the database name, in the FROM.

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

### Map

- **Sources:** `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** `by_job` (job_id, long_failed, mid_mins, failed_or_test), a summary: its typed job_ids 1, 2 and 3 are typed in, and its three formula columns are groups read from job_runs.
- **Settings, neither a source, step nor a final:** `Parameters` (empty; no formula reads it) and `Keys` (empty; no value is typed over a formula, so no row).
- **Typed over a formula:** none.
- **Marks:** none. The blank status in job_runs row 98 is kept as it is inside the `<>TEST` condition, which counts a blank as Excel does.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the D1 notes on the Parameters and Keys sheets, which are cells outside a Table.
- **To fill in:** `<database>`, the database that holds job_runs (in each read of it in by_job's query).

### Hive

```sql
SELECT j.job_id,
  COALESCE(lf.long_failed, 0) AS long_failed,
  COALESCE(mm.mid_mins, 0) AS mid_mins,
  COALESCE(ft.failed_or_test, 0) AS failed_or_test
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS long_failed
  FROM <database>.job_runs
  WHERE status = 'FAILED' AND duration_mins >= 20
  GROUP BY job_id
) lf ON j.job_id = lf.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS mid_mins
  FROM <database>.job_runs
  WHERE duration_mins > 10 AND duration_mins <= 30 AND (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) mm ON j.job_id = mm.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS failed_or_test
  FROM <database>.job_runs
  WHERE status IN ('FAILED', 'TEST')
  GROUP BY job_id
) ft ON j.job_id = ft.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X82

### Map

- **Sources:** `job_runs` (its typed columns: run_id, job_id, status, duration_mins, dt), read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** `job_runs` (run_id, job_id, status, duration_mins, dt, needs_look, failed_long_mins, failed_or_late). It is a final because no other Table's formula or query reads it; its formulas reading its own columns don't count. failed_long_mins and failed_or_late read the whole column of their own Table, so each is a window total with OVER (), as each row shows the same total.
- **Settings, neither a source, step nor a final:** `Parameters` (empty; no formula reads it) and `Keys` (empty; no value is typed over a formula, so no row).
- **Typed over a formula:** none. Every row holds the same formulas, and Keys is empty.
- **Marks:** blank. needs_look reads status, which is blank in row 98 (job_id 2); it is written as `COALESCE(status, '')` there. The status reads inside the SUMPRODUCT conditions are written as they are.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the D1 notes on the Parameters and Keys sheets, which are cells outside a Table.
- **To fill in:** `<database>`, the database that holds job_runs.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins, dt,
  IF((COALESCE(status, '') = 'FAILED' OR duration_mins > 25) AND NOT (job_id = 1), 1, 0) AS needs_look,
  SUM(CASE WHEN status = 'FAILED' AND duration_mins > 15 THEN duration_mins ELSE 0 END) OVER () AS failed_long_mins,
  COUNT(CASE WHEN status = 'FAILED' OR dt = '2026-09-24' THEN 1 END) OVER () AS failed_or_late
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
