date: 2026-10-29
arm: C
model: haiku
files: 68effd5

## X01

**Map**
- Sources: job_runs (typed run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours).
- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: none. Parameters and Keys are empty, so neither a source nor a final.
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
    FROM(job_runs, reads_all_partitions=True),  # the workbook's formulas read every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X02

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag).
- Typed over a formula: none.
- Marks: none. The blank status in row 98 is not read by a formula, so it stays as it is.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins,
       (r.duration_mins > 10 AND r.job_id = 1) AS slow_job1,
       IF((r.duration_mins > 25 OR r.job_id = 3), 'check', 'ok') AS flag
FROM <database>.job_runs r
```

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, any_of, equals, if_else, more_than, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           AS(if_else(all_of(more_than(job_runs.duration_mins, 10), equals(job_runs.job_id, 1)),
                      True, False), "slow_job1"),
           AS(if_else(any_of(more_than(job_runs.duration_mins, 25), equals(job_runs.job_id, 3)),
                      "check", "ok"), "flag")),
    FROM(job_runs),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X03

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs).
- Typed over a formula: none.
- Marks:
  - blank: status in row 98 is read by score, so it is wrapped as COALESCE(status, '').
  - blank: avg_retry_secs in row 98 is read by mins_per_retry and total_secs, so it is wrapped as COALESCE(avg_retry_secs, 0).
  - IFERROR(a / b, 0) is converted as COALESCE(a / b, 0), since Hive gives NULL for a divide by 0.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
       CASE COALESCE(r.status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
       COALESCE(r.duration_mins / COALESCE(r.avg_retry_secs, 0), 0) AS mins_per_retry,
       r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs r
```

