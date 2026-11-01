date: 2026-11-01
arm: C
model: haiku
files: 19-held

## X21

### Map
- **Sources:** region_budgets (typed columns job_id, budget_cents, region), read as `<database>.region_budgets`.
- **Steps:** none.
- **Finals:** region_budgets (job_id, budget_cents, region, budget_dollars, with_margin). Its two formula columns read only its own row and nothing else reads it, so it is a final.
- **Typed over a formula:** none, so Keys needs no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys (both empty; settings Tables, never a source, step or final); the Steps sheet (cells outside a Table). No Power Query or Total Row in this workbook.
- **To fill in:** `<database>`.

### Hive
```sql
SELECT job_id, budget_cents, region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X22

### Map
- **Sources:** jobs (typed columns job_id, job_name, team), read as `<database>.jobs`.
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, team, is_finance, ratio). Its formula columns read only its own row and nothing else reads it, so it is a final.
- **Typed over a formula:** none, so Keys needs no row.
- **Marks:** is_finance. Excel's `=` ignores case and Hive's `=` keeps it. The sample's team values are all lower case, so every row gives the value Excel gives.
- **Refusals:** none.
- **Left alone:** Parameters and Keys (both empty; settings Tables, never a source, step or final); the Steps sheet (cells outside a Table). No Power Query or Total Row in this workbook.
- **To fill in:** `<database>`.

### Hive
```sql
SELECT job_id, job_name, team,
  IF(team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(job_id / (job_id - 2), 0) AS ratio
FROM <database>.jobs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X23

### Map
- **Sources:** job_runs (typed columns run_id, status, avg_retry_secs), read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, status, avg_retry_secs, label, risky). Its formula columns read only its own row and nothing else reads it, so it is a final.
- **Typed over a formula:** none, so Keys needs no row.
- **Marks:**
  - blank: row 98 has a blank status and a blank avg_retry_secs. status is read by label and risky, so it is written COALESCE(status, '') in both. avg_retry_secs is read by risky, so it is written COALESCE(avg_retry_secs, 0) there. Excel gives "other" and FALSE for that row, and so does the Hive.
  - case: Excel's SWITCH and `=` ignore case and Hive's keep it. The sample's status values are all upper case, so every row matches.
  - `_xlfn.SWITCH` is read as SWITCH, with its two pairs and its default written as a CASE.
- **Refusals:** none.
- **Left alone:** Parameters and Keys (both empty; settings Tables, never a source, step or final); the Steps sheet (cells outside a Table). No Power Query or Total Row in this workbook.
- **To fill in:** `<database>`.

### Hive
```sql
SELECT run_id, status, avg_retry_secs,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label,
  (COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X24

### Map
- **Sources:** team_notes (typed columns team, note, written_on), read as `<database>.team_notes`.
- **Steps:** none.
- **Finals:** team_notes (team, note, written_on, first_word, shout, month, tens_of_chars). Its formula columns read only its own row and nothing else reads it, so it is a final.
- **Typed over a formula:** none, so Keys needs no row.
- **Marks:** none. No blank sits in a column a formula reads, every note has a space for FIND, and no formula compares text.
- **Refusals:** none.
- **Left alone:** Parameters and Keys (both empty; settings Tables, never a source, step or final); the Steps sheet (cells outside a Table). No Power Query or Total Row in this workbook.
- **To fill in:** `<database>`.

### Hive
```sql
SELECT team, note, written_on,
  SUBSTR(note, 1, INSTR(note, ' ') - 1) AS first_word,
  UPPER(team) AS shout,
  MONTH(written_on) AS month,
  ROUND(LENGTH(note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X25

### Map
- **Sources:**
  - Costs (typed columns Job, Cost (cents), Region, Day Key), read as `<database>.Costs`.
  - Budgets (typed columns Job, Budget, Region), read as `<database>.Budgets`.
- **Steps:** none.
- **Finals:**
  - Costs (Job, Cost (cents), Region, Day Key, Day). Its formula column reads only its own row and nothing else reads it, so it is a final.
  - Budgets (Job, Budget, Region, Dollars). Its formula column reads only its own row and nothing else reads it, so it is a final.
- **Typed over a formula:** none, so Keys needs no row.
- **Marks:**
  - Costs Day: Day Key is a date held as text (20260911). It is written as CONCAT(SUBSTR, '-', SUBSTR, '-', SUBSTR), giving a 'yyyy-mm-dd' string, the form Excel's DATE gives. Check the Day column against the workbook.
  - Costs row 29 has a blank Cost (cents). No formula reads that column, so it is no mark and passes through as NULL.
- **Refusals:** none.
- **Left alone:** Parameters and Keys (both empty; settings Tables, never a source, step or final); the Steps sheet (cells outside a Table). No Power Query or Total Row in this workbook.
- **To fill in:** `<database>`, `<cost_cents>` (the Cost (cents) column) and `<day_key>` (the Day Key column).

### Hive
```sql
SELECT Job, <cost_cents>, Region, <day_key>,
  CONCAT(SUBSTR(<day_key>, 1, 4), '-', SUBSTR(<day_key>, 5, 2), '-', SUBSTR(<day_key>, 7, 2)) AS Day
FROM <database>.Costs
```
```sql
SELECT Job, Budget, Region, Budget / 100 AS Dollars
FROM <database>.Budgets
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X26

### Map
- **Sources**: `job_runs`, all its columns typed (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read by no query; `run_alerts`, its typed columns (alert_id, run_id, severity).
- **Steps**: none. No query loads a Table, and no Table's formula is read by another.
- **Finals**: `run_alerts` (alert_id, run_id, severity, job_id, status, avg_mins). Its formula columns are read by nothing else, so it is a final.
  - job_id: XLOOKUP on run_id into job_runs, a LEFT JOIN on run_id, then job_id.
  - status: VLOOKUP on run_id, column 3 of job_runs, the same LEFT JOIN, then status.
  - avg_mins: AVERAGEIFS over job_runs on this row's job_id, as AVG; left NULL where no run matches.
- **Typed over a formula**: none. Every formula cell in run_alerts holds its formula, and Keys is empty.
- **Marks**: blank. job_runs' status is blank at run 98 in the sample, and the VLOOKUP reads that column, so status is written `COALESCE(jr.status, '')`.
- **Refusals**: none.
- **Left alone**: the Steps sheet and the D1 notes (cells outside a Table); Parameters and Keys, both empty settings, never a source, step or final.
- **To fill in**: `<database>`, in each source and in the final.

### Hive
```sql
SELECT ra.alert_id, ra.run_id, ra.severity,
  jr.job_id,
  COALESCE(jr.status, '') AS status,
  g.avg_mins
FROM <database>.run_alerts ra
LEFT JOIN <database>.job_runs jr ON ra.run_id = jr.run_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) g ON jr.job_id = g.job_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X27

### Map
- **Sources**: `jobs`, all its columns typed (job_id, job_name, team, region), read by no query.
- **Steps**: none.
- **Finals**: `by_team` (team, jobs_in_team, last_job_id, last_job_name), a summary. Its only typed column, team, is the one its COUNTIFS matches on, so its typed groups (data, finance, web) are typed in and `jobs` is read.
  - jobs_in_team: COUNTIFS over jobs on team, as COUNT(*), with COALESCE to 0.
  - last_job_id: MAXIFS over jobs on team, as MAX, with COALESCE to 0.
  - last_job_name: INDEX and MATCH on this row's last_job_id, a LEFT JOIN on job_id, then job_name.
- **Typed over a formula**: none. Keys is empty.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet and the D1 notes (cells outside a Table); Parameters and Keys, both empty settings, never a source, step or final.
- **To fill in**: `<database>`, in each source and in the final.

### Hive
```sql
SELECT t.team,
  COALESCE(c.jobs_in_team, 0) AS jobs_in_team,
  COALESCE(m.last_job_id, 0) AS last_job_id,
  jn.job_name AS last_job_name
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (SELECT team, COUNT(*) AS jobs_in_team FROM <database>.jobs GROUP BY team) c
  ON t.team = c.team
LEFT JOIN (SELECT team, MAX(job_id) AS last_job_id FROM <database>.jobs GROUP BY team) m
  ON t.team = m.team
LEFT JOIN <database>.jobs jn
  ON m.last_job_id = jn.job_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X28

### Map
- **Sources**: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read by no query; `jobs`, its typed columns (job_id, job_name).
- **Steps**: none.
- **Finals**: `jobs` (job_id, job_name, ok_mins). It is not a summary, as job_name is typed too. ok_mins is SUMIFS over job_runs on this row's job_id with status "SUCCESS": a LEFT JOIN onto a grouped SUM, with COALESCE to 0.
- **Typed over a formula**: ok_mins at job_id 3 (report_build), typed as 99. The Keys row is `jobs` with `job_id`, so the CASE matches on job_id.
- **Marks**: none. The blank status at run 98 is skipped by SUMIFS, which sits in an -IFS form, so status is written as it is.
- **Refusals**: none.
- **Left alone**: the Steps sheet and the D1 notes (cells outside a Table); Parameters, an empty settings Table, never a source, step or final.
- **To fill in**: `<database>`, in each source and in the final.

### Hive
```sql
SELECT j.job_id, j.job_name,
  CASE WHEN j.job_id = 3 THEN 99 ELSE COALESCE(s.total, 0) END AS ok_mins
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
  GROUP BY job_id
) s ON j.job_id = s.job_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X29

