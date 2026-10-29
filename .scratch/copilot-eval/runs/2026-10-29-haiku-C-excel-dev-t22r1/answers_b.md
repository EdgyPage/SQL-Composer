date: 2026-10-29
arm: C
model: haiku
files: fa48987

## X41

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total).
- Parameters and Keys are empty, so there are no Keys rows and none are needed.

**Typed over a formula:** none.

**Marks:** row 98's blank status is skipped by the MINIFS criterion (the -IFS form), so it is not wrapped.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins,
  RANK() OVER (ORDER BY duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN status = 'SUCCESS' THEN duration_mins END) OVER (PARTITION BY job_id), 0) AS shortest_ok,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0) AS job_total
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, descending, equals, fill_null, min_of, rank, statement, sum_of, window
from references.ops__job_runs import job_runs

by_job = window(PARTITION_BY=job_runs.job_id)
by_longest = window(ORDER_BY=descending(job_runs.duration_mins))

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           AS(rank(over=by_longest), "longest_first"),
           AS(fill_null(min_of(job_runs.duration_mins, where=equals(job_runs.status, "SUCCESS"),
                               over=by_job), 0), "shortest_ok"),
           AS(fill_null(sum_of(job_runs.duration_mins, over=by_job), 0), "job_total")),
    FROM(job_runs),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X42

**Map**
- Sources: job_runs (typed; read by jobs' formulas, no formulas of its own), jobs (typed job_id, job_name).
- Steps: none.
- Finals: jobs (job_id, job_name, runs, avg_mins, id_order).
- Parameters and Keys are empty, so there are no Keys rows.

**Typed over a formula:** none.

**Marks:** avg_mins is IFERROR(AVERAGEIF(...), 0), so it is COALESCE(avg, 0), since a job with no runs gives NULL. The blank status and avg_retry_secs cells in job_runs are read by no formula, so they are left as they are.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(rb.runs, 0) AS runs,
  COALESCE(rb.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id) AS id_order
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS runs, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) rb ON j.job_id = rb.job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, count_rows, derived, equals, fill_null, rank, statement, window
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

runs_by_job = derived("runs_by_job", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
by_id = window(ORDER_BY=jobs.job_id)

s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(fill_null(runs_by_job.runs, 0), "runs"),
           AS(fill_null(runs_by_job.avg_mins, 0), "avg_mins"),
           AS(rank(over=by_id), "id_order")),
    FROM(jobs),
    LEFT_JOIN(runs_by_job, ON=equals(runs_by_job.job_id, jobs.job_id)),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X43

**Map**
- Sources: job_runs, jobs (both typed, both read by queries).
- Steps: none.
- Finals: busy_teams (team, runs, shortest, avg_mins), statuses (job_id, status).
- busy_teams is a query loaded into a Table that nothing reads, so it is a final. statuses is the same.
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:** none. The blank status in the sample comes through DISTINCT as NULL, as M keeps it.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

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

```python
from sqlglot_composer import AS, FROM, GROUP_BY, HAVING, JOIN, SELECT, SELECT_DISTINCT, average_of, count_rows, equals, min_of, more_than, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

busy_teams = statement(
    SELECT(jobs.team, AS(count_rows(), "runs"), AS(min_of(job_runs.duration_mins), "shortest"),
           AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    GROUP_BY(jobs.team),
    HAVING(more_than(count_rows(), 4)),
)

statuses = statement(
    SELECT_DISTINCT(job_runs.job_id, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X44

**Map**
- Sources: job_runs, jobs, scheduler_runs (all typed, all read by queries).
- Steps: none.
- Finals: jobs_with_runs (run_id, job_name), never_scheduled (job_id, job_name, team).
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:** jobs_with_runs is a RightOuter join, so it is a LEFT JOIN with the two tables swapped. Job 4 (cache_warm) has no runs, so its run_id is NULL, as in the sample.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

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

```python
from sqlglot_composer import ANTI_JOIN, FROM, LEFT_JOIN, SELECT, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__scheduler_runs import scheduler_runs

