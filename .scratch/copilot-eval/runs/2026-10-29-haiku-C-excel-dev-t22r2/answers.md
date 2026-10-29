date: 2026-10-29
arm: C
model: haiku
files: 423bc80

## X01

Sources: job_runs (run_id, job_id, duration_mins, dt).
Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours).
Steps: none.
Typed over: none. Marks: none. Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins, dt,
  duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

Toolbox code, by file 03:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(job_runs.duration_mins / 60, "duration_hours")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's sample: every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X02

Sources: job_runs (run_id, job_id, status, duration_mins).
Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag).
Steps: none.
Typed over: none.
Marks: the blank status in the row for run_id 98 is not read by a formula, so it stays as it is.
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF(duration_mins > 25 OR job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs
```

Toolbox code, by files 03 and 04:

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, any_of, equals, if_else, more_than, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           AS(if_else(all_of(more_than(job_runs.duration_mins, 10), equals(job_runs.job_id, 1)),
                      True, False), "slow_job1"),
           AS(if_else(any_of(more_than(job_runs.duration_mins, 25), equals(job_runs.job_id, 3)),
                      "check", "ok"), "flag")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's sample: every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X03

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs).
Steps: none.
Typed over: none.
Marks:
- blank: status in the row for run_id 98 is read by score, so it is wrapped as COALESCE(status, '').
- blank: avg_retry_secs in the row for run_id 98 is read by mins_per_retry and total_secs, so it is wrapped as COALESCE(avg_retry_secs, 0).
- `_xlfn.SWITCH` becomes CASE; the `_xlfn.` prefix is dropped.
- IFERROR(a / b, 0) becomes COALESCE(a / b, 0), as a divide by 0 is NULL in Hive.
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

Toolbox code, by files 03 and 11:

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, first_match, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt,
           AS(first_match([(equals(fill_null(job_runs.status, ""), "SUCCESS"), 1),
                           (equals(fill_null(job_runs.status, ""), "FAILED"), -1)],
                          otherwise=0), "score"),
           AS(fill_null(job_runs.duration_mins / fill_null(job_runs.avg_retry_secs, 0), 0),
              "mins_per_retry"),
           AS(job_runs.duration_mins * 60 + fill_null(job_runs.avg_retry_secs, 0), "total_secs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's sample: every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X04

Sources: jobs (job_id, job_name, team, region).
Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd).
Steps: none.
Typed over: none. Marks: none; there are no blanks in the sample.
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT job_id, job_name, team, region,
  CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-', region) AS code,
  LENGTH(job_name) AS name_length,
  ROUND(job_id / 3, 2) AS third,
  PMOD(job_id, 2) AS odd
FROM <database>.jobs
```

Toolbox code, by file 03:

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs, reads_all_partitions=True),  # a workbook's sample: every row
)
# code, name_length, third and odd use UPPER, SUBSTR, LENGTH, ROUND and PMOD, which
# files 03 to 05 don't name. Load file 10 to add them.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X05

Sources: job_runs (run_id, dt); region_costs (job_id, cost_cents, region, dt).
Finals: job_runs (run_id, dt, month, days_since); region_costs (job_id, cost_cents, region, dt, day).
Steps: none.
Typed over: none.
Marks:
- A date held as text: region_costs' dt is held as text, such as 20260911. It is converted with CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)); day is the same date built from the same pieces, DATE(LEFT, MID, RIGHT).
- DATEDIF(DATE(2026,9,1), dt, "d") becomes DATEDIFF(dt, '2026-09-01').
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT run_id, dt, MONTH(dt) AS month,
  DATEDIFF(dt, '2026-09-01') AS days_since
FROM <database>.job_runs
```

```sql
SELECT job_id, cost_cents, region,
  CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS dt,
  CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, -2)) AS day
