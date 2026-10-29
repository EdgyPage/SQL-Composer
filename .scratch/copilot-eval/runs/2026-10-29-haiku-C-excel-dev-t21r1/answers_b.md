date: 2026-10-29
arm: C
model: haiku
files: aa75911

## X20

Map.
- Sources: run_alerts (alert_id, run_id, severity, dt), typed and read by the query below.
- Steps: none.
- Finals: alert_pivot (run_id, high, low), the Table loaded by Power Query "alert_pivot"; nothing reads it.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- Table.Pivot: one column per severity in the sample, high and low. The pivot's columns are now fixed; a new severity value would need a new column.
- The query adds n as 1 on every row, so List.Sum counts: THEN 1 in each CASE.
- NULL where none, as M leaves it.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

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

Map.
- Sources: job_runs (run_id, job_id, status, duration_mins), typed.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). Nothing else reads it, so it is a final, and its typed columns are its source.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- longest_first: RANK.EQ with no third argument is descending, so RANK() OVER (ORDER BY duration_mins DESC).
- shortest_ok: MINIFS is MIN over the condition status = 'SUCCESS', with COALESCE, as Excel gives 0 where nothing matches. The blank status on run 98 is skipped by the condition, so it is not wrapped.
- job_total: SUMIF over its own Table is SUM OVER the job_id partition, with COALESCE.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins,
  RANK() OVER (ORDER BY duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN status = 'SUCCESS' THEN duration_mins END) OVER (PARTITION BY job_id), 0) AS shortest_ok,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0) AS job_total
FROM <database>.job_runs
```

## X42

Map.
- Sources: job_runs (job_id, duration_mins), typed. It is read by jobs' formulas, so it is a source only.
- Sources also: jobs (job_id, job_name), typed.
- Steps: none.
- Finals: jobs (job_id, job_name, runs, avg_mins, id_order).
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- runs: COUNTIF over another Table is a LEFT JOIN to the counts per job_id, with COALESCE(.., 0), as Excel gives 0 where nothing matches.
- avg_mins: AVERAGEIF over another Table is AVG, left NULL. IFERROR(x, 0) is COALESCE(x, 0), as a divide by 0 is NULL.
- id_order: RANK.EQ with 1 as third argument is ascending, so RANK() OVER (ORDER BY job_id ASC).
- Blank cells on job_runs (status and avg_retry_secs, run 98) are not read by a formula here, so nothing is wrapped.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(b.runs, 0) AS runs,
  COALESCE(b.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS runs, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) b ON j.job_id = b.job_id
```

## X43

Map.
- Sources: job_runs (run_id, job_id, status, duration_mins), typed; jobs (job_id, team), typed.
- Steps: none.
- Finals: busy_teams (team, runs, shortest, avg_mins), loaded by Power Query "busy_teams"; statuses (job_id, status), loaded by Power Query "statuses". Nothing reads either Table.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- busy_teams: Inner join is JOIN. Table.Group is COUNT(*), MIN and AVG, and the filter runs > 4 is HAVING COUNT(*) > 4.
- statuses: Table.Distinct with no column list is SELECT DISTINCT. The blank status on run 98 is kept as a row, as M keeps it.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

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

Map.
- Sources: job_runs (run_id, job_id), typed; jobs (job_id, job_name, team), typed; scheduler_runs (job_id), typed.
- Steps: none.
- Finals: jobs_with_runs (run_id, job_name), loaded by Power Query "jobs_with_runs"; never_scheduled (job_id, job_name, team), loaded by Power Query "never_scheduled". Nothing reads either Table.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- jobs_with_runs: JoinKind.RightOuter is a LEFT JOIN with the two tables swapped, so every job is kept. cache_warm has no run, so its run_id is NULL (the blank row in the sample).
- never_scheduled: JoinKind.LeftAnti is a LEFT JOIN with WHERE on the joined table's key IS NULL, and only jobs' columns are kept. Only cache_warm has no scheduler run.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

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

