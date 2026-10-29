date: 2026-10-29
arm: C
model: haiku
files: f80b90b

## X40

Sources: `Runs` (Run, Job, Mins), `jobs` (job_id, job_name, team, region).
Steps: `Runs`, for its Team and Cost columns, which `Teams` reads.
Finals: `Teams`, a summary of `Runs` (GROUP BY Team): Team, `<total_cost>`. `run_alerts`: alert_id, run_id, severity, dt, `<run_mins>`.
Parameters: none. The rate, 2, is written into Cost.
Keys: blank, and nothing is typed over, so none is needed.

Typed over: none. Marks: none. Refused: none.
Left alone: the PivotTable on sheet "Pivot" (from Runs), and the Steps sheet (text).

Final `Teams`:

```sql
WITH Runs AS (
  SELECT r.Run, r.Job, r.Mins,
    j.team AS Team,
    r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT Team,
  COALESCE(SUM(Cost), 0) AS <total_cost>
FROM Runs
GROUP BY Team
```

Final `run_alerts`:

```sql
SELECT a.alert_id, a.run_id, a.severity, a.dt,
  r.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN <database>.Runs r ON a.run_id = r.Run
```

Fill in: `<database>`, `<total_cost>`, `<run_mins>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X46

Sources: `jobs` (job_id, job_name, team), `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: none.
Finals: `jobs`: job_id, job_name, team, shortest, runs, busiest.
Parameters and Keys: blank, so none.

Typed over: none. Marks: none. Refused: none.
Left alone: the Steps sheet (text).

Final `jobs`:

```sql
SELECT job_id, job_name, team, shortest, runs,
  RANK() OVER (ORDER BY runs DESC) AS busiest
FROM (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(s.shortest, 0) AS shortest,
    COALESCE(c.runs, 0) AS runs
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, MIN(duration_mins) AS shortest
    FROM <database>.job_runs
    GROUP BY job_id
  ) s ON j.job_id = s.job_id
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS runs
    FROM <database>.job_runs
    GROUP BY job_id
  ) c ON j.job_id = c.job_id
) t
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X47

Sources: `region_budgets` (job_id, budget_cents, region).
Steps: none.
Finals: `region_budgets`: job_id, budget_cents, region, cheapest_first, region_total, region_avg.
Parameters and Keys: blank, so none.

Typed over: none. Marks: none. Refused: none.
Notes: cheapest_first is RANK ascending, as the third argument is 1. region_total is the SUMIF form, COALESCE to 0. region_avg is the AVERAGEIF form, left NULL where nothing matches.
Left alone: the Steps sheet (text).

Final `region_budgets`:

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X48

Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), `jobs` (job_id, job_name, team, region), `run_alerts` (alert_id, run_id, severity, dt).
Steps: none.
Finals: `quiet_runs` (loaded by its query): run_id, job_id, status. `slow_regions` (loaded by its query): region, avg_mins, fastest.
Parameters and Keys: blank, so none.

Typed over: none. Marks: none. Refused: none.
Notes: quiet_runs' LeftAnti join is a LEFT JOIN with WHERE on the null key, t's columns only. slow_regions' Table.Group is a GROUP BY, and the filter after it is HAVING on the aggregate.
Left alone: the Steps sheet (text).

Final `quiet_runs`:

```sql
SELECT t.run_id, t.job_id, t.status
FROM <database>.job_runs t
LEFT JOIN <database>.run_alerts u ON t.run_id = u.run_id
WHERE u.run_id IS NULL
```

Final `slow_regions`:

```sql
SELECT j.region, AVG(t.duration_mins) AS avg_mins, MIN(t.duration_mins) AS fastest
FROM <database>.job_runs t
JOIN <database>.jobs j ON t.job_id = j.job_id
GROUP BY j.region
HAVING AVG(t.duration_mins) >= 20
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X49

Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), `jobs` (job_id, job_name, team, region), `run_alerts` (alert_id, run_id, severity, dt), `scheduler_runs` (run_id, job_id, dt), `job_owners` (job_id, team, owner, dt).
Steps: none.
Finals: `alert_status` (loaded by its query): alert_id, severity, status. `run_check` (loaded by its query): run_id, status, scheduled_run. `teams` (loaded by its query): team.
Parameters and Keys: blank, so none.

Typed over: none. Marks: none. Refused: none.
Notes: alert_status is a RightOuter join, so it is a LEFT JOIN with the two tables swapped and keeps every job_runs row, with NULL alert columns where no alert matches. run_check is a FULL OUTER JOIN. teams is a UNION, as Table.Combine inside Table.Distinct.
Left alone: the Steps sheet (text).

