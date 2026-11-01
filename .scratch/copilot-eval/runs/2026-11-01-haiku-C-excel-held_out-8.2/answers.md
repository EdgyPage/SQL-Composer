date: 2026-11-01
arm: C
model: haiku
files: 93b81356

Copilot reply, file 11 and file 12 with the Excel path. Toolbox code (file 11 step 8, files 03 to 05) is left out of this reply to keep it within the output limit; ask for it workbook by workbook. Fill in every `<database>` and every `<name>` placeholder before you run a query. Save each final's query as a .hql file named for its Table and run the convert Workflow on them as one batch (file 13), DEV filled in; its checked code wins where the two differ.

## X21
Map. Sources: region_budgets. Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin). No Keys row, no Parameters.
```sql
SELECT job_id, budget_cents, region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets
```
Marks: none. Left alone: none.

## X22
Map. Sources: jobs. Finals: jobs (job_id, job_name, team, is_finance, ratio). No Keys row, no Parameters.
```sql
SELECT job_id, job_name, team,
  IF(team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(job_id / (job_id - 2), 0) AS ratio
FROM <database>.jobs
```
Marks: IFERROR converted to COALESCE, as a divide by 0 is NULL (job 2 gives 0).

## X23
Map. Sources: job_runs. Finals: job_runs (run_id, status, avg_retry_secs, label, risky). No Keys row, no Parameters.
```sql
SELECT run_id, status, avg_retry_secs,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label,
  COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5 AS risky
FROM <database>.job_runs
```
Marks: blank. Run 98 has a blank status and a blank avg_retry_secs, both read by formulas, so each is wrapped in COALESCE. SWITCH converted to CASE with an ELSE 'other'.

## X24
Map. Sources: team_notes. Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars). No Keys row, no Parameters.
```sql
SELECT team, note, written_on,
  SUBSTR(note, 1, INSTR(note, ' ') - 1) AS first_word,
  UPPER(team) AS shout,
  MONTH(written_on) AS month,
  ROUND(LENGTH(note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes
```
Marks: none.

## X25
Map. Sources: Costs, Budgets. Finals: Costs (Job, <cost_cents>, Region, <day_key>, Day); Budgets (Job, Budget, Region, Dollars). No Keys row, no Parameters.
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
Marks: blank. Day Key is held as text (20260911), so Day uses CONCAT and returns text. Cost (cents) has a blank on row 29, not read by any formula, so it stays NULL.

## X26
Map. Sources: run_alerts, job_runs. Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins). No Keys row, no Parameters.
```sql
SELECT ra.alert_id, ra.run_id, ra.severity,
  r.job_id, r.status, a.avg_mins
FROM <database>.run_alerts ra
LEFT JOIN <database>.job_runs r ON ra.run_id = r.run_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins FROM <database>.job_runs GROUP BY job_id) a ON r.job_id = a.job_id
```
Marks: XLOOKUP and VLOOKUP (exact, FALSE) become LEFT JOINs to job_runs; VLOOKUP column 3 is status. AVERAGEIFS becomes AVG, left NULL.

## X27
Map. Sources: jobs. Finals: by_team (team, jobs_in_team, last_job_id, last_job_name), a summary of jobs grouped by team. No Keys row, no Parameters.
```sql
SELECT g.team,
  g.jobs_in_team,
  g.last_job_id,
  j.job_name AS last_job_name
FROM (
  SELECT team,
    COALESCE(COUNT(*), 0) AS jobs_in_team,
    COALESCE(MAX(job_id), 0) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
) g
LEFT JOIN <database>.jobs j ON g.last_job_id = j.job_id
```
Marks: COUNTIFS, MAXIFS and INDEX/MATCH converted. by_team is a summary (its only typed column is what COUNTIFS matches), so it is a GROUP BY of jobs.

