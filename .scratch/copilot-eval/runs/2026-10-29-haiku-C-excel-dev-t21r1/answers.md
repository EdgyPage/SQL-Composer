date: 2026-10-29
arm: C
model: haiku
files: aa75911

## X01

Sources: job_runs (run_id, job_id, duration_mins, dt, all typed).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours).

Typed over a formula: none. Every duration_hours cell is the formula, so no Keys row is needed.
Marks: none.
Refused: none.
Left alone: the Steps sheet (cells outside a Table). Parameters and Keys are empty, so they are none.
To fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins, dt,
  duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(job_runs.duration_mins / 60, "duration_hours")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X02

Sources: job_runs (run_id, job_id, status, duration_mins, all typed).
Steps: none.
Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag).

Typed over a formula: none, so no Keys row is needed.
Marks: none. The blank status in run 98 is not read by either formula, so it stays as it is.
Refused: none.
Left alone: the Steps sheet.
To fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF(duration_mins > 25 OR job_id = 3, 'check', 'ok') AS flag
FROM <database>.job_runs
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
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X03

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, all typed).
Steps: none.
Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs).

Typed over a formula: none, so no Keys row is needed.
Marks (blank):
- status is read by score. The blank in run 98 is wrapped as COALESCE(status, ''), and it is a blank.
- avg_retry_secs is read by mins_per_retry and total_secs. The blank in run 98 is wrapped as COALESCE(avg_retry_secs, 0), and it is a blank.
Refused: none.
Converted: SWITCH with two cases and a default, as CASE with two WHEN branches and ELSE 0.
Left alone: the Steps sheet.
To fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.<database>__job_runs import job_runs

status = fill_null(job_runs.status, "")
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt,
           AS(if_else(equals(status, "SUCCESS"), 1,
                      if_else(equals(status, "FAILED"), -1, 0)), "score"),
           AS(fill_null(job_runs.duration_mins / fill_null(job_runs.avg_retry_secs, 0), 0),
              "mins_per_retry"),
           AS(job_runs.duration_mins * 60 + fill_null(job_runs.avg_retry_secs, 0), "total_secs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X04

Sources: jobs (job_id, job_name, team, region, all typed).
Steps: none.
Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd).

Typed over a formula: none.
Marks: none, as the sample has no blanks.
Refused: none.
Left alone: the Steps sheet.
Converted: `&` as CONCAT, LEFT as SUBSTR, LEN as LENGTH, MOD as PMOD.
Note: the Toolbox code for UPPER, LEFT, LEN, ROUND, MOD and & is not in files 03, 04 or 05. Load file 10 (Hive functions) in a new chat for code, name_length, third and odd. The Python below covers the plain columns only.
To fill in: `<database>`.