Final `alert_status`:

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON a.run_id = r.run_id
```

Final `run_check`:

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM (SELECT run_id, status FROM <database>.job_runs) r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

Final `teams`:

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X50

Sources: `job_owners` (job_id, team, owner, dt), `jobs` (job_id, job_name, team, region).
Steps: none.
Finals: `owners` (loaded by its query, a SELECT DISTINCT of job_id and owner from job_owners): job_id, owner, job_name, newest_first.
Parameters and Keys: blank, so none.

Typed over: none. Marks: the blank owner for job 4 stays NULL, as no formula reads owner. Refused: none.
Left alone: the Steps sheet (text).

Final `owners`:

```sql
SELECT o.job_id, o.owner,
  j.job_name AS job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X59

Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), `jobs` (job_id, job_name), `run_alerts` (alert_id, run_id, severity, dt).
Steps: none.
Finals: `jobs`: job_id, job_name, long_runs, failed_mins, not_test. `run_alerts`: alert_id, run_id, severity, dt, alerts_so_far.
Parameters and Keys: blank, so none.

Typed over: none.
Marks: the blank status on run 98 is left NULL and not wrapped. It sits in the COUNTIFS and SUMIFS forms, which skip a blank, and the "<>TEST" form counts it through `status IS NULL`.
Refused: none.
Left alone: the Steps sheet (text).

Final `jobs`:

```sql
SELECT j.job_id, j.job_name,
  COALESCE(l.long_runs, 0) AS long_runs,
  COALESCE(f.failed_mins, 0) AS failed_mins,
  COALESCE(n.not_test, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS long_runs
  FROM <database>.job_runs
  WHERE duration_mins >= 20
  GROUP BY job_id
) l ON j.job_id = l.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS failed_mins
  FROM <database>.job_runs
  WHERE LOWER(status) LIKE 'f%'
  GROUP BY job_id
) f ON j.job_id = f.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS not_test
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) n ON j.job_id = n.job_id
```

Final `run_alerts`:

```sql
SELECT alert_id, run_id, severity, dt,
  COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X60

Sources: `region_budgets` (job_id, budget_cents, region).
Steps: none.
Finals: `region_budgets`: job_id, budget_cents, region, share, above_avg, rank_in_region. `region_budgets (Total Row)`: one row, two columns, job_id (a count) and budget_cents (an average), with no label.
Parameters and Keys: blank, so none.

Typed over: none. Marks: none.
Notes: the Total Row's "Total" label is dropped. Its totals are COUNT (SUBTOTAL 103) and AVG (SUBTOTAL 101), so it has a query of its own.
Refused: none.
Left alone: the Steps sheet (text).

Final `region_budgets`:

```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

Final `region_budgets (Total Row)`:

```sql
SELECT COUNT(job_id) AS job_id,
  AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X61

Sources: `region_costs` (job_id, cost_cents, region, dt). `jobs` (job_id, job_name, team, region), which the costed_jobs query reads as a Table of this name; this workbook doesn't hold it, so it is used as `<database>.jobs`, and you should check it.
Steps: none.
Finals:
- `by_region`, a summary of `region_costs` (GROUP BY region). Its Total Row needs no query of its own, as its totals are SUMs and a MAX: the query ends GROUP BY region WITH ROLLUP, and the NULL-region row is the Total. Columns: region, total_cents, entries, priciest.
- `picked_costs`: job_id, cost_cents, region, size.
- `costed_jobs`: job_id, job_name, team, region.
- `costs_filled`: job_id, cost_cents, dt, day.
Parameters and Keys: blank, so none.

Typed over: none.
Marks: the blank cost_cents on row 29 (job 2, 20260924) is replaced by 0 in costs_filled, so `COALESCE(cost_cents, 0)` (blank). The SUMIFS and MAXIFS in by_region skip it, so no wrap there. dt is held as text (20260911); day takes its last 2 characters, so no date conversion.
Refused: none.
Left alone: the Steps sheet (text).

Final `by_region`:

```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(*), 0) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

Final `picked_costs`:

```sql
SELECT job_id, cost_cents,
  UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

Final `costed_jobs`:

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

Final `costs_filled`:

```sql
SELECT job_id,
  COALESCE(cost_cents, 0) AS cost_cents,
  dt,
  SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X62

Sources: `team_notes` (team, note, written_on).
Steps: none.
Finals: `team_notes`: team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short.
Parameters and Keys: blank, so none.

Typed over: none. Marks: none. Refused: none.
Left alone: the Steps sheet (text).

