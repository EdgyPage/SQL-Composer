date: 2026-10-29
arm: C
model: haiku
files: 6fc91ff

## X20

Map
- Sources: run_alerts (alert_id, run_id, severity, dt).
- Steps: none. The query's own steps (filter, keep, add n, pivot) are read in order inside alert_pivot's query.
- Finals: alert_pivot (run_id, high, low).
- Parameters and Keys: none.

Marks
- Pivot: a column per severity in the sample, high and low, with SUM(CASE ... THEN 1 END) as M's List.Sum of n = 1. A severity that is not in the sample gets no column. The pivot's columns are now fixed.
- The Toolbox count gives 0 where a run has no high or low row; the Hive gives NULL there, as M does. The checked code wins where they differ.

Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT run_id,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
WHERE run_id = 97 OR run_id = 101
GROUP BY run_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, equals, is_in, statement
from references.ops__run_alerts import run_alerts

s = statement(
    SELECT(run_alerts.run_id,
           AS(count_rows(where=equals(run_alerts.severity, "high")), "high"),
           AS(count_rows(where=equals(run_alerts.severity, "low")), "low")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_in(run_alerts.run_id, [97, 101])),
    GROUP_BY(run_alerts.run_id),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.

## X41

Map
- Sources: job_runs (run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total).
- Parameters and Keys: none.

Marks
- shortest_ok: MINIFS over the rows where status is 'SUCCESS', over the row's own job_id, with COALESCE(.., 0) since Excel gives 0 where nothing matches. The blank status on run 98 is inside an -IFS form, so it is skipped and not wrapped.
- longest_first: RANK.EQ descending, as RANK() OVER (ORDER BY duration_mins DESC).

Refusals: none.
Left alone: none.
Fill in: `<database>`.

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
by_duration = window(ORDER_BY=descending(job_runs.duration_mins))

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           AS(rank(over=by_duration), "longest_first"),
           AS(fill_null(min_of(job_runs.duration_mins, where=equals(job_runs.status, "SUCCESS"), over=by_job), 0), "shortest_ok"),
           AS(fill_null(sum_of(job_runs.duration_mins, over=by_job), 0), "job_total")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.

## X42

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name). job_runs has no formula column, so it is a source only, and jobs has typed columns only as well, so it is a source for the formulas in its own Table.
- Steps: none.
- Finals: jobs (job_id, job_name, runs, avg_mins, id_order).
- Parameters and Keys: none.

Marks
- runs: COUNTIF over job_runs, a LEFT JOIN to a count per job_id, with COALESCE(.., 0).
- avg_mins: AVERAGEIF over job_runs, left NULL inside the join, and IFERROR(.., 0) as COALESCE(.., 0).
- id_order: RANK.EQ ascending with 1 as the third argument, as RANK() OVER (ORDER BY job_id ASC).

Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(r.runs, 0) AS runs,
  COALESCE(a.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r ON j.job_id = r.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins FROM <database>.job_runs GROUP BY job_id) a ON j.job_id = a.job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, count_rows, derived, equals, fill_null, rank, statement, window
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

runs_per_job = derived("runs_per_job", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))

s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(fill_null(runs_per_job.runs, 0), "runs"),
           AS(fill_null(runs_per_job.avg_mins, 0), "avg_mins"),
           AS(rank(over=window(ORDER_BY=jobs.job_id)), "id_order")),
    FROM(jobs),
    LEFT_JOIN(runs_per_job, ON=equals(runs_per_job.job_id, jobs.job_id)),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.

## X43

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: busy_teams (team, runs, shortest, avg_mins); statuses (job_id, status).
- Parameters and Keys: none.

Marks
- busy_teams: the Inner join, then a group by team, with the runs over 4 kept as HAVING.
- statuses: Table.Distinct with no column list, so SELECT DISTINCT. The blank status on run 98 comes through as one NULL row.

Refusals: none.
Left alone: none.
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

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, HAVING, JOIN, SELECT, SELECT_DISTINCT, average_of, count_rows, equals, min_of, more_than, statement)
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
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.

## X44

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region); scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: jobs_with_runs (run_id, job_name); never_scheduled (job_id, job_name, team).
- Parameters and Keys: none.

