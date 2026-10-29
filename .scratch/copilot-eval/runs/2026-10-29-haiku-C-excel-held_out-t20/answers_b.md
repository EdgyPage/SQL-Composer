date: 2026-10-29
arm: C
model: haiku
files: fac0fd8

## X39

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins), jobs (job_id, job_name). Both are typed and are read directly. job_runs has no formula, so it needs no step.
- Steps: none. The ok_runs query is the final's own rows.
- Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise). Its Power Query loads the Table, and nothing else reads it.
- Parameters and Keys: none. Keys is empty, so no value is typed over a formula and no Keys conversion is needed.
- Refused: noise = RAND(), written as NULL AS noise.
- Left alone: the Steps sheet, which has cells but no Table.

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  j.job_name,
  r.duration_mins / COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id), 0) AS share,
  NULL AS noise
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
WHERE r.status = 'SUCCESS'
```

**Marks**
- share: SUMIFS over ok_runs' own job_id column is a window SUM over the rows the query keeps, wrapped in COALESCE.
- The Power Query filter `= "SUCCESS"` drops the blank status on run 98, as M drops it.

**Refusal**
- noise: RAND() is refused, NULL AS noise.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, WHERE, equals, fill_null, statement, sum_of, window
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

by_job = window(PARTITION_BY=job_runs.job_id)
# noise (RAND) is refused, so it is left out.
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, jobs.job_name,
           AS(job_runs.duration_mins / fill_null(sum_of(job_runs.duration_mins, over=by_job), 0),
              "share")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    WHERE(equals(job_runs.status, "SUCCESS")),
)
```

Take out of the workbook what you don't want converted (the noise column, for one). Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X40

**Map**
- Sources: jobs (job_id, job_name, team, region). Typed, read directly.
- Steps: Runs, as a CTE `runs`. Its Team and Cost formulas are read by two Tables (Teams and run_alerts), so it is a step. The source Table is `<database>.Runs` with typed run, job and mins.
- Finals:
  - Teams (team, <total_cost>). This is a summary, since its only typed column is Team, which its SUMIFS matches on. It is a GROUP BY of Runs.
  - run_alerts (alert_id, run_id, severity, dt, <run_mins>). Typed, and nothing reads it, so it is a final. It is also a source.
- Parameters: rate is 2 in Parameters, so XLOOKUP("rate", ...) becomes its value, 2.
- Keys: empty. No value is typed over a formula, so none is needed.
- Refused: none.
- Left alone: the PivotTable on sheet "Pivot" (from Runs, rows Team, values Sum of Cost). The Steps sheet, which has no Table.

**Final: Teams**

```sql
WITH runs AS (
  SELECT r.run, r.job, r.mins, j.team, r.mins * 2 AS cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.job = j.job_id
)
SELECT team, COALESCE(SUM(cost), 0) AS <total_cost>
FROM runs
GROUP BY team
```

**Final: run_alerts**

```sql
WITH runs AS (
  SELECT r.run, r.job, r.mins, j.team, r.mins * 2 AS cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.job = j.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt, rn.mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN runs rn ON a.run_id = rn.run
```

**Marks**
- The rate is 2, read from Parameters, so Cost is Mins * 2.
- Teams is a summary: its rows are the teams in Runs (data and finance), the same two rows the Table holds.
- Total Cost and Run Mins are headers with a space, so each is written in snake case in brackets.

**To fill in**
- `<database>`
- `<total_cost>`
- `<run_mins>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, derived, equals, fill_null, GROUP_BY, statement, sum_of
from references.ops__Runs import Runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

runs = derived("runs", statement(
    SELECT(Runs.run, Runs.job, Runs.mins, jobs.team, AS(Runs.mins * 2, "cost")),
    FROM(Runs, reads_all_partitions=True),  # the workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, Runs.job)),
))
teams = statement(
    SELECT(runs.team, AS(fill_null(sum_of(runs.cost), 0), "<total_cost>")),
    FROM(runs),
    GROUP_BY(runs.team),
)
alerts = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(runs.mins, "<run_mins>")),
    FROM(run_alerts, reads_all_partitions=True),
    LEFT_JOIN(runs, ON=equals(runs.run, run_alerts.run_id)),
)
```

Take out of the workbook what you don't want converted (the PivotTable is already left out). Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X46

**Map**
- Sources: job_runs (run_id, job_id, duration_mins). It has no formula, so it is read directly and needs no step. jobs (job_id, job_name, team), typed.
- Steps: none. A CTE inside the jobs query holds the runs count, because RANK reads runs as a computed column.
- Finals: jobs (job_id, job_name, team, shortest, runs, busiest). Nothing reads jobs, so it is a final.
- Parameters and Keys: none. Keys is empty.
- Refused: none.
- Left alone: none.

