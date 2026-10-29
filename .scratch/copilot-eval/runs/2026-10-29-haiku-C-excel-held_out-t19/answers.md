date: 2026-10-29
arm: C
model: haiku
files: 61c9ca2

## X21

**Map**
- Sources: region_budgets (job_id, budget_cents, region)
- Steps: none
- Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin)

**Notes**
- Nothing is typed over a formula, so no CASE and no Keys row is needed (Keys is empty).
- No blanks in the sample. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
SELECT r.job_id, r.budget_cents, r.region,
  r.budget_cents / 100 AS budget_dollars,
  r.budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets r
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__region_budgets import region_budgets

s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(region_budgets.budget_cents / 100, "budget_dollars"),
           AS(region_budgets.budget_cents * 1.1, "with_margin")),
    FROM(region_budgets, reads_all_partitions=True),  # every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X22

**Map**
- Sources: jobs (job_id, job_name, team)
- Steps: none
- Finals: jobs (job_id, job_name, team, is_finance, ratio)

**Notes**
- Nothing is typed over a formula. Keys is empty, so no Keys row is needed.
- `is_finance` is IF as it is.
- `ratio`: IFERROR becomes COALESCE, as Hive gives NULL for a divide by 0. Job 2 has job_id - 2 = 0, so its ratio is 0.
- No blanks. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team,
  IF(j.team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(j.job_id / (j.job_id - 2), 0) AS ratio
FROM <database>.jobs j
```

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.<database>__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(if_else(equals(jobs.team, "finance"), "yes", "no"), "is_finance"),
           AS(fill_null(jobs.job_id / (jobs.job_id - 2), 0), "ratio")),
    FROM(jobs, reads_all_partitions=True),  # every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X23

**Map**
- Sources: job_runs (run_id, status, avg_retry_secs)
- Steps: none
- Finals: job_runs (run_id, status, avg_retry_secs, label, risky)

**Notes**
- Nothing is typed over a formula. Keys is empty.
- Blank: status and avg_retry_secs are both blank on run 98. Both columns are read by formulas, and neither formula is an -IF(S) form, so each read is wrapped: COALESCE(status, '') and COALESCE(avg_retry_secs, 0).
- `label`: SWITCH with three cases becomes a CASE with a WHEN per case and ELSE 'other' for the default.
- `risky`: OR as it is.
- No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.status, r.avg_retry_secs,
  CASE COALESCE(r.status, '')
    WHEN 'SUCCESS' THEN 'ok'
    WHEN 'FAILED' THEN 'bad'
    ELSE 'other'
  END AS label,
  (COALESCE(r.status, '') = 'FAILED' OR COALESCE(r.avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs r
```

```python
from sqlglot_composer import AS, FROM, SELECT, any_of, equals, fill_null, first_match, more_than, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.status, job_runs.avg_retry_secs,
           AS(first_match([(equals(fill_null(job_runs.status, ""), "SUCCESS"), "ok"),
                           (equals(fill_null(job_runs.status, ""), "FAILED"), "bad")],
                          otherwise="other"), "label"),
           AS(any_of(equals(fill_null(job_runs.status, ""), "FAILED"),
                     more_than(fill_null(job_runs.avg_retry_secs, 0), 5)), "risky")),
    FROM(job_runs, reads_all_partitions=True),  # every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X24

**Map**
- Sources: team_notes (team, note, written_on)
- Steps: none
- Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars)

**Notes**
- `first_word`: LEFT(note, FIND(" ", note) - 1) becomes SUBSTR(note, 1, INSTR(note, ' ') - 1).
- `shout`: UPPER as it is. `month`: MONTH as it is. `tens_of_chars`: ROUND(LEN(note) / 10, 1) becomes ROUND(LENGTH(note) / 10, 1).
- Nothing typed over. No blanks. Keys is empty. No refusals. Nothing left alone.
- The Toolbox code for `first_word`, `shout`, `month` and `tens_of_chars` needs Hive functions (SUBSTR, INSTR, UPPER, MONTH, ROUND, LENGTH) that files 03 to 05 don't name. Load file 10 in a new chat for those.
- Fill in: `<database>`.

```sql
SELECT n.team, n.note, n.written_on,
  SUBSTR(n.note, 1, INSTR(n.note, ' ') - 1) AS first_word,
  UPPER(n.team) AS shout,
  MONTH(n.written_on) AS month,
  ROUND(LENGTH(n.note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes n
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__team_notes import team_notes

s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on),
    FROM(team_notes, reads_all_partitions=True),  # every row
)
# first_word, shout, month and tens_of_chars: load file 10 in a new chat.
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X25

**Map**
- Sources: Costs (Job, `<cost_cents>`, Region, `<day_key>`); Budgets (Job, Budget, Region)
- Steps: none
- Finals: Costs (Job, `<cost_cents>`, Region, `<day_key>`, Day); Budgets (Job, Budget, Region, Dollars)

**Notes**
- Names: `Cost (cents)` is `<cost_cents>` and `Day Key` is `<day_key>`. Costs, Budgets, Job, Budget, Region, Day and Dollars are plain names and are kept.
- Mark: `Day Key` holds a date as text (20260911). `Day` becomes CONCAT(SUBSTR(day_key, 1, 4), '-', SUBSTR(day_key, 5, 2), '-', SUBSTR(day_key, 7, 2)) in place of DATE(LEFT, MID, RIGHT).
- Blank: `Cost (cents)` is blank on Costs row 29. No formula reads it, so it stays NULL and is not wrapped.
- `Dollars` is Budget / 100.
- Nothing typed over. Keys is empty. No refusals. Nothing left alone.
- Fill in: `<database>`, `<cost_cents>`, `<day_key>`.

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

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__Costs import Costs
from references.<database>__Budgets import Budgets

costs = statement(
    SELECT(Costs.Job, Costs.<cost_cents>, Costs.Region, Costs.<day_key>),
    FROM(Costs, reads_all_partitions=True),  # every row
)
budgets = statement(
    SELECT(Budgets.Job, Budgets.Budget, Budgets.Region,
           AS(Budgets.Budget / 100, "Dollars")),
    FROM(Budgets, reads_all_partitions=True),  # every row
)
# Day needs CONCAT and SUBSTR: load file 10 in a new chat.
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X26

**Map**
- Sources: run_alerts (alert_id, run_id, severity); job_runs (run_id, job_id, status, duration_mins)
- Steps: none
- Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins)

