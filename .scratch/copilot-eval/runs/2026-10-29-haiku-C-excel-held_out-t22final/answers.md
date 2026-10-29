date: 2026-10-29
arm: C
model: haiku
files: 5df4678

## X21

**Map**
- Sources: region_budgets (typed job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin).
- Parameters and Keys: none. No value is typed over a formula, so no Keys row is needed.
- Typed over: none. Marks: none. Refusals: none. Left alone: none.
- To fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets
```

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

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X22

**Map**
- Sources: jobs (typed job_id, job_name, team).
- Steps: none.
- Finals: jobs (job_id, job_name, team, is_finance, ratio).
- Parameters and Keys: none.
- Typed over: none. Marks: none.
- Refusals: none. Left alone: none.
- IFERROR in ratio is COALESCE, so job 2 (divide by zero) gives 0.
- To fill in: `<database>`.

```sql
SELECT job_id, job_name, team,
  IF(team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(job_id / (job_id - 2), 0) AS ratio
FROM <database>.jobs
```

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

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X23

**Map**
- Sources: job_runs (typed run_id, status, avg_retry_secs).
- Steps: none.
- Finals: job_runs (run_id, status, avg_retry_secs, label, risky).
- Parameters and Keys: none.
- Typed over: none. Every formula row matches.
- Marks: blank. Run 98 has a blank status and a blank avg_retry_secs. Both formulas read them, so status is wrapped as COALESCE(status, '') and avg_retry_secs as COALESCE(avg_retry_secs, 0). SWITCH and OR are not -IF(S) forms, so the blanks are wrapped.
- Refusals: none. Left alone: none.
- To fill in: `<database>`.

```sql
SELECT run_id, status, avg_retry_secs,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label,
  COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5 AS risky
FROM <database>.job_runs
```

```python
from sqlglot_composer import AS, FROM, SELECT, any_of, equals, fill_null, first_match, more_than, statement
from references.<database>__job_runs import job_runs

status = fill_null(job_runs.status, "")  # a blank status reads as ''
s = statement(
    SELECT(job_runs.run_id, job_runs.status, job_runs.avg_retry_secs,
           AS(first_match([(equals(status, "SUCCESS"), "ok"), (equals(status, "FAILED"), "bad")],
                          otherwise="other"), "label"),
           AS(any_of(equals(status, "FAILED"),
                     more_than(fill_null(job_runs.avg_retry_secs, 0), 5)), "risky")),
    FROM(job_runs),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X24

**Map**
- Sources: team_notes (typed team, note, written_on).
- Steps: none.
- Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars).
- Parameters and Keys: none.
- Typed over: none. Marks: none, since no cell is blank.
- Refusals: none. Left alone: none.
- first_word: LEFT(note, FIND(" ", note) - 1) as SUBSTR(note, 1, INSTR(note, ' ') - 1).
- To fill in: `<database>`.

```sql
SELECT team, note, written_on,
  SUBSTR(note, 1, INSTR(note, ' ') - 1) AS first_word,
  UPPER(team) AS shout,
  MONTH(written_on) AS month,
  ROUND(LENGTH(note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__team_notes import team_notes

s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on),
    FROM(team_notes),
)
# first_word, shout, month and tens_of_chars use LEFT, FIND, UPPER, MONTH, ROUND and LEN.
# Those are Hive functions, not in files 03 to 05. Load file 10 in a new chat to add them.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X25

**Map**
- Sources: Costs (typed Job, Cost (cents), Region, Day Key); Budgets (typed Job, Budget, Region).
- Steps: none.
- Finals: Costs (Job, <cost_cents>, Region, <day_key>, Day); Budgets (Job, Budget, Region, Dollars).
- Parameters and Keys: none.
- Typed over: none.
- Marks: Day Key is a date held as text (20260911), so Day is built with CONCAT and SUBSTR. Cost (cents) is blank in row 29, but no formula reads it, so it stays NULL with no wrap.
- Refusals: none. Left alone: none.
- To fill in: `<database>`, `<cost_cents>`, `<day_key>`.

```sql
SELECT Job, <cost_cents>, Region, <day_key>,
  CONCAT(SUBSTR(<day_key>, 1, 4), '-', SUBSTR(<day_key>, 5, 2), '-', SUBSTR(<day_key>, 7, 2)) AS Day
FROM <database>.Costs;

SELECT Job, Budget, Region,
  Budget / 100 AS Dollars
FROM <database>.Budgets;
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__Costs import Costs
from references.<database>__Budgets import Budgets

costs = statement(
    SELECT(Costs.Job, Costs.<cost_cents>, Costs.Region, Costs.<day_key>),
    FROM(Costs),
)  # Day needs CONCAT and SUBSTR from file 10, to load in a new chat.

budgets = statement(
    SELECT(Budgets.Job, Budgets.Budget, Budgets.Region,
           AS(Budgets.Budget / 100, "Dollars")),
    FROM(Budgets),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X26

**Map**
- Sources: run_alerts (typed alert_id, run_id, severity); job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none. job_runs has no formulas.
- Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins).
- Parameters and Keys: none.
- Typed over: none.
- Marks: job_runs has a blank status in run 98. The VLOOKUP reads status, so it is wrapped as COALESCE(status, ''). Run 98 is not in run_alerts, so the output is unchanged.
- Refusals: none. Left alone: none.
- XLOOKUP and VLOOKUP (exact) become one LEFT JOIN on run_id. AVERAGEIFS is AVG over job_runs grouped by job_id, joined in, with no COALESCE, so it stays NULL where nothing matches.
- To fill in: `<database>`.

```sql
SELECT ra.alert_id, ra.run_id, ra.severity,
  jr.job_id,
  COALESCE(jr.status, '') AS status,
  a.avg_mins
FROM <database>.run_alerts ra
LEFT JOIN <database>.job_runs jr ON ra.run_id = jr.run_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) a ON a.job_id = jr.job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, derived, equals, fill_null, statement
from references.<database>__run_alerts import run_alerts
from references.<database>__job_runs import job_runs

avg_by_job = derived("avg_by_job", statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs),
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity,
           job_runs.job_id,
           AS(fill_null(job_runs.status, ""), "status"),
           avg_by_job.avg_mins),
    FROM(run_alerts),
    LEFT_JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
    LEFT_JOIN(avg_by_job, ON=equals(avg_by_job.job_id, job_runs.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X27

**Map**
- Sources: jobs (typed job_id, job_name, team, region).
- Steps: none.
- Summary: by_team, typed team only. It is a GROUP BY team over jobs.
- Finals: by_team (team, jobs_in_team, last_job_id, last_job_name).
- Parameters and Keys: none.
- Typed over: none. Marks: none.
- Refusals: none. Left alone: none.
- INDEX(MATCH) on last_job_id becomes a LEFT JOIN of jobs on last_job_id, then job_name.
- To fill in: `<database>`.

```sql
SELECT g.team, g.jobs_in_team, g.last_job_id,
  j.job_name AS last_job_name
FROM (
  SELECT team,
    COALESCE(COUNT(*), 0) AS jobs_in_team,
    COALESCE(MAX(job_id), 0) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
) g
LEFT JOIN <database>.jobs j ON g.last_job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived, equals, fill_null, max_of, statement
from references.<database>__jobs import jobs

by_team = derived("by_team", statement(
    SELECT(jobs.team,
           AS(fill_null(count_rows(), 0), "jobs_in_team"),
           AS(fill_null(max_of(jobs.job_id), 0), "last_job_id")),
    FROM(jobs),
    GROUP_BY(jobs.team),
))
named = AS(jobs, "named")
s = statement(
    SELECT(by_team.team, by_team.jobs_in_team, by_team.last_job_id,
           AS(named.job_name, "last_job_name")),
    FROM(by_team),
    LEFT_JOIN(named, ON=equals(named.job_id, by_team.last_job_id)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X28

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed job_id, job_name).
- Steps: none.
- Finals: jobs (job_id, job_name, ok_mins).
- Parameters: none. Keys: jobs | job_id.
- Typed over: ok_mins in row 4 (job_id 3, report_build) is 99, matched on Keys column job_id.
- Marks: none. SUMIFS is an -IFS form, so the blank status in run 98 is skipped, not wrapped.
- Refusals: none. Left alone: none.
- SUMIFS over another Table becomes a LEFT JOIN to a SUM grouped by job_id where status is SUCCESS, with COALESCE to 0.
- To fill in: `<database>`.

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
) s ON s.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals, fill_null, first_match, statement, sum_of
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

ok_by_job = derived("ok_by_job", statement(
    SELECT(job_runs.job_id,
           AS(sum_of(job_runs.duration_mins, where=equals(job_runs.status, "SUCCESS")), "total")),
    FROM(job_runs),
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(first_match([(equals(jobs.job_id, 3), 99)],
                          otherwise=fill_null(ok_by_job.total, 0)), "ok_mins")),
    FROM(jobs),
    LEFT_JOIN(ok_by_job, ON=equals(ok_by_job.job_id, jobs.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X29

**Map**
- Sources: region_budgets (typed job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer).
- Parameters: cents_per_dollar is 100. The XLOOKUP on it is replaced by its value, 100, so there is no Parameters reference left.
- Keys: none. The Keys row is blank, so the typed-over row is matched on every typed column of the row: job_id, budget_cents and region. There is no Keys row for region_budgets.
- Typed over: in_dollars in row 4 (job 3, 350 cents, us) is 5.
- Marks: none.
- Refusals: pointer, which is INDIRECT, so it is NULL AS pointer.
- Left alone: none.
- To fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  CASE WHEN job_id = 3 AND budget_cents = 350 AND region = 'us' THEN 5
    ELSE budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets
```

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, equals, first_match, statement
from references.<database>__region_budgets import region_budgets

s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(first_match([(all_of(equals(region_budgets.job_id, 3),
                                   equals(region_budgets.budget_cents, 350),
                                   equals(region_budgets.region, "us")), 5)],
                          otherwise=region_budgets.budget_cents / 100), "in_dollars")),
    FROM(region_budgets),
)
# pointer is refused (INDIRECT), so it is NULL in the Hive and left out here.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X30

**Map**
- Sources: scheduler_runs (typed run_id, job_id, dt).
- Steps: none.
- Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter).
- Parameters and Keys: none.
- Typed over: none. Marks: none.
- Refusals: prev_run, which is OFFSET and hangs on the order of the rows, so NULL AS prev_run. jitter, which is RANDBETWEEN, so NULL AS jitter.
- Left alone: the bar chart on sheet "Summary", and the PivotTable on sheet "Pivot".
- day is RIGHT(dt, 2), written as SUBSTR(dt, -2).
- To fill in: `<database>`.

```sql
SELECT run_id, job_id, dt,
  SUBSTR(dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__scheduler_runs import scheduler_runs

s = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs),
)
# day needs RIGHT from file 10, to load in a new chat.
# prev_run (OFFSET) and jitter (RANDBETWEEN) are refused, so they are NULL in the Hive.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X31

**Map**
- Sources: jobs (typed job_id, team).
- Steps: none.
- Finals: jobs (job_id, team, bump, tag, scaled, boosted).
- Parameters and Keys: none.
- Typed over: none. Marks: boost is a defined name for Summary!B2, which is 10. It is used as 10 here, and it should move into Parameters.
- Refusals:
  - bump is a formula reading its own column (circular), so NULL AS bump.
  - tag uses the defined name TAG, which holds a LAMBDA, so NULL AS tag.
  - scaled reads the cell Summary!D4 (outside a Table, not a defined name), so NULL AS scaled.
- Left alone: the Summary sheet, with cells B2 and D4, and defined names boost and TAG.
- To fill in: `<database>`.

```sql
SELECT job_id, team,
  NULL AS bump,
  NULL AS tag,
  NULL AS scaled,
  job_id * 10 AS boosted
FROM <database>.jobs
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.team,
           AS(jobs.job_id * 10, "boosted")),  # boost is Summary!B2, 10: move it into Parameters
    FROM(jobs),
)
# bump, tag and scaled are refused, so they are NULL in the Hive and left out here.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X32

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed job_id, job_name, team, region).
- Steps: job_runs. Its formula job_name is read by by_name's COUNTIFS, so it is a CTE, job_runs_step.
- Finals: by_name (job_name, runs). It is a summary, a GROUP BY job_name over job_runs_step.
- Parameters and Keys: none.
- Typed over: none. Marks: VLOOKUP with TRUE is approximate. It is converted as an exact LEFT JOIN on job_id, and this is said here. Blank status and avg_retry_secs in run 98 are not read by a formula, so no wrap.
- Refusals: none. Left alone: none.
- To fill in: `<database>`.

```sql
WITH job_runs_step AS (
  SELECT jr.run_id, jr.job_id, jr.status, jr.duration_mins, jr.avg_retry_secs, jr.dt, j.job_name
  FROM <database>.job_runs jr
  LEFT JOIN <database>.jobs j ON jr.job_id = j.job_id
)
SELECT job_name, COALESCE(COUNT(*), 0) AS runs
FROM job_runs_step
GROUP BY job_name
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived, equals, fill_null, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

job_runs_step = derived("job_runs_step", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt, jobs.job_name),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))
s = statement(
    SELECT(job_runs_step.job_name, AS(fill_null(count_rows(), 0), "runs")),
    FROM(job_runs_step),
    GROUP_BY(job_runs_step.job_name),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X33

**Map**
- Sources: the Power Query reads Sql.Database, server dwh01, schema ops, item job_runs. It is a non-workbook source, so the table it names is used: `<database>.job_runs`. Check that the Hive database is ops and that the server is dwh01.
- Steps: none.
- Finals: slow_runs (run_id, duration_mins, over_by), loaded by its query.
- Parameters and Keys: none.
- Typed over: none. Marks: M's `<>` keeps a null and Hive's does not, so status <> 'TEST' becomes (status <> 'TEST' OR status IS NULL). The over_by column is duration_mins - 20.
- Refusals: none. Left alone: none.
- To fill in: `<database>`.

```sql
SELECT run_id, duration_mins, duration_mins - 20 AS over_by
FROM <database>.job_runs
WHERE duration_mins >= 20 AND (status <> 'TEST' OR status IS NULL)
```

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, any_of, at_least, is_null, not_equals, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins - 20, "over_by")),
    FROM(job_runs),
    WHERE(at_least(job_runs.duration_mins, 20),
          any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X34

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed job_id, job_name, team, region).
- Steps: runs_with_team. It is connection-only, but team_totals reads it, so it is kept as a CTE, not left out. It is a LEFT JOIN of job_runs to jobs, expanded to team.
- Finals: team_totals (team, total_mins, longest), loaded by its query.
- Parameters and Keys: none.
- Typed over: none. Marks: none.
- Refusals: none. Left alone: none.
- To fill in: `<database>`.