Map.
- Sources: job_runs (run_id, dt, status), typed; scheduler_runs (run_id, job_id, dt), typed.
- Steps: none.
- Finals: run_days (run_id, dt), loaded by Power Query "run_days"; matched (run_id, job_id, dt, status), loaded by Power Query "matched". Nothing reads either Table.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- run_days: Table.Combine then Table.Distinct is UNION, which drops repeated rows.
- matched: JoinKind.FullOuter is FULL OUTER JOIN. Run 99 is only in job_runs, so its scheduler columns are NULL, as in the sample's blank row. The blank status on run 98 is kept.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

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

## X51

Map.
- Sources: job_runs (run_id, job_id, status, duration_mins, dt), typed.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins). Nothing reads it.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- long_in_job: COUNTIFS over its own Table with job_id and duration_mins > 15, as a COUNT with a CASE, per job_id, with COALESCE.
- not_ok: COUNTIFS "<>SUCCESS" is the form (status <> 'SUCCESS' OR status IS NULL), as Excel counts the blank on run 98. It counts over the whole column, so OVER (), with COALESCE.
- failed_in_job: "*ail*" is LOWER(status) LIKE '%ail%', as Excel ignores case, per job_id, with COALESCE.
- running_mins: SUMIFS with job_id and "<="&dt over its own Table is a running total per job_id, ties included: SUM OVER the job_id partition ordered by dt, RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW, with COALESCE.
- The blank status on run 98 is read by not_ok and failed_in_job, both in -IFS forms, so it is not wrapped.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins, dt,
  COALESCE(COUNT(CASE WHEN duration_mins > 15 THEN 1 END) OVER (PARTITION BY job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (status <> 'SUCCESS' OR status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY job_id), 0) AS failed_in_job,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs
```

## X52

Map.
- Sources: job_runs (run_id, job_id, duration_mins), typed.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job). Nothing reads it.
- Finals, Total Row: job_runs (Total Row) (duration_mins, share), a query of its own.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- share: SUM(job_runs[duration_mins]) over the whole column is SUM OVER ().
- vs_avg: AVERAGE over the whole column is AVG OVER ().
- rank_in_job: COUNTIFS ">"&duration plus 1, per job_id, is RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC).
- Total Row: SUBTOTAL(109) is SUM for duration_mins and share, in that order, with no label. It is not a summary Table, so it has its own query. A window cannot sit inside an aggregate, so share is worked out in a CTE first.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

```sql
WITH shares AS (
  SELECT duration_mins,
    duration_mins / SUM(duration_mins) OVER () AS share
  FROM <database>.job_runs
)
SELECT SUM(duration_mins) AS duration_mins, SUM(share) AS share
FROM shares
```

## X53

Map.
- Sources: job_runs (job_id, duration_mins), typed.
- Steps: none.
- Finals: by_job (job_id, total_mins, runs, longest). by_job's typed column is job_id, which its SUMIFS and COUNTIFS match on, so it is a summary: a GROUP BY of job_runs.
- Finals, Total Row: none of its own. Its totals are SUMs and a MAX of MAXes, so the summary's query ends GROUP BY job_id WITH ROLLUP, and the Total is the rollup row with job_id NULL.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- The GROUP BY lists the job_ids in job_runs. Excel gives 0 for a job_id with no runs; in this sample each by_job job_id has runs, so no zero case arises.
- MAXIFS is MAX.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT job_id,
  SUM(duration_mins) AS total_mins,
  COUNT(*) AS runs,
  MAX(duration_mins) AS longest
FROM <database>.job_runs
GROUP BY job_id WITH ROLLUP
```

## X54

Map.
- Sources: job_runs (run_id, dt), typed; scheduler_runs (run_id, job_id, dt), typed.
- Steps: none.
- Finals: job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label). Nothing reads it.
- Finals: scheduler_runs (run_id, job_id, dt). No formula reads it, so it is a final with no formula, copied as it stands.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- a_month_on: EDATE is ADD_MONTHS, and a month's end stays one, so a date on the last day of a month stays on the last day of the target month.
- week_of: the Monday start, d - WEEKDAY(d, 2) + 1, is written as in the week-start form, CAST(NEXT_DAY(DATE_ADD(d, 7 * -1), 'MO') AS STRING).
- month_of: DATE(YEAR(d), MONTH(d), 1) is written as CAST(TRUNC(d, 'MM') AS STRING).
- weekday: WEEKDAY(d) is DAYOFWEEK(d).
- label: TEXT(d, "yyyy-mm") is DATE_FORMAT(dt, 'yyyy-MM').

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

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

