date: 2026-10-29
arm: C
model: sonnet
files: 6fc91ff

## X40

**Map**
- Sources: Runs (Run, Job, Mins), jobs (job_id, team), run_alerts. Parameters and Keys are none. From Parameters, `rate` is 2, so I used its value.
- Steps: Runs adds Team and Cost, and Teams and run_alerts read it, so it is a step (a CTE) and not a final.
- Finals: Teams (Team, Total Cost), a summary: a GROUP BY of Runs. run_alerts (alert_id, run_id, severity, dt, Run Mins).
- Typed over a formula: none. Refusals: none.
- Left alone: the PivotTable on sheet "Pivot".
- Fill in: `<database>`. The headers with spaces become `<total_cost>` (Total Cost) and `<run_mins>` (Run Mins).

Teams:

```sql
WITH runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT Team, COALESCE(SUM(Cost), 0) AS <total_cost>
FROM runs
GROUP BY Team
```

run_alerts (Run and Mins are typed in Runs, so it reads the table directly):

```sql
SELECT a.alert_id, a.run_id, a.severity, a.dt, r.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN <database>.Runs r ON a.run_id = r.Run
```

Next: take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. I gave the Hive you asked for. Ask if you also want the Toolbox code.

## X46

**Map**
- Sources: job_runs (read for job_id, duration_mins). Parameters and Keys are none.
- Steps: none.
- Finals: jobs (job_id, job_name, team, shortest, runs, busiest). It has typed columns, so it reads its own table, `<database>.jobs`, plus job_runs.
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- MINIFS and COUNTIF give 0 where nothing matches, as Excel does, so job 4, with no runs, gets shortest 0 and runs 0.
- busiest is RANK.EQ, highest runs first.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team,
  COALESCE(r.shortest, 0) AS shortest,
  COALESCE(r.runs, 0) AS runs,
  RANK() OVER (ORDER BY COALESCE(r.runs, 0) DESC) AS busiest
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, MIN(duration_mins) AS shortest, COUNT(*) AS runs
  FROM <database>.job_runs
  GROUP BY job_id
) r ON j.job_id = r.job_id
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X47

**Map**
- Sources: region_budgets. Parameters and Keys are none.
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- cheapest_first is RANK.EQ with 1 as the third argument, so ASC. region_total (SUMIF) is wrapped in COALESCE(.., 0), as Excel gives 0 where nothing matches. region_avg (AVERAGEIF) is left NULL.
- Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X48

**Map**
- Sources: job_runs, jobs, run_alerts. Parameters and Keys are none.
- Steps: none. No query reads another.
- Finals: quiet_runs (run_id, job_id, status). slow_regions (region, avg_mins, fastest).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- quiet_runs is a LeftAnti join, so it is a LEFT JOIN with `WHERE a.run_id IS NULL`, giving job_runs' columns only.
- slow_regions: the inner join expands region, and the filter on the grouped avg_mins becomes HAVING, repeating the aggregate.
- Fill in: `<database>`.

quiet_runs:

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

slow_regions:

```sql
SELECT j.region, AVG(r.duration_mins) AS avg_mins, MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X49

**Map**
- Sources: job_runs, jobs, run_alerts, scheduler_runs, job_owners. Parameters and Keys are none.
- Steps: none.
- Finals: alert_status (alert_id, severity, status). run_check (run_id, status, scheduled_run). teams (team).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- alert_status is a RightOuter join, so it is a LEFT JOIN with the two tables swapped (job_runs first).
- run_check is a FullOuter join. The SelectColumns on job_runs is only the select list. Expanding run_id with the new name scheduled_run is an AS.
- teams is Table.Distinct over a Table.Combine, so UNION.
- Fill in: `<database>`.

alert_status:

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON a.run_id = r.run_id
```

run_check:

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

teams:

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X50

**Map**
- Sources: job_owners, jobs. Parameters and Keys are none.
- Steps: none. The owners query is read only by its own Table's formulas, so it is not a step of another query.
- Finals: owners (job_id, owner, job_name, newest_first). It is the query plus the two formula columns its Table adds.
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Table.Distinct alone is SELECT DISTINCT. The window has to run after it, so I put the distinct rows in a CTE.
- newest_first is RANK.EQ with no third argument, so DESC, over the distinct rows. Job 3 appears twice, once per owner, so both rows rank equal.
- Fill in: `<database>`.

