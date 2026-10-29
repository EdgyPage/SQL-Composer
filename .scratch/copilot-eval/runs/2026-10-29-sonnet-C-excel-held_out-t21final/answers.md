date: 2026-10-29
arm: C
model: sonnet
files: f80b90b

## X21

**Map.** Sources: region_budgets. Steps: none. Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin). Parameters and Keys are empty, so they are none.

- Typed over a formula: none. No Keys row is needed.
- Marks: no blanks in the column the formulas read.
- Refused: none. Left alone: nothing outside the Tables.
- Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.ops__region_budgets import region_budgets

s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(region_budgets.budget_cents / 100, "budget_dollars"),
           AS(region_budgets.budget_cents * 1.1, "with_margin")),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's table holds every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X22

**Map.** Sources: jobs. Steps: none. Finals: jobs (job_id, job_name, team, is_finance, ratio).

- Typed over a formula: none.
- Marks: no blanks in the columns the formulas read.
- IFERROR(a / b, 0) becomes COALESCE(a / b, 0), because a divide by 0 is NULL in Hive. For job 2 that is 2 / 0.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT job_id, job_name, team,
  IF(team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(job_id / (job_id - 2), 0) AS ratio
FROM <database>.jobs
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(if_else(equals(jobs.team, "finance"), "yes", "no"), "is_finance"),
           AS(fill_null(jobs.job_id / (jobs.job_id - 2), 0), "ratio")),
    FROM(jobs, reads_all_partitions=True),  # a workbook's table holds every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X23

**Map.** Sources: job_runs. Steps: none. Finals: job_runs (run_id, status, avg_retry_secs, label, risky).

- Typed over a formula: none.
- Marks, blank: run 98 has a blank status and a blank avg_retry_secs, and both columns are read by SWITCH and OR. So I wrapped them: COALESCE(status, '') and COALESCE(avg_retry_secs, 0). Excel reads them as "" and 0, and Hive would read NULL.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT run_id, status, avg_retry_secs,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label,
  (COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, SELECT, any_of, equals, fill_null, first_match,
                              if_else, more_than, statement)
from references.ops__job_runs import job_runs