```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
```

## X55

Map.
- Sources: jobs (job_id, job_name, team, region), typed.
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens). Nothing reads it.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- title: PROPER(SUBSTITUTE(job_name, "_", " ")) is INITCAP(REPLACE(job_name, '_', ' ')).
- tag: TEXTJOIN("/", TRUE, team, region) is CONCAT_WS('/', team, region), which skips a blank.
- code: CONCATENATE is CONCAT.
- has_sync: ISNUMBER(SEARCH("SYNC", job_name)) is INSTR(LOWER(job_name), 'sync') > 0, as Excel ignores case.
- tens: VALUE(job_id & "0") is CAST(CONCAT(job_id, '0') AS DOUBLE).

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT job_id, job_name, team, region,
  INITCAP(REPLACE(job_name, '_', ' ')) AS title,
  CONCAT_WS('/', team, region) AS tag,
  CONCAT(region, '-', job_id) AS code,
  INSTR(LOWER(job_name), 'sync') > 0 AS has_sync,
  CAST(CONCAT(job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs
```

## X56

Map.
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs), typed; scheduler_runs (run_id, dt), typed, read by scheduled_on.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on). Nothing reads it.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- no_status: ISBLANK(status) is status IS NULL. Not wrapped.
- weeks: INT is FLOOR.
- at_least_20: MAX of one row's cells is GREATEST.
- spread: STDEV.S is STDDEV_SAMP, over the whole column.
- weighted: SUMPRODUCT is SUM of the product over the whole column. The blank avg_retry_secs on run 98 is wrapped as COALESCE(avg_retry_secs, 0), as the formula reads it. Blank.
- scheduled_on: XLOOKUP is a LEFT JOIN on run_id, with the fourth argument as COALESCE. The date is held with 'unscheduled', a text, so dt is CAST to STRING. Run 99 has no scheduler run, so it reads unscheduled.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT j.run_id, j.job_id, j.status, j.duration_mins, j.avg_retry_secs,
  j.status IS NULL AS no_status,
  FLOOR(j.duration_mins / 7) AS weeks,
  GREATEST(j.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(j.duration_mins) OVER () AS spread,
  SUM(j.duration_mins * COALESCE(j.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(CAST(s.dt AS STRING), 'unscheduled') AS scheduled_on
FROM <database>.job_runs j
LEFT JOIN <database>.scheduler_runs s ON j.run_id = s.run_id
```

## X57

Map.
- Sources: job_runs (run_id, job_id, status, avg_retry_secs), typed; jobs (job_id, job_name, team, region), typed.
- Steps: none.
- Finals: picked (run_id, job_id, status, avg_retry_secs, status_lc), loaded by Power Query "picked"; ran_jobs (job_id, job_name, team, region), loaded by Power Query "ran_jobs". Nothing reads either Table.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- picked: List.Contains({1, 2}, job_id) is job_id IN (1, 2). [status] = null is status IS NULL, and Text.StartsWith is LIKE 'S%', case kept.
- picked: Table.ReplaceValue null to 0 on avg_retry_secs is COALESCE(avg_retry_secs, 0). The blank on run 98 becomes 0.
- picked: Text.Lower is LOWER, so the blank status on run 98 gives a blank status_lc.
- ran_jobs: List.Contains(job_runs job_id, job_id) for a row whose key is in another table is LEFT SEMI JOIN. Text.Contains "a" is LIKE '%a%', case kept.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, COALESCE(avg_retry_secs, 0) AS avg_retry_secs, LOWER(status) AS status_lc
FROM <database>.job_runs
WHERE job_id IN (1, 2) AND (status IS NULL OR status LIKE 'S%')
```

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r ON r.job_id = j.job_id
WHERE j.job_name LIKE '%a%'
```

## X58

Map.
- Sources: job_runs (run_id, job_id, duration_mins, dt), typed; jobs (job_id), typed; scheduler_runs (run_id, job_id), typed; region_budgets (region), typed.
- Steps: none.
- Finals: job_regions (job_id, region), loaded by Power Query "job_regions"; numbered (run_id, dt, duration_mins, n), loaded by "numbered"; days_per_job (job_id, days), loaded by "days_per_job"; unrun (run_id, job_id), loaded by "unrun"; measures (run_id, measure, amount), loaded by "measures". Nothing reads these Tables.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- job_regions: Table.AddColumn with each Regions, expanded, is CROSS JOIN with the distinct regions of region_budgets.
- numbered: Table.Sort then Table.AddIndexColumn is ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC). The sample order matches.
- days_per_job: List.Count(List.Distinct(dt)) is COUNT(DISTINCT dt). Table.Sort by days with no FirstN or index after it: no ORDER BY, as a Hive table holds no order, so the order was dropped.
- unrun: NestedJoin on every column of scheduler_runs's key pair, LeftAnti, then Table.Distinct, is EXCEPT.
- measures: Table.UnpivotOtherColumns is one SELECT per column unpivoted, stacked with UNION ALL, each with WHERE ... IS NOT NULL, as M drops the blank avg_retry_secs on run 98.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) r
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

