date: 2026-10-31
arm: C
model: haiku
files: ea80a87

## X21

Sources: region_budgets (job_id, budget_cents, region). Steps: none. Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin). Keys: none, so no value is typed over a formula. Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets
```

## X22

Sources: jobs (job_id, job_name, team). Steps: none. Finals: jobs (job_id, job_name, team, is_finance, ratio). Keys: none. Marks: IFERROR converted to COALESCE, since a divide by 0 is NULL (job 2 gives ratio 0). Fill in: `<database>`.

```sql
SELECT job_id, job_name, team,
  IF(team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(job_id / (job_id - 2), 0) AS ratio
FROM <database>.jobs
```

## X23

Sources: job_runs (run_id, status, avg_retry_secs). Steps: none. Finals: job_runs (run_id, status, avg_retry_secs, label, risky). Keys: none. Marks: blank status and blank avg_retry_secs on run 98, both read by formulas, so wrapped in COALESCE and marked blank. SWITCH converted to CASE with ELSE 'other'. Fill in: `<database>`.

```sql
SELECT run_id, status, avg_retry_secs,
  CASE COALESCE(status, '')
    WHEN 'SUCCESS' THEN 'ok'
    WHEN 'FAILED' THEN 'bad'
    ELSE 'other'
  END AS label,
  (COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs
```

## X24

Sources: team_notes (team, note, written_on). Steps: none. Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars). Keys: none. written_on is a date held as yyyy-mm-dd text, read as it is. Fill in: `<database>`.

```sql
SELECT team, note, written_on,
  SUBSTR(note, 1, INSTR(note, ' ') - 1) AS first_word,
  UPPER(team) AS shout,
  MONTH(written_on) AS month,
  ROUND(LENGTH(note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes
```

## X25

Sources: Costs (Job, `<cost_cents>`, Region, `<day_key>`); Budgets (Job, Budget, Region). Steps: none. Finals: Costs (Job, `<cost_cents>`, Region, `<day_key>`, Day) and Budgets (Job, Budget, Region, Dollars). Keys: none. Marks: Day Key is held as text, so Day is built with CONCAT and SUBSTR, as a date held as text. Cost (cents) is read by no formula, so its blank row is left NULL. Fill in: `<database>`, and each `<...>` header name.

```sql
SELECT Job, <cost_cents>, Region, <day_key>,
  CONCAT(SUBSTR(<day_key>, 1, 4), '-', SUBSTR(<day_key>, 5, 2), '-', SUBSTR(<day_key>, 7, 2)) AS Day
FROM <database>.Costs
```

```sql
SELECT Job, Budget, Region,
  Budget / 100 AS Dollars
FROM <database>.Budgets
```

## X26

Sources: run_alerts (alert_id, run_id, severity); job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Steps: none. Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins). Keys: none. Marks: the XLOOKUP and VLOOKUP become one LEFT JOIN on run_id. The blank status on run 98 is read by the VLOOKUP, so it is wrapped in COALESCE and marked blank. AVERAGEIFS becomes AVG grouped by job_id, left NULL. Fill in: `<database>`.

```sql
SELECT a.alert_id, a.run_id, a.severity, j.job_id,
  COALESCE(j.status, '') AS status,
  m.avg_mins
FROM <database>.run_alerts a
LEFT JOIN <database>.job_runs j ON a.run_id = j.run_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) m ON j.job_id = m.job_id
```

## X27

Sources: jobs (job_id, job_name, team, region). Steps: none. Finals: by_team (team, jobs_in_team, last_job_id, last_job_name). Keys: none. Marks: by_team's only typed column is team, matched by COUNTIFS, so it is a summary: a GROUP BY of jobs. COUNTIFS, MAXIFS get COALESCE. INDEX and MATCH become a LEFT JOIN on job_id. Fill in: `<database>`.

```sql
SELECT g.team, g.jobs_in_team, g.last_job_id, j.job_name AS last_job_name
FROM (
  SELECT team,
    COALESCE(COUNT(*), 0) AS jobs_in_team,
    COALESCE(MAX(job_id), 0) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
) g
LEFT JOIN <database>.jobs j ON g.last_job_id = j.job_id
```

## X28

Sources: jobs (job_id, job_name); job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Steps: none. Finals: jobs (job_id, job_name, ok_mins). Keys: jobs with job_id. Marks: the value typed over in row 4 (job 3, report_build, 99) is converted with CASE on its Keys column job_id. Blank statuses are skipped by the SUMIFS-form, so no COALESCE there. Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  CASE WHEN j.job_id = 3 THEN 99 ELSE COALESCE(s.ok_mins, 0) END AS ok_mins
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS ok_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
  GROUP BY job_id
) s ON j.job_id = s.job_id
```

## X29

Sources: region_budgets (job_id, budget_cents, region). Parameters: cents_per_dollar is 100, read as its value. Steps: none. Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer). Keys: none, so the typed value in row 4 is matched on every typed column (job_id 3, budget_cents 350, region us). Refused: pointer, INDIRECT with ROW, so NULL AS pointer. Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  CASE WHEN job_id = 3 AND budget_cents = 350 AND region = 'us' THEN 5
    ELSE budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets
```

## X30

Sources: scheduler_runs (run_id, job_id, dt). Steps: none. Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter). Keys: none. Refused: prev_run (OFFSET, which hangs on row order) and jitter (RANDBETWEEN), each NULL. Left alone: the Summary bar chart and the PivotTable on sheet "Pivot". Fill in: `<database>`.

```sql
SELECT run_id, job_id, dt,
  SUBSTR(dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs
```

## X31

Sources: jobs (job_id, team). Steps: none. Finals: jobs (job_id, team, bump, tag, scaled, boosted). Keys: none. Refused: bump (reads its own column, circular), tag (TAG is a defined name holding a LAMBDA), scaled (reads the cell Summary!D4 by address, outside a Table), each NULL. boosted uses boost, a defined name for Summary!B2 (value 10): the value is used, and it should move into Parameters. Left alone: the Summary sheet cells B2 and D4. Fill in: `<database>`.

```sql
SELECT job_id, team,
  NULL AS bump,
  NULL AS tag,
  NULL AS scaled,
  job_id * 10 AS boosted
FROM <database>.jobs
```

## X32

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region). Steps: job_runs, since by_name's COUNTIFS reads its job_name column. Finals: by_name (job_name, runs). Keys: none. Marks: VLOOKUP with TRUE is approximate; converted to an exact LEFT JOIN on job_id, as stated. Fill in: `<database>`.

```sql
WITH runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT job_name, COALESCE(COUNT(*), 0) AS runs
FROM runs
GROUP BY job_name
```

## X33

Sources: job_runs, read by the Power Query through Sql.Database("dwh01", "ops") and table job_runs; please check the server dwh01 and schema ops, which I named as `<database>`. Steps: none. Finals: slow_runs (run_id, duration_mins, over_by). Keys: none. Marks: M's `<>` keeps a null, so the TEST filter keeps a NULL status. Fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  duration_mins - 20 AS over_by
FROM <database>.job_runs
WHERE duration_mins >= 20 AND (status <> 'TEST' OR status IS NULL)
```

## X34

Sources: job_runs, jobs. Steps: runs_with_team (the connection-only query, read by team_totals), a CTE. Finals: team_totals (team, total_mins, longest). Keys: none. Fill in: `<database>`.

```sql
WITH runs_with_team AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT team, SUM(duration_mins) AS total_mins, MAX(duration_mins) AS longest
FROM runs_with_team
GROUP BY team
```

## X35

Sources: job_runs (run_id, dt); scheduler_runs (run_id, job_id, dt). Steps: none. Finals: recent (run_id, dt). Left out: the connection-only query "rates", which reads a web source through Web.Contents. Keys: none. Marks: Table.Sort then FirstN becomes ORDER BY ... LIMIT. Fill in: `<database>`.

```sql
SELECT run_id, dt
FROM (
  SELECT run_id, dt FROM <database>.job_runs
  UNION ALL
  SELECT run_id, dt FROM <database>.scheduler_runs
) combined
ORDER BY run_id DESC
LIMIT 4
```

## X36

Sources: run_alerts (alert_id, run_id, severity, dt); job_runs (run_id, status). Steps: none. Finals: job_runs (run_id, status, alerts); severity_by_day (dt, high, low). Keys: none. Marks: the Pivot's columns are now fixed to high and low, NULL where none. Fill in: `<database>`.

```sql
SELECT j.run_id, j.status, COALESCE(a.alerts, 0) AS alerts
FROM <database>.job_runs j
LEFT JOIN (
  SELECT run_id, COUNT(*) AS alerts
  FROM <database>.run_alerts
  GROUP BY run_id
) a ON j.run_id = a.run_id
```

```sql
SELECT dt,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
GROUP BY dt
```

## X37

Sources: Owners (Job No, Team Name, Owner, Day). Steps: none. Finals: Owners (Job No, Team Name, Owner, Day, Is Ana). Keys: none. Marks: blank Owner on the web rows is read by IF, so wrapped in COALESCE and marked blank. IF is not an -IF(S) form. Fill in: `<database>`, and each `<...>` header.

```sql
SELECT <job_no>, <team_name>, Owner, Day,
  IF(COALESCE(Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners
```

## X38

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region). Steps: none. Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost). Keys: job_runs with run_id, so the value typed over in run 102 (retry_cost 1) is a CASE on run_id. Marks: blank avg_retry_secs on run 98 is read by retry_cost, so wrapped in COALESCE and marked blank. Fill in: `<database>`.

```sql
WITH runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, j.region
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, region,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY region), 0) AS region_mins,
  CASE WHEN run_id = 102 THEN 1
    ELSE (COALESCE(avg_retry_secs, 0) + duration_mins) * 2 END AS retry_cost
FROM runs
```

## X39

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region). Steps: none. Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise). Keys: none. Refused: noise (RAND), NULL. Marks: the Table's query keeps SUCCESS rows, and share's SUMIFS becomes a window SUM over job_id. Fill in: `<database>`.

