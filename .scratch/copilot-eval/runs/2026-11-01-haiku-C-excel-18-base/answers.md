date: 2026-11-01
arm: C
model: haiku
files: 18-base

## X01

**Map**
- Sources: job_runs (run_id, job_id, duration_mins, dt). duration_hours is a formula, not typed.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours).
- Parameters and Keys: none. Both Tables are empty, so there is no Keys row and no typed-over value to match.
- Typed over a formula: none.
- Marks: none.
- Refused: none.
- Left alone: none. The D1 notes are text, not calculations.
- Fill in: `<database>`.

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
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out what you don't want and fill in `<database>`. Save the query as job_runs.hql, then run the convert Workflow on it as one batch (file 13), with DEV filled in. Where its checked code and this differ, its checked code wins.

## X02

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag).
- Parameters and Keys: none. No value is typed over a formula, so no Keys row is needed.
- Typed over a formula: none.
- Marks: none. The blank status on row 98 stays NULL, as no formula reads status.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

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
           AS(if_else(any_of(more_than(job_runs.duration_mins, 25),
                             equals(job_runs.job_id, 3)), "check", "ok"), "flag")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

The slow_job1 column is not in the code above. File 03 has no form for a Condition written as a column, so load file 10 in a new chat to write it.

Take out what you don't want and fill in `<database>`. Save the query as job_runs.hql, then run the convert Workflow on it as one batch (file 13), with DEV filled in. Where its checked code and this differ, its checked code wins.

## X03

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs).
- Parameters and Keys: none. No value is typed over a formula, so no Keys row is needed.
- Typed over a formula: none.
- Marks:
  - blank: row 98 has a blank status, which score reads, and a blank avg_retry_secs, which mins_per_retry and total_secs read. Each is wrapped in COALESCE, with 0 for avg_retry_secs and '' for status.
  - The `_xlfn.` prefix on SWITCH is dropped. SWITCH becomes a CASE.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, fill_null, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt,
           AS(fill_null(job_runs.duration_mins / fill_null(job_runs.avg_retry_secs, 0), 0),
              "mins_per_retry"),
           AS(job_runs.duration_mins * 60 + fill_null(job_runs.avg_retry_secs, 0), "total_secs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

The score column has three labels, so it is left out of the code above. Load file 10 in a new chat to write it.

Take out what you don't want and fill in `<database>`. Save the query as job_runs.hql, then run the convert Workflow on it as one batch (file 13), with DEV filled in. Where its checked code and this differ, its checked code wins.

## X04

**Map**
- Sources: jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd).
- Parameters and Keys: none. No value is typed over a formula, so no Keys row is needed.
- Typed over a formula: none.
- Marks: none.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

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
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

The code, name_length, third and odd columns are not in the code above. File 03 has no names for UPPER, LEFT, LEN, ROUND or MOD, so load file 10 in a new chat to write them.

Take out what you don't want and fill in `<database>`. Save the query as jobs.hql, then run the convert Workflow on it as one batch (file 13), with DEV filled in. Where its checked code and this differ, its checked code wins.

## X05

**Map**
- Sources: job_runs (run_id, dt); region_costs (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month, days_since); region_costs (job_id, cost_cents, region, dt, day).
- Parameters and Keys: none. No value is typed over a formula, so no Keys row is needed.
- Typed over a formula: none.
- Marks:
  - Date held as text: region_costs dt holds 20260911 as text, so day is built with SUBSTR and CONCAT, not DATE.
  - The blank cost_cents on row 29 stays NULL, as no formula reads cost_cents.
- Refused: none.
- Left alone: none.
- Fill in: `<database>` in both queries.

job_runs:

```sql
SELECT run_id, dt,
  MONTH(dt) AS month,
  DATEDIFF(dt, '2026-09-01') AS days_since
FROM <database>.job_runs
```

region_costs:

```sql
SELECT job_id, cost_cents, region, dt,
  CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS day
FROM <database>.region_costs
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__job_runs import job_runs
from references.ops__region_costs import region_costs

runs_s = statement(
    SELECT(job_runs.run_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
costs_s = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region, region_costs.dt),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

The month, days_since and day columns are not in the code above. MONTH, DATEDIFF, CONCAT and SUBSTR have no names in files 03, 04 or 05, so load file 10 in a new chat to write them.

Take out what you don't want and fill in `<database>`. Save each query as a .hql file named for its Table, job_runs.hql and region_costs.hql, then run the convert Workflow on them as one batch (file 13), with DEV filled in. Where its checked code and this differ, its checked code wins.

## X06

Map
- Sources: job_runs (run_id, job_id, duration_mins), jobs (job_id, job_name). job_runs is both a source and a final, as in file 11's worked example; jobs is read by job_runs, so it is a source only.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job).
- Parameters: none. Keys: none, as no value is typed over a formula.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

- Marks: none. The XLOOKUP becomes a LEFT JOIN on job_id, so every run keeps its row. The COUNTIFS reads its own Table on job_id, so it is a window, with COALESCE as Excel gives 0 where nothing matches.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>` (in both table names).

## X07

Map
- Sources: job_runs (run_id, job_id, status), jobs (job_id, team, region). job_runs is both a source and a final. The VLOOKUP reads jobs' third column, team, and the INDEX and MATCH read jobs' region.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, team, region).
- Parameters: none. Keys: none.

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

- Marks: the VLOOKUP (FALSE) and the MATCH (0) are both exact, so one LEFT JOIN on job_id covers team and region. The blank status in run 98 is left as NULL, as no formula reads status, so it is not wrapped.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>` (in both table names).

## X08

Map
- Sources: job_runs (job_id, duration_mins, avg_retry_secs), the columns the final uses.
- Steps: none.
- Finals: by_job (job_id, total_mins, avg_retry, longest), a summary. Its only typed column, job_id, is what its SUMIFS, AVERAGEIFS and MAXIFS match on, so it is a GROUP BY of job_runs. Nothing reads it, so it is a final.
- Parameters: none. Keys: none, as no value is typed over a formula.

```sql
SELECT job_id,
  COALESCE(SUM(duration_mins), 0) AS total_mins,
  AVG(avg_retry_secs) AS avg_retry,
  COALESCE(MAX(duration_mins), 0) AS longest
FROM <database>.job_runs
GROUP BY job_id
```

- Marks: the blank avg_retry_secs in run 98 is not wrapped, as AVERAGEIFS is an -IFS form and AVG skips NULL, as AVERAGEIFS skips a blank. SUMIFS and MAXIFS get COALESCE, and AVERAGEIFS is left NULL, as file 11 says.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>`.

## X09

Map
- Sources: job_runs (run_id, job_id, duration_mins, avg_retry_secs), jobs (job_id, team). job_runs is both a source and a final.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost).
- Parameters: rate, which is 0.5; the XLOOKUP reads it as its value.
- Keys: job_runs with run_id.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs, j.team,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.team), 0) AS team_mins,
  CASE WHEN r.run_id = 97 THEN 100
    ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5 END AS cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

- Marks: the value typed over a formula is cost in run 97, which is 100; the Keys row matches on run_id, so the CASE tests run_id = 97. The blank avg_retry_secs in run 98 is read by cost, so it is wrapped as COALESCE(avg_retry_secs, 0), and that is the blank. team_mins is a SUMIFS over its own Table on team, so it is a window partitioned by team (j.team), with COALESCE for 0. The team is the XLOOKUP, which is the LEFT JOIN on job_id.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>` (in both table names).

## X10

Map
- Sources: job_runs (run_id, job_id, duration_mins, dt). job_runs is both a source and a final.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample).
- Parameters: none. Keys: none; the Keys Table has no row.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
  CASE WHEN r.run_id = 103 AND r.job_id = 3 AND r.duration_mins = 30 AND r.dt = '2026-09-24'
    THEN 9 ELSE r.duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs r
```

- Marks: the value typed over a formula is hours in run 103, which is 9. There is no Keys row for job_runs, so the CASE matches every typed column of that row (run_id, job_id, duration_mins and dt). Adding job_runs with run_id to Keys would let it match on run_id alone.
- Refusals: sample, which is =RAND(). RAND is random and refused, so the column is NULL AS sample.
- Left alone: none.
- To fill in: `<database>`.

## X11

Map.

- Sources: job_runs, its typed columns run_id and duration_mins.
- Steps: none.
- Finals: job_runs (run_id, duration_mins, pick, scaled).
- Parameters and Keys are empty, so there are no fixed values and no value typed over a formula.

Refused, NULL in its place:

- pick: `INDIRECT("B"&ROW())`. INDIRECT and ROW() hang on the order of the sheet's rows and on text references.
- scaled: `Summary!$C$2`, a cell outside a Table read by its address. It is not a defined name, so it is refused.

Left alone, and named: the bar chart, and the cell Summary C2 (value 3), which only scaled reads.

Marks: none. The sample has no blank cells, no date held as text and no typed-over value.

Fill in: `<database>`.

```sql
SELECT run_id, duration_mins, NULL AS pick, NULL AS scaled
FROM <database>.job_runs
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__job_runs import job_runs

# pick and scaled are refused, so NULL in the Hive; the Toolbox has no NULL to write them with, so they are left out here
s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs),
)
```

