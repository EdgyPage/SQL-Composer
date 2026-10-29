date: 2026-10-29
arm: C
model: haiku
files: f80b90b

## X20

Map. Sources: run_alerts (typed alert_id, run_id, severity, dt; read by the alert_pivot query). Steps: none. Finals: alert_pivot (run_id, high, low), loaded by the Power Query "alert_pivot" and read by nothing. Parameters and Keys: none; Keys is empty and no value is typed over a formula, so no Keys row is needed. Refused: none. Left alone: the Steps sheet, which holds no Table.

Marks:
- Table.Pivot: one column per severity value in the sample (high, low), NULL where none. The pivot's columns are now fixed: a new severity value in later data gets no column.
- The pivot groups by run_id, the other column, and adds up the 1 each row gets from the Counted step, so THEN 1 counts.
- The Python counts with count_rows, which gives 0 where no row matches, while M gives null. Both sample runs have high and low rows, so the sample shows no difference.

```sql
SELECT r.run_id,
  SUM(CASE WHEN r.severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN r.severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts r
WHERE r.run_id = 97 OR r.run_id = 101
GROUP BY r.run_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, any_of, count_rows, equals, statement
from references.ops__run_alerts import run_alerts

r = AS(run_alerts, "r")

s = statement(
    SELECT(
        r.run_id,
        AS(count_rows(where=equals(r.severity, "high")), "high"),
        AS(count_rows(where=equals(r.severity, "low")), "low"),
    ),
    FROM(r, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(any_of(equals(r.run_id, 97), equals(r.run_id, 101))),
    GROUP_BY(r.run_id),
)
```

Take out of the workbook what you don't want converted, such as the Steps sheet. Fill in `<database>` in the Hive (ops in the Python stands for it, as in file 12's example). Run `project.convert` on the Hive; its checked code wins where the two differ.

## X41

Map. Sources: job_runs (typed run_id, job_id, status, duration_mins). Steps: none. Finals: job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- RANK.EQ(x, column) is RANK() OVER (ORDER BY x DESC); ties share a rank, as Excel does.
- MINIFS over its own Table is MIN over a CASE, partitioned by job_id, with COALESCE, as Excel gives 0 where nothing matches.
- SUMIF over its own Table is SUM over the job_id partition, with COALESCE.
- Blank status in run 98: it sits inside the MINIFS condition, so it is skipped and not wrapped.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins,
  RANK() OVER (ORDER BY r.duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN r.status = 'SUCCESS' THEN r.duration_mins END) OVER (PARTITION BY r.job_id), 0) AS shortest_ok,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id), 0) AS job_total
FROM <database>.job_runs r
```

```python
from sqlglot_composer import AS, FROM, SELECT, descending, equals, fill_null, min_of, rank, statement, sum_of, window
from references.ops__job_runs import job_runs

by_job = window(PARTITION_BY=job_runs.job_id)
longest = window(ORDER_BY=descending(job_runs.duration_mins))

