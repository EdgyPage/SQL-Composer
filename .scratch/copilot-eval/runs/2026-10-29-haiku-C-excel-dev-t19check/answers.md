date: 2026-10-29
arm: C
model: haiku
files: 61c9ca2

## X01

Map
- Sources: job_runs (run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs, with the columns run_id, job_id, duration_mins, dt, duration_hours.
- Typed over a formula: none.
- Marks: none. Parameters and Keys are empty, and nothing is typed over, so no Keys row is needed.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
  r.duration_mins / 60 AS duration_hours
FROM <database>.job_runs r
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(job_runs.duration_mins / 60, "duration_hours")),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X02

Map
- Sources: job_runs (run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs, with the columns run_id, job_id, status, duration_mins, slow_job1, flag.
- Typed over a formula: none.
- Marks: none. Nothing is typed over, so no Keys row is needed. The blank status in row 98 is read by no formula, so it passes through as NULL.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins,
  (r.duration_mins > 10 AND r.job_id = 1) AS slow_job1,
  IF(r.duration_mins > 25 OR r.job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs r
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, any_of, equals, if_else, more_than, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           AS(all_of(more_than(job_runs.duration_mins, 10), equals(job_runs.job_id, 1)), "slow_job1"),
           AS(if_else(any_of(more_than(job_runs.duration_mins, 25), equals(job_runs.job_id, 3)),
                      "check", "ok"), "flag")),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X03

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: job_runs, with the columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs.
- Typed over a formula: none.
- Marks:
  - score: `_xlfn.` removed. The blank status in row 98 is read by score, so it is wrapped as COALESCE(status, ''). Say blank.
  - mins_per_retry and total_secs: the blank avg_retry_secs in row 98 is read by both, so it is wrapped as COALESCE(avg_retry_secs, 0). Say blank.
  - IFERROR(a / b, 0) is written as COALESCE(a / b, 0).
  - No Keys row is needed, as nothing is typed over.
- Refused: none.
- Left alone: none.
- Left out of the Toolbox code: score is a label with three values (1, -1, 0). Labels with more than two values are covered by Copilot file 10, which is not loaded in this chat. Load file 10 in a new chat for score.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
  CASE COALESCE(r.status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(r.duration_mins / COALESCE(r.avg_retry_secs, 0), 0) AS mins_per_retry,
  r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs r
```

Toolbox code, without score, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, SELECT, fill_null, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt,
           AS(fill_null(job_runs.duration_mins / fill_null(job_runs.avg_retry_secs, 0), 0),
              "mins_per_retry"),
           AS(job_runs.duration_mins * 60 + fill_null(job_runs.avg_retry_secs, 0), "total_secs")),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
    # score is left out here: load Copilot file 10 in a new chat for it
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X04

Map
- Sources: jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: jobs, with the columns job_id, job_name, team, region, code, name_length, third, odd.
- Typed over a formula: none.
- Marks: none. No Keys row is needed.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team, j.region,
  CONCAT(CONCAT(UPPER(SUBSTR(j.job_name, 1, 3)), '-'), j.region) AS code,
  LENGTH(j.job_name) AS name_length,
  ROUND(j.job_id / 3, 2) AS third,
  PMOD(j.job_id, 2) AS odd
FROM <database>.jobs j
```

Toolbox code. The four typed columns are covered by files 03 to 05. The calculated columns code, name_length, third and odd need Copilot file 10 (Hive functions), which is not loaded in this chat, so load it in a new chat for them.

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
    # code, name_length, third and odd: load Copilot file 10 in a new chat for them
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X05

Map
- Sources: job_runs (run_id, dt); region_costs (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: job_runs, with the columns run_id, dt, month, days_since; region_costs, with the columns job_id, cost_cents, region, dt, day.
- Typed over a formula: none.
- Marks:
  - region_costs dt is a date held as text (such as 20260911). The day column converts it as CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)). Say the date is held as text.
  - days_since: DATEDIF(DATE(2026,9,1), dt, "d") is DATEDIFF(dt, '2026-09-01').
  - No Keys row is needed, as nothing is typed over.
- Refused: none.
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

Toolbox code. The plain columns are covered by files 03 to 05. The calculated columns month, days_since and day need Copilot file 10 (Hive functions), which is not loaded in this chat, so load it in a new chat for them.

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__job_runs import job_runs
from references.<database>__region_costs import region_costs

job_runs_out = statement(
    SELECT(job_runs.run_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # every row
    # month and days_since: load Copilot file 10 in a new chat for them
)
region_costs_out = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region, region_costs.dt),
    FROM(region_costs, reads_all_partitions=True),  # every row
    # day: load Copilot file 10 in a new chat for it
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X06

Map
- Sources: job_runs (run_id, job_id, duration_mins); jobs (job_id, job_name).
- Steps: none.
- Finals: job_runs, with the columns run_id, job_id, duration_mins, job_name, runs_of_job.
- Typed over a formula: none.
- Marks: none. No blanks in the columns read, and no Keys row is needed.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, count_rows, equals, fill_null, statement, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

each_job = window(PARTITION_BY=job_runs.job_id)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, jobs.job_name,
           AS(fill_null(count_rows(over=each_job), 0), "runs_of_job")),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X07

