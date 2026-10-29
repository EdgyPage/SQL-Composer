date: 2026-10-29
arm: C
model: haiku
files: 5df4678

## X01

Map
- Sources: job_runs (typed columns run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs, one query, with columns run_id, job_id, duration_mins, dt, duration_hours.
- Parameters and Keys are empty, so none.

Marks: none. No value is typed over a formula, and no blank is read by a formula.
Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
  r.duration_mins / 60 AS duration_hours
FROM <database>.job_runs r
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X02

Map
- Sources: job_runs (typed columns run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs, one query, with columns run_id, job_id, status, duration_mins, slow_job1, flag.
- Parameters and Keys are empty, so none.

Marks: none. No value is typed over a formula. The blank status in row 98 is read by no formula, so it stays NULL.
Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins,
  (r.duration_mins > 10 AND r.job_id = 1) AS slow_job1,
  IF(r.duration_mins > 25 OR r.job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs r
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X03

Map
- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: job_runs, one query, with columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs.
- Parameters and Keys are empty, so none.

Marks
- Blank: status in row 98 is a blank that the score formula reads, so it is wrapped as COALESCE(status, '').
- Blank: avg_retry_secs in row 98 is a blank that two formulas read, so it is wrapped as COALESCE(avg_retry_secs, 0).
- IFERROR(a / b, 0) becomes COALESCE(a / b, 0), as a divide by 0 is NULL in Hive.
- _xlfn.SWITCH with two pairs becomes CASE, and the _xlfn. prefix is dropped.

Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
  CASE COALESCE(r.status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(r.duration_mins / COALESCE(r.avg_retry_secs, 0), 0) AS mins_per_retry,
  r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs r
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X04

Map
- Sources: none. The jobs Table is read by nothing, so it is a final.
- Steps: none.
- Finals: jobs, one query, with columns job_id, job_name, team, region, code, name_length, third, odd.
- Parameters and Keys are empty, so none.

Marks: none. No value is typed over a formula, and no blank is read by a formula.
Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team, j.region,
  CONCAT(UPPER(SUBSTR(j.job_name, 1, 3)), '-', j.region) AS code,
  LENGTH(j.job_name) AS name_length,
  ROUND(j.job_id / 3, 2) AS third,
  PMOD(j.job_id, 2) AS odd
FROM <database>.jobs j
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X05

Map
- Sources: job_runs (typed columns run_id, dt); region_costs (typed columns job_id, cost_cents, region, dt).
- Steps: none.
- Finals: job_runs, with columns run_id, dt, month, days_since; region_costs, with columns job_id, cost_cents, region, dt, day.
- Parameters and Keys are empty, so none.

Marks
- region_costs dt is a date held as text, such as 20260911. The day column uses CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) in place of DATE(LEFT, MID, RIGHT).
- DATEDIF(DATE(2026,9,1), dt, "d") becomes DATEDIFF(dt, '2026-09-01').
- The blank cost_cents in row 29 of region_costs is no formula's input, so it stays NULL.

Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

job_runs final:

```sql
SELECT r.run_id, r.dt,
  MONTH(r.dt) AS month,
  DATEDIFF(r.dt, '2026-09-01') AS days_since
FROM <database>.job_runs r
```

region_costs final:

```sql
SELECT rc.job_id, rc.cost_cents, rc.region, rc.dt,
  CONCAT(SUBSTR(rc.dt, 1, 4), '-', SUBSTR(rc.dt, 5, 2), '-', SUBSTR(rc.dt, 7, 2)) AS day
FROM <database>.region_costs rc
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X06

Map
- Sources: job_runs (typed columns run_id, job_id, duration_mins); jobs (typed columns job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs, one query, with columns run_id, job_id, duration_mins, job_name, runs_of_job.
- Parameters and Keys are empty, so none.

Marks: none. No value is typed over a formula, and no blank is read by a formula. COUNTIFS over its own Table is COUNT(*) OVER (PARTITION BY job_id), wrapped in COALESCE.
Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X07

Map
- Sources: job_runs (typed columns run_id, job_id, status); jobs (typed columns job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs, one query, with columns run_id, job_id, status, team, region.
- Parameters and Keys are empty, so none.

Marks: none. VLOOKUP(..., jobs, 3, FALSE) and INDEX/MATCH with 0 are both exact, so both become one LEFT JOIN on jobs, taking team (column 3) and region. No blank is read by a formula.
Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X08

Map
- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt). It is read by by_job, and has no formula, so it is not a step or a final.
- Steps: none.
- Finals: by_job, a summary, one GROUP BY query over job_runs, with columns job_id, total_mins, avg_retry, longest. Its only typed column is job_id, which SUMIFS and MAXIFS match on.
- Parameters and Keys are empty, so none.

Marks
- The blank avg_retry_secs in row 98 is skipped, as AVERAGEIFS skips a blank and AVG skips NULL. No wrap, and no mention of a COALESCE for it.
- SUMIFS and MAXIFS are wrapped in COALESCE(.., 0), as Excel gives 0 where nothing matches.
- AVERAGEIFS stays NULL where nothing matches.

Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT r.job_id,
  COALESCE(SUM(r.duration_mins), 0) AS total_mins,
  AVG(r.avg_retry_secs) AS avg_retry,
  COALESCE(MAX(r.duration_mins), 0) AS longest
FROM <database>.job_runs r
GROUP BY r.job_id
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X09

Map
- Sources: job_runs (typed columns run_id, job_id, duration_mins, avg_retry_secs); jobs (typed columns job_id, job_name, team, region), read by the team formula.
- Steps: none. team_mins reads team in the same Table, so it is a window over the same query.
- Finals: job_runs, one query, with columns run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost.
- Parameters: the rate row (rate = 0.5). Keys: job_runs, run_id.

Typed over
- cost in run_id 97 is typed as 100. It matches the row on the Keys column run_id.

Marks
- The blank avg_retry_secs in row 98 is wrapped as COALESCE(avg_retry_secs, 0) in cost.
- XLOOKUP("rate", Parameters[name], Parameters[value]) is written as its value, 0.5.
- team, XLOOKUP on jobs, becomes a LEFT JOIN on jobs, taking team.
- team_mins, SUMIFS over its own Table matched on team, becomes SUM(duration_mins) OVER (PARTITION BY team), wrapped in COALESCE.

Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs,
  j.team,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.team), 0) AS team_mins,
  CASE WHEN r.run_id = 97 THEN 100
    ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5 END AS cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X10

Map
- Sources: job_runs (typed columns run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs, one query, with columns run_id, job_id, duration_mins, dt, hours, sample.
- Parameters and Keys are empty, so none. There is no Keys row for job_runs.

Typed over
- hours in run 103 is typed as 9. There is no Keys row for job_runs, so the row matches on every typed column of the row: run_id 103, job_id 3, duration_mins 30 and dt '2026-09-24'.

Marks: none beyond the typed-over value above.
Refused
- sample: RAND() is random on every calculation, so it is refused and written as NULL AS sample.

Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
  CASE WHEN r.run_id = 103 AND r.job_id = 3 AND r.duration_mins = 30 AND r.dt = '2026-09-24' THEN 9
    ELSE r.duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs r
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X11

Map
- Sources: job_runs (typed columns run_id, duration_mins).
- Steps: none.
- Finals: job_runs, one query, with columns run_id, duration_mins, pick, scaled.
- Parameters and Keys are empty, so none.

Marks: none.
Refused
- pick: INDIRECT("B"&ROW()) uses INDIRECT and ROW(), so it is written as NULL AS pick.
- scaled: it reads cell C2 on the Summary sheet, a cell outside a Table, by its address, so it is written as NULL AS scaled.

Left alone: the bar chart on the Summary sheet, and the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.duration_mins,
  NULL AS pick,
  NULL AS scaled
FROM <database>.job_runs r
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X12

Map
- Sources: job_runs (typed columns run_id, duration_mins).
- Steps: none.
- Finals: job_runs, one query, with columns run_id, duration_mins, running, loop, with_tax.
- Parameters and Keys are empty, so none.

Marks
- tax_rate is a defined name for Summary!$B$3, a cell outside a Table. Its value, 0.2, is used in with_tax, and the user should move it into Parameters.

Refused
- running: SUM(OFFSET(..., ROW()-1, ...)) uses OFFSET and ROW(), so it is written as NULL AS running.
- loop: it reads its own column, loop + 1, which is circular, so it is written as NULL AS loop.

Left alone: the Steps sheet, which holds cells outside a Table. The Summary sheet's B3 is named above and left as its value.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.duration_mins,
  NULL AS running,
  NULL AS loop,
  r.duration_mins * 0.2 AS with_tax
FROM <database>.job_runs r
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X13

Map
- Sources: job_runs (typed columns run_id, job_id); jobs (typed columns job_id, job_name, team, region), read by the name formula.
- Steps: none.
- Finals: job_runs, one query, with columns run_id, job_id, name, doubled.
- Parameters and Keys are empty, so none.

Marks
- name: VLOOKUP(job_id, jobs, 2, TRUE) is approximate. It is converted as an exact LEFT JOIN on jobs, taking job_name, as the user asked for an exact match, and the change is named here.

Refused
- doubled: DOUBLE is a defined name holding a LAMBDA, so it is written as NULL AS doubled.

Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, j.job_name AS name,
  NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X14

Map
- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: job_runs, the Table with the hours formula, which by_job reads as job_runs[hours]. It becomes a CTE in by_job's query.
- Finals: by_job, a summary, one GROUP BY query over the step, with columns job_id, total_hours. Its only typed column is job_id, which SUMIFS matches on.
- Parameters and Keys are empty, so none.

Marks: none. The blanks in status and avg_retry_secs are read by no formula, so they stay NULL.
Refused: none.
Left alone: the PivotTable on sheet Pivot, which is from job_runs, and the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
WITH job_runs AS (
  SELECT r.job_id, r.duration_mins / 60 AS hours
  FROM <database>.job_runs r
)
SELECT job_id, COALESCE(SUM(hours), 0) AS total_hours
FROM job_runs
GROUP BY job_id
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X15

Map
- Sources: tblRuns (typed columns Run ID, Job ID, Duration (mins)).
- Steps: none.
- Finals: tblRuns, one query, with columns Run ID, Job ID, Duration (mins), Hours.
- Parameters and Keys are empty, so none.

Marks
- Names: the Table name tblRuns is a plain name, so it stays. The headers that are not plain names become snake case in brackets: Run ID is `<run_id>`, Job ID is `<job_id>`, and Duration (mins) is `<duration_mins>`. Hours is plain.
- Hours: [@[Duration (mins)]]/60 becomes duration / 60.

Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`, `<run_id>`, `<job_id>` and `<duration_mins>`.

```sql
SELECT t.<run_id>, t.<job_id>, t.<duration_mins>,
  t.<duration_mins> / 60 AS hours
FROM <database>.tblRuns t
```

Next: take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X16

Map
- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt). The long_runs query reads it.
- Steps: none.
- Finals: long_runs, the query's rows, with columns run_id, job_id, minutes, hours. Nothing reads the Table, so it is a final.
- Parameters and Keys are empty, so none.

Marks
- The Table long_runs is loaded by its query, so it is not a source. Its final is the query's rows.
- Table.SelectRows with [duration_mins] > 15 becomes WHERE duration_mins > 15.
- Table.AddColumn hours = [duration_mins] / 60 becomes duration_mins / 60 AS hours.
- Table.RenameColumns duration_mins to minutes becomes AS minutes.

Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins AS minutes,
  r.duration_mins / 60 AS hours
FROM <database>.job_runs r
WHERE r.duration_mins > 15
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X17

Map
- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: ok_runs, the connection-only query that ok_by_job reads. It becomes a CTE in ok_by_job's query.
- Finals: ok_by_job, the query's rows, one query, with columns job_id, runs, total_mins. Nothing reads the Table, so it is a final.
- Parameters and Keys are empty, so none.

Marks
- Table.Group with Table.RowCount becomes COUNT(*) AS runs. List.Sum becomes SUM AS total_mins.
- The M filter [status] = "SUCCESS" becomes status = 'SUCCESS'. The blank status in row 98 is not SUCCESS, so it is dropped, as M drops it.

Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
WITH ok_runs AS (
  SELECT r.job_id, r.duration_mins
  FROM <database>.job_runs r
  WHERE r.status = 'SUCCESS'
)
SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X18

Map
- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed columns job_id, job_name, team, region).
- Steps: none.
- Finals: top_runs, the query's rows, with columns run_id, job_name, duration_mins.
- Parameters and Keys are empty, so none.

Marks
- Table.NestedJoin with JoinKind.LeftOuter becomes LEFT JOIN jobs, expanded to job_name.
- Table.Sort descending, then Table.FirstN 3, becomes ORDER BY duration_mins DESC LIMIT 3.
- The two runs of 30 minutes tie. The top 3 holds both, but Hive does not fix the order between them.

Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC
LIMIT 3
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X19

Map
- Sources: scheduler_runs (typed columns run_id, job_id, dt); job_runs, the table the Sql.Database query names. Its M is Sql.Database("dwh01", "ops") with Item "job_runs", so the source is the job_runs table in <database>.
- Steps: none.
- Finals: all_runs, the query's rows, with columns run_id, job_id, dt. Nothing reads the Table, so it is a final.
- Left out: the connection-only query holidays. Nothing reads it, and its source is Web.Contents, a web source, which is refused.
- Parameters and Keys are empty, so none.

Marks
- Sql.Database: the table it names, job_runs, is used. Please check that <database> holds job_runs, as the query names server dwh01 and database ops.
- Table.Combine({Scheduled, RunsKept}) becomes UNION ALL. Table.SelectColumns keeps run_id, job_id and dt.

Refused
- holidays: Web.Contents is a web source, so the query is left out and named.

Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT s.run_id, s.job_id, s.dt
FROM <database>.scheduler_runs s
UNION ALL
SELECT r.run_id, r.job_id, r.dt
FROM <database>.job_runs r
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.

## X20

Map
- Sources: run_alerts (typed columns alert_id, run_id, severity, dt). The alert_pivot query reads it.
- Steps: none.
- Finals: alert_pivot, the query's rows after the pivot, with columns run_id, high, low. Nothing reads the Table, so it is a final.
- Parameters and Keys are empty, so none.

Marks
- Table.SelectRows [run_id] = 97 or [run_id] = 101 becomes WHERE run_id = 97 OR run_id = 101.
- Table.Pivot over the values in the sample, high then low, becomes a SUM(CASE WHEN severity = 'high' THEN 1 END) AS high column and a SUM(CASE WHEN severity = 'low' THEN 1 END) AS low column. The count of 1 per row is the THEN 1. NULL shows where a run has no value, as M leaves it.
- The pivot's columns are now fixed to high and low. A new severity value would need a new column.

Refused: none.
Left alone: the Steps sheet, which holds cells outside a Table.
Fill in: `<database>`.

```sql
SELECT a.run_id,
  SUM(CASE WHEN a.severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN a.severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts a
WHERE a.run_id = 97 OR a.run_id = 101
GROUP BY a.run_id
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive. Its checked code wins where the two differ. I can write the Toolbox code next if you ask for it.
