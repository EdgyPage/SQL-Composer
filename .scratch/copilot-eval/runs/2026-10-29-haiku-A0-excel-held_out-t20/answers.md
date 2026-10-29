date: 2026-10-29
arm: A0
model: haiku
files: none

## X21

The Parameters, Keys and Steps sheets are empty here, so only the table's two calculated columns need converting. Hive's `/` returns a fractional result, so 150 / 100 gives 1.5.

```sql
SELECT
  job_id,
  budget_cents,
  region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM region_budgets;
```

## X22

Excel's `=` on text ignores case, so `LOWER(team)` keeps that behaviour. Hive returns NULL for division by zero, not an error, so the IFERROR becomes an explicit CASE that returns 0 when the divisor is 0.

```sql
SELECT
  job_id,
  job_name,
  team,
  CASE WHEN LOWER(team) = 'finance' THEN 'yes' ELSE 'no' END AS is_finance,
  CASE WHEN job_id - 2 = 0 THEN 0 ELSE job_id / (job_id - 2) END AS ratio
FROM jobs;
```

## X23

SWITCH becomes a CASE, with the default "other" also catching a NULL status, as it does in Excel. The Excel blank in avg_retry_secs counts as 0, and the NULL-safe wrapping stops the OR from returning NULL when status is missing.

```sql
SELECT
  run_id,
  status,
  avg_retry_secs,
  CASE status
    WHEN 'SUCCESS' THEN 'ok'
    WHEN 'FAILED' THEN 'bad'
    ELSE 'other'
  END AS label,
  (COALESCE(status = 'FAILED', FALSE))
    OR (COALESCE(avg_retry_secs, 0) > 5) AS risky
FROM job_runs;
```

## X24

LEFT, FIND, UPPER, MONTH and ROUND map to substr with instr, upper, month and round. The `- 1` after the FIND position matches the Excel formula.

```sql
SELECT
  team,
  note,
  written_on,
  substr(note, 1, instr(note, ' ') - 1) AS first_word,
  upper(team) AS shout,
  month(written_on) AS month,
  round(length(note) / 10, 1) AS tens_of_chars
FROM team_notes;
```

## X25

The Day Key is a number like 20260911, so it is cast to a string and split into a yyyy-MM-dd text that Hive casts to DATE. Headers with spaces and brackets are renamed to plain column names. The blank cost on row 29 becomes NULL.

```sql
SELECT
  job,
  cost_cents,
  region,
  day_key,
  CAST(
    CONCAT(
      SUBSTR(CAST(day_key AS STRING), 1, 4), '-',
      SUBSTR(CAST(day_key AS STRING), 5, 2), '-',
      SUBSTR(CAST(day_key AS STRING), 7, 2)
    ) AS DATE) AS day
FROM costs;
```

Budgets sheet:

```sql
SELECT
  job,
  budget,
  region,
  budget / 100 AS dollars
FROM budgets;
```

## X26

XLOOKUP becomes a join on run_id. The VLOOKUP at column 3 of job_runs is status. AVERAGEIFS by job_id becomes a per-job average joined back on job_id.

```sql
SELECT
  a.alert_id,
  a.run_id,
  a.severity,
  r.job_id,
  r.status,
  avg_by_job.avg_mins
FROM run_alerts a
LEFT JOIN job_runs r
  ON r.run_id = a.run_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM job_runs
  GROUP BY job_id
) avg_by_job
  ON avg_by_job.job_id = r.job_id;
```

## X27

COUNTIFS becomes COUNT per team, MAXIFS becomes MAX, and INDEX/MATCH on the last job id becomes a join back to jobs.

```sql
WITH team_stats AS (
  SELECT
    team,
    COUNT(*) AS jobs_in_team,
    MAX(job_id) AS last_job_id
  FROM jobs
  GROUP BY team
)
SELECT
  t.team,
  t.jobs_in_team,
  t.last_job_id,
  j.job_name AS last_job_name
FROM team_stats t
LEFT JOIN jobs j
  ON j.job_id = t.last_job_id;
```

## X28

SUMIFS with the two criteria becomes a conditional SUM over a LEFT JOIN, and COALESCE returns 0 for a job with no matching runs. Row 3 (report_build) is a typed 99 in the sheet, not a formula, so the SQL keeps it as an override and flags it.