Map
- Sources: job_runs (run_id, job_id, status); jobs (job_id, team, region).
- Steps: none.
- Finals: job_runs, with the columns run_id, job_id, status, team, region.
- Typed over a formula: none.
- Marks: VLOOKUP(job_id, jobs, 3, FALSE) and INDEX/MATCH are both exact. One LEFT JOIN on job_id covers both lookups.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, jobs.team, jobs.region),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X08

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: by_job, with the columns job_id, total_mins, avg_retry, longest. by_job only has job_id typed, so it is a summary: a GROUP BY of job_runs.
- Typed over a formula: none.
- Marks:
  - total_mins and longest are SUMIFS and MAXIFS, so each is wrapped in COALESCE(.., 0).
  - avg_retry is AVERAGEIFS, which is left NULL. The blank avg_retry_secs in row 98 is skipped by AVG, so it is not wrapped.
  - No Keys row is needed, as nothing is typed over.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.job_id,
  COALESCE(SUM(r.duration_mins), 0) AS total_mins,
  AVG(r.avg_retry_secs) AS avg_retry,
  COALESCE(MAX(r.duration_mins), 0) AS longest
FROM <database>.job_runs r
GROUP BY r.job_id
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, average_of, fill_null, max_of, statement, sum_of
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id,
           AS(fill_null(sum_of(job_runs.duration_mins), 0), "total_mins"),
           AS(average_of(job_runs.avg_retry_secs), "avg_retry"),
           AS(fill_null(max_of(job_runs.duration_mins), 0), "longest")),
    FROM(job_runs, reads_all_partitions=True),  # every row, the summary adds up all of them
    GROUP_BY(job_runs.job_id),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X09

Map
- Sources: job_runs (run_id, job_id, duration_mins, avg_retry_secs); jobs (job_id, team).
- Steps: none.
- Finals: job_runs, with the columns run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost.
- Typed over a formula: cost where run_id is 97 is typed as 100. The Keys sheet has a row for job_runs, key run_id, so the row is matched on run_id.
- Parameters: rate is read as 0.5 from the Parameters table.
- Marks:
  - The blank avg_retry_secs in row 98 is read by cost, so it is wrapped as COALESCE(avg_retry_secs, 0). Say blank.
  - team_mins is SUMIFS over its own Table, so it is a window partitioned by team, wrapped in COALESCE(.., 0).
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs, j.team,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.team), 0) AS team_mins,
  CASE WHEN r.run_id = 97 THEN 100
       ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5 END AS cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, first_match, statement, sum_of, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

each_team = window(PARTITION_BY=jobs.team)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.avg_retry_secs,
           jobs.team,
           AS(fill_null(sum_of(job_runs.duration_mins, over=each_team), 0), "team_mins"),
           AS(first_match([(equals(job_runs.run_id, 97), 100)],
                          otherwise=(job_runs.duration_mins * 60 + fill_null(job_runs.avg_retry_secs, 0)) * 0.5),
              "cost")),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X10

Map
- Sources: job_runs (run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs, with the columns run_id, job_id, duration_mins, dt, hours, sample.
- Typed over a formula: hours where run_id is 103 is typed as 9. There is no Keys row for job_runs, so the row is matched on every typed column of the row (run_id, job_id, duration_mins, dt). Say there is no Keys row.
- Marks: none beyond the above.
- Refused: sample, because RAND is refused. It is NULL.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
  CASE WHEN r.run_id = 103 AND r.job_id = 3 AND r.duration_mins = 30 AND r.dt = '2026-09-24' THEN 9
       ELSE r.duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs r
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, equals, first_match, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(first_match([(all_of(equals(job_runs.run_id, 103), equals(job_runs.job_id, 3),
                                    equals(job_runs.duration_mins, 30),
                                    equals(job_runs.dt, "2026-09-24")), 9)],
                          otherwise=job_runs.duration_mins / 60),
              "hours"),
           # sample is refused (RAND), so it is NULL in the Hive and left out here
    ),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X11