**Notes**
- `job_id`: XLOOKUP on run_id becomes LEFT JOIN job_runs ON run_id = run_id, then job_id.
- `status`: VLOOKUP with FALSE is an exact match on the same join, column 3 (status).
- `avg_mins`: AVERAGEIFS over another Table becomes a LEFT JOIN onto (SELECT job_id, AVG(duration_mins) ... GROUP BY job_id). AVG is left NULL, with no COALESCE.
- Blank: job_runs status is blank on run 98. The VLOOKUP reads that column, so it is wrapped as COALESCE(status, ''). No alert points at run 98.
- Nothing typed over. Keys is empty. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
WITH looked_up AS (
  SELECT a.alert_id, a.run_id, a.severity, r.job_id,
    COALESCE(r.status, '') AS status
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT l.alert_id, l.run_id, l.severity, l.job_id, l.status, av.avg_mins
FROM looked_up l
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) av ON l.job_id = av.job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, derived, equals, fill_null, statement
from references.<database>__run_alerts import run_alerts
from references.<database>__job_runs import job_runs

jr = AS(job_runs, "jr")
avg_by_job = derived("avg_by_job", statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # every row
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, jr.job_id,
           AS(fill_null(jr.status, ""), "status"), avg_by_job.avg_mins),
    FROM(run_alerts, reads_all_partitions=True),  # every row
    LEFT_JOIN(jr, ON=equals(jr.run_id, run_alerts.run_id)),
    LEFT_JOIN(avg_by_job, ON=equals(avg_by_job.job_id, jr.job_id)),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X27

**Map**
- Sources: jobs (job_id, job_name, team)
- Steps: none
- Finals: by_team (team, jobs_in_team, last_job_id, last_job_name)

**Notes**
- `by_team` has one typed column, team, and COUNTIFS and MAXIFS match on it. It is a summary: a GROUP BY of jobs.
- `jobs_in_team`: COUNTIFS becomes COUNT(*), with COALESCE. `last_job_id`: MAXIFS becomes MAX, with COALESCE.
- `last_job_name`: INDEX with MATCH(..., 0) is exact, so it becomes LEFT JOIN jobs ON last_job_id = job_id, then job_name.
- No blanks. Nothing typed over. Keys is empty. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
WITH summary AS (
  SELECT team,
    COALESCE(COUNT(*), 0) AS jobs_in_team,
    COALESCE(MAX(job_id), 0) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
)
SELECT s.team, s.jobs_in_team, s.last_job_id, j.job_name AS last_job_name
FROM summary s
LEFT JOIN <database>.jobs j ON s.last_job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived, equals, fill_null, max_of, statement
from references.<database>__jobs import jobs

