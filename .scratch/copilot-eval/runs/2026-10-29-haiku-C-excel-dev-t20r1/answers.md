date: 2026-10-29
arm: C
model: haiku
files: 10de2a9

## X01

Sources: job_runs (run_id, job_id, duration_mins, dt, typed).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours). Its one calculation is duration_hours = duration_mins / 60.
Parameters and Keys: neither; both are empty, so there is no Keys row.
Typed over: none, so no conversion of typed values is needed.
Marks: dt holds dates as dates ('2026-09-23'), so no text date conversion.
Refusals: none.
Left alone: the Steps sheet, which holds no Table.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins, dt,
  duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(job_runs.duration_mins / 60, "duration_hours")),
    FROM(job_runs),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. If job_runs is partitioned on dt, the Python needs a bound on dt, as file 03 shows.

## X02

Sources: job_runs (run_id, job_id, status, duration_mins, typed).
Steps: none.
Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag).
- slow_job1 = AND(duration_mins > 10, job_id = 1), as it is.
- flag = IF(OR(duration_mins > 25, job_id = 3), "check", "ok"), as it is, with the strings in single quotes.
Parameters and Keys: neither; both empty. Typed over: none.
Marks: status is blank in row 98, but no formula reads status, so it stays NULL and is not wrapped.
Refusals: none.
Left alone: the Steps sheet, which holds no Table.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF(duration_mins > 25 OR job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, any_of, equals, if_else, more_than, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           # slow_job1 (AND as a value) needs file 10, Hive functions, in a new chat
           AS(if_else(any_of(more_than(job_runs.duration_mins, 25), equals(job_runs.job_id, 3)),
                      "check", "ok"), "flag")),
    FROM(job_runs),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. If job_runs is partitioned on dt, bound it as file 03 shows.

## X03

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, typed).
Steps: none.
Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs).
- score = SWITCH(status, "SUCCESS", 1, "FAILED", -1, 0), converted as a CASE on status.
- mins_per_retry = IFERROR(duration_mins / avg_retry_secs, 0), converted as COALESCE(a / b, 0).
- total_secs = duration_mins * 60 + avg_retry_secs.
Parameters and Keys: neither; both empty. Typed over: none.
Marks:
- status is blank in row 98 and score reads it, so it is wrapped as COALESCE(status, '') for score. Blank.
- avg_retry_secs is blank in row 98 and two formulas read it, so it is wrapped as COALESCE(avg_retry_secs, 0) in both. Blank.
Refusals: none.
Left alone: the Steps sheet, which holds no Table.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt,
           AS(if_else(equals(fill_null(job_runs.status, ""), "SUCCESS"), 1,
                      if_else(equals(fill_null(job_runs.status, ""), "FAILED"), -1, 0)), "score"),
           # mins_per_retry (IFERROR on a divide) needs file 10, Hive functions, in a new chat
           AS(job_runs.duration_mins * 60 + fill_null(job_runs.avg_retry_secs, 0), "total_secs")),
    FROM(job_runs),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. If job_runs is partitioned on dt, bound it as file 03 shows.

## X04

Sources: jobs (job_id, job_name, team, region, typed).
Steps: none.
Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd). Nothing reads jobs, so it is a final.
- code = UPPER(LEFT(job_name, 3)) & "-" & region, converted with LEFT as SUBSTR and & as CONCAT.
- name_length = LEN(job_name), as LENGTH.
- third = ROUND(job_id / 3, 2), as it is.
- odd = MOD(job_id, 2), as PMOD.
Parameters and Keys: neither; both empty. Typed over: none.
Marks: none; no blank in a column a formula reads.
Refusals: none.
Fill in: `<database>`.

```sql
SELECT job_id, job_name, team, region,
  CONCAT(CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-'), region) AS code,
  LENGTH(job_name) AS name_length,
  ROUND(job_id / 3, 2) AS third,
  PMOD(job_id, 2) AS odd
FROM <database>.jobs
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
)
# code, name_length, third and odd need file 10, Hive functions, in a new chat
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X05

Sources: job_runs (run_id, dt, typed) and region_costs (job_id, cost_cents, region, dt, typed).
Steps: none.
Finals:
- job_runs (run_id, dt, month, days_since).
- region_costs (job_id, cost_cents, region, dt, day).
Parameters and Keys: neither; both empty. Typed over: none.
Marks:
- region_costs dt is held as text (20260911, not a date). Day is converted with the text date form, CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)).
- region_costs cost_cents is blank in row 29. No formula reads it, so it stays NULL.
- job_runs dt holds dates, so no conversion there.
- days_since = DATEDIF(DATE(2026,9,1), dt, "d"), converted as DATEDIFF(dt, '2026-09-01').
Refusals: none.
Fill in: `<database>`.

```sql
SELECT run_id, dt,
  MONTH(dt) AS month,
  DATEDIFF(dt, '2026-09-01') AS days_since
FROM <database>.job_runs
```

```sql
SELECT job_id, cost_cents, region, dt,
  CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS day
FROM <database>.region_costs
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__job_runs import job_runs
from references.ops__region_costs import region_costs

s_runs = statement(
    SELECT(job_runs.run_id, job_runs.dt),
    FROM(job_runs),
)
s_costs = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region, region_costs.dt),
    FROM(region_costs),
)
# month, days_since and day need file 10, Hive functions, in a new chat
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X06

