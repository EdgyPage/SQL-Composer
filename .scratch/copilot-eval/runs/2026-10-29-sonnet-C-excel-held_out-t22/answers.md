date: 2026-10-29
arm: C
model: sonnet
files: 423bc80

## X21

Map. Sources: region_budgets (job_id, budget_cents, region). Steps: none. Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin). Parameters and Keys hold no rows, so they are none.
Typed over a formula: none. Marks: none, no blank in a column a formula reads. Refused: none. Left alone: the Steps sheet (nothing to convert). Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets
```

Toolbox code (replace `<database>` in the import with your database's name):

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__region_budgets import region_budgets

s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(region_budgets.budget_cents / 100, "budget_dollars"),
           AS(region_budgets.budget_cents * 1.1, "with_margin")),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X22

Map. Sources: jobs (job_id, job_name, team). Steps: none. Finals: jobs (job_id, job_name, team, is_finance, ratio).
Typed over: none. Marks: `IFERROR(a / b, 0)` is `COALESCE(a / b, 0)`, as a divide by 0 is NULL in Hive (job 2 gives 0, as in Excel). No blanks in the columns the formulas read. Refused: none. Fill in: `<database>`.

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
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X23

Map. Sources: job_runs (run_id, status, avg_retry_secs). Steps: none. Finals: job_runs (run_id, status, avg_retry_secs, label, risky).
Typed over: none. Marks: blank. Run 98 has a blank status and a blank avg_retry_secs, which Hive reads as NULL and Excel as "" or 0, so both are wrapped (`COALESCE(status, '')`, `COALESCE(avg_retry_secs, 0)`). Without the wrap, `risky` would be NULL for that row where Excel gives FALSE. Refused: none. Fill in: `<database>`.

```sql
SELECT run_id, status, avg_retry_secs,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label,
  (COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs
```

```python
from sqlglot_composer import (AS, FROM, SELECT, any_of, equals, fill_null, first_match,
                              if_else, more_than, statement)
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.status, job_runs.avg_retry_secs,
           AS(first_match([(equals(fill_null(job_runs.status, ""), "SUCCESS"), "ok"),
                           (equals(fill_null(job_runs.status, ""), "FAILED"), "bad")],
                          otherwise="other"), "label"),
           AS(if_else(any_of(equals(fill_null(job_runs.status, ""), "FAILED"),
                             more_than(fill_null(job_runs.avg_retry_secs, 0), 5)),
                      True, False), "risky")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ (I am least sure of the TRUE/FALSE in `risky`).

## X24

Map. Sources: team_notes (team, note, written_on). Steps: none. Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars).
Typed over: none. Marks: none (no blanks; every note holds a space, so FIND finds one). Refused: none. Fill in: `<database>`. Check that written_on is held as a date or as 'yyyy-MM-dd' text, which MONTH reads either way.

```sql
SELECT team, note, written_on,
  SUBSTR(note, 1, INSTR(note, ' ') - 1) AS first_word,
  UPPER(team) AS shout,
  MONTH(written_on) AS month,
  ROUND(LENGTH(note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes
```

Files 03 to 05 name no Toolbox function for SUBSTR, INSTR, UPPER, MONTH, ROUND or LENGTH. Those are Hive functions, which file 10 covers (load it in a new chat). So the Toolbox code here holds only the plain columns, and `project.convert` on the Hive above gives the four calculated ones.

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__team_notes import team_notes

s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on),
    # first_word, shout, month, tens_of_chars: from project.convert on the Hive (or file 10)
    FROM(team_notes, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X25

Map. Sources: Costs (Job, `<cost_cents>`, Region, `<day_key>`), Budgets (Job, Budget, Region). Steps: none. Finals: Costs (Job, `<cost_cents>`, Region, `<day_key>`, Day) and Budgets (Job, Budget, Region, Dollars).
Typed over: none. Marks: the date is held as text. `Day Key` (20260911) is turned into 'yyyy-MM-dd' text with CONCAT and SUBSTR, so Day is a text date, not a date value. No blank is read by a formula (Cost (cents) is blank on row 29, but no formula reads it). Names: `Cost (cents)` is `<cost_cents>` and `Day Key` is `<day_key>`; fill in what your database calls them. Refused: none. Fill in: `<database>`, `<cost_cents>`, `<day_key>`.

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

Toolbox code for Budgets. For Costs, CONCAT and SUBSTR are Hive functions (file 10), so take them from `project.convert` on the Hive above.

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__Budgets import Budgets

s = statement(
    SELECT(Budgets.Job, Budgets.Budget, Budgets.Region,
           AS(Budgets.Budget / 100, "Dollars")),
    FROM(Budgets, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X26

Map. Sources: run_alerts (alert_id, run_id, severity), job_runs (run_id, job_id, status, duration_mins). Steps: none. Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins). job_runs has no formulas and only run_alerts reads it, so it is a source only.
Typed over: none. Marks: no blank is looked up. job_runs has a blank status on run 98, but no alert points at run 98. If one did, Excel's VLOOKUP would show 0 where Hive gives NULL. `VLOOKUP(.., job_runs, 3, FALSE)` is column 3 of job_runs, status. AVERAGEIFS is left NULL where nothing matches. avg_mins averages over the job_id that the XLOOKUP found, and over every job_runs row of that job (status is not filtered). There is no Keys row, so I assumed run_id is unique in job_runs (it is in the sample). Refused: none. Fill in: `<database>`.

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
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity,
           job_runs.job_id, job_runs.status, per_job.avg_mins),
    FROM(run_alerts, reads_all_partitions=True),
    LEFT_JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id),
              reads_all_partitions=True),
    LEFT_JOIN(per_job, ON=equals(per_job.job_id, job_runs.job_id)),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X27

Map. Sources: jobs (job_id, job_name, team, region). Steps: none. Finals: by_team (team, jobs_in_team, last_job_id, last_job_name). by_team's only typed column, team, is what its COUNTIFS and MAXIFS match on, so it is a summary: a GROUP BY of jobs.
Typed over: none. Marks: none. Every team in jobs gets a row, which are the three typed ones (data, finance, web). Refused: none. Fill in: `<database>`. last_job_name looks up jobs by job_id, which I assume is unique (there is no Keys row, and it is in the sample).

