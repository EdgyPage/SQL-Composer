date: 2026-10-29
arm: A0
model: sonnet
files: none

## X21

The `region_budgets` table has two calculated columns: `budget_dollars` (cents / 100) and `with_margin` (cents * 1.1).

```sql
SELECT
  job_id,
  budget_cents,
  region,
  budget_cents / 100  AS budget_dollars,
  budget_cents * 1.1  AS with_margin
FROM region_budgets;
```

Hive's `/` always returns a decimal (double) result, like Excel's, so `150 / 100` gives `1.5`.

## X22

The `jobs` table has two calculated columns, `is_finance` and `ratio`.

```sql
SELECT
  job_id,
  job_name,
  team,
  CASE WHEN team = 'finance' THEN 'yes' ELSE 'no' END AS is_finance,
  COALESCE(job_id / (job_id - 2), 0)                  AS ratio
FROM jobs;
```

- `IFERROR(x, 0)` turns an Excel error into 0. In Hive, dividing by zero returns NULL instead of raising an error, so `COALESCE(..., 0)` does the same job. This hits job 2, where `job_id - 2` is 0.
- Excel's `=` on text ignores case (`"Finance"` = `"finance"`), but Hive's `=` does not. If `team` could hold mixed case, use `LOWER(team) = 'finance'`.

## X23

`job_runs` has two calculated columns, `label` and `risky`.

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
  COALESCE(status = 'FAILED', FALSE)
    OR COALESCE(avg_retry_secs > 5, FALSE) AS risky
FROM job_runs;
```

- `SWITCH` becomes `CASE`. A blank status (run 98) falls to `'other'` in both.
- A blank cell in Excel compares as FALSE, so `OR(blank="FAILED", blank>5)` is FALSE. In Hive a NULL comparison is NULL, and `NULL OR NULL` would be NULL. The `COALESCE(..., FALSE)` calls keep run 98 as FALSE, as in the workbook.

## X24

`team_notes` has four calculated columns.

```sql
SELECT
  team,
  note,
  written_on,
  SUBSTR(note, 1, INSTR(note, ' ') - 1) AS first_word,
  UPPER(team)                           AS shout,
  MONTH(written_on)                     AS month,
  ROUND(LENGTH(note) / 10, 1)           AS tens_of_chars
FROM team_notes;
```

- `LEFT(note, FIND(" ", note) - 1)` is the text before the first space. Excel gives `#VALUE!` for a note with no space. Hive gives an empty string, because `INSTR` returns 0 and `SUBSTR(note, 1, -1)` is empty. Every note in this workbook has a space.
- `MONTH(written_on)` works if `written_on` is a Hive DATE or a `yyyy-MM-dd` string.
- `month` as an alias is fine in Hive. Backtick it if your Hive version complains.

## X25

There are two Excel Tables with calculations, so two queries. The column names have spaces, so they need backticks.

`Costs`: `Day` rebuilds a date from the `Day Key` number (yyyymmdd).

```sql
SELECT
  `Job`,
  `Cost (cents)`,
  `Region`,
  `Day Key`,
  CAST(
    CONCAT(
      SUBSTR(CAST(`Day Key` AS STRING), 1, 4), '-',
      SUBSTR(CAST(`Day Key` AS STRING), 5, 2), '-',
      SUBSTR(CAST(`Day Key` AS STRING), -2)
    ) AS DATE
  ) AS `Day`
FROM Costs;
```

`Budgets`: `Dollars` is the budget divided by 100.

```sql
SELECT
  `Job`,
  `Budget`,
  `Region`,
  `Budget` / 100 AS `Dollars`
FROM Budgets;
```

- `LEFT`, `MID` and `RIGHT` become `SUBSTR` with start positions 1, 5 and -2 (the last two characters).
- Excel's `DATE` gives a serial number that is formatted as a date. Hive gets a real DATE.
- The last `Costs` row has a blank `Cost (cents)`. It comes through as NULL.

## X26

`run_alerts` looks up three things from `job_runs`:
- `job_id` is an exact-match XLOOKUP on `run_id`.
- `status` is the VLOOKUP, column 3 of `job_runs`, which is `status`.
- `avg_mins` is the average `duration_mins` of every run of that job (AVERAGEIFS).

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

- Left joins keep every alert, as the lookups do. Where Excel would show `#N/A` or `#DIV/0!`, Hive gives NULL.
- XLOOKUP and VLOOKUP take the first match. This join assumes `job_runs.run_id` is unique, which it is in this workbook.
- `AVERAGEIFS` here averages all runs of the job, including the TEST run. Add a filter inside `job_avg` if you did not mean that.
- The `status` VLOOKUP would return 0 for a blank status cell. Here Hive returns NULL. None of the alerted runs has a blank status.

## X27

`by_team` has a fixed list of teams. Each one gets a count, the highest `job_id` in the team, and that job's name.

