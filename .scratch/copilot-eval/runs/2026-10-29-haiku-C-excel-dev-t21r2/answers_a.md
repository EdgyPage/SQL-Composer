date: 2026-10-29
arm: C
model: haiku
files: 6fc91ff

## X01

**Map**
- Sources: `job_runs` (typed run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: `job_runs` (run_id, job_id, duration_mins, dt, duration_hours). Nothing reads it.
- Typed over a formula: none.
- Marks: none. No blank in the sample.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
  r.duration_mins / 60 AS duration_hours
FROM <database>.job_runs r
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(job_runs.duration_mins / 60, "duration_hours")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X02

**Map**
- Sources: `job_runs` (typed run_id, job_id, status, duration_mins).
- Finals: `job_runs` (run_id, job_id, status, duration_mins, slow_job1, flag). Nothing reads it.
- Typed over a formula: none.
- Marks: none. Status is blank in row 98, but no formula reads status.
- Refusals: none.
- Converted: AND as it is; IF as it is.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins,
  (r.duration_mins > 10 AND r.job_id = 1) AS slow_job1,
  IF(r.duration_mins > 25 OR r.job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs r
```

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, any_of, equals, if_else, more_than, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           AS(all_of(more_than(job_runs.duration_mins, 10), equals(job_runs.job_id, 1)), "slow_job1"),
           AS(if_else(any_of(more_than(job_runs.duration_mins, 25), equals(job_runs.job_id, 3)),
                      "check", "ok"), "flag")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X03

**Map**
- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Finals: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs). Nothing reads it.
- Typed over a formula: none.
- Marks, blank:
  - status in row 98 is blank and score reads it, so it is `COALESCE(status, '')`.
  - avg_retry_secs in row 98 is blank and mins_per_retry and total_secs read it, so it is `COALESCE(avg_retry_secs, 0)`.
- Converted: `_xlfn.SWITCH` as a CASE with three results; IFERROR(a / b, 0) as `COALESCE(a / b, 0)`.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
  CASE COALESCE(r.status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(r.duration_mins / COALESCE(r.avg_retry_secs, 0), 0) AS mins_per_retry,
  r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs r
```

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, first_match, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt,
           AS(first_match([(equals(fill_null(job_runs.status, ""), "SUCCESS"), 1),
                           (equals(fill_null(job_runs.status, ""), "FAILED"), -1)],
                          otherwise=0), "score"),
           AS(fill_null(job_runs.duration_mins / fill_null(job_runs.avg_retry_secs, 0), 0),
              "mins_per_retry"),
           AS(job_runs.duration_mins * 60 + fill_null(job_runs.avg_retry_secs, 0), "total_secs")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
)
```

score has three results, so the Python uses `first_match`, the file 11 name for a CASE. Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X04

**Map**
- Sources: `jobs` (typed job_id, job_name, team, region). Nothing reads it, so it is also a final.
- Finals: `jobs` (job_id, job_name, team, region, code, name_length, third, odd).
- Typed over a formula: none.
- Marks: none. No blank in the sample.
- Converted:
  - `code`: `UPPER(LEFT(job_name, 3)) & "-" & region` as nested CONCAT, with UPPER and LEFT as SUBSTR.
  - `name_length`: LEN as LENGTH.
  - `third`: ROUND as it is.
  - `odd`: MOD as PMOD.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team, j.region,
  CONCAT(CONCAT(UPPER(SUBSTR(j.job_name, 1, 3)), '-'), j.region) AS code,
  LENGTH(j.job_name) AS name_length,
  ROUND(j.job_id / 3, 2) AS third,
  PMOD(j.job_id, 2) AS odd
FROM <database>.jobs j
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
)
```

The Python covers only the plain columns. `code`, `name_length`, `third` and `odd` need UPPER, SUBSTR, CONCAT, LENGTH, ROUND and PMOD, which files 03 to 05 don't show, so load file 10 for those columns. Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X05

**Map**
- Sources: `job_runs` (typed run_id, dt); `region_costs` (typed job_id, cost_cents, region, dt).
- Finals: `job_runs` (run_id, dt, month, days_since); `region_costs` (job_id, cost_cents, region, dt, day). Nothing reads either.
- Typed over a formula: none.
- Marks:
  - region_costs `dt` holds dates as text, such as 20260911. `day` converts with the text-date form, and the date is held as text.
  - cost_cents is blank in row 29, but no formula reads it, so it stays NULL.
- Converted:
  - `DATEDIF(DATE(2026,9,1), dt, "d")` as `DATEDIFF(dt, '2026-09-01')`.
  - `MONTH` as it is.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.dt,
  MONTH(r.dt) AS month,
  DATEDIFF(r.dt, '2026-09-01') AS days_since
FROM <database>.job_runs r
```

```sql
SELECT c.job_id, c.cost_cents, c.region, c.dt,
  CONCAT(SUBSTR(c.dt, 1, 4), '-', SUBSTR(c.dt, 5, 2), '-', SUBSTR(c.dt, 7, 2)) AS day
FROM <database>.region_costs c
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__job_runs import job_runs
from references.<database>__region_costs import region_costs

job_runs_plain = statement(
    SELECT(job_runs.run_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
)
region_costs_plain = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region, region_costs.dt),
    FROM(region_costs, reads_all_partitions=True),  # the workbook's rows are every row
)
```

The Python covers only the plain columns. `month`, `days_since` and `day` need MONTH, DATEDIFF, CONCAT and SUBSTR, which files 03 to 05 don't show, so load file 10 for them. Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X06

**Map**
- Sources: `job_runs` (typed run_id, job_id, duration_mins); `jobs` (typed job_id, job_name, team, region).
- Finals: `job_runs` (run_id, job_id, duration_mins, job_name, runs_of_job). Nothing reads it.
- Typed over a formula: none.
- Marks: none.
- Converted:
  - `_xlfn.XLOOKUP` as a LEFT JOIN on jobs.
  - `COUNTIFS` over its own Table, one match on job_id, as COUNT(*) over the job_id partition, with COALESCE to 0.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, count_rows, equals, fill_null, statement, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

each_job = window(PARTITION_BY=job_runs.job_id)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, jobs.job_name,
           AS(fill_null(count_rows(over=each_job), 0), "runs_of_job")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X07

**Map**
- Sources: `job_runs` (typed run_id, job_id, status); `jobs` (typed job_id, job_name, team, region).
- Finals: `job_runs` (run_id, job_id, status, team, region). Nothing reads it.
- Typed over a formula: none.
- Marks: none. Status is blank in row 98, but no formula reads it.
- Converted: the exact VLOOKUP and the exact INDEX/MATCH both become one LEFT JOIN on jobs, since both match the same job_id. `team` is `jobs.team` and `region` is `jobs.region`.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import FROM, LEFT_JOIN, SELECT, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, jobs.team, jobs.region),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X08

**Map**
- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Summary: `by_job` (typed job_id only, which its SUMIFS, AVERAGEIFS and MAXIFS match on). It is a GROUP BY of `job_runs` on job_id.
- Finals: `by_job` (job_id, total_mins, avg_retry, longest). Nothing reads it.
- Typed over a formula: none.
- Marks: avg_retry_secs is blank in row 98. AVERAGEIFS skips it, and AVG skips NULL, so it is not wrapped.
- Converted:
  - SUMIFS as SUM with COALESCE to 0.
  - MAXIFS as MAX with COALESCE to 0.
  - AVERAGEIFS as AVG, left NULL where nothing matches.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.job_id,
  COALESCE(SUM(r.duration_mins), 0) AS total_mins,
  AVG(r.avg_retry_secs) AS avg_retry,
  COALESCE(MAX(r.duration_mins), 0) AS longest
FROM <database>.job_runs r
GROUP BY r.job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, average_of, fill_null, max_of, statement, sum_of
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id,
           AS(fill_null(sum_of(job_runs.duration_mins), 0), "total_mins"),
           AS(average_of(job_runs.avg_retry_secs), "avg_retry"),
           AS(fill_null(max_of(job_runs.duration_mins), 0), "longest")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
    GROUP_BY(job_runs.job_id),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X09

**Map**
- Sources: `job_runs` (typed run_id, job_id, duration_mins, avg_retry_secs); `jobs` (typed job_id, job_name, team, region).
- Parameters: `rate` is 0.5. The XLOOKUP on `rate` reads its value, so 0.5 is written in.
- Keys: `job_runs`, run_id.
- Finals: `job_runs` (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost). Nothing reads it.
- Typed over a formula: `cost` in row 97 (run_id 97) is typed as 100. The Keys row for job_runs is run_id, so the CASE matches on run_id.
- Marks: avg_retry_secs is blank in row 98, and cost reads it, so it is `COALESCE(avg_retry_secs, 0)`.
- Converted:
  - `team`: XLOOKUP as a LEFT JOIN on jobs.
  - `team_mins`: SUMIFS over its own Table, one match on team, as SUM over the team partition, with COALESCE to 0.
  - `cost`: `* XLOOKUP("rate", ...)` as `* 0.5`.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs, j.team,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.team), 0) AS team_mins,
  CASE WHEN r.run_id = 97 THEN 100
    ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5 END AS cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, first_match, statement, sum_of, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

by_team = window(PARTITION_BY=jobs.team)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.avg_retry_secs,
           jobs.team,
           AS(fill_null(sum_of(job_runs.duration_mins, over=by_team), 0), "team_mins"),
           AS(first_match([(equals(job_runs.run_id, 97), 100)],
                          otherwise=(job_runs.duration_mins * 60
                                     + fill_null(job_runs.avg_retry_secs, 0)) * 0.5),
              "cost")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X10

**Map**
- Sources: `job_runs` (typed run_id, job_id, duration_mins, dt).
- Finals: `job_runs` (run_id, job_id, duration_mins, dt, hours, sample). Nothing reads it.
- Typed over a formula: `hours` in row 9 (run_id 103) is typed as 9. There is no Keys row for job_runs, so the CASE matches every typed column of that row: run_id 103, job_id 3, duration_mins 30, dt 2026-09-24.
- Refusals: `sample` is `RAND()`, so it is `NULL AS sample`.
- Marks: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
  CASE WHEN r.run_id = 103 AND r.job_id = 3 AND r.duration_mins = 30
       AND r.dt = '2026-09-24' THEN 9
    ELSE r.duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs r
```

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, equals, first_match, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(first_match([(all_of(equals(job_runs.run_id, 103), equals(job_runs.job_id, 3),
                                    equals(job_runs.duration_mins, 30),
                                    equals(job_runs.dt, "2026-09-24")), 9)],
                          otherwise=job_runs.duration_mins / 60), "hours")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
)
```

The Python leaves out `sample`, because RAND is refused and the Toolbox names in files 03 to 05 don't write a NULL column. The Hive keeps it as `NULL AS sample`. Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X11

**Map**
- Sources: `job_runs` (typed run_id, duration_mins).
- Finals: `job_runs` (run_id, duration_mins, pick, scaled). Nothing reads it.
- Typed over a formula: none.
- Refusals:
  - `pick` is `INDIRECT("B"&ROW())`, so `NULL AS pick`.
  - `scaled` reads the cell Summary!C2, a cell outside a Table that isn't a defined name, so `NULL AS scaled`.
- Marks: none.
- Left alone: the bar chart on Summary; the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.duration_mins,
  NULL AS pick,
  NULL AS scaled
FROM <database>.job_runs r
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
)
```