Sources: job_runs (run_id, job_id, duration_mins, typed) and jobs (job_id, job_name, team, region, typed).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job). job_runs is not a summary, because it has typed columns beyond its match key. jobs is read by job_runs, so it is not a final.
- job_name = XLOOKUP(job_id, jobs[job_id], jobs[job_name]): a LEFT JOIN of jobs on job_id, then job_name.
- runs_of_job = COUNTIFS(job_runs[job_id], job_id): over its own Table, COUNT(*) OVER (PARTITION BY job_id), with COALESCE.
Parameters and Keys: neither; both empty. Typed over: none.
Marks: COUNTIFS converted to COUNT(*) with COALESCE, as for every COUNTIFS.
Refusals: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, count_rows, equals, statement, window
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

each_job = window(PARTITION_BY=job_runs.job_id)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, jobs.job_name,
           AS(count_rows(over=each_job), "runs_of_job")),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. If job_runs is partitioned on dt, bound it as file 03 shows.

## X07

Sources: job_runs (run_id, job_id, status, typed) and jobs (job_id, job_name, team, region, typed).
Steps: none.
Finals: job_runs (run_id, job_id, status, team, region).
- team = VLOOKUP(job_id, jobs, 3, FALSE): the third column of jobs, team. Exact.
- region = INDEX(jobs[region], MATCH(job_id, jobs[job_id], 0)): exact.
Both match on job_id, so one LEFT JOIN of jobs serves both columns.
Parameters and Keys: neither; both empty. Typed over: none.
Marks: both lookups are exact, so no approximate match to flag. status is blank in row 98, but no formula reads it, so it stays NULL.
Refusals: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import FROM, LEFT_JOIN, SELECT, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, jobs.team, jobs.region),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. If job_runs is partitioned on dt, bound it as file 03 shows.

## X08

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, typed).
Steps: none.
Finals: by_job (job_id, total_mins, avg_retry, longest). by_job's only typed column is job_id, the match key of its SUMIFS, AVERAGEIFS and MAXIFS, so it is a summary: a GROUP BY job_id of job_runs, one query.
- total_mins = SUMIFS(duration_mins, job_id): SUM, with COALESCE.
- avg_retry = AVERAGEIFS(avg_retry_secs, job_id): AVG, left NULL.
- longest = MAXIFS(duration_mins, job_id): MAX, with COALESCE.
Parameters and Keys: neither; both empty. Typed over: none.
Marks: the blank avg_retry_secs in row 98 is skipped by AVG, as AVERAGEIFS skips it, so it is not wrapped. _xlfn. prefixes are dropped.
Refusals: none.
Left alone: the Steps sheet, which holds no Table.
Fill in: `<database>`.