```python
from sqlglot_composer import AS, FROM, SELECT, fill_null, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt,
           AS(job_runs.duration_mins / fill_null(job_runs.avg_retry_secs, 0), "mins_per_retry"),
           AS(job_runs.duration_mins * 60 + fill_null(job_runs.avg_retry_secs, 0), "total_secs")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's formulas read every row
    # score has three labels and the divide-by-0 guard is not in files 03 to 05: load file 10
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ. The score column and the 0 for a divide by 0 need file 10, which you load in a new chat.

## X04

**Map**
- Sources: jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd).
- Typed over a formula: none.
- Marks: none. No blanks in the sample.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team, j.region,
       CONCAT(UPPER(SUBSTR(j.job_name, 1, 3)), '-', j.region) AS code,
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
    # code, name_length, third and odd use UPPER, SUBSTR, CONCAT, LENGTH, ROUND and PMOD: load file 10
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ. The four calculated columns need file 10, which you load in a new chat.

## X05

**Map**
- Sources: job_runs (typed run_id, dt); region_costs (typed job_id, cost_cents, region, dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month, days_since); region_costs (job_id, cost_cents, region, dt, day).
- Typed over a formula: none.
- Marks:
  - region_costs.dt is held as text (such as 20260911), so day is converted with CONCAT(SUBSTR(...)) instead of DATE(LEFT, MID, RIGHT).
  - The blank cost_cents in row 29 of region_costs is not read by a formula, so it stays as it is.
- Refusals: none.
- Left alone: none.
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

runs = statement(
    SELECT(job_runs.run_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's formulas read every row
    # month and days_since use MONTH and DATEDIFF: load file 10
)
costs = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region, region_costs.dt),
    FROM(region_costs, reads_all_partitions=True),  # the workbook's formulas read every row
    # day converts text dates with SUBSTR and CONCAT: load file 10
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ. The calculated columns need file 10, which you load in a new chat.

## X06

**Map**
- Sources: job_runs (typed run_id, job_id, duration_mins); jobs (typed job_id, job_name, team, region).
- Steps: none. jobs is read by job_runs, so it is a source and not a final.
- Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job).
- Mapping: XLOOKUP becomes a LEFT JOIN of jobs on job_id. COUNTIFS over job_runs' own job_id becomes COUNT(*) OVER (PARTITION BY job_id).
- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
       j.job_name AS job_name,
       COUNT(*) OVER (PARTITION BY r.job_id) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, count_rows, equals, statement, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

by_job = window(PARTITION_BY=job_runs.job_id)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, jobs.job_name,
           AS(count_rows(over=by_job), "runs_of_job")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's formulas read every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X07

**Map**
- Sources: job_runs (typed run_id, job_id, status); jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, team, region).
- Mapping: VLOOKUP(job_id, jobs, 3, FALSE) is exact and returns column 3 of jobs, team. INDEX(jobs[region], MATCH(...)) is exact and returns region. Both are one LEFT JOIN of jobs on job_id.
- Typed over a formula: none.
- Marks: none. The blank status in row 98 is not read by a formula.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status,
       j.team AS team,
       j.region AS region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import FROM, LEFT_JOIN, SELECT, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, jobs.team, jobs.region),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X08

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: by_job (job_id, total_mins, avg_retry, longest). by_job's only typed column is job_id, which its SUMIFS, AVERAGEIFS and MAXIFS match on, so it is a summary: a GROUP BY of job_runs. Nothing reads it, so it is a final.
- Typed over a formula: none.
- Marks: blank avg_retry_secs in row 98 is read by AVERAGEIFS, so it is wrapped as COALESCE(avg_retry_secs, 0). Note that Excel's AVERAGEIFS skips a blank, while the COALESCE counts it as 0, so check avg_retry against the workbook.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.job_id,
       SUM(r.duration_mins) AS total_mins,
       AVG(COALESCE(r.avg_retry_secs, 0)) AS avg_retry,
       MAX(r.duration_mins) AS longest
FROM <database>.job_runs r
GROUP BY r.job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, average_of, fill_null, max_of, statement, sum_of
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id,
           AS(sum_of(job_runs.duration_mins), "total_mins"),
           AS(average_of(fill_null(job_runs.avg_retry_secs, 0)), "avg_retry"),
           AS(max_of(job_runs.duration_mins), "longest")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's formulas read every row
    GROUP_BY(job_runs.job_id),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X09

**Map**
- Sources: job_runs (typed run_id, job_id, duration_mins, avg_retry_secs); jobs (typed job_id, job_name, team, region).
- Parameters: neither a source nor a final. The rate is read from Parameters as 0.5.
- Keys: job_runs, run_id. This is the Keys row used for the typed-over value.
- Steps: none. jobs is read by job_runs, so it is a source and not a final.
- Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost).
- Typed over a formula: cost in row 97 (run_id 97) is typed as 100. Matched on run_id from the Keys row.
- Marks: blank avg_retry_secs in row 98 is read by cost, so it is wrapped as COALESCE(avg_retry_secs, 0).
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`.
- team_mins is SUMIFS over job_runs' own team column, so it is a window partitioned by team.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs,
       j.team AS team,
       SUM(r.duration_mins) OVER (PARTITION BY j.team) AS team_mins,
       CASE WHEN r.run_id = 97 THEN 100
            ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5
       END AS cost
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
           AS(sum_of(job_runs.duration_mins, over=by_team), "team_mins"),
           AS(first_match([(equals(job_runs.run_id, 97), 100)],
                          otherwise=(job_runs.duration_mins * 60 + fill_null(job_runs.avg_retry_secs, 0)) * 0.5),
              "cost")),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X10

**Map**
- Sources: job_runs (typed run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample).
- Keys: there is no Keys row for job_runs, since the Keys table is empty. So the typed-over row is matched on every typed column of the row.
- Typed over a formula: hours in row 9 (run_id 103) is typed as 9. Matched on run_id = 103, job_id = 3, duration_mins = 30 and dt = '2026-09-24'.
- Marks: none.
- Refusals: sample is `=RAND()`, so it is `NULL AS sample`.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
       CASE WHEN r.run_id = 103 AND r.job_id = 3 AND r.duration_mins = 30 AND r.dt = '2026-09-24'
            THEN 9 ELSE r.duration_mins / 60 END AS hours,
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
    FROM(job_runs, reads_all_partitions=True),  # the workbook's formulas read every row
    # sample is refused (RAND), so it is left out here; the Hive keeps it as NULL AS sample
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X11

**Map**
- Sources: job_runs (typed run_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, duration_mins, pick, scaled).
- Typed over a formula: none.
- Marks: none.
- Refusals:
  - pick is `INDIRECT`, so it is `NULL AS pick`.
  - scaled reads Summary!$C$2, a cell outside a Table that is not a defined name, so it is `NULL AS scaled`.
- Left alone: the cell Summary!C2 (outside a Table), and the bar chart on Summary.
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
    FROM(job_runs),
    # pick (INDIRECT) and scaled (Summary C2, outside a Table) are refused; the Hive keeps them as NULL
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X12

