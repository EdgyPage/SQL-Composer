date: 2026-10-29
arm: C
model: haiku
files: 67b7e92

## X01

Map
- Sources: job_runs (typed run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours). Nothing reads it.
- Parameters and Keys: neither. Both are empty, so nothing is converted from them.
- Steps sheet: no Table, left alone.

Typed over a formula: none. Every row has the same formula, so no Keys row is needed.
Marks: none. Refused: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins, dt,
  duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

## X02

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag). Nothing reads it.
- Parameters and Keys: neither. Both are empty.
- Steps sheet: no Table, left alone.

Typed over a formula: none.
Marks: none. The blank status in run 98 is not read by a formula, so it stays NULL.
Refused: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF(duration_mins > 25 OR job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs
```

## X03

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs). Nothing reads it.
- Parameters and Keys: neither. Both are empty.
- Steps sheet: no Table, left alone.

Typed over a formula: none.
Marks:
- blank: status in run 98 is read by score, so it is wrapped as COALESCE(status, '').
- blank: avg_retry_secs in run 98 is read by mins_per_retry and total_secs, so it is wrapped as COALESCE(avg_retry_secs, 0).
- `_xlfn.SWITCH` becomes CASE, and the `_xlfn.` prefix is dropped.
- IFERROR(a / b, 0) becomes COALESCE(a / b, 0), with the blank wrapped inside the divisor.

Refused: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

## X04

Map
- Sources: jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd). Nothing reads it.
- Parameters and Keys: neither. Both are empty.
- Steps sheet: no Table, left alone.

Typed over a formula: none.
Marks: none. No blanks are read by a formula.
Refused: none.
Fill in: `<database>`.

```sql
SELECT job_id, job_name, team, region,
  CONCAT(CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-'), region) AS code,
  LENGTH(job_name) AS name_length,
  ROUND(job_id / 3, 2) AS third,
  PMOD(job_id, 2) AS odd
FROM <database>.jobs
```

## X05

Map
- Sources: job_runs (typed run_id, dt); region_costs (typed job_id, cost_cents, region, dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month, days_since); region_costs (job_id, cost_cents, region, dt, day). Nothing reads either.
- Parameters and Keys: neither. Both are empty.
- Steps sheet: no Table, left alone.

Typed over a formula: none.
Marks:
- region_costs dt is held as text in the form 20260911. The day formula is rebuilt as CONCAT of its parts, and the date is held as text.
- DATEDIF(DATE(2026,9,1), dt, "d") becomes DATEDIFF(dt, '2026-09-01').
- The blank cost_cents in run 29 of region_costs is not read by a formula, so it stays NULL.

Refused: none.
Fill in: `<database>` in both queries.

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

## X06

Map
- Sources: job_runs (typed run_id, job_id, duration_mins); jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job). Nothing reads it.
- Parameters and Keys: neither. Both are empty.
- Steps sheet: no Table, left alone.

Typed over a formula: none.
Marks:
- job_name is XLOOKUP on jobs, so it becomes a LEFT JOIN of jobs on job_id, taking job_name.
- runs_of_job is COUNTIFS over job_runs' own Table, so it is COUNT(*) OVER (PARTITION BY job_id).

Refused: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  j.job_name AS job_name,
  COUNT(*) OVER (PARTITION BY r.job_id) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

## X07

Map
- Sources: job_runs (typed run_id, job_id, status); jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, team, region). Nothing reads it.
- Parameters and Keys: neither. Both are empty.
- Steps sheet: no Table, left alone.

Typed over a formula: none.
Marks:
- team is VLOOKUP(job_id, jobs, 3, FALSE), an exact match, so it becomes a LEFT JOIN of jobs taking column 3 (team).
- region is INDEX/MATCH with 0, also exact, and takes the same join.
- The blank status in run 98 is not read by a formula, so it stays NULL.

Refused: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status,
  j.team AS team,
  j.region AS region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

## X08

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: by_job (job_id, total_mins, avg_retry, longest). Nothing reads it.
- Parameters and Keys: neither. Both are empty.
- Steps sheet: no Table, left alone.
- by_job is a summary: its only typed column, job_id, is what its SUMIFS, AVERAGEIFS and MAXIFS match on. It is a GROUP BY of job_runs.

Typed over a formula: none.
Marks:
- The blank avg_retry_secs in run 98 is skipped by AVG, as AVERAGEIFS skips it, so it is not wrapped.
- COALESCE is not needed in the GROUP BY, because each job_id group has rows.

Refused: none.
Fill in: `<database>`.

```sql
SELECT job_id,
  SUM(duration_mins) AS total_mins,
  AVG(avg_retry_secs) AS avg_retry,
  MAX(duration_mins) AS longest
FROM <database>.job_runs
GROUP BY job_id
```

## X09

Map
- Sources: job_runs (typed run_id, job_id, duration_mins, avg_retry_secs); jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost). Nothing reads it.
- Parameters: neither. The XLOOKUP on "rate" gives its value, 0.5.
- Keys: job_runs has run_id as its key column.
- Steps sheet: no Table, left alone.

Typed over a formula: cost in run 97 is typed as 100. The Keys row is job_runs run_id, so it becomes CASE WHEN run_id = 97 THEN 100.
Marks:
- blank: avg_retry_secs in run 98 is read by cost, so it is wrapped as COALESCE(avg_retry_secs, 0).
- team is XLOOKUP on jobs, so it becomes a LEFT JOIN of jobs on job_id.
- team_mins is SUMIFS over job_runs' own Table on team, so it is SUM(duration_mins) OVER (PARTITION BY team).
- The typed 100 is carried over as typed. The formula would give 904 for run 97, so check that value.

Refused: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs,
  j.team AS team,
  SUM(r.duration_mins) OVER (PARTITION BY j.team) AS team_mins,
  CASE WHEN r.run_id = 97 THEN 100
    ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5
  END AS cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

## X10

Map
- Sources: job_runs (typed run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample). Nothing reads it.
- Parameters and Keys: neither. Both are empty.
- Keys: there is no Keys row for job_runs.
- Steps sheet: no Table, left alone.

Typed over a formula: hours in run 103 is typed as 9. There is no Keys row for job_runs, so the match is on every typed column of that row: run_id 103, job_id 3, duration_mins 30 and dt '2026-09-24'.
Marks: the typed 9 differs from the formula's 0.5 (30 / 60). It is carried over as typed, so check it.
Refused: sample is RAND(), so it is NULL AS sample.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24' THEN 9
    ELSE duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

## X11

Map
- Sources: job_runs (typed run_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, duration_mins, pick, scaled). Nothing reads it.
- Parameters and Keys: neither. Both are empty.

Typed over a formula: none.
Refused:
- pick: INDIRECT, so NULL AS pick.
- scaled: a reference to a cell outside a Table, Summary!C2, which is not a defined name, so NULL AS scaled.

Left alone: cell Summary!C2 (outside a Table), the bar chart on the Summary sheet, and the Steps sheet (no Table).
Fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  NULL AS pick,
  NULL AS scaled
FROM <database>.job_runs
```

## X12

Map
- Sources: job_runs (typed run_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, duration_mins, running, loop, with_tax). Nothing reads it.
- Parameters and Keys: neither. Both are empty.

Typed over a formula: none.
Marks:
- tax_rate is a defined name for Summary!B3, a cell outside a Table. Its value, 0.2, is used, and tax_rate should be moved into Parameters.

Refused:
- running: OFFSET, so NULL AS running.
- loop: it reads its own column (circular), so NULL AS loop.

Left alone: the Summary sheet otherwise (no Table).
Fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  NULL AS running,
  NULL AS loop,
  duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

## X13

Map
- Sources: job_runs (typed run_id, job_id); jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, name, doubled). Nothing reads it.
- Parameters and Keys: neither. Both are empty.

Typed over a formula: none.
Marks:
- name is VLOOKUP(job_id, jobs, 2, TRUE). That is approximate. It is converted as an exact match, a LEFT JOIN of jobs on job_id taking column 2 (job_name). Check the results, since the Excel formula was approximate.

Refused:
- doubled: DOUBLE is a defined name holding a LAMBDA, so NULL AS doubled.

Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id,
  j.job_name AS name,
  NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

## X14

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: by_job (job_id, total_hours). Nothing reads it.
- Parameters and Keys: neither. Both are empty.
- by_job is a summary: its only typed column, job_id, is what its SUMIFS matches on. It is a GROUP BY of job_runs.
- Left alone: the PivotTable on the Pivot sheet, from job_runs.

Typed over a formula: none.
Marks: hours is duration_mins / 60, so SUMIFS over hours becomes SUM(duration_mins / 60). No blanks are read.
Refused: none.
Fill in: `<database>`.

```sql
SELECT job_id, SUM(duration_mins / 60) AS total_hours
FROM <database>.job_runs
GROUP BY job_id
```

## X15

Map
- Sources: tblRuns (typed Run ID, Job ID, Duration (mins)). The Table name tblRuns is a plain name, so it is kept.
- Steps: none.
- Finals: tblRuns (<run_id>, <job_id>, <duration_mins>, hours). Nothing reads it.

Typed over a formula: none.
Marks: the headers are not plain names, so they are snake case in brackets: Run ID is `<run_id>`, Job ID is `<job_id>`, Duration (mins) is `<duration_mins>`. Hours is a plain name.
Refused: none.
Fill in: `<database>`, `<run_id>`, `<job_id>` and `<duration_mins>`.

```sql
SELECT <run_id>, <job_id>, <duration_mins>,
  <duration_mins> / 60 AS hours
FROM <database>.tblRuns
```

## X16

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: long_runs (run_id, job_id, minutes, hours). It is loaded by the query long_runs, and nothing reads it.
- Parameters and Keys: neither. Both are empty.

Typed over a formula: none.
Marks, from the query:
- SelectColumns is the SELECT list.
- SelectRows, duration_mins > 15, is WHERE.
- AddColumn hours is duration_mins / 60 AS hours.
- RenameColumns, duration_mins to minutes, is AS minutes.

Refused: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins AS minutes, duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

## X17

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: ok_runs (connection-only query, read by ok_by_job), so it is a CTE.
- Finals: ok_by_job (job_id, runs, total_mins). It is loaded by the query ok_by_job, and nothing reads it.
- Parameters and Keys: neither. Both are empty.

Typed over a formula: none. The loaded values are the query's output.
Marks: none. The blank status in run 98 is dropped by WHERE status = 'SUCCESS', as M drops it.
Refused: none.
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

## X18

Map
- Sources: job_runs (typed run_id, job_id, duration_mins); jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: top_runs (run_id, job_name, duration_mins). It is loaded by the query top_runs, and nothing reads it.
- Parameters and Keys: neither. Both are empty.

Typed over a formula: none.
Marks, from the query:
- NestedJoin with LeftOuter is a LEFT JOIN.
- ExpandTableColumn job_name is j.job_name.
- Table.Sort descending is ORDER BY duration_mins DESC.
- FirstN 3 is LIMIT 3.
- Ties: runs 97 and 103 both have 30 minutes, so Hive may return either first. M kept the sort order.

Refused: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC
LIMIT 3
```

## X19

Map
- Sources: scheduler_runs (typed run_id, job_id, dt); job_runs, which the query reads from Sql.Database("dwh01", "ops") as table job_runs.
- Steps: none.
- Finals: all_runs (run_id, job_id, dt). It is loaded by the query all_runs, and nothing reads it.
- Parameters and Keys: neither. Both are empty.
- Left out: the holidays query. It reads Web.Contents from an online source, so it is left out. Nothing reads it.

Typed over a formula: none.
Marks:
- Table.Combine is UNION ALL, with scheduler_runs first.
- Sql.Database: the table it names is job_runs. Check that `<database>` is the database the M names, ops, and that job_runs is in it.

Refused: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt
FROM <database>.job_runs
```

## X20

Map
- Sources: run_alerts (typed alert_id, run_id, severity, dt).
- Steps: none.
- Finals: alert_pivot (run_id, high, low). It is loaded by the query alert_pivot, and nothing reads it.
- Parameters and Keys: neither. Both are empty.

Typed over a formula: none.
Marks, from the query:
- SelectRows, run_id = 97 or run_id = 101, is WHERE.
- Table.Pivot on severity, summing n, gives one column per severity value in the sample, high and low. Each is SUM(CASE WHEN severity = ... THEN 1 END), NULL where none, as M leaves it.
- The pivot's columns are now fixed: high and low. A new severity value needs a new column.

Refused: none.
Fill in: `<database>`.

```sql
SELECT run_id,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
WHERE run_id = 97 OR run_id = 101
GROUP BY run_id
```

## X41

Map
- Sources: job_runs (typed run_id, job_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, longest_first, job_shortest, job_total). Nothing reads it.
- Parameters and Keys: neither. Both are empty.

Typed over a formula: none.
Marks:
- RANK.EQ(duration_mins, all rows) is RANK() OVER (ORDER BY duration_mins DESC), largest first.
- MINIFS and SUMIF over job_runs' own Table are MIN and SUM OVER (PARTITION BY job_id). No COALESCE is needed, since each row matches its own job.

Refused: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins,
  RANK() OVER (ORDER BY duration_mins DESC) AS longest_first,
  MIN(duration_mins) OVER (PARTITION BY job_id) AS job_shortest,
  SUM(duration_mins) OVER (PARTITION BY job_id) AS job_total
FROM <database>.job_runs
```

## X42

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: jobs (job_id, job_name, runs, avg_mins, id_order). Nothing reads it.
- Parameters and Keys: neither. Both are empty.
- jobs is not a summary: its typed job_name is not matched on.

Typed over a formula: none.
Marks:
- runs is COUNTIF over job_runs, so it is a LEFT JOIN of a COUNT(*) subquery, with COALESCE(total, 0).
- avg_mins is IFERROR(AVERAGEIF(...), 0), so it is a LEFT JOIN of an AVG subquery, with COALESCE(avg_mins, 0) giving 0 where nothing matches.
- id_order is RANK.EQ(job_id, jobs[job_id], 1), ascending, so it is RANK() OVER (ORDER BY job_id).

Refused: none.
Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(c.total, 0) AS runs,
  COALESCE(a.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id) AS id_order
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS total
  FROM <database>.job_runs
  GROUP BY job_id
) c ON j.job_id = c.job_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) a ON j.job_id = a.job_id
```

## X43

Map
- Sources: job_runs (typed run_id, job_id, duration_mins, status, dt, and the rest); jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: busy_teams (team, runs, shortest, avg_mins), loaded by the query busy_teams; statuses (job_id, status), loaded by the query statuses. Nothing reads either.
- Parameters and Keys: neither. Both are empty.

Typed over a formula: none.
Marks, from the queries:
- busy_teams: NestedJoin with Inner is JOIN. Table.Group is GROUP BY team, with COUNT(*), MIN and AVG. SelectRows runs > 4 is HAVING COUNT(*) > 4.
- statuses: Table.Distinct alone is SELECT DISTINCT. The blank status for job 2 stays NULL, as the sample has it.

Refused: none.
Fill in: `<database>` in both.

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

## X44

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed job_id, job_name, team, region); scheduler_runs (typed run_id, job_id, dt).
- Steps: none.
- Finals: jobs_with_runs (run_id, job_name) and never_scheduled (job_id, job_name, team). Both are loaded by queries, and nothing reads them.
- Parameters and Keys: neither. Both are empty.

Typed over a formula: none.
Marks, from the queries:
- jobs_with_runs: RightOuter becomes LEFT JOIN with the tables swapped, so jobs is the kept table. cache_warm, with no run, shows NULL run_id, as the sample does.
- never_scheduled: LeftAnti becomes a LEFT JOIN of scheduler_runs with WHERE s.job_id IS NULL, keeping the first table's columns.

Refused: none.
Fill in: `<database>` in each.

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

## X45

Map
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); scheduler_runs (typed run_id, job_id, dt).
- Steps: none.
- Finals: run_days (run_id, dt) and matched (run_id, job_id, dt, status). Both are loaded by queries, and nothing reads them.
- Parameters and Keys: neither. Both are empty.

Typed over a formula: none.
Marks, from the queries:
- run_days: Table.Distinct of Table.Combine is UNION, which drops repeats.
- matched: NestedJoin with FullOuter is FULL OUTER JOIN. Run 99 is only in job_runs, so its run_id, job_id and dt are NULL, as the sample shows. Only status is expanded from job_runs.

Refused: none.
Fill in: `<database>` in each.

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