## X28
Map. Sources: jobs, job_runs. Finals: jobs (job_id, job_name, ok_mins). Keys: jobs, job_id.
```sql
SELECT j.job_id, j.job_name,
  CASE WHEN j.job_id = 3 THEN 99 ELSE COALESCE(s.total, 0) END AS ok_mins
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
  GROUP BY job_id
) s ON j.job_id = s.job_id
```
Marks: typed over: ok_mins for job 3 is 99 (the Keys row is jobs with job_id), so the CASE keeps it. SUMIFS over another Table is a LEFT JOIN with COALESCE.

## X29
Map. Sources: region_budgets. Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer). Parameters: cents_per_dollar is 100, used as its value. Keys: no row, so the typed row matches on every typed column (job_id, budget_cents, region).
```sql
SELECT job_id, budget_cents, region,
  CASE WHEN job_id = 3 AND budget_cents = 350 AND region = 'us' THEN 5
       ELSE budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets
```
Marks: typed over: in_dollars for job 3 is 5. Refused: pointer uses INDIRECT and ROW(), so it is NULL AS pointer. No Keys row.

## X30
Map. Sources: scheduler_runs. Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter).
```sql
SELECT run_id, job_id, dt,
  SUBSTR(dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs
```
Marks: refused: prev_run uses OFFSET (NULL AS prev_run) and jitter uses RANDBETWEEN (NULL AS jitter). Left alone: the bar chart on Summary and the PivotTable on Pivot.

## X31
Map. Sources: jobs. Finals: jobs (job_id, team, bump, tag, scaled, boosted). Defined name boost is Summary!B2, value 10, used as 10; move it into Parameters.
```sql
SELECT job_id, team,
  NULL AS bump,
  NULL AS tag,
  NULL AS scaled,
  job_id * 10 AS boosted
FROM <database>.jobs
```
Marks: refused: bump reads its own column (circular), TAG is a LAMBDA defined name, scaled reads Summary!$D$4, a cell outside a Table (D4). Left alone: the Summary sheet cells B2 and D4.

## X32
Map. Sources: job_runs, jobs. Finals: by_name (job_name, runs), a summary of job_runs grouped by job_name. Step: job_runs with job_name, a CTE inside by_name's query. No Keys row, no Parameters.
```sql
WITH job_runs_named AS (
  SELECT r.job_id, j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT job_name, COALESCE(COUNT(*), 0) AS runs
FROM job_runs_named
GROUP BY job_name
```
Marks: VLOOKUP with TRUE is approximate; converted here as an exact LEFT JOIN on job_id, as the file says. COUNTIFS becomes COUNT(*) with COALESCE. Rows come out in no fixed order.

## X33
Map. Sources: ops.job_runs read by Sql.Database("dwh01", "ops"). Check that the Hive database is <database> and that it holds job_runs. Finals: slow_runs (run_id, duration_mins, over_by).
```sql
SELECT run_id, duration_mins,
  duration_mins - 20 AS over_by
FROM <database>.job_runs
WHERE duration_mins >= 20
  AND (status <> 'TEST' OR status IS NULL)
```
Marks: Sql.Database read: use the table it names, ops.job_runs, and check the database name. M's <> keeps a null, so the status test keeps NULL.

## X34
Map. Sources: job_runs, jobs. Finals: team_totals (team, total_mins, longest). Step: runs_with_team (connection only), a CTE inside team_totals' query.
```sql
WITH runs_with_team AS (
  SELECT r.run_id, r.job_id, r.duration_mins, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT team,
  SUM(duration_mins) AS total_mins,
  MAX(duration_mins) AS longest
FROM runs_with_team
GROUP BY team
```
Marks: none.

## X35
Map. Sources: job_runs, scheduler_runs. Finals: recent (run_id, dt). Left out: rates, a connection-only query reading Web.Contents (a web source, refused).
```sql
SELECT run_id, dt
FROM (
  SELECT run_id, dt FROM <database>.job_runs
  UNION ALL
  SELECT run_id, dt FROM <database>.scheduler_runs
) both_runs
ORDER BY run_id DESC
LIMIT 4
```
Marks: Table.Combine as UNION ALL; Table.Sort then FirstN as ORDER BY with LIMIT. The rates query is left out and named.

