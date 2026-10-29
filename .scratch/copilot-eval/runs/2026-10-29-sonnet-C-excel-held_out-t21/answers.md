date: 2026-10-29
arm: C
model: sonnet
files: 6fc91ff

## X21

**Map**
- Sources: region_budgets.
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin).
- Typed over a formula: none. Marks: none (no blank in a column a formula reads). Refusals: none. Left alone: nothing outside the Tables (Steps, Parameters and Keys are none; the Keys Table is empty, which is fine as nothing is typed over).
- Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets
```

Toolbox code, with `<database>` as the same database you fill in above:

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

Take out of the workbook anything you don't want converted, fill in each `<...>`, then run `project.convert` on the Hive. Its checked code wins where the two differ.

## X22

**Map**
- Sources: jobs.
- Steps: none.
- Finals: jobs (job_id, job_name, team, is_finance, ratio).
- Typed over: none. Marks: none (no blank in the sample). Refusals: none. Left alone: nothing.
- `ratio` is `IFERROR(a / b, 0)`, so `COALESCE(a / b, 0)`: a divide by 0 is NULL in Hive (job_id 2 gives 0, as in Excel).
- Fill in: `<database>`.

```sql
SELECT job_id, job_name, team,
  IF(team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(job_id / (job_id - 2), 0) AS ratio
FROM <database>.jobs
```

```python
from sqlglot_composer import (AS, FROM, SELECT, equals, fill_null, if_else, statement)
from references.<database>__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(if_else(equals(jobs.team, "finance"), "yes", "no"), "is_finance"),
           AS(fill_null(jobs.job_id / (jobs.job_id - 2), 0), "ratio")),
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X23

**Map**
- Sources: job_runs.
- Steps: none.
- Finals: job_runs (run_id, status, avg_retry_secs, label, risky).
- Typed over: none. Refusals: none. Left alone: nothing.
- Mark, blank: run 98 has a blank `status` and a blank `avg_retry_secs`, which the formulas read. Excel reads a blank as "" or 0, Hive as NULL, so `status` is wrapped in `COALESCE(status, '')` and `avg_retry_secs` in `COALESCE(avg_retry_secs, 0)`. Without it `risky` for run 98 would be NULL, not FALSE.
- `_xlfn.` is only Excel's prefix. `SWITCH` becomes a `CASE x WHEN`, and `OR` stays `OR`.
- Fill in: `<database>`.

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