### Map
- **Sources**: `region_budgets`, its typed columns (job_id, budget_cents, region).
- **Steps**: none.
- **Finals**: `region_budgets` (job_id, budget_cents, region, in_dollars, pointer).
  - in_dollars: budget_cents divided by Parameters' cents_per_dollar, read in as its value, 100.
  - pointer: refused.
- **Typed over a formula**: in_dollars at job_id 3 (budget_cents 350, region us), typed as 5. Keys holds no row for region_budgets, so there is no Keys row here, and the CASE matches every typed column of the row: job_id, budget_cents and region.
- **Marks**: none.
- **Refusals**: pointer, `NULL AS pointer`. Both INDIRECT and ROW() are refused.
- **Left alone**: the Steps sheet and the D1 notes (cells outside a Table); Keys, an empty settings Table; Parameters, read in by value, never a source, step or final.
- **To fill in**: `<database>`, in each source and in the final.

### Hive
```sql
SELECT job_id, budget_cents, region,
  CASE WHEN job_id = 3 AND budget_cents = 350 AND region = 'us' THEN 5
    ELSE budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X30

### Map
- **Sources**: `scheduler_runs`, its typed columns (run_id, job_id, dt).
- **Steps**: none.
- **Finals**: `scheduler_runs` (run_id, job_id, dt, day, prev_run, jitter). Its formula columns are read by nothing else, so it is a final.
  - day: RIGHT(dt, 2), written as SUBSTR(dt, -2).
  - prev_run: refused.
  - jitter: refused.
- **Typed over a formula**: none. Keys and Parameters are empty.
- **Marks**: none.
- **Refusals**: prev_run, `NULL AS prev_run`, as OFFSET reads the row before. jitter, `NULL AS jitter`, as RANDBETWEEN is refused.
- **Left alone**: the bar chart on the Summary sheet, and the PivotTable on the Pivot sheet (from scheduler_runs); the Steps sheet and the D1 notes (cells outside a Table); Parameters and Keys, both empty settings, never a source, step or final.
- **To fill in**: `<database>`, in the source and in the final.

### Hive
```sql
SELECT run_id, job_id, dt,
  SUBSTR(dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X31

### Map

**Sources**
- `jobs`: typed columns `job_id`, `team`, read from `<database>.jobs`. The typed rows are a sample, so the table is read, not the rows.

**Steps**
- None. No query loads a Table, and no other Table's formula reads `jobs`.

**Finals**
- `jobs` (job_id, team, bump, tag, scaled, boosted). No query loads it and no other Table's formula reads it, so it is a final. Its own formula columns reading its own row don't count.

**Typed over a formula**
- None. The Keys Table is empty.

**Marks**
- `boosted`: `boost` is a defined name for `Summary!B2`, a cell outside a Table. Written as its value 10: `job_id * 10`. Move the 10 into Parameters.

**Refusals (NULL AS its header)**
- `bump`: the formula reads its own column (circular).
- `tag`: `TAG` is a defined name holding a LAMBDA.
- `scaled`: reads `Summary!D4`, a cell outside a Table that is not a defined name.

**Left alone**
- Parameters and Keys: both empty, never a source, step or final, so left out.
- The Steps sheet, as it ships.
- The Summary cells other than B2 and D4.

**To fill in**
- `<database>` in the `jobs` final.

### Hive

```sql
SELECT job_id, team,
  NULL AS bump,
  NULL AS tag,
  NULL AS scaled,
  job_id * 10 AS boosted
FROM <database>.jobs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X32

### Map

**Sources**
- `job_runs`: typed columns `run_id`, `job_id`, `status`, `duration_mins`, `avg_retry_secs`, `dt`, read from `<database>.job_runs`.
- `jobs`: typed columns `job_id`, `job_name`, `team`, `region`, read from `<database>.jobs`.

**Steps**
- `job_runs`, with its formula column `job_name` (run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name). `by_name`'s COUNTIFS reads `job_runs[job_name]`, so `job_runs` is a step, not a final. It is a CTE in `by_name`'s block.

**Finals**
- `by_name` (job_name, runs), a summary. Its only typed column is the one COUNTIFS matches on. Its typed groups (invoice_sync, nightly_load, report_build) are typed in, and runs is a COUNT(*) over the `job_runs` step, COALESCE to 0.

**Typed over a formula**
- None. The Keys Table is empty.

**Marks**
- `job_name` in `job_runs`: `VLOOKUP(..., jobs, 2, TRUE)` is approximate. Written as the exact match, a LEFT JOIN on `job_id` to `jobs`, taking `job_name`.
- No blank mark: the blanks in `status` and `avg_retry_secs` (run 98) are read by no formula.

**Refusals**
- None.

**Left alone**
- Parameters and Keys: both empty, left out.

**To fill in**
- `<database>` in each read.

### Hive

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT g.job_name, COALESCE(c.runs, 0) AS runs
FROM (SELECT 'invoice_sync' AS job_name
  UNION ALL SELECT 'nightly_load'
  UNION ALL SELECT 'report_build') g
LEFT JOIN (SELECT job_name, COUNT(*) AS runs FROM job_runs GROUP BY job_name) c
  ON g.job_name = c.job_name
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X33

### Map

**Sources**
- `job_runs`, outside the workbook: the Power Query `slow_runs` reads `Sql.Database("dwh01", "ops")`, item `job_runs`. Columns read: run_id, duration_mins, status. Read as `<database>.job_runs`.

**Steps**
- None.

**Finals**
- `slow_runs` (run_id, duration_mins, over_by). The query `slow_runs` loads it and no Table's formula reads it, so it is a final. Its rows are the query's, not the sample rows typed in.

**Typed over a formula**
- None. The Keys Table is empty.

**Marks**
- Source named for the user to check: the query reads server `dwh01`, schema `ops`, table `job_runs`. Check that `<database>` is that database.
- `status <> "TEST"`: M's `<>` keeps a null, so it is written `(status <> 'TEST' OR status IS NULL)`.

**Refusals**
- None.

**Left alone**
- Parameters and Keys: both empty, left out.

**To fill in**
- `<database>` in the final.

### Hive

```sql
SELECT run_id, duration_mins, duration_mins - 20 AS over_by
FROM <database>.job_runs
WHERE duration_mins >= 20 AND (status <> 'TEST' OR status IS NULL)
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X34

### Map

**Sources**
- `job_runs`: typed columns `run_id`, `job_id`, `status`, `duration_mins`, `avg_retry_secs`, `dt`, read from `<database>.job_runs`.
- `jobs`: typed columns `job_id`, `job_name`, `team`, `region`, read from `<database>.jobs`.

**Steps**
- `runs_with_team` (query, connection only, columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, team). `team_totals` names it, so it is a step, a CTE in `team_totals`'s block. Its NestedJoin, LeftOuter, is a LEFT JOIN on `job_id`, expanding `team`.

**Finals**
- `team_totals` (team, total_mins, longest). The query `team_totals` loads it and no Table's formula reads it, so it is a final. Its rows are the query's.

**Typed over a formula**
- None. The Keys Table is empty.

**Marks**
- None.

**Refusals**
- None.

**Left alone**
- Parameters and Keys: both empty, left out.

**To fill in**
- `<database>` in each read.

### Hive

```sql
WITH runs_with_team AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT team, SUM(duration_mins) AS total_mins, MAX(duration_mins) AS longest
FROM runs_with_team
GROUP BY team
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X35

### Map

**Sources**
- `job_runs`: columns run_id, dt, read from `<database>.job_runs`.
- `scheduler_runs`: columns run_id, dt, read from `<database>.scheduler_runs`.

**Steps**
- None. No Table's formula reads `recent`, and no query names another query.

**Finals**
- `recent` (run_id, dt). The query `recent` loads it and no formula reads it, so it is a final. Its rows are the query's: the two sources stacked with UNION ALL, sorted by run_id descending, the top 4 kept.

**Typed over a formula**
- None. The Keys Table is empty.

**Marks**
- None.

**Refusals**
- The query `rates` is left out: it reads a web source through `Web.Contents`, loads nothing, and nothing reads it. Named here, not in the Hive.

**Left alone**
- Parameters and Keys: both empty, left out.

**To fill in**
- `<database>` in each read.

### Hive

```sql
SELECT run_id, dt
FROM (
  SELECT run_id, dt FROM <database>.job_runs
  UNION ALL
  SELECT run_id, dt FROM <database>.scheduler_runs
) runs_both
ORDER BY run_id DESC
LIMIT 4
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X36

### Map

**Sources**
- `run_alerts` (alert_id, run_id, severity, dt): its typed columns, read as `<database>.run_alerts`.
- `job_runs` (run_id, status): its typed columns, read as `<database>.job_runs`.

**Steps**
- None.

**Finals**
- Table `job_runs` (run_id, status, alerts): it has a formula column, no query loads it, and no other Table's formula or query reads it, so it is a final.
- Table `severity_by_day` (dt, high, low): loaded by query `severity_by_day`, and no Table's formula reads it, so it is a final, its rows the query's.
- Query `severity_by_day`: it loads Table `severity_by_day` and nothing names it, so it is not a step. Its M is that final's query.

**Parameters and Keys**: empty settings Tables, never a source, step or final. Nothing to convert.

**Typed over a formula**: none.

**Marks**
- `severity_by_day`, Table.Pivot: the pivot columns `high` and `low` are fixed as the severity values in the sample now. NULL where a severity has no rows, as M leaves it.

**Refusals**: none.

**Left alone**: the Steps sheet and the D1 notes on the Parameters and Keys sheets (cells outside a Table).

**To fill in**: `<database>` in each block.

### Hive

```sql
-- severity_by_day
SELECT dt,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
GROUP BY dt
```

```sql
-- job_runs
SELECT r.run_id, r.status, COALESCE(c.alerts, 0) AS alerts
FROM <database>.job_runs r
LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) c
  ON r.run_id = c.run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X37

### Map

**Sources**
- `Owners` (Job No, Team Name, Owner, Day): its typed columns, read as `<database>.Owners`.

**Steps**
- None.

**Finals**
- Table `Owners` (Job No, Team Name, Owner, Day, Is Ana): it has a formula column, no query loads it, and no other Table's formula or query reads it, so it is a final. Its own formula reads its own row, which does not count.

**Parameters and Keys**: empty settings Tables, never a source, step or final. Nothing to convert.

**Typed over a formula**: none. Keys has no row.

**Marks**
- `blank`: Owner is blank on the web rows of the sample, and Is Ana reads Owner, so Owner is read as COALESCE(Owner, '').

**Refusals**: none.

**Left alone**: the Steps sheet and the D1 notes on the Parameters and Keys sheets (cells outside a Table).

**To fill in**: `<database>`, `<job_no>`, `<team_name>` and `<is_ana>` (the headers with spaces, in snake case).

### Hive

```sql
-- Owners
SELECT <job_no>, <team_name>, Owner, Day,
  IF(COALESCE(Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X38

### Map

**Sources**
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs): its typed columns, read as `<database>.job_runs`.
- `jobs` (job_id, job_name, team, region): its typed columns, read as `<database>.jobs` for region, the XLOOKUP's source.

**Steps**
- None.

**Finals**
- Table `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost): it has formula columns, no query loads it, and no other Table's formula or query reads it, so it is a final. It is not a summary, as status is a typed column its COUNTIFS-style formulas don't match on.

**Parameters**: empty, nothing to convert.
**Keys**: row job_runs, run_id. Read here to match the typed value, not converted.

**Typed over a formula**
- `retry_cost` where run_id is 102 (typed as 1). Matched on run_id, the Keys row's column for job_runs.

**Marks**
- `blank`: avg_retry_secs is blank on run 98 and retry_cost reads it, so it is read as COALESCE(avg_retry_secs, 0).
- `region_mins` (SUMIFS over its own Table) is COALESCE'd, as Excel gives 0 where nothing matches. Not a mark, named for the reader.

**Refusals**: none.

**Left alone**: the Steps sheet and the D1 notes on the Parameters and Keys sheets (cells outside a Table).

**To fill in**: `<database>` in the block.

### Hive

```sql
-- job_runs
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, j.region
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, region,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY region), 0) AS region_mins,
  CASE WHEN run_id = 102 THEN 1
    ELSE (COALESCE(avg_retry_secs, 0) + duration_mins) * 2
  END AS retry_cost