```sql
WITH runs_with_team AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT team,
  SUM(duration_mins) AS total_mins,
  MAX(duration_mins) AS longest
FROM runs_with_team
GROUP BY team
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals, max_of, statement, sum_of
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

runs_with_team = derived("runs_with_team", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt, jobs.team),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))
s = statement(
    SELECT(runs_with_team.team,
           AS(sum_of(runs_with_team.duration_mins), "total_mins"),
           AS(max_of(runs_with_team.duration_mins), "longest")),
    FROM(runs_with_team),
    GROUP_BY(runs_with_team.team),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X35

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); scheduler_runs (typed run_id, job_id, dt).
- Steps: Runs and Scheduled, as CTEs, stacked as Both_runs.
- Finals: recent (run_id, dt), loaded by its query.
- Parameters and Keys: none.
- Typed over: none.
- Marks: Table.Sort then FirstN 4 becomes ORDER BY run_id DESC LIMIT 4.
- Refusals: the connection-only query rates reads Web.Contents, so it is left out and named here.
- Left alone: none.
- To fill in: `<database>`.

```sql
WITH runs AS (
  SELECT run_id, dt FROM <database>.job_runs
),
scheduled AS (
  SELECT run_id, dt FROM <database>.scheduler_runs
),
both_runs AS (
  SELECT run_id, dt FROM runs
  UNION ALL
  SELECT run_id, dt FROM scheduled
)
SELECT run_id, dt
FROM both_runs
ORDER BY run_id DESC
LIMIT 4
```

```python
from sqlglot_composer import AS, FROM, LIMIT, ORDER_BY, SELECT, UNION_ALL, derived, descending, statement
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

