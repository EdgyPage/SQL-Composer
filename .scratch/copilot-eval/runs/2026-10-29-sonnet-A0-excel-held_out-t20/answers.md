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

## X39

I assumed each Excel Table is a Hive table with the same name and columns (`job_runs`, `jobs`). The `Parameters` and `Keys` tables are empty, so nothing uses them.

`ok_runs` is a Power Query step (filter, then keep columns) with three formula columns on top. The Power Query step becomes the CTE. The formula columns become the final SELECT:

- `job_name`: the XLOOKUP becomes a left join to `jobs`.
- `share`: the SUMIFS over the table's own rows becomes a windowed SUM per `job_id`.
- `noise`: `RAND()` becomes `rand()`.

```sql
WITH ok_runs AS (
  -- Power Query "ok_runs": keep SUCCESS rows, keep three columns
  SELECT run_id, job_id, duration_mins
  FROM job_runs
  WHERE status = 'SUCCESS'
),
shared AS (
  SELECT run_id, job_id, duration_mins,
         duration_mins / SUM(duration_mins) OVER (PARTITION BY job_id) AS share
  FROM ok_runs
)
SELECT s.run_id,
       s.job_id,
       s.duration_mins,
       j.job_name,          -- XLOOKUP(job_id, jobs[job_id], jobs[job_name])
       s.share,             -- duration / SUMIFS(duration, same job_id) over the filtered rows
       rand() AS noise      -- =RAND()
FROM shared s
LEFT JOIN jobs j ON s.job_id = j.job_id;
```

Notes:
- The window runs over the filtered rows only, as in the sheet, because SUMIFS reads the loaded `ok_runs` table, not `job_runs`.
- `rand()` gives a new value on every run, like `RAND()` on every recalculation. It will not match the numbers in the workbook, and there is no seed that reproduces them.
- XLOOKUP gives `#N/A` for a job with no match. The left join gives NULL.
- `status = 'SUCCESS'` is case-sensitive in both M and Hive.

## X40

I assumed each Excel Table is a Hive table with the same name (`parameters`, `runs`, `jobs`, `teams`, `run_alerts`). `Parameters` holds `rate = 2`, which `Runs[Cost]` uses. I read it from the table instead of hard-coding 2.

```sql
-- Runs: Team and Cost columns
WITH rate AS (
  SELECT MIN(CAST(value AS DOUBLE)) AS rate      -- XLOOKUP("rate", Parameters[name], Parameters[value])
  FROM parameters
  WHERE name = 'rate'
)
SELECT r.Run,
       r.Job,
       r.Mins,
       j.team AS Team,                           -- XLOOKUP(Job, jobs[job_id], jobs[team])
       r.Mins * p.rate AS Cost
FROM runs r
CROSS JOIN rate p
LEFT JOIN jobs j ON r.Job = j.job_id;
```

```sql
-- Teams: Total Cost = SUMIFS(Runs[Cost], Runs[Team], this Team)
WITH rate AS (
  SELECT MIN(CAST(value AS DOUBLE)) AS rate FROM parameters WHERE name = 'rate'
),
runs_costed AS (
  SELECT r.Run, j.team AS Team, r.Mins * p.rate AS Cost
  FROM runs r
  CROSS JOIN rate p
  LEFT JOIN jobs j ON r.Job = j.job_id
)
SELECT t.Team,
       COALESCE(SUM(c.Cost), 0) AS `Total Cost`   -- SUMIFS gives 0 when nothing matches
FROM teams t
LEFT JOIN runs_costed c ON c.Team = t.Team
GROUP BY t.Team;
```

```sql
-- run_alerts: Run Mins = XLOOKUP(run_id, Runs[Run], Runs[Mins])
SELECT a.alert_id, a.run_id, a.severity, a.dt,
       r.Mins AS `Run Mins`
FROM run_alerts a
LEFT JOIN runs r ON a.run_id = r.Run;
```