Marks
- jobs_with_runs: RightOuter, so the jobs table is the left side and job_runs is joined to it with LEFT JOIN. A job with no run keeps a NULL run_id (cache_warm in the sample).
- never_scheduled: LeftAnti, the jobs with no scheduler_runs row.

Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON r.job_id = j.job_id
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
    LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id), reads_all_partitions=True),  # a job with no run keeps NULL
)

never_scheduled = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team),
    FROM(jobs),
    ANTI_JOIN(scheduler_runs, ON=equals(scheduler_runs.job_id, jobs.job_id), reads_all_partitions=True),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.

## X45

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: run_days (run_id, dt); matched (run_id, job_id, dt, status).
- Parameters and Keys: none.

Marks
- run_days: Table.Combine then Table.Distinct with no column list, so UNION of the two selects.
- matched: FullOuter, so FULL OUTER JOIN keeps runs with no schedule (run 99, status TEST, with NULL run_id, job_id and dt) and scheduler rows with no run (run 100, blank status, NULL).

Refusals: none.
Left alone: none.
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

```python
from sqlglot_composer import FROM, FULL_JOIN, SELECT, UNION, equals, statement
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

run_days = UNION(
    statement(SELECT(job_runs.run_id, job_runs.dt), FROM(job_runs, reads_all_partitions=True)),
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt), FROM(scheduler_runs, reads_all_partitions=True)),
)

matched = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt, job_runs.status),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
    FULL_JOIN(job_runs, ON=equals(job_runs.run_id, scheduler_runs.run_id), reads_all_partitions=True),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.

## X51

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins).
- Parameters and Keys: none.

Marks
- not_ok: COUNTIFS with "<>SUCCESS" counts a blank status, as Excel does, so the Hive keeps the IS NULL branch.
- failed_in_job: the wildcard "*ail*" becomes LOWER(status) LIKE '%ail%', as Excel ignores case.
- running_mins: the "<="&dt criterion is a running total over the job's rows, ties included, so RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW.
- long_in_job and failed_in_job are COUNTIFS over the row's own job_id, so COUNT with CASE over PARTITION BY job_id, each with COALESCE.

Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, status, duration_mins, dt,
  COALESCE(COUNT(CASE WHEN duration_mins > 15 THEN 1 END) OVER (PARTITION BY job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (status <> 'SUCCESS' OR status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY job_id), 0) AS failed_in_job,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, any_of, contains, count_rows, equals, is_null, more_than, not_equals, statement, sum_of, window
from references.ops__job_runs import job_runs

by_job = window(PARTITION_BY=job_runs.job_id)
whole_table = window()
running = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt, rows=(None, 0))  # ROWS, not RANGE: ties differ

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins, job_runs.dt,
           AS(count_rows(where=more_than(job_runs.duration_mins, 15), over=by_job), "long_in_job"),
           AS(count_rows(where=any_of(not_equals(job_runs.status, "SUCCESS"), is_null(job_runs.status)), over=whole_table), "not_ok"),
           AS(count_rows(where=contains(job_runs.status, "ail"), over=by_job), "failed_in_job"),  # Excel ignores case here; the Hive lowers status
           AS(sum_of(job_runs.duration_mins, over=running), "running_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.

## X52

Map
- Sources: job_runs (run_id, job_id, duration_mins).
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job).
- Total Row: job_runs (Total Row), a query of its own, one row, with no label and a column per total in order: duration_mins and share. Its share total comes from the final's query, since a total of a window cannot be nested.
- Parameters and Keys: none.

Marks
- share and vs_avg: whole-table SUM and AVG, as SUM(v) OVER () and AVG(v) OVER ().
- rank_in_job: COUNTIFS of the greater rows in the job, plus 1, is RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC).

Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT run_id, job_id, duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

```sql
SELECT SUM(duration_mins) AS duration_mins, SUM(share) AS share
FROM (
  SELECT duration_mins, duration_mins / SUM(duration_mins) OVER () AS share
  FROM <database>.job_runs
) t
```

```python
from sqlglot_composer import AS, FROM, SELECT, average_of, derived, descending, rank, statement, sum_of, window
from references.ops__job_runs import job_runs

