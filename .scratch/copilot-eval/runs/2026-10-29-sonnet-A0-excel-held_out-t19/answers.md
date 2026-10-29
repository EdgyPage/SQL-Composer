date: 2026-10-29
arm: A0
model: sonnet
files: none

## X21

The only calculations are the two formula columns on `region_budgets`. Hive's `/` always returns a double, so `/100` behaves like Excel.

```sql
SELECT
  job_id,
  budget_cents,
  region,
  budget_cents / 100  AS budget_dollars,
  budget_cents * 1.1  AS with_margin
FROM region_budgets;
```

## X22

`IFERROR(job_id/(job_id-2),0)` turns a divide-by-zero into 0. In Hive, dividing by zero returns NULL instead of raising an error. I made the zero case explicit so the intent is clear (job 2 gives 0).

```sql
SELECT
  job_id,
  job_name,
  team,
  CASE WHEN team = 'finance' THEN 'yes' ELSE 'no' END AS is_finance,
  CASE WHEN job_id - 2 = 0 THEN 0
       ELSE job_id / (job_id - 2) END                 AS ratio
FROM jobs;
```

## X23

`SWITCH` becomes a simple `CASE`. The blank status in run 98 falls to "other". `OR` with a blank needs care. In Excel a blank compares as FALSE, but in SQL NULL makes the whole OR NULL. So I wrap each test in `COALESCE(..., false)`.

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
  COALESCE(status = 'FAILED', false)
    OR COALESCE(avg_retry_secs > 5, false) AS risky
FROM job_runs;
```

## X24

- `LEFT(note, FIND(" ", note) - 1)` becomes `substr(note, 1, instr(note, ' ') - 1)`. Excel would show #VALUE! if a note had no space. In Hive `instr` returns 0 and you get an empty string. Every note here has a space.
- `MONTH` works on a `yyyy-MM-dd` date or string.
- `ROUND(x, 1)` is `round(x, 1)`.

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

The workbook has two tables.

- `Costs` gets a `Day` column rebuilt from the `Day Key` number (yyyymmdd). I build an ISO string and cast it to DATE. Column names with spaces or brackets need backticks in Hive.
- `Budgets` gets `Dollars`.
- The last Costs row has an empty `Cost (cents)`. It stays NULL.

```sql
SELECT
  `Job`,
  `Cost (cents)`,
  `Region`,
  `Day Key`,
  CAST(CONCAT(SUBSTR(CAST(`Day Key` AS STRING), 1, 4), '-',
              SUBSTR(CAST(`Day Key` AS STRING), 5, 2), '-',
              SUBSTR(CAST(`Day Key` AS STRING), 7, 2)) AS DATE) AS `Day`
FROM Costs;

SELECT
  `Job`,
  `Budget`,
  `Region`,
  `Budget` / 100 AS `Dollars`
FROM Budgets;
```

## X26

- `XLOOKUP` and `VLOOKUP(...,3,FALSE)` are both exact lookups on `run_id`. Column 3 of `job_runs` is `status`. In SQL they are one left join, which assumes `run_id` is unique in `job_runs`.
- `AVERAGEIFS` averages `duration_mins` over all `job_runs` rows of that job. A window over the joined rows would average over alert rows, so I compute it separately per job and join it back.
- No match gives NULL, where Excel shows #N/A or #DIV/0!.

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
LEFT JOIN job_runs r  ON a.run_id = r.run_id
LEFT JOIN job_avg  ja ON r.job_id = ja.job_id;
```

## X27

`by_team` is a typed list of teams (data, finance, web) with calculated columns. So it stays the driving table and the other values are joined to it. `COUNTIFS` is a count, `MAXIFS` is a max, and `INDEX/MATCH` on the max id is a join back to `jobs` (job_id is unique). For a team with no jobs, `COUNTIFS` gives 0 and `MAXIFS` gives 0 in Excel. Here the count is 0 and the id is NULL.