Take out what you don't want, and fill in each `<database>`. Save the query above as a file named job_runs.hql, and run the convert Workflow on it as one batch (file 13), with DEV filled in. Where that checked code and this Python differ, the checked code wins. If job_runs is partitioned, its Table reference needs a bound on the partition column; the workbook has no filter to copy, so use reads_all_partitions=True only if you want every day.

## X12

Map.

- Sources: job_runs, its typed columns run_id and duration_mins.
- Steps: none.
- Finals: job_runs (run_id, duration_mins, running, loop, with_tax).
- Parameters and Keys are empty; no value is typed over a formula.

Refused, NULL in its place:

- running: `SUM(OFFSET(...))` and ROW(). OFFSET and ROW() are refused.
- loop: `job_runs[[#This Row],[loop]]+1` reads its own column, which is circular, so it is refused.

Marks:

- with_tax: `tax_rate` is a defined name for Summary!$B$3 (a cell outside a Table). Its value, 0.2, is used. Move tax_rate into Parameters, as the Parameters note says.

Left alone, and named: nothing else.

Fill in: `<database>`.

```sql
SELECT run_id, duration_mins, NULL AS running, NULL AS loop, duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__job_runs import job_runs

# running and loop are refused, so NULL in the Hive; the Toolbox has no NULL to write them with, so they are left out here
s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins * 0.2, "with_tax")),
    FROM(job_runs),
)
```

Take out what you don't want, and fill in each `<database>`. Save the query above as a file named job_runs.hql, and run the convert Workflow on it as one batch (file 13), with DEV filled in. Where that checked code and this Python differ, the checked code wins. If job_runs is partitioned, its Table reference needs a bound on the partition column; use reads_all_partitions=True only if you want every day.

## X13

Map.

- Sources: job_runs, its typed columns run_id and job_id; jobs, its typed columns job_id, job_name, team and region.
- Steps: none.
- Finals: job_runs (run_id, job_id, name, doubled).
- Parameters and Keys are empty; no value is typed over a formula.

Refused, NULL in its place:

- doubled: `DOUBLE`, a defined name holding `_xlfn.LAMBDA(x,x*2)`. A LAMBDA is refused.

Marks:

- name: `VLOOKUP(job_id, jobs, 2, TRUE)` is approximate. It is converted as an exact LEFT JOIN on job_id, returning job_name (column 2 of jobs). The sample's jobs are sorted, so the result matches here, but the Hive matches exactly.

Left alone, and named: nothing.

Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, j.job_name AS name, NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

# doubled is refused, so NULL in the Hive; the Toolbox has no NULL to write it with, so it is left out here
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, AS(jobs.job_name, "name")),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
)
```

Take out what you don't want, and fill in each `<database>`. Save the query above as a file named job_runs.hql, and run the convert Workflow on it as one batch (file 13), with DEV filled in. Where that checked code and this Python differ, the checked code wins. Because the approximate VLOOKUP became an exact join, check the jobs table has one row per job_id.

## X14

Map.

- Sources: job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt.
- Steps: job_runs, its hours column (`duration_mins / 60`), which by_job's SUMIFS reads.
- Summary: by_job is a GROUP BY of job_runs, as its only typed column, job_id, is the one its SUMIFS matches on.
- Finals: by_job (job_id, total_hours).
- Parameters and Keys are empty; no value is typed over a formula.

Refused, NULL in its place: nothing.

Left alone, and named: the PivotTable on sheet Pivot, from job_runs (rows job_id, values Sum of duration_mins).

Marks: none. The blanks in status and avg_retry_secs are in columns no formula reads, so they need no COALESCE.

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

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, derived, statement, sum_of
from references.<database>__job_runs import job_runs

runs = derived("job_runs", statement(
    SELECT(job_runs.job_id, AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs),
))
# every job here has rows, so the sum needs no COALESCE to give 0
s = statement(
    SELECT(runs.job_id, AS(sum_of(runs.hours), "total_hours")),
    FROM(runs),
    GROUP_BY(runs.job_id),
)
```

Take out what you don't want, and fill in each `<database>`. Save the query above as a file named by_job.hql, and run the convert Workflow on it as one batch (file 13), with DEV filled in. Where that checked code and this Python differ, the checked code wins. If job_runs is partitioned, its Table reference needs a bound on the partition column; use reads_all_partitions=True only if you want every day.

## X15

Map.

- Sources: tblRuns, its typed columns Run ID, Job ID and Duration (mins).
- Steps: none.
- Finals: tblRuns (<run_id>, <job_id>, <duration_mins>, hours).
- Parameters and Keys are empty; no value is typed over a formula.

Refused, NULL in its place: nothing.

Left alone, and named: nothing.

Marks: none. The sample has no blank cells and no date held as text.

Fill in: `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`.

```sql
SELECT <run_id>, <job_id>, <duration_mins>, <duration_mins> / 60 AS hours
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

Take out what you don't want, and fill in each `<...>`. Save the query above as a file named tblRuns.hql, and run the convert Workflow on it as one batch (file 13), with DEV filled in. Where that checked code and this Python differ, the checked code wins. If tblRuns is partitioned, its Table reference needs a bound on the partition column; use reads_all_partitions=True only if you want every day.

## X16

Map.
- Sources: job_runs (run_id, job_id, duration_mins read; typed columns, not loaded by a query).
- Steps: none. Nothing reads a step.
- Finals: long_runs (run_id, job_id, minutes, hours), one query, from the Power Query "long_runs".
- Parameters: none, the Table is empty. Keys: none, no value is typed over a formula.

Marks, and what converts.
- Table.SelectColumns becomes the SELECT list. Table.SelectRows `[duration_mins] > 15` becomes WHERE duration_mins > 15; run 98 (15 minutes) is out, as in M.
- Table.AddColumn `hours` becomes `duration_mins / 60 AS hours`.
- Table.RenameColumns `duration_mins` to `minutes` becomes `duration_mins AS minutes`.
- No blank cell is read by these columns, so nothing is wrapped.

Refused: none.
Left alone: the Steps sheet and the notes in D1 of the Parameters and Keys sheets. They are the workbook's guide, not calculations.

Fill in: `<database>`, the database that holds job_runs.

```sql
SELECT r.run_id, r.job_id, r.duration_mins AS minutes, r.duration_mins / 60 AS hours
FROM <database>.job_runs r
WHERE r.duration_mins > 15
```

Toolbox code, by files 03 and 02:

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

Take out what you don't want. Fill in each `<database>`, in the SQL and in the import. Save the query as long_runs.hql. Then run the convert Workflow (file 13) on long_runs.hql as a batch, with DEV filled in. Where the two differ, the convert Workflow's checked code wins.

## X17

Map.
- Sources: job_runs (job_id, duration_mins, status read; typed columns, not loaded by a query).
- Steps: ok_runs, the connection-only query `[status] = "SUCCESS"` over job_runs. It is not left out, because ok_by_job reads it. It becomes a CTE inside ok_by_job's query.
- Finals: ok_by_job (job_id, runs, total_mins), loaded by the Power Query "ok_by_job".
- Parameters: none. Keys: none.

Marks, and what converts.
- Table.SelectRows `[status] = "SUCCESS"` becomes WHERE status = 'SUCCESS'. The blank status (run 98) is dropped in M and in Hive alike, since a null never equals the text, so nothing is wrapped.
- Table.Group: Table.RowCount becomes COUNT(*) AS runs; List.Sum of duration_mins becomes SUM(duration_mins) AS total_mins, grouped by job_id.
- Checked against the sample: job 1 has 3 runs and 62 minutes, job 2 has 1 run and 18 minutes, job 3 has 1 run and 30 minutes, as the Table holds.

Refused: none.
Left alone: the Steps sheet and the notes in D1 of the Parameters and Keys sheets.

Fill in: `<database>`, the database that holds job_runs.

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

Toolbox code, by files 03 and 05:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived,
                              equals, statement, sum_of)
from references.<database>__job_runs import job_runs

ok_runs = derived("ok_runs", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
))
s = statement(
    SELECT(ok_runs.job_id, AS(count_rows(), "runs"),
           AS(sum_of(ok_runs.duration_mins), "total_mins")),
    FROM(ok_runs),
    GROUP_BY(ok_runs.job_id),
)
```

Take out what you don't want. Fill in each `<database>`. Save the query as ok_by_job.hql, then run the convert Workflow (file 13) on it as a batch, with DEV filled in. Where the two differ, the convert Workflow's checked code wins.

## X18

Map.
- Sources: job_runs (run_id, job_id, duration_mins read) and jobs (job_id, job_name read); both typed, not loaded by a query.
- Steps: none.
- Finals: top_runs (run_id, job_name, duration_mins), loaded by the Power Query "top_runs".
- Parameters: none. Keys: none.

Marks, and what converts.
- Table.NestedJoin with JoinKind.LeftOuter and ExpandTableColumn `job_name` become LEFT JOIN jobs ON job_runs.job_id = jobs.job_id, reading jobs.job_name.
- Table.Sort descending on duration_mins and Table.FirstN 3 become ORDER BY ... DESC LIMIT 3.
- Ties: runs 97 and 103 both have 30 minutes and sit second and third. M keeps them in sheet order (97, then 103). Hive's LIMIT does not promise that order, so this converts with run_id as a second sort key, which keeps the sheet's order. Say so when you check the output.
- Table.SelectColumns becomes the SELECT list.
- No date filter is in M, so the query reads every row of job_runs.

