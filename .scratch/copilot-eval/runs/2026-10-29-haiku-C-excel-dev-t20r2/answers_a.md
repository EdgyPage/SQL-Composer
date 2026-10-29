date: 2026-10-29
arm: C
model: haiku
files: fac0fd8

## X01

Sources: job_runs (run_id, job_id, duration_mins, dt).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours).
Typed over: none, so no Keys row is needed (Keys is empty).
Marks: none. No formula filters the rows, so every sample row is kept.
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins, dt,
  duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X02

Sources: job_runs (run_id, job_id, status, duration_mins).
Steps: none.
Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag).
Typed over: none.
Marks: the blank status in row 98 is read by no formula, so it passes through as NULL.
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF(duration_mins > 25 OR job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X03

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: none.
Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs).
Typed over: none.
Marks:
- blank: status in row 98 is read by score, so it is wrapped as COALESCE(status, ''). Excel gives 0 for it, and so does the ELSE here.
- blank: avg_retry_secs in row 98 is read by mins_per_retry and total_secs, so it is wrapped as COALESCE(avg_retry_secs, 0). Excel reads it as 0, which gives total_secs of 900 for that row.
- SWITCH with two values and a default is written in the one-pair form, CASE ... WHEN ... ELSE ... END, with one more WHEN. This extends the listed form.
- IFERROR(a / b, 0) is COALESCE(a / b, 0), as Hive gives NULL for a divide by 0.
- The _xlfn. prefix is dropped.
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X04

Sources: jobs (job_id, job_name, team, region).
Steps: none.
Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd). Nothing reads jobs, so it is a final as well as a source.
Typed over: none.
Marks:
- `&` is CONCAT, nested as CONCAT(a, b) for the two joins.
- LEN is LENGTH.
- MOD(a, b) is PMOD(a, b).
- The _xlfn. prefix is not present.
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT job_id, job_name, team, region,
  CONCAT(CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-'), region) AS code,
  LENGTH(job_name) AS name_length,
  ROUND(job_id / 3, 2) AS third,
  PMOD(job_id, 2) AS odd
FROM <database>.jobs
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X05

Sources: job_runs (run_id, dt); region_costs (job_id, cost_cents, region, dt).
Steps: none.
Finals: job_runs (run_id, dt, month, days_since); region_costs (job_id, cost_cents, region, dt, day).
Typed over: none.
Marks:
- region_costs.dt is a date held as text (20260911), so day is built from CONCAT(SUBSTR ...), which gives yyyy-mm-dd text. DATE(LEFT, MID, RIGHT) is replaced by this text form.
- DATE(2026,9,1) is '2026-09-01', the start for days_since.
- DATEDIF(start, dt, "d") is DATEDIFF(dt, start).
- blank: cost_cents in row 29 of region_costs is read by no formula, so it passes through as NULL.
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT run_id, dt, MONTH(dt) AS month,
  DATEDIFF(dt, '2026-09-01') AS days_since
FROM <database>.job_runs
```

```sql
SELECT job_id, cost_cents, region, dt,
  CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS day
FROM <database>.region_costs
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X06

Sources: job_runs (run_id, job_id, duration_mins); jobs (job_id, job_name).
Steps: none. jobs is read by job_runs, so it stays a source and is not a final.
Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job).
Typed over: none.
Marks:
- XLOOKUP(job_id, jobs[job_id], jobs[job_name]) is LEFT JOIN jobs ON job_id, then jobs.job_name. It has no fourth argument, so there is no COALESCE. A job_id with no match gives NULL here, where Excel shows #N/A.
- COUNTIFS over its own Table on job_id is COUNT(*) OVER (PARTITION BY job_id), with COALESCE.
- The _xlfn. prefix is dropped.
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X07