j = AS(jobs, "j")
summary = derived("summary", statement(
    SELECT(jobs.team, AS(fill_null(count_rows(), 0), "jobs_in_team"),
           AS(fill_null(max_of(jobs.job_id), 0), "last_job_id")),
    FROM(jobs, reads_all_partitions=True),  # every row
    GROUP_BY(jobs.team),
))
s = statement(
    SELECT(summary.team, summary.jobs_in_team, summary.last_job_id,
           AS(j.job_name, "last_job_name")),
    FROM(summary),
    LEFT_JOIN(j, ON=equals(j.job_id, summary.last_job_id)),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X28

**Map**
- Sources: jobs (job_id, job_name); job_runs (job_id, status, duration_mins)
- Steps: none
- Finals: jobs (job_id, job_name, ok_mins)

**Notes**
- `ok_mins`: SUMIFS over another Table becomes a LEFT JOIN onto (SELECT job_id, SUM(duration_mins) AS total FROM job_runs WHERE status = 'SUCCESS' GROUP BY job_id), with COALESCE(total, 0).
- Typed over: report_build (job_id 3) has 99 in ok_mins, where the formula would give its sum. Keys says jobs | job_id, so the row matches on job_id: CASE WHEN job_id = 3 THEN 99.
- Blank: job_runs status is blank on run 98. SUMIFS is an -IFS form, which skips blanks, so the status is not wrapped.
- No refusals. Nothing left alone.
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

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, derived, equals, fill_null, if_else, statement, sum_of
from references.<database>__jobs import jobs
from references.<database>__job_runs import job_runs

ok = derived("ok", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),  # every row
    WHERE(equals(job_runs.status, "SUCCESS")),
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(if_else(equals(jobs.job_id, 3), 99, fill_null(ok.total, 0)), "ok_mins")),
    FROM(jobs, reads_all_partitions=True),  # every row
    LEFT_JOIN(ok, ON=equals(ok.job_id, jobs.job_id)),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X29

**Map**
- Sources: region_budgets (job_id, budget_cents, region)
- Steps: none
- Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer)

**Notes**
- `in_dollars`: budget_cents / XLOOKUP("cents_per_dollar", Parameters) is the Parameters value, 100. Parameters is neither a source nor a step.
- Typed over: in_dollars is 5 on job 3 (budget_cents 350, region us). Keys is empty, so there is no Keys row for region_budgets. The row matches on every typed column: job_id = 3 AND budget_cents = 350 AND region = 'us'.
- `pointer`: INDIRECT is refused, so `NULL AS pointer`. Refused: INDIRECT.
- No blanks. Nothing left alone.
- Fill in: `<database>`.

```sql
SELECT r.job_id, r.budget_cents, r.region,
  CASE WHEN r.job_id = 3 AND r.budget_cents = 350 AND r.region = 'us' THEN 5
       ELSE r.budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets r
```

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, equals, if_else, statement
from references.<database>__region_budgets import region_budgets

s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(if_else(all_of(equals(region_budgets.job_id, 3),
                             equals(region_budgets.budget_cents, 350),
                             equals(region_budgets.region, "us")),
                      5, region_budgets.budget_cents / 100), "in_dollars")),
    FROM(region_budgets, reads_all_partitions=True),  # every row
)
# pointer is refused (INDIRECT): load file 09 in a new chat to fix it.
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X30

**Map**
- Sources: scheduler_runs (run_id, job_id, dt)
- Steps: none
- Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter)

**Notes**
- `day`: RIGHT(dt, 2) becomes SUBSTR(dt, -2).
- Refused: `prev_run` (OFFSET), so `NULL AS prev_run`; `jitter` (RANDBETWEEN), so `NULL AS jitter`.
- Left alone: the Summary sheet's bar chart, and the PivotTable on sheet Pivot.
- No blanks. Nothing typed over. Keys is empty.
- Fill in: `<database>`.

```sql
SELECT s.run_id, s.job_id, s.dt,
  SUBSTR(s.dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs s
```

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__scheduler_runs import scheduler_runs

s = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # every row
)
# day needs SUBSTR: load file 10. prev_run and jitter are refused: load file 09.
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X31

**Map**
- Sources: jobs (job_id, team)
- Steps: none
- Finals: jobs (job_id, team, bump, tag, scaled, boosted)

**Notes**
- `bump` reads its own column, so it is circular and refused: `NULL AS bump`.
- `tag` calls TAG, a defined name holding a LAMBDA, which is refused: `NULL AS tag`.
- `scaled` reads Summary!$D$4, a cell outside any Table that is not a defined name. Refused: `NULL AS scaled` (the cell is Summary!D4).
- `boosted`: the defined name boost is Summary!$B$2, which is 10. It converts with its value: job_id * 10. Move 10 into Parameters, as the defined name points outside a Table.
- Left alone: the other cells on Summary, which are outside a Table.
- No blanks. Nothing typed over. Keys is empty.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.team,
  NULL AS bump,
  NULL AS tag,
  NULL AS scaled,
  j.job_id * 10 AS boosted
FROM <database>.jobs j
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.team,
           AS(jobs.job_id * 10, "boosted")),
    FROM(jobs, reads_all_partitions=True),  # every row
)
# bump, tag and scaled are refused: load file 09 in a new chat to fix them.
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X32

