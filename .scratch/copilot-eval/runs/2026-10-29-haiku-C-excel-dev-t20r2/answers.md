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

## X19

**Map**

- Sources: `scheduler_runs` (workbook Table, typed run_id, job_id, dt); `job_runs` (not in the workbook: `Sql.Database("dwh01", "ops")` names it, as the query reads it).
- Steps: none.
- Finals: `all_runs` (run_id, job_id, dt), one query, loaded by the Power Query `all_runs`.
- Parameters and Keys: none.

**Marks**

- `Sql.Database("dwh01", "ops")` is not a workbook source: converted to the table it names, `job_runs`. Check that `job_runs` is in `<database>` (the ops database on dwh01).

**Refused**

- Query `holidays` (connection only): `Web.Contents` of a web address. Left out, and named: a web source, and nothing reads it.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in both table names.

```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt
FROM <database>.job_runs
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X20

**Map**

- Sources: `run_alerts` (typed alert_id, run_id, severity, dt).
- Steps: none (the steps of the query are inside the final).
- Finals: `alert_pivot` (run_id, high, low), one query, loaded by the Power Query `alert_pivot`.
- Parameters and Keys: none.

**Marks**

- Table.Pivot: one column per severity value in the sample, `high` and `low`, with THEN 1 to count and NULL where none, as M leaves it. The pivot's columns are now fixed at high and low; a new severity gets no column.
- The filter `[run_id] = 97 or [run_id] = 101` is kept as `run_id = 97 OR run_id = 101`.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in the table name.

```sql
SELECT run_id,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
WHERE run_id = 97 OR run_id = 101
GROUP BY run_id
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X41

**Map**