FROM <database>.region_costs
```

Toolbox code, by file 03:

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__job_runs import job_runs
from references.ops__region_costs import region_costs

runs = statement(
    SELECT(job_runs.run_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's sample: every row
)
costs = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's sample: every row
)
# month, days_since, the text dt and day use MONTH, DATEDIFF, SUBSTR and CONCAT, which
# files 03 to 05 don't name. Load file 10 to add them.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X06

Sources: job_runs (run_id, job_id, duration_mins); jobs (job_id, job_name).
Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job).
Steps: none.
Typed over: none.
Marks: COUNTIFS over its own Table, one match, becomes COUNT(*) over the job_id partition, with COALESCE.
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code, by files 03 and 04:

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, count_rows, equals, statement, window
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

each_job = window(PARTITION_BY=job_runs.job_id)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, jobs.job_name,
           AS(count_rows(over=each_job), "runs_of_job")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's sample: every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X07

Sources: job_runs (run_id, job_id, status); jobs (job_id, team, region).
Finals: job_runs (run_id, job_id, status, team, region).
Steps: none.
Typed over: none.
Marks: VLOOKUP(..., 3, FALSE) reads column 3 of jobs, which is team; the exact match is kept, and both lookups come from one join on jobs.
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code, by files 03 and 04:

```python
from sqlglot_composer import FROM, LEFT_JOIN, SELECT, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, jobs.team, jobs.region),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's sample: every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X08

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: none.
Finals: by_job (job_id, total_mins, avg_retry, longest), a summary: its only typed column, job_id, is what its SUMIFS and AVERAGEIFS match on, so it is a GROUP BY of job_runs.
Typed over: none.
Marks: AVERAGEIFS becomes AVG and is left NULL, as AVG skips the blank avg_retry_secs in the row for run_id 98. SUMIFS and MAXIFS become SUM and MAX, each with COALESCE.
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT job_id,
  COALESCE(SUM(duration_mins), 0) AS total_mins,
  AVG(avg_retry_secs) AS avg_retry,
  COALESCE(MAX(duration_mins), 0) AS longest
FROM <database>.job_runs
GROUP BY job_id
```

Toolbox code, by file 03:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, average_of, fill_null, max_of, statement, sum_of
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id,
           AS(fill_null(sum_of(job_runs.duration_mins), 0), "total_mins"),
           AS(average_of(job_runs.avg_retry_secs), "avg_retry"),
           AS(fill_null(max_of(job_runs.duration_mins), 0), "longest")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's sample: every row
    GROUP_BY(job_runs.job_id),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X09

Sources: job_runs (run_id, job_id, duration_mins, avg_retry_secs); jobs (job_id, team).
Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost).
Steps: none.
Typed over: cost in the row for run_id 97 is typed as 100. Keys holds job_runs, run_id, so the row is matched on run_id: `CASE WHEN run_id = 97 THEN 100 ELSE ... END`.
Marks:
- blank: avg_retry_secs in the row for run_id 98 is read by cost, so it is wrapped as COALESCE(avg_retry_secs, 0).
- Parameters: rate is 0.5, written in as its value. Move rate into Parameters is not needed, as it already is one.
- team_mins, SUMIFS over its own Table on one match, becomes SUM over the team partition, with COALESCE.
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs, j.team,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.team), 0) AS team_mins,
  CASE WHEN r.run_id = 97 THEN 100
    ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5 END AS cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code, by files 03, 04, 05 and 11:

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, first_match, statement, sum_of, window
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

r = AS(job_runs, "r")
by_team = window(PARTITION_BY=jobs.team)
s = statement(
    SELECT(r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs, jobs.team,
           AS(fill_null(sum_of(r.duration_mins, over=by_team), 0), "team_mins"),
           AS(first_match([(equals(r.run_id, 97), 100)],
                          otherwise=(r.duration_mins * 60 + fill_null(r.avg_retry_secs, 0)) * 0.5),
              "cost")),
    FROM(r, reads_all_partitions=True),  # a workbook's sample: every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, r.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X10

Sources: job_runs (run_id, job_id, duration_mins, dt).
Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample).
Steps: none.
Typed over: hours in the row for run_id 103 is typed as 9. There is no Keys row for job_runs, so the row is matched on every typed column of the row: run_id, job_id, duration_mins and dt.
Marks: none.
Refused: sample is RAND(), so it is NULL AS sample.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24' THEN 9
    ELSE duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

Toolbox code, by files 03 and 11:

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, equals, first_match, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(first_match([(all_of(equals(job_runs.run_id, 103), equals(job_runs.job_id, 3),
                                   equals(job_runs.duration_mins, 30),
                                   equals(job_runs.dt, "2026-09-24")), 9)],
                          otherwise=job_runs.duration_mins / 60), "hours")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's sample: every row
)
# sample is RAND(), refused, so it is left out.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X11

Sources: job_runs (run_id, duration_mins).
Finals: job_runs (run_id, duration_mins, pick, scaled).
Steps: none.
Typed over: none.
Marks: none.
Refused:
- pick: INDIRECT (and ROW()) is refused, so NULL AS pick.
- scaled: it reads Summary!C2 by its address, a cell outside a Table that isn't a defined name, so NULL AS scaled.
Left alone: the bar chart on Summary, the Steps sheet, and the cell Summary!C2 (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  NULL AS pick,
  NULL AS scaled
FROM <database>.job_runs
```