```sql
WITH ok AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT ok.run_id, ok.job_id, ok.duration_mins, j.job_name,
  ok.duration_mins / COALESCE(SUM(ok.duration_mins) OVER (PARTITION BY ok.job_id), 0) AS share,
  NULL AS noise
FROM ok
LEFT JOIN <database>.jobs j ON ok.job_id = j.job_id
```

## X40

Sources: jobs (job_id, job_name, team, region); Runs (Run, Job, Mins). Parameters: rate is 2, read as its value. Steps: runs, a CTE holding Team and Cost, read by Teams and run_alerts. Finals: Teams (Team, `<total_cost>`); run_alerts (alert_id, run_id, severity, dt, `<run_mins>`). Keys: none. Marks: Teams is a summary, its only typed column Team is matched by SUMIFS, so a GROUP BY of Runs. Left alone: the PivotTable on sheet "Pivot". Fill in: `<database>`.

```sql
WITH runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT Team, COALESCE(SUM(Cost), 0) AS <total_cost>
FROM runs
GROUP BY Team
```

```sql
SELECT a.alert_id, a.run_id, a.severity, a.dt,
  r.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN <database>.Runs r ON a.run_id = r.Run
```

## X46

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team). Steps: none. Finals: jobs (job_id, job_name, team, shortest, runs, busiest). Keys: none. Marks: MINIFS and COUNTIF become COALESCE'd aggregates on a LEFT JOIN. RANK.EQ is descending by default, so it is RANK() OVER (ORDER BY runs DESC). Fill in: `<database>`.

