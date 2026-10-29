date: 2026-10-29
arm: C
model: haiku
files: f80b90b

## X21

Map:
- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin).
- Parameters and Keys are empty, so they are none. No value is typed over a formula, so no Keys row is needed.
- Typed over: none. Marks: none. Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.job_id, r.budget_cents, r.region,
  r.budget_cents / 100 AS budget_dollars,
  r.budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets r
```

Toolbox code, by files 03 to 05:

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

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs from the Python above.

## X22

Map:
- Sources: jobs (job_id, job_name, team).
- Steps: none.
- Finals: jobs (job_id, job_name, team, is_finance, ratio).
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Typed over: none.
- Marks: IFERROR(job_id / (job_id - 2), 0) becomes COALESCE(job_id / (job_id - 2), 0), as a divide by 0 is NULL. The row with job_id 2 gives 0.
- Refusals: none.
- Left alone: the Steps sheet (cells outside a Table).
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team,
  IF(j.team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(j.job_id / (j.job_id - 2), 0) AS ratio
FROM <database>.jobs j
```

Toolbox code, by files 03 to 05:

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

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs from the Python above.

## X23

Map:
- Sources: job_runs (run_id, status, avg_retry_secs).
- Steps: none.
- Finals: job_runs (run_id, status, avg_retry_secs, label, risky).
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks, blank: row 98 has a blank status and a blank avg_retry_secs, and both are read by formulas. Inside the formulas they are wrapped as COALESCE(status, '') and COALESCE(avg_retry_secs, 0). The raw columns are kept as they are. The label for the blank status is 'other', as in Excel.
- Marks: _xlfn.SWITCH becomes a CASE with ELSE 'other'. The _xlfn. prefix is dropped.
- Refusals: none.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT j.run_id, j.status, j.avg_retry_secs,
  CASE COALESCE(j.status, '')
    WHEN 'SUCCESS' THEN 'ok'
    WHEN 'FAILED' THEN 'bad'
    ELSE 'other'
  END AS label,
  (COALESCE(j.status, '') = 'FAILED' OR COALESCE(j.avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs j
```

Toolbox code, by files 03 to 05. The label has three outcomes, which file 10 (labels) covers. Load file 10 in a new chat for it.

```python
from sqlglot_composer import AS, FROM, SELECT, any_of, equals, fill_null, more_than, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.status, job_runs.avg_retry_secs,
           AS(any_of(equals(fill_null(job_runs.status, ""), "FAILED"),
                     more_than(fill_null(job_runs.avg_retry_secs, 0), 5)), "risky")),
    FROM(job_runs),
)
```

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs from the Python above.

## X24

Map:
- Sources: team_notes (team, note, written_on).
- Steps: none.
- Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars).
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Typed over: none. Marks: none. Refusals: none.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT t.team, t.note, t.written_on,
  SUBSTR(t.note, 1, INSTR(t.note, ' ') - 1) AS first_word,
  UPPER(t.team) AS shout,
  MONTH(t.written_on) AS month,
  ROUND(LENGTH(t.note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes t
```

Toolbox code: the names in files 03 to 05 have no LEFT, FIND, UPPER, MONTH, ROUND or LENGTH. Load file 10 (Hive functions) in a new chat for this Toolbox code. The Hive above is the converted version.

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X25

Map:
- Sources: Costs (Job, Cost (cents), Region, Day Key); Budgets (Job, Budget, Region).
- Steps: none.
- Finals: Costs (Job, <cost_cents>, Region, <day_key>, Day); Budgets (Job, Budget, Region, Dollars).
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks: Day Key is a date held as text (20260911). Day is therefore CONCAT of the SUBSTR pieces, not DATE, and the date is held as text. A blank Cost (cents) in row 29 is not read by a formula, so it stays NULL.
- Refusals: none.
- Left alone: the Steps sheet.
- Fill in: `<database>`, `<cost_cents>` (header Cost (cents)), `<day_key>` (header Day Key).

```sql
SELECT c.Job, c.<cost_cents>, c.Region, c.<day_key>,
  CONCAT(SUBSTR(c.<day_key>, 1, 4), '-', SUBSTR(c.<day_key>, 5, 2), '-', SUBSTR(c.<day_key>, 7, 2)) AS Day
FROM <database>.Costs c
```

```sql
SELECT b.Job, b.Budget, b.Region,
  b.Budget / 100 AS Dollars
FROM <database>.Budgets b
```

Toolbox code, by files 03 to 05, for Budgets:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__budgets import budgets