**Map**
- Sources: jobs (job_id, job_name); job_runs (job_id)
- Steps: job_runs (job_id, job_name), read by by_name, so it is a step and not a final
- Finals: by_name (job_name, runs)

**Notes**
- `job_name` on job_runs: VLOOKUP(job_id, jobs, 2, TRUE) is approximate. It is converted exactly, as a LEFT JOIN jobs ON job_id = job_id, then job_name. The workbook's TRUE was approximate, so the exact join may differ where job_id has no match.
- `by_name` has one typed column, job_name, which COUNTIFS matches on. It is a summary: a GROUP BY of the job_runs step.
- `runs`: COUNTIFS becomes COUNT(*), with COALESCE. It is left as the count of every job_runs row with that name.
- No blanks in the read columns. Nothing typed over. Keys is empty. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
WITH named AS (
  SELECT r.job_id, j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT n.job_name, COALESCE(COUNT(*), 0) AS runs
FROM named n
GROUP BY n.job_name
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived, equals, fill_null, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

named = derived("named", statement(
    SELECT(job_runs.job_id, AS(jobs.job_name, "job_name")),
    FROM(job_runs, reads_all_partitions=True),  # every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))
s = statement(
    SELECT(named.job_name, AS(fill_null(count_rows(), 0), "runs")),
    FROM(named),
    GROUP_BY(named.job_name),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X33

**Map**
- Sources: job_runs (run_id, duration_mins, status), read by Power Query from Sql.Database("dwh01", "ops"), item job_runs in schema ops
- Steps: none
- Finals: slow_runs (run_id, duration_mins, over_by)

**Notes**
- Check: the Power Query reads job_runs from server dwh01, database ops. Converted as `<database>.job_runs`. Check that this is the table you mean.
- Table.SelectRows: `[duration_mins] >= 20 and [status] <> "TEST"` becomes WHERE duration_mins >= 20 AND (status <> 'TEST' OR status IS NULL). M's `<>` keeps a null, and Hive's does not, so the IS NULL is added.
- Table.AddColumn: `over_by` is duration_mins - 20.
- Table.SelectColumns: the SELECT list.
- `slow_runs` is loaded by a query, so its typed columns are not sources.
- Nothing typed over. Keys is empty. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.duration_mins,
  r.duration_mins - 20 AS over_by
FROM <database>.job_runs r
WHERE r.duration_mins >= 20
  AND (r.status <> 'TEST' OR r.status IS NULL)
```

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, any_of, at_least, is_null, not_equals, statement
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins - 20, "over_by")),
    FROM(job_runs, reads_all_partitions=True),  # every row
    WHERE(at_least(job_runs.duration_mins, 20),
          any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X34

**Map**
- Sources: job_runs (job_id, duration_mins); jobs (job_id, team)
- Steps: runs_with_team (the connection-only query: job_runs LEFT JOIN jobs, with team), read by team_totals
- Finals: team_totals (team, total_mins, longest)

**Notes**
- `runs_with_team`: NestedJoin with LeftOuter becomes LEFT JOIN jobs ON job_id = job_id. ExpandTableColumn brings in team.
- `team_totals`: Table.Group on team. List.Sum becomes SUM(duration_mins) AS total_mins. List.Max becomes MAX(duration_mins) AS longest.
- `team_totals` is loaded by a query, so its typed columns are not sources.
- No blanks in the read columns. Nothing typed over. Keys is empty. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
WITH runs_with_team AS (
  SELECT r.duration_mins, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT t.team,
  SUM(t.duration_mins) AS total_mins,
  MAX(t.duration_mins) AS longest
FROM runs_with_team t
GROUP BY t.team
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals, max_of, statement, sum_of
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

runs_with_team = derived("runs_with_team", statement(
    SELECT(job_runs.duration_mins, jobs.team),
    FROM(job_runs, reads_all_partitions=True),  # every row
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

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X35

**Map**
- Sources: job_runs (run_id, dt); scheduler_runs (run_id, dt)
- Steps: none
- Finals: recent (run_id, dt)

**Notes**
- `recent`: Table.Combine becomes UNION ALL. Table.Sort on run_id descending becomes ORDER BY run_id DESC. Table.FirstN 4 becomes LIMIT 4.
- Left out: the `rates` query. It reads Web.Contents("https://rates.example.com/today.json"), a web source, so the query is left out. It is connection-only and nothing reads it.
- Nothing typed over. Keys is empty. No blanks in the read columns. Nothing left alone.
- Fill in: `<database>`.

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

```python
from sqlglot_composer import FROM, SELECT, UNION_ALL, statement
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

both = UNION_ALL(
    statement(SELECT(job_runs.run_id, job_runs.dt),
              FROM(job_runs, reads_all_partitions=True)),  # every row
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt),
              FROM(scheduler_runs, reads_all_partitions=True)),  # every row
)
# The sort and the top 4 are not in files 03 to 05. Sort the result in pandas:
# run_query(both, query).sort_values("run_id", ascending=False).head(4)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X36

**Map**
- Sources: run_alerts (run_id, severity, dt); job_runs (run_id, status)
- Steps: none
- Finals: job_runs (run_id, status, alerts); severity_by_day (dt, high, low)

**Notes**
- `alerts`: COUNTIFS over another Table becomes a LEFT JOIN onto (SELECT run_id, COUNT(*) AS n FROM run_alerts GROUP BY run_id), with COALESCE(n, 0).
- `severity_by_day`: Table.Pivot on severity gives one column per value in the sample, high and low, each as SUM(CASE WHEN severity = '...' THEN 1 END), NULL where a day has none. Table.Pivot's columns are now fixed at high and low: a new severity value will not get its own column.
- Table.SelectColumns (dt, severity) is the source. Table.AddColumn `n` = 1 is folded into the count.
- Nothing typed over. Keys is empty. No blanks in the read columns. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
SELECT j.run_id, j.status, COALESCE(a.n, 0) AS alerts
FROM <database>.job_runs j
LEFT JOIN (
  SELECT run_id, COUNT(*) AS n
  FROM <database>.run_alerts
  GROUP BY run_id
) a ON j.run_id = a.run_id
```

```sql
SELECT dt,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
GROUP BY dt
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived, equals, fill_null, statement
from references.<database>__run_alerts import run_alerts
from references.<database>__job_runs import job_runs

per_run = derived("per_run", statement(
    SELECT(run_alerts.run_id, AS(fill_null(count_rows(), 0), "n")),
    FROM(run_alerts, reads_all_partitions=True),  # every row
    GROUP_BY(run_alerts.run_id),
))
job_runs_alerts = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(fill_null(per_run.n, 0), "alerts")),
    FROM(job_runs, reads_all_partitions=True),  # every row
    LEFT_JOIN(per_run, ON=equals(per_run.run_id, job_runs.run_id)),
)
severity_by_day = statement(
    SELECT(run_alerts.dt,
           AS(count_rows(where=equals(run_alerts.severity, "high")), "high"),
           AS(count_rows(where=equals(run_alerts.severity, "low")), "low")),
    FROM(run_alerts, reads_all_partitions=True),  # every row
    GROUP_BY(run_alerts.dt),
)
# count_rows gives 0 where a day has no such severity; the SQL above keeps NULL, as M does.
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X37