```sql
SELECT
  j.job_id,
  j.job_name,
  CASE
    WHEN j.job_id = 3 THEN 99
    ELSE COALESCE(SUM(CASE WHEN r.status = 'SUCCESS' THEN r.duration_mins END), 0)
  END AS ok_mins
FROM jobs j
LEFT JOIN job_runs r
  ON r.job_id = j.job_id
GROUP BY j.job_id, j.job_name;
```

Note: the Keys sheet says jobs is keyed on job_id. Hive does not enforce that, so keep job_id unique in the data.

## X29

The Parameters lookup of cents_per_dollar is 100, so the division uses 100 directly. Row 3's in_dollars is a typed 5 and not a formula, and it does not equal 350 / 100, so the SQL keeps it as an override. INDIRECT("A"&ROW()) reads column A of the same row, which is job_id.

```sql
SELECT
  job_id,
  budget_cents,
  region,
  CASE WHEN job_id = 3 THEN 5 ELSE budget_cents / 100 END AS in_dollars,
  job_id AS pointer
FROM region_budgets;
```

## X30

OFFSET(run_id, -1, 0) is the run_id one row up, which LAG gives when the rows are ordered by run_id. The first row's Excel value is the header text, and the SQL gives NULL there. RIGHT(dt, 2) becomes SUBSTR with a negative start. RANDBETWEEN is volatile, so it is best stored once with CREATE TABLE AS and not recomputed in a view.

```sql
SELECT
  run_id,
  job_id,
  dt,
  SUBSTR(CAST(dt AS STRING), -2) AS day,
  LAG(run_id) OVER (ORDER BY run_id) AS prev_run,
  CAST(FLOOR(RAND() * 5) + 1 AS INT) AS jitter
FROM scheduler_runs;
```

Pivot sheet (count of run_id by job_id):

```sql
SELECT
  job_id,
  COUNT(run_id) AS count_of_run_id
FROM scheduler_runs
GROUP BY job_id;
```

The bar chart on Summary has no Hive equivalent, so it is not converted.

## X31

- tag: the TAG LAMBDA becomes an inline expression.
- scaled: Summary!$D$4 is 7, so the formula is job_id * 7.
- boosted: the name boost is Summary!$B$2, which is 10, so the formula is job_id * 10.
- bump: its formula refers to its own column, so it is a circular reference and has no value to convert. It is left out and flagged.

```sql
SELECT
  job_id,
  team,
  -- bump: circular reference in the sheet (=bump * 2 refers to itself), no value to convert
  CONCAT(UPPER(team), '!') AS tag,
  job_id * 7 AS scaled,
  job_id * 10 AS boosted
FROM jobs;
```

## X32

VLOOKUP with TRUE at column 2 of jobs is the job_name for each job_id, so a LEFT JOIN on job_id gives the same result for these ids. COUNTIFS on job_name is a count of runs per name.

```sql
SELECT
  r.run_id,
  r.job_id,
  r.status,
  r.duration_mins,
  r.avg_retry_secs,
  r.dt,
  j.job_name
FROM job_runs r
LEFT JOIN jobs j
  ON j.job_id = r.job_id;
```

by_name sheet:

```sql
WITH runs_named AS (
  SELECT r.run_id, j.job_name
  FROM job_runs r
  LEFT JOIN jobs j
    ON j.job_id = r.job_id
)
SELECT
  b.job_name,
  COUNT(n.run_id) AS runs
FROM by_name b
LEFT JOIN runs_named n
  ON n.job_name = b.job_name
GROUP BY b.job_name;
```

## X33

The Power Query is a filter and a computed column on the source table. In Power Query a null status is not equal to "TEST", so those rows are kept. Hive's `<>` returns NULL for a null status, so the condition adds an explicit IS NULL check.

```sql
SELECT
  run_id,
  duration_mins,
  duration_mins - 20 AS over_by
FROM job_runs
WHERE duration_mins >= 20
  AND (status <> 'TEST' OR status IS NULL);
```

The Sql.Database source (dwh01, ops.job_runs) is the table this query reads from, so it is not part of the Hive.

## X34

The NestedJoin and ExpandTableColumn steps become a LEFT JOIN to jobs. Table.Group becomes GROUP BY team with SUM and MAX.

```sql
SELECT
  j.team,
  SUM(r.duration_mins) AS total_mins,
  MAX(r.duration_mins) AS longest
FROM job_runs r
LEFT JOIN jobs j
  ON j.job_id = r.job_id
GROUP BY j.team;
```