both_runs = derived("both_runs", UNION_ALL(
    statement(SELECT(job_runs.run_id, job_runs.dt),
              FROM(job_runs, reads_all_partitions=True)),  # a workbook's query reads every row
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt),
              FROM(scheduler_runs, reads_all_partitions=True)),  # a workbook's query reads every row
))
s = statement(
    SELECT(both_runs.run_id, both_runs.dt),
    FROM(both_runs),
    ORDER_BY(descending(both_runs.run_id)),
    LIMIT(4),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X36

**Map**
- Sources: run_alerts (typed alert_id, run_id, severity, dt).
- Steps: none.
- Finals: job_runs (run_id, status, alerts). It is a final, not a summary, because status is typed too. Also severity_by_day (dt, high, low), loaded by its Power Query.
- Parameters and Keys: none.
- Typed over: none.
- Marks: the pivot's columns are fixed to high and low, from the sample. Each is a SUM of 1 where severity matches, so the value is NULL where there is none, as M leaves it. Each COUNTIFS is a COUNT with COALESCE to 0.
- Refusals: none. Left alone: none.
- To fill in: `<database>`.

```sql
SELECT jr.run_id, jr.status,
  COALESCE(a.alerts, 0) AS alerts
FROM <database>.job_runs jr
LEFT JOIN (
  SELECT run_id, COUNT(*) AS alerts
  FROM <database>.run_alerts
  GROUP BY run_id
) a ON a.run_id = jr.run_id;

SELECT dt,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
GROUP BY dt
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived, equals, fill_null, statement
from references.<database>__job_runs import job_runs
from references.<database>__run_alerts import run_alerts

alerts_by_run = derived("alerts_by_run", statement(
    SELECT(run_alerts.run_id, AS(count_rows(), "alerts")),
    FROM(run_alerts),
    GROUP_BY(run_alerts.run_id),
))
s = statement(
    SELECT(job_runs.run_id, job_runs.status,
           AS(fill_null(alerts_by_run.alerts, 0), "alerts")),
    FROM(job_runs),
    LEFT_JOIN(alerts_by_run, ON=equals(alerts_by_run.run_id, job_runs.run_id)),
)
severity_by_day = statement(
    SELECT(run_alerts.dt,
           AS(count_rows(where=equals(run_alerts.severity, "high")), "high"),
           AS(count_rows(where=equals(run_alerts.severity, "low")), "low")),
    FROM(run_alerts),
    GROUP_BY(run_alerts.dt),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X37

**Map**
- Sources: Owners (typed Job No, Team Name, Owner, Day).
- Steps: none.
- Finals: Owners (Job No, Team Name, Owner, Day, Is Ana).
- Parameters and Keys: none.
- Typed over: none. Every Is Ana row is the formula.
- Marks: blank. Web rows have a blank Owner, which the formula reads. IF is not an -IF(S) form, so Owner is wrapped as COALESCE(Owner, '').
- Refusals: none. Left alone: none.
- To fill in: `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

```sql
SELECT <job_no>, <team_name>, Owner, Day,
  IF(COALESCE(Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners
```

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.<database>__Owners import Owners

s = statement(
    SELECT(Owners.<job_no>, Owners.<team_name>, Owners.Owner, Owners.Day,
           AS(if_else(equals(fill_null(Owners.Owner, ""), "ana"), 1, 0), "<is_ana>")),
    FROM(Owners),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X38

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs); jobs (typed job_id, job_name, team, region).
- Steps: with_region. The region formula, from XLOOKUP on jobs, is read by region_mins within job_runs, so it is a CTE.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost).
- Parameters: none. Keys: job_runs | run_id.
- Typed over: retry_cost in row 8 (run_id 102) is 1, matched on run_id.
- Marks: blank. Run 98 has a blank avg_retry_secs, which retry_cost reads, so it is wrapped as COALESCE(avg_retry_secs, 0).
- Refusals: none. Left alone: none.
- SUMIFS over its own Table becomes SUM over PARTITION BY region, with COALESCE to 0.
- To fill in: `<database>`.