```sql
SELECT job_id, job_name, team, region,
  CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-', region) AS code,
  LENGTH(job_name) AS name_length,
  ROUND(job_id / 3, 2) AS third,
  PMOD(job_id, 2) AS odd
FROM <database>.jobs
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
)
# code, name_length, third and odd: load file 10 (Hive functions) in a new chat
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X05

Sources: job_runs (run_id, dt, all typed); region_costs (job_id, cost_cents, region, dt, all typed).
Steps: none.
Finals: job_runs (run_id, dt, month, days_since); region_costs (job_id, cost_cents, region, dt, day).

Typed over a formula: none.
Marks:
- region_costs dt is a date held as text, such as 20260911. The day column converts it with CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)). The date is held as text.
- The blank cost_cents in row 29 is not read by a formula, so it stays as it is.
Refused: none.
Converted: DATEDIF(DATE(2026,9,1), dt, "d") as DATEDIFF(dt, '2026-09-01').
Left alone: the Steps sheet.
To fill in: `<database>`.

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
from references.<database>__job_runs import job_runs
from references.<database>__region_costs import region_costs

s1 = statement(
    SELECT(job_runs.run_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
s2 = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region, region_costs.dt),
    FROM(region_costs, reads_all_partitions=True),
)
# month, days_since and day: load file 10 (Hive functions) in a new chat
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X06

Sources: job_runs (run_id, job_id, duration_mins, all typed); jobs (job_id, job_name, team, region, all typed).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job). jobs has no formula, so it is a source only.

Typed over a formula: none.
Marks: none, as the sample has no blanks.
Refused: none.
Converted:
- XLOOKUP on jobs as a LEFT JOIN on job_id, then jobs.job_name.
- COUNTIFS with one match over its own Table, as COUNT(*) OVER (PARTITION BY job_id), wrapped in COALESCE with 0.
Left alone: the Steps sheet.
To fill in: `<database>`.

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
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X07

Sources: job_runs (run_id, job_id, status, all typed); jobs (job_id, job_name, team, region, all typed).
Steps: none.
Finals: job_runs (run_id, job_id, status, team, region).

Typed over a formula: none.
Marks: the blank status in run 98 is not read by a formula, so it stays as it is. The VLOOKUP is exact (FALSE), so there is no approximate mark. Both lookups read the same join, so one LEFT JOIN serves both columns.
Refused: none.
Left alone: the Steps sheet.
To fill in: `<database>`.

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
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X08

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, all typed). job_runs has no formula.
Steps: none.
Summary: by_job. Its only typed column, job_id, is what its SUMIFS, AVERAGEIFS and MAXIFS match on, so it is a GROUP BY of job_runs.
Finals: by_job (job_id, total_mins, avg_retry, longest).

Typed over a formula: none.
Marks:
- AVERAGEIFS is left NULL. The blank avg_retry_secs in run 98 is skipped by AVG, as Excel skips it, so it is not wrapped.
- The blank status is not read by a formula.
Refused: none.
Converted: SUMIFS as COALESCE(SUM(...), 0); MAXIFS as COALESCE(MAX(...), 0).
Left alone: the Steps sheet.
To fill in: `<database>`.

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
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id,
           AS(fill_null(sum_of(job_runs.duration_mins), 0), "total_mins"),
           AS(average_of(job_runs.avg_retry_secs), "avg_retry"),
           AS(fill_null(max_of(job_runs.duration_mins), 0), "longest")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X09

Sources: job_runs (run_id, job_id, duration_mins, avg_retry_secs, all typed); jobs (job_id, job_name, team, region, all typed).
Steps: none.
Parameters: rate is read from it, and it is not a source or a final.
Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost).

Typed over a formula: cost in run 97 is typed as 100. The Keys sheet has a row for job_runs with key run_id, so the row is matched on run_id.
Marks:
- The blank avg_retry_secs in run 98 is read by cost, so it is wrapped as COALESCE(avg_retry_secs, 0), and it is a blank.
- XLOOKUP("rate", ...) reads 0.5 from Parameters. The Hive writes 0.5 in its place.
Refused: none.
Converted: team as a LEFT JOIN on job_id, then jobs.team. team_mins as SUM over the team's window, wrapped in COALESCE with 0.
Left alone: the Steps sheet.
To fill in: `<database>`.

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

r = AS(job_runs, "r")
by_team = window(PARTITION_BY=jobs.team)
s = statement(
    SELECT(r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs, jobs.team,
           AS(fill_null(sum_of(r.duration_mins, over=by_team), 0), "team_mins"),
           AS(first_match([(equals(r.run_id, 97), 100)],
                          otherwise=(r.duration_mins * 60 + fill_null(r.avg_retry_secs, 0)) * 0.5),
              "cost")),
    FROM(r, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, r.job_id)),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X10

Sources: job_runs (run_id, job_id, duration_mins, dt, all typed).
Steps: none.
Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample).

Typed over a formula: hours in run 103 is typed as 9. The workbook has no Keys row for job_runs, so every typed column of the row is matched: run_id 103, job_id 3, duration_mins 30 and dt '2026-09-24'. There is no Keys row.
Marks: none.
Refused: sample reads RAND(), which is refused, so it is NULL AS sample.
Left alone: the Steps sheet.
To fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24' THEN 9
    ELSE duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, equals, first_match, statement
from references.<database>__job_runs import job_runs

r = AS(job_runs, "r")
s = statement(
    SELECT(r.run_id, r.job_id, r.duration_mins, r.dt,
           AS(first_match([(all_of(equals(r.run_id, 103), equals(r.job_id, 3),
                                   equals(r.duration_mins, 30), equals(r.dt, "2026-09-24")), 9)],
                          otherwise=r.duration_mins / 60), "hours")),
    FROM(r, reads_all_partitions=True),  # a workbook's query reads every row
)
# sample is RAND(), which is refused: it stays NULL in the Hive
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X11

Sources: job_runs (run_id, duration_mins, both typed).
Steps: none.
Finals: job_runs (run_id, duration_mins, pick, scaled).

Typed over a formula: none.
Marks: none.
Refused:
- pick uses INDIRECT and ROW(), both refused: NULL AS pick.
- scaled reads Summary!$C$2, a cell outside a Table that is not a defined name: NULL AS scaled.

Left alone: the bar chart on the Summary sheet, the cell Summary!C2 (outside a Table), and the Steps sheet.
To fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  NULL AS pick,
  NULL AS scaled
FROM <database>.job_runs
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
# pick and scaled are refused, so they stay NULL in the Hive
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X12

Sources: job_runs (run_id, duration_mins, both typed).
Steps: none.
Finals: job_runs (run_id, duration_mins, running, loop, with_tax).

Typed over a formula: none.
Marks:
- tax_rate is a defined name for Summary!$B$3, a cell outside a Table. Its value 0.2 is used, and move it into Parameters.
Refused:
- running uses OFFSET and ROW(), both refused: NULL AS running.
- loop reads its own column, so it is circular: NULL AS loop.
Converted: with_tax as duration_mins * 0.2.
Left alone: the Steps sheet and the Summary sheet.
To fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  NULL AS running,
  NULL AS loop,
  duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins * 0.2, "with_tax")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
# running and loop are refused, so they stay NULL in the Hive
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X13

Sources: job_runs (run_id, job_id, both typed); jobs (job_id, job_name, team, region, all typed).
Steps: none.
Finals: job_runs (run_id, job_id, name, doubled).

Typed over a formula: none.
Marks:
- name uses VLOOKUP with TRUE, which is approximate. It is converted exactly, as a LEFT JOIN on job_id to jobs, then job_name, and I am saying so: the approximate match and the exact match agree for these job_ids, but check it.
Refused:
- doubled calls DOUBLE, a defined name holding a LAMBDA: NULL AS doubled.
Left alone: the Steps sheet.
To fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, j.job_name AS name, NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, AS(jobs.job_name, "name")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
# doubled is refused (a defined name holding a LAMBDA), so it stays NULL in the Hive
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X14

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, all typed).
Steps: job_runs's hours column, read by by_job, as a CTE job_runs_step.
Summary: by_job. Its only typed column, job_id, is what its SUMIFS matches on, so it is a GROUP BY of job_runs.
Finals: by_job (job_id, total_hours).

Typed over a formula: none.
Marks: none. No blank is read by a formula.
Refused: none.
Left alone: the PivotTable on sheet Pivot, from job_runs; the Steps sheet.
To fill in: `<database>`.

```sql
WITH job_runs_step AS (
  SELECT job_id, duration_mins / 60 AS hours
  FROM <database>.job_runs
)
SELECT job_id, COALESCE(SUM(hours), 0) AS total_hours
FROM job_runs_step
GROUP BY job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, derived, fill_null, statement, sum_of
from references.<database>__job_runs import job_runs