s = statement(
    SELECT(
        job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
        AS(rank(over=longest), "longest_first"),
        AS(fill_null(min_of(job_runs.duration_mins, where=equals(job_runs.status, "SUCCESS"), over=by_job), 0), "shortest_ok"),
        AS(fill_null(sum_of(job_runs.duration_mins, over=by_job), 0), "job_total"),
    ),
    FROM(job_runs),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ.

## X42

Map. Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt; read by the jobs formulas) and jobs (job_id, job_name). Steps: none. Finals: jobs (job_id, job_name, runs, avg_mins, id_order). Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- COUNTIF over another Table: COUNT(*) per job_id, joined with LEFT JOIN, COALESCE to 0.
- AVERAGEIF over another Table: AVG per job_id, left NULL; the IFERROR(..., 0) becomes COALESCE(avg, 0).
- RANK.EQ with 1 as third argument is ascending: RANK() OVER (ORDER BY job_id).
- cache_warm (job 4) has no runs, so runs and avg_mins are 0.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(a.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins FROM <database>.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, count_rows, derived, equals, fill_null, rank, statement, window
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

counts = derived("counts", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "runs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
averages = derived("averages", statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))

s = statement(
    SELECT(
        jobs.job_id, jobs.job_name,
        AS(fill_null(counts.runs, 0), "runs"),
        AS(fill_null(averages.avg_mins, 0), "avg_mins"),
        AS(rank(over=window(ORDER_BY=jobs.job_id)), "id_order"),
    ),
    FROM(jobs),
    LEFT_JOIN(counts, ON=equals(counts.job_id, jobs.job_id)),
    LEFT_JOIN(averages, ON=equals(averages.job_id, jobs.job_id)),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ.

## X43

Map. Sources: job_runs (job_id, status, duration_mins, dt) and jobs (job_id, job_name, team, region). Steps: none. Finals: busy_teams (team, runs, shortest, avg_mins), loaded by the Power Query "busy_teams"; statuses (job_id, status), loaded by the Power Query "statuses". Nothing reads either, so both are finals. Parameters and Keys: none. Refused: none. Left alone: the Steps sheet.

Marks:
- busy_teams: the inner join on job_id, then Table.Group as GROUP BY team, and the Table.SelectRows after it as HAVING, repeating COUNT(*). Only finance passes (5 runs; shortest 15 and average 22.6 match the sample). web has no runs, so it is absent.
- statuses: Table.Distinct alone is SELECT DISTINCT. The blank status of job 2 stays as NULL, as M keeps a null in Distinct.

```sql
SELECT j.team, COUNT(*) AS runs, MIN(r.duration_mins) AS shortest, AVG(r.duration_mins) AS avg_mins
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.team
HAVING COUNT(*) > 4
```

```sql
SELECT DISTINCT r.job_id, r.status
FROM <database>.job_runs r
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, HAVING, JOIN, SELECT, SELECT_DISTINCT, average_of, count_rows, equals, min_of, more_than, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

busy_teams = statement(
    SELECT(
        jobs.team,
        AS(count_rows(), "runs"),
        AS(min_of(job_runs.duration_mins), "shortest"),
        AS(average_of(job_runs.duration_mins), "avg_mins"),
    ),
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

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ.

## X44

Map. Sources: job_runs (run_id, job_id, dt), jobs (job_id, job_name, team, region) and scheduler_runs (run_id, job_id, dt). Steps: none. Finals: jobs_with_runs (run_id, job_name), loaded by the Power Query "jobs_with_runs"; never_scheduled (job_id, job_name, team), loaded by the Power Query "never_scheduled". Nothing reads either. Parameters and Keys: none. Refused: none. Left alone: the Steps sheet.

Marks:
- RightOuter: a LEFT JOIN with the two tables swapped, so every job is kept. cache_warm has no run, so its run_id is NULL, as the sample shows.
- LeftAnti: a LEFT JOIN with WHERE on the right key IS NULL, keeping jobs' columns only. Only cache_warm has no scheduler run.
- The jobs_with_runs join is on job_id, not job_runs's whole key (run_id), so the Toolbox warns about repeats. The sample keeps every run of a job, so the repeats are wanted; add many_matches=True once the user confirms that.

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

# many_matches=True is left out: add it once the user confirms the repeats are wanted.
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

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ.

## X45

Map. Sources: job_runs (run_id, job_id, dt, status) and scheduler_runs (run_id, job_id, dt). Steps: none. Finals: run_days (run_id, dt), loaded by the Power Query "run_days"; matched (run_id, job_id, dt, status), loaded by the Power Query "matched". Nothing reads either. Parameters and Keys: none. Refused: none. Left alone: the Steps sheet.

Marks:
- run_days: Table.Combine inside Table.Distinct is UNION, so the duplicate (run, day) pairs drop out. Ten rows, as the sample shows.
- matched: a FULL OUTER JOIN keeping the scheduler's columns, as M does. Run 99 is only in job_runs, so its run_id, job_id and dt are NULL and its status is TEST, as the sample shows. Run 100 is only in scheduler_runs, so its status is NULL. The blank status of run 98 stays NULL.

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

runs_days = statement(
    SELECT(job_runs.run_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
scheduled_days = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
run_days = UNION(runs_days, scheduled_days)

matched = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt, job_runs.status),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
    FULL_JOIN(job_runs, ON=equals(job_runs.run_id, scheduler_runs.run_id), reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ.

## X51

Map. Sources: job_runs (run_id, job_id, status, duration_mins, dt). Steps: none. Finals: job_runs (run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins). Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- COUNTIFS over its own Table with [@job_id] is a COUNT over a job_id partition, with the condition as a CASE, and COALESCE.
- COUNTIFS on status "<>SUCCESS" is `(status <> 'SUCCESS' OR status IS NULL)`, as Excel counts a blank there. The blank in run 98 is counted and not wrapped.
- "*ail*" is LOWER(status) LIKE '%ail%', as Excel ignores case.
- SUMIFS with "<="&[@dt] over its own Table is a running total over the job_id partition, RANGE so that tied dates are included, as Excel does.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.dt,
  COALESCE(COUNT(CASE WHEN r.duration_mins > 15 THEN 1 END) OVER (PARTITION BY r.job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (r.status <> 'SUCCESS' OR r.status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(r.status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY r.job_id), 0) AS failed_in_job,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs r
```

```python
from sqlglot_composer import AS, FROM, SELECT, any_of, contains, count_rows, is_null, more_than, not_equals, statement, sum_of, window
from references.ops__job_runs import job_runs

by_job = window(PARTITION_BY=job_runs.job_id)
whole = window()
# rows= counts rows, not tied dates: on dt ties the sum can differ from Excel's. The Hive's RANGE is the checked form.
running = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt, rows=(None, 0))

s = statement(
    SELECT(
        job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins, job_runs.dt,
        AS(count_rows(where=more_than(job_runs.duration_mins, 15), over=by_job), "long_in_job"),
        AS(count_rows(where=any_of(not_equals(job_runs.status, "SUCCESS"), is_null(job_runs.status)), over=whole), "not_ok"),
        # contains keeps case, so "AIL" matches the sample's capitals; LOWER for any case needs file 10.
        AS(count_rows(where=contains(job_runs.status, "AIL"), over=by_job), "failed_in_job"),
        AS(sum_of(job_runs.duration_mins, over=running), "running_mins"),
    ),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ. The Python's case-blind match and tied-date running total differ from Excel; the Hive is the checked form for both.

## X52

Map. Sources: job_runs (run_id, job_id, duration_mins). Steps: a CTE, runs, inside the Total Row query only, which reads share. Finals: job_runs (run_id, job_id, duration_mins, share, vs_avg, rank_in_job). Total Row: job_runs (Total Row), a query of its own with one row and a column per total (duration_mins, share), with no label. Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- SUM(duration_mins) in the share formula is a window over the whole column, so share is `duration_mins / SUM(duration_mins) OVER ()`.
- vs_avg is `duration_mins - AVG(duration_mins) OVER ()`.
- rank_in_job is COUNTIFS(...)+1, which is RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC); ties share a rank in both.
- The Total Row's share total cannot add up a window inside an aggregate, so the share is worked out first in the CTE.
- The "Total" label is dropped, as the Total Row has no label.

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  r.duration_mins / SUM(r.duration_mins) OVER () AS share,
  r.duration_mins - AVG(r.duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY r.job_id ORDER BY r.duration_mins DESC) AS rank_in_job
FROM <database>.job_runs r
```

```sql
WITH runs AS (
  SELECT r.duration_mins, r.duration_mins / SUM(r.duration_mins) OVER () AS share
  FROM <database>.job_runs r
)
SELECT SUM(duration_mins) AS duration_mins, SUM(share) AS share
FROM runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, average_of, derived, descending, rank, statement, sum_of, window
from references.ops__job_runs import job_runs

whole = window()

s = statement(
    SELECT(
        job_runs.run_id, job_runs.job_id, job_runs.duration_mins,
        AS(job_runs.duration_mins / sum_of(job_runs.duration_mins, over=whole), "share"),
        AS(job_runs.duration_mins - average_of(job_runs.duration_mins, over=whole), "vs_avg"),
        AS(rank(over=window(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.duration_mins))), "rank_in_job"),
    ),
    FROM(job_runs),
)

shares = derived("shares", statement(
    SELECT(job_runs.duration_mins, AS(job_runs.duration_mins / sum_of(job_runs.duration_mins, over=whole), "share")),
    FROM(job_runs),
))
total_row = statement(
    SELECT(AS(sum_of(shares.duration_mins), "duration_mins"), AS(sum_of(shares.share), "share")),  # the Toolbox may refuse adding up a window's value; if so the Hive stands
    FROM(shares),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ.

## X53

Map. Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Steps: none. Finals: by_job (job_id, total_mins, runs, longest). by_job's only typed column is job_id, which its SUMIFS and COUNTIFS match on, so it is a summary: a GROUP BY of job_runs. Total Row: by_job (Total Row) needs no query of its own, because its totals add up SUMs and COUNTs and take the MAX of MAXes; the summary's query ends GROUP BY job_id WITH ROLLUP, and the NULL job_id row is the total. Parameters and Keys: none. Refused: none. Left alone: the Steps sheet.

Marks:
- SUMIFS, COUNTIFS and MAXIFS over the job_runs Table become SUM, COUNT and MAX of each job_id group, each with COALESCE, as Excel gives 0 where nothing matches.
- SUBTOTAL(109) is SUM and SUBTOTAL(104) is MAX, so the ROLLUP row is the Total Row.

```sql
SELECT r.job_id,
  COALESCE(SUM(r.duration_mins), 0) AS total_mins,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(MAX(r.duration_mins), 0) AS longest
FROM <database>.job_runs r
GROUP BY r.job_id WITH ROLLUP
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, count_rows, max_of, rollup, statement, sum_of
from references.ops__job_runs import job_runs

by_job = statement(
    SELECT(
        job_runs.job_id,
        AS(sum_of(job_runs.duration_mins), "total_mins"),
        AS(count_rows(), "runs"),
        AS(max_of(job_runs.duration_mins), "longest"),
    ),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(rollup(job_runs.job_id)),  # the NULL job_id row is the Total Row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ.

## X54

Map. Sources: job_runs (run_id, dt) and scheduler_runs (run_id, job_id, dt). Steps: none. Finals: job_runs (run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label), since nothing reads it; scheduler_runs (run_id, job_id, dt), since nothing reads it either. Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- EDATE is ADD_MONTHS. ADD_MONTHS keeps a month's end as the month's end, as EDATE does, so check any date on the 31st.
- week_of is `d - WEEKDAY(d, 2) + 1`, the Monday of the week, written as CAST(NEXT_DAY(DATE_ADD(d, 7 * -1), 'MO') AS STRING).
- month_of is DATE(YEAR(d), MONTH(d), 1), written as CAST(TRUNC(d, 'MM') AS STRING).
- label is TEXT(dt, "yyyy-mm"), written as DATE_FORMAT(dt, 'yyyy-MM').
- The Python covers only week_of and month_of. month_end, a_month_on, due, weekday and label have no Toolbox name in the loaded files; file 10 (Hive functions) covers them in a new chat, or use the Hive.

```sql
SELECT r.run_id, r.dt,
  LAST_DAY(r.dt) AS month_end,
  ADD_MONTHS(r.dt, 1) AS a_month_on,
  DATE_ADD(r.dt, 7) AS due,
  CAST(NEXT_DAY(DATE_ADD(r.dt, 7 * -1), 'MO') AS STRING) AS week_of,
  CAST(TRUNC(r.dt, 'MM') AS STRING) AS month_of,
  DAYOFWEEK(r.dt) AS weekday,
  DATE_FORMAT(r.dt, 'yyyy-MM') AS label
FROM <database>.job_runs r
```

```sql
SELECT s.run_id, s.job_id, s.dt
FROM <database>.scheduler_runs s
```

```python
from sqlglot_composer import AS, FROM, SELECT, month_start, statement, week_start
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

s = statement(
    SELECT(
        job_runs.run_id, job_runs.dt,
        AS(week_start(job_runs.dt), "week_of"),
        AS(month_start(job_runs.dt), "month_of"),
    ),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)

scheduled = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). The month_end, a_month_on, due, weekday and label columns need file 10 or the Hive above. Run `project.convert` on the Hive; its checked code wins where the two differ.

## X55

Map. Sources: jobs (job_id, job_name, team, region). Steps: none. Finals: jobs (job_id, job_name, team, region, title, tag, code, has_sync, tens), since nothing reads it. Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- PROPER(SUBSTITUTE(name, "_", " ")) is INITCAP(REPLACE(job_name, '_', ' ')).
- TEXTJOIN("/", TRUE, team, region) is CONCAT_WS('/', team, region); CONCAT_WS skips a blank, as TRUE does.
- CONCATENATE(region, "-", job_id) is CONCAT(region, '-', job_id).
- ISNUMBER(SEARCH("SYNC", job_name)) is INSTR(LOWER(job_name), LOWER('SYNC')) > 0, as SEARCH ignores case.
- VALUE(job_id & "0") is CAST(CONCAT(job_id, '0') AS DOUBLE).
- The Python covers only the typed columns: none of the five formula columns has a Toolbox name in the loaded files, so use file 10 or the Hive.

```sql
SELECT j.job_id, j.job_name, j.team, j.region,
  INITCAP(REPLACE(j.job_name, '_', ' ')) AS title,
  CONCAT_WS('/', j.team, j.region) AS tag,
  CONCAT(j.region, '-', j.job_id) AS code,
  INSTR(LOWER(j.job_name), LOWER('SYNC')) > 0 AS has_sync,
  CAST(CONCAT(j.job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs j
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ.

## X56

Map. Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs) and scheduler_runs (run_id, job_id, dt; read by the scheduled_on XLOOKUP). Steps: none. Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on), since nothing reads it. Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- ISBLANK(status) is `status IS NULL`.
- INT(duration / 7) is FLOOR(duration_mins / 7).
- MAX(duration, 20) on one row is GREATEST(duration_mins, 20).
- STDEV.S is STDDEV_SAMP over the whole column.
- SUMPRODUCT(duration, avg_retry) is SUM(a * b) OVER (). The blank avg_retry_secs in run 98 is read by this formula, so it is wrapped: COALESCE(avg_retry_secs, 0), as blank.
- XLOOKUP with "unscheduled" is a LEFT JOIN to scheduler_runs on run_id, then COALESCE(dt, 'unscheduled'). Each run_id is unique in scheduler_runs, so the join keeps one row per run.
- The Python covers the join, weighted and scheduled_on only: no_status, weeks, at_least_20 and spread have no Toolbox name in the loaded files, so use file 10 or the Hive.

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

whole = window()

s = statement(
    SELECT(
        job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins, job_runs.avg_retry_secs,
        AS(sum_of(job_runs.duration_mins * fill_null(job_runs.avg_retry_secs, 0), over=whole), "weighted"),
        AS(fill_null(scheduler_runs.dt, "unscheduled"), "scheduled_on"),
    ),
    FROM(job_runs),
    LEFT_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id), reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). The no_status, weeks, at_least_20 and spread columns need file 10 or the Hive above. Run `project.convert` on the Hive; its checked code wins where the two differ.

## X57

Map. Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (job_id, job_name, team, region). Steps: none. Finals: picked (run_id, job_id, status, avg_retry_secs, status_lc), loaded by the Power Query "picked"; ran_jobs (job_id, job_name, team, region), loaded by the Power Query "ran_jobs". Nothing reads either. Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- `[status] = null` is `status IS NULL`, so the blank status of run 98 is kept.
- Text.StartsWith(status, "S") is LIKE 'S%', case kept.
- Table.ReplaceValue(null, 0) on avg_retry_secs is COALESCE(avg_retry_secs, 0), as blank: run 98's blank becomes 0, as the sample shows.
- Text.Lower(status) is LOWER(status); the blank status gives NULL.
- ran_jobs: List.Contains(job_runs[job_id], [job_id]) is a LEFT SEMI JOIN on job_id, which keeps jobs' columns only.
- Text.Contains(job_name, "a") is LIKE '%a%', case kept, so only lowercase a matches. Only nightly_load passes, as the sample shows.
- The Python does not cover LOWER(status) for status_lc: no Toolbox name for it is loaded, so use file 10 or the Hive.

```sql
SELECT r.run_id, r.job_id, r.status, COALESCE(r.avg_retry_secs, 0) AS avg_retry_secs,
  LOWER(r.status) AS status_lc
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
from sqlglot_composer import AS, FROM, SEMI_JOIN, SELECT, WHERE, any_of, contains, equals, fill_null, is_in, is_null, starts_with, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

picked = statement(
    SELECT(
        job_runs.run_id, job_runs.job_id, job_runs.status,
        AS(fill_null(job_runs.avg_retry_secs, 0), "avg_retry_secs"),
    ),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_in(job_runs.job_id, [1, 2]), any_of(is_null(job_runs.status), starts_with(job_runs.status, "S"))),
)

ran_jobs = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
    SEMI_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id), reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(contains(jobs.job_name, "a")),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). The status_lc column is not in the Python: it needs LOWER, which file 10 covers. Run `project.convert` on the Hive; its checked code wins where the two differ.

## X58

Map. Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), jobs (job_id, job_name, team, region), scheduler_runs (run_id, job_id, dt) and region_budgets (job_id, budget_cents, region). Steps: none. Finals: job_regions (job_id, region), loaded by the Power Query "job_regions"; numbered (run_id, dt, duration_mins, n); days_per_job (job_id, days); unrun (run_id, job_id); measures (run_id, measure, amount). Nothing reads any of them. Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- job_regions: each job paired with each distinct region, as a CROSS JOIN with SELECT DISTINCT region: 4 jobs by 2 regions gives 8 rows, as the sample shows.
- numbered: the sort is followed by an index, so it is ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC). The ties 97 and 103 at 30 are ordered by run_id, as the sample shows.
- days_per_job: List.Count(List.Distinct(dt)) is COUNT(DISTINCT dt). dt has no blank in the sample. The Table.Sort after the group has no FirstN or index after it, so the order is dropped: no ORDER BY.
- unrun: a LEFT ANTI join on both keys, then Table.Distinct as SELECT DISTINCT. Only run 100 (job 3) is in scheduler_runs but not job_runs, as the sample shows.
- measures: UnpivotOtherColumns is one SELECT per column, stacked with UNION ALL, each with WHERE IS NOT NULL, as M drops a null. Run 98's blank avg_retry_secs drops out, so its only row is the duration.
- The Python writes the literal labels "duration_mins" and "avg_retry_secs" as text, a form no loaded file names; the checked code wins if it differs.

```sql
SELECT j.job_id, rg.region
FROM <database>.jobs j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) rg
```

```sql
SELECT r.run_id, r.dt, r.duration_mins,
  ROW_NUMBER() OVER (ORDER BY r.duration_mins DESC, r.run_id ASC) AS n
FROM <database>.job_runs r
```

```sql
SELECT r.job_id, COUNT(DISTINCT r.dt) AS days
FROM <database>.job_runs r
GROUP BY r.job_id
```

```sql
SELECT DISTINCT s.run_id, s.job_id
FROM <database>.scheduler_runs s
LEFT JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.job_id = r.job_id
WHERE r.run_id IS NULL
```

```sql
SELECT r.run_id, 'duration_mins' AS measure, r.duration_mins AS amount
FROM <database>.job_runs r
WHERE r.duration_mins IS NOT NULL
UNION ALL
SELECT r.run_id, 'avg_retry_secs' AS measure, r.avg_retry_secs AS amount
FROM <database>.job_runs r
WHERE r.avg_retry_secs IS NOT NULL
```

```python
from sqlglot_composer import (ANTI_JOIN, AS, CROSS_JOIN, FROM, GROUP_BY, SELECT, SELECT_DISTINCT,
                              UNION_ALL, WHERE, all_of, count_distinct, derived, descending,
                              equals, is_not_null, row_number, statement)
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs
from references.ops__region_budgets import region_budgets

regions = derived("regions", statement(SELECT_DISTINCT(region_budgets.region), FROM(region_budgets)))
job_regions = statement(
    SELECT(jobs.job_id, regions.region),
    FROM(jobs),
    CROSS_JOIN(regions),
)

numbered = statement(
    SELECT(
        job_runs.run_id, job_runs.dt, job_runs.duration_mins,
        AS(row_number(ORDER_BY=[descending(job_runs.duration_mins), job_runs.run_id]), "n"),
    ),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)

# No ORDER BY: the sort after the group is dropped, as a Hive table holds no order.
days_per_job = statement(
    SELECT(job_runs.job_id, AS(count_distinct(job_runs.dt), "days")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
)

unrun = statement(
    SELECT_DISTINCT(scheduler_runs.run_id, scheduler_runs.job_id),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
    ANTI_JOIN(
        job_runs,
        ON=all_of(equals(job_runs.run_id, scheduler_runs.run_id), equals(job_runs.job_id, scheduler_runs.job_id)),
        reads_all_partitions=True,  # a workbook's query reads every row
    ),
)

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

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ.

## X67

Map. Sources: jobs (job_id, job_name, team, region), run_alerts (alert_id, run_id, severity, dt) and job_runs's typed columns (run_id, job_id, duration_mins, dt). Steps: runs_step, the job_runs Table with its formulas team, alerts and running_mins, read by by_team and by the noisy_runs query, so it is a CTE in each final that reads it. Finals: by_team (team, total_mins, alerted_runs), a summary of runs_step, with its Total Row as the WITH ROLLUP row (no query of its own); noisy_runs (run_id, team, alerts, running_mins), loaded by the Power Query "noisy_runs". Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- XLOOKUP(job_id, jobs[job_id], jobs[team]) is a LEFT JOIN to jobs, then team. It has no fourth argument, so there is no COALESCE.
- COUNTIF(run_alerts[run_id], [@run_id]) is COUNT(*) per run_id, joined with LEFT JOIN, with COALESCE to 0.
- SUMIFS with "<="&[@dt] is a running total over the job_id partition, RANGE so tied dates are included. Run 101 (dt 24) gets 67, which includes run 104 on the same date, as the sample shows.
- by_team: SUBTOTAL(109) is SUM, so the ROLLUP row is the Total Row.
- The Python below covers the joins, the counts and the summary, but its running window is ROWS, which counts rows and so gives 27 for run 101 instead of 67. The Hive is the checked form.

```sql
WITH runs_step AS (
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
FROM runs_step
GROUP BY team WITH ROLLUP
```

```sql
WITH runs_step AS (
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
FROM runs_step
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

# rows= counts rows, not tied dates: run 101 gives 27 here, where Excel gives 67. The Hive is the checked form.
running = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt, rows=(None, 0))

runs_step = derived("runs_step", statement(
    SELECT(
        job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
        AS(jobs.team, "team"),
        AS(fill_null(alert_counts.alerts, 0), "alerts"),
        AS(fill_null(sum_of(job_runs.duration_mins, over=running), 0), "running_mins"),
    ),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    LEFT_JOIN(alert_counts, ON=equals(alert_counts.run_id, job_runs.run_id)),
))

whole = window()
by_team = statement(
    SELECT(
        runs_step.team,
        AS(fill_null(sum_of(runs_step.duration_mins), 0), "total_mins"),
        AS(fill_null(count_rows(where=more_than(runs_step.alerts, 0)), 0), "alerted_runs"),
    ),
    FROM(runs_step),
    GROUP_BY(rollup(runs_step.team)),  # the NULL team row is the Total Row
)

noisy_runs = statement(
    SELECT(runs_step.run_id, runs_step.team, runs_step.alerts, runs_step.running_mins),
    FROM(runs_step),
    WHERE(at_least(runs_step.alerts, 2)),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ, and on tied dates it does.

## X68

Map. Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), jobs (job_id, job_name, team, region) and region_budgets (job_id, budget_cents, region). Steps: base, the connection-only Power Query "base". Two queries read it, so it is a step and a CTE, not left out. Finals: by_region (region, total_mins, runs, share), loaded by the Power Query "by_region"; top_runs (run_id, job_name, region), loaded by the Power Query "top_runs". Total Row: by_region (Total Row), a query of its own with one column, total_mins, and no label. Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- base: the inner join to jobs and the LEFT OUTER join to region_budgets give each run its job_name and region. region_budgets has one row per job, so no run is repeated.
- by_region: Table.Group is GROUP BY region with HAVING COUNT(*) >= 2, as the sample's eu (7 runs) and us (2) show. share is total_mins over the SUM of the Table's rows, a window on the grouped rows, so the grouped rows sit in a subquery. eu is 120 and us 60.
- top_runs: Table.Sort then FirstN is ORDER BY duration_mins DESC, run_id ASC, LIMIT 2. The tie at 30 between 97 and 103 goes to 97, as the sample shows.
- The Total Row sums the grouped totals, with no label.

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.duration_mins, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT g.region, g.total_mins, g.runs,
  g.total_mins / SUM(g.total_mins) OVER () AS share
FROM (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) g
```

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.duration_mins, j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT SUM(g.total_mins) AS total_mins
FROM (
  SELECT region, SUM(duration_mins) AS total_mins
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
) g
```

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.duration_mins, j.job_name, b.region
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
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, jobs.job_name, region_budgets.region),
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

whole = window()
by_region = statement(
    SELECT(
        grouped.region, grouped.total_mins, grouped.runs,
        AS(grouped.total_mins / sum_of(grouped.total_mins, over=whole), "share"),
    ),
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

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ.

## X71

Map. Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Steps: ok, the Power Query query "ok_runs" (status = 'SUCCESS', three columns), read by the query "ok_by_job", so it is a CTE in that final's query. Finals: ok_runs (run_id, job_id, duration_mins, hours), loaded by the Power Query "ok_runs"; ok_by_job (job_id, total_mins), loaded by the Power Query "ok_by_job". Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- `[status] = "SUCCESS"` is `status = 'SUCCESS'`. The blank status of run 98 and the TEST row are both dropped, as M's = keeps only a true result, and NULL = 'SUCCESS' is not true in Hive either.
- hours is duration_mins / 60, as the formula; Hive's `/` gives a decimal.
- ok_by_job: Table.Group is GROUP BY job_id with SUM(duration_mins). Job 1 gives 62, job 2 gives 18 and job 3 gives 30, as the sample shows.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.duration_mins / 60 AS hours
FROM <database>.job_runs r
WHERE r.status = 'SUCCESS'
```

```sql
WITH ok AS (
  SELECT r.run_id, r.job_id, r.duration_mins
  FROM <database>.job_runs r
  WHERE r.status = 'SUCCESS'
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

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ.

## X72

Map. Sources: jobs (job_id, job_name, team) and job_runs (run_id, job_id, duration_mins, dt). Steps: jobs_step, the jobs Table with its formula columns runs (COUNTIF) and total (SUMIF), read by by_team and by the busy_jobs query, so it is a CTE in each final that reads it. Finals: by_team (team, team_total), a summary: its only typed column is team, which its SUMIFS match on, so it is a GROUP BY of jobs_step; busy_jobs (job_id, job_name, runs), loaded by the Power Query "busy_jobs". Parameters and Keys: none; Keys is empty and no value is typed over a formula. Refused: none. Left alone: the Steps sheet.

Marks:
- COUNTIF(job_runs[job_id], [@job_id]) is COUNT(*) per job_id, joined with LEFT JOIN, with COALESCE to 0.
- SUMIF(job_runs[job_id], [@job_id], duration_mins) is SUM per job_id, joined with LEFT JOIN, with COALESCE to 0.
- by_team: the SUMIFS over jobs[total] by team is SUM(total) grouped by team, with COALESCE. web (job 4) has no runs, so its total is 0 and it still appears, as the sample shows.
- busy_jobs: Table.SelectRows [runs] >= 3 is WHERE runs >= 3. Jobs 1 (4 runs) and 2 (3 runs) pass, as the sample shows.

```sql
WITH jobs_step AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(t.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
    ON j.job_id = c.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) t
    ON j.job_id = t.job_id
)
SELECT team, COALESCE(SUM(total), 0) AS team_total
FROM jobs_step
GROUP BY team
```

```sql
WITH jobs_step AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(t.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
    ON j.job_id = c.job_id
  LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs GROUP BY job_id) t
    ON j.job_id = t.job_id
)
SELECT job_id, job_name, runs
FROM jobs_step
WHERE runs >= 3
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, at_least, count_rows, derived, equals, fill_null, statement, sum_of
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

runs_per_job = derived("runs_per_job", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "runs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
total_per_job = derived("total_per_job", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
jobs_step = derived("jobs_step", statement(
    SELECT(
        jobs.job_id, jobs.job_name, jobs.team,
        AS(fill_null(runs_per_job.runs, 0), "runs"),
        AS(fill_null(total_per_job.total, 0), "total"),
    ),
    FROM(jobs),
    LEFT_JOIN(runs_per_job, ON=equals(runs_per_job.job_id, jobs.job_id)),
    LEFT_JOIN(total_per_job, ON=equals(total_per_job.job_id, jobs.job_id)),
))

by_team = statement(
    SELECT(jobs_step.team, AS(fill_null(sum_of(jobs_step.total), 0), "team_total")),
    FROM(jobs_step),
    GROUP_BY(jobs_step.team),
)

busy_jobs = statement(
    SELECT(jobs_step.job_id, jobs_step.job_name, jobs_step.runs),
    FROM(jobs_step),
    WHERE(at_least(jobs_step.runs, 3)),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` in the Hive (ops in the Python stands for it). Run `project.convert` on the Hive; its checked code wins where the two differ.
