date: 2026-10-29
arm: C
model: sonnet
files: fac0fd8

## X21

Map. Sources: region_budgets. Steps: none. Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin). Parameters and Keys hold nothing, so they are none. Typed over a formula: none. Marks: none, as the sample has no blank in a column a formula reads. Refusals: none. Left alone: nothing. Fill in: `<database>`.

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
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (here `<database>`, in the SQL and in the `references.<database>__region_budgets` import). Then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X22

Map. Sources: jobs. Steps: none. Finals: jobs (job_id, job_name, team, is_finance, ratio). Typed over a formula: none. Marks: none, as no blank is in a column a formula reads. IFERROR(a / b, 0) becomes COALESCE(a / b, 0), because Hive gives NULL for a divide by 0 (job 2 divides by 0 and gets 0, as in Excel). Refusals: none. Left alone: nothing. Fill in: `<database>`.

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

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X23

Map. Sources: job_runs. Steps: none. Finals: job_runs (run_id, status, avg_retry_secs, label, risky). Typed over a formula: none. Marks: blank. Run 98 has a blank status and a blank avg_retry_secs, and the formulas read both. Excel reads them as "" and 0, Hive as NULL, so I wrapped them: COALESCE(status, '') and COALESCE(avg_retry_secs, 0). Without that, risky would be NULL for run 98 where Excel gives FALSE. Refusals: none. Left alone: nothing. Fill in: `<database>`.

```sql
SELECT run_id, status, avg_retry_secs,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label,
  (COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs
```

```python
from sqlglot_composer import (AS, FROM, SELECT, any_of, equals, fill_null, if_else,
                              more_than, statement)
from references.<database>__job_runs import job_runs

status = fill_null(job_runs.status, "")  # blank: Excel reads it as ""
s = statement(
    SELECT(job_runs.run_id, job_runs.status, job_runs.avg_retry_secs,
           AS(if_else(equals(status, "SUCCESS"), "ok",
                      if_else(equals(status, "FAILED"), "bad", "other")), "label"),
           AS(if_else(any_of(equals(status, "FAILED"),
                             more_than(fill_null(job_runs.avg_retry_secs, 0), 5)),
                      True, False), "risky")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ. The SWITCH as nested if_else and the TRUE/FALSE column are the two places most likely to change.

## X24

Map. Sources: team_notes. Steps: none. Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars). Typed over a formula: none. Marks: none. No blank is in a column a formula reads. written_on is read as a date in ISO form, so MONTH is used as it is. Refusals: none. Left alone: nothing. Fill in: `<database>`.

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

# first_word, shout, month and tens_of_chars use Hive functions (SUBSTR, INSTR, UPPER,
# MONTH, LENGTH, ROUND). Those are in file 10, which isn't loaded, so I haven't made up names for them.
s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on),
    FROM(team_notes, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive, which will give the four function columns as checked code (file 10, in a new chat, covers Hive functions). Its checked code wins where the two differ.

## X25

Map. Sources: Costs, Budgets. Steps: none. Finals: two, each its own query.
- Costs (Job, `<cost_cents>`, Region, `<day_key>`, Day)
- Budgets (Job, Budget, Region, Dollars)

Names: Table and header names that are plain are kept (Costs, Budgets, Job, Region, Day, Budget, Dollars). `Cost (cents)` is `<cost_cents>` and `Day Key` is `<day_key>`. I haven't guessed any name.

Typed over a formula: none. Marks:
- The Day column is built from a date held as text (20260911), so it is rebuilt with SUBSTR. The date is held as text.
- `Cost (cents)` has a blank in the sample (the last row), but no formula reads it, so I left it as it is.

Refusals: none. Left alone: nothing. Fill in: `<database>`, `<cost_cents>`, `<day_key>`.

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
from references.<database>__Costs import Costs
from references.<database>__Budgets import Budgets

# Costs: Day is a SUBSTR/CONCAT of the text <day_key> (file 10's Hive functions), so it isn't written here.
costs = statement(
    SELECT(Costs.Job, Costs.<cost_cents>, Costs.Region, Costs.<day_key>),  # fill in the two <...> names
    FROM(Costs, reads_all_partitions=True),  # a workbook's query reads every row
)

budgets = statement(
    SELECT(Budgets.Job, Budgets.Budget, Budgets.Region,
           AS(Budgets.Budget / 100, "Dollars")),
    FROM(Budgets, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`, `<cost_cents>`, `<day_key>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X26

Map. Sources: run_alerts, job_runs. Steps: none. Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins). job_runs has no formulas and run_alerts reads it, so it isn't a final. Typed over a formula: none. Marks:
- job_id (XLOOKUP) and status (VLOOKUP, FALSE, third column of job_runs) are one LEFT JOIN on run_id.
- avg_mins (AVERAGEIFS over another Table) is a LEFT JOIN of a per-job average. It stays NULL where nothing matches, as the rule for AVERAGEIFS says.
- blank: job_runs.status has a blank (run 98) and a formula reads it, so I wrapped it with COALESCE(.., ''). No alert points at run 98, so the result doesn't change.

Refusals: none. Left alone: nothing. Fill in: `<database>`.

```sql
SELECT a.alert_id, a.run_id, a.severity,
  r.job_id AS job_id,
  COALESCE(r.status, '') AS status,
  v.avg_mins AS avg_mins