runs = derived("runs", statement(
    SELECT(job_runs.job_id, AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
))
s = statement(
    SELECT(runs.job_id, AS(fill_null(sum_of(runs.hours), 0), "total_hours")),
    FROM(runs),
    GROUP_BY(runs.job_id),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X15

Sources: tblRuns (Run ID, Job ID, Duration (mins), and Hours as a formula column).
Steps: none.
Finals: tblRuns (<run_id>, <job_id>, <duration_mins>, hours).

Typed over a formula: none.
Marks: the headers Run ID, Job ID and Duration (mins) are not plain names. They are written in snake case in brackets, `<run_id>`, `<job_id>` and `<duration_mins>`, to fill in. The Table name tblRuns is plain.
Refused: none.
Left alone: the Steps sheet.
To fill in: `<database>`, and the three header names above.

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
    FROM(tblRuns, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X16

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, all typed).
Steps: none.
Finals: long_runs (run_id, job_id, minutes, hours). The Power Query long_runs is read by no other query, so its query is the final's query.

Typed over a formula: none.
Marks: none. The query's filter is kept as the query makes it: rows with duration_mins above 15.
Refused: none.
Converted: Table.SelectColumns as the SELECT list; Table.RenameColumns duration_mins to minutes; Table.AddColumn hours as duration_mins / 60, read before the rename.
Left alone: the Steps sheet.
To fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins AS minutes, duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, more_than, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, AS(job_runs.duration_mins, "minutes"),
           AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(more_than(job_runs.duration_mins, 15)),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X17

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, all typed).
Steps: ok_runs, the connection-only Power Query, read by ok_by_job. It is a CTE.
Finals: ok_by_job (job_id, runs, total_mins).

Typed over a formula: none.
Marks: none. The blank status in run 98 is not SUCCESS, so it drops out, as M's = drops it.
Refused: none.
Converted: Table.Group as GROUP BY job_id, Table.RowCount as COUNT(*), List.Sum as SUM.
Left alone: the Steps sheet.
To fill in: `<database>`.

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
from references.<database>__job_runs import job_runs

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

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X18

Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, all typed); jobs (job_id, job_name, team, region, all typed).
Steps: none.
Finals: top_runs (run_id, job_name, duration_mins), the Power Query top_runs's query.