```sql
WITH agg AS (
  SELECT
    team,
    COUNT(*)    AS jobs_in_team,
    MAX(job_id) AS last_job_id
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

- `COUNTIFS` and `MAXIFS` return 0 when nothing matches, hence the `COALESCE`. Then `INDEX/MATCH` finds no job, so `last_job_name` is NULL (Excel shows `#N/A`).
- Excel matches team names ignoring case, but Hive joins are case-sensitive.

## X28

`jobs.ok_mins` is the total `duration_mins` of that job's runs with status `SUCCESS`. The Keys sheet says `job_id` is the key of `jobs`.

```sql
SELECT
  j.job_id,
  j.job_name,
  COALESCE(r.ok_mins, 0) AS ok_mins
FROM jobs j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS ok_mins
  FROM job_runs
  WHERE status = 'SUCCESS'
  GROUP BY job_id
) r ON j.job_id = r.job_id;
```

Check this: in the `jobs` table, the `ok_mins` cell for job 3 (`report_build`) is the typed number `99`, not the formula. The formula would give 30 for that job. I used the column's formula for every row. If the 99 is deliberate, add this line to the select list in place of the `COALESCE`:

```sql
CASE WHEN j.job_id = 3 THEN 99 ELSE COALESCE(r.ok_mins, 0) END AS ok_mins
```

It is better to fix the cell in the workbook, or to say why 99 is right.

`SUMIFS` gives 0 for no match, which is why job 4 gets 0.

## X29

`Parameters` holds `cents_per_dollar = 100`. The XLOOKUP into it becomes a one-row CTE joined to every row.

```sql
WITH params AS (
  SELECT CAST(`value` AS DOUBLE) AS cents_per_dollar
  FROM Parameters
  WHERE `name` = 'cents_per_dollar'
  LIMIT 1
)
SELECT
  r.job_id,
  r.budget_cents,
  r.region,
  r.budget_cents / p.cents_per_dollar AS in_dollars
FROM region_budgets r
CROSS JOIN params p;
```

Things I did not carry over:
- The `in_dollars` cell for job 3 is the typed number `5`, but the column's formula gives 3.5 (350 / 100). I used the formula for all rows. If 5 is deliberate, that should be a different column or a documented override.
- The `pointer` column is `INDIRECT("A"&ROW())`. It builds a cell address as text, then reads that cell. That is a reference to whatever sits in column A of the same row, which is `job_id`. Hive has no cell addresses, and this breaks if columns move. I left it out. If you meant `job_id`, select `job_id` directly.

## X30

```sql
SELECT
  run_id,
  job_id,
  dt,
  SUBSTR(CAST(dt AS STRING), -2)           AS `day`,
  LAG(run_id) OVER (ORDER BY run_id)       AS prev_run,
  1 + CAST(FLOOR(RAND() * 5) AS INT)       AS jitter
FROM scheduler_runs;
```

The PivotTable (job_id with a count of run_id) is a plain group-by:

```sql
SELECT
  job_id,
  COUNT(run_id) AS count_of_run_id
FROM scheduler_runs
GROUP BY job_id;
```

Decisions to check:
- `OFFSET(run_id, -1, 0)` reads the cell one row up. That is the previous row of the sheet, so I used `LAG`. A Hive table has no row order, so I ordered by `run_id`, which matches the sheet order. On the first row, the cell above is the header, so Excel shows the text `run_id`. Hive gives NULL.
- `RANDBETWEEN(1,5)` is random and changes on every recalculation. The `RAND()` version has the same behaviour: it differs on each run and cannot be matched to the workbook's values.
- The bar chart on "Summary" has no SQL equivalent. Chart it from the pivot query in your BI tool.

## X31

```sql
WITH params AS (
  SELECT
    7  AS summary_d4,  -- Summary!D4
    10 AS boost        -- defined name boost = Summary!B2
)
SELECT
  j.job_id,
  j.team,
  CONCAT(UPPER(j.team), '!')  AS tag,      -- LAMBDA TAG(t) = UPPER(t)&"!"
  j.job_id * p.summary_d4     AS scaled,
  j.job_id * p.boost          AS boosted
FROM jobs j
CROSS JOIN params p;
```

- I left out `bump`. Its formula is `jobs[[#This Row],[bump]]*2`, in the `bump` column itself. That is a circular reference, so Excel cannot calculate it and there is nothing for Hive to compute. Tell me what it should be based on.
- The `TAG` name is a LAMBDA (a user-defined function), so I wrote its body inline.
- The two numbers are loose cells on `Summary`. I inlined them as constants. Better to put them in the `Parameters` table (for example `summary_d4 = 7`, `boost = 10`) and read them from there.

## X32

```sql
WITH job_runs_named AS (
  SELECT
    r.run_id,
    r.job_id,
    r.status,
    r.duration_mins,
    r.avg_retry_secs,
    r.dt,
    j.job_name
  FROM job_runs r
  LEFT JOIN jobs j ON r.job_id = j.job_id
),
runs_per_name AS (
  SELECT job_name, COUNT(*) AS runs
  FROM job_runs_named
  GROUP BY job_name
)
-- job_runs with the looked-up job_name:
-- SELECT * FROM job_runs_named;

-- by_name:
SELECT
  n.job_name,
  COALESCE(p.runs, 0) AS runs
FROM by_name n
LEFT JOIN runs_per_name p ON n.job_name = p.job_name;
```