FROM <database>.run_alerts a
LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins
           FROM <database>.job_runs
           GROUP BY job_id) v ON r.job_id = v.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, derived,
                              equals, fill_null, statement)
from references.<database>__run_alerts import run_alerts
from references.<database>__job_runs import job_runs

r = AS(job_runs, "r")
v = derived("v", statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity,
           AS(r.job_id, "job_id"),
           AS(fill_null(r.status, ""), "status"),
           AS(v.avg_mins, "avg_mins")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(r, ON=equals(r.run_id, run_alerts.run_id), reads_all_partitions=True),
    LEFT_JOIN(v, ON=equals(v.job_id, r.job_id)),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X27

Map. Sources: jobs. Steps: none. Finals: by_team (team, jobs_in_team, last_job_id, last_job_name). by_team is a summary: its only typed column, team, is what its COUNTIFS and MAXIFS match on, so it is a GROUP BY of jobs. last_job_name looks the name up again by last_job_id, so that is one more join, which I wrote as a CTE. Typed over a formula: none. Marks: none, as no blank is in a column a formula reads. Refusals: none. Left alone: nothing. Fill in: `<database>`.

```sql
WITH teams AS (
  SELECT team, COUNT(*) AS jobs_in_team, MAX(job_id) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
)
SELECT t.team, t.jobs_in_team, t.last_job_id, j.job_name AS last_job_name
FROM teams t
LEFT JOIN <database>.jobs j ON t.last_job_id = j.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, max_of, statement)
from references.<database>__jobs import jobs

teams = derived("teams", statement(
    SELECT(jobs.team, AS(count_rows(), "jobs_in_team"), AS(max_of(jobs.job_id), "last_job_id")),
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(jobs.team),
))
j = AS(jobs, "j")
s = statement(
    SELECT(teams.team, teams.jobs_in_team, teams.last_job_id, AS(j.job_name, "last_job_name")),
    FROM(teams),
    LEFT_JOIN(j, ON=equals(j.job_id, teams.last_job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X28

Map. Sources: jobs, job_runs. Steps: none. Finals: jobs (job_id, job_name, ok_mins). jobs isn't a summary, because job_name is typed and isn't matched on. Typed over a formula: ok_mins where job_id is 3 (99), matched on the Keys row for jobs, job_id. Marks: the SUMIFS reads job_runs over another Table, so it is a LEFT JOIN of per-job sums with COALESCE(.., 0), as Excel gives 0 where nothing matches. The blank status (run 98) sits inside an -IFS form, so it is not wrapped. Refusals: none. Left alone: nothing. Fill in: `<database>`.

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
from references.<database>__jobs import jobs
from references.<database>__job_runs import job_runs

s_ok = derived("s", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
    GROUP_BY(job_runs.job_id),
))
j = AS(jobs, "j")
s = statement(
    SELECT(j.job_id, j.job_name,
           AS(first_match([(equals(j.job_id, 3), 99)], otherwise=fill_null(s_ok.total, 0)),
              "ok_mins")),
    FROM(j, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(s_ok, ON=equals(s_ok.job_id, j.job_id)),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X29

Map. Sources: region_budgets. Steps: none. Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer). Parameters holds cents_per_dollar = 100, so the XLOOKUP into it becomes 100. Parameters is none as a source.

Typed over: in_dollars where job_id is 3 (5). The Keys Table has no row for region_budgets, so there is no Keys row. I matched every typed column of that row: job_id 3, budget_cents 350, region 'us'.

Refusals: pointer, `=INDIRECT("A"&ROW())`, is refused (INDIRECT, and ROW() hangs on the order of the sheet's rows), so `NULL AS pointer`. Left alone: nothing. Fill in: `<database>`. Check that 100 is still the cents_per_dollar value you want in the Hive.

```sql
SELECT job_id, budget_cents, region,
  CASE WHEN job_id = 3 AND budget_cents = 350 AND region = 'us' THEN 5
       ELSE budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets
```

```python
from sqlglot_composer import (AS, FROM, SELECT, all_of, equals, first_match, statement)
from references.<database>__region_budgets import region_budgets

# pointer is refused (INDIRECT / ROW()): it is NULL AS pointer in the Hive, so it isn't selected here.
s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(first_match([(all_of(equals(region_budgets.job_id, 3),
                                   equals(region_budgets.budget_cents, 350),
                                   equals(region_budgets.region, "us")), 5)],
                          otherwise=region_budgets.budget_cents / 100), "in_dollars")),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X30

