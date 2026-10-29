date: 2026-10-29
arm: C
model: haiku
files: a596632

## X01

Map:
- Sources: job_runs (run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours).

Typed over a formula: none.
Marks: none.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
  r.duration_mins / 60 AS duration_hours
FROM <database>.job_runs r
```

```python
# reads_all_partitions=True: the workbook's formula reads every row, so every partition
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(job_runs.duration_mins / 60, "duration_hours")),
    FROM(job_runs, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X02

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag).

Typed over a formula: none.
Marks: none. The blank status in run 98 is not read by either formula, so it stays NULL.
Refused: none.
Left alone: none.
Fill in: `<database>`.

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
    FROM(job_runs),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X03

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs).

Typed over a formula: none.
Marks:
- blank: status and avg_retry_secs are blank in run 98, and both are read by formulas. Each formula wraps the blank (COALESCE(status, ''), COALESCE(avg_retry_secs, 0)). The typed columns stay as they are.
- IFERROR(duration_mins / avg_retry_secs, 0) becomes COALESCE(duration_mins / ..., 0).
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
  CASE COALESCE(r.status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(r.duration_mins / COALESCE(r.avg_retry_secs, 0), 0) AS mins_per_retry,
  r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs r
```

```python
# reads_all_partitions=True: the workbook's formulas read every row, so every partition
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, first_match, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt,
           AS(first_match([(equals(job_runs.status, "SUCCESS"), 1),
                           (equals(job_runs.status, "FAILED"), -1)], otherwise=0), "score"),
           AS(fill_null(job_runs.duration_mins / fill_null(job_runs.avg_retry_secs, 0), 0), "mins_per_retry"),
           AS(job_runs.duration_mins * 60 + fill_null(job_runs.avg_retry_secs, 0), "total_secs")),
    FROM(job_runs, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X04

Map:
- Sources: none beyond jobs.
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd).

Sources: jobs (job_id, job_name, team, region).
Typed over a formula: none.
Marks: none. No blanks in the sample.
Refused: none.
Left alone: none.
Fill in: `<database>`.

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

# code, name_length, third and odd use UPPER, SUBSTR, CONCAT, LENGTH, ROUND and PMOD,
# which files 03 to 05 don't name, so project.convert writes them from the Hive
s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X05

Map:
- Sources: job_runs (run_id, dt); region_costs (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month, days_since); region_costs (job_id, cost_cents, region, dt, day).

Typed over a formula: none.
Marks:
- A date held as text: region_costs dt (20260911 and so on). day uses the text form: CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)).
- DATEDIF(DATE(2026,9,1), dt, "d") becomes DATEDIFF(dt, '2026-09-01').
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
-- final: job_runs
SELECT r.run_id, r.dt,
  MONTH(r.dt) AS month,
  DATEDIFF(r.dt, '2026-09-01') AS days_since
FROM <database>.job_runs r

-- final: region_costs
SELECT c.job_id, c.cost_cents, c.region, c.dt,
  CONCAT(SUBSTR(c.dt, 1, 4), '-', SUBSTR(c.dt, 5, 2), '-', SUBSTR(c.dt, 7, 2)) AS day
FROM <database>.region_costs c
```

```python
# reads_all_partitions=True: the workbook's formulas read every row, so every partition
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__job_runs import job_runs
from references.<database>__region_costs import region_costs

# month and days_since (MONTH, DATEDIFF) and day (SUBSTR, CONCAT) use names files 03 to 05
# don't give, so project.convert writes them from the Hive
s_runs = statement(
    SELECT(job_runs.run_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),
)
s_costs = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region, region_costs.dt),
    FROM(region_costs, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X06

Map:
- Sources: job_runs (run_id, job_id, duration_mins); jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job).

Typed over a formula: none.
Marks: none.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  COUNT(*) OVER (PARTITION BY r.job_id) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, count_rows, equals, statement, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

