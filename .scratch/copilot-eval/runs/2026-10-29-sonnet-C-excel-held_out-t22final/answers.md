date: 2026-10-29
arm: C
model: sonnet
files: 5df4678

## X21

Map. Sources: region_budgets. Steps: none. Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin); nothing reads it. Parameters and Keys hold nothing, so they are none.
Typed over a formula: none. Marks: none, as no formula reads a blank. Refused: none. Left alone: nothing outside a Table. Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets
```

Toolbox code, with `<database>` filled in the import:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__region_budgets import region_budgets

s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(region_budgets.budget_cents / 100, "budget_dollars"),
           AS(region_budgets.budget_cents * 1.1, "with_margin")),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted; fill in each `<...>` (`<database>`, here and in the import); run `project.convert` on the Hive. Its checked code wins where the two differ. If region_budgets has no partitions, drop `reads_all_partitions=True`.

## X22

Map. Sources: jobs. Steps: none. Finals: jobs (job_id, job_name, team, is_finance, ratio). Typed over: none. Marks: none; no blank in a column a formula reads. Refused: none. Left alone: nothing outside a Table. Fill in: `<database>`.

IFERROR(a / b, 0) is `COALESCE(a / b, 0)`: a divide by 0 is NULL in Hive (job_id 2 gives 0).

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
    FROM(jobs, reads_all_partitions=True),  # a workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X23

Map. Sources: job_runs. Steps: none. Finals: job_runs (run_id, status, avg_retry_secs, label, risky). Typed over: none. Refused: none. Left alone: nothing outside a Table. Fill in: `<database>`.
Mark, blank: run 98 has a blank status and a blank avg_retry_secs, and label and risky read them. Excel reads a blank as "" or 0, Hive as NULL, so I wrapped them: `COALESCE(status, '')` and `COALESCE(avg_retry_secs, 0)`. The typed columns themselves stay as they are.

```sql
SELECT run_id, status, avg_retry_secs,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label,
  (COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs
```

```python
from sqlglot_composer import (AS, FROM, SELECT, any_of, equals, fill_null, first_match,
                              more_than, statement)
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.status, job_runs.avg_retry_secs,
           AS(first_match([(equals(fill_null(job_runs.status, ""), "SUCCESS"), "ok"),
                           (equals(fill_null(job_runs.status, ""), "FAILED"), "bad")],
                          otherwise="other"), "label"),
           AS(any_of(equals(fill_null(job_runs.status, ""), "FAILED"),
                     more_than(fill_null(job_runs.avg_retry_secs, 0), 5)), "risky")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ (a true/false column is the one to look at).

## X24

Map. Sources: team_notes. Steps: none. Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars). Typed over: none. Marks: none; no blank in a column a formula reads. Refused: none. Left alone: nothing outside a Table. Fill in: `<database>`.

Every note holds a space, so FIND has a match in each row; in Hive a note with no space would give an empty first_word where Excel gives an error.

```sql
SELECT team, note, written_on,
  SUBSTR(note, 1, INSTR(note, ' ') - 1) AS first_word,
  UPPER(team) AS shout,
  MONTH(written_on) AS month,
  ROUND(LENGTH(note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes
```

The Toolbox code for the calculated columns needs Hive functions (SUBSTR, INSTR, UPPER, MONTH, LENGTH, ROUND), which file 10 covers and none of the files loaded here does. So the Python below holds the plain columns, and the five calculated ones are left to `project.convert` on the Hive above, or to a new chat with file 10.

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__team_notes import team_notes

s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on),
    # first_word, shout, month and tens_of_chars: Hive functions, file 10
    FROM(team_notes, reads_all_partitions=True),  # a workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X25

Map. Sources: Costs, Budgets. Steps: none. Finals: Costs (Job, Cost (cents), Region, Day Key, Day) and Budgets (Job, Budget, Region, Dollars); nothing reads either. Typed over: none. Refused: none. Left alone: nothing outside a Table.
Names: `Cost (cents)` is `<cost_cents>` and `Day Key` is `<day_key>`; the others are plain names and stay. Fill in: `<database>`, `<cost_cents>`, `<day_key>`.
Mark, date held as text: Day Key holds 20260911, so Day is built with SUBSTR and CONCAT as a 'yyyy-MM-dd' text. The date is held as text.
The blank Cost (cents) in the last-but-one row (job 2, 20260924) is not read by a formula, so it is left as it is.

```sql
SELECT Job, <cost_cents>, Region, <day_key>,
  CONCAT(SUBSTR(<day_key>, 1, 4), '-', SUBSTR(<day_key>, 5, 2), '-', SUBSTR(<day_key>, 7, 2)) AS Day
FROM <database>.Costs
```

```sql
SELECT Job, Budget, Region,
  Budget / 100 AS Dollars
FROM <database>.Budgets
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__Budgets import Budgets
from references.<database>__Costs import Costs

budgets = statement(
    SELECT(Budgets.Job, Budgets.Budget, Budgets.Region,
           AS(Budgets.Budget / 100, "Dollars")),
    FROM(Budgets, reads_all_partitions=True),  # a workbook's formulas read every row
)

costs = statement(
    SELECT(Costs.Job, Costs.<cost_cents>, Costs.Region, Costs.<day_key>),
    # Day: SUBSTR and CONCAT are Hive functions, file 10; take it from the Hive above
    FROM(Costs, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X26

Map. Sources: run_alerts, job_runs. Steps: none. Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins); nothing reads it. job_runs has no formulas, so it is only a source. Typed over: none. Refused: none. Left alone: nothing outside a Table. Fill in: `<database>`.
- job_id (XLOOKUP) and status (VLOOKUP, column 3 of job_runs, exact) are a LEFT JOIN to job_runs on run_id.
- avg_mins (AVERAGEIFS) is a LEFT JOIN to a grouped job_runs on the looked-up job_id, left NULL where nothing matches.
- There is no Keys row for job_runs, so I joined on run_id and took it to be one row per run, as in the sample. Blank: job_runs has a blank status (run 98) and avg_retry_secs, but no alert points at run 98 and no formula reads avg_retry_secs, so nothing is wrapped.

```sql
SELECT a.alert_id, a.run_id, a.severity,
  r.job_id AS job_id,
  r.status AS status,
  g.avg_mins AS avg_mins
FROM <database>.run_alerts a
LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins
           FROM <database>.job_runs
           GROUP BY job_id) g ON r.job_id = g.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, derived,
                              equals, statement)
from references.<database>__job_runs import job_runs
from references.<database>__run_alerts import run_alerts

per_job = derived("per_job", statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formulas read every row
    GROUP_BY(job_runs.job_id),
))
r = AS(job_runs, "r")
s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity,
           AS(r.job_id, "job_id"), AS(r.status, "status"), AS(per_job.avg_mins, "avg_mins")),
    FROM(run_alerts, reads_all_partitions=True),
    LEFT_JOIN(r, ON=equals(r.run_id, run_alerts.run_id), reads_all_partitions=True),
    LEFT_JOIN(per_job, ON=equals(per_job.job_id, r.job_id)),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ (the Toolbox may warn that run_id is not job_runs' Key, as the Keys sheet is empty).

## X27

Map. Sources: jobs. Steps: none. Finals: by_team (team, jobs_in_team, last_job_id, last_job_name); nothing reads it. by_team's only typed column, team, is what its COUNTIFS and MAXIFS match on, so it is a summary: a GROUP BY of jobs. Typed over: none. Refused: none. Left alone: nothing outside a Table. Fill in: `<database>`.
- last_job_name (INDEX/MATCH, exact) is a LEFT JOIN back to jobs on last_job_id.
- Every team of the summary has a match, so COUNT and MAX need no COALESCE.

```sql
WITH g AS (
  SELECT team, COUNT(*) AS jobs_in_team, MAX(job_id) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
)
SELECT g.team, g.jobs_in_team, g.last_job_id, j.job_name AS last_job_name
FROM g
LEFT JOIN <database>.jobs j ON g.last_job_id = j.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, max_of, statement)
from references.<database>__jobs import jobs

g = derived("g", statement(
    SELECT(jobs.team, AS(count_rows(), "jobs_in_team"), AS(max_of(jobs.job_id), "last_job_id")),
    FROM(jobs, reads_all_partitions=True),  # a workbook's formulas read every row
    GROUP_BY(jobs.team),
))
j = AS(jobs, "j")
s = statement(
    SELECT(g.team, g.jobs_in_team, g.last_job_id, AS(j.job_name, "last_job_name")),
    FROM(g),
    LEFT_JOIN(j, ON=equals(j.job_id, g.last_job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X28

Map. Sources: jobs, job_runs. Steps: none. Finals: jobs (job_id, job_name, ok_mins); nothing reads it. Keys row: jobs, job_id.
Typed over a formula: ok_mins where job_id is 3 (99), matched on the Keys column job_id. Refused: none. Left alone: nothing outside a Table. Fill in: `<database>`.
SUMIFS over another Table is a LEFT JOIN of job_runs grouped by job_id, kept to status 'SUCCESS', with COALESCE(.., 0) as Excel gives 0 where nothing matches. job_runs has a blank status (run 98), but SUMIFS skips a blank, so it is not wrapped.

```sql
SELECT j.job_id, j.job_name,
  CASE WHEN j.job_id = 3 THEN 99 ELSE COALESCE(s.total, 0) END AS ok_mins
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total
           FROM <database>.job_runs
           WHERE status = 'SUCCESS'
           GROUP BY job_id) s ON j.job_id = s.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, derived, equals,
                              fill_null, first_match, statement, sum_of)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