```sql
WITH g AS (
  SELECT team,
    COALESCE(COUNT(*), 0) AS jobs_in_team,
    COALESCE(MAX(job_id), 0) AS last_job_id
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
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(jobs.team),
))
j = AS(jobs, "j")
s = statement(
    SELECT(g.team, g.jobs_in_team, g.last_job_id, j.job_name),
    FROM(g),
    LEFT_JOIN(j, ON=equals(j.job_id, g.last_job_id), reads_all_partitions=True),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X28

Map. Sources: jobs (job_id, job_name), job_runs (run_id, job_id, status, duration_mins). Steps: none. Finals: jobs (job_id, job_name, ok_mins).
Typed over: ok_mins where job_id is 3 (99). Keys holds jobs, job_id, so the row is matched on job_id. Marks: none. Run 98 has a blank status, but SUMIFS skips it in its condition, so it is not wrapped. SUMIFS over another Table is a LEFT JOIN of a grouped copy, with COALESCE(.., 0) as Excel gives 0 where nothing matches. Refused: none. Fill in: `<database>`.

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

s_ok = derived("s", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(first_match([(equals(jobs.job_id, 3), 99)],
                          otherwise=fill_null(s_ok.total, 0)), "ok_mins")),
    FROM(jobs, reads_all_partitions=True),
    LEFT_JOIN(s_ok, ON=equals(s_ok.job_id, jobs.job_id)),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X29

Map. Sources: region_budgets (job_id, budget_cents, region). Steps: none. Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer). Parameters holds cents_per_dollar = 100, which XLOOKUP reads, so I use its value, 100. Parameters is not a table of its own.
Typed over: in_dollars is 5 on the row where job_id is 3. There is no Keys row for region_budgets, so I matched every typed column of that row (job_id 3, budget_cents 350, region 'us').
Refused: `pointer`, INDIRECT("A"&ROW()). INDIRECT is refused, and ROW() hangs on the order of the sheet's rows. It is `NULL AS pointer`.
Fill in: `<database>`.

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
    # pointer (NULL, refused) is left out here; project.convert on the Hive keeps it as NULL
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. The 100 now sits in the SQL, so if the rate changes, change it there.

## X30

Map. Sources: scheduler_runs (run_id, job_id, dt). Steps: none. Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter).
Typed over: none. Marks: none; `RIGHT(dt, 2)` is `SUBSTR(dt, -2)`, which assumes dt is held as text 'yyyy-MM-dd' (if it were a real date, Excel's RIGHT would take the last two digits of its serial number).
Refused: `prev_run` (OFFSET, and it hangs on the order of the rows) and `jitter` (RANDBETWEEN): `NULL AS prev_run`, `NULL AS jitter`.
Left alone: the bar chart on sheet Summary, and the PivotTable on sheet Pivot (from scheduler_runs). Fill in: `<database>`.

```sql
SELECT run_id, job_id, dt,
  SUBSTR(dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs
```

SUBSTR is a Hive function that file 10 covers, so the Toolbox code holds only the plain columns, and `project.convert` on the Hive above gives day and the two NULL columns.

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__scheduler_runs import scheduler_runs

s = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    # day, prev_run, jitter: from project.convert on the Hive (or file 10)
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X31

Map. Sources: jobs (job_id, team). Steps: none. Finals: jobs (job_id, team, bump, tag, scaled, boosted).
Typed over: none. Marks: `boosted` uses the defined name boost, which is the cell Summary!B2 outside a Table, value 10. I use 10, and you should move it into Parameters.
Refused:
- `bump`: `[@bump]*2` reads its own column (circular). `NULL AS bump`.
- `tag`: `TAG(...)` is a defined name holding a LAMBDA. `NULL AS tag`.
- `scaled`: reads the cell Summary!D4, which is outside a Table and not a defined name. `NULL AS scaled`.
Left alone: the cells on sheet Summary (B2, D4). Fill in: `<database>`.

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
           AS(jobs.job_id * 10, "boosted")),  # 10 is boost, Summary!B2: move it into Parameters
    # bump, tag, scaled are refused (NULL); project.convert on the Hive keeps them as NULL
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X32

Map. Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), jobs (job_id, job_name, team, region). Steps: job_runs, because by_name reads its formula column job_name. Finals: by_name (job_name, runs), which is a summary, a GROUP BY of the job_runs step, as job_name is its only typed column and COUNTIFS matches on it. job_runs is read, so it is not a final.
Typed over: none. Marks: `VLOOKUP(.., jobs, 2, TRUE)` is an approximate match. I converted it exactly (a LEFT JOIN on job_id), and the result can differ if jobs isn't sorted or a job_id is missing. Run 98 has a blank status, which no formula reads. Refused: none. Fill in: `<database>`.

```sql
WITH job_runs AS (
  SELECT r.run_id, j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT job_name, COALESCE(COUNT(*), 0) AS runs
FROM job_runs
GROUP BY job_name
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, statement)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

runs_named = derived("runs_named", statement(
    SELECT(job_runs.run_id, jobs.job_name),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
))
s = statement(
    SELECT(runs_named.job_name, AS(count_rows(), "runs")),
    FROM(runs_named),
    GROUP_BY(runs_named.job_name),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X33

Map. Sources: none in the workbook. The query reads a database table, ops.job_runs. Steps: none. Finals: slow_runs (run_id, duration_mins, over_by), the Table that Power Query "slow_runs" loads.
Marks: the M reads Sql.Database("dwh01", "ops") and the item job_runs in schema ops. I used the table it names, `ops.job_runs`. Check that the server dwh01 and that ops is the database you mean (if not, change `ops` to your `<database>`). The `<>` keeps a null, so the filter is `(status <> 'TEST' OR status IS NULL)`. The query's rows are not filtered to the sample's dates.
Typed over: none. Refused: none. Fill in: `<database>` (if ops is not it).

```sql
SELECT run_id, duration_mins,
  duration_mins - 20 AS over_by
FROM ops.job_runs
WHERE duration_mins >= 20 AND (status <> 'TEST' OR status IS NULL)
```

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, any_of, at_least, is_null, not_equals,
                              statement)
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins - 20, "over_by")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(at_least(job_runs.duration_mins, 20),
          any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X34

Map. Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), jobs (job_id, job_name, team, region). Steps: query runs_with_team (connection only, but team_totals reads it, so it is a CTE and not left out). Finals: Table team_totals (team, total_mins, longest), loaded by query team_totals.
Typed over: none. Marks: none. The M's LeftOuter join is a LEFT JOIN. Web has no runs, so it has no row, as in the sample. No ORDER BY, as there is no sort in the query. Refused: none. Fill in: `<database>`.