each_job = window(PARTITION_BY=job_runs.job_id)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, jobs.job_name,
           AS(count_rows(over=each_job), "runs_of_job")),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(job_runs.job_id, jobs.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X07

Map:
- Sources: job_runs (run_id, job_id, status); jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, team, region).

Typed over a formula: none.
Marks: none. VLOOKUP(..., FALSE) is exact; the blank status in run 98 is not read by a formula.
Refused: none.
Left alone: none.
Fill in: `<database>`.

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
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(job_runs.job_id, jobs.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X08

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: by_job (job_id, total_mins, avg_retry, longest). by_job's only typed column is job_id, which its SUMIFS and AVERAGEIFS match on, so it is a summary: a GROUP BY of job_runs.
- job_runs is read by by_job, so it is not a final.

Typed over a formula: none.
Marks: the blank avg_retry_secs in run 98 is skipped by AVG, as AVERAGEIFS skips it. No COALESCE, since every group has rows.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
-- final: by_job
SELECT r.job_id,
  SUM(r.duration_mins) AS total_mins,
  AVG(r.avg_retry_secs) AS avg_retry,
  MAX(r.duration_mins) AS longest
FROM <database>.job_runs r
GROUP BY r.job_id
```

```python
# reads_all_partitions=True: the workbook's formulas read every row, so every partition
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, average_of, max_of, statement, sum_of
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id,
           AS(sum_of(job_runs.duration_mins), "total_mins"),
           AS(average_of(job_runs.avg_retry_secs), "avg_retry"),
           AS(max_of(job_runs.duration_mins), "longest")),
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X09

Map:
- Sources: job_runs (run_id, job_id, duration_mins, avg_retry_secs); jobs (job_id, job_name, team, region).
- Parameters: rate is 0.5, so XLOOKUP("rate", ...) becomes 0.5. Parameters is neither a source nor a final.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost).
- Keys: job_runs, run_id.

Typed over a formula: cost in run 97 is typed as 100. Keys has a row for job_runs (run_id), so the match is on run_id: `CASE WHEN run_id = 97 THEN 100 ELSE ... END`.
Marks:
- blank: avg_retry_secs in run 98 is wrapped in COALESCE inside cost.
- team_mins is SUMIFS over its own Table, so it is SUM(duration_mins) OVER (PARTITION BY team).
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs,
  j.team,
  SUM(r.duration_mins) OVER (PARTITION BY j.team) AS team_mins,
  CASE WHEN r.run_id = 97 THEN 100
    ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5 END AS cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, first_match, statement, sum_of, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

each_team = window(PARTITION_BY=jobs.team)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.avg_retry_secs,
           jobs.team,
           AS(sum_of(job_runs.duration_mins, over=each_team), "team_mins"),
           AS(first_match([(equals(job_runs.run_id, 97), 100)],
                          otherwise=(job_runs.duration_mins * 60 + fill_null(job_runs.avg_retry_secs, 0)) * 0.5),
              "cost")),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(job_runs.job_id, jobs.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X10

Map:
- Sources: job_runs (run_id, job_id, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample).
- Keys: none. The Keys Table has no row for job_runs, so the typed hours match on every typed column of the row, and there is no Keys row.

Typed over a formula: hours is 9 in run 103 (job 3, 30 minutes, 2026-09-24). It becomes `CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24' THEN 9 ELSE duration_mins / 60 END`.
Marks: none.
Refused: sample is RAND(), which is refused: `NULL AS sample`.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
  CASE WHEN r.run_id = 103 AND r.job_id = 3 AND r.duration_mins = 30 AND r.dt = '2026-09-24'
    THEN 9 ELSE r.duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs r
```

```python
# reads_all_partitions=True: the workbook's formulas read every row, so every partition
from sqlglot_composer import AS, FROM, SELECT, all_of, equals, first_match, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(first_match([(all_of(equals(job_runs.run_id, 103), equals(job_runs.job_id, 3),
                                   equals(job_runs.duration_mins, 30),
                                   equals(job_runs.dt, "2026-09-24")), 9)],
                          otherwise=job_runs.duration_mins / 60), "hours")),
    FROM(job_runs, reads_all_partitions=True),
)
# sample is RAND(), refused: NULL AS sample in the Hive, so it is left out of this statement
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X11