whole_table = window()
by_job = window(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.duration_mins))

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins,
           AS(job_runs.duration_mins / sum_of(job_runs.duration_mins, over=whole_table), "share"),
           AS(job_runs.duration_mins - average_of(job_runs.duration_mins, over=whole_table), "vs_avg"),
           AS(rank(over=by_job), "rank_in_job")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)

shares = derived("shares", statement(
    SELECT(job_runs.duration_mins,
           AS(job_runs.duration_mins / sum_of(job_runs.duration_mins, over=whole_table), "share")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
))

job_runs_total = statement(
    SELECT(AS(sum_of(shares.duration_mins), "duration_mins"), AS(sum_of(shares.share), "share")),
    FROM(shares),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.

## X53

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Summary: by_job (job_id, total_mins, runs, longest), a GROUP BY job_id of job_runs, since its only typed column is the one its SUMIFS and COUNTIFS match on.
- Finals: by_job (job_id, total_mins, runs, longest).
- Total Row: by_job's totals are SUMs, a COUNT and a MAX of MAXes, so it needs no query of its own. The summary's query ends WITH ROLLUP, and the NULL job_id row is the Subtotal row, which is the Total Row.
- Parameters and Keys: none.

Marks
- The Subtotal row (job_id NULL) is the Total Row; keep it or filter it out in the view.
- The summary's aggregates have no COALESCE, as each group has rows from job_runs.

Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT job_id,
  SUM(duration_mins) AS total_mins,
  COUNT(*) AS runs,
  MAX(duration_mins) AS longest
FROM <database>.job_runs
GROUP BY job_id WITH ROLLUP
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, count_rows, max_of, rollup, statement, sum_of
from references.ops__job_runs import job_runs

by_job = statement(
    SELECT(job_runs.job_id,
           AS(sum_of(job_runs.duration_mins), "total_mins"),
           AS(count_rows(), "runs"),
           AS(max_of(job_runs.duration_mins), "longest")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(rollup(job_runs.job_id)),  # the rollup row is the Total Row
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.

## X54

Map
- Sources: job_runs (run_id, dt).
- Steps: none.
- Finals: job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label).
- Parameters and Keys: none.

Marks
- a_month_on: EDATE is ADD_MONTHS. A month's end stays one, so a run dated on a month's last day gets that month's last day again.
- week_of: Monday of the week, as d - WEEKDAY(d, 2) + 1.
- month_of: the first day of the month, as text.
- label: TEXT with "yyyy-mm" is DATE_FORMAT with 'yyyy-MM'.
- The dates are typed dates, not text, so no text-date conversion is needed.

Refusals: none.
Left alone: none.
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

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__job_runs import job_runs

# The date columns (month_end, a_month_on, due, week_of, month_of, weekday, label)
# have no Toolbox name in files 03 to 05. Load Copilot file 10 in a new chat for them.
s = statement(
    SELECT(job_runs.run_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. The Python covers only run_id and dt, so load file 10 for the rest. Where the two differ, the checked code wins.

## X55

Map
- Sources: jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens).
- Parameters and Keys: none.

Marks
- title: PROPER(SUBSTITUTE(.., "_", " ")) is INITCAP(REPLACE(..)).
- tag: TEXTJOIN("/", TRUE, ..) is CONCAT_WS('/', ..).
- has_sync: ISNUMBER(SEARCH) is INSTR(LOWER(..), LOWER(..)) > 0, as Excel's SEARCH ignores case.
- tens: the & is CONCAT, and VALUE is CAST(.. AS DOUBLE).

Refusals: none.
Left alone: none.
Fill in: `<database>`.

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

# The text columns (title, tag, code, has_sync, tens) have no Toolbox name in files 03 to 05.
# Load Copilot file 10 in a new chat for them.
s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. The Python covers only the typed columns, so load file 10 for the rest. Where the two differ, the checked code wins.

## X56

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs); scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on).
- Parameters and Keys: none.

Marks
- blank: avg_retry_secs is blank on run 98, and weighted reads it, so it is wrapped as COALESCE(avg_retry_secs, 0), as SUMPRODUCT reads a blank as 0.
- The blank status on run 98 is read only by ISBLANK, which is an -IF form, so no wrap; no_status is status IS NULL.
- scheduled_on: XLOOKUP is a LEFT JOIN on run_id, then COALESCE with 'unscheduled'.

Refusals: none.
Left alone: none.
Fill in: `<database>`.

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
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, statement, sum_of, window
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins, job_runs.avg_retry_secs,
           AS(sum_of(job_runs.duration_mins * fill_null(job_runs.avg_retry_secs, 0), over=window()), "weighted"),
           AS(fill_null(scheduler_runs.dt, "unscheduled"), "scheduled_on")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id), reads_all_partitions=True),
)
# no_status, weeks, at_least_20 and spread have no Toolbox name in files 03 to 05: load Copilot file 10 in a new chat.
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. The Python lacks four columns, so load file 10 for them. Where the two differ, the checked code wins.