**Map**
- Sources: Owners (Job No, Team Name, Owner, Day)
- Steps: none
- Finals: Owners (`<job_no>`, `<team_name>`, Owner, Day, `<is_ana>`)

**Notes**
- Names: `Job No` is `<job_no>`, `Team Name` is `<team_name>`, `Is Ana` is `<is_ana>`. Owners, Owner and Day are plain names and are kept.
- `Is Ana`: IF([@Owner] = "ana", 1, 0) becomes IF(owner = 'ana', 1, 0).
- Blank: Owner is blank on the web rows. The IF reads Owner, and a plain IF is not an -IF(S) form, so the read is wrapped: COALESCE(owner, ''). Blank.
- Nothing typed over. Keys is empty. No refusals. Nothing left alone.
- Fill in: `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

```sql
SELECT o.<job_no>, o.<team_name>, o.Owner, o.Day,
  IF(COALESCE(o.Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners o
```

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.<database>__Owners import Owners

s = statement(
    SELECT(Owners.<job_no>, Owners.<team_name>, Owners.Owner, Owners.Day,
           AS(if_else(equals(fill_null(Owners.Owner, ""), "ana"), 1, 0), "<is_ana>")),
    FROM(Owners, reads_all_partitions=True),  # every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X38

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs); jobs (job_id, region)
- Steps: none (region is computed in an inner CTE that the window reads)
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost)

**Notes**
- `region`: XLOOKUP on job_id becomes LEFT JOIN jobs ON job_id = job_id, then region.
- `region_mins`: SUMIFS over its own Table, matching on its region column (a formula column), becomes SUM(duration_mins) OVER (PARTITION BY region), with COALESCE.
- `retry_cost`: typed over. Run 102 has 1. Keys says job_runs | run_id, so the row matches on run_id: CASE WHEN run_id = 102 THEN 1.
- Blank: avg_retry_secs is blank on run 98. retry_cost reads it, so the read is wrapped: COALESCE(avg_retry_secs, 0). Blank.
- status is blank on run 98 but no formula reads it, so it stays NULL.
- No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
WITH with_region AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
    j.region AS region
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT w.run_id, w.job_id, w.status, w.duration_mins, w.avg_retry_secs, w.region,
  COALESCE(SUM(w.duration_mins) OVER (PARTITION BY w.region), 0) AS region_mins,
  CASE WHEN w.run_id = 102 THEN 1
       ELSE (COALESCE(w.avg_retry_secs, 0) + w.duration_mins) * 2 END AS retry_cost
FROM with_region w
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, derived, equals, fill_null, if_else, statement, sum_of, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

with_region = derived("with_region", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, AS(jobs.region, "region")),
    FROM(job_runs, reads_all_partitions=True),  # every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))
by_region = window(PARTITION_BY=with_region.region)
s = statement(
    SELECT(with_region.run_id, with_region.job_id, with_region.status,
           with_region.duration_mins, with_region.avg_retry_secs, with_region.region,
           AS(fill_null(sum_of(with_region.duration_mins, over=by_region), 0), "region_mins"),
           AS(if_else(equals(with_region.run_id, 102), 1,
                      (fill_null(with_region.avg_retry_secs, 0) + with_region.duration_mins) * 2),
              "retry_cost")),
    FROM(with_region),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X39

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins); jobs (job_id, job_name)
- Steps: none
- Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise)

**Notes**
- `ok_runs` is loaded by a query: Table.SelectRows status = 'SUCCESS', then Table.SelectColumns (run_id, job_id, duration_mins). Its typed columns are not sources.
- `job_name`: XLOOKUP on job_id becomes LEFT JOIN jobs ON job_id = job_id, then job_name.
- `share`: SUMIFS over its own Table becomes SUM(duration_mins) OVER (PARTITION BY job_id), with COALESCE, and share is duration_mins divided by it.
- `noise`: RAND is refused, so `NULL AS noise`.
- No blanks in the read columns. Nothing typed over. Keys is empty. Nothing left alone.
- Fill in: `<database>`.

```sql
WITH ok AS (
  SELECT r.run_id, r.job_id, r.duration_mins
  FROM <database>.job_runs r
  WHERE r.status = 'SUCCESS'
)
SELECT o.run_id, o.job_id, o.duration_mins, j.job_name,
  o.duration_mins / COALESCE(SUM(o.duration_mins) OVER (PARTITION BY o.job_id), 0) AS share,
  NULL AS noise
FROM ok o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, WHERE, derived, equals, fill_null, statement, sum_of, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

ok = derived("ok", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # every row
    WHERE(equals(job_runs.status, "SUCCESS")),
))
per_job = window(PARTITION_BY=ok.job_id)
s = statement(
    SELECT(ok.run_id, ok.job_id, ok.duration_mins, jobs.job_name,
           AS(ok.duration_mins / fill_null(sum_of(ok.duration_mins, over=per_job), 0), "share")),
    FROM(ok),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, ok.job_id)),
)
# noise is refused (RAND): load file 09 in a new chat to fix it.
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X40