Toolbox code, by file 03:

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's sample: every row
)
# pick and scaled are refused, so they are left out.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X12

Sources: job_runs (run_id, duration_mins).
Finals: job_runs (run_id, duration_mins, running, loop, with_tax).
Steps: none.
Typed over: none.
Marks: tax_rate is a defined name for Summary!B3, a cell outside a Table, so its value 0.2 is used in with_tax. Move tax_rate into Parameters.
Refused:
- running: OFFSET (and ROW()) is refused, so NULL AS running.
- loop: it reads its own column, so it is circular and NULL AS loop.
Left alone: the Summary sheet's cell B3 (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  NULL AS running,
  NULL AS loop,
  duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

Toolbox code, by file 03:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.ops__job_runs import job_runs

# tax_rate is Summary!B3, 0.2, used as its value. Move it into Parameters.
s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins * 0.2, "with_tax")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's sample: every row
)
# running and loop are refused, so they are left out.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X13

Sources: job_runs (run_id, job_id); jobs (job_id, job_name).
Finals: job_runs (run_id, job_id, name, doubled).
Steps: none.
Typed over: none.
Marks: VLOOKUP(job_id, jobs, 2, TRUE) is approximate; it is converted as an exact join on job_id, and the sample's ids match exactly, so the values are the same.
Refused: doubled calls the defined name DOUBLE, which holds a LAMBDA, so NULL AS doubled.
Left alone: the defined name DOUBLE (refused), the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, j.job_name AS name,
  NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code, by files 03 and 04:

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, AS(jobs.job_name, "name")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's sample: every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
)
# doubled calls a LAMBDA, refused, so it is left out.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X14

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: job_runs (hours, duration_mins / 60), a step because by_job reads its formula column hours.
Finals: by_job (job_id, total_hours), a summary: its only typed column, job_id, is what its SUMIFS matches on, so it is a GROUP BY of the step.
Typed over: none.
Marks: SUMIFS becomes SUM with COALESCE.
Refused: none.
Left alone: the PivotTable on sheet Pivot, the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
WITH job_runs AS (
  SELECT job_id, duration_mins / 60 AS hours
  FROM <database>.job_runs
)
SELECT job_id, COALESCE(SUM(hours), 0) AS total_hours
FROM job_runs
GROUP BY job_id
```

Toolbox code, by files 03 and 11:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, derived, fill_null, statement, sum_of
from references.ops__job_runs import job_runs

timed = derived("timed", statement(
    SELECT(job_runs.job_id, AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's sample: every row
))
s = statement(
    SELECT(timed.job_id, AS(fill_null(sum_of(timed.hours), 0), "total_hours")),
    FROM(timed),
    GROUP_BY(timed.job_id),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X15

Sources: tblRuns (`<run_id>`, `<job_id>`, `<duration_mins>`), where `<run_id>` stands for the header "Run ID", `<job_id>` for "Job ID" and `<duration_mins>` for "Duration (mins)".
Finals: tblRuns (`<run_id>`, `<job_id>`, `<duration_mins>`, hours).
Steps: none.
Typed over: none.
Marks: the header names are not plain, so each is written in snake case in brackets, to fill in.
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`.

```sql
SELECT <run_id>, <job_id>, <duration_mins>,
  <duration_mins> / 60 AS hours
FROM <database>.tblRuns
```

Toolbox code, by file 03, with the Table reference's name to fill in:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.ops__<tbl_runs> import <tbl_runs>  # fill in the Table reference for tblRuns

