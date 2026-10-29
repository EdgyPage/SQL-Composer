date: 2026-10-29
arm: C
model: haiku
files: fac0fd8

## X21

Map
- Sources: region_budgets (typed: job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin).
- Parameters and Keys: empty, none. No value is typed over a formula, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

```sql
SELECT r.job_id, r.budget_cents, r.region,
  r.budget_cents / 100 AS budget_dollars,
  r.budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets r
```

Marks: none. Refusals: none. Fill in: `<database>`.

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__region_budgets import region_budgets

s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(region_budgets.budget_cents / 100, "budget_dollars"),
           AS(region_budgets.budget_cents * 1.1, "with_margin")),
    FROM(region_budgets),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X22

Map
- Sources: jobs (typed: job_id, job_name, team).
- Steps: none.
- Finals: jobs (job_id, job_name, team, is_finance, ratio).
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

```sql
SELECT j.job_id, j.job_name, j.team,
  IF(j.team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(j.job_id / (j.job_id - 2), 0) AS ratio
FROM <database>.jobs j
```

Marks: IFERROR(a / b, 0) is written as COALESCE(a / b, 0), since Hive gives NULL for a divide by 0. Job 2 has job_id - 2 = 0, so its ratio is 0.
Refusals: none. Fill in: `<database>`.

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.<database>__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(if_else(equals(jobs.team, "finance"), "yes", "no"), "is_finance"),
           AS(fill_null(jobs.job_id / (jobs.job_id - 2), 0), "ratio")),
    FROM(jobs),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X23

Map
- Sources: job_runs (typed: run_id, status, avg_retry_secs).
- Steps: none.
- Finals: job_runs (run_id, status, avg_retry_secs, label, risky).
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

```sql
SELECT r.run_id, r.status, r.avg_retry_secs,
  CASE COALESCE(r.status, '') WHEN 'SUCCESS' THEN 'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label,
  (COALESCE(r.status, '') = 'FAILED' OR COALESCE(r.avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs r
```

Marks: run 98 has a blank status and a blank avg_retry_secs. Both are wrapped in COALESCE in label and risky, so run 98 gives label 'other' and risky FALSE, as Excel does.
Converted: `_xlfn.SWITCH` is written as CASE, with the `_xlfn.` prefix dropped.
Refusals: none. Fill in: `<database>`.