```sql
-- PivotTable on "Pivot": rows Team, values Sum of Cost
WITH rate AS (
  SELECT MIN(CAST(value AS DOUBLE)) AS rate FROM parameters WHERE name = 'rate'
),
runs_costed AS (
  SELECT j.team AS Team, r.Mins * p.rate AS Cost
  FROM runs r
  CROSS JOIN rate p
  LEFT JOIN jobs j ON r.Job = j.job_id
)
SELECT Team, SUM(Cost) AS `Sum of Cost`
FROM runs_costed
GROUP BY Team;
```

Notes:
- If `rate` is missing, Excel shows `#N/A`. Here `Cost` comes out NULL.
- The `Teams` rows (data, finance) are typed values, so `teams` is an input table. `web` has no row there, so it does not appear in `Teams`. The PivotTable does list every team found in `Runs`.
- A pivot is not a formula. The last query gives the same numbers, but Excel still draws the pivot itself.

## X46

I assumed the tables `jobs` and `job_runs`. The three `jobs` formula columns need a left join, because job 4 has no runs.

- MINIFS returns 0 when nothing matches, so I wrap MIN in `COALESCE(..., 0)`.
- COUNTIF becomes `COUNT(r.job_id)`, which is 0 for job 4.
- `RANK.EQ` with no order argument ranks descending, and ties share a rank. That is `RANK()` ordered by `runs` descending.

```sql
SELECT j.job_id,
       j.job_name,
       j.team,
       COALESCE(MIN(r.duration_mins), 0)            AS shortest,  -- MINIFS (0 if no match)
       COUNT(r.job_id)                              AS runs,      -- COUNTIF
       RANK() OVER (ORDER BY COUNT(r.job_id) DESC)  AS busiest    -- RANK.EQ(runs, jobs[runs]) descending
FROM jobs j
LEFT JOIN job_runs r ON r.job_id = j.job_id
GROUP BY j.job_id, j.job_name, j.team;
```

Expected result: shortest = 5, 15, 30, 0; runs = 4, 3, 2, 0; busiest = 1, 2, 3, 4.

## X47

I assumed the table `region_budgets` and kept all four rows.

- `RANK.EQ(..., 1)` is ascending, so the cheapest budget ranks 1.
- `SUMIF` and `AVERAGEIF` over the same region become windowed SUM and AVG per region.

```sql
SELECT job_id,
       budget_cents,
       region,
       RANK() OVER (ORDER BY budget_cents ASC)     AS cheapest_first,  -- RANK.EQ(.., 1)
       SUM(budget_cents) OVER (PARTITION BY region) AS region_total,   -- SUMIF
       AVG(budget_cents) OVER (PARTITION BY region) AS region_avg      -- AVERAGEIF
FROM region_budgets;
```

Expected result: cheapest_first = 2, 3, 4, 1. eu total = 400, eu average = 133.33. us total = 350, us average = 350.

## X48

I assumed the tables `job_runs`, `jobs` and `run_alerts`. The two Power Queries become two queries. Nothing in the workbook has Excel formulas.

`quiet_runs` is a left anti join: runs with no alert. `slow_regions` is an inner join, a group by, and a filter on the group. That filter becomes HAVING.

```sql
-- Power Query "quiet_runs": runs that have no alert (left anti join)
SELECT r.run_id, r.job_id, r.status
FROM job_runs r
LEFT JOIN run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL;
```

```sql
-- Power Query "slow_regions": average duration per region, keep those >= 20
SELECT j.region,
       AVG(r.duration_mins) AS avg_mins,
       MIN(r.duration_mins) AS fastest
FROM job_runs r
JOIN jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20;
```

Expected result: `quiet_runs` is runs 95, 96, 98 and 99. `slow_regions` is NYC with average 30 and fastest 30. LON averages 16.75 and PAR averages 17.67, so both are dropped.

Note: SQL does not promise row order. Add `ORDER BY` if the order matters.