## X36
Map. Sources: run_alerts, job_runs. Finals: job_runs (run_id, status, alerts), severity_by_day (dt, high, low). No Keys row, no Parameters.
```sql
SELECT r.run_id, r.status,
  COALESCE(a.alerts, 0) AS alerts
FROM <database>.job_runs r
LEFT JOIN (
  SELECT run_id, COUNT(*) AS alerts
  FROM <database>.run_alerts
  GROUP BY run_id
) a ON r.run_id = a.run_id
```
```sql
SELECT dt,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
GROUP BY dt
```
Marks: Table.Pivot: one column per value in the sample (high, low), NULL where none. The pivot's columns are now fixed to high and low.

## X37
Map. Sources: Owners. Finals: Owners (<job_no>, <team_name>, Owner, Day, <is_ana>). No Keys row, no Parameters.
```sql
SELECT <job_no>, <team_name>, Owner, Day,
  IF(COALESCE(Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners
```
Marks: blank. Owner is blank on the web rows and is read by the formula, so it is wrapped in COALESCE.

## X38
Map. Sources: job_runs, jobs. Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost). Step: a CTE carrying region from jobs. Keys: job_runs, run_id.
```sql
WITH step AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, j.region
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, region,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY region), 0) AS region_mins,
  CASE WHEN run_id = 102 THEN 1
       ELSE (COALESCE(avg_retry_secs, 0) + duration_mins) * 2 END AS retry_cost
FROM step
```
Marks: blank: run 98 has a blank avg_retry_secs read by retry_cost, so it is wrapped in COALESCE. Typed over: retry_cost for run 102 is 1. SUMIFS over its own Table is a window over region.

## X39
Map. Sources: job_runs, jobs. Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise). Power Query ok_runs is the step's filter.
```sql
WITH ok AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT o.run_id, o.job_id, o.duration_mins, j.job_name,
  o.duration_mins / SUM(o.duration_mins) OVER (PARTITION BY o.job_id) AS share,
  NULL AS noise
FROM ok o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```
Marks: refused: noise uses RAND(), so NULL AS noise. Blank status rows are dropped by the = 'SUCCESS' test, as M drops them.

## X40
Map. Sources: Runs, jobs, run_alerts. Finals: Teams (Team, Total Cost), a summary of Runs grouped by team; run_alerts (alert_id, run_id, severity, dt, Run Mins). Step: Runs with Team and Cost. Parameters: rate is 2, used as its value. No Keys row. Left alone: the Pivot sheet (a PivotTable on Runs).
```sql
WITH runs_step AS (
  SELECT r.Run, r.Job, r.Mins,
    j.team AS Team,
    r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT Team, COALESCE(SUM(Cost), 0) AS <total_cost>
FROM runs_step
GROUP BY Team
```
```sql
WITH runs_step AS (
  SELECT r.Run, r.Job, r.Mins,
    j.team AS Team,
    r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt,
  r.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN runs_step r ON a.run_id = r.Run
```
Marks: XLOOKUP for Team and Run Mins becomes LEFT JOINs; Cost uses rate's value 2.

## X46
Map. Sources: jobs, job_runs. Finals: jobs (job_id, job_name, team, shortest, runs, busiest). No Keys row, no Parameters.
```sql
WITH counted AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(m.shortest, 0) AS shortest,
    COALESCE(c.runs, 0) AS runs
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, MIN(duration_mins) AS shortest FROM <database>.job_runs GROUP BY job_id) m ON j.job_id = m.job_id
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c ON j.job_id = c.job_id
)
SELECT job_id, job_name, team, shortest, runs,
  RANK() OVER (ORDER BY runs DESC) AS busiest
FROM counted
```
Marks: MINIFS, COUNTIF and RANK.EQ (largest first) converted. Job 4 has no runs, so shortest and runs are 0.

## X47
Map. Sources: region_budgets. Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg). No Keys row, no Parameters.
```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```
Marks: RANK.EQ with 1 is ascending. AVERAGEIF is left NULL where nothing matches.

