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