Refused: none.
Left alone: the Steps sheet and the notes in D1 of the Parameters and Keys sheets.

Fill in: `<database>`, the database that holds job_runs and jobs.

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC, r.run_id
LIMIT 3
```

Checked against the sample: run 104 (nightly_load, 40), run 97 (report_build, 30), run 103 (report_build, 30).

Toolbox code, by files 04, 03 and 05:

```python
from sqlglot_composer import FROM, LEFT_JOIN, LIMIT, ORDER_BY, SELECT, descending, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, jobs.job_name, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    ORDER_BY(descending(job_runs.duration_mins), job_runs.run_id),  # run_id settles the tie at 30
    LIMIT(3),
)
```

Take out what you don't want. Fill in each `<database>`. Save the query as top_runs.hql, then run the convert Workflow (file 13) on it as a batch, with DEV filled in. Where the two differ, the convert Workflow's checked code wins.

## X19

Map.
- Sources: scheduler_runs (run_id, job_id, dt read; typed, read by all_runs). job_runs, read from the warehouse by the Power Query "all_runs" through Sql.Database("dwh01", "ops"), taking schema ops, item job_runs (run_id, job_id, dt read). This is not the workbook's job_runs sheet; it is a table outside the workbook, and M names it, so it is used as named.
- Steps: none.
- Finals: all_runs (run_id, job_id, dt), loaded by the Power Query "all_runs".
- Parameters: none. Keys: none.
- Left out: the connection-only query "holidays". Nothing reads it, and it reads a web source (Web.Contents on calendar.example.com), which is refused.

Marks, and what converts.
- Table.Combine({Scheduled, RunsKept}) becomes UNION ALL. It keeps repeated rows, as Table.Combine does; the sample's repeats (95, 96, 97 and others listed twice) stay.
- Table.SelectColumns RunsKept becomes the SELECT list of the second part.
- Sql.Database: check that `<database>.job_runs` is the table on dwh01 in schema ops that M reads, not another job_runs. The Hive table it names is the one you fill in.
- The warehouse read has no date filter, so it reads every row.

Refused: the query "holidays", left out, because it reads a web source (Web.Contents). Left alone: the Steps sheet and the notes in D1 of the Parameters and Keys sheets.

Fill in: `<database>`, the database that holds scheduler_runs and the warehouse job_runs.

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
from references.<database>__scheduler_runs import scheduler_runs
from references.<database>__job_runs import job_runs

scheduled = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
warehouse_runs = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # the Sql.Database query reads every row
)
s = UNION_ALL(scheduled, warehouse_runs)
```

Take out what you don't want. Fill in each `<database>`, and check the warehouse job_runs is the one on dwh01, schema ops. Save the query as all_runs.hql, then run the convert Workflow (file 13) on it as a batch, with DEV filled in. Where the two differ, the convert Workflow's checked code wins. The holidays query is not converted; add it by hand only if it is replaced by a source you can read.

## X20

Map.
- Sources: run_alerts (run_id, severity read; typed, read by alert_pivot).
- Steps: none.
- Finals: alert_pivot (run_id, high, low), loaded by the Power Query "alert_pivot".
- Parameters: none. Keys: none.

Marks, and what converts.
- Table.SelectRows `[run_id] = 97 or [run_id] = 101` becomes WHERE run_id = 97 OR run_id = 101.
- Table.AddColumn `n` = 1 and Table.Pivot with List.Sum become `SUM(CASE WHEN severity = 'high' THEN 1 END) AS high` and the same for low, one column per severity value in the sample (high and low, from the filtered rows), grouped by run_id. The count is 1 for each row and the total is SUM, so NULL is left where a run has none, as M does.
- Checked against the sample: run 97 has 1 high and 1 low; run 101 has 1 high and 2 low; both as the Table holds.
- The pivot's columns are now fixed: a severity that is not in the sample gets no column until the pivot is written again.

Refused: none.
Left alone: the Steps sheet and the notes in D1 of the Parameters and Keys sheets.

Fill in: `<database>`, the database that holds run_alerts.

```sql
SELECT run_id,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
WHERE run_id = 97 OR run_id = 101
GROUP BY run_id
```

Toolbox code, by files 03 and 04:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, any_of, count_rows, equals, statement
from references.<database>__run_alerts import run_alerts

s = statement(
    SELECT(run_alerts.run_id,
           AS(count_rows(where=equals(run_alerts.severity, "high")), "high"),
           AS(count_rows(where=equals(run_alerts.severity, "low")), "low")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(any_of(equals(run_alerts.run_id, 97), equals(run_alerts.run_id, 101))),
    GROUP_BY(run_alerts.run_id),
)
```

The Toolbox counts give 0, not NULL, where a run has no alert of that severity. Both severities appear for runs 97 and 101, so the sample is the same either way. Take out what you don't want. Fill in each `<database>`. Save the query as alert_pivot.hql, then run the convert Workflow (file 13) on it as a batch, with DEV filled in. Where the two differ, the convert Workflow's checked code wins.

## X41

Map:
- Sources: job_runs (its typed columns run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). Nothing else reads it.
- Parameters and Keys are empty, so there is no Keys row; no value is typed over a formula.

Converted:
- longest_first: RANK.EQ with no third argument, so the longest run is 1: `RANK() OVER (ORDER BY duration_mins DESC)`.
- shortest_ok: MINIFS over its own Table, a MIN per job_id with the status condition, COALESCE to 0.
- job_total: SUMIF over its own Table, a SUM per job_id, COALESCE to 0.

Marks:
- Blank: run 98 has no status. shortest_ok's MINIFS reads status inside an -IFS form, which skips the blank as Excel does, so it stays NULL with no COALESCE.

Refused: none.

Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table. No charts or PivotTables.

To fill in: `<database>`, in the block below.

```sql
SELECT
  run_id,
  job_id,
  status,
  duration_mins,
  RANK() OVER (ORDER BY duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN status = 'SUCCESS' THEN duration_mins END) OVER (PARTITION BY job_id), 0) AS shortest_ok,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0) AS job_total
FROM <database>.job_runs
```

Toolbox code:

```python
from sqlglot_composer import (AS, FROM, SELECT, descending, equals, fill_null, min_of, rank,
                              statement, sum_of, window)
from references.ops__job_runs import job_runs

by_job = window(PARTITION_BY=job_runs.job_id)
longest = window(ORDER_BY=descending(job_runs.duration_mins))

s = statement(
    SELECT(
        job_runs.run_id,
        job_runs.job_id,
        job_runs.status,
        job_runs.duration_mins,
        AS(rank(over=longest), "longest_first"),
        AS(fill_null(min_of(job_runs.duration_mins,
                            where=equals(job_runs.status, "SUCCESS"), over=by_job), 0),
           "shortest_ok"),
        AS(fill_null(sum_of(job_runs.duration_mins, over=by_job), 0), "job_total"),
    ),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Next steps: take out what you don't want; fill in `<database>`; save the query above as job_runs.hql; then run the convert Workflow on it as one batch (file 13), with DEV filled in. Where the Workflow's checked code and this answer differ, the checked code wins.

## X42

Map:
- Sources: job_runs and jobs (their typed columns). job_runs has no formula; jobs' formulas read job_runs.
- Steps: none.
- Finals: jobs (job_id, job_name, runs, avg_mins, id_order). Nothing reads it.
- Parameters and Keys are empty, so there is no Keys row; no value is typed over a formula.

Converted:
- runs: COUNTIF over another Table, the -IFS form with one match, so a count of job_runs per job_id in a LEFT JOIN, COALESCE to 0.
- avg_mins: IFERROR(AVERAGEIF(...), 0) over another Table, so an average of duration_mins per job_id in a LEFT JOIN. AVERAGEIF gives NULL where no run matches; the IFERROR's 0 is kept as COALESCE(avg, 0).
- id_order: `_xlfn.RANK.EQ` with 1 as the third argument, so ascending: `RANK() OVER (ORDER BY job_id ASC)`. The `_xlfn.` prefix is dropped.

Marks:
- cache_warm (job 4) has no run in job_runs, so its runs and avg_mins are 0. It is kept as a row.
- Blank: run 98's status and avg_retry_secs are blank. No formula reads either, so they stay NULL and are not wrapped.

Refused: none.

Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table. No charts or PivotTables.

To fill in: `<database>`, in each place it appears below.

```sql
SELECT
  j.job_id,
  j.job_name,
  COALESCE(runs_per_job.runs, 0) AS runs,
  COALESCE(avg_per_job.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) runs_per_job
  ON j.job_id = runs_per_job.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins FROM <database>.job_runs GROUP BY job_id) avg_per_job
  ON j.job_id = avg_per_job.job_id
```

Toolbox code:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, count_rows,
                              derived, equals, fill_null, rank, statement, window)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

runs_per_job = derived("runs_per_job", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "runs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
avg_per_job = derived("avg_per_job", statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))