- Sources: `job_runs` (typed run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: `job_runs` (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). Nothing else reads it, so it is a final. Its formulas read its typed columns, not their own column.
- Parameters and Keys: none. No value is typed over a formula, so no Keys row is needed.

**Marks**

- `MINIFS` over its own Table: `MIN(CASE WHEN status = 'SUCCESS' THEN duration_mins END) OVER (PARTITION BY job_id)`, with COALESCE to 0.
- Blank: the status on run 98 is blank. The MINIFS condition is an -IFS form, which skips a blank, so no COALESCE is added to status.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in the table name.

```sql
SELECT run_id, job_id, status, duration_mins,
  RANK() OVER (ORDER BY duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN status = 'SUCCESS' THEN duration_mins END) OVER (PARTITION BY job_id), 0) AS shortest_ok,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0) AS job_total
FROM <database>.job_runs
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X42

**Map**

- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt), read for job_id and duration_mins; `jobs` (typed job_id, job_name).
- Steps: none. `job_runs` has no formula, so it is only a source.
- Finals: `jobs` (job_id, job_name, runs, avg_mins, id_order). Nothing reads it, so it is a final.
- Parameters and Keys: none.

**Marks**

- `COUNTIF` over another Table: LEFT JOIN to a count per job_id, COALESCE to 0.
- `IFERROR(AVERAGEIF(...), 0)`: LEFT JOIN to an average per job_id, with COALESCE(avg, 0) as IFERROR gives 0.
- `RANK.EQ(x, jobs[job_id], 1)`: the third argument 1 makes it ascending.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in each table name.

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

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X43

**Map**

- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (typed job_id, job_name, team, region).
- Steps: none. Each query's steps are inside its final.
- Finals: `busy_teams` (team, runs, shortest, avg_mins), one query, loaded by the Power Query `busy_teams`; `statuses` (job_id, status), one query, loaded by the Power Query `statuses`.
- Parameters and Keys: none.

**Marks**

- Table.Distinct with no column list: SELECT DISTINCT. The blank status for job 2 stays NULL, as Table.Distinct keeps it.
- Table.NestedJoin Inner: JOIN.
- `[runs] > 4` after the Table.Group: HAVING.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in each table name.

`busy_teams`:

```sql
SELECT j.team, COUNT(*) AS runs, MIN(r.duration_mins) AS shortest, AVG(r.duration_mins) AS avg_mins
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.team
HAVING COUNT(*) > 4
```

`statuses`:

```sql
SELECT DISTINCT job_id, status
FROM <database>.job_runs
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X44

**Map**

- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (typed job_id, job_name, team, region); `scheduler_runs` (typed run_id, job_id, dt).
- Steps: none.
- Finals: `jobs_with_runs` (run_id, job_name), one query, loaded by the Power Query `jobs_with_runs`; `never_scheduled` (job_id, job_name, team), one query, loaded by the Power Query `never_scheduled`.
- Parameters and Keys: none.

**Marks**

- Table.NestedJoin RightOuter: LEFT JOIN with the two tables swapped, so `jobs` is first. The job cache_warm has no run, so its run_id is NULL (the blank row in the sample).
- Table.NestedJoin LeftAnti: LEFT JOIN, then WHERE the joined key IS NULL, with the columns of `jobs` only.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in each table name.

`jobs_with_runs`:

```sql
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON j.job_id = r.job_id
```

`never_scheduled`:

```sql
SELECT j.job_id, j.job_name, j.team
FROM <database>.jobs j
LEFT JOIN <database>.scheduler_runs s ON j.job_id = s.job_id
WHERE s.job_id IS NULL
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X45

**Map**

- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); `scheduler_runs` (typed run_id, job_id, dt).
- Steps: none.
- Finals: `run_days` (run_id, dt), one query, loaded by the Power Query `run_days`; `matched` (run_id, job_id, dt, status), one query, loaded by the Power Query `matched`.
- Parameters and Keys: none.

**Marks**

- Table.Combine inside Table.Distinct: UNION.
- Table.NestedJoin FullOuter: FULL OUTER JOIN. run_id, job_id and dt come from `scheduler_runs` (the left table), so they are NULL for run 99, which only `job_runs` holds (the blank row in the sample). Its status comes from `job_runs`.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in each table name.

`run_days`:

```sql
SELECT run_id, dt FROM <database>.job_runs
UNION
SELECT run_id, dt FROM <database>.scheduler_runs
```

`matched`:

```sql
SELECT s.run_id, s.job_id, s.dt, r.status
FROM <database>.scheduler_runs s
FULL OUTER JOIN <database>.job_runs r ON s.run_id = r.run_id
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X51

**Map**

- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, dt).
- Steps: none.
- Finals: `job_runs` (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins). Nothing else reads it, so it is a final.
- Parameters and Keys: none. No value is typed over a formula.

**Marks**

- `COUNTIFS` over its own Table with the job_id match: a COUNT of CASE WHEN over partition job_id, COALESCE to 0.
- `COUNTIFS(status, "<>SUCCESS")` with no match column: `(status <> 'SUCCESS' OR status IS NULL)`, over the whole column. The blank status on run 98 is counted, as Excel counts a blank there.
- `"*ail*"`: `LOWER(status) LIKE '%ail%'`, as Excel ignores case.
- `SUMIFS` with `"<="&[@dt]`: a running total over job_id, ORDER BY dt, RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW, so ties are included as Excel includes them. COALESCE to 0.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in the table name.

```sql
SELECT run_id, job_id, status, duration_mins, dt,
  COALESCE(COUNT(CASE WHEN duration_mins > 15 THEN 1 END) OVER (PARTITION BY job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (status <> 'SUCCESS' OR status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY job_id), 0) AS failed_in_job,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X52

**Map**

- Sources: `job_runs` (typed run_id, job_id, duration_mins). It is not a summary, since its typed columns go beyond what a formula matches on.
- Steps: none.
- Finals: `job_runs` (run_id, job_id, duration_mins, share, vs_avg, rank_in_job). Nothing else reads it, so it is a final.
- Total Row: `job_runs (Total Row)`, a query of its own, one row, with a column per total in order (duration_mins, share), no label.
- Parameters and Keys: none.

**Marks**

- `SUM(...)` and `AVERAGE` over the whole column: `OVER ()`.
- `COUNTIFS(job_id, ">"&duration) + 1` ranks within job_id: `RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC)`. Ties share a rank, as the COUNTIFS form gives.
- The Total Row's SUBTOTAL(109, share) sums the share column, so the share is worked out in a CTE first.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in each table name.

`job_runs`:

```sql
SELECT run_id, job_id, duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