**Map**
- Sources: job_runs (typed run_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, duration_mins, running, loop, with_tax).
- Typed over a formula: none.
- Marks:
  - The defined name tax_rate is Summary!$B$3, a cell outside a Table. Its value 0.2 is used, and move tax_rate into Parameters.
- Refusals:
  - running is `SUM(OFFSET(...))`, so it is `NULL AS running`.
  - loop reads its own column (circular), so it is `NULL AS loop`.
- Left alone: the cell Summary!B3 (outside a Table), read only through the defined name.
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
           AS(job_runs.duration_mins * 0.2, "with_tax")),  # tax_rate is Summary!B3 = 0.2; move it into Parameters
    FROM(job_runs),
    # running (OFFSET) and loop (circular) are refused; the Hive keeps them as NULL
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X13

**Map**
- Sources: job_runs (typed run_id, job_id); jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, name, doubled).
- Typed over a formula: none.
- Marks: VLOOKUP(job_id, jobs, 2, TRUE) is approximate. It is converted exactly, as a LEFT JOIN of jobs on job_id, then job_name (column 2 of jobs).
- Refusals: doubled calls DOUBLE, a defined name holding a LAMBDA, so it is `NULL AS doubled`.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id,
       j.job_name AS name,
       NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, AS(jobs.job_name, "name")),  # approximate VLOOKUP, converted exactly
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    # doubled (a LAMBDA defined name) is refused; the Hive keeps it as NULL
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X14

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); its hours column is `duration_mins / 60`.
- Steps: none.
- Finals: by_job (job_id, total_hours). by_job's only typed column is job_id, which its SUMIFS matches on, so it is a summary: a GROUP BY of job_runs. Nothing reads it, so it is a final. job_runs is read by by_job, so it is a source and not a final.
- Typed over a formula: none.
- Marks: none. The blanks in row 98 are not read by a formula.
- Refusals: none.
- Left alone: the PivotTable on sheet Pivot.
- Fill in: `<database>`.

```sql
SELECT r.job_id,
       SUM(r.duration_mins / 60) AS total_hours
FROM <database>.job_runs r
GROUP BY r.job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, statement, sum_of
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins / 60), "total_hours")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's formulas read every row
    GROUP_BY(job_runs.job_id),
)
```

Take out of the workbook anything you don't want converted, such as the PivotTable, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X15

**Map**
- Sources: tblRuns (typed Run ID, Job ID, Duration (mins)).
- Steps: none.
- Finals: tblRuns (Run ID, Job ID, Duration (mins), Hours).
- Names: the headers that aren't plain names are written in snake case in brackets: `Run ID` is `<run_id>`, `Job ID` is `<job_id>`, `Duration (mins)` is `<duration_mins>`. The Table name tblRuns and the header Hours are plain, so they are kept.
- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`, and the three names `<run_id>`, `<job_id>` and `<duration_mins>`, to check against the Table's headers.

```sql
SELECT t.<run_id>, t.<job_id>, t.<duration_mins>,
       t.<duration_mins> / 60 AS Hours
FROM <database>.tblRuns t
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__tblRuns import tblRuns