Map
- Sources: job_runs (run_id, duration_mins).
- Steps: none.
- Finals: job_runs, with the columns run_id, duration_mins, pick, scaled.
- Typed over a formula: none.
- Marks: none.
- Refused:
  - pick: INDIRECT is refused.
  - scaled: Summary!C2 is a cell outside a Table and is not a defined name, so it is refused.
- Left alone: the Summary sheet's cell C2 and the bar chart on Summary.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.duration_mins,
  NULL AS pick,
  NULL AS scaled
FROM <database>.job_runs r
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
    # pick (INDIRECT) and scaled (Summary!C2) are refused, so they are NULL in the Hive and left out here
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X12

Map
- Sources: job_runs (run_id, duration_mins).
- Steps: none.
- Finals: job_runs, with the columns run_id, duration_mins, running, loop, with_tax.
- Typed over a formula: none.
- Marks:
  - with_tax: the defined name tax_rate is Summary!B3, a cell outside a Table, so its value 0.2 is used. Move it into Parameters.
- Refused:
  - running: OFFSET is refused.
  - loop: it reads its own column, so it is circular and refused.
- Left alone: the Summary sheet, with cell B3 outside a Table.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.duration_mins,
  NULL AS running,
  NULL AS loop,
  r.duration_mins * 0.2 AS with_tax
FROM <database>.job_runs r
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins * 0.2, "with_tax")),  # 0.2 is tax_rate from Summary!B3; move it into Parameters
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X13

Map
- Sources: job_runs (run_id, job_id); jobs (job_id, job_name).
- Steps: none.
- Finals: job_runs, with the columns run_id, job_id, name, doubled.
- Typed over a formula: none.
- Marks:
  - name: VLOOKUP(job_id, jobs, 2, TRUE) is approximate. It is converted exactly, as a LEFT JOIN on job_id, and the match is said to have been approximate.
- Refused:
  - doubled: DOUBLE is a defined name holding a LAMBDA, so it is refused.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, j.job_name AS name,
  NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, AS(jobs.job_name, "name")),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X14

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: job_runs's hours column is read by by_job, so it is a step. It is a CTE.
- Finals: by_job, with the columns job_id, total_hours. job_runs is not a final, as by_job reads it.
- Typed over a formula: none.
- Marks: none.
- Refused: none.
- Left alone: the PivotTable on sheet Pivot, from job_runs.
- Fill in: `<database>`.

```sql
WITH runs_with_hours AS (
  SELECT r.job_id, r.duration_mins / 60 AS hours
  FROM <database>.job_runs r
)
SELECT w.job_id,
  COALESCE(SUM(w.hours), 0) AS total_hours
FROM runs_with_hours w
GROUP BY w.job_id
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, derived, fill_null, statement, sum_of
from references.<database>__job_runs import job_runs

runs_with_hours = derived("runs_with_hours", statement(
    SELECT(job_runs.job_id, AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the summary adds up all of them
))
s = statement(
    SELECT(runs_with_hours.job_id, AS(fill_null(sum_of(runs_with_hours.hours), 0), "total_hours")),
    FROM(runs_with_hours),
    GROUP_BY(runs_with_hours.job_id),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X15

Map
- Sources: tblRuns (`<run_id>`, `<job_id>`, `<duration_mins>`).
- Steps: none.
- Finals: tblRuns, with the columns `<run_id>`, `<job_id>`, `<duration_mins>`, hours.
- Names: the Table name tblRuns is a plain name, so it is kept. The headers are "Run ID" as `<run_id>`, "Job ID" as `<job_id>`, and "Duration (mins)" as `<duration_mins>`. Fill each in with the real column name. Hours is a plain name, so it is kept.
- Typed over a formula: none.
- Marks: none. No Keys row is needed.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`.