## X49

I assumed the tables `job_runs`, `jobs`, `run_alerts`, `scheduler_runs` and `job_owners`. There are three Power Queries and no Excel formulas.

```sql
-- Power Query "alert_status": alerts RIGHT OUTER JOIN runs, so every run is kept
SELECT a.alert_id, a.severity, r.status
FROM run_alerts a
RIGHT OUTER JOIN job_runs r ON a.run_id = r.run_id;
```

```sql
-- Power Query "run_check": full outer join of runs and scheduled runs
SELECT r.run_id,
       r.status,
       s.run_id AS scheduled_run
FROM (SELECT run_id, status FROM job_runs) r
FULL OUTER JOIN scheduler_runs s ON r.run_id = s.run_id;
```

```sql
-- Power Query "teams": distinct teams from jobs and job_owners
SELECT team FROM jobs
UNION                       -- UNION (not UNION ALL) removes duplicates, like Table.Distinct
SELECT team FROM job_owners;
```

Expected result:
- `alert_status`: 13 rows. Runs with no alert (95, 96, 98, 99) have NULL alert_id and severity.
- `run_check`: run 99 has no scheduled run. Run 100 is scheduled but has no run, so its run_id and status are NULL.
- `teams`: data, finance, web.

## X50

I assumed the tables `job_owners` and `jobs`. `owners` is a Power Query with two formula columns on its output.

The Power Query keeps `job_id` and `owner` and removes duplicates, so one row per distinct pair. Job 4's NULL owner stays as a row, because DISTINCT keeps one NULL.

- `job_name` is the XLOOKUP, a left join to `jobs`.
- `newest_first` is `RANK.EQ(job_id, owners[job_id])`, descending by default. That is `RANK()` ordered by `job_id` descending.

```sql
WITH owners AS (
  SELECT DISTINCT job_id, owner
  FROM job_owners
)
SELECT o.job_id,
       o.owner,
       j.job_name,
       RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM owners o
LEFT JOIN jobs j ON o.job_id = j.job_id;
```

Expected result: five rows (1 ana, 2 ben, 3 ana, 3 chloe, 4 NULL). newest_first = 5, 4, 2, 2, 1.

The window runs over the de-duplicated rows, as in the sheet, since the formula reads the loaded `owners` table.

## X59

I assumed the tables `jobs`, `job_runs` and `run_alerts`.

`jobs` has three columns that count or sum matching `job_runs` rows.
- **Left join:** job 4 has no runs and must still show 0.
- **`"f*"`:** Excel wildcards are case-insensitive, so I compare `lower(status) LIKE 'f%'`.
- **`"<>TEST"`:** COUNTIFS counts blank statuses too, since blank is not equal to TEST. Run 98 has a blank status and counts. In SQL, `NULL <> 'TEST'` is NULL, so I use `COALESCE`.

`alerts_so_far` counts rows whose `run_id` is less than or equal to this row's. Ties are included. That is a running count with a RANGE frame.

```sql
-- jobs
SELECT j.job_id,
       j.job_name,
       COALESCE(SUM(CASE WHEN r.duration_mins >= 20 THEN 1 ELSE 0 END), 0)                    AS long_runs,
       COALESCE(SUM(CASE WHEN lower(r.status) LIKE 'f%' THEN r.duration_mins END), 0)         AS failed_mins,
       COALESCE(SUM(CASE WHEN r.job_id IS NOT NULL AND COALESCE(upper(r.status), '') <> 'TEST'
                         THEN 1 ELSE 0 END), 0)                                               AS not_test
FROM jobs j
LEFT JOIN job_runs r ON r.job_id = j.job_id
GROUP BY j.job_id, j.job_name;
```

```sql
-- run_alerts
SELECT alert_id, run_id, severity, dt,
       COUNT(run_id) OVER (ORDER BY run_id
                           RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM run_alerts;
```