## X35

Table.Combine is UNION ALL, Table.Sort descending on run_id is ORDER BY, and Table.FirstN 4 is LIMIT 4. Rows that tie on run_id have no fixed order in either version.

```sql
SELECT run_id, dt
FROM (
  SELECT run_id, dt FROM job_runs
  UNION ALL
  SELECT run_id, dt FROM scheduler_runs
) combined
ORDER BY run_id DESC
LIMIT 4;
```

The "rates" query fetches https://rates.example.com/today.json over the web. That is not part of a Hive conversion, so it is not converted here.

## X36

The COUNTIFS on run_alerts becomes a LEFT JOIN with COUNT. The Table.Pivot by severity becomes conditional SUMs by dt. The pivot columns are fixed in SQL, while Power Query picks the distinct severities each time it refreshes.

```sql
SELECT
  dt,
  SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) AS low
FROM run_alerts
GROUP BY dt;
```

job_runs sheet:

```sql
SELECT
  r.run_id,
  r.status,
  COUNT(a.alert_id) AS alerts
FROM job_runs r
LEFT JOIN run_alerts a
  ON a.run_id = r.run_id
GROUP BY r.run_id, r.status;
```

## X37

IF([@Owner]="ana",1,0) becomes a CASE. Excel's `=` ignores case, so LOWER keeps that. A blank owner gives 0 in both. The headers with spaces are renamed, and `day` is back-quoted in case it clashes with the DAY function name.

```sql
SELECT
  job_no,
  team_name,
  owner,
  `day`,
  CASE WHEN LOWER(owner) = 'ana' THEN 1 ELSE 0 END AS is_ana
FROM owners;
```

## X38

XLOOKUP becomes a LEFT JOIN to jobs for region. SUMIFS by region becomes a windowed SUM over the same region. In the retry_cost formula, the blank avg_retry_secs in Excel counts as 0, so COALESCE is used. Row 8 (run 102) is a typed 1 in the sheet, not a formula, so the SQL keeps it as an override.

```sql
SELECT
  r.run_id,
  r.job_id,
  r.status,
  r.duration_mins,
  r.avg_retry_secs,
  j.region,
  SUM(r.duration_mins) OVER (PARTITION BY j.region) AS region_mins,
  CASE
    WHEN r.run_id = 102 THEN 1
    ELSE (COALESCE(r.avg_retry_secs, 0) + r.duration_mins) * 2
  END AS retry_cost
FROM job_runs r
LEFT JOIN jobs j
  ON j.job_id = r.job_id;
```

## X39

Each Excel Table becomes a Hive table or view. The Power Query "ok_runs" becomes a view, and the table's calculated columns sit on a second view. The Parameters, Keys and Steps sheets are empty here, so they produce no SQL.

```sql
-- Power Query "ok_runs": SUCCESS rows, three columns
CREATE VIEW ok_runs_loaded AS
SELECT run_id, job_id, duration_mins
FROM job_runs
WHERE status = 'SUCCESS';

-- Table ok_runs with its calculated columns
CREATE VIEW ok_runs AS
SELECT
  o.run_id,
  o.job_id,
  o.duration_mins,
  j.job_name,
  o.duration_mins / t.job_total_mins AS share,
  rand() AS noise
FROM ok_runs_loaded o
LEFT JOIN jobs j
  ON j.job_id = o.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS job_total_mins
  FROM ok_runs_loaded
  GROUP BY job_id
) t
  ON t.job_id = o.job_id;
```

- XLOOKUP becomes a LEFT JOIN. A job with no match gives NULL where Excel gives #N/A.
- SUMIFS by job_id becomes a grouped subquery joined back on job_id.
- RAND() becomes rand(). It changes on every query, as Excel's does, so keep it out of anything that needs stable results.

## X40

The raw Runs columns (Run, Job, Mins) are a table. Team and Cost become a view, and the rate comes from Parameters.