ok = derived("s", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formulas read every row
    WHERE(equals(job_runs.status, "SUCCESS")),
    GROUP_BY(job_runs.job_id),
))
j = AS(jobs, "j")
s = statement(
    SELECT(j.job_id, j.job_name,
           AS(first_match([(equals(j.job_id, 3), 99)],
                          otherwise=fill_null(ok.total, 0)), "ok_mins")),
    FROM(j, reads_all_partitions=True),
    LEFT_JOIN(ok, ON=equals(ok.job_id, j.job_id)),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X29

Map. Sources: region_budgets. Steps: none. Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer); nothing reads it. Parameters is none as a Table; its row cents_per_dollar is used as its value, 100.
Typed over a formula: in_dollars where job_id is 3 (5). There is no Keys row for region_budgets, so I matched every typed column of that row: job_id 3, budget_cents 350, region 'us'.
Refused: pointer, `INDIRECT("A"&ROW())` (INDIRECT, and ROW() hangs on the order of the sheet's rows): `NULL AS pointer`. Left alone: nothing outside a Table. Fill in: `<database>`.

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
    # pointer: refused, NULL in the Hive above
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ. You may also add a Keys row (region_budgets, job_id) and ask again, so the typed-over row matches on job_id alone.

## X30

Map. Sources: scheduler_runs. Steps: none. Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter); nothing reads it. Typed over: none. Fill in: `<database>`.
- day: `RIGHT(dt, 2)` is `SUBSTR(dt, -2)`. dt is read as text, as the sample shows.
- Refused: prev_run, `OFFSET` (and it hangs on the order of the rows): `NULL AS prev_run`. jitter, `RANDBETWEEN`: `NULL AS jitter`.
- Left alone: the bar chart on sheet Summary, and the PivotTable on sheet Pivot (from Table scheduler_runs, rows job_id, count of run_id).

```sql
SELECT run_id, job_id, dt,
  SUBSTR(dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs
```

SUBSTR is a Hive function (file 10), so the Python holds the plain columns; day is left to `project.convert` on the Hive, and the two refused ones are NULL there.

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__scheduler_runs import scheduler_runs

s = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    # day: SUBSTR, file 10; prev_run and jitter: refused, NULL in the Hive
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X31

Map. Sources: jobs. Steps: none. Finals: jobs (job_id, team, bump, tag, scaled, boosted); nothing reads it. Typed over: none. Fill in: `<database>`.
- Refused: bump, `[@bump]*2` reads its own column (circular): `NULL AS bump`.
- Refused: tag, a defined name TAG holding a LAMBDA: `NULL AS tag`.
- Refused: scaled, it reads cell D4 of sheet Summary, a cell outside a Table that isn't a defined name: `NULL AS scaled`.
- Mark, defined name for a cell outside a Table: boost is Summary B2, 10, so boosted uses its value, `job_id * 10`. Move it into the Parameters Table.
- Left alone: the cells on sheet Summary (B2, D4) outside a Table.

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
           AS(jobs.job_id * 10, "boosted")),  # boost = Summary B2, 10: move it into Parameters
    # bump, tag, scaled: refused, NULL in the Hive
    FROM(jobs, reads_all_partitions=True),  # a workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X32

Map. Sources: job_runs, jobs. Steps: job_runs, as it has a formula (job_name) that by_name reads. Finals: by_name (job_name, runs); nothing reads it. by_name's only typed column, job_name, is what its COUNTIFS matches on, so it is a summary: a GROUP BY of job_runs. Typed over: none. Refused: none. Left alone: nothing outside a Table. Fill in: `<database>`.
Mark, approximate: `VLOOKUP(.., jobs, 2, TRUE)` is approximate; I converted it exactly, a LEFT JOIN on job_id. The sample's jobs are sorted by job_id, so it agrees here; a job_id missing from jobs gives NULL, where Excel's approximate match would take the nearest lower row. No blank is read by a formula that matters here.

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name AS job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT job_name, COUNT(*) AS runs
FROM job_runs
GROUP BY job_name
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, statement)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

