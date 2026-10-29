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