```sql
WITH agg AS (
  SELECT team, COUNT(*) AS jobs_in_team, MAX(job_id) AS last_job_id
  FROM jobs
  GROUP BY team
)
SELECT
  t.team,
  COALESCE(a.jobs_in_team, 0) AS jobs_in_team,
  a.last_job_id,
  j.job_name                  AS last_job_name
FROM by_team t
LEFT JOIN agg  a ON t.team = a.team
LEFT JOIN jobs j ON j.job_id = a.last_job_id;
```

## X28

`ok_mins` is the sum of `duration_mins` for that job where status is `SUCCESS`. `SUMIFS` gives 0 when nothing matches, so I use `COALESCE(..., 0)`. The `Keys` table says `jobs` is keyed on `job_id`.

One thing needs your decision. Row 3 (job 3, report_build) holds a typed value, 99, instead of the formula. With the formula it would be 30. A typed number in the middle of a formula column is usually a mistake or an old override. I converted the formula for every row. If 99 is deliberate, swap in the commented line.

```sql
WITH ok AS (
  SELECT job_id, SUM(duration_mins) AS ok_mins
  FROM job_runs
  WHERE status = 'SUCCESS'
  GROUP BY job_id
)
SELECT
  j.job_id,
  j.job_name,
  COALESCE(ok.ok_mins, 0) AS ok_mins
  -- to keep the typed 99 for job 3:
  -- CASE WHEN j.job_id = 3 THEN 99 ELSE COALESCE(ok.ok_mins, 0) END AS ok_mins
FROM jobs j
LEFT JOIN ok ON j.job_id = ok.job_id;
```

## X29

- `in_dollars` divides by the `cents_per_dollar` value looked up in `Parameters`. I read it as a single-row table and cross join it.
- Row 3 (job 3) holds a typed 5, but 350 / 100 is 3.5. That looks like a mistake, so I applied the formula to every row. If 5 is intended, add a `CASE WHEN job_id = 3 THEN 5` override.
- `pointer = INDIRECT("A"&ROW())` has no SQL equivalent. It reads whatever is in column A of the same sheet row, which depends on cell positions rather than data. On this sheet column A is `job_id`, so `job_id AS pointer` would give the same values today. I left it out rather than guess. Tell me if you want it as `job_id`.

```sql
SELECT
  r.job_id,
  r.budget_cents,
  r.region,
  r.budget_cents / p.cents_per_dollar AS in_dollars
FROM region_budgets r
CROSS JOIN (
  SELECT CAST(value AS DOUBLE) AS cents_per_dollar
  FROM Parameters
  WHERE name = 'cents_per_dollar'
) p;
```

## X30

Per column:

- `day = RIGHT(dt, 2)` is `substr(dt, -2)`.
- `prev_run = OFFSET(run_id, -1, 0)` is the run_id of the row above. In SQL that is `lag` over the table's order. I assume the sheet order is run_id ascending, because SQL tables have no row order. For the first row Excel reads the header cell ("run_id"), while `lag` gives NULL.
- `jitter = RANDBETWEEN(1,5)` is random and recalculates each time. The Hive version is `1 + floor(rand() * 5)`. It will give different numbers on every run and cannot reproduce the workbook's values.

The PivotTable (count of run_id per job_id) is a plain `GROUP BY`, shown second. The bar chart on `Summary` is not a calculation, so it has no SQL.

```sql
SELECT
  run_id,
  job_id,
  dt,
  substr(dt, -2)                              AS day,
  lag(run_id) OVER (ORDER BY run_id)          AS prev_run,
  CAST(1 + floor(rand() * 5) AS INT)          AS jitter
FROM scheduler_runs;

-- PivotTable "Pivot"
SELECT job_id, COUNT(run_id) AS count_of_run_id
FROM scheduler_runs
GROUP BY job_id;
```

## X31

- `TAG` is a LAMBDA: `UPPER(t) & "!"`, so `concat(upper(team), '!')`.
- `scaled` uses `Summary!D4` (7) and `boosted` uses the defined name `boost`, which is `Summary!B2` (10). I inline both as constants, with a comment saying where they came from.
- **`bump` can't be converted.** Its formula is `jobs[bump] * 2`, which refers to itself, a circular reference. Excel can't calculate it. I left `bump` out. Tell me what it should be built from, such as `job_id * 2`, and I'll add it.