Sources: job_runs (run_id, job_id, status); jobs (job_id, team, region).
Steps: none.
Finals: job_runs (run_id, job_id, status, team, region).
Typed over: none.
Marks:
- VLOOKUP([@job_id], jobs, 3, FALSE) is exact. Column 3 of jobs is team. It is a LEFT JOIN jobs ON job_id, then jobs.team.
- INDEX(jobs[region], MATCH([@job_id], jobs[job_id], 0)) is exact and uses the same LEFT JOIN, then jobs.region. One join serves both formulas.
- The blank status in row 98 is read by no formula, so it passes through as NULL.
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X08

Sources: job_runs (job_id, duration_mins, avg_retry_secs).
Steps: none.
Finals: by_job (job_id, total_mins, avg_retry, longest). by_job's only typed column is job_id, which its SUMIFS and MAXIFS match on, so by_job is a summary: a GROUP BY of job_runs. Its rows are job_id 1, 2 and 3, the same as the GROUP BY gives here.
Typed over: none.
Marks:
- SUMIFS is SUM, with COALESCE(..., 0).
- AVERAGEIFS is AVG, left NULL. The blank avg_retry_secs in row 98 is skipped, as Excel skips it and AVG skips NULL.
- MAXIFS is MAX, with COALESCE(..., 0).
- The _xlfn. prefix is dropped.
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT job_id,
  COALESCE(SUM(duration_mins), 0) AS total_mins,
  AVG(avg_retry_secs) AS avg_retry,
  COALESCE(MAX(duration_mins), 0) AS longest
FROM <database>.job_runs
GROUP BY job_id
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X09

Sources: job_runs (run_id, job_id, duration_mins, avg_retry_secs); jobs (job_id, team).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost).
Typed over: cost in row 4 (run 97) is 100, typed over its formula. Keys holds job_runs, run_id, so that row is matched on run_id: CASE WHEN run_id = 97 THEN 100 ELSE ... END.
Marks:
- XLOOKUP(job_id, jobs[job_id], jobs[team]) is LEFT JOIN jobs ON job_id, then jobs.team.
- SUMIFS(duration_mins, team, [team]) over its own Table is SUM(duration_mins) OVER (PARTITION BY team), computed after the join.
- XLOOKUP("rate", Parameters[name], Parameters[value]) is its value, 0.5. Parameters is not a source.
- blank: avg_retry_secs in row 98 is read by cost, so it is wrapped as COALESCE(avg_retry_secs, 0).
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs,
  j.team,
  SUM(r.duration_mins) OVER (PARTITION BY j.team) AS team_mins,
  CASE WHEN r.run_id = 97 THEN 100
    ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5
  END AS cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X10

Sources: job_runs (run_id, job_id, duration_mins, dt).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample).
Typed over: hours in row 9 (run 103) is 9, typed over its formula. Keys is empty, so there is no Keys row for job_runs. The row is matched on every typed column: run_id, job_id, duration_mins and dt.
Marks: hours is duration_mins / 60, as Excel's /60.
Refused: sample is =RAND(), which is refused as NULL AS sample.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24'
    THEN 9
    ELSE duration_mins / 60
  END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X11

Sources: job_runs (run_id, duration_mins).
Steps: none.
Finals: job_runs (run_id, duration_mins, pick, scaled).
Typed over: none.
Marks: none.
Refused:
- pick is =INDIRECT("B"&ROW()). INDIRECT and ROW() are refused, so it is NULL AS pick.
- scaled reads Summary!C2, a cell outside a Table that is not a defined name, so it is refused and NULL AS scaled. To convert it, put the value of Summary!C2 (3) into a Table, such as Parameters, and ask again.
Left alone: the bar chart on the Summary sheet, and the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  NULL AS pick,
  NULL AS scaled
FROM <database>.job_runs
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X12

Sources: job_runs (run_id, duration_mins).
Steps: none.
Finals: job_runs (run_id, duration_mins, running, loop, with_tax).
Typed over: none.
Marks:
- tax_rate is a defined name for Summary!$B$3, a cell outside a Table. Its value, 0.2, is used, and it should move into Parameters.
Refused:
- running is =SUM(OFFSET(...)). OFFSET and ROW() are refused, so it is NULL AS running.
- loop reads its own column, so it is circular and refused as NULL AS loop.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  NULL AS running,
  NULL AS loop,
  duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X13

