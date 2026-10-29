date: 2026-10-29
arm: C
model: sonnet
files: 61c9ca2

## X21

**Map.** Sources: region_budgets. Steps: none. Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin). Parameters and Keys are neither (both empty).

- Typed over: none. Marks: no blanks in the columns the formulas read. Refusals: none. Left alone: the Steps sheet (outside a Table).
- Fill in: `<database>`.

```sql
SELECT r.job_id, r.budget_cents, r.region,
  r.budget_cents / 100 AS budget_dollars,
  r.budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets r
```

Toolbox code, with `<database>` as in your Table references' module names:

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__region_budgets import region_budgets  # fill in <database>, such as ops

s = statement(
    SELECT(region_budgets.job_id, region_budgets.budget_cents, region_budgets.region,
           AS(region_budgets.budget_cents / 100, "budget_dollars"),
           AS(region_budgets.budget_cents * 1.1, "with_margin")),
    FROM(region_budgets, reads_all_partitions=True),  # every row, as the workbook holds them
)
```

Take out of the workbook what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X22

**Map.** Sources: jobs. Steps: none. Finals: jobs (job_id, job_name, team, is_finance, ratio).

- Typed over: none. Refusals: none. Left alone: the Steps sheet.
- Marks: `IFERROR(.. / ..., 0)` becomes `COALESCE(.., 0)`, because Hive gives NULL for a divide by 0 (job 2 divides by 0 and gives 0, as Excel's IFERROR does).
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team,
  IF(j.team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(j.job_id / (j.job_id - 2), 0) AS ratio
FROM <database>.jobs j
```

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.<database>__jobs import jobs  # fill in <database>

s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(if_else(equals(jobs.team, "finance"), "yes", "no"), "is_finance"),
           AS(fill_null(jobs.job_id / (jobs.job_id - 2), 0), "ratio")),
    FROM(jobs, reads_all_partitions=True),  # every row
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X23

**Map.** Sources: job_runs. Steps: none. Finals: job_runs (run_id, status, avg_retry_secs, label, risky).