FROM base
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X39

### Map

**Sources**
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): its typed columns, read as `<database>.job_runs` by query `ok_runs`.
- `jobs` (job_id, job_name, team, region): its typed columns, read as `<database>.jobs` for job_name, the XLOOKUP's source.

**Steps**
- None. Query `ok_runs` is not named by another query's M, so it is not a step.

**Finals**
- Table `ok_runs` (run_id, job_id, duration_mins, job_name, share, noise): loaded by query `ok_runs`, and no other Table's formula reads it, so it is a final, its rows the query's. Its own formulas read its own rows, which does not count.
- Query `ok_runs` (a query, apart from its Table of the same name): its M reads job_runs with status = 'SUCCESS' and keeps run_id, job_id, duration_mins. The blank status on run 98 drops out in both M and Hive.

**Parameters and Keys**: empty settings Tables, never a source, step or final. Nothing to convert.

**Typed over a formula**: none.

**Marks**: none.

**Refusals**
- `noise`: `=RAND()` is refused, as RAND has no Hive that gives the same values. `NULL AS noise`.

**Left alone**: the Steps sheet and the D1 notes on the Parameters and Keys sheets (cells outside a Table).

**To fill in**: `<database>` in the block.

### Hive

```sql
-- ok_runs
WITH kept AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
),
looked AS (
  SELECT k.run_id, k.job_id, k.duration_mins, j.job_name
  FROM kept k
  LEFT JOIN <database>.jobs j ON k.job_id = j.job_id
)
SELECT run_id, job_id, duration_mins, job_name,
  duration_mins / COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0) AS share,
  NULL AS noise
FROM looked
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X40

### Map

**Sources**
- `Runs` (Run, Job, Mins): its typed columns, read as `<database>.Runs`. It is a step too, see below.
- `jobs` (job_id, job_name, team, region): its typed columns, read as `<database>.jobs` for team, the XLOOKUP's source.
- `run_alerts` (alert_id, run_id, severity, dt): its typed columns, read as `<database>.run_alerts`.

**Steps**
- `Runs` (Run, Job, Mins, Team, Cost): its formula columns are read by the formulas of Teams and run_alerts, so it is a step, a CTE `runs` in each final that reads it.

**Finals**
- Table `Teams` (Team, Total Cost): a summary, as its only typed column, Team, is what its SUMIFS matches on. Its groups `data` and `finance` are typed in; Runs is read.
- Table `run_alerts` (alert_id, run_id, severity, dt, Run Mins): no query loads it, and no other Table's formula reads it, so it is a final.

**Parameters**: `rate` = 2, read in as its value in Cost (`Mins * 2`). Nothing else to convert.
**Keys**: empty, nothing to convert.

**Typed over a formula**: none.

**Marks**: none.

**Refusals**: none.

**Left alone**
- The PivotTable on sheet "Pivot" (from Runs, rows Team, values Sum of Cost): left alone, as PivotTables are.
- The Steps sheet and the D1 notes on the Parameters and Keys sheets (cells outside a Table).

**To fill in**: `<database>`, `<total_cost>` (Total Cost) and `<run_mins>` (Run Mins).

### Hive

```sql
-- Teams
WITH runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT t.team AS Team, COALESCE(c.total, 0) AS <total_cost>
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance') t
LEFT JOIN (SELECT Team AS team, SUM(Cost) AS total FROM runs GROUP BY Team) c
  ON t.team = c.team