s = statement(
    SELECT(budgets.Job, budgets.Budget, budgets.Region,
           AS(budgets.Budget / 100, "Dollars")),
    FROM(budgets),
)
```

The Costs Day needs file 10 (Hive functions, for SUBSTR and CONCAT on the text date). Load it in a new chat for that Toolbox code.

Next: take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X26

Map:
- Sources: run_alerts (alert_id, run_id, severity); job_runs (run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins).
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks: the XLOOKUP and the VLOOKUP both look up job_runs on run_id, so one LEFT JOIN gives job_id and status. The VLOOKUP is exact (FALSE). AVERAGEIFS over another Table is a LEFT JOIN to an AVG subquery, left NULL where nothing matches, with no COALESCE.
- Refusals: none.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT a.alert_id, a.run_id, a.severity,
  r.job_id,
  r.status,
  m.avg_mins
FROM <database>.run_alerts a
LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) m ON r.job_id = m.job_id
```

Toolbox code, by files 03 to 05:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, derived, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__run_alerts import run_alerts

all_runs = AS(job_runs, "all_runs")
avg_by_job = derived("avg_by_job", statement(
    SELECT(all_runs.job_id, AS(average_of(all_runs.duration_mins), "avg_mins")),
    FROM(all_runs),
    GROUP_BY(all_runs.job_id),
))
s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity,
           job_runs.job_id, job_runs.status, avg_by_job.avg_mins),
    FROM(run_alerts),
    LEFT_JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
    LEFT_JOIN(avg_by_job, ON=equals(avg_by_job.job_id, job_runs.job_id)),
)
```

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X27

Map:
- Sources: jobs (job_id, job_name, team, region).
- Steps: none.
- Summary: by_team has only team typed, which COUNTIFS and MAXIFS match on, so it is a summary: a GROUP BY team of jobs.
- Finals: by_team (team, jobs_in_team, last_job_id, last_job_name).
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks: COUNTIFS becomes COALESCE(COUNT(*), 0). MAXIFS becomes COALESCE(MAX(job_id), 0). INDEX/MATCH with MATCH's 0 is exact, so it becomes a LEFT JOIN of jobs on last_job_id, then job_name.
- Refusals: none.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT s.team, s.jobs_in_team, s.last_job_id, j.job_name AS last_job_name
FROM (
  SELECT team,
    COALESCE(COUNT(*), 0) AS jobs_in_team,
    COALESCE(MAX(job_id), 0) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
) s
LEFT JOIN <database>.jobs j ON s.last_job_id = j.job_id
```

Toolbox code, by files 03 to 05:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived, equals, fill_null, max_of, statement
from references.<database>__jobs import jobs

by_team = derived("by_team", statement(
    SELECT(jobs.team, AS(fill_null(count_rows(), 0), "jobs_in_team"),
           AS(fill_null(max_of(jobs.job_id), 0), "last_job_id")),
    FROM(jobs),
    GROUP_BY(jobs.team),
))
j = AS(jobs, "j")
s = statement(
    SELECT(by_team.team, by_team.jobs_in_team, by_team.last_job_id, j.job_name),
    FROM(by_team),
    LEFT_JOIN(j, ON=equals(j.job_id, by_team.last_job_id)),
)
```

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X28

Map:
- Sources: job_runs (job_id, status, duration_mins), read for these columns; jobs (job_id, job_name).
- Steps: none.
- Finals: jobs (job_id, job_name, ok_mins).
- Keys: the Keys sheet has a row, jobs | job_id, so the typed value matches on job_id.
- Typed over: ok_mins for job_id 3 is 99, not the SUMIFS. Converted as CASE WHEN job_id = 3 THEN 99.
- Marks: SUMIFS over another Table is a LEFT JOIN to a SUM subquery with COALESCE(total, 0), as Excel gives 0 where nothing matches. The blank status in job_runs row 98 is skipped by the status condition, as NULL is in WHERE, so it is not wrapped.
- Refusals: none.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

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

Toolbox code, by files 03 to 05:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, derived, equals, fill_null, first_match, statement, sum_of
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

ok_totals = derived("ok_totals", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs),
    WHERE(equals(job_runs.status, "SUCCESS")),
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(first_match([(equals(jobs.job_id, 3), 99)],
                          otherwise=fill_null(ok_totals.total, 0)), "ok_mins")),
    FROM(jobs),
    LEFT_JOIN(ok_totals, ON=equals(ok_totals.job_id, jobs.job_id)),
)
```

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X29