```sql
WITH with_region AS (
  SELECT jr.run_id, jr.job_id, jr.status, jr.duration_mins, jr.avg_retry_secs, j.region
  FROM <database>.job_runs jr
  LEFT JOIN <database>.jobs j ON jr.job_id = j.job_id
)
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, region,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY region), 0) AS region_mins,
  CASE WHEN run_id = 102 THEN 1
    ELSE (COALESCE(avg_retry_secs, 0) + duration_mins) * 2 END AS retry_cost
FROM with_region
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, derived, equals, fill_null, first_match, statement, sum_of, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

with_region = derived("with_region", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, jobs.region),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))
by_region = window(PARTITION_BY=with_region.region)
s = statement(
    SELECT(with_region.run_id, with_region.job_id, with_region.status,
           with_region.duration_mins, with_region.avg_retry_secs, with_region.region,
           AS(fill_null(sum_of(with_region.duration_mins, over=by_region), 0), "region_mins"),
           AS(first_match([(equals(with_region.run_id, 102), 1)],
                          otherwise=(fill_null(with_region.avg_retry_secs, 0)
                                     + with_region.duration_mins) * 2), "retry_cost")),
    FROM(with_region),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X39

**Map**
- Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed job_id, job_name, team, region).
- Steps: ok, the SUCCESS rows of job_runs, as a CTE. Also with_name, the join to jobs for job_name, as a CTE.
- Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise), loaded by its query.
- Parameters and Keys: none.
- Typed over: none. Marks: none.
- Refusals: noise is RAND(), so NULL AS noise.
- Left alone: none.
- share is duration_mins divided by SUMIFS over the Table's own job_id, a window with COALESCE to 0.
- To fill in: `<database>`.

```sql
WITH ok AS (
  SELECT r.run_id, r.job_id, r.duration_mins
  FROM <database>.job_runs r
  WHERE r.status = 'SUCCESS'
),
with_name AS (
  SELECT ok.run_id, ok.job_id, ok.duration_mins, j.job_name
  FROM ok
  LEFT JOIN <database>.jobs j ON ok.job_id = j.job_id
)
SELECT run_id, job_id, duration_mins, job_name,
  duration_mins / COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0) AS share,
  NULL AS noise