jobs_with_runs = statement(
    SELECT(job_runs.run_id, jobs.job_name),
    FROM(jobs),
    LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id), reads_all_partitions=True),  # a workbook's query reads every row
)

never_scheduled = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team),
    FROM(jobs),
    ANTI_JOIN(scheduler_runs, ON=equals(scheduler_runs.job_id, jobs.job_id), reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X45

**Map**
- Sources: job_runs, scheduler_runs (typed, read by queries).
- Steps: none.
- Finals: run_days (run_id, dt), matched (run_id, job_id, dt, status).
- A Table.Distinct over a Table.Combine is a UNION, not UNION ALL.
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:** matched is a FullOuter join. Its scheduler columns are NULL for run 99, which exists only in job_runs, as in the sample. The status comes from job_runs.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

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

```python
from sqlglot_composer import FROM, FULL_JOIN, SELECT, UNION, equals, statement
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

run_days = UNION(
    statement(SELECT(job_runs.run_id, job_runs.dt), FROM(job_runs, reads_all_partitions=True)),  # a workbook's query reads every row
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt), FROM(scheduler_runs, reads_all_partitions=True)),  # a workbook's query reads every row
)

matched = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt, job_runs.status),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
    FULL_JOIN(job_runs, ON=equals(job_runs.run_id, scheduler_runs.run_id), reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X51

**Map**
- Sources and finals: job_runs (typed run_id, job_id, status, duration_mins, dt). Nothing else reads it, so it is a final too.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins).
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:**
- The blank status in row 98 is inside COUNTIFS, which skips it, so it is not wrapped. not_ok counts it, as Excel's "<>SUCCESS" does.
- running_mins is a running total with ties included, as Excel's "<=" gives. The Hive uses RANGE, so tied dates share one total.
- Excel's "*ail*" ignores case, so the Hive uses LOWER(status).

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins, dt,
  COALESCE(COUNT(CASE WHEN duration_mins > 15 THEN 1 END) OVER (PARTITION BY job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (status <> 'SUCCESS' OR status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY job_id), 0) AS failed_in_job,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, any_of, contains, count_rows, fill_null, is_null, more_than, not_equals, statement, sum_of, window
from references.ops__job_runs import job_runs

whole = window()
by_job = window(PARTITION_BY=job_runs.job_id)
running = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt, rows=(None, 0))

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins, job_runs.dt,
           AS(fill_null(count_rows(where=more_than(job_runs.duration_mins, 15), over=by_job), 0), "long_in_job"),
           AS(fill_null(count_rows(where=any_of(not_equals(job_runs.status, "SUCCESS"), is_null(job_runs.status)), over=whole), 0), "not_ok"),
           AS(fill_null(count_rows(where=contains(job_runs.status, "ail"), over=by_job), 0), "failed_in_job"),
           AS(fill_null(sum_of(job_runs.duration_mins, over=running), 0), "running_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. The Python's rows= counts tied dates one row at a time, and its contains keeps case, so for running_mins and failed_in_job the checked code may differ from the Hive.

## X52

**Map**
- Sources: job_runs (typed run_id, job_id, duration_mins).
- Steps: share is read by the Total Row, so the Total Row's query builds share in a CTE.
- Finals: job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job); job_runs (Total Row).
- The Total Row is its own query, because job_runs is not a summary.
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:** share is duration / SUM over the whole column, vs_avg is duration less AVERAGE over the whole column, and rank_in_job is COUNTIFS + 1, which is RANK() descending within job.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
SELECT run_id, job_id, duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

```sql
WITH shares AS (
  SELECT duration_mins, duration_mins / SUM(duration_mins) OVER () AS share
  FROM <database>.job_runs
)
SELECT SUM(duration_mins) AS duration_mins, SUM(share) AS share
FROM shares
```

```python
from sqlglot_composer import AS, FROM, SELECT, average_of, derived, descending, rank, statement, sum_of, window
from references.ops__job_runs import job_runs

whole = window()
by_job = window(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.duration_mins))

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins,
           AS(job_runs.duration_mins / sum_of(job_runs.duration_mins, over=whole), "share"),
           AS(job_runs.duration_mins - average_of(job_runs.duration_mins, over=whole), "vs_avg"),
           AS(rank(over=by_job), "rank_in_job")),
    FROM(job_runs),
)