## X57

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: picked (run_id, job_id, status, avg_retry_secs, status_lc); ran_jobs (job_id, job_name, team, region).
- Parameters and Keys: none.

Marks
- picked: List.Contains({1, 2}, job_id) is job_id IN (1, 2). The status test keeps a null: status IS NULL OR status LIKE 'S%', with StartsWith kept case.
- picked: the blank avg_retry_secs on run 98 is replaced with 0 (ReplaceValue to 0), as COALESCE(avg_retry_secs, 0).
- picked: Text.Lower is LOWER, so status_lc is LOWER(status), and the blank status stays NULL.
- ran_jobs: a row whose job_id is in job_runs is a LEFT SEMI JOIN, and Text.Contains is LIKE '%a%', case kept.

Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, COALESCE(r.avg_retry_secs, 0) AS avg_retry_secs, LOWER(r.status) AS status_lc
FROM <database>.job_runs r
WHERE r.job_id IN (1, 2) AND (r.status IS NULL OR r.status LIKE 'S%')
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
# status_lc (LOWER of status) has no Toolbox name in files 03 to 05: load Copilot file 10 in a new chat for it.

ran_jobs = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
    SEMI_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id), reads_all_partitions=True),
    WHERE(contains(jobs.job_name, "a")),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. The Python lacks status_lc, so load file 10 for it. Where the two differ, the checked code wins.

## X58

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region); scheduler_runs (run_id, job_id, dt); region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: job_regions (job_id, region); numbered (run_id, dt, duration_mins, n); days_per_job (job_id, days); unrun (run_id, job_id); measures (run_id, measure, amount).
- Parameters and Keys: none.

Marks
- job_regions: the Regions value is a distinct list, and expanding it per job is a CROSS JOIN.
- numbered: Table.Sort then AddIndexColumn is ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC) AS n.
- days_per_job: List.Count(List.Distinct) is COUNT(DISTINCT dt); no blank dt in the sample. The Table.Sort after it has no FirstN or index, so the order is dropped.
- unrun: LeftAnti on run_id and job_id, then Table.Distinct with no column list, so SELECT DISTINCT.
- measures: UnpivotOtherColumns is one SELECT per column unpivoted, stacked with UNION ALL, each with WHERE .. IS NOT NULL, so the blank avg_retry_secs on run 98 is dropped.

Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
SELECT j.job_id, g.region
FROM <database>.jobs j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) g
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
SELECT DISTINCT s.run_id, s.job_id
FROM <database>.scheduler_runs s
LEFT JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.job_id = r.job_id
WHERE r.run_id IS NULL
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
from sqlglot_composer import (ANTI_JOIN, AS, CROSS_JOIN, FROM, GROUP_BY, SELECT, SELECT_DISTINCT, all_of, count_distinct, derived, descending, equals, row_number, statement)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets
from references.ops__scheduler_runs import scheduler_runs