FROM with_name
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, WHERE, derived, equals, fill_null, statement, sum_of, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

ok = derived("ok", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(equals(job_runs.status, "SUCCESS")),
))
with_name = derived("with_name", statement(
    SELECT(ok.run_id, ok.job_id, ok.duration_mins, jobs.job_name),
    FROM(ok),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, ok.job_id)),
))
by_job = window(PARTITION_BY=with_name.job_id)
s = statement(
    SELECT(with_name.run_id, with_name.job_id, with_name.duration_mins, with_name.job_name,
           AS(with_name.duration_mins / fill_null(sum_of(with_name.duration_mins, over=by_job), 0),
              "share")),
    FROM(with_name),
)
# noise is RAND(), refused, so it is NULL in the Hive and left out here.
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X40

**Map**
- Sources: Runs (typed Run, Job, Mins); jobs (typed job_id, job_name, team, region).
- Steps: Runs. Its formulas Team and Cost are read by Teams and run_alerts, so it is a CTE, runs_step, in each of their queries.
- Finals: Teams (Team, <total_cost>), a summary that is a GROUP BY Team over runs_step; run_alerts (alert_id, run_id, severity, dt, <run_mins>).
- Parameters: rate is 2, so Cost is Mins * 2. Keys: none.
- Typed over: none. Marks: none.
- Refusals: none. Left alone: the PivotTable on sheet "Pivot" from Table Runs.
- To fill in: `<database>`, `<total_cost>`, `<run_mins>`.