shares = derived("shares", statement(
    SELECT(job_runs.duration_mins,
           AS(job_runs.duration_mins / sum_of(job_runs.duration_mins, over=whole), "share")),
    FROM(job_runs),
))
total_row = statement(
    SELECT(AS(sum_of(shares.duration_mins), "duration_mins"), AS(sum_of(shares.share), "share")),
    FROM(shares),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X53

**Map**
- Sources: job_runs (typed; read by the summary).
- Steps: none.
- Finals: by_job (job_id, total_mins, runs, longest).
- by_job's only typed column is job_id, which its SUMIFS and COUNTIFS match on, so it is a summary: a GROUP BY of job_runs.
- by_job (Total Row) needs no query of its own. Its totals are SUMs, SUMs and MAX of MAXes, so the summary's query ends GROUP BY job_id WITH ROLLUP, and the NULL job_id row is the Total Row.
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:** the GROUP BY keys are the job_ids that have runs. A job with no runs drops out, rather than showing 0. The sample's three jobs all have runs.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
SELECT job_id, SUM(duration_mins) AS total_mins, COUNT(*) AS runs, MAX(duration_mins) AS longest
FROM <database>.job_runs
GROUP BY job_id WITH ROLLUP
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, count_rows, max_of, rollup, statement, sum_of
from references.ops__job_runs import job_runs

by_job = statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total_mins"),
           AS(count_rows(), "runs"), AS(max_of(job_runs.duration_mins), "longest")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(rollup(job_runs.job_id)),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X54

**Map**
- Sources: job_runs (typed run_id, dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label).
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:**
- a_month_on is EDATE, converted as ADD_MONTHS. As in Excel, a month's end stays a month's end.
- week_of and month_of follow file 11's week and month forms.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

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

```python
from sqlglot_composer import AS, FROM, SELECT, month_start, statement, week_start
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.dt,
           AS(week_start(job_runs.dt), "week_of"),
           AS(month_start(job_runs.dt), "month_of")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

The Python covers only week_of and month_of. month_end, a_month_on, due, weekday and label have no name in files 03, 04, 05 or 11 (LAST_DAY, ADD_MONTHS, DATE_ADD, DAYOFWEEK, DATE_FORMAT). For those, load file 10 (Hive functions) in a new chat.

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X55

**Map**
- Sources and finals: jobs (typed job_id, job_name, team, region). Nothing reads it, so it is a final.
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens).
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:** TEXTJOIN with TRUE becomes CONCAT_WS, which skips NULLs as Excel does. VALUE(job_id & "0") becomes CAST(CONCAT(job_id, '0') AS DOUBLE). ISNUMBER(SEARCH(...)) becomes INSTR(...) > 0.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
SELECT job_id, job_name, team, region,
  INITCAP(REPLACE(job_name, '_', ' ')) AS title,
  CONCAT_WS('/', team, region) AS tag,
  CONCAT(region, '-', job_id) AS code,
  INSTR(LOWER(job_name), LOWER('SYNC')) > 0 AS has_sync,
  CAST(CONCAT(job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
)
```

The Python covers the four typed columns only. title, tag, code, has_sync and tens have no name in files 03, 04, 05 or 11 (PROPER, TEXTJOIN, CONCATENATE, ISNUMBER and VALUE). Load file 10 (Hive functions) in a new chat for them.

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X56

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs); scheduler_runs (typed run_id, job_id, dt, read by XLOOKUP).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on).
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:**
- The blank avg_retry_secs in row 98 is read by SUMPRODUCT, so it is wrapped as COALESCE(avg_retry_secs, 0). The product for that row is 0 either way.
- The blank status in row 98 is read by ISBLANK, which skips it, so it is not wrapped.
- XLOOKUP's fourth argument is COALESCE(dt, 'unscheduled').

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
SELECT j.run_id, j.job_id, j.status, j.duration_mins, j.avg_retry_secs,
  j.status IS NULL AS no_status,
  FLOOR(j.duration_mins / 7) AS weeks,
  GREATEST(j.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(j.duration_mins) OVER () AS spread,
  SUM(j.duration_mins * COALESCE(j.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(s.dt, 'unscheduled') AS scheduled_on
FROM <database>.job_runs j
LEFT JOIN <database>.scheduler_runs s ON j.run_id = s.run_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, statement, sum_of, window
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

whole = window()

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins, job_runs.avg_retry_secs,
           AS(sum_of(job_runs.duration_mins * fill_null(job_runs.avg_retry_secs, 0), over=whole), "weighted"),
           AS(fill_null(scheduler_runs.dt, "unscheduled"), "scheduled_on")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id), reads_all_partitions=True),  # a workbook's query reads every row
)
```

The Python covers weighted and scheduled_on, with the other columns left out. no_status (ISBLANK), weeks (INT), at_least_20 (MAX of two cells) and spread (STDEV.S) have no name in files 03, 04, 05 or 11. Load file 10 (Hive functions) in a new chat for them.

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X57

**Map**
- Sources: job_runs, jobs (typed; read by queries).
- Steps: none.
- Finals: picked (run_id, job_id, status, avg_retry_secs, status_lc); ran_jobs (job_id, job_name, team, region).
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:**
- picked's Power Query replaces the blank avg_retry_secs with 0, so it is COALESCE(avg_retry_secs, 0). Row 98 gives 0.
- The blank status in row 98 is kept, as `status IS NULL` in the filter. status_lc is LOWER of it, so it stays NULL, as in the sample.
- ran_jobs: List.Contains(job_runs[job_id], [job_id]) is a LEFT SEMI JOIN, and Text.Contains is case-kept LIKE '%a%'.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

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

```python
from sqlglot_composer import AS, FROM, SELECT, SEMI_JOIN, WHERE, any_of, contains, equals, fill_null, is_in, is_null, starts_with, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

