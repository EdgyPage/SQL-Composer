date: 2026-10-29
arm: C
model: sonnet
files: 44f6c5d

## X21

**Map**

- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin).
- Typed over: none. Marks: none, and there are no blanks. Refused: none.
- Left alone: the Steps sheet. Parameters and Keys hold no rows, so they are neither source nor final.
- Fill in: `<database>`.

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
    FROM(region_budgets, reads_all_partitions=True),  # the workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X22

**Map**

- Sources: jobs (job_id, job_name, team).
- Steps: none.
- Finals: jobs (job_id, job_name, team, is_finance, ratio).
- Typed over: none. Marks: none, and there are no blanks.
- Converted: `IFERROR(a / b, 0)` is `COALESCE(a / b, 0)`, because Hive gives NULL for a divide by 0. The only zero divisor is job 2.
- Refused: none. Fill in: `<database>`.

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
    FROM(jobs, reads_all_partitions=True),  # the workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X23

**Map**

- Sources: job_runs (run_id, status, avg_retry_secs).
- Steps: none.
- Finals: job_runs (run_id, status, avg_retry_secs, label, risky).
- Typed over: none, so no Keys row is needed.
- Blank: run 98 has a blank status and a blank avg_retry_secs, and both columns are read by formulas. I wrapped them as `COALESCE(status, '')` and `COALESCE(avg_retry_secs, 0)`, so Hive reads them as Excel does.
- SWITCH becomes `CASE x WHEN ... ELSE ... END`. OR is kept as it is.
- Refused: none. Fill in: `<database>`.

```sql
SELECT run_id, status, avg_retry_secs,
       CASE COALESCE(status, '')
            WHEN 'SUCCESS' THEN 'ok'
            WHEN 'FAILED' THEN 'bad'
            ELSE 'other' END AS label,
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
    FROM(job_runs, reads_all_partitions=True),  # the workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ (this matters most for the `risky` column).

## X24

**Map**

- Sources: team_notes (team, note, written_on).
- Steps: none.
- Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars).
- Typed over: none. Marks: none, and there are no blanks. `written_on` already holds ISO dates (2026-09-11), not text like 20260911, so MONTH reads it as it is.
- Refused: none. Fill in: `<database>`.

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

# files 03, 04 and 05 hold no names for SUBSTR, INSTR, UPPER, MONTH, ROUND or LENGTH.
# Those four columns are in file 10 (Hive functions), so load it in a new chat for them.
s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on),
    FROM(team_notes, reads_all_partitions=True),  # the workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ. For the four calculated columns, the Hive is the answer.

## X25

**Map**

- Sources: Costs (Job, `<cost_cents>`, Region, `<day_key>`) and Budgets (Job, Budget, Region).
- Steps: none. Neither Table reads the other.
- Finals, one query each:
  - Costs (Job, `<cost_cents>`, Region, `<day_key>`, Day)
  - Budgets (Job, Budget, Region, Dollars)
- Typed over: none.
- Marks:
  - Date held as text. `Day Key` holds 20260911 and `Day` rebuilds the date from it, so I used the text form `CONCAT(SUBSTR(<day_key>, 1, 4), '-', SUBSTR(<day_key>, 5, 2), '-', SUBSTR(<day_key>, 7, 2))`.
  - Blank: Costs row 29 has a blank `Cost (cents)`. No formula reads that column, so I left it as it is.
- Names: the headers `Cost (cents)` and `Day Key` are not plain names, so they become `<cost_cents>` and `<day_key>`.
- Refused: none. Fill in: `<database>`, `<cost_cents>`, `<day_key>`.

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
from references.<database>__Budgets import Budgets  # name as your Table reference gives it

budgets = statement(
    SELECT(Budgets.Job, Budgets.Budget, Budgets.Region,
           AS(Budgets.Budget / 100, "Dollars")),
    FROM(Budgets, reads_all_partitions=True),  # the workbook's formulas read every row
)
# Costs: the Day column needs SUBSTR and CONCAT, which are in file 10 (Hive functions),
# not in files 03, 04 and 05. Convert the Costs Hive above with project.convert.
```

Take out of the workbook what you don't want converted. Fill in `<database>`, `<cost_cents>` and `<day_key>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X26

**Map**