Map:
- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer).
- Parameters: the XLOOKUP("cents_per_dollar", ...) is replaced by its value, 100, so in_dollars is budget_cents / 100.
- Keys: the Keys sheet is empty, so there is no Keys row for region_budgets. The typed value is matched on every typed column of its row: job_id 3, budget_cents 350, region 'us'.
- Typed over: in_dollars for the job_id 3 row is 5, not the formula.
- Refusals: pointer = INDIRECT("A"&ROW()) is refused (INDIRECT and ROW()), so NULL AS pointer.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT r.job_id, r.budget_cents, r.region,
  CASE WHEN r.job_id = 3 AND r.budget_cents = 350 AND r.region = 'us' THEN 5
    ELSE r.budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets r
```

Toolbox code, by files 03 to 05 and 11:

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, equals, first_match, statement
from references.<database>__region_budgets import region_budgets

s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(first_match([(all_of(equals(region_budgets.job_id, 3),
                                   equals(region_budgets.budget_cents, 350),
                                   equals(region_budgets.region, "us")), 5)],
                          otherwise=region_budgets.budget_cents / 100), "in_dollars"),
           AS(None, "pointer")),  # refused: INDIRECT, NULL in the Hive
    FROM(region_budgets),
)
```

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X30

Map:
- Sources: scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter).
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks: RIGHT(dt, 2) becomes SUBSTR(dt, -2).
- Refusals: prev_run = OFFSET(...), the row before, is refused, so NULL AS prev_run. jitter = RANDBETWEEN(1,5) is refused, so NULL AS jitter.
- Left alone: the Summary sheet's bar chart; the Pivot sheet's PivotTable from scheduler_runs (rows job_id, Count of run_id); the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT s.run_id, s.job_id, s.dt,
  SUBSTR(s.dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs s
```

Toolbox code: the day column needs file 10 (RIGHT is a Hive function, not in files 03 to 05). The two refused columns have no Toolbox form. Load file 10 in a new chat for the day column.

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X31

Map:
- Sources: jobs (job_id, team).
- Steps: none.
- Finals: jobs (job_id, team, bump, tag, scaled, boosted).
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks: the defined name boost is Summary!$B$2, a cell outside a Table, so boosted uses its value, 10: job_id * 10. Move boost into Parameters.
- Refusals:
  - bump = bump * 2 reads its own column (circular), so NULL AS bump.
  - tag = TAG(team) calls the defined name TAG, which holds a LAMBDA, so NULL AS tag.
  - scaled = job_id * Summary!$D$4 reads a cell outside a Table (D4) that is not a defined name, so NULL AS scaled.
- Left alone: the cells of the Summary sheet (outside a Table, B2 and D4); the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.team,
  NULL AS bump,
  NULL AS tag,
  NULL AS scaled,
  j.job_id * 10 AS boosted
FROM <database>.jobs j
```

Toolbox code, by files 03 to 05:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.team,
           AS(None, "bump"),      # refused: circular, NULL in the Hive
           AS(None, "tag"),       # refused: LAMBDA, NULL in the Hive
           AS(None, "scaled"),    # refused: Summary!D4, NULL in the Hive
           AS(jobs.job_id * 10, "boosted")),  # boost = Summary!B2 = 10; move it into Parameters
    FROM(jobs),
)
```

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X32

Map:
- Sources: jobs (job_id, job_name, team, region); job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: job_runs, because its job_name formula is read by by_name. It is a CTE in by_name's query.
- Finals: by_name (job_name, runs). by_name is a summary: COUNTIFS on job_name makes it a GROUP BY of job_runs.
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks: VLOOKUP(job_id, jobs, 2, TRUE) is approximate. It is converted exactly as a LEFT JOIN of jobs on job_id, and this is said here. The sample's job_ids match exactly, so the rows are the same. COUNTIFS becomes COALESCE(COUNT(*), 0). cache_warm has no runs and no row in by_name, so it is not in the GROUP BY.
- Refusals: none.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
WITH job_runs_with_name AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT w.job_name, COALESCE(COUNT(*), 0) AS runs
FROM job_runs_with_name w
GROUP BY w.job_name
```

Toolbox code, by files 03 to 05:

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived, equals, fill_null, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

with_name = derived("with_name", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt, jobs.job_name),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))
s = statement(
    SELECT(with_name.job_name, AS(fill_null(count_rows(), 0), "runs")),
    FROM(with_name),
    GROUP_BY(with_name.job_name),
)
```

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X33

Map:
- Sources: none in the workbook. The Power Query reads the table job_runs from Sql.Database("dwh01", "ops") and the schema "ops". Its Hive source is `<database>.job_runs`.
- Steps: none.
- Finals: slow_runs (run_id, duration_mins, over_by). Its query is the final's query. No formula reads slow_runs.
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks: the Sql.Database source is replaced by the table it names, job_runs. Check that `<database>` is the Hive database holding ops.job_runs from dwh01, and that job_runs is the table to read. M's `[status] <> "TEST"` keeps a NULL, as Hive's `<>` doesn't, so it becomes (status <> 'TEST' OR status IS NULL).
- Refusals: none.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT s.run_id, s.duration_mins,
  s.duration_mins - 20 AS over_by
FROM <database>.job_runs s
WHERE s.duration_mins >= 20
  AND (s.status <> 'TEST' OR s.status IS NULL)
```