Typed over a formula: none.
Marks: none. The top 3 cut falls between 30 and 20, so the tie at 30 is wholly inside the top 3.
Refused: none.
Converted: Table.NestedJoin LeftOuter as LEFT JOIN on job_id; Table.ExpandTableColumn as jobs.job_name; Table.Sort descending as ORDER BY ... DESC; Table.FirstN 3 as LIMIT 3.
Left alone: the Steps sheet.
To fill in: `<database>`.

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
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    ORDER_BY(descending(job_runs.duration_mins)),
    LIMIT(3),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X19

Sources: scheduler_runs (run_id, job_id, dt, all typed); job_runs from the Sql.Database query on dwh01, database ops, read by the Power Query all_runs.
Steps: none.
Finals: all_runs (run_id, job_id, dt), the Power Query all_runs's query, which stacks the two sources with Table.Combine as UNION ALL.

Typed over a formula: none.
Marks:
- The Sql.Database source is not in the workbook. Its table, ops.job_runs on dwh01, is written as <database>.job_runs. Check that this Hive table is the one it names.
Refused:
- The connection-only Power Query holidays reads Web.Contents, a web source. It is left out, and named: nothing reads it, and a web source is refused.
Left alone: the Steps sheet.
To fill in: `<database>`.

```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt
FROM <database>.job_runs
```

```python
from sqlglot_composer import FROM, SELECT, UNION_ALL, statement
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

scheduled = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
warehouse_runs = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # the Sql.Database table ops.job_runs: check it
)
s = UNION_ALL(scheduled, warehouse_runs)
# the holidays query reads a web source, so it is left out
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive; its checked code wins where the two differ.

## X20

Map.
- Sources: run_alerts (alert_id, run_id, severity, dt), typed and read by the query below.
- Steps: none.
- Finals: alert_pivot (run_id, high, low), the Table loaded by Power Query "alert_pivot"; nothing reads it.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- Table.Pivot: one column per severity in the sample, high and low. The pivot's columns are now fixed; a new severity value would need a new column.
- The query adds n as 1 on every row, so List.Sum counts: THEN 1 in each CASE.
- NULL where none, as M leaves it.

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

## X41

Map.
- Sources: job_runs (run_id, job_id, status, duration_mins), typed.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). Nothing else reads it, so it is a final, and its typed columns are its source.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- longest_first: RANK.EQ with no third argument is descending, so RANK() OVER (ORDER BY duration_mins DESC).
- shortest_ok: MINIFS is MIN over the condition status = 'SUCCESS', with COALESCE, as Excel gives 0 where nothing matches. The blank status on run 98 is skipped by the condition, so it is not wrapped.
- job_total: SUMIF over its own Table is SUM OVER the job_id partition, with COALESCE.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins,
  RANK() OVER (ORDER BY duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN status = 'SUCCESS' THEN duration_mins END) OVER (PARTITION BY job_id), 0) AS shortest_ok,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0) AS job_total
FROM <database>.job_runs
```

## X42

Map.
- Sources: job_runs (job_id, duration_mins), typed. It is read by jobs' formulas, so it is a source only.
- Sources also: jobs (job_id, job_name), typed.
- Steps: none.
- Finals: jobs (job_id, job_name, runs, avg_mins, id_order).
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- runs: COUNTIF over another Table is a LEFT JOIN to the counts per job_id, with COALESCE(.., 0), as Excel gives 0 where nothing matches.
- avg_mins: AVERAGEIF over another Table is AVG, left NULL. IFERROR(x, 0) is COALESCE(x, 0), as a divide by 0 is NULL.
- id_order: RANK.EQ with 1 as third argument is ascending, so RANK() OVER (ORDER BY job_id ASC).
- Blank cells on job_runs (status and avg_retry_secs, run 98) are not read by a formula here, so nothing is wrapped.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(b.runs, 0) AS runs,
  COALESCE(b.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS runs, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) b ON j.job_id = b.job_id
