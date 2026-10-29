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