status = fill_null(job_runs.status, "")  # blank
s = statement(
    SELECT(job_runs.run_id, job_runs.status, job_runs.avg_retry_secs,
           AS(first_match([(equals(status, "SUCCESS"), "ok"),
                           (equals(status, "FAILED"), "bad")], otherwise="other"), "label"),
           AS(if_else(any_of(equals(status, "FAILED"),
                             more_than(fill_null(job_runs.avg_retry_secs, 0), 5)),
                      True, False), "risky")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X24

**Map**
- Sources: team_notes.
- Steps: none.
- Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars).
- Typed over: none. Marks: none (no blank). Refusals: none. Left alone: nothing.
- `written_on` is read as a date in ISO form (`2026-09-11`); if it is held as text, `MONTH` still reads it in Hive.
- `FIND(" ", note)` is `INSTR(note, ' ')`; `LEFT(x, n)` is `SUBSTR(x, 1, n)`; `LEN` is `LENGTH`.
- Fill in: `<database>`.

```sql
SELECT team, note, written_on,
  SUBSTR(note, 1, INSTR(note, ' ') - 1) AS first_word,
  UPPER(team) AS shout,
  MONTH(written_on) AS month,
  ROUND(LENGTH(note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes
```

Toolbox code. The loaded files (03, 04, 05) have no names for SUBSTR, INSTR, UPPER, MONTH, LENGTH or ROUND, so I have not made any up. The plain columns are below; the five calculated columns are in the Hive above, so run `project.convert` on it to get checked code for them (or load file 10 in a new chat, which covers Hive functions).

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__team_notes import team_notes

s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on),
    # first_word, shout, month and tens_of_chars: add from project.convert's code for the Hive above
    FROM(team_notes, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X25

**Map**
- Sources: Costs, Budgets.
- Steps: none.
- Finals: Costs (Job, `<cost_cents>`, Region, `<day_key>`, Day), Budgets (Job, Budget, Region, Dollars).
- Typed over: none. Refusals: none. Left alone: nothing.
- Names: the headers `Cost (cents)` and `Day Key` are not plain names, so they are `<cost_cents>` and `<day_key>`. Fill them in, and the database `<database>`, from your warehouse; I have not guessed them. The Tables `Costs` and `Budgets` and the headers `Job`, `Budget`, `Region`, `Dollars`, `Day` are plain, so I kept them.
- Mark, date held as text: `Day Key` (such as 20260911) is a date held as text, so `Day` is written with `CONCAT(SUBSTR(..., 1, 4), '-', SUBSTR(..., 5, 2), '-', SUBSTR(..., 7, 2))`.
- Blank: Costs row 29 has a blank `Cost (cents)`, but no formula reads that column, so I did not wrap it. The row is kept.
- No Keys row: nothing is typed over a formula, so none is needed.

Costs:

```sql
SELECT Job, <cost_cents>, Region, <day_key>,
  CONCAT(SUBSTR(<day_key>, 1, 4), '-', SUBSTR(<day_key>, 5, 2), '-', SUBSTR(<day_key>, 7, 2)) AS Day
FROM <database>.Costs
```

Budgets:

```sql
SELECT Job, Budget, Region,
  Budget / 100 AS Dollars
FROM <database>.Budgets
```

Toolbox code. Files 03 to 05 have no CONCAT or SUBSTR name, so `Day` is left to `project.convert` (or file 10, in a new chat).

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__costs import costs
from references.<database>__budgets import budgets

costs_s = statement(
    SELECT(costs.Job, costs.<cost_cents>, costs.Region, costs.<day_key>),
    # Day: add from project.convert's code for the Costs Hive above
    FROM(costs, reads_all_partitions=True),  # a workbook's query reads every row
)

budgets_s = statement(
    SELECT(budgets.Job, budgets.Budget, budgets.Region,
           AS(budgets.Budget / 100, "Dollars")),
    FROM(budgets, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X26

**Map**
- Sources: run_alerts, job_runs.
- Steps: none (job_runs is read by run_alerts, but it has no formula and no query, so it is only a source).
- Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins).
- Typed over: none. Refusals: none. Left alone: nothing.
- `job_id`: XLOOKUP on `run_id`, a `LEFT JOIN` of job_runs, then its `job_id`. `status`: `VLOOKUP(.., job_runs, 3, FALSE)` is column 3 of job_runs, `status`, by the same join. `avg_mins`: AVERAGEIFS over another Table, a `LEFT JOIN` of a `GROUP BY job_id` with `AVG`, left NULL as Excel gives an error where nothing matches.
- Mark, blank: job_runs row 98 has a blank `status`, which `status` here reads, so it is wrapped in `COALESCE(.., '')`. No alert points to run 98, so no row changes. (Excel would show a blank lookup as 0.) `duration_mins` has no blank.
- Fill in: `<database>`.

```sql
SELECT a.alert_id, a.run_id, a.severity,
  r.job_id AS job_id,
  COALESCE(r.status, '') AS status,
  m.avg_mins AS avg_mins
FROM <database>.run_alerts a
LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins
           FROM <database>.job_runs
           GROUP BY job_id) m ON r.job_id = m.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, derived,
                              equals, fill_null, statement)
from references.<database>__run_alerts import run_alerts
from references.<database>__job_runs import job_runs

r = AS(job_runs, "r")
m = derived("m", statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity,
           AS(r.job_id, "job_id"),
           AS(fill_null(r.status, ""), "status"),  # blank
           m.avg_mins),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(r, ON=equals(r.run_id, run_alerts.run_id), reads_all_partitions=True),
    LEFT_JOIN(m, ON=equals(m.job_id, r.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X27

**Map**
- Sources: jobs.
- Steps: none.
- Finals: by_team (team, jobs_in_team, last_job_id, last_job_name). by_team's only typed column, `team`, is what its COUNTIFS and MAXIFS match on, so it is a summary: a `GROUP BY team` of jobs.
- Typed over: none. Marks: none (no blank). Refusals: none. Left alone: nothing.
- `COUNTIFS` is `COUNT(*)` and `MAXIFS` is `MAX`, each with `COALESCE(.., 0)`. `last_job_name` is `INDEX/MATCH`, so a `LEFT JOIN` of jobs on `last_job_id`, then `job_name`.
- Fill in: `<database>`.

```sql
SELECT g.team, g.jobs_in_team, g.last_job_id,
  j.job_name AS last_job_name
FROM (SELECT team,
        COALESCE(COUNT(*), 0) AS jobs_in_team,
        COALESCE(MAX(job_id), 0) AS last_job_id
      FROM <database>.jobs
      GROUP BY team) g
LEFT JOIN <database>.jobs j ON g.last_job_id = j.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, fill_null, max_of, statement)
from references.<database>__jobs import jobs

g = derived("g", statement(
    SELECT(jobs.team,
           AS(fill_null(count_rows(), 0), "jobs_in_team"),
           AS(fill_null(max_of(jobs.job_id), 0), "last_job_id")),
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(jobs.team),
))
j = AS(jobs, "j")
s = statement(
    SELECT(g.team, g.jobs_in_team, g.last_job_id, AS(j.job_name, "last_job_name")),
    FROM(g),
    LEFT_JOIN(j, ON=equals(j.job_id, g.last_job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X28

**Map**
- Sources: jobs, job_runs.
- Steps: none.
- Finals: jobs (job_id, job_name, ok_mins).
- Typed over: `ok_mins` where `job_id` is 3 (the value 99). The Keys row says jobs, job_id, so I matched the row on `job_id`.
- Marks: job_runs row 98 has a blank `status`; SUMIFS skips a blank, so I did not wrap it. Refusals: none. Left alone: nothing.
- `ok_mins` is SUMIFS over another Table: a `LEFT JOIN` of a `GROUP BY job_id` with `WHERE status = 'SUCCESS'`, with `COALESCE(.., 0)` as Excel gives 0 where nothing matches.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name,
  CASE WHEN j.job_id = 3 THEN 99 ELSE COALESCE(r.total, 0) END AS ok_mins
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total
           FROM <database>.job_runs
           WHERE status = 'SUCCESS'
           GROUP BY job_id) r ON j.job_id = r.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, derived, equals,
                              fill_null, first_match, statement, sum_of)
from references.<database>__jobs import jobs
from references.<database>__job_runs import job_runs

r = derived("r", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(first_match([(equals(jobs.job_id, 3), 99)],
                          otherwise=fill_null(r.total, 0)), "ok_mins")),
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(r, ON=equals(r.job_id, jobs.job_id)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X29

**Map**
- Sources: region_budgets. (Parameters is none.)
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer).
- Typed over: `in_dollars` in the row where `job_id` is 3 (the value 5). There is no Keys row for region_budgets, so I matched every typed column of that row (`job_id` 3, `budget_cents` 350, `region` 'us').
- Parameters: `XLOOKUP("cents_per_dollar", Parameters[name], Parameters[value])` is its value, 100.
- Refused: `pointer` (`INDIRECT("A"&ROW())`, and ROW() hangs on the order of the sheet's rows), so `NULL AS pointer`.
- Marks: none (no blank). Left alone: nothing.
- Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  CASE WHEN job_id = 3 AND budget_cents = 350 AND region = 'us' THEN 5
       ELSE budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets
```

Toolbox code. There is no name in files 03 to 05 for a NULL column, so `pointer` is left out of the Python; `project.convert` on the Hive above will carry it.

```python
from sqlglot_composer import (AS, FROM, SELECT, all_of, equals, first_match, statement)
from references.<database>__region_budgets import region_budgets

rb = region_budgets
s = statement(
    SELECT(rb.job_id, rb.budget_cents, rb.region,
           AS(first_match([(all_of(equals(rb.job_id, 3), equals(rb.budget_cents, 350),
                                   equals(rb.region, "us")), 5)],
                          otherwise=rb.budget_cents / 100), "in_dollars")),
    # pointer: NULL, refused; add from project.convert's code
    FROM(rb, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X30

**Map**
- Sources: scheduler_runs.
- Steps: none.
- Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter).
- Typed over: none. Marks: none (no blank).
- Refused: `prev_run` (`OFFSET`, which hangs on the order of the rows) and `jitter` (`RANDBETWEEN`, random), each `NULL AS`.
- Left alone: the bar chart on sheet "Summary" and the PivotTable on sheet "Pivot" (from scheduler_runs).
- `day` is `RIGHT(dt, 2)`, `SUBSTR(dt, -2)`.
- Fill in: `<database>`.

```sql
SELECT run_id, job_id, dt,
  SUBSTR(dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs
```

Toolbox code. Files 03 to 05 have no SUBSTR or NULL name, so `day`, `prev_run` and `jitter` come from `project.convert` (or file 10, in a new chat).

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__scheduler_runs import scheduler_runs

s = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    # day, prev_run, jitter: add from project.convert's code for the Hive above
    FROM(scheduler_runs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X31

**Map**
- Sources: jobs.
- Steps: none.
- Finals: jobs (job_id, team, bump, tag, scaled, boosted).
- Typed over: none. Marks: none (no blank).
- Refused, each `NULL AS`:
  - `bump` reads its own column (`jobs[[#This Row],[bump]]*2`), circular.
  - `tag` is `TAG`, a defined name holding a LAMBDA.
  - `scaled` reads `Summary!$D$4` (cell D4), a cell outside a Table that isn't a defined name.
- Converted with a mark: `boosted` reads the defined name `boost`, which is the cell `Summary!B2` outside a Table. I used its value, 10. Move it into the Parameters Table.
- Left alone: the cells outside a Table on sheet "Summary" (B2 and D4).
- Fill in: `<database>`.

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
           # bump, tag, scaled: NULL, refused; add from project.convert's code
           AS(jobs.job_id * 10, "boosted")),  # boost = Summary!B2 = 10, to move into Parameters
    FROM(jobs, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X32

**Map**
- Sources: job_runs, jobs.
- Steps: job_runs (it adds `job_name`, and by_name reads it), a CTE inside by_name's query. It is read by another Table, so it is not a final and has no block of its own.
- Finals: by_name (job_name, runs). by_name's only typed column, `job_name`, is what its COUNTIFS matches on, so it is a summary: a `GROUP BY job_name` of job_runs.
- Typed over: none. Refusals: none. Left alone: nothing.
- Marks: `VLOOKUP(.., jobs, 2, TRUE)` is approximate; I converted it exactly (a `LEFT JOIN` on `job_id`), so check that the jobs' ids are what you meant. job_runs has blanks in `status` and `avg_retry_secs` but no formula reads them, so I did not wrap them.
- `COUNTIFS` is `COUNT(*)` with `COALESCE(.., 0)`.
- Fill in: `<database>`.

```sql
WITH job_runs_step AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name AS job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT job_name, COALESCE(COUNT(*), 0) AS runs
FROM job_runs_step
GROUP BY job_name
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, fill_null, statement)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

job_runs_step = derived("job_runs_step", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt, jobs.job_name),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
))
s = statement(
    SELECT(job_runs_step.job_name, AS(fill_null(count_rows(), 0), "runs")),
    FROM(job_runs_step),
    GROUP_BY(job_runs_step.job_name),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X33

**Map**
- Sources: none in the workbook. The query reads `Sql.Database("dwh01", "ops")`, item `job_runs`, a non-workbook source, so I used the table it names, `job_runs`. Check which server, database and schema that is (dwh01, ops, ops) and fill in `<database>`.
- Steps: none.
- Finals: slow_runs (run_id, duration_mins, over_by), the Table the query "slow_runs" loads.
- Typed over: none. Refusals: none. Left alone: nothing.
- Marks: M's `<>` keeps a null, as Hive's doesn't, so `status <> 'TEST'` is `(status <> 'TEST' OR status IS NULL)`. TransformColumnTypes and `type number` change nothing.
- Fill in: `<database>`.

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
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins - 20, "over_by")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(at_least(job_runs.duration_mins, 20),
          any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X34

**Map**
- Sources: job_runs, jobs.
- Steps: runs_with_team (a connection-only query that team_totals reads), a CTE inside team_totals' query.
- Finals: team_totals (team, total_mins, longest), the Table the query "team_totals" loads.
- Typed over: none. Marks: none. Refusals: none. Left alone: nothing.
- `NestedJoin` with `LeftOuter` then `ExpandTableColumn` is a `LEFT JOIN`. `List.Sum` and `List.Max` are `SUM` and `MAX`.
- Fill in: `<database>`.

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
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals, max_of,
                              statement, sum_of)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

runs_with_team = derived("runs_with_team", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt, jobs.team),
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

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X35

**Map**
- Sources: job_runs, scheduler_runs.
- Steps: none.
- Finals: recent (run_id, dt), the Table the query "recent" loads.
- Left out and named: the query "rates" (connection only, nothing reads it). It reads `Web.Contents("https://rates.example.com/today.json")`, a web source, which is refused, so I left it out.
- Typed over: none. Marks: none. Left alone: nothing else.
- `Table.Combine` is `UNION ALL`. `Table.Sort` then `FirstN` is `ORDER BY run_id DESC LIMIT 4`, which I kept as it has a LIMIT. Where run_ids tie, which row Hive keeps is not fixed.
- Fill in: `<database>`.

```sql
SELECT run_id, dt
FROM (
  SELECT run_id, dt FROM <database>.job_runs
  UNION ALL
  SELECT run_id, dt FROM <database>.scheduler_runs
) both_runs
ORDER BY run_id DESC
LIMIT 4
```

```python
from sqlglot_composer import (FROM, LIMIT, ORDER_BY, SELECT, UNION_ALL, derived, descending,
                              statement)
from references.<database>__job_runs import job_runs
from references.<database>__scheduler_runs import scheduler_runs

both_runs = derived("both_runs", UNION_ALL(
    statement(SELECT(job_runs.run_id, job_runs.dt),
              FROM(job_runs, reads_all_partitions=True)),  # a workbook's query reads every row
    statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt),
              FROM(scheduler_runs, reads_all_partitions=True)),
))
s = statement(
    SELECT(both_runs.run_id, both_runs.dt),
    FROM(both_runs),
    ORDER_BY(descending(both_runs.run_id)),
    LIMIT(4),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X36

**Map**
- Sources: run_alerts, job_runs.
- Steps: none (run_alerts is read, but it has no formula or query of its own, so it is only a source).
- Finals: severity_by_day (dt, high, low), loaded by the query "severity_by_day"; job_runs (run_id, status, alerts).
- Typed over: none. Refusals: none. Left alone: nothing.
- `alerts`: COUNTIFS over another Table, a `LEFT JOIN` of a `GROUP BY run_id` with `COUNT(*)` and `COALESCE(.., 0)`. job_runs has a blank `status` (run 98), but no formula reads it, so no wrap.
- `Table.Pivot`: a `SUM(CASE WHEN severity = '..' THEN 1 END)` column per value in the sample (high, low), NULL where none, as M leaves it. The pivot's columns are now fixed: a new severity in the data will not get a column.
- Fill in: `<database>`.

severity_by_day:

```sql
SELECT dt,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
GROUP BY dt
```

job_runs:

```sql
SELECT r.run_id, r.status,
  COALESCE(a.total, 0) AS alerts
FROM <database>.job_runs r
LEFT JOIN (SELECT run_id, COUNT(*) AS total
           FROM <database>.run_alerts
           GROUP BY run_id) a ON r.run_id = a.run_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, fill_null, statement)
from references.<database>__run_alerts import run_alerts
from references.<database>__job_runs import job_runs

# severity_by_day. count_rows(where=...) gives 0 where the SQL above gives NULL: check it
severity_by_day = statement(
    SELECT(run_alerts.dt,
           AS(count_rows(where=equals(run_alerts.severity, "high")), "high"),
           AS(count_rows(where=equals(run_alerts.severity, "low")), "low")),
    FROM(run_alerts, reads_all_partitions=True),  # a workbook's query reads every row
    GROUP_BY(run_alerts.dt),
)

# job_runs
a = derived("a", statement(
    SELECT(run_alerts.run_id, AS(count_rows(), "total")),
    FROM(run_alerts, reads_all_partitions=True),
    GROUP_BY(run_alerts.run_id),
))
job_runs_s = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(fill_null(a.total, 0), "alerts")),
    FROM(job_runs, reads_all_partitions=True),
    LEFT_JOIN(a, ON=equals(a.run_id, job_runs.run_id)),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X37

**Map**
- Sources: Owners.
- Steps: none.
- Finals: Owners (`<job_no>`, `<team_name>`, Owner, Day, `<is_ana>`).
- Typed over: none. Refusals: none. Left alone: nothing.
- Names: the headers `Job No`, `Team Name` and `Is Ana` are not plain, so `<job_no>`, `<team_name>` and `<is_ana>`; fill them in with your warehouse's names (I have not guessed them), and fill in `<database>`. `Owner`, `Day` and the Table `Owners` are plain, so I kept them.
- Mark, blank: `Owner` is blank for the web jobs (job 4 on every day), and `Is Ana` reads it. Excel reads that as "", Hive as NULL, so I wrapped it: `COALESCE(Owner, '')`.

```sql
SELECT <job_no>, <team_name>, Owner, Day,
  IF(COALESCE(Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners
```

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.<database>__owners import owners

s = statement(
    SELECT(owners.<job_no>, owners.<team_name>, owners.Owner, owners.Day,
           AS(if_else(equals(fill_null(owners.Owner, ""), "ana"), 1, 0), "<is_ana>")),  # blank
    FROM(owners, reads_all_partitions=True),  # a workbook's query reads every row
)
```

Take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X38

**Map**
- Sources: job_runs, jobs.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost).
- Typed over: `retry_cost` where `run_id` is 102 (the value 1). The Keys row says job_runs, run_id, so I matched the row on `run_id`.
- Refusals: none. Left alone: nothing.
- `region`: XLOOKUP, a `LEFT JOIN` of jobs on `job_id`. `region_mins`: SUMIFS over its own Table, so `SUM(duration_mins) OVER (PARTITION BY region)` (the joined region), with `COALESCE(.., 0)`.
- Mark, blank: run 98 has a blank `avg_retry_secs`, which `retry_cost` reads, so I wrapped it in `COALESCE(.., 0)`. The blank `status` is not read.
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

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, equals, fill_null, first_match,
                              statement, sum_of, window)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

by_region = window(PARTITION_BY=jobs.region)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs,
           AS(jobs.region, "region"),
           AS(fill_null(sum_of(job_runs.duration_mins, over=by_region), 0), "region_mins"),
           AS(first_match([(equals(job_runs.run_id, 102), 1)],
                          otherwise=(fill_null(job_runs.avg_retry_secs, 0)  # blank
                                     + job_runs.duration_mins) * 2), "retry_cost")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X39

**Map**
- Sources: job_runs, jobs.
- Steps: none. The query "ok_runs" is read by no other query, so it is not a step: it is the query of its final.
- Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise): the Table the query loads, with the formula columns it adds.
- Typed over: none. Left alone: nothing.
- Refused: `noise` (`RAND()`), so `NULL AS noise`.
- `job_name`: XLOOKUP, a `LEFT JOIN` of jobs. `share`: SUMIFS over its own Table (the rows the query keeps), so `SUM(duration_mins) OVER (PARTITION BY job_id)`, with `COALESCE(.., 0)`. A 0 there makes the share NULL, where Excel gives an error.
- Marks: the blank `status` (run 98) is only read by the query's `WHERE`, which skips it as M's `=` does, so no wrap.
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

Toolbox code. There is no name in files 03 to 05 for a NULL column, so `noise` is left to `project.convert`.

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, WHERE, equals, fill_null, statement,
                              sum_of, window)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

by_job = window(PARTITION_BY=job_runs.job_id)
s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins,
           AS(jobs.job_name, "job_name"),
           AS(job_runs.duration_mins / fill_null(sum_of(job_runs.duration_mins, over=by_job), 0),
              "share")),
    # noise: NULL, refused; add from project.convert's code
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
    WHERE(equals(job_runs.status, "SUCCESS")),
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X40

**Map**
- Sources: Runs (Run, Job, Mins), jobs (job_id, team), run_alerts. Parameters and Keys are none. From Parameters, `rate` is 2, so I used its value.
- Steps: Runs adds Team and Cost, and Teams and run_alerts read it, so it is a step (a CTE) and not a final.
- Finals: Teams (Team, Total Cost), a summary: a GROUP BY of Runs. run_alerts (alert_id, run_id, severity, dt, Run Mins).
- Typed over a formula: none. Refusals: none.
- Left alone: the PivotTable on sheet "Pivot".
- Fill in: `<database>`. The headers with spaces become `<total_cost>` (Total Cost) and `<run_mins>` (Run Mins).

Teams:

```sql
WITH runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT Team, COALESCE(SUM(Cost), 0) AS <total_cost>
FROM runs
GROUP BY Team
```

run_alerts (Run and Mins are typed in Runs, so it reads the table directly):

```sql
SELECT a.alert_id, a.run_id, a.severity, a.dt, r.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN <database>.Runs r ON a.run_id = r.Run
```

Next: take out of the workbook what you don't want converted, fill in each `<...>`, and run `project.convert` on the Hive. Its checked code wins where the two differ. I gave the Hive you asked for. Ask if you also want the Toolbox code.

## X46

**Map**
- Sources: job_runs (read for job_id, duration_mins). Parameters and Keys are none.
- Steps: none.
- Finals: jobs (job_id, job_name, team, shortest, runs, busiest). It has typed columns, so it reads its own table, `<database>.jobs`, plus job_runs.
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- MINIFS and COUNTIF give 0 where nothing matches, as Excel does, so job 4, with no runs, gets shortest 0 and runs 0.
- busiest is RANK.EQ, highest runs first.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team,
  COALESCE(r.shortest, 0) AS shortest,
  COALESCE(r.runs, 0) AS runs,
  RANK() OVER (ORDER BY COALESCE(r.runs, 0) DESC) AS busiest
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, MIN(duration_mins) AS shortest, COUNT(*) AS runs
  FROM <database>.job_runs
  GROUP BY job_id
) r ON j.job_id = r.job_id
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X47