s = statement(
    SELECT(
        jobs.job_id,
        jobs.job_name,
        AS(fill_null(runs_per_job.runs, 0), "runs"),
        AS(fill_null(avg_per_job.avg_mins, 0), "avg_mins"),
        AS(rank(over=window(ORDER_BY=jobs.job_id)), "id_order"),
    ),
    FROM(jobs),
    LEFT_JOIN(runs_per_job, ON=equals(runs_per_job.job_id, jobs.job_id)),
    LEFT_JOIN(avg_per_job, ON=equals(avg_per_job.job_id, jobs.job_id)),
)
```

Next steps: take out what you don't want; fill in `<database>`; save the query above as jobs.hql; then run the convert Workflow on it as one batch (file 13), with DEV filled in. Where the Workflow's checked code and this answer differ, the checked code wins.

## X43

Map:
- Sources: job_runs and jobs, their typed columns read as they are.
- Steps: none. Neither Table has a formula, and no query reads either.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (job_id, job_name, team, region). Nothing reads either, so each is a final.
- Nothing is calculated in this workbook: each final is a plain read of its columns. Parameters and Keys are empty, so there is no Keys row.

Converted: no calculation to convert; each final keeps every column and every row.

Marks:
- Blank: run 98's status and avg_retry_secs are blank. No formula reads them, so they stay NULL and are not wrapped.

Refused: none.

Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table. No charts or PivotTables.

To fill in: `<database>`, in each block below.

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
FROM <database>.job_runs
```

```sql
SELECT job_id, job_name, team, region
FROM <database>.jobs
```

Toolbox code:

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

job_runs_final = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)

jobs_final = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
)
```

Next steps: nothing is calculated, so take out either final you don't want; fill in `<database>`; save each query as job_runs.hql and jobs.hql; then run the convert Workflow on them as one batch (file 13), with DEV filled in. Where the Workflow's checked code and this answer differ, the checked code wins.

## X44

Map:
- Sources: job_runs, jobs and scheduler_runs, their typed columns, read by the two queries below.
- Steps: none.
- Finals: jobs_with_runs (run_id, job_name), loaded by its Power Query; never_scheduled (job_id, job_name, team), loaded by its Power Query. Nothing reads either Table.
- Parameters and Keys are empty; no value is typed over a formula.

Converted:
- jobs_with_runs: its query joins with JoinKind.RightOuter, so the two tables swap: jobs LEFT JOIN job_runs on job_id, keeping every job, then the query keeps run_id and job_name.
- never_scheduled: its query joins with JoinKind.LeftAnti: jobs LEFT JOIN scheduler_runs on job_id, keeping rows where no scheduler run matches, then jobs' three columns only.

Marks:
- cache_warm (job 4) has no run, so its row has a NULL run_id, as the sample's first row does.
- The join is on job_id, so a job's several runs give several rows, one per run, as the query does. The Toolbox warns about a join on less than the whole key; the repeats are what this query gives.

Refused: none.

Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table. No charts or PivotTables.

To fill in: `<database>`, in each block below.

```sql
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON r.job_id = j.job_id
```

```sql
SELECT j.job_id, j.job_name, j.team
FROM <database>.jobs j
LEFT JOIN <database>.scheduler_runs s ON s.job_id = j.job_id
WHERE s.job_id IS NULL
```

Toolbox code:

```python
from sqlglot_composer import ANTI_JOIN, FROM, LEFT_JOIN, SELECT, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__scheduler_runs import scheduler_runs

jobs_with_runs = statement(
    SELECT(job_runs.run_id, jobs.job_name),
    FROM(jobs),
    LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id), reads_all_partitions=True),
)

never_scheduled = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team),
    FROM(jobs),
    ANTI_JOIN(scheduler_runs, ON=equals(scheduler_runs.job_id, jobs.job_id),
              reads_all_partitions=True),
)
```

Next steps: take out what you don't want; fill in `<database>`; save each query as jobs_with_runs.hql and never_scheduled.hql; then run the convert Workflow on them as one batch (file 13), with DEV filled in. Where the Workflow's checked code and this answer differ, the checked code wins.

## X45

Map:
- Sources: job_runs and scheduler_runs, their typed columns, read by the two queries below.
- Steps: none.
- Finals: run_days (run_id, dt), loaded by its Power Query; matched (run_id, job_id, dt, status), loaded by its Power Query. Nothing reads either Table.
- Parameters and Keys are empty; no value is typed over a formula.

Converted:
- run_days: Table.Combine of run_id and dt from both tables, then Table.Distinct, so a UNION of the two selects, which drops repeated rows.
- matched: JoinKind.FullOuter on run_id, so FULL OUTER JOIN, keeping every row of both tables; status comes from job_runs.

Marks:
- Run 99 is in job_runs only, so its row has NULL run_id, job_id and dt, with status TEST, as the sample's first row does. Those three columns come from scheduler_runs, as the query expands only status from job_runs.
- Run 100 is in scheduler_runs only, so its status is NULL, as the sample shows.
- Blank: run 98's status is blank in job_runs; it stays NULL.

Refused: none.

Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table. No charts or PivotTables.

To fill in: `<database>`, in each block below.

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

Toolbox code:

```python
from sqlglot_composer import FROM, FULL_JOIN, SELECT, UNION, equals, statement
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

run_days = UNION(
    statement(
        SELECT(job_runs.run_id, job_runs.dt),
        FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    ),
    statement(
        SELECT(scheduler_runs.run_id, scheduler_runs.dt),
        FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
    ),
)

matched = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt, job_runs.status),
    FROM(scheduler_runs),
    FULL_JOIN(job_runs, ON=equals(job_runs.run_id, scheduler_runs.run_id),
              reads_all_partitions=True),  # a workbook's query reads every row
)
```

Next steps: take out what you don't want; fill in `<database>`; save each query as run_days.hql and matched.hql; then run the convert Workflow on them as one batch (file 13), with DEV filled in. Where the Workflow's checked code and this answer differ, the checked code wins.

## X51

Map
- Sources: job_runs, read from `<database>.job_runs` (its typed columns run_id, job_id, status, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins).
- Parameters and Keys: none. Keys is empty, so there is no Keys row.

Typed over a formula: none.

Marks
- Blank: row 98 has no status. It stays NULL. not_ok counts it, as Excel's "<>SUCCESS" counts a blank, and failed_in_job skips it, as "*ail*" does. Both are in the -IFS form, so status is not wrapped in COALESCE.
- long_in_job: COUNTIFS over job_id and duration_mins > 15 is a count per job, a window with PARTITION BY job_id.
- not_ok: COUNTIFS on status alone has no match column, so it counts over the whole column, OVER ().
- failed_in_job: the wildcard "*ail*" is LOWER(status) LIKE '%ail%', as Excel ignores case.
- running_mins: SUMIFS with "<="&dt is a running total of each job's duration_mins, ties included, so RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW.

Refused: none.

Left alone: the Steps sheet's text, and the notes in D1 of the Parameters and Keys sheets (cells outside a Table). No charts or PivotTables.

Fill in: `<database>`, once, in the FROM.

Save the query as job_runs.hql, take out any column you don't want, fill in `<database>`, and run the convert Workflow on it as one batch with the others (file 13), DEV filled in.

```sql
SELECT
  run_id,
  job_id,
  status,
  duration_mins,
  dt,
  COALESCE(COUNT(CASE WHEN duration_mins > 15 THEN 1 END) OVER (PARTITION BY job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (status <> 'SUCCESS' OR status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY job_id), 0) AS failed_in_job,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs
```

## X52

Map
- Sources: job_runs, read from `<database>.job_runs` (its typed columns run_id, job_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job).
- Total Row: job_runs (Total Row) (duration_mins, share).
- Parameters and Keys: none. Keys is empty, so there is no Keys row.

Typed over a formula: none.

Marks
- share: duration_mins / SUM(duration_mins) over the whole column, OVER ().
- vs_avg: AVERAGE over the whole column, AVG(...) OVER ().
- rank_in_job: COUNTIFS(job_id match, duration_mins > this row's) + 1 is RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC); ties share a rank, as the COUNTIFS form gives them too.
- Total Row: the label "Total" is left out, as file 12 says a Total Row has no label. The blank cells under vs_avg and rank_in_job are not totals, so they are left out. The Total Row has a column per total, in order: duration_mins, then share.
- The share total adds up a formula column, so the share is worked out in a CTE and then summed; a window cannot sit inside SUM.

Refused: none.

Left alone: the Steps sheet's text and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).

Fill in: `<database>`, in the final and in the Total Row.

Save the final as job_runs.hql and the Total Row as job_runs (Total Row).hql, take out any column you don't want, fill in `<database>`, and run the convert Workflow on them as one batch (file 13), DEV filled in.

```sql
SELECT
  run_id,
  job_id,
  duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

```sql
WITH job_runs AS (
  SELECT
    duration_mins,
    duration_mins / SUM(duration_mins) OVER () AS share
  FROM <database>.job_runs
)
SELECT
  SUM(duration_mins) AS duration_mins,
  SUM(share) AS share
FROM job_runs
```

## X53

Map
- Sources: job_runs, read from `<database>.job_runs` (its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt). Only job_id and duration_mins are read by a formula.
- Steps: none.
- Finals: by_job (job_id, total_mins, runs, longest). by_job is a summary: its only typed column, job_id, is what its SUMIFS and COUNTIFS match on, so it is a GROUP BY of job_runs.
- Total Row: by_job (Total Row) (total_mins, runs, longest).
- Parameters and Keys: none. Keys is empty, so there is no Keys row.

Typed over a formula: none.

Marks
- The typed job_ids are 1, 2 and 3. The GROUP BY gives one row for each job_id in job_runs, which are these three, so every row of by_job holds.
- total_mins: SUMIFS on job_id is SUM(duration_mins) per job.
- runs: COUNTIFS on job_id is COUNT(*) per job, and it counts every job_runs row of the job, including the one with a blank status.
- longest: _xlfn.MAXIFS is MAX; the _xlfn. prefix is Excel's only.
- Total Row: SUBTOTAL 109 is SUM, and SUBTOTAL 104 is MAX. The label "Total" is left out. The Total Row is its own query and reads by_job as a CTE.
- Blank cells: row 98 has a blank status and a blank avg_retry_secs. No formula reads either, so they stay NULL and are not wrapped.

Refused: none.

Left alone: the Steps sheet's text and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).

Fill in: `<database>`, in the final and in the Total Row.

Save the final as by_job.hql and the Total Row as by_job (Total Row).hql, take out any column you don't want, fill in `<database>`, and run the convert Workflow on them as one batch (file 13), DEV filled in.

```sql
SELECT
  job_id,
  COALESCE(SUM(duration_mins), 0) AS total_mins,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(MAX(duration_mins), 0) AS longest
FROM <database>.job_runs
GROUP BY job_id
```

```sql
WITH by_job AS (
  SELECT
    job_id,
    COALESCE(SUM(duration_mins), 0) AS total_mins,
    COALESCE(COUNT(*), 0) AS runs,
    COALESCE(MAX(duration_mins), 0) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
)
SELECT
  SUM(total_mins) AS total_mins,
  SUM(runs) AS runs,
  MAX(longest) AS longest
FROM by_job
```

## X54

Map
- Sources: job_runs, read from `<database>.job_runs` (its typed columns run_id and dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label).
- Parameters and Keys: none. Keys is empty, so there is no Keys row.

Typed over a formula: none.

Marks
- a_month_on: EDATE is ADD_MONTHS, and a month's end stays one, as Excel does. No date in the sample is a month's end, so no row moves.
- week_of: d - WEEKDAY(d, 2) + 1, the Monday of the week, is written in the week-start form, and cast to text as that form gives.
- month_of: DATE(YEAR, MONTH, 1), the first of the month, is written in the month-start form, cast to text.
- weekday: WEEKDAY(d) with Excel's default, Sunday 1 to Saturday 7, is DAYOFWEEK, which counts the same way.
- label: TEXT(dt, "yyyy-mm") is DATE_FORMAT(dt, 'yyyy-MM').
- dt is written as 2026-09-23, not in the 20260911 text form, so no text-date conversion is needed.
- Blank cells: none.

Refused: none.

Left alone: the Steps sheet's text and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).

Fill in: `<database>`, once, in the FROM.

Save the query as job_runs.hql, take out any column you don't want, fill in `<database>`, and run the convert Workflow on it as one batch with the others (file 13), DEV filled in.

```sql
SELECT
  run_id,
  dt,
  LAST_DAY(dt) AS month_end,
  ADD_MONTHS(dt, 1) AS a_month_on,
  DATE_ADD(dt, 7) AS due,
  CAST(NEXT_DAY(DATE_ADD(dt, 7 * -1), 'MO') AS STRING) AS week_of,
  CAST(TRUNC(dt, 'MM') AS STRING) AS month_of,
  DAYOFWEEK(dt) AS weekday,
  DATE_FORMAT(dt, 'yyyy-MM') AS label
FROM <database>.job_runs
```

## X55

Map
- Sources: jobs, read from `<database>.jobs` (its typed columns job_id, job_name, team, region).
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens).
- Parameters and Keys: none. Keys is empty, so there is no Keys row.