```

## X43

Map.
- Sources: job_runs (run_id, job_id, status, duration_mins), typed; jobs (job_id, team), typed.
- Steps: none.
- Finals: busy_teams (team, runs, shortest, avg_mins), loaded by Power Query "busy_teams"; statuses (job_id, status), loaded by Power Query "statuses". Nothing reads either Table.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- busy_teams: Inner join is JOIN. Table.Group is COUNT(*), MIN and AVG, and the filter runs > 4 is HAVING COUNT(*) > 4.
- statuses: Table.Distinct with no column list is SELECT DISTINCT. The blank status on run 98 is kept as a row, as M keeps it.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT j.team, COUNT(*) AS runs, MIN(r.duration_mins) AS shortest, AVG(r.duration_mins) AS avg_mins
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.team
HAVING COUNT(*) > 4
```

```sql
SELECT DISTINCT job_id, status
FROM <database>.job_runs
```

## X44

Map.
- Sources: job_runs (run_id, job_id), typed; jobs (job_id, job_name, team), typed; scheduler_runs (job_id), typed.
- Steps: none.
- Finals: jobs_with_runs (run_id, job_name), loaded by Power Query "jobs_with_runs"; never_scheduled (job_id, job_name, team), loaded by Power Query "never_scheduled". Nothing reads either Table.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- jobs_with_runs: JoinKind.RightOuter is a LEFT JOIN with the two tables swapped, so every job is kept. cache_warm has no run, so its run_id is NULL (the blank row in the sample).
- never_scheduled: JoinKind.LeftAnti is a LEFT JOIN with WHERE on the joined table's key IS NULL, and only jobs' columns are kept. Only cache_warm has no scheduler run.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON j.job_id = r.job_id
```

```sql
SELECT j.job_id, j.job_name, j.team
FROM <database>.jobs j
LEFT JOIN <database>.scheduler_runs s ON j.job_id = s.job_id
WHERE s.job_id IS NULL
```

## X45

Map.
- Sources: job_runs (run_id, dt, status), typed; scheduler_runs (run_id, job_id, dt), typed.
- Steps: none.
- Finals: run_days (run_id, dt), loaded by Power Query "run_days"; matched (run_id, job_id, dt, status), loaded by Power Query "matched". Nothing reads either Table.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- run_days: Table.Combine then Table.Distinct is UNION, which drops repeated rows.
- matched: JoinKind.FullOuter is FULL OUTER JOIN. Run 99 is only in job_runs, so its scheduler columns are NULL, as in the sample's blank row. The blank status on run 98 is kept.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT run_id, dt FROM <database>.job_runs
UNION
SELECT run_id, dt FROM <database>.scheduler_runs
```

```sql
SELECT s.run_id, s.job_id, s.dt, r.status
FROM <database>.scheduler_runs s
FULL OUTER JOIN <database>.job_runs r ON s.run_id = r.run_id
```

## X51