```sql
WITH counted AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(m.shortest, 0) AS shortest,
    COALESCE(c.runs, 0) AS runs
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, MIN(duration_mins) AS shortest
    FROM <database>.job_runs GROUP BY job_id
  ) m ON j.job_id = m.job_id
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS runs
    FROM <database>.job_runs GROUP BY job_id
  ) c ON j.job_id = c.job_id
)
SELECT job_id, job_name, team, shortest, runs,
  RANK() OVER (ORDER BY runs DESC) AS busiest
FROM counted
```

## X47

Sources: region_budgets (job_id, budget_cents, region). Steps: none. Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg). Keys: none. Marks: region_total gets COALESCE; region_avg is AVG left NULL. Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

## X48

Sources: job_runs, jobs, run_alerts (all typed only). Steps: none. Finals: quiet_runs (run_id, job_id, status); slow_regions (region, avg_mins, fastest). Keys: none. Marks: the LeftAnti join becomes LEFT JOIN with WHERE IS NULL. The average is AVG and the minimum MIN, and the HAVING repeats the average. Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

```sql
SELECT j.region,
  AVG(r.duration_mins) AS avg_mins,
  MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

## X49

Sources: job_runs, jobs, run_alerts, scheduler_runs, job_owners (typed only, so sources, not finals). Steps: none. Finals: alert_status (alert_id, severity, status); run_check (run_id, status, scheduled_run); teams (team). Keys: none. Marks: RightOuter is a LEFT JOIN with the tables swapped. FullOuter is a FULL OUTER JOIN, so a scheduled run with no job run shows a NULL run_id and its number in scheduled_run. Table.Distinct over Table.Combine is UNION. Fill in: `<database>`.

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
```

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