with_name = derived("with_name", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt, AS(jobs.job_name, "job_name")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formulas read every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
))
s = statement(
    SELECT(with_name.job_name, AS(count_rows(), "runs")),
    FROM(with_name),
    GROUP_BY(with_name.job_name),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X33

Map. Sources: job_runs, a database table, read by the query slow_runs (no workbook Table holds it). Steps: none. Finals: slow_runs (run_id, duration_mins, over_by), loaded by the query slow_runs. Typed over: none. Refused: none. Left alone: nothing outside a Table.
Mark, a non-workbook source: the query reads `Sql.Database("dwh01", "ops")`, schema ops, item job_runs. I used the table it names, `<database>.job_runs`. Check that the server dwh01 and database ops are the `<database>` you fill in. Fill in: `<database>`.
`[status] <> "TEST"` keeps a null in M, so it is `(status <> 'TEST' OR status IS NULL)`.

```sql
SELECT run_id, duration_mins,
  duration_mins - 20 AS over_by
FROM <database>.job_runs
WHERE duration_mins >= 20 AND (status <> 'TEST' OR status IS NULL)
```

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, any_of, at_least, is_null,
                              not_equals, statement)
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins - 20, "over_by")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(at_least(job_runs.duration_mins, 20),
          any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X34

Map. Sources: job_runs, jobs. Steps: query runs_with_team (connection only, but team_totals reads it), a CTE. Finals: team_totals (team, total_mins, longest), loaded by the query team_totals; nothing reads it. Typed over: none. Refused: none. Left alone: nothing outside a Table. Fill in: `<database>`.
The NestedJoin and ExpandTableColumn of job_runs with jobs, LeftOuter, is a LEFT JOIN on job_id that adds team; Table.Group is GROUP BY with SUM and MAX.

```sql
WITH runs_with_team AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT team, SUM(duration_mins) AS total_mins, MAX(duration_mins) AS longest
FROM runs_with_team
GROUP BY team
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals,
                              max_of, statement, sum_of)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

runs_with_team = derived("runs_with_team", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt, AS(jobs.team, "team")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
))
s = statement(
    SELECT(runs_with_team.team,
           AS(sum_of(runs_with_team.duration_mins), "total_mins"),
           AS(max_of(runs_with_team.duration_mins), "longest")),
    FROM(runs_with_team),
    GROUP_BY(runs_with_team.team),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X35

Map. Sources: job_runs, scheduler_runs. Steps: none. Finals: recent (run_id, dt), loaded by the query recent; nothing reads it. Typed over: none. Fill in: `<database>`.
- Table.Combine is UNION ALL; Table.Sort then FirstN 4 is ORDER BY run_id DESC LIMIT 4. I put the union in a subquery so the ORDER BY and LIMIT apply to all of it.
- Refused and left out: the query rates (connection only, nothing reads it), as it reads `Web.Contents("https://rates.example.com/today.json")`, a web source. I did not convert it.

```sql
SELECT run_id, dt
FROM (
  SELECT run_id, dt FROM <database>.job_runs
  UNION ALL
  SELECT run_id, dt FROM <database>.scheduler_runs
) u
ORDER BY run_id DESC
LIMIT 4
```

```python
from sqlglot_composer import (FROM, LIMIT, ORDER_BY, SELECT, UNION_ALL, derived, descending,
                              statement)
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

u = derived("u", UNION_ALL(
    statement(SELECT(job_runs.run_id, job_runs.dt),
              FROM(job_runs, reads_all_partitions=True)),  # a workbook's query reads every row
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt),
              FROM(scheduler_runs, reads_all_partitions=True)),
))
s = statement(
    SELECT(u.run_id, u.dt),
    FROM(u),
    ORDER_BY(descending(u.run_id)),
    LIMIT(4),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ (a stacked Statement inside a Derived table is the line to look at). Rows tied on run_id come in no set order.

## X36

Map. Sources: run_alerts, job_runs. Steps: none. Finals: job_runs (run_id, status, alerts), and severity_by_day (dt, high, low), loaded by the query severity_by_day. Nothing reads either. job_runs also has a typed status that its COUNTIFS does not match on, so it is not a summary. Typed over: none. Refused: none. Left alone: nothing outside a Table. Fill in: `<database>`.
- alerts: COUNTIFS over another Table is a LEFT JOIN to run_alerts counted by run_id, with COALESCE(.., 0).
- Mark, Table.Pivot: the pivot's columns are now fixed to the values in the sample, high and low. Each is `SUM(CASE WHEN severity = .. THEN 1 END)`, NULL where none, as M leaves it.
- A blank status (run 98) is not read by a formula.

```sql
SELECT r.run_id, r.status,
  COALESCE(a.total, 0) AS alerts
FROM <database>.job_runs r
LEFT JOIN (SELECT run_id, COUNT(*) AS total
           FROM <database>.run_alerts
           GROUP BY run_id) a ON r.run_id = a.run_id
```

```sql
SELECT dt,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
GROUP BY dt
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, fill_null, statement)
from references.<database>__job_runs import job_runs
from references.<database>__run_alerts import run_alerts

per_run = derived("a", statement(
    SELECT(run_alerts.run_id, AS(count_rows(), "total")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's formulas read every row
    GROUP_BY(run_alerts.run_id),
))
job_runs_final = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(fill_null(per_run.total, 0), "alerts")),
    FROM(job_runs, reads_all_partitions=True),
    LEFT_JOIN(per_run, ON=equals(per_run.run_id, job_runs.run_id)),
)

severity_by_day = statement(
    SELECT(run_alerts.dt,
           AS(count_rows(where=equals(run_alerts.severity, "high")), "high"),
           AS(count_rows(where=equals(run_alerts.severity, "low")), "low")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(run_alerts.dt),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ: the Toolbox's count gives 0 where the Hive above gives NULL for a day with no alert of a severity (none in the sample).

## X37

Map. Sources: Owners. Steps: none. Finals: Owners (Job No, Team Name, Owner, Day, Is Ana); nothing reads it. Typed over: none. Refused: none. Left alone: nothing outside a Table.
Names: `Job No` is `<job_no>`, `Team Name` is `<team_name>`, `Is Ana` is `<is_ana>`; Owner, Day and the Table Owners are plain names and stay. Fill in: `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.
Mark, blank: the web rows have a blank Owner, which Is Ana reads. Excel reads it as "", Hive as NULL, so it is `COALESCE(Owner, '')`. The Owner column itself is left as it is.

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
    FROM(Owners, reads_all_partitions=True),  # a workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`, in the Python too; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X38

Map. Sources: job_runs, jobs. Steps: none. Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost); nothing reads it. Keys row: job_runs, run_id.
Typed over a formula: retry_cost where run_id is 102 (1), matched on the Keys column run_id. Refused: none. Left alone: nothing outside a Table. Fill in: `<database>`.
- region: XLOOKUP is a LEFT JOIN to jobs on job_id. region_mins: SUMIFS over its own Table is `SUM(duration_mins) OVER (PARTITION BY region)` with COALESCE(.., 0). As it reads region, a calculated column, the join is a step inside.
- Mark, blank: run 98 has a blank avg_retry_secs, which retry_cost reads, so it is `COALESCE(avg_retry_secs, 0)`. SUMIFS skips a blank, so duration_mins is not wrapped.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.region,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.region), 0) AS region_mins,
  CASE WHEN r.run_id = 102 THEN 1
       ELSE (COALESCE(r.avg_retry_secs, 0) + r.duration_mins) * 2 END AS retry_cost
FROM (
  SELECT t.run_id, t.job_id, t.status, t.duration_mins, t.avg_retry_secs,
    j.region AS region
  FROM <database>.job_runs t
  LEFT JOIN <database>.jobs j ON t.job_id = j.job_id
) r
```

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, derived, equals, fill_null,
                              first_match, statement, sum_of, window)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

r = derived("r", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, AS(jobs.region, "region")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formulas read every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
))
by_region = window(PARTITION_BY=r.region)
s = statement(
    SELECT(r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.region,
           AS(fill_null(sum_of(r.duration_mins, over=by_region), 0), "region_mins"),
           AS(first_match([(equals(r.run_id, 102), 1)],
                          otherwise=(fill_null(r.avg_retry_secs, 0) + r.duration_mins) * 2),
              "retry_cost")),
    FROM(r),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ (the Toolbox may warn that jobs' job_id is not declared a Key).

## X39

Map. Sources: job_runs, jobs. Steps: none. Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise), the query ok_runs with its formula columns; nothing reads it (it reads only itself). Typed over: none. Left alone: nothing outside a Table. Fill in: `<database>`.
- job_name: XLOOKUP is a LEFT JOIN to jobs on job_id.
- share: SUMIFS over its own Table is `SUM(duration_mins) OVER (PARTITION BY job_id)`, with COALESCE(.., 0).
- Refused: noise, `RAND()`: `NULL AS noise`.
- The window is worked out after the join, so it assumes job_id is one row in jobs, as in the sample.

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT o.run_id, o.job_id, o.duration_mins,
  j.job_name AS job_name,
  o.duration_mins / COALESCE(SUM(o.duration_mins) OVER (PARTITION BY o.job_id), 0) AS share,
  NULL AS noise
FROM ok_runs o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, WHERE, derived, equals,
                              fill_null, statement, sum_of, window)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

ok_runs = derived("ok_runs", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
))
by_job = window(PARTITION_BY=ok_runs.job_id)
s = statement(
    SELECT(ok_runs.run_id, ok_runs.job_id, ok_runs.duration_mins,
           AS(jobs.job_name, "job_name"),
           AS(ok_runs.duration_mins / fill_null(sum_of(ok_runs.duration_mins, over=by_job), 0),
              "share")),
    # noise: refused (RAND), NULL in the Hive
    FROM(ok_runs),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, ok_runs.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X40

Map. Sources: jobs, run_alerts, Runs (its typed columns Run, Job, Mins). Steps: Runs, as it has formulas (Team, Cost) that Teams and run_alerts read. Finals: Teams (Team, Total Cost), a summary of Runs (its only typed column, Team, is what SUMIFS matches on), and run_alerts (alert_id, run_id, severity, dt, Run Mins). Parameters is none as a Table; its row rate is used as its value, 2. Typed over: none. Refused: none.
Left alone: the PivotTable on sheet Pivot (from Runs, rows Team, sum of Cost).
Names: `Total Cost` is `<total_cost>`, `Run Mins` is `<run_mins>`; Run, Job, Mins, Team, Cost are plain and stay. Fill in: `<database>`, `<total_cost>`, `<run_mins>`.
Every team in Teams has runs, so SUM needs no COALESCE. Move the rate into Parameters if you keep it in one place.

```sql
WITH Runs AS (
  SELECT r.Run, r.Job, r.Mins,
    j.team AS Team,
    r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT Team, SUM(Cost) AS <total_cost>
FROM Runs
GROUP BY Team
```

```sql
WITH Runs AS (
  SELECT r.Run, r.Job, r.Mins,
    j.team AS Team,
    r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt,
  Runs.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN Runs ON a.run_id = Runs.Run
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals,
                              statement, sum_of)
from references.<database>__jobs import jobs
from references.<database>__run_alerts import run_alerts
from references.<database>__Runs import Runs

runs_step = derived("runs_step", statement(
    SELECT(Runs.Run, Runs.Job, Runs.Mins,
           AS(jobs.team, "Team"),
           AS(Runs.Mins * 2, "Cost")),  # rate = Parameters row rate, 2
    FROM(Runs, reads_all_partitions=True),  # a workbook's formulas read every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, Runs.Job), reads_all_partitions=True),
))

teams = statement(
    SELECT(runs_step.Team, AS(sum_of(runs_step.Cost), "<total_cost>")),
    FROM(runs_step),
    GROUP_BY(runs_step.Team),
)

run_alerts_final = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(runs_step.Mins, "<run_mins>")),
    FROM(run_alerts, reads_all_partitions=True),
    LEFT_JOIN(runs_step, ON=equals(runs_step.Run, run_alerts.run_id)),
)
```

Take out of the workbook what you don't want converted; fill in each `<...>`, in the Python too; run `project.convert` on the Hive. Its checked code wins where the two differ.

## X46

Map
- Sources: job_runs (read for job_id, duration_mins), jobs (read for job_id, job_name, team).
- Steps: none.
- Finals: jobs (job_id, job_name, team, shortest, runs, busiest).
- Formulas: shortest is MINIFS over job_runs, runs is COUNTIF over job_runs, so each is a LEFT JOIN of a grouped sub-query with COALESCE(.., 0), as Excel gives 0 where nothing matches (job 4 has no runs). busiest is RANK.EQ over the Table's own runs column, so `RANK() OVER (ORDER BY runs DESC)`.
- Marks: no blank in a column these formulas read (the blank avg_retry_secs and status are not read). Typed over: none. Refusals: none. Left alone: the Steps, Parameters and Keys sheets. Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team,
  COALESCE(m.shortest, 0) AS shortest,
  COALESCE(m.runs, 0) AS runs,
  RANK() OVER (ORDER BY COALESCE(m.runs, 0) DESC) AS busiest
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, MIN(duration_mins) AS shortest, COUNT(*) AS runs
  FROM <database>.job_runs
  GROUP BY job_id
) m ON j.job_id = m.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              descending, equals, fill_null, min_of, rank, statement, window)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

per_job = derived("per_job", statement(
    SELECT(job_runs.job_id, AS(min_of(job_runs.duration_mins), "shortest"),
           AS(count_rows(), "runs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formula reads every row
    GROUP_BY(job_runs.job_id),
))
filled = derived("filled", statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(fill_null(per_job.shortest, 0), "shortest"),
           AS(fill_null(per_job.runs, 0), "runs")),
    FROM(jobs, reads_all_partitions=True),
    LEFT_JOIN(per_job, ON=equals(per_job.job_id, jobs.job_id)),
))
s = statement(
    SELECT(filled.job_id, filled.job_name, filled.team, filled.shortest, filled.runs,
           AS(rank(over=window(ORDER_BY=descending(filled.runs))), "busiest")),
    FROM(filled),
)
```