Expected result:
- `jobs`: long_runs = 1, 1, 2, 0. failed_mins = 0, 20, 30, 0. not_test = 3, 3, 2, 0.
- `run_alerts`: alerts_so_far = 2, 2, 5, 5, 5, 6, 8, 8, 9.

## X60

I assumed the table `region_budgets`. It has a total row, which is not part of the data. I give it as a separate query.

- `share`: budget divided by the table's total, so `SUM(...) OVER ()`.
- `above_avg`: budget greater than the table's average.
- `rank_in_region`: `COUNTIFS(same region, budget < this) + 1` is the same as `RANK()` ascending within the region, with ties sharing a rank.

```sql
SELECT job_id,
       budget_cents,
       region,
       budget_cents / SUM(budget_cents) OVER ()                                AS share,
       budget_cents > AVG(budget_cents) OVER ()                                AS above_avg,
       RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC)             AS rank_in_region
FROM region_budgets;
```

```sql
-- Total row: SUBTOTAL(103, job_id) = count of non-empty, SUBTOTAL(101, budget) = average
SELECT COUNT(job_id)       AS job_id,
       AVG(budget_cents)   AS budget_cents,
       'Total'             AS region
FROM region_budgets;
```

Expected result:
- shares: 0.2, 0.2667, 0.4667, 0.0667.
- above_avg (average is 187.5): false, true, true, false.
- rank_in_region: 2, 3, 1, 1.
- Total row: 4, 187.5, "Total".

Note: SUBTOTAL skips rows hidden by a filter. SQL cannot see that, so the totals cover every row.

## X61

I assumed the tables `region_costs` and `by_region`. The two region rows (eu, us) are typed values, so `by_region` is an input table that I left join.

- SUMIFS ignores the NULL cost (the last eu row).
- COUNTIFS counts rows, so `entries` counts that row too.
- MAXIFS returns 0 if nothing matches.

```sql
SELECT b.region,
       COALESCE(SUM(c.cost_cents), 0)  AS total_cents,   -- SUMIFS
       COUNT(c.region)                 AS entries,       -- COUNTIFS on region only: counts rows
       COALESCE(MAX(c.cost_cents), 0)  AS priciest       -- MAXIFS
FROM by_region b
LEFT JOIN region_costs c ON c.region = b.region
GROUP BY b.region;
```

```sql
-- Total row: SUBTOTAL(109, ...) is a sum, SUBTOTAL(104, ...) is a max
WITH by_region_calc AS (
  SELECT b.region,
         COALESCE(SUM(c.cost_cents), 0) AS total_cents,
         COUNT(c.region)                AS entries,
         COALESCE(MAX(c.cost_cents), 0) AS priciest
  FROM by_region b
  LEFT JOIN region_costs c ON c.region = b.region
  GROUP BY b.region
)
SELECT 'Total'            AS region,
       SUM(total_cents)   AS total_cents,
       SUM(entries)       AS entries,
       MAX(priciest)      AS priciest
FROM by_region_calc;
```

Expected result: us = 1160 total, 4 entries, 410 priciest. eu has 24 entries and priciest 250. The Total row sums the two and takes max 410.

## X62

I assumed the table `team_notes`, with `written_on` as a DATE. Cast it first if it is a string.

All the formula columns are date or text functions on one row:

- `week_of`: the Monday of the week. WEEKDAY(..., 2) numbers Monday as 1, so the formula steps back to Monday. In Hive, `next_day(d, 'MO')` gives the next Monday after d, and subtracting 7 days gives the Monday on or before d.
- `month_end`: `last_day`.
- `month_of`: the first of the month, from `EOMONTH(d, -1) + 1`.
- `months_in`: `DATEDIF(..., "m")` counts whole months, so I take `floor(months_between(...))`. The start is the 1st, so no day-of-month edge case.
- `three_before`: `date_sub(d, 3)`.
- `who`: PROPER is `initcap`.
- `short`: TEXTJOIN with `", "` and TRUE (skip empties) is `concat_ws` with empty strings turned into NULL first.