## X50

Sources: job_owners (job_id, team, owner, dt); jobs (job_id, job_name, team, region). Steps: none. Finals: owners (job_id, owner, job_name, newest_first). Keys: none. Marks: Table.Distinct is SELECT DISTINCT. RANK.EQ over the column is RANK() OVER (ORDER BY job_id DESC). Blank owner on job 4 is kept as NULL, as no formula reads it. Fill in: `<database>`.

```sql
WITH uniq AS (
  SELECT DISTINCT job_id, owner
  FROM <database>.job_owners
)
SELECT u.job_id, u.owner, j.job_name,
  RANK() OVER (ORDER BY u.job_id DESC) AS newest_first
FROM uniq u
LEFT JOIN <database>.jobs j ON u.job_id = j.job_id
```

## X59

Sources: job_runs (typed only); jobs (job_id, job_name). Steps: none. Finals: jobs (job_id, job_name, long_runs, failed_mins, not_test); run_alerts (alert_id, run_id, severity, dt, alerts_so_far). Keys: none. Marks: the wildcard "f*" becomes LOWER(status) LIKE 'f%'. "<>TEST" keeps a blank status. The running count with ties is a window with RANGE. Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(l.n, 0) AS long_runs,
  COALESCE(f.total, 0) AS failed_mins,
  COALESCE(t.n, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS n FROM <database>.job_runs
  WHERE duration_mins >= 20 GROUP BY job_id
) l ON j.job_id = l.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs
  WHERE LOWER(status) LIKE 'f%' GROUP BY job_id
) f ON j.job_id = f.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS n FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL) GROUP BY job_id
) t ON j.job_id = t.job_id
```

```sql
SELECT alert_id, run_id, severity, dt,
  COALESCE(COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
FROM <database>.run_alerts
```

## X60

Sources: region_budgets (job_id, budget_cents, region). Steps: none. Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region); region_budgets (Total Row). Keys: none. Marks: the whole-column SUM and AVERAGE become window functions. COUNTIFS with "<" and +1 is RANK ASC within region. The Total Row's SUBTOTAL 103 is COUNT and 101 is AVG, as its own query. Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

```sql
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

## X61

Sources: region_costs (job_id, cost_cents, region, dt). Steps: none. Finals: by_region (region, total_cents, entries, priciest). Keys: none. Marks: by_region is a summary (its only typed column is region, matched by SUMIFS and COUNTIFS), so a GROUP BY of region_costs. The Total Row adds up SUMs and COUNTs and takes the MAX of MAXes, so it needs no query of its own: the ROLLUP row is the total (region NULL). The blank cost on row 29 is skipped by SUM and MAX. Fill in: `<database>`.

```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(*), 0) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

## X62

Sources: team_notes (team, note, written_on). Steps: none. Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short). Keys: none. Marks: WEEKDAY(d, 2) start of week and EOMONTH(d, -1)+1 as file 11 writes them; DATEDIF "m" as FLOOR(MONTHS_BETWEEN); TEXTJOIN with TRUE as CONCAT_WS, which skips NULL. Fill in: `<database>`.

```sql
SELECT team, note, written_on,
  CAST(NEXT_DAY(DATE_ADD(written_on, 7 * -1), 'MO') AS STRING) AS week_of,
  LAST_DAY(written_on) AS month_end,
  CAST(TRUNC(written_on, 'MM') AS STRING) AS month_of,
  FLOOR(MONTHS_BETWEEN(written_on, '2026-01-01')) AS months_in,
  DATE_SUB(written_on, 3) AS three_before,
  INITCAP(team) AS who,
  CONCAT_WS(': ', team, SUBSTR(note, 1, 5)) AS short
FROM <database>.team_notes
```

## X63

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs); scheduler_runs (run_id, job_id, dt). Steps: none. Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded). Keys: none. Marks: blank status on run 98 is read by SEARCH, so wrapped in COALESCE and marked blank. ISBLANK becomes IS NULL with no COALESCE. XLOOKUP's fourth argument -1 is COALESCE. Whole-column VAR.S and SUMPRODUCT become window functions. Fill in: `<database>`.

```sql
SELECT j.run_id, j.job_id, j.status, j.duration_mins, j.avg_retry_secs,
  j.avg_retry_secs IS NULL AS no_retry,
  FLOOR(j.duration_mins / 4) AS quarters,
  LEAST(j.duration_mins, 25) AS capped,
  VAR_SAMP(j.duration_mins) OVER () AS variance,
  SUM(j.duration_mins * j.job_id) OVER () AS weighted,
  COALESCE(s.job_id, -1) AS scheduled_job,
  CONCAT('run ', j.run_id) AS label,
  (INSTR(LOWER(COALESCE(j.status, '')), 'cess') > 0) AS succeeded
FROM <database>.job_runs j
LEFT JOIN <database>.scheduler_runs s ON j.run_id = s.run_id
```

## X64

Sources: jobs (job_id, job_name, team, region); region_costs (job_id, cost_cents, region, dt). Steps: none. Finals: picked_costs (job_id, cost_cents, region, size); costed_jobs (job_id, job_name, team, region); costs_filled (job_id, cost_cents, dt, day). Keys: none. Marks: the connection-only region filter becomes IN, and the <> null becomes IS NOT NULL. A row whose key is in another table becomes LEFT SEMI JOIN. The blank cost on row 29 is wrapped in COALESCE and marked blank. Fill in: `<database>`.

```sql
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

```sql
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt,
  SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

## X65

Sources: jobs (job_id, job_name, team, region); region_budgets (job_id, budget_cents, region); job_owners (job_id, team, owner, dt); scheduler_runs (run_id, job_id, dt); job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Steps: none. Finals: team_regions (team, region); budget_places (job_id, budget_cents, region, place); jobs_per_team (team, jobs); ran_as_scheduled (run_id, dt); run_measures (run_id, job_id, measure, amount). Keys: none. Marks: team_regions' Table.Sort by team has no FirstN or index after it, so the order is dropped. Table.Distinct is SELECT DISTINCT. The Table.Unpivot becomes one SELECT per column with a NULL filter, stacked with UNION ALL. Fill in: `<database>`.

```sql
SELECT t.team, r.region
FROM (SELECT DISTINCT team FROM <database>.jobs) t
CROSS JOIN (SELECT DISTINCT region FROM <database>.jobs) r
```

```sql
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

```sql
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

```sql
SELECT DISTINCT s.run_id, s.dt
FROM <database>.scheduler_runs s
JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.dt = r.dt
```

```sql
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

## X66

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Steps: ok, the Power Query's rows as a CTE. Finals: ok_runs (run_id, job_id, duration_mins, dt, running, share); ok_runs (Total Row). Keys: none. Marks: SUMIFS with "<=" becomes a running total with ties, COALESCE'd. The Total Row is SUBTOTAL 109, a SUM. Fill in: `<database>`.

```sql
WITH ok AS (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT run_id, job_id, duration_mins, dt,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM ok
```

```sql
WITH ok AS (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT SUM(duration_mins) AS duration_mins
FROM ok
```

## X69

Sources: region_costs (job_id, cost_cents, region, dt); jobs (job_id, job_name, team, region); region_budgets (job_id, budget_cents, region). Steps: none. Finals: region_costs (job_id, cost_cents, region, dt, job_name, budget, over_budget, running_cost). Keys: none. Marks: the blank cost on row 29 is read by over_budget, so wrapped in COALESCE and marked blank. SUMIFS with "<=" is a running total by job_id, COALESCE'd. Fill in: `<database>`.

```sql
SELECT rc.job_id, rc.cost_cents, rc.region, rc.dt,
  j.job_name,
  rb.budget_cents AS budget,
  COALESCE(rc.cost_cents, 0) > rb.budget_cents AS over_budget,
  COALESCE(SUM(rc.cost_cents) OVER (PARTITION BY rc.job_id ORDER BY rc.dt
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
FROM <database>.region_costs rc
LEFT JOIN <database>.jobs j ON rc.job_id = j.job_id
LEFT JOIN <database>.region_budgets rb ON rc.job_id = rb.job_id
```

## X70

Sources: jobs (job_id, job_name, team, region); job_owners (job_id, team, owner, dt); job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Steps: staffed (connection-only, read by owner_load), a CTE. Finals: owner_load (owner, total_mins, runs, avg_mins); owner_load (Total Row); busiest_owner (owner, total_mins, runs). Keys: none. Marks: Table.Distinct is SELECT DISTINCT. The Total Row's SUBTOTAL 109 is a SUM of runs, which is the count of joined rows. Table.FirstN after Table.Sort is ORDER BY ... LIMIT. Fill in: `<database>`.

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
)
SELECT s.owner,
  SUM(r.duration_mins) AS total_mins,
  COUNT(*) AS runs,
  SUM(r.duration_mins) / COUNT(*) AS avg_mins