picked = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status,
           AS(fill_null(job_runs.avg_retry_secs, 0), "avg_retry_secs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_in(job_runs.job_id, [1, 2]),
          any_of(is_null(job_runs.status), starts_with(job_runs.status, "S"))),
)

ran_jobs = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
    SEMI_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id), reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(contains(jobs.job_name, "a")),
)
```

The Python leaves out status_lc, which is LOWER(status) and has no name in files 03, 04, 05 or 11. Load file 10 (labels and Hive functions) in a new chat for it.

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X58

**Map**
- Sources: job_runs, scheduler_runs, jobs, region_budgets (typed; read by queries).
- Steps: none.
- Finals: job_regions (job_id, region), numbered (run_id, dt, duration_mins, n), days_per_job (job_id, days), unrun (run_id, job_id), measures (run_id, measure, amount).
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:**
- job_regions: AddColumn of the distinct regions, then expanded, is a CROSS JOIN.
- numbered: the Table.Sort then AddIndexColumn is ROW_NUMBER over duration_mins DESC, run_id ASC. The rows come out in no order; only n carries it.
- days_per_job: the Table.Sort by days is dropped, since a Hive table holds no order. COUNT(DISTINCT dt) leaves out NULL, and dt has no blank in the sample.
- unrun: the NestedJoin on both columns of scheduler_runs, with its new column removed inside Table.Distinct, is EXCEPT.
- measures: UnpivotOtherColumns is one SELECT per column, stacked with UNION ALL, each with WHERE ... IS NOT NULL, so the blank avg_retry_secs in row 98 is dropped.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
SELECT j.job_id, r.region
FROM (SELECT job_id FROM <database>.jobs) j
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

```python
from sqlglot_composer import AS, CROSS_JOIN, EXCEPT, FROM, GROUP_BY, SELECT, SELECT_DISTINCT, UNION_ALL, WHERE, count_distinct, derived, descending, is_not_null, row_number, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets
from references.ops__scheduler_runs import scheduler_runs

regions = derived("regions", statement(
    SELECT_DISTINCT(region_budgets.region),
    FROM(region_budgets),
))
job_regions = statement(
    SELECT(jobs.job_id, regions.region),
    FROM(jobs),
    CROSS_JOIN(regions),
)