Map. Sources: scheduler_runs. Steps: none. Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter). Typed over a formula: none. Marks: day is RIGHT(dt, 2), so SUBSTR(dt, -2). I read dt as text such as 2026-09-23. Refusals:
- prev_run, `OFFSET(..., -1, 0)`: OFFSET is refused, and the row before hangs on the order of the rows. It is NULL.
- jitter, `RANDBETWEEN(1,5)`: refused, and it is NULL.

Left alone: the bar chart on sheet "Summary" and the PivotTable on sheet "Pivot" (from Table scheduler_runs). Fill in: `<database>`.

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

# day is SUBSTR(dt, -2), a Hive function (file 10); prev_run and jitter are refused (NULL in the Hive).
s = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X31

Map. Sources: jobs. Steps: none. Finals: jobs (job_id, team, bump, tag, scaled, boosted). Typed over a formula: none. Marks: boosted uses the defined name boost, which is the cell Summary!$B$2 outside a Table, with the value 10. I used 10; move it into Parameters. Refusals:
- bump, `[@bump]*2`: it reads its own column (circular). NULL.
- tag, `TAG(...)`: TAG is a defined name holding a LAMBDA. NULL.
- scaled, `Summary!$D$4`: a reference to a cell outside a Table that isn't a defined name (D4 on sheet Summary). NULL.

Left alone: the cells outside a Table, B2 and D4 on sheet "Summary". Fill in: `<database>`.

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