```

```sql
-- run_alerts
WITH runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt, x.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN runs x ON a.run_id = x.Run
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X46

### Map

- **Sources**
  - `job_runs`, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read as `<database>.job_runs`. It has no formula and no query loads it.
  - `jobs`, its typed columns: job_id, job_name, team. Read as `<database>.jobs`.
- **Steps**: none.
- **Finals**
  - `jobs` (job_id, job_name, team, shortest, runs, busiest). It has formula columns, but no other Table's formula and no query reads it, so it is a final. Its formulas read job_runs and its own runs column.
- **Typed over a formula**: none (Keys is empty).
- **Marks**: none. The blanks in job_runs (status and avg_retry_secs on row 98) are not read by a formula.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty settings Tables; the Steps sheet, which is a sheet and not a Table. The workbook has no defined names, charts or PivotTables.
- **To fill in**: `<database>`.
- **Note**: shortest and runs are COUNT and MIN over job_runs, joined in by job_id, with COALESCE to 0 where nothing matches. busiest is RANK over runs, so the joined rows sit in a CTE that RANK reads.

### Hive

```sql
WITH jobs_calc AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(s.shortest, 0) AS shortest,
    COALESCE(r.runs, 0) AS runs
  FROM <database>.jobs j
  LEFT JOIN (SELECT job_id, MIN(duration_mins) AS shortest FROM <database>.job_runs GROUP BY job_id) s
    ON j.job_id = s.job_id
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
    ON j.job_id = r.job_id
)
SELECT job_id, job_name, team, shortest, runs,
  RANK() OVER (ORDER BY runs DESC) AS busiest
FROM jobs_calc
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X47

### Map

- **Sources**
  - `region_budgets`, its typed columns: job_id, budget_cents, region. Read as `<database>.region_budgets`.
- **Steps**: none.
- **Finals**
  - `region_budgets` (job_id, budget_cents, region, cheapest_first, region_total, region_avg). Its formulas read only its own Table, and no other Table or query reads it, so it is a final. It is not a summary, since job_id is typed and no formula matches on it.
- **Typed over a formula**: none (Keys is empty).
- **Marks**: none. The Table has no blanks.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty settings Tables; the Steps sheet. The workbook has no defined names, charts or PivotTables.
- **To fill in**: `<database>`.
- **Note**: each formula is an own-Table window, so no join is needed. cheapest_first is RANK ascending, as the third argument is 1. region_total is COALESCE of a SUM OVER region, and region_avg is an AVG OVER region, left NULL.

### Hive

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X48

### Map

- **Sources**
  - `job_runs`, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read as `<database>.job_runs`.
  - `jobs`, its typed columns: job_id, job_name, team, region. Read as `<database>.jobs`.
  - `run_alerts`, its typed columns: alert_id, run_id, severity, dt. Read as `<database>.run_alerts`.
- **Steps**: none. Neither query names another query.
- **Finals**
  - `quiet_runs` (run_id, job_id, status). The Table is loaded by Power Query quiet_runs, and no formula reads it, so it is a final whose rows are the query's: job_runs rows with no run_alerts row (LeftAnti).
  - `slow_regions` (region, avg_mins, fastest). The Table is loaded by Power Query slow_regions, and no formula reads it, so it is a final whose rows are the query's: job_runs joined to jobs, grouped by region, kept where the average is 20 or more.
- **Typed over a formula**: none (Keys is empty).
- **Marks**: none. No formula reads a blank.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty settings Tables. The workbook has no formulas, defined names, charts or PivotTables.
- **To fill in**: `<database>`.

### Hive

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

```sql
SELECT j.region, AVG(r.duration_mins) AS avg_mins, MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X49

### Map

- **Sources**
  - `job_runs`, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read as `<database>.job_runs`.
  - `jobs`, its typed columns: job_id, job_name, team, region. Read as `<database>.jobs`.
  - `run_alerts`, its typed columns: alert_id, run_id, severity, dt. Read as `<database>.run_alerts`.
  - `scheduler_runs`, its typed columns: run_id, job_id, dt. Read as `<database>.scheduler_runs`.
  - `job_owners`, its typed columns: job_id, team, owner, dt. Read as `<database>.job_owners`.
- **Steps**: none. No query names another query.
- **Finals**
  - `alert_status` (alert_id, severity, status). Loaded by Power Query alert_status, which is a right outer join of job_runs to run_alerts (a LEFT JOIN from job_runs). No formula reads it, so it is a final.
  - `run_check` (run_id, status, scheduled_run). Loaded by Power Query run_check, a full outer join of job_runs to scheduler_runs. run_id is the job_runs side, as the query gives it, so run 100 (scheduler only) has a NULL run_id. No formula reads it, so it is a final.
  - `teams` (team). Loaded by Power Query teams, the distinct teams of jobs and job_owners (a UNION). No formula reads it, so it is a final.