Map:
- Sources: job_runs (run_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, duration_mins, pick, scaled).

Typed over a formula: none.
Marks: none.
Refused:
- pick: INDIRECT, so `NULL AS pick`.
- scaled: a reference to Summary!C2, a cell outside a Table that isn't a defined name, so `NULL AS scaled`.
Left alone: the bar chart on Summary; Summary!C2 (outside a Table, used only by the refused scaled).
Fill in: `<database>`.

```sql
SELECT r.run_id, r.duration_mins,
  NULL AS pick,
  NULL AS scaled
FROM <database>.job_runs r
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__job_runs import job_runs

# pick (INDIRECT) and scaled (Summary!C2, outside a Table) are refused: NULL in the Hive
s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X12

Map:
- Sources: job_runs (run_id, duration_mins, running, loop, with_tax) becomes job_runs (run_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, duration_mins, running, loop, with_tax).

Typed over a formula: none.
Marks:
- tax_rate is a defined name for Summary!B3. Its value 0.2 is used. Move tax_rate into Parameters.
Refused:
- running: OFFSET, so `NULL AS running`.
- loop: reads its own column (circular), so `NULL AS loop`.
Left alone: Summary!B3 (outside a Table, used through the defined name's value).
Fill in: `<database>`.

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

# running (OFFSET) and loop (circular) are refused: NULL in the Hive
# with_tax uses tax_rate's value, 0.2; move tax_rate into Parameters
s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins * 0.2, "with_tax")),
    FROM(job_runs),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X13

Map:
- Sources: job_runs (run_id, job_id); jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, name, doubled).

Typed over a formula: none.
Marks:
- name is VLOOKUP(job_id, jobs, 2, TRUE), which is approximate. It is converted as an exact match on job_id, column 2 of jobs (job_name). The approximate match was TRUE in the workbook, and the conversion is exact.
Refused:
- doubled: DOUBLE is a defined name holding a LAMBDA, so `NULL AS doubled`.
Left alone: none.
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

# doubled (a LAMBDA defined name) is refused: NULL in the Hive
# name is an exact match, although the workbook's VLOOKUP was approximate (TRUE)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, AS(jobs.job_name, "name")),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(job_runs.job_id, jobs.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X14

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: by_job (job_id, total_hours). by_job's only typed column is job_id, so it is a summary: a GROUP BY of job_runs.
- job_runs is read by by_job, so it is not a final. Its hours column is computed inside by_job's query as duration_mins / 60.

Typed over a formula: none.
Marks: none.
Refused: none.
Left alone: the PivotTable on sheet "Pivot", built from job_runs.
Fill in: `<database>`.

```sql
-- final: by_job
SELECT r.job_id, SUM(r.duration_mins / 60) AS total_hours
FROM <database>.job_runs r
GROUP BY r.job_id
```

```python
# reads_all_partitions=True: the workbook's formulas read every row, so every partition
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, statement, sum_of
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins / 60), "total_hours")),
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X15

Map:
- Sources: tblRuns (Run ID, Job ID, Duration (mins)).
- Steps: none.
- Finals: tblRuns (Run ID, Job ID, Duration (mins), Hours).

Typed over a formula: none.
Marks: headers with spaces or parentheses are snake case in brackets: Run ID is `<run_id>`, Job ID is `<job_id>`, Duration (mins) is `<duration_mins>`. The Table name tblRuns is a plain name and is kept. Hours is a plain name and is kept.
Refused: none.
Left alone: none.
Fill in: `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`.

