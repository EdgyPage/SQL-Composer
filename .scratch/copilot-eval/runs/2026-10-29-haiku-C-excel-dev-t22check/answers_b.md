date: 2026-10-29
arm: C
model: haiku
files: 5df4678

## X41

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total).
- Parameters and Keys: both empty, so none.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins,
  RANK() OVER (ORDER BY r.duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN r.status = 'SUCCESS' THEN r.duration_mins END) OVER (PARTITION BY r.job_id), 0) AS shortest_ok,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id), 0) AS job_total
FROM <database>.job_runs r
```

- Typed over a formula: none.
- Marks: the blank status in run 98 is read only inside MINIFS, which skips it, so it is not wrapped.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X42

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt; no formulas of its own, read by jobs' formulas); jobs (typed job_id, job_name).
- Steps: none.
- Finals: jobs (job_id, job_name, runs, avg_mins, id_order).
- Parameters and Keys: both empty, so none.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(a.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id) AS id_order
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins FROM <database>.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

- Typed over a formula: none.
- Marks: avg_mins is IFERROR(AVERAGEIF(...), 0). AVG is left NULL where no run matches, and IFERROR's 0 becomes COALESCE(..., 0). The blanks in run 98 are read by no formula, so nothing is wrapped.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X43

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: busy_teams (team, runs, shortest, avg_mins), from its Power Query; statuses (job_id, status), from its Power Query.
- Parameters and Keys: both empty, so none.

```sql
-- busy_teams
SELECT j.team,
  COUNT(*) AS runs,
  MIN(r.duration_mins) AS shortest,
  AVG(r.duration_mins) AS avg_mins
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.team
HAVING COUNT(*) > 4
```

```sql
-- statuses
SELECT DISTINCT job_id, status
FROM <database>.job_runs
```

- Typed over a formula: none.
- Marks: the blank status of job 2 (row 4 of statuses) is kept as NULL by DISTINCT.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X44

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed job_id, job_name, team, region); scheduler_runs (typed run_id, job_id, dt).
- Steps: none.
- Finals: jobs_with_runs (run_id, job_name), from its Power Query; never_scheduled (job_id, job_name, team), from its Power Query.
- Parameters and Keys: both empty, so none.

```sql
-- jobs_with_runs
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON r.job_id = j.job_id
```

```sql
-- never_scheduled
SELECT j.job_id, j.job_name, j.team
FROM <database>.jobs j
LEFT JOIN <database>.scheduler_runs s ON s.job_id = j.job_id
WHERE s.job_id IS NULL
```

- Typed over a formula: none.
- Marks: the RightOuter join is written as LEFT JOIN with the two tables swapped, so every job keeps a row. cache_warm has no run, so its run_id is NULL, as the sample shows. The LeftAnti join is a LEFT JOIN with WHERE ... IS NULL and keeps jobs' columns only.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X45

**Map**
- Sources: job_runs (typed run_id, job_id, status, dt); scheduler_runs (typed run_id, job_id, dt).
- Steps: none.
- Finals: run_days (run_id, dt), from its Power Query; matched (run_id, job_id, dt, status), from its Power Query.
- Parameters and Keys: both empty, so none.

```sql
-- run_days
SELECT run_id, dt FROM <database>.job_runs
UNION
SELECT run_id, dt FROM <database>.scheduler_runs
```

```sql
-- matched
SELECT s.run_id, s.job_id, s.dt, r.status
FROM <database>.scheduler_runs s
FULL OUTER JOIN <database>.job_runs r ON s.run_id = r.run_id
```

- Typed over a formula: none.
- Marks: Table.Distinct over Table.Combine is UNION, which drops repeats. In matched, run 99 has only a job_runs row, so its run_id, job_id and dt are NULL, since the query expands only status from job_runs; the blank status of run 98 and of run 100 stays NULL.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X51

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins).
- Parameters and Keys: both empty, so none.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.dt,
  COALESCE(COUNT(CASE WHEN r.duration_mins > 15 THEN 1 END) OVER (PARTITION BY r.job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (r.status <> 'SUCCESS' OR r.status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(r.status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY r.job_id), 0) AS failed_in_job,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs r
```

- Typed over a formula: none.
- Marks: the blank status in run 98 is not wrapped, because it sits inside COUNTIFS forms. not_ok counts it through its IS NULL, as Excel's "<>" counts a blank. running_mins uses RANGE, so ties on the same dt are included, as Excel's "<=" does.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X52