- Sources: run_alerts (alert_id, run_id, severity) and job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins).
- Typed over: none. Marks:
  - Blank: job_runs has a blank status (run 98), and the VLOOKUP reads that column, so I wrapped it as `COALESCE(status, '')`.
  - The blank avg_retry_secs is not read by a formula. The AVERAGEIFS reads duration_mins and job_id, so nothing inside it is wrapped.
- Converted:
  - XLOOKUP and `VLOOKUP(..., 3, FALSE)` (exact, column 3 is status) are one LEFT JOIN of job_runs on run_id.
  - AVERAGEIFS reads another Table, so it is a LEFT JOIN of a grouped `AVG`, matched on the looked-up job_id.
- Refused: none. Fill in: `<database>`.

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

a, r = AS(run_alerts, "a"), AS(job_runs, "r")
m = derived("m", statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's formulas read every row
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(a.alert_id, a.run_id, a.severity, r.job_id,
           AS(fill_null(r.status, ""), "status"),  # blank
           m.avg_mins),
    FROM(a, reads_all_partitions=True),
    LEFT_JOIN(r, ON=equals(r.run_id, a.run_id), reads_all_partitions=True),
    LEFT_JOIN(m, ON=equals(m.job_id, r.job_id)),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X27

**Map**

- Sources: jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: by_team (team, jobs_in_team, last_job_id, last_job_name). It is a summary: its only typed column, team, is what its COUNTIFS and MAXIFS match on, so it is a GROUP BY of jobs. jobs is read by by_team, so it is not a final.
- Typed over: none. Blanks: none.
- Converted:
  - COUNTIFS is `COUNT(*)` and MAXIFS is `MAX`.
  - `INDEX(jobs[job_name], MATCH(last_job_id, jobs[job_id], 0))` is an exact LEFT JOIN of jobs on last_job_id.
- Refused: none. Fill in: `<database>`.

```sql
WITH grouped AS (
  SELECT team, COUNT(*) AS jobs_in_team, MAX(job_id) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
)
SELECT g.team, g.jobs_in_team, g.last_job_id, j.job_name AS last_job_name
FROM grouped g
LEFT JOIN <database>.jobs j ON g.last_job_id = j.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, max_of, statement)
from references.<database>__jobs import jobs

grouped = derived("grouped", statement(
    SELECT(jobs.team, AS(count_rows(), "jobs_in_team"), AS(max_of(jobs.job_id), "last_job_id")),
    FROM(jobs, reads_all_partitions=True),  # the workbook's formulas read every row
    GROUP_BY(jobs.team),
))
j = AS(jobs, "j")
s = statement(
    SELECT(grouped.team, grouped.jobs_in_team, grouped.last_job_id,
           AS(j.job_name, "last_job_name")),
    FROM(grouped),
    LEFT_JOIN(j, ON=equals(j.job_id, grouped.last_job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X28

**Map**

- Sources: jobs (job_id, job_name) and job_runs (job_id, status, duration_mins, and the other typed columns).
- Steps: none.
- Finals: jobs (job_id, job_name, ok_mins).
- Typed over: ok_mins where job_id is 3 (value 99). The Keys row for jobs is job_id, so I matched on that.
- Converted: SUMIFS reads another Table, so it is a LEFT JOIN of a grouped sum of the SUCCESS runs, with `COALESCE(total, 0)` because Excel gives 0 where nothing matches.
- Blank: job_runs has a blank status (run 98). It sits inside SUMIFS, which skips it, so it is not wrapped. A blank never equals 'SUCCESS' in either tool.
- Refused: none. Fill in: `<database>`.

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
    FROM(job_runs, reads_all_partitions=True),  # the workbook's formulas read every row
    WHERE(equals(job_runs.status, "SUCCESS")),
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(first_match([(equals(jobs.job_id, 3), 99)], otherwise=fill_null(s_ok.total, 0)),
              "ok_mins")),
    FROM(jobs, reads_all_partitions=True),
    LEFT_JOIN(s_ok, ON=equals(s_ok.job_id, jobs.job_id)),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X29

**Map**

- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none. Parameters (cents_per_dollar = 100) is neither source nor final, so I used its value.
- Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer).
- Typed over: in_dollars is typed 5 in the row where job_id is 3. There is no Keys row for region_budgets, so I matched every typed column of the row (job_id = 3, budget_cents = 350, region = 'us').
- Converted: `XLOOKUP("cents_per_dollar", Parameters[name], Parameters[value])` is the value, 100.
- Refused: `pointer` is `INDIRECT("A"&ROW())`, and INDIRECT is not converted, so it is `NULL AS pointer`.
- Fill in: `<database>`.

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

b = region_budgets
s = statement(
    SELECT(b.job_id, b.budget_cents, b.region,
           AS(first_match([(all_of(equals(b.job_id, 3), equals(b.budget_cents, 350),
                                   equals(b.region, "us")), 5)],
                          otherwise=b.budget_cents / 100), "in_dollars")),
    # pointer (INDIRECT) is refused: files 03, 04 and 05 hold no name for a NULL column,
    # so project.convert on the Hive above gives the `NULL AS pointer` column.
    FROM(b, reads_all_partitions=True),  # the workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X30

**Map**

- Sources: scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter).
- Typed over: none. Blanks: none. I read dt as text, as the sample shows it.
- Refused:
  - `prev_run` is OFFSET, so it is `NULL AS prev_run`.
  - `jitter` is RANDBETWEEN, so it is `NULL AS jitter`.
- Left alone: the bar chart on the Summary sheet and the PivotTable on the Pivot sheet (job_id with the count of run_id).
- Fill in: `<database>`.

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

# day is SUBSTR (file 10); prev_run and jitter are refused (NULL). None of these three has a
# name in files 03, 04 and 05, so project.convert on the Hive above builds them.
s = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    FROM(scheduler_runs, reads_all_partitions=True),  # the workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X31

**Map**

- Sources: jobs (job_id, team).
- Steps: none.
- Finals: jobs (job_id, team, bump, tag, scaled, boosted).
- Typed over: none. Blanks: none.
- Refused, each as NULL:
  - `bump` is `jobs[@bump]*2`, a formula reading its own column (circular), so `NULL AS bump`.
  - `tag` is `TAG(...)`, a defined name holding a LAMBDA, so `NULL AS tag`.
  - `scaled` reads `Summary!$D$4`, a cell outside a Table that is not a defined name, so `NULL AS scaled`.
- Marks: `boosted` uses the defined name `boost`, which is the cell Summary!$B$2 outside a Table. I used its value, 10. Move that value into the Parameters Table.
- Left alone: the cells on the Summary sheet outside a Table (B2 and D4).
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

# bump, tag and scaled are refused (NULL columns): files 03, 04 and 05 hold no name for them,
# so project.convert on the Hive above builds them.
s = statement(
    SELECT(jobs.job_id, jobs.team,
           AS(jobs.job_id * 10, "boosted")),  # boost = Summary!B2 = 10, to move into Parameters
    FROM(jobs, reads_all_partitions=True),  # the workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`, and move boost into Parameters. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X32

**Map**

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (job_id, job_name, team, region).
- Steps: job_runs, because by_name reads it. It adds job_name, and the CTE is `runs_named`.
- Finals: by_name (job_name, runs). It is a summary: its only typed column, job_name, is what its COUNTIFS matches on, so it is a GROUP BY of job_runs.
- Typed over: none. Blanks: job_runs has blanks in status and avg_retry_secs, but no formula reads them.
- Marks: `VLOOKUP(job_id, jobs, 2, TRUE)` is approximate. I converted it exactly, as a LEFT JOIN of jobs on job_id. The sample's job_ids are all in jobs, so the answers match.
- Refused: none. Fill in: `<database>`.

```sql
WITH runs_named AS (
  SELECT r.job_id, j.job_name AS job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT job_name, COUNT(*) AS runs
FROM runs_named
GROUP BY job_name
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              equals, statement)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

r, j = AS(job_runs, "r"), AS(jobs, "j")
runs_named = derived("runs_named", statement(
    SELECT(r.job_id, AS(j.job_name, "job_name")),
    FROM(r, reads_all_partitions=True),  # the workbook's formulas read every row
    LEFT_JOIN(j, ON=equals(j.job_id, r.job_id), reads_all_partitions=True),
))
s = statement(
    SELECT(runs_named.job_name, AS(count_rows(), "runs")),
    FROM(runs_named),
    GROUP_BY(runs_named.job_name),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X33

**Map**

- Sources: job_runs, which the query reads through `Sql.Database("dwh01", "ops")`, schema ops, item job_runs. I used the table it names, `ops.job_runs`. **Check** that this is the Hive table you mean.
- Steps: none (the M is one query).
- Finals: slow_runs (run_id, duration_mins, over_by), the Table that the Power Query loads.
- Typed over: none. Formulas: none.
- Converted:
  - `[status] <> "TEST"` in M keeps a null status, as Hive's `<>` doesn't, so I wrote `(status <> 'TEST' OR status IS NULL)`.
  - `over_by` is the AddColumn `duration_mins - 20`. SelectColumns sets the SELECT list.
- Refused: none. Fill in: nothing, but check `ops.job_runs`.

```sql
SELECT run_id, duration_mins,
       duration_mins - 20 AS over_by
FROM ops.job_runs
WHERE duration_mins >= 20
  AND (status <> 'TEST' OR status IS NULL)
```

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, any_of, at_least, is_null, not_equals,
                              statement)
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins - 20, "over_by")),
    FROM(job_runs, reads_all_partitions=True),  # the query reads every row; its WHERE is below
    WHERE(at_least(job_runs.duration_mins, 20),
          any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
)
```

Take out of the workbook what you don't want converted. Check which table the Sql.Database source names. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X34

**Map**

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (job_id, job_name, team, region).
- Steps: the query runs_with_team (connection only), which team_totals reads. It is a CTE.
- Finals: team_totals (team, total_mins, longest), the Table that the query team_totals loads.
- Typed over: none. Formulas: none. Blanks: none in the columns the query uses.
- Converted:
  - NestedJoin with ExpandTableColumn (JoinKind.LeftOuter) is a LEFT JOIN.
  - Table.Group with `List.Sum` and `List.Max` is GROUP BY with SUM and MAX.
- Refused: none. Fill in: `<database>`.

```sql
WITH runs_with_team AS (
  SELECT r.run_id, r.job_id, r.duration_mins, j.team AS team
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

r, j = AS(job_runs, "r"), AS(jobs, "j")
runs_with_team = derived("runs_with_team", statement(
    SELECT(r.run_id, r.job_id, r.duration_mins, AS(j.team, "team")),
    FROM(r, reads_all_partitions=True),  # the query reads every row
    LEFT_JOIN(j, ON=equals(j.job_id, r.job_id), reads_all_partitions=True),
))
s = statement(
    SELECT(runs_with_team.team,
           AS(sum_of(runs_with_team.duration_mins), "total_mins"),
           AS(max_of(runs_with_team.duration_mins), "longest")),
    FROM(runs_with_team),
    GROUP_BY(runs_with_team.team),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X35

**Map**

- Sources: job_runs (run_id, dt) and scheduler_runs (run_id, dt).
- Steps: none (the M steps are one query).
- Finals: recent (run_id, dt), the Table that the query recent loads. Table.Combine is UNION ALL, and Sort then FirstN is `ORDER BY run_id DESC LIMIT 4`.
- Typed over: none. Formulas: none.
- Refused: the query `rates` reads `Web.Contents` (an online source). I left that query out. It loads no Table.
- Fill in: `<database>`.

```sql
WITH both_runs AS (
  SELECT run_id, dt FROM <database>.job_runs
  UNION ALL
  SELECT run_id, dt FROM <database>.scheduler_runs
)
SELECT run_id, dt
FROM both_runs
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
              FROM(job_runs, reads_all_partitions=True)),  # the query reads every row
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