```sql
SELECT t.<run_id>, t.<job_id>, t.<duration_mins>,
  t.<duration_mins> / 60 AS hours
FROM <database>.tblRuns t
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

Take out of the workbook what you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X16

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none. The Power Query "long_runs" loads the final Table, and nothing else reads it, so the query is the final's query.
- Finals: long_runs (run_id, job_id, minutes, hours).

Typed over a formula: none.
Marks: none.
Refused: none.
Left alone: the Power Query's Table is a query output, so it has no typed columns and is not a source.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins AS minutes,
  r.duration_mins / 60 AS hours
FROM <database>.job_runs r
WHERE r.duration_mins > 15
```

```python
# reads_all_partitions=True: the query reads every row, so every partition
from sqlglot_composer import AS, FROM, SELECT, WHERE, more_than, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id,
           AS(job_runs.duration_mins, "minutes"),
           AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(more_than(job_runs.duration_mins, 15)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X17

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: ok_runs, the connection-only query that filters job_runs to SUCCESS. ok_by_job reads it, so it is a CTE.
- Finals: ok_by_job (job_id, runs, total_mins).

Typed over a formula: none.
Marks: none.
Refused: none.
Left alone: none.
Fill in: `<database>`.

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
# reads_all_partitions=True: the query reads every row, so every partition
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived, equals, statement, sum_of
from references.<database>__job_runs import job_runs

ok_runs = derived("ok_runs", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(equals(job_runs.status, "SUCCESS")),
))
s = statement(
    SELECT(ok_runs.job_id, AS(count_rows(), "runs"), AS(sum_of(ok_runs.duration_mins), "total_mins")),
    FROM(ok_runs),
    GROUP_BY(ok_runs.job_id),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X18

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: top_runs (run_id, job_name, duration_mins).

Typed over a formula: none.
Marks: Table.Sort then Table.FirstN becomes ORDER BY ... LIMIT 3. Two runs tie at 30 minutes (runs 97 and 103), so run_id ascending breaks the tie, as M keeps the earlier row first.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC, r.run_id
LIMIT 3
```

```python
# reads_all_partitions=True: the query reads every row, so every partition
from sqlglot_composer import FROM, LEFT_JOIN, LIMIT, ORDER_BY, SELECT, descending, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, jobs.job_name, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),
    LEFT_JOIN(jobs, ON=equals(job_runs.job_id, jobs.job_id)),
    ORDER_BY(descending(job_runs.duration_mins), job_runs.run_id),
    LIMIT(3),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X19

Map:
- Sources: scheduler_runs (run_id, job_id, dt); job_runs (run_id, job_id, dt), read by Sql.Database("dwh01", "ops") and Item "job_runs".
- Steps: none.
- Finals: all_runs (run_id, job_id, dt). Table.Combine becomes UNION ALL.

Typed over a formula: none.
Marks:
- Sql.Database: the table named is job_runs in the ops schema on dwh01. Check that `<database>` is that ops database and that job_runs is the table in it.
Refused:
- The connection-only query "holidays" reads Web.Contents, an online source, so it is left out.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT s.run_id, s.job_id, s.dt
FROM <database>.scheduler_runs s
UNION ALL
SELECT w.run_id, w.job_id, w.dt
FROM <database>.job_runs w
```

```python
# reads_all_partitions=True: the query reads every row, so every partition
from sqlglot_composer import FROM, SELECT, UNION_ALL, statement
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

s = UNION_ALL(
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
              FROM(scheduler_runs, reads_all_partitions=True)),
    statement(SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
              FROM(job_runs, reads_all_partitions=True)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X20

Map:
- Sources: run_alerts (alert_id, run_id, severity, dt).
- Steps: none.
- Finals: alert_pivot (run_id, high, low).

Typed over a formula: none.
Marks: Table.Pivot becomes one SUM(CASE WHEN severity = '...' THEN 1 END) column per severity value in the sample, high and low, NULL where none. The pivot's columns are now fixed: a new severity in the data needs a new column.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT a.run_id,
  SUM(CASE WHEN a.severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN a.severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts a
WHERE a.run_id = 97 OR a.run_id = 101
GROUP BY a.run_id
```