- **Typed over a formula**: none (Keys is empty).
- **Marks**: none. The workbook has no formulas, so no blank is read by one.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty settings Tables. The workbook has no formulas, defined names, charts or PivotTables.
- **To fill in**: `<database>`.

### Hive

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
```

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X50

### Map

- **Sources**
  - `job_owners`, its typed columns: job_id, team, owner, dt. Read as `<database>.job_owners`, by the query that loads owners.
  - `jobs`, its typed columns: job_id, job_name, team, region. Read as `<database>.jobs`, by the job_name formula.
- **Steps**: none. Query owners names no other query.
- **Finals**
  - `owners` (job_id, owner, job_name, newest_first). The Table is loaded by Power Query owners, and no other Table's formula reads it, so it is a final whose rows are the query's: the distinct job_id and owner pairs of job_owners. Its own formulas read its own job_id column and the jobs Table, not themselves.
- **Typed over a formula**: none (Keys is empty).
- **Marks**: none. The blank owner on job 4 is not read by a formula.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty settings Tables; the Steps sheet. The workbook has no defined names, charts or PivotTables.
- **To fill in**: `<database>`.
- **Note**: job_name is XLOOKUP into jobs, a LEFT JOIN. newest_first is RANK descending over the distinct owner rows, so those rows sit in a CTE that the RANK reads.

### Hive

```sql
WITH distinct_owners AS (
  SELECT DISTINCT job_id, owner FROM <database>.job_owners
)
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM distinct_owners o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X59

### Map

- **Sources:** job_runs, read as `<database>.job_runs` (its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt). It has no formula, so no query or formula makes it a step or final.
- **Steps:** none.
- **Finals:**
  - jobs (job_id, job_name, long_runs, failed_mins, not_test). A final: no formula reads jobs, and job_name is typed but not a COUNTIFS match column, so it is not a summary.
  - run_alerts (alert_id, run_id, severity, dt, alerts_so_far). A final: nothing else reads it. alerts_so_far is a running count over its own run_id.
- **Parameters and Keys:** both empty, so neither is read. They are never a source, step or final.
- **Typed over a formula:** none. Keys has no row.
- **Marks:**
  - jobs.failed_mins: the "f*" wildcard is `LOWER(status) LIKE 'f%'`, as Excel ignores case.
  - jobs.not_test: "<>TEST" counts a blank status (job_runs run 98) as Excel does: `(status <> 'TEST' OR status IS NULL)`. The blank is in a condition, so it is written as it is, with no COALESCE.
- **Refusals:** none.
- **Left alone:** the D1 notes on the Parameters, Keys and Steps sheets (cells outside a Table).
- **To fill in:** `<database>` in each query. The Table and column names are plain, so they stay as they are.

### Hive

```sql
SELECT j.job_id, j.job_name,
  COALESCE(lr.long_runs, 0) AS long_runs,
  COALESCE(fm.failed_mins, 0) AS failed_mins,
  COALESCE(nt.not_test, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS long_runs
  FROM <database>.job_runs
  WHERE duration_mins >= 20
  GROUP BY job_id
) lr ON j.job_id = lr.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS failed_mins
  FROM <database>.job_runs
  WHERE LOWER(status) LIKE 'f%'
  GROUP BY job_id
) fm ON j.job_id = fm.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS not_test
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) nt ON j.job_id = nt.job_id
```

```sql
SELECT alert_id, run_id, severity, dt,
  COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X60

### Map

- **Sources:** none. region_budgets has formulas, so it is a final, not a source. Its typed columns are read from `<database>.region_budgets`.
- **Steps:** none.
- **Finals:**
  - region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region).
  - region_budgets (Total Row) (job_id, budget_cents). Its own final, with a column only for each Total Row cell that holds a total: job_id (SUBTOTAL 103, a count) and budget_cents (SUBTOTAL 101, an average). The "Total" label and the three empty cells get no column.
- **Parameters and Keys:** both empty, so neither is read. They are never a source, step or final.
- **Typed over a formula:** none. Keys has no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the D1 notes on the Parameters, Keys and Steps sheets (cells outside a Table); the Total Row's "Total" label.
- **To fill in:** `<database>` in each query.

### Hive

```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

```sql
WITH region_budgets AS (
  SELECT job_id, budget_cents, region,
    budget_cents / SUM(budget_cents) OVER () AS share,
    budget_cents > AVG(budget_cents) OVER () AS above_avg,
    RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
  FROM <database>.region_budgets
)
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents
FROM region_budgets
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X61

### Map

- **Sources:** region_costs, read as `<database>.region_costs` (its typed columns job_id, cost_cents, region, dt). It has no formula and no query loads it.
- **Steps:** none.
- **Finals:**
  - by_region, a summary. Its only typed column is region, which its SUMIFS, COUNTIFS and MAXIFS match on. Its final query is a GROUP BY of region_costs, with its typed groups eu and us typed in (region, total_cents, entries, priciest).
  - by_region (Total Row) (total_cents, entries, priciest). Its own final, with a column for each Total Row cell that holds a total: SUBTOTAL 109 is a SUM for total_cents and entries, and SUBTOTAL 104 is a MAX for priciest. The "Total" label gets no column.
- **Parameters and Keys:** both empty, so neither is read. They are never a source, step or final.
- **Typed over a formula:** none. Keys has no row.
- **Marks:**
  - blank: region_costs row 29 has no cost_cents. It sits inside SUMIFS and MAXIFS, which skip a blank as SUM and MAX skip NULL, so the column is written as it is with no COALESCE. The row still counts in entries, as Excel's COUNTIFS counts it.
- **Refusals:** none.
- **Left alone:** the D1 notes on the Parameters, Keys and Steps sheets (cells outside a Table); the Total Row's "Total" label.
- **To fill in:** `<database>` in each query.

### Hive

```sql
SELECT g.region,
  COALESCE(t.total_cents, 0) AS total_cents,
  COALESCE(c.entries, 0) AS entries,
  COALESCE(m.priciest, 0) AS priciest
FROM (SELECT 'eu' AS region UNION ALL SELECT 'us') g
LEFT JOIN (SELECT region, SUM(cost_cents) AS total_cents FROM <database>.region_costs GROUP BY region) t
  ON g.region = t.region
LEFT JOIN (SELECT region, COUNT(*) AS entries FROM <database>.region_costs GROUP BY region) c
  ON g.region = c.region
LEFT JOIN (SELECT region, MAX(cost_cents) AS priciest FROM <database>.region_costs GROUP BY region) m
  ON g.region = m.region
```

```sql
WITH by_region AS (
  SELECT g.region,
    COALESCE(t.total_cents, 0) AS total_cents,
    COALESCE(c.entries, 0) AS entries,
    COALESCE(m.priciest, 0) AS priciest
  FROM (SELECT 'eu' AS region UNION ALL SELECT 'us') g
  LEFT JOIN (SELECT region, SUM(cost_cents) AS total_cents FROM <database>.region_costs GROUP BY region) t
    ON g.region = t.region
  LEFT JOIN (SELECT region, COUNT(*) AS entries FROM <database>.region_costs GROUP BY region) c
    ON g.region = c.region
  LEFT JOIN (SELECT region, MAX(cost_cents) AS priciest FROM <database>.region_costs GROUP BY region) m
    ON g.region = m.region
)
SELECT SUM(total_cents) AS total_cents, SUM(entries) AS entries, MAX(priciest) AS priciest
FROM by_region
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X62