s = statement(
    SELECT(<tbl_runs>.<run_id>, <tbl_runs>.<job_id>, <tbl_runs>.<duration_mins>,
           AS(<tbl_runs>.<duration_mins> / 60, "hours")),
    FROM(<tbl_runs>, reads_all_partitions=True),  # a workbook's sample: every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X16

Sources: job_runs (run_id, job_id, duration_mins).
Steps: none.
Finals: long_runs (run_id, job_id, minutes, hours), the Table loaded by the Power Query "long_runs".
Typed over: none.
Marks: Table.SelectRows(duration_mins > 15) becomes WHERE; Table.RenameColumns becomes AS minutes; Table.AddColumn becomes duration_mins / 60 AS hours.
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins AS minutes,
  duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

Toolbox code, by files 03 and 11:

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, more_than, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id,
           AS(job_runs.duration_mins, "minutes"),
           AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(more_than(job_runs.duration_mins, 15)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X17

Sources: job_runs (job_id, status, duration_mins).
Steps: ok_runs, the connection-only query, which the query loading ok_by_job reads, so it is a CTE.
Finals: ok_by_job (job_id, runs, total_mins), the Table loaded by the Power Query "ok_by_job".
Typed over: none.
Marks: Table.RowCount becomes COUNT(*); List.Sum becomes SUM. The filter on status = "SUCCESS" is a WHERE, and the blank status in the row for run_id 98 is skipped by it, as M does.
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
WITH ok_runs AS (
  SELECT job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

Toolbox code, by files 03 and 11:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived, equals, statement, sum_of
from references.ops__job_runs import job_runs

ok_runs = derived("ok_runs", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
))
s = statement(
    SELECT(ok_runs.job_id, AS(count_rows(), "runs"), AS(sum_of(ok_runs.duration_mins), "total_mins")),
    FROM(ok_runs),
    GROUP_BY(ok_runs.job_id),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X18

Sources: job_runs (run_id, job_id, duration_mins); jobs (job_id, job_name).
Steps: none.
Finals: top_runs (run_id, job_name, duration_mins), the Table loaded by the Power Query "top_runs".
Typed over: none.
Marks: NestedJoin with LeftOuter becomes LEFT JOIN; Table.Sort descending becomes ORDER BY ... DESC; FirstN(3) becomes LIMIT 3. The ties at 30 are both inside the top 3, so the order among them does not change the rows.
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC
LIMIT 3
```

Toolbox code, by files 03 and 04:

```python
from sqlglot_composer import FROM, LEFT_JOIN, LIMIT, ORDER_BY, SELECT, descending, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, jobs.job_name, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
    ORDER_BY(descending(job_runs.duration_mins)),
    LIMIT(3),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X19

Sources: scheduler_runs (run_id, job_id, dt); job_runs, read from the Sql.Database("dwh01", "ops") as the table it names: `<database>.job_runs`.
Steps: none.
Finals: all_runs (run_id, job_id, dt), the Table loaded by the Power Query "all_runs", the two selections stacked with Table.Combine as UNION ALL.
Typed over: none.
Marks: Sql.Database is not a workbook source, so the table it names, job_runs, is used. Check that `<database>` is the ops database on dwh01.
Refused: none.
Left out: the connection-only query "holidays", which reads Web.Contents (a web source) and which nothing reads.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt
FROM <database>.job_runs
```

Toolbox code, by files 05 and 03:

```python
from sqlglot_composer import FROM, SELECT, UNION_ALL, statement
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

scheduled = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's sample: every row
)
warehouse = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),
)
s = UNION_ALL(scheduled, warehouse)
# Check that the Table reference job_runs is ops.job_runs on dwh01.
# holidays reads a web source, so it is left out.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X20

Sources: run_alerts (run_id, severity).
Steps: none.
Finals: alert_pivot (run_id, high, low), the Table loaded by the Power Query "alert_pivot".
Typed over: none.
Marks: Table.Pivot with List.Sum of n = 1 becomes SUM(CASE WHEN severity = 'high' THEN 1 END) AS high and the same for low, NULL where none, as M leaves it. The pivot's columns are now fixed at high and low, the values in the sample.
Refused: none.
Left alone: the Steps sheet (cells outside a Table).
Fill in: `<database>`.

```sql
SELECT run_id,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
WHERE run_id = 97 OR run_id = 101
GROUP BY run_id
```

Toolbox code, by files 03 and 11:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, any_of, count_rows, equals, statement
from references.ops__run_alerts import run_alerts