```sql
WITH runs_with_team AS (
  SELECT r.duration_mins, j.team
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
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals, max_of,
                              statement, sum_of)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

runs_with_team = derived("runs_with_team", statement(
    SELECT(job_runs.duration_mins, jobs.team),
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

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X35

Map. Sources: job_runs (run_id, dt), scheduler_runs (run_id, dt). Steps: none. Finals: Table recent (run_id, dt), loaded by query recent.
Left out and named: query rates (connection only, nothing reads it). It reads Web.Contents("https://rates.example.com/today.json"), a web source, which is refused, so it is not converted.
Typed over: none. Marks: Table.Combine is UNION ALL (repeats kept, as in the sample, where 104 and 103 each show twice). Table.Sort then FirstN 4 is ORDER BY run_id DESC LIMIT 4, which is kept because of the LIMIT. Fill in: `<database>`.

```sql
WITH combined AS (
  SELECT run_id, dt FROM <database>.job_runs
  UNION ALL
  SELECT run_id, dt FROM <database>.scheduler_runs
)
SELECT run_id, dt
FROM combined
ORDER BY run_id DESC
LIMIT 4
```

```python
from sqlglot_composer import (FROM, LIMIT, ORDER_BY, SELECT, UNION_ALL, derived, descending,
                              statement)
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

combined = derived("combined", UNION_ALL(
    statement(SELECT(job_runs.run_id, job_runs.dt),
              FROM(job_runs, reads_all_partitions=True)),  # a workbook's query reads every row
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt),
              FROM(scheduler_runs, reads_all_partitions=True)),
))
s = statement(
    SELECT(combined.run_id, combined.dt),
    FROM(combined),
    ORDER_BY(descending(combined.run_id)),
    LIMIT(4),
)
```

If the Toolbox refuses a stacked Statement inside `derived`, use `project.convert` on the Hive. Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X36

Map. Sources: run_alerts (alert_id, run_id, severity, dt), job_runs (run_id, status). Steps: none. Finals: job_runs (run_id, status, alerts) and Table severity_by_day (dt, high, low), loaded by query severity_by_day. job_runs is not a summary, as status is typed too.
Typed over: none. Marks: `alerts` is a COUNTIFS over another Table, so a LEFT JOIN of run_alerts counted per run_id, with COALESCE(.., 0). Run 98 has a blank status, which no formula reads. The pivot's columns are now fixed: high and low, the values in the sample. A new severity would need a new column. As M leaves it, a day with none of a severity gives NULL. Refused: none. Fill in: `<database>`.

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
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(run_alerts.run_id),
))
job_runs_final = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(fill_null(per_run.total, 0), "alerts")),
    FROM(job_runs, reads_all_partitions=True),
    LEFT_JOIN(per_run, ON=equals(per_run.run_id, job_runs.run_id)),
)

# count_rows gives 0 where M's pivot gives NULL; the Hive above keeps NULL
severity_by_day = statement(
    SELECT(run_alerts.dt,
           AS(count_rows(where=equals(run_alerts.severity, "high")), "high"),
           AS(count_rows(where=equals(run_alerts.severity, "low")), "low")),
    FROM(run_alerts, reads_all_partitions=True),
    GROUP_BY(run_alerts.dt),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X37

Map. Sources: Owners (`<job_no>`, `<team_name>`, Owner, Day). Steps: none. Finals: Owners (`<job_no>`, `<team_name>`, Owner, Day, `<is_ana>`), all 56 rows, none filtered.
Names: `Job No` is `<job_no>`, `Team Name` is `<team_name>` and `Is Ana` is `<is_ana>`; fill in what your database calls them. Owner and Day are plain names and are kept.
Typed over: none. Marks: blank. Owner is blank on the web rows (job 4), and IF is not an -IFS form, so it is wrapped, `COALESCE(Owner, '')`. Refused: none. Fill in: `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

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
    FROM(Owners, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X38

Map. Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs), jobs (job_id, job_name, team, region). Steps: none. Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost).
Typed over: retry_cost is 1 on the row where run_id is 102. Keys holds job_runs, run_id, so it matches on run_id.
Marks: blank. avg_retry_secs is blank on run 98 and retry_cost reads it, so it is wrapped, `COALESCE(avg_retry_secs, 0)`. region is an XLOOKUP, a LEFT JOIN on jobs (I assume job_id is unique in jobs). region_mins is a SUMIFS over its own Table, so a window over each region, `PARTITION BY j.region` (written on the join's column, as Hive can't use the alias of the same SELECT), with COALESCE(.., 0). Refused: none. Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  j.region AS region,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.region), 0) AS region_mins,
  CASE WHEN r.run_id = 102 THEN 1
       ELSE (COALESCE(r.avg_retry_secs, 0) + r.duration_mins) * 2 END AS retry_cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, first_match,
                              statement, sum_of, window)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

each_region = window(PARTITION_BY=jobs.region)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs,
           AS(jobs.region, "region"),
           AS(fill_null(sum_of(job_runs.duration_mins, over=each_region), 0), "region_mins"),
           AS(first_match([(equals(job_runs.run_id, 102), 1)],
                          otherwise=(fill_null(job_runs.avg_retry_secs, 0)
                                     + job_runs.duration_mins) * 2), "retry_cost")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X39

Map. Sources: job_runs (run_id, job_id, status, duration_mins), jobs (job_id, job_name). Steps: none. Finals: Table ok_runs (run_id, job_id, duration_mins, job_name, share, noise): the rows of query ok_runs plus its formula columns. Nothing reads the Table, so it is a final, with the query's rows as its own query.
Typed over: none. Marks: the query keeps `status = 'SUCCESS'` (M's `=`, so a blank status is dropped). `share` is a SUMIFS over its own Table, so a window `PARTITION BY job_id` over the rows left after the WHERE, with COALESCE(.., 0). job_name is a LEFT JOIN on jobs. No blank is read by a formula.
Refused: `noise`, RAND(): `NULL AS noise`. Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  j.job_name AS job_name,
  r.duration_mins / COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id), 0) AS share,
  NULL AS noise
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
WHERE r.status = 'SUCCESS'
```

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, WHERE, equals, fill_null,
                              statement, sum_of, window)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

each_job = window(PARTITION_BY=job_runs.job_id)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins,
           AS(jobs.job_name, "job_name"),
           AS(job_runs.duration_mins
              / fill_null(sum_of(job_runs.duration_mins, over=each_job), 0), "share")),
    # noise (RAND, refused) is NULL: project.convert on the Hive keeps it
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
    WHERE(equals(job_runs.status, "SUCCESS")),
)
```

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X40