```sql
SELECT team,
       note,
       written_on,
       date_sub(next_day(CAST(written_on AS DATE), 'MO'), 7)                       AS week_of,
       last_day(CAST(written_on AS DATE))                                          AS month_end,
       date_add(last_day(add_months(CAST(written_on AS DATE), -1)), 1)             AS month_of,
       CAST(floor(months_between(CAST(written_on AS DATE), DATE '2026-01-01')) AS INT) AS months_in,
       date_sub(CAST(written_on AS DATE), 3)                                       AS three_before,
       initcap(team)                                                               AS who,
       concat_ws(': ',
                 CASE WHEN team = '' THEN NULL ELSE team END,
                 CASE WHEN substr(note, 1, 5) = '' THEN NULL ELSE substr(note, 1, 5) END) AS short
FROM team_notes;
```

Expected result, for the first row (2026-09-11, a Friday): week_of 2026-09-07, month_end 2026-09-30, month_of 2026-09-01, months_in 8, three_before 2026-09-08, who "Web", short "web: cache".

Notes:
- `DATEDIF` errors if `written_on` is before 2026-01-01. `floor(months_between(...))` would give a negative number instead.
- `date_sub` and `next_day` return strings in some older Hive versions. Cast to DATE if you need a date type.

## X63

I assumed the tables `job_runs` and `scheduler_runs`. All the new columns are on `job_runs`.

- `variance` and `weighted` use the whole column, not the row, so I compute them once in a one-row CTE and cross join it.
- Hive's `/` always gives a double, so `INT(x/4)` is `floor(x/4)`.
- `MIN(duration, 25)` on a blank cell ignores the blank in Excel, so I use `least(COALESCE(duration_mins, 25), 25)`.
- XLOOKUP with `-1` as the not-found value is a left join with a CASE.
- `ISNUMBER(SEARCH(...))` is never an error or NULL in Excel, so I wrap it in `COALESCE(..., false)`.

```sql
WITH stats AS (
  SELECT var_samp(duration_mins)          AS variance,   -- VAR.S(duration_mins)
         SUM(duration_mins * job_id)      AS weighted    -- SUMPRODUCT(duration_mins, job_id)
  FROM job_runs
)
SELECT r.run_id,
       r.job_id,
       r.status,
       r.duration_mins,
       r.avg_retry_secs,
       r.avg_retry_secs IS NULL                                       AS no_retry,        -- ISBLANK
       floor(r.duration_mins / 4)                                     AS quarters,        -- INT(x/4)
       least(COALESCE(r.duration_mins, 25), 25)                       AS capped,          -- MIN(x, 25)
       s.variance,
       s.weighted,
       CASE WHEN sr.run_id IS NULL THEN -1 ELSE sr.job_id END         AS scheduled_job,   -- XLOOKUP(..., -1)
       concat('run ', r.run_id)                                       AS label,           -- CONCATENATE
       COALESCE(instr(lower(r.status), 'cess') > 0, false)            AS succeeded        -- ISNUMBER(SEARCH(..))
FROM job_runs r
CROSS JOIN stats s
LEFT JOIN scheduler_runs sr ON sr.run_id = r.run_id;
```

Expected result:
- no_retry is true for run 98 only.
- quarters = 3, 4, 7, 3, 1, 2, 5, 7, 10.
- capped = 12, 18, 25, 15, 5, 10, 20, 25, 25.
- scheduled_job = 1, 2, 3, 2, -1, 1, 2, 3, 1. Run 99 is not scheduled.
- succeeded is true for SUCCESS runs (95, 96, 101, 103, 104) and false for the rest, including the blank status.

Note: `SEARCH` treats `?` and `*` in the search text as wildcards. "cess" has none, so `instr` is equivalent here.

## X64