Final `team_notes`:

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

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X63

Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs), `scheduler_runs` (run_id, job_id, dt).
Steps: none.
Finals: `job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded.
Parameters and Keys: blank, so none.

Typed over: none.
Marks: the blank status on run 98 (blank) is wrapped as `COALESCE(status, '')` in succeeded, since SEARCH reads it and it is not in an -IF(S) form. The blank avg_retry_secs on run 98 is not wrapped: ISBLANK is `IS NULL`, which skips it.
Notes: scheduled_job takes -1 from XLOOKUP's fourth argument, as COALESCE.
Refused: none.
Left alone: the Steps sheet (text).

Final `job_runs`:

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

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X64

Sources: `jobs` (job_id, job_name, team, region), `region_costs` (job_id, cost_cents, region, dt).
Steps: none.
Finals:
- `picked_costs`: job_id, cost_cents, region, size.
- `costed_jobs`: job_id, job_name, team, region.
- `costs_filled`: job_id, cost_cents, dt, day.
Parameters and Keys: blank, so none.

Typed over: none.
Marks: the blank cost_cents on row 29 (job 2, 20260924) becomes 0 in costs_filled, so `COALESCE(cost_cents, 0)` (blank). dt is held as text (20260911); day takes its last 2 characters, so no date conversion.
Refused: none.
Left alone: the Steps sheet (text).

Final `picked_costs`:

```sql
SELECT job_id, cost_cents,
  UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

Final `costed_jobs`:

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

Final `costs_filled`:

```sql
SELECT job_id,
  COALESCE(cost_cents, 0) AS cost_cents,
  dt,
  SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X65

Sources: `jobs` (job_id, job_name, team, region), `region_budgets` (job_id, budget_cents, region), `job_owners` (job_id, team, owner, dt), `scheduler_runs` (run_id, job_id, dt), `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: none.
Finals (each loaded by its query):
- `team_regions`: team, region.
- `budget_places`: job_id, budget_cents, region, place.
- `jobs_per_team`: team, jobs.
- `ran_as_scheduled`: run_id, dt.
- `run_measures`: run_id, job_id, measure, amount.
Parameters and Keys: blank, so none.

Typed over: none.
Marks: the blank avg_retry_secs on run 98 drops out of run_measures, as M's unpivot drops a null there. team_regions' Table.Sort has nothing after it but the cross join, so its order is dropped, as a Hive table holds no order. budget_places' sort is kept as ROW_NUMBER's ORDER BY.
Refused: none.
Left alone: the Steps sheet (text).

Final `team_regions`:

```sql
SELECT t.team, r.region
FROM (SELECT DISTINCT team FROM <database>.jobs) t
CROSS JOIN (SELECT DISTINCT region FROM <database>.jobs) r
```

Final `budget_places`:

```sql
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

Final `jobs_per_team`:

```sql
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

Final `ran_as_scheduled`:

```sql
SELECT DISTINCT s.run_id, s.dt
FROM <database>.scheduler_runs s
JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.dt = r.dt
```

Final `run_measures`:

```sql
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X66

Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: none.
Finals:
- `ok_runs` (loaded by its query): run_id, job_id, duration_mins, dt, running, share.
- `ok_runs (Total Row)`: one row, one column, duration_mins (a SUM), with no label.
Parameters and Keys: blank, so none.

Typed over: none.
Marks: the blank status on run 98 drops out of the query, as M's `<> null` filter does.
Notes: running is a running total per job_id in dt order, ties included, so it uses RANGE. The Total Row is a SUM, and ok_runs is not a summary, so it has a query of its own.
Refused: none.
Left alone: the Steps sheet (text).

Final `ok_runs`:

```sql
SELECT run_id, job_id, duration_mins, dt,
  SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
) ok
```

Final `ok_runs (Total Row)`:

```sql
SELECT SUM(duration_mins) AS duration_mins
FROM (
  SELECT duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
) ok
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X69

Sources: `region_costs` (job_id, cost_cents, region, dt), `jobs` (job_id, job_name, team, region), `region_budgets` (job_id, budget_cents, region).
Steps: `region_costs`, for its job_name, budget, over_budget and running_cost columns, which `job_totals` and `late_costs` read. It is a CTE in each of their queries.
Finals:
- `job_totals`, a summary of `region_costs` (GROUP BY job_id): job_id, total_cents, over_count. Its Total Row needs no query of its own: the query ends GROUP BY job_id WITH ROLLUP, and the NULL-job row is the Total.
- `late_costs` (loaded by its query): job_id, dt, running_cost.
Parameters and Keys: blank, so none.

Typed over: none.
Marks: the blank cost_cents on row 29 (job 2, 20260924) is wrapped as `COALESCE(cost_cents, 0)` in over_budget, since a comparison is not an -IF(S) form (blank). The SUMIFS in running_cost and total_cents skip it. dt is held as text (20260911), so running_cost orders by the converted date, and the output dt stays as text.
Refused: none.
Left alone: the Steps sheet (text).

