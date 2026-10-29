date: 2026-10-29
arm: C
model: haiku
files: 44f6c5d

## X01

**Map**
- Sources: job_runs (run_id, job_id, duration_mins, dt)
- Steps: none
- Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours)
- Typed over a formula: none
- Marks: none
- Refused: none
- Left alone: none (Parameters and Keys are empty and are neither a source, a step nor a final)
- To fill in: `<database>`

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
    FROM(job_runs, reads_all_partitions=True),  # no filter: the final reads every row
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X02

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins)
- Steps: none
- Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag)
- Typed over a formula: none
- Marks: AND and OR become the operators; IF stays IF. No formula reads a blank (the blank status in row 98 is not read by a formula).
- Refused: none
- Left alone: none (Parameters and Keys are empty)
- To fill in: `<database>`

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
    FROM(job_runs, reads_all_partitions=True),  # no filter: the final reads every row
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X03

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt)
- Steps: none
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs)
- Typed over a formula: none
- Marks:
  - blank: row 98's blank status, read by score, is wrapped as COALESCE(status, '').
  - blank: row 98's blank avg_retry_secs, read by mins_per_retry and total_secs, is wrapped as COALESCE(avg_retry_secs, 0).
  - SWITCH becomes a CASE; IFERROR becomes COALESCE, as Hive gives NULL for a divide by 0.
- Refused: none
- Left alone: none
- To fill in: `<database>`

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

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt,
           AS(if_else(equals(fill_null(job_runs.status, ""), "SUCCESS"), 1,
                      if_else(equals(fill_null(job_runs.status, ""), "FAILED"), -1, 0)), "score"),
           AS(fill_null(job_runs.duration_mins / fill_null(job_runs.avg_retry_secs, 0), 0),
              "mins_per_retry"),
           AS(job_runs.duration_mins * 60 + fill_null(job_runs.avg_retry_secs, 0), "total_secs")),
    FROM(job_runs, reads_all_partitions=True),  # no filter: the final reads every row
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X04

**Map**
- Sources: jobs (job_id, job_name, team, region)
- Steps: none
- Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd)
- Typed over a formula: none
- Marks: none. The formulas become UPPER and SUBSTR inside CONCAT (for `&`), LENGTH for LEN, ROUND as it is, and PMOD for MOD.
- Refused: none
- Left alone: none
- To fill in: `<database>`

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
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region,
           # code, name_length, third and odd use UPPER, SUBSTR, LENGTH, ROUND and PMOD, which
           # files 03 to 05 and 11 don't name, so project.convert takes them from the Hive
    ),
    FROM(jobs, reads_all_partitions=True),  # no filter: the final reads every row
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X05

**Map**
- Sources: job_runs (run_id, dt), region_costs (job_id, cost_cents, region, dt)
- Steps: none
- Finals: job_runs (run_id, dt, month, days_since); region_costs (job_id, cost_cents, region, dt, day)
- Typed over a formula: none
- Marks:
  - region_costs dt is held as text, such as 20260911; day is converted with CONCAT(SUBSTR(...)) as a date held as text.
  - DATE(2026,9,1) becomes '2026-09-01'; DATEDIF(a, b, "d") becomes DATEDIFF(b, a).
  - blank: row 29's cost_cents is blank; no formula reads it, so it stays NULL.
- Refused: none
- Left alone: none
- To fill in: `<database>` (both tables)

```sql
-- final job_runs
SELECT run_id, dt,
       MONTH(dt) AS month,
       DATEDIFF(dt, '2026-09-01') AS days_since
FROM <database>.job_runs
```