s = statement(
    SELECT(tblRuns.<run_id>, tblRuns.<job_id>, tblRuns.<duration_mins>,
           AS(tblRuns.<duration_mins> / 60, "Hours")),
    FROM(tblRuns),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X16

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none. The Power Query's steps are its own query.
- Finals: long_runs (run_id, job_id, minutes, hours). It is loaded by the Power Query long_runs, which is the final's query.
- Power Query: Table.SelectColumns is the SELECT list; Table.SelectRows is WHERE duration_mins > 15; Table.AddColumn is duration_mins / 60 AS hours; Table.RenameColumns is duration_mins AS minutes.
- Typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id,
       r.duration_mins AS minutes,
       r.duration_mins / 60 AS hours
FROM <database>.job_runs r
WHERE r.duration_mins > 15
```

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, more_than, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id,
           AS(job_runs.duration_mins, "minutes"),
           AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's query reads every row
    WHERE(more_than(job_runs.duration_mins, 15)),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X17

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: ok_runs, the connection-only Power Query, which ok_by_job's query reads. It is a CTE: WHERE status = 'SUCCESS'.
- Finals: ok_by_job (job_id, runs, total_mins). Its query is Table.Group: GROUP BY job_id, COUNT(*) as runs, SUM(duration_mins) as total_mins.
- Typed over a formula: none.
- Marks: none. The blank status in row 98 is filtered by the query, which M's = keeps out.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
WITH ok_runs AS (
  SELECT r.job_id, r.duration_mins
  FROM <database>.job_runs r
  WHERE r.status = 'SUCCESS'
)
SELECT o.job_id, COUNT(*) AS runs, SUM(o.duration_mins) AS total_mins
FROM ok_runs o
GROUP BY o.job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived, equals, statement, sum_of
from references.<database>__job_runs import job_runs

ok_runs = derived("ok_runs", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's query reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
))
s = statement(
    SELECT(ok_runs.job_id, AS(count_rows(), "runs"), AS(sum_of(ok_runs.duration_mins), "total_mins")),
    FROM(ok_runs),
    GROUP_BY(ok_runs.job_id),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X18

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed job_id, job_name, team, region).
- Steps: none.
- Finals: top_runs (run_id, job_name, duration_mins).
- Power Query: Table.NestedJoin with JoinKind.LeftOuter is a LEFT JOIN of jobs on job_id; Table.ExpandTableColumn gives job_name; Table.Sort with Order.Descending is ORDER BY duration_mins DESC; Table.FirstN(3) is LIMIT 3; Table.SelectColumns is the SELECT list.
- Typed over a formula: none.
- Marks: the rows at 30 minutes tie (runs 97 and 103), so their order may differ from the sample.
- Refusals: none.
- Left alone: none.
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
    FROM(job_runs, reads_all_partitions=True),  # the workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    ORDER_BY(descending(job_runs.duration_mins)),
    LIMIT(3),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X19

**Map**
- Sources: scheduler_runs (typed run_id, job_id, dt); job_runs, read through the Power Query's `Sql.Database("dwh01", "ops")` and its table `ops.job_runs`.
- Check: the M names ops.job_runs on server dwh01. I wrote `<database>.job_runs`; check that it is the same table.
- Steps: none.
- Finals: all_runs (run_id, job_id, dt). Table.Combine is UNION ALL.
- Typed over a formula: none.
- Marks: the Sql.Database source is named above, so check the server and the database.
- Refusals: the connection-only query holidays reads Web.Contents, an online source, so it is left out.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT s.run_id, s.job_id, s.dt
FROM <database>.scheduler_runs s
UNION ALL
SELECT r.run_id, r.job_id, r.dt
FROM <database>.job_runs r
```

```python
from sqlglot_composer import FROM, SELECT, UNION_ALL, statement
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

scheduled = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # the workbook's query reads every row
)
warehouse_runs = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # the M reads every row
)
s = UNION_ALL(scheduled, warehouse_runs)
```

Take out of the workbook anything you don't want converted, such as the holidays query, fill in each `<...>`, check that `<database>.job_runs` is the table the M names, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X20

**Map**
- Sources: run_alerts (typed alert_id, run_id, severity, dt).
- Steps: none.
- Finals: alert_pivot (run_id, high, low).
- Power Query: Table.SelectRows is WHERE run_id = 97 OR run_id = 101; Table.SelectColumns is the SELECT list; the n column of 1 is the 1 inside each CASE; Table.Pivot is GROUP BY run_id with SUM(CASE WHEN severity = ...) columns.
- Typed over a formula: none.
- Marks: the pivot's columns are now fixed to high and low, the values in the sample. A new severity will not get a column. Where a run has no alert of a severity, the column is NULL, as M leaves it.
- Refusals: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT a.run_id,
       SUM(CASE WHEN a.severity = 'high' THEN 1 END) AS high,
       SUM(CASE WHEN a.severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts a
WHERE (a.run_id = 97 OR a.run_id = 101)
GROUP BY a.run_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, any_of, count_rows, equals, statement
from references.<database>__run_alerts import run_alerts

s = statement(
    SELECT(run_alerts.run_id,
           AS(count_rows(where=equals(run_alerts.severity, "high")), "high"),  # 0 where Hive gives NULL
           AS(count_rows(where=equals(run_alerts.severity, "low")), "low")),
    FROM(run_alerts, reads_all_partitions=True),  # the workbook's query reads every row
    WHERE(any_of(equals(run_alerts.run_id, 97), equals(run_alerts.run_id, 101))),
    GROUP_BY(run_alerts.run_id),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive, whose code is checked and wins where the two differ.
