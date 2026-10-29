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