```sql
SELECT
  job_id,
  team,
  concat(upper(team), '!') AS tag,
  job_id * 7               AS scaled,   -- Summary!D4
  job_id * 10              AS boosted   -- name "boost" = Summary!B2
FROM jobs;
```

## X32

`VLOOKUP(job_id, jobs, 2, TRUE)` is an approximate match, which only works on a sorted list. It takes the closest job_id at or below the one you look up. Here `jobs` is sorted and every job_id in `job_runs` has an exact match, so the results equal an exact left join. I converted it as an exact join. If you ever have a job_id missing from `jobs`, Excel would return a neighbouring job's name and this SQL returns NULL. That is probably what you want.

`by_name.runs` counts `job_runs` rows with that job name.

```sql
WITH runs_named AS (
  SELECT r.run_id, j.job_name
  FROM job_runs r
  LEFT JOIN jobs j ON r.job_id = j.job_id
)
SELECT
  b.job_name,
  COUNT(rn.run_id) AS runs
FROM by_name b
LEFT JOIN runs_named rn ON rn.job_name = b.job_name
GROUP BY b.job_name;
```

For the full `job_runs` table with its `job_name` column:

```sql
SELECT r.*, j.job_name
FROM job_runs r
LEFT JOIN jobs j ON r.job_id = j.job_id;
```

## X33

This is a Power Query pulling from the SQL Server table `ops.job_runs`, so I wrote it as SQL on that table.

One difference between the two languages: in Power Query, `[status] <> "TEST"` is true for a null status. In SQL `NULL <> 'TEST'` is NULL, so those rows would be dropped. I added a null-safe test so they stay. With this data it makes no difference.

```sql
SELECT
  run_id,
  duration_mins,
  duration_mins - 20 AS over_by
FROM ops.job_runs
WHERE duration_mins >= 20
  AND (status IS NULL OR status <> 'TEST');
```

## X34

Two queries. `runs_with_team` is connection-only: a left outer join of `job_runs` to `jobs`, keeping `team`. `team_totals` groups it by team.

```sql
WITH runs_with_team AS (
  SELECT r.*, j.team
  FROM job_runs r
  LEFT OUTER JOIN jobs j ON r.job_id = j.job_id
)
SELECT
  team,
  SUM(duration_mins) AS total_mins,
  MAX(duration_mins) AS longest
FROM runs_with_team
GROUP BY team;
```

This returns data 67 / 40 and finance 113 / 30, matching the sheet. SQL does not promise an output order, so add `ORDER BY` if you need one.

## X35

- `recent`: `Table.Combine` is `UNION ALL`, which keeps duplicates. The sort is by run_id descending and `FirstN(4)` is `LIMIT 4`. The result 104, 104, 103, 103 shows the duplicates are kept. I added `dt` as a tie-breaker so the result is stable.
- The `rates` query calls a web address (`rates.example.com`). It is connection-only and nothing in the workbook uses it. Hive can't make a web call, so I left it out. If you need those rates, load them into a table first.

```sql
SELECT run_id, dt
FROM (
  SELECT run_id, dt FROM job_runs
  UNION ALL
  SELECT run_id, dt FROM scheduler_runs
) both_tables
ORDER BY run_id DESC, dt DESC
LIMIT 4;
```

## X36

- `job_runs.alerts` counts matching rows in `run_alerts`, so it is a left join with a count.
- `severity_by_day` is a pivot. Power Query builds the columns from the distinct severities it finds. Hive can't create columns from data, so I wrote out `high` and `low`. A new severity value would need a new line. Cells with no alerts stay NULL, as in the pivot (a `SUM` of nothing).

```sql
SELECT
  r.run_id,
  r.status,
  COUNT(a.run_id) AS alerts
FROM job_runs r
LEFT JOIN run_alerts a ON a.run_id = r.run_id
GROUP BY r.run_id, r.status;

SELECT
  dt,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low'  THEN 1 END) AS low
FROM run_alerts
GROUP BY dt;
```

## X37

Only `Is Ana` is calculated. A blank owner is not "ana", so it gets 0. A `CASE` does this, because `NULL = 'ana'` would otherwise stay NULL.

