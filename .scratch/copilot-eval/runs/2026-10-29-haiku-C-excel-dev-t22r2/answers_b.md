date: 2026-10-29
arm: C
model: haiku
files: 423bc80

## X41

Map
- Sources: job_runs (run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total).
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins,
  RANK() OVER (ORDER BY r.duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN r.status = 'SUCCESS' THEN r.duration_mins END) OVER (PARTITION BY r.job_id), 0) AS shortest_ok,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id), 0) AS job_total
FROM <database>.job_runs r
```

Marks
- status is blank in run 98. It is read inside the MINIFS condition, so it is not wrapped; that row matches no SUCCESS, as Excel does.
- shortest_ok and job_total are wrapped in COALESCE(..., 0), as Excel gives 0 where nothing matches.

## X42

Map
- Sources: job_runs (job_id, duration_mins); jobs (job_id, job_name).
- Steps: none.
- Finals: jobs (job_id, job_name, runs, avg_mins, id_order).
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS runs, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) c ON j.job_id = c.job_id
```

Marks
- avg_mins is IFERROR(AVERAGEIF(...), 0), so it is COALESCE(..., 0). No blank is read by a formula in the sample.
- id_order is RANK.EQ with 1 as its third argument, so it ranks ascending.

## X43

Map
- Sources: job_runs (job_id, status, duration_mins); jobs (job_id, team).
- Steps: none.
- Finals: busy_teams (team, runs, shortest, avg_mins), the Table loaded by its Power Query; statuses (job_id, status), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

busy_teams:

```sql
SELECT j.team,
  COUNT(*) AS runs,
  MIN(r.duration_mins) AS shortest,
  AVG(r.duration_mins) AS avg_mins
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.team
HAVING COUNT(*) > 4
```

statuses:

```sql
SELECT DISTINCT r.job_id, r.status
FROM <database>.job_runs r
```

Marks
- The inner join to jobs is the Power Query's Table.NestedJoin with JoinKind.Inner, so a run with no job is dropped.
- statuses keeps the blank status of job 2 as a NULL row, as Table.Distinct does.

## X44

Map
- Sources: job_runs (run_id, job_id); jobs (job_id, job_name, team); scheduler_runs (job_id).
- Steps: none.
- Finals: jobs_with_runs (run_id, job_name), the Table loaded by its Power Query; never_scheduled (job_id, job_name, team), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

jobs_with_runs:

```sql
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON j.job_id = r.job_id
```

never_scheduled:

```sql
SELECT j.job_id, j.job_name, j.team
FROM <database>.jobs j
LEFT JOIN <database>.scheduler_runs s ON j.job_id = s.job_id
WHERE s.job_id IS NULL
```

Marks
- The RightOuter join keeps every job, as LEFT JOIN with the tables swapped does. cache_warm (job 4) has no run, so its run_id is NULL, as in the sample.
- never_scheduled is the LeftAnti join: jobs' columns only.

## X45

Map
- Sources: job_runs (run_id, dt, status); scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: run_days (run_id, dt), the Table loaded by its Power Query; matched (run_id, job_id, dt, status), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

run_days:

```sql
SELECT run_id, dt FROM <database>.job_runs
UNION
SELECT run_id, dt FROM <database>.scheduler_runs
```

matched:

```sql
SELECT s.run_id, s.job_id, s.dt, r.status
FROM <database>.scheduler_runs s
FULL OUTER JOIN <database>.job_runs r ON s.run_id = r.run_id
```

Marks
- run_days is UNION, not UNION ALL, because Table.Distinct wraps Table.Combine.
- matched is a FULL OUTER JOIN. Run 99, only in job_runs, has NULL run_id, job_id and dt; run 100, only in scheduler_runs, has a NULL status, as in the sample.