# bump, tag and scaled are refused (NULL in the Hive), so they aren't selected here.
s = statement(
    SELECT(jobs.job_id, jobs.team, AS(jobs.job_id * 10, "boosted")),  # 10 is boost: move it into Parameters
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X32

Map. Sources: job_runs, jobs. Steps: job_runs, which by_name reads, so it is a CTE with job_name added. Finals: by_name (job_name, runs). job_runs is read by another Table, so it is not a final. by_name is a summary: its only typed column, job_name, is what the COUNTIFS matches on, so it is a GROUP BY of job_runs. Typed over a formula: none. Marks:
- The VLOOKUP uses TRUE (approximate). I converted it exactly, as a LEFT JOIN on job_id, so check the result.
- The blanks in job_runs (status, avg_retry_secs) aren't read by a formula, so nothing is wrapped.

Refusals: none. Left alone: nothing. Fill in: `<database>`.

```sql
WITH job_runs AS (
  SELECT r.job_id, j.job_name
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

j = AS(jobs, "j")
named = derived("named", statement(
    SELECT(job_runs.job_id, AS(j.job_name, "job_name")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(j, ON=equals(j.job_id, job_runs.job_id), reads_all_partitions=True),
))
s = statement(
    SELECT(named.job_name, AS(count_rows(), "runs")),
    FROM(named),
    GROUP_BY(named.job_name),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X33

Map. Sources: job_runs, which the query reads with Sql.Database("dwh01", "ops"), schema ops, item job_runs. The M reads a non-workbook source, so I used the table it names. Check that `<database>.job_runs` is the right one (server dwh01, database ops). Steps: none. Finals: slow_runs (run_id, duration_mins, over_by), the Table the query loads. Typed over a formula: none. Marks: `[status] <> "TEST"` keeps a null in M, so it is `(status <> 'TEST' OR status IS NULL)`. Refusals: none. Left alone: nothing. Fill in: `<database>`.

```sql
SELECT run_id, duration_mins,
  duration_mins - 20 AS over_by
FROM <database>.job_runs
WHERE duration_mins >= 20 AND (status <> 'TEST' OR status IS NULL)
```

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, any_of, at_least, is_null, not_equals,
                              statement)
from references.<database>__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins, AS(job_runs.duration_mins - 20, "over_by")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(at_least(job_runs.duration_mins, 20),
          any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X34

Map. Sources: job_runs, jobs. Steps: runs_with_team (connection only, read by team_totals), a CTE inside the final. Finals: team_totals (team, total_mins, longest), the Table the query team_totals loads. Typed over a formula: none. Marks: the NestedJoin with LeftOuter and ExpandTableColumn is a LEFT JOIN. No blank is in a column the query reads. Refusals: none. Left alone: nothing. Fill in: `<database>`.

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

j = AS(jobs, "j")
runs_with_team = derived("runs_with_team", statement(
    SELECT(job_runs.duration_mins, AS(j.team, "team")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(j, ON=equals(j.job_id, job_runs.job_id), reads_all_partitions=True),
))
s = statement(
    SELECT(runs_with_team.team,
           AS(sum_of(runs_with_team.duration_mins), "total_mins"),
           AS(max_of(runs_with_team.duration_mins), "longest")),
    FROM(runs_with_team),
    GROUP_BY(runs_with_team.team),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X35

Map. Sources: job_runs, scheduler_runs. Steps: none (the M's steps are read in order inside the one query). Finals: recent (run_id, dt), the Table the query "recent" loads. Typed over a formula: none. Marks: Table.Combine is UNION ALL, and Table.Sort then FirstN is ORDER BY ... DESC with LIMIT 4, so the ORDER BY stays. Ties on run_id are not ordered, so the 104 and 103 rows can come in either order.

Refusals: the query "rates" (connection only, nothing reads it) is left out and named. It reads `Web.Contents("https://rates.example.com/today.json")`, a web source, which I don't convert. Left alone: nothing else. Fill in: `<database>`.

```sql
WITH runs AS (
  SELECT run_id, dt FROM <database>.job_runs
),
scheduled AS (
  SELECT run_id, dt FROM <database>.scheduler_runs
),
combined AS (
  SELECT run_id, dt FROM runs
  UNION ALL
  SELECT run_id, dt FROM scheduled
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

runs = statement(
    SELECT(job_runs.run_id, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
scheduled = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
combined = derived("combined", UNION_ALL(runs, scheduled))
s = statement(
    SELECT(combined.run_id, combined.dt),
    FROM(combined),
    ORDER_BY(descending(combined.run_id)),
    LIMIT(4),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ. A Derived table holding a UNION_ALL is the part to watch.

## X36

Map. Sources: run_alerts, job_runs. Steps: none. Finals: two.
- job_runs (run_id, status, alerts). It isn't a summary, because status is typed and isn't matched on.
- severity_by_day (dt, high, low), the Table the query severity_by_day loads.

Typed over a formula: none. Marks:
- alerts is a COUNTIFS over another Table, so a LEFT JOIN of per-run counts with COALESCE(.., 0).
- The blank status (run 98) isn't read by a formula, so it is left alone.
- Table.Pivot gives one SUM(CASE WHEN severity = ... THEN 1 END) column per value in the sample, high and low, with NULL where none. The pivot's columns are now fixed: a new severity in the data needs a new column.

Refusals: none. Left alone: nothing. Fill in: `<database>`.

```sql
SELECT r.run_id, r.status, COALESCE(a.alerts, 0) AS alerts
FROM <database>.job_runs r
LEFT JOIN (SELECT run_id, COUNT(*) AS alerts
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

a = derived("a", statement(
    SELECT(run_alerts.run_id, AS(count_rows(), "alerts")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(run_alerts.run_id),
))
alerts_per_run = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(fill_null(a.alerts, 0), "alerts")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(a, ON=equals(a.run_id, job_runs.run_id)),
)

# count_rows(where=...) gives 0 where the Hive's SUM(CASE ...) gives NULL when none match.
severity_by_day = statement(
    SELECT(run_alerts.dt,
           AS(count_rows(where=equals(run_alerts.severity, "high")), "high"),
           AS(count_rows(where=equals(run_alerts.severity, "low")), "low")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(run_alerts.dt),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X37

Map. Sources: Owners. Steps: none. Finals: Owners (`<job_no>`, `<team_name>`, Owner, Day, `<is_ana>`). Names: `Job No` is `<job_no>`, `Team Name` is `<team_name>`, `Is Ana` is `<is_ana>`. Owner, Day and Owners are plain and kept. I haven't guessed any name. Typed over a formula: none. Marks: blank. Owner is blank for the web job in the sample and the formula reads it. Excel reads it as "", so I wrapped it: COALESCE(Owner, ''). Refusals: none. Left alone: nothing. Fill in: `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

```sql
SELECT <job_no>, <team_name>, Owner, Day,
  IF(COALESCE(Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners
```

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.<database>__Owners import Owners

s = statement(
    SELECT(Owners.<job_no>, Owners.<team_name>, Owners.Owner, Owners.Day,  # fill in the <...> names
           AS(if_else(equals(fill_null(Owners.Owner, ""), "ana"), 1, 0), "<is_ana>")),
    FROM(Owners, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`, `<job_no>`, `<team_name>`, `<is_ana>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X38

Map. Sources: job_runs, jobs. Steps: none. Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost). Typed over: retry_cost where run_id is 102 (1), matched on the Keys row for job_runs, run_id. Marks:
- region is an XLOOKUP, so a LEFT JOIN of jobs on job_id.
- region_mins is a SUMIFS over its own Table: SUM(duration_mins) OVER (PARTITION BY region), with COALESCE(.., 0).
- blank: avg_retry_secs is blank for run 98 and retry_cost reads it, so I wrapped it with COALESCE(avg_retry_secs, 0). duration_mins in the SUMIFS has no blank and sits in an -IFS form anyway.

Refusals: none. Left alone: nothing. Fill in: `<database>`.

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

j = AS(jobs, "j")
by_region = window(PARTITION_BY=j.region)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs,
           AS(j.region, "region"),
           AS(fill_null(sum_of(job_runs.duration_mins, over=by_region), 0), "region_mins"),
           AS(first_match([(equals(job_runs.run_id, 102), 1)],
                          otherwise=(fill_null(job_runs.avg_retry_secs, 0)
                                     + job_runs.duration_mins) * 2), "retry_cost")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(j, ON=equals(j.job_id, job_runs.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>` (`<database>`). Run `project.convert` on the Hive. Its checked code wins where the two differ.