Sources: job_runs (run_id, job_id); jobs (job_id, job_name).
Steps: none.
Finals: job_runs (run_id, job_id, name, doubled).
Typed over: none.
Marks:
- VLOOKUP(job_id, jobs, 2, TRUE) is approximate. It is converted as exact, a LEFT JOIN ON job_id = job_id, then jobs.job_name AS name. The sample's job_ids all match, so the result is the same here.
Refused:
- doubled uses DOUBLE, a defined name holding a LAMBDA, so it is refused as NULL AS doubled.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, j.job_name AS name,
  NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X14

Sources: job_runs (job_id, duration_mins).
Steps: job_runs_hours. job_runs has a calculated hours column that by_job reads, so it is a step: a CTE of duration_mins / 60 AS hours.
Finals: by_job (job_id, total_hours). by_job's only typed column is job_id, which its SUMIFS matches on, so it is a summary: a GROUP BY of the step.
Typed over: none.
Marks: SUMIFS is SUM, with COALESCE(..., 0).
Refused: none.
Left alone: the PivotTable on sheet "Pivot", which is charted from job_runs and is left alone; and the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
WITH job_runs_hours AS (
  SELECT job_id, duration_mins / 60 AS hours
  FROM <database>.job_runs
)
SELECT job_id,
  COALESCE(SUM(hours), 0) AS total_hours
FROM job_runs_hours
GROUP BY job_id
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X15

Sources: tblRuns (`<run_id>`, `<job_id>`, `<duration_mins>`). The Table name tblRuns is a plain name, so it is kept.
Steps: none.
Finals: tblRuns (`<run_id>`, `<job_id>`, `<duration_mins>`, hours).
Typed over: none.
Marks: the headers are not plain names, so they are in snake case in brackets: "Run ID" is `<run_id>`, "Job ID" is `<job_id>`, and "Duration (mins)" is `<duration_mins>`. Check each against the database. The Hours header is plain.
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`.

```sql
SELECT <run_id>, <job_id>, <duration_mins>,
  <duration_mins> / 60 AS hours
FROM <database>.tblRuns
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X16

Sources: job_runs (run_id, job_id, duration_mins), read by the query long_runs.
Steps: none. The query has no other query or Table reading it, so its steps are the final's query.
Finals: long_runs (run_id, job_id, minutes, hours), the rows of the Power Query "long_runs".
Typed over: none.
Marks: Table.SelectRows is WHERE duration_mins > 15. Table.AddColumn's hours is duration_mins / 60, taken before the rename. Table.RenameColumns is duration_mins AS minutes. The type on AddColumn is not converted.
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins AS minutes,
  duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X17

Sources: job_runs (job_id, status, duration_mins).
Steps: ok_runs. The connection-only query ok_runs is read by ok_by_job, so it is kept as a CTE inside ok_by_job's query and is not left out.
Finals: ok_by_job (job_id, runs, total_mins), the rows of the Power Query "ok_by_job".
Typed over: none.
Marks:
- Table.Group: Table.RowCount is COUNT(*), and List.Sum is SUM.
- The blank status in row 98 is left out, as M's = leaves it out.
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
WITH ok_runs AS (
  SELECT job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT job_id,
  COUNT(*) AS runs,
  SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X18

Sources: job_runs (run_id, job_id, duration_mins); jobs (job_id, job_name).
Steps: none.
Finals: top_runs (run_id, job_name, duration_mins), the rows of the Power Query "top_runs".
Typed over: none.
Marks:
- Table.NestedJoin with JoinKind.LeftOuter is LEFT JOIN jobs ON job_id, and Table.ExpandTableColumn takes job_name.
- Table.Sort with Order.Descending is ORDER BY duration_mins DESC.
- Table.FirstN(3) is LIMIT 3. The two 30-minute runs both fall inside the top 3 and the next run is 20, so no tie is cut.
Refused: none.
Left alone: the Steps sheet's text, which is outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC
LIMIT 3
```

Toolbox code is not written here, as this asks for Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.
