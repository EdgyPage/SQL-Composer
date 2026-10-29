date: 2026-10-29
arm: A0
model: haiku
files: none

## X21

Each column is a row-level formula, so each one becomes an expression in a SELECT over the `region_budgets` table. The Steps, Parameters and Keys sheets hold no calculations here (Parameters and Keys are empty).

```sql
SELECT
  job_id,
  budget_cents,
  region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM region_budgets;
```

Hive's `/` returns a decimal, so 150 / 100 gives 1.5 as Excel does.

## X22

Each column is a row-level formula over the `jobs` table. Hive has no IFERROR, so the division is guarded with a CASE on the zero denominator.

```sql
SELECT
  job_id,
  job_name,
  team,
  CASE WHEN team = 'finance' THEN 'yes' ELSE 'no' END AS is_finance,
  CASE WHEN job_id - 2 = 0 THEN 0 ELSE job_id / (job_id - 2) END AS ratio
FROM jobs;
```

- Excel's `=` ignores case, so "Finance" matches there. Hive's `=` is case-sensitive; use `lower(team) = 'finance'` if the case can vary.
- Expected ratios are -1, 0 (the job 2 case, where Excel's IFERROR returns 0), 3 and 2.

## X23

SWITCH becomes a CASE with the same default, and OR becomes a boolean OR with blanks treated as Excel treats them.

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
  (COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5) AS risky
FROM job_runs;
```

- The blank status on run 98 and the TEST status on run 99 both fall to 'other', as in Excel.
- Excel reads a blank `avg_retry_secs` as 0. The COALESCE does the same; without it, Hive would return NULL where Excel returns FALSE.

## X24

LEFT, FIND, MID-style slicing, LEN, MONTH and ROUND each have a Hive counterpart, so the formulas map one to one.

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

- LEFT(note, FIND(" ", note) - 1) becomes substr with instr. Hive has no FIND, and instr returns 0 when there is no space, where Excel would return an error.
- MONTH works on a 'yyyy-mm-dd' string as well as a date.

## X25

The DATE formula is rebuilt from the Day Key text, and the Dollars column is a divide by 100. Column names with spaces become snake_case names in Hive.

```sql
CREATE VIEW costs_dated AS
SELECT
  job,
  cost_cents,
  region,
  day_key,
  to_date(concat(
    substr(CAST(day_key AS STRING), 1, 4), '-',
    substr(CAST(day_key AS STRING), 5, 2), '-',
    substr(CAST(day_key AS STRING), 7, 2)
  )) AS day
FROM costs;

CREATE VIEW budgets_dollars AS
SELECT
  job,
  budget,
  region,
  budget / 100 AS dollars
FROM budgets;
```

- The blank cost on the last Costs row stays NULL, so it adds nothing to a SUM.

## X26

XLOOKUP becomes a join on run_id, and the AVERAGEIFS over job_runs becomes a per-job average joined on job_id. Computing the average once per job is cheaper than a correlated subquery, which older Hive does not support.

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
  ja.avg_mins
FROM run_alerts a
LEFT JOIN job_runs r
  ON a.run_id = r.run_id
LEFT JOIN job_avg ja
  ON r.job_id = ja.job_id;
```

- The VLOOKUP with column 3 returns `status` (column 3 of job_runs), which matches the status column header.
- A run_id with no match gives NULL, where Excel gives #N/A.

## X27

COUNTIFS and MAXIFS become COUNT and MAX with GROUP BY. The INDEX/MATCH becomes a join, since job_id is unique.

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
  s.team,
  s.jobs_in_team,
  s.last_job_id,
  j.job_name AS last_job_name
FROM team_stats s
LEFT JOIN jobs j
  ON j.job_id = s.last_job_id;
```

- Expected output: data 1 job (last job 1, nightly_load), finance 2 jobs (last job 3, report_build), web 1 job (last job 4, cache_warm).

## X28

SUMIFS becomes a filtered SUM per job, joined back to jobs. Jobs with no successful runs get 0.

```sql
SELECT
  j.job_id,
  j.job_name,
  COALESCE(s.ok_mins, 0) AS ok_mins
FROM jobs j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS ok_mins
  FROM job_runs
  WHERE status = 'SUCCESS'
  GROUP BY job_id
) s
  ON s.job_id = j.job_id;