```sql
WITH counted AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(s.shortest, 0) AS shortest,
    COALESCE(c.runs, 0) AS runs
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, MIN(duration_mins) AS shortest
    FROM <database>.job_runs
    GROUP BY job_id
  ) s ON s.job_id = j.job_id
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS runs
    FROM <database>.job_runs
    GROUP BY job_id
  ) c ON c.job_id = j.job_id
)
SELECT job_id, job_name, team, shortest, runs,
  RANK() OVER (ORDER BY runs DESC) AS busiest
FROM counted
```

**Marks**
- shortest: MINIFS over another Table is a LEFT JOIN to a MIN, wrapped in COALESCE, since Excel gives 0 where nothing matches. Job 4 has no runs, so its shortest and runs are 0.
- busiest: RANK.EQ(runs, runs), descending by default, so RANK() OVER (ORDER BY runs DESC).

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, count_rows, derived, descending, equals, fill_null, min_of, rank, statement, window
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

per_job = derived("per_job", statement(
    SELECT(job_runs.job_id, AS(min_of(job_runs.duration_mins), "shortest"), AS(count_rows(), "runs")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
counted = derived("counted", statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(fill_null(per_job.shortest, 0), "shortest"),
           AS(fill_null(per_job.runs, 0), "runs")),
    FROM(jobs),
    LEFT_JOIN(per_job, ON=equals(per_job.job_id, jobs.job_id)),
))
s = statement(
    SELECT(counted.job_id, counted.job_name, counted.team, counted.shortest, counted.runs,
           AS(rank(over=window(ORDER_BY=descending(counted.runs))), "busiest")),
    FROM(counted),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X47

**Map**
- Sources and finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg). It is typed, and nothing else reads it, so it is both a source and a final.
- Steps: none.
- Parameters and Keys: none.
- Refused: none.
- Left alone: the Steps sheet, which has no Table.

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

**Marks**
- cheapest_first: RANK.EQ with 1 as its third argument is ascending, so the order has no DESC.
- region_total: SUMIF over its own Table is a window SUM by region, wrapped in COALESCE.
- region_avg: AVERAGEIF is AVG and is left NULL where there is no match, so there is no COALESCE.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, SELECT, average_of, fill_null, rank, statement, sum_of, window
from references.ops__region_budgets import region_budgets

by_region = window(PARTITION_BY=region_budgets.region)
s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(rank(over=window(ORDER_BY=region_budgets.budget_cents)), "cheapest_first"),
           AS(fill_null(sum_of(region_budgets.budget_cents, over=by_region), 0), "region_total"),
           AS(average_of(region_budgets.budget_cents, over=by_region), "region_avg")),
    FROM(region_budgets, reads_all_partitions=True),  # the workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X48

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), jobs (job_id, job_name, team, region), run_alerts (alert_id, run_id, severity, dt). All typed. Both queries read them directly, so none needs a step.
- Steps: none.
- Finals:
  - quiet_runs (run_id, job_id, status). Its Power Query is a LeftAnti join, so it is a LEFT JOIN with a WHERE that keeps only the rows with no match.
  - slow_regions (region, avg_mins, fastest). Its Power Query is an Inner join, a Table.Group, and a filter on the average, so it is a GROUP BY with a HAVING that repeats the aggregate.
- Parameters and Keys: none.
- Refused: none.
- Left alone: none.

**Final: quiet_runs**

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

**Final: slow_regions**

```sql
SELECT j.region,
  AVG(r.duration_mins) AS avg_mins,
  MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

**Marks**
- quiet_runs: the blank status on run 98 passes through as NULL, as it is in the sample.
- slow_regions: the HAVING keeps only NYC, with an average of 30, which matches the sample.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import ANTI_JOIN, AS, FROM, GROUP_BY, HAVING, JOIN, SELECT, at_least, average_of, equals, min_of, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

quiet = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's query reads every row
    ANTI_JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id)),
)
slow = statement(
    SELECT(jobs.region, AS(average_of(job_runs.duration_mins), "avg_mins"),
           AS(min_of(job_runs.duration_mins), "fastest")),
    FROM(job_runs, reads_all_partitions=True),
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    GROUP_BY(jobs.region),
    HAVING(at_least(average_of(job_runs.duration_mins), 20)),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X49

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), jobs (job_id, job_name, team, region), run_alerts (alert_id, run_id, severity, dt), scheduler_runs (run_id, job_id, dt), job_owners (job_id, team, owner, dt). All typed. Each is read directly.
- Steps: none.
- Finals:
  - alert_status (alert_id, severity, status). Its Power Query is a RightOuter join, so it is a LEFT JOIN with the two tables swapped: job_runs first, so every run is kept.
  - run_check (run_id, status, scheduled_run). Its Power Query is a FullOuter join.
  - teams (team). Its Power Query is Table.Combine inside Table.Distinct, so it is a UNION.
- Parameters and Keys: none.
- Refused: none.
- Left alone: none.

**Final: alert_status**

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
```