Final `job_totals`:

```sql
WITH region_costs AS (
  SELECT c.job_id, c.cost_cents, c.region, c.dt,
    j.job_name AS job_name,
    b.budget_cents AS budget,
    COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
    SUM(c.cost_cents) OVER (
      PARTITION BY c.job_id
      ORDER BY CONCAT(SUBSTR(c.dt, 1, 4), '-', SUBSTR(c.dt, 5, 2), '-', SUBSTR(c.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_cost
  FROM <database>.region_costs c
  LEFT JOIN <database>.jobs j ON c.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON c.job_id = b.job_id
)
SELECT job_id,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(CASE WHEN over_budget = TRUE THEN 1 END), 0) AS over_count
FROM region_costs
GROUP BY job_id WITH ROLLUP
```

Final `late_costs`:

```sql
WITH region_costs AS (
  SELECT c.job_id, c.cost_cents, c.region, c.dt,
    j.job_name AS job_name,
    b.budget_cents AS budget,
    COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
    SUM(c.cost_cents) OVER (
      PARTITION BY c.job_id
      ORDER BY CONCAT(SUBSTR(c.dt, 1, 4), '-', SUBSTR(c.dt, 5, 2), '-', SUBSTR(c.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_cost
  FROM <database>.region_costs c
  LEFT JOIN <database>.jobs j ON c.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON c.job_id = b.job_id
)
SELECT job_id, dt, running_cost
FROM region_costs
WHERE running_cost > 1500
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X70

Sources: `jobs` (job_id, job_name, team, region), `job_owners` (job_id, team, owner, dt), `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps:
- `owner_load` (owner, total_mins, runs, avg_mins), loaded by its query and read by `busiest_owner`.
- `staffed`, a connection-only query, kept as a CTE because `owner_load`'s query reads it.
Finals:
- `busiest_owner`: owner, total_mins, runs.
- `owner_load (Total Row)`: one row, one column, runs (a SUM), with no label.
Parameters and Keys: blank, so none.

Typed over: none.
Marks: job 4's blank owner is dropped by the `owner <> null` filter, as M does, so it becomes `owner IS NOT NULL`. busiest_owner's query also carries avg_mins, but the sheet's Table shows three headers. The final gives those three, so check the Table.
Refused: none.
Left alone: the Steps sheet (text).

Final `busiest_owner`:

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_rows AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
),
owner_load AS (
  SELECT owner, total_mins, runs, total_mins / runs AS avg_mins
  FROM owner_rows
)
SELECT owner, total_mins, runs
FROM owner_load
ORDER BY runs DESC
LIMIT 1
```

Final `owner_load (Total Row)`:

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_rows AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
),
owner_load AS (
  SELECT owner, total_mins, runs, total_mins / runs AS avg_mins
  FROM owner_rows
)
SELECT SUM(runs) AS runs
FROM owner_load
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X73

Sources: `region_budgets` (job_id, budget_cents, region), `jobs` (job_id, job_name, team, region).
Steps: `eu_budgets` (job_id, budget_cents, region, job_name, dollars), loaded by its query and read by the eu_count query. It is a CTE in that query.
Finals: `eu_count` (loaded by its query): region, jobs, total_cents.
Parameters and Keys: blank, so none.

Typed over: none. Marks: none. Refused: none.
Left alone: the Steps sheet (text).

Final `eu_count`:

```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region,
    j.job_name AS job_name,
    b.budget_cents / 100 AS dollars
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT region,
  COUNT(*) AS jobs,
  SUM(budget_cents) AS total_cents
FROM eu_budgets
GROUP BY region
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X74

Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), `run_alerts` (alert_id, run_id, severity, dt).
Steps: `run_alerts`, for its status, job_id and alerts_so_far columns, which `by_status` and `late_alerts` read. It is a CTE in each of their queries.
Finals:
- `by_status`, a summary of `run_alerts` (GROUP BY status): status, alerts. No Total Row.
- `late_alerts` (loaded by its query): alert_id, run_id, alerts_so_far.
Parameters and Keys: blank, so none.

Typed over: none.
Marks: the blank status on run 98 in job_runs is read by the status lookup, so it is wrapped as `COALESCE(r.status, '')` (blank). alerts_so_far is a running count, so it uses RANGE with ties.
Refused: none.
Left alone: the Steps sheet (text).

Final `by_status`:

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(r.status, '') AS status,
    r.job_id AS job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT status, COALESCE(COUNT(*), 0) AS alerts
FROM run_alerts
GROUP BY status
```

Final `late_alerts`:

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(r.status, '') AS status,
    r.job_id AS job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM run_alerts
WHERE alerts_so_far > 5
```

Fill in: `<database>`.
Take out what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.