### Map

- **Sources:** none. team_notes has formulas, so it is a final.
- **Steps:** none.
- **Finals:** team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short). Nothing else reads it, and its formulas read only its own row.
- **Parameters and Keys:** both empty, so neither is read. They are never a source, step or final.
- **Typed over a formula:** none. Keys has no row.
- **Marks:** none. written_on is read as a date, as the sample shows ISO dates rather than 8-digit text.
- **Refusals:** none.
- **Left alone:** the D1 notes on the Parameters, Keys and Steps sheets (cells outside a Table).
- **To fill in:** `<database>` in the query.

### Hive

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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X63

### Map

- **Sources:** scheduler_runs, read as `<database>.scheduler_runs` (its typed columns run_id, job_id, dt). It has no formula and no query loads it. It is read in job_runs' scheduled_job, as a LEFT JOIN on run_id.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded). Nothing else reads it, and its own formulas don't count. It is not a summary, as it has no SUMIFS or COUNTIFS.
- **Parameters and Keys:** both empty, so neither is read. They are never a source, step or final.
- **Typed over a formula:** none. Keys has no row.
- **Marks:**
  - blank: status is blank in run 98 and is read by SEARCH, so it is written as `COALESCE(status, '')`. That keeps succeeded FALSE, as Excel's SEARCH gives.
  - SEARCH ignores case, so the Hive lowers both sides: `INSTR(LOWER(...), 'cess') > 0`.
  - blank avg_retry_secs in run 98: ISBLANK is written as `IS NULL`, with the column as it is and no COALESCE.
  - scheduled_job: XLOOKUP's not-found value, -1, is written as COALESCE. Run 99 has no scheduler_runs row, so it takes -1.
- **Refusals:** none.
- **Left alone:** the D1 notes on the Parameters, Keys and Steps sheets (cells outside a Table).
- **To fill in:** `<database>` in each query.

### Hive

```sql
SELECT j.run_id, j.job_id, j.status, j.duration_mins, j.avg_retry_secs,
  j.avg_retry_secs IS NULL AS no_retry,
  FLOOR(j.duration_mins / 4) AS quarters,
  LEAST(j.duration_mins, 25) AS capped,
  VAR_SAMP(j.duration_mins) OVER () AS variance,
  SUM(j.duration_mins * j.job_id) OVER () AS weighted,
  COALESCE(s.job_id, -1) AS scheduled_job,
  CONCAT('run ', j.run_id) AS label,
  INSTR(LOWER(COALESCE(j.status, '')), 'cess') > 0 AS succeeded
FROM <database>.job_runs j
LEFT JOIN <database>.scheduler_runs s ON j.run_id = s.run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X64

### Map
- **Sources**: `jobs` (job_id, job_name, team, region), its typed columns, read by costed_jobs. `region_costs` (job_id, cost_cents, region, dt), its typed columns, read by picked_costs, costed_jobs and costs_filled.
- **Steps**: none.
- **Finals**:
  - `picked_costs` (job_id, cost_cents, region, size). Query picked_costs loads it and no formula reads it, so it is a final with the query's rows: region_costs rows with a cost for jobs 1 and 3, region in capitals, size "big" from 200 up and "small" below.
  - `costed_jobs` (job_id, job_name, team, region). Query costed_jobs loads it: jobs rows that have a region_costs row, with no job name starting "n".
  - `costs_filled` (job_id, cost_cents, dt, day). Query costs_filled loads it: region_costs with a blank cost_cents read as 0, and day as the last two characters of dt.
- **Values typed over a formula**: none. The workbook has no formula column, and Keys holds no row.
- **Marks**: blank. region_costs has a blank cost_cents on row 29 (job 2, 20260924). costs_filled reads it as COALESCE(cost_cents, 0), as its Table.ReplaceValue does.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty. The Steps sheet, which holds instructions and is not a Table.
- **`<...>` to fill in**: `<database>`, in each block.

### Hive

```sql
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

```sql
SELECT t.job_id, t.job_name, t.team, t.region
FROM <database>.jobs t
LEFT SEMI JOIN <database>.region_costs u ON u.job_id = t.job_id
WHERE NOT t.job_name LIKE 'n%'
```

```sql
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt, SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X65

### Map
- **Sources**: `jobs` (job_id, job_name, team, region), read by team_regions. `region_budgets` (job_id, budget_cents, region), read by budget_places. `job_owners` (job_id, team, owner, dt), read by jobs_per_team. `scheduler_runs` (run_id, job_id, dt), read by ran_as_scheduled. `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read by ran_as_scheduled and run_measures. Each is its typed columns.
- **Steps**: none.
- **Finals**:
  - `team_regions` (team, region). Query team_regions loads it: each distinct team crossed with each distinct region.
  - `budget_places` (job_id, budget_cents, region, place). Query budget_places loads it: region_budgets, ranked by budget_cents descending.
  - `jobs_per_team` (team, jobs). Query jobs_per_team loads it: distinct job_ids per team in job_owners.
  - `ran_as_scheduled` (run_id, dt). Query ran_as_scheduled loads it: the run_id and dt pairs found in both scheduler_runs and job_runs, once each.
  - `run_measures` (run_id, job_id, measure, amount). Query run_measures loads it: duration_mins and avg_retry_secs unpivoted into measure and amount.
- **Values typed over a formula**: none. The workbook has no formula column, and Keys holds no row.
- **Marks**:
  - Order dropped: team_regions sorts by team with no FirstN or index after it, so the Hive has no ORDER BY, and the order is dropped.
  - run_measures: the blank avg_retry_secs on run 98 is left out, as M's Unpivot drops a null.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty. The Steps sheet, which holds instructions and is not a Table.
- **`<...>` to fill in**: `<database>`, in each block.

### Hive

```sql
SELECT t.team, r.region
FROM (SELECT DISTINCT team FROM <database>.jobs) t
CROSS JOIN (SELECT DISTINCT region FROM <database>.jobs) r
```

```sql
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

```sql
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

```sql
SELECT run_id, dt FROM <database>.scheduler_runs
INTERSECT
SELECT run_id, dt FROM <database>.job_runs
```

```sql
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X66

### Map
- **Sources**: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), its typed columns, read by query ok_runs.
- **Steps**: none.
- **Finals**:
  - `ok_runs` (run_id, job_id, duration_mins, dt, running, share). Query ok_runs loads it and no other Table's formula reads it, so it is a final with the query's rows: job_runs rows whose status starts with SUCC. running is the running total of duration_mins per job_id by dt, ties included. share is each row's duration_mins over the sum of the whole column.
  - `ok_runs (Total Row)` (duration_mins). The Total Row's one total cell is SUBTOTAL(109, duration_mins), a SUM. Its label and empty cells get no column.
- **Values typed over a formula**: none. Keys holds no row.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty. The Steps sheet, which holds instructions and is not a Table.
- **`<...>` to fill in**: `<database>`, in each block.

### Hive

```sql
SELECT run_id, job_id, duration_mins, dt,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins, dt,
    COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
    duration_mins / SUM(duration_mins) OVER () AS share
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT SUM(duration_mins) AS duration_mins
FROM ok_runs
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X69

### Map
- **Sources**: `region_costs` (job_id, cost_cents, region, dt), its typed columns, read by the region_costs step. `jobs` (job_id, job_name, team, region), read by the region_costs step. `region_budgets` (job_id, budget_cents, region), read by the region_costs step.
- **Steps**:
  - `region_costs` (job_id, cost_cents, region, dt, job_name, budget, over_budget, running_cost). It is a step, not a final, because job_totals' formulas read it. Its formulas: job_name is the jobs lookup, budget is the region_budgets lookup, over_budget is cost_cents above budget, and running_cost is the running total of cost_cents per job_id by dt, ties included.