s = statement(
    SELECT(run_alerts.run_id,
           AS(count_rows(where=equals(run_alerts.severity, "high")), "high"),
           AS(count_rows(where=equals(run_alerts.severity, "low")), "low")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's sample: every row
    WHERE(any_of(equals(run_alerts.run_id, 97), equals(run_alerts.run_id, 101))),
    GROUP_BY(run_alerts.run_id),
)
# count_rows gives 0 where a severity has no row; the Hive gives NULL there, as M does.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X41

Map
- Sources: job_runs (run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total).
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins,
  RANK() OVER (ORDER BY r.duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN r.status = 'SUCCESS' THEN r.duration_mins END) OVER (PARTITION BY r.job_id), 0) AS shortest_ok,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id), 0) AS job_total
FROM <database>.job_runs r
```

Marks
- status is blank in run 98. It is read inside the MINIFS condition, so it is not wrapped; that row matches no SUCCESS, as Excel does.
- shortest_ok and job_total are wrapped in COALESCE(..., 0), as Excel gives 0 where nothing matches.

## X42

Map
- Sources: job_runs (job_id, duration_mins); jobs (job_id, job_name).
- Steps: none.
- Finals: jobs (job_id, job_name, runs, avg_mins, id_order).
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS runs, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) c ON j.job_id = c.job_id
```

Marks
- avg_mins is IFERROR(AVERAGEIF(...), 0), so it is COALESCE(..., 0). No blank is read by a formula in the sample.
- id_order is RANK.EQ with 1 as its third argument, so it ranks ascending.

## X43

Map
- Sources: job_runs (job_id, status, duration_mins); jobs (job_id, team).
- Steps: none.
- Finals: busy_teams (team, runs, shortest, avg_mins), the Table loaded by its Power Query; statuses (job_id, status), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

busy_teams:

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

statuses:

```sql
SELECT DISTINCT r.job_id, r.status
FROM <database>.job_runs r
```

Marks
- The inner join to jobs is the Power Query's Table.NestedJoin with JoinKind.Inner, so a run with no job is dropped.
- statuses keeps the blank status of job 2 as a NULL row, as Table.Distinct does.

## X44

Map
- Sources: job_runs (run_id, job_id); jobs (job_id, job_name, team); scheduler_runs (job_id).
- Steps: none.
- Finals: jobs_with_runs (run_id, job_name), the Table loaded by its Power Query; never_scheduled (job_id, job_name, team), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

jobs_with_runs:

```sql
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON j.job_id = r.job_id
```

never_scheduled:

```sql
SELECT j.job_id, j.job_name, j.team
FROM <database>.jobs j
LEFT JOIN <database>.scheduler_runs s ON j.job_id = s.job_id
WHERE s.job_id IS NULL
```

Marks
- The RightOuter join keeps every job, as LEFT JOIN with the tables swapped does. cache_warm (job 4) has no run, so its run_id is NULL, as in the sample.
- never_scheduled is the LeftAnti join: jobs' columns only.

## X45

Map
- Sources: job_runs (run_id, dt, status); scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: run_days (run_id, dt), the Table loaded by its Power Query; matched (run_id, job_id, dt, status), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

run_days:

```sql
SELECT run_id, dt FROM <database>.job_runs
UNION
SELECT run_id, dt FROM <database>.scheduler_runs
```

matched:

```sql
SELECT s.run_id, s.job_id, s.dt, r.status
FROM <database>.scheduler_runs s
FULL OUTER JOIN <database>.job_runs r ON s.run_id = r.run_id
```

Marks
- run_days is UNION, not UNION ALL, because Table.Distinct wraps Table.Combine.
- matched is a FULL OUTER JOIN. Run 99, only in job_runs, has NULL run_id, job_id and dt; run 100, only in scheduler_runs, has a NULL status, as in the sample.