```python
# reads_all_partitions=True: the query reads every row, so every partition
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, any_of, equals, first_match, statement, sum_of
from references.<database>__run_alerts import run_alerts

s = statement(
    SELECT(run_alerts.run_id,
           AS(sum_of(first_match([(equals(run_alerts.severity, "high"), 1)])), "high"),
           AS(sum_of(first_match([(equals(run_alerts.severity, "low"), 1)])), "low")),
    FROM(run_alerts, reads_all_partitions=True),
    WHERE(any_of(equals(run_alerts.run_id, 97), equals(run_alerts.run_id, 101))),
    GROUP_BY(run_alerts.run_id),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X41

Map:
- Sources: job_runs (run_id, job_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, longest_first, job_shortest, job_total).

Typed over a formula: none.
Marks: none.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  RANK() OVER (ORDER BY r.duration_mins DESC) AS longest_first,
  MIN(r.duration_mins) OVER (PARTITION BY r.job_id) AS job_shortest,
  SUM(r.duration_mins) OVER (PARTITION BY r.job_id) AS job_total
FROM <database>.job_runs r
```

```python
from sqlglot_composer import AS, FROM, SELECT, descending, min_of, rank, statement, sum_of, window
from references.<database>__job_runs import job_runs

each_job = window(PARTITION_BY=job_runs.job_id)
by_length = window(ORDER_BY=descending(job_runs.duration_mins))
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins,
           AS(rank(over=by_length), "longest_first"),
           AS(min_of(job_runs.duration_mins, over=each_job), "job_shortest"),
           AS(sum_of(job_runs.duration_mins, over=each_job), "job_total")),
    FROM(job_runs),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X42

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs is typed, but its formulas also read job_runs.
- Steps: none. The summary-style counts are LEFT JOIN subqueries over job_runs, written inline.
- Finals: jobs (job_id, job_name, runs, avg_mins, id_order).
- job_runs is read by jobs, so it is not a final.

Typed over a formula: none.
Marks:
- IFERROR(AVERAGEIF(...), 0) becomes COALESCE(avg, 0), since AVG of no rows is NULL.
- COUNTIF over another Table: LEFT JOIN a COUNT(*) subquery, with COALESCE(total, 0), as Excel gives 0 where nothing matches.
- id_order is RANK.EQ with 1 as a third argument, so ASC.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(c.total, 0) AS runs,
  COALESCE(a.avg_total, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id) AS id_order
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, COUNT(*) AS total FROM <database>.job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_total FROM <database>.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

```python
# reads_all_partitions=True: the derived tables read every row, so every partition
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, count_rows, derived, equals, fill_null, rank, statement, window
from references.<database>__jobs import jobs
from references.<database>__job_runs import job_runs