Typed over a formula: none.

Marks
- title: PROPER(SUBSTITUTE(job_name, "_", " ")) is INITCAP(REPLACE(job_name, '_', ' ')).
- tag: TEXTJOIN("/", TRUE, team, region) is CONCAT_WS('/', team, region). TEXTJOIN's TRUE skips blanks, and CONCAT_WS skips NULLs; the sample has no blank, so nothing changes.
- code: CONCATENATE is CONCAT.
- has_sync: ISNUMBER(SEARCH("SYNC", job_name)) is INSTR(LOWER(job_name), LOWER('SYNC')) > 0, as SEARCH ignores case.
- tens: VALUE(job_id & "0") is CAST(CONCAT(job_id, '0') AS DOUBLE), so the values are 10, 20, 30 and 40.

Refused: none.

Left alone: the Steps sheet's text and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).

Fill in: `<database>`, once, in the FROM.

Save the query as jobs.hql, take out any column you don't want, fill in `<database>`, and run the convert Workflow on it as one batch with the others (file 13), DEV filled in.

```sql
SELECT
  job_id,
  job_name,
  team,
  region,
  INITCAP(REPLACE(job_name, '_', ' ')) AS title,
  CONCAT_WS('/', team, region) AS tag,
  CONCAT(region, '-', job_id) AS code,
  INSTR(LOWER(job_name), LOWER('SYNC')) > 0 AS has_sync,
  CAST(CONCAT(job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs
```

## X51 to X55: what is not in these answers

- No Toolbox (Python) code is written here, as the request asks for Hive SQL only. Ask for it and it follows files 03, 04 and 05.
- None of the five workbooks has a value typed over a formula, a refused formula, or a Keys row, so no Keys row is needed.

## X56

Map

- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs) and scheduler_runs (typed columns run_id, job_id, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on). job_runs is both a source and a final, as nothing else reads its formula columns.
- Parameters: none. Keys: none. Nothing is typed over a formula, so no Keys row is needed.

Converted

- no_status: ISBLANK becomes `status IS NULL`. The blank status of run 98 is skipped by ISBLANK, so no COALESCE.
- weeks: INT becomes FLOOR(duration_mins / 7).
- at_least_20: MAX of one row's cells becomes GREATEST(duration_mins, 20).
- spread: STDEV.S of the whole column becomes STDDEV_SAMP(...) OVER (), the same value on every row.
- weighted: SUMPRODUCT of two whole columns becomes SUM(a * b) OVER (). Blank: avg_retry_secs is blank on run 98, so the formula wraps it, COALESCE(avg_retry_secs, 0). The plain avg_retry_secs column stays as the sample has it.
- scheduled_on: XLOOKUP becomes a LEFT JOIN to scheduler_runs on run_id, with the fourth argument as COALESCE. Run 99 has no scheduler row, so it reads 'unscheduled'. scheduler_runs has one row per run_id, so no row doubles.

Refused: none. Left alone: nothing.

Fill in: `<database>` in the FROM and the JOIN.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  r.status IS NULL AS no_status,
  FLOOR(r.duration_mins / 7) AS weeks,
  GREATEST(r.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(r.duration_mins) OVER () AS spread,
  SUM(r.duration_mins * COALESCE(r.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(s.dt, 'unscheduled') AS scheduled_on
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, at_least, equals, fill_null,
                              if_else, is_null, statement, sum_of, window)
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

whole_column = window()  # no PARTITION_BY: every row of the column

# weeks (FLOOR) and spread (STDDEV_SAMP) have no name in files 03 to 05, so the SQL keeps them.
job_runs_final = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs,
           AS(if_else(is_null(job_runs.status), True, False), "no_status"),
           AS(if_else(at_least(job_runs.duration_mins, 20), job_runs.duration_mins, 20),
              "at_least_20"),
           AS(sum_of(job_runs.duration_mins * fill_null(job_runs.avg_retry_secs, 0),
                     over=whole_column), "weighted"),
           AS(fill_null(scheduler_runs.dt, "unscheduled"), "scheduled_on")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id),
              reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out what you don't want, fill in each `<database>`, and save the query as job_runs.hql. Then run the convert Workflow on it as one batch (file 13), with DEV filled in. Where the Workflow's checked code and this differ, the checked code wins.

## X57

Map

- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (typed columns job_id, job_name, team, region).
- Steps: none. No query reads another query, and no Table has formulas.
- Finals: picked (run_id, job_id, status, avg_retry_secs, status_lc) and ran_jobs (job_id, job_name, team, region).
- Parameters: none. Keys: none. Nothing is typed over, and there are no formulas.

Converted

- picked: `[status] = null` becomes `status IS NULL`. Run 98's status is blank; Power Query reads it as null, so Hive's NULL matches it and the row passes the filter. No COALESCE on status.
- picked: List.Contains({1, 2}, [job_id]) becomes `job_id IN (1, 2)`.
- picked: Text.StartsWith([status], "S") becomes `status LIKE 'S%'`, case kept.
- picked: the ReplaceValue of null to 0 on avg_retry_secs becomes COALESCE(avg_retry_secs, 0). Blank: run 98's avg_retry_secs is blank and becomes 0, as the sample shows.
- picked: Text.Lower becomes LOWER(status) AS status_lc. Run 98's status_lc stays NULL, as the sample shows it blank.
- ran_jobs: List.Contains(Runs[job_id], [job_id]) reads as the job_id values of job_runs, so it becomes a LEFT SEMI JOIN on job_runs.
- ran_jobs: Text.Contains([job_name], "a") becomes `job_name LIKE '%a%'`, case kept.

Refused: none. Left alone: nothing.

Fill in: `<database>` in each FROM and JOIN.

```sql
-- picked
SELECT r.run_id, r.job_id, r.status,
  COALESCE(r.avg_retry_secs, 0) AS avg_retry_secs,
  LOWER(r.status) AS status_lc
FROM <database>.job_runs r
WHERE r.job_id IN (1, 2)
  AND (r.status IS NULL OR r.status LIKE 'S%')
```

```sql
-- ran_jobs
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs u ON u.job_id = j.job_id
WHERE j.job_name LIKE '%a%'
```

```python
from sqlglot_composer import (AS, FROM, SELECT, SEMI_JOIN, WHERE, all_columns, any_of, contains,
                              equals, fill_null, is_in, is_null, starts_with, statement)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

# picked: Text.Lower (status_lc) has no name in files 03 to 05, so the SQL keeps it.
picked = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status,
           AS(fill_null(job_runs.avg_retry_secs, 0), "avg_retry_secs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_in(job_runs.job_id, [1, 2]),
          any_of(is_null(job_runs.status), starts_with(job_runs.status, "S"))),
)

# ran_jobs: the jobs that have a run, with "a" in the name
ran_jobs = statement(
    SELECT(*all_columns(jobs)),
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
    SEMI_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id),
              reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(contains(jobs.job_name, "a")),
)
```

Take out what you don't want, fill in each `<database>`, and save each final's query as a .hql file named for its Table: picked.hql and ran_jobs.hql. Then run the convert Workflow on them as one batch (file 13), with DEV filled in. Where the Workflow's checked code and this differ, the checked code wins.

## X58

Map

- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt), jobs (job_id, job_name, team, region), scheduler_runs (run_id, job_id, dt) and region_budgets (job_id, budget_cents, region).
- Steps: none. No query reads another query, and no Table has formulas.
- Finals: job_regions (job_id, region), numbered (run_id, dt, duration_mins, n), days_per_job (job_id, days), unrun (run_id, job_id) and measures (run_id, measure, amount).
- Parameters: none. Keys: none. Nothing is typed over, and there are no formulas.

