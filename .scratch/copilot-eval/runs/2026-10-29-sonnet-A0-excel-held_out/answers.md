date: 2026-10-29
arm: A0
model: sonnet
files: none

General notes for every workbook: the "Steps" sheet is empty, so nothing there converts. "Parameters" and "Keys" are lookup tables, not calculations. I read "Keys" as "this column is unique in this table" and only use it when it matters. I assume each Excel Table is a Hive table of the same name and column names (rename the backticked ones if your Hive columns are snake_case). Hive differs from Excel in a few ways that I handle below: dividing by zero gives NULL (not an error), NULL propagates through arithmetic and comparisons (Excel treats a blank as 0 or ""), and string comparison is case-sensitive (Excel's is not).

## X21

Both columns are plain row-by-row arithmetic.

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

`IFERROR(job_id/(job_id-2), 0)` only guards a divide-by-zero (job 2). In Hive that division returns NULL rather than an error, so I test the divisor explicitly.

```sql
SELECT
  job_id,
  job_name,
  team,
  CASE WHEN team = 'finance' THEN 'yes' ELSE 'no' END AS is_finance,
  CASE WHEN job_id - 2 = 0 THEN 0
       ELSE job_id / (job_id - 2) END AS ratio
FROM jobs;
```

## X23

`SWITCH` becomes a simple `CASE`. Run 98 has a blank status and blank avg_retry_secs. In Excel a blank equals nothing, and a blank is not > 5, so `risky` is FALSE. In Hive both comparisons would be NULL, so I wrap them in `COALESCE(..., FALSE)` to keep FALSE. Excel's `=` ignores case and Hive's does not. If the statuses might vary in case, use `upper(status)`.

```sql
SELECT
  run_id,
  status,
  avg_retry_secs,
  CASE status
    WHEN 'SUCCESS' THEN 'ok'
    WHEN 'FAILED'  THEN 'bad'
    ELSE 'other'
  END AS label,
  COALESCE(status = 'FAILED' OR avg_retry_secs > 5, FALSE) AS risky
FROM job_runs;
```

## X24

`FIND(" ", note) - 1` becomes `instr(note, ' ') - 1`. A note with no space would give #VALUE! in Excel. Here every note has one, and Hive would return an empty string. `LEN` is `length`, and `ROUND(x, 1)` is `round(x, 1)`. `written_on` can be a DATE or a 'yyyy-MM-dd' string.

```sql
SELECT
  team,
  note,
  written_on,
  substr(note, 1, instr(note, ' ') - 1) AS first_word,
  upper(team)                           AS shout,
  month(written_on)                     AS month,
  round(length(note) / 10, 1)           AS tens_of_chars
FROM team_notes;
```

## X25

Two tables, so two queries. The `Day` formula rebuilds a date from the 8-digit key, which I do with `substr` and a cast. Hive has no `RIGHT`, so I use `substr` for it too. The last Costs row has a blank cost. Nothing is calculated from that column, so it stays NULL. Column names with spaces or brackets need backticks.

```sql
-- Costs
SELECT
  `Job`,
  `Cost (cents)`,
  `Region`,
  `Day Key`,
  CAST(concat(substr(CAST(`Day Key` AS STRING), 1, 4), '-',
              substr(CAST(`Day Key` AS STRING), 5, 2), '-',
              substr(CAST(`Day Key` AS STRING), 7, 2)) AS DATE) AS `Day`
FROM Costs;

-- Budgets
SELECT
  `Job`,
  `Budget`,
  `Region`,
  `Budget` / 100 AS `Dollars`
FROM Budgets;
```

## X26

All three `run_alerts` formulas look something up in `job_runs`. `XLOOKUP` and `VLOOKUP(...,3,FALSE)` (column 3 is `status`) become a left join on `run_id`. This assumes `run_id` is unique in `job_runs`, as both lookups assume. They return only the first match, so duplicates would multiply rows here. `AVERAGEIFS` becomes an average per `job_id` over all `job_runs` rows (TEST rows included, as in the workbook), joined back on the looked-up `job_id`. Excel's VLOOKUP would show 0 for a blank status, while Hive gives NULL. None of the alerted runs has a blank status.

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
LEFT JOIN job_avg  j ON r.job_id = j.job_id;
```

## X27

`COUNTIFS` becomes `COUNT(*)` per team, `MAXIFS` becomes `MAX(job_id)` per team, and `INDEX/MATCH` becomes a join back to `jobs` on that id. Excel's `MAXIFS` returns 0 when nothing matches, so I use `COALESCE`. The query starts from `by_team` so every team listed there keeps its row.

```sql
WITH agg AS (
  SELECT team, COUNT(*) AS jobs_in_team, MAX(job_id) AS last_job_id
  FROM jobs
  GROUP BY team
)
SELECT
  t.team,
  COALESCE(a.jobs_in_team, 0) AS jobs_in_team,
  COALESCE(a.last_job_id, 0)  AS last_job_id,
  j.job_name                  AS last_job_name
FROM by_team t
LEFT JOIN agg  a ON t.team = a.team
LEFT JOIN jobs j ON j.job_id = COALESCE(a.last_job_id, 0);
```

## X28

`ok_mins` is a sum of `duration_mins` for successful runs of the job. Job 4 has no runs, where Excel's `SUMIFS` gives 0 and Hive's `SUM` gives NULL, so I use `COALESCE`. Row 3 (job 3, report_build) is not a formula. Someone typed 99 over it. I kept it as written, but 99 is probably a mistake: the formula would give 30. Delete the `CASE` line if you want the formula result.

```sql
SELECT
  j.job_id,
  j.job_name,
  CASE
    WHEN j.job_id = 3 THEN 99                -- hard-coded in the workbook
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

## X29

Two things to flag.

1. The parameter lookup `XLOOKUP("cents_per_dollar", Parameters[name], Parameters[value])` becomes a one-row subquery that I cross join. Job 3's `in_dollars` is a typed-in 5 instead of the formula, which would give 3.5. I kept the 5 and marked it, so remove that line if it's a mistake.
2. `INDIRECT("A"&ROW())` reads whatever is in column A of the same sheet row. That is `job_id` in this layout. Hive has no cell addresses, so I can't translate the formula itself. I replaced it with `job_id`, which gives the same values today. It would silently break if columns were reordered in Excel, so please confirm that is what `pointer` was meant to hold.

```sql
WITH p AS (
  SELECT CAST(`value` AS DOUBLE) AS cents_per_dollar
  FROM Parameters
  WHERE name = 'cents_per_dollar'
  LIMIT 1
)
SELECT
  r.job_id,
  r.budget_cents,
  r.region,
  CASE
    WHEN r.job_id = 3 THEN 5                 -- hard-coded in the workbook
    ELSE r.budget_cents / p.cents_per_dollar
  END AS in_dollars,
  r.job_id AS pointer                        -- stands in for INDIRECT("A"&ROW())
FROM region_budgets r
CROSS JOIN p;
```

## X30

- `RIGHT(dt, 2)` becomes `substr(dt, -2)`. This assumes `dt` is text or a date shown as yyyy-MM-dd. I cast it to a string.
- `OFFSET(run_id, -1, 0)` means "the run_id from the row above". Hive tables have no row order, so I use `LAG` ordered by `run_id`, which matches the sheet's order. For the first row Excel returns the header text "run_id" (it points at the header cell), while `LAG` gives NULL.
- `RANDBETWEEN(1,5)` is volatile and gives a different answer on each run, in Excel as well. The Hive version is `floor(rand()*5)+1`. Use `rand(42)` if you want repeatable numbers.
- The bar chart on "Summary" has no SQL equivalent. Draw it in your BI tool from the pivot query below.

```sql
SELECT
  run_id,
  job_id,
  dt,
  substr(CAST(dt AS STRING), -2)               AS `day`,
  LAG(run_id, 1) OVER (ORDER BY run_id)        AS prev_run,
  CAST(floor(rand() * 5) + 1 AS INT)           AS jitter
FROM scheduler_runs;

-- The PivotTable "Pivot" (rows job_id, Count of run_id), and the data behind the chart
SELECT job_id, COUNT(run_id) AS count_of_run_id
FROM scheduler_runs
GROUP BY job_id;
```

## X31

- `TAG` is a named LAMBDA, `UPPER(t)&"!"`, so it becomes `concat(upper(team), '!')`.
- `scaled` uses `Summary!$D$4` (7) and `boosted` uses the name `boost`, which points at `Summary!$B$2` (10). Hive has no cell references, so I put both values in a small `consts` CTE. A row in your Parameters table would be a better home for them.
- `bump` can't be converted. Its formula, `jobs[[#This Row],[bump]]*2`, refers to its own cell, which is a circular reference. Excel shows a warning and 0. There is nothing to compute it from, so the query returns NULL for it. Tell me what it was meant to multiply and I'll fix it.

```sql
WITH consts AS (
  SELECT 7 AS summary_d4,   -- Summary!$D$4
         10 AS boost        -- Summary!$B$2
)
SELECT
  j.job_id,
  j.team,
  CAST(NULL AS INT)                 AS bump,     -- circular reference in the workbook
  concat(upper(j.team), '!')        AS tag,
  j.job_id * c.summary_d4           AS scaled,
  j.job_id * c.boost                AS boosted
FROM jobs j
CROSS JOIN consts c;
```

## X32

`VLOOKUP(job_id, jobs, 2, TRUE)` is an approximate match. It relies on `jobs` being sorted by `job_id` and, for an id that isn't there, returns the name of the next lower id. Every `job_id` in `job_runs` (1, 2, 3) exists in `jobs`, so an ordinary left join gives the same result. If a job_id were ever missing, Excel would return a wrong name where the join returns NULL, which is safer. `by_name.runs` counts rows in `job_runs` with that name (`job_name` is the calculated column, so I derive it in a CTE first).

```sql
WITH job_runs_named AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
         j.job_name
  FROM job_runs r
  LEFT JOIN jobs j ON r.job_id = j.job_id
)
-- job_runs with its job_name column
SELECT * FROM job_runs_named;

-- by_name
WITH job_runs_named AS (
  SELECT r.run_id, j.job_name
  FROM job_runs r
  LEFT JOIN jobs j ON r.job_id = j.job_id
)
SELECT
  n.job_name,
  COUNT(r.run_id) AS runs
FROM by_name n
LEFT JOIN job_runs_named r ON r.job_name = n.job_name
GROUP BY n.job_name;
```

## X33

The table comes from a Power Query against the SQL Server `ops.job_runs` table. The M code translates directly. The `status <> "TEST"` in M treats a NULL status as "not TEST", so the row is kept. In Hive `NULL <> 'TEST'` is NULL and the row would be dropped, so I use the null-safe `<=>`. Adjust the table name if your Hive copy lives in another database (for example `ops.job_runs`).

```sql
SELECT
  run_id,
  duration_mins,
  duration_mins - 20 AS over_by
FROM job_runs
WHERE duration_mins >= 20
  AND NOT (status <=> 'TEST');
```

## X34

`Table.NestedJoin` with a left outer join and then expanding `team` is a left join. `Table.Group` with sum and max is a `GROUP BY`. `runs_with_team` is a connection-only query, so I keep it as a CTE. The result matches the sheet (data 67 and 40, finance 113 and 30). Team `web` has no runs, so it doesn't appear.

```sql
WITH runs_with_team AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
         j.team
  FROM job_runs r
  LEFT JOIN jobs j ON r.job_id = j.job_id
)
SELECT
  team,
  SUM(duration_mins) AS total_mins,
  MAX(duration_mins) AS longest
FROM runs_with_team
GROUP BY team;
```

## X35

`Table.Combine` keeps duplicates, so it is `UNION ALL`, not `UNION`. That is why 104 and 103 each appear twice. Then sort descending and take 4. The `rates` query calls a web URL (`rates.example.com`). It is connection-only and nothing in the workbook uses it, so there is nothing to convert, and a Hive query shouldn't fetch from the web.

```sql
SELECT run_id, dt
FROM (
  SELECT run_id, dt FROM job_runs
  UNION ALL
  SELECT run_id, dt FROM scheduler_runs
) both_tables
ORDER BY run_id DESC
LIMIT 4;
```

## X36

Two parts. `alerts` counts matching alerts per run, so I count in a subquery and left join to keep one output row per `job_runs` row. Runs with no alerts get 0, as `COUNTIFS` does.

The Power Query pivot builds one column per distinct severity. Hive can't create columns dynamically, so I write them for the values in the data (high, low). A new severity would need a new line. Combinations with no alerts stay NULL, like the blanks in the sheet.

```sql
-- job_runs.alerts
SELECT
  r.run_id,
  r.status,
  COALESCE(a.n, 0) AS alerts
FROM job_runs r
LEFT JOIN (
  SELECT run_id, COUNT(*) AS n
  FROM run_alerts
  GROUP BY run_id
) a ON r.run_id = a.run_id;

-- severity_by_day
SELECT
  dt,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low'  THEN 1 END) AS low
FROM run_alerts
GROUP BY dt;
```

## X37

`Is Ana` is a flag. The blank owners on the `web` rows are NULL in Hive. In Excel a blank is not "ana", so they get 0, and the `CASE ... ELSE 0` does the same. Excel's `=` ignores case, so `lower()` keeps that behaviour.

```sql
SELECT
  `Job No`,
  `Team Name`,
  `Owner`,
  `Day`,
  CASE WHEN lower(`Owner`) = 'ana' THEN 1 ELSE 0 END AS `Is Ana`
FROM Owners;
```

## X38

- `XLOOKUP` is a left join to `jobs`.
- `region_mins` is the sum of `duration_mins` across all runs in the same region, which is a window sum over the region. I compute it after the join.
- `retry_cost` is `(avg_retry_secs + duration_mins) * 2`. Run 98 has a blank `avg_retry_secs`, which Excel counts as 0 (giving 30). `NULL + 15` would be NULL in Hive, so I wrap it in `COALESCE`.
- Run 102's `retry_cost` is a typed-in 1 instead of the formula (which would give 52). I kept it and marked it. Remove that line if it's a mistake.

```sql
WITH runs_with_region AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
         j.region
  FROM job_runs r
  LEFT JOIN jobs j ON r.job_id = j.job_id
)
SELECT
  run_id,
  job_id,
  status,
  duration_mins,
  avg_retry_secs,
  region,
  SUM(duration_mins) OVER (PARTITION BY region) AS region_mins,
  CASE
    WHEN run_id = 102 THEN 1                 -- hard-coded in the workbook
    ELSE (COALESCE(avg_retry_secs, 0) + COALESCE(duration_mins, 0)) * 2
  END AS retry_cost
FROM runs_with_region;
```

## X39

The query filters to successful runs, keeps three columns, then the sheet adds three calculated columns to that result:

- `job_name` is a left join to `jobs`.
- `share` divides each run's minutes by the total for its job within this filtered set. I do that with a window sum before the join.
- `noise` is `RAND()`. It is volatile, so it changes every time the query runs. `rand(42)` would make it repeatable, but the numbers still won't match Excel's.

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins
  FROM job_runs
  WHERE status = 'SUCCESS'
),
shared AS (
  SELECT run_id, job_id, duration_mins,
         duration_mins / SUM(duration_mins) OVER (PARTITION BY job_id) AS share
  FROM ok_runs
)
SELECT
  s.run_id,
  s.job_id,
  s.duration_mins,
  j.job_name,
  s.share,
  rand() AS noise