**Map**
- Sources: region_budgets. Parameters and Keys are none.
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- cheapest_first is RANK.EQ with 1 as the third argument, so ASC. region_total (SUMIF) is wrapped in COALESCE(.., 0), as Excel gives 0 where nothing matches. region_avg (AVERAGEIF) is left NULL.
- Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X48

**Map**
- Sources: job_runs, jobs, run_alerts. Parameters and Keys are none.
- Steps: none. No query reads another.
- Finals: quiet_runs (run_id, job_id, status). slow_regions (region, avg_mins, fastest).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- quiet_runs is a LeftAnti join, so it is a LEFT JOIN with `WHERE a.run_id IS NULL`, giving job_runs' columns only.
- slow_regions: the inner join expands region, and the filter on the grouped avg_mins becomes HAVING, repeating the aggregate.
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

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X49

**Map**
- Sources: job_runs, jobs, run_alerts, scheduler_runs, job_owners. Parameters and Keys are none.
- Steps: none.
- Finals: alert_status (alert_id, severity, status). run_check (run_id, status, scheduled_run). teams (team).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- alert_status is a RightOuter join, so it is a LEFT JOIN with the two tables swapped (job_runs first).
- run_check is a FullOuter join. The SelectColumns on job_runs is only the select list. Expanding run_id with the new name scheduled_run is an AS.
- teams is Table.Distinct over a Table.Combine, so UNION.
- Fill in: `<database>`.