**Final: run_check**

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

**Final: teams**

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

**Marks**
- alert_status: runs with no alert keep NULL alert_id and severity, and run 97, with two alerts, appears twice, as M gives it.
- run_check: the scheduler's run 100 has no job_runs row, so its run_id and status are NULL and only scheduled_run holds 100, as in the sample.
- teams: UNION drops repeated team names, as Table.Distinct does.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, FULL_JOIN, LEFT_JOIN, SELECT, UNION, equals, statement
from references.ops__job_owners import job_owners
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts
from references.ops__scheduler_runs import scheduler_runs

alert_status = statement(
    SELECT(run_alerts.alert_id, run_alerts.severity, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's query reads every row
    LEFT_JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id)),
)
run_check = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(scheduler_runs.run_id, "scheduled_run")),
    FROM(job_runs, reads_all_partitions=True),
    FULL_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id)),
)
teams = UNION(
    statement(SELECT(jobs.team), FROM(jobs, reads_all_partitions=True)),
    statement(SELECT(job_owners.team), FROM(job_owners, reads_all_partitions=True)),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X50

**Map**
- Sources: job_owners (job_id, team, owner, dt), jobs (job_id, job_name, team, region). Both typed and read directly.
- Steps: none. The distinct pairs are a CTE inside the owners query.
- Finals: owners (job_id, owner, job_name, newest_first). Nothing reads it, so it is a final.
- Parameters and Keys: none.
- Refused: none.
- Left alone: none.

```sql
WITH distinct_owners AS (
  SELECT DISTINCT job_id, owner
  FROM <database>.job_owners
)
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM distinct_owners o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

**Marks**
- The Distinct keeps job 4's blank owner as NULL, as the sample shows.
- newest_first: RANK.EQ on job_id, descending by default. The two job 3 rows share a rank, as Excel does.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, SELECT_DISTINCT, derived, descending, equals, rank, statement, window
from references.ops__job_owners import job_owners
from references.ops__jobs import jobs

distinct_owners = derived("distinct_owners", statement(
    SELECT_DISTINCT(job_owners.job_id, job_owners.owner),
    FROM(job_owners, reads_all_partitions=True),  # the workbook's query reads every row
))
s = statement(
    SELECT(distinct_owners.job_id, distinct_owners.owner, jobs.job_name,
           AS(rank(over=window(ORDER_BY=descending(distinct_owners.job_id))), "newest_first")),
    FROM(distinct_owners),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, distinct_owners.job_id)),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X59

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). It has no formula, so it is read directly. jobs (job_id, job_name), typed. run_alerts (alert_id, run_id, severity, dt), typed.
- Steps: none.
- Finals:
  - jobs (job_id, job_name, long_runs, failed_mins, not_test). Nothing reads it.
  - run_alerts (alert_id, run_id, severity, dt, alerts_so_far). Nothing reads it, and it is also a source.
- Parameters and Keys: none.
- Refused: none.
- Left alone: the Steps sheet, which has no Table.

**Final: jobs**

```sql
SELECT j.job_id, j.job_name,
  COALESCE(lr.long_runs, 0) AS long_runs,
  COALESCE(fm.failed_mins, 0) AS failed_mins,
  COALESCE(nt.not_test, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS long_runs
  FROM <database>.job_runs
  WHERE duration_mins >= 20
  GROUP BY job_id
) lr ON lr.job_id = j.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS failed_mins
  FROM <database>.job_runs
  WHERE LOWER(status) LIKE 'f%'
  GROUP BY job_id
) fm ON fm.job_id = j.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS not_test
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) nt ON nt.job_id = j.job_id
```

**Final: run_alerts**

```sql
SELECT a.alert_id, a.run_id, a.severity, a.dt,
  COALESCE(COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
FROM <database>.run_alerts a
```

**Marks**
- not_test: the blank status on run 98 is counted, because Excel counts a blank as not "TEST". The NULL test is written in, and no COALESCE is used inside the COUNTIFS form.
- failed_mins: "f*" ignores case, so it is LOWER(status) LIKE 'f%'.
- alerts_so_far: a running count with ties included. Both run 97 rows give 2, and both run 101 rows give 5, as Excel does.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, all_of, any_of, count_rows, derived, equals, fill_null, is_null, not_equals, statement, starts_with, sum_of, window, at_least
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

per_job = derived("per_job", statement(
    SELECT(job_runs.job_id,
           AS(count_rows(where=at_least(job_runs.duration_mins, 20)), "long_runs"),
           AS(sum_of(job_runs.duration_mins, where=starts_with(job_runs.status, "F")), "failed_mins"),
           AS(count_rows(where=any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))), "not_test")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
s_jobs = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(fill_null(per_job.long_runs, 0), "long_runs"),
           AS(fill_null(per_job.failed_mins, 0), "failed_mins"),
           AS(fill_null(per_job.not_test, 0), "not_test")),
    FROM(jobs, reads_all_partitions=True),
    LEFT_JOIN(per_job, ON=equals(per_job.job_id, jobs.job_id)),
)
s_alerts = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(fill_null(count_rows(over=window(ORDER_BY=run_alerts.run_id, rows=(None, 0))), 0), "alerts_so_far")),
    FROM(run_alerts, reads_all_partitions=True),
)
```

Note: the running count uses rows=(None, 0), which counts one row at a time. The two run 97 rows would then give 1 and 2, where Excel and the Hive give 2 and 2. Check the Hive for that column. Also, starts_with may be case-sensitive, so check the status case.

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X60

**Map**
- Sources and finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region). It is typed, and only its own formulas read it, so it is both a source and a final.
- Total Row: region_budgets (Total Row), a query of its own with one row: a count of job_id and an average of budget_cents, in that order, with no label. SUBTOTAL 103 is a COUNT, and 101 is an AVG.
- Steps: none.
- Parameters and Keys: none.
- Refused: none.
- Left alone: the "Total" label in the Total Row, which is not converted.