**Map**
- Sources: job_runs (typed run_id, job_id, duration_mins).
- Steps: job_runs' share, read by its Total Row, is a CTE inside the Total Row's query.
- Finals: job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job); job_runs (Total Row) (duration_mins, share), one row, no label.
- Parameters and Keys: both empty, so none.

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  r.duration_mins / SUM(r.duration_mins) OVER () AS share,
  r.duration_mins - AVG(r.duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY r.job_id ORDER BY r.duration_mins DESC) AS rank_in_job
FROM <database>.job_runs r
```

```sql
-- job_runs (Total Row)
WITH job_runs AS (
  SELECT r.duration_mins, r.duration_mins / SUM(r.duration_mins) OVER () AS share
  FROM <database>.job_runs r
)
SELECT SUM(duration_mins) AS duration_mins, SUM(share) AS share
FROM job_runs
```

- Typed over a formula: none.
- Marks: the Total row's "Total" label is left out, as the Total Row has no label column. rank_in_job's COUNTIFS(... ">" ...) + 1 becomes RANK(), so the two 30s in job 3 both rank 1, as Excel gives.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X53

**Map**
- Sources: job_runs (typed job_id, duration_mins; read by by_job's formulas, with no formulas of its own).
- Steps: none.
- Finals: by_job (job_id, total_mins, runs, longest), a summary, with its Total Row folded in.
- Parameters and Keys: both empty, so none.

```sql
SELECT job_id,
  COALESCE(SUM(duration_mins), 0) AS total_mins,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(MAX(duration_mins), 0) AS longest