alert_status:

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON a.run_id = r.run_id
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

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X50

**Map**
- Sources: job_owners, jobs. Parameters and Keys are none.
- Steps: none. The owners query is read only by its own Table's formulas, so it is not a step of another query.
- Finals: owners (job_id, owner, job_name, newest_first). It is the query plus the two formula columns its Table adds.
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Table.Distinct alone is SELECT DISTINCT. The window has to run after it, so I put the distinct rows in a CTE.
- newest_first is RANK.EQ with no third argument, so DESC, over the distinct rows. Job 3 appears twice, once per owner, so both rows rank equal.
- Fill in: `<database>`.

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

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X59

**Map**
- Sources: job_runs. Parameters and Keys are none.
- Steps: none.
- Finals: jobs (job_id, job_name, long_runs, failed_mins, not_test). run_alerts (alert_id, run_id, severity, dt, alerts_so_far).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - `"f*"` is `LOWER(status) LIKE 'f%'`, as Excel ignores case.
  - `"<>TEST"` is `(status <> 'TEST' OR status IS NULL)`, as Excel counts a blank there.
  - The blank status (run 98) sits inside -IFS forms, which skip a blank, so I did not wrap it.
  - All three jobs columns are wrapped in COALESCE(.., 0), as Excel gives 0 where nothing matches. Job 4 has no runs.
  - alerts_so_far, `"<="&[@run_id]` over its own Table, is a running count with ties included.