Toolbox code, by files 03 to 05:

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

Next: take out of the workbook what you don't want converted; fill in `<database>`; check the table it reads, job_runs, against the source database; run `project.convert` on the Hive. Its checked code wins where it differs.

## X34

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region).
- Steps: runs_with_team, a connection-only query that team_totals reads. It is a CTE in team_totals' query, with a LEFT JOIN of jobs on job_id (LeftOuter).
- Finals: team_totals (team, total_mins, longest). It is loaded by its query and nothing reads it.
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks: List.Sum becomes SUM and List.Max becomes MAX, grouped by team.
- Refusals: none.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
WITH runs_with_team AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT w.team,
  SUM(w.duration_mins) AS total_mins,
  MAX(w.duration_mins) AS longest
FROM runs_with_team w
GROUP BY w.team
```

Toolbox code, by files 03 to 05:

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

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X35

Map:
- Sources: job_runs (run_id, dt); scheduler_runs (run_id, dt).
- Steps: none. The Runs and Scheduled steps are inside one query.
- Finals: recent (run_id, dt). Its query is the final's query.
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks: Table.Combine becomes UNION ALL. Table.Sort descending on run_id, then Table.FirstN 4, becomes ORDER BY run_id DESC LIMIT 4.
- Refusals: the connection-only query "rates" reads Web.Contents, a web source, so it is left out, and named. Nothing reads it.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT u.run_id, u.dt
FROM (
  SELECT r.run_id, r.dt
  FROM <database>.job_runs r
  UNION ALL
  SELECT s.run_id, s.dt
  FROM <database>.scheduler_runs s
) u
ORDER BY u.run_id DESC
LIMIT 4
```

Toolbox code, by files 03 to 05:

```python
from sqlglot_composer import AS, FROM, LIMIT, ORDER_BY, SELECT, UNION_ALL, derived, descending, statement
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

both = derived("both", UNION_ALL(
    statement(SELECT(job_runs.run_id, job_runs.dt), FROM(job_runs)),
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt), FROM(scheduler_runs)),
))
s = statement(
    SELECT(both.run_id, both.dt),
    FROM(both),
    ORDER_BY(descending(both.run_id)),
    LIMIT(4),
)
```

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X36

Map:
- Sources: run_alerts (run_id, severity, dt); job_runs (run_id, status).
- Steps: none.
- Finals: job_runs (run_id, status, alerts); severity_by_day (dt, high, low). severity_by_day is loaded by its Power Query and nothing reads it.
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks: alerts = COUNTIFS over another Table, so it is a LEFT JOIN to a COUNT subquery, with COALESCE(alerts, 0). The Table.Pivot becomes a SUM(CASE WHEN ... THEN 1 END) for each value in the sample, high and low, grouped by dt, NULL where none, as M leaves it. The pivot's columns are now fixed: high and low.
- Refusals: none.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT j.run_id, j.status,
  COALESCE(a.alerts, 0) AS alerts