Take out of the workbook what you don't want converted (the `rates` query). Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ. If `derived` won't take a stacked Statement, the Hive is the answer for this one.

## X36

**Map**

- Sources: run_alerts (alert_id, run_id, severity, dt) and job_runs (run_id, status).
- Steps: none.
- Finals, one query each:
  - job_runs (run_id, status, alerts)
  - severity_by_day (dt, high, low), the Table that the Power Query loads
- Typed over: none. Formulas: only `alerts`.
- Blank: job_runs row 98 has a blank status, but no formula reads status, so I left it as it is.
- Converted:
  - COUNTIFS reads another Table, so it is a LEFT JOIN of a grouped `COUNT(*)`, with `COALESCE(n, 0)` because Excel gives 0 for no match.
  - Table.Pivot is one `SUM(CASE WHEN severity = '...' THEN 1 END)` column per value in the sample (high, low), NULL where none, as M leaves it. **The pivot's columns are now fixed.** A new severity value in the data adds no column.
- Refused: none. Fill in: `<database>`.

```sql
SELECT r.run_id, r.status,
       COALESCE(a.n, 0) AS alerts
FROM <database>.job_runs r
LEFT JOIN (SELECT run_id, COUNT(*) AS n
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
                              equals, fill_null, first_match, statement, sum_of)
from references.<database>__job_runs import job_runs
from references.<database>__run_alerts import run_alerts

a = derived("a", statement(
    SELECT(run_alerts.run_id, AS(count_rows(), "n")),
    FROM(run_alerts, reads_all_partitions=True),  # the workbook's formulas read every row
    GROUP_BY(run_alerts.run_id),
))
job_runs_final = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(fill_null(a.n, 0), "alerts")),
    FROM(job_runs, reads_all_partitions=True),
    LEFT_JOIN(a, ON=equals(a.run_id, job_runs.run_id)),
)

severity_by_day = statement(
    SELECT(run_alerts.dt,
           AS(sum_of(first_match([(equals(run_alerts.severity, "high"), 1)])), "high"),
           AS(sum_of(first_match([(equals(run_alerts.severity, "low"), 1)])), "low")),
    FROM(run_alerts, reads_all_partitions=True),  # the query reads every row
    GROUP_BY(run_alerts.dt),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X37

**Map**

- Sources: Owners (`<job_no>`, `<team_name>`, Owner, Day).
- Steps: none.
- Finals: Owners (`<job_no>`, `<team_name>`, Owner, Day, `<is_ana>`).
- Typed over: none. Refused: none.
- Names: `Job No`, `Team Name` and `Is Ana` are not plain names, so they become `<job_no>`, `<team_name>` and `<is_ana>`. `Owner` and `Day` are kept.
- Blank: Owner is blank for job 4 (web) on every day, and the formula reads it, so I wrapped it as `COALESCE(Owner, '')`.
- All 56 rows are kept, with no filter.
- Fill in: `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