**Map**
- Sources: Runs (Run, Job, Mins); jobs (job_id, team); run_alerts (alert_id, run_id, severity, dt)
- Steps: runs (Runs with Team and Cost), read by Teams and by run_alerts
- Finals: Teams (Team, `<total_cost>`); run_alerts (alert_id, run_id, severity, dt, `<run_mins>`)

**Notes**
- Parameters: "rate" is 2, taken as its value. Cost is Mins * 2. Parameters is neither a source nor a step.
- `runs`: Team is XLOOKUP on Job, so LEFT JOIN jobs ON Job = job_id, then team. Cost is Mins * 2.
- `Teams`: its only typed column is Team, which SUMIFS matches on. It is a summary: a GROUP BY of runs. `Total Cost` is `<total_cost>`, with COALESCE around the SUM.
- `Run Mins` is XLOOKUP(run_id, Runs[Run], Runs[Mins]), which becomes LEFT JOIN runs ON run_id = Run, then Mins. It is `<run_mins>`.
- Left alone: the PivotTable on sheet Pivot.
- No blanks. Nothing typed over. Keys is empty. No refusals.
- Fill in: `<database>`, `<total_cost>`, `<run_mins>`.

```sql
WITH runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT t.Team, COALESCE(t.total_cost, 0) AS <total_cost>
FROM (
  SELECT Team, SUM(Cost) AS total_cost
  FROM runs
  GROUP BY Team
) t
```