```sql
SELECT
  `Job No`,
  `Team Name`,
  `Owner`,
  `Day`,
  CASE WHEN `Owner` = 'ana' THEN 1 ELSE 0 END AS `Is Ana`
FROM Owners;
```

## X38

- `region` is a lookup of `jobs.region` by `job_id`, so a left join.
- `region_mins` is `SUMIFS` of `duration_mins` over all rows in the same region, which is a window sum partitioned by region.
- `retry_cost` is `(avg_retry_secs + duration_mins) * 2`. Excel treats the blank `avg_retry_secs` (run 98) as 0, so I use `COALESCE(..., 0)`.
- Row 8 (run 102) holds a typed 1 where the formula would give 52. That looks like a pasted-over value. I converted the formula for every row, with the override in a comment if you want it kept.
- The `Keys` table lists `run_id` as the key of `job_runs`. The SQL assumes `run_id` is unique and `jobs.job_id` is unique.

```sql
WITH with_region AS (
  SELECT r.*, j.region
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
  (COALESCE(avg_retry_secs, 0) + duration_mins) * 2 AS retry_cost
  -- to keep the typed 1 for run 102:
  -- CASE WHEN run_id = 102 THEN 1 ELSE (COALESCE(avg_retry_secs, 0) + duration_mins) * 2 END AS retry_cost
FROM with_region;
```

## X39

`ok_runs` is a Power Query over `job_runs` (status = SUCCESS, three columns). Calculated columns sit on top of it.

- `job_name`: a lookup, so a left join to `jobs`.
- `share`: `duration_mins` divided by the sum for the same job within `ok_runs`, so a window sum.
- `noise = RAND()` is random and changes on every recalculation. `rand()` in Hive does the same, but the numbers will not match the workbook, and they differ on every run.

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins
  FROM job_runs
  WHERE status = 'SUCCESS'
)
SELECT
  o.run_id,
  o.job_id,
  o.duration_mins,
  j.job_name,
  o.duration_mins / SUM(o.duration_mins) OVER (PARTITION BY o.job_id) AS share,
  rand() AS noise
FROM ok_runs o
LEFT JOIN jobs j ON o.job_id = j.job_id;
```

## X40

The workbook has four parts.

- `Runs.Team`: lookup of `jobs.team`.
- `Runs.Cost`: `Mins` times the `rate` row of `Parameters` (2).
- `Teams.Total Cost`: sum of cost per team.
- `run_alerts.Run Mins`: lookup of `Runs.Mins`.

The PivotTable (sum of cost by team) is the last query.

```sql
WITH runs_calc AS (
  SELECT
    r.`Run`,
    r.`Job`,
    r.`Mins`,
    j.team                AS `Team`,
    r.`Mins` * p.rate     AS `Cost`
  FROM Runs r
  LEFT JOIN jobs j ON r.`Job` = j.job_id
  CROSS JOIN (
    SELECT CAST(value AS DOUBLE) AS rate
    FROM Parameters
    WHERE name = 'rate'
  ) p
)
SELECT * FROM runs_calc;

-- Teams
WITH runs_calc AS (
  SELECT j.team AS team, r.`Mins` * p.rate AS cost
  FROM Runs r
  LEFT JOIN jobs j ON r.`Job` = j.job_id
  CROSS JOIN (SELECT CAST(value AS DOUBLE) AS rate FROM Parameters WHERE name = 'rate') p
)
SELECT
  t.`Team`,
  COALESCE(SUM(c.cost), 0) AS `Total Cost`
FROM Teams t
LEFT JOIN runs_calc c ON c.team = t.`Team`
GROUP BY t.`Team`;

-- run_alerts
SELECT
  a.alert_id,
  a.run_id,
  a.severity,
  a.dt,
  r.`Mins` AS `Run Mins`
FROM run_alerts a
LEFT JOIN Runs r ON a.run_id = r.`Run`;