```sql
-- final region_costs
SELECT job_id, cost_cents, region, dt,
       CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS day
FROM <database>.region_costs
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__job_runs import job_runs
from references.<database>__region_costs import region_costs

job_runs_out = statement(
    SELECT(job_runs.run_id, job_runs.dt,
           # month (MONTH) and days_since (DATEDIFF from '2026-09-01') are not named in these files
    ),
    FROM(job_runs, reads_all_partitions=True),  # no filter: the final reads every row
)
region_costs_out = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region, region_costs.dt,
           # day (SUBSTR on a date held as text) is not named in these files
    ),
    FROM(region_costs, reads_all_partitions=True),  # no filter: the final reads every row
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X06

**Map**
- Sources: job_runs (run_id, job_id, duration_mins), jobs (job_id, job_name)
- Steps: none
- Finals: job_runs (run_id, job_id, duration_mins, job_name, runs_of_job)
- Typed over a formula: none
- Marks: XLOOKUP becomes a LEFT JOIN on jobs; COUNTIFS over its own Table becomes COUNT(*) OVER (PARTITION BY job_id). No blanks.
- Refused: none
- Left alone: none
- To fill in: `<database>`

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

r, j = AS(job_runs, "r"), AS(jobs, "j")
s = statement(
    SELECT(r.run_id, r.job_id, r.duration_mins, j.job_name,
           AS(count_rows(over=window(PARTITION_BY=r.job_id)), "runs_of_job")),
    FROM(r, reads_all_partitions=True),  # no filter: the final reads every row
    LEFT_JOIN(j, ON=equals(r.job_id, j.job_id)),
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X07

**Map**
- Sources: job_runs (run_id, job_id, status), jobs (job_id, team, region)
- Steps: none
- Finals: job_runs (run_id, job_id, status, team, region)
- Typed over a formula: none
- Marks: VLOOKUP exact (FALSE) and INDEX with MATCH exact (0) both become one LEFT JOIN on jobs. No blanks in a column a formula reads.
- Refused: none
- Left alone: none
- To fill in: `<database>`

```sql
SELECT r.run_id, r.job_id, r.status, j.team, j.region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

r, j = AS(job_runs, "r"), AS(jobs, "j")
s = statement(
    SELECT(r.run_id, r.job_id, r.status, j.team, j.region),
    FROM(r, reads_all_partitions=True),  # no filter: the final reads every row
    LEFT_JOIN(j, ON=equals(r.job_id, j.job_id)),
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X08

**Map**
- Sources: job_runs (job_id, duration_mins, avg_retry_secs)
- Steps: none
- Finals: by_job (job_id, total_mins, avg_retry, longest). by_job is a summary: its only typed column is job_id, which SUMIFS matches on, so it is a GROUP BY of job_runs.
- Typed over a formula: none
- Marks: blank: row 98's blank avg_retry_secs (job 2) is not wrapped, because AVERAGEIFS skips a blank and AVG skips NULL.
- Refused: none
- Left alone: none
- To fill in: `<database>`

```sql
SELECT job_id,
       SUM(duration_mins) AS total_mins,
       AVG(avg_retry_secs) AS avg_retry,
       MAX(duration_mins) AS longest
FROM <database>.job_runs
GROUP BY job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, average_of, max_of, statement, sum_of
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id,
           AS(sum_of(job_runs.duration_mins), "total_mins"),
           AS(average_of(job_runs.avg_retry_secs), "avg_retry"),
           AS(max_of(job_runs.duration_mins), "longest")),
    FROM(job_runs, reads_all_partitions=True),  # the summary reads every row
    GROUP_BY(job_runs.job_id),
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X09

**Map**
- Sources: job_runs (run_id, job_id, duration_mins, avg_retry_secs), jobs (job_id, team)
- Steps: none
- Finals: job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost)
- Keys: job_runs, run_id
- Typed over a formula: cost in row 97 (run_id 97) is typed as 100. It converts as CASE WHEN run_id = 97 THEN 100 ELSE ... END, matched on run_id from the Keys row.
- Marks:
  - blank: row 98's blank avg_retry_secs is wrapped as COALESCE(avg_retry_secs, 0) in cost.
  - rate is read from Parameters as its value, 0.5.
  - team_mins is SUMIFS over its own Table on team, so it is SUM(duration_mins) OVER (PARTITION BY team).
- Refused: none
- Left alone: none
- To fill in: `<database>`

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
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, if_else, statement, sum_of, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

r, j = AS(job_runs, "r"), AS(jobs, "j")
s = statement(
    SELECT(r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs, j.team,
           AS(sum_of(r.duration_mins, over=window(PARTITION_BY=j.team)), "team_mins"),
           # row 97's cost is typed over as 100, matched on run_id from Keys
           AS(if_else(equals(r.run_id, 97), 100,
                      (r.duration_mins * 60 + fill_null(r.avg_retry_secs, 0)) * 0.5), "cost")),
    FROM(r, reads_all_partitions=True),  # no filter: the final reads every row
    LEFT_JOIN(j, ON=equals(r.job_id, j.job_id)),
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X10

**Map**
- Sources: job_runs (run_id, job_id, duration_mins, dt)
- Steps: none
- Finals: job_runs (run_id, job_id, duration_mins, dt, hours, sample)
- Keys: none. The job_runs Table has no Keys row, so row 103 is matched on every typed column of the row: run_id, job_id, duration_mins and dt. Say so before you rely on it.
- Typed over a formula: hours in row 103 (run_id 103) is typed as 9. It converts as CASE WHEN ... THEN 9 ELSE duration_mins / 60 END.
- Marks: none (no blanks in a column a formula reads)
- Refused: sample is RAND(), so it is NULL AS sample.
- Left alone: none
- To fill in: `<database>`

```sql
SELECT run_id, job_id, duration_mins, dt,
       CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24'
            THEN 9 ELSE duration_mins / 60 END AS hours,
       NULL AS sample
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, equals, if_else, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           # no Keys row: row 103 is matched on every typed column, and typed over as 9
           AS(if_else(all_of(equals(job_runs.run_id, 103), equals(job_runs.job_id, 3),
                             equals(job_runs.duration_mins, 30), equals(job_runs.dt, "2026-09-24")),
                      9, job_runs.duration_mins / 60), "hours"),
           # sample is RAND(), refused: NULL in the Hive
    ),
    FROM(job_runs, reads_all_partitions=True),  # no filter: the final reads every row
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X11