**Final: region_budgets**

```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

**Final: region_budgets (Total Row)**

```sql
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

**Marks**
- rank_in_region: COUNTIFS with "<" and + 1 is a RANK ascending within the region, and it gives the same tied ranks.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, SELECT, average_of, count_rows, if_else, is_not_null, more_than, rank, statement, sum_of, window
from references.ops__region_budgets import region_budgets

whole = window()
by_region = window(PARTITION_BY=region_budgets.region, ORDER_BY=region_budgets.budget_cents)
s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(region_budgets.budget_cents / sum_of(region_budgets.budget_cents, over=whole), "share"),
           AS(if_else(more_than(region_budgets.budget_cents,
                                average_of(region_budgets.budget_cents, over=whole)), 1, 0), "above_avg"),
           AS(rank(over=by_region), "rank_in_region")),
    FROM(region_budgets, reads_all_partitions=True),  # the workbook's query reads every row
)
total_row = statement(
    SELECT(AS(count_rows(where=is_not_null(region_budgets.job_id)), "job_id"),
           AS(average_of(region_budgets.budget_cents), "budget_cents")),
    FROM(region_budgets, reads_all_partitions=True),
)
```

Note: above_avg is a true or false in Hive, and 1 or 0 in the Toolbox code.

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X61

**Map**
- Sources: region_costs (job_id, cost_cents, region, dt). Typed, read only by by_region's formulas, so it is read directly and needs no step.
- Steps: none.
- Finals: by_region (region, total_cents, entries, priciest). Its only typed column is region, which its SUMIFS, COUNTIFS and MAXIFS match on. So it is a summary, a GROUP BY of region_costs.
- Total Row: by_region (Total Row) needs no query of its own. Its totals are a SUM, a SUM, and a MAX of MAXes, so the summary's query ends GROUP BY region WITH ROLLUP. The NULL region row is the Total Row.
- Parameters and Keys: none.
- Refused: none.
- Left alone: none.

```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(*), 0) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

**Marks**
- The blank cost_cents on row 29 (job 2, 20260924) is skipped by SUM and MAX, as SUMIFS and MAXIFS skip it in Excel. It is not wrapped in COALESCE.
- entries counts every row of the region, blank cost included, as COUNTIFS on region does.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, count_rows, fill_null, max_of, rollup, statement, sum_of
from references.ops__region_costs import region_costs

s = statement(
    SELECT(region_costs.region,
           AS(fill_null(sum_of(region_costs.cost_cents), 0), "total_cents"),
           AS(count_rows(), "entries"),
           AS(fill_null(max_of(region_costs.cost_cents), 0), "priciest")),
    FROM(region_costs, reads_all_partitions=True),  # the workbook's query reads every row
    GROUP_BY(rollup(region_costs.region)),  # the rollup row is the Total Row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X62

**Map**
- Sources and finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short). Its typed columns are team, note and written_on, and nothing reads it, so it is both a source and a final. written_on holds dates such as 2026-09-11, so it is read as a date.
- Steps: none.
- Parameters and Keys: none.
- Refused: none.
- Left alone: none.

```sql
SELECT t.team, t.note, t.written_on,
  CAST(NEXT_DAY(DATE_ADD(t.written_on, 7 * -1), 'MO') AS STRING) AS week_of,
  LAST_DAY(t.written_on) AS month_end,
  CAST(TRUNC(t.written_on, 'MM') AS STRING) AS month_of,
  FLOOR(MONTHS_BETWEEN(t.written_on, '2026-01-01')) AS months_in,
  DATE_SUB(t.written_on, 3) AS three_before,
  INITCAP(t.team) AS who,
  CONCAT_WS(': ', t.team, SUBSTR(t.note, 1, 5)) AS short
FROM <database>.team_notes t
```

