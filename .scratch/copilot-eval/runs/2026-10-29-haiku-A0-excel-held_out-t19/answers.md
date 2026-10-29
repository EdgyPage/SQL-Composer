date: 2026-10-29
arm: A0
model: haiku
files: none

## X21

Each calculated column becomes an expression in the SELECT. The structured references become plain column names. Hive's `/` returns a double, as Excel's does.

```sql
SELECT
  job_id,
  budget_cents,
  region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM region_budgets;
```

Note: Hive returns the raw floating-point value (150 * 1.1 is 165.00000000000003). Wrap it in `ROUND(..., 2)` if you want Excel's displayed value.

## X22

```sql
SELECT
  job_id,
  job_name,
  team,
  CASE WHEN LOWER(team) = 'finance' THEN 'yes' ELSE 'no' END AS is_finance,
  COALESCE(job_id / (job_id - 2), 0) AS ratio
FROM jobs;
```

Notes:
- Excel's `=` on text ignores case, so `LOWER` is used to match it. Hive's `=` does not.
- Hive's `/` returns NULL on divide by zero, so `COALESCE(..., 0)` stands in for `IFERROR(..., 0)`. Only job 2 hits the zero divisor, and it gets 0.

## X23

```sql
SELECT
  run_id,
  status,
  avg_retry_secs,
  CASE
    WHEN status = 'SUCCESS' THEN 'ok'
    WHEN status = 'FAILED' THEN 'bad'
    ELSE 'other'
  END AS label,
  (COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5) AS risky
FROM job_runs;
```

Notes:
- `SWITCH` becomes a `CASE` with the default as `ELSE 'other'`. Run 98, with a blank status, gets `other`.
- A blank `avg_retry_secs` counts as 0 in Excel. The `COALESCE` calls keep `risky` at FALSE instead of NULL for run 98.

## X24

```sql
SELECT
  team,
  note,
  written_on,
  SUBSTR(note, 1, INSTR(note, ' ') - 1) AS first_word,
  UPPER(team) AS shout,
  MONTH(written_on) AS month,
  ROUND(LENGTH(note) / 10, 1) AS tens_of_chars
FROM team_notes;
```

Notes:
- `FIND` maps to `INSTR`. Both are 1-based. `LEFT(x, n)` maps to `SUBSTR(x, 1, n)`.
- `MONTH` accepts a `yyyy-mm-dd` string. If `written_on` is a DATE column, the same call works.
- If a note had no space, `INSTR` returns 0 and the result is an empty string where Excel shows `#VALUE!`. All six notes contain a space.

## X25

Excel's column names contain spaces and parentheses, which Hive does not allow. The Hive tables are assumed to be `costs` (job, cost_cents, region, day_key) and `budgets` (job, budget, region, dollars), with the names snake-cased.

```sql
CREATE VIEW costs_dated AS
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
    ) AS DATE
  ) AS day
FROM costs;

CREATE VIEW budgets_dollars AS
SELECT
  job,
  budget,
  region,
  budget / 100 AS dollars
FROM budgets;
```

The `DATE(LEFT, MID, RIGHT)` in Excel is rebuilt as a `yyyy-mm-dd` string and cast to DATE.

## X26

```sql
WITH job_avg AS (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM job_runs
  GROUP BY job_id
)
SELECT
  a.alert_id,
  a.run_id,
  a.severity,
  r.job_id,
  r.status,
  j.avg_mins
FROM run_alerts a
LEFT JOIN job_runs r ON a.run_id = r.run_id
LEFT JOIN job_avg j ON r.job_id = j.job_id;
```

Notes:
- The `XLOOKUP` for `job_id` and the `VLOOKUP` for `status` both become one join on `run_id`. `run_id` is unique in `job_runs`.
- `AVERAGEIFS` by job becomes a pre-aggregated average joined on `job_id`. It includes TEST runs, as the Excel formula does.

## X27

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
JOIN jobs j ON t.last_job_id = j.job_id;
```

Notes: `COUNTIFS` becomes `COUNT` per team, and `MAXIFS` becomes `MAX` per team. The `INDEX`/`MATCH` becomes a join on `job_id`. Expected output: data 1 nightly_load, finance 2 report_build, web 1 cache_warm.

## X28

```sql
SELECT
  j.job_id,
  j.job_name,
  CASE
    WHEN j.job_id = 3 THEN 99
    ELSE COALESCE(s.ok_mins, 0)
  END AS ok_mins