Converted

- job_regions: Table.AddColumn with each Regions, then expanded, is a CROSS JOIN of the jobs with the distinct regions of region_budgets (eu and us), 8 rows.
- numbered: Table.Sort then Table.AddIndexColumn becomes ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC) AS n. The index carries the sort, so no ORDER BY is kept on the final; the rows come out in no order.
- days_per_job: List.Count(List.Distinct([dt])) becomes COUNT(DISTINCT dt). The sort after the group has no FirstN or index after it, so the order is dropped, and no ORDER BY is written. dt has no blanks, so no NULL caveat.
- unrun: the LeftAnti NestedJoin on both columns, its new column removed inside Table.Distinct, is EXCEPT. It gives run 100 (job 3), the one scheduled run with no job run.
- measures: Table.UnpivotOtherColumns becomes one SELECT per unpivoted column, stacked with UNION ALL, each with WHERE ... IS NOT NULL. Blank: run 98's avg_retry_secs is blank, so it drops out, as M drops a null there. The sample has 17 rows.

Refused: none. Left alone: nothing.

Fill in: `<database>` in each FROM and JOIN.

```sql
-- job_regions
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN (SELECT DISTINCT b.region FROM <database>.region_budgets b) r
```

```sql
-- numbered
SELECT t.run_id, t.dt, t.duration_mins,
  ROW_NUMBER() OVER (ORDER BY t.duration_mins DESC, t.run_id ASC) AS n
FROM <database>.job_runs t
```

```sql
-- days_per_job
SELECT t.job_id, COUNT(DISTINCT t.dt) AS days
FROM <database>.job_runs t
GROUP BY t.job_id
```

```sql
-- unrun
SELECT s.run_id, s.job_id
FROM <database>.scheduler_runs s
EXCEPT
SELECT r.run_id, r.job_id
FROM <database>.job_runs r
```

```sql
-- measures
SELECT r.run_id, 'duration_mins' AS measure, r.duration_mins AS amount
FROM <database>.job_runs r
WHERE r.duration_mins IS NOT NULL
UNION ALL
SELECT r.run_id, 'avg_retry_secs' AS measure, r.avg_retry_secs AS amount
FROM <database>.job_runs r
WHERE r.avg_retry_secs IS NOT NULL
```

```python
from sqlglot_composer import (AS, CROSS_JOIN, EXCEPT, FROM, GROUP_BY, SELECT, SELECT_DISTINCT,
                              UNION_ALL, WHERE, count_distinct, derived, descending, is_not_null,
                              row_number, statement)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets
from references.ops__scheduler_runs import scheduler_runs

# job_regions: every job with every distinct region
regions = derived("regions", statement(
    SELECT_DISTINCT(region_budgets.region),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's query reads every row
))
job_regions = statement(
    SELECT(jobs.job_id, regions.region),
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
    CROSS_JOIN(regions),
)

# numbered: the row number by duration, largest first, then by run_id
numbered = statement(
    SELECT(job_runs.run_id, job_runs.dt, job_runs.duration_mins,
           AS(row_number(ORDER_BY=[descending(job_runs.duration_mins), job_runs.run_id]), "n")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)

# days_per_job: the sort is dropped, as a Hive table holds no order
days_per_job = statement(
    SELECT(job_runs.job_id, AS(count_distinct(job_runs.dt), "days")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
)

# unrun: scheduled runs with no matching job run
scheduled = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
ran = statement(
    SELECT(job_runs.run_id, job_runs.job_id),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
unrun = EXCEPT(scheduled, ran)

# measures: each measure's rows, stacked, blanks dropped.
# The text label is a literal; files 03 to 05 show none, so check its form against the checked code.
duration_rows = statement(
    SELECT(job_runs.run_id, AS("duration_mins", "measure"), AS(job_runs.duration_mins, "amount")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_not_null(job_runs.duration_mins)),
)
retry_rows = statement(
    SELECT(job_runs.run_id, AS("avg_retry_secs", "measure"), AS(job_runs.avg_retry_secs, "amount")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_not_null(job_runs.avg_retry_secs)),
)
measures = UNION_ALL(duration_rows, retry_rows)
```

Take out what you don't want, fill in each `<database>`, and save each final's query as a .hql file named for its Table: job_regions.hql, numbered.hql, days_per_job.hql, unrun.hql and measures.hql. Then run the convert Workflow on them as one batch (file 13), with DEV filled in. Where the Workflow's checked code and this differ, the checked code wins.

## X67

Map

- Sources: job_runs (typed columns run_id, job_id, duration_mins, dt), jobs (job_id, job_name, team, region) and run_alerts (alert_id, run_id, severity, dt).
- Steps: job_runs. Its formula columns team, alerts and running_mins are read by by_team and by noisy_runs, so it is a step, a CTE inside each of those finals' queries.
- Finals: noisy_runs (run_id, team, alerts, running_mins); by_team (team, total_mins, alerted_runs), a summary, a GROUP BY of job_runs; and by_team (Total Row), a query of its own with one column per total, no label. Its Total Row reads by_team as a CTE, and the Total Row is never in by_team's own query.
- Parameters: none. Keys: none. Nothing is typed over a formula.

Converted

- team: XLOOKUP becomes a LEFT JOIN to jobs on job_id, then jobs.team.
- alerts: COUNTIF(run_alerts[run_id], [@run_id]), the -IFS form with one match, over another Table becomes a LEFT JOIN to a count of run_alerts per run_id, with COALESCE to 0.
- running_mins: SUMIFS over its own Table with "<=" on dt is a running total, SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), with COALESCE to 0. Ties are included as Excel includes them: runs 95 and 99 share the date 2026-09-23 and both show 17.
- total_mins: SUMIFS over the team becomes SUM in the GROUP BY, with COALESCE to 0.
- alerted_runs: COUNTIFS(team, [@team], alerts, ">0") becomes COUNT of the rows with alerts > 0 in the group, with COALESCE to 0.
- Total Row: SUBTOTAL(109, ...) becomes SUM, with no label.
- noisy_runs: Table.SelectRows with [alerts] >= 2 becomes WHERE alerts >= 2.

Marks

- The running total's ties are counted as Excel counts them. The Toolbox's window takes rows= only, which counts a tie one row at a time, so its checked code will differ on ties here (95 and 99). The SQL keeps RANGE.
- The sample has no blanks in the columns the formulas read.

Refused: none. Left alone: nothing.

Fill in: `<database>` in each FROM and JOIN.

```sql
-- noisy_runs
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(al.n, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS n FROM <database>.run_alerts GROUP BY run_id) al
    ON r.run_id = al.run_id
)
SELECT k.run_id, k.team, k.alerts, k.running_mins
FROM job_runs k
WHERE k.alerts >= 2
```

```sql
-- by_team
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(al.n, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS n FROM <database>.run_alerts GROUP BY run_id) al
    ON r.run_id = al.run_id
)
SELECT k.team,
  COALESCE(SUM(k.duration_mins), 0) AS total_mins,
  COALESCE(COUNT(CASE WHEN k.alerts > 0 THEN 1 END), 0) AS alerted_runs
FROM job_runs k
GROUP BY k.team
```