```sql
SELECT job_id,
  COALESCE(SUM(duration_mins), 0) AS total_mins,
  AVG(avg_retry_secs) AS avg_retry,
  COALESCE(MAX(duration_mins), 0) AS longest
FROM <database>.job_runs
GROUP BY job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, average_of, fill_null, max_of, statement, sum_of
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id,
           AS(fill_null(sum_of(job_runs.duration_mins), 0), "total_mins"),
           AS(average_of(job_runs.avg_retry_secs), "avg_retry"),
           AS(fill_null(max_of(job_runs.duration_mins), 0), "longest")),
    FROM(job_runs),
    GROUP_BY(job_runs.job_id),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. If job_runs is partitioned on dt, bound it as file 03 shows.

## X09

Sources: job_runs (run_id, job_id, duration_mins, avg_retry_secs, typed) and jobs (job_id, job_name, team, region, typed).
Steps: with_team (a CTE). It joins jobs to job_runs on job_id to give team, because team_mins reads team, and a window cannot read a column computed in the same SELECT.
Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost).
- team = XLOOKUP(job_id, jobs[job_id], jobs[team]): the LEFT JOIN, then team.
- team_mins = SUMIFS(duration_mins, team, team): over its own Table, SUM(duration_mins) OVER (PARTITION BY team), with COALESCE.
- cost = (duration_mins * 60 + avg_retry_secs) * XLOOKUP("rate", ...) = (duration_mins * 60 + avg_retry_secs) * 0.5. The rate is the Parameters value 0.5.
Parameters: rate = 0.5, read as the value 0.5 in cost. Parameters is neither a source nor a final.
Keys: job_runs, run_id.
Typed over: cost in run 97 is typed as 100. Matched on Keys column run_id: CASE WHEN run_id = 97 THEN 100.
Marks:
- avg_retry_secs is blank in row 98, and cost reads it, so it is wrapped as COALESCE(avg_retry_secs, 0). Blank.
Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
WITH with_team AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT run_id, job_id, duration_mins, avg_retry_secs, team,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY team), 0) AS team_mins,
  CASE WHEN run_id = 97 THEN 100
    ELSE (duration_mins * 60 + COALESCE(avg_retry_secs, 0)) * 0.5
  END AS cost
FROM with_team
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, statement, sum_of, window
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

by_team = window(PARTITION_BY=jobs.team)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.avg_retry_secs,
           jobs.team,
           AS(sum_of(job_runs.duration_mins, over=by_team), "team_mins")),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
# cost (the typed 100 on run 97, the blank avg_retry_secs, and the rate 0.5) needs file 10, Hive functions, in a new chat
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. Move the rate into Parameters if the Table reference has it there. If job_runs is partitioned on dt, bound it as file 03 shows.

## X10

Sources: job_runs (run_id, job_id, duration_mins, dt, typed).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample).
- hours = duration_mins / 60.
- sample = RAND(), refused.
Keys: there is no Keys row for job_runs (the Keys sheet is empty). So the typed-over value is matched on every typed column of its row: run_id 103, job_id 3, duration_mins 30, dt '2026-09-24'. Say so.
Typed over: hours is typed as 9 in run 103 (its formula would give 0.5).
Marks: none beyond the typed value.
Refusals: sample = RAND() is refused, NULL AS sample. RAND is on the refused list.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24' THEN 9
    ELSE duration_mins / 60
  END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt),
    FROM(job_runs),
)
# hours (with the typed 9 on run 103) needs file 10, Hive functions, in a new chat; sample is refused and left out
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. If job_runs is partitioned on dt, bound it as file 03 shows.

## X11

Sources: job_runs (run_id, duration_mins, typed).
Steps: none.
Finals: job_runs (run_id, duration_mins, pick, scaled).
Refusals:
- pick = INDIRECT("B"&ROW()): INDIRECT is refused, and ROW() hangs on the row order. NULL AS pick.
- scaled = duration_mins * Summary!$C$2: C2 on the Summary sheet is a cell outside a Table, and it is not a defined name. Refused. NULL AS scaled.
Left alone: the bar chart on the Summary sheet, and the cell Summary!C2, which is outside a Table.
Parameters and Keys: neither; both empty. Typed over: none.
Fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  NULL AS pick,
  NULL AS scaled
FROM <database>.job_runs
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs),
)
# pick and scaled are refused, so they are left out
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. If job_runs is partitioned on dt, bound it as file 03 shows.

## X12

Sources: job_runs (run_id, duration_mins, typed).
Steps: none.
Finals: job_runs (run_id, duration_mins, running, loop, with_tax).
Refusals:
- running = SUM(OFFSET(...)): OFFSET is refused, and it hangs on the row order. NULL AS running.
- loop = loop + 1: the formula reads its own column, which is circular. NULL AS loop.
Defined name: tax_rate = Summary!$B$3, holding 0.2. It is a defined name for a cell outside a Table, so with_tax uses its value, 0.2, and you should move it into Parameters.
- with_tax = duration_mins * 0.2.
Parameters and Keys: neither; both empty. Typed over: none.
Left alone: the cell Summary!B3 itself, outside a Table, since the defined name carries its value.
Fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  NULL AS running,
  NULL AS loop,
  duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins * 0.2, "with_tax")),
    FROM(job_runs),
)
# running and loop are refused, so they are left out
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. Move tax_rate into Parameters, and if job_runs is partitioned on dt, bound it as file 03 shows.

## X13

Sources: job_runs (run_id, job_id, typed) and jobs (job_id, job_name, team, region, typed).
Steps: none.
Finals: job_runs (run_id, job_id, name, doubled).
- name = VLOOKUP(job_id, jobs, 2, TRUE). The TRUE makes this an approximate match. It is converted as an exact match on job_id, a LEFT JOIN of jobs, then job_name, and the user should check it, since the approximate match may differ from the exact one. Column 2 of jobs is job_name.
- doubled = DOUBLE(job_id). DOUBLE is a defined name holding a LAMBDA, which is refused. NULL AS doubled.
Parameters and Keys: neither; both empty. Typed over: none.
Marks: the approximate VLOOKUP, as above.
Refusals: doubled, the LAMBDA defined name DOUBLE.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, j.job_name AS name, NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, AS(jobs.job_name, "name")),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
# doubled is refused, so it is left out
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. Check the name column, since the approximate match was converted as exact.

## X14

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, typed). Its hours column is a formula.
Steps: job_hours (a CTE). by_job's SUMIFS reads job_runs[hours], so hours is worked out in a step over job_runs.
Finals: by_job (job_id, total_hours). by_job's only typed column is job_id, the match key of its SUMIFS, so it is a summary: a GROUP BY job_id of job_runs. job_runs is not a final, because by_job reads it.
- total_hours = SUMIFS(job_runs[hours], job_id): SUM of hours by job_id, with COALESCE.
Parameters and Keys: neither; both empty. Typed over: none.
Marks: none. The hours formula reads duration_mins, which has no blank.
Refusals: none.
Left alone: the PivotTable on sheet "Pivot", from Table job_runs, rows job_id and sum of duration_mins, since PivotTables are left alone.
Fill in: `<database>`.

```sql
WITH job_hours AS (
  SELECT job_id, duration_mins / 60 AS hours
  FROM <database>.job_runs
)
SELECT job_id, COALESCE(SUM(hours), 0) AS total_hours
FROM job_hours
GROUP BY job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, derived, fill_null, statement, sum_of
from references.ops__job_runs import job_runs