FROM <database>.job_runs
GROUP BY job_id WITH ROLLUP
```

- Typed over a formula: none.
- Marks: by_job is a summary, since its only typed column, job_id, is what its SUMIFS, COUNTIFS and MAXIFS match on, so its query is a GROUP BY of job_runs. Its Total Row needs no query of its own: SUBTOTAL 109 adds SUMs and COUNTs and SUBTOTAL 104 takes a MAX of MAXes, so WITH ROLLUP adds the total as one more row, with a NULL job_id (a Subtotal row). The "Total" label is left out.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X54

**Map**
- Sources: job_runs (typed run_id, dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label).
- Parameters and Keys: both empty, so none.

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

- Typed over a formula: none.
- Marks: a_month_on, EDATE(dt, 1), is ADD_MONTHS; marked, a month's end stays a month's end. week_of and month_of are written as the start of the week and month, as text.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X55

**Map**
- Sources: jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens).
- Parameters and Keys: both empty, so none.

```sql
SELECT j.job_id, j.job_name, j.team, j.region,
  INITCAP(REPLACE(j.job_name, '_', ' ')) AS title,
  CONCAT_WS('/', j.team, j.region) AS tag,
  CONCAT(j.region, '-', j.job_id) AS code,
  INSTR(LOWER(j.job_name), LOWER('SYNC')) > 0 AS has_sync,
  CAST(CONCAT(j.job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs j
```

- Typed over a formula: none.
- Marks: none. SEARCH ignores case, so both sides are lowered.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X56

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs); scheduler_runs (typed run_id, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on).
- Parameters and Keys: both empty, so none.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  r.status IS NULL AS no_status,
  FLOOR(r.duration_mins / 7) AS weeks,
  GREATEST(r.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(r.duration_mins) OVER () AS spread,
  SUM(r.duration_mins * COALESCE(r.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(s.dt, 'unscheduled') AS scheduled_on
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs s ON s.run_id = r.run_id
```

- Typed over a formula: none.
- Marks: the blank avg_retry_secs in run 98 is read by weighted, a SUMPRODUCT, which is not an IF(S) form, so it is wrapped: COALESCE(avg_retry_secs, 0), and that blank is named. The blank status in run 98 is read only by ISBLANK, so it is not wrapped. scheduled_on takes XLOOKUP's fourth argument as COALESCE, so run 99, which has no scheduler row, reads 'unscheduled' and the column is text.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X57

**Map**
- Sources: job_runs (typed run_id, job_id, status, avg_retry_secs, duration_mins, dt); jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: picked (run_id, job_id, status, avg_retry_secs, status_lc), from its Power Query; ran_jobs (job_id, job_name, team, region), from its Power Query.
- Parameters and Keys: both empty, so none.

```sql
-- picked
SELECT r.run_id, r.job_id, r.status,
  COALESCE(r.avg_retry_secs, 0) AS avg_retry_secs,
  LOWER(r.status) AS status_lc
FROM <database>.job_runs r
WHERE r.job_id IN (1, 2) AND (r.status IS NULL OR r.status LIKE 'S%')
```

```sql
-- ran_jobs
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r ON r.job_id = j.job_id
WHERE j.job_name LIKE '%a%'
```

- Typed over a formula: none.
- Marks: the blank avg_retry_secs in run 98 is filled by Table.ReplaceValue, so it is wrapped: COALESCE(avg_retry_secs, 0). The blank status in run 98 is kept as NULL, and its status_lc is NULL too. Text.StartsWith and Text.Contains keep case, so LIKE 'S%' and LIKE '%a%' are case-sensitive.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X58

**Map**
- Sources: jobs (typed job_id); job_runs (typed run_id, job_id, duration_mins, dt); scheduler_runs (typed run_id, job_id, dt); region_budgets (typed job_id, budget_cents, region).
- Steps: none.
- Finals: job_regions (job_id, region); numbered (run_id, dt, duration_mins, n); days_per_job (job_id, days); unrun (run_id, job_id); measures (run_id, measure, amount).
- Parameters and Keys: both empty, so none.

```sql
-- job_regions
SELECT j.job_id, rg.region
FROM <database>.jobs j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) rg
```

```sql
-- numbered
SELECT r.run_id, r.dt, r.duration_mins,
  ROW_NUMBER() OVER (ORDER BY r.duration_mins DESC, r.run_id ASC) AS n
FROM <database>.job_runs r
```

```sql
-- days_per_job
SELECT job_id, COUNT(DISTINCT dt) AS days
FROM <database>.job_runs
GROUP BY job_id
```

```sql
-- unrun
SELECT DISTINCT s.run_id, s.job_id
FROM <database>.scheduler_runs s
LEFT JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.job_id = r.job_id
WHERE r.run_id IS NULL
```

```sql
-- measures
SELECT run_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

- Typed over a formula: none.
- Marks: days_per_job's sort by days, descending, is dropped: no ORDER BY, since a Hive table holds no order. numbered's index comes after the sort, so the ORDER BY sits inside ROW_NUMBER. measures drops run 98's blank avg_retry_secs, with no row for it, as M drops a null there.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X67

**Map**
- Sources: job_runs (typed run_id, job_id, duration_mins, dt); jobs (typed job_id, team); run_alerts (typed alert_id, run_id, severity, dt).
- Steps: job_runs, whose formulas team, alerts and running_mins are read by by_team and noisy_runs, so it is a CTE inside each of those queries. job_runs has no final of its own; if you want its rows as a final, say so.
- Finals: by_team (team, total_mins, alerted_runs), a summary with its Total Row folded in; noisy_runs (run_id, team, alerts, running_mins), from its Power Query.
- Parameters and Keys: both empty, so none.

```sql
-- by_team
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt, j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON j.job_id = r.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON a.run_id = r.run_id
)
SELECT team,
  COALESCE(SUM(duration_mins), 0) AS total_mins,
  COALESCE(COUNT(CASE WHEN alerts > 0 THEN 1 END), 0) AS alerted_runs
FROM job_runs
GROUP BY team WITH ROLLUP
```

```sql
-- noisy_runs
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt, j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON j.job_id = r.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON a.run_id = r.run_id
)
SELECT run_id, team, alerts, running_mins
FROM job_runs
WHERE alerts >= 2
```

- Typed over a formula: none.
- Marks: team comes from XLOOKUP, a LEFT JOIN on jobs. alerts comes from COUNTIF over run_alerts, a LEFT JOIN on a grouped run_alerts with COALESCE. by_team's Total Row needs no query of its own: its totals are SUBTOTAL 109 over a SUM and over COUNTs, so WITH ROLLUP adds it with a NULL team. running_mins uses RANGE, so ties on the same dt are included, as Excel's "<=" does.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X68

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed job_id, job_name, team, region); region_budgets (typed job_id, budget_cents, region).
- Steps: base, a connection-only query that by_region and top_runs read; a CTE inside each of their queries.
- Finals: by_region (region, total_mins, runs, share), from its Power Query; by_region (Total Row) (total_mins), one row, no label; top_runs (run_id, job_name, region), from its Power Query.
- Parameters and Keys: both empty, so none.

```sql
-- by_region
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON j.job_id = r.job_id
  LEFT JOIN <database>.region_budgets b ON b.job_id = r.job_id
),
by_region AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT region, total_mins, runs, total_mins / SUM(total_mins) OVER () AS share
FROM by_region
```

```sql
-- by_region (Total Row)
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON j.job_id = r.job_id
  LEFT JOIN <database>.region_budgets b ON b.job_id = r.job_id
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
-- top_runs
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON j.job_id = r.job_id
  LEFT JOIN <database>.region_budgets b ON b.job_id = r.job_id
)
SELECT run_id, job_name, region
FROM base
ORDER BY duration_mins DESC, run_id ASC
LIMIT 2
```

- Typed over a formula: none.
- Marks: top_runs is Table.Sort then FirstN, so it is ORDER BY ... LIMIT 2, and the tie at 30 between runs 97 and 103 is broken by run_id ascending, as the sample has it. by_region's Total Row gets its own query, because by_region is loaded by a Group rather than being a SUMIFS-style summary. base's join to region_budgets is a LEFT JOIN, as Table.NestedJoin's LeftOuter gives.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X71

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: the query ok_runs, which ok_by_job reads; a CTE inside each final's query that reads it.
- Finals: ok_runs (Table: run_id, job_id, duration_mins, hours), with hours added; ok_by_job (job_id, total_mins), from its Power Query.
- Parameters and Keys: both empty, so none.

```sql
-- ok_runs (Table, with hours)
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT run_id, job_id, duration_mins, duration_mins / 60 AS hours
FROM ok_runs
```

```sql
-- ok_by_job
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT job_id, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