```sql
-- by_team (Total Row)
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(al.n, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS n FROM <database>.run_alerts GROUP BY run_id) al
    ON r.run_id = al.run_id
),
by_team AS (
  SELECT k.team,
    COALESCE(SUM(k.duration_mins), 0) AS total_mins,
    COALESCE(COUNT(CASE WHEN k.alerts > 0 THEN 1 END), 0) AS alerted_runs
  FROM job_runs k
  GROUP BY k.team
)
SELECT SUM(b.total_mins) AS total_mins, SUM(b.alerted_runs) AS alerted_runs
FROM by_team b
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, at_least, count_rows,
                              derived, equals, fill_null, more_than, statement, sum_of, window)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

# COUNTIF over run_alerts: one count per run_id
alert_counts = derived("alert_counts", statement(
    SELECT(run_alerts.run_id, AS(count_rows(), "n")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(run_alerts.run_id),
))

# job_runs as a step: team, alerts and running_mins.
# The window takes rows= only, so a tie is counted one row at a time (see the marks).
each_job = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt, rows=(None, 0))
runs = derived("runs", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           jobs.team,
           AS(fill_null(alert_counts.n, 0), "alerts"),
           AS(fill_null(sum_of(job_runs.duration_mins, over=each_job), 0), "running_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    LEFT_JOIN(alert_counts, ON=equals(alert_counts.run_id, job_runs.run_id)),
))

# noisy_runs
noisy_runs = statement(
    SELECT(runs.run_id, runs.team, runs.alerts, runs.running_mins),
    FROM(runs),
    WHERE(at_least(runs.alerts, 2)),
)

# by_team: a summary of runs, one row per team
by_team_rows = derived("by_team", statement(
    SELECT(runs.team, AS(sum_of(runs.duration_mins), "total_mins"),
           AS(count_rows(where=more_than(runs.alerts, 0)), "alerted_runs")),
    FROM(runs),
    GROUP_BY(runs.team),
))
by_team = statement(
    SELECT(by_team_rows.team, by_team_rows.total_mins, by_team_rows.alerted_runs),
    FROM(by_team_rows),
)

# by_team (Total Row): SUBTOTAL(109) is a SUM, with no label
by_team_total = statement(
    SELECT(AS(sum_of(by_team_rows.total_mins), "total_mins"),
           AS(sum_of(by_team_rows.alerted_runs), "alerted_runs")),
    FROM(by_team_rows),
)
```

Take out what you don't want, fill in each `<database>`, and save each final's query as a .hql file named for its Table: noisy_runs.hql, by_team.hql, and by_team_total_row.hql for the Total Row. Then run the convert Workflow on them as one batch (file 13), with DEV filled in. Where the Workflow's checked code and this differ, the checked code wins, and the running total's ties are the case to check.

## X68

Map

- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt), jobs (job_id, job_name, team, region) and region_budgets (job_id, budget_cents, region).
- Steps: base, a connection-only query that two queries read (by_region and top_runs). Its CTE is in each of those finals' queries. base takes job_name from jobs and region from region_budgets, not from jobs' own region column; the sample's eu totals confirm it.
- Finals: by_region (region, total_mins, runs, share) and top_runs (run_id, job_name, region), with by_region (Total Row) as a separate query of one column, total_mins, no label.
- Parameters: none. Keys: none. Nothing is typed over a formula.

Converted

- base: Table.NestedJoin Inner on job_id becomes a JOIN to jobs, and LeftOuter becomes a LEFT JOIN to region_budgets. Each run gets its job's name and budget region.
- by_region: Table.Group by region with List.Sum and Table.RowCount becomes GROUP BY region with SUM and COUNT(*). Table.SelectRows on runs >= 2, after the group, becomes HAVING COUNT(*) >= 2.
- share: `[total_mins] / SUM(by_region[total_mins])` becomes total_mins / SUM(total_mins) OVER (), over the kept rows.
- top_runs: Table.Sort by duration_mins descending then run_id ascending, with FirstN 2, becomes ORDER BY duration_mins DESC, run_id ASC LIMIT 2. The tie at 30 (runs 97 and 103) goes to 97 by run_id.
- Total Row: SUBTOTAL(109, by_region[total_mins]) becomes SUM(total_mins), with no label. Only total_mins has a total.

Marks

- Blank: run 98's status and avg_retry_secs are blank, and they pass through base as NULL. No output reads them, so nothing is wrapped.

Refused: none. Left alone: nothing.

Fill in: `<database>` in each FROM and JOIN.

```sql
-- by_region
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
kept AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT region, total_mins, runs,
  total_mins / SUM(total_mins) OVER () AS share
FROM kept
```

```sql
-- top_runs
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT b.run_id, b.job_name, b.region
FROM base b
ORDER BY b.duration_mins DESC, b.run_id ASC
LIMIT 2
```

```sql
-- by_region (Total Row)
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
kept AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT SUM(k.total_mins) AS total_mins
FROM kept k
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, HAVING, JOIN, LEFT_JOIN, LIMIT, ORDER_BY, SELECT,
                              all_columns, at_least, count_rows, derived, descending, equals,
                              statement, sum_of, window)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets

# base: each run with its job's name and the region its budget gives
base = derived("base", statement(
    SELECT(*all_columns(job_runs), jobs.job_name, region_budgets.region),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    LEFT_JOIN(region_budgets, ON=equals(region_budgets.job_id, job_runs.job_id)),
))

# kept: one row per region with at least 2 runs (the group's HAVING)
kept = derived("kept", statement(
    SELECT(base.region, AS(sum_of(base.duration_mins), "total_mins"), AS(count_rows(), "runs")),
    FROM(base),
    GROUP_BY(base.region),
    HAVING(at_least(count_rows(), 2)),
))

# by_region: share is each total over the total of the kept rows
by_region = statement(
    SELECT(kept.region, kept.total_mins, kept.runs,
           AS(kept.total_mins / sum_of(kept.total_mins, over=window()), "share")),
    FROM(kept),
)

# top_runs: the two longest runs, ties by run_id
top_runs = statement(
    SELECT(base.run_id, base.job_name, base.region),
    FROM(base),
    ORDER_BY(descending(base.duration_mins), base.run_id),
    LIMIT(2),
)

# by_region (Total Row): SUBTOTAL(109) is a SUM, with no label
by_region_total = statement(
    SELECT(AS(sum_of(kept.total_mins), "total_mins")),
    FROM(kept),
)
```

Take out what you don't want, fill in each `<database>`, and save each final's query as a .hql file named for its Table: by_region.hql, top_runs.hql, and by_region_total_row.hql for the Total Row. Then run the convert Workflow on them as one batch (file 13), with DEV filled in. Where the Workflow's checked code and this differ, the checked code wins.

## X71

**Map**

- Sources: `job_runs` (run_id, job_id, status, duration_mins are read; avg_retry_secs and dt are not used by any final). It is a typed Table that no query loads.
- Steps: query `ok_runs` (the SUCCESS rows of job_runs, with run_id, job_id, duration_mins). Query `ok_by_job` reads it, so it is a CTE `ok_runs` inside each final's query.
- Finals:
  - `ok_runs` (run_id, job_id, duration_mins, hours). Its Table is loaded by the query, and nothing reads the Table, so it is a final. Its formula column `hours` is kept.
  - `ok_by_job` (job_id, total_mins). Table.Group, and nothing reads it.
- Parameters: none, the Table is empty. Keys: none, since no value is typed over a formula.
- Typed over a formula: none.
- Marks:
  - `hours` (`=ok_runs[[#This Row],[duration_mins]]/60`) converts to `duration_mins / 60 AS hours`.
  - Table.Group with List.Sum converts to SUM(duration_mins) AS total_mins, grouped by job_id.
  - Blank: job_runs row 98 has a blank status. Hive reads it as NULL. The filter `[status] = "SUCCESS"` drops it in M and the Hive WHERE drops it too, so it stays NULL and the row stays out.
- Refusals: none.
- Left alone: none (no charts, PivotTables or cells outside a Table).
- To fill in: `<database>`.

**Hive, one block per final**

`ok_runs`:

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT run_id, job_id, duration_mins, duration_mins / 60 AS hours
FROM ok_runs
```

`ok_by_job`:

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

**Toolbox code**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, derived, equals, statement,
                              sum_of)
from references.<database>__job_runs import job_runs

# a workbook's query reads every row
ok_runs = derived("ok_runs", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(equals(job_runs.status, "SUCCESS")),
))

ok_runs_table = statement(
    SELECT(ok_runs.run_id, ok_runs.job_id, ok_runs.duration_mins,
           AS(ok_runs.duration_mins / 60, "hours")),
    FROM(ok_runs),
)

ok_by_job_table = statement(
    SELECT(ok_runs.job_id, AS(sum_of(ok_runs.duration_mins), "total_mins")),
    FROM(ok_runs),
    GROUP_BY(ok_runs.job_id),
)
```

Take out what you don't want, and fill in `<database>`. Save each final's query as a .hql file named for its Table: `ok_runs.hql` and `ok_by_job.hql`. Then run the convert Workflow on them as one batch (Copilot file 13, which you load in a new chat), with DEV filled in. Where the checked code and this differ, the checked code wins.

## X72

**Map**

- Sources:
  - `job_runs` (job_id and duration_mins are read by the formulas). It is a typed Table that no query loads.
  - `jobs` (job_id, job_name, team, its typed columns).