```sql
SELECT <job_no>, <team_name>, Owner, Day,
       IF(COALESCE(Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners
```

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.<database>__Owners import Owners  # name as your Table reference gives it

s = statement(
    SELECT(Owners.<job_no>, Owners.<team_name>, Owners.Owner, Owners.Day,  # fill in the <...> names
           AS(if_else(equals(fill_null(Owners.Owner, ""), "ana"), 1, 0), "<is_ana>")),  # blank
    FROM(Owners, reads_all_partitions=True),  # the workbook's formulas read every row
)
```

Take out of the workbook what you don't want converted. Fill in `<database>` and each `<...>` name. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X38

**Map**

- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs) and jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost). jobs is read by job_runs, so it is not a final.
- Typed over: retry_cost is typed 1 where run_id is 102. The Keys row (job_runs, run_id) gives the match.
- Blank: run 98 has a blank avg_retry_secs, and retry_cost reads it, so I wrapped it as `COALESCE(avg_retry_secs, 0)`.
- Converted:
  - `XLOOKUP(job_id, jobs[job_id], jobs[region])` is a LEFT JOIN of jobs.
  - SUMIFS over its own Table with one criterion is `SUM(duration_mins) OVER (PARTITION BY region)`. The inside of SUMIFS is not wrapped for blanks.
- Refused: none. Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
       j.region AS region,
       SUM(r.duration_mins) OVER (PARTITION BY j.region) AS region_mins,
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

r, j = AS(job_runs, "r"), AS(jobs, "j")
by_region = window(PARTITION_BY=j.region)
s = statement(
    SELECT(r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
           AS(j.region, "region"),
           AS(sum_of(r.duration_mins, over=by_region), "region_mins"),
           AS(first_match([(equals(r.run_id, 102), 1)],
                          otherwise=(fill_null(r.avg_retry_secs, 0) + r.duration_mins) * 2),
              "retry_cost")),  # blank in avg_retry_secs
    FROM(r, reads_all_partitions=True),  # the workbook's formulas read every row
    LEFT_JOIN(j, ON=equals(j.job_id, r.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X39

**Map**

- Sources: job_runs (run_id, job_id, status, duration_mins, ...) and jobs (job_id, job_name, team, region).
- Steps: the query ok_runs, as a CTE (`ok_runs_query`). Its M is SelectRows with `status = "SUCCESS"`, then SelectColumns. `=` keeps no null, so there is no IS NULL clause.
- Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise), the Table that the query loads plus its formula columns.
- Typed over: none. Blanks: none in the columns the query keeps.
- Converted:
  - `job_name` is a LEFT JOIN of jobs.
  - `share` is `duration_mins / SUMIFS(...)` over its own Table, so `duration_mins / SUM(duration_mins) OVER (PARTITION BY job_id)`.
- Refused: `noise` is RAND, so `NULL AS noise`.
- Fill in: `<database>`.

```sql
WITH ok_runs_query AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT q.run_id, q.job_id, q.duration_mins,
       j.job_name AS job_name,
       q.duration_mins / SUM(q.duration_mins) OVER (PARTITION BY q.job_id) AS share,
       NULL AS noise