FROM <database>.job_runs j
LEFT JOIN (
  SELECT r.run_id, COUNT(*) AS alerts
  FROM <database>.run_alerts r
  GROUP BY r.run_id
) a ON j.run_id = a.run_id
```

```sql
SELECT a.dt,
  SUM(CASE WHEN a.severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN a.severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts a
GROUP BY a.dt
```

Toolbox code, by files 03 to 05, for job_runs:

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
```

The severity_by_day pivot needs file 10 (Hive written by hand, for the CASE in SUM). Load it in a new chat for that Toolbox code.

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X37

Map:
- Sources: Owners (Job No, Team Name, Owner, Day).
- Steps: none.
- Finals: Owners (<job_no>, <team_name>, Owner, Day, <is_ana>). All 56 rows are kept.
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks, blank: the Owner is blank on every web row. Owner is read by the IF, so it is wrapped as COALESCE(Owner, ''), and this is said here. The result is 0 for those rows, as Excel gives.
- Marks: header names with spaces become placeholders: Job No is <job_no>, Team Name is <team_name>, Is Ana is <is_ana>.
- Refusals: none.
- Left alone: the Steps sheet.
- Fill in: `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

```sql
SELECT o.<job_no>, o.<team_name>, o.Owner, o.Day,
  IF(COALESCE(o.Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners o
```

Toolbox code, by files 03 to 05:

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.<database>__owners import owners

s = statement(
    SELECT(owners.<job_no>, owners.<team_name>, owners.Owner, owners.Day,
           AS(if_else(equals(fill_null(owners.Owner, ""), "ana"), 1, 0), "<is_ana>")),
    FROM(owners),
)
```

Next: take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X38

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs); jobs (job_id, region).
- Steps: none. job_runs is read by no other Table; its region formula is read by its own region_mins, so a CTE holds region for the same query.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost).
- Keys: the Keys sheet has job_runs | run_id, so the typed value matches on run_id.
- Typed over: retry_cost for run_id 102 is 1, not the formula. Converted as CASE WHEN run_id = 102 THEN 1.
- Marks: the blank avg_retry_secs in row 98 is read by retry_cost, so it is wrapped as COALESCE(avg_retry_secs, 0), and this is a blank. XLOOKUP becomes a LEFT JOIN of jobs on job_id, then region. SUMIFS over its own Table becomes a window, SUM(duration_mins) OVER (PARTITION BY region), wrapped in COALESCE(.., 0).
- Refusals: none.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
WITH with_region AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
    j.region
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT w.run_id, w.job_id, w.status, w.duration_mins, w.avg_retry_secs, w.region,
  COALESCE(SUM(w.duration_mins) OVER (PARTITION BY w.region), 0) AS region_mins,
  CASE WHEN w.run_id = 102 THEN 1
    ELSE (COALESCE(w.avg_retry_secs, 0) + w.duration_mins) * 2 END AS retry_cost
FROM with_region w
```

Toolbox code, by files 03 to 05:

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, derived, equals, fill_null,
                              first_match, statement, sum_of, window)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

with_region = derived("with_region", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, jobs.region),
    FROM(job_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))
each_region = window(PARTITION_BY=with_region.region)
s = statement(
    SELECT(with_region.run_id, with_region.job_id, with_region.status,
           with_region.duration_mins, with_region.avg_retry_secs, with_region.region,
           AS(fill_null(sum_of(with_region.duration_mins, over=each_region), 0), "region_mins"),
           AS(first_match([(equals(with_region.run_id, 102), 1)],
                          otherwise=(fill_null(with_region.avg_retry_secs, 0)
                                     + with_region.duration_mins) * 2), "retry_cost")),
    FROM(with_region),
)
```

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.

## X39

Map:
- Sources: job_runs (run_id, job_id, status, duration_mins); jobs (job_id, job_name).
- Steps: none.
- Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise). ok_runs is loaded by its Power Query, and its formulas read only its own columns, so its query is the final's query.
- Parameters and Keys are empty, so they are none. No value is typed over a formula.
- Marks: the Power Query's status = "SUCCESS" becomes WHERE status = 'SUCCESS'. The blank status in row 98 drops out, as it does in M. share = duration_mins / SUMIFS over its own Table becomes a window, SUM(duration_mins) OVER (PARTITION BY job_id), wrapped in COALESCE(.., 0). XLOOKUP becomes a LEFT JOIN of jobs on job_id, then job_name.
- Refusals: noise = RAND() is refused, so NULL AS noise.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT o.run_id, o.job_id, o.duration_mins,
  j.job_name,
  o.duration_mins / COALESCE(SUM(o.duration_mins) OVER (PARTITION BY o.job_id), 0) AS share,
  NULL AS noise
FROM (
  SELECT r.run_id, r.job_id, r.duration_mins
  FROM <database>.job_runs r
  WHERE r.status = 'SUCCESS'
) o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

Toolbox code, by files 03 to 05:

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, WHERE, derived, equals, fill_null, statement, sum_of, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

succeeded = derived("succeeded", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(equals(job_runs.status, "SUCCESS")),
))
by_job = window(PARTITION_BY=succeeded.job_id)
s = statement(
    SELECT(succeeded.run_id, succeeded.job_id, succeeded.duration_mins,
           AS(jobs.job_name, "job_name"),
           AS(succeeded.duration_mins / fill_null(sum_of(succeeded.duration_mins, over=by_job), 0), "share"),
           AS(None, "noise")),  # refused: RAND(), NULL in the Hive
    FROM(succeeded),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, succeeded.job_id)),
)
```

Next: take out of the workbook what you don't want converted; fill in `<database>`; run `project.convert` on the Hive. Its checked code wins where it differs.