status = fill_null(job_runs.status, "")        # blank
retry = fill_null(job_runs.avg_retry_secs, 0)  # blank
s = statement(
    SELECT(job_runs.run_id, job_runs.status, job_runs.avg_retry_secs,
           AS(first_match([(equals(status, "SUCCESS"), "ok"),
                           (equals(status, "FAILED"), "bad")], otherwise="other"), "label"),
           AS(if_else(any_of(equals(status, "FAILED"), more_than(retry, 5)), True, False), "risky")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's table holds every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ, for instance on how `risky` is written.

## X24

**Map.** Sources: team_notes. Steps: none. Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars).

- Typed over a formula: none.
- Marks: no blanks. written_on is read as it stands, a date such as 2026-09-11, and MONTH is used as is.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT team, note, written_on,
  SUBSTR(note, 1, INSTR(note, ' ') - 1) AS first_word,
  UPPER(team) AS shout,
  MONTH(written_on) AS month,
  ROUND(LENGTH(note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes
```

Toolbox code, with `<database>` as ops. Files 03, 04 and 05 give no names for SUBSTR, INSTR, UPPER, MONTH, ROUND or LENGTH. File 10 (labels, Hive functions) does, so load it in a new chat for those four columns. Until then they are left as comments, and `project.convert` on the Hive above will write them.

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__team_notes import team_notes

s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on
           # first_word, shout, month, tens_of_chars: Hive functions, file 10
           ),
    FROM(team_notes, reads_all_partitions=True),  # a workbook's table holds every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X25

**Map.** Sources: Costs, Budgets. Steps: none. Finals: Costs (Job, `<cost_cents>`, Region, `<day_key>`, Day) and Budgets (Job, Budget, Region, Dollars).

- Names: `Cost (cents)` is `<cost_cents>` and `Day Key` is `<day_key>`. The plain names Costs, Budgets, Job, Region, Day, Budget and Dollars stay as they are.
- Marks, date held as text: Day Key holds 20260911 as text or a number, so Day is built from its parts with CONCAT and SUBSTR.
- Marks, blank: Cost (cents) is blank in the last row, but no formula reads it, so I left it alone.
- Typed over a formula: none. Refused: none. Left alone: nothing outside the Tables.
- Fill in: `<database>`, `<cost_cents>`, `<day_key>`.

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

Toolbox code, with `<database>` as ops. I wrote the Table reference imports in lower case. Check them against your Table references, because I don't have file 02. Costs' Day needs CONCAT and SUBSTR, which are in file 10, so it is left as a comment. `project.convert` on the Hive will write it.

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.ops__costs import costs
from references.ops__budgets import budgets

costs_s = statement(
    SELECT(costs.Job, costs.<cost_cents>, costs.Region, costs.<day_key>
           # Day: CONCAT(SUBSTR(...)) of the text Day Key, file 10
           ),
    FROM(costs, reads_all_partitions=True),  # a workbook's table holds every row
)

budgets_s = statement(
    SELECT(budgets.Job, budgets.Budget, budgets.Region,
           AS(budgets.Budget / 100, "Dollars")),
    FROM(budgets, reads_all_partitions=True),  # a workbook's table holds every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X26

**Map.** Sources: run_alerts, job_runs. Steps: none. Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins). job_runs is read by run_alerts and has no formulas, so it is a source only.

- job_id: XLOOKUP on run_id becomes a LEFT JOIN of job_runs.
- status: VLOOKUP(.., job_runs, 3, FALSE) reads the third column of job_runs, which is status. It uses the same join.
- avg_mins: AVERAGEIFS over another Table becomes a LEFT JOIN of the average per job_id. It is left NULL where nothing matches, as the file says. It matches on the looked-up job_id.
- Marks: the lookups are exact. Run 98's status is blank in job_runs, but no alert points at it, so I added nothing.
- Keys has no row for job_runs. I joined on run_id, which is unique in the sample. If it isn't unique in your data, rows would repeat.
- Typed over a formula: none. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT a.alert_id, a.run_id, a.severity,
  r.job_id AS job_id,
  r.status AS status,
  m.avg_mins AS avg_mins
FROM <database>.run_alerts a
LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins
           FROM <database>.job_runs
           GROUP BY job_id) m ON r.job_id = m.job_id
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, derived,
                              equals, statement)
from references.ops__run_alerts import run_alerts
from references.ops__job_runs import job_runs

r = AS(job_runs, "r")
m = derived("m", statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity,
           AS(r.job_id, "job_id"), AS(r.status, "status"), AS(m.avg_mins, "avg_mins")),
    FROM(run_alerts, reads_all_partitions=True),
    LEFT_JOIN(r, ON=equals(r.run_id, run_alerts.run_id), reads_all_partitions=True),
    LEFT_JOIN(m, ON=equals(m.job_id, r.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X27

**Map.** Sources: jobs. Steps: none. Finals: by_team (team, jobs_in_team, last_job_id, last_job_name). by_team is a summary. Its only typed column, team, is what its COUNTIFS and MAXIFS match on, so it is a GROUP BY of jobs.

- last_job_name is INDEX/MATCH on last_job_id, so it is a LEFT JOIN of jobs, and the grouped query goes in a CTE.
- Marks: no blanks. Typed over a formula: none. Refused: none. Left alone: nothing.
- A team in by_team with no job in jobs would drop out of the GROUP BY. In the sample all three are there.
- Fill in: `<database>`.

```sql
WITH team_stats AS (
  SELECT team,
    COALESCE(COUNT(*), 0) AS jobs_in_team,
    COALESCE(MAX(job_id), 0) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
)
SELECT t.team, t.jobs_in_team, t.last_job_id, j.job_name AS last_job_name
FROM team_stats t
LEFT JOIN <database>.jobs j ON t.last_job_id = j.job_id
```

Toolbox code, with `<database>` as ops. The COALESCE around the counts is left out here, since every group has a row. `project.convert` will show the difference.

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, max_of, statement)
from references.ops__jobs import jobs

team_stats = derived("team_stats", statement(
    SELECT(jobs.team, AS(count_rows(), "jobs_in_team"), AS(max_of(jobs.job_id), "last_job_id")),
    FROM(jobs, reads_all_partitions=True),  # a workbook's table holds every row
    GROUP_BY(jobs.team),
))
s = statement(
    SELECT(team_stats.team, team_stats.jobs_in_team, team_stats.last_job_id,
           AS(jobs.job_name, "last_job_name")),
    FROM(team_stats),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, team_stats.last_job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X28

**Map.** Sources: jobs, job_runs. Steps: none. Finals: jobs (job_id, job_name, ok_mins). job_runs is read by jobs, so it is a source only.

- SUMIFS over another Table becomes a LEFT JOIN of a grouped SUM with WHERE status = 'SUCCESS', then COALESCE(.., 0).
- Typed over: ok_mins is 99 where job_id is 3. The Keys row for jobs gives job_id, so I matched on it.
- Marks: run 98's status is blank. SUMIFS skips a blank, so I added nothing.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  CASE WHEN j.job_id = 3 THEN 99 ELSE COALESCE(s.total, 0) END AS ok_mins
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total
           FROM <database>.job_runs
           WHERE status = 'SUCCESS'
           GROUP BY job_id) s ON j.job_id = s.job_id
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, derived, equals,
                              fill_null, first_match, statement, sum_of)
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

s_ok = derived("s", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's table holds every row
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

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X29

**Map.** Sources: region_budgets. Steps: none. Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer). Parameters is none.

- in_dollars: XLOOKUP("cents_per_dollar", Parameters[name], Parameters[value]) is its value, 100. If that value will change, keep it in Parameters.
- Typed over: in_dollars is 5 in the row for job 3. Keys has no row for region_budgets, so I matched every typed column of that row (job_id 3, budget_cents 350, region 'us'). There is no Keys row.
- Refused: pointer, `=INDIRECT("A"&ROW())`. INDIRECT and ROW() are refused, so it is `NULL AS pointer`.
- Marks: no blanks. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  CASE WHEN job_id = 3 AND budget_cents = 350 AND region = 'us' THEN 5
       ELSE budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets
```

Toolbox code, with `<database>` as ops. `pointer` is NULL in the Hive and is left out here.

```python
from sqlglot_composer import (AS, FROM, SELECT, all_of, equals, first_match, statement)
from references.ops__region_budgets import region_budgets

s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(first_match([(all_of(equals(region_budgets.job_id, 3),
                                   equals(region_budgets.budget_cents, 350),
                                   equals(region_budgets.region, "us")), 5)],
                          otherwise=region_budgets.budget_cents / 100), "in_dollars")
           # pointer: refused (INDIRECT, ROW()), NULL in the Hive
           ),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's table holds every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X30

**Map.** Sources: scheduler_runs. Steps: none. Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter).

- day: RIGHT(dt, 2) becomes SUBSTR(dt, -2).
- Refused: prev_run uses OFFSET and jitter uses RANDBETWEEN. Both are `NULL AS ...`.
- Left alone: the bar chart on sheet Summary, and the PivotTable on sheet Pivot (Count of run_id by job_id).
- Marks: no blanks. Typed over a formula: none.
- Fill in: `<database>`.

```sql
SELECT run_id, job_id, dt,
  SUBSTR(dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs
```

Toolbox code, with `<database>` as ops. SUBSTR is in file 10, so `day` is left as a comment. `project.convert` on the Hive will write it.

```python
from sqlglot_composer import FROM, SELECT, statement
from references.ops__scheduler_runs import scheduler_runs

s = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt
           # day: SUBSTR(dt, -2), file 10
           # prev_run, jitter: refused (OFFSET, RANDBETWEEN), NULL in the Hive
           ),
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's table holds every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X31

**Map.** Sources: jobs. Steps: none. Finals: jobs (job_id, team, bump, tag, scaled, boosted).

- boosted: `boost` is a defined name for Summary!$B$2, a cell outside a Table, whose value is 10. I used 10. Move it into Parameters.
- Refused:
  - bump: it reads its own column (circular), so it is NULL.
  - tag: TAG is a defined name holding a LAMBDA, so it is NULL.
  - scaled: it reads Summary!D4, a cell outside a Table that isn't a defined name, so it is NULL. Its value in the sheet is 7.
- Left alone: the cells outside the Tables on Summary (B2 and D4).
- Marks: no blanks. Typed over a formula: none.
- Fill in: `<database>`.

```sql
SELECT job_id, team,
  NULL AS bump,
  NULL AS tag,
  NULL AS scaled,
  job_id * 10 AS boosted
FROM <database>.jobs
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.team,
           # bump, tag, scaled: refused, NULL in the Hive
           AS(jobs.job_id * 10, "boosted")),  # 10 is the defined name boost; move it to Parameters
    FROM(jobs, reads_all_partitions=True),  # a workbook's table holds every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X32

**Map.** Sources: job_runs, jobs. Steps: job_runs, which adds the formula column job_name and is read by by_name. Finals: by_name (job_name, runs). by_name is a summary: its only typed column, job_name, is what its COUNTIFS matches on, so it is a GROUP BY of the job_runs step.

- Marks: VLOOKUP(.., jobs, 2, TRUE) is approximate. I converted it exactly, as a LEFT JOIN on job_id.
- Marks: run 98's status and avg_retry_secs are blank, but nothing reads them.
- Typed over a formula: none. Refused: none. Left alone: nothing.
- cache_warm has no runs, so it is not in by_name's groups, as in the sample.
- Fill in: `<database>`.

```sql
WITH job_runs_step AS (
  SELECT r.run_id, r.job_id, j.job_name AS job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT job_name, COALESCE(COUNT(*), 0) AS runs
FROM job_runs_step
GROUP BY job_name
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, statement)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

job_runs_step = derived("job_runs_step", statement(
    SELECT(job_runs.run_id, job_runs.job_id, AS(jobs.job_name, "job_name")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's table holds every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
))
s = statement(
    SELECT(job_runs_step.job_name, AS(count_rows(), "runs")),
    FROM(job_runs_step),
    GROUP_BY(job_runs_step.job_name),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X33

**Map.** Sources: job_runs, read by the query through Sql.Database, not from the workbook. Steps: none. Finals: slow_runs (run_id, duration_mins, over_by), the Table that query loads.

- Marks: the query reads Sql.Database("dwh01", "ops"), schema ops, item job_runs. I used the table it names, `<database>.job_runs`. Check that your `<database>` is the one the query names (ops).
- Steps converted:
  - The filter `[status] <> "TEST"` keeps a null in M, so it is `(status <> 'TEST' OR status IS NULL)`.
  - over_by is `duration_mins - 20`.
  - The select keeps run_id, duration_mins and over_by.
- Typed over a formula: none. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT run_id, duration_mins, duration_mins - 20 AS over_by
FROM <database>.job_runs
WHERE duration_mins >= 20
  AND (status <> 'TEST' OR status IS NULL)
```

Toolbox code, with `<database>` as ops:

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

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X34

**Map.** Sources: job_runs, jobs. Steps: the query runs_with_team (connection only, but team_totals reads it), so it is a CTE. Finals: team_totals (team, total_mins, longest), the Table the team_totals query loads.

- runs_with_team: a LEFT JOIN of jobs on job_id, expanding team.
- team_totals: GROUP BY team, with List.Sum as SUM and List.Max as MAX.
- No ORDER BY was in the query. Typed over a formula: none. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
WITH runs_with_team AS (
  SELECT r.job_id, r.duration_mins, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT team,
  SUM(duration_mins) AS total_mins,
  MAX(duration_mins) AS longest
FROM runs_with_team
GROUP BY team
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals, max_of,
                              statement, sum_of)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

runs_with_team = derived("runs_with_team", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins, jobs.team),
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

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X35

**Map.** Sources: job_runs, scheduler_runs. Steps: none. Finals: recent (run_id, dt), the Table the recent query loads.

- recent: Table.Combine is UNION ALL, then Table.Sort and FirstN is ORDER BY run_id DESC LIMIT 4.
- Left out, and named: the query `rates` (connection only, nothing reads it). It reads Web.Contents, a web source, which I don't convert.
- Typed over a formula: none. Refused: none besides rates. Left alone: nothing.
- Fill in: `<database>`.

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

Toolbox code, with `<database>` as ops. Reading a stacked Statement as a Derived table is my reading of files 03 and 05, so check it against `project.convert`.

```python
from sqlglot_composer import (FROM, LIMIT, ORDER_BY, SELECT, UNION_ALL, derived, descending,
                              statement)
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

combined = derived("combined", UNION_ALL(
    statement(SELECT(job_runs.run_id, job_runs.dt),
              FROM(job_runs, reads_all_partitions=True)),        # a workbook's query reads every row
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

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X36

**Map.** Sources: run_alerts, job_runs. Steps: none. Finals: severity_by_day (dt, high, low), the Table the query loads, and job_runs (run_id, status, alerts). Two finals, so two queries.

- job_runs.alerts: COUNTIFS over another Table is a LEFT JOIN of the count per run_id, then COALESCE(.., 0), because Excel gives 0 where nothing matches. job_runs also has a typed status, so it is not a summary.
- severity_by_day: Table.Pivot is a `SUM(CASE WHEN severity = 'high' THEN 1 END)` column per value in the sample, high and low. They are NULL where there is none, as M leaves it. The pivot's columns are now fixed, so a new severity value needs a new column.
- Marks: run 98's status is blank, and nothing reads it. Typed over a formula: none. Refused: none. Left alone: nothing.
- Fill in: `<database>`.

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

Toolbox code, with `<database>` as ops. In the pivot I used `count_rows(where=...)`, which gives 0 where the Hive above gives NULL, so check it against `project.convert`.

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, fill_null, statement)
from references.ops__job_runs import job_runs
from references.ops__run_alerts import run_alerts

per_run = derived("a", statement(
    SELECT(run_alerts.run_id, AS(count_rows(), "total")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's table holds every row
    GROUP_BY(run_alerts.run_id),
))
job_runs_s = statement(
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

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X37

**Map.** Sources: Owners. Steps: none. Finals: Owners (`<job_no>`, `<team_name>`, Owner, Day, `<is_ana>`), all 56 rows.

- Names: `Job No` is `<job_no>`, `Team Name` is `<team_name>`, `Is Ana` is `<is_ana>`. Owner and Day are plain names and stay.
- Marks, blank: Owner is blank for the web rows and the formula reads it, so I wrapped it in COALESCE(Owner, '').
- No filter: the sample's dates are not a filter.
- Typed over a formula: none. Refused: none. Left alone: nothing.
- Fill in: `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

```sql
SELECT <job_no>, <team_name>, Owner, Day,
  IF(COALESCE(Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners
```

Toolbox code, with `<database>` as ops. I wrote the Table reference import in lower case, so check it against your Table references.

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.ops__owners import owners

s = statement(
    SELECT(owners.<job_no>, owners.<team_name>, owners.Owner, owners.Day,
           AS(if_else(equals(fill_null(owners.Owner, ""), "ana"), 1, 0), "<is_ana>")),  # blank
    FROM(owners, reads_all_partitions=True),  # a workbook's table holds every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X38

**Map.** Sources: job_runs, jobs. Steps: none. Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost). jobs is read by job_runs, so it is a source only.

- region: XLOOKUP is a LEFT JOIN of jobs on job_id.
- region_mins: SUMIFS over its own Table is `SUM(duration_mins) OVER (PARTITION BY region)`, with COALESCE(.., 0). It partitions by the looked-up region.
- Typed over: retry_cost is 1 where run_id is 102. The Keys row for job_runs gives run_id, so I matched on it.
- Marks, blank: run 98's avg_retry_secs is blank and retry_cost reads it, so it is COALESCE(avg_retry_secs, 0). region_mins reads duration_mins and region, which have no blanks. SUMIFS also skips a blank status.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  j.region AS region,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.region), 0) AS region_mins,
  CASE WHEN r.run_id = 102 THEN 1
       ELSE (COALESCE(r.avg_retry_secs, 0) + r.duration_mins) * 2 END AS retry_cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, first_match,
                              statement, sum_of, window)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

by_region = window(PARTITION_BY=jobs.region)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs,
           AS(jobs.region, "region"),
           AS(fill_null(sum_of(job_runs.duration_mins, over=by_region), 0), "region_mins"),
           AS(first_match([(equals(job_runs.run_id, 102), 1)],
                          otherwise=(fill_null(job_runs.avg_retry_secs, 0)  # blank
                                     + job_runs.duration_mins) * 2), "retry_cost")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's table holds every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X39

**Map.** Sources: job_runs, jobs. Steps: none. Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise). ok_runs is the Table its query loads plus three formula columns, and nothing reads it. The query and the Table are two things, and here they make one final.

- Query rows: job_runs where status = 'SUCCESS', keeping run_id, job_id and duration_mins.
- job_name: XLOOKUP is a LEFT JOIN of jobs on job_id.
- share: SUMIFS over its own Table is `SUM(duration_mins) OVER (PARTITION BY job_id)` over the query's rows, with COALESCE(.., 0).
- Refused: noise, `=RAND()`, so it is `NULL AS noise`.
- Marks: run 98's status and avg_retry_secs are blank, but the filter is a plain `=` that drops it, as M does. Typed over a formula: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  j.job_name AS job_name,
  r.duration_mins / COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id), 0) AS share,
  NULL AS noise
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
WHERE r.status = 'SUCCESS'
```

Toolbox code, with `<database>` as ops. `noise` is NULL in the Hive and is left out here.

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, WHERE, equals, fill_null,
                              statement, sum_of, window)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

by_job = window(PARTITION_BY=job_runs.job_id)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins,
           AS(jobs.job_name, "job_name"),
           AS(job_runs.duration_mins / fill_null(sum_of(job_runs.duration_mins, over=by_job), 0),
              "share")
           # noise: refused (RAND), NULL in the Hive
           ),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
    WHERE(equals(job_runs.status, "SUCCESS")),
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X40

**Map**

- Sources: Runs (typed columns Run, Job, Mins), jobs (job_id, team). `Parameters` and `Keys` are none.
- Steps: Runs, because it has formulas (Team, Cost) and Teams and run_alerts read it. It is a CTE in each final's query.
- Finals: Teams (Team, `<total_cost>`) and run_alerts (alert_id, run_id, severity, dt, `<run_mins>`).
- Teams is a summary: its only typed column, Team, is what its SUMIFS matches on. It is a GROUP BY of the Runs step.
- Value typed over a formula: none.
- Parameters: `XLOOKUP("rate", Parameters[name], Parameters[value])` is its value, 2, written into Cost. Move it into Parameters if you want to change it.
- Blank: none in the columns the formulas read.
- Refused: none.
- Left alone: the PivotTable on "Pivot", which is not a Table.
- Fill in: `<database>`, `<total_cost>` (header `Total Cost`) and `<run_mins>` (header `Run Mins`).
- Teams lists data and finance. The GROUP BY gives one row for every team that has runs, which is the same two teams here.

Teams:

```sql
WITH runs_step AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT Team, COALESCE(SUM(Cost), 0) AS <total_cost>
FROM runs_step
GROUP BY Team
```

run_alerts:

```sql
WITH runs_step AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt, s.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN runs_step s ON a.run_id = s.Run
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals,
                              fill_null, statement, sum_of)
from references.ops__Runs import Runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

r = AS(Runs, "r")
runs_step = derived("runs_step", statement(
    SELECT(r.Run, r.Job, r.Mins, AS(jobs.team, "Team"),
           AS(r.Mins * 2, "Cost")),  # 2 is the rate from Parameters
    FROM(r, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, r.Job), reads_all_partitions=True),
))

teams = statement(
    SELECT(runs_step.Team, AS(fill_null(sum_of(runs_step.Cost), 0), "<total_cost>")),
    FROM(runs_step),
    GROUP_BY(runs_step.Team),
)

alerts = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(runs_step.Mins, "<run_mins>")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(runs_step, ON=equals(runs_step.Run, run_alerts.run_id)),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X46

**Map**

- Sources: job_runs (job_id, duration_mins).
- Steps: none as a Table. The per-job figures are a subquery and then a CTE, so the rank can read `runs`.
- Finals: jobs (job_id, job_name, team, shortest, runs, busiest).
- jobs has typed columns, so it is not a summary. It is a final that reads the job_runs source.
- Value typed over a formula: none. No Keys row is needed.
- Blank: the blanks in job_runs (status, avg_retry_secs) are not read by any formula. duration_mins and job_id have none.
- Zero for no match: MINIFS and COUNTIF give 0 in Excel where a job has no runs (job 4, cache_warm). So both are wrapped in COALESCE(.., 0).
- RANK.EQ is RANK() OVER (ORDER BY runs DESC). It is written over the already computed `runs`.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
WITH base AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(m.shortest, 0) AS shortest,
    COALESCE(m.runs, 0) AS runs
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, MIN(duration_mins) AS shortest, COUNT(*) AS runs
    FROM <database>.job_runs
    GROUP BY job_id
  ) m ON j.job_id = m.job_id
)
SELECT job_id, job_name, team, shortest, runs,
  RANK() OVER (ORDER BY runs DESC) AS busiest
FROM base
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              descending, equals, fill_null, min_of, rank, statement, window)
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

m = derived("m", statement(
    SELECT(job_runs.job_id, AS(min_of(job_runs.duration_mins), "shortest"),
           AS(count_rows(), "runs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formula reads every row
    GROUP_BY(job_runs.job_id),
))
base = derived("base", statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(fill_null(m.shortest, 0), "shortest"), AS(fill_null(m.runs, 0), "runs")),
    FROM(jobs, reads_all_partitions=True),
    LEFT_JOIN(m, ON=equals(m.job_id, jobs.job_id)),
))
s = statement(
    SELECT(base.job_id, base.job_name, base.team, base.shortest, base.runs,
           AS(rank(over=window(ORDER_BY=descending(base.runs))), "busiest")),
    FROM(base),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X47

**Map**

- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg). It reads its own columns.
- Value typed over a formula: none. No Keys row is needed.
- Blank: none in the columns the formulas read.
- RANK.EQ with 1 as its third argument is ascending, so cheapest is 1.
- SUMIF over its own Table is a window SUM, with COALESCE(.., 0). AVERAGEIF is a window AVG, left NULL.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, SELECT, average_of, fill_null, rank, statement,
                              sum_of, window)
from references.ops__region_budgets import region_budgets

by_region = window(PARTITION_BY=region_budgets.region)
s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(rank(over=window(ORDER_BY=region_budgets.budget_cents)), "cheapest_first"),
           AS(fill_null(sum_of(region_budgets.budget_cents, over=by_region), 0), "region_total"),
           AS(average_of(region_budgets.budget_cents, over=by_region), "region_avg")),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's formula reads every row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X48

**Map**

- Sources: job_runs, jobs, run_alerts. Their Tables have no formulas and no query.
- Steps: none.
- Finals: quiet_runs (run_id, job_id, status) and slow_regions (region, avg_mins, fastest). Each is a Table loaded by a query, and nothing reads either.
- quiet_runs is a LeftAnti NestedJoin, so it is a LEFT JOIN with `WHERE a.run_id IS NULL`, with job_runs' columns only.
- slow_regions is an Inner join, a GROUP BY region, and a Table.SelectRows after the group, which is a HAVING that repeats the aggregate.
- Value typed over a formula: none. There are no formulas.
- Blank: status is blank on run 98. It is only passed through, so it stays NULL.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

quiet_runs:

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

slow_regions:

```sql
SELECT j.region, AVG(r.duration_mins) AS avg_mins, MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (ANTI_JOIN, FROM, GROUP_BY, HAVING, JOIN, SELECT, AS, at_least,
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
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
    GROUP_BY(jobs.region),
    HAVING(at_least(average_of(job_runs.duration_mins), 20)),
)
```

The Toolbox writes the anti join as LEFT ANTI JOIN, which keeps the same rows as the LEFT JOIN above. Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X49

**Map**

- Sources: job_runs, jobs, run_alerts, scheduler_runs, job_owners. None has a formula or a query.
- Steps: none. No query reads another query.
- Finals: alert_status (alert_id, severity, status), run_check (run_id, status, scheduled_run) and teams (team).
- alert_status is a RightOuter join, so it is a LEFT JOIN with the two tables swapped. It keeps every run, with NULL alert columns for runs with no alert.
- run_check is a FullOuter join. The expanded `run_id` is renamed `scheduled_run`.
- teams is Table.Distinct over Table.Combine, so it is a UNION.
- Value typed over a formula: none.
- Blank: owner is blank for job 4 and is not read here. The NULLs in the outputs come from the joins, as in the sample.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

alert_status:

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
```

run_check:

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

teams:

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

Toolbox code, with `<database>` as ops:

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
    # a run can have many alerts and the query keeps each one, so many_matches=True
    LEFT_JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id),
              many_matches=True, reads_all_partitions=True),
)

run_check = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(scheduler_runs.run_id, "scheduled_run")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    FULL_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id),
              reads_all_partitions=True),
)

teams = UNION(
    statement(SELECT(jobs.team), FROM(jobs, reads_all_partitions=True)),
    statement(SELECT(job_owners.team), FROM(job_owners, reads_all_partitions=True)),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X50

**Map**

- Sources: job_owners, jobs.
- Steps: none. Nothing reads the owners Table, so the owners query's rows and the two formula columns are one final.
- Finals: owners (job_id, owner, job_name, newest_first).
- The query is `SELECT DISTINCT job_id, owner`. `job_name` is an XLOOKUP into jobs, so it is a LEFT JOIN. `newest_first` is RANK.EQ over the Table's own job_id, so it is `RANK() OVER (ORDER BY job_id DESC)` over the query's rows.
- The query's rows are a CTE so the rank counts the distinct rows, not the 56 raw ones.
- Value typed over a formula: none.
- Blank: owner is blank for job 4. It is only passed through, so it stays NULL, and Distinct keeps it as a value.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
WITH owners_query AS (
  SELECT DISTINCT job_id, owner
  FROM <database>.job_owners
)
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM owners_query o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, SELECT_DISTINCT, derived,
                              descending, equals, rank, statement, window)
from references.ops__job_owners import job_owners
from references.ops__jobs import jobs

owners_query = derived("owners_query", statement(
    SELECT_DISTINCT(job_owners.job_id, job_owners.owner),
    FROM(job_owners, reads_all_partitions=True),  # a workbook's query reads every row
))
s = statement(
    SELECT(owners_query.job_id, owners_query.owner, jobs.job_name,
           AS(rank(over=window(ORDER_BY=descending(owners_query.job_id))), "newest_first")),
    FROM(owners_query),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, owners_query.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X59

**Map**

- Sources: job_runs.
- Steps: none.
- Finals: jobs (job_id, job_name, long_runs, failed_mins, not_test) and run_alerts (alert_id, run_id, severity, dt, alerts_so_far).
- Value typed over a formula: none. No Keys row is needed.
- jobs reads another Table, job_runs, so each -IFS is a LEFT JOIN of a grouped subquery with COALESCE(.., 0):
  - `">=20"` is `duration_mins >= 20`.
  - `"f*"` is `LOWER(status) LIKE 'f%'`, as Excel ignores case.
  - `"<>TEST"` is `(status <> 'TEST' OR status IS NULL)`, as Excel counts a blank there.
- Blank: status is blank on run 98 (job 2). It sits inside an -IFS form, so it is not wrapped. not_test counts it, as Excel does.
- run_alerts: `COUNTIFS(run_alerts[run_id], "<="&[@run_id])` over its own Table is a running count with ties included, so it is a RANGE window.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

jobs:

```sql
SELECT j.job_id, j.job_name,
  COALESCE(lr.total, 0) AS long_runs,
  COALESCE(fm.total, 0) AS failed_mins,
  COALESCE(nt.total, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS total
  FROM <database>.job_runs
  WHERE duration_mins >= 20
  GROUP BY job_id
) lr ON j.job_id = lr.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total
  FROM <database>.job_runs
  WHERE LOWER(status) LIKE 'f%'
  GROUP BY job_id
) fm ON j.job_id = fm.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS total
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) nt ON j.job_id = nt.job_id
```

run_alerts:

```sql
SELECT alert_id, run_id, severity, dt,
  COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, any_of, at_least,
                              count_rows, derived, equals, fill_null, is_null, not_equals,
                              starts_with, statement, sum_of, window)
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs
from references.ops__run_alerts import run_alerts

lr = derived("lr", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "total")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formula reads every row
    WHERE(at_least(job_runs.duration_mins, 20)),
    GROUP_BY(job_runs.job_id),
))
fm = derived("fm", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),
    # Excel's "f*" ignores case. Both cases are written here, and project.convert on the Hive keeps LOWER
    WHERE(any_of(starts_with(job_runs.status, "f"), starts_with(job_runs.status, "F"))),
    GROUP_BY(job_runs.job_id),
))
nt = derived("nt", statement(
    SELECT(job_runs.job_id, AS(count_rows(), "total")),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
    GROUP_BY(job_runs.job_id),
))
jobs_s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(fill_null(lr.total, 0), "long_runs"),
           AS(fill_null(fm.total, 0), "failed_mins"),
           AS(fill_null(nt.total, 0), "not_test")),
    FROM(jobs, reads_all_partitions=True),
    LEFT_JOIN(lr, ON=equals(lr.job_id, jobs.job_id)),
    LEFT_JOIN(fm, ON=equals(fm.job_id, jobs.job_id)),
    LEFT_JOIN(nt, ON=equals(nt.job_id, jobs.job_id)),
)

# window() has rows= and no RANGE, so run 97's two alerts count one at a time here.
# The Hive above has the RANGE that counts ties as Excel does, and project.convert checks it.
run_alerts_s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(count_rows(over=window(ORDER_BY=run_alerts.run_id, rows=(None, 0))),
              "alerts_so_far")),
    FROM(run_alerts, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X60

**Map**

- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region), and `region_budgets (Total Row)`.
- Value typed over a formula: none.
- Formulas:
  - `share` divides by the whole column, so it is a `SUM(..) OVER ()`.
  - `above_avg` compares with `AVG(..) OVER ()`.
  - `rank_in_region` is `COUNTIFS(.., "<"&..)+1`, which is `RANK() OVER (PARTITION BY region ORDER BY budget_cents)`, ascending.
- Total Row: job_id is SUBTOTAL(103), a COUNT. budget_cents is SUBTOTAL(101), an AVG. The "Total" label is left out. region_budgets is not a summary, so the Total Row is a query of its own, one row with a column per total, in order.
- Blank: none.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

region_budgets:

```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

region_budgets (Total Row):

```sql
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, SELECT, average_of, count_rows, if_else, is_not_null,
                              more_than, rank, statement, sum_of, window)
from references.ops__region_budgets import region_budgets

whole = window()
s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(region_budgets.budget_cents / sum_of(region_budgets.budget_cents, over=whole), "share"),
           AS(if_else(more_than(region_budgets.budget_cents,
                                average_of(region_budgets.budget_cents, over=whole)),
                      True, False), "above_avg"),
           AS(rank(over=window(PARTITION_BY=region_budgets.region,
                               ORDER_BY=region_budgets.budget_cents)), "rank_in_region")),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's formula reads every row
)

total_row = statement(
    SELECT(AS(count_rows(where=is_not_null(region_budgets.job_id)), "job_id"),
           AS(average_of(region_budgets.budget_cents), "budget_cents")),
    FROM(region_budgets, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X61

**Map**

- Sources: region_costs (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: by_region (region, total_cents, entries, priciest).
- by_region is a summary: its only typed column, region, is what its SUMIFS, COUNTIFS and MAXIFS match on. It is a GROUP BY region of region_costs.
- Total Row: the totals are SUM of sums (109), SUM of counts (109) and MAX of maxes (104), so it needs no query of its own. The query ends `GROUP BY region WITH ROLLUP`, which adds the total as one more row with region NULL (a Subtotal row). The "Total" label is not written, so that row has region NULL.
- Value typed over a formula: none.
- Blank: cost_cents is blank for job 2 on 20260924. It sits inside the -IFS forms, so it is not wrapped. The SUM and MAX skip it, and `entries` still counts that row, as Excel does.
- dt is held as text (20260911) but no formula reads it, so it is not converted.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(*), 0) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, count_rows, fill_null, max_of,
                              rollup, statement, sum_of)
from references.ops__region_costs import region_costs

s = statement(
    SELECT(region_costs.region,
           AS(fill_null(sum_of(region_costs.cost_cents), 0), "total_cents"),
           AS(count_rows(), "entries"),
           AS(fill_null(max_of(region_costs.cost_cents), 0), "priciest")),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's formula reads every row
    GROUP_BY(rollup(region_costs.region)),  # the Total Row, as a Subtotal row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X62

**Map**

- Sources: team_notes (team, note, written_on).
- Steps: none.
- Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short).
- Value typed over a formula: none.
- Formulas:
  - `week_of` is `d-WEEKDAY(d,2)+1`, written as week_start does.
  - `month_end` is EOMONTH(d, 0).
  - `month_of` is `EOMONTH(d,-1)+1`, written as month_start does.
  - `months_in` is DATEDIF with "m", from DATE(2026,1,1).
  - `three_before` is d - 3.
  - `who` is PROPER.
  - `short` is TEXTJOIN with a ": " separator.
- week_of and month_of come out as text (`CAST(.. AS STRING)`), not as dates.
- Blank: none.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

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

Toolbox code, with `<database>` as ops. Files 03, 04 and 05 hold `week_start` and `month_start` but no names for LAST_DAY, MONTHS_BETWEEN, DATE_SUB, INITCAP or CONCAT_WS. Those columns are left as comments, and file 10 (Hive functions), in a new chat, covers them.

```python
from sqlglot_composer import AS, FROM, SELECT, month_start, statement, week_start
from references.ops__team_notes import team_notes

s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on,
           AS(week_start(team_notes.written_on), "week_of"),
           # month_end: LAST_DAY(written_on)           (file 10)
           AS(month_start(team_notes.written_on), "month_of"),
           # months_in: FLOOR(MONTHS_BETWEEN(written_on, '2026-01-01'))   (file 10)
           # three_before: DATE_SUB(written_on, 3)     (file 10)
           # who: INITCAP(team)                        (file 10)
           # short: CONCAT_WS(': ', team, SUBSTR(note, 1, 5))   (file 10)
           ),
    FROM(team_notes, reads_all_partitions=True),  # a workbook's formula reads every row
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X63

**Map**

- Sources: scheduler_runs (run_id, job_id). job_runs' typed columns (run_id, job_id, status, duration_mins, avg_retry_secs) stand for the database table job_runs.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded).
- Value typed over a formula: none.
- Formulas:
  - ISBLANK is `IS NULL`.
  - INT is FLOOR.
  - MIN of two cells is LEAST.
  - VAR.S of the whole column is `VAR_SAMP(..) OVER ()`.
  - SUMPRODUCT is `SUM(a * b) OVER ()`.
  - XLOOKUP's fourth argument, -1, is a COALESCE after a LEFT JOIN of scheduler_runs.
  - CONCATENATE is CONCAT.
  - ISNUMBER(SEARCH(..)) is `INSTR(LOWER(x), LOWER(a)) > 0`.
- Blank: status is blank on run 98. SEARCH on a blank gives FALSE in Excel, so status is wrapped as COALESCE(status, ''). avg_retry_secs is blank on run 98 too, and ISBLANK reads it, so it is not wrapped.
- If run_id repeats in scheduler_runs, the join repeats job_runs rows where XLOOKUP takes the first match. In the sample it does not repeat.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

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

Toolbox code, with `<database>` as ops. The columns that need FLOOR, LEAST, VAR_SAMP, CONCAT, INSTR and LOWER have no name in files 03, 04 and 05. They are left as comments, and file 10 (Hive functions), in a new chat, covers them.

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, if_else,
                              is_null, statement, sum_of, window)
from references.ops__job_runs import job_runs
from references.ops__scheduler_runs import scheduler_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs,
           AS(if_else(is_null(job_runs.avg_retry_secs), True, False), "no_retry"),
           # quarters: FLOOR(duration_mins / 4)            (file 10)
           # capped: LEAST(duration_mins, 25)              (file 10)
           # variance: VAR_SAMP(duration_mins) OVER ()     (file 10)
           AS(sum_of(job_runs.duration_mins * job_runs.job_id, over=window()), "weighted"),
           AS(fill_null(scheduler_runs.job_id, -1), "scheduled_job"),
           # label: CONCAT('run ', run_id)                 (file 10)
           # succeeded: INSTR(LOWER(COALESCE(status, '')), 'cess') > 0   (file 10)
           ),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formula reads every row
    LEFT_JOIN(scheduler_runs, ON=equals(scheduler_runs.run_id, job_runs.run_id),
              reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X64

**Map**

- Sources: region_costs and jobs. Neither has a formula.
- Steps: none. No query reads another query.
- Finals: picked_costs (job_id, cost_cents, region, size), costed_jobs (job_id, job_name, team, region) and costs_filled (job_id, cost_cents, dt, day).
- Value typed over a formula: none.
- M `<> null` is `IS NOT NULL`. List.Contains({1, 3}, ..) is `IN (1, 3)`. Text.Upper is UPPER. The `if ... then ... else` is IF.
- costed_jobs: List.Contains over another table's column is a LEFT SEMI JOIN. `not Text.StartsWith(.., "n")` is `NOT ... LIKE 'n%'`, with the case kept as M keeps it.
- costs_filled: ReplaceValue of null with 0 is `COALESCE(cost_cents, 0)`. `Text.End([dt], 2)` is `SUBSTR(dt, -2)`.
- dt is held as text (20260911). Text.End reads the last two characters, so it is used as it is and not turned into a date.
- Blank: cost_cents is blank for job 2 on 20260924. picked_costs drops it (`IS NOT NULL`) and costs_filled turns it into 0, as the queries do.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

picked_costs:

```sql
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

costed_jobs:

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

costs_filled:

```sql
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt, SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

Toolbox code, with `<database>` as ops. UPPER, SUBSTR and a negated LIKE have no name in files 03, 04 and 05. Those parts are left as comments, and file 10, in a new chat, covers them.

```python
from sqlglot_composer import (AS, FROM, SELECT, SEMI_JOIN, WHERE, at_least, equals,
                              fill_null, if_else, is_in, is_not_null, statement)
from references.ops__region_costs import region_costs
from references.ops__jobs import jobs

picked_costs = statement(
    SELECT(region_costs.job_id, region_costs.cost_cents,
           region_costs.region,  # UPPER(region) AS region needs file 10
           AS(if_else(at_least(region_costs.cost_cents, 200), "big", "small"), "size")),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_not_null(region_costs.cost_cents), is_in(region_costs.job_id, [1, 3])),
)

costed_jobs = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs, reads_all_partitions=True),
    SEMI_JOIN(region_costs, ON=equals(region_costs.job_id, jobs.job_id),
              reads_all_partitions=True),
    # WHERE NOT (job_name LIKE 'n%') has no name here (file 10)
)

costs_filled = statement(
    SELECT(region_costs.job_id, AS(fill_null(region_costs.cost_cents, 0), "cost_cents"),
           region_costs.dt),
    # day: SUBSTR(dt, -2) AS day needs file 10
    FROM(region_costs, reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X65

**Map**

- Sources: jobs, region_budgets, job_owners, scheduler_runs, job_runs. None has a formula.
- Steps: none. No query reads another query.
- Finals: team_regions (team, region), budget_places (job_id, budget_cents, region, place), jobs_per_team (team, jobs), ran_as_scheduled (run_id, dt) and run_measures (run_id, job_id, measure, amount).
- Value typed over a formula: none.
- team_regions is `Table.AddColumn(t, "r", each Regions)` and then expanded, so it is a CROSS JOIN. The Table.Sort after it has no FirstN or index, so there is no ORDER BY. The order was dropped, as a Hive table holds no order.
- budget_places: the sort feeds Table.AddIndexColumn, so it is `ROW_NUMBER() OVER (ORDER BY budget_cents DESC)`. The final sort is not kept, because there is no LIMIT. The order was dropped.
- jobs_per_team: `List.Count(List.Distinct([job_id]))` is `COUNT(DISTINCT job_id)`. It leaves out NULL where M counts it as a value. job_id has no blank in the sample.
- ran_as_scheduled: a NestedJoin on every column, its new column removed, in Table.Distinct, is an Inner join, so it is INTERSECT.
- run_measures: Table.Unpivot is one SELECT per column, stacked with UNION ALL. Each has `WHERE .. IS NOT NULL`, as M drops a null. Run 98's blank avg_retry_secs is dropped.
- Blank: only the unpivot one above.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

team_regions:

```sql
SELECT t.team, r.region
FROM (SELECT DISTINCT team FROM <database>.jobs) t
CROSS JOIN (SELECT DISTINCT region FROM <database>.jobs) r
```

budget_places:

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

ran_as_scheduled:

```sql
SELECT run_id, dt FROM <database>.scheduler_runs
INTERSECT
SELECT run_id, dt FROM <database>.job_runs
```

run_measures:

```sql
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, CROSS_JOIN, FROM, GROUP_BY, INTERSECT, SELECT,
                              SELECT_DISTINCT, UNION_ALL, WHERE, count_distinct, derived,
                              descending, is_not_null, row_number, statement)
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets
from references.ops__job_owners import job_owners
from references.ops__scheduler_runs import scheduler_runs
from references.ops__job_runs import job_runs