FROM shared s
LEFT JOIN jobs j ON s.job_id = j.job_id;
```

## X40

There are four outputs here: the `Runs` table, the `Teams` table, `run_alerts`, and the PivotTable. The rate comes from `Parameters` (name `rate`, value 2). I read it once in a CTE and cross join it. `Runs.Team` is a left join to `jobs`, and `Cost` is `Mins * rate`. The pivot is the same grouping as `Teams` but over every team that appears in `Runs`.

```sql
-- Runs (Team and Cost added)
WITH rate AS (
  SELECT CAST(`value` AS DOUBLE) AS rate
  FROM Parameters
  WHERE name = 'rate'
  LIMIT 1
)
SELECT
  r.`Run`,
  r.`Job`,
  r.`Mins`,
  j.team                AS `Team`,
  r.`Mins` * p.rate     AS `Cost`
FROM Runs r
LEFT JOIN jobs j ON r.`Job` = j.job_id
CROSS JOIN rate p;

-- Teams: Total Cost (0 when a team has no runs, like SUMIFS)
WITH rate AS (
  SELECT CAST(`value` AS DOUBLE) AS rate
  FROM Parameters
  WHERE name = 'rate'
  LIMIT 1
),
runs_calc AS (
  SELECT j.team AS team, r.`Mins` * p.rate AS cost
  FROM Runs r
  LEFT JOIN jobs j ON r.`Job` = j.job_id
  CROSS JOIN rate p
)
SELECT
  t.`Team`,
  COALESCE(SUM(c.cost), 0) AS `Total Cost`
FROM Teams t
LEFT JOIN runs_calc c ON c.team = t.`Team`
GROUP BY t.`Team`;

-- run_alerts: Run Mins (first matching Run, like XLOOKUP; assumes Run is unique)
SELECT
  a.alert_id,
  a.run_id,
  a.severity,
  a.dt,
  r.`Mins` AS `Run Mins`
FROM run_alerts a
LEFT JOIN Runs r ON a.run_id = r.`Run`;

-- PivotTable "Pivot": rows Team, Sum of Cost
WITH rate AS (
  SELECT CAST(`value` AS DOUBLE) AS rate
  FROM Parameters
  WHERE name = 'rate'
  LIMIT 1
)
SELECT
  j.team                      AS `Team`,
  SUM(r.`Mins` * p.rate)      AS `Sum of Cost`
FROM Runs r
LEFT JOIN jobs j ON r.`Job` = j.job_id
CROSS JOIN rate p
GROUP BY j.team;
```

The pivot's grand-total row isn't in the query. Add it in your BI tool, or `GROUP BY ... WITH ROLLUP`.