numbered = statement(
    SELECT(job_runs.run_id, job_runs.dt, job_runs.duration_mins,
           AS(row_number(ORDER_BY=[descending(job_runs.duration_mins), job_runs.run_id]), "n")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)

days_per_job = statement(
    SELECT(job_runs.job_id, AS(count_distinct(job_runs.dt), "days")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
)

unrun = EXCEPT(
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.job_id),
              FROM(scheduler_runs, reads_all_partitions=True)),  # a workbook's query reads every row
    statement(SELECT(job_runs.run_id, job_runs.job_id),
              FROM(job_runs, reads_all_partitions=True)),  # a workbook's query reads every row
)

measures = UNION_ALL(
    statement(SELECT(job_runs.run_id, AS(job_runs.duration_mins, "amount")),
              FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
              WHERE(is_not_null(job_runs.duration_mins))),
    statement(SELECT(job_runs.run_id, AS(job_runs.avg_retry_secs, "amount")),
              FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
              WHERE(is_not_null(job_runs.avg_retry_secs))),
)
```

The Python leaves out the measure label column, which is a label and needs file 10 (labels) in a new chat. It also omits the sorted order of days_per_job, which Hive does not keep.

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X67

**Map**
- Sources: jobs, run_alerts (typed; read by queries and formulas). job_runs is typed too, and its formulas are read by two Tables and a query, so it is a step.
- Steps: job_runs (team, alerts and running_mins are read by by_team and noisy_runs). Its CTE is named runs.
- Finals: by_team (team, total_mins, alerted_runs), noisy_runs (run_id, team, alerts, running_mins).
- by_team is a summary (its only typed column is team, which its SUMIFS and COUNTIFS match on): a GROUP BY of the runs step.
- by_team (Total Row) needs no query of its own: its totals are SUMs, so the summary's query ends GROUP BY team WITH ROLLUP.
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:**
- team: XLOOKUP is a LEFT JOIN on jobs; no fourth argument, so no COALESCE.
- alerts: COUNTIF over run_alerts is a LEFT JOIN on a grouped count, wrapped in COALESCE(.., 0).
- running_mins: SUMIFS with "<=" over its own rows, ties included, so tied dates (95 and 99 on 2026-09-23) share one total.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
WITH runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a ON r.run_id = a.run_id
)
SELECT team, SUM(duration_mins) AS total_mins, COUNT(CASE WHEN alerts > 0 THEN 1 END) AS alerted_runs
FROM runs
GROUP BY team WITH ROLLUP
```