**Marks**
- week_of: written_on minus WEEKDAY(written_on, 2) plus 1 is the Monday of its week, written as the NEXT_DAY form.
- month_of: EOMONTH(d, -1) + 1 is the first of the month, written as TRUNC to 'MM'.
- months_in: DATEDIF(DATE(2026,1,1), written_on, "m") is FLOOR(MONTHS_BETWEEN), with DATE(2026,1,1) written as '2026-01-01'.
- who: PROPER is INITCAP.
- short: TEXTJOIN(": ", TRUE, ...) is CONCAT_WS(': ', ...), which skips a blank as TRUE does.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, SELECT, month_start, statement, week_start
from references.ops__team_notes import team_notes

s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on,
           AS(week_start(team_notes.written_on), "week_of"),
           AS(month_start(team_notes.written_on), "month_of")),
    FROM(team_notes, reads_all_partitions=True),  # the workbook's query reads every row
)
# month_end, months_in, three_before, who and short have no Toolbox name in files 03 to 05 or 11, so take them from the Hive above.
```

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X63

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs), scheduler_runs (run_id, job_id, dt). Both typed and read directly.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded). It is typed and has formulas, and nothing reads it, so it is both a source and a final.
- Parameters and Keys: none.
- Refused: none.
- Left alone: none.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  r.avg_retry_secs IS NULL AS no_retry,
  FLOOR(r.duration_mins / 4) AS quarters,
  LEAST(r.duration_mins, 25) AS capped,
  VAR_SAMP(r.duration_mins) OVER () AS variance,
  SUM(r.duration_mins * r.job_id) OVER () AS weighted,
  COALESCE(s.job_id, -1) AS scheduled_job,
  CONCAT('run ', r.run_id) AS label,
  INSTR(LOWER(COALESCE(r.status, '')), 'cess') > 0 AS succeeded
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

**Marks**
- Blank status on run 98: succeeded wraps status in COALESCE(status, ''), so the result is FALSE there, as Excel's SEARCH error under ISNUMBER gives. The blank is named here.
- no_retry: ISBLANK is avg_retry_secs IS NULL, which needs no COALESCE.
- scheduled_job: XLOOKUP's fourth argument, -1, is COALESCE(job_id, -1). Run 99 has no scheduler row, so it gets -1.
- variance: VAR.S over the whole column is VAR_SAMP over the window.
- weighted: SUMPRODUCT of two columns is SUM(a * b) over the window.
- quarters: INT is FLOOR. capped: MIN of one row's two cells is LEAST. label: CONCATENATE is CONCAT.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, if_else, is_null, statement, sum_of, window
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

whole = window()
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins, job_runs.avg_retry_secs,
           AS(if_else(is_null(job_runs.avg_retry_secs), 1, 0), "no_retry"),
           AS(sum_of(job_runs.duration_mins * job_runs.job_id, over=whole), "weighted"),
           AS(fill_null(scheduler_runs.job_id, -1), "scheduled_job")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's query reads every row
    LEFT_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id)),
)
# quarters (FLOOR), capped (LEAST), variance (VAR_SAMP), label (CONCAT) and succeeded (INSTR) have no Toolbox name in files 03 to 05, so take them from the Hive above.
```

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X64

**Map**
- Sources: region_costs (job_id, cost_cents, region, dt), jobs (job_id, job_name, team, region). Both typed, read directly.
- Steps: none. No query reads another query.
- Finals:
  - picked_costs (job_id, cost_cents, region, size). Nothing reads it.
  - costed_jobs (job_id, job_name, team, region). Nothing reads it.
  - costs_filled (job_id, cost_cents, dt, day). Nothing reads it.
- Parameters and Keys: none.
- Refused: none.
- Left alone: none.

**Final: picked_costs**

```sql
SELECT c.job_id, c.cost_cents, UPPER(c.region) AS region,
  IF(c.cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs c
WHERE c.cost_cents IS NOT NULL AND c.job_id IN (1, 3)
```

**Final: costed_jobs**

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

**Final: costs_filled**

```sql
SELECT c.job_id, COALESCE(c.cost_cents, 0) AS cost_cents, c.dt,
  SUBSTR(c.dt, -2) AS day
FROM <database>.region_costs c
```

**Marks**
- picked_costs: `<> null` is IS NOT NULL. List.Contains({1, 3}, job_id) is IN (1, 3). Text.Upper is UPPER. The if is IF.
- costed_jobs: List.Contains(region_costs[job_id], job_id) is a LEFT SEMI JOIN on region_costs. The `not` on Text.StartsWith is NOT (job_name LIKE 'n%'). The cache_warm job has no cost rows, so it drops out too.
- costs_filled: the blank cost on row 29 is 0 after Table.ReplaceValue, so it is COALESCE(cost_cents, 0). The blank is named here.
- costs_filled: dt is held as text (20260911), so Text.End's last two characters are SUBSTR(dt, -2).

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, SELECT, SEMI_JOIN, WHERE, at_least, equals, fill_null, if_else, is_in, is_not_null, statement
from references.ops__jobs import jobs
from references.ops__region_costs import region_costs