Map.
- Sources: job_runs (run_id, job_id, status, duration_mins, dt), typed.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins). Nothing reads it.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- long_in_job: COUNTIFS over its own Table with job_id and duration_mins > 15, as a COUNT with a CASE, per job_id, with COALESCE.
- not_ok: COUNTIFS "<>SUCCESS" is the form (status <> 'SUCCESS' OR status IS NULL), as Excel counts the blank on run 98. It counts over the whole column, so OVER (), with COALESCE.
- failed_in_job: "*ail*" is LOWER(status) LIKE '%ail%', as Excel ignores case, per job_id, with COALESCE.
- running_mins: SUMIFS with job_id and "<="&dt over its own Table is a running total per job_id, ties included: SUM OVER the job_id partition ordered by dt, RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW, with COALESCE.
- The blank status on run 98 is read by not_ok and failed_in_job, both in -IFS forms, so it is not wrapped.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins, dt,
  COALESCE(COUNT(CASE WHEN duration_mins > 15 THEN 1 END) OVER (PARTITION BY job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (status <> 'SUCCESS' OR status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY job_id), 0) AS failed_in_job,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs
```

## X52

Map.
- Sources: job_runs (run_id, job_id, duration_mins), typed.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job). Nothing reads it.
- Finals, Total Row: job_runs (Total Row) (duration_mins, share), a query of its own.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- share: SUM(job_runs[duration_mins]) over the whole column is SUM OVER ().
- vs_avg: AVERAGE over the whole column is AVG OVER ().
- rank_in_job: COUNTIFS ">"&duration plus 1, per job_id, is RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC).
- Total Row: SUBTOTAL(109) is SUM for duration_mins and share, in that order, with no label. It is not a summary Table, so it has its own query. A window cannot sit inside an aggregate, so share is worked out in a CTE first.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

```sql
WITH shares AS (
  SELECT duration_mins,
    duration_mins / SUM(duration_mins) OVER () AS share
  FROM <database>.job_runs
)
SELECT SUM(duration_mins) AS duration_mins, SUM(share) AS share
FROM shares
```

## X53

Map.
- Sources: job_runs (job_id, duration_mins), typed.
- Steps: none.
- Finals: by_job (job_id, total_mins, runs, longest). by_job's typed column is job_id, which its SUMIFS and COUNTIFS match on, so it is a summary: a GROUP BY of job_runs.
- Finals, Total Row: none of its own. Its totals are SUMs and a MAX of MAXes, so the summary's query ends GROUP BY job_id WITH ROLLUP, and the Total is the rollup row with job_id NULL.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- The GROUP BY lists the job_ids in job_runs. Excel gives 0 for a job_id with no runs; in this sample each by_job job_id has runs, so no zero case arises.
- MAXIFS is MAX.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT job_id,
  SUM(duration_mins) AS total_mins,
  COUNT(*) AS runs,
  MAX(duration_mins) AS longest
FROM <database>.job_runs
GROUP BY job_id WITH ROLLUP
```

## X54

Map.
- Sources: job_runs (run_id, dt), typed; scheduler_runs (run_id, job_id, dt), typed.
- Steps: none.
- Finals: job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label). Nothing reads it.
- Finals: scheduler_runs (run_id, job_id, dt). No formula reads it, so it is a final with no formula, copied as it stands.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- a_month_on: EDATE is ADD_MONTHS, and a month's end stays one, so a date on the last day of a month stays on the last day of the target month.
- week_of: the Monday start, d - WEEKDAY(d, 2) + 1, is written as in the week-start form, CAST(NEXT_DAY(DATE_ADD(d, 7 * -1), 'MO') AS STRING).
- month_of: DATE(YEAR(d), MONTH(d), 1) is written as CAST(TRUNC(d, 'MM') AS STRING).
- weekday: WEEKDAY(d) is DAYOFWEEK(d).
- label: TEXT(d, "yyyy-mm") is DATE_FORMAT(dt, 'yyyy-MM').

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

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

```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
```

## X55

