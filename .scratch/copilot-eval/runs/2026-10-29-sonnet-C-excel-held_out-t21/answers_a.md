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