**Map**
- Sources: job_runs (run_id, duration_mins)
- Steps: none
- Finals: job_runs (run_id, duration_mins, pick, scaled)
- Typed over a formula: none
- Marks: none
- Refused:
  - pick: INDIRECT, so NULL AS pick.
  - scaled: reads Summary!C2, a cell outside a Table that isn't a defined name, so NULL AS scaled.
- Left alone: the bar chart on Summary
- To fill in: `<database>`

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
    SELECT(
        job_runs.run_id,
        job_runs.duration_mins,
        # pick (INDIRECT) and scaled (Summary!C2, outside a Table) are refused: NULL in the Hive
    ),
    FROM(job_runs, reads_all_partitions=True),  # no filter: the final reads every row
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X12

**Map**
- Sources: job_runs (run_id, duration_mins)
- Steps: none
- Finals: job_runs (run_id, duration_mins, running, loop, with_tax)
- Typed over a formula: none
- Marks:
  - defined name tax_rate is Summary!$B$3, a cell outside a Table. Its value, 0.2, is used. Move it into Parameters.
- Refused:
  - running: OFFSET, so NULL AS running.
  - loop: reads its own column (circular), so NULL AS loop.
- Left alone: none
- To fill in: `<database>`

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
           # running (OFFSET) and loop (circular) are refused: NULL in the Hive
           AS(job_runs.duration_mins * 0.2, "with_tax")),  # tax_rate = 0.2; move it into Parameters
    FROM(job_runs, reads_all_partitions=True),  # no filter: the final reads every row
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X13

**Map**
- Sources: job_runs (run_id, job_id), jobs (job_id, job_name)
- Steps: none
- Finals: job_runs (run_id, job_id, name, doubled)
- Typed over a formula: none
- Marks: VLOOKUP with TRUE is approximate. It is converted as an exact LEFT JOIN on job_id, as the file says, and the sample matches exactly because every job_id is in jobs.
- Refused: doubled, because DOUBLE is a defined name holding a LAMBDA, so NULL AS doubled.
- Left alone: none
- To fill in: `<database>`

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