## X67

Map.
- Sources: job_runs (run_id, job_id, duration_mins, dt), typed; jobs (job_id, team), typed; run_alerts (run_id), typed.
- Steps: job_runs, its formula columns team, alerts and running_mins, read by by_team and noisy_runs. It is a CTE, job_runs_calc, in each final that reads it.
- Finals: by_team (team, total_mins, alerted_runs), a summary: its typed column is team, which its SUMIFS and COUNTIFS match on. noisy_runs (run_id, team, alerts, running_mins), loaded by Power Query "noisy_runs".
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- team: XLOOKUP is a LEFT JOIN to jobs on job_id.
- alerts: COUNTIF over another Table is a LEFT JOIN to the counts per run_id, with COALESCE(.., 0).
- running_mins: SUMIFS with job_id and "<="&dt is a running total per job_id, ties included: RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW, with COALESCE.
- by_team: COUNTIFS ">0" is a CASE. Its Total Row sums only, so the summary ends GROUP BY team WITH ROLLUP; the Total is the row with team NULL.
- noisy_runs: [alerts] >= 2 is WHERE alerts >= 2.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
WITH job_runs_calc AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (
    SELECT run_id, COUNT(*) AS alerts
    FROM <database>.run_alerts
    GROUP BY run_id
  ) a ON r.run_id = a.run_id
)
SELECT team,
  SUM(duration_mins) AS total_mins,
  COUNT(CASE WHEN alerts > 0 THEN 1 END) AS alerted_runs