FROM ok_runs_query q
LEFT JOIN <database>.jobs j ON q.job_id = j.job_id
```

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, WHERE, derived, equals, statement,
                              sum_of, window)
from references.<database>__job_runs import job_runs
from references.<database>__jobs import jobs

q = derived("q", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # the query reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
))
j = AS(jobs, "j")
s = statement(
    SELECT(q.run_id, q.job_id, q.duration_mins,
           AS(j.job_name, "job_name"),
           AS(q.duration_mins / sum_of(q.duration_mins, over=window(PARTITION_BY=q.job_id)),
              "share")),
    # noise (RAND) is refused: no name for a NULL column in files 03, 04 and 05,
    # so project.convert on the Hive above builds `NULL AS noise`.
    FROM(q),
    LEFT_JOIN(j, ON=equals(j.job_id, q.job_id), reads_all_partitions=True),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.

## X40

**Map**

- Sources: Runs (Run, Job, Mins), jobs (job_id, job_name, team, region) and run_alerts (alert_id, run_id, severity, dt).
- Steps: Runs, because Teams and run_alerts read it. It adds Team (a LEFT JOIN of jobs) and Cost (Mins times the rate). The CTE is `runs_calc`.
- Finals, one query each:
  - Teams (Team, `<total_cost>`), a summary: its only typed column, Team, is what its SUMIFS matches on, so it is a GROUP BY of Runs.
  - run_alerts (alert_id, run_id, severity, dt, `<run_mins>`).
- Typed over: none. Blanks: none. Refused: none.
- Converted: `XLOOKUP("rate", Parameters[name], Parameters[value])` is the value, 2.
- Names: `Total Cost` and `Run Mins` are not plain names, so they become `<total_cost>` and `<run_mins>`.
- Left alone: the PivotTable on the Pivot sheet (Team with Sum of Cost).
- The run_alerts query needs only Run and Mins from Runs, so its CTE keeps only those.
- Fill in: `<database>`, `<total_cost>`, `<run_mins>`.

```sql
WITH runs_calc AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT Team, SUM(Cost) AS <total_cost>
FROM runs_calc
GROUP BY Team
```

```sql
WITH runs_calc AS (
  SELECT Run, Mins
  FROM <database>.Runs
)
SELECT a.alert_id, a.run_id, a.severity, a.dt,
       r.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN runs_calc r ON a.run_id = r.Run
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals, statement,
                              sum_of)
