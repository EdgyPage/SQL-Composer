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