I assumed the tables `jobs` and `region_costs`. The workbook has three Power Queries and no formulas.

```sql
-- Power Query "picked_costs"
SELECT job_id,
       cost_cents,
       upper(region) AS region,
       CASE WHEN cost_cents >= 200 THEN 'big' ELSE 'small' END AS size
FROM region_costs
WHERE cost_cents IS NOT NULL
  AND job_id IN (1, 3);
```

```sql
-- Power Query "costed_jobs": jobs that appear in region_costs, and whose name does not start with "n"
SELECT j.job_id, j.job_name, j.team, j.region
FROM jobs j
WHERE j.job_id IN (SELECT job_id FROM region_costs)
  AND j.job_name NOT LIKE 'n%';        -- Text.StartsWith is case-sensitive, and so is LIKE
```

```sql
-- Power Query "costs_filled": NULL cost becomes 0, plus the last two characters of dt as "day"
SELECT job_id,
       COALESCE(cost_cents, 0)        AS cost_cents,
       dt,
       substr(CAST(dt AS STRING), -2) AS day
FROM region_costs;
```

Expected result:
- `picked_costs`: 18 rows (jobs 1 and 3, no NULL costs). Region is upper-cased, and size is "big" for 200 and above.
- `costed_jobs`: job 2 and job 3. Job 1 starts with "n", and job 4 has no costs.
- `costs_filled`: 28 rows, with the last row's cost changed from blank to 0 and day = "24".

## X65

I assumed the tables `jobs`, `region_budgets`, `job_owners`, `scheduler_runs` and `job_runs`. There are five Power Queries and no formulas.

```sql
-- Power Query "team_regions": every team paired with every region (cross join), sorted by team
SELECT t.team, r.region
FROM (SELECT DISTINCT team FROM jobs) t
CROSS JOIN (SELECT DISTINCT region FROM jobs) r
ORDER BY t.team;
```

```sql
-- Power Query "budget_places": biggest budget first, numbered from 1
SELECT job_id,
       budget_cents,
       region,
       row_number() OVER (ORDER BY budget_cents DESC) AS place
FROM region_budgets;
```

```sql
-- Power Query "jobs_per_team": distinct jobs per team
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM job_owners
GROUP BY team;
```

```sql
-- Power Query "ran_as_scheduled": scheduled runs that also ran on that date
SELECT DISTINCT s.run_id, s.dt
FROM scheduler_runs s
JOIN job_runs r
  ON s.run_id = r.run_id
 AND s.dt = r.dt;
```

```sql
-- Power Query "run_measures": unpivot the two measure columns into rows.
-- Table.Unpivot drops rows where the value is null, so the WHERE clauses do the same.
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM job_runs
WHERE avg_retry_secs IS NOT NULL;
```

Expected result:
- `team_regions`: 9 rows (3 teams by 3 regions).
- `budget_places`: job 3 first (350), then 2, 1, 4.
- `jobs_per_team`: data 2, finance 2, web 1. The job_owners history changes finance's owner of job 3 but not the distinct count.
- `ran_as_scheduled`: 8 rows. Run 100 is dropped because it only exists in the scheduler.
- `run_measures`: the query gives 17 rows (9 durations and 8 retry values; run 98 has no retry value).

Notes:
- The workbook's `run_measures` table is only 9 rows long, and shows only the `duration_mins` rows. That cached table looks cut short. I followed the query, which also produces the `avg_retry_secs` rows.
- `row_number()` breaks ties arbitrarily. Power Query's sort keeps the original order for equal budgets. There are no ties here, so it makes no difference.
- Without an `ORDER BY`, SQL does not keep a row order for the other queries.

## X66

I assumed the table `job_runs`. `ok_runs` is a Power Query with three computed columns and a total row.