`job_runs (Total Row)`:

```sql
WITH shares AS (
  SELECT duration_mins,
    duration_mins / SUM(duration_mins) OVER () AS share
  FROM <database>.job_runs
)
SELECT SUM(duration_mins) AS duration_mins,
  SUM(share) AS share
FROM shares
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X53

**Map**

- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: `by_job` (job_id, total_mins, runs, longest). Its only typed column, job_id, is what its SUMIFS, COUNTIFS and MAXIFS match on, so it is a summary: a GROUP BY of `job_runs`.
- Total Row: no query of its own. Its totals add up SUMs and COUNTs and take a MAX of MAXes, so the `by_job` query ends `GROUP BY job_id WITH ROLLUP`, and the rollup row (job_id NULL) is the Total Row.
- Parameters and Keys: none.

**Marks**

- The summary's rows come from the job_ids in `job_runs`. A job_id with no runs gives no row, where SUMIFS would give 0. Check that every job_id of `by_job` has runs.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in the table name.

```sql
SELECT job_id,
  SUM(duration_mins) AS total_mins,
  COUNT(*) AS runs,
  MAX(duration_mins) AS longest
FROM <database>.job_runs
GROUP BY job_id WITH ROLLUP
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X54

**Map**

- Sources: `job_runs` (typed run_id, dt); `scheduler_runs` (typed run_id, job_id, dt).
- Steps: none.
- Finals: `job_runs` (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label), a final with its own formulas; `scheduler_runs` (run_id, job_id, dt), one query, since nothing reads it.
- Parameters and Keys: none.

**Marks**

- `EDATE([@dt],1)`: ADD_MONTHS. A month's end stays one.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in each table name.

`job_runs`:

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

`scheduler_runs`:

```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X55

**Map**

- Sources: `jobs` (typed job_id, job_name, team, region).
- Steps: none.
- Finals: `jobs` (job_id, job_name, team, region, title, tag, code, has_sync, tens). Nothing else reads it, so it is a final.
- Parameters and Keys: none.

**Marks**

- None beyond the conversions: `SEARCH` ignores case through LOWER, as the formula rule gives.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in the table name.

```sql
SELECT job_id, job_name, team, region,
  INITCAP(REPLACE(job_name, '_', ' ')) AS title,
  CONCAT_WS('/', team, region) AS tag,
  CONCAT(region, '-', job_id) AS code,
  INSTR(LOWER(job_name), LOWER('SYNC')) > 0 AS has_sync,
  CAST(CONCAT(job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X56

**Map**

- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs); `scheduler_runs` (typed run_id, job_id, dt), read by the scheduled_on formula.
- Steps: none. `scheduler_runs` is read by a formula, so it is a source, not a final.
- Finals: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on).
- Parameters and Keys: none.

**Marks**

- Blank: the avg_retry_secs on run 98 is blank, and `weighted` (SUMPRODUCT, not an -IFS form) reads it, so it is wrapped as `COALESCE(avg_retry_secs, 0)`.
- Blank: the status on run 98 is blank; `no_status` is `status IS NULL`, the ISBLANK form.
- `XLOOKUP` with its fourth argument "unscheduled": LEFT JOIN to `scheduler_runs` on run_id, then COALESCE of its dt to 'unscheduled'.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in each table name.