FROM staffed s
LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
GROUP BY s.owner
```

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
)
SELECT COUNT(*) AS runs
FROM staffed s
LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
```

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner,
    SUM(r.duration_mins) AS total_mins,
    COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs
FROM owner_load
ORDER BY runs DESC
LIMIT 1
```

## X73

Sources: region_budgets (job_id, budget_cents, region); jobs (job_id, job_name, team, region). Steps: none. Finals: eu_budgets (job_id, budget_cents, region, job_name, dollars); eu_count (region, jobs, total_cents). Keys: none. Marks: the inner join is a JOIN and the region filter comes first. eu_count's Table.Group is a GROUP BY over eu_budgets, which is read as a CTE. Fill in: `<database>`.

```sql
SELECT b.job_id, b.budget_cents, b.region, j.job_name,
  b.budget_cents / 100 AS dollars
FROM <database>.region_budgets b
JOIN <database>.jobs j ON b.job_id = j.job_id
WHERE b.region = 'eu'
```

```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT region, COUNT(*) AS jobs, SUM(budget_cents) AS total_cents
FROM eu_budgets
GROUP BY region
```

## X74

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); run_alerts (alert_id, run_id, severity, dt). Steps: alerts, a CTE holding run_alerts' status, job_id and alerts_so_far, since by_status's COUNTIFS reads status. Finals: by_status (status, alerts); late_alerts (alert_id, run_id, alerts_so_far). Keys: none. Marks: by_status is a summary, its only typed column status matched by COUNTIFS. The blank status on run 98 is read by XLOOKUP, so wrapped in COALESCE and marked blank. The running count with ties is a window with RANGE. Fill in: `<database>`.

```sql
WITH alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(j.status, '') AS status,
    j.job_id,
    COALESCE(COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs j ON a.run_id = j.run_id
)
SELECT status, COALESCE(COUNT(*), 0) AS alerts
FROM alerts
GROUP BY status
```

```sql
WITH alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(j.status, '') AS status,
    j.job_id,
    COALESCE(COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs j ON a.run_id = j.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM alerts
WHERE alerts_so_far > 5
```

## X77

Sources: run_alerts (alert_id, run_id, severity, dt). Steps: none. Finals: high_alerts (alert_id, run_id, dt, late_run); high_per_day (dt, alerts). Keys: none. Marks: high_per_day reads high_alerts as a CTE, and its Table.Group is a GROUP BY dt with COUNT(*). Fill in: `<database>`.

```sql
SELECT alert_id, run_id, dt,
  run_id > 100 AS late_run
FROM <database>.run_alerts
WHERE severity = 'high'
```

```sql
WITH high_alerts AS (
  SELECT alert_id, run_id, dt
  FROM <database>.run_alerts
  WHERE severity = 'high'
)
SELECT dt, COUNT(*) AS alerts
FROM high_alerts
GROUP BY dt
```

## X78

Sources: region_costs (job_id, cost_cents, region, dt). Steps: none. Finals: known_costs (job_id, cost_cents, dt, dollars); known_costs (Total Row); cost_per_job (job_id, total_cents). Keys: none. Marks: the cost_cents <> null filter becomes IS NOT NULL, so the blank cost on row 29 is dropped. The Total Row is SUBTOTAL 109, a SUM. Fill in: `<database>`.

```sql
SELECT job_id, cost_cents, dt,
  cost_cents / 100 AS dollars
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL
```

```sql
SELECT SUM(cost_cents) AS cost_cents
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL
```

```sql
SELECT job_id, SUM(cost_cents) AS total_cents
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL
GROUP BY job_id
```

Note for all tasks: this reply gives the map and the Hive for each final. The Toolbox code of step 8 is not written here. To finish, take out what you don't want converted, fill in each `<...>`, save each final's Hive as a .hql file, and run the convert Workflow (file 13) on them as one batch with DEV filled in. Its checked code wins where the two differ.