- Fill in: `<database>`.

jobs:

```sql
SELECT j.job_id, j.job_name,
  COALESCE(r.long_runs, 0) AS long_runs,
  COALESCE(r.failed_mins, 0) AS failed_mins,
  COALESCE(r.not_test, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id,
    COUNT(CASE WHEN duration_mins >= 20 THEN 1 END) AS long_runs,
    SUM(CASE WHEN LOWER(status) LIKE 'f%' THEN duration_mins END) AS failed_mins,
    COUNT(CASE WHEN (status <> 'TEST' OR status IS NULL) THEN 1 END) AS not_test
  FROM <database>.job_runs
  GROUP BY job_id
) r ON j.job_id = r.job_id
```

run_alerts:

```sql
SELECT alert_id, run_id, severity, dt,
  COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X60

**Map**
- Sources: region_budgets. Parameters and Keys are none.
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region). `region_budgets (Total Row)` (job_id, budget_cents).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- The Total Row is a query of its own: one row, a column per total, in order, with no label. SUBTOTAL(103) is a COUNT and 101 is an AVG. The "Total" label is left out.
- rank_in_region, COUNTIFS(.., "<"&[@budget_cents])+1, is RANK ASC within the region.
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

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X61

**Map**
- Sources: region_costs (read for region, cost_cents). Parameters and Keys are none.
- Steps: none.
- Finals: by_region (region, total_cents, entries, priciest). It is a summary: its only typed column, region, is what its SUMIFS, COUNTIFS and MAXIFS match on, so it is a GROUP BY of region_costs.
- Total Row: its totals only add up SUMs and COUNTs and take the MAX of MAXes. It needs no query of its own, so the query ends `GROUP BY region WITH ROLLUP`, which adds the total as one more row with region NULL (a Subtotal row). The "Total" label is left out.
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - blank: the sample has a blank cost_cents (job 2, 20260924). SUMIFS and MAXIFS skip it, as SUM and MAX skip NULL, so I did not wrap it. COUNTIFS still counts that row.
  - SUMIFS, COUNTIFS and MAXIFS are wrapped in COALESCE(.., 0).
  - dt is held as text (20260911), but no formula here reads it, so I did not convert it.
- Fill in: `<database>`.

```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(*), 0) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X62