FROM jobs j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS ok_mins
  FROM job_runs
  WHERE status = 'SUCCESS'
  GROUP BY job_id
) s ON j.job_id = s.job_id;
```

Notes:
- `SUMIFS` becomes a `SUM` with a `WHERE status = 'SUCCESS'`. `COALESCE` gives 0 where Excel's `SUMIFS` finds no rows.
- Row 3 (report_build) is a typed 99 in the workbook, not a formula. I kept it as typed. The formula pattern would give 30, from run 103. Check which one is intended.
- The Keys table (jobs | job_id) only declares the key. It is not a calculation.

## X29

```sql
SELECT
  r.job_id,
  r.budget_cents,
  r.region,
  CASE
    WHEN r.job_id = 3 THEN 5
    ELSE r.budget_cents / p.cents_per_dollar
  END AS in_dollars,
  r.job_id AS pointer
FROM region_budgets r
CROSS JOIN (
  SELECT CAST(value AS DOUBLE) AS cents_per_dollar
  FROM parameters
  WHERE name = 'cents_per_dollar'
) p;
```

Notes:
- The `XLOOKUP` into Parameters becomes a one-row join on `parameters`, which holds `cents_per_dollar` = 100.
- `INDIRECT("A"&ROW())` returns the value in column A of the same row, which is `job_id`. Hive uses `job_id` directly. `INDIRECT` is volatile and fragile, so it has no direct equivalent.
- Row 3 (job 3) has a typed 5 in `in_dollars`. The formula would give 3.5. I kept the typed value. Check which one is intended.

## X30

```sql
SELECT
  run_id,
  job_id,
  dt,
  SUBSTR(dt, 9, 2) AS day,
  LAG(run_id) OVER (ORDER BY run_id) AS prev_run,
  CAST(FLOOR(RAND() * 5) + 1 AS INT) AS jitter
FROM scheduler_runs;
```

Notes:
- `RIGHT(dt, 2)` becomes `SUBSTR(dt, 9, 2)` for a `yyyy-mm-dd` string.
- `OFFSET(run_id, -1, 0)` reads the row above, so it becomes `LAG` over row order. The table is in run_id order. In Excel, the first row's offset lands on the header text "run_id". Hive returns NULL there.
- `RANDBETWEEN(1, 5)` becomes `FLOOR(RAND() * 5) + 1`. Like Excel, it gives new values on every run. Store the values if they must stay fixed.
- The PivotTable on the Pivot sheet is not Hive SQL. The equivalent is:

```sql
SELECT job_id, COUNT(run_id) AS runs
FROM scheduler_runs
GROUP BY job_id;
```

- The bar chart on the Summary sheet has no SQL equivalent.

## X31

```sql
SELECT
  job_id,
  team,
  CAST(NULL AS INT) AS bump,
  CONCAT(UPPER(team), '!') AS tag,
  job_id * 7 AS scaled,
  job_id * 10 AS boosted