- Steps: `jobs`, with its formula columns `runs` and `total`. The formulas in by_team and the query busy_jobs read the Table jobs, so it is a CTE `jobs` inside each final's query that reads it.
- Finals:
  - `busy_jobs` (job_id, job_name, runs). The Table is loaded by the query busy_jobs, and nothing reads it.
  - `by_team` (team, team_total). Its only typed column is `team`, which its SUMIFS matches on, so it is a summary: a GROUP BY of jobs.
- Parameters: none, the Table is empty. Keys: none, since no value is typed over a formula.
- Typed over a formula: none.
- Marks:
  - `runs` (`COUNTIF(job_runs[job_id], [@job_id])`) converts to COUNT(*) per job_id from job_runs, joined with LEFT JOIN, COALESCE(.., 0). Job 4 has no runs, so it gives 0.
  - `total` (`SUMIF(job_runs[job_id], [@job_id], job_runs[duration_mins])`) converts to SUM(duration_mins) per job_id from job_runs, joined with LEFT JOIN, COALESCE(.., 0). Job 4 gives 0.
  - busy_jobs: the filter `[runs] >= 3` tests the step's runs, so it is `WHERE runs >= 3` on the CTE, where the calculated column is already named.
  - by_team: the rows are the teams that jobs holds (data, finance, web). A GROUP BY gives no row for a team with no job, where SUMIFS would give 0. No team here is without a job.
  - Table.SelectColumns in busy_jobs is the SELECT list.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>`.

**Hive, one block per final**

`busy_jobs`:

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(r.runs, 0) AS runs,
    COALESCE(s.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
    ON j.job_id = r.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) s
    ON j.job_id = s.job_id
)
SELECT job_id, job_name, runs
FROM jobs
WHERE runs >= 3
```

`by_team`:

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(r.runs, 0) AS runs,
    COALESCE(s.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
    ON j.job_id = r.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) s
    ON j.job_id = s.job_id
)
SELECT team, SUM(total) AS team_total
FROM jobs
GROUP BY team
```

**Toolbox code**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, at_least,
                              count_rows, derived, equals, fill_null, statement, sum_of)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

# a workbook's query reads every row
run_counts = derived("run_counts", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "runs")),
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
))
run_minutes = derived("run_minutes", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
))
job_step = derived("jobs", statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(fill_null(run_counts.runs, 0), "runs"),
           AS(fill_null(run_minutes.total, 0), "total")),
    FROM(jobs, reads_all_partitions=True),
    LEFT_JOIN(run_counts, ON=equals(run_counts.job_id, jobs.job_id)),
    LEFT_JOIN(run_minutes, ON=equals(run_minutes.job_id, jobs.job_id)),
))

busy_jobs_table = statement(
    SELECT(job_step.job_id, job_step.job_name, job_step.runs),
    FROM(job_step),
    WHERE(at_least(job_step.runs, 3)),
)

by_team_table = statement(
    SELECT(job_step.team, AS(sum_of(job_step.total), "team_total")),
    FROM(job_step),
    GROUP_BY(job_step.team),
)
```

Take out what you don't want, and fill in each `<database>`. Save each final's query as a .hql file named for its Table: `busy_jobs.hql` and `by_team.hql`. Then run the convert Workflow on them as one batch (Copilot file 13, which you load in a new chat), with DEV filled in. Where the checked code and this differ, the checked code wins.

## X75

**Map**

- Sources: `job_runs` (run_id, dt and duration_mins are read; status, job_id and avg_retry_secs are not used). It is a typed Table that no query loads.
- Steps: query `long_runs` (the rows of job_runs with duration_mins at least 15, with run_id, dt, duration_mins). Query `long_per_day` reads it, so it is a CTE `long_runs` inside each final's query.
- Finals:
  - `long_runs` (run_id, dt, duration_mins, over). Its Table is loaded by the query, and nothing reads the Table. Its formula column `over` is kept.
  - `long_per_day` (dt, runs). Table.Group, and nothing reads it.
- Parameters: none, the Table is empty. Keys: none, since no value is typed over a formula.
- Typed over a formula: none.
- Marks:
  - `over` (`=long_runs[[#This Row],[duration_mins]]-15`) converts to `duration_mins - 15 AS over`. `over` is a word Hive reserves, so the SQL writes it in backticks; the header stays `over`.
  - Table.RowCount in Table.Group converts to COUNT(*) AS runs, grouped by dt.
  - Blanks: none in duration_mins or dt, so no blank mark.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>`.

**Hive, one block per final**

`long_runs`:

```sql
WITH long_runs AS (
  SELECT run_id, dt, duration_mins
  FROM <database>.job_runs
  WHERE duration_mins >= 15
)
SELECT run_id, dt, duration_mins, duration_mins - 15 AS `over`
FROM long_runs
```

`long_per_day`:

```sql
WITH long_runs AS (
  SELECT run_id, dt, duration_mins
  FROM <database>.job_runs
  WHERE duration_mins >= 15
)
SELECT dt, COUNT(*) AS runs
FROM long_runs
GROUP BY dt
```

**Toolbox code**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, at_least, count_rows,
                              derived, statement)
from references.<database>__job_runs import job_runs

# a workbook's query reads every row
long_runs = derived("long_runs", statement(
    SELECT(job_runs.run_id, job_runs.dt, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(at_least(job_runs.duration_mins, 15)),
))

long_runs_table = statement(
    SELECT(long_runs.run_id, long_runs.dt, long_runs.duration_mins,
           AS(long_runs.duration_mins - 15, "over")),
    FROM(long_runs),
)

long_per_day_table = statement(
    SELECT(long_runs.dt, AS(count_rows(), "runs")),
    FROM(long_runs),
    GROUP_BY(long_runs.dt),
)
```

Take out what you don't want, and fill in `<database>`. Save each final's query as a .hql file named for its Table: `long_runs.hql` and `long_per_day.hql`. Then run the convert Workflow on them as one batch (Copilot file 13, which you load in a new chat), with DEV filled in. Where the checked code and this differ, the checked code wins.

## X76

**Map**

- Sources:
  - `job_runs` (run_id, job_id and duration_mins are read; status, avg_retry_secs and dt are not used). It is a typed Table that no query loads.
  - `jobs` (job_id, job_name and team are read; region is not used). It is a typed Table that no query loads.
- Steps: query `finance_jobs` (the finance rows of jobs, with job_id and job_name). Query `finance_runs` reads it, so it is a CTE `finance_jobs` inside each final's query that reads it. The Table finance_jobs' formula column `label` is read by no formula, so it is not a step.
- Finals:
  - `finance_jobs` (job_id, job_name, label). Its Table is loaded by the query, and nothing reads the Table.
  - `finance_runs` (run_id, job_name, duration_mins). Its query inner-joins job_runs to the finance_jobs step, and nothing reads it.
- Parameters: none, the Table is empty. Keys: none, since no value is typed over a formula.
- Typed over a formula: none.
- Marks:
  - `label` (`=UPPER(finance_jobs[[#This Row],[job_name]])`) converts to `UPPER(job_name) AS label`.
  - Table.SelectRows with `[team] = "finance"` converts to `team = 'finance'`.
  - Table.NestedJoin with JoinKind.Inner converts to JOIN; the expanded job_name keeps its name.
  - Blank: job_runs row 98 has a blank status. No step reads status, so the row stays in finance_runs, as it does in M.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>`.

**Hive, one block per final**

`finance_jobs`:

```sql
WITH finance_jobs AS (
  SELECT job_id, job_name
  FROM <database>.jobs
  WHERE team = 'finance'
)
SELECT job_id, job_name, UPPER(job_name) AS label
FROM finance_jobs
```

`finance_runs`:

```sql
WITH finance_jobs AS (
  SELECT job_id, job_name
  FROM <database>.jobs
  WHERE team = 'finance'
)
SELECT r.run_id, f.job_name, r.duration_mins
FROM <database>.job_runs r
JOIN finance_jobs f ON r.job_id = f.job_id
```

**Toolbox code**

```python
from sqlglot_composer import AS, FROM, JOIN, SELECT, WHERE, derived, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

# a workbook's query reads every row
finance_jobs = derived("finance_jobs", statement(
    SELECT(jobs.job_id, jobs.job_name),
    FROM(jobs, reads_all_partitions=True),
    WHERE(equals(jobs.team, "finance")),
))

# The label column, UPPER(job_name), is left out here: UPPER has no name in files 03 to 05.
# Load file 10 (labels, Hive functions) in a new chat to add it.
finance_jobs_table = statement(
    SELECT(finance_jobs.job_id, finance_jobs.job_name),
    FROM(finance_jobs),
)

finance_runs = statement(
    SELECT(job_runs.run_id, finance_jobs.job_name, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),
    JOIN(finance_jobs, ON=equals(finance_jobs.job_id, job_runs.job_id)),
)
```

Take out what you don't want, and fill in each `<database>`. Save each final's query as a .hql file named for its Table: `finance_jobs.hql` and `finance_runs.hql`. Then run the convert Workflow on them as one batch (Copilot file 13, which you load in a new chat), with DEV filled in. Where the checked code and this differ, the checked code wins. The label column's UPPER is not in the Python above, so take it from the Hive block, or load file 10 for it.