## X51

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins).
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.dt,
  COALESCE(COUNT(CASE WHEN r.duration_mins > 15 THEN 1 END) OVER (PARTITION BY r.job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (r.status <> 'SUCCESS' OR r.status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(r.status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY r.job_id), 0) AS failed_in_job,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs r
```

Marks
- not_ok: "<>SUCCESS" is written as (status <> 'SUCCESS' OR status IS NULL), so the blank status in run 98 is counted, as Excel counts a blank there. status is not wrapped in COALESCE, as it sits inside a COUNTIFS form.
- failed_in_job: "*ail*" is LOWER(status) LIKE '%ail%', as Excel ignores case.
- running_mins: the running total within each job, with ties on dt included, as Excel's "<=" does.

## X52

Map
- Sources: job_runs (run_id, job_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job).
- Total Row: job_runs (Total Row), a query of its own: one row, the total of duration_mins and the total of share, in order, with no label.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

job_runs:

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  r.duration_mins / SUM(r.duration_mins) OVER () AS share,
  r.duration_mins - AVG(r.duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY r.job_id ORDER BY r.duration_mins DESC) AS rank_in_job
FROM <database>.job_runs r
```

job_runs (Total Row):

```sql
WITH shares AS (
  SELECT r.duration_mins,
    r.duration_mins / SUM(r.duration_mins) OVER () AS share
  FROM <database>.job_runs r
)
SELECT SUM(duration_mins) AS duration_mins,
  SUM(share) AS share
FROM shares
```

Marks
- whole-column references in share and vs_avg are OVER (), as the Excel formulas use the whole column.
- rank_in_job: COUNTIFS(... ">" ...) + 1 is RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC), so tied durations share a rank, as Excel does.

## X53

Map
- Sources: job_runs (job_id, duration_mins).
- Steps: none.
- Finals: by_job (job_id, total_mins, runs, longest). by_job is a summary, since its only typed column, job_id, is what its SUMIFS and COUNTIFS match on, so it is a GROUP BY of job_runs.
- Total Row: no query of its own. Its totals add up SUMs and COUNTs and take the MAX, so the summary's query ends GROUP BY ... WITH ROLLUP. The total is the row whose job_id is NULL.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT r.job_id,
  COALESCE(SUM(r.duration_mins), 0) AS total_mins,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(MAX(r.duration_mins), 0) AS longest
FROM <database>.job_runs r
GROUP BY r.job_id WITH ROLLUP
```

Marks
- The summary's rows are the job_ids that have runs in job_runs. A job with no runs gets no row, where Excel would show 0 for it.

## X54

Map
- Sources: job_runs (run_id, dt); scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label); scheduler_runs (run_id, job_id, dt). scheduler_runs has no formulas and nothing reads it, so its final is the table as it stands.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

job_runs:

```sql
SELECT r.run_id, r.dt,
  LAST_DAY(r.dt) AS month_end,
  ADD_MONTHS(r.dt, 1) AS a_month_on,
  DATE_ADD(r.dt, 7) AS due,
  CAST(NEXT_DAY(DATE_ADD(r.dt, 7 * -1), 'MO') AS STRING) AS week_of,
  CAST(TRUNC(r.dt, 'MM') AS STRING) AS month_of,
  DAYOFWEEK(r.dt) AS weekday,
  DATE_FORMAT(r.dt, 'yyyy-MM') AS label
FROM <database>.job_runs r
```

scheduler_runs:

```sql
SELECT s.run_id, s.job_id, s.dt
FROM <database>.scheduler_runs s
```

Marks
- a_month_on: EDATE is ADD_MONTHS, which keeps a month's end at the month's end, as EDATE does.
- week_of and month_of are cast to text, as the Hive form writes them.

## X55

Map
- Sources: jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens).
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team, j.region,
  INITCAP(REPLACE(j.job_name, '_', ' ')) AS title,
  CONCAT_WS('/', j.team, j.region) AS tag,
  CONCAT(j.region, '-', j.job_id) AS code,
  INSTR(LOWER(j.job_name), LOWER('SYNC')) > 0 AS has_sync,
  CAST(CONCAT(j.job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs j
```

Marks
- None: no blank is read in the sample. TEXTJOIN with TRUE is CONCAT_WS, which skips NULLs.

## X56

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs); scheduler_runs (run_id, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on).
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  r.status IS NULL AS no_status,
  FLOOR(r.duration_mins / 7) AS weeks,
  GREATEST(r.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(r.duration_mins) OVER () AS spread,
  SUM(r.duration_mins * COALESCE(r.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(sr.dt, 'unscheduled') AS scheduled_on
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs sr ON r.run_id = sr.run_id
```

Marks
- avg_retry_secs is blank in run 98, and weighted reads it, so it is wrapped: COALESCE(avg_retry_secs, 0) (blank).
- scheduled_on: XLOOKUP is a LEFT JOIN on run_id, and its fourth argument is COALESCE. Run 99 is not in scheduler_runs, so it reads "unscheduled".
- weeks: INT is FLOOR.

## X57

Map
- Sources: job_runs (run_id, job_id, status, avg_retry_secs); jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: picked (run_id, job_id, status, avg_retry_secs, status_lc), the Table loaded by its Power Query; ran_jobs (job_id, job_name, team, region), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

picked:

```sql
SELECT r.run_id, r.job_id, r.status,
  COALESCE(r.avg_retry_secs, 0) AS avg_retry_secs,
  LOWER(r.status) AS status_lc
FROM <database>.job_runs r
WHERE r.job_id IN (1, 2) AND (r.status IS NULL OR r.status LIKE 'S%')
```

ran_jobs:

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r ON r.job_id = j.job_id
WHERE j.job_name LIKE '%a%'
```

Marks
- avg_retry_secs is blank in run 98, and Table.ReplaceValue sets it to 0: COALESCE(avg_retry_secs, 0) (blank).
- Text.StartsWith is LIKE 'S%' with the case kept. The M test "status = null" is status IS NULL, so the blank row stays; status_lc is NULL there, as Text.Lower gives null.
- List.Contains(Runs[job_id], [job_id]) is a LEFT SEMI JOIN, which keeps jobs' columns only.

## X58

Map
- Sources: job_runs (run_id, job_id, duration_mins, avg_retry_secs, dt); jobs (job_id); region_budgets (region); scheduler_runs (run_id, job_id).
- Steps: none.
- Finals: job_regions (job_id, region); numbered (run_id, dt, duration_mins, n); days_per_job (job_id, days); unrun (run_id, job_id); measures (run_id, measure, amount). Each is a Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

job_regions:

```sql
WITH regions AS (
  SELECT DISTINCT region FROM <database>.region_budgets
)
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN regions r
```

numbered:

```sql
SELECT r.run_id, r.dt, r.duration_mins,
  ROW_NUMBER() OVER (ORDER BY r.duration_mins DESC, r.run_id ASC) AS n
FROM <database>.job_runs r
```

days_per_job:

```sql
SELECT r.job_id, COUNT(DISTINCT r.dt) AS days
FROM <database>.job_runs r
GROUP BY r.job_id
```

unrun:

```sql
SELECT DISTINCT s.run_id, s.job_id
FROM <database>.scheduler_runs s
LEFT JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.job_id = r.job_id
WHERE r.run_id IS NULL
```

measures:

```sql
SELECT r.run_id, 'duration_mins' AS measure, r.duration_mins AS amount
FROM <database>.job_runs r
WHERE r.duration_mins IS NOT NULL
UNION ALL
SELECT r.run_id, 'avg_retry_secs' AS measure, r.avg_retry_secs AS amount
FROM <database>.job_runs r
WHERE r.avg_retry_secs IS NOT NULL
```

Marks
- days_per_job: the sort by days descending has no FirstN or index after it, so there is no ORDER BY. The order was dropped.
- measures: the blank avg_retry_secs of run 98 is dropped, as M drops a null there.
- job_regions is a CROSS JOIN of every job with each distinct region.

## X67

Map
- Sources: job_runs (run_id, job_id, duration_mins, dt); jobs (job_id, team); run_alerts (run_id).
- Steps: job_runs, the Table's formula columns team, alerts and running_mins. It is read by by_team and noisy_runs, so each of their queries has it as a CTE.
- Finals: by_team (team, total_mins, alerted_runs); noisy_runs (run_id, team, alerts, running_mins).
- Total Row: by_team (Total Row) is the WITH ROLLUP row, whose team is NULL. It needs no query of its own.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

by_team:

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
)
SELECT team,
  COALESCE(SUM(duration_mins), 0) AS total_mins,
  COALESCE(COUNT(CASE WHEN alerts > 0 THEN 1 END), 0) AS alerted_runs
FROM job_runs
GROUP BY team WITH ROLLUP
```

noisy_runs:

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
)
SELECT run_id, team, alerts, running_mins
FROM job_runs
WHERE alerts >= 2
```

Marks
- alerts: COUNTIF over run_alerts is a LEFT JOIN to a count per run, wrapped in COALESCE(..., 0).
- running_mins: the running total within each job, ties on dt included.
- by_team: web has no run in job_runs, so it gets no row, where Excel would show 0 for it.

## X68

Map
- Sources: job_runs (run_id, job_id, duration_mins); jobs (job_id, job_name); region_budgets (job_id, region).
- Steps: base, the connection-only Power Query. by_region and top_runs read it, so each of their queries has it as a CTE. It is not loaded to a Table.
- Finals: by_region (region, total_mins, runs, share), the Table loaded by its Power Query; top_runs (run_id, job_name, region), the Table loaded by its Power Query.
- Total Row: by_region (Total Row), a query of its own: one row, the total of total_mins, with no label.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

by_region:

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT g.region, g.total_mins, g.runs,
  g.total_mins / SUM(g.total_mins) OVER () AS share
FROM (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) g
```

by_region (Total Row):

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT SUM(g.total_mins) AS total_mins
FROM (
  SELECT region, SUM(duration_mins) AS total_mins
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) g
```

top_runs:

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

Marks
- The Total Row is not a summary, so it gets its own query. Its total is SUM over the by_region rows.
- top_runs sorts by duration_mins descending, then run_id ascending for ties, and takes the first 2.

## X71

Map
- Sources: job_runs (run_id, job_id, status, duration_mins).
- Steps: ok_runs, the Power Query's rows with its formula column hours. It is read by ok_by_job, so ok_by_job's query has it as a CTE.
- Finals: ok_by_job (job_id, total_mins), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
WITH ok_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins,
    r.duration_mins / 60 AS hours
  FROM <database>.job_runs r
  WHERE r.status = 'SUCCESS'
)
SELECT job_id, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

Marks
- None. The blank status of run 98 is not SUCCESS, so it drops out, as the M equality does.

## X72

Map
- Sources: job_runs (job_id, duration_mins); jobs (job_id, job_name, team).
- Steps: jobs, the Table's formula columns runs and total. It is read by by_team and busy_jobs, so each of their queries has it as a CTE.
- Finals: by_team (team, team_total), a summary: its only typed column, team, is what its SUMIFS matches, so it is a GROUP BY of jobs. busy_jobs (job_id, job_name, runs), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

by_team:

```sql
WITH jobs AS (
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
SELECT team, COALESCE(SUM(total), 0) AS team_total
FROM jobs
GROUP BY team
```

busy_jobs:

```sql
WITH jobs AS (
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
FROM jobs
WHERE runs >= 3
```

Marks
- The COUNTIF and SUMIF over job_runs are one LEFT JOIN to a count and a sum per job, each wrapped in COALESCE(..., 0).

## X75

Map
- Sources: job_runs (run_id, dt, duration_mins).
- Steps: long_runs, the Power Query's rows with its formula column over. It is read by long_per_day, so that query has it as a CTE.
- Finals: long_per_day (dt, runs), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
WITH long_runs AS (
  SELECT r.run_id, r.dt, r.duration_mins,
    r.duration_mins - 15 AS over
  FROM <database>.job_runs r
  WHERE r.duration_mins >= 15
)
SELECT dt, COUNT(*) AS runs
FROM long_runs
GROUP BY dt
```

Marks
- None. Run 98, at exactly 15 minutes, is kept by >= 15, as M keeps it.

## X76

Map
- Sources: jobs (job_id, job_name, team); job_runs (run_id, job_id, duration_mins).
- Steps: finance_jobs, the Power Query's rows with its formula column label. It is read by finance_runs, so that query has it as a CTE.
- Finals: finance_runs (run_id, job_name, duration_mins), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
WITH finance_jobs AS (
  SELECT j.job_id, j.job_name,
    UPPER(j.job_name) AS label
  FROM <database>.jobs j
  WHERE j.team = 'finance'
)
SELECT r.run_id, f.job_name, r.duration_mins
FROM <database>.job_runs r
JOIN finance_jobs f ON r.job_id = f.job_id
```

Marks
- None. The NestedJoin is JoinKind.Inner, so it is a JOIN, and a run whose job is not in finance is dropped.