```sql
CREATE VIEW runs_costed AS
SELECT
  r.Run,
  r.Job,
  r.Mins,
  j.team AS Team,
  r.Mins * CAST(p.value AS DOUBLE) AS Cost
FROM runs r
LEFT JOIN jobs j
  ON j.job_id = r.Job
CROSS JOIN (SELECT value FROM parameters WHERE name = 'rate') p;

-- Table Teams: Team | Total Cost
CREATE VIEW teams_costed AS
SELECT
  t.team AS Team,
  COALESCE(SUM(r.Cost), 0) AS total_cost
FROM teams t
LEFT JOIN runs_costed r
  ON r.Team = t.team
GROUP BY t.team;

-- Table run_alerts with Run Mins
CREATE VIEW run_alerts_mins AS
SELECT
  a.alert_id,
  a.run_id,
  a.severity,
  a.dt,
  r.Mins AS run_mins
FROM run_alerts a
LEFT JOIN runs r
  ON r.Run = a.run_id;

-- PivotTable on Runs: rows Team, values Sum of Cost
SELECT Team, SUM(Cost) AS sum_of_cost
FROM runs_costed
GROUP BY Team;
```

- Hive has no PivotTable, so the last query returns the same numbers: data 134, finance 226.
- The Teams total is a SUMIFS, which becomes a grouped join. COALESCE gives 0 for a team with no runs.

## X46

```sql
CREATE VIEW jobs_stats AS
SELECT
  j.job_id,
  j.job_name,
  j.team,
  COALESCE(s.shortest, 0) AS shortest,
  COALESCE(s.runs, 0) AS runs
FROM jobs j
LEFT JOIN (
  SELECT job_id, MIN(duration_mins) AS shortest, COUNT(*) AS runs
  FROM job_runs
  GROUP BY job_id
) s
  ON s.job_id = j.job_id;

CREATE VIEW jobs_ranked AS
SELECT
  job_id,
  job_name,
  team,
  shortest,
  runs,
  RANK() OVER (ORDER BY runs DESC) AS busiest
FROM jobs_stats;
```

- MINIFS returns 0 when nothing matches in Excel, so COALESCE(..., 0) keeps cache_warm at 0.
- RANK.EQ with no order argument ranks descending, and ties share a rank, which is RANK() OVER (ORDER BY runs DESC).

## X47

```sql
CREATE VIEW region_budgets_calc AS
SELECT
  job_id,
  budget_cents,
  region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  SUM(budget_cents) OVER (PARTITION BY region) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM region_budgets;
```

- RANK.EQ with order 1 ranks across the whole table, so there is no PARTITION on cheapest_first.
- SUMIF and AVERAGEIF become window functions. Each row keeps its place, where a GROUP BY would collapse them.
- Results: cheapest_first 2, 3, 4, 1 for jobs 1 to 4. region_total is 400 for eu and 350 for us.

## X48

```sql
-- Power Query "quiet_runs": job runs with no run_alerts row
CREATE VIEW quiet_runs AS
SELECT r.run_id, r.job_id, r.status
FROM job_runs r
LEFT JOIN (SELECT DISTINCT run_id FROM run_alerts) a
  ON a.run_id = r.run_id
WHERE a.run_id IS NULL;

-- Power Query "slow_regions": average and fastest per region, average >= 20
CREATE VIEW slow_regions AS
SELECT
  x.region,
  AVG(x.duration_mins) AS avg_mins,
  MIN(x.duration_mins) AS fastest
FROM (
  SELECT r.duration_mins, j.region
  FROM job_runs r
  INNER JOIN jobs j
    ON j.job_id = r.job_id
) x
GROUP BY x.region
HAVING AVG(x.duration_mins) >= 20;
```

- The left anti join is written as LEFT JOIN ... IS NULL, because Hive's LEFT ANTI JOIN depends on the version. The DISTINCT stops duplicate run_alerts rows from matching twice.
- quiet_runs gives runs 95, 96, 98 and 99. slow_regions gives NYC with 30 and 30.

## X49

```sql
-- Power Query "alert_status": every job run, with its alert if it has one
CREATE VIEW alert_status AS
SELECT a.alert_id, a.severity, r.status
FROM run_alerts a
RIGHT OUTER JOIN job_runs r
  ON r.run_id = a.run_id;

-- Power Query "run_check": job runs and scheduled runs, both sides kept
CREATE VIEW run_check AS
SELECT
  r.run_id,
  r.status,
  s.run_id AS scheduled_run
FROM (SELECT run_id, status FROM job_runs) r
FULL OUTER JOIN scheduler_runs s
  ON s.run_id = r.run_id;

-- Power Query "teams": distinct teams from jobs and job_owners
CREATE VIEW teams AS
SELECT DISTINCT team
FROM (
  SELECT team FROM jobs
  UNION ALL
  SELECT team FROM job_owners
) t;
```