- Typed over: none. Refusals: none. Left alone: the Steps sheet.
- Marks: blank. Run 98 has a blank status and a blank avg_retry_secs, and both formulas read them, so I wrapped `COALESCE(status, '')` and `COALESCE(avg_retry_secs, 0)`. Without that, risky would be NULL for run 98 in Hive where Excel gives FALSE.
- SWITCH becomes `CASE status WHEN ... ELSE 'other' END`; `_xlfn.` is only Excel's prefix.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.status, r.avg_retry_secs,
  CASE COALESCE(r.status, '') WHEN 'SUCCESS' THEN 'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label,
  (COALESCE(r.status, '') = 'FAILED' OR COALESCE(r.avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs r
```

```python
from sqlglot_composer import (AS, FROM, SELECT, any_of, at_least, equals, fill_null,
                              first_match, if_else, more_than, statement)
from references.<database>__job_runs import job_runs  # fill in <database>

s = statement(
    SELECT(job_runs.run_id, job_runs.status, job_runs.avg_retry_secs,
           AS(first_match([(equals(fill_null(job_runs.status, ""), "SUCCESS"), "ok"),
                           (equals(fill_null(job_runs.status, ""), "FAILED"), "bad")],
                          otherwise="other"), "label"),
           AS(if_else(any_of(equals(fill_null(job_runs.status, ""), "FAILED"),
                             more_than(fill_null(job_runs.avg_retry_secs, 0), 5)), True, False),
              "risky")),
    FROM(job_runs, reads_all_partitions=True),  # every row
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ (the TRUE/FALSE in `risky` is the place to look).

## X24

**Map.** Sources: team_notes. Steps: none. Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars).

- Typed over: none. Refusals: none. Left alone: the Steps sheet.
- Marks: no blanks. written_on is a real date (2026-09-11), not text, so MONTH is used as it is.
- Fill in: `<database>`.

```sql
SELECT t.team, t.note, t.written_on,
  SUBSTR(t.note, 1, INSTR(t.note, ' ') - 1) AS first_word,
  UPPER(t.team) AS shout,
  MONTH(t.written_on) AS month,
  ROUND(LENGTH(t.note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes t
```

Toolbox code: files 03, 04 and 05 have no name for SUBSTR, INSTR, UPPER, MONTH, ROUND or LENGTH. Hive functions and Hive written by hand are file 10, to load in a new chat. Here is the part they cover; the four calculated columns come in when you run `project.convert` on the Hive above.

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__team_notes import team_notes  # fill in <database>

s = statement(
    SELECT(team_notes.team, team_notes.note, team_notes.written_on),
    # first_word, shout, month and tens_of_chars: use project.convert on the Hive above
    FROM(team_notes, reads_all_partitions=True),  # every row
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X25

**Map.** Sources: Costs, Budgets. Steps: none. Finals: Costs (Job, `<cost_cents>`, Region, `<day_key>`, Day) and Budgets (Job, Budget, Region, Dollars). Two finals, one query each.

- Typed over: none. Keys is empty. Refusals: none. Left alone: the Steps sheet.
- Marks: the date is held as text. Day Key is 20260911 (year, month, day run together), so Day is built with CONCAT and SUBSTR into `2026-09-11`. If Day Key is a number in your table, Hive will cast it for SUBSTR; check this.
- Blank: Costs row 29 has a blank in Cost (cents), but no formula reads that column, so nothing is wrapped.
- Names: header `Cost (cents)` is `<cost_cents>` and `Day Key` is `<day_key>`; `Job`, `Region`, `Day`, `Budget` and `Dollars` are plain names, kept.
- Fill in: `<database>`, `<cost_cents>`, `<day_key>`.

```sql
SELECT c.Job, c.<cost_cents>, c.Region, c.<day_key>,
  CONCAT(SUBSTR(c.<day_key>, 1, 4), '-', SUBSTR(c.<day_key>, 5, 2), '-', SUBSTR(c.<day_key>, 7, 2)) AS Day
FROM <database>.Costs c
```

```sql
SELECT b.Job, b.Budget, b.Region,
  b.Budget / 100 AS Dollars
FROM <database>.Budgets b
```

Toolbox code. Costs.Day needs CONCAT and SUBSTR, which are file 10 (Hive functions); `project.convert` on the Hive brings it in.

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__Costs import Costs      # fill in <database>
from references.<database>__Budgets import Budgets

costs = statement(
    SELECT(Costs.Job, Costs.<cost_cents>, Costs.Region, Costs.<day_key>),  # fill in the two names
    # Day: project.convert on the Hive above
    FROM(Costs, reads_all_partitions=True),  # every row
)
budgets = statement(
    SELECT(Budgets.Job, Budgets.Budget, Budgets.Region,
           AS(Budgets.Budget / 100, "Dollars")),
    FROM(Budgets, reads_all_partitions=True),  # every row
)
```

Take out what you don't want converted, fill in each `<...>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X26

**Map.** Sources: run_alerts (its typed columns alert_id, run_id, severity), job_runs. Steps: job_runs, read by run_alerts; it has no formula, so it is used as the table itself. Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins).

- Typed over: none. Keys is empty. Refusals: none. Left alone: the Steps sheet.
- Marks: job_id is an XLOOKUP and status a VLOOKUP with FALSE (exact, column 3 of job_runs is status), both a LEFT JOIN on run_id. avg_mins is an AVERAGEIFS over another Table: a LEFT JOIN of a grouped subquery, left NULL where no run matches.
- Blank: job_runs run 98 has a blank status, and status is read by the VLOOKUP, so I wrapped `COALESCE(status, '')`. No alert points at run 98 today, so nothing changes in this sample.
- Fill in: `<database>`.

```sql
SELECT a.alert_id, a.run_id, a.severity,
  jr.job_id AS job_id,
  COALESCE(jr.status, '') AS status,
  m.avg_mins AS avg_mins
FROM <database>.run_alerts a
LEFT JOIN <database>.job_runs jr ON a.run_id = jr.run_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins
           FROM <database>.job_runs GROUP BY job_id) m ON jr.job_id = m.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, average_of, derived,
                              equals, fill_null, statement)
from references.<database>__run_alerts import run_alerts   # fill in <database>
from references.<database>__job_runs import job_runs

a, jr = AS(run_alerts, "a"), AS(job_runs, "jr")
m = derived("m", statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_mins")),
    FROM(job_runs, reads_all_partitions=True),  # every row, as AVERAGEIFS reads the whole Table
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(a.alert_id, a.run_id, a.severity, jr.job_id,
           AS(fill_null(jr.status, ""), "status"), m.avg_mins),
    FROM(a, reads_all_partitions=True),  # every row
    LEFT_JOIN(jr, ON=equals(jr.run_id, a.run_id), reads_all_partitions=True),
    LEFT_JOIN(m, ON=equals(m.job_id, jr.job_id)),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X27

**Map.** Sources: jobs. Steps: none apart from the summary's own grouping. Finals: by_team (team, jobs_in_team, last_job_id, last_job_name).

- by_team is a summary: its only typed column, team, is what its COUNTIFS and MAXIFS match on, so it is a GROUP BY of jobs. Typed over: none. Refusals: none. Left alone: the Steps sheet.
- Marks: COUNTIFS is COUNT(*) and MAXIFS is MAX; last_job_name is INDEX/MATCH with 0 (exact), a LEFT JOIN back to jobs on last_job_id.
- Fill in: `<database>`.

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
from references.<database>__jobs import jobs  # fill in <database>

g = derived("g", statement(
    SELECT(jobs.team, AS(count_rows(), "jobs_in_team"), AS(max_of(jobs.job_id), "last_job_id")),
    FROM(jobs, reads_all_partitions=True),  # every row
    GROUP_BY(jobs.team),
))
j = AS(jobs, "j")
s = statement(
    SELECT(g.team, g.jobs_in_team, g.last_job_id, AS(j.job_name, "last_job_name")),
    FROM(g),
    LEFT_JOIN(j, ON=equals(g.last_job_id, j.job_id), reads_all_partitions=True),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X28

**Map.** Sources: jobs, job_runs. Steps: none. Finals: jobs (job_id, job_name, ok_mins). job_runs is read by jobs, so it is not a final.

- Typed over: ok_mins where job_id is 3 (value 99), matched on the Keys row for jobs, job_id.
- ok_mins is a SUMIFS over another Table: a LEFT JOIN of a grouped subquery with `status = 'SUCCESS'`, wrapped in COALESCE(.., 0), as Excel gives 0 where nothing matches (job 4).
- Blank: job_runs has a blank status in run 98, but it is read inside a SUMIFS, which skips it, so nothing is wrapped. Refusals: none. Left alone: the Steps sheet.
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

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, WHERE, derived, equals,
                              fill_null, first_match, statement, sum_of)
from references.<database>__jobs import jobs          # fill in <database>
from references.<database>__job_runs import job_runs

s_ok = derived("s", statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "total")),
    FROM(job_runs, reads_all_partitions=True),  # every day, as the SUMIFS reads every row
    WHERE(equals(job_runs.status, "SUCCESS")),
    GROUP_BY(job_runs.job_id),
))
s = statement(
    SELECT(jobs.job_id, jobs.job_name,
           AS(first_match([(equals(jobs.job_id, 3), 99)], otherwise=fill_null(s_ok.total, 0)),
              "ok_mins")),
    FROM(jobs, reads_all_partitions=True),  # every row
    LEFT_JOIN(s_ok, ON=equals(s_ok.job_id, jobs.job_id)),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X29

**Map.** Sources: region_budgets. Steps: none. Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer). Parameters is neither a source nor a final.

- Typed over: in_dollars in row 4 (job 3), value 5. Keys has no row for region_budgets, so I matched every typed column of that row (job_id 3, budget_cents 350, region 'us'). There is no Keys row for this Table; add one if you want a shorter match.
- Marks: `XLOOKUP("cents_per_dollar", Parameters[name], Parameters[value])` is the value, 100.
- Refused: pointer, `=INDIRECT("A"&ROW())`, is INDIRECT, so `NULL AS pointer`.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT r.job_id, r.budget_cents, r.region,
  CASE WHEN r.job_id = 3 AND r.budget_cents = 350 AND r.region = 'us' THEN 5
       ELSE r.budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets r
```

```python
from sqlglot_composer import AS, FROM, SELECT, all_of, equals, first_match, statement
from references.<database>__region_budgets import region_budgets  # fill in <database>

t = region_budgets
s = statement(
    SELECT(t.job_id, t.budget_cents, t.region,
           AS(first_match([(all_of(equals(t.job_id, 3), equals(t.budget_cents, 350),
                                   equals(t.region, "us")), 5)],
                          otherwise=t.budget_cents / 100), "in_dollars"),
           # pointer: NULL AS pointer (refused, INDIRECT); files 03 to 05 have no NULL name, so
           # it comes in with project.convert on the Hive above
           ),
    FROM(t, reads_all_partitions=True),  # every row
)
```

Take out what you don't want converted (the pointer column, for one), fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X30

**Map.** Sources: scheduler_runs. Steps: none. Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter).

- Typed over: none. Marks: day is `RIGHT(dt, 2)`, so `SUBSTR(dt, -2)`.
- Refused: prev_run, `OFFSET(...)`, so `NULL AS prev_run`; jitter, `RANDBETWEEN(1,5)`, so `NULL AS jitter`.
- Left alone: the bar chart on sheet Summary, the PivotTable on sheet Pivot, the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT s.run_id, s.job_id, s.dt,
  SUBSTR(s.dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs s
```

Toolbox code: SUBSTR and NULL are not in files 03 to 05 (file 10 covers Hive functions), so only the plain columns are here; the rest comes in with `project.convert`.

```python
from sqlglot_composer import FROM, SELECT, statement
from references.<database>__scheduler_runs import scheduler_runs  # fill in <database>

s = statement(
    SELECT(scheduler_runs.run_id, scheduler_runs.job_id, scheduler_runs.dt),
    # day, prev_run, jitter: project.convert on the Hive above
    FROM(scheduler_runs, reads_all_partitions=True),  # every row, every day
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X31

**Map.** Sources: jobs. Steps: none. Finals: jobs (job_id, team, bump, tag, scaled, boosted).

- Typed over: none.
- Refused: bump (`[@bump]*2` reads its own column, circular): `NULL AS bump`. tag (`TAG(...)` is a defined name holding a LAMBDA): `NULL AS tag`. scaled (`Summary!$D$4` is a cell outside a Table, D4 on sheet Summary, and not a defined name): `NULL AS scaled`.
- Marks: boosted uses the defined name `boost`, a cell outside a Table (Summary!B2), so I used its value, 10. Move it into the Parameters Table, and use it from there.
- Left alone: the cells on Summary (B2, D4), which are outside a Table, and the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT j.job_id, j.team,
  NULL AS bump,
  NULL AS tag,
  NULL AS scaled,
  j.job_id * 10 AS boosted
FROM <database>.jobs j
```

```python
from sqlglot_composer import AS, FROM, SELECT, statement
from references.<database>__jobs import jobs  # fill in <database>

s = statement(
    SELECT(jobs.job_id, jobs.team,
           # bump, tag, scaled: NULL (refused); they come in with project.convert on the Hive
           AS(jobs.job_id * 10, "boosted")),  # 10 is the value of the name boost; move it to Parameters
    FROM(jobs, reads_all_partitions=True),  # every row
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X32

**Map.** Sources: job_runs (typed columns run_id to dt), jobs. Steps: job_runs (adds job_name; read by by_name). Finals: by_name (job_name, runs).

- by_name is a summary: its only typed column, job_name, is what its COUNTIFS matches on, so it is a GROUP BY of the job_runs step. Typed over: none. Refusals: none. Left alone: the Steps sheet.
- Marks: `VLOOKUP(.., jobs, 2, TRUE)` was approximate; I converted it exactly (a LEFT JOIN on job_id). The blanks in job_runs (run 98) aren't read by any formula.
- Fill in: `<database>`.

```sql
WITH job_runs_step AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name AS job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT job_name, COUNT(*) AS runs
FROM job_runs_step
GROUP BY job_name
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, all_columns, count_rows,
                              derived, equals, statement)
from references.<database>__job_runs import job_runs  # fill in <database>
from references.<database>__jobs import jobs

r, j = AS(job_runs, "r"), AS(jobs, "j")
job_runs_step = derived("job_runs_step", statement(
    SELECT(*all_columns(r), j.job_name),
    FROM(r, reads_all_partitions=True),  # every row
    LEFT_JOIN(j, ON=equals(r.job_id, j.job_id), reads_all_partitions=True),
))
s = statement(
    SELECT(job_runs_step.job_name, AS(count_rows(), "runs")),
    FROM(job_runs_step),
    GROUP_BY(job_runs_step.job_name),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X33

**Map.** Sources: job_runs (read by the query). Steps: none. Finals: slow_runs (run_id, duration_mins, over_by).

- The M reads `Sql.Database("dwh01", "ops")`, schema ops, item job_runs: I used the table it names, `<database>.job_runs`. Check which database that is (the M says server dwh01, database ops, schema ops).
- M's `<>` keeps a null, as Hive's doesn't, so `status <> 'TEST'` is written `(status <> 'TEST' OR status IS NULL)`. TransformColumnTypes: nothing. No formulas, no typed-over values, no refusals.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.duration_mins,
  r.duration_mins - 20 AS over_by
FROM <database>.job_runs r
WHERE r.duration_mins >= 20
  AND (r.status <> 'TEST' OR r.status IS NULL)
```

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, any_of, at_least, is_null, not_equals,
                              statement)
from references.<database>__job_runs import job_runs  # fill in <database>

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins,
           AS(job_runs.duration_mins - 20, "over_by")),
    FROM(job_runs, reads_all_partitions=True),  # the query has no date filter: every day
    WHERE(at_least(job_runs.duration_mins, 20),
          any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X34

**Map.** Sources: job_runs, jobs. Steps: runs_with_team (a query another reads). Finals: team_totals (team, total_mins, longest).

- No formulas, typed-over values or refusals. Table.NestedJoin with LeftOuter then ExpandTableColumn is a LEFT JOIN; Table.Group is a GROUP BY with List.Sum as SUM and List.Max as MAX. Left alone: the Steps sheet.
- Fill in: `<database>`.

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
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, all_columns, derived,
                              equals, max_of, statement, sum_of)
from references.<database>__job_runs import job_runs  # fill in <database>
from references.<database>__jobs import jobs

r, j = AS(job_runs, "r"), AS(jobs, "j")
runs_with_team = derived("runs_with_team", statement(
    SELECT(*all_columns(r), j.team),
    FROM(r, reads_all_partitions=True),  # every row
    LEFT_JOIN(j, ON=equals(r.job_id, j.job_id), reads_all_partitions=True),
))
s = statement(
    SELECT(runs_with_team.team,
           AS(sum_of(runs_with_team.duration_mins), "total_mins"),
           AS(max_of(runs_with_team.duration_mins), "longest")),
    FROM(runs_with_team),
    GROUP_BY(runs_with_team.team),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X35

**Map.** Sources: job_runs, scheduler_runs. Steps: none beyond the query's own parts. Finals: recent (run_id, dt).

- recent: SelectColumns on both, Table.Combine is UNION ALL, Table.Sort then FirstN is ORDER BY run_id DESC LIMIT 4. No formulas, typed-over values or blanks read.
- Refused: the query "rates" reads Web.Contents (a web source), so I left that query out; it has no Table and no final.
- Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
WITH runs AS (
  SELECT run_id, dt FROM <database>.job_runs
), scheduled AS (
  SELECT run_id, dt FROM <database>.scheduler_runs
), both_runs AS (
  SELECT run_id, dt FROM runs
  UNION ALL
  SELECT run_id, dt FROM scheduled
)
SELECT run_id, dt
FROM both_runs
ORDER BY run_id DESC
LIMIT 4
```

```python
from sqlglot_composer import (FROM, LIMIT, ORDER_BY, SELECT, UNION_ALL, derived, descending,
                              statement)
from references.<database>__job_runs import job_runs  # fill in <database>
from references.<database>__scheduler_runs import scheduler_runs

runs = statement(SELECT(job_runs.run_id, job_runs.dt),
                 FROM(job_runs, reads_all_partitions=True))  # every day
scheduled = statement(SELECT(scheduler_runs.run_id, scheduler_runs.dt),
                      FROM(scheduler_runs, reads_all_partitions=True))
both_runs = derived("both_runs", UNION_ALL(runs, scheduled))  # if a Derived table won't take a stack, run project.convert on the Hive
s = statement(
    SELECT(both_runs.run_id, both_runs.dt),
    FROM(both_runs),
    ORDER_BY(descending(both_runs.run_id)),
    LIMIT(4),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X36

**Map.** Sources: run_alerts, job_runs. Steps: none. Finals: job_runs (run_id, status, alerts) and severity_by_day (dt, high, low).

- job_runs: alerts is a COUNTIFS over another Table, so a LEFT JOIN of `(SELECT run_id, COUNT(*) AS total FROM run_alerts GROUP BY run_id)`, wrapped in COALESCE(.., 0), as Excel gives 0 where nothing matches. job_runs is not a summary (status is typed and isn't matched on). The blank status of run 98 isn't read by a formula.
- severity_by_day: Table.Pivot, one `SUM(CASE WHEN severity = '..' THEN 1 END)` column per value in the sample, `high` and `low`, NULL where none, as M leaves it. The pivot's columns are now fixed: a new severity value won't get a column.
- Typed over: none. Refusals: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.status,
  COALESCE(a.total, 0) AS alerts
FROM <database>.job_runs r
LEFT JOIN (SELECT run_id, COUNT(*) AS total
           FROM <database>.run_alerts GROUP BY run_id) a ON r.run_id = a.run_id
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
                              equals, fill_null, statement, sum_of, if_else)
from references.<database>__job_runs import job_runs      # fill in <database>
from references.<database>__run_alerts import run_alerts

a = derived("a", statement(
    SELECT(run_alerts.run_id, AS(count_rows(), "total")),
    FROM(run_alerts, reads_all_partitions=True),  # every day
    GROUP_BY(run_alerts.run_id),
))
runs = statement(
    SELECT(job_runs.run_id, job_runs.status, AS(fill_null(a.total, 0), "alerts")),
    FROM(job_runs, reads_all_partitions=True),  # every row
    LEFT_JOIN(a, ON=equals(a.run_id, job_runs.run_id)),
)
by_day = statement(
    SELECT(run_alerts.dt,
           AS(sum_of(if_else(equals(run_alerts.severity, "high"), 1, None)), "high"),
           AS(sum_of(if_else(equals(run_alerts.severity, "low"), 1, None)), "low")),
    FROM(run_alerts, reads_all_partitions=True),  # every day
    GROUP_BY(run_alerts.dt),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ (the pivot's `None` is the first place to check).

## X37

**Map.** Sources: Owners. Steps: none. Finals: Owners (`<job_no>`, `<team_name>`, Owner, Day, `<is_ana>`).

- Names: `Job No` is `<job_no>`, `Team Name` is `<team_name>`, `Is Ana` is `<is_ana>`; `Owner` and `Day` are plain, kept. Typed over: none. Refusals: none. Left alone: the Steps sheet.
- Marks: blank. Job 4 (web) has a blank Owner, and the IF reads it, so I wrapped `COALESCE(Owner, '')`; Excel reads it as "", Hive as NULL. All 56 rows are kept, as no formula or query filters.
- Fill in: `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

```sql
SELECT o.<job_no>, o.<team_name>, o.Owner, o.Day,
  IF(COALESCE(o.Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners o
```

```python
from sqlglot_composer import AS, FROM, SELECT, equals, fill_null, if_else, statement
from references.<database>__Owners import Owners  # fill in <database>

s = statement(
    SELECT(Owners.<job_no>, Owners.<team_name>, Owners.Owner, Owners.Day,  # fill in the names
           AS(if_else(equals(fill_null(Owners.Owner, ""), "ana"), 1, 0), "<is_ana>")),
    FROM(Owners, reads_all_partitions=True),  # every row
)
```

Take out what you don't want converted, fill in each `<...>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X38

**Map.** Sources: job_runs, jobs. Steps: none. Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost).

- Typed over: retry_cost where run_id is 102 (value 1), matched on the Keys row for job_runs, run_id.
- region: XLOOKUP, a LEFT JOIN on jobs. region_mins: SUMIFS over its own Table, `SUM(duration_mins) OVER (PARTITION BY region)`, in COALESCE(.., 0); the partition uses the joined region.
- Marks: blank. Run 98 has a blank avg_retry_secs, which retry_cost reads, so `COALESCE(avg_retry_secs, 0)`. duration_mins in the SUMIFS isn't wrapped.
- Refusals: none. Left alone: the Steps sheet.
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
from references.<database>__job_runs import job_runs  # fill in <database>
from references.<database>__jobs import jobs

r, j = AS(job_runs, "r"), AS(jobs, "j")
per_region = window(PARTITION_BY=j.region)
s = statement(
    SELECT(r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
           AS(j.region, "region"),
           AS(fill_null(sum_of(r.duration_mins, over=per_region), 0), "region_mins"),
           AS(first_match([(equals(r.run_id, 102), 1)],
                          otherwise=(fill_null(r.avg_retry_secs, 0) + r.duration_mins) * 2),
              "retry_cost")),
    FROM(r, reads_all_partitions=True),  # every row
    LEFT_JOIN(j, ON=equals(r.job_id, j.job_id), reads_all_partitions=True),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X39

**Map.** Sources: job_runs, jobs. Steps: none. Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise), loaded by a query and given three formula columns.

- The query: Table.SelectRows `status = "SUCCESS"` is a WHERE; SelectColumns is the SELECT list. job_name is XLOOKUP, a LEFT JOIN on jobs. share is `duration_mins / SUMIFS(..)` over its own Table: `SUM(duration_mins) OVER (PARTITION BY job_id)`, in COALESCE(.., 0); the window runs after the WHERE, so it adds up only the ok runs.
- Refused: noise, `RAND()`, so `NULL AS noise`.
- Typed over: none. Blanks: the blank status of run 98 is filtered out by the query. Left alone: the Steps sheet.
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

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, WHERE, equals, fill_null,
                              statement, sum_of, window)
from references.<database>__job_runs import job_runs  # fill in <database>
from references.<database>__jobs import jobs

r, j = AS(job_runs, "r"), AS(jobs, "j")
per_job = window(PARTITION_BY=r.job_id)
s = statement(
    SELECT(r.run_id, r.job_id, r.duration_mins,
           AS(j.job_name, "job_name"),
           AS(r.duration_mins / fill_null(sum_of(r.duration_mins, over=per_job), 0), "share"),
           # noise: NULL AS noise (refused, RAND); it comes in with project.convert
           ),
    FROM(r, reads_all_partitions=True),  # the query has no date filter: every day
    LEFT_JOIN(j, ON=equals(r.job_id, j.job_id), reads_all_partitions=True),
    WHERE(equals(r.status, "SUCCESS")),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X40

**Map.** Sources: Runs (typed Run, Job, Mins), jobs, run_alerts. Steps: Runs (adds Team and Cost; read by Teams and run_alerts). Finals: Teams (Team, `<total_cost>`) and run_alerts (alert_id, run_id, severity, dt, `<run_mins>`). Parameters is neither.

- Teams is a summary: its only typed column, Team, is what its SUMIFS matches on, so it is a GROUP BY of the Runs step, with `COALESCE(SUM(Cost), 0)`.
- Marks: `XLOOKUP("rate", Parameters[name], Parameters[value])` is the value, 2. Runs.Team is a LEFT JOIN on jobs. run_alerts' Run Mins is a LEFT JOIN on the Runs step.
- Names: `Total Cost` is `<total_cost>`, `Run Mins` is `<run_mins>`; Run, Job, Mins, Team, Cost are plain.
- Typed over: none. Refusals: none. Left alone: the PivotTable on sheet "Pivot" (from Table Runs), and the Steps sheet.
- Fill in: `<database>`, `<total_cost>`, `<run_mins>`.

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

```sql
WITH runs_step AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt,
  s.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN runs_step s ON a.run_id = s.Run
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, derived, equals,
                              fill_null, statement, sum_of)
from references.<database>__Runs import Runs              # fill in <database>
from references.<database>__jobs import jobs
from references.<database>__run_alerts import run_alerts

j = AS(jobs, "j")
runs_step = derived("runs_step", statement(
    SELECT(Runs.Run, Runs.Job, Runs.Mins, AS(j.team, "Team"), AS(Runs.Mins * 2, "Cost")),
    FROM(Runs, reads_all_partitions=True),  # every row
    LEFT_JOIN(j, ON=equals(Runs.Job, j.job_id), reads_all_partitions=True),
))
teams = statement(
    SELECT(runs_step.Team, AS(fill_null(sum_of(runs_step.Cost), 0), "<total_cost>")),  # fill in
    FROM(runs_step),
    GROUP_BY(runs_step.Team),
)
alerts = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt,
           AS(runs_step.Mins, "<run_mins>")),  # fill in
    FROM(run_alerts, reads_all_partitions=True),  # every day
    LEFT_JOIN(runs_step, ON=equals(run_alerts.run_id, runs_step.Run)),
)
```

Take out what you don't want converted, fill in each `<...>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X46

**Map.** Sources: jobs, job_runs. Steps: counts (the MINIFS and COUNTIF over job_runs, one grouped subquery since both use only job_id). Finals: jobs (job_id, job_name, team, shortest, runs, busiest).

- shortest: MINIFS is MIN, in COALESCE(.., 0); runs: COUNTIF is COUNT(*), in COALESCE(.., 0). busiest: `RANK.EQ(runs, jobs[runs])` is `RANK() OVER (ORDER BY runs DESC)`, on the same COALESCE(runs, 0) expression, since a window can't read its own SELECT's alias.
- Typed over: none. Refusals: none. Blanks: job_runs' blank status and avg_retry_secs aren't read; duration_mins sits inside an -IFS form, which skips a blank. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
WITH counts AS (
  SELECT job_id, MIN(duration_mins) AS shortest, COUNT(*) AS runs
  FROM <database>.job_runs
  GROUP BY job_id
)
SELECT j.job_id, j.job_name, j.team,
  COALESCE(c.shortest, 0) AS shortest,
  COALESCE(c.runs, 0) AS runs,
  RANK() OVER (ORDER BY COALESCE(c.runs, 0) DESC) AS busiest
FROM <database>.jobs j
LEFT JOIN counts c ON j.job_id = c.job_id
```

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, count_rows, derived,
                              descending, equals, fill_null, min_of, rank, statement, window)
from references.<database>__jobs import jobs          # fill in <database>
from references.<database>__job_runs import job_runs

counts = derived("counts", statement(
    SELECT(job_runs.job_id, AS(min_of(job_runs.duration_mins), "shortest"),
           AS(count_rows(), "runs")),
    FROM(job_runs, reads_all_partitions=True),  # every day
    GROUP_BY(job_runs.job_id),
))
by_runs = window(ORDER_BY=descending(fill_null(counts.runs, 0)))
s = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team,
           AS(fill_null(counts.shortest, 0), "shortest"),
           AS(fill_null(counts.runs, 0), "runs"),
           AS(rank(over=by_runs), "busiest")),
    FROM(jobs, reads_all_partitions=True),  # every row
    LEFT_JOIN(counts, ON=equals(counts.job_id, jobs.job_id)),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X47

**Map.** Sources: region_budgets. Steps: none. Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg).

- cheapest_first: `RANK.EQ(x, t[x], 1)` with 1 as the third argument is ascending: `RANK() OVER (ORDER BY budget_cents ASC)`. region_total: SUMIF over its own Table, `SUM(budget_cents) OVER (PARTITION BY region)`, in COALESCE(.., 0). region_avg: AVERAGEIF, `AVG(budget_cents) OVER (PARTITION BY region)`, left NULL.
- Typed over: none. Refusals: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT r.job_id, r.budget_cents, r.region,
  RANK() OVER (ORDER BY r.budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(r.budget_cents) OVER (PARTITION BY r.region), 0) AS region_total,
  AVG(r.budget_cents) OVER (PARTITION BY r.region) AS region_avg
FROM <database>.region_budgets r
```

```python
from sqlglot_composer import (AS, FROM, SELECT, average_of, fill_null, rank, statement,
                              sum_of, window)
from references.<database>__region_budgets import region_budgets  # fill in <database>

t = region_budgets
by_budget = window(ORDER_BY=t.budget_cents)
by_region = window(PARTITION_BY=t.region)
s = statement(
    SELECT(t.job_id, t.budget_cents, t.region,
           AS(rank(over=by_budget), "cheapest_first"),
           AS(fill_null(sum_of(t.budget_cents, over=by_region), 0), "region_total"),
           AS(average_of(t.budget_cents, over=by_region), "region_avg")),
    FROM(t, reads_all_partitions=True),  # every row
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X48

**Map.** Sources: job_runs, jobs, run_alerts. Steps: none. Finals: quiet_runs (run_id, job_id, status) and slow_regions (region, avg_mins, fastest).

- quiet_runs: NestedJoin with LeftAnti is `LEFT JOIN run_alerts ON .. WHERE a.run_id IS NULL`, giving the first table's columns. slow_regions: an Inner join (JOIN) with jobs, Table.Group by region (List.Average as AVG, List.Min as MIN), then the SelectRows on the grouped column as HAVING, repeating the aggregate.
- No formulas, typed-over values or refusals. Blank: the blank status in run 98 is kept as it is, and duration_mins is not filtered. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

```sql
SELECT j.region,
  AVG(r.duration_mins) AS avg_mins,
  MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

```python
from sqlglot_composer import (ANTI_JOIN, AS, FROM, GROUP_BY, HAVING, JOIN, SELECT, at_least,
                              average_of, equals, min_of, statement)
from references.<database>__job_runs import job_runs      # fill in <database>
from references.<database>__jobs import jobs
from references.<database>__run_alerts import run_alerts

r, j, a = AS(job_runs, "r"), AS(jobs, "j"), AS(run_alerts, "a")
quiet_runs = statement(
    SELECT(r.run_id, r.job_id, r.status),
    FROM(r, reads_all_partitions=True),  # every day
    ANTI_JOIN(a, ON=equals(a.run_id, r.run_id), reads_all_partitions=True),  # same rows as the LEFT JOIN .. IS NULL
)
slow_regions = statement(
    SELECT(j.region, AS(average_of(r.duration_mins), "avg_mins"),
           AS(min_of(r.duration_mins), "fastest")),
    FROM(r, reads_all_partitions=True),
    JOIN(j, ON=equals(j.job_id, r.job_id), reads_all_partitions=True),
    GROUP_BY(j.region),
    HAVING(at_least(average_of(r.duration_mins), 20)),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X49

**Map.** Sources: job_runs, jobs, run_alerts, scheduler_runs, job_owners. Steps: none. Finals: alert_status (alert_id, severity, status), run_check (run_id, status, scheduled_run), teams (team): three queries, nothing reads any of them.

- alert_status: JoinKind.RightOuter is a LEFT JOIN with the tables swapped (job_runs first, run_alerts joined), so every run is kept and the alert columns are NULL for a run with no alert.
- run_check: FullOuter is a FULL OUTER JOIN of the run_id and status columns of job_runs with scheduler_runs, the joined run_id named scheduled_run.
- teams: Table.Distinct around Table.Combine is UNION (it drops repeats).
- No formulas, typed-over values or refusals. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
```

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM (SELECT run_id, status FROM <database>.job_runs) r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

```python
from sqlglot_composer import (AS, FROM, FULL_JOIN, LEFT_JOIN, SELECT, UNION, derived, equals,
                              statement)
from references.<database>__job_runs import job_runs            # fill in <database>
from references.<database>__run_alerts import run_alerts
from references.<database>__scheduler_runs import scheduler_runs
from references.<database>__jobs import jobs
from references.<database>__job_owners import job_owners

r, a, sr = AS(job_runs, "r"), AS(run_alerts, "a"), AS(scheduler_runs, "s")

alert_status = statement(
    SELECT(a.alert_id, a.severity, r.status),
    FROM(r, reads_all_partitions=True),  # every day
    LEFT_JOIN(a, ON=equals(a.run_id, r.run_id), reads_all_partitions=True),
)

runs = derived("r", statement(
    SELECT(job_runs.run_id, job_runs.status),
    FROM(job_runs, reads_all_partitions=True),
))
run_check = statement(
    SELECT(runs.run_id, runs.status, AS(sr.run_id, "scheduled_run")),
    FROM(runs),
    FULL_JOIN(sr, ON=equals(runs.run_id, sr.run_id), reads_all_partitions=True),
)

teams = UNION(
    statement(SELECT(jobs.team), FROM(jobs, reads_all_partitions=True)),
    statement(SELECT(job_owners.team), FROM(job_owners, reads_all_partitions=True)),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.

## X50

**Map.** Sources: job_owners, jobs. Steps: owners_q (the query: job_id and owner, distinct). Finals: owners (job_id, owner, job_name, newest_first), a query-loaded Table given two formula columns.

- The query: SelectColumns then Table.Distinct alone is `SELECT DISTINCT job_id, owner`. job_name is an XLOOKUP, a LEFT JOIN on jobs. newest_first is `RANK.EQ(job_id, owners[job_id])`: `RANK() OVER (ORDER BY job_id DESC)`, over the owners rows (so job 3, with two owners, has two rows of the same rank).
- Blank: owner is blank for job 4, but no formula reads owner, so nothing is wrapped. Typed over: none. Refusals: none. Left alone: the Steps sheet.
- Fill in: `<database>`.

```sql
WITH owners_q AS (
  SELECT DISTINCT job_id, owner
  FROM <database>.job_owners
)
SELECT o.job_id, o.owner,
  j.job_name AS job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM owners_q o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, SELECT_DISTINCT, derived,
                              descending, equals, rank, statement, window)
from references.<database>__job_owners import job_owners  # fill in <database>
from references.<database>__jobs import jobs

owners_q = derived("owners_q", statement(
    SELECT_DISTINCT(job_owners.job_id, job_owners.owner),
    FROM(job_owners, reads_all_partitions=True),  # the query has no date filter: every day
))
j = AS(jobs, "j")
newest = window(ORDER_BY=descending(owners_q.job_id))
s = statement(
    SELECT(owners_q.job_id, owners_q.owner, AS(j.job_name, "job_name"),
           AS(rank(over=newest), "newest_first")),
    FROM(owners_q),
    LEFT_JOIN(j, ON=equals(owners_q.job_id, j.job_id), reads_all_partitions=True),
)
```

Take out what you don't want converted, fill in `<database>`, run `project.convert` on the Hive; its checked code wins where the two differ.