```sql
SELECT j.run_id, j.job_id, j.status, j.duration_mins, j.avg_retry_secs,
  j.status IS NULL AS no_status,
  FLOOR(j.duration_mins / 7) AS weeks,
  GREATEST(j.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(j.duration_mins) OVER () AS spread,
  SUM(j.duration_mins * COALESCE(j.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(s.dt, 'unscheduled') AS scheduled_on
FROM <database>.job_runs j
LEFT JOIN <database>.scheduler_runs s ON j.run_id = s.run_id
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X57

**Map**

- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (typed job_id, job_name, team, region).
- Steps: none. Each query's steps are inside its final.
- Finals: `picked` (run_id, job_id, status, avg_retry_secs, status_lc), one query, loaded by the Power Query `picked`; `ran_jobs` (job_id, job_name, team, region), one query, loaded by the Power Query `ran_jobs`.
- Parameters and Keys: none.

**Marks**

- `List.Contains({1, 2}, [job_id])`: `job_id IN (1, 2)`.
- `[status] = null`: `status IS NULL`. `Text.StartsWith([status], "S")`: `status LIKE 'S%'`, case kept.
- Table.ReplaceValue null to 0 on avg_retry_secs: COALESCE(avg_retry_secs, 0), for the blank on run 98.
- `Text.Lower`: LOWER, so the blank status on run 98 gives a NULL status_lc.
- `List.Contains(Runs[job_id], [job_id])`, a row whose job_id is in another table: LEFT SEMI JOIN on job_runs.
- `Text.Contains([job_name], "a")`: `job_name LIKE '%a%'`, case kept.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in each table name.

`picked`:

```sql
SELECT run_id, job_id, status,
  COALESCE(avg_retry_secs, 0) AS avg_retry_secs,
  LOWER(status) AS status_lc
FROM <database>.job_runs
WHERE job_id IN (1, 2) AND (status IS NULL OR status LIKE 'S%')
```

`ran_jobs`:

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r ON r.job_id = j.job_id
WHERE j.job_name LIKE '%a%'
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X58

**Map**

- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (typed job_id, job_name, team, region); `scheduler_runs` (typed run_id, job_id, dt); `region_budgets` (typed job_id, budget_cents, region).
- Steps: none. Each query's steps are inside its final.
- Finals, each one query, loaded by its Power Query:
  - `job_regions` (job_id, region)
  - `numbered` (run_id, dt, duration_mins, n)
  - `days_per_job` (job_id, days)
  - `unrun` (run_id, job_id)
  - `measures` (run_id, measure, amount)
- Parameters and Keys: none.

**Marks**

- `job_regions`: Table.AddColumn with a table, expanded: CROSS JOIN with the distinct regions of `region_budgets` (Table.Distinct alone: SELECT DISTINCT).
- `numbered`: Table.AddIndexColumn after Table.Sort: ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC).
- `days_per_job`: `List.Count(List.Distinct([dt]))` is COUNT(DISTINCT dt). The Table.Sort after it has no FirstN or index, so the order is dropped; Hive holds no order.
- `unrun`: Table.NestedJoin LeftAnti on run_id and job_id: LEFT JOIN, then WHERE the joined key IS NULL; Table.Distinct: SELECT DISTINCT.
- `measures`: Table.UnpivotOtherColumns: one SELECT per column unpivoted, stacked with UNION ALL, each with WHERE the column IS NOT NULL, as M drops a null there. The blank avg_retry_secs on run 98 is dropped.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in each table name.

`job_regions`:

```sql
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) r
```

`numbered`:

```sql
SELECT run_id, dt, duration_mins,
  ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC) AS n
FROM <database>.job_runs
```

`days_per_job`:

```sql
SELECT job_id, COUNT(DISTINCT dt) AS days
FROM <database>.job_runs
GROUP BY job_id
```

`unrun`:

```sql
SELECT DISTINCT s.run_id, s.job_id
FROM <database>.scheduler_runs s
LEFT JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.job_id = r.job_id
WHERE r.run_id IS NULL
```

`measures`:

```sql
SELECT run_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X67