FROM job_runs_calc
GROUP BY team WITH ROLLUP
```

```sql
WITH job_runs_calc AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (
    SELECT run_id, COUNT(*) AS alerts
    FROM <database>.run_alerts
    GROUP BY run_id
  ) a ON r.run_id = a.run_id
)
SELECT run_id, team, alerts, running_mins
FROM job_runs_calc
WHERE alerts >= 2
```

## X68

Map.
- Sources: job_runs (run_id, job_id, duration_mins), typed; jobs (job_id, job_name), typed; region_budgets (job_id, region), typed.
- Steps: base, the connection-only query. Two queries read it, so it is a step, a CTE, in each final's query that reads it. It is not left out.
- Finals: by_region (region, total_mins, runs, share), loaded by Power Query "by_region"; its Total Row, by_region (Total Row) (total_mins), a query of its own; top_runs (run_id, job_name, region), loaded by Power Query "top_runs".
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- base: Inner NestedJoin is JOIN; LeftOuter is LEFT JOIN.
- by_region: Table.Group is SUM and COUNT(*); the filter runs >= 2 is HAVING COUNT(*) >= 2.
- share: total_mins / SUM(total_mins) over the Table is SUM OVER (). It is computed in an outer SELECT, since a window cannot sit in the same SELECT as its GROUP BY.
- by_region (Total Row): SUBTOTAL(109) is SUM for total_mins, with no label. It is a query of its own.
- top_runs: Table.Sort then FirstN is ORDER BY duration_mins DESC, run_id ASC LIMIT 2.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
WITH base AS (
  SELECT r.run_id, r.duration_mins, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT region, total_mins, runs,
  total_mins / SUM(total_mins) OVER () AS share
FROM (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) by_region
```

```sql
WITH base AS (
  SELECT r.run_id, r.duration_mins, j.job_name, b.region
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
SELECT SUM(total_mins) AS total_mins
FROM by_region
```

```sql
WITH base AS (
  SELECT r.run_id, r.duration_mins, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT run_id, job_name, region
FROM base
ORDER BY duration_mins DESC, run_id ASC
LIMIT 2
```

## X71

Map.
- Sources: job_runs (run_id, job_id, status, duration_mins), typed.
- Steps: ok_runs, the query loaded by Power Query "ok_runs"; ok_by_job reads it, so it is a CTE in each final that reads it.
- Finals: ok_runs (run_id, job_id, duration_mins, hours). The Table is nothing-read, so it is a final: the query plus the hours formula.
- Finals: ok_by_job (job_id, total_mins), loaded by Power Query "ok_by_job".
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- ok_runs: [status] = "SUCCESS" is status = 'SUCCESS'. The blank status on run 98 is not kept, as M leaves it out.
- hours: [duration_mins]/60 is duration_mins / 60.
- ok_by_job: Table.Group with List.Sum is GROUP BY job_id with SUM.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT run_id, job_id, duration_mins,
  duration_mins / 60 AS hours
FROM ok_runs
```

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT job_id, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

## X72

Map.
- Sources: job_runs (job_id, duration_mins), typed; jobs (job_id, job_name, team), typed.
- Steps: jobs, its formula columns runs and total. It is read by by_team and busy_jobs, so it is a CTE, jobs_calc, in each final that reads it.
- Finals: by_team (team, team_total). Its typed column is team, which its SUMIFS matches on, so it is a summary: a GROUP BY of jobs. It has no Total Row.
- Finals: busy_jobs (job_id, job_name, runs), loaded by Power Query "busy_jobs".
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- runs: COUNTIF over another Table is a LEFT JOIN to the counts per job_id, with COALESCE(.., 0).
- total: SUMIF over another Table is a LEFT JOIN to the sums per job_id, with COALESCE(.., 0), as Excel gives 0 where nothing matches. Job 4 has no runs, so it gives 0.
- by_team: SUMIFS over jobs[total] by team is SUM grouped by team. The rows are data, finance and web.
- busy_jobs: [runs] >= 3 is WHERE runs >= 3.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
WITH jobs_calc AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(c.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total
    FROM <database>.job_runs
    GROUP BY job_id
  ) c ON j.job_id = c.job_id
)
SELECT team, SUM(total) AS team_total
FROM jobs_calc
GROUP BY team
```

```sql
WITH jobs_calc AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(c.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total
    FROM <database>.job_runs
    GROUP BY job_id
  ) c ON j.job_id = c.job_id
)
SELECT job_id, job_name, runs
FROM jobs_calc
WHERE runs >= 3
```