**Map**
- Sources: team_notes (team, note, written_on). Parameters and Keys are none.
- Steps: none.
- Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - week_of is the Monday of the week, as week_start writes it. month_of is the first of the month, as month_start writes it. Both are text.
  - DATEDIF "m" is `FLOOR(MONTHS_BETWEEN(written_on, '2026-01-01'))`.
  - TEXTJOIN with TRUE is CONCAT_WS, which skips NULL.
  - The sample has no blanks in the columns the formulas read.
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

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X63

**Map**
- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs), scheduler_runs. Parameters and Keys are none.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - blank: the sample has a blank status (run 98), and `succeeded` reads it outside an -IF(S) form. SEARCH on a blank gives FALSE in Excel, so I wrapped it as COALESCE(status, '').
  - avg_retry_secs is blank in run 98, but ISBLANK is exactly `IS NULL`, so no wrap.
  - XLOOKUP's fourth argument, -1, is COALESCE(.., -1). Run 99 has no scheduler row and gets -1.
  - variance (VAR.S) and weighted (SUMPRODUCT) are whole-column windows over all rows.
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

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X64

**Map**
- Sources: jobs, region_costs. Parameters and Keys are none.
- Steps: none. No query reads another.
- Finals: picked_costs (job_id, cost_cents, region, size). costed_jobs (job_id, job_name, team, region). costs_filled (job_id, cost_cents, dt, day).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - M's `[cost_cents] <> null` is `IS NOT NULL`.
  - costed_jobs: `List.Contains(Costs[job_id], [job_id])` is a LEFT SEMI JOIN. The `not Text.StartsWith` is a NOT LIKE, and case is kept, as M keeps it.
  - costs_filled: the null cost (job 2, 20260924) becomes 0 by the query's own ReplaceValue.
  - dt is held as text (20260911). Text.End reads it as text, so it stays text and I did not convert it to a date.
  - No query sorts, so no order is lost.
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

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X65

