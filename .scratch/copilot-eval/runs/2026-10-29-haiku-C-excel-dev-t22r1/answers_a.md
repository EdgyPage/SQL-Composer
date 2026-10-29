date: 2026-10-29
arm: C
model: haiku
files: fa48987

## X01

Sources: job_runs (run_id, job_id, duration_mins, dt).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours).
Typed over: none. Parameters and Keys: none.
Marks: none.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins, dt,
  duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X02

Sources: job_runs (run_id, job_id, status, duration_mins).
Steps: none.
Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag).
Typed over: none. Parameters and Keys: none.
Marks: none. The blank status at run 98 is not read by either formula, so it stays NULL.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF(duration_mins > 25 OR job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X03

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: none.
Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs).
Typed over: none. Parameters and Keys: none.
Marks: blank. Run 98 has a blank status and a blank avg_retry_secs, and formulas read both, so each is wrapped: COALESCE(status, '') in score and COALESCE(avg_retry_secs, 0) in mins_per_retry and total_secs. Excel reads the blank as 0 or "" in each case.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X04

Sources: jobs (job_id, job_name, team, region).
Steps: none.
Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd).
Typed over: none. Parameters and Keys: none.
Marks: none. MOD is converted as PMOD.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT job_id, job_name, team, region,
  CONCAT(CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-'), region) AS code,
  LENGTH(job_name) AS name_length,
  ROUND(job_id / 3, 2) AS third,
  PMOD(job_id, 2) AS odd
FROM <database>.jobs
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X05

Sources: job_runs (run_id, dt); region_costs (job_id, cost_cents, region, dt).
Steps: none.
Finals: job_runs (run_id, dt, month, days_since); region_costs (job_id, cost_cents, region, dt, day).
Typed over: none. Parameters and Keys: none.
Marks: blank. region_costs' dt is held as text (20260911), so day is built from its parts with CONCAT, and the date is held as text. Run 29 has a blank cost_cents; no formula reads it, so it stays NULL. DATE(2026,9,1) is written as '2026-09-01'.
Refused: none.
Left alone: none.
Fill in: `<database>`.

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

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X06

Sources: job_runs (run_id, job_id, duration_mins); jobs (job_id, job_name).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job).
Typed over: none. Parameters and Keys: none.
Marks: none. runs_of_job is COUNTIFS over its own Table on job_id, so it is a window count, with COALESCE.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X07

Sources: job_runs (run_id, job_id, status); jobs (job_id, team, region).
Steps: none.
Finals: job_runs (run_id, job_id, status, team, region).
Typed over: none. Parameters and Keys: none.
Marks: none. The blank status at run 98 is not read by a formula, so it stays NULL. team and region both come from one join on jobs, since they share the key.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X08

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: none.
Finals: by_job (job_id, total_mins, avg_retry, longest). Its only typed column is job_id, which its SUMIFS, AVERAGEIFS and MAXIFS match on, so by_job is a summary: a GROUP BY of job_runs.
Typed over: none. Parameters and Keys: none.
Marks: AVERAGEIFS becomes AVG and is left NULL where nothing matches. The blank avg_retry_secs at run 98 is skipped by AVG, as AVERAGEIFS skips it, so it is not wrapped.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT job_id,
  COALESCE(SUM(duration_mins), 0) AS total_mins,
  AVG(avg_retry_secs) AS avg_retry,
  COALESCE(MAX(duration_mins), 0) AS longest
FROM <database>.job_runs
GROUP BY job_id
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X09

Sources: job_runs (run_id, job_id, duration_mins, avg_retry_secs); jobs (job_id, team).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost).
Typed over: cost at run 97 is typed 100. Keys has a row for job_runs on run_id, so the row is matched on run_id = 97.
Parameters: rate is read from Parameters as 0.5, so XLOOKUP("rate", ...) becomes 0.5.
Marks: blank. Run 98 has a blank avg_retry_secs, which cost reads, so it is wrapped in COALESCE(avg_retry_secs, 0). team_mins is SUMIFS over its own Table on team, a window sum partitioned by team, with COALESCE.
Refused: none.
Left alone: none.
Fill in: `<database>`.

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

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X10

Sources: job_runs (run_id, job_id, duration_mins, dt).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample).
Typed over: hours at run 103 is typed 9. There is no Keys row for job_runs, so the row is matched on every typed column (run_id, job_id, duration_mins and dt).
Marks: none.
Refused: sample is RAND(), which is random and is refused, so it is NULL.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24' THEN 9
    ELSE duration_mins / 60
  END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X11

Sources: job_runs (run_id, duration_mins).
Steps: none.
Finals: job_runs (run_id, duration_mins, pick, scaled).
Typed over: none. Parameters and Keys: none.
Marks: none.
Refused: pick is INDIRECT and ROW(), which hang on the sheet's cells and row order, so it is NULL. scaled reads Summary!C2, a cell outside a Table that is not a defined name, so it is NULL.
Left alone: the bar chart, and cell C2 on sheet Summary (named above).
Fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  NULL AS pick,
  NULL AS scaled