```sql
WITH owners AS (
  SELECT DISTINCT job_id, owner
  FROM <database>.job_owners
)
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM owners o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X59

**Map**
- Sources: job_runs. Parameters and Keys are none.
- Steps: none.
- Finals: jobs (job_id, job_name, long_runs, failed_mins, not_test). run_alerts (alert_id, run_id, severity, dt, alerts_so_far).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - `"f*"` is `LOWER(status) LIKE 'f%'`, as Excel ignores case.
  - `"<>TEST"` is `(status <> 'TEST' OR status IS NULL)`, as Excel counts a blank there.
  - The blank status (run 98) sits inside -IFS forms, which skip a blank, so I did not wrap it.
  - All three jobs columns are wrapped in COALESCE(.., 0), as Excel gives 0 where nothing matches. Job 4 has no runs.
  - alerts_so_far, `"<="&[@run_id]` over its own Table, is a running count with ties included.
- Fill in: `<database>`.

jobs:

```sql
SELECT j.job_id, j.job_name,
  COALESCE(r.long_runs, 0) AS long_runs,
  COALESCE(r.failed_mins, 0) AS failed_mins,
  COALESCE(r.not_test, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id,
    COUNT(CASE WHEN duration_mins >= 20 THEN 1 END) AS long_runs,
    SUM(CASE WHEN LOWER(status) LIKE 'f%' THEN duration_mins END) AS failed_mins,
    COUNT(CASE WHEN (status <> 'TEST' OR status IS NULL) THEN 1 END) AS not_test
  FROM <database>.job_runs
  GROUP BY job_id
) r ON j.job_id = r.job_id
```

run_alerts:

```sql
SELECT alert_id, run_id, severity, dt,
  COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X60

**Map**
- Sources: region_budgets. Parameters and Keys are none.
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region). `region_budgets (Total Row)` (job_id, budget_cents).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- The Total Row is a query of its own: one row, a column per total, in order, with no label. SUBTOTAL(103) is a COUNT and 101 is an AVG. The "Total" label is left out.
- rank_in_region, COUNTIFS(.., "<"&[@budget_cents])+1, is RANK ASC within the region.
- Fill in: `<database>`.

region_budgets:

```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

region_budgets (Total Row):

```sql
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X61

**Map**
- Sources: region_costs (read for region, cost_cents). Parameters and Keys are none.
- Steps: none.
- Finals: by_region (region, total_cents, entries, priciest). It is a summary: its only typed column, region, is what its SUMIFS, COUNTIFS and MAXIFS match on, so it is a GROUP BY of region_costs.
- Total Row: its totals only add up SUMs and COUNTs and take the MAX of MAXes. It needs no query of its own, so the query ends `GROUP BY region WITH ROLLUP`, which adds the total as one more row with region NULL (a Subtotal row). The "Total" label is left out.
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - blank: the sample has a blank cost_cents (job 2, 20260924). SUMIFS and MAXIFS skip it, as SUM and MAX skip NULL, so I did not wrap it. COUNTIFS still counts that row.
  - SUMIFS, COUNTIFS and MAXIFS are wrapped in COALESCE(.., 0).
  - dt is held as text (20260911), but no formula here reads it, so I did not convert it.
- Fill in: `<database>`.

```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(*), 0) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X62

**Map**
- Sources: team_notes (team, note, written_on). Parameters and Keys are none.
- Steps: none.
- Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - week_of is the Monday of the week, as week_start writes it. month_of is the first of the month, as month_start writes it. Both are text.
  - DATEDIF "m" is `FLOOR(MONTHS_BETWEEN(written_on, '2026-01-01'))`.
  - TEXTJOIN with TRUE is CONCAT_WS, which skips NULL.
  - The sample has no blanks in the columns the formulas read.
- Fill in: `<database>`.

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

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X63

**Map**
- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs), scheduler_runs. Parameters and Keys are none.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - blank: the sample has a blank status (run 98), and `succeeded` reads it outside an -IF(S) form. SEARCH on a blank gives FALSE in Excel, so I wrapped it as COALESCE(status, '').
  - avg_retry_secs is blank in run 98, but ISBLANK is exactly `IS NULL`, so no wrap.
  - XLOOKUP's fourth argument, -1, is COALESCE(.., -1). Run 99 has no scheduler row and gets -1.
  - variance (VAR.S) and weighted (SUMPRODUCT) are whole-column windows over all rows.
- Fill in: `<database>`.

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

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X64

**Map**
- Sources: jobs, region_costs. Parameters and Keys are none.
- Steps: none. No query reads another.
- Finals: picked_costs (job_id, cost_cents, region, size). costed_jobs (job_id, job_name, team, region). costs_filled (job_id, cost_cents, dt, day).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - M's `[cost_cents] <> null` is `IS NOT NULL`.
  - costed_jobs: `List.Contains(Costs[job_id], [job_id])` is a LEFT SEMI JOIN. The `not Text.StartsWith` is a NOT LIKE, and case is kept, as M keeps it.
  - costs_filled: the null cost (job 2, 20260924) becomes 0 by the query's own ReplaceValue.
  - dt is held as text (20260911). Text.End reads it as text, so it stays text and I did not convert it to a date.
  - No query sorts, so no order is lost.
- Fill in: `<database>`.

picked_costs:

```sql
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