## X48
Map. Sources: job_runs, jobs, run_alerts. Finals: quiet_runs (run_id, job_id, status), slow_regions (region, avg_mins, fastest). No Keys row, no Parameters.
```sql
SELECT t.run_id, t.job_id, t.status
FROM <database>.job_runs t
LEFT JOIN <database>.run_alerts a ON t.run_id = a.run_id
WHERE a.run_id IS NULL
```
```sql
SELECT j.region,
  AVG(r.duration_mins) AS avg_mins,
  MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
INNER JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```
Marks: LeftAnti join as LEFT JOIN with WHERE IS NULL. The slow_regions filter moves to HAVING, repeating the aggregate.

## X49
Map. Sources: job_runs, jobs, run_alerts, scheduler_runs, job_owners. Finals: alert_status (alert_id, severity, status), run_check (run_id, status, scheduled_run), teams (team). No Keys row, no Parameters.
```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON a.run_id = r.run_id
```
```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM (SELECT run_id, status FROM <database>.job_runs) r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```
```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```
Marks: RightOuter is job_runs as the kept side, so it is LEFT JOIN with the tables swapped. FullOuter is FULL OUTER JOIN; run_id is NULL on scheduler-only rows. Table.Distinct over Table.Combine is UNION.

## X50
Map. Sources: job_owners, jobs. Finals: owners (job_id, owner, job_name, newest_first). No Keys row, no Parameters.
```sql
WITH distinct_owners AS (
  SELECT DISTINCT job_id, owner FROM <database>.job_owners
)
SELECT d.job_id, d.owner, j.job_name,
  RANK() OVER (ORDER BY d.job_id DESC) AS newest_first
FROM distinct_owners d
LEFT JOIN <database>.jobs j ON d.job_id = j.job_id
```
Marks: Table.Distinct alone is SELECT DISTINCT. RANK.EQ with the column itself is largest first. Job 4 keeps its NULL owner, as M counts it.

## X59
Map. Sources: jobs, job_runs, run_alerts. Finals: jobs (job_id, job_name, long_runs, failed_mins, not_test), run_alerts (alert_id, run_id, severity, dt, alerts_so_far). No Keys row, no Parameters.
```sql
SELECT j.job_id, j.job_name,
  COALESCE(l.long_runs, 0) AS long_runs,
  COALESCE(f.failed_mins, 0) AS failed_mins,
  COALESCE(n.not_test, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, COUNT(*) AS long_runs FROM <database>.job_runs WHERE duration_mins >= 20 GROUP BY job_id) l ON j.job_id = l.job_id
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS failed_mins FROM <database>.job_runs WHERE LOWER(status) LIKE 'f%' GROUP BY job_id) f ON j.job_id = f.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS not_test FROM <database>.job_runs WHERE (status <> 'TEST' OR status IS NULL) GROUP BY job_id) n ON j.job_id = n.job_id
```
```sql
SELECT alert_id, run_id, severity, dt,
  COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts
```
Marks: the wildcard "f*" is LOWER(status) LIKE 'f%', case ignored. The "<>TEST" count keeps the blank status. COUNTIFS with ties is a running COUNT over run_id.

## X60
Map. Sources: region_budgets. Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region); region_budgets (Total Row). No Keys row, no Parameters.
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
Marks: the Total Row's label "Total" is left out, as it has no label. SUBTOTAL(103) is COUNT, SUBTOTAL(101) is AVG.

## X61
Map. Sources: region_costs. Finals: by_region (region, total_cents, entries, priciest), a summary of region_costs grouped by region; by_region (Total Row). No Keys row, no Parameters.
```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(*), 0) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region
```
```sql
WITH by_region AS (
  SELECT region,
    COALESCE(SUM(cost_cents), 0) AS total_cents,
    COALESCE(COUNT(*), 0) AS entries,
    COALESCE(MAX(cost_cents), 0) AS priciest
  FROM <database>.region_costs
  GROUP BY region
)
SELECT SUM(total_cents) AS total_cents,
  SUM(entries) AS entries,
  MAX(priciest) AS priciest
FROM by_region
```
Marks: row 29 has a blank cost_cents; SUMIFS, MAXIFS skip it, so it is not wrapped. Total Row has no label.