```sql
WITH runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt, r.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN runs r ON a.run_id = r.Run
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals, statement, sum_of
from references.<database>__Runs import Runs
from references.<database>__jobs import jobs
from references.<database>__run_alerts import run_alerts

runs = derived("runs", statement(
    SELECT(Runs.Run, Runs.Job, Runs.Mins, AS(jobs.team, "Team"), AS(Runs.Mins * 2, "Cost")),
    FROM(Runs, reads_all_partitions=True),  # every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, Runs.Job)),
))
teams = statement(
    SELECT(runs.Team, AS(sum_of(runs.Cost), "<total_cost>")),
    FROM(runs),
    GROUP_BY(runs.Team),
)
alerts = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(runs.Mins, "<run_mins>")),
    FROM(run_alerts, reads_all_partitions=True),  # every row
    LEFT_JOIN(runs, ON=equals(runs.Run, run_alerts.run_id)),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X46

**Map**
- Sources: jobs (job_id, job_name, team); job_runs (job_id, duration_mins)
- Steps: none (runs is computed in an inner CTE that the rank reads)
- Finals: jobs (job_id, job_name, team, shortest, runs, busiest)

**Notes**
- `shortest`: MINIFS over another Table becomes a LEFT JOIN onto (SELECT job_id, MIN(duration_mins) AS shortest FROM job_runs GROUP BY job_id), with COALESCE.
- `runs`: COUNTIF with one match becomes COUNT(*) on the same join, with COALESCE.
- `busiest`: RANK.EQ(runs, runs) becomes RANK() OVER (ORDER BY runs DESC). It reads runs, not its own column, so it is not circular.
- No blanks in the read columns. Nothing typed over. Keys is empty. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
WITH counted AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(m.shortest, 0) AS shortest,
    COALESCE(c.n, 0) AS runs
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, MIN(duration_mins) AS shortest
    FROM <database>.job_runs
    GROUP BY job_id
  ) m ON j.job_id = m.job_id
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS n
    FROM <database>.job_runs
    GROUP BY job_id
  ) c ON j.job_id = c.job_id
)
SELECT k.job_id, k.job_name, k.team, k.shortest, k.runs,
  RANK() OVER (ORDER BY k.runs DESC) AS busiest
FROM counted k
```

```python
from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived, descending, equals, fill_null, min_of, rank, statement, window
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

shortest_by_job = derived("shortest_by_job", statement(
    SELECT(job_runs.job_id, AS(min_of(job_runs.duration_mins), "shortest")),
    FROM(job_runs, reads_all_partitions=True),  # every row
    GROUP_BY(job_runs.job_id),
))
runs_by_job = derived("runs_by_job", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "n")),
    FROM(job_runs, reads_all_partitions=True),  # every row
    GROUP_BY(job_runs.job_id),
))
counted = derived("counted", statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(fill_null(shortest_by_job.shortest, 0), "shortest"),
           AS(fill_null(runs_by_job.n, 0), "runs")),
    FROM(jobs, reads_all_partitions=True),  # every row
    LEFT_JOIN(shortest_by_job, ON=equals(shortest_by_job.job_id, jobs.job_id)),
    LEFT_JOIN(runs_by_job, ON=equals(runs_by_job.job_id, jobs.job_id)),
))
s = statement(
    SELECT(counted.job_id, counted.job_name, counted.team, counted.shortest, counted.runs,
           AS(rank(over=window(ORDER_BY=descending(counted.runs))), "busiest")),
    FROM(counted),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X47

**Map**
- Sources: region_budgets (job_id, budget_cents, region)
- Steps: none
- Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg)

**Notes**
- `cheapest_first`: RANK.EQ with 1 as the third argument is ascending: RANK() OVER (ORDER BY budget_cents ASC).
- `region_total`: SUMIF over its own Table becomes SUM(budget_cents) OVER (PARTITION BY region), with COALESCE.
- `region_avg`: AVERAGEIF over its own Table becomes AVG(budget_cents) OVER (PARTITION BY region). AVG is left NULL, with no COALESCE.
- No blanks. Nothing typed over. Keys is empty. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
SELECT r.job_id, r.budget_cents, r.region,
  RANK() OVER (ORDER BY r.budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(r.budget_cents) OVER (PARTITION BY r.region), 0) AS region_total,
  AVG(r.budget_cents) OVER (PARTITION BY r.region) AS region_avg
FROM <database>.region_budgets r
```

```python
from sqlglot_composer import AS, FROM, SELECT, average_of, fill_null, rank, statement, sum_of, window
from references.<database>__region_budgets import region_budgets

by_region = window(PARTITION_BY=region_budgets.region)
by_cost = window(ORDER_BY=region_budgets.budget_cents)
s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(rank(over=by_cost), "cheapest_first"),
           AS(fill_null(sum_of(region_budgets.budget_cents, over=by_region), 0), "region_total"),
           AS(average_of(region_budgets.budget_cents, over=by_region), "region_avg")),
    FROM(region_budgets, reads_all_partitions=True),  # every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X48

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins); jobs (job_id, region); run_alerts (run_id)
- Steps: none
- Finals: quiet_runs (run_id, job_id, status); slow_regions (region, avg_mins, fastest)

**Notes**
- `quiet_runs` is a LeftAnti join: LEFT JOIN run_alerts ON run_id = run_id, WHERE run_alerts.run_id IS NULL, with the first table's columns (run_id, job_id, status) from Table.SelectColumns.
- `slow_regions`: NestedJoin Inner becomes JOIN jobs. Table.Group on region gives AVG(duration_mins) AS avg_mins and MIN(duration_mins) AS fastest. The Table.SelectRows on avg_mins after the group becomes HAVING, repeating the AVG.
- Both finals are loaded by queries, so their typed columns are not sources.
- No blanks in the read columns. Nothing typed over. Keys is empty. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

```sql
SELECT j.region,
  AVG(r.duration_mins) AS avg_mins,
  MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