FROM <database>.job_runs
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X12

Sources: job_runs (run_id, duration_mins).
Steps: none.
Finals: job_runs (run_id, duration_mins, running, loop, with_tax).
Typed over: none. Parameters and Keys: none.
Marks: tax_rate is a defined name for Summary!B3, a cell outside a Table, so its value 0.2 is used. Move it into Parameters.
Refused: running is SUM(OFFSET(...)) with ROW(), so it is NULL. loop reads its own column, which is circular, so it is NULL.
Left alone: the Summary sheet, except B3 as read above.
Fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  NULL AS running,
  NULL AS loop,
  duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X13

Sources: job_runs (run_id, job_id); jobs (job_id, job_name).
Steps: none.
Finals: job_runs (run_id, job_id, name, doubled).
Typed over: none. Parameters and Keys: none.
Marks: VLOOKUP with TRUE is approximate. It is converted as an exact match on job_id, and this gives the same rows here because every job_id in job_runs is in jobs.
Refused: doubled calls DOUBLE, a defined name holding a LAMBDA, so it is NULL.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, j.job_name AS name, NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X14

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: job_runs' hours column, which by_job reads. It is a CTE, job_runs_step, inside by_job's query.
Finals: by_job (job_id, total_hours). Its only typed column is job_id, so it is a summary: a GROUP BY of job_runs.
Typed over: none. Parameters and Keys: none.
Marks: none.
Refused: none.
Left alone: the PivotTable on sheet Pivot, from job_runs.
Fill in: `<database>`.

```sql
WITH job_runs_step AS (
  SELECT job_id, duration_mins / 60 AS hours
  FROM <database>.job_runs
)
SELECT job_id, COALESCE(SUM(hours), 0) AS total_hours
FROM job_runs_step
GROUP BY job_id
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X15

Sources: tblRuns (`<run_id>`, `<job_id>`, `<duration_mins>`). Headers Run ID, Job ID and Duration (mins) are not plain names, so each is in snake case in brackets.
Steps: none.
Finals: tblRuns (`<run_id>`, `<job_id>`, `<duration_mins>`, hours).
Typed over: none. Parameters and Keys: none.
Marks: none.
Refused: none.
Left alone: none.
Fill in: `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`.

```sql
SELECT <run_id>, <job_id>, <duration_mins>,
  <duration_mins> / 60 AS hours
FROM <database>.tblRuns
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X16

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: none. The query reads job_runs directly, and no Table reads long_runs.
Finals: long_runs (run_id, job_id, minutes, hours), from its Power Query's rows: job_runs with duration_mins above 15, run_id, job_id and duration_mins kept, hours = duration_mins / 60, and duration_mins renamed minutes.
Typed over: none. Parameters and Keys: none.
Marks: none.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins AS minutes,
  duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X17

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: ok_runs, the connection-only query, which ok_by_job reads. It is a CTE inside ok_by_job's query.
Finals: ok_by_job (job_id, runs, total_mins).
Typed over: none. Parameters and Keys: none.
Marks: the blank status at run 98 drops out of status = 'SUCCESS', as M's = drops it too.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
WITH ok_runs AS (
  SELECT job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X18

Sources: job_runs (run_id, job_id, duration_mins); jobs (job_id, job_name).
Steps: none.
Finals: top_runs (run_id, job_name, duration_mins), from its Power Query's rows: a left join to jobs, sorted by duration_mins descending, the first 3 kept.
Typed over: none. Parameters and Keys: none.
Marks: ties. Runs 97 and 103 both have 30 minutes, so the third row is one of them and Hive decides which. Add a second sort column if the order matters.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC
LIMIT 3
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X19

Sources: scheduler_runs (run_id, job_id, dt); job_runs, from the Sql.Database("dwh01", "ops") call, which is not in the workbook.
Steps: none.
Finals: all_runs (run_id, job_id, dt), the two sources stacked with UNION ALL, scheduler_runs first.
Typed over: none. Parameters and Keys: none.
Marks: Sql.Database reads the job_runs table of dwh01's ops database, which is the table used as `<database>.job_runs`. Check that `<database>.job_runs` is that table.
Refused: holidays reads Web.Contents, a web source, so it is left out.
Left alone: the holidays connection-only query (named above, left out).
Fill in: `<database>`.

```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt
FROM <database>.job_runs
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.

## X20

Sources: run_alerts (alert_id, run_id, severity, dt).
Steps: none. The query's filter, kept columns and count of 1 per row are steps inside the one query.
Finals: alert_pivot (run_id, high, low).
Typed over: none. Parameters and Keys: none.
Marks: Table.Pivot. The pivot's columns are now fixed at high and low, the values in the sample; a new severity would not get a column. n is 1 on each row, so the count is THEN 1. Runs without a high or low give NULL, as M leaves it.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT run_id,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
WHERE run_id = 97 OR run_id = 101
GROUP BY run_id
```

Take out of the workbook anything you don't want converted, fill in the `<...>`, and run `project.convert` on this Hive; its checked code wins where they differ.