## X62
Map. Sources: team_notes. Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short). No Keys row, no Parameters.
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
Marks: DATEDIF "m" is FLOOR(MONTHS_BETWEEN). The week start and month start use the file's forms.

## X63
Map. Sources: job_runs, scheduler_runs. Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded). No Keys row, no Parameters.
```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  r.avg_retry_secs IS NULL AS no_retry,
  FLOOR(r.duration_mins / 4) AS quarters,
  LEAST(r.duration_mins, 25) AS capped,
  VAR_SAMP(r.duration_mins) OVER () AS variance,
  SUM(r.duration_mins * r.job_id) OVER () AS weighted,
  COALESCE(s.job_id, -1) AS scheduled_job,
  CONCAT('run ', r.run_id) AS label,
  INSTR(LOWER(COALESCE(r.status, '')), LOWER('cess')) > 0 AS succeeded
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```
Marks: blank: run 98 has a blank status, read by SEARCH, so it is wrapped in COALESCE. ISBLANK is avg_retry_secs IS NULL. MIN of two cells is LEAST, SUMPRODUCT is SUM of the product, VAR.S is VAR_SAMP, and XLOOKUP's fourth argument is COALESCE.

## X64
Map. Sources: region_costs, jobs. Finals: picked_costs (job_id, cost_cents, region, size), costed_jobs (job_id, job_name, team, region), costs_filled (job_id, cost_cents, dt, day). No Keys row, no Parameters.
```sql
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL
  AND job_id IN (1, 3)
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
Marks: the picked_costs filter uses List.Contains as IN and <> null as IS NOT NULL. costed_jobs is a LEFT SEMI JOIN, and Text.StartsWith "n" is NOT LIKE 'n%'. costs_filled replaces a blank cost with 0. dt is text and is not converted.

## X65
Map. Sources: jobs, region_budgets, job_owners, scheduler_runs, job_runs. Each Table has typed values only, no formula, no query, so each final is a plain copy. No Keys row, no Parameters.
```sql
SELECT job_id, job_name, team, region FROM <database>.jobs
```
```sql
SELECT job_id, budget_cents, region FROM <database>.region_budgets
```
```sql
SELECT job_id, team, owner, dt FROM <database>.job_owners
```
```sql
SELECT run_id, job_id, dt FROM <database>.scheduler_runs
```
```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt FROM <database>.job_runs
```
Marks: none. Left alone: the Pivot sheet and the Summary chart, if any, are not part of these Tables.

## X66
Map. Sources: job_runs. Finals: ok_runs (run_id, job_id, duration_mins, dt, running, share), ok_runs (Total Row). Step: the Power Query filter as a CTE. No Keys row, no Parameters.
```sql
WITH ok AS (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT run_id, job_id, duration_mins, dt,
  SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,
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
Marks: Text.StartsWith is LIKE 'SUCC%'. SUMIFS with an "<=" on dt is a running sum within job_id, ties included. The Total Row has no label.

## X69
Map. Sources: region_costs, jobs, region_budgets. Step: region_costs (job_name, budget, over_budget, running_cost), a CTE in each final that reads it. Finals: job_totals (job_id, total_cents, over_count), job_totals (Total Row), late_costs (job_id, dt, running_cost). No Keys row, no Parameters.
```sql
WITH step AS (
  SELECT r.job_id, r.cost_cents, r.region, r.dt, j.job_name,
    b.budget_cents AS budget,
    CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) AS dt_date,
    COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget,
    SUM(r.cost_cents) OVER (PARTITION BY r.job_id ORDER BY dt_date RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT job_id,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(CASE WHEN over_budget THEN 1 END), 0) AS over_count
FROM step
GROUP BY job_id
```
```sql
WITH step AS (
  SELECT r.job_id, r.cost_cents, r.dt, b.budget_cents AS budget,
    COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget,
    CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) AS dt_date,
    SUM(r.cost_cents) OVER (PARTITION BY r.job_id ORDER BY dt_date RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
  FROM <database>.region_costs r
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
summary AS (
  SELECT job_id,
    COALESCE(SUM(cost_cents), 0) AS total_cents,
    COALESCE(COUNT(CASE WHEN over_budget THEN 1 END), 0) AS over_count
  FROM step
  GROUP BY job_id
)
SELECT SUM(total_cents) AS total_cents, SUM(over_count) AS over_count
FROM summary
```
```sql
WITH step AS (
  SELECT r.job_id, r.cost_cents, r.dt,
    SUM(r.cost_cents) OVER (PARTITION BY r.job_id ORDER BY CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
  FROM <database>.region_costs r
)
SELECT job_id, dt, running_cost
FROM step
WHERE running_cost > 1500
```
Marks: over_budget uses COALESCE for the blank cost on row 29, since blank > budget is FALSE in Excel. The late_costs filter tests a window's value, so the window sits in the CTE and the WHERE is outside it. The job_totals Total Row has no label. dt is text and is held as text, so the running order uses CONCAT.

## X70
Map. Sources: jobs, job_owners. Finals: jobs (job_id, job_name, team, region), job_owners (job_id, team, owner, dt). No formulas, no queries. No Keys row, no Parameters.
```sql
SELECT job_id, job_name, team, region FROM <database>.jobs
```
```sql
SELECT job_id, team, owner, dt FROM <database>.job_owners
```
Marks: none.

## X73
Map. Sources: region_budgets, jobs. Step: eu_budgets (job_id, budget_cents, region, job_name, dollars), a CTE in eu_count's query. Finals: eu_count (region, jobs, total_cents). No Keys row, no Parameters.
```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name,
    b.budget_cents / 100 AS dollars
  FROM <database>.region_budgets b
  INNER JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT region,
  COUNT(*) AS jobs,
  SUM(budget_cents) AS total_cents
FROM eu_budgets
GROUP BY region
```
Marks: none. Table.Group is GROUP BY, with RowCount as COUNT(*) and List.Sum as SUM.

## X74
Map. Sources: run_alerts, job_runs. Step: run_alerts (status, job_id, alerts_so_far), a CTE in each final that reads it. Finals: by_status (status, alerts), a summary of the step grouped by status; late_alerts (alert_id, run_id, alerts_so_far). No Keys row, no Parameters.
```sql
WITH run_alerts_step AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt, r.status, r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT status, COALESCE(COUNT(*), 0) AS alerts
FROM run_alerts_step
GROUP BY status
```
```sql
WITH run_alerts_step AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt, r.status, r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM run_alerts_step
WHERE alerts_so_far > 5
```
Marks: XLOOKUP becomes LEFT JOIN on run_id. COUNTIFS with "<=" is a running COUNT with ties. The late_alerts filter tests a window, so it sits outside the CTE.

## X77
Map. Sources: run_alerts. Step: high_alerts (alert_id, run_id, dt, late_run), a CTE in high_per_day's query. Finals: high_per_day (dt, alerts). No Keys row, no Parameters.
```sql
WITH high_alerts AS (
  SELECT alert_id, run_id, dt,
    run_id > 100 AS late_run
  FROM <database>.run_alerts
  WHERE severity = 'high'
)
SELECT dt, COUNT(*) AS alerts
FROM high_alerts
GROUP BY dt
```
Marks: Table.Group is GROUP BY dt with COUNT(*).

## X78
Map. Sources: region_costs. Step: known_costs (job_id, cost_cents, dt, dollars), a CTE in each final that reads it. Finals: cost_per_job (job_id, total_cents); known_costs (Total Row). No Keys row, no Parameters.
```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt,
    cost_cents / 100 AS dollars
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT job_id, SUM(cost_cents) AS total_cents
FROM known_costs
GROUP BY job_id
```
```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt,
    cost_cents / 100 AS dollars
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT SUM(cost_cents) AS cost_cents
FROM known_costs
```
Marks: the blank cost on row 29 is dropped by IS NOT NULL, as M's <> null drops it. The known_costs Total Row has no label. Left out: none.