The query above returns `by_name`. To get `job_runs` with its new `job_name` column, run `SELECT * FROM job_runs_named` after the same CTE.

Check this: `VLOOKUP(..., jobs, 2, TRUE)` is an approximate match. It assumes `jobs` is sorted by `job_id` and returns the closest lower id when there is no exact one. I wrote an exact join. For the ids in this workbook (1, 2, 3, all present) the answers are the same. If a `job_id` is missing from `jobs`, Excel would return the previous job's name where Hive gives NULL. Almost certainly an exact match is what was meant, so `FALSE` in the VLOOKUP would be the fix.

## X33

The Power Query reads `ops.job_runs` from the warehouse. The Hive query is the same filter and the new column:

```sql
SELECT
  run_id,
  duration_mins,
  duration_mins - 20 AS over_by
FROM ops.job_runs
WHERE duration_mins >= 20
  AND (status IS NULL OR status <> 'TEST');
```

- In Power Query, `null <> "TEST"` is true, so a run with a blank status is kept. In Hive a plain `status <> 'TEST'` is NULL for those rows and would drop them, so I added `status IS NULL OR`. No such row passes the 20-minute filter in the sample data, but the query is right for the real table.
- The `Sql.Database("dwh01", "ops")` connection is not part of the SQL. You run this against the same warehouse.

## X34

`runs_with_team` is a connection-only query (a step with no table of its own), so it is a CTE. `team_totals` groups it by team.

```sql
WITH runs_with_team AS (
  SELECT r.*, j.team
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

This matches the sheet: data gives 67 and 40, finance gives 113 and 30. The `web` team has no runs, so it does not appear.

## X35

`recent` stacks the run ids and dates from `job_runs` and `scheduler_runs`, sorts by `run_id` descending and keeps the top four.

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

- `Table.Combine` keeps duplicates, so this is `UNION ALL`, not `UNION`. That is why runs 104 and 103 each appear twice.
- The `rates` query fetches JSON from a web address. Nothing else in the workbook uses it, and Hive cannot call a URL, so I left it out. If you need the rates in the warehouse, load them as a table first.

## X36

`job_runs.alerts` counts the alerts per run. `severity_by_day` pivots the alerts, counting per day and severity.

```sql
-- job_runs.alerts
SELECT
  r.run_id,
  r.status,
  COALESCE(a.alerts, 0) AS alerts
FROM job_runs r
LEFT JOIN (
  SELECT run_id, COUNT(*) AS alerts
  FROM run_alerts
  GROUP BY run_id
) a ON r.run_id = a.run_id;
```

```sql
-- severity_by_day
SELECT
  dt,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low'  THEN 1 END) AS low
FROM run_alerts
GROUP BY dt;
```

- The Power Query builds its columns from whatever severity values it finds (`List.Distinct`). Hive needs the column list written out. If a new severity such as `medium` appears, add a line for it.
- A day with no alert of a given severity is NULL here, as in the pivot, not 0.
- This gives the sheet's values: 09-23 has 1 high and 1 low, and 09-24 has 2 high and 5 low.

## X37

The column names have spaces, so they get backticks.

```sql
SELECT
  `Job No`,
  `Team Name`,
  `Owner`,
  `Day`,
  CASE WHEN `Owner` = 'ana' THEN 1 ELSE 0 END AS `Is Ana`
FROM Owners;
```

A blank `Owner` gives 0 in both Excel and Hive (the `ELSE` catches the NULL). Excel compares text ignoring case, but Hive does not, so `'Ana'` would not match. Use `LOWER(`Owner`) = 'ana'` if the case varies. You could also rename the columns to `job_no`, `team_name`, `is_ana` to avoid backticks, but I kept the workbook's names.

## X38

`Keys` says `job_runs` has the key `run_id`.

```sql
SELECT
  r.run_id,
  r.job_id,
  r.status,
  r.duration_mins,
  r.avg_retry_secs,
  j.region,
  SUM(r.duration_mins) OVER (PARTITION BY j.region)            AS region_mins,
  (COALESCE(r.avg_retry_secs, 0) + COALESCE(r.duration_mins, 0)) * 2 AS retry_cost
FROM job_runs r
LEFT JOIN jobs j ON r.job_id = j.job_id;
```

- `region` is a lookup from `jobs`, so it is a left join (`jobs.job_id` is unique, so no rows are duplicated).
- `SUMIFS` over the table's own `region` column adds up every run in the same region. That is a window sum partitioned by region, so each row keeps its own and the total repeats.
- Excel treats a blank cell as 0 in `+`, but Hive's NULL + 15 is NULL. Run 98 has a blank `avg_retry_secs`, so I used `COALESCE(..., 0)`.

Check this: the `retry_cost` cell for run 102 is the typed number `1`, but the column's formula gives (6 + 20) * 2 = 52. I used the formula for every row. If 1 was deliberate, say why. Otherwise it is a stale hard-coded value, and the workbook should be fixed.