- Typed over a formula: none.
- Marks: the blank status in run 98 is dropped, as M's = drops it too.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X72

**Map**
- Sources: job_runs (typed run_id, job_id, duration_mins); jobs (typed job_id, job_name, team).
- Steps: jobs, whose formulas runs and total are read by by_team and busy_jobs; a CTE inside each of their queries.
- Finals: by_team (team, team_total), a summary; busy_jobs (job_id, job_name, runs), from its Power Query.
- Parameters and Keys: both empty, so none.

```sql
-- by_team
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(s.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
    ON c.job_id = j.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) s
    ON s.job_id = j.job_id
)
SELECT team, COALESCE(SUM(total), 0) AS team_total
FROM jobs
GROUP BY team
```

```sql
-- busy_jobs
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(s.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
    ON c.job_id = j.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) s
    ON s.job_id = j.job_id
)
SELECT job_id, job_name, runs
FROM jobs
WHERE runs >= 3
```

- Typed over a formula: none.
- Marks: by_team is a summary, since its only typed column, team, is what SUMIFS matches on, so it is a GROUP BY of jobs. It has no Total Row, so no ROLLUP. Both formulas of jobs are over another Table, so each is a LEFT JOIN with COALESCE.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X75

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: the query long_runs, which long_per_day reads; a CTE inside each final's query that reads it.
- Finals: long_runs (Table: run_id, dt, duration_mins, over), with over added; long_per_day (dt, runs), from its Power Query.
- Parameters and Keys: both empty, so none.

```sql
-- long_runs (Table, with over)
WITH long_runs AS (
  SELECT run_id, dt, duration_mins
  FROM <database>.job_runs
  WHERE duration_mins >= 15
)
SELECT run_id, dt, duration_mins, duration_mins - 15 AS over
FROM long_runs
```

```sql
-- long_per_day
WITH long_runs AS (
  SELECT run_id, dt, duration_mins
  FROM <database>.job_runs
  WHERE duration_mins >= 15
)
SELECT dt, COUNT(*) AS runs
FROM long_runs
GROUP BY dt
```

- Typed over a formula: none.
- Marks: none. The header over is a plain name, so it is kept.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.

## X76

**Map**
- Sources: jobs (typed job_id, job_name, team, region); job_runs (typed run_id, job_id, duration_mins, avg_retry_secs, dt, status).
- Steps: the query finance_jobs, which finance_runs reads; a CTE inside each final's query that reads it.
- Finals: finance_jobs (Table: job_id, job_name, label), with label added; finance_runs (run_id, job_name, duration_mins), from its Power Query.
- Parameters and Keys: both empty, so none.

```sql
-- finance_jobs (Table, with label)
WITH finance_jobs AS (
  SELECT job_id, job_name
  FROM <database>.jobs
  WHERE team = 'finance'
)
SELECT job_id, job_name, UPPER(job_name) AS label
FROM finance_jobs
```

```sql
-- finance_runs
WITH finance_jobs AS (
  SELECT job_id, job_name
  FROM <database>.jobs
  WHERE team = 'finance'
)
SELECT r.run_id, f.job_name, r.duration_mins
FROM <database>.job_runs r
JOIN finance_jobs f ON f.job_id = r.job_id
```

- Typed over a formula: none.
- Marks: the query finance_jobs is the step, since finance_runs reads it by name. The Table finance_jobs is a final, because no formula reads its label.
- Refused: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`. Before the Toolbox code, take out of the workbook what you don't want converted, and run `project.convert` on this Hive; its checked code wins where the two differ.