```sql
SELECT t.<run_id>, t.<job_id>, t.<duration_mins>,
  t.<duration_mins> / 60 AS hours
FROM <database>.tblRuns t
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__tblRuns import tblRuns

s = statement(
    SELECT(tblRuns.<run_id>, tblRuns.<job_id>, tblRuns.<duration_mins>,
           AS(tblRuns.<duration_mins> / 60, "hours")),
    FROM(tblRuns, reads_all_partitions=True),  # every row, as the final keeps every row
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X16

Map
- Sources: job_runs (run_id, job_id, duration_mins).
- Steps: none. The long_runs query is the Power Query that loads the final Table.
- Finals: long_runs, with the columns run_id, job_id, minutes, hours. Its query keeps the rows over 15 minutes, so it is one query.
- Typed over a formula: none.
- Marks:
  - Table.SelectRows is WHERE duration_mins > 15.
  - Table.AddColumn hours is duration_mins / 60.
  - Table.RenameColumns is duration_mins AS minutes.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT j.run_id, j.job_id, j.duration_mins AS minutes, j.duration_mins / 60 AS hours
FROM <database>.job_runs j
WHERE j.duration_mins > 15
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, more_than, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id,
           AS(job_runs.duration_mins, "minutes"),
           AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs, reads_all_partitions=True),  # every row, the query only filters out the short ones
    WHERE(more_than(job_runs.duration_mins, 15)),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X17

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: ok_runs, the connection-only query that ok_by_job reads. It is a CTE.
- Finals: ok_by_job, with the columns job_id, runs, total_mins.
- Typed over a formula: none.
- Marks:
  - Table.SelectRows on status = "SUCCESS" is WHERE status = 'SUCCESS'.
  - Table.RowCount is COUNT(*), and List.Sum is SUM.
- Refused: none.
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

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived, equals, statement, sum_of
from references.<database>__job_runs import job_runs

ok_runs = derived("ok_runs", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # every row, the query keeps only the successes
    WHERE(equals(job_runs.status, "SUCCESS")),
))
ok_by_job = statement(
    SELECT(ok_runs.job_id, AS(count_rows(), "runs"), AS(sum_of(ok_runs.duration_mins), "total_mins")),
    FROM(ok_runs),
    GROUP_BY(ok_runs.job_id),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X18

Map
- Sources: job_runs (run_id, job_id, duration_mins); jobs (job_id, job_name).
- Steps: none.
- Finals: top_runs, with the columns run_id, job_name, duration_mins.
- Typed over a formula: none.
- Marks:
  - Table.NestedJoin with LeftOuter is a LEFT JOIN on job_id.
  - Table.Sort descending is ORDER BY duration_mins DESC, and Table.FirstN 3 is LIMIT 3.
  - Ties: runs 97 and 103 both have 30 minutes, so run_id is added as a second ORDER BY column so the order is one.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC, r.run_id
LIMIT 3
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import FROM, LEFT_JOIN, LIMIT, ORDER_BY, SELECT, descending, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, jobs.job_name, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    ORDER_BY(descending(job_runs.duration_mins), job_runs.run_id),  # run_id keeps the order one when runs tie
    LIMIT(3),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X19

Map
- Sources: scheduler_runs (run_id, job_id, dt); job_runs, the table the all_runs query reads from the warehouse with Sql.Database("dwh01", "ops"), named job_runs in schema ops.
- Steps: none.
- Finals: all_runs, with the columns run_id, job_id, dt. Its query is a UNION ALL of the two sources, as Table.Combine gives.
- Typed over a formula: none.
- Marks:
  - job_runs comes from the warehouse, not a workbook Table. Check that `<database>` is the ops database holding job_runs on dwh01.
  - Table.SelectColumns on run_id, job_id, dt is the SELECT list of each side.
- Refused:
  - The holidays query reads Web.Contents, so it is refused and left out.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT s.run_id, s.job_id, s.dt
FROM <database>.scheduler_runs s
UNION ALL
SELECT w.run_id, w.job_id, w.dt
FROM <database>.job_runs w
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import FROM, SELECT, UNION_ALL, statement
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

scheduled = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # every row
)
warehouse_runs = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # every row
)
all_runs = UNION_ALL(scheduled, warehouse_runs)
# holidays (Web.Contents) is refused and left out
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X20

Map
- Sources: run_alerts (alert_id, run_id, severity, dt).
- Steps: none.
- Finals: alert_pivot, with the columns run_id, high, low.
- Typed over a formula: none.
- Marks:
  - Table.SelectRows on run_id = 97 or run_id = 101 is WHERE with OR.
  - Table.Pivot: a SUM(CASE WHEN severity = 'high' THEN 1 END) AS high column and a SUM(CASE WHEN severity = 'low' THEN 1 END) AS low column, one per value in the sample. Each is NULL where a run has none, as M leaves it. The pivot's columns are now fixed at high and low.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT a.run_id,
  SUM(CASE WHEN a.severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN a.severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts a
WHERE a.run_id = 97 OR a.run_id = 101
GROUP BY a.run_id
```