Map. Sources: Runs (Run, Job, Mins), jobs (job_id, job_name, team, region), run_alerts (alert_id, run_id, severity, dt). Steps: Runs, because Teams and run_alerts read its formula columns Team and Cost. Finals: Teams (Team, `<total_cost>`), a summary, a GROUP BY of the Runs step, as Team is its only typed column and its SUMIFS matches on it; and run_alerts (alert_id, run_id, severity, dt, `<run_mins>`). Runs is read, so it is not a final. Parameters holds rate = 2, which Cost's XLOOKUP reads, so I use its value, 2.
Names: `Total Cost` is `<total_cost>` and `Run Mins` is `<run_mins>`; fill in what your database calls them. Run, Job, Mins, Team and Cost are plain names and are kept.
Typed over: none. Marks: none (no blanks). Teams has a row for each team in Runs (data and finance, as typed). Assuming job_id is unique in jobs and Run in Runs (no Keys row; true in the sample). Refused: none.
Left alone: the PivotTable on sheet Pivot (from Runs). Fill in: `<database>`, `<total_cost>`, `<run_mins>`.

```sql
WITH Runs AS (
  SELECT r.Run, r.Job, r.Mins,
    j.team AS Team,
    r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT Team, COALESCE(SUM(Cost), 0) AS <total_cost>
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
  r.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN Runs r ON a.run_id = r.Run
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals,
                              fill_null, statement, sum_of)
from references.<database>__Runs import Runs
from references.<database>__jobs import jobs
from references.<database>__run_alerts import run_alerts

runs_step = derived("runs_step", statement(
    SELECT(Runs.Run, Runs.Job, Runs.Mins,
           AS(jobs.team, "Team"),
           AS(Runs.Mins * 2, "Cost")),  # 2 is rate, from Parameters
    FROM(Runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, Runs.Job), reads_all_partitions=True),
))

teams = statement(
    SELECT(runs_step.Team, AS(fill_null(sum_of(runs_step.Cost), 0), "<total_cost>")),
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

Take out of the workbook anything you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. The 2 now sits in the SQL, so if the rate changes in Parameters, change it there.

## X46

**Map**
- Sources: job_runs, jobs.
- Steps: none.
- Finals: jobs (job_id, job_name, team, shortest, runs, busiest).
- Typed over a formula: none. Marks: none (the blank in job_runs.avg_retry_secs and status is in no formula's column). Refusals: none.
- Fill in: `<database>`.

The three formulas read job_runs, another Table, so they are one grouped subquery joined on job_id, with COALESCE(.., 0) as Excel gives 0 where nothing matches. busiest is RANK.EQ over the runs column, descending.

```sql
SELECT j.job_id, j.job_name, j.team,
  COALESCE(s.shortest, 0) AS shortest,
  COALESCE(s.runs, 0) AS runs,
  RANK() OVER (ORDER BY COALESCE(s.runs, 0) DESC) AS busiest
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, MIN(duration_mins) AS shortest, COUNT(*) AS runs
           FROM <database>.job_runs
           GROUP BY job_id) s ON j.job_id = s.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              descending, equals, fill_null, min_of, rank, statement, window)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = derived("s", statement(
    SELECT(job_runs.job_id, AS(min_of(job_runs.duration_mins), "shortest"),
           AS(count_rows(), "runs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formula reads every row
    GROUP_BY(job_runs.job_id),
))
most_runs_first = window(ORDER_BY=descending(fill_null(s.runs, 0)))
jobs_s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(fill_null(s.shortest, 0), "shortest"),
           AS(fill_null(s.runs, 0), "runs"),
           AS(rank(over=most_runs_first), "busiest")),
    FROM(jobs),
    LEFT_JOIN(s, ON=equals(s.job_id, jobs.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X47

**Map**
- Sources: region_budgets. Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg).
- Typed over: none. Marks: none (no blank in the sample). Refusals: none. Fill in: `<database>`.

All three formulas read the Table's own rows, so they are windows: RANK.EQ with 1 is ASC; SUMIF is a SUM over the region (COALESCE(.., 0)); AVERAGEIF is AVG, left NULL.

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

```python
from sqlglot_composer import (AS, FROM, SELECT, average_of, fill_null, rank, statement,
                              sum_of, window)
from references.ops__region_budgets import region_budgets

cheapest_first = window(ORDER_BY=region_budgets.budget_cents)
in_region = window(PARTITION_BY=region_budgets.region)
s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(rank(over=cheapest_first), "cheapest_first"),
           AS(fill_null(sum_of(region_budgets.budget_cents, over=in_region), 0), "region_total"),
           AS(average_of(region_budgets.budget_cents, over=in_region), "region_avg")),
    FROM(region_budgets, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X48

**Map**
- Sources: job_runs, jobs, run_alerts. Steps: none.
- Finals: quiet_runs (run_id, job_id, status); slow_regions (region, avg_mins, fastest).
- Typed over: none. Marks: none. Refusals: none. Fill in: `<database>`.
- quiet_runs is a LeftAnti join: `LEFT JOIN .. WHERE a.run_id IS NULL`, job_runs' columns only. slow_regions is an Inner join, grouped, then a HAVING that repeats the aggregate.

```sql
-- quiet_runs
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

```sql
-- slow_regions
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
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    GROUP_BY(jobs.region),
    HAVING(at_least(average_of(job_runs.duration_mins), 20)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X49

**Map**
- Sources: job_runs, run_alerts, scheduler_runs, jobs, job_owners. Steps: none.
- Finals: alert_status (alert_id, severity, status); run_check (run_id, status, scheduled_run); teams (team).
- Typed over: none. Marks: none. Refusals: none. Fill in: `<database>`.
- alert_status is a RightOuter join: LEFT JOIN with the two tables swapped (every run kept). run_check is a FullOuter join, the second run_id expanded as scheduled_run. teams is Table.Distinct over Table.Combine: UNION.
- Order: no query sorts, and a Hive table holds no order, so none is written.

```sql
-- alert_status
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON a.run_id = r.run_id
```

```sql
-- run_check
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

```sql
-- teams
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

```python
from sqlglot_composer import (AS, FROM, FULL_JOIN, LEFT_JOIN, SELECT, UNION, equals, statement)
from references.ops__job_runs import job_runs
from references.ops__run_alerts import run_alerts
from references.ops__scheduler_runs import scheduler_runs
from references.ops__jobs import jobs
from references.ops__job_owners import job_owners

alert_status = statement(
    SELECT(run_alerts.alert_id, run_alerts.severity, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id),
              reads_all_partitions=True),
)

run_check = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(scheduler_runs.run_id, "scheduled_run")),
    FROM(job_runs, reads_all_partitions=True),
    FULL_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id),
              reads_all_partitions=True),
)