Map.
- Sources: jobs (job_id, job_name, team, region), typed.
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens). Nothing reads it.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- title: PROPER(SUBSTITUTE(job_name, "_", " ")) is INITCAP(REPLACE(job_name, '_', ' ')).
- tag: TEXTJOIN("/", TRUE, team, region) is CONCAT_WS('/', team, region), which skips a blank.
- code: CONCATENATE is CONCAT.
- has_sync: ISNUMBER(SEARCH("SYNC", job_name)) is INSTR(LOWER(job_name), 'sync') > 0, as Excel ignores case.
- tens: VALUE(job_id & "0") is CAST(CONCAT(job_id, '0') AS DOUBLE).

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT job_id, job_name, team, region,
  INITCAP(REPLACE(job_name, '_', ' ')) AS title,
  CONCAT_WS('/', team, region) AS tag,
  CONCAT(region, '-', job_id) AS code,
  INSTR(LOWER(job_name), 'sync') > 0 AS has_sync,
  CAST(CONCAT(job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs
```

## X56

Map.
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs), typed; scheduler_runs (run_id, dt), typed, read by scheduled_on.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on). Nothing reads it.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- no_status: ISBLANK(status) is status IS NULL. Not wrapped.
- weeks: INT is FLOOR.
- at_least_20: MAX of one row's cells is GREATEST.
- spread: STDEV.S is STDDEV_SAMP, over the whole column.
- weighted: SUMPRODUCT is SUM of the product over the whole column. The blank avg_retry_secs on run 98 is wrapped as COALESCE(avg_retry_secs, 0), as the formula reads it. Blank.
- scheduled_on: XLOOKUP is a LEFT JOIN on run_id, with the fourth argument as COALESCE. The date is held with 'unscheduled', a text, so dt is CAST to STRING. Run 99 has no scheduler run, so it reads unscheduled.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT j.run_id, j.job_id, j.status, j.duration_mins, j.avg_retry_secs,
  j.status IS NULL AS no_status,
  FLOOR(j.duration_mins / 7) AS weeks,
  GREATEST(j.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(j.duration_mins) OVER () AS spread,
  SUM(j.duration_mins * COALESCE(j.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(CAST(s.dt AS STRING), 'unscheduled') AS scheduled_on
FROM <database>.job_runs j
LEFT JOIN <database>.scheduler_runs s ON j.run_id = s.run_id
```

## X57

Map.
- Sources: job_runs (run_id, job_id, status, avg_retry_secs), typed; jobs (job_id, job_name, team, region), typed.
- Steps: none.
- Finals: picked (run_id, job_id, status, avg_retry_secs, status_lc), loaded by Power Query "picked"; ran_jobs (job_id, job_name, team, region), loaded by Power Query "ran_jobs". Nothing reads either Table.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- picked: List.Contains({1, 2}, job_id) is job_id IN (1, 2). [status] = null is status IS NULL, and Text.StartsWith is LIKE 'S%', case kept.
- picked: Table.ReplaceValue null to 0 on avg_retry_secs is COALESCE(avg_retry_secs, 0). The blank on run 98 becomes 0.
- picked: Text.Lower is LOWER, so the blank status on run 98 gives a blank status_lc.
- ran_jobs: List.Contains(job_runs job_id, job_id) for a row whose key is in another table is LEFT SEMI JOIN. Text.Contains "a" is LIKE '%a%', case kept.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, COALESCE(avg_retry_secs, 0) AS avg_retry_secs, LOWER(status) AS status_lc
FROM <database>.job_runs
WHERE job_id IN (1, 2) AND (status IS NULL OR status LIKE 'S%')
```

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r ON r.job_id = j.job_id
WHERE j.job_name LIKE '%a%'
```

## X58

Map.
- Sources: job_runs (run_id, job_id, duration_mins, dt), typed; jobs (job_id), typed; scheduler_runs (run_id, job_id), typed; region_budgets (region), typed.
- Steps: none.
- Finals: job_regions (job_id, region), loaded by Power Query "job_regions"; numbered (run_id, dt, duration_mins, n), loaded by "numbered"; days_per_job (job_id, days), loaded by "days_per_job"; unrun (run_id, job_id), loaded by "unrun"; measures (run_id, measure, amount), loaded by "measures". Nothing reads these Tables.
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- job_regions: Table.AddColumn with each Regions, expanded, is CROSS JOIN with the distinct regions of region_budgets.
- numbered: Table.Sort then Table.AddIndexColumn is ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC). The sample order matches.
- days_per_job: List.Count(List.Distinct(dt)) is COUNT(DISTINCT dt). Table.Sort by days with no FirstN or index after it: no ORDER BY, as a Hive table holds no order, so the order was dropped.
- unrun: NestedJoin on every column of scheduler_runs's key pair, LeftAnti, then Table.Distinct, is EXCEPT.
- measures: Table.UnpivotOtherColumns is one SELECT per column unpivoted, stacked with UNION ALL, each with WHERE ... IS NOT NULL, as M drops the blank avg_retry_secs on run 98.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) r
```

```sql
SELECT run_id, dt, duration_mins,
  ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC) AS n
FROM <database>.job_runs
```

```sql
SELECT job_id, COUNT(DISTINCT dt) AS days
FROM <database>.job_runs
GROUP BY job_id
```

```sql
SELECT run_id, job_id FROM <database>.scheduler_runs
EXCEPT
SELECT run_id, job_id FROM <database>.job_runs
```

```sql
SELECT run_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

## X67

Map.
- Sources: job_runs (run_id, job_id, duration_mins, dt), typed; jobs (job_id, team), typed; run_alerts (run_id), typed.
- Steps: job_runs, its formula columns team, alerts and running_mins, read by by_team and noisy_runs. It is a CTE, job_runs_calc, in each final that reads it.
- Finals: by_team (team, total_mins, alerted_runs), a summary: its typed column is team, which its SUMIFS and COUNTIFS match on. noisy_runs (run_id, team, alerts, running_mins), loaded by Power Query "noisy_runs".
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- team: XLOOKUP is a LEFT JOIN to jobs on job_id.
- alerts: COUNTIF over another Table is a LEFT JOIN to the counts per run_id, with COALESCE(.., 0).
- running_mins: SUMIFS with job_id and "<="&dt is a running total per job_id, ties included: RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW, with COALESCE.
- by_team: COUNTIFS ">0" is a CASE. Its Total Row sums only, so the summary ends GROUP BY team WITH ROLLUP; the Total is the row with team NULL.
- noisy_runs: [alerts] >= 2 is WHERE alerts >= 2.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
WITH job_runs_calc AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (
    SELECT run_id, COUNT(*) AS alerts
    FROM <database>.run_alerts
    GROUP BY run_id
  ) a ON r.run_id = a.run_id
)
SELECT team,
  SUM(duration_mins) AS total_mins,
  COUNT(CASE WHEN alerts > 0 THEN 1 END) AS alerted_runs