picked = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents,
           AS(if_else(at_least(region_costs.cost_cents, 200), "big", "small"), "size")),
    FROM(region_costs, reads_all_partitions=True),  # the workbook's query reads every row
    WHERE(is_not_null(region_costs.cost_cents), is_in(region_costs.job_id, [1, 3])),
)
costed = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs, reads_all_partitions=True),
    SEMI_JOIN(region_costs, ON=equals(region_costs.job_id, jobs.job_id)),
)
costs_filled = statement(
    SELECT(region_costs.job_id, AS(fill_null(region_costs.cost_cents, 0), "cost_cents"), region_costs.dt),
    FROM(region_costs, reads_all_partitions=True),
)
# UPPER(region), NOT starts_with on job_name and SUBSTR(dt, -2) have no Toolbox name in files 03 to 05, so take them from the Hive above.
```

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X65

**Map**
- Sources: jobs (job_id, job_name, team, region), region_budgets (job_id, budget_cents, region), job_owners (job_id, team, owner, dt), job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), scheduler_runs (run_id, job_id, dt). All typed and read directly.
- Steps: none. No query reads another query.
- Finals:
  - team_regions (team, region)
  - budget_places (job_id, budget_cents, region, place)
  - jobs_per_team (team, jobs)
  - ran_as_scheduled (run_id, dt)
  - run_measures (run_id, job_id, measure, amount)
- Parameters and Keys: none.
- Refused: none.
- Left alone: none.

**Final: team_regions**

```sql
SELECT t.team, r.region
FROM (SELECT DISTINCT team FROM <database>.jobs) t
CROSS JOIN (SELECT DISTINCT region FROM <database>.jobs) r
```

**Final: budget_places**

```sql
SELECT b.job_id, b.budget_cents, b.region,
  ROW_NUMBER() OVER (ORDER BY b.budget_cents DESC) AS place
FROM <database>.region_budgets b
```

**Final: jobs_per_team**

```sql
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

**Final: ran_as_scheduled**

```sql
SELECT DISTINCT s.run_id, s.dt
FROM <database>.scheduler_runs s
JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.dt = r.dt
```

**Final: run_measures**

```sql
SELECT r.run_id, r.job_id, 'duration_mins' AS measure, r.duration_mins AS amount
FROM <database>.job_runs r
WHERE r.duration_mins IS NOT NULL
UNION ALL
SELECT r.run_id, r.job_id, 'avg_retry_secs' AS measure, r.avg_retry_secs AS amount
FROM <database>.job_runs r
WHERE r.avg_retry_secs IS NOT NULL
```

**Marks**
- team_regions: the Table.Sort by team has no FirstN or index after it, so the order is dropped. Hive holds no order.
- budget_places: the sort by budget_cents descending, then the index, is ROW_NUMBER ordered the same way. The place numbers hold the order.
- jobs_per_team: List.Count(List.Distinct) is COUNT(DISTINCT job_id). job_id has no blank, so nothing is left out.
- run_measures: Table.Unpivot is one SELECT per column, stacked with UNION ALL. Each has WHERE ... IS NOT NULL, as M drops the null. So run 98's blank avg_retry_secs is dropped, which leaves 17 rows, as the Table holds.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, CROSS_JOIN, FROM, GROUP_BY, JOIN, SELECT, SELECT_DISTINCT, UNION_ALL, all_of, count_distinct, derived, descending, equals, is_not_null, row_number, statement
from references.ops__job_owners import job_owners
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets
from references.ops__scheduler_runs import scheduler_runs

teams = derived("teams", statement(SELECT_DISTINCT(jobs.team), FROM(jobs, reads_all_partitions=True)))
regions = derived("regions", statement(SELECT_DISTINCT(jobs.region), FROM(jobs, reads_all_partitions=True)))
team_regions = statement(SELECT(teams.team, regions.region), FROM(teams), CROSS_JOIN(regions))