```

- The report_build row has a typed 99 in ok_mins instead of the formula. The query follows the formula, which gives 30 for job 3 (run 103 is its only successful run), so the 99 is not reproduced. Please confirm whether the 99 was meant to stay.
- The Keys sheet names jobs.job_id as the key. It does not change the SQL.

## X29

XLOOKUP becomes a single-row join to parameters, and INDIRECT is replaced by the value it reads.

```sql
SELECT
  r.job_id,
  r.budget_cents,
  r.region,
  r.budget_cents / p.value AS in_dollars,
  r.job_id AS pointer
FROM region_budgets r
CROSS JOIN (
  SELECT value FROM parameters WHERE name = 'cents_per_dollar'
) p;
```

- INDIRECT("A"&ROW()) reads column A of the same row, which holds job_id, so pointer is job_id. Hive has no INDIRECT or cell addresses.
- The row for job 3 has a typed 5 in in_dollars instead of the formula. The query gives 3.5 (350 / 100). Please confirm whether the typed 5 was meant.

## X30

RIGHT becomes substr. OFFSET one row up becomes LAG over run_id, and RANDBETWEEN becomes a RAND-based expression.

```sql
SELECT
  run_id,
  job_id,
  dt,
  substr(dt, 9, 2) AS day,
  LAG(run_id) OVER (ORDER BY run_id) AS prev_run,
  CAST(FLOOR(RAND() * 5) + 1 AS INT) AS jitter
FROM scheduler_runs;

SELECT
  job_id,
  COUNT(run_id) AS count_of_run_id
FROM scheduler_runs
GROUP BY job_id;
```

- The first row's prev_run is NULL. Excel's OFFSET reads the header cell there, so it would show the text "run_id".
- jitter changes on every run, as RANDBETWEEN does in Excel. Store the values in a table if they must stay fixed.
- The second query is the PivotTable (rows job_id, count of run_id). The Summary bar chart is not SQL, so build it in a BI tool.

## X31

The jobs table has three things to convert. The tag LAMBDA becomes an inline expression, and the two Summary references become constants.

```sql
SELECT
  job_id,
  team,
  concat(upper(team), '!') AS tag,
  job_id * 7 AS scaled,
  job_id * 10 AS boosted
FROM jobs;
```

- The bump column refers to itself (bump = bump * 2), which is a circular reference. Excel cannot calculate it, so there is no Hive version to give. I left it out. Please tell me which base column bump should double.
- scaled uses Summary!D4 (7), and boosted uses the name boost, Summary!B2 (10). Both are typed in as constants. If they must change, move them into a parameters table and join to it.

## X32

VLOOKUP with an approximate match becomes a join on job_id, and COUNTIFS becomes a COUNT over the joined rows.

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
LEFT JOIN jobs j
  ON r.job_id = j.job_id;

SELECT
  b.job_name,
  COUNT(n.run_id) AS runs
FROM by_name b
LEFT JOIN job_runs_named n
  ON n.job_name = b.job_name
GROUP BY b.job_name;
```

- Expected output: invoice_sync 3, nightly_load 4, report_build 2.
- The approximate VLOOKUP would return the nearest smaller job_id for an id missing from jobs. The join returns NULL there. For ids 1 to 4 the results are the same.

## X33

Power Query has no Hive form, so the view stands in for it. The Sql.Database source becomes the job_runs table, and the filter, added column and column list become WHERE, an expression and a select list.

```sql
CREATE VIEW slow_runs AS
SELECT
  run_id,
  duration_mins,
  duration_mins - 20 AS over_by
FROM job_runs
WHERE duration_mins >= 20
  AND COALESCE(status, '') <> 'TEST';
```

- COALESCE keeps rows with a blank status, as the M filter does. Without it, SQL's `<>` drops them.
- The view gives runs 97, 102, 103 and 104, with over_by 10, 0, 10 and 20, matching the table.

## X34

The runs_with_team query becomes a view with a LEFT JOIN, and team_totals becomes a GROUP BY over that view.

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
LEFT JOIN jobs j
  ON r.job_id = j.job_id;

CREATE VIEW team_totals AS
SELECT
  team,
  SUM(duration_mins) AS total_mins,
  MAX(duration_mins) AS longest
