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