```sql
WITH runs_step AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT Team, COALESCE(SUM(Cost), 0) AS <total_cost>
FROM runs_step
GROUP BY Team;

WITH runs_step AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT ra.alert_id, ra.run_id, ra.severity, ra.dt,
  rs.Mins AS <run_mins>
FROM <database>.run_alerts ra
LEFT JOIN runs_step rs ON ra.run_id = rs.Run
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals, fill_null, statement, sum_of
from references.<database>__Runs import Runs
from references.<database>__jobs import jobs
from references.<database>__run_alerts import run_alerts

runs_step = derived("runs_step", statement(
    SELECT(Runs.Run, Runs.Job, Runs.Mins,
           AS(jobs.team, "Team"),
           AS(Runs.Mins * 2, "Cost")),  # rate is 2 in Parameters
    FROM(Runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, Runs.Job)),
))
teams = statement(
    SELECT(runs_step.Team,
           AS(fill_null(sum_of(runs_step.Cost), 0), "<total_cost>")),
    FROM(runs_step),
    GROUP_BY(runs_step.Team),
)
alerts = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(runs_step.Mins, "<run_mins>")),
    FROM(run_alerts),
    LEFT_JOIN(runs_step, ON=equals(runs_step.Run, run_alerts.run_id)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X46

**Map**
- Sources: job_runs, jobs (each has typed columns).
- Steps: none.
- Finals: jobs (job_id, job_name, team, shortest, runs, busiest). job_runs has no formula of its own, so it is a source only.
- Parameters and Keys: empty, none.
- Left alone: the Steps sheet, which holds no Table.

```sql
SELECT j.job_id, j.job_name, j.team,
  COALESCE(s.shortest, 0) AS shortest,
  COALESCE(c.runs, 0) AS runs,
  RANK() OVER (ORDER BY COALESCE(c.runs, 0) DESC) AS busiest
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, MIN(duration_mins) AS shortest
  FROM <database>.job_runs
  GROUP BY job_id
) s ON j.job_id = s.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS runs
  FROM <database>.job_runs
  GROUP BY job_id
) c ON j.job_id = c.job_id
```

**Marks:** none. No blank sits in duration_mins or job_id.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X47

**Map**
- Sources: region_budgets.
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg).
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

**Marks:** none. No blanks. region_avg is left NULL where nothing matches, as AVERAGEIF is left NULL.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X48

**Map**
- Sources: job_runs, jobs, run_alerts.
- Steps: none.
- Finals: quiet_runs (run_id, job_id, status), from query quiet_runs; slow_regions (region, avg_mins, fastest), from query slow_regions.
- Connection-only queries: none.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

quiet_runs, a LeftAnti join, which is a LEFT JOIN with WHERE IS NULL:

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

slow_regions, an Inner join, a GROUP BY, and HAVING for the Table.SelectRows after the Table.Group:

```sql
SELECT j.region,
  AVG(r.duration_mins) AS avg_mins,
  MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

**Marks:** none. The blank status on run 98 is read by no formula, so it passes through as NULL.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X49

**Map**
- Sources: job_runs, jobs, run_alerts, scheduler_runs, job_owners.
- Steps: none.
- Finals: alert_status (alert_id, severity, status), from query alert_status; run_check (run_id, status, scheduled_run), from query run_check; teams (team), from query teams.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

alert_status, a RightOuter join, which is a LEFT JOIN with the two tables swapped:

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON a.run_id = r.run_id
```

run_check, a FullOuter join:

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

teams, Table.Combine then Table.Distinct, which is UNION:

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

**Marks:** none needed. No formula reads a blank. Run 100, which is only in scheduler_runs, keeps run_id NULL, as the full outer join gives.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X50

**Map**
- Sources: job_owners, jobs.
- Steps: none.
- Finals: owners (job_id, owner, job_name, newest_first), from query owners.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

**Marks:** the blank owner for job 4 stays NULL. No formula reads owner, so nothing is wrapped.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X59

**Map**
- Sources: job_runs, jobs, run_alerts.
- Steps: none.
- Finals: jobs (job_id, job_name, long_runs, failed_mins, not_test); run_alerts (alert_id, run_id, severity, dt, alerts_so_far).
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
SELECT j.job_id, j.job_name,
  COALESCE(lr.n, 0) AS long_runs,
  COALESCE(fr.total, 0) AS failed_mins,
  COALESCE(nt.n, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS n
  FROM <database>.job_runs
  WHERE duration_mins >= 20
  GROUP BY job_id
) lr ON j.job_id = lr.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total
  FROM <database>.job_runs
  WHERE LOWER(status) LIKE 'f%'
  GROUP BY job_id
) fr ON j.job_id = fr.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS n
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) nt ON j.job_id = nt.job_id
```

```sql
WITH run_alerts AS (
  SELECT alert_id, run_id, severity, dt,
    COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts
)
SELECT alert_id, run_id, severity, dt, alerts_so_far
FROM run_alerts
```

Note: the second block is the run_alerts Table written as a single query. It needs no CTE, so the same SELECT without the WITH works too.

**Marks:**
- The blank status on run 98 is not wrapped. It sits in -IFS forms, which skip a blank, and "<>TEST" counts it as Excel does, through `OR status IS NULL`.
- The "f*" wildcard becomes `LOWER(status) LIKE 'f%'`, as Excel ignores case.
- alerts_so_far is a running count, ties included, so no COALESCE.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X60

**Map**
- Sources: region_budgets.
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region); region_budgets (Total Row), a query of its own, one row, with the label left out.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

Total Row, SUBTOTAL(103) as COUNT, SUBTOTAL(101) as AVG:

```sql
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

**Marks:**
- The Total Row's "Total" label is left out.
- rank_in_region is the COUNTIFS "<" plus 1 form, so it is RANK with ASC inside each region.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X61

**Map**
- Sources: region_costs.
- Steps: none.
- Finals: by_region (region, total_cents, entries, priciest). It is a summary, since its only typed column is region, so it is a GROUP BY of region_costs.
- Total Row: its totals are SUM, SUM and MAX of MAXes, so it needs no query of its own. The GROUP BY ends WITH ROLLUP, and the NULL-region row it adds is the Total Row. Its "Total" label is left out.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
SELECT region,
  SUM(cost_cents) AS total_cents,
  COUNT(*) AS entries,
  MAX(cost_cents) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

**Marks:**
- The blank cost_cents on job 2, 20260924, stays NULL. SUM and MAX skip it, as the -IFS forms do, and COUNTIFS counts the row.
- dt is held as text, but no formula reads it, so no date conversion.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X62

**Map**
- Sources: team_notes.
- Steps: none.
- Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short).
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
SELECT team, note, written_on,
  CAST(NEXT_DAY(DATE_ADD(written_on, 7 * -1), 'MO') AS STRING) AS week_of,
  LAST_DAY(written_on) AS month_end,
  CAST(TRUNC(written_on, 'MM') AS STRING) AS month_of,
  FLOOR(MONTHS_BETWEEN(written_on, '2026-01-01')) AS months_in,
  DATE_SUB(written_on, 3) AS three_before,
  INITCAP(team) AS who,
  CONCAT_WS(': ', team, SUBSTR(note, 1, 5)) AS short
FROM <database>.team_notes
```