regions = derived("regions", statement(
    SELECT_DISTINCT(region_budgets.region),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's query reads every row
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

unrun = statement(
    SELECT_DISTINCT(scheduler_runs.run_id, scheduler_runs.job_id),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
    ANTI_JOIN(job_runs, ON=all_of(equals(job_runs.run_id, scheduler_runs.run_id),
                                  equals(job_runs.job_id, scheduler_runs.job_id)),
              reads_all_partitions=True),
)

# measures: the labels 'duration_mins' and 'avg_retry_secs' are literal text, which files 03 to 05 do not cover.
# Load Copilot file 10 in a new chat for the UNION ALL of the two SELECTs.
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. The Python lacks measures, so load file 10 for it. Where the two differ, the checked code wins.

## X67

Map
- Sources: jobs (job_id, job_name, team, region); run_alerts (alert_id, run_id, severity, dt); job_runs (run_id, job_id, duration_mins, dt).
- Steps: job_runs, as a CTE, since by_team and noisy_runs read its formula columns team, alerts and running_mins.
- Summary: by_team (team, total_mins, alerted_runs), a GROUP BY team of job_runs, since its only typed column is the one its SUMIFS and COUNTIFS match on.
- Finals: by_team (team, total_mins, alerted_runs); noisy_runs (run_id, team, alerts, running_mins).
- Total Row: by_team's totals are SUMs, so the summary's query ends WITH ROLLUP, and the NULL team row is the Subtotal row.
- Parameters and Keys: none.

Marks
- running_mins: the "<="&dt criterion is a running total over the job's rows, ties included, so RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW.
- alerts: COUNTIF over run_alerts is a LEFT JOIN to a count per run_id, with COALESCE(.., 0).
- team: XLOOKUP is a LEFT JOIN to jobs.

Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt, j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a ON r.run_id = a.run_id
)
SELECT team, SUM(duration_mins) AS total_mins, COUNT(CASE WHEN alerts > 0 THEN 1 END) AS alerted_runs
FROM job_runs
GROUP BY team WITH ROLLUP
```

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt, j.team,
    COALESCE(a.alerts, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) a ON r.run_id = a.run_id
)
SELECT run_id, team, alerts, running_mins
FROM job_runs
WHERE alerts >= 2
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, at_least, count_rows, derived, equals, fill_null, more_than, rollup, statement, sum_of, window
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

alert_counts = derived("alert_counts", statement(
    SELECT(run_alerts.run_id, AS(count_rows(), "alerts")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(run_alerts.run_id),
))

runs_with_team = derived("runs_with_team", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(jobs.team, "team"),
           AS(fill_null(alert_counts.alerts, 0), "alerts"),
           AS(fill_null(sum_of(job_runs.duration_mins,
                               over=window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt, rows=(None, 0))), 0),
              "running_mins")),  # ROWS, not RANGE: ties differ
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    LEFT_JOIN(alert_counts, ON=equals(alert_counts.run_id, job_runs.run_id)),
))

by_team = statement(
    SELECT(runs_with_team.team,
           AS(sum_of(runs_with_team.duration_mins), "total_mins"),
           AS(count_rows(where=more_than(runs_with_team.alerts, 0)), "alerted_runs")),
    FROM(runs_with_team),
    GROUP_BY(rollup(runs_with_team.team)),  # the rollup row is the Total Row
)

noisy_runs = statement(
    SELECT(runs_with_team.run_id, runs_with_team.team, runs_with_team.alerts, runs_with_team.running_mins),
    FROM(runs_with_team),
    WHERE(at_least(runs_with_team.alerts, 2)),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.

## X68

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region); region_budgets (job_id, budget_cents, region).
- Steps: base, the connection-only query, as a CTE, since by_region and top_runs read it.
- Finals: by_region (region, total_mins, runs, share); top_runs (run_id, job_name, region).
- Total Row: job_runs is not involved; by_region (Total Row) is a query of its own, one row, with no label and one column, total_mins.
- Parameters and Keys: none.

Marks
- base: the Inner join to jobs keeps only runs with a job; the LeftOuter join to region_budgets keeps every run, with region NULL if it has none.
- by_region: the group keeps only regions with at least 2 runs (HAVING COUNT(*) >= 2), and share is total_mins over SUM(total_mins) of the kept rows.
- top_runs: Table.Sort then FirstN is ORDER BY duration_mins DESC, run_id ASC with LIMIT 2.

Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT region, total_mins, runs, total_mins / SUM(total_mins) OVER () AS share
FROM (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) g
```

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT SUM(total_mins) AS total_mins
FROM (
  SELECT SUM(duration_mins) AS total_mins
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) g
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

groups = derived("groups", statement(
    SELECT(base.region, AS(sum_of(base.duration_mins), "total_mins"), AS(count_rows(), "runs")),
    FROM(base),
    GROUP_BY(base.region),
    HAVING(at_least(count_rows(), 2)),
))

by_region = statement(
    SELECT(groups.region, groups.total_mins, groups.runs,
           AS(groups.total_mins / sum_of(groups.total_mins, over=window()), "share")),
    FROM(groups),
)

by_region_total = statement(
    SELECT(AS(sum_of(groups.total_mins), "total_mins")),
    FROM(groups),
)

top_runs = statement(
    SELECT(base.run_id, base.job_name, base.region),
    FROM(base),
    ORDER_BY(descending(base.duration_mins), base.run_id),
    LIMIT(2),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.

## X71

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: ok_runs, the query, as a CTE, since ok_by_job reads it.
- Finals: ok_runs (run_id, job_id, duration_mins, hours); ok_by_job (job_id, total_mins).
- Parameters and Keys: none.

Marks
- ok_runs: hours is duration_mins / 60, as the Table's own formula column, and its query is the step.
- The status test is = 'SUCCESS', so the blank status on run 98 is left out, as M leaves it out.

Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT run_id, job_id, duration_mins, duration_mins / 60 AS hours
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

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, derived, equals, statement, sum_of
from references.ops__job_runs import job_runs

ok_runs = derived("ok_runs", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
))

ok_runs_table = statement(
    SELECT(ok_runs.run_id, ok_runs.job_id, ok_runs.duration_mins,
           AS(ok_runs.duration_mins / 60, "hours")),
    FROM(ok_runs),
)

ok_by_job = statement(
    SELECT(ok_runs.job_id, AS(sum_of(ok_runs.duration_mins), "total_mins")),
    FROM(ok_runs),
    GROUP_BY(ok_runs.job_id),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.

## X72

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team).
- Steps: jobs, as a CTE, since by_team and busy_jobs read its formula columns runs and total.
- Summary: by_team (team, team_total), a GROUP BY team of jobs, since its only typed column is the one its SUMIFS matches on.
- Finals: by_team (team, team_total); busy_jobs (job_id, job_name, runs).
- Total Row: none in this workbook.
- Parameters and Keys: none.

Marks
- runs: COUNTIF over job_runs is a LEFT JOIN to a count per job_id, with COALESCE(.., 0).
- total: SUMIF over job_runs is a LEFT JOIN to a sum per job_id, with COALESCE(.., 0).

Refusals: none.
Left alone: none.
Fill in: `<database>`.

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(r.runs, 0) AS runs,
    COALESCE(t.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r ON j.job_id = r.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) t ON j.job_id = t.job_id
)
SELECT team, SUM(total) AS team_total
FROM jobs
GROUP BY team
```

```sql
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(r.runs, 0) AS runs,
    COALESCE(t.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r ON j.job_id = r.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) t ON j.job_id = t.job_id
)
SELECT job_id, job_name, runs
FROM jobs
WHERE runs >= 3
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, at_least, count_rows, derived, equals, fill_null, statement, sum_of
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

runs_per_job = derived("runs_per_job", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))

with_totals = derived("with_totals", statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(fill_null(runs_per_job.runs, 0), "runs"),
           AS(fill_null(runs_per_job.total, 0), "total")),
    FROM(jobs),
    LEFT_JOIN(runs_per_job, ON=equals(runs_per_job.job_id, jobs.job_id)),
))

by_team = statement(
    SELECT(with_totals.team, AS(sum_of(with_totals.total), "team_total")),
    FROM(with_totals),
    GROUP_BY(with_totals.team),
)

busy_jobs = statement(
    SELECT(with_totals.job_id, with_totals.job_name, with_totals.runs),
    FROM(with_totals),
    WHERE(at_least(with_totals.runs, 3)),
)
```

Take out of the workbook anything you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Where the two differ, the checked code wins.