# every read below is a workbook's query, which reads every row

t = derived("t", statement(SELECT_DISTINCT(jobs.team), FROM(jobs, reads_all_partitions=True)))
r = derived("r", statement(SELECT_DISTINCT(jobs.region), FROM(jobs, reads_all_partitions=True)))
team_regions = statement(SELECT(t.team, r.region), FROM(t), CROSS_JOIN(r))

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

# the measure's text value is written through AS. If the Toolbox reads it as a column,
# project.convert on the Hive above gives the checked code
run_measures = UNION_ALL(
    statement(SELECT(job_runs.run_id, job_runs.job_id,
                     AS("duration_mins", "measure"), AS(job_runs.duration_mins, "amount")),
              FROM(job_runs, reads_all_partitions=True),
              WHERE(is_not_null(job_runs.duration_mins))),
    statement(SELECT(job_runs.run_id, job_runs.job_id,
                     AS("avg_retry_secs", "measure"), AS(job_runs.avg_retry_secs, "amount")),
              FROM(job_runs, reads_all_partitions=True),
              WHERE(is_not_null(job_runs.avg_retry_secs))),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X66

**Map**

- Sources: job_runs.
- Steps: none. Nothing reads the ok_runs Table, so the query's rows and the two formula columns are one final.
- Finals: ok_runs (run_id, job_id, duration_mins, dt, running, share), and `ok_runs (Total Row)`.
- Value typed over a formula: none.
- The query: `[status] <> null` is `status IS NOT NULL`. Text.StartsWith keeps the case, so it is `LIKE 'SUCC%'`. Run 98's blank status is left out by it.
- Formulas, which read the query's rows:
  - `running` is `SUMIFS(.., job_id, [@job_id], dt, "<="&[@dt])` over its own Table. It is a running total with ties included, so it is a RANGE window partitioned by job_id and ordered by dt, with COALESCE(.., 0).
  - `share` divides by the whole column, so it is `SUM(..) OVER ()`.
  - The window functions run after the WHERE, so they see only the kept rows.
- Total Row: SUBTOTAL(109, duration_mins), a SUM. ok_runs is not a summary, so the Total Row is a query of its own, one row, with no "Total" label.
- Blank: none in the kept rows.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

ok_runs:

```sql
SELECT run_id, job_id, duration_mins, dt,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

ok_runs (Total Row):

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT SUM(duration_mins) AS duration_mins
FROM ok_runs
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, derived, fill_null, is_not_null,
                              starts_with, statement, sum_of, window)
from references.ops__job_runs import job_runs

# window() has rows= and no RANGE, so jobs with two runs on one dt (job 1 on 2026-09-24) count one
# at a time here. The Hive above has the RANGE that counts ties as Excel does.
each_job = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.dt, rows=(None, 0))
ok_runs = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt,
           AS(fill_null(sum_of(job_runs.duration_mins, over=each_job), 0), "running"),
           AS(job_runs.duration_mins / sum_of(job_runs.duration_mins, over=window()), "share")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_not_null(job_runs.status), starts_with(job_runs.status, "SUCC")),
)

ok = derived("ok", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(is_not_null(job_runs.status), starts_with(job_runs.status, "SUCC")),
))
total_row = statement(
    SELECT(AS(sum_of(ok.duration_mins), "duration_mins")),
    FROM(ok),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X69

**Map**

- Sources: region_costs' typed columns (job_id, cost_cents, region, dt) as the database table region_costs, jobs, and region_budgets.
- Steps: region_costs, because it has formulas (job_name, budget, over_budget, running_cost) and job_totals and the late_costs query read it. It is the CTE `region_costs_step` in each final's query.
- Finals: job_totals (job_id, total_cents, over_count), late_costs (job_id, dt, running_cost). The Total Row of job_totals is covered below.
- Value typed over a formula: none.
- Formulas in the step:
  - job_name and budget are XLOOKUPs, so each is a LEFT JOIN.
  - over_budget compares cost_cents with the looked-up budget. It uses `b.budget_cents` because a same-SELECT alias cannot be read.
  - running_cost is `SUMIFS(.., job_id, [@job_id], dt, "<="&[@dt])` over its own Table. It is a running total with ties included, so it is a RANGE window with COALESCE(.., 0).
- Blank: cost_cents is blank for job 2 on 20260924. over_budget reads it outside an -IFS form, so it is COALESCE(cost_cents, 0), which makes that row FALSE as in Excel. In running_cost and the SUMIFS it is skipped.
- dt is held as text (20260911). It is ordered as a date here, `CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2))`. The dt column in late_costs is passed through as it is.
- job_totals is a summary: its only typed column, job_id, is what its SUMIFS and COUNTIFS match on. It is a GROUP BY job_id of the region_costs step. The `COUNTIFS(.., over_budget, TRUE)` is a COUNT of the rows where over_budget holds.
- job_totals (Total Row): both totals are SUMs of a summary's SUMs and COUNTs, so it needs no query of its own. The query ends `GROUP BY job_id WITH ROLLUP`, which adds the total as one more row with job_id NULL (a Subtotal row). The "Total" label is not written.
- late_costs is a query that filters on the Table's formula column `running_cost`, so it reads the region_costs step.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

job_totals:

```sql
WITH region_costs_step AS (
  SELECT r.job_id, r.cost_cents, r.region, r.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(r.cost_cents) OVER (PARTITION BY r.job_id
      ORDER BY CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT job_id,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(CASE WHEN over_budget THEN 1 END), 0) AS over_count
FROM region_costs_step
GROUP BY job_id WITH ROLLUP
```

late_costs:

```sql
WITH region_costs_step AS (
  SELECT r.job_id, r.cost_cents, r.region, r.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(r.cost_cents) OVER (PARTITION BY r.job_id
      ORDER BY CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT job_id, dt, running_cost
FROM region_costs_step
WHERE running_cost > 1500
```

Toolbox code, with `<database>` as ops. The dt-as-date ordering needs CONCAT and SUBSTR, which have no name in files 03, 04 and 05 (file 10 covers them). Here the window orders by the text dt, which sorts the same way for yyyymmdd.

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, count_rows, derived,
                              equals, fill_null, if_else, more_than, rollup, statement,
                              sum_of, window)
from references.ops__region_costs import region_costs
from references.ops__jobs import jobs
from references.ops__region_budgets import region_budgets

# window() has rows= and no RANGE. Each job has one row per dt in the sample, so no ties are lost.
# The Hive above keeps the RANGE, and project.convert checks it.
run_so_far = window(PARTITION_BY=region_costs.job_id, ORDER_BY=region_costs.dt, rows=(None, 0))
step = derived("region_costs_step", statement(
    SELECT(region_costs.job_id, region_costs.cost_cents, region_costs.region, region_costs.dt,
           jobs.job_name,
           AS(region_budgets.budget_cents, "budget"),
           AS(if_else(more_than(fill_null(region_costs.cost_cents, 0), region_budgets.budget_cents),
                      True, False), "over_budget"),
           AS(fill_null(sum_of(region_costs.cost_cents, over=run_so_far), 0), "running_cost")),
    FROM(region_costs, reads_all_partitions=True),  # a workbook's formula reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, region_costs.job_id), reads_all_partitions=True),
    LEFT_JOIN(region_budgets, ON=equals(region_budgets.job_id, region_costs.job_id),
              reads_all_partitions=True),
))

job_totals = statement(
    SELECT(step.job_id,
           AS(fill_null(sum_of(step.cost_cents), 0), "total_cents"),
           AS(count_rows(where=equals(step.over_budget, True)), "over_count")),
    FROM(step),
    GROUP_BY(rollup(step.job_id)),  # the Total Row, as a Subtotal row
)

late_costs = statement(
    SELECT(step.job_id, step.dt, step.running_cost),
    FROM(step),
    WHERE(more_than(step.running_cost, 1500)),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X70

**Map**

- Sources: jobs, job_owners, job_runs.
- Steps: the query staffed, which is connection only and which owner_load reads. The query owner_load, which busiest_owner reads. Each is a CTE.
- Finals: owner_load (owner, total_mins, runs, avg_mins), `owner_load (Total Row)`, and busiest_owner (owner, total_mins, runs).
- Nothing reads the owner_load Table, so the Table is a final: its query's rows plus the formula column avg_mins. busiest_owner reads the owner_load query, never the Table, so avg_mins is not in it.
- Value typed over a formula: none.
- staffed: Table.Distinct of job_owners' job_id and owner, an Inner join to jobs, and `[owner] <> null`, which is `owner IS NOT NULL`. That leaves out job 4, whose owner is blank.
- owner_load: a LeftOuter join to job_runs and a GROUP BY owner. `Table.RowCount(_)` is COUNT(*).
- avg_mins is `total_mins / runs`, a row-level formula.
- Total Row: SUBTOTAL(109, runs), a SUM. owner_load is a query-loaded Table and not a summary, so the Total Row is a query of its own, one row, with no label.
- busiest_owner: Table.Sort then FirstN 1 is `ORDER BY runs DESC LIMIT 1`.
- Blank: none that a formula reads.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

owner_load:

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
), owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs, total_mins / runs AS avg_mins
FROM owner_load
```

owner_load (Total Row):

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
), owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT SUM(runs) AS runs
FROM owner_load
```

busiest_owner:

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
), owner_load AS (
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

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, JOIN, LEFT_JOIN, LIMIT, ORDER_BY, SELECT,
                              SELECT_DISTINCT, WHERE, count_rows, derived, descending, equals,
                              is_not_null, statement, sum_of)
from references.ops__jobs import jobs
from references.ops__job_owners import job_owners
from references.ops__job_runs import job_runs

# every read below is a workbook's query, which reads every row
o = derived("o", statement(
    SELECT_DISTINCT(job_owners.job_id, job_owners.owner),
    FROM(job_owners, reads_all_partitions=True),
))
staffed = derived("staffed", statement(
    SELECT(jobs.job_id, jobs.job_name, o.owner),
    FROM(jobs, reads_all_partitions=True),
    # job 3 has two owners and the query keeps both, so many_matches=True
    JOIN(o, ON=equals(o.job_id, jobs.job_id), many_matches=True),
    WHERE(is_not_null(o.owner)),
))
owner_load = derived("owner_load", statement(
    SELECT(staffed.owner, AS(sum_of(job_runs.duration_mins), "total_mins"),
           AS(count_rows(), "runs")),
    FROM(staffed),
    # a job has many runs and the query keeps each one, so many_matches=True
    LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, staffed.job_id), many_matches=True,
              reads_all_partitions=True),
    GROUP_BY(staffed.owner),
))

owner_load_s = statement(
    SELECT(owner_load.owner, owner_load.total_mins, owner_load.runs,
           AS(owner_load.total_mins / owner_load.runs, "avg_mins")),
    FROM(owner_load),
)
owner_load_total = statement(
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

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X73

**Map**

- Sources: region_budgets, jobs.
- Steps: the query eu_budgets, which the eu_count query reads. It is a CTE in eu_count's query.
- Finals: eu_budgets (job_id, budget_cents, region, job_name, dollars) and eu_count (region, jobs, total_cents).
- The eu_budgets Table is read by nothing, since eu_count reads the query, never the Table. So the Table is a final: its query's rows plus the formula column `dollars`. eu_count does not have `dollars`.
- Value typed over a formula: none.
- eu_budgets: `[region] = "eu"` is a WHERE. The Inner join to jobs expands only job_name, so region is region_budgets' region. `dollars` is `budget_cents / 100`.
- eu_count: a GROUP BY region. `Table.RowCount(_)` is COUNT(*) and `List.Sum` is SUM.
- Blank: none.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

eu_budgets:

```sql
SELECT b.job_id, b.budget_cents, b.region, j.job_name,
  b.budget_cents / 100 AS dollars
FROM <database>.region_budgets b
JOIN <database>.jobs j ON b.job_id = j.job_id
WHERE b.region = 'eu'
```

eu_count:

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

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, JOIN, SELECT, WHERE, count_rows, derived,
                              equals, statement, sum_of)
from references.ops__region_budgets import region_budgets
from references.ops__jobs import jobs

eu_budgets = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           jobs.job_name, AS(region_budgets.budget_cents / 100, "dollars")),
    FROM(region_budgets, reads_all_partitions=True),  # a workbook's query reads every row
    JOIN(jobs, ON=equals(jobs.job_id, region_budgets.job_id), reads_all_partitions=True),
    WHERE(equals(region_budgets.region, "eu")),
)

eu_rows = derived("eu_budgets", statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           jobs.job_name),
    FROM(region_budgets, reads_all_partitions=True),
    JOIN(jobs, ON=equals(jobs.job_id, region_budgets.job_id), reads_all_partitions=True),
    WHERE(equals(region_budgets.region, "eu")),
))
eu_count = statement(
    SELECT(eu_rows.region, AS(count_rows(), "jobs"),
           AS(sum_of(eu_rows.budget_cents), "total_cents")),
    FROM(eu_rows),
    GROUP_BY(eu_rows.region),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.

## X74

**Map**

- Sources: job_runs, and run_alerts' typed columns (alert_id, run_id, severity, dt) as the database table run_alerts.
- Steps: run_alerts, because it has formulas (status, job_id, alerts_so_far) and by_status and the late_alerts query read it. It is the CTE `run_alerts_step` in each final's query.
- Finals: by_status (status, alerts) and late_alerts (alert_id, run_id, alerts_so_far).
- Value typed over a formula: none.
- In the step:
  - status and job_id are XLOOKUPs into job_runs, so they are one LEFT JOIN.
  - alerts_so_far is `COUNTIFS(run_alerts[run_id], "<="&[@run_id])` over its own Table. It is a running count with ties included, so it is a RANGE window.
- by_status is a summary: its only typed column, status, is what its COUNTIFS matches on. It is a GROUP BY status of the step, with COALESCE(COUNT(*), 0). It has no Total Row.
- late_alerts: the query filters on the Table's formula column `alerts_so_far`, so it reads the step.
- Blank: none that a formula reads.
- Refused: none. Left alone: nothing.
- Fill in: `<database>`.

by_status:

```sql
WITH run_alerts_step AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt, r.status, r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT status, COALESCE(COUNT(*), 0) AS alerts
FROM run_alerts_step
GROUP BY status
```

late_alerts:

```sql
WITH run_alerts_step AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt, r.status, r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM run_alerts_step
WHERE alerts_so_far > 5
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, count_rows, derived,
                              equals, fill_null, more_than, statement, window)
from references.ops__run_alerts import run_alerts
from references.ops__job_runs import job_runs

# window() has rows= and no RANGE, so alerts of one run (97, 101, 103) count one at a time here.
# The Hive above has the RANGE that counts ties as Excel does, and project.convert checks it.
so_far = window(ORDER_BY=run_alerts.run_id, rows=(None, 0))
step = derived("run_alerts_step", statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           job_runs.status, job_runs.job_id,
           AS(count_rows(over=so_far), "alerts_so_far")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's formula reads every row
    LEFT_JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id),
              reads_all_partitions=True),
))

by_status = statement(
    SELECT(step.status, AS(fill_null(count_rows(), 0), "alerts")),
    FROM(step),
    GROUP_BY(step.status),
)

late_alerts = statement(
    SELECT(step.alert_id, step.run_id, step.alerts_so_far),
    FROM(step),
    WHERE(more_than(step.alerts_so_far, 5)),
)
```

Take out of the workbook what you don't want converted. Fill in each `<...>`. Run `project.convert` on the Hive. Its checked code wins where the two differ.