teams = UNION(
    statement(SELECT(jobs.team), FROM(jobs)),
    statement(SELECT(job_owners.team), FROM(job_owners, reads_all_partitions=True)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X50

**Map**
- Sources: job_owners, jobs. Steps: none (the query owners is read by nothing but its own Table).
- Finals: Table owners, i.e. its query's rows plus its formula columns (job_id, owner, job_name, newest_first).
- Typed over: none. Marks: none (owner has a blank, but no formula reads owner). Refusals: none. Fill in: `<database>`.
- The query is Table.Distinct without a column list: SELECT DISTINCT. job_name is the XLOOKUP: a LEFT JOIN on jobs; newest_first is RANK.EQ over the Table's own job_id, descending, over the distinct rows, so the query is a CTE under it.

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

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, SELECT_DISTINCT, derived,
                              descending, equals, rank, statement, window)
from references.ops__job_owners import job_owners
from references.ops__jobs import jobs

owners = derived("owners", statement(
    SELECT_DISTINCT(job_owners.job_id, job_owners.owner),
    FROM(job_owners, reads_all_partitions=True),  # a workbook's query reads every row
))
newest_first = window(ORDER_BY=descending(owners.job_id))
s = statement(
    SELECT(owners.job_id, owners.owner, jobs.job_name,
           AS(rank(over=newest_first), "newest_first")),
    FROM(owners),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, owners.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X59

**Map**
- Sources: job_runs, jobs, run_alerts. Steps: none.
- Finals: jobs (job_id, job_name, long_runs, failed_mins, not_test); run_alerts (alert_id, run_id, severity, dt, alerts_so_far).
- Typed over: none. Refusals: none. Fill in: `<database>`.
- Marks: job_runs.status has a blank, but it is read only inside COUNTIFS and SUMIFS, which skip a blank, so nothing is wrapped. "<>TEST" counts the blank row, as Excel does, so it is `(status <> 'TEST' OR status IS NULL)`. "f*" ignores case: `LOWER(status) LIKE 'f%'`.
- jobs reads another Table: one grouped subquery per formula, LEFT JOINed, COALESCE(.., 0). run_alerts reads its own Table: a running total, ties included (RANGE).

```sql
-- jobs
SELECT j.job_id, j.job_name,
  COALESCE(l.long_runs, 0) AS long_runs,
  COALESCE(f.failed_mins, 0) AS failed_mins,
  COALESCE(n.not_test, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, COUNT(*) AS long_runs
           FROM <database>.job_runs
           WHERE duration_mins >= 20
           GROUP BY job_id) l ON j.job_id = l.job_id
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS failed_mins
           FROM <database>.job_runs
           WHERE LOWER(status) LIKE 'f%'
           GROUP BY job_id) f ON j.job_id = f.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS not_test
           FROM <database>.job_runs
           WHERE (status <> 'TEST' OR status IS NULL)
           GROUP BY job_id) n ON j.job_id = n.job_id
```

```sql
-- run_alerts
SELECT alert_id, run_id, severity, dt,
  COUNT(*) OVER (ORDER BY run_id
                 RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, any_of, at_least,
                              count_rows, derived, equals, fill_null, is_null, not_equals,
                              starts_with, statement, sum_of, window)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

long_runs = derived("l", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "long_runs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formula reads every row
    WHERE(at_least(job_runs.duration_mins, 20)),
    GROUP_BY(job_runs.job_id),
))
failed = derived("f", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "failed_mins")),
    FROM(job_runs, reads_all_partitions=True),
    # Excel's "f*" ignores case, starts_with does not: this needs LOWER (file 10)
    WHERE(starts_with(job_runs.status, "F")),
    GROUP_BY(job_runs.job_id),
))
not_test = derived("n", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "not_test")),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
    GROUP_BY(job_runs.job_id),
))
jobs_s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(fill_null(long_runs.long_runs, 0), "long_runs"),
           AS(fill_null(failed.failed_mins, 0), "failed_mins"),
           AS(fill_null(not_test.not_test, 0), "not_test")),
    FROM(jobs),
    LEFT_JOIN(long_runs, ON=equals(long_runs.job_id, jobs.job_id)),
    LEFT_JOIN(failed, ON=equals(failed.job_id, jobs.job_id)),
    LEFT_JOIN(not_test, ON=equals(not_test.job_id, jobs.job_id)),
)

# rows=(None, 0) is a ROWS frame: Hive's RANGE above counts both rows of run 97 as 2,
# this counts them 1 then 2. project.convert's checked code wins; check the ties.
so_far = window(ORDER_BY=run_alerts.run_id, rows=(None, 0))
run_alerts_s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(count_rows(over=so_far), "alerts_so_far")),
    FROM(run_alerts, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X60

**Map**
- Sources: region_budgets. Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region) and `region_budgets (Total Row)` (job_id, budget_cents).
- Typed over: none. Marks: none (no blank in the sample). Refusals: none. Fill in: `<database>`.
- Whole-column SUM and AVERAGE are windows over (). COUNTIFS(.., "<"&[@budget_cents])+1 is a RANK, ascending, in the region. The Total Row (SUBTOTAL 103 a COUNT, 101 an AVG) is a query of its own, one row, with no label (the "Total" text and the empty cells are not converted). region_budgets is not a summary Table, so no ROLLUP.

```sql
-- region_budgets
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

```sql
-- region_budgets (Total Row)
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

```python
from sqlglot_composer import (AS, FROM, SELECT, average_of, count_rows, if_else, is_not_null,
                              more_than, rank, statement, sum_of, window)
from references.ops__region_budgets import region_budgets

whole = window()
in_region = window(PARTITION_BY=region_budgets.region, ORDER_BY=region_budgets.budget_cents)
region_budgets_s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(region_budgets.budget_cents / sum_of(region_budgets.budget_cents, over=whole),
              "share"),
           # a TRUE/FALSE column; the Hive above gives NULL, not FALSE, for a NULL budget
           AS(if_else(more_than(region_budgets.budget_cents,
                                average_of(region_budgets.budget_cents, over=whole)),
                      True, False), "above_avg"),
           AS(rank(over=in_region), "rank_in_region")),
    FROM(region_budgets, reads_all_partitions=True),
)