from references.<database>__Runs import Runs  # name as your Table reference gives it
from references.<database>__jobs import jobs
from references.<database>__run_alerts import run_alerts

j = AS(jobs, "j")
runs_calc = derived("runs_calc", statement(
    SELECT(Runs.Run, Runs.Job, Runs.Mins, AS(j.team, "Team"), AS(Runs.Mins * 2, "Cost")),
    FROM(Runs, reads_all_partitions=True),  # the workbook's formulas read every row
    LEFT_JOIN(j, ON=equals(j.job_id, Runs.Job), reads_all_partitions=True),
))
teams = statement(
    SELECT(runs_calc.Team, AS(sum_of(runs_calc.Cost), "<total_cost>")),  # fill in <total_cost>
    FROM(runs_calc),
    GROUP_BY(runs_calc.Team),
)

run_mins = derived("run_mins", statement(
    SELECT(Runs.Run, Runs.Mins),
    FROM(Runs, reads_all_partitions=True),
))
a = AS(run_alerts, "a")
alerts = statement(
    SELECT(a.alert_id, a.run_id, a.severity, a.dt, AS(run_mins.Mins, "<run_mins>")),  # fill in
    FROM(a, reads_all_partitions=True),
    LEFT_JOIN(run_mins, ON=equals(run_mins.Run, a.run_id)),
)
```

Take out of the workbook what you don't want converted. Fill in `<database>`, `<total_cost>` and `<run_mins>`. Run `project.convert` on the Hive, whose code is checked and wins where the two differ.