FROM runs_with_team
GROUP BY team;
```

- Expected output: data 67 and 40, finance 113 and 30, as in the table.

## X35

Table.Combine is a UNION ALL, the descending sort is ORDER BY, and FirstN 4 is LIMIT 4.

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

- The output is 104, 104, 103, 103, as in the table. The two rows that tie on each run_id have the same dt, so the order between them does not change the result.
- The rates query fetches a web address. Hive cannot do that, and no table loads from it, so I left it out. If the rates are needed in Hive, load the JSON into a table first.

## X36

The pivot becomes a conditional SUM per severity. COUNTIFS becomes a COUNT over a LEFT JOIN, so a run with no alerts shows 0.

```sql
CREATE VIEW severity_by_day AS
SELECT
  dt,
  SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) AS low
FROM run_alerts
GROUP BY dt;

SELECT
  j.run_id,
  j.status,
  COUNT(a.alert_id) AS alerts
FROM job_runs j
LEFT JOIN run_alerts a
  ON a.run_id = j.run_id
GROUP BY j.run_id, j.status;
```

- SQL has no dynamic pivot, so the severity values (high, low) are typed in. A new severity needs a new column.
- Expected severity_by_day: 2026-09-23 high 1 and low 1; 2026-09-24 high 2 and low 5.

## X37

IF becomes CASE, and the column names with spaces become snake_case names.

```sql
SELECT
  job_no,
  team_name,
  owner,
  day,
  CASE WHEN owner = 'ana' THEN 1 ELSE 0 END AS is_ana
FROM owners;
```

- A blank owner gives 0, as in Excel.
- Excel's `=` ignores case, but Hive's does not. Use `lower(owner) = 'ana'` if the case of the owner names can vary.

## X38

XLOOKUP becomes a join to jobs for region. The SUMIFS over the region becomes a per-region total joined back to each run.

```sql
WITH runs AS (
  SELECT
    r.run_id,
    r.job_id,
    r.status,
    r.duration_mins,
    r.avg_retry_secs,
    j.region
  FROM job_runs r
  LEFT JOIN jobs j
    ON r.job_id = j.job_id
),
region_totals AS (
  SELECT region, SUM(duration_mins) AS region_mins
  FROM runs
  GROUP BY region
)
SELECT
  r.run_id,
  r.job_id,
  r.status,
  r.duration_mins,
  r.avg_retry_secs,
  r.region,
  t.region_mins,
  (COALESCE(r.avg_retry_secs, 0) + r.duration_mins) * 2 AS retry_cost
FROM runs r
LEFT JOIN region_totals t
  ON r.region = t.region;
```

- A blank avg_retry_secs counts as 0, as in Excel.
- The retry_cost for run 102 is a typed 1 instead of the formula. The query gives 52, which is (6 + 20) * 2. Please confirm whether the typed 1 was meant.

## X39

The Power Query becomes a view with a WHERE. The share column becomes a window SUM per job, which covers the same rows as the SUMIFS.

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
LEFT JOIN jobs j
  ON o.job_id = j.job_id;
```

- RAND() gives a new value on every query, as Excel's RAND does on recalculation.

## X40

XLOOKUP for the team and the rate becomes joins. The per-team SUMIFS and the PivotTable both become a GROUP BY over the costed runs. This assumes the base Runs data sits in a table `runs` with columns run, job and mins.

```sql
CREATE VIEW runs_costed AS
SELECT
  r.run,
  r.job,
  r.mins,
  j.team,
  r.mins * p.value AS cost
FROM runs r
LEFT JOIN jobs j
  ON r.job = j.job_id
CROSS JOIN (
  SELECT value FROM parameters WHERE name = 'rate'
) p;

SELECT
  t.team,
  SUM(r.cost) AS total_cost
FROM teams t
LEFT JOIN runs_costed r
  ON r.team = t.team
GROUP BY t.team;

SELECT
  a.alert_id,
  a.run_id,
  a.severity,
  a.dt,
  r.mins AS run_mins
FROM run_alerts a
LEFT JOIN runs_costed r
  ON a.run_id = r.run;

SELECT
  team,
  SUM(cost) AS sum_of_cost
FROM runs_costed
GROUP BY team;
```

- The rate comes from the parameters row named rate (2).
- The last query is the PivotTable (rows Team, sum of Cost).