budget_places = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(row_number(ORDER_BY=descending(region_budgets.budget_cents)), "place")),
    FROM(region_budgets, reads_all_partitions=True),
)
jobs_per_team = statement(
    SELECT(job_owners.team, AS(count_distinct(job_owners.job_id), "jobs")),
    FROM(job_owners, reads_all_partitions=True),
    GROUP_BY(job_owners.team),
)
ran_as_scheduled = statement(
    SELECT_DISTINCT(scheduler_runs.run_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),
    JOIN(job_runs, ON=all_of(equals(job_runs.run_id, scheduler_runs.run_id),
                             equals(job_runs.dt, scheduler_runs.dt))),
)
run_measures = UNION_ALL(
    statement(SELECT(job_runs.run_id, job_runs.job_id, AS(job_runs.duration_mins, "amount")),
              FROM(job_runs, reads_all_partitions=True), WHERE(is_not_null(job_runs.duration_mins))),
    statement(SELECT(job_runs.run_id, job_runs.job_id, AS(job_runs.avg_retry_secs, "amount")),
              FROM(job_runs, reads_all_partitions=True), WHERE(is_not_null(job_runs.avg_retry_secs))),
)
# The labels 'duration_mins' and 'avg_retry_secs' (the measure column) have no Toolbox name in files 03 to 05, so add them from the Hive above.
```

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X66

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Typed, read by the ok_runs query, with no formula, so it needs no step.
- Steps: none.
- Finals:
  - ok_runs (run_id, job_id, duration_mins, dt, running, share). Nothing reads it except its own Total Row.
  - ok_runs (Total Row), a query of its own with one column, duration_mins, a SUM. The "Total" label is not converted.
- Parameters and Keys: none.
- Refused: none.
- Left alone: none.

**Final: ok_runs**

```sql
SELECT o.run_id, o.job_id, o.duration_mins, o.dt,
  COALESCE(SUM(o.duration_mins) OVER (PARTITION BY o.job_id ORDER BY o.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  o.duration_mins / SUM(o.duration_mins) OVER () AS share
FROM <database>.job_runs o
WHERE o.status IS NOT NULL AND o.status LIKE 'SUCC%'
```

**Final: ok_runs (Total Row)**

```sql
WITH ok AS (
  SELECT o.run_id, o.job_id, o.duration_mins, o.dt
  FROM <database>.job_runs o
  WHERE o.status IS NOT NULL AND o.status LIKE 'SUCC%'
)
SELECT SUM(duration_mins) AS duration_mins
FROM ok
```

**Marks**
- The `<> null` filter is IS NOT NULL, and Text.StartsWith "SUCC" is LIKE 'SUCC%', case kept.
- running: a running total per job by date, with ties included. Runs 101 and 104 are both on 2026-09-24 for job 1, so both give 62, as Excel gives.
- share: the whole-column SUM of the rows the query keeps, which is 110.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, descending, is_not_null, starts_with, statement, sum_of, window
from references.ops__job_runs import job_runs

by_job = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt, rows=(None, 0))
whole = window()
kept = (is_not_null(job_runs.status), starts_with(job_runs.status, "SUCC"))  # SUCC kept in case
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(sum_of(job_runs.duration_mins, over=by_job), "running"),
           AS(job_runs.duration_mins / sum_of(job_runs.duration_mins, over=whole), "share")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's query reads every row
    WHERE(*kept),
)
total_row = statement(
    SELECT(AS(sum_of(job_runs.duration_mins), "duration_mins")),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(*kept),
)
```

Note: rows=(None, 0) counts one row at a time, so runs 101 and 104 would give 22 and 62 there. Excel and the Hive give 62 and 62. Check the running column in the Hive.

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X69

**Map**
- Sources: jobs (job_id, job_name, team, region), region_budgets (job_id, budget_cents, region), region_costs (job_id, cost_cents, region, dt). All typed.
- Steps: region_costs, as a CTE `costs`. Its formulas (job_name, budget, over_budget, running_cost) are read by job_totals and late_costs, so it is a step, not a final.
- Finals:
  - job_totals (job_id, total_cents, over_count). A summary: its only typed column is job_id, which its SUMIFS and COUNTIFS match on. It is a GROUP BY of costs. Its Total Row takes SUMs only, so it is the rollup row and needs no query of its own.
  - late_costs (job_id, dt, running_cost). Loaded by a query, read by nothing, so it is a final.
- Parameters and Keys: none.
- Refused: none.
- Left alone: none.

**Step: costs (used by both finals)**

```sql
WITH costs AS (
  SELECT r.job_id, r.cost_cents, r.region, r.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(r.cost_cents) OVER (
      PARTITION BY r.job_id
      ORDER BY CAST(CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) AS DATE)
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
```

**Final: job_totals (with its Total Row)**

```sql
WITH costs AS (
  -- the step above, in full
  SELECT r.job_id, r.cost_cents, r.region, r.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(r.cost_cents) OVER (
      PARTITION BY r.job_id
      ORDER BY CAST(CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) AS DATE)
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT c.job_id,
  COALESCE(SUM(c.cost_cents), 0) AS total_cents,
  COALESCE(COUNT(CASE WHEN c.over_budget = TRUE THEN 1 END), 0) AS over_count
FROM costs c
GROUP BY c.job_id WITH ROLLUP
```

**Final: late_costs**

```sql
WITH costs AS (
  -- the step above, in full
  SELECT r.job_id, r.cost_cents, r.region, r.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(r.cost_cents) OVER (
      PARTITION BY r.job_id
      ORDER BY CAST(CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) AS DATE)
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT c.job_id, c.dt, c.running_cost
FROM costs c
WHERE c.running_cost > 1500
```

**Marks**
- over_budget: the blank cost on row 29 (job 2, 20260924) is read as 0 by COALESCE(cost_cents, 0), so 0 > 200 is FALSE, as Excel gives.
- running_cost: SUMIFS skips the blank, so no COALESCE is needed on the input. The running total for job 2 on 2026-09-24 stays at 1690, as the sample shows.
- dt is held as text (20260911). The running total orders by it, so it is converted to a date with CONCAT(SUBSTR ...) and the date is held as text here. The output dt keeps its original text.
- job_totals (Total Row): the rollup row, with a NULL job_id, is the Total Row. Its totals are SUMs, so no query of its own is needed.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, derived, equals, fill_null, if_else, more_than, rollup, statement, sum_of, window
from references.ops__region_budgets import region_budgets
from references.ops__region_costs import region_costs

each_job = window(PARTITION_BY=region_costs.job_id, ORDER_BY=region_costs.dt, rows=(None, 0))
costs = derived("costs", statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.dt,
           AS(if_else(more_than(fill_null(region_costs.cost_cents, 0), region_budgets.budget_cents), 1, 0),
              "over_budget"),
           AS(sum_of(region_costs.cost_cents, over=each_job), "running_cost")),
    FROM(region_costs, reads_all_partitions=True),  # the workbook's query reads every row
    LEFT_JOIN(region_budgets, ON=equals(region_budgets.job_id, region_costs.job_id)),
))
job_totals = statement(
    SELECT(costs.job_id,
           AS(fill_null(sum_of(costs.cost_cents), 0), "total_cents"),
           AS(fill_null(sum_of(costs.over_budget), 0), "over_count")),
    FROM(costs),
    GROUP_BY(rollup(costs.job_id)),  # the rollup row is the Total Row
)
late_costs = statement(
    SELECT(costs.job_id, costs.dt, costs.running_cost),
    FROM(costs),
    WHERE(more_than(costs.running_cost, 1500)),
)
```

Note: each job has one row per day, so rows=(None, 0) and Excel's RANGE give the same running total here. over_budget is 1 or 0 in the Toolbox code, and TRUE or FALSE in Hive, so the count of over_budget rows is a sum of those.

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X70

**Map**
- Sources: jobs (job_id, job_name, team, region), job_owners (job_id, team, owner, dt), job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). All typed and read directly.
- Steps:
  - staffed (job_id, job_name, owner), a CTE. Its Power Query is marked connection only, but owner_load reads it, so it is a step, not left out.
  - owner_load (owner, total_mins, runs), a CTE. busiest_owner reads it. Its avg_mins formula is read by no final, so it is not written.
- Finals:
  - busiest_owner (owner, total_mins, runs). Nothing reads it.
  - owner_load (Total Row), one column, runs, a SUM. The "Total" label is not converted.
- Parameters and Keys: none.
- Refused: none.
- Left alone: none.

**Final: busiest_owner**

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

**Final: owner_load (Total Row)**

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

**Marks**
- staffed: Table.Distinct on job_id and owner is a SELECT DISTINCT. The blank owner of job 4 drops out, since the join keeps it and the filter removes it.
- owner_load: the LEFT OUTER join fans out. Job 3 has two owners (ana and chloe), so each of its runs counts under both. That gives ana 6 runs and chloe 2, which matches the sample.
- busiest_owner: the sort is descending on runs, then FirstN 1, so it is ORDER BY runs DESC LIMIT 1.

**To fill in**
- `<database>`

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, JOIN, LEFT_JOIN, LIMIT, ORDER_BY, SELECT, SELECT_DISTINCT, WHERE, count_rows, derived, descending, equals, is_not_null, statement, sum_of
from references.ops__job_owners import job_owners
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

owners = derived("owners", statement(
    SELECT_DISTINCT(job_owners.job_id, job_owners.owner),
    FROM(job_owners, reads_all_partitions=True),  # the workbook's query reads every row
))
staffed = derived("staffed", statement(
    SELECT(jobs.job_id, jobs.job_name, owners.owner),
    FROM(jobs, reads_all_partitions=True),
    JOIN(owners, ON=equals(owners.job_id, jobs.job_id)),
    WHERE(is_not_null(owners.owner)),
))
owner_load = derived("owner_load", statement(
    SELECT(staffed.owner, AS(sum_of(job_runs.duration_mins), "total_mins"), AS(count_rows(), "runs")),
    FROM(staffed),
    LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, staffed.job_id)),
    GROUP_BY(staffed.owner),
))
busiest_owner = statement(
    SELECT(owner_load.owner, owner_load.total_mins, owner_load.runs),
    FROM(owner_load),
    ORDER_BY(descending(owner_load.runs)),
    LIMIT(1),
)
owner_load_total = statement(
    SELECT(AS(sum_of(owner_load.runs), "runs")),
    FROM(owner_load),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`, then run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.