**Marks:**
- written_on is a date, so no text-date conversion.
- week_of and month_of are cast to STRING, as file 11's rules write a week's and a month's start.
- No blanks.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X63

**Map**
- Sources: scheduler_runs (read by a formula, so a source only), job_runs.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded).
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  r.avg_retry_secs IS NULL AS no_retry,
  FLOOR(r.duration_mins / 4) AS quarters,
  LEAST(r.duration_mins, 25) AS capped,
  VAR_SAMP(r.duration_mins) OVER () AS variance,
  SUM(r.duration_mins * r.job_id) OVER () AS weighted,
  COALESCE(s.job_id, -1) AS scheduled_job,
  CONCAT('run ', r.run_id) AS label,
  INSTR(LOWER(COALESCE(r.status, '')), LOWER('cess')) > 0 AS succeeded
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

**Marks:**
- Blank status on run 98: wrapped as COALESCE(status, ''), because the SEARCH inside ISNUMBER reads it outside an -IFS form. Say blank.
- Blank avg_retry_secs on run 98: ISBLANK becomes `IS NULL`, not wrapped.
- scheduled_job: XLOOKUP's fourth argument, -1, becomes COALESCE(s.job_id, -1). Run 99 has no scheduler row, so it gets -1.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X64

**Map**
- Sources: jobs, region_costs.
- Steps: none.
- Finals: picked_costs (job_id, cost_cents, region, size), from query picked_costs; costed_jobs (job_id, job_name, team, region), from query costed_jobs; costs_filled (job_id, cost_cents, dt, day), from query costs_filled.
- Connection-only queries: none.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

picked_costs:

```sql
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

costed_jobs, a LEFT SEMI JOIN on region_costs:

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

costs_filled:

```sql
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt,
  SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

**Marks:**
- The blank cost on job 2, 20260924, is wrapped as COALESCE(cost_cents, 0) in costs_filled, as Table.ReplaceValue does. Say blank. picked_costs drops it with IS NOT NULL.
- dt is held as text. Text.End reads its last two characters, so day is SUBSTR(dt, -2) with no date conversion.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X65

**Map**
- Sources: jobs, region_budgets, job_owners, scheduler_runs, job_runs.
- Steps: none.
- Finals: team_regions (team, region); budget_places (job_id, budget_cents, region, place); jobs_per_team (team, jobs); ran_as_scheduled (run_id, dt); run_measures (run_id, job_id, measure, amount).
- Connection-only queries: none.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

team_regions, a cross join. The final Table.Sort has no FirstN or index after it, so its order is dropped:

```sql
SELECT t.team, r.region
FROM (SELECT DISTINCT team FROM <database>.jobs) t
CROSS JOIN (SELECT DISTINCT region FROM <database>.jobs) r
```

budget_places, Table.Sort then Table.AddIndexColumn:

```sql
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

jobs_per_team:

```sql
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

ran_as_scheduled, an inner join on both keys, then Table.Distinct:

```sql
SELECT DISTINCT s.run_id, s.dt
FROM <database>.scheduler_runs s
JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.dt = r.dt
```

run_measures, Table.Unpivot as one SELECT per column, stacked with UNION ALL:

```sql
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

**Marks:**
- team_regions: the order was dropped, since a Hive table holds no order and the Table.Sort has nothing after it to keep it.
- The blank avg_retry_secs on run 98 gets no row in run_measures, as M drops a null there.
- jobs_per_team: COUNT(DISTINCT) counts job_id, which has no blank.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X66

**Map**
- Sources: job_runs.
- Steps: none.
- Finals: ok_runs (run_id, job_id, duration_mins, dt, running, share), from query ok_runs; ok_runs (Total Row), a query of its own, one row, with the label left out. ok_runs is not a summary, so the Total Row gets its own query.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

ok_runs:

```sql
WITH ok AS (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT run_id, job_id, duration_mins, dt,
  SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM ok
```

Total Row, SUBTOTAL(109) as SUM:

```sql
WITH ok AS (
  SELECT duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT SUM(duration_mins) AS duration_mins
FROM ok
```

**Marks:**
- The blank status on run 98 is dropped by `status IS NOT NULL`, as the query's <> null does.
- running is a running total by job, ties included, so it is RANGE UNBOUNDED PRECEDING to CURRENT ROW.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X69

**Map**
- Sources: region_costs, jobs, region_budgets. jobs and region_budgets are read by formulas, so they are sources only.
- Steps: none.
- Finals: region_costs (job_id, cost_cents, region, dt, job_name, budget, over_budget, running_cost).
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
WITH region_costs AS (
  SELECT job_id, cost_cents, region, dt,
    CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS dt_date
  FROM <database>.region_costs
)
SELECT c.job_id, c.cost_cents, c.region, c.dt,
  j.job_name,
  b.budget_cents AS budget,
  COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
  SUM(c.cost_cents) OVER (PARTITION BY c.job_id ORDER BY c.dt_date RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
FROM region_costs c
LEFT JOIN <database>.jobs j ON c.job_id = j.job_id
LEFT JOIN <database>.region_budgets b ON c.job_id = b.job_id
```

**Marks:**
- dt is held as text, so it is converted to a date string, dt_date, for the running order. Say the date is held as text.
- The blank cost on job 2, 20260924, is wrapped as COALESCE(cost_cents, 0) in over_budget, since that comparison is not an -IFS form. Say blank.
- In running_cost the blank is skipped, as SUMIFS skips it, so it is not wrapped.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X70

**Map**
- Sources: jobs, job_owners, job_runs.
- Steps:
  - staffed, a connection-only query that owner_load reads, so it is a CTE.
  - owner_load, a Table with a formula (avg_mins) that busiest_owner reads, so it is a step.
- Finals:
  - busiest_owner (owner, total_mins, runs), from query busiest_owner.
  - owner_load (Total Row), a query of its own, one row, with the label left out.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

busiest_owner:

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs,
    SUM(r.duration_mins) / COUNT(*) AS avg_mins
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs
FROM owner_load
ORDER BY runs DESC
LIMIT 1
```

owner_load (Total Row), SUBTOTAL(109) as SUM:

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs,
    SUM(r.duration_mins) / COUNT(*) AS avg_mins
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT SUM(runs) AS runs
FROM owner_load
```

**Marks:**
- Owner blank on job 4 is dropped by `owner IS NOT NULL`, as the query's <> null does.
- Table.RowCount becomes COUNT(*), and List.Sum becomes SUM.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X73

**Map**
- Sources: region_budgets, jobs.
- Steps: eu_budgets, a Table with a formula (dollars) that eu_count's query reads, so it is a CTE.
- Finals: eu_count (region, jobs, total_cents), from query eu_count.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name,
    b.budget_cents / 100 AS dollars
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT region, COUNT(*) AS jobs, SUM(budget_cents) AS total_cents
FROM eu_budgets
GROUP BY region
```

**Marks:** none. No blanks.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X74

**Map**
- Sources: run_alerts, job_runs.
- Steps: run_alerts, a Table with formulas (status, job_id, alerts_so_far) that by_status and late_alerts read, so it is a CTE in both.
- Finals:
  - by_status (status, alerts), a summary, since its only typed column is status, which COUNTIFS matches on. It is a GROUP BY of the run_alerts step.
  - late_alerts (alert_id, run_id, alerts_so_far), from query late_alerts.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

by_status:

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(r.status, '') AS status,
    r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT status, COUNT(*) AS alerts
FROM run_alerts
GROUP BY status
```

late_alerts:

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(r.status, '') AS status,
    r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM run_alerts
WHERE alerts_so_far > 5
```

**Marks:**
- The status lookup reads job_runs.status, which is blank on run 98. It is wrapped as COALESCE(status, ''). Say blank. No alert belongs to run 98, so the blank does not show in this sample.
- alerts_so_far is a running count, ties included. It is computed in the step, and late_alerts tests it in its WHERE.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X77

**Map**
- Sources: run_alerts.
- Steps: high_alerts, a Table with a formula (late_run) that high_per_day's query reads, so it is a CTE. late_run is in the step only and no final reads it.
- Finals: high_per_day (dt, alerts), from query high_per_day.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

```sql
WITH high_alerts AS (
  SELECT alert_id, run_id, dt, run_id > 100 AS late_run
  FROM <database>.run_alerts
  WHERE severity = 'high'
)
SELECT dt, COUNT(*) AS alerts
FROM high_alerts
GROUP BY dt
```

**Marks:** none. No blanks.
**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.

## X78

**Map**
- Sources: region_costs.
- Steps: known_costs, a Table with a formula (dollars) that cost_per_job's query reads, so it is a CTE.
- Finals:
  - cost_per_job (job_id, total_cents), from query cost_per_job.
  - known_costs (Total Row), a query of its own, since known_costs is not a summary. One row, the label left out.
- Parameters and Keys: empty, none. Steps sheet: no Table, left alone.

cost_per_job:

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt, cost_cents / 100 AS dollars
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT job_id, SUM(cost_cents) AS total_cents
FROM known_costs
GROUP BY job_id
```

known_costs (Total Row), SUBTOTAL(109) as SUM:

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt, cost_cents / 100 AS dollars
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT SUM(cost_cents) AS cost_cents
FROM known_costs
```

**Marks:**
- The blank cost on job 2, 20260924, is dropped by `cost_cents IS NOT NULL`, as the query's <> null does.
- The Total Row's SUM skips NULL.

**Refusals:** none.
**Fill in:** `<database>`. Take out of the workbook anything you don't want converted, then run `project.convert` on this Hive.