- **Finals**:
  - `job_totals` (job_id, total_cents, over_count). A summary: its only typed column, job_id, is what its SUMIFS and COUNTIFS match on. Its typed job_ids 1, 2 and 3 are typed in as its groups, and region_costs is read as a GROUP BY.
  - `job_totals (Total Row)` (total_cents, over_count). Both Total Row cells hold a total: SUBTOTAL(109) over total_cents and over_count, each a SUM.
  - `late_costs` (job_id, dt, running_cost). Query late_costs loads it and reads the region_costs step, keeping rows with running_cost above 1500.
- **Values typed over a formula**: none. Keys holds no row.
- **Marks**:
  - blank: region_costs has a blank cost_cents on row 29 (job 2, 20260924). over_budget compares it, so it reads COALESCE(cost_cents, 0), as Excel reads the blank as 0.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty. The Steps sheet, which holds instructions and is not a Table.
- **`<...>` to fill in**: `<database>`, in each block.

### Hive

```sql
WITH region_costs AS (
  SELECT rc.job_id, rc.cost_cents, rc.region, rc.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(rc.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(rc.cost_cents) OVER (PARTITION BY rc.job_id ORDER BY rc.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs rc
  LEFT JOIN <database>.jobs j ON rc.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON rc.job_id = b.job_id
),
job_totals AS (
  SELECT j.job_id, COALESCE(t.total_cents, 0) AS total_cents, COALESCE(o.over_count, 0) AS over_count
  FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
  LEFT JOIN (SELECT job_id, SUM(cost_cents) AS total_cents FROM region_costs GROUP BY job_id) t
    ON j.job_id = t.job_id
  LEFT JOIN (SELECT job_id, COUNT(*) AS over_count FROM region_costs WHERE over_budget = TRUE GROUP BY job_id) o
    ON j.job_id = o.job_id
)
SELECT job_id, total_cents, over_count
FROM job_totals
```

```sql
WITH region_costs AS (
  SELECT rc.job_id, rc.cost_cents, rc.region, rc.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(rc.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(rc.cost_cents) OVER (PARTITION BY rc.job_id ORDER BY rc.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs rc
  LEFT JOIN <database>.jobs j ON rc.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON rc.job_id = b.job_id
),
job_totals AS (
  SELECT j.job_id, COALESCE(t.total_cents, 0) AS total_cents, COALESCE(o.over_count, 0) AS over_count
  FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
  LEFT JOIN (SELECT job_id, SUM(cost_cents) AS total_cents FROM region_costs GROUP BY job_id) t
    ON j.job_id = t.job_id
  LEFT JOIN (SELECT job_id, COUNT(*) AS over_count FROM region_costs WHERE over_budget = TRUE GROUP BY job_id) o
    ON j.job_id = o.job_id
)
SELECT SUM(total_cents) AS total_cents, SUM(over_count) AS over_count
FROM job_totals
```

```sql
WITH region_costs AS (
  SELECT rc.job_id, rc.cost_cents, rc.region, rc.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(rc.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(rc.cost_cents) OVER (PARTITION BY rc.job_id ORDER BY rc.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs rc
  LEFT JOIN <database>.jobs j ON rc.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON rc.job_id = b.job_id
)
SELECT job_id, dt, running_cost
FROM region_costs
WHERE running_cost > 1500
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X70

### Map
- **Sources**: `jobs` (job_id, job_name, team, region), read by the staffed step. `job_owners` (job_id, team, owner, dt), read by the staffed step. `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read by the owner_load step. Each is its typed columns.
- **Steps**:
  - `staffed` (job_id, job_name, owner): query staffed, connection only, read by query owner_load's M. Each job with each distinct owner, owner blanks left out.
  - query `owner_load` (owner, total_mins, runs): read by query busiest_owner's M, so it is a step. It is not the Table of the same name, which is a final.
- **Finals**:
  - `owner_load` (owner, total_mins, runs, avg_mins). The Table is loaded by query owner_load, and no other Table's formula reads it, so it is a final with the query's rows. avg_mins is total_mins over runs.
  - `owner_load (Total Row)` (runs). The one total cell is SUBTOTAL(109, runs), a SUM. Its label and empty cells get no column.
  - `busiest_owner` (owner, total_mins, runs). Query busiest_owner loads it: the owner with the most runs, one row.
- **Values typed over a formula**: none. Keys holds no row.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty. The Steps sheet, which holds instructions and is not a Table.
- **`<...>` to fill in**: `<database>`, in each block.

### Hive

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
grouped AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs, total_mins / runs AS avg_mins
FROM grouped
```

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
grouped AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
),
owner_load AS (
  SELECT owner, total_mins, runs, total_mins / runs AS avg_mins
  FROM grouped
)
SELECT SUM(runs) AS runs
FROM owner_load
```

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

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X73

### Map

- **Sources:** `region_budgets` (job_id, budget_cents, region), read as `<database>.region_budgets`; `jobs` (job_id, job_name, team, region), read as `<database>.jobs`.
- **Steps:** query `eu_budgets` (job_id, budget_cents, region, job_name). Query `eu_count`'s M names it, so it is a CTE in the `eu_count` final.
- **Finals:** Table `eu_budgets` (job_id, budget_cents, region, job_name, dollars), its rows the query `eu_budgets`'s, with dollars by its formula; Table `eu_count` (region, jobs, total_cents), a GROUP BY of the step.
- **Typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty, so they have no role; no formula uses a fixed value and no value is typed over a formula, so no Keys row is needed. The Steps sheet is the Formula workbook's own instructions, not read.
- **To fill in:** `<database>` in each FROM.

### Hive

```sql
SELECT b.job_id, b.budget_cents, b.region, j.job_name,
  b.budget_cents / 100 AS dollars
FROM <database>.region_budgets b
JOIN <database>.jobs j ON b.job_id = j.job_id
WHERE b.region = 'eu'
```

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

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X74

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
- **Steps:** Table `run_alerts` (alert_id, run_id, severity, dt, status, job_id, alerts_so_far), a step since query `late_alerts` reads it and `by_status`'s formula reads it. Its typed columns are read from `<database>.run_alerts`; its formulas are its status and job_id lookups into job_runs and its running count of run_id. It is a CTE in each final that reads it.
- **Finals:** Table `late_alerts` (alert_id, run_id, alerts_so_far), its rows the query `late_alerts`'s (alerts_so_far > 5 over the step); Table `by_status` (status, alerts), a summary, since its only typed column, status, is what its COUNTIFS matches: its typed groups FAILED and SUCCESS are typed in, and alerts is a GROUP BY count over the step.
- **Typed over a formula:** none.
- **Marks:** `blank`: job_runs run 98 has no status, and the step's status reads job_runs status through the lookup, so it is `COALESCE(j.status, '')`. The running COUNTIFS on run_id is written as a RANGE window, ties included, as Excel counts them.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty, so no role. job_runs avg_retry_secs has a blank in run 98, but no formula reads it, so it is left as it is.
- **To fill in:** `<database>` in each FROM.

### Hive

```sql
WITH run_alerts AS (
  SELECT r.alert_id, r.run_id, r.severity, r.dt,
    COALESCE(j.status, '') AS status, j.job_id,
    COUNT(*) OVER (ORDER BY r.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts r
  LEFT JOIN <database>.job_runs j ON r.run_id = j.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM run_alerts
WHERE alerts_so_far > 5
```