total_row = statement(
    SELECT(AS(count_rows(where=is_not_null(region_budgets.job_id)), "job_id"),
           AS(average_of(region_budgets.budget_cents), "budget_cents")),
    FROM(region_budgets, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X61

**Map**
- Sources: region_costs. Steps: none.
- Finals: by_region (region, total_cents, entries, priciest). by_region is a summary: its only typed column, region, is what its SUMIFS, COUNTIFS and MAXIFS match on, so it is a GROUP BY of region_costs. region_costs itself is read by by_region, so it is a source, not a final.
- Total Row: SUM of SUMs, SUM of COUNTs and MAX of MAXes, so no query of its own: the query ends `GROUP BY region WITH ROLLUP`, which adds the total as one more row, its region NULL (a Subtotal row).
- Typed over: none. Refusals: none. Fill in: `<database>`.
- Marks: cost_cents has a blank (job 2 on 20260924), but it is read only by SUMIFS and MAXIFS, which skip a blank, so nothing is wrapped; COUNTIFS counts that row, as Excel does. dt is held as text (20260911) but no formula reads it, so it is not converted.

```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COUNT(*) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, count_rows, fill_null, max_of,
                              rollup, statement, sum_of)
from references.ops__region_costs import region_costs

by_region = statement(
    SELECT(region_costs.region,
           AS(fill_null(sum_of(region_costs.cost_cents), 0), "total_cents"),
           AS(count_rows(), "entries"),
           AS(fill_null(max_of(region_costs.cost_cents), 0), "priciest")),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's formula reads every row
    GROUP_BY(rollup(region_costs.region)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X62

**Map**
- Sources: team_notes. Steps: none.
- Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short).
- Typed over: none. Marks: none (no blank; written_on is ISO text-looking dates, not 20260911, so no conversion). Refusals: none. Fill in: `<database>`.
- week_of and month_of are written as week_start and month_start write them. EDATE is not used.

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
from sqlglot_composer import AS, FROM, SELECT, month_start, statement, week_start
from references.ops__team_notes import team_notes

s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on,
           AS(week_start(team_notes.written_on), "week_of"),
           # month_end (LAST_DAY), months_in (MONTHS_BETWEEN), three_before (DATE_SUB),
           # who (INITCAP) and short (CONCAT_WS, SUBSTR) are Hive functions that files
           # 03, 04 and 05 do not hold: load file 10 in a new chat for them, or let
           # project.convert write them from the Hive above, in this column order
           AS(month_start(team_notes.written_on), "month_of")),
    FROM(team_notes, reads_all_partitions=True),
)
```

Only week_of and month_of are in the code above, so it is not a full Toolbox version of the Hive; the Hive is the whole conversion. Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X63

**Map**
- Sources: job_runs, scheduler_runs. Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded).
- Typed over: none. Refusals: none. Fill in: `<database>`.
- Marks: **blank**: status has a blank (run 98) and SEARCH reads it, so it is wrapped, COALESCE(status, ''). avg_retry_secs has a blank too, but ISBLANK reads it, so it is not wrapped (`IS NULL`).
- XLOOKUP's fourth argument, -1, is COALESCE(.., -1) over a LEFT JOIN. VAR.S and SUMPRODUCT over a whole column are windows over ().

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
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, if_else,
                              is_null, statement, sum_of, window)
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs,
           AS(if_else(is_null(job_runs.avg_retry_secs), True, False), "no_retry"),
           # quarters (FLOOR), capped (LEAST), variance (VAR_SAMP), label (CONCAT) and
           # succeeded (INSTR, LOWER) are Hive functions: file 10, in a new chat
           AS(sum_of(job_runs.duration_mins * job_runs.job_id, over=window()), "weighted"),
           AS(fill_null(scheduler_runs.job_id, -1), "scheduled_job")),
    FROM(job_runs, reads_all_partitions=True),
    LEFT_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id),
              reads_all_partitions=True),
)
```

The code leaves out five columns that need file 10; the Hive above is the whole conversion. Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X64

**Map**
- Sources: region_costs, jobs. Steps: none.
- Finals (three queries): picked_costs (job_id, cost_cents, region, size); costed_jobs (job_id, job_name, team, region); costs_filled (job_id, cost_cents, dt, day).
- Typed over: none. Refusals: none. Fill in: `<database>`.
- Marks: dt is held as text (20260911), but costs_filled only takes its last two characters as text (Text.End), so it is not turned into a date. M's `<> null` is `IS NOT NULL`. `List.Contains(Costs[job_id], [job_id])` is a LEFT SEMI JOIN, and `not` is NOT.

```sql
-- picked_costs
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

```sql
-- costed_jobs
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

```sql
-- costs_filled
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt, SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

```python
from sqlglot_composer import (AS, FROM, SELECT, SEMI_JOIN, WHERE, at_least, equals, fill_null,
                              if_else, is_in, is_not_null, statement)
from references.ops__jobs import jobs
from references.ops__region_costs import region_costs

picked_costs = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents,
           region_costs.region,  # UPPER(region): a Hive function, file 10
           AS(if_else(at_least(region_costs.cost_cents, 200), "big", "small"), "size")),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_not_null(region_costs.cost_cents), is_in(region_costs.job_id, [1, 3])),
)

costed_jobs = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
    SEMI_JOIN(region_costs, ON=equals(region_costs.job_id, jobs.job_id),
              reads_all_partitions=True),
    # NOT (job_name LIKE 'n%') has no function in files 03 to 05: file 10
)

costs_filled = statement(
    SELECT(region_costs.job_id, AS(fill_null(region_costs.cost_cents, 0), "cost_cents"),
           region_costs.dt),  # day: SUBSTR(dt, -2), a Hive function, file 10
    FROM(region_costs, reads_all_partitions=True),
)
```

The code is partial where a Hive function is needed (UPPER, NOT LIKE, SUBSTR); the Hive is the whole conversion. Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X65

**Map**
- Sources: jobs, region_budgets, job_owners, scheduler_runs, job_runs. Steps: none.
- Finals (five queries): team_regions (team, region); budget_places (job_id, budget_cents, region, place); jobs_per_team (team, jobs); ran_as_scheduled (run_id, dt); run_measures (run_id, job_id, measure, amount).
- Typed over: none. Marks: none. Refusals: none. Fill in: `<database>`.
- Order dropped: team_regions' Table.Sort and budget_places' Table.Sort have no FirstN, so there is no ORDER BY, as a Hive table holds no order (budget_places' sort is kept only as the ROW_NUMBER's order). jobs_per_team: COUNT(DISTINCT job_id) leaves out NULL where M counts it as a value; job_id has no blank in the sample.
- team_regions: the AddColumn of a table, expanded, is a CROSS JOIN. ran_as_scheduled: a join on every column, its new column removed, in Table.Distinct is INTERSECT. run_measures: one SELECT per unpivoted column, UNION ALL, each dropping a NULL.