- alert_status has 13 rows, one per run per alert, and one row for each run with no alert.
- run_check has 10 rows. Run 100 exists only in scheduler_runs, so its run_id is NULL.

## X50

```sql
-- Power Query "owners": distinct job_id and owner pairs, with job_name and newest_first
CREATE VIEW owners AS
SELECT
  o.job_id,
  o.owner,
  j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM (SELECT DISTINCT job_id, owner FROM job_owners) o
LEFT JOIN jobs j
  ON j.job_id = o.job_id;
```

- XLOOKUP becomes a LEFT JOIN on job_id.
- RANK.EQ defaults to descending, so the largest job_id gets rank 1, and the two job 3 rows share rank 2.

## X59

```sql
CREATE VIEW jobs_summary AS
SELECT
  j.job_id,
  j.job_name,
  SUM(CASE WHEN r.duration_mins >= 20 THEN 1 ELSE 0 END) AS long_runs,
  COALESCE(SUM(CASE WHEN lower(r.status) LIKE 'f%' THEN r.duration_mins END), 0) AS failed_mins,
  SUM(CASE WHEN r.run_id IS NOT NULL AND COALESCE(r.status, '') <> 'TEST' THEN 1 ELSE 0 END) AS not_test
FROM jobs j
LEFT JOIN job_runs r
  ON r.job_id = j.job_id
GROUP BY j.job_id, j.job_name;

CREATE VIEW run_alerts_running AS
SELECT
  a.alert_id,
  a.run_id,
  a.severity,
  a.dt,
  COUNT(b.alert_id) AS alerts_so_far
FROM run_alerts a
CROSS JOIN run_alerts b
WHERE b.run_id <= a.run_id
GROUP BY a.alert_id, a.run_id, a.severity, a.dt;
```

- SUMIFS with "f*" is a case-insensitive prefix match, so lower(status) LIKE 'f%' is the match.
- COUNTIFS with "<>TEST" counts blank statuses too. COALESCE(status, '') keeps them, and the run_id IS NOT NULL guard stops job 4, which has no runs, from counting 1.
- COUNTIFS with "<="&run_id becomes a self join with a WHERE, because Hive joins need equality conditions.
- Results: long_runs 1, 1, 2, 0. failed_mins 0, 20, 30, 0. not_test 3, 3, 2, 0.

## X60

```sql
CREATE VIEW region_budgets_calc AS
SELECT
  job_id,
  budget_cents,
  region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM region_budgets;

-- The Total row, which is a display row and not stored data
SELECT
  'Total' AS region,
  COUNT(job_id) AS job_id_count,
  AVG(budget_cents) AS avg_budget_cents
FROM region_budgets;
```

- COUNTIFS(... "<"&budget)+1 within a region is the same as RANK() ascending within that PARTITION, ties included.
- SUBTOTAL(103) counts non-blank job_id values, which is COUNT. SUBTOTAL(101) is AVERAGE.
- Results: share 0.20, 0.27, 0.47, 0.07. above_avg false, true, true, false. rank_in_region 2, 3, 1, 1. The Total row shows 4 and 187.5.

## X61

```sql
CREATE VIEW by_region AS
SELECT
  region,
  SUM(cost_cents) AS total_cents,
  COUNT(*) AS entries,
  MAX(cost_cents) AS priciest
FROM region_costs
GROUP BY region;

-- The Total row
SELECT
  SUM(total_cents) AS total_cents,
  SUM(entries) AS entries,
  MAX(priciest) AS priciest
FROM by_region;
```

- COUNT(*) counts the row with a blank cost, as COUNTIFS does. SUM and MAX skip it, as SUMIFS and MAXIFS do.
- SUBTOTAL(109) is SUM and SUBTOTAL(104) is MAX.
- Results: eu 3460, 24 entries, priciest 250. us 1160, 4 entries, priciest 410. Total row 4620, 28, 410.

## X62

```sql
CREATE VIEW team_notes_calc AS
SELECT
  team,
  note,
  written_on,
  date_sub(written_on, pmod(datediff(written_on, '1970-01-05'), 7)) AS week_of,
  last_day(written_on) AS month_end,
  trunc(written_on, 'MM') AS month_of,
  (year(written_on) - 2026) * 12 + (month(written_on) - 1) AS months_in,
  date_sub(written_on, 3) AS three_before,
  initcap(team) AS who,
  concat_ws(': ', team, substr(note, 1, 5)) AS short
FROM team_notes;
```