## X51

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins).
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.dt,
  COALESCE(COUNT(CASE WHEN r.duration_mins > 15 THEN 1 END) OVER (PARTITION BY r.job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (r.status <> 'SUCCESS' OR r.status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(r.status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY r.job_id), 0) AS failed_in_job,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs r
```

Marks
- not_ok: "<>SUCCESS" is written as (status <> 'SUCCESS' OR status IS NULL), so the blank status in run 98 is counted, as Excel counts a blank there. status is not wrapped in COALESCE, as it sits inside a COUNTIFS form.
- failed_in_job: "*ail*" is LOWER(status) LIKE '%ail%', as Excel ignores case.
- running_mins: the running total within each job, with ties on dt included, as Excel's "<=" does.

## X52

Map
- Sources: job_runs (run_id, job_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job).
- Total Row: job_runs (Total Row), a query of its own: one row, the total of duration_mins and the total of share, in order, with no label.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

job_runs:

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  r.duration_mins / SUM(r.duration_mins) OVER () AS share,
  r.duration_mins - AVG(r.duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY r.job_id ORDER BY r.duration_mins DESC) AS rank_in_job
FROM <database>.job_runs r
```

job_runs (Total Row):

```sql
WITH shares AS (
  SELECT r.duration_mins,
    r.duration_mins / SUM(r.duration_mins) OVER () AS share
  FROM <database>.job_runs r
)
SELECT SUM(duration_mins) AS duration_mins,
  SUM(share) AS share
FROM shares
```

Marks
- whole-column references in share and vs_avg are OVER (), as the Excel formulas use the whole column.
- rank_in_job: COUNTIFS(... ">" ...) + 1 is RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC), so tied durations share a rank, as Excel does.

## X53

Map
- Sources: job_runs (job_id, duration_mins).
- Steps: none.
- Finals: by_job (job_id, total_mins, runs, longest). by_job is a summary, since its only typed column, job_id, is what its SUMIFS and COUNTIFS match on, so it is a GROUP BY of job_runs.
- Total Row: no query of its own. Its totals add up SUMs and COUNTs and take the MAX, so the summary's query ends GROUP BY ... WITH ROLLUP. The total is the row whose job_id is NULL.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT r.job_id,
  COALESCE(SUM(r.duration_mins), 0) AS total_mins,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(MAX(r.duration_mins), 0) AS longest
FROM <database>.job_runs r
GROUP BY r.job_id WITH ROLLUP
```

Marks
- The summary's rows are the job_ids that have runs in job_runs. A job with no runs gets no row, where Excel would show 0 for it.

## X54

Map
- Sources: job_runs (run_id, dt); scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label); scheduler_runs (run_id, job_id, dt). scheduler_runs has no formulas and nothing reads it, so its final is the table as it stands.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

job_runs:

```sql
SELECT r.run_id, r.dt,
  LAST_DAY(r.dt) AS month_end,
  ADD_MONTHS(r.dt, 1) AS a_month_on,
  DATE_ADD(r.dt, 7) AS due,
  CAST(NEXT_DAY(DATE_ADD(r.dt, 7 * -1), 'MO') AS STRING) AS week_of,
  CAST(TRUNC(r.dt, 'MM') AS STRING) AS month_of,
  DAYOFWEEK(r.dt) AS weekday,
  DATE_FORMAT(r.dt, 'yyyy-MM') AS label
FROM <database>.job_runs r
```

scheduler_runs:

```sql
SELECT s.run_id, s.job_id, s.dt
FROM <database>.scheduler_runs s
```

Marks
- a_month_on: EDATE is ADD_MONTHS, which keeps a month's end at the month's end, as EDATE does.
- week_of and month_of are cast to text, as the Hive form writes them.

## X55

Map
- Sources: jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens).
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team, j.region,
  INITCAP(REPLACE(j.job_name, '_', ' ')) AS title,
  CONCAT_WS('/', j.team, j.region) AS tag,
  CONCAT(j.region, '-', j.job_id) AS code,
  INSTR(LOWER(j.job_name), LOWER('SYNC')) > 0 AS has_sync,
  CAST(CONCAT(j.job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs j
```

Marks
- None: no blank is read in the sample. TEXTJOIN with TRUE is CONCAT_WS, which skips NULLs.

## X56

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs); scheduler_runs (run_id, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on).
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  r.status IS NULL AS no_status,
  FLOOR(r.duration_mins / 7) AS weeks,
  GREATEST(r.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(r.duration_mins) OVER () AS spread,
  SUM(r.duration_mins * COALESCE(r.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(sr.dt, 'unscheduled') AS scheduled_on
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs sr ON r.run_id = sr.run_id
```

Marks
- avg_retry_secs is blank in run 98, and weighted reads it, so it is wrapped: COALESCE(avg_retry_secs, 0) (blank).
- scheduled_on: XLOOKUP is a LEFT JOIN on run_id, and its fourth argument is COALESCE. Run 99 is not in scheduler_runs, so it reads "unscheduled".
- weeks: INT is FLOOR.

## X57

Map
- Sources: job_runs (run_id, job_id, status, avg_retry_secs); jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: picked (run_id, job_id, status, avg_retry_secs, status_lc), the Table loaded by its Power Query; ran_jobs (job_id, job_name, team, region), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

picked:

```sql
SELECT r.run_id, r.job_id, r.status,
  COALESCE(r.avg_retry_secs, 0) AS avg_retry_secs,
  LOWER(r.status) AS status_lc
FROM <database>.job_runs r
WHERE r.job_id IN (1, 2) AND (r.status IS NULL OR r.status LIKE 'S%')
```

ran_jobs:

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r ON r.job_id = j.job_id
WHERE j.job_name LIKE '%a%'
```

Marks
- avg_retry_secs is blank in run 98, and Table.ReplaceValue sets it to 0: COALESCE(avg_retry_secs, 0) (blank).
- Text.StartsWith is LIKE 'S%' with the case kept. The M test "status = null" is status IS NULL, so the blank row stays; status_lc is NULL there, as Text.Lower gives null.
- List.Contains(Runs[job_id], [job_id]) is a LEFT SEMI JOIN, which keeps jobs' columns only.

## X58

Map
- Sources: job_runs (run_id, job_id, duration_mins, avg_retry_secs, dt); jobs (job_id); region_budgets (region); scheduler_runs (run_id, job_id).
- Steps: none.
- Finals: job_regions (job_id, region); numbered (run_id, dt, duration_mins, n); days_per_job (job_id, days); unrun (run_id, job_id); measures (run_id, measure, amount). Each is a Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

job_regions:

```sql
WITH regions AS (
  SELECT DISTINCT region FROM <database>.region_budgets
)
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN regions r
```

numbered:

```sql
SELECT r.run_id, r.dt, r.duration_mins,
  ROW_NUMBER() OVER (ORDER BY r.duration_mins DESC, r.run_id ASC) AS n
FROM <database>.job_runs r
```

days_per_job:

```sql
SELECT r.job_id, COUNT(DISTINCT r.dt) AS days
FROM <database>.job_runs r
GROUP BY r.job_id
```

unrun:

```sql
SELECT DISTINCT s.run_id, s.job_id
FROM <database>.scheduler_runs s
LEFT JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.job_id = r.job_id
WHERE r.run_id IS NULL
```

measures:

```sql
SELECT r.run_id, 'duration_mins' AS measure, r.duration_mins AS amount
FROM <database>.job_runs r
WHERE r.duration_mins IS NOT NULL
UNION ALL
SELECT r.run_id, 'avg_retry_secs' AS measure, r.avg_retry_secs AS amount
FROM <database>.job_runs r
WHERE r.avg_retry_secs IS NOT NULL
```

Marks
- days_per_job: the sort by days descending has no FirstN or index after it, so there is no ORDER BY. The order was dropped.
- measures: the blank avg_retry_secs of run 98 is dropped, as M drops a null there.
- job_regions is a CROSS JOIN of every job with each distinct region.

## X67

Map
- Sources: job_runs (run_id, job_id, duration_mins, dt); jobs (job_id, team); run_alerts (run_id).
- Steps: job_runs, the Table's formula columns team, alerts and running_mins. It is read by by_team and noisy_runs, so each of their queries has it as a CTE.
- Finals: by_team (team, total_mins, alerted_runs); noisy_runs (run_id, team, alerts, running_mins).
- Total Row: by_team (Total Row) is the WITH ROLLUP row, whose team is NULL. It needs no query of its own.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

by_team:

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
)
SELECT team,
  COALESCE(SUM(duration_mins), 0) AS total_mins,
  COALESCE(COUNT(CASE WHEN alerts > 0 THEN 1 END), 0) AS alerted_runs
FROM job_runs
GROUP BY team WITH ROLLUP
```

noisy_runs:

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
)
SELECT run_id, team, alerts, running_mins
FROM job_runs
WHERE alerts >= 2
```

Marks
- alerts: COUNTIF over run_alerts is a LEFT JOIN to a count per run, wrapped in COALESCE(..., 0).
- running_mins: the running total within each job, ties on dt included.
- by_team: web has no run in job_runs, so it gets no row, where Excel would show 0 for it.

## X68

Map
- Sources: job_runs (run_id, job_id, duration_mins); jobs (job_id, job_name); region_budgets (job_id, region).
- Steps: base, the connection-only Power Query. by_region and top_runs read it, so each of their queries has it as a CTE. It is not loaded to a Table.
- Finals: by_region (region, total_mins, runs, share), the Table loaded by its Power Query; top_runs (run_id, job_name, region), the Table loaded by its Power Query.
- Total Row: by_region (Total Row), a query of its own: one row, the total of total_mins, with no label.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

by_region:

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT g.region, g.total_mins, g.runs,
  g.total_mins / SUM(g.total_mins) OVER () AS share
FROM (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) g
```

by_region (Total Row):

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT SUM(g.total_mins) AS total_mins
FROM (
  SELECT region, SUM(duration_mins) AS total_mins
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) g
```

top_runs:

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT run_id, job_name, region
FROM base
ORDER BY duration_mins DESC, run_id ASC
LIMIT 2
```

Marks
- The Total Row is not a summary, so it gets its own query. Its total is SUM over the by_region rows.
- top_runs sorts by duration_mins descending, then run_id ascending for ties, and takes the first 2.

## X71

Map
- Sources: job_runs (run_id, job_id, status, duration_mins).
- Steps: ok_runs, the Power Query's rows with its formula column hours. It is read by ok_by_job, so ok_by_job's query has it as a CTE.
- Finals: ok_by_job (job_id, total_mins), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
WITH ok_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins,
    r.duration_mins / 60 AS hours
  FROM <database>.job_runs r
  WHERE r.status = 'SUCCESS'
)
SELECT job_id, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

Marks
- None. The blank status of run 98 is not SUCCESS, so it drops out, as the M equality does.

## X72

Map
- Sources: job_runs (job_id, duration_mins); jobs (job_id, job_name, team).
- Steps: jobs, the Table's formula columns runs and total. It is read by by_team and busy_jobs, so each of their queries has it as a CTE.
- Finals: by_team (team, team_total), a summary: its only typed column, team, is what its SUMIFS matches, so it is a GROUP BY of jobs. busy_jobs (job_id, job_name, runs), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

by_team:

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(c.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total
    FROM <database>.job_runs
    GROUP BY job_id
  ) c ON j.job_id = c.job_id
)
SELECT team, COALESCE(SUM(total), 0) AS team_total
FROM jobs
GROUP BY team
```

busy_jobs:

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(c.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total
    FROM <database>.job_runs
    GROUP BY job_id
  ) c ON j.job_id = c.job_id
)
SELECT job_id, job_name, runs
FROM jobs
WHERE runs >= 3
```

Marks
- The COUNTIF and SUMIF over job_runs are one LEFT JOIN to a count and a sum per job, each wrapped in COALESCE(..., 0).

## X75

Map
- Sources: job_runs (run_id, dt, duration_mins).
- Steps: long_runs, the Power Query's rows with its formula column over. It is read by long_per_day, so that query has it as a CTE.
- Finals: long_per_day (dt, runs), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
WITH long_runs AS (
  SELECT r.run_id, r.dt, r.duration_mins,
    r.duration_mins - 15 AS over
  FROM <database>.job_runs r
  WHERE r.duration_mins >= 15
)
SELECT dt, COUNT(*) AS runs
FROM long_runs
GROUP BY dt
```

Marks
- None. Run 98, at exactly 15 minutes, is kept by >= 15, as M keeps it.

## X76

Map
- Sources: jobs (job_id, job_name, team); job_runs (run_id, job_id, duration_mins).
- Steps: finance_jobs, the Power Query's rows with its formula column label. It is read by finance_runs, so that query has it as a CTE.
- Finals: finance_runs (run_id, job_name, duration_mins), the Table loaded by its Power Query.
- Typed over a formula: none. Parameters and Keys: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
WITH finance_jobs AS (
  SELECT j.job_id, j.job_name,
    UPPER(j.job_name) AS label
  FROM <database>.jobs j
  WHERE j.team = 'finance'
)
SELECT r.run_id, f.job_name, r.duration_mins
FROM <database>.job_runs r
JOIN finance_jobs f ON r.job_id = f.job_id
```

Marks
- None. The NestedJoin is JoinKind.Inner, so it is a JOIN, and a run whose job is not in finance is dropped.