job_hours = derived("job_hours", statement(
    SELECT(job_runs.job_id, AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs),
))
s = statement(
    SELECT(job_hours.job_id, AS(fill_null(sum_of(job_hours.hours), 0), "total_hours")),
    FROM(job_hours),
    GROUP_BY(job_hours.job_id),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. If job_runs is partitioned on dt, bound it as file 03 shows.

## X15

Sources: tblRuns (Run ID, Job ID, Duration (mins), typed). Table name tblRuns is a plain name, so it is kept.
Steps: none.
Finals: tblRuns (Run ID, Job ID, Duration (mins), Hours).
- Column names: Run ID is `<run_id>`, Job ID is `<job_id>`, Duration (mins) is `<duration_mins>`. Hours is a plain name, so it stays hours.
- hours = [@[Duration (mins)]] / 60, written as <duration_mins> / 60.
Parameters and Keys: neither; both empty. Typed over: none.
Marks: the headers with spaces and brackets are placeholders, since the user's names must be filled in and never guessed.
Refusals: none.
Fill in: `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`.

```sql
SELECT <run_id>, <job_id>, <duration_mins>,
  <duration_mins> / 60 AS hours
FROM <database>.tblRuns
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__tblRuns import tblRuns

s = statement(
    SELECT(tblRuns.<run_id>, tblRuns.<job_id>, tblRuns.<duration_mins>,
           AS(tblRuns.<duration_mins> / 60, "hours")),
    FROM(tblRuns),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. Fill in the Python's import and column names from your Table reference.

## X16

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, typed).
Steps: none.
Finals: long_runs (run_id, job_id, minutes, hours), loaded by the Power Query "long_runs". Nothing reads long_runs, so it is a final, one query.
The Power Query, as Hive:
- Source = job_runs, the Table read.
- Kept = SelectColumns run_id, job_id, duration_mins.
- Long = rows where duration_mins > 15 (WHERE).
- Hours = duration_mins / 60.
- Renamed = duration_mins to minutes.
The sample's five rows (runs 96, 97, 102, 103, 104) are what this filter keeps.
Parameters and Keys: neither; both empty. Typed over: none.
Marks: none.
Refusals: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins AS minutes, duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, more_than, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id,
           AS(job_runs.duration_mins, "minutes"),
           AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs),
    WHERE(more_than(job_runs.duration_mins, 15)),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. If job_runs is partitioned on dt, bound it as file 03 shows.

## X17

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, typed).
Steps: ok_runs (a CTE). It is the connection-only Power Query "ok_runs", but ok_by_job reads it, so it is a step and is not left out.
- ok_runs = rows of job_runs where status = 'SUCCESS'.
Finals: ok_by_job (job_id, runs, total_mins), loaded by the Power Query "ok_by_job". Nothing reads it, so it is a final, one query.
- runs = Table.RowCount, as COUNT(*).
- total_mins = List.Sum of duration_mins, as SUM.
Parameters and Keys: neither; both empty. Typed over: none.
Marks: status is blank in row 98. M's = "SUCCESS" and Hive's = 'SUCCESS' both leave it out, so no wrap is needed.
Refusals: none.
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

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived, equals, statement, sum_of
from references.ops__job_runs import job_runs

ok_runs = derived("ok_runs", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(equals(job_runs.status, "SUCCESS")),
))
s = statement(
    SELECT(ok_runs.job_id, AS(count_rows(), "runs"), AS(sum_of(ok_runs.duration_mins), "total_mins")),
    FROM(ok_runs),
    GROUP_BY(ok_runs.job_id),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. If job_runs is partitioned on dt, bound it as file 03 shows.

## X18

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, typed) and jobs (job_id, job_name, team, region, typed).
Steps: none.
Finals: top_runs (run_id, job_name, duration_mins), loaded by the Power Query "top_runs". Nothing reads it, so it is a final, one query.
The Power Query, as Hive:
- NestedJoin, LeftOuter, then ExpandTableColumn job_name: LEFT JOIN jobs on job_id.
- Table.Sort by duration_mins, descending: ORDER BY duration_mins DESC.
- FirstN 3: LIMIT 3.
- SelectColumns run_id, job_name, duration_mins.
Marks: runs 97 and 103 tie at 30 minutes. Both fall in the top 3 in any order, so the three rows are the same whichever order Hive gives them. The sample lists 104, 97, 103.
Parameters and Keys: neither; both empty. Typed over: none.
Refusals: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC
LIMIT 3
```

```python
from sqlglot_composer import FROM, LEFT_JOIN, LIMIT, ORDER_BY, SELECT, descending, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, jobs.job_name, job_runs.duration_mins),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    ORDER_BY(descending(job_runs.duration_mins)),
    LIMIT(3),
)
```

Next: take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. If job_runs is partitioned on dt, bound it as file 03 shows.

## X19

Sources: `<database>.scheduler_runs` (run_id, job_id, dt; the workbook's typed Table). `<database>.job_runs` (run_id, job_id, dt; read through the Sql.Database step, not a workbook Table).
Steps: none.
Finals: all_runs (run_id, job_id, dt), loaded by Power Query all_runs; nothing reads it.

```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt
FROM <database>.job_runs
```

Marks:
- `Sql.Database("dwh01", "ops")` with Schema "ops" and Item "job_runs" is written as `<database>.job_runs`. Check that `<database>` is ops, on server dwh01, and that job_runs there holds run_id, job_id and dt.
- Table.Combine is UNION ALL, so every row of both is kept.

Refused, left out:
- Power Query "holidays" is connection only, reads a web source (Web.Contents to calendar.example.com), and nothing reads it. It is left out and named here.

Left alone: the Steps sheet, which holds no Table. Parameters and Keys are empty and are neither a source nor a step.

Fill in: `<database>` in both table names. Before any Toolbox code, take out what you don't want converted.

## X20

Sources: `<database>.run_alerts` (alert_id, run_id, severity, dt; the workbook's typed Table).
Steps: none.
Finals: alert_pivot (run_id, high, low), loaded by Power Query alert_pivot; nothing reads it.

```sql
SELECT run_id,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
WHERE run_id = 97 OR run_id = 101
GROUP BY run_id
```

Marks:
- Table.SelectRows is the WHERE, with `or` kept as OR.
- Table.Pivot: one column per severity value in the kept rows, which are high and low (List.Distinct on the sample). Each cell is NULL where no row has that severity, as M leaves it.
- The pivot's columns are now fixed: a new severity value in run_alerts gets no column until the query is changed.
- The Counted step's n column is always 1, so the SUM counts 1 directly.

Left alone: nothing. The Steps sheet holds no Table; Parameters and Keys are empty.

Fill in: `<database>` in `<database>.run_alerts`.

## X41

Sources: `<database>.job_runs` (run_id, job_id, status, duration_mins; the workbook's typed columns).
Steps: none.
Finals: job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total); nothing reads it.

```sql
SELECT run_id, job_id, status, duration_mins,
  RANK() OVER (ORDER BY duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN status = 'SUCCESS' THEN duration_mins END) OVER (PARTITION BY job_id), 0) AS shortest_ok,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0) AS job_total
FROM <database>.job_runs
```

Marks:
- RANK.EQ with no third argument is RANK() descending. Ties (the two 30s) share a rank, as in Excel.
- MINIFS on job_id and status "SUCCESS", over its own Table: MIN of the matching rows for each job_id, with COALESCE(..., 0) as Excel gives 0 where nothing matches.
- SUMIF on job_id, read as the -IFS form with one match: SUM per job_id, with COALESCE.
- The blank status (run 98) is skipped by the status = 'SUCCESS' condition, as MINIFS skips it. No blank is wrapped.
- No value is typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in `<database>.job_runs`.

## X42

Sources: `<database>.job_runs` (job_id, duration_mins are read; its typed columns hold no formula, and jobs reads it). `<database>.jobs` (job_id, job_name; typed).
Steps: none.
Finals: jobs (job_id, job_name, runs, avg_mins, id_order); nothing reads it.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(r.runs, 0) AS runs,
  COALESCE(a.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
  ON j.job_id = r.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins FROM <database>.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

Marks:
- COUNTIF on job_id, read as the -IFS form with one match: COUNT(*) per job_id, joined, with COALESCE as Excel gives 0.
- AVERAGEIF on job_id: AVG per job_id, left NULL. The IFERROR around it gives 0 where nothing matches, so the outer part is COALESCE(avg, 0), as IFERROR(a / b, 0) is.
- RANK.EQ with 1 as third argument is ascending: RANK() OVER (ORDER BY job_id ASC).
- The `_xlfn.` prefix is Excel's only and is dropped.
- No blank in a column these formulas read (status and avg_retry_secs are not read). No value is typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in `<database>.jobs` and `<database>.job_runs`.

## X43

Sources: `<database>.job_runs` (job_id, status, duration_mins; typed). `<database>.jobs` (job_id, team; typed).
Steps: none.
Finals:
- busy_teams (team, runs, shortest, avg_mins), loaded by Power Query busy_teams; nothing reads it.
- statuses (job_id, status), loaded by Power Query statuses; nothing reads it.

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
SELECT DISTINCT job_id, status
FROM <database>.job_runs
```

Marks:
- Inner NestedJoin is JOIN. Table.Group's RowCount, List.Min and List.Average are COUNT(*), MIN and AVG.
- The SelectRows after the group is HAVING, repeating COUNT(*) > 4.
- Table.Distinct alone is SELECT DISTINCT. The blank status (job 2, run 98) stays NULL, and DISTINCT keeps it as Table.Distinct keeps null.
- No value is typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in `<database>.job_runs` and `<database>.jobs`.

## X44

Sources: `<database>.job_runs` (run_id, job_id). `<database>.jobs` (job_id, job_name, team). `<database>.scheduler_runs` (job_id).
Steps: none.
Finals:
- jobs_with_runs (run_id, job_name), loaded by Power Query jobs_with_runs; nothing reads it.
- never_scheduled (job_id, job_name, team), loaded by Power Query never_scheduled; nothing reads it.

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

Marks:
- RightOuter is a LEFT JOIN with the two tables swapped, so jobs is the left table. cache_warm, with no run, gets a NULL run_id, as M gives it.
- LeftAnti is a LEFT JOIN that keeps jobs' columns only, with WHERE on the joined key IS NULL.
- No value is typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in each table name.

## X45

Sources: `<database>.job_runs` (run_id, job_id, dt, status; typed). `<database>.scheduler_runs` (run_id, job_id, dt; typed).
Steps: none.
Finals:
- run_days (run_id, dt), loaded by Power Query run_days; nothing reads it.
- matched (run_id, job_id, dt, status), loaded by Power Query matched; nothing reads it.

run_days:
```sql
SELECT run_id, dt
FROM <database>.job_runs
UNION
SELECT run_id, dt
FROM <database>.scheduler_runs
```

matched:
```sql
SELECT s.run_id, s.job_id, s.dt, r.status
FROM <database>.scheduler_runs s
FULL OUTER JOIN <database>.job_runs r ON s.run_id = r.run_id
```

Marks:
- Table.Distinct around Table.Combine is UNION, which drops repeated rows, not UNION ALL.
- FullOuter is FULL OUTER JOIN. run_id, job_id and dt come from the scheduler side, so run 99, which is only in job_runs, has NULL there, as M gives it. Status comes from job_runs, so run 100, which has no job_runs row, has a NULL status.
- No value is typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in each table name.

## X51

Sources: `<database>.job_runs` (run_id, job_id, status, duration_mins, dt; the workbook's typed columns).
Steps: none.
Finals: job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins); nothing reads it.

```sql
SELECT run_id, job_id, status, duration_mins, dt,
  COALESCE(COUNT(CASE WHEN duration_mins > 15 THEN 1 END) OVER (PARTITION BY job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (status <> 'SUCCESS' OR status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY job_id), 0) AS failed_in_job,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs
```

Marks:
- COUNTIFS with `">15"` on job_id is COUNT per job_id over the rows with duration_mins above 15.
- COUNTIFS on status `"<>SUCCESS"` has no row reference, so it counts the whole column: OVER (). A blank status (run 98) counts, as Excel counts a blank there.
- `"*ail*"` becomes LOWER(status) LIKE '%ail%', which ignores case, as Excel does. A blank does not match.
- SUMIFS with `"<="&dt` is a running total over dt per job_id, with ties included as in Excel.
- Each COUNTIFS and SUMIFS has COALESCE(..., 0).
- No value is typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in `<database>.job_runs`.

## X52

Sources: `<database>.job_runs` (run_id, job_id, duration_mins; the workbook's typed columns).
Steps: none.
Finals:
- job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job); nothing reads it.
- job_runs (total row), one row; nothing reads it.

job_runs:
```sql
SELECT run_id, job_id, duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

job_runs (total row):
```sql
SELECT SUM(duration_mins) AS duration_mins, SUM(share) AS share
FROM (
  SELECT duration_mins, duration_mins / SUM(duration_mins) OVER () AS share
  FROM <database>.job_runs
) t
```

Marks:
- SUM and AVERAGE of the whole column are SUM(...) OVER () and AVG(...) OVER ().
- COUNTIFS with `">"&duration` plus 1 is RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC). The tie of 30 for job 3 (runs 97 and 103) shares rank 1, as the count does.
- The Total Row is a final of its own, since job_runs is not a summary. It is one row, the two SUBTOTAL(109) totals in order, with no label. The share total needs the subquery, because share is a window.
- No value is typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in `<database>.job_runs`.

## X53

Sources: `<database>.job_runs` (job_id, duration_mins are read).
Steps: none.
Finals: by_job (job_id, total_mins, runs, longest), a summary. Its only typed column, job_id, is what its SUMIFS, COUNTIFS and MAXIFS match on, so it is a GROUP BY of job_runs. Nothing reads it. Its Total Row is rolled up into this query (see marks).

```sql
SELECT job_id,
  COALESCE(SUM(duration_mins), 0) AS total_mins,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(MAX(duration_mins), 0) AS longest
FROM <database>.job_runs
GROUP BY job_id WITH ROLLUP
```

Marks:
- SUMIFS is SUM, COUNTIFS is COUNT(*), MAXIFS is MAX, each with COALESCE.
- The Total Row's SUBTOTAL(109) on total_mins and on runs (SUM over a SUM and a COUNT) and SUBTOTAL(104) on longest (MAX over a MAX) makes this summary's Total Row none of its own. WITH ROLLUP gives it, and its job_id is NULL. On the sample it gives total_mins 180, runs 9 and longest 40.

Left alone: nothing.

Fill in: `<database>` in `<database>.job_runs`.

## X54

Sources: `<database>.job_runs` (run_id, dt; the workbook's typed columns). `<database>.scheduler_runs` (run_id, job_id, dt; typed).
Steps: none.
Finals:
- job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label); nothing reads it.
- scheduler_runs (run_id, job_id, dt); no formula reads it, so it is a final of its own, and its query gives its rows.

job_runs:
```sql
SELECT run_id, dt,
  LAST_DAY(dt) AS month_end,
  ADD_MONTHS(dt, 1) AS a_month_on,
  DATE_ADD(dt, 7) AS due,
  CAST(NEXT_DAY(DATE_ADD(dt, 7 * -1), 'MO') AS STRING) AS week_of,
  CAST(TRUNC(dt, 'MM') AS STRING) AS month_of,
  DAYOFWEEK(dt) AS weekday,
  DATE_FORMAT(dt, 'yyyy-MM') AS label
FROM <database>.job_runs
```

scheduler_runs:
```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
```

Marks:
- EOMONTH(dt, 0) is LAST_DAY; EDATE(dt, 1) is ADD_MONTHS; dt + 7 is DATE_ADD.
- `dt - WEEKDAY(dt, 2) + 1` (the Monday start) is `CAST(NEXT_DAY(DATE_ADD(dt, 7 * -1), 'MO') AS STRING)`. The month start, DATE(YEAR, MONTH, 1), is `CAST(TRUNC(dt, 'MM') AS STRING)`. Both are text, as file 11 writes them.
- WEEKDAY(dt) is DAYOFWEEK(dt).
- TEXT(dt, "yyyy-mm") is DATE_FORMAT(dt, 'yyyy-MM'), which gives 2026-09.
- No blank cell in dt.

Left alone: nothing.

Fill in: `<database>` in each table name.

## X55

Sources: `<database>.jobs` (job_id, job_name, team, region; typed).
Steps: none.
Finals: jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens); nothing reads it.

```sql
SELECT job_id, job_name, team, region,
  INITCAP(REPLACE(job_name, '_', ' ')) AS title,
  CONCAT_WS('/', team, region) AS tag,
  CONCAT(region, '-', job_id) AS code,
  INSTR(LOWER(job_name), LOWER('SYNC')) > 0 AS has_sync,
  CAST(CONCAT(job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs
```

Marks:
- PROPER(SUBSTITUTE(job_name, "_", " ")) is INITCAP(REPLACE(job_name, '_', ' ')).
- TEXTJOIN("/", TRUE, team, region) is CONCAT_WS('/', team, region); a NULL is skipped, as TRUE (ignore empty) skips it.
- ISNUMBER(SEARCH("SYNC", job_name)) is INSTR(LOWER(job_name), LOWER('SYNC')) > 0, which ignores case.
- CONCATENATE is CONCAT. VALUE(job_id & "0") is CAST(CONCAT(job_id, '0') AS DOUBLE).
- No blank cell, and no value typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in `<database>.jobs`.

## X56

Sources: `<database>.job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs; typed). `<database>.scheduler_runs` (run_id, dt; typed, read by scheduled_on).
Steps: none.
Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on); nothing reads it.

```sql
SELECT j.run_id, j.job_id, j.status, j.duration_mins, j.avg_retry_secs,
  (j.status IS NULL) AS no_status,
  FLOOR(j.duration_mins / 7) AS weeks,
  GREATEST(j.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(j.duration_mins) OVER () AS spread,
  SUM(j.duration_mins * COALESCE(j.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(s.dt, 'unscheduled') AS scheduled_on
FROM <database>.job_runs j
LEFT JOIN <database>.scheduler_runs s ON j.run_id = s.run_id
```

Marks:
- Blank avg_retry_secs (run 98): SUMPRODUCT does not skip a blank the way SUM does, so the blank is wrapped as COALESCE(avg_retry_secs, 0).
- ISBLANK(status) is status IS NULL, so the blank status of run 98 gives no_status true.
- INT(x / 7) is FLOOR. MAX(a, b) of one row is GREATEST.
- STDEV.S is STDDEV_SAMP over the whole column; SUMPRODUCT(a, b) is SUM(a * b) OVER ().
- XLOOKUP with the fourth argument "unscheduled" is a LEFT JOIN on run_id, then COALESCE(dt, 'unscheduled'). dt is a date and the fallback is text, so check the type of that column.
- No value is typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in each table name.

## X57

Sources: `<database>.job_runs` (run_id, job_id, status, avg_retry_secs). `<database>.jobs` (job_id, job_name, team, region).
Steps: none.
Finals:
- picked (run_id, job_id, status, avg_retry_secs, status_lc), loaded by Power Query picked; nothing reads it.
- ran_jobs (job_id, job_name, team, region), loaded by Power Query ran_jobs; nothing reads it.

picked:
```sql
SELECT run_id, job_id, status,
  COALESCE(avg_retry_secs, 0) AS avg_retry_secs,
  LOWER(status) AS status_lc
FROM <database>.job_runs
WHERE job_id IN (1, 2) AND (status IS NULL OR status LIKE 'S%')
```

ran_jobs:
```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r ON r.job_id = j.job_id
WHERE j.job_name LIKE '%a%'
```

Marks:
- List.Contains({1, 2}, job_id) is job_id IN (1, 2). `[status] = null` is status IS NULL. Text.StartsWith is LIKE 'S%', case kept.
- Table.ReplaceValue of null with 0 on avg_retry_secs is COALESCE(avg_retry_secs, 0), so the blank of run 98 becomes 0.
- Text.Lower is LOWER. The blank status gives a NULL status_lc, as M's null does.
- List.Contains(Runs[job_id], [job_id]) is a LEFT SEMI JOIN, so each job appears once. Text.Contains([job_name], "a") is LIKE '%a%', case kept.
- No value is typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in `<database>.job_runs` and `<database>.jobs`.

## X58

Sources: `<database>.job_runs` (run_id, job_id, duration_mins, dt). `<database>.jobs` (job_id). `<database>.scheduler_runs` (run_id, job_id). `<database>.region_budgets` (region).
Steps: none.
Finals, each loaded by a Power Query and read by nothing:
- job_regions (job_id, region)
- numbered (run_id, dt, duration_mins, n)
- days_per_job (job_id, days)
- unrun (run_id, job_id)
- measures (run_id, measure, amount)

job_regions:
```sql
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) r
```

numbered:
```sql
SELECT run_id, dt, duration_mins,
  ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC) AS n
FROM <database>.job_runs
```

days_per_job:
```sql
SELECT job_id, COUNT(DISTINCT dt) AS days
FROM <database>.job_runs
GROUP BY job_id
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
SELECT run_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

Marks:
- job_regions: Table.AddColumn with each Regions, then expanded, is CROSS JOIN. Regions is Table.Distinct of the region column, so SELECT DISTINCT.
- numbered: Table.Sort then AddIndexColumn is ROW_NUMBER() OVER (ORDER BY ...). The query has no ORDER BY of its own. Ties at 30 go to run 97 then 103, as the sort's run_id ascending does.
- days_per_job: List.Count(List.Distinct(dt)) is COUNT(DISTINCT dt). No dt is blank. The Table.Sort by days descending has no FirstN or index after it, so the order is dropped; a Hive table holds no order.
- unrun: LeftAnti on run_id and job_id is a LEFT JOIN with WHERE r.run_id IS NULL. RemoveColumns then Table.Distinct is SELECT DISTINCT.
- measures: UnpivotOtherColumns is one SELECT per unpivoted column, stacked with UNION ALL, each with WHERE IS NOT NULL, as M drops a null there.
- The measures sample holds only duration_mins rows (9). The M also unpivots avg_retry_secs, which has 8 non-blank rows, so a refresh gives 17 rows. The sample looks out of date; refresh the Table.
- No value is typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in each table name.

## X67

Sources: `<database>.job_runs` (run_id, job_id, duration_mins, dt; typed). `<database>.jobs` (job_id, team). `<database>.run_alerts` (run_id; typed).
Steps: job_runs' calculated columns team, alerts and running_mins, as the CTE job_runs_calc. Both finals read them.
Finals:
- by_team (team, total_mins, alerted_runs), a summary: its only typed column, team, is what its SUMIFS and COUNTIFS match on. Nothing reads it. Its Total Row is rolled up into this query.
- noisy_runs (run_id, team, alerts, running_mins), loaded by Power Query noisy_runs; nothing reads it.

by_team:
```sql
WITH job_runs_calc AS (
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
FROM job_runs_calc
GROUP BY team WITH ROLLUP
```

noisy_runs:
```sql
WITH job_runs_calc AS (
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
FROM job_runs_calc
WHERE alerts >= 2
```

Marks:
- job_runs is read by by_team and noisy_runs, so it is a step, not a final. Its own columns are a source.
- XLOOKUP(job_id, jobs[job_id], jobs[team]) is a LEFT JOIN to jobs, then team.
- COUNTIF(run_alerts[run_id], run_id) is COUNT(*) per run_id, joined, with COALESCE.
- SUMIFS with `"<="&dt` on job_id is a running total over dt per job_id, with ties included, and COALESCE.
- by_team's SUMIFS is SUM and COUNTIFS with `">0"` is COUNT(CASE WHEN alerts > 0 THEN 1 END), each with COALESCE, grouped by team.
- The Total Row sums a SUM and a COUNT, so it is none of its own: WITH ROLLUP gives it, with team NULL. Sample gives the rolled-up total row, not a separate Table.
- noisy_runs: SelectRows `[alerts] >= 2` is WHERE alerts >= 2.
- No blank cell in the columns read, and no value is typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in each table name.

## X68

Sources: `<database>.job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). `<database>.jobs` (job_id, job_name). `<database>.region_budgets` (job_id, region).
Steps: base, the connection-only query, read by by_region and top_runs, so it is a CTE in each final's query. Its columns are run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name and region.
Finals:
- by_region (region, total_mins, runs, share), loaded by Power Query by_region; nothing reads it.
- by_region (total row), one row; nothing reads it.
- top_runs (run_id, job_name, region), loaded by Power Query top_runs; nothing reads it.

base, in each query:
```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
```

by_region:
```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
grouped AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT region, total_mins, runs,
  total_mins / SUM(total_mins) OVER () AS share
FROM grouped
```

by_region (total row):
```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
grouped AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT SUM(total_mins) AS total_mins
FROM grouped
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

Marks:
- base is connection only, but two queries read it, so it is kept as a CTE rather than left out. Inner NestedJoin is JOIN; LeftOuter is LEFT JOIN.
- Table.Group: List.Sum is SUM and RowCount is COUNT(*). The SelectRows on runs >= 2 after the group is HAVING COUNT(*) >= 2.
- share is a whole-column SUM(total_mins) OVER () over the rows kept by the HAVING.
- by_region is not a summary (it has no typed columns), so its Total Row is a final of its own: one row, only the total_mins SUBTOTAL, with no label.
- top_runs: Table.Sort then FirstN is ORDER BY ... LIMIT 2. The tie at 30 (runs 97 and 103) goes to run 97, as the run_id ascending sort does.
- No blank cell in the columns read, and no value is typed over a formula, so no Keys row is needed.

Left alone: nothing.

Fill in: `<database>` in each table name.