## X47

Map
- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg).
- Formulas: cheapest_first is RANK.EQ with 1 as third argument, so ASC. region_total is SUMIF over its own Table: a window sum partitioned by region, with COALESCE(.., 0). region_avg is AVERAGEIF: a window AVG, left NULL.
- Marks: no blank in the sample. Typed over: none. Refusals: none. Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

```python
from sqlglot_composer import AS, FROM, SELECT, average_of, rank, statement, sum_of, window
from references.ops__region_budgets import region_budgets

per_region = window(PARTITION_BY=region_budgets.region)
s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(rank(over=window(ORDER_BY=region_budgets.budget_cents)), "cheapest_first"),
           AS(sum_of(region_budgets.budget_cents, over=per_region), "region_total"),
           AS(average_of(region_budgets.budget_cents, over=per_region), "region_avg")),
    FROM(region_budgets, reads_all_partitions=True),
)
```
The COALESCE(.., 0) around region_total is in the Hive; a sum of a column with no blanks is never NULL, so the Toolbox code leaves it out.

## X48

Map
- Sources: job_runs, jobs, run_alerts.
- Steps: none (nothing reads either query).
- Finals: Table quiet_runs (run_id, job_id, status) and Table slow_regions (region, avg_mins, fastest).
- quiet_runs: a LeftAnti NestedJoin, so a LEFT JOIN with `WHERE a.run_id IS NULL`, job_runs' columns only. slow_regions: an Inner join, a GROUP BY region, and the SelectRows after the Group as HAVING, repeating the aggregate.
- Marks: none to add. Refusals: none. Left alone: no chart, PivotTable or cell outside a Table. Fill in: `<database>`.

quiet_runs
```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

slow_regions
```sql
SELECT j.region, AVG(r.duration_mins) AS avg_mins, MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

```python
from sqlglot_composer import (ANTI_JOIN, AS, FROM, GROUP_BY, HAVING, JOIN, SELECT, at_least,
                              average_of, equals, min_of, statement)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

quiet_runs = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    ANTI_JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id),
              reads_all_partitions=True),
)

slow_regions = statement(
    SELECT(jobs.region, AS(average_of(job_runs.duration_mins), "avg_mins"),
           AS(min_of(job_runs.duration_mins), "fastest")),
    FROM(job_runs, reads_all_partitions=True),
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
    GROUP_BY(jobs.region),
    HAVING(at_least(average_of(job_runs.duration_mins), 20)),
)
```
(GROUP_BY is imported above too: add it to the import line, `GROUP_BY` is used by slow_regions.)

## X49

Map
- Sources: job_runs, jobs (read by nothing here, but a source of the workbook), run_alerts, scheduler_runs, job_owners. Only the ones a query reads are used below: job_runs, run_alerts, scheduler_runs, jobs, job_owners.
- Steps: none.
- Finals: Table alert_status (alert_id, severity, status), Table run_check (run_id, status, scheduled_run), Table teams (team).
- alert_status: RightOuter join of run_alerts to job_runs, so LEFT JOIN with the two tables swapped (job_runs first). run_check: FullOuter, FULL OUTER JOIN, the expanded column renamed with AS. teams: Table.Distinct of a Table.Combine, so UNION.
- Marks: no formula, so no blank mark. Refusals: none. Fill in: `<database>`.

alert_status
```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
```

run_check
```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

teams
```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

```python
from sqlglot_composer import (AS, FROM, FULL_JOIN, LEFT_JOIN, SELECT, UNION, equals, statement)
from references.ops__job_owners import job_owners
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts
from references.ops__scheduler_runs import scheduler_runs

alert_status = statement(
    SELECT(run_alerts.alert_id, run_alerts.severity, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    # a run repeats for each of its alerts, as the workbook's join does
    LEFT_JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id),
              many_matches=True, reads_all_partitions=True),
)

run_check = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(scheduler_runs.run_id, "scheduled_run")),
    FROM(job_runs, reads_all_partitions=True),
    FULL_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id),
              reads_all_partitions=True),
)

teams = UNION(
    statement(SELECT(jobs.team), FROM(jobs, reads_all_partitions=True)),
    statement(SELECT(job_owners.team), FROM(job_owners, reads_all_partitions=True)),
)
```

## X50

Map
- Sources: job_owners (job_id, owner), jobs (job_id, job_name).
- Steps: none (nothing reads the query or the Table owners).
- Finals: Table owners (job_id, owner, job_name, newest_first): the query's rows (SelectColumns then Table.Distinct, so SELECT DISTINCT) plus its two formula columns.
- job_name is an XLOOKUP, a LEFT JOIN of jobs, then jobs.job_name. newest_first is RANK.EQ over the Table's own job_id: `RANK() OVER (ORDER BY job_id DESC)`, over the distinct rows, so the distinct rows are a CTE first.
- Marks: owner is blank for job 4 but no formula reads owner. Refusals: none. Fill in: `<database>`.

```sql
WITH owners AS (
  SELECT DISTINCT job_id, owner
  FROM <database>.job_owners
)
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM owners o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```
This joins on jobs.job_id with no Keys row for jobs: it assumes one row per job_id, as the sample has.

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, SELECT_DISTINCT, derived,
                              descending, equals, rank, statement, window)
from references.ops__job_owners import job_owners
from references.ops__jobs import jobs