Toolbox code, with `<database>` filled in as your database. count_rows gives 0, not NULL, where a run has no such severity, so check that against the Hive.

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, any_of, count_rows, equals, statement
from references.<database>__run_alerts import run_alerts

alert_pivot = statement(
    SELECT(run_alerts.run_id,
           AS(count_rows(where=equals(run_alerts.severity, "high")), "high"),
           AS(count_rows(where=equals(run_alerts.severity, "low")), "low")),
    FROM(run_alerts, reads_all_partitions=True),  # every row, as the final keeps every row
    WHERE(any_of(equals(run_alerts.run_id, 97), equals(run_alerts.run_id, 101))),
    GROUP_BY(run_alerts.run_id),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X41

Map
- Sources: job_runs (run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs, with the columns run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total.
- Typed over a formula: none.
- Marks:
  - RANK.EQ(x, t[x]) is RANK() OVER (ORDER BY x DESC).
  - MINIFS over its own Table is MIN(CASE WHEN status = 'SUCCESS' THEN duration_mins END) OVER (PARTITION BY job_id), wrapped in COALESCE(.., 0). The blank status in row 98 is skipped by the -IFS form, so it is not wrapped.
  - SUMIF over its own Table is SUM over the window, wrapped in COALESCE(.., 0).
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins,
  RANK() OVER (ORDER BY r.duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN r.status = 'SUCCESS' THEN r.duration_mins END) OVER (PARTITION BY r.job_id), 0) AS shortest_ok,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id), 0) AS job_total
FROM <database>.job_runs r
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, SELECT, descending, equals, fill_null, min_of, rank, statement, sum_of, window
from references.<database>__job_runs import job_runs

by_job = window(PARTITION_BY=job_runs.job_id)
longest = window(ORDER_BY=descending(job_runs.duration_mins))
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           AS(rank(over=longest), "longest_first"),
           AS(fill_null(min_of(job_runs.duration_mins, where=equals(job_runs.status, "SUCCESS"), over=by_job), 0),
              "shortest_ok"),
           AS(fill_null(sum_of(job_runs.duration_mins, over=by_job), 0), "job_total")),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X42

Map
- Sources: jobs (job_id, job_name); job_runs (job_id, duration_mins).
- Steps: none.
- Finals: jobs, with the columns job_id, job_name, runs, avg_mins, id_order.
- Typed over a formula: none.
- Marks:
  - runs is COUNTIF over another Table, so it is a LEFT JOIN to a count per job_id, wrapped in COALESCE(.., 0).
  - avg_mins is AVERAGEIF over another Table, so it is a LEFT JOIN to an average per job_id. AVERAGEIF is left NULL where nothing matches, and IFERROR(.., 0) becomes COALESCE(.., 0).
  - id_order is RANK.EQ(job_id, jobs[job_id], 1), which is RANK() OVER (ORDER BY job_id ASC), since 1 gives ascending order.
  - _xlfn. is removed.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(a.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins FROM <database>.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, count_rows, derived, equals, fill_null, rank, statement, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

runs_per_job = derived("runs_per_job", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the summary adds up all of them
    GROUP_BY(job_runs.job_id),
))
by_id = window(ORDER_BY=jobs.job_id)
s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(fill_null(runs_per_job.runs, 0), "runs"),
           AS(fill_null(runs_per_job.avg_mins, 0), "avg_mins"),
           AS(rank(over=by_id), "id_order")),
    FROM(jobs),
    LEFT_JOIN(runs_per_job, ON=equals(runs_per_job.job_id, jobs.job_id)),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X43

Map
- Sources: job_runs (run_id, job_id, status, duration_mins); jobs (job_id, team).
- Steps: none.
- Finals:
  - busy_teams, with the columns team, runs, shortest, avg_mins. It is an inner join, grouped by team, with HAVING for runs over 4.
  - statuses, with the columns job_id, status. It is a Table.Distinct alone, so SELECT DISTINCT.