```sql
-- team_regions
WITH teams AS (SELECT DISTINCT team FROM <database>.jobs),
regions AS (SELECT DISTINCT region FROM <database>.jobs)
SELECT t.team, r.region
FROM teams t
CROSS JOIN regions r
```

```sql
-- budget_places
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

```sql
-- jobs_per_team
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

```sql
-- ran_as_scheduled
SELECT run_id, dt FROM <database>.scheduler_runs
INTERSECT
SELECT run_id, dt FROM <database>.job_runs
```

```sql
-- run_measures
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

```python
from sqlglot_composer import (AS, CROSS_JOIN, FROM, GROUP_BY, INTERSECT, SELECT, SELECT_DISTINCT,
                              UNION_ALL, WHERE, count_distinct, derived, descending,
                              is_not_null, row_number, statement)
from references.ops__job_owners import job_owners
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets
from references.ops__scheduler_runs import scheduler_runs

teams = derived("teams", statement(SELECT_DISTINCT(jobs.team), FROM(jobs)))
regions = derived("regions", statement(SELECT_DISTINCT(jobs.region), FROM(jobs)))
team_regions = statement(
    SELECT(teams.team, regions.region),
    FROM(teams),
    CROSS_JOIN(regions),
)

budget_places = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(row_number(ORDER_BY=descending(region_budgets.budget_cents)), "place")),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's query reads every row
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

# the quoted names are text values, not columns: the Toolbox may refuse them
# as columns, so check this one with project.convert on the Hive
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

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X66

**Map**
- Sources: job_runs. Steps: none (the query ok_runs is read by nothing but its own Table).
- Finals: Table ok_runs, i.e. its query's rows plus its formulas (run_id, job_id, duration_mins, dt, running, share), and `ok_runs (Total Row)` (duration_mins).
- Typed over: none. Marks: none (status has a blank, but the filter is the query's, not a formula's; dt is ISO, so it compares in order as it is). Refusals: none. Fill in: `<database>`.
- running is a SUMIFS over the Table's own rows: a running total by job, ties included (RANGE), COALESCE(.., 0). share is a whole-column SUM, a window over (). The windows read the query's filtered rows, which is what WHERE gives them in the same SELECT. The Total Row is a query of its own (ok_runs is not a summary Table), one row, no label ("Total" and the empty cells are not converted).

```sql
-- ok_runs
SELECT run_id, job_id, duration_mins, dt,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt
           RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

```sql
-- ok_runs (Total Row)
SELECT SUM(duration_mins) AS duration_mins
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, fill_null, is_not_null, starts_with,
                              statement, sum_of, window)
from references.ops__job_runs import job_runs

# rows=(None, 0) is a ROWS frame; the Hive's RANGE counts two runs of one job on one
# day (101 and 104) together. project.convert's checked code wins; check those ties.
so_far = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt, rows=(None, 0))
ok_runs = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(fill_null(sum_of(job_runs.duration_mins, over=so_far), 0), "running"),
           AS(job_runs.duration_mins / sum_of(job_runs.duration_mins, over=window()), "share")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_not_null(job_runs.status), starts_with(job_runs.status, "SUCC")),
)