r, j = AS(job_runs, "r"), AS(jobs, "j")
s = statement(
    SELECT(r.run_id, r.job_id, AS(j.job_name, "name"),
           # doubled (DOUBLE, a LAMBDA defined name) is refused: NULL in the Hive
    ),
    FROM(r, reads_all_partitions=True),  # no filter: the final reads every row
    LEFT_JOIN(j, ON=equals(r.job_id, j.job_id)),  # VLOOKUP ... TRUE is approximate; converted as exact
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X14

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt)
- Steps: runs, the job_runs Table with its hours column (a Table with a formula that by_job reads). It is a CTE with job_id and hours.
- Finals: by_job (job_id, total_hours). by_job is a summary: its only typed column is job_id, so it is a GROUP BY of runs.
- Typed over a formula: none
- Marks: none (hours reads duration_mins, which has no blanks)
- Refused: none
- Left alone: the PivotTable on sheet "Pivot", from job_runs
- To fill in: `<database>`

```sql
WITH runs AS (
  SELECT job_id, duration_mins / 60 AS hours
  FROM <database>.job_runs
)
SELECT job_id, SUM(hours) AS total_hours
FROM runs
GROUP BY job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, derived, statement, sum_of
from references.<database>__job_runs import job_runs

runs = derived("runs", statement(
    SELECT(job_runs.job_id, AS(job_runs.duration_mins / 60, "hours")),
    FROM(job_runs, reads_all_partitions=True),  # no filter: the step reads every row
))
s = statement(
    SELECT(runs.job_id, AS(sum_of(runs.hours), "total_hours")),
    FROM(runs),
    GROUP_BY(runs.job_id),
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X15

**Map**
- Sources: tblRuns (`<run_id>`, `<job_id>`, `<duration_mins>`)
- Steps: none
- Finals: tblRuns (`<run_id>`, `<job_id>`, `<duration_mins>`, Hours)
- Typed over a formula: none
- Marks: headers Run ID, Job ID and Duration (mins) are not plain names, so each is in snake case in brackets. The Table name tblRuns and the header Hours are plain and kept.
- Refused: none
- Left alone: none
- To fill in: `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`

```sql
SELECT <run_id>, <job_id>, <duration_mins>,
       <duration_mins> / 60 AS Hours
FROM <database>.tblRuns
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__tblRuns import tblRuns