- Typed over a formula: none.
- Marks:
  - Table.NestedJoin with Inner is a JOIN.
  - Table.Group: RowCount is COUNT(*), List.Min is MIN, List.Average is AVG.
  - Table.SelectRows on runs > 4 is HAVING COUNT(*) > 4.
  - The blank status in row 98 is kept as NULL in statuses. It is not read by a formula.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT j.team,
  COUNT(*) AS runs,
  MIN(r.duration_mins) AS shortest,
  AVG(r.duration_mins) AS avg_mins
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.team
HAVING COUNT(*) > 4
```

```sql
SELECT DISTINCT r.job_id, r.status
FROM <database>.job_runs r
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, HAVING, JOIN, SELECT, SELECT_DISTINCT, average_of, count_rows, equals, min_of, more_than, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

busy_teams = statement(
    SELECT(jobs.team, AS(count_rows(), "runs"), AS(min_of(job_runs.duration_mins), "shortest"),
           AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    GROUP_BY(jobs.team),
    HAVING(more_than(count_rows(), 4)),
)
statuses = statement(
    SELECT_DISTINCT(job_runs.job_id, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),  # every row, as the final keeps every row
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X44

Map
- Sources: job_runs (run_id, job_id); jobs (job_id, job_name, team); scheduler_runs (job_id).
- Steps: none.
- Finals:
  - jobs_with_runs, with the columns run_id, job_name. Its join is RightOuter, so it is a LEFT JOIN with the tables swapped.
  - never_scheduled, with the columns job_id, job_name, team. Its join is LeftAnti, so it is a LEFT JOIN with WHERE the joined key is NULL.
- Typed over a formula: none.
- Marks:
  - job_runs is joined on job_id only. There is no Keys row for job_runs, and the join is not on its whole key, so one job matches many runs and the Toolbox warns. The sheet keeps one row per run, so tell the user that many_matches=True is needed if the repeats are wanted, and do not add it without that.
  - Cache_warm has no runs, so its run_id is NULL in jobs_with_runs.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON r.job_id = j.job_id
```

```sql
SELECT j.job_id, j.job_name, j.team
FROM <database>.jobs j
LEFT JOIN <database>.scheduler_runs s ON j.job_id = s.job_id
WHERE s.job_id IS NULL
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import ANTI_JOIN, FROM, LEFT_JOIN, SELECT, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs
from references.<database>__scheduler_runs import scheduler_runs

jobs_with_runs = statement(
    SELECT(job_runs.run_id, jobs.job_name),
    FROM(jobs),
    LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id), reads_all_partitions=True),  # every row
)
never_scheduled = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team),
    FROM(jobs),
    ANTI_JOIN(scheduler_runs, ON=equals(scheduler_runs.job_id, jobs.job_id), reads_all_partitions=True),  # every day
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.

## X45

Map
- Sources: job_runs (run_id, job_id, dt, status); scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals:
  - run_days, with the columns run_id, dt. Its query is Table.Combine then Table.Distinct, so UNION.
  - matched, with the columns run_id, job_id, dt, status. Its join is FullOuter, so FULL OUTER JOIN.
- Typed over a formula: none.
- Marks:
  - matched: rows in only one of the two sources have NULL in the other side's columns, as M leaves them.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.dt
FROM <database>.job_runs r
UNION
SELECT s.run_id, s.dt
FROM <database>.scheduler_runs s
```

```sql
SELECT s.run_id, s.job_id, s.dt, r.status
FROM <database>.scheduler_runs s
FULL OUTER JOIN <database>.job_runs r ON s.run_id = r.run_id
```

Toolbox code, with `<database>` filled in as your database:

```python
from sqlglot_composer import AS, FROM, FULL_JOIN, SELECT, UNION, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

run_days = UNION(
    statement(SELECT(job_runs.run_id, job_runs.dt), FROM(job_runs, reads_all_partitions=True)),  # every row
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt),
              FROM(scheduler_runs, reads_all_partitions=True)),  # every row
)
matched = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt, job_runs.status),
    FROM(scheduler_runs, reads_all_partitions=True),  # every row
    FULL_JOIN(job_runs, ON=equals(job_runs.run_id, scheduler_runs.run_id), reads_all_partitions=True),  # every row
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Where the Hive and the checked code differ, the checked code wins.