The Python leaves out `pick` and `scaled`, which are refused, and the Hive keeps them as NULL. Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X12

**Map**
- Sources: `job_runs` (typed run_id, duration_mins).
- Finals: `job_runs` (run_id, duration_mins, running, loop, with_tax). Nothing reads it.
- Typed over a formula: none.
- Refusals:
  - `running` uses OFFSET and ROW(), so `NULL AS running`.
  - `loop` reads its own column, which is circular, so `NULL AS loop`.
- Defined name: `tax_rate` is Summary!$B$3, a cell outside a Table, so its value 0.2 is used. Move tax_rate's 0.2 into Parameters.
- Marks: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.duration_mins,
  NULL AS running,
  NULL AS loop,
  r.duration_mins * 0.2 AS with_tax
FROM <database>.job_runs r
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins * 0.2, "with_tax")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
)
```

The Python leaves out `running` and `loop`, which are refused, and the Hive keeps them as NULL. Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X13

**Map**
- Sources: `job_runs` (typed run_id, job_id); `jobs` (typed job_id, job_name, team, region).
- Finals: `job_runs` (run_id, job_id, name, doubled). Nothing reads it.
- Typed over a formula: none.
- Converted: `VLOOKUP(job_id, jobs, 2, TRUE)` is approximate. It is converted exactly, as a LEFT JOIN on jobs.job_id returning job_name (column 2). Check that the match you want is exact.
- Refusals: `doubled` is `DOUBLE`, a defined name holding a LAMBDA, so `NULL AS doubled`.
- Marks: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, j.job_name AS name,
  NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, AS(jobs.job_name, "name")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

The Python leaves out `doubled`, which is refused and kept as NULL in the Hive. Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X14

**Map**
- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Step: `job_runs`'s formula column `hours` (`duration_mins / 60`) is read by `by_job`, so it is a CTE named `job_runs`.
- Summary: `by_job` (typed job_id only). It is a GROUP BY of the step on job_id.
- Finals: `by_job` (job_id, total_hours). Nothing reads it.
- Typed over a formula: none.
- Marks: none.
- Converted: SUMIFS over `hours` as SUM with COALESCE to 0.
- Refusals: none.
- Left alone: a PivotTable on sheet Pivot (from job_runs, rows job_id, sum of duration_mins); the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
WITH job_runs AS (
  SELECT r.job_id, r.duration_mins / 60 AS hours
  FROM <database>.job_runs r
)
SELECT job_id, COALESCE(SUM(hours), 0) AS total_hours
FROM job_runs
GROUP BY job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, derived, fill_null, statement, sum_of
from references.<database>__job_runs import job_runs

runs = derived("runs", statement(
    SELECT(job_runs.job_id, AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
))
s = statement(
    SELECT(runs.job_id, AS(fill_null(sum_of(runs.hours), 0), "total_hours")),
    FROM(runs),
    GROUP_BY(runs.job_id),
)
```