-- PivotTable "Pivot": sum of Cost by Team
WITH runs_calc AS (
  SELECT j.team AS team, r.`Mins` * p.rate AS cost
  FROM Runs r
  LEFT JOIN jobs j ON r.`Job` = j.job_id
  CROSS JOIN (SELECT CAST(value AS DOUBLE) AS rate FROM Parameters WHERE name = 'rate') p
)
SELECT team, SUM(cost) AS sum_of_cost
FROM runs_calc
GROUP BY team;
```

## X46

- `shortest = MINIFS`. Excel gives 0 when no row matches (job 4 has no runs). A SQL `MIN` gives NULL, so I use `COALESCE(..., 0)` to match.
- `runs = COUNTIF`.
- `busiest = RANK.EQ(runs, jobs[runs])`, descending by default, so rank 1 is the job with the most runs. That is `RANK() OVER (ORDER BY runs DESC)`, which also gives tied rows the same rank.

```sql
WITH per_job AS (
  SELECT job_id, MIN(duration_mins) AS shortest, COUNT(*) AS runs
  FROM job_runs
  GROUP BY job_id
),
calc AS (
  SELECT
    j.job_id,
    j.job_name,
    j.team,
    COALESCE(p.shortest, 0) AS shortest,
    COALESCE(p.runs, 0)     AS runs
  FROM jobs j
  LEFT JOIN per_job p ON j.job_id = p.job_id
)
SELECT
  job_id,
  job_name,
  team,
  shortest,
  runs,
  RANK() OVER (ORDER BY runs DESC) AS busiest
FROM calc;
```

## X47

- `RANK.EQ(x, range, 1)` is an ascending rank, so `RANK() OVER (ORDER BY budget_cents ASC)`.
- `SUMIF` and `AVERAGEIF` by region are window functions partitioned by region.

```sql
SELECT
  job_id,
  budget_cents,
  region,
  RANK() OVER (ORDER BY budget_cents ASC)   AS cheapest_first,
  SUM(budget_cents) OVER (PARTITION BY region) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM region_budgets;
```

## X48

There are two Power Queries.

- `quiet_runs` is a left anti join: runs with no alert. Hive has no `LEFT ANTI JOIN` keyword, so I use a left join and keep the unmatched rows.
- `slow_regions` joins runs to jobs (inner join), groups by region, then keeps regions averaging 20 or more minutes. The filter after the grouping is `HAVING`. Only NYC qualifies (30 / 30).

```sql
-- quiet_runs
SELECT r.run_id, r.job_id, r.status
FROM job_runs r
LEFT JOIN run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL;

-- slow_regions
SELECT
  j.region,
  AVG(r.duration_mins) AS avg_mins,
  MIN(r.duration_mins) AS fastest
FROM job_runs r
INNER JOIN jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20;
```

## X49

There are three Power Queries.

- `alert_status`: `Alerts` right outer join `Runs`, so every run is kept, with its alert if any. Runs with no alert have NULL `alert_id` and `severity`.
- `run_check`: full outer join of runs and scheduler runs on `run_id`. Run 99 has no scheduled run, and scheduled run 100 has no run.
- `teams`: the distinct teams of `jobs` and `job_owners` combined. `UNION` (without `ALL`) removes duplicates.

```sql
-- alert_status
SELECT a.alert_id, a.severity, r.status
FROM run_alerts a
RIGHT OUTER JOIN job_runs r ON a.run_id = r.run_id;

-- run_check
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM job_runs r
FULL OUTER JOIN scheduler_runs s ON r.run_id = s.run_id;

-- teams
SELECT team FROM jobs
UNION
SELECT team FROM job_owners;
```

## X50

`owners` is a Power Query: `job_id` and `owner` from `job_owners`, duplicates removed (`SELECT DISTINCT`). Two calculated columns sit on top.

- `job_name`: lookup from `jobs`.
- `newest_first = RANK.EQ(job_id, owners[job_id])`, descending, so the highest job_id is rank 1. Tied job_ids share a rank, as in `RANK()`. Job 3 appears twice (ana and chloe), so both rows get rank 2 and job 2 gets rank 4.

```sql
WITH owners AS (
  SELECT DISTINCT job_id, owner
  FROM job_owners
)
SELECT
  o.job_id,
  o.owner,
  j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM owners o
LEFT JOIN jobs j ON o.job_id = j.job_id;
```