- The Power Query keeps rows where status is not null and starts with "SUCC". `Text.StartsWith` is case-sensitive, so I use `LIKE 'SUCC%'`.
- `running`: SUMIFS over rows with the same job and `dt` less than or equal to this row's. That is a running sum per job, ordered by `dt`, with ties included (RANGE).
- `share`: duration divided by the table's total.
- The total row is separate from the data.

```sql
WITH ok_runs AS (
  -- Power Query "ok_runs"
  SELECT run_id, job_id, duration_mins, dt
  FROM job_runs
  WHERE status IS NOT NULL
    AND status LIKE 'SUCC%'
)
SELECT run_id,
       job_id,
       duration_mins,
       dt,
       SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt
                                RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,
       duration_mins / SUM(duration_mins) OVER ()                                  AS share
FROM ok_runs;
```

```sql
-- Total row: SUBTOTAL(109, ok_runs[duration_mins])
SELECT 'Total' AS run_id,
       SUM(duration_mins) AS duration_mins
FROM job_runs
WHERE status IS NOT NULL
  AND status LIKE 'SUCC%';
```

Expected result: 5 rows (runs 95, 96, 101, 103, 104). Total duration = 110.

| run_id | running | share |
|---|---|---|
| 95 | 12 | 0.109 |
| 96 | 18 | 0.164 |
| 101 | 62 | 0.091 |
| 103 | 30 | 0.273 |
| 104 | 62 | 0.364 |

Runs 101 and 104 are the same job on the same date, so each running sum includes the other (62 for both). That is how the `"<="&dt` criterion behaves.

SUBTOTAL ignores rows hidden by a filter. SQL cannot see that.

## X69

I assumed the tables `region_costs`, `jobs`, `region_budgets` and `job_totals`. `late_costs` is a Power Query that reads `region_costs` after its formula columns have been added, so it is built on the same CTE.

`region_costs` formula columns:
- `job_name` and `budget`: XLOOKUPs, so left joins. `jobs.job_id` and `region_budgets.job_id` are unique, so there is no fan-out.
- `over_budget`: `cost_cents > budget`. A blank cost counts as 0 in Excel, so the last row is FALSE, not NULL. I use `COALESCE(cost_cents, 0)`.
- `running_cost`: SUMIFS of cost for the same job with `dt` less than or equal to this row's. That is a running sum per job ordered by `dt`, with ties included (RANGE).

```sql
-- region_costs with its four formula columns
SELECT c.job_id,
       c.cost_cents,
       c.region,
       c.dt,
       j.job_name,                                                          -- XLOOKUP
       b.budget_cents                                         AS budget,    -- XLOOKUP
       COALESCE(c.cost_cents, 0) > b.budget_cents             AS over_budget,
       SUM(c.cost_cents) OVER (PARTITION BY c.job_id ORDER BY c.dt
                               RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
FROM region_costs c
LEFT JOIN jobs j           ON c.job_id = j.job_id
LEFT JOIN region_budgets b ON c.job_id = b.job_id;
```

```sql
-- job_totals: per job, total and number of over-budget entries, then a Total row
WITH rc AS (
  SELECT c.job_id, c.dt, c.cost_cents,
         COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget
  FROM region_costs c
  LEFT JOIN region_budgets b ON c.job_id = b.job_id
),
totals AS (
  SELECT t.job_id,
         COALESCE(SUM(rc.cost_cents), 0)                                           AS total_cents,
         COALESCE(SUM(CASE WHEN rc.over_budget THEN 1 ELSE 0 END), 0)               AS over_count
  FROM job_totals t
  LEFT JOIN rc ON rc.job_id = t.job_id
  GROUP BY t.job_id
)
SELECT job_id, total_cents, over_count FROM totals;
```

