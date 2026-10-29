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