owners = derived("owners", statement(
    SELECT_DISTINCT(job_owners.job_id, job_owners.owner),
    FROM(job_owners, reads_all_partitions=True),  # a workbook's query reads every row
))
s = statement(
    SELECT(owners.job_id, owners.owner, jobs.job_name,
           AS(rank(over=window(ORDER_BY=descending(owners.job_id))), "newest_first")),
    FROM(owners),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, owners.job_id), reads_all_partitions=True),
)
```

## X59

Map
- Sources: jobs (job_id, job_name), job_runs, run_alerts (alert_id, run_id, severity, dt).
- Steps: none.
- Finals: jobs (job_id, job_name, long_runs, failed_mins, not_test) and run_alerts (alert_id, run_id, severity, dt, alerts_so_far).
- jobs: each COUNTIFS or SUMIFS over job_runs is a LEFT JOIN of a grouped sub-query with COALESCE(.., 0). ">=20": `duration_mins >= 20`. "f*": `LOWER(status) LIKE 'f%'`. "<>TEST": `(status <> 'TEST' OR status IS NULL)`, as Excel counts a blank there.
- Marks: job_runs.status has a blank (run 98), but it is read only inside a -IFS form, which skips a blank, so no COALESCE around it. run_alerts: alerts_so_far is a running count over its own Table, ties included as Excel's (run 97 and 101 repeat): COUNT(*) with a RANGE window.
- Refusals: none. Fill in: `<database>`.

jobs
```sql
SELECT j.job_id, j.job_name,
  COALESCE(l.long_runs, 0) AS long_runs,
  COALESCE(f.failed_mins, 0) AS failed_mins,
  COALESCE(n.not_test, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS long_runs
  FROM <database>.job_runs
  WHERE duration_mins >= 20
  GROUP BY job_id
) l ON j.job_id = l.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS failed_mins
  FROM <database>.job_runs
  WHERE LOWER(status) LIKE 'f%'
  GROUP BY job_id
) f ON j.job_id = f.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS not_test
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) n ON j.job_id = n.job_id
```

run_alerts
```sql
SELECT alert_id, run_id, severity, dt,
  COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, any_of, at_least,
                              count_rows, derived, equals, fill_null, is_null, not_equals,
                              starts_with, statement, sum_of, window)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

long_runs = derived("long_runs", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "long_runs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formula reads every row
    WHERE(at_least(job_runs.duration_mins, 20)),
    GROUP_BY(job_runs.job_id),
))
failed = derived("failed", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "failed_mins")),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(any_of(starts_with(job_runs.status, "f"), starts_with(job_runs.status, "F"))),
    GROUP_BY(job_runs.job_id),
))
not_test = derived("not_test", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "not_test")),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
    GROUP_BY(job_runs.job_id),
))
jobs_final = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(fill_null(long_runs.long_runs, 0), "long_runs"),
           AS(fill_null(failed.failed_mins, 0), "failed_mins"),
           AS(fill_null(not_test.not_test, 0), "not_test")),
    FROM(jobs, reads_all_partitions=True),
    LEFT_JOIN(long_runs, ON=equals(long_runs.job_id, jobs.job_id)),
    LEFT_JOIN(failed, ON=equals(failed.job_id, jobs.job_id)),
    LEFT_JOIN(not_test, ON=equals(not_test.job_id, jobs.job_id)),
)

# rows=(None, 0) counts row by row, so tied run_ids count 1, 2 where Excel counts 2, 2:
# the Hive above (RANGE) is the exact one, and project.convert's checked code wins.
alerts_final = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(count_rows(over=window(ORDER_BY=run_alerts.run_id, rows=(None, 0))),
              "alerts_so_far")),
    FROM(run_alerts, reads_all_partitions=True),
)
```

## X60

Map
- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region), and `region_budgets (Total Row)`.
- share: the row over the whole column's SUM, `SUM(..) OVER ()`. above_avg: the row compared with AVERAGE of the column, `AVG(..) OVER ()`. rank_in_region: COUNTIFS(.., "<"&..)+1 is `RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC)`.
- Total Row: job_id SUBTOTAL(103) is a COUNT, budget_cents SUBTOTAL(101) an AVG. The "Total" label is left out, the other columns have no total. It is not a summary Table, so it has a query of its own.
- Marks: no blank in the sample. Typed over: none. Refusals: none. Fill in: `<database>`.

region_budgets
```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

region_budgets (Total Row)
```sql
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

```python
from sqlglot_composer import (AS, FROM, SELECT, average_of, count_rows, is_not_null, rank,
                              statement, sum_of, window)
from references.ops__region_budgets import region_budgets

whole = window()
s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(region_budgets.budget_cents / sum_of(region_budgets.budget_cents, over=whole),
              "share"),
           # above_avg is a comparison with a window: left to project.convert on the Hive
           AS(rank(over=window(PARTITION_BY=region_budgets.region,
                               ORDER_BY=region_budgets.budget_cents)), "rank_in_region")),
    FROM(region_budgets, reads_all_partitions=True),
)

total_row = statement(
    SELECT(AS(count_rows(where=is_not_null(region_budgets.job_id)), "job_id"),
           AS(average_of(region_budgets.budget_cents), "budget_cents")),
    FROM(region_budgets, reads_all_partitions=True),
)
```

## X61

Map
- Sources: region_costs (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: by_region (region, total_cents, entries, priciest), a summary: its only typed column, region, is what its SUMIFS, COUNTIFS and MAXIFS match on, so a GROUP BY of region_costs.
- Total Row: SUBTOTAL(109) of total_cents and entries, SUBTOTAL(104) of priciest: SUMs and the MAX of MAXes, so no query of its own: the summary ends `GROUP BY region WITH ROLLUP`, which adds the total as one more row, its region NULL (a Subtotal row, in place of the label "Total").
- Marks: cost_cents has a blank (job 2, 20260924), but it is read inside -IFS forms, which skip a blank, so no wrap; the blank row still counts in entries, as COUNTIFS counts it. dt is held as text (20260911) but no formula reads it. Refusals: none. Fill in: `<database>`.

```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COUNT(*) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, count_rows, max_of, rollup,
                              statement, sum_of)
from references.ops__region_costs import region_costs

s = statement(
    SELECT(region_costs.region,
           AS(sum_of(region_costs.cost_cents), "total_cents"),
           AS(count_rows(), "entries"),
           AS(max_of(region_costs.cost_cents), "priciest")),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's formula reads every row
    GROUP_BY(rollup(region_costs.region)),  # the Total Row, as a Subtotal row
)
```

## X62

Map
- Sources: team_notes (team, note, written_on).
- Steps: none.
- Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short).
- week_of: written_on - WEEKDAY(written_on, 2) + 1, the Monday of the week, as week_start writes it. month_end: EOMONTH(d, 0), LAST_DAY. month_of: EOMONTH(d, -1)+1, the month's first day, as month_start writes it. months_in: DATEDIF(.., "m"). three_before: d - 3, DATE_SUB. who: PROPER, INITCAP. short: TEXTJOIN, CONCAT_WS, with LEFT as SUBSTR.
- Marks: no blank in the sample; written_on is a real date, not text like 20260911. Typed over: none. Refusals: none. Fill in: `<database>`.

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

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__team_notes import team_notes

# Only the columns these files' names can write are here. week_of, month_end, month_of,
# months_in, three_before, who and short use Hive functions: they come from
# project.convert on the Hive above (Hive functions are in Copilot file 10).
s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on),
    FROM(team_notes, reads_all_partitions=True),
)
```

## X63

