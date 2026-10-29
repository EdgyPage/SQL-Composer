date: 2026-10-29
arm: C
model: haiku
files: f80b90b

## X01

Map
- Sources: job_runs (typed run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours).
- Parameters and Keys: none.

```sql
SELECT run_id, job_id, duration_mins, dt,
  duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

- Typed over a formula: none.
- Marks: none. Refusals: none.
- Left alone: the Steps sheet, which holds no Table.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X02

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag).
- Parameters and Keys: none.

```sql
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF(duration_mins > 25 OR job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs
```

- Typed over a formula: none.
- Marks: none. The blank status on run 98 is not read by any formula, so it is not wrapped.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X03

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs).
- Parameters and Keys: none.

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

- Typed over a formula: none.
- Marks: blank. The status on run 98 is blank and score reads it, so it is wrapped as COALESCE(status, ''). The avg_retry_secs on run 98 is blank and mins_per_retry and total_secs read it, so it is wrapped as COALESCE(avg_retry_secs, 0).
- Refusals: none. The `_xlfn.` prefix is only Excel's and is dropped. SWITCH is written as a CASE with its two cases and an ELSE 0 default.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X04

Map
- Sources: jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd).
- Parameters and Keys: none.

```sql
SELECT job_id, job_name, team, region,
  CONCAT(CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-'), region) AS code,
  LENGTH(job_name) AS name_length,
  ROUND(job_id / 3, 2) AS third,
  PMOD(job_id, 2) AS odd
FROM <database>.jobs
```

- Typed over a formula: none.
- Marks: none. No blank in a column a formula reads.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X05

Map
- Sources: job_runs (typed run_id, dt); region_costs (typed job_id, cost_cents, region, dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month, days_since); region_costs (job_id, cost_cents, region, dt, day).
- Parameters and Keys: none.

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

- Typed over a formula: none.
- Marks: region_costs dt is held as text (such as 20260911), so day uses the text-date pattern rather than DATE(LEFT, MID, RIGHT). The day comes out as a yyyy-mm-dd string. DATE(2026,9,1) is written as '2026-09-01'.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X06

Map
- Sources: job_runs (typed run_id, job_id, duration_mins); jobs (typed job_id, job_name).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job).
- Parameters and Keys: none.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

- Typed over a formula: none.
- Marks: the COUNTIFS over its own Table is COUNT(*) over the job_id partition, with COALESCE. The XLOOKUP is a LEFT JOIN on job_id.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X07

Map
- Sources: job_runs (typed run_id, job_id, status); jobs (typed job_id, team, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, team, region).
- Parameters and Keys: none.

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

- Typed over a formula: none.
- Marks: none. The VLOOKUP (exact, column 3) gives team and the INDEX/MATCH gives region; one LEFT JOIN on job_id serves both. The blank status on run 98 is not read by a formula.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X08

Map
- Sources: job_runs (typed job_id, duration_mins, avg_retry_secs).
- Steps: none.
- Finals: by_job (job_id, total_mins, avg_retry, longest), a GROUP BY of job_runs, since by_job's only typed column is what its SUMIFS match on.
- Parameters and Keys: none.

```sql
SELECT job_id,
  COALESCE(SUM(duration_mins), 0) AS total_mins,
  AVG(avg_retry_secs) AS avg_retry,
  COALESCE(MAX(duration_mins), 0) AS longest
FROM <database>.job_runs
GROUP BY job_id
```

- Typed over a formula: none.
- Marks: the avg_retry_secs blank on run 98 is not wrapped. AVERAGEIFS is an -IFS form and AVG skips a NULL the same way, so the blank is skipped.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X09

Map
- Sources: job_runs (typed run_id, job_id, duration_mins, avg_retry_secs); jobs (typed job_id, team).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost).
- Parameters: none as a source. The XLOOKUP("rate") is written as its value, 0.5.
- Keys: job_runs holds run_id, which is what the typed-over cell matches on.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs, j.team,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.team), 0) AS team_mins,
  CASE WHEN r.run_id = 97 THEN 100
    ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5
  END AS cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

- Typed over a formula: cost on run 97 is 100, converted as CASE WHEN run_id = 97 THEN 100, matched on the Keys column run_id.
- Marks: blank. The avg_retry_secs on run 98 is blank and cost reads it, so it is wrapped as COALESCE(avg_retry_secs, 0).
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X10

Map
- Sources: job_runs (typed run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample).
- Parameters and Keys: none. The Keys Table has no row for job_runs, so the typed-over value matches on every typed column of its row.

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24' THEN 9
    ELSE duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

- Typed over a formula: hours on run 103 is 9. There is no Keys row for job_runs, so the match is on run_id, job_id, duration_mins and dt.
- Marks: none.
- Refusals: sample is RAND(), which changes on every recalculation, so it is NULL AS sample.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X11

Map
- Sources: job_runs (typed run_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, duration_mins, pick, scaled).
- Parameters and Keys: none.

```sql
SELECT run_id, duration_mins,
  NULL AS pick,
  NULL AS scaled
FROM <database>.job_runs
```

- Typed over a formula: none.
- Marks: none.
- Refusals: pick is INDIRECT (it also hangs on ROW()), so NULL AS pick. scaled reads the cell Summary!C2, a cell outside a Table that is not a defined name, so NULL AS scaled.
- Left alone: the cell Summary!C2 (value 3), and the bar chart on Summary.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X12

Map
- Sources: job_runs (typed run_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, duration_mins, running, loop, with_tax).
- Parameters and Keys: none.

```sql
SELECT run_id, duration_mins,
  NULL AS running,
  NULL AS loop,
  duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

- Typed over a formula: none.
- Marks: the defined name tax_rate is Summary!B3, a cell outside a Table, so its value 0.2 is used. Move tax_rate into Parameters.
- Refusals: running is SUM(OFFSET(...)), so NULL AS running. loop reads its own column, which is circular, so NULL AS loop.
- Left alone: the cell Summary!B3.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X13

Map
- Sources: job_runs (typed run_id, job_id); jobs (typed job_id, job_name).
- Steps: none.
- Finals: job_runs (run_id, job_id, name, doubled).
- Parameters and Keys: none.

```sql
SELECT r.run_id, r.job_id, j.job_name AS name,
  NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

- Typed over a formula: none.
- Marks: VLOOKUP with TRUE is approximate. It is converted to an exact LEFT JOIN on job_id, which is what the sample's job_id values need; the match was made exact, so say so and check it.
- Refusals: doubled uses DOUBLE, a defined name holding a LAMBDA formula, so NULL AS doubled.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X14

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: job_runs (hours), a step because by_job's SUMIFS reads its formula column hours. It is a CTE in by_job's query.
- Finals: by_job (job_id, total_hours), a GROUP BY over the step.
- Parameters and Keys: none.

```sql
WITH job_runs AS (
  SELECT job_id, duration_mins / 60 AS hours
  FROM <database>.job_runs
)
SELECT job_id, COALESCE(SUM(hours), 0) AS total_hours
FROM job_runs
GROUP BY job_id
```

- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the PivotTable on sheet Pivot, from job_runs, is left alone and not converted.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X15

Map
- Sources: tblRuns (typed Run ID, Job ID, Duration (mins)).
- Steps: none.
- Finals: tblRuns (Run ID, Job ID, Duration (mins), Hours).
- Parameters and Keys: none.
- Names: the Table name tblRuns is plain, so it is kept. The headers are not plain, so they are written as <run_id>, <job_id> and <duration_mins>. Hours is plain.

```sql
SELECT <run_id>, <job_id>, <duration_mins>,
  <duration_mins> / 60 AS hours
FROM <database>.tblRuns
```

- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`, and each of `<run_id>`, `<job_id>`, `<duration_mins>` with the real column name. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X16

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: long_runs (run_id, job_id, minutes, hours), the Table loaded by the Power Query "long_runs". Nothing reads it, so it is a final, and its query is the Power Query's steps.
- Parameters and Keys: none.

```sql
SELECT run_id, job_id, duration_mins AS minutes,
  duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X17

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: ok_runs, the connection-only query. It is read by ok_by_job, so it is a step and a CTE, not left out.
- Finals: ok_by_job (job_id, runs, total_mins), the Table loaded by the Power Query "ok_by_job".
- Parameters and Keys: none.

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

- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X18

Map
- Sources: job_runs (typed run_id, job_id, duration_mins); jobs (typed job_id, job_name).
- Steps: none.
- Finals: top_runs (run_id, job_name, duration_mins), the Table loaded by the Power Query "top_runs".
- Parameters and Keys: none.

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC
LIMIT 3
```

- Typed over a formula: none.
- Marks: the sort then FirstN 3 is ORDER BY with LIMIT 3. The NestedJoin with LeftOuter is a LEFT JOIN.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.

## X19

Map
- Sources: scheduler_runs (typed run_id, job_id, dt); <database>.job_runs, read from Sql.Database("dwh01", "ops") with Item job_runs. This source is not a workbook Table.
- Steps: none.
- Finals: all_runs (run_id, job_id, dt), the Table loaded by the Power Query "all_runs", a UNION ALL of the two sources.
- Parameters and Keys: none.
- Left out: the connection-only query "holidays" reads Web.Contents, a web source, so it is left out and named. Nothing reads it.

```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt
FROM <database>.job_runs
```

- Typed over a formula: none.
- Marks: check the second half. The Sql.Database source names server dwh01, database ops, schema ops and table job_runs. Check that the Hive table you fill in as `<database>.job_runs` is that same table.
- Refusals: the web source in "holidays" is refused and left out.
- Left alone: none.
- Fill in: `<database>`, in both halves. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive; its checked code wins where the two differ.