- WEEKDAY(date, 2) minus 1 is the number of days back to Monday. 1970-01-05 was a Monday, so the day count from it, modulo 7, gives the same offset.
- DATEDIF(DATE(2026,1,1), d, "m") counts whole months from 1 January 2026. The start is on the 1st, so it is the year and month difference.
- TEXTJOIN with ignore-empty is concat_ws, which skips NULLs. The notes are never empty.
- Sample row (web, 2026-09-11): week_of 2026-09-07, month_end 2026-09-30, month_of 2026-09-01, months_in 8, three_before 2026-09-08, who Web, short "web: cache".

## X63

```sql
CREATE VIEW job_runs_calc AS
SELECT
  r.run_id,
  r.job_id,
  r.status,
  r.duration_mins,
  r.avg_retry_secs,
  r.avg_retry_secs IS NULL AS no_retry,
  floor(r.duration_mins / 4) AS quarters,
  CASE WHEN r.duration_mins < 25 THEN r.duration_mins ELSE 25 END AS capped,
  var_samp(r.duration_mins) OVER () AS variance,
  SUM(r.duration_mins * r.job_id) OVER () AS weighted,
  COALESCE(s.job_id, -1) AS scheduled_job,
  concat('run ', r.run_id) AS label,
  COALESCE(lower(r.status) LIKE '%cess%', false) AS succeeded
FROM job_runs r
LEFT JOIN scheduler_runs s
  ON s.run_id = r.run_id;
```

- VAR.S is var_samp. Over the nine durations it is 127.25.
- SUMPRODUCT of duration and job_id over the whole table is a SUM ... OVER (), the same value (353) on every row.
- SEARCH("cess") becomes a case-insensitive LIKE. A blank status gives false, as ISNUMBER(SEARCH) does.
- XLOOKUP with -1 as the not-found value becomes COALESCE(..., -1), so run 99 gets -1.

## X64

```sql
CREATE VIEW picked_costs AS
SELECT
  job_id,
  cost_cents,
  upper(region) AS region,
  CASE WHEN cost_cents >= 200 THEN 'big' ELSE 'small' END AS `size`
FROM region_costs
WHERE cost_cents IS NOT NULL
  AND job_id IN (1, 3);

CREATE VIEW costed_jobs AS
SELECT job_id, job_name, team, region
FROM jobs
WHERE job_id IN (SELECT job_id FROM region_costs)
  AND job_name NOT LIKE 'n%';

CREATE VIEW costs_filled AS
SELECT
  job_id,
  COALESCE(cost_cents, 0) AS cost_cents,
  dt,
  substr(CAST(dt AS STRING), -2) AS `day`
FROM region_costs;
```

- Text.StartsWith(name, "n") becomes NOT LIKE 'n%'. costed_jobs returns invoice_sync and report_build.
- Table.ReplaceValue of null with 0 becomes COALESCE(cost_cents, 0).
- Text.End(dt, 2) becomes substr of the cast string with a start of -2.

## X65

```sql
-- Power Query "team_regions": every team with every region
CREATE VIEW team_regions AS
SELECT t.team, r.region
FROM (SELECT DISTINCT team FROM jobs) t
CROSS JOIN (SELECT DISTINCT region FROM jobs) r;

-- Power Query "budget_places": rank by budget, highest first
CREATE VIEW budget_places AS
SELECT
  job_id,
  budget_cents,
  region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM region_budgets;

-- Power Query "jobs_per_team": distinct jobs per team
CREATE VIEW jobs_per_team AS
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM job_owners
GROUP BY team;

-- Power Query "ran_as_scheduled": scheduled runs that match a job run on run_id and dt
CREATE VIEW ran_as_scheduled AS
SELECT DISTINCT s.run_id, s.dt
FROM scheduler_runs s
INNER JOIN job_runs r
  ON r.run_id = s.run_id
 AND r.dt = s.dt;

-- Power Query "run_measures": both measures stacked into one measure column
CREATE VIEW run_measures AS
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM job_runs
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM job_runs;
```