costed_jobs:

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

costs_filled:

```sql
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt, SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X65

**Map**
- Sources: jobs, region_budgets, job_owners, scheduler_runs, job_runs. Parameters and Keys are none.
- Steps: none read across queries. team_regions has two CTEs of its own, which are steps inside that query.
- Finals: team_regions (team, region). budget_places (job_id, budget_cents, region, place). jobs_per_team (team, jobs). ran_as_scheduled (run_id, dt). run_measures (run_id, job_id, measure, amount).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - The order was dropped. team_regions sorts by team with no FirstN or index after it, so there is no ORDER BY, as a Hive table holds no order. The same goes for the order of run_measures' rows.
  - budget_places sorts and then adds an index, so place is `ROW_NUMBER() OVER (ORDER BY budget_cents DESC)`, with no outer ORDER BY.
  - jobs_per_team: COUNT(DISTINCT job_id) leaves out NULL where M counts it as a value. job_id has no blank in the sample, so nothing changes here.
  - ran_as_scheduled: the NestedJoin on every column, in Table.Distinct, is INTERSECT.
  - run_measures: the unpivot is one SELECT per column, stacked with UNION ALL, each with `IS NOT NULL`, as M drops a null there. Run 98's blank avg_retry_secs is dropped.
- Fill in: `<database>`.

team_regions:

```sql
WITH teams AS (
  SELECT DISTINCT team FROM <database>.jobs
),
regions AS (
  SELECT DISTINCT region FROM <database>.jobs
)
SELECT t.team, r.region
FROM teams t
CROSS JOIN regions r
```

budget_places:

```sql
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

jobs_per_team:

```sql
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

ran_as_scheduled:

```sql
SELECT run_id, dt FROM <database>.scheduler_runs
INTERSECT
SELECT run_id, dt FROM <database>.job_runs
```

run_measures:

```sql
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X66

**Map**
- Sources: job_runs. Parameters and Keys are none.
- Steps: none.
- Finals: ok_runs (run_id, job_id, duration_mins, dt, running, share), the query plus its two formula columns. `ok_runs (Total Row)` (duration_mins).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - The window formulas run over the rows the filter keeps, which are the Table's rows.
  - running is a running total with ties included, as Excel's. It is wrapped in COALESCE(.., 0).
  - The Total Row is a query of its own: one row, one column, no label. The "Total" label is left out.
  - The status blank is in the query's M filter, where `status IS NOT NULL` handles it.
- Fill in: `<database>`.

ok_runs:

```sql
SELECT run_id, job_id, duration_mins, dt,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

ok_runs (Total Row):

```sql
SELECT SUM(duration_mins) AS duration_mins
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X69

**Map**
- Sources: jobs, region_budgets, region_costs (the typed columns job_id, cost_cents, region, dt). Parameters and Keys are none.
- Steps: region_costs with its formula columns (job_name, budget, over_budget, running_cost). job_totals and late_costs read it, so it is a CTE, `costs`, in each of their queries. It is not a final.
- Finals: job_totals (job_id, total_cents, over_count), a summary: its only typed column, job_id, is what its SUMIFS and COUNTIFS match on, so it is a GROUP BY of costs. late_costs (job_id, dt, running_cost).
- Total Row of job_totals: it only adds up a SUM and a COUNT, so it needs no query of its own. The query ends `GROUP BY job_id WITH ROLLUP`, which adds the total as one more row with job_id NULL (a Subtotal row). The "Total" label is left out.
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - blank: the sample has a blank cost_cents (job 2, 20260924). over_budget reads it, so I wrapped it as COALESCE(cost_cents, 0). The SUMIFS skips it, as SUM skips NULL, so I did not wrap that.
  - dt is held as text (20260911). I compare it as a date, so the window orders by `CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2))`. The dt column itself passes through unchanged.
  - running_cost is a running total per job, ties included.
  - The XLOOKUPs are LEFT JOINs on job_id.
  - COUNTIFS on over_budget TRUE counts only the rows where the Condition is true.