The PivotTable is left alone, as the file asks. Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X15

**Map**
- Sources: `tblRuns` (typed `<run_id>` from Run ID, `<job_id>` from Job ID, `<duration_mins>` from Duration (mins)). The Table name tblRuns is a plain name, so it is kept.
- Finals: `tblRuns` (`<run_id>`, `<job_id>`, `<duration_mins>`, hours). Nothing reads it.
- Typed over a formula: none.
- Marks: none.
- Converted: `[@[Duration (mins)]]/60` as `<duration_mins> / 60`, named hours.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`, and each header in snake case: `<run_id>`, `<job_id>`, `<duration_mins>`.

```sql
SELECT r.<run_id>, r.<job_id>, r.<duration_mins>,
  r.<duration_mins> / 60 AS hours
FROM <database>.tblRuns r
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__tblRuns import tblRuns

s = statement(
    SELECT(tblRuns.<run_id>, tblRuns.<job_id>, tblRuns.<duration_mins>,
           AS(tblRuns.<duration_mins> / 60, "hours")),
    FROM(tblRuns, reads_all_partitions=True),  # the workbook's rows are every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X16

**Map**
- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Finals: `long_runs`, the Table loaded by the Power Query `long_runs` (run_id, job_id, minutes, hours). Nothing reads the Table.
- Steps: none. The query `long_runs` is read by no other query, so it is only the Table's query.
- Typed over a formula: none.
- Converted:
  - `Table.SelectColumns` as the SELECT list.
  - `Table.SelectRows` on `duration_mins > 15` as WHERE.
  - `Table.AddColumn` `hours` as `duration_mins / 60`.
  - `Table.RenameColumns` as `duration_mins AS minutes`.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins AS minutes,
  r.duration_mins / 60 AS hours
FROM <database>.job_runs r
WHERE r.duration_mins > 15
```

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, more_than, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, AS(job_runs.duration_mins, "minutes"),
           AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
    WHERE(more_than(job_runs.duration_mins, 15)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X17

**Map**
- Sources: `job_runs` (typed).
- Steps: `ok_runs`, the connection-only query, is read by the query `ok_by_job`, so it is a CTE.
- Finals: `ok_by_job` (job_id, runs, total_mins), the Table loaded by the Power Query `ok_by_job`. Nothing reads the Table.
- Typed over a formula: none.
- Marks: none.
- Converted:
  - `Table.SelectRows` on `[status] = "SUCCESS"` as WHERE status = 'SUCCESS'.
  - `Table.Group` on job_id: `Table.RowCount` as COUNT(*), `List.Sum` as SUM.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
WITH ok_runs AS (
  SELECT r.job_id, r.duration_mins
  FROM <database>.job_runs r
  WHERE r.status = 'SUCCESS'
)
SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived, equals, statement, sum_of
from references.<database>__job_runs import job_runs

ok_runs = derived("ok_runs", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
    WHERE(equals(job_runs.status, "SUCCESS")),
))
s = statement(
    SELECT(ok_runs.job_id, AS(count_rows(), "runs"), AS(sum_of(ok_runs.duration_mins), "total_mins")),
    FROM(ok_runs),
    GROUP_BY(ok_runs.job_id),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X18

**Map**
- Sources: `job_runs` (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (typed job_id, job_name, team, region).
- Steps: none.
- Finals: `top_runs`, the Table loaded by the Power Query `top_runs` (run_id, job_name, duration_mins). Nothing reads it.
- Typed over a formula: none.
- Converted:
  - `Table.NestedJoin` with JoinKind.LeftOuter and the expansion of job_name as LEFT JOIN jobs.
  - `Table.Sort` descending on duration_mins, then `Table.FirstN` 3, as ORDER BY ... DESC LIMIT 3.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC
LIMIT 3
```

```python
from sqlglot_composer import FROM, LEFT_JOIN, LIMIT, ORDER_BY, SELECT, descending, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, jobs.job_name, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's rows are every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    ORDER_BY(descending(job_runs.duration_mins)),
    LIMIT(3),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X19

**Map**
- Sources: `scheduler_runs` (typed run_id, job_id, dt); and the table the Sql.Database call names, `job_runs` in schema `ops` on server `dwh01`, written as `<database>.job_runs`.
- Finals: `all_runs`, the Table loaded by the Power Query `all_runs` (run_id, job_id, dt). Nothing reads it.
- Steps: none.
- Typed over a formula: none.
- Converted: `Table.Combine` as UNION ALL of the two SELECTs.
- Marks: check that `<database>` is the Hive database for the warehouse's `ops` job_runs on `dwh01`. It may differ from the workbook's database.
- Refusals: the connection-only query `holidays` reads `Web.Contents`, a web source. It is left out, and named here.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>` (both places, as checked above).

```sql
SELECT s.run_id, s.job_id, s.dt
FROM <database>.scheduler_runs s
UNION ALL
SELECT w.run_id, w.job_id, w.dt
FROM <database>.job_runs w
```

```python
from sqlglot_composer import FROM, SELECT, UNION_ALL, statement
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

scheduled = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # the workbook's rows are every row
)
warehouse_runs = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # the warehouse's ops job_runs: check it
)
s = UNION_ALL(scheduled, warehouse_runs)
```

The holidays query is left out, since it reads a web source. Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.