```sql
WITH runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a ON r.run_id = a.run_id
)
SELECT run_id, team, alerts, running_mins
FROM runs
WHERE alerts >= 2
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, at_least, count_rows, derived, equals, fill_null, more_than, rollup, statement, sum_of, window
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

alerts_per_run = derived("alerts_per_run", statement(
    SELECT(run_alerts.run_id, AS(count_rows(), "alerts")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(run_alerts.run_id),
))

running = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt, rows=(None, 0))

runs = derived("runs", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           jobs.team,
           AS(fill_null(alerts_per_run.alerts, 0), "alerts"),
           AS(fill_null(sum_of(job_runs.duration_mins, over=running), 0), "running_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    LEFT_JOIN(alerts_per_run, ON=equals(alerts_per_run.run_id, job_runs.run_id)),
))

by_team = statement(
    SELECT(runs.team, AS(sum_of(runs.duration_mins), "total_mins"),
           AS(count_rows(where=more_than(runs.alerts, 0)), "alerted_runs")),
    FROM(runs),
    GROUP_BY(rollup(runs.team)),
)

noisy_runs = statement(
    SELECT(runs.run_id, runs.team, runs.alerts, runs.running_mins),
    FROM(runs),
    WHERE(at_least(runs.alerts, 2)),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. The Python's rows= counts tied dates one row at a time, so running_mins may differ from Excel on tied dates; the checked code wins.

## X68

**Map**
- Sources: job_runs, jobs, region_budgets (typed; read by queries).
- Steps: base (a connection-only query, read by by_region and top_runs, so it is a CTE in each).
- Finals: by_region (region, total_mins, runs, share); by_region (Total Row) (total_mins); top_runs (run_id, job_name, region).
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:**
- share divides by the sum over by_region's own rows, after its HAVING, so the window runs over the grouped rows.
- The Total Row has no SUBTOTAL other than the SUM of total_mins, but by_region is loaded by a query, not a summary, so it needs its own one-row query.
- top_runs: the sort is run_id ascending within equal durations. The two 30-minute runs (97 and 103) straddle the cut, so 97 is kept.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.job_name, b.region
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

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.job_name, b.region
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

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT run_id, job_name, region
FROM base
ORDER BY duration_mins DESC, run_id ASC
LIMIT 2
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, HAVING, JOIN, LEFT_JOIN, LIMIT, ORDER_BY, SELECT, at_least, count_rows, derived, descending, equals, statement, sum_of, window
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets

base = derived("base", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt, jobs.job_name, region_budgets.region),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    LEFT_JOIN(region_budgets, ON=equals(region_budgets.job_id, job_runs.job_id)),
))

grouped = derived("grouped", statement(
    SELECT(base.region, AS(sum_of(base.duration_mins), "total_mins"), AS(count_rows(), "runs")),
    FROM(base),
    GROUP_BY(base.region),
    HAVING(at_least(count_rows(), 2)),
))

by_region = statement(
    SELECT(grouped.region, grouped.total_mins, grouped.runs,
           AS(grouped.total_mins / sum_of(grouped.total_mins, over=window()), "share")),
    FROM(grouped),
)

by_region_total = statement(
    SELECT(AS(sum_of(grouped.total_mins), "total_mins")),
    FROM(grouped),
)

top_runs = statement(
    SELECT(base.run_id, base.job_name, base.region),
    FROM(base),
    ORDER_BY(descending(base.duration_mins), base.run_id),
    LIMIT(2),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X71

**Map**
- Sources: job_runs (typed; read by the queries).
- Steps: ok (the ok_runs query, read by the ok_by_job query, so it is a CTE in each final that reads it).
- Finals: ok_runs (run_id, job_id, duration_mins, hours); ok_by_job (job_id, total_mins).
- ok_runs's hours formula is read by no formula, so the ok_runs Table is a final. Its query is the step.
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:** status = "SUCCESS" drops the blank status in row 98, as M does.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
WITH ok AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT run_id, job_id, duration_mins, duration_mins / 60 AS hours
FROM ok
```

```sql
WITH ok AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT job_id, SUM(duration_mins) AS total_mins
FROM ok
GROUP BY job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, derived, equals, statement, sum_of
from references.ops__job_runs import job_runs

ok = derived("ok", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
))

ok_runs = statement(
    SELECT(ok.run_id, ok.job_id, ok.duration_mins, AS(ok.duration_mins / 60, "hours")),
    FROM(ok),
)

ok_by_job = statement(
    SELECT(ok.job_id, AS(sum_of(ok.duration_mins), "total_mins")),
    FROM(ok),
    GROUP_BY(ok.job_id),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X72

**Map**
- Sources: job_runs (typed; read by jobs' formulas); jobs (typed job_id, job_name, team).
- Steps: jobs. Its formulas runs and total are read by by_team and busy_jobs, so the Table is a step. Its CTE is jobs_calc.
- Finals: by_team (team, team_total); busy_jobs (job_id, job_name, runs).
- by_team is a summary: its only typed column, team, is what its SUMIFS matches on. It is a GROUP BY of jobs_calc.
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:** COUNTIF and SUMIF over job_runs are LEFT JOINs on a grouped subquery, each wrapped in COALESCE(.., 0). Job 4 (web) has no runs, so its team_total is 0.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
WITH jobs_calc AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(r.runs, 0) AS runs,
    COALESCE(r.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total
    FROM <database>.job_runs
    GROUP BY job_id
  ) r ON j.job_id = r.job_id
)
SELECT team, SUM(total) AS team_total
FROM jobs_calc
GROUP BY team
```