runs_per_job = derived("runs_per_job", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "total")),
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
))
avg_per_job = derived("avg_per_job", statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_total")),
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(fill_null(runs_per_job.total, 0), "runs"),
           AS(fill_null(avg_per_job.avg_total, 0), "avg_mins"),
           AS(rank(over=window(ORDER_BY=jobs.job_id)), "id_order")),
    FROM(jobs),
    LEFT_JOIN(runs_per_job, ON=equals(jobs.job_id, runs_per_job.job_id)),
    LEFT_JOIN(avg_per_job, ON=equals(jobs.job_id, avg_per_job.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X43

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: busy_teams (team, runs, shortest, avg_mins); statuses (job_id, status).

Typed over a formula: none.
Marks:
- Table.Group becomes GROUP BY team, with COUNT(*), MIN and AVG.
- Table.SelectRows on the grouped Table becomes HAVING COUNT(*) > 4.
- Table.Distinct alone becomes SELECT DISTINCT. The blank status for job 2 is kept as a NULL value, as M keeps it.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
-- final: busy_teams
SELECT j.team, COUNT(*) AS runs, MIN(r.duration_mins) AS shortest,
  AVG(r.duration_mins) AS avg_mins
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.team
HAVING COUNT(*) > 4

-- final: statuses
SELECT DISTINCT r.job_id, r.status
FROM <database>.job_runs r
```

```python
# reads_all_partitions=True: the queries read every row, so every partition
from sqlglot_composer import AS, FROM, GROUP_BY, HAVING, JOIN, SELECT, SELECT_DISTINCT, average_of, count_rows, equals, min_of, more_than, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

busy_teams = statement(
    SELECT(jobs.team, AS(count_rows(), "runs"), AS(min_of(job_runs.duration_mins), "shortest"),
           AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),
    JOIN(jobs, ON=equals(job_runs.job_id, jobs.job_id)),
    GROUP_BY(jobs.team),
    HAVING(more_than(count_rows(), 4)),
)
statuses = statement(
    SELECT_DISTINCT(job_runs.job_id, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X44

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region); scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: jobs_with_runs (run_id, job_name); never_scheduled (job_id, job_name, team).

Typed over a formula: none.
Marks:
- RightOuter becomes RIGHT JOIN, so a job with no run keeps a NULL run_id (cache_warm).
- LeftAnti becomes LEFT JOIN scheduler_runs ... WHERE the scheduler's job_id IS NULL, keeping jobs' columns.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
-- final: jobs_with_runs
SELECT r.run_id, j.job_name
FROM <database>.job_runs r
RIGHT JOIN <database>.jobs j ON r.job_id = j.job_id

-- final: never_scheduled
SELECT j.job_id, j.job_name, j.team
FROM <database>.jobs j
LEFT JOIN <database>.scheduler_runs s ON j.job_id = s.job_id
WHERE s.job_id IS NULL
```

```python
# reads_all_partitions=True: the queries read every row, so every partition
from sqlglot_composer import ANTI_JOIN, AS, FROM, LEFT_JOIN, SELECT, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs
from references.<database>__scheduler_runs import scheduler_runs

# there is no RIGHT_JOIN: the tables are swapped and LEFT_JOIN is used
jobs_with_runs = statement(
    SELECT(job_runs.run_id, jobs.job_name),
    FROM(jobs),
    LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id), reads_all_partitions=True),
)
never_scheduled = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team),
    FROM(jobs),
    ANTI_JOIN(scheduler_runs, ON=equals(scheduler_runs.job_id, jobs.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.

## X45

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: run_days (run_id, dt); matched (run_id, job_id, dt, status).

Typed over a formula: none.
Marks:
- run_days: Table.Combine then Table.Distinct becomes UNION.
- matched: FullOuter becomes FULL OUTER JOIN. A run that only job_runs has (run 99) gets NULL run_id, job_id and dt from scheduler_runs, as M leaves them.
Refused: none.
Left alone: none.
Fill in: `<database>`.

```sql
-- final: run_days
SELECT r.run_id, r.dt
FROM <database>.job_runs r
UNION
SELECT s.run_id, s.dt
FROM <database>.scheduler_runs s

-- final: matched
SELECT s.run_id, s.job_id, s.dt, r.status
FROM <database>.scheduler_runs s
FULL OUTER JOIN <database>.job_runs r ON s.run_id = r.run_id
```

```python
# reads_all_partitions=True: the queries read every row, so every partition
from sqlglot_composer import AS, FROM, FULL_JOIN, SELECT, UNION, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

run_days = UNION(
    statement(SELECT(job_runs.run_id, job_runs.dt), FROM(job_runs, reads_all_partitions=True)),
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt),
              FROM(scheduler_runs, reads_all_partitions=True)),
)
matched = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt, job_runs.status),
    FROM(scheduler_runs, reads_all_partitions=True),
    FULL_JOIN(job_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, then run `project.convert` on the Hive; its checked code wins where the two differ.