```sql
-- job_totals Total row: SUBTOTAL(109, ...) on both columns
WITH rc AS (
  SELECT c.job_id, c.cost_cents,
         COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget
  FROM region_costs c
  LEFT JOIN region_budgets b ON c.job_id = b.job_id
),
totals AS (
  SELECT t.job_id,
         COALESCE(SUM(rc.cost_cents), 0)                                           AS total_cents,
         COALESCE(SUM(CASE WHEN rc.over_budget THEN 1 ELSE 0 END), 0)               AS over_count
  FROM job_totals t
  LEFT JOIN rc ON rc.job_id = t.job_id
  GROUP BY t.job_id
)
SELECT 'Total' AS job_id, SUM(total_cents) AS total_cents, SUM(over_count) AS over_count
FROM totals;
```

```sql
-- Power Query "late_costs": rows whose running_cost is over 1500
WITH rc AS (
  SELECT c.job_id, c.dt,
         SUM(c.cost_cents) OVER (PARTITION BY c.job_id ORDER BY c.dt
                                 RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
  FROM region_costs c
)
SELECT job_id, dt, running_cost
FROM rc
WHERE running_cost > 1500;
```

Notes:
- The `late_costs` table in the workbook shows `running_cost` values of 100, 120 and 180. Those cannot pass a `> 1500` filter, and they look like plain `cost_cents`. I treat that cache as stale and follow the query.
- Running totals from the data: job 1 passes 1500 on 20260922 (1550), 20260923 (1670) and 20260924 (1770). Job 2 passes it on 20260922 (1510), 20260923 (1690) and 20260924 (1690, because the last cost is blank and SUMIFS ignores it). So the query returns those six rows, with the real running totals.
- If a job has no row in `region_budgets`, XLOOKUP gives `#N/A` and `over_budget` is NULL here. Every costed job has a budget in this data.
- The job_totals Total row mixes a text label with numbers in a column. In a real table, keep it as its own query or add it in a report.

## X70

I assumed the tables `jobs`, `job_owners` and `job_runs`. There are three Power Queries.

- `staffed` is connection only (never loaded to a sheet), so it is a CTE that the next two queries share. The CTE is repeated in each query, since a CTE only lives inside one statement.
- `owner_load` joins `staffed` to `job_runs` with a left join. Its `runs` column is `Table.RowCount(_)`, a row count of the group, so it is `COUNT(*)`.
- `avg_mins` is a formula column added on the sheet after loading, so it is not part of the Power Query output (and `busiest_owner` does not carry it).
- `busiest_owner` takes the top row after sorting `owner_load` by `runs`.

```sql
-- Power Query "owner_load" (+ the sheet's avg_mins column)
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM (SELECT job_id, job_name FROM jobs) j
  JOIN (SELECT DISTINCT job_id, owner FROM job_owners) o
    ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner,
         SUM(r.duration_mins) AS total_mins,
         COUNT(*)             AS runs
  FROM staffed s
  LEFT JOIN job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner,
       total_mins,
       runs,
       total_mins / runs AS avg_mins
FROM owner_load;
```

```sql
-- owner_load Total row: SUBTOTAL(109, owner_load[runs])
WITH staffed AS (
  SELECT j.job_id, o.owner
  FROM jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT 'Total' AS owner, SUM(runs) AS runs
FROM owner_load;
```

```sql
-- Power Query "busiest_owner": the owner with the most runs
WITH staffed AS (
  SELECT j.job_id, o.owner
  FROM jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs
FROM owner_load
ORDER BY runs DESC
LIMIT 1;
```

Expected result:
- `staffed` has four rows: (1, ana), (2, ben), (3, ana), (3, chloe). Job 4 has no owner and is dropped.
- `owner_load`: ana 127 mins over 6 runs (avg 21.17), ben 53 over 3 (17.67), chloe 60 over 2 (30). The Total row's runs = 11.
- `busiest_owner`: ana, 127, 6.

Notes:
- Job 3 has two owners (ana and chloe), so both are credited with all of job 3's runs. The 11 total counts those runs twice.
- If two owners tie on `runs`, `LIMIT 1` picks one arbitrarily. Power Query's stable sort would pick the first in `owner_load` order. Add a second sort key to make it deterministic.