**Map**
- Sources: jobs, region_budgets, job_owners, scheduler_runs, job_runs. Parameters and Keys are none.
- Steps: none read across queries. team_regions has two CTEs of its own, which are steps inside that query.
- Finals: team_regions (team, region). budget_places (job_id, budget_cents, region, place). jobs_per_team (team, jobs). ran_as_scheduled (run_id, dt). run_measures (run_id, job_id, measure, amount).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - The order was dropped. team_regions sorts by team with no FirstN or index after it, so there is no ORDER BY, as a Hive table holds no order. The same goes for the order of run_measures' rows.
  - budget_places sorts and then adds an index, so place is `ROW_NUMBER() OVER (ORDER BY budget_cents DESC)`, with no outer ORDER BY.
  - jobs_per_team: COUNT(DISTINCT job_id) leaves out NULL where M counts it as a value. job_id has no blank in the sample, so nothing changes here.
  - ran_as_scheduled: the NestedJoin on every column, in Table.Distinct, is INTERSECT.
  - run_measures: the unpivot is one SELECT per column, stacked with UNION ALL, each with `IS NOT NULL`, as M drops a null there. Run 98's blank avg_retry_secs is dropped.
- Fill in: `<database>`.

team_regions:

```sql
WITH teams AS (
  SELECT DISTINCT team FROM <database>.jobs
),
regions AS (
  SELECT DISTINCT region FROM <database>.jobs
)
SELECT t.team, r.region
FROM teams t
CROSS JOIN regions r
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

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X66

**Map**
- Sources: job_runs. Parameters and Keys are none.
- Steps: none.
- Finals: ok_runs (run_id, job_id, duration_mins, dt, running, share), the query plus its two formula columns. `ok_runs (Total Row)` (duration_mins).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - The window formulas run over the rows the filter keeps, which are the Table's rows.
  - running is a running total with ties included, as Excel's. It is wrapped in COALESCE(.., 0).
  - The Total Row is a query of its own: one row, one column, no label. The "Total" label is left out.
  - The status blank is in the query's M filter, where `status IS NOT NULL` handles it.
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
SELECT SUM(duration_mins) AS duration_mins
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X69

**Map**
- Sources: jobs, region_budgets, region_costs (the typed columns job_id, cost_cents, region, dt). Parameters and Keys are none.
- Steps: region_costs with its formula columns (job_name, budget, over_budget, running_cost). job_totals and late_costs read it, so it is a CTE, `costs`, in each of their queries. It is not a final.
- Finals: job_totals (job_id, total_cents, over_count), a summary: its only typed column, job_id, is what its SUMIFS and COUNTIFS match on, so it is a GROUP BY of costs. late_costs (job_id, dt, running_cost).
- Total Row of job_totals: it only adds up a SUM and a COUNT, so it needs no query of its own. The query ends `GROUP BY job_id WITH ROLLUP`, which adds the total as one more row with job_id NULL (a Subtotal row). The "Total" label is left out.
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - blank: the sample has a blank cost_cents (job 2, 20260924). over_budget reads it, so I wrapped it as COALESCE(cost_cents, 0). The SUMIFS skips it, as SUM skips NULL, so I did not wrap that.
  - dt is held as text (20260911). I compare it as a date, so the window orders by `CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2))`. The dt column itself passes through unchanged.
  - running_cost is a running total per job, ties included.
  - The XLOOKUPs are LEFT JOINs on job_id.
  - COUNTIFS on over_budget TRUE counts only the rows where the Condition is true.
- Fill in: `<database>`.

job_totals:

```sql
WITH costs AS (
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
  COALESCE(COUNT(CASE WHEN over_budget = TRUE THEN 1 END), 0) AS over_count
FROM costs
GROUP BY job_id WITH ROLLUP
```

late_costs:

```sql
WITH costs AS (
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
FROM costs
WHERE running_cost > 1500
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X70

**Map**
- Sources: jobs, job_owners, job_runs. Parameters and Keys are none.
- Steps:
  - staffed, a connection-only query that owner_load reads, so it is a CTE.
  - The owner_load query, which busiest_owner reads, so it is a CTE. The query and the Table it loads are read apart.
- Finals:
  - owner_load, the Table, which nothing reads: (owner, total_mins, runs, avg_mins).
  - `owner_load (Total Row)`: (runs).
  - busiest_owner (owner, total_mins, runs).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - staffed's `[owner] <> null` is `IS NOT NULL`, so job 4, with no owner, drops out.
  - The LeftOuter join is a LEFT JOIN, and Table.RowCount is COUNT(*), as M counts a row with no match as one.
  - busiest_owner is ORDER BY with LIMIT 1, so the ORDER BY stays.
  - The Total Row is a query of its own: one row, a column per total, no label. The "Total" label is left out.
- Fill in: `<database>`.

owner_load:

```sql
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

owner_load (Total Row):

```sql
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

busiest_owner:

```sql
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

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X73

**Map**
- Sources: region_budgets, jobs. Parameters and Keys are none.
- Steps: the eu_budgets query, which eu_count reads, so it is a CTE in eu_count's query.
- Finals:
  - eu_budgets, the Table plus its formula column dollars, which nothing reads: (job_id, budget_cents, region, job_name, dollars).
  - eu_count (region, jobs, total_cents).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - The Inner join on job_id is a plain JOIN.
  - The filter `[region] = "eu"` keeps its case, as M does.
  - Table.RowCount is COUNT(*) and List.Sum is SUM.
- Fill in: `<database>`.

eu_budgets:

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

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.

## X74

**Map**
- Sources: job_runs, and run_alerts' typed columns (alert_id, run_id, severity, dt). Parameters and Keys are none.
- Steps: run_alerts with its formula columns (status, job_id, alerts_so_far). by_status and late_alerts read it, so it is a CTE, `alerts`, in each of their queries. It is not a final.
- Finals:
  - by_status (status, alerts), a summary: its only typed column, status, is what its COUNTIFS matches on, so it is a GROUP BY of alerts.
  - late_alerts (alert_id, run_id, alerts_so_far).
- Typed over a formula: none. Refusals: none. Left alone: nothing.
- Marks:
  - The XLOOKUPs are LEFT JOINs on run_id.
  - alerts_so_far is a running count, ties included.
  - COUNTIFS is COALESCE(COUNT(*), 0).
  - by_status groups on whatever statuses the alerts have. In the sample these are exactly FAILED and SUCCESS.
- Fill in: `<database>`.

by_status:

```sql
WITH alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    r.status, r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT status, COALESCE(COUNT(*), 0) AS alerts
FROM alerts
GROUP BY status
```

late_alerts:

```sql
WITH alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    r.status, r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM alerts
WHERE alerts_so_far > 5
```

Next: take out of the workbook what you don't want converted, fill in `<database>`, and run `project.convert` on the Hive. Its checked code wins where the two differ.