FROM job_runs_calc
GROUP BY team WITH ROLLUP
```

```sql
WITH job_runs_calc AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (
    SELECT run_id, COUNT(*) AS alerts
    FROM <database>.run_alerts
    GROUP BY run_id
  ) a ON r.run_id = a.run_id
)
SELECT run_id, team, alerts, running_mins
FROM job_runs_calc
WHERE alerts >= 2
```

## X68

Map.
- Sources: job_runs (run_id, job_id, duration_mins), typed; jobs (job_id, job_name), typed; region_budgets (job_id, region), typed.
- Steps: base, the connection-only query. Two queries read it, so it is a step, a CTE, in each final's query that reads it. It is not left out.
- Finals: by_region (region, total_mins, runs, share), loaded by Power Query "by_region"; its Total Row, by_region (Total Row) (total_mins), a query of its own; top_runs (run_id, job_name, region), loaded by Power Query "top_runs".
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- base: Inner NestedJoin is JOIN; LeftOuter is LEFT JOIN.
- by_region: Table.Group is SUM and COUNT(*); the filter runs >= 2 is HAVING COUNT(*) >= 2.
- share: total_mins / SUM(total_mins) over the Table is SUM OVER (). It is computed in an outer SELECT, since a window cannot sit in the same SELECT as its GROUP BY.
- by_region (Total Row): SUBTOTAL(109) is SUM for total_mins, with no label. It is a query of its own.
- top_runs: Table.Sort then FirstN is ORDER BY duration_mins DESC, run_id ASC LIMIT 2.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
WITH base AS (
  SELECT r.run_id, r.duration_mins, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT region, total_mins, runs,
  total_mins / SUM(total_mins) OVER () AS share
FROM (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) by_region
```

```sql
WITH base AS (
  SELECT r.run_id, r.duration_mins, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
by_region AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT SUM(total_mins) AS total_mins
FROM by_region
```

```sql
WITH base AS (
  SELECT r.run_id, r.duration_mins, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT run_id, job_name, region
FROM base
ORDER BY duration_mins DESC, run_id ASC
LIMIT 2
```

## X71

Map.
- Sources: job_runs (run_id, job_id, status, duration_mins), typed.
- Steps: ok_runs, the query loaded by Power Query "ok_runs"; ok_by_job reads it, so it is a CTE in each final that reads it.
- Finals: ok_runs (run_id, job_id, duration_mins, hours). The Table is nothing-read, so it is a final: the query plus the hours formula.
- Finals: ok_by_job (job_id, total_mins), loaded by Power Query "ok_by_job".
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- ok_runs: [status] = "SUCCESS" is status = 'SUCCESS'. The blank status on run 98 is not kept, as M leaves it out.
- hours: [duration_mins]/60 is duration_mins / 60.
- ok_by_job: Table.Group with List.Sum is GROUP BY job_id with SUM.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT run_id, job_id, duration_mins,
  duration_mins / 60 AS hours
FROM ok_runs
```

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT job_id, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

## X72

Map.
- Sources: job_runs (job_id, duration_mins), typed; jobs (job_id, job_name, team), typed.
- Steps: jobs, its formula columns runs and total. It is read by by_team and busy_jobs, so it is a CTE, jobs_calc, in each final that reads it.
- Finals: by_team (team, team_total). Its typed column is team, which its SUMIFS matches on, so it is a summary: a GROUP BY of jobs. It has no Total Row.
- Finals: busy_jobs (job_id, job_name, runs), loaded by Power Query "busy_jobs".
- Parameters and Keys: empty, none.

Typed over a formula: none.

Marks.
- runs: COUNTIF over another Table is a LEFT JOIN to the counts per job_id, with COALESCE(.., 0).
- total: SUMIF over another Table is a LEFT JOIN to the sums per job_id, with COALESCE(.., 0), as Excel gives 0 where nothing matches. Job 4 has no runs, so it gives 0.
- by_team: SUMIFS over jobs[total] by team is SUM grouped by team. The rows are data, finance and web.
- busy_jobs: [runs] >= 3 is WHERE runs >= 3.

Refused: none.

Left alone: the Steps sheet (cells outside a Table).

Fill in: `<database>`.

```sql
WITH jobs_calc AS (
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
SELECT team, SUM(total) AS team_total
FROM jobs_calc
GROUP BY team
```

```sql
WITH jobs_calc AS (
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
FROM jobs_calc
WHERE runs >= 3
```