```python
from sqlglot_composer import ANTI_JOIN, FROM, GROUP_BY, HAVING, JOIN, SELECT, at_least, average_of, equals, min_of, statement
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs
from references.<database>__run_alerts import run_alerts

quiet_runs = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),  # every row
    ANTI_JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id),
              reads_all_partitions=True),  # every row
)
slow_regions = statement(
    SELECT(jobs.region,
           AS(average_of(job_runs.duration_mins), "avg_mins"),
           AS(min_of(job_runs.duration_mins), "fastest")),
    FROM(job_runs, reads_all_partitions=True),  # every row
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    GROUP_BY(jobs.region),
    HAVING(at_least(average_of(job_runs.duration_mins), 20)),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X49

**Map**
- Sources: job_runs (run_id, status); run_alerts (alert_id, run_id, severity); scheduler_runs (run_id); jobs (team); job_owners (team)
- Steps: none
- Finals: alert_status (alert_id, severity, status); run_check (run_id, status, scheduled_run); teams (team)

**Notes**
- `alert_status`: NestedJoin RightOuter becomes LEFT JOIN with the tables swapped: job_runs LEFT JOIN run_alerts ON run_id. Every job_runs row is kept, as in the sample (13 rows).
- `run_check`: NestedJoin FullOuter becomes FULL OUTER JOIN scheduler_runs ON run_id. `scheduled_run` is the scheduler's run_id.
- `teams`: Table.Distinct over Table.Combine becomes UNION, which drops the repeats.
- Repeats: the join on run_id is not the whole key of run_alerts, so run 97 gives two rows, as the sample shows. The Toolbox warns about this. Add many_matches=True only if you confirm the repeats are wanted, as the sample suggests.
- No formulas, Keys is empty, no blanks read by a formula. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
```

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

```python
from sqlglot_composer import AS, FROM, FULL_JOIN, LEFT_JOIN, SELECT, UNION, equals, statement
from references.<database>__job_runs import job_runs
from references.<database>__run_alerts import run_alerts
from references.<database>__scheduler_runs import scheduler_runs
from references.<database>__jobs import jobs
from references.<database>__job_owners import job_owners

alert_status = statement(
    SELECT(run_alerts.alert_id, run_alerts.severity, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),  # every row
    LEFT_JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id)),
)
run_check = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(scheduler_runs.run_id, "scheduled_run")),
    FROM(job_runs, reads_all_partitions=True),  # every row
    FULL_JOIN(scheduler_runs, ON=equals(job_runs.run_id, scheduler_runs.run_id),
              reads_all_partitions=True),  # every row
)
teams = UNION(
    statement(SELECT(jobs.team), FROM(jobs, reads_all_partitions=True)),  # every row
    statement(SELECT(job_owners.team), FROM(job_owners, reads_all_partitions=True)),  # every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X50

**Map**
- Sources: job_owners (job_id, owner); jobs (job_id, job_name)
- Steps: none
- Finals: owners (job_id, owner, job_name, newest_first)

**Notes**
- `owners` is loaded by a query: Table.SelectColumns (job_id, owner), then Table.Distinct, which is SELECT DISTINCT.
- `job_name`: XLOOKUP on job_id becomes LEFT JOIN jobs ON job_id = job_id, then job_name.
- `newest_first`: RANK.EQ(job_id, owners[job_id]) becomes RANK() OVER (ORDER BY job_id DESC).
- Blank: owner is blank for job 4. No formula reads owner, so it stays NULL and is not wrapped.
- Nothing typed over. Keys is empty. No refusals. Nothing left alone.
- Fill in: `<database>`.

```sql
WITH owners AS (
  SELECT DISTINCT o.job_id, o.owner
  FROM <database>.job_owners o
)
SELECT w.job_id, w.owner, j.job_name,
  RANK() OVER (ORDER BY w.job_id DESC) AS newest_first
FROM owners w
LEFT JOIN <database>.jobs j ON w.job_id = j.job_id
```

```python
from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT_DISTINCT, SELECT, derived, descending, equals, rank, statement, window
from references.<database>__job_owners import job_owners
from references.<database>__jobs import jobs

owners = derived("owners", statement(
    SELECT_DISTINCT(job_owners.job_id, job_owners.owner),
    FROM(job_owners, reads_all_partitions=True),  # every row
))
s = statement(
    SELECT(owners.job_id, owners.owner,
           AS(jobs.job_name, "job_name"),
           AS(rank(over=window(ORDER_BY=descending(owners.job_id))), "newest_first")),
    FROM(owners),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, owners.job_id)),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.