FROM jobs;
```

Notes:
- `bump` refers to its own column, `=jobs[[#This Row],[bump]]*2`. That is a circular reference, so the workbook has no value for it. Excel shows 0 with a warning. Hive returns NULL here. Fix the source formula before converting this column.
- The `TAG` LAMBDA is inlined as `CONCAT(UPPER(team), '!')`.
- `Summary!$D$4` is 7 and the defined name `boost` (Summary!$B$2) is 10. Both are written as literals here. If they need to change, move them into a parameters table.

## X32

```sql
CREATE VIEW job_runs_named AS
SELECT
  r.run_id,
  r.job_id,
  r.status,
  r.duration_mins,
  r.avg_retry_secs,
  r.dt,
  j.job_name
FROM job_runs r
LEFT JOIN jobs j ON r.job_id = j.job_id;

SELECT
  b.job_name,
  COUNT(r.run_id) AS runs
FROM by_name b
LEFT JOIN job_runs_named r ON b.job_name = r.job_name
GROUP BY b.job_name;
```

Notes:
- The approximate `VLOOKUP(..., TRUE)` is a plain join here. Every job_id in the runs exists in `jobs`, so the approximate match gives the same rows as an exact one.
- `COUNT(r.run_id)` is used rather than `COUNT(*)`, so a name with no runs gives 0 instead of 1.
- Expected output: invoice_sync 3, nightly_load 4, report_build 2.

## X33

The table is loaded by a Power Query that reads `ops.job_runs` from a SQL Server database. Hive cannot reach that source. This view assumes the same table is available in Hive as `ops.job_runs`.

```sql
CREATE VIEW slow_runs AS
SELECT
  run_id,
  duration_mins,
  duration_mins - 20 AS over_by
FROM ops.job_runs
WHERE duration_mins >= 20
  AND status <> 'TEST';
```

The view returns runs 97, 102, 103 and 104, with over_by 10, 0, 10 and 20. That matches the cached Excel table.

## X34

```sql
CREATE VIEW runs_with_team AS
SELECT
  r.run_id,
  r.job_id,
  r.status,
  r.duration_mins,
  r.avg_retry_secs,
  r.dt,
  j.team
FROM job_runs r
LEFT JOIN jobs j ON r.job_id = j.job_id;

CREATE VIEW team_totals AS
SELECT
  team,
  SUM(duration_mins) AS total_mins,
  MAX(duration_mins) AS longest
FROM runs_with_team
GROUP BY team;
```

Notes: `runs_with_team` is the connection-only query and becomes a view. `team_totals` is the `Table.Group`, which becomes `SUM` and `MAX` per team. Expected output: data 67 and 40, finance 113 and 30.

## X35

```sql
CREATE VIEW recent AS
SELECT run_id, dt
FROM (
  SELECT run_id, dt FROM job_runs
  UNION ALL
  SELECT run_id, dt FROM scheduler_runs
) both_runs
ORDER BY run_id DESC
LIMIT 4;
```

Notes:
- The `recent` query combines the two tables, sorts by run_id descending, and keeps the top 4. Ties at 104 and 103 are kept as the cached table shows: 104, 104, 103, 103.
- The "rates" query fetches `https://rates.example.com/today.json` over the web. Hive cannot make that call, so it is left out of the SQL. No table in this workbook uses it.

## X36

```sql
CREATE VIEW severity_by_day AS
SELECT
  dt,
  SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) AS low
FROM run_alerts
GROUP BY dt;

SELECT
  r.run_id,
  r.status,
  COUNT(a.alert_id) AS alerts
FROM job_runs r
LEFT JOIN run_alerts a ON a.run_id = r.run_id
GROUP BY r.run_id, r.status;
```

Notes:
- `Table.Pivot` becomes one conditional `SUM` per severity column. For 2026-09-23 that gives high 1 and low 1. For 2026-09-24 it gives high 2 and low 5. Both match the cached table.
- The pivot columns are fixed in SQL. A new severity value would need a new column.
- `COUNTIFS` on the job_runs `alerts` column becomes a `LEFT JOIN` and `COUNT`, so runs with no alerts show 0.

## X37

```sql
SELECT
  job_no,
  team_name,
  owner,
  day,
  CASE WHEN LOWER(owner) = 'ana' THEN 1 ELSE 0 END AS is_ana
FROM owners;
```

Notes:
- The Excel headers with spaces ("Job No", "Team Name", "Is Ana") are renamed to snake case for Hive.
- `IF(... = "ana")` ignores case in Excel, so `LOWER` is used. A blank owner gives 0.

## X38

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
LEFT JOIN jobs j ON r.job_id = j.job_id;
```

Notes:
- `XLOOKUP` for region becomes a join on `jobs`.
- `SUMIFS` by region becomes a window `SUM` over the region partition.
- Row 8 (run 102) has a typed 1 for `retry_cost`. The formula would give 52. I kept the typed value. Check which one is intended.
- A blank `avg_retry_secs` counts as 0, as in Excel. That is why `COALESCE` is used.

## X39

```sql
CREATE VIEW ok_runs AS
SELECT run_id, job_id, duration_mins
FROM job_runs
WHERE status = 'SUCCESS';

SELECT
  o.run_id,
  o.job_id,
  o.duration_mins,
  j.job_name,
  o.duration_mins / SUM(o.duration_mins) OVER (PARTITION BY o.job_id) AS share,
  RAND() AS noise
FROM ok_runs o
LEFT JOIN jobs j ON o.job_id = j.job_id;
```

Notes:
- `ok_runs` is the Power Query result, so `share` sums over the rows of that view, as the Excel `SUMIFS` does.
- `RAND()` is random on every query. `noise` has no stable equivalent, so do not rely on it.

## X40

```sql
CREATE VIEW runs_costed AS
SELECT
  r.run,
  r.job,
  r.mins,
  j.team,
  r.mins * p.rate AS cost
FROM runs r
LEFT JOIN jobs j ON r.job = j.job_id
CROSS JOIN (
  SELECT CAST(value AS DOUBLE) AS rate
  FROM parameters
  WHERE name = 'rate'
) p;

SELECT
  t.team,
  SUM(c.cost) AS total_cost
FROM teams t
LEFT JOIN runs_costed c ON c.team = t.team
GROUP BY t.team;

SELECT
  a.alert_id,
  a.run_id,
  a.severity,
  a.dt,
  r.mins AS run_mins
FROM run_alerts a
LEFT JOIN runs r ON a.run_id = r.run;
```

Notes:
- `XLOOKUP` for team becomes a join on `jobs`. The rate of 2 comes from `parameters`, joined as a one-row subquery.
- The Teams sheet's `SUMIFS` becomes a `SUM` per team. Expected output: data 134 and finance 226.
- The PivotTable on the Pivot sheet has no Hive equivalent. The grouped query above gives the same numbers.
- The `run_alerts` lookup of `Run Mins` becomes a join on run. Each alert's run exists in `runs`.

## X46

```sql
WITH run_stats AS (
  SELECT
    job_id,
    MIN(duration_mins) AS shortest,
    COUNT(*) AS runs
  FROM job_runs
  GROUP BY job_id
)
SELECT
  j.job_id,
  j.job_name,
  j.team,
  COALESCE(s.shortest, 0) AS shortest,
  COALESCE(s.runs, 0) AS runs,
  RANK() OVER (ORDER BY COALESCE(s.runs, 0) DESC) AS busiest
FROM jobs j
LEFT JOIN run_stats s ON j.job_id = s.job_id;
```

Notes:
- `MINIFS` becomes `MIN` per job. `COALESCE` gives 0 for cache_warm, which has no runs, as `MINIFS` does.
- `COUNTIF` becomes `COUNT` per job.
- `RANK.EQ` with the default descending order becomes `RANK() ... DESC`. Ties share a rank, as in Excel.

## X47

```sql
SELECT
  job_id,
  budget_cents,
  region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  SUM(budget_cents) OVER (PARTITION BY region) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM region_budgets;
```

Notes:
- `RANK.EQ(..., 1)` with order 1 means ascending, so it becomes `RANK() ... ASC`.
- `SUMIF` and `AVERAGEIF` by region become window `SUM` and `AVG` over the region partition, keeping every row.
- Expected output: cheapest_first 1 for job 4 (50), 2 for job 1, 3 for job 2, 4 for job 3. Region totals are eu 400 and us 350.

## X48

```sql
CREATE VIEW quiet_runs AS
SELECT r.run_id, r.job_id, r.status
FROM job_runs r
LEFT JOIN run_alerts a ON a.run_id = r.run_id
WHERE a.run_id IS NULL;

CREATE VIEW slow_regions AS
SELECT
  j.region,
  AVG(r.duration_mins) AS avg_mins,
  MIN(r.duration_mins) AS fastest
FROM job_runs r
JOIN jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20;
```

Notes:
- The left anti join is written as a `LEFT JOIN` with `IS NULL`. It returns runs 95, 96, 98 and 99.
- `Table.Group` plus `Table.SelectRows` becomes `GROUP BY` plus `HAVING`. Only NYC passes (average 30, fastest 30). LON averages 16.75 and PAR averages 17.67.

## X49

```sql
CREATE VIEW alert_status AS
SELECT
  a.alert_id,
  a.severity,
  r.status
FROM run_alerts a
RIGHT OUTER JOIN job_runs r ON a.run_id = r.run_id;

CREATE VIEW run_check AS
SELECT
  r.run_id,
  r.status,
  s.run_id AS scheduled_run
FROM (SELECT run_id, status FROM job_runs) r
FULL OUTER JOIN scheduler_runs s ON r.run_id = s.run_id;

CREATE VIEW teams AS
SELECT team FROM jobs
UNION
SELECT team FROM job_owners;
```

Notes:
- `alert_status` is a right outer join, so every run stays. Runs with no alert get NULL for alert_id and severity. This gives 13 rows, as the cached table does.
- `run_check` is a full outer join. Run 99 has no scheduled run. Scheduled run 100 has no job run, so its run_id is NULL.
- `teams` is the distinct union of the two team columns, which `UNION` gives. Teams are data, finance and web.

## X50

```sql
CREATE VIEW owners AS
SELECT DISTINCT job_id, owner
FROM job_owners;

SELECT
  o.job_id,
  o.owner,
  j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM owners o
LEFT JOIN jobs j ON o.job_id = j.job_id;
```

Notes:
- `Table.Distinct` on (job_id, owner) becomes `SELECT DISTINCT`. The blank owner of job 4 stays as a NULL row. Five rows result.
- `XLOOKUP` for job_name becomes a join on `jobs`.
- `RANK.EQ` with no order argument ranks the largest first, so it becomes `RANK() ... DESC` over all rows. Both job 3 rows get rank 2.