s = statement(
    SELECT(tblRuns.<run_id>, tblRuns.<job_id>, tblRuns.<duration_mins>,
           AS(tblRuns.<duration_mins> / 60, "Hours")),
    FROM(tblRuns, reads_all_partitions=True),  # no filter: the final reads every row
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X16

**Map**
- Sources: job_runs (run_id, job_id, duration_mins)
- Steps: none
- Finals: long_runs (run_id, job_id, minutes, hours). The Table has no typed columns (a query loads it) and nothing reads it, so the query "long_runs" is the final.
- Typed over a formula: none
- Marks: Table.SelectRows with > becomes WHERE; Table.AddColumn becomes an expression AS hours; Table.RenameColumns becomes AS minutes.
- Refused: none
- Left alone: none
- To fill in: `<database>`

```sql
SELECT run_id, job_id,
       duration_mins AS minutes,
       duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

```python
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

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X17

**Map**
- Sources: job_runs (job_id, status, duration_mins)
- Steps: ok_runs (the connection-only query, which ok_by_job reads). It is a CTE with WHERE status = 'SUCCESS'.
- Finals: ok_by_job (job_id, runs, total_mins)
- Typed over a formula: none
- Marks: Table.Group becomes GROUP BY job_id, with Table.RowCount as COUNT(*) and List.Sum as SUM. The blank status in row 98 is dropped in both M and Hive, since it isn't equal to "SUCCESS".
- Refused: none
- Left alone: none
- To fill in: `<database>`

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
    FROM(job_runs, reads_all_partitions=True),  # no filter beyond the query's own WHERE
    WHERE(equals(job_runs.status, "SUCCESS")),
))
s = statement(
    SELECT(ok_runs.job_id, AS(count_rows(), "runs"), AS(sum_of(ok_runs.duration_mins), "total_mins")),
    FROM(ok_runs),
    GROUP_BY(ok_runs.job_id),
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X18

**Map**
- Sources: job_runs (run_id, job_id, duration_mins), jobs (job_id, job_name)
- Steps: none
- Finals: top_runs (run_id, job_name, duration_mins)
- Typed over a formula: none
- Marks: NestedJoin with JoinKind.LeftOuter becomes a LEFT JOIN. Table.Sort descending then Table.FirstN 3 become ORDER BY ... DESC LIMIT 3. Runs 97 and 103 tie at 30 but both fall inside the top 3, so the set is fixed; their order in Hive is not.
- Refused: none
- Left alone: none
- To fill in: `<database>`

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC
LIMIT 3
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, LIMIT, ORDER_BY, SELECT, descending, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

r, j = AS(job_runs, "r"), AS(jobs, "j")
s = statement(
    SELECT(r.run_id, j.job_name, r.duration_mins),
    FROM(r, reads_all_partitions=True),  # no filter: the final reads every row
    LEFT_JOIN(j, ON=equals(r.job_id, j.job_id)),
    ORDER_BY(descending(r.duration_mins)),
    LIMIT(3),
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X19

**Map**
- Sources: scheduler_runs (run_id, job_id, dt); job_runs (run_id, job_id, dt), from Sql.Database("dwh01", "ops"), which is outside this workbook
- Steps: none
- Finals: all_runs (run_id, job_id, dt). Table.Combine becomes UNION ALL.
- Typed over a formula: none
- Marks:
  - Sql.Database: the table it names is ops.job_runs on dwh01. Check that `<database>.job_runs` is that table.
- Refused:
  - the connection-only query "holidays" reads Web.Contents, an online source, so it is left out.
- Left alone: none
- To fill in: `<database>`

```sql
SELECT run_id, job_id, dt
FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt
FROM <database>.job_runs
```

```python
from sqlglot_composer import FROM, SELECT, UNION_ALL, statement
from references.<database>__scheduler_runs import scheduler_runs
from references.<database>__job_runs import job_runs  # M's ops.job_runs on dwh01: check it

scheduled = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # no filter: every row
)
runs = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # no filter: every row
)
s = UNION_ALL(scheduled, runs)
# the "holidays" query (Web.Contents) is left out
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.

## X20

**Map**
- Sources: run_alerts (run_id, severity)
- Steps: none
- Finals: alert_pivot (run_id, high, low)
- Typed over a formula: none
- Marks:
  - Table.SelectRows with `or` becomes WHERE run_id = 97 OR run_id = 101.
  - Table.Pivot becomes SUM(CASE WHEN ... END) for each severity value in the sample, high and low, NULL where none, as M leaves it.
  - The pivot's columns are now fixed: high and low. A new severity value gets no column.
- Refused: none
- Left alone: none
- To fill in: `<database>`

```sql
SELECT run_id,
       SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
       SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
WHERE run_id = 97 OR run_id = 101
GROUP BY run_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, any_of, count_rows, equals, statement
from references.<database>__run_alerts import run_alerts

s = statement(
    SELECT(run_alerts.run_id,
           # high and low: the Hive's SUM(CASE ... END) gives NULL where none; count_rows gives 0,
           # so the Hive's code wins where the two differ
           AS(count_rows(where=equals(run_alerts.severity, "high")), "high"),
           AS(count_rows(where=equals(run_alerts.severity, "low")), "low")),
    FROM(run_alerts, reads_all_partitions=True),
    WHERE(any_of(equals(run_alerts.run_id, 97), equals(run_alerts.run_id, 101))),
    GROUP_BY(run_alerts.run_id),
)
```

Next: take out anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its code is checked and wins where the two differ.