**Map**

- Sources: `job_runs` (typed run_id, job_id, duration_mins, dt); `jobs` (typed job_id, job_name, team, region); `run_alerts` (typed alert_id, run_id, severity, dt).
- Steps: `job_runs`'s formula columns (team, alerts, running_mins) are read by `by_team` and `noisy_runs`, so they are a step, `job_runs_step`, a CTE inside each final that reads it.
- Finals:
  - `by_team` (team, total_mins, alerted_runs). Its only typed column, team, is what its SUMIFS and COUNTIFS match on, so it is a summary: a GROUP BY of `job_runs_step`.
  - `noisy_runs` (run_id, team, alerts, running_mins), one query, loaded by the Power Query `noisy_runs`.
- Total Row: `by_team (Total Row)` has no query of its own. Its totals add up SUMs and a COUNT, so the `by_team` query ends `GROUP BY team WITH ROLLUP`; the rollup row (team NULL) is the Total Row.
- Parameters and Keys: none.

**Marks**

- `XLOOKUP(job_id, jobs[job_id], jobs[team])`: LEFT JOIN to `jobs`, then its team.
- `COUNTIF(run_alerts[run_id], run_id)`: LEFT JOIN to a count of run_alerts per run_id, COALESCE to 0.
- `SUMIFS` with `"<="&[@dt]`: a running total over job_id, ORDER BY dt, RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW, with ties included. COALESCE to 0.
- `COUNTIFS(team, ..., alerts, ">0")`: COUNT of CASE WHEN alerts > 0 in the GROUP BY, so a team with no alerted run gives 0.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in each table name.

`by_team`:

```sql
WITH job_runs_step AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt, j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
)
SELECT team,
  SUM(duration_mins) AS total_mins,
  COUNT(CASE WHEN alerts > 0 THEN 1 END) AS alerted_runs
FROM job_runs_step
GROUP BY team WITH ROLLUP
```

`noisy_runs`:

```sql
WITH job_runs_step AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt, j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
)
SELECT run_id, team, alerts, running_mins
FROM job_runs_step
WHERE alerts >= 2
```

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X68

**Map**

- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (typed job_id, job_name, team, region); `region_budgets` (typed job_id, budget_cents, region).
- Steps: `base`, the connection-only query, is read by `by_region` and `top_runs`, so it is a step: a CTE, `WITH base AS (...)`, inside each final that reads it.
- Finals:
  - `by_region` (region, total_mins, runs, share), loaded by the Power Query `by_region`. Its query reads `base` and keeps the groups with 2 or more runs (HAVING). `share` is `total_mins / SUM(total_mins) OVER ()`, worked out after the groups are made.
  - `top_runs` (run_id, job_name, region), one query, loaded by the Power Query `top_runs`.
- Total Row: `by_region (Total Row)`, a query of its own, one row, a column for total_mins only, no label. by_region is not a summary, so its Total Row is not a rollup.
- Parameters and Keys: none.

**Marks**

- `base`: the Inner join on job_id is JOIN to `jobs`; the LeftOuter join to `region_budgets` is LEFT JOIN, and region comes from it.
- `top_runs`: Table.Sort on duration_mins descending then run_id ascending, with Table.FirstN 2: ORDER BY ... LIMIT 2.
- `by_region`'s share is a window over the grouped rows, so `grouped` is a CTE that the window reads.

**Refused**

- None.

**Left alone**

- The Steps sheet (cells outside a Table, no calculation).

**To fill in**

- `<database>` in each table name.

`by_region`:

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
grouped AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT region, total_mins, runs,
  total_mins / SUM(total_mins) OVER () AS share
FROM grouped
```

`by_region (Total Row)`:

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
grouped AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT SUM(total_mins) AS total_mins
FROM grouped
```

`top_runs`:

```sql
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

Take out of the workbook what you don't want converted, fill in each `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.