```python
from sqlglot_composer import AS, FROM, SELECT, any_of, equals, fill_null, more_than, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.status, job_runs.avg_retry_secs,
           # label is a three-way SWITCH, which is file 10's (not loaded here)
           AS(any_of(equals(fill_null(job_runs.status, ""), "FAILED"),
                     more_than(fill_null(job_runs.avg_retry_secs, 0), 5)), "risky")),
    FROM(job_runs),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. The label column's Python needs file 10, to load in a new chat.

## X24

Map
- Sources: team_notes (typed: team, note, written_on).
- Steps: none.
- Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars).
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

```sql
SELECT t.team, t.note, t.written_on,
  SUBSTR(t.note, 1, INSTR(t.note, ' ') - 1) AS first_word,
  UPPER(t.team) AS shout,
  MONTH(t.written_on) AS month,
  ROUND(LENGTH(t.note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes t
```

Marks: LEFT(x, n) with FIND(" ", x) - 1 becomes SUBSTR(x, 1, INSTR(x, ' ') - 1). LEN is LENGTH. Every note in the sample has a space, so FIND gives no error.
Refusals: none. Fill in: `<database>`.

Toolbox code: this workbook's text and date functions (LEFT, FIND, UPPER, MONTH, ROUND, LEN) are file 10's, Hive functions. This reply has no Python for X24, and load file 10 in a new chat to get it.

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X25

Map
- Sources: Costs (typed: Job, Cost (cents), Region, Day Key); Budgets (typed: Job, Budget, Region).
- Steps: none.
- Finals: Costs (Job, Cost (cents), Region, Day Key, Day); Budgets (Job, Budget, Region, Dollars).
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

Costs final:

```sql
SELECT c.Job, c.<cost_cents>, c.Region, c.<day_key>,
  CONCAT(SUBSTR(c.<day_key>, 1, 4), '-', SUBSTR(c.<day_key>, 5, 2), '-', SUBSTR(c.<day_key>, 7, 2)) AS Day
FROM <database>.Costs c
```

Budgets final:

```sql
SELECT b.Job, b.Budget, b.Region,
  b.Budget / 100 AS Dollars
FROM <database>.Budgets b
```

Marks: Day Key holds 20260911 as a date held as text. Day is DATE(LEFT, MID, RIGHT) in Excel, so it is converted as CONCAT(SUBSTR(...)) and gives text dates such as '2026-09-11'. Cost (cents) is blank in row 29, and no formula reads it, so it stays NULL and no COALESCE is written.
Refusals: none. Fill in: `<database>`, `<cost_cents>`, `<day_key>`.

Toolbox code, for Budgets:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__Budgets import Budgets

s = statement(
    SELECT(Budgets.Job, Budgets.Budget, Budgets.Region, AS(Budgets.Budget / 100, "Dollars")),
    FROM(Budgets),
)
```

The Costs Day column's CONCAT and SUBSTR are file 10's, to load in a new chat.

Next: take out of the workbook what you don't want converted, fill in the `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X26

Map
- Sources: run_alerts (typed: alert_id, run_id, severity); job_runs (typed: run_id, job_id, status, duration_mins, avg_retry_secs, dt). job_runs has no formula, so it is a source only.
- Steps: none.
- Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins).
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

```sql
SELECT a.alert_id, a.run_id, a.severity,
  j.job_id,
  j.status,
  m.avg_mins
FROM <database>.run_alerts a
LEFT JOIN <database>.job_runs j ON a.run_id = j.run_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) m ON m.job_id = j.job_id
```

Marks: XLOOKUP (job_id) and VLOOKUP exact (status, column 3 of job_runs) both become a LEFT JOIN on run_id. The two lookups share one key and run_id is unique in job_runs, so one join gives both. AVERAGEIFS over another Table is an AVG in a LEFT JOIN subquery grouped by job_id, with no COALESCE, as the rule says.
Refusals: none. Fill in: `<database>`.

Toolbox code:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, derived, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__run_alerts import run_alerts

j = AS(job_runs, "j")
per_job = derived("per_job", statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity,
           AS(j.job_id, "job_id"), AS(j.status, "status"), per_job.avg_mins),
    FROM(run_alerts),
    LEFT_JOIN(j, ON=equals(j.run_id, run_alerts.run_id), reads_all_partitions=True),
    LEFT_JOIN(per_job, ON=equals(per_job.job_id, j.job_id)),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X27

Map
- Sources: jobs (typed: job_id, job_name, team, region).
- Steps: none.
- Finals: by_team (team, jobs_in_team, last_job_id, last_job_name). by_team's only typed column is team, which COUNTIFS and MAXIFS match on, so it is a summary: a GROUP BY of jobs.
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

```sql
SELECT g.team, g.jobs_in_team, g.last_job_id, j.job_name AS last_job_name
FROM (
  SELECT team,
    COALESCE(COUNT(*), 0) AS jobs_in_team,
    COALESCE(MAX(job_id), 0) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
) g
LEFT JOIN <database>.jobs j ON g.last_job_id = j.job_id
```

Marks: COUNTIFS becomes COUNT(*), MAXIFS becomes MAX, each with COALESCE. INDEX(job_name, MATCH(last_job_id, job_id, 0)) becomes a LEFT JOIN on job_id, then job_name.
Refusals: none. Fill in: `<database>`.

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived, equals, max_of, statement
from references.<database>__jobs import jobs

j = AS(jobs, "j")
by_team = derived("by_team", statement(
    SELECT(jobs.team, AS(count_rows(), "jobs_in_team"), AS(max_of(jobs.job_id), "last_job_id")),
    FROM(jobs),
    GROUP_BY(jobs.team),
))
s = statement(
    SELECT(by_team.team, by_team.jobs_in_team, by_team.last_job_id, AS(j.job_name, "last_job_name")),
    FROM(by_team),
    LEFT_JOIN(j, ON=equals(j.job_id, by_team.last_job_id)),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X28

Map
- Sources: jobs (typed: job_id, job_name); job_runs (typed: run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: jobs (job_id, job_name, ok_mins).
- Parameters and Keys: Keys has a row for jobs, key job_id.
- Left alone: the Steps sheet (cells outside a Table).

```sql
SELECT j.job_id, j.job_name,
  CASE WHEN j.job_id = 3 THEN 99
    ELSE COALESCE(s.total, 0) END AS ok_mins
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
  GROUP BY job_id
) s ON j.job_id = s.job_id
```

Marks: the value typed over in row 4 (report_build, job_id 3) is converted as CASE WHEN job_id = 3 THEN 99, matching on the Keys column job_id. SUMIFS over another Table is a SUM in a LEFT JOIN subquery with COALESCE(.., 0). The blank status in run 98 is not wrapped, since SUMIFS skips a blank, and the criterion 'SUCCESS' does not match it.
Refusals: none. Fill in: `<database>`.

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, derived, equals, fill_null, first_match, statement, sum_of
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

ok = derived("ok", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(first_match([(equals(jobs.job_id, 3), 99)], otherwise=fill_null(ok.total, 0)), "ok_mins")),
    FROM(jobs),
    LEFT_JOIN(ok, ON=equals(ok.job_id, jobs.job_id)),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X29

Map
- Sources: region_budgets (typed: job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer).
- Parameters: the one value, cents_per_dollar = 100, is read as its value (100), as XLOOKUP reads it. Parameters is not a step.
- Keys: empty, so there is no Keys row for region_budgets.
- Left alone: the Steps sheet (cells outside a Table).

```sql
SELECT r.job_id, r.budget_cents, r.region,
  CASE WHEN r.job_id = 3 AND r.budget_cents = 350 AND r.region = 'us' THEN 5
    ELSE r.budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets r
```

Marks: the value typed over in row 4 (in_dollars = 5) is converted with no Keys row for this Table. So the match is on every typed column of that row: job_id = 3, budget_cents = 350 and region = 'us'. XLOOKUP("cents_per_dollar", ...) is read as 100, and the value should be moved into Parameters.
Refusals: pointer, `=INDIRECT("A"&ROW())`, is refused (INDIRECT, and ROW() which hangs on the order of rows), so it is NULL AS pointer in every row.
Fill in: `<database>`.

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, equals, first_match, statement
from references.<database>__region_budgets import region_budgets

r = AS(region_budgets, "r")
s = statement(
    SELECT(r.job_id, r.budget_cents, r.region,
           AS(first_match([(all_of(equals(r.job_id, 3), equals(r.budget_cents, 350), equals(r.region, "us")), 5)],
                          otherwise=r.budget_cents / 100), "in_dollars")),
    # pointer is refused (INDIRECT and ROW()), NULL in the Hive, so left out here
    FROM(r),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X30

Map
- Sources: scheduler_runs (typed: run_id, job_id, dt).
- Steps: none.
- Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter).
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the bar chart on sheet Summary, and the PivotTable on sheet Pivot (charts and PivotTables), and the Steps sheet (cells outside a Table).

```sql
SELECT s.run_id, s.job_id, s.dt,
  SUBSTR(s.dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs s
```

Marks: RIGHT(dt, 2) becomes SUBSTR(dt, -2).
Refusals: prev_run, `=OFFSET(...)`, is refused as OFFSET, so NULL AS prev_run. jitter, `=RANDBETWEEN(1,5)`, is refused as RAND and RANDBETWEEN, so NULL AS jitter.
Fill in: `<database>`.

Toolbox code:

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__scheduler_runs import scheduler_runs

s = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

The day column needs file 10's SUBSTR, to load in a new chat. prev_run and jitter are refused, so they are left out of the Python.

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X31

Map
- Sources: jobs (typed: job_id, team).
- Steps: none.
- Finals: jobs (job_id, team, bump, tag, scaled, boosted).
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: cells B2 and D4 on sheet Summary (cells outside a Table), and the Steps sheet.

```sql
SELECT j.job_id, j.team,
  NULL AS bump,
  NULL AS tag,
  NULL AS scaled,
  j.job_id * 10 AS boosted
FROM <database>.jobs j
```

Marks: the defined name boost is Summary!$B$2, a cell outside a Table, so boosted uses its value, 10. Move it into Parameters.
Refusals:
- bump, `=jobs[[#This Row],[bump]]*2`, reads its own column, so it is circular and NULL AS bump.
- tag, `=TAG(...)`, calls the defined name TAG, which holds a LAMBDA, so NULL AS tag.
- scaled, `=...*Summary!$D$4`, reads a cell outside a Table (Summary!D4) that is not a defined name, so NULL AS scaled.

Fill in: `<database>`.

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.team, AS(jobs.job_id * 10, "boosted")),
    FROM(jobs),
    # bump, tag and scaled are refused, NULL in the Hive, so left out here
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X32

Map
- Sources: job_runs (typed: run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed: job_id, job_name, team, region).
- Steps: runs_with_job, the job_runs Table with its job_name formula, read by by_name, so it is a CTE.
- Finals: by_name (job_name, runs). by_name's only typed column is job_name, which COUNTIFS matches on, so it is a summary: a GROUP BY of the job_runs step.
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

```sql
WITH runs_with_job AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT job_name, COALESCE(COUNT(*), 0) AS runs
FROM runs_with_job
GROUP BY job_name
```

Marks: VLOOKUP(job_id, jobs, 2, TRUE) is approximate, so it is converted exactly, as a LEFT JOIN on job_id = job_id. Job ids 1 to 4 all match exactly in the sample, so the result is the same. COUNTIFS becomes COUNT(*), with COALESCE.
Refusals: none. Fill in: `<database>`.

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

j = AS(jobs, "j")  # exact match, not VLOOKUP's approximate one
runs_with_job = derived("runs_with_job", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt, AS(j.job_name, "job_name")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(j, ON=equals(j.job_id, job_runs.job_id)),
))
s = statement(
    SELECT(runs_with_job.job_name, AS(count_rows(), "runs")),
    FROM(runs_with_job),
    GROUP_BY(runs_with_job.job_name),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X33

Map
- Sources: job_runs, read from the Sql.Database("dwh01", "ops") connection, schema ops, table job_runs (a non-workbook source).
- Steps: none.
- Finals: slow_runs (run_id, duration_mins, over_by), loaded by its Power Query.
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

```sql
SELECT j.run_id, j.duration_mins, j.duration_mins - 20 AS over_by
FROM <database>.job_runs j
WHERE j.duration_mins >= 20 AND (j.status <> 'TEST' OR j.status IS NULL)
```

Marks: Sql.Database is not a workbook source, so the query uses the table it names, job_runs in schema ops on server dwh01. Check that `<database>.job_runs` is that table. M's `<>` keeps a null status, so the filter is `(status <> 'TEST' OR status IS NULL)`.
Refusals: none. Fill in: `<database>`.

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, any_of, at_least, is_null, not_equals, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins - 20, "over_by")),
    FROM(job_runs, reads_all_partitions=True),  # the query reads every row, as its M does
    WHERE(at_least(job_runs.duration_mins, 20),
          any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and check that `<database>.job_runs` is ops.job_runs on dwh01. Then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X34

Map
- Sources: job_runs (typed: run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed: job_id, job_name, team, region).
- Steps: runs_with_team, the connection-only query read by team_totals, so it is a CTE.
- Finals: team_totals (team, total_mins, longest), loaded by its Power Query.
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

```sql
WITH runs_with_team AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT team, SUM(duration_mins) AS total_mins, MAX(duration_mins) AS longest
FROM runs_with_team
GROUP BY team
```

Marks: Table.NestedJoin LeftOuter becomes LEFT JOIN, then the expanded team column. List.Sum becomes SUM and List.Max becomes MAX.
Refusals: none. Fill in: `<database>`.

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals, max_of, statement, sum_of
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

j = AS(jobs, "j")
runs_with_team = derived("runs_with_team", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt, AS(j.team, "team")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(j, ON=equals(j.job_id, job_runs.job_id)),
))
s = statement(
    SELECT(runs_with_team.team, AS(sum_of(runs_with_team.duration_mins), "total_mins"),
           AS(max_of(runs_with_team.duration_mins), "longest")),
    FROM(runs_with_team),
    GROUP_BY(runs_with_team.team),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X35

Map
- Sources: job_runs (typed: run_id, job_id, status, duration_mins, avg_retry_secs, dt); scheduler_runs (typed: run_id, job_id, dt).
- Steps: none.
- Finals: recent (run_id, dt), loaded by its Power Query.
- Left out, and named: the connection-only query "rates". It reads Web.Contents("https://rates.example.com/today.json"), a web source, so it is refused and nothing reads it.
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

```sql
SELECT u.run_id, u.dt
FROM (
  SELECT run_id, dt FROM <database>.job_runs
  UNION ALL
  SELECT run_id, dt FROM <database>.scheduler_runs
) u
ORDER BY u.run_id DESC
LIMIT 4
```

Marks: Table.Combine becomes UNION ALL. Table.Sort descending then Table.FirstN 4 becomes ORDER BY run_id DESC, then LIMIT 4.
Refusals: the "rates" query, which reads a web source, is left out (see above). Fill in: `<database>`.

```python
from sqlglot_composer import AS, FROM, LIMIT, ORDER_BY, SELECT, UNION_ALL, derived, descending, statement
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

runs = statement(SELECT(job_runs.run_id, job_runs.dt), FROM(job_runs, reads_all_partitions=True))
sched = statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt), FROM(scheduler_runs, reads_all_partitions=True))
stacked = derived("stacked", UNION_ALL(runs, sched))
s = statement(
    SELECT(stacked.run_id, stacked.dt),
    FROM(stacked),
    ORDER_BY(descending(stacked.run_id)),
    LIMIT(4),
)
```

Next: take out of the workbook what you don't want converted, including the "rates" query, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X36

Map
- Sources: run_alerts (typed: alert_id, run_id, severity, dt); job_runs (typed: run_id, status).
- Steps: none.
- Finals: job_runs (run_id, status, alerts); severity_by_day (dt, high, low), loaded by its Power Query.
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

Final job_runs:

```sql
SELECT j.run_id, j.status, COALESCE(c.alerts, 0) AS alerts
FROM <database>.job_runs j
LEFT JOIN (
  SELECT run_id, COUNT(*) AS alerts
  FROM <database>.run_alerts
  GROUP BY run_id
) c ON j.run_id = c.run_id
```

Final severity_by_day, its Power Query:

```sql
WITH counted AS (
  SELECT a.dt, a.severity, 1 AS n
  FROM <database>.run_alerts a
)
SELECT c.dt,
  SUM(CASE WHEN c.severity = 'high' THEN c.n END) AS high,
  SUM(CASE WHEN c.severity = 'low' THEN c.n END) AS low
FROM counted c
GROUP BY c.dt
```

Marks: COUNTIFS over another Table becomes COUNT(*) in a LEFT JOIN subquery, with COALESCE(.., 0). Table.Pivot becomes one SUM(CASE WHEN severity = '...' THEN n END) column per severity value in the sample, THEN n to add up n as List.Sum does, NULL where none. The pivot's columns are now fixed at high and low.
Refusals: none. Fill in: `<database>`.

Toolbox code, for job_runs:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived, equals, fill_null, statement
from references.<database>__job_runs import job_runs
from references.<database>__run_alerts import run_alerts

per_run = derived("per_run", statement(
    SELECT(run_alerts.run_id, AS(count_rows(), "alerts")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(run_alerts.run_id),
))
s = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(fill_null(per_run.alerts, 0), "alerts")),
    FROM(job_runs),
    LEFT_JOIN(per_run, ON=equals(per_run.run_id, job_runs.run_id)),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. The pivot's Python is file 12's, and its Hive above is the checked one where they differ (count_rows gives 0 where a severity is absent, the Hive gives NULL).

## X37

Map
- Sources: Owners (typed: Job No, Team Name, Owner, Day).
- Steps: none.
- Finals: Owners (Job No, Team Name, Owner, Day, Is Ana).
- Parameters and Keys: none. No value is typed over, so no Keys row is needed.
- Left alone: the Steps sheet (cells outside a Table).

```sql
SELECT o.<job_no>, o.<team_name>, o.Owner, o.Day,
  IF(COALESCE(o.Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners o
```

Marks: the blank Owner in rows for job 4 (web) is wrapped as COALESCE(Owner, ''), and that is a blank. Plain IF, not an -IF(S) form, so the wrap applies; the result is 0 for those rows, as Excel gives.
Refusals: none. Fill in: `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.<database>__Owners import Owners

s = statement(
    SELECT(Owners.<job_no>, Owners.<team_name>, Owners.Owner, Owners.Day,
           AS(if_else(equals(fill_null(Owners.Owner, ""), "ana"), 1, 0), "<is_ana>")),
    FROM(Owners),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X38

Map
- Sources: job_runs (typed: run_id, job_id, status, duration_mins, avg_retry_secs); jobs (typed: job_id, job_name, team, region).
- Steps: runs_with_region, the job_runs Table with its region formula (XLOOKUP on jobs), read by its own region_mins, so it is a CTE.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost).
- Parameters: none. Keys: a row for job_runs, key run_id.
- Left alone: the Steps sheet (cells outside a Table).

```sql
WITH runs_with_region AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
    j.region
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT w.run_id, w.job_id, w.status, w.duration_mins, w.avg_retry_secs, w.region,
  COALESCE(SUM(w.duration_mins) OVER (PARTITION BY w.region), 0) AS region_mins,
  CASE WHEN w.run_id = 102 THEN 1
    ELSE (COALESCE(w.avg_retry_secs, 0) + w.duration_mins) * 2 END AS retry_cost
FROM runs_with_region w
```

Marks: the value typed over in run 102 (retry_cost = 1) is converted as CASE WHEN run_id = 102, matching the Keys column run_id. XLOOKUP becomes a LEFT JOIN on job_id, then region. SUMIFS over its own Table with the criterion region becomes SUM OVER (PARTITION BY region), with COALESCE. The blank avg_retry_secs in run 98 is wrapped in COALESCE in retry_cost, and that is a blank. The typed avg_retry_secs column itself stays NULL.
Refusals: none. Fill in: `<database>`.

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, derived, equals, first_match, fill_null, statement, sum_of, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

runs = derived("runs", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, AS(jobs.region, "region")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))
by_region = window(PARTITION_BY=runs.region)
s = statement(
    SELECT(runs.run_id, runs.job_id, runs.status, runs.duration_mins, runs.avg_retry_secs, runs.region,
           AS(sum_of(runs.duration_mins, over=by_region), "region_mins"),
           AS(first_match([(equals(runs.run_id, 102), 1)],
                          otherwise=(fill_null(runs.avg_retry_secs, 0) + runs.duration_mins) * 2), "retry_cost")),
    FROM(runs),
)
```

Next: take out of the workbook what you don't want converted, fill in the `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.
