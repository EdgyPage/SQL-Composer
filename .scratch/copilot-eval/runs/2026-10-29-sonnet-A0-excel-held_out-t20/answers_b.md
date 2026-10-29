date: 2026-10-29
arm: A0
model: sonnet
files: none

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