```sql
WITH jobs_calc AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(r.runs, 0) AS runs,
    COALESCE(r.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total
    FROM <database>.job_runs
    GROUP BY job_id
  ) r ON j.job_id = r.job_id
)
SELECT job_id, job_name, runs
FROM jobs_calc
WHERE runs >= 3
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, at_least, count_rows, derived, equals, fill_null, statement, sum_of
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

per_job = derived("per_job", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))

jobs_calc = derived("jobs_calc", statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(fill_null(per_job.runs, 0), "runs"),
           AS(fill_null(per_job.total, 0), "total")),
    FROM(jobs),
    LEFT_JOIN(per_job, ON=equals(per_job.job_id, jobs.job_id)),
))

by_team = statement(
    SELECT(jobs_calc.team, AS(sum_of(jobs_calc.total), "team_total")),
    FROM(jobs_calc),
    GROUP_BY(jobs_calc.team),
)

busy_jobs = statement(
    SELECT(jobs_calc.job_id, jobs_calc.job_name, jobs_calc.runs),
    FROM(jobs_calc),
    WHERE(at_least(jobs_calc.runs, 3)),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X75

**Map**
- Sources: job_runs (typed; read by queries).
- Steps: long_runs (the long_runs query, read by the long_per_day query, so it is a CTE in each final that reads it).
- Finals: long_runs (run_id, dt, duration_mins, over); long_per_day (dt, runs).
- The long_runs Table's over formula is read by nothing, so the Table is a final.
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:** `over` is a Hive keyword, so it is quoted with backticks in the SQL. The Table's header stays over.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
WITH long_runs AS (
  SELECT run_id, dt, duration_mins
  FROM <database>.job_runs
  WHERE duration_mins >= 15
)
SELECT run_id, dt, duration_mins, duration_mins - 15 AS `over`
FROM long_runs
```

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

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, at_least, count_rows, derived, statement
from references.ops__job_runs import job_runs

long_runs = derived("long_runs", statement(
    SELECT(job_runs.run_id, job_runs.dt, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(at_least(job_runs.duration_mins, 15)),
))

long_runs_table = statement(
    SELECT(long_runs.run_id, long_runs.dt, long_runs.duration_mins,
           AS(long_runs.duration_mins - 15, "over")),
    FROM(long_runs),
)

long_per_day = statement(
    SELECT(long_runs.dt, AS(count_rows(), "runs")),
    FROM(long_runs),
    GROUP_BY(long_runs.dt),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X76

**Map**
- Sources: job_runs (typed; read by a query), jobs (typed; read by a query).
- Steps: finance_jobs (the finance_jobs query, read by the finance_runs query, so it is a CTE in each final that reads it).
- Finals: finance_jobs (job_id, job_name, label); finance_runs (run_id, job_name, duration_mins).
- The finance_jobs Table's label formula is read by nothing, so the Table is a final.
- Parameters and Keys are empty.

**Typed over a formula:** none.

**Marks:** the Inner NestedJoin is a JOIN. team = 'finance' keeps jobs 2 and 3.

**Refusals:** none.

**Left alone:** the Steps sheet.

**Fill in:** `<database>`.

```sql
WITH finance_jobs AS (
  SELECT job_id, job_name
  FROM <database>.jobs
  WHERE team = 'finance'
)
SELECT job_id, job_name, UPPER(job_name) AS label
FROM finance_jobs
```

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

```python
from sqlglot_composer import FROM, JOIN, SELECT, WHERE, derived, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

finance_jobs = derived("finance_jobs", statement(
    SELECT(jobs.job_id, jobs.job_name),
    FROM(jobs),
    WHERE(equals(jobs.team, "finance")),
))

finance_jobs_table = statement(
    SELECT(finance_jobs.job_id, finance_jobs.job_name),
    FROM(finance_jobs),
)

finance_runs = statement(
    SELECT(job_runs.run_id, finance_jobs.job_name, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    JOIN(finance_jobs, ON=equals(finance_jobs.job_id, job_runs.job_id)),
)
```

The Python leaves out the label column, which is UPPER(job_name) and has no name in files 03, 04, 05 or 11. Load file 10 (Hive functions) in a new chat for it.

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.