Map
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs), scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded).
- no_retry: ISBLANK, `avg_retry_secs IS NULL`. quarters: INT, FLOOR. capped: MIN of one row's cells, LEAST. variance: VAR.S of the column, `VAR_SAMP(..) OVER ()`. weighted: SUMPRODUCT, `SUM(a * b) OVER ()`. scheduled_job: XLOOKUP, a LEFT JOIN of scheduler_runs, with its fourth argument -1 as COALESCE(.., -1). label: CONCATENATE, CONCAT. succeeded: ISNUMBER(SEARCH(..)), `INSTR(LOWER(status), LOWER('cess')) > 0`.
- Marks: blank. status has a blank (run 98) and succeeded reads it, so COALESCE(status, ''). avg_retry_secs has a blank too, but only ISBLANK reads it, so no wrap. The join to scheduler_runs on run_id assumes one row per run_id there (no Keys row), as the sample has.
- Refusals: none. Fill in: `<database>`.

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

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, statement,
                              sum_of, window)
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs,
           # no_retry, quarters, capped, variance and succeeded use Hive functions or a
           # comparison: left to project.convert on the Hive above
           AS(sum_of(job_runs.duration_mins * job_runs.job_id, over=window()), "weighted"),
           AS(fill_null(scheduler_runs.job_id, -1), "scheduled_job")),
    FROM(job_runs, reads_all_partitions=True),
    LEFT_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id),
              reads_all_partitions=True),
)
```

## X64

Map
- Sources: jobs (job_id, job_name, team, region), region_costs (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: Table picked_costs (job_id, cost_cents, region, size), Table costed_jobs (job_id, job_name, team, region), Table costs_filled (job_id, cost_cents, dt, day).
- picked_costs: `[cost_cents] <> null` is IS NOT NULL; List.Contains({1, 3}, ..) is IN (1, 3); Text.Upper is UPPER; the `if` is IF. costed_jobs: List.Contains(Costs[job_id], [job_id]) is a LEFT SEMI JOIN of region_costs; `not Text.StartsWith` is NOT (.. LIKE 'n%'), case kept as M keeps it. costs_filled: ReplaceValue null with 0 is COALESCE(cost_cents, 0); Text.End([dt], 2) is SUBSTR(dt, -2).
- Marks: dt is held as text (20260911) and the query reads it as text, so it is kept as it is. Refusals: none. Fill in: `<database>`.

picked_costs
```sql
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

costed_jobs
```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

costs_filled
```sql
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt, SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

```python
from sqlglot_composer import (AS, FROM, SELECT, SEMI_JOIN, WHERE, all_of, at_least, equals,
                              fill_null, if_else, is_in, is_not_null, statement)
from references.ops__jobs import jobs
from references.ops__region_costs import region_costs

picked_costs = statement(
    # UPPER(region) is a Hive function: left to project.convert on the Hive above
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region,
           AS(if_else(at_least(region_costs.cost_cents, 200), "big", "small"), "size")),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_not_null(region_costs.cost_cents), is_in(region_costs.job_id, [1, 3])),
)

# costed_jobs: the SEMI_JOIN is here; its NOT LIKE 'n%' has no name in these files, so it
# comes from project.convert on the Hive above.
costed_jobs = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs, reads_all_partitions=True),
    SEMI_JOIN(region_costs, ON=equals(region_costs.job_id, jobs.job_id),
              reads_all_partitions=True),
)

# costs_filled: day (SUBSTR(dt, -2)) is a Hive function, left to project.convert.
costs_filled = statement(
    SELECT(region_costs.job_id, AS(fill_null(region_costs.cost_cents, 0), "cost_cents"),
           region_costs.dt),
    FROM(region_costs, reads_all_partitions=True),
)
```

## X65

Map
- Sources: jobs, region_budgets, job_owners, scheduler_runs, job_runs.
- Steps: none.
- Finals: Table team_regions (team, region), Table budget_places (job_id, budget_cents, region, place), Table jobs_per_team (team, jobs), Table ran_as_scheduled (run_id, dt), Table run_measures (run_id, job_id, measure, amount).
- team_regions: two Table.Distinct tables, AddColumn then expand is a CROSS JOIN. The Table.Sort has no FirstN or index after it, so no ORDER BY: the order was dropped, as a Hive table holds no order. budget_places: Sort then AddIndexColumn(.., 1, 1) is ROW_NUMBER() OVER (ORDER BY budget_cents DESC). jobs_per_team: List.Count(List.Distinct(..)) is COUNT(DISTINCT job_id); job_id has no blank in the sample, so nothing is left out. ran_as_scheduled: an Inner NestedJoin on every column, its new column removed, in Table.Distinct, is INTERSECT. run_measures: Table.Unpivot is one SELECT per column, UNION ALL, each WHERE .. IS NOT NULL (as M drops a null: run 98 has no avg_retry_secs row).
- Refusals: none. Fill in: `<database>`.

team_regions
```sql
SELECT t.team, r.region
FROM (SELECT DISTINCT team FROM <database>.jobs) t
CROSS JOIN (SELECT DISTINCT region FROM <database>.jobs) r
```

budget_places
```sql
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

jobs_per_team
```sql
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

ran_as_scheduled
```sql
SELECT run_id, dt FROM <database>.scheduler_runs
INTERSECT
SELECT run_id, dt FROM <database>.job_runs
```

run_measures
```sql
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

```python
from sqlglot_composer import (AS, CROSS_JOIN, FROM, GROUP_BY, INTERSECT, SELECT,
                              SELECT_DISTINCT, UNION_ALL, WHERE, count_distinct, derived,
                              descending, is_not_null, row_number, statement)
from references.ops__job_owners import job_owners
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets
from references.ops__scheduler_runs import scheduler_runs

teams = derived("teams", statement(SELECT_DISTINCT(jobs.team),
                                   FROM(jobs, reads_all_partitions=True)))
regions = derived("regions", statement(SELECT_DISTINCT(jobs.region),
                                       FROM(jobs, reads_all_partitions=True)))
team_regions = statement(
    SELECT(teams.team, regions.region),
    FROM(teams),
    CROSS_JOIN(regions),
)

budget_places = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(row_number(ORDER_BY=descending(region_budgets.budget_cents)), "place")),
    FROM(region_budgets, reads_all_partitions=True),
)

jobs_per_team = statement(
    SELECT(job_owners.team, AS(count_distinct(job_owners.job_id), "jobs")),
    FROM(job_owners, reads_all_partitions=True),
    GROUP_BY(job_owners.team),
)

ran_as_scheduled = INTERSECT(
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt),
              FROM(scheduler_runs, reads_all_partitions=True)),
    statement(SELECT(job_runs.run_id, job_runs.dt),
              FROM(job_runs, reads_all_partitions=True)),
)

# the quoted labels are literal text: check them in project.convert's checked code
run_measures = UNION_ALL(
    statement(SELECT(job_runs.run_id, job_runs.job_id, AS("duration_mins", "measure"),
                     AS(job_runs.duration_mins, "amount")),
              FROM(job_runs, reads_all_partitions=True),
              WHERE(is_not_null(job_runs.duration_mins))),
    statement(SELECT(job_runs.run_id, job_runs.job_id, AS("avg_retry_secs", "measure"),
                     AS(job_runs.avg_retry_secs, "amount")),
              FROM(job_runs, reads_all_partitions=True),
              WHERE(is_not_null(job_runs.avg_retry_secs))),
)
```

## X66

Map
- Sources: job_runs.
- Steps: none (nothing reads the query or the Table).
- Finals: Table ok_runs (run_id, job_id, duration_mins, dt, running, share), and `ok_runs (Total Row)`.
- The query: `[status] <> null` is IS NOT NULL, Text.StartsWith is LIKE 'SUCC%'. running: SUMIFS(.., job_id, [@job_id], dt, "<="&[@dt]) over its own Table, a running total by job in date order, ties included as Excel's: a RANGE window, COALESCE(.., 0). share: duration_mins over the SUM of the column, `SUM(..) OVER ()`.
- Total Row: only duration_mins has a total, SUBTOTAL(109), a SUM; the label "Total" is left out. It is not a summary Table, so it has a query of its own, reading the Table's rows as a CTE.
- Marks: status has a blank in the sample, but only the query reads it (IS NOT NULL, no wrap). dt is an ordinary date here. Refusals: none. Fill in: `<database>`.

ok_runs
```sql
SELECT run_id, job_id, duration_mins, dt,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

ok_runs (Total Row)
```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT SUM(duration_mins) AS duration_mins
FROM ok_runs
```

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, is_not_null, starts_with, statement,
                              sum_of, window)
from references.ops__job_runs import job_runs

# rows=(None, 0) counts row by row, so two rows with the same dt for a job differ from
# Excel's "<=": the Hive above (RANGE) is the exact one, and project.convert's checked code wins.
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(sum_of(job_runs.duration_mins,
                     over=window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt,
                                 rows=(None, 0))), "running"),
           AS(job_runs.duration_mins / sum_of(job_runs.duration_mins, over=window()), "share")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_not_null(job_runs.status), starts_with(job_runs.status, "SUCC")),
)