- Fill in: `<database>`.

job_totals:

```sql
WITH costs AS (
  SELECT c.job_id, c.cost_cents, c.region, c.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(c.cost_cents) OVER (PARTITION BY c.job_id
      ORDER BY CONCAT(SUBSTR(c.dt, 1, 4), '-', SUBSTR(c.dt, 5, 2), '-', SUBSTR(c.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs c
  LEFT JOIN <database>.jobs j ON c.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON c.job_id = b.job_id
)
SELECT job_id,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(CASE WHEN over_budget = TRUE THEN 1 END), 0) AS over_count
FROM costs
GROUP BY job_id WITH ROLLUP
```

late_costs:

```sql
WITH costs AS (
  SELECT c.job_id, c.cost_cents, c.region, c.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(c.cost_cents) OVER (PARTITION BY c.job_id
      ORDER BY CONCAT(SUBSTR(c.dt, 1, 4), '-', SUBSTR(c.dt, 5, 2), '-', SUBSTR(c.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs c
  LEFT JOIN <database>.jobs j ON c.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON c.job_id = b.job_id
)
SELECT job_id, dt, running_cost
FROM costs
WHERE running_cost > 1500
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X70

**Map**
- Sources: jobs, job_owners, job_runs. Parameters and Keys are none.
- Steps:
  - staffed, a connection-only query that owner_load reads, so it is a CTE.
  - The owner_load query, which busiest_owner reads, so it is a CTE. The query and the Table it loads are read apart.
- Finals:
  - owner_load, the Table, which nothing reads: (owner, total_mins, runs, avg_mins).
  - `owner_load (Total Row)`: (runs).
  - busiest_owner (owner, total_mins, runs).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - staffed's `[owner] <> null` is `IS NOT NULL`, so job 4, with no owner, drops out.
  - The LeftOuter join is a LEFT JOIN, and Table.RowCount is COUNT(*), as M counts a row with no match as one.
  - busiest_owner is ORDER BY with LIMIT 1, so the ORDER BY stays.
  - The Total Row is a query of its own: one row, a column per total, no label. The "Total" label is left out.
- Fill in: `<database>`.

owner_load:

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs, total_mins / runs AS avg_mins
FROM owner_load
```

owner_load (Total Row):

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT SUM(runs) AS runs
FROM owner_load
```

busiest_owner:

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs
FROM owner_load
ORDER BY runs DESC
LIMIT 1
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X73

**Map**
- Sources: region_budgets, jobs. Parameters and Keys are none.
- Steps: the eu_budgets query, which eu_count reads, so it is a CTE in eu_count's query.
- Finals:
  - eu_budgets, the Table plus its formula column dollars, which nothing reads: (job_id, budget_cents, region, job_name, dollars).
  - eu_count (region, jobs, total_cents).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - The Inner join on job_id is a plain JOIN.
  - The filter `[region] = "eu"` keeps its case, as M does.
  - Table.RowCount is COUNT(*) and List.Sum is SUM.
- Fill in: `<database>`.

eu_budgets:

```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT job_id, budget_cents, region, job_name, budget_cents / 100 AS dollars
FROM eu_budgets
```

eu_count:

```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT region, COUNT(*) AS jobs, SUM(budget_cents) AS total_cents
FROM eu_budgets
GROUP BY region
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X74

**Map**
- Sources: job_runs, and run_alerts' typed columns (alert_id, run_id, severity, dt). Parameters and Keys are none.
- Steps: run_alerts with its formula columns (status, job_id, alerts_so_far). by_status and late_alerts read it, so it is a CTE, `alerts`, in each of their queries. It is not a final.
- Finals:
  - by_status (status, alerts), a summary: its only typed column, status, is what its COUNTIFS matches on, so it is a GROUP BY of alerts.
  - late_alerts (alert_id, run_id, alerts_so_far).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - The XLOOKUPs are LEFT JOINs on run_id.
  - alerts_so_far is a running count, ties included.
  - COUNTIFS is COALESCE(COUNT(*), 0).
  - by_status groups on whatever statuses the alerts have. In the sample these are exactly FAILED and SUCCESS.
- Fill in: `<database>`.

by_status:

```sql
WITH alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    r.status, r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT status, COALESCE(COUNT(*), 0) AS alerts
FROM alerts
GROUP BY status
```

late_alerts:

```sql
WITH alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    r.status, r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM alerts
WHERE alerts_so_far > 5
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.