```sql
WITH run_alerts AS (
  SELECT r.alert_id, r.run_id, r.severity, r.dt,
    COALESCE(j.status, '') AS status, j.job_id,
    COUNT(*) OVER (ORDER BY r.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts r
  LEFT JOIN <database>.job_runs j ON r.run_id = j.run_id
)
SELECT s.status, COALESCE(c.alerts, 0) AS alerts
FROM (SELECT 'FAILED' AS status UNION ALL SELECT 'SUCCESS') s
LEFT JOIN (SELECT status, COUNT(*) AS alerts FROM run_alerts GROUP BY status) c
  ON s.status = c.status
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X77

### Map

- **Sources:** `run_alerts` (alert_id, run_id, severity, dt), read as `<database>.run_alerts`.
- **Steps:** query `high_alerts` (alert_id, run_id, dt), named by query `high_per_day`'s M, so a CTE in the `high_per_day` final. Its rows are the Table `high_alerts`'s.
- **Finals:** Table `high_alerts` (alert_id, run_id, dt, late_run), its rows the query's, with late_run by its formula; Table `high_per_day` (dt, alerts), a GROUP BY of the step.
- **Typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty, so no role.
- **To fill in:** `<database>` in each FROM.

### Hive

```sql
SELECT alert_id, run_id, dt, run_id > 100 AS late_run
FROM <database>.run_alerts
WHERE severity = 'high'
```

```sql
WITH high_alerts AS (
  SELECT alert_id, run_id, dt
  FROM <database>.run_alerts
  WHERE severity = 'high'
)
SELECT dt, COUNT(*) AS alerts
FROM high_alerts
GROUP BY dt
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X78

### Map

- **Sources:** `region_costs` (job_id, cost_cents, region, dt), read as `<database>.region_costs`.
- **Steps:** query `known_costs` (job_id, cost_cents, dt), named by query `cost_per_job`'s M, so a CTE in the `cost_per_job` final. Its rows are the Table `known_costs`'s.
- **Finals:** Table `known_costs` (job_id, cost_cents, dt, dollars), its rows the query's, with dollars by its formula; `known_costs (Total Row)` (cost_cents), a column only for the one Total Row cell that holds a total (the "Total" label and the empty dt and dollars cells get no column), reading the Table's final as a CTE; Table `cost_per_job` (job_id, total_cents), a GROUP BY of the step.
- **Typed over a formula:** none.
- **Marks:** `blank`: region_costs row 29 (job 2, dt 20260924) has no cost_cents. The step's `cost_cents <> null` drops it, which `cost_cents IS NOT NULL` does in Hive too, so no COALESCE is needed. Without it, job 2's total is 1690, as the sample shows.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty, so no role.
- **To fill in:** `<database>` in each FROM.

### Hive

```sql
SELECT job_id, cost_cents, dt, cost_cents / 100 AS dollars
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL
```

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt, cost_cents / 100 AS dollars
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT SUM(cost_cents) AS cost_cents
FROM known_costs
```

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT job_id, SUM(cost_cents) AS total_cents
FROM known_costs
GROUP BY job_id
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X80

### Map

- **Sources:** `job_runs` (run_id, job_id, duration_mins), its typed columns, read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** Table `job_runs` (run_id, job_id, duration_mins, look), its rows the Source's, with look by its formula; no query loads it and nothing else reads it.
- **Typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty, so no role; no Keys row is needed.
- **To fill in:** `<database>` in the FROM.

### Hive

```sql
SELECT run_id, job_id, duration_mins,
  IF((duration_mins > 20 AND job_id <> 3 OR NOT job_id = 2), 'look', 'fine') AS look
FROM <database>.job_runs
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X83

### Map

- **Sources:** job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** by_day, with the columns dt, kept_runs, short_mins and success_or_failed. It is a summary: its only typed column, dt, is the one its COUNTIFS and SUMIFS match on, so its typed dt groups ('2026-09-23' and '2026-09-24') are typed in and job_runs is read. No query loads it and no other Table's formula reads it, so it is a final.
- **Left out:** Parameters and Keys, both empty. They are never a source, step or final. No formula reads a Parameters value.
- **Values typed over a formula:** none. Keys has no row, as none is needed.
- **Marks:** none.
- **Refusals:** none.
- **Blank, written as it is:** job_runs row 98 (run_id 98) has a blank status. Its status is read only inside -IFS forms, which skip a blank, so it gets no COALESCE.
- **Left alone:** the Steps sheet, and the notes in D1 of the Parameters and Keys sheets. These are cells outside a Table.
- **To fill in:** `<database>`, in the three reads of job_runs in the by_day block.

### Hive

```sql
SELECT g.dt,
  COALESCE(k.kept_runs, 0) AS kept_runs,
  COALESCE(s.short_mins, 0) AS short_mins,
  COALESCE(f.success_or_failed, 0) AS success_or_failed
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') g
LEFT JOIN (
  SELECT dt, COUNT(*) AS kept_runs
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL) AND status IS NOT NULL
  GROUP BY dt
) k ON g.dt = k.dt
LEFT JOIN (
  SELECT dt, SUM(duration_mins) AS short_mins
  FROM <database>.job_runs
  WHERE duration_mins < 20
  GROUP BY dt
) s ON g.dt = s.dt
LEFT JOIN (
  SELECT dt, COUNT(*) AS success_or_failed
  FROM <database>.job_runs
  WHERE status IN ('SUCCESS', 'FAILED')
  GROUP BY dt
) f ON g.dt = f.dt
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X84

### Map

- **Sources:** job_runs, its typed columns run_id, job_id, status and duration_mins, read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs, with the columns run_id, job_id, status, duration_mins, flag, job2_short and failed_or_test_mins. It has formula columns and no query loads it. Its formulas read only its own rows and columns, and no other Table's formula reads it, so it is a final. It is not a summary: none of its formulas is a SUMIFS or COUNTIFS.
- **Left out:** Parameters and Keys, both empty. They are never a source, step or final. No formula reads a Parameters value.
- **Values typed over a formula:** none. Every flag, job2_short and failed_or_test_mins cell holds its formula, and Keys has no row, as none is needed.
- **Marks:**
  - blank: job_runs row 98 (run_id 98) has a blank status. failed_or_test_mins reads status in a SUMPRODUCT, which is not an -IF(S) form, so status is written as COALESCE(status, '').
  - flag and job2_short read only job_id and duration_mins, which have no blanks, so they are written as they are.
- **Refusals:** none.
- **Whole-table forms, no change in values:** job2_short and failed_or_test_mins read their own Table, so each uses OVER () and shows the same total on every row, as Excel's SUMPRODUCT does.
- **Left alone:** the Steps sheet, and the notes in D1 of the Parameters and Keys sheets. These are cells outside a Table.
- **To fill in:** `<database>`, in the FROM of the job_runs block.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins,
  IF(((job_id = 2 AND duration_mins < 20) OR (job_id = 3 AND NOT duration_mins >= 30)), 'review', '') AS flag,
  COUNT(CASE WHEN job_id = 2 AND duration_mins < 20 THEN 1 END) OVER () AS job2_short,
  SUM(CASE WHEN COALESCE(status, '') = 'FAILED' OR COALESCE(status, '') = 'TEST' THEN duration_mins ELSE 0 END) OVER () AS failed_or_test_mins
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