total_row = statement(
    SELECT(AS(sum_of(job_runs.duration_mins), "duration_mins")),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(is_not_null(job_runs.status), starts_with(job_runs.status, "SUCC")),
)
```

## X69

Map
- Sources: region_costs (job_id, cost_cents, region, dt), jobs, region_budgets.
- Steps: Table region_costs, with its formula columns job_name, budget, over_budget and running_cost, since Table job_totals and the query late_costs read it. It is a CTE inside each final that reads it, never a block alone.
- Finals: job_totals (job_id, total_cents, over_count), a summary: its only typed column, job_id, is what its SUMIFS and COUNTIFS match on, so a GROUP BY of region_costs. Its Total Row adds up SUMs only (109 and 109), so no query of its own: the summary ends `GROUP BY job_id WITH ROLLUP`, which adds the total as one more row, its job_id NULL (a Subtotal row, in place of the label "Total"). And Table late_costs (job_id, dt, running_cost).
- region_costs formulas: job_name and budget are XLOOKUPs, LEFT JOINs of jobs and region_budgets (one row per job_id assumed, as the sample has; no Keys row). over_budget compares cost_cents with the budget. running_cost is a running SUMIFS by job and date, ties included as Excel's: a RANGE window, COALESCE(.., 0). job_totals: total_cents is SUMIFS, SUM with COALESCE(.., 0); over_count is COUNTIFS(.., over_budget, TRUE), a COUNT of the rows where over_budget holds.
- Marks: blank. cost_cents has a blank (job 2, 20260924) and over_budget reads it, so COALESCE(cost_cents, 0); running_cost and total_cents read it inside a -IFS form, which skips a blank, so no wrap there. The date is held as text (20260911): the window orders by it converted to a date; the dt column itself is passed on as it is.
- Refusals: none. Fill in: `<database>`.

job_totals
```sql
WITH region_costs AS (
  SELECT c.job_id, c.cost_cents, c.region, c.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(c.cost_cents) OVER (PARTITION BY c.job_id
      ORDER BY CONCAT(SUBSTR(c.dt, 1, 4), '-', SUBSTR(c.dt, 5, 2), '-', SUBSTR(c.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs c
  LEFT JOIN <database>.jobs j ON c.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON c.job_id = b.job_id
)
SELECT job_id,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COUNT(CASE WHEN over_budget = TRUE THEN 1 END) AS over_count
FROM region_costs
GROUP BY job_id WITH ROLLUP
```

late_costs
```sql
WITH region_costs AS (
  SELECT c.job_id, c.cost_cents, c.region, c.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(c.cost_cents) OVER (PARTITION BY c.job_id
      ORDER BY CONCAT(SUBSTR(c.dt, 1, 4), '-', SUBSTR(c.dt, 5, 2), '-', SUBSTR(c.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs c
  LEFT JOIN <database>.jobs j ON c.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON c.job_id = b.job_id
)
SELECT job_id, dt, running_cost
FROM region_costs
WHERE running_cost > 1500
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, count_rows,
                              derived, equals, fill_null, if_else, more_than, rollup,
                              statement, sum_of, window)
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets
from references.ops__region_costs import region_costs

# the step: Table region_costs with its formula columns
# (the date held as text is ordered as it is; rows=(None, 0) counts row by row, so equal
# dates for a job differ from Excel's "<=": the Hive above (RANGE) is the exact one)
costs_step = derived("costs_step", statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region, region_costs.dt,
           jobs.job_name, AS(region_budgets.budget_cents, "budget"),
           AS(if_else(more_than(fill_null(region_costs.cost_cents, 0),
                                region_budgets.budget_cents), True, False), "over_budget"),
           AS(sum_of(region_costs.cost_cents,
                     over=window(PARTITION_BY=region_costs.job_id, ORDER_BY=region_costs.dt,
                                 rows=(None, 0))), "running_cost")),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's formula reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, region_costs.job_id), reads_all_partitions=True),
    LEFT_JOIN(region_budgets, ON=equals(region_budgets.job_id, region_costs.job_id),
              reads_all_partitions=True),
))

job_totals = statement(
    SELECT(costs_step.job_id, AS(sum_of(costs_step.cost_cents), "total_cents"),
           AS(count_rows(where=equals(costs_step.over_budget, True)), "over_count")),
    FROM(costs_step),
    GROUP_BY(rollup(costs_step.job_id)),  # the Total Row, as a Subtotal row
)

late_costs = statement(
    SELECT(costs_step.job_id, costs_step.dt, costs_step.running_cost),
    FROM(costs_step),
    WHERE(more_than(costs_step.running_cost, 1500)),
)
```

## X70

Map
- Sources: jobs (job_id, job_name), job_owners (job_id, owner), job_runs.
- Steps: query staffed (connection-only, but query owner_load reads it) and query owner_load (query busiest_owner reads it). A query and the Table it loads are two things: the Table owner_load is read by nothing.
- Finals: Table owner_load (owner, total_mins, runs, avg_mins), `owner_load (Total Row)`, and Table busiest_owner (owner, total_mins, runs). Each final holds the CTEs it reads.
- staffed: Table.Distinct of (job_id, owner), an Inner join with jobs, `[owner] <> null` as IS NOT NULL. owner_load: a LeftOuter join of staffed to job_runs, a GROUP BY owner, Table.RowCount(_) as COUNT(*) (a staffed job with no run counts as one row, as M does). avg_mins is a formula on the Table: total_mins / runs. busiest_owner: Table.Sort then FirstN(1) is ORDER BY runs DESC LIMIT 1.
- Total Row: only runs has a total, SUBTOTAL(109), a SUM; the label "Total" is left out. owner_load's own query ends in a GROUP BY but is not a summary Table (its columns are not typed to be matched), so the Total Row has a query of its own.
- Marks: owner is blank for job 4, and the query drops it. duration_mins has no blank. Refusals: none. Fill in: `<database>`.

owner_load
```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
    ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs, total_mins / runs AS avg_mins
FROM owner_load
```

owner_load (Total Row)
```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
    ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT SUM(runs) AS runs
FROM owner_load
```

busiest_owner
```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
    ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs
FROM owner_load
ORDER BY runs DESC
LIMIT 1
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, JOIN, LEFT_JOIN, LIMIT, ORDER_BY, SELECT,
                              SELECT_DISTINCT, WHERE, count_rows, derived, descending,
                              equals, is_not_null, statement, sum_of)
from references.ops__job_owners import job_owners
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

owners = derived("owners", statement(
    SELECT_DISTINCT(job_owners.job_id, job_owners.owner),
    FROM(job_owners, reads_all_partitions=True),  # a workbook's query reads every row
))
staffed = derived("staffed", statement(
    SELECT(jobs.job_id, jobs.job_name, owners.owner),
    FROM(jobs, reads_all_partitions=True),
    JOIN(owners, ON=equals(owners.job_id, jobs.job_id)),
    WHERE(is_not_null(owners.owner)),
))
owner_load = derived("owner_load", statement(
    SELECT(staffed.owner, AS(sum_of(job_runs.duration_mins), "total_mins"),
           AS(count_rows(), "runs")),
    FROM(staffed),
    LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, staffed.job_id), many_matches=True,
              reads_all_partitions=True),  # a staffed job has many runs, as the query's join does
    GROUP_BY(staffed.owner),
))

owner_load_final = statement(
    SELECT(owner_load.owner, owner_load.total_mins, owner_load.runs,
           AS(owner_load.total_mins / owner_load.runs, "avg_mins")),
    FROM(owner_load),
)
owner_load_total_row = statement(
    SELECT(AS(sum_of(owner_load.runs), "runs")),
    FROM(owner_load),
)
busiest_owner = statement(
    SELECT(owner_load.owner, owner_load.total_mins, owner_load.runs),
    FROM(owner_load),
    ORDER_BY(descending(owner_load.runs)),
    LIMIT(1),
)
```

## X73

Map
- Sources: region_budgets (job_id, budget_cents, region), jobs (job_id, job_name).
- Steps: query eu_budgets, since query eu_count reads it (a CTE inside each final that reads it). The Table eu_budgets, its query's rows plus the formula column dollars, is read by nothing, so it is a final.
- Finals: Table eu_budgets (job_id, budget_cents, region, job_name, dollars) and Table eu_count (region, jobs, total_cents).
- The query: SelectRows `[region] = "eu"` is WHERE region = 'eu'; an Inner NestedJoin with jobs, expanding only job_name, is JOIN. dollars is budget_cents / 100. eu_count: Table.Group by region, Table.RowCount(_) as COUNT(*), List.Sum as SUM.
- Marks: no blank in the sample (the join assumes one row per job_id in jobs, as the sample has). Refusals: none. Fill in: `<database>`.

eu_budgets
```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT job_id, budget_cents, region, job_name, budget_cents / 100 AS dollars
FROM eu_budgets
```

eu_count
```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT region, COUNT(*) AS jobs, SUM(budget_cents) AS total_cents
FROM eu_budgets
GROUP BY region
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, JOIN, SELECT, WHERE, count_rows, derived,
                              equals, statement, sum_of)
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets

eu_budgets = derived("eu_budgets", statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           jobs.job_name),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's query reads every row
    JOIN(jobs, ON=equals(jobs.job_id, region_budgets.job_id), reads_all_partitions=True),
    WHERE(equals(region_budgets.region, "eu")),
))

eu_budgets_final = statement(
    SELECT(eu_budgets.job_id, eu_budgets.budget_cents, eu_budgets.region, eu_budgets.job_name,
           AS(eu_budgets.budget_cents / 100, "dollars")),
    FROM(eu_budgets),
)

eu_count = statement(
    SELECT(eu_budgets.region, AS(count_rows(), "jobs"),
           AS(sum_of(eu_budgets.budget_cents), "total_cents")),
    FROM(eu_budgets),
    GROUP_BY(eu_budgets.region),
)
```

## X74

Map
- Sources: job_runs (run_id, job_id, status, ...), and run_alerts (alert_id, run_id, severity, dt).
- Steps: Table run_alerts, with its formula columns status, job_id and alerts_so_far, since Table by_status and the query late_alerts read it. It is a CTE inside each final that reads it.
- Finals: by_status (status, alerts), a summary: its only typed column, status, is what its COUNTIFS matches on, so a GROUP BY of run_alerts. And Table late_alerts (alert_id, run_id, alerts_so_far).
- run_alerts formulas: status and job_id are XLOOKUPs, so a LEFT JOIN of job_runs (one row per run_id assumed, as the sample has; no Keys row), then job_runs.status and job_runs.job_id. alerts_so_far is a running COUNTIFS over its own Table, ties included as Excel's (runs 101 and 103 repeat): COUNT(*) with a RANGE window. late_alerts: SelectRows alerts_so_far > 5, SelectColumns.
- Marks: blank. job_runs.status has a blank (run 98), and the status formula reads that column, so COALESCE(.., ''). The sample's alerts do not reach that run. by_status lists only FAILED and SUCCESS as typed; the GROUP BY gives one row per status present, which is the same two in the sample.
- Refusals: none. Fill in: `<database>`.

by_status
```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(r.status, '') AS status,
    r.job_id AS job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT status, COUNT(*) AS alerts
FROM run_alerts
GROUP BY status
```

late_alerts
```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(r.status, '') AS status,
    r.job_id AS job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM run_alerts
WHERE alerts_so_far > 5
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, count_rows,
                              derived, equals, fill_null, more_than, statement, window)
from references.ops__job_runs import job_runs
from references.ops__run_alerts import run_alerts

# rows=(None, 0) counts row by row, so tied run_ids count 1, 2 where Excel counts 2, 2:
# the Hive above (RANGE) is the exact one, and project.convert's checked code wins.
alerts_step = derived("alerts_step", statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(fill_null(job_runs.status, ""), "status"),
           AS(job_runs.job_id, "job_id"),
           AS(count_rows(over=window(ORDER_BY=run_alerts.run_id, rows=(None, 0))),
              "alerts_so_far")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's formula reads every row
    LEFT_JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id),
              reads_all_partitions=True),
))

by_status = statement(
    SELECT(alerts_step.status, AS(count_rows(), "alerts")),
    FROM(alerts_step),
    GROUP_BY(alerts_step.status),
)

late_alerts = statement(
    SELECT(alerts_step.alert_id, alerts_step.run_id, alerts_step.alerts_so_far),
    FROM(alerts_step),
    WHERE(more_than(alerts_step.alerts_so_far, 5)),
)
```

## X77

Map
- Sources: run_alerts (alert_id, run_id, severity, dt).
- Steps: query high_alerts, since query high_per_day reads it (a CTE inside each final that reads it). The Table high_alerts, its query's rows plus the formula column late_run, is read by nothing, so it is a final.
- Finals: Table high_alerts (alert_id, run_id, dt, late_run) and Table high_per_day (dt, alerts).
- The query: `[severity] = "high"` is WHERE severity = 'high', then SelectColumns. late_run is run_id > 100. high_per_day: Table.Group by dt, Table.RowCount(_) as COUNT(*).
- Marks: no blank in the sample. Refusals: none. Fill in: `<database>`.

high_alerts
```sql
WITH high_alerts AS (
  SELECT alert_id, run_id, dt
  FROM <database>.run_alerts
  WHERE severity = 'high'
)
SELECT alert_id, run_id, dt, run_id > 100 AS late_run
FROM high_alerts
```

high_per_day
```sql
WITH high_alerts AS (
  SELECT alert_id, run_id, dt
  FROM <database>.run_alerts
  WHERE severity = 'high'
)
SELECT dt, COUNT(*) AS alerts
FROM high_alerts
GROUP BY dt
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived, equals,
                              if_else, more_than, statement)
from references.ops__run_alerts import run_alerts

high_alerts = derived("high_alerts", statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.dt),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(equals(run_alerts.severity, "high")),
))

high_alerts_final = statement(
    SELECT(high_alerts.alert_id, high_alerts.run_id, high_alerts.dt,
           AS(if_else(more_than(high_alerts.run_id, 100), True, False), "late_run")),
    FROM(high_alerts),
)

high_per_day = statement(
    SELECT(high_alerts.dt, AS(count_rows(), "alerts")),
    FROM(high_alerts),
    GROUP_BY(high_alerts.dt),
)
```

## X78

Map
- Sources: region_costs (job_id, cost_cents, region, dt).
- Steps: query known_costs, since query cost_per_job reads it (a CTE inside each final that reads it). The Table known_costs, its query's rows plus the formula column dollars, is read by nothing, so it is a final.
- Finals: Table known_costs (job_id, cost_cents, dt, dollars), `known_costs (Total Row)`, and Table cost_per_job (job_id, total_cents).
- The query: `[cost_cents] <> null` is IS NOT NULL, so the blank-cost row (job 2, 20260924) is dropped; then SelectColumns. dollars is cost_cents / 100. cost_per_job: Table.Group by job_id, List.Sum as SUM.
- Total Row: only cost_cents has a total, SUBTOTAL(109), a SUM; the label "Total" is left out. known_costs is not a summary Table, so the Total Row has a query of its own, reading the Table's rows as a CTE.
- Marks: dt is held as text (20260911) but no formula or query reads it as a date, so it is kept as it is. Refusals: none. Fill in: `<database>`.

known_costs
```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT job_id, cost_cents, dt, cost_cents / 100 AS dollars
FROM known_costs
```

known_costs (Total Row)
```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT SUM(cost_cents) AS cost_cents
FROM known_costs
```

cost_per_job
```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT job_id, SUM(cost_cents) AS total_cents
FROM known_costs
GROUP BY job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, derived, is_not_null,
                              statement, sum_of)
from references.ops__region_costs import region_costs

known_costs = derived("known_costs", statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.dt),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_not_null(region_costs.cost_cents)),
))

known_costs_final = statement(
    SELECT(known_costs.job_id, known_costs.cost_cents, known_costs.dt,
           AS(known_costs.cost_cents / 100, "dollars")),
    FROM(known_costs),
)

known_costs_total_row = statement(
    SELECT(AS(sum_of(known_costs.cost_cents), "cost_cents")),
    FROM(known_costs),
)

cost_per_job = statement(
    SELECT(known_costs.job_id, AS(sum_of(known_costs.cost_cents), "total_cents")),
    FROM(known_costs),
    GROUP_BY(known_costs.job_id),
)
```