ok_runs_total = statement(
    SELECT(AS(sum_of(job_runs.duration_mins), "duration_mins")),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(is_not_null(job_runs.status), starts_with(job_runs.status, "SUCC")),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X69

**Map**
- Sources: region_costs (job_id, cost_cents, region, dt), jobs, region_budgets.
- Steps: Table region_costs (it adds job_name, budget, over_budget and running_cost, and job_totals and the query late_costs read it): a CTE in each final's query.
- Finals: job_totals (job_id, total_cents, over_count), a summary, since its only typed column, job_id, is what its SUMIFS and COUNTIFS match on; late_costs (job_id, dt, running_cost).
- Total Row of job_totals: SUM of SUMs and SUM of COUNTs, so no query of its own: `GROUP BY job_id WITH ROLLUP` adds it as one more row, its job_id NULL (a Subtotal row).
- Typed over: none. Refusals: none. Fill in: `<database>`.
- Marks: **blank**: cost_cents has a blank (job 2 on 20260924) and over_budget (`>`) reads it, so it is COALESCE(cost_cents, 0); running_cost and total_cents read it only in SUMIFS, which skips it. **dt is held as text** (20260911), so the running total orders by `CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2))`; the dt column itself is kept as the Table holds it. running_cost's `"<="&dt` is a running total, ties included. The XLOOKUPs are LEFT JOINs.

```sql
-- job_totals
WITH region_costs AS (
  SELECT c.job_id, c.cost_cents, c.region, c.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(c.cost_cents) OVER (
      PARTITION BY c.job_id
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

```sql
-- late_costs
WITH region_costs AS (
  SELECT c.job_id, c.cost_cents, c.region, c.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(c.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(c.cost_cents) OVER (
      PARTITION BY c.job_id
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

# rows=(None, 0) is a ROWS frame, the Hive's RANGE counts equal dates together; no job has
# two rows on one dt in the sample. dt is text: its order here is the same as the date's.
so_far = window(PARTITION_BY=region_costs.job_id, ORDER_BY=region_costs.dt, rows=(None, 0))
rc = derived("region_costs", statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region, region_costs.dt,
           jobs.job_name,
           AS(region_budgets.budget_cents, "budget"),
           AS(if_else(more_than(fill_null(region_costs.cost_cents, 0),
                                region_budgets.budget_cents), True, False), "over_budget"),
           AS(fill_null(sum_of(region_costs.cost_cents, over=so_far), 0), "running_cost")),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's formula reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, region_costs.job_id)),
    LEFT_JOIN(region_budgets, ON=equals(region_budgets.job_id, region_costs.job_id)),
))

job_totals = statement(
    SELECT(rc.job_id,
           AS(fill_null(sum_of(rc.cost_cents), 0), "total_cents"),
           AS(count_rows(where=equals(rc.over_budget, True)), "over_count")),
    FROM(rc),
    GROUP_BY(rollup(rc.job_id)),
)

late_costs = statement(
    SELECT(rc.job_id, rc.dt, rc.running_cost),
    FROM(rc),
    WHERE(more_than(rc.running_cost, 1500)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X70

**Map**
- Sources: jobs, job_owners, job_runs.
- Steps: query staffed (connection only, but owner_load reads it) and query owner_load (busiest_owner reads it): CTEs in each final's query that reads them.
- Finals: Table owner_load, i.e. its query's rows plus avg_mins (owner, total_mins, runs, avg_mins); `owner_load (Total Row)` (runs); busiest_owner (owner, total_mins, runs). The Table owner_load is read by nothing (busiest_owner reads the query), so it is a final.
- Typed over: none. Marks: none (duration_mins has no blank). Refusals: none. Left out: no connection-only query is left unread. Fill in: `<database>`.
- Order: busiest_owner's sort has a LIMIT, so it keeps its ORDER BY. M's `<> null` is `IS NOT NULL`; Table.Distinct on SelectColumns is SELECT DISTINCT.
- The Total Row (SUBTOTAL 109 on runs) is a query of its own, one row, no label; owner_load is not a summary Table.

```sql
-- owner_load
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
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

```sql
-- owner_load (Total Row)
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
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

```sql
-- busiest_owner
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
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
                              SELECT_DISTINCT, WHERE, count_rows, derived, descending, equals,
                              is_not_null, statement, sum_of)
from references.ops__job_owners import job_owners
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

owners = derived("o", statement(
    SELECT_DISTINCT(job_owners.job_id, job_owners.owner),
    FROM(job_owners, reads_all_partitions=True),  # a workbook's query reads every row
))
staffed = derived("staffed", statement(
    SELECT(jobs.job_id, jobs.job_name, owners.owner),
    FROM(jobs),
    JOIN(owners, ON=equals(owners.job_id, jobs.job_id)),
    WHERE(is_not_null(owners.owner)),
))
owner_load = derived("owner_load", statement(
    SELECT(staffed.owner, AS(sum_of(job_runs.duration_mins), "total_mins"),
           AS(count_rows(), "runs")),
    FROM(staffed),
    LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, staffed.job_id),
              reads_all_partitions=True),
    GROUP_BY(staffed.owner),
))

owner_load_table = statement(
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

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X73

**Map**
- Sources: region_budgets, jobs.
- Steps: query eu_budgets (the query eu_count reads): a CTE in each final's query.
- Finals: Table eu_budgets, i.e. its query's rows plus dollars (job_id, budget_cents, region, job_name, dollars); eu_count (region, jobs, total_cents).
- Typed over: none. Marks: none. Refusals: none. Fill in: `<database>`.
- Table.SelectRows `[region] = "eu"` is `region = 'eu'`, case kept as M keeps it. The Inner NestedJoin then expand is a JOIN.

```sql
-- eu_budgets
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT job_id, budget_cents, region, job_name, budget_cents / 100 AS dollars
FROM eu_budgets
```

```sql
-- eu_count
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
    JOIN(jobs, ON=equals(jobs.job_id, region_budgets.job_id)),
    WHERE(equals(region_budgets.region, "eu")),
))

eu_budgets_table = statement(
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

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X74

**Map**
- Sources: job_runs, run_alerts (alert_id, run_id, severity, dt).
- Steps: Table run_alerts (it adds status, job_id and alerts_so_far, and by_status and the query late_alerts read it): a CTE in each final's query.
- Finals: by_status (status, alerts), a summary (its only typed column, status, is what its COUNTIFS matches on), so a GROUP BY of the step; late_alerts (alert_id, run_id, alerts_so_far).
- Typed over: none. Refusals: none. Fill in: `<database>`.
- Marks: **blank**: job_runs.status has a blank (run 98) and the XLOOKUP reads that column, so it is COALESCE(status, ''); no alert in the sample points to run 98. alerts_so_far is a running total over the Table's own run_id, ties included (RANGE).

```sql
-- by_status
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(r.status, '') AS status,
    r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id
                   RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT status, COUNT(*) AS alerts
FROM run_alerts
GROUP BY status
```

```sql
-- late_alerts
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(r.status, '') AS status,
    r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id
                   RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM run_alerts
WHERE alerts_so_far > 5
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, count_rows, derived,
                              equals, fill_null, more_than, statement, window)
from references.ops__job_runs import job_runs
from references.ops__run_alerts import run_alerts

# rows=(None, 0) is a ROWS frame; the Hive's RANGE counts equal run_ids together
# (97, 101, 103 repeat). project.convert's checked code wins; check those ties.
so_far = window(ORDER_BY=run_alerts.run_id, rows=(None, 0))
ra = derived("run_alerts", statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(fill_null(job_runs.status, ""), "status"), job_runs.job_id,
           AS(count_rows(over=so_far), "alerts_so_far")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's formula reads every row
    LEFT_JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id),
              reads_all_partitions=True),
))

by_status = statement(
    SELECT(ra.status, AS(count_rows(), "alerts")),
    FROM(ra),
    GROUP_BY(ra.status),
)

late_alerts = statement(
    SELECT(ra.alert_id, ra.run_id, ra.alerts_so_far),
    FROM(ra),
    WHERE(more_than(ra.alerts_so_far, 5)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X77

**Map**
- Sources: run_alerts.
- Steps: query high_alerts (the query high_per_day reads): a CTE in each final's query.
- Finals: Table high_alerts, i.e. its query's rows plus late_run (alert_id, run_id, dt, late_run); high_per_day (dt, alerts).
- Typed over: none. Marks: none. Refusals: none. Fill in: `<database>`.

```sql
-- high_alerts
WITH high_alerts AS (
  SELECT alert_id, run_id, dt
  FROM <database>.run_alerts
  WHERE severity = 'high'
)
SELECT alert_id, run_id, dt, run_id > 100 AS late_run
FROM high_alerts
```

```sql
-- high_per_day
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

high_alerts_table = statement(
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

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.

## X78

**Map**
- Sources: region_costs.
- Steps: query known_costs (the query cost_per_job reads): a CTE in each final's query.
- Finals: Table known_costs, i.e. its query's rows plus dollars (job_id, cost_cents, dt, dollars); `known_costs (Total Row)` (cost_cents); cost_per_job (job_id, total_cents).
- Typed over: none. Marks: none (cost_cents has a blank in region_costs, but the query drops it with `IS NOT NULL`, as M's `<> null` is). dt is held as text (20260911) but no formula reads it, so it is not converted. Refusals: none. Fill in: `<database>`.
- The Total Row (SUBTOTAL 109 on cost_cents) is a query of its own, one row, no label (known_costs is not a summary Table).

```sql
-- known_costs
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT job_id, cost_cents, dt, cost_cents / 100 AS dollars
FROM known_costs
```

```sql
-- known_costs (Total Row)
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT SUM(cost_cents) AS cost_cents
FROM known_costs
```

```sql
-- cost_per_job
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

known_costs_table = statement(
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

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive; its checked code wins where the two differ.