- Hive has no UNPIVOT, so Table.Unpivot becomes UNION ALL.
- The run_measures query as written gives 18 rows, both measures for 9 runs. The cached sheet holds only the nine duration_mins rows, so the sheet is out of step with its query. The SQL follows the query.
- team_regions and budget_places are views, so they have no guaranteed order. Add ORDER BY when you query them.
- jobs_per_team gives data 2, finance 2, web 1. ran_as_scheduled gives 8 rows, as the sheet does.

## X66

```sql
CREATE VIEW ok_runs_loaded AS
SELECT run_id, job_id, duration_mins, dt
FROM job_runs
WHERE status IS NOT NULL
  AND status LIKE 'SUCC%';

CREATE VIEW ok_runs AS
SELECT
  run_id,
  job_id,
  duration_mins,
  dt,
  SUM(duration_mins) OVER (
    PARTITION BY job_id
    ORDER BY dt
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM ok_runs_loaded;

-- The Total row
SELECT SUM(duration_mins) AS duration_mins
FROM ok_runs_loaded;
```

- SUMIFS with "<="&dt includes every row of the same job on the same date. RANGE ... CURRENT ROW does the same, since it includes peers.
- Results: running 12, 18, 62, 30, 62. The 62 on both job 1 rows on 2026-09-24 is correct, as run 104 falls on the same date as run 101. share is each duration over 110.

## X69

```sql
CREATE VIEW region_costs_calc AS
SELECT
  c.job_id,
  c.cost_cents,
  c.region,
  c.dt,
  j.job_name,
  b.budget_cents AS budget,
  COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
  SUM(c.cost_cents) OVER (
    PARTITION BY c.job_id
    ORDER BY c.dt
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS running_cost
FROM region_costs c
LEFT JOIN jobs j
  ON j.job_id = c.job_id
LEFT JOIN region_budgets b
  ON b.job_id = c.job_id;

CREATE VIEW job_totals_calc AS
SELECT
  t.job_id,
  COALESCE(SUM(c.cost_cents), 0) AS total_cents,
  COALESCE(SUM(CASE WHEN c.over_budget THEN 1 ELSE 0 END), 0) AS over_count
FROM job_totals t
LEFT JOIN region_costs_calc c
  ON c.job_id = t.job_id
GROUP BY t.job_id;

CREATE VIEW late_costs AS
SELECT job_id, dt, running_cost
FROM region_costs_calc
WHERE running_cost > 1500;

-- The Total row
SELECT
  SUM(total_cents) AS total_cents,
  SUM(over_count) AS over_count
FROM job_totals_calc;
```

- The budget is looked up per job, not per region, as the formula does.
- A blank cost compares as 0 in Excel, so COALESCE(cost_cents, 0) gives the same over_budget.
- Results: job totals 1770 (1 over), 1690 (2 over), 1160 (1 over). The Total row is 4620 and 4.
- late_costs gives six rows: job 1 on 22, 23 and 24 September with running cost 1550, 1670 and 1770, and job 2 on the same dates with 1510, 1690 and 1690.
- The cached late_costs sheet shows cost values (100, 120, 100, 180, 180, blank), not running costs above 1500. The sheet does not match its query, and the SQL follows the query.

## X70

```sql
CREATE VIEW staffed AS
SELECT j.job_id, j.job_name, o.owner
FROM jobs j
INNER JOIN (SELECT DISTINCT job_id, owner FROM job_owners) o
  ON o.job_id = j.job_id
WHERE o.owner IS NOT NULL;

CREATE VIEW owner_load AS
SELECT
  x.owner,
  x.total_mins,
  x.runs,
  x.total_mins / x.runs AS avg_mins
FROM (
  SELECT
    s.owner,
    SUM(r.duration_mins) AS total_mins,
    COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN job_runs r
    ON r.job_id = s.job_id
  GROUP BY s.owner
) x;

CREATE VIEW busiest_owner AS
SELECT owner, total_mins, runs
FROM owner_load
ORDER BY runs DESC
LIMIT 1;

-- The Total row
SELECT SUM(runs) AS runs
FROM owner_load;
```

- Job 3 has two owners (ana and chloe), so its runs count for both, as the Power Query's join does. COUNT(*) matches Table.RowCount.
- Results: ana 127 minutes over 6 runs (avg 21.17), ben 53 over 3 (17.67), chloe 60 over 2 (30). The Total row is 11, and busiest_owner is ana.
