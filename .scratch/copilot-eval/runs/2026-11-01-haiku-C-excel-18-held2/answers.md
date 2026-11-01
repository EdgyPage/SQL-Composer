date: 2026-11-01
arm: C
model: haiku
files: 18-held2

## X21

### Map

- **Sources:** none.
- **Steps:** none.
- **Finals:** region_budgets (job_id, budget_cents, region, budget_dollars, with_margin). Its typed columns are read from `<database>.region_budgets`.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters (empty; no formula uses a fixed value). Keys (empty; no value is typed over a formula, so no row is needed). The Steps sheet is the guide, not a Table or query.
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

- **Sources:** none.
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, team, is_finance, ratio). Its typed columns are read from `<database>.jobs`.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters (empty; no formula uses a fixed value). Keys (empty; no value is typed over a formula, so no row is needed). The Steps sheet is the guide, not a Table or query.
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

- **Sources:** none.
- **Steps:** none.
- **Finals:** job_runs (run_id, status, avg_retry_secs, label, risky). Its typed columns are read from `<database>.job_runs`.
- **Values typed over a formula:** none.
- **Marks:** blank. Row run_id 98 has a blank status and a blank avg_retry_secs, and the label and risky formulas read both. They are written as COALESCE(status, '') and COALESCE(avg_retry_secs, 0), in those formulas only.
- **Refusals:** none.
- **Left alone:** Parameters (empty; no formula uses a fixed value). Keys (empty; no value is typed over a formula, so no row is needed). The Steps sheet is the guide, not a Table or query.
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

- **Sources:** none.
- **Steps:** none.
- **Finals:** team_notes (team, note, written_on, first_word, shout, month, tens_of_chars). Its typed columns are read from `<database>.team_notes`.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters (empty; no formula uses a fixed value). Keys (empty; no value is typed over a formula, so no row is needed). The Steps sheet is the guide, not a Table or query.
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

- **Sources:** none.
- **Steps:** none.
- **Finals:** Costs (Job, `<cost_cents>` for Cost (cents), Region, `<day_key>` for Day Key, Day). Its typed columns are read from `<database>.Costs`. Budgets (Job, Budget, Region, Dollars). Its typed columns are read from `<database>.Budgets`.
- **Values typed over a formula:** none.
- **Marks:** date held as text. Costs' Day Key holds yyyymmdd values such as 20260911, so Day is written as CONCAT(SUBSTR(day_key, 1, 4), '-', SUBSTR(day_key, 5, 2), '-', SUBSTR(day_key, 7, 2)), which gives text yyyy-mm-dd, not a date.
- **Refusals:** none.
- **Left alone:** Parameters (empty; no formula uses a fixed value). Keys (empty; no value is typed over a formula, so no row is needed). The Steps sheet is the guide, not a Table or query.
- **To fill in:** `<database>`, `<cost_cents>` (header Cost (cents)), `<day_key>` (header Day Key).

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

**Sources**
- job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed only, no query loads it; read as `<database>.job_runs`.

**Steps**
- None.

**Finals**
- run_alerts (alert_id, run_id, severity, job_id, status, avg_mins): it has formula columns, and no other Table's formula or query reads it, so it is a final. Its typed columns (alert_id, run_id, severity) are read from `<database>.run_alerts`. job_id is XLOOKUP on job_runs by run_id; status is the exact VLOOKUP on job_runs by run_id, column 3; avg_mins is AVERAGEIFS of duration_mins over job_runs by the row's job_id.

**Settings, not a source, step or final**
- Parameters and Keys: both empty. No formula reads Parameters, and no value is typed over a formula, so Keys needs no row.

**Values typed over a formula**
- None.

**Marks**
- blank: status. The sample has a blank status on job_runs run 98, and the VLOOKUP reads that column, so it is written COALESCE(j.status, '').

**Refusals**
- None.

**Left alone**
- The Steps sheet, and the notes in D1 of Parameters and Keys (cells outside a Table).

**To fill in**
- `<database>`, once in each query.

### Hive

```sql
SELECT
  r.alert_id,
  r.run_id,
  r.severity,
  j.job_id AS job_id,
  COALESCE(j.status, '') AS status,
  a.avg_mins AS avg_mins
FROM <database>.run_alerts r
LEFT JOIN <database>.job_runs j ON r.run_id = j.run_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) a ON j.job_id = a.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X27

### Map

**Sources**
- jobs (job_id, job_name, team, region): typed only, no query loads it; read as `<database>.jobs`. by_team's formulas read it.

**Steps**
- None.

**Finals**
- by_team (team, jobs_in_team, last_job_id, last_job_name), a summary: its only typed column, team, is the one its COUNTIFS match on. Its final is a GROUP BY of jobs, with its typed groups (data, finance, web) typed in.
- jobs_in_team is COUNTIFS, COUNT(*), with COALESCE. last_job_id is MAXIFS, MAX, with COALESCE. last_job_name is INDEX and MATCH with 0, an exact match on last_job_id, so it joins jobs on job_id.

**Settings, not a source, step or final**
- Parameters and Keys: both empty. No value is typed over a formula, so Keys needs no row.

**Values typed over a formula**
- None.

**Marks**
- None.

**Refusals**
- None.

**Left alone**
- The Steps sheet, and the notes in D1 of Parameters and Keys (cells outside a Table).

**To fill in**
- `<database>`, once in each query.

### Hive

```sql
SELECT g.team,
  COALESCE(c.jobs_in_team, 0) AS jobs_in_team,
  COALESCE(m.last_job_id, 0) AS last_job_id,
  n.job_name AS last_job_name
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') g
LEFT JOIN (
  SELECT team, COUNT(*) AS jobs_in_team
  FROM <database>.jobs
  GROUP BY team
) c ON g.team = c.team
LEFT JOIN (
  SELECT team, MAX(job_id) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
) m ON g.team = m.team
LEFT JOIN <database>.jobs n ON m.last_job_id = n.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X28

### Map

**Sources**
- job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed only, no query loads it; read as `<database>.job_runs`. jobs' ok_mins reads it.

**Steps**
- None.

**Finals**
- jobs (job_id, job_name, ok_mins): ok_mins is a formula no other formula or query reads. Its typed columns are not only the ones its SUMIFS match on (job_name is not), so it is a final, not a summary.
- ok_mins is SUMIFS of duration_mins over job_runs where status is SUCCESS and job_id is the row's job_id: a LEFT JOIN to a GROUP BY of job_runs, with COALESCE to 0.

**Settings, not a source, step or final**
- Parameters: empty.
- Keys: a row for jobs, with key_columns job_id.

**Values typed over a formula**
- jobs.ok_mins, the row where job_id is 3 (report_build), typed as 99. Keys names job_id for jobs, so it is a CASE on job_id.

**Marks**
- None. The blank status on job_runs run 98 sits inside SUMIFS's status condition, so the column is written as it is.

**Refusals**
- None.

**Left alone**
- The Steps sheet, and the notes in D1 of Parameters and Keys (cells outside a Table).

**To fill in**
- `<database>`, once in each query.

### Hive

```sql
SELECT j.job_id, j.job_name,
  CASE WHEN j.job_id = 3 THEN 99 ELSE COALESCE(s.ok_mins, 0) END AS ok_mins
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS ok_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
  GROUP BY job_id
) s ON j.job_id = s.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X29

### Map

**Sources**
- None. region_budgets has formula columns, and no other Table's formula or query reads it, so it is a final, not a source.

**Steps**
- None.

**Finals**
- region_budgets (job_id, budget_cents, region, in_dollars, pointer): read from `<database>.region_budgets` for its typed columns. in_dollars is budget_cents divided by the Parameters value cents_per_dollar, typed in as 100.

**Settings, not a source, step or final**
- Parameters: cents_per_dollar is 100. Its value is typed into in_dollars where the formula reads it by name.
- Keys: empty. No Keys row names region_budgets, so there is no Keys row.

**Values typed over a formula**
- region_budgets.in_dollars, the row with job_id 3, budget_cents 350, region us, typed as 5. No Keys row names region_budgets, so the CASE matches every typed column of the row (job_id, budget_cents, region), and there is no Keys row.

**Marks**
- None.

**Refusals**
- pointer: INDIRECT (its formula also reads ROW()), which reads a cell by its address. Written as `NULL AS pointer`.

**Left alone**
- The Steps sheet, and the notes in D1 of Parameters and Keys (cells outside a Table).

**To fill in**
- `<database>`, once in each query.

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

**Sources**
- None.

**Steps**
- None.

**Finals**
- scheduler_runs (run_id, job_id, dt, day, prev_run, jitter): it has formula columns, and no other Table's formula or query reads it, so it is a final. Its typed columns (run_id, job_id, dt) are read from `<database>.scheduler_runs`. day is RIGHT(dt, 2), written as SUBSTR(dt, -2).

**Settings, not a source, step or final**
- Parameters and Keys: both empty.

**Values typed over a formula**
- None.

**Marks**
- None.

**Refusals**
- prev_run: OFFSET, which reads a row by its position in the sheet, written as `NULL AS prev_run`.
- jitter: RANDBETWEEN, which is random, written as `NULL AS jitter`.

**Left alone**
- The bar chart on the Summary sheet.
- The PivotTable on the Pivot sheet, from scheduler_runs.
- The Steps sheet, and the notes in D1 of Parameters and Keys (cells outside a Table).

**To fill in**
- `<database>`, once in each query.

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

**Map**

- Sources: none.
- Steps: none.
- Finals: `jobs` (job_id, team, bump, tag, scaled, boosted). Its typed columns job_id and team are read from `<database>.jobs`. bump, tag and scaled are refused. boosted is converted, with a mark.
- Value typed over a formula: none. Keys gets no row, as no value is typed over a formula.
- Marks: boosted reads the defined name `boost`, which is Summary!$B$2, a cell outside a Table, holding 10. It is written as the value 10. Move it into Parameters: a row with name `boost` and value 10, then read it with XLOOKUP("boost", Parameters[name], Parameters[value]).
- Refusals:
  - bump: `=jobs[[#This Row],[bump]]*2` reads its own column (circular), so `NULL AS bump`.
  - tag: TAG is a defined name holding a LAMBDA, so `NULL AS tag`.
  - scaled: reads Summary!$D$4 (D4 on Summary), a cell outside a Table that is not a defined name, so `NULL AS scaled`.
- Left alone: the Summary sheet's cells outside a Table (B2 is read through boost, D4 is the refused address), the Parameters and Keys Tables (empty settings, never a source, step or final), the D1 notes on Parameters and Keys, and the Steps sheet.
- `<...>` to fill in: `<database>` in the query.

**Hive**

### jobs

```sql
SELECT job_id, team,
  NULL AS bump,
  NULL AS tag,
  NULL AS scaled,
  job_id * 10 AS boosted
FROM <database>.jobs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X32

**Map**

- Sources: `jobs` (job_id, job_name, team, region), read as `<database>.jobs` inside job_runs' step.
- Steps: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name). Its job_name is the formula column, and by_name's COUNTIFS reads it, so it is a step, a CTE in by_name's block.
- Finals: `by_name` (job_name, runs), a summary. Its only typed column, job_name, is the one COUNTIFS matches on, so its final query is a GROUP BY of job_runs, with its typed job_names (invoice_sync, nightly_load, report_build) typed in.
- Value typed over a formula: none. Keys gets no row.
- Marks: job_name: VLOOKUP with TRUE is approximate, written as the exact match on job_id.
- Refusals: none.
- Left alone: the Parameters and Keys Tables (empty settings), their D1 notes, and the Steps sheet.
- `<...>` to fill in: `<database>` in the query.

**Hive**

### by_name

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT g.job_name, COALESCE(c.runs, 0) AS runs
FROM (SELECT 'invoice_sync' AS job_name UNION ALL SELECT 'nightly_load' UNION ALL SELECT 'report_build') g
LEFT JOIN (SELECT job_name, COUNT(*) AS runs FROM job_runs GROUP BY job_name) c
  ON g.job_name = c.job_name
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X33

**Map**

- Sources: `<database>.job_runs`, the table that the Power Query's Sql.Database("dwh01", "ops") reads (schema ops, item job_runs). It is outside the workbook, so it is named for the user to check.
- Steps: none.
- Finals: `slow_runs` (run_id, duration_mins, over_by). The query loads the Table, and no formula reads it, so the Table is a final, its rows the query's, not the four sample rows.
- Value typed over a formula: none. Keys gets no row.
- Marks:
  - The query reads Sql.Database dwh01, ops, table job_runs. It is read as `<database>.job_runs`; check that it is that table.
  - M's `<>` keeps a null, as Hive's doesn't, so `status <> 'TEST'` is written `(status <> 'TEST' OR status IS NULL)`.
- Refusals: none.
- Left alone: the Parameters and Keys Tables (empty settings), their D1 notes, and the Steps sheet.
- `<...>` to fill in: `<database>` in the query.

**Hive**

### slow_runs

```sql
SELECT run_id, duration_mins, duration_mins - 20 AS over_by
FROM <database>.job_runs
WHERE duration_mins >= 20 AND (status <> 'TEST' OR status IS NULL)
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X34

**Map**

- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`; `jobs` (job_id, job_name, team, region), read as `<database>.jobs`.
- Steps: `runs_with_team` (run_id, job_id, status, duration_mins, avg_retry_secs, dt, team). It is connection only, but team_totals' M names it, so it is a step, a CTE in team_totals' final.
- Finals: `team_totals` (team, total_mins, longest). The query loads the Table and no formula reads it, so the Table is a final, its rows the query's: SUM and MAX of duration_mins per team.
- Value typed over a formula: none. Keys gets no row.
- Marks: none.
- Refusals: none.
- Left alone: the Parameters and Keys Tables (empty settings), their D1 notes, and the Steps sheet.
- `<...>` to fill in: `<database>` in the query.

**Hive**

### team_totals

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

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X35

**Map**

- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`; `scheduler_runs` (run_id, job_id, dt), read as `<database>.scheduler_runs`.
- Steps: none.
- Finals: `recent` (run_id, dt). The query loads the Table and no formula reads it, so the Table is a final, its rows the query's: the run_id and dt of both Tables stacked, sorted by run_id descending, the first 4.
- Value typed over a formula: none. Keys gets no row.
- Marks: none.
- Refusals:
  - Power Query `rates` is left out. It reads a web address through Web.Contents, a web source, and it is connection only with nothing reading it, so it is not converted.
- Left alone: the Parameters and Keys Tables (empty settings), their D1 notes, and the Steps sheet.
- `<...>` to fill in: `<database>` in the query.

**Hive**

### recent

```sql
SELECT run_id, dt
FROM (
  SELECT run_id, dt FROM <database>.job_runs
  UNION ALL
  SELECT run_id, dt FROM <database>.scheduler_runs
) combined
ORDER BY run_id DESC
LIMIT 4
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X36

### Map

**Sources**
- run_alerts (alert_id, run_id, severity, dt): typed only, and no query loads it. Read by job_runs' alerts column and by query severity_by_day.

**Steps**
- None.

**Finals**
- job_runs (run_id, status, alerts): its alerts column is a COUNTIFS over run_alerts, so run_alerts is read in a LEFT JOIN with COALESCE(alerts, 0).
- severity_by_day (dt, high, low): the Table that query severity_by_day loads, so its rows are the query's. The query's steps (Source, Kept, Counted, Pivoted) are folded into this final's query.

**Values typed over a formula**
- None, so Keys needs no row.

**Marks**
- severity_by_day: the Pivot's columns are fixed as high and low, the severity values in the sample. A new severity value gets no column until the pivot is changed.

**Refusals**
- None.

**Left alone**
- Parameters and Keys, both empty.
- The Steps sheet, as cells outside a Table.

**To fill in**
- `<database>` in both blocks.

### Hive

```sql
SELECT j.run_id, j.status, COALESCE(c.alerts, 0) AS alerts
FROM <database>.job_runs j
LEFT JOIN (SELECT run_id, COUNT(*) AS alerts FROM <database>.run_alerts GROUP BY run_id) c
  ON j.run_id = c.run_id
```

```sql
SELECT dt,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
GROUP BY dt
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X37

### Map

**Sources**
- None.

**Steps**
- None.

**Finals**
- Owners (`<job_no>`, `<team_name>`, owner, day, `<is_ana>`): a Table with a formula column. No query loads it and nothing reads it, so it is a final. Its rows are read from `<database>.Owners`.

**Values typed over a formula**
- None, so Keys needs no row.

**Marks**
- blank: Owner is blank on the web rows, and the formula is a plain IF, not an -IF(S) form. So Owner is written as COALESCE(owner, ''), and a blank gives 0 as in Excel.
- case: Excel's = ignores case and Hive's does not. The sample's Owner values are all lower case, so no row changes.

**Refusals**
- None.

**Left alone**
- Parameters and Keys, both empty.

**To fill in**
- `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

### Hive

```sql
SELECT <job_no>, <team_name>, owner, day,
  IF(COALESCE(owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X38

### Map

**Sources**
- jobs (job_id, job_name, team, region): typed only, and no query loads it. Read by job_runs' region column.

**Steps**
- None.

**Finals**
- job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost). No query loads it and nothing reads it, so it is a final. Its typed columns are read from `<database>.job_runs`.
  - region: XLOOKUP on jobs, as a LEFT JOIN on job_id.
  - region_mins: a SUMIFS over its own Table on region, as a window over region.
  - retry_cost: a formula, with its typed-over value in a CASE.

**Values typed over a formula**
- retry_cost where run_id is 102: typed as 1. Keys holds job_runs, run_id, so the CASE matches on run_id.

**Marks**
- blank: avg_retry_secs is blank on run_id 98, and retry_cost reads it. Written as COALESCE(avg_retry_secs, 0).

**Refusals**
- None.

**Left alone**
- Parameters, empty.
- The blank status on run_id 98, as no formula reads status.

**To fill in**
- `<database>` in the block.

### Hive

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  j.region,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.region), 0) AS region_mins,
  CASE WHEN r.run_id = 102 THEN 1
    ELSE (COALESCE(r.avg_retry_secs, 0) + r.duration_mins) * 2 END AS retry_cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X39

### Map

**Sources**
- job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed only. Read by query ok_runs.
- jobs (job_id, job_name, team, region): typed only. Read by ok_runs' job_name column.

**Steps**
- None.

**Finals**
- ok_runs (run_id, job_id, duration_mins, job_name, share, noise): the Table that query ok_runs loads, so its rows are the query's. The query's steps (Source, Succeeded, Kept) are folded into this final's query. share is a SUMIFS over ok_runs by job_id, so it is a window over the query's rows.

**Values typed over a formula**
- None, so Keys needs no row.

**Marks**
- None.

**Refusals**
- noise: `=RAND()` is refused, as it gives a new value on each recalculation. Written as `NULL AS noise`.

**Left alone**
- Parameters and Keys, both empty.

**To fill in**
- `<database>` in the block.

### Hive

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  j.job_name,
  r.duration_mins / COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id), 0) AS share,
  NULL AS noise
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
WHERE r.status = 'SUCCESS'
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X40

### Map

**Sources**
- jobs (job_id, job_name, team, region): typed only. Read by the Runs step.

**Steps**
- Runs (Run, Job, Mins, Team, Cost): no query loads it, but run_alerts' Run Mins and Teams' Total Cost read it, so it is a step. It is a CTE in each final that reads it.
  - Team: XLOOKUP on jobs, as a LEFT JOIN on Job.
  - Cost: Mins times the Parameters value of rate, which is 2.

**Finals**
- run_alerts (alert_id, run_id, severity, dt, `<run_mins>`): no query loads it and nothing reads it, so it is a final. Its rows are read from `<database>.run_alerts`.
- Teams (Team, `<total_cost>`): a summary, since its only typed column, Team, is the one its SUMIFS matches on. Its typed groups, data and finance, are typed in, and it reads the Runs step through a GROUP BY.

**Values typed over a formula**
- None, so Keys needs no row.

**Marks**
- None.

**Refusals**
- None.

**Left alone**
- The PivotTable on sheet Pivot, from Runs.
- Parameters, read as its value 2, and Keys, empty.

**To fill in**
- `<database>`, `<run_mins>`, `<total_cost>`.

### Hive

```sql
WITH Runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt, r.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN Runs r ON a.run_id = r.Run
```

```sql
WITH Runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT t.Team, COALESCE(c.total_cost, 0) AS <total_cost>
FROM (SELECT 'data' AS Team UNION ALL SELECT 'finance') t
LEFT JOIN (SELECT Team, SUM(Cost) AS total_cost FROM Runs GROUP BY Team) c
  ON t.Team = c.Team
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X46

### Map
- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Typed columns only, and no query loads it.
- Steps: none.
- Finals: `jobs` (job_id, job_name, team, shortest, runs, busiest). It has formula columns, no query loads it, and no other Table's formula or query reads it.
- Parameters and Keys: both empty. Nothing is read by name, no value is typed over a formula, and no Keys row is needed.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`, the database that holds `job_runs` and `jobs`, in each read of them.

### Hive
```sql
-- final: jobs
SELECT j.job_id, j.job_name, j.team,
  COALESCE(s.shortest, 0) AS shortest,
  COALESCE(c.runs, 0) AS runs,
  RANK() OVER (ORDER BY COALESCE(c.runs, 0) DESC) AS busiest
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, MIN(duration_mins) AS shortest FROM <database>.job_runs GROUP BY job_id) s
  ON j.job_id = s.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X47

### Map
- Sources: none.
- Steps: none.
- Finals: `region_budgets` (job_id, budget_cents, region, cheapest_first, region_total, region_avg). No query loads it and no other Table reads it. Its typed job_id is not one a SUMIF or AVERAGEIF matches on, so it is a final, not a summary.
- Parameters and Keys: both empty. Nothing is read by name, and no Keys row is needed.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`, the database that holds `region_budgets`.

### Hive
```sql
-- final: region_budgets
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
- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (job_id, job_name, team, region); `run_alerts` (alert_id, run_id, severity, dt). Typed columns only, and no query loads them.
- Steps: none.
- Finals:
  - `quiet_runs` (run_id, job_id, status), the Table loaded by query quiet_runs. No formula reads it, so its rows are the query's.
  - `slow_regions` (region, avg_mins, fastest), the Table loaded by query slow_regions. No formula reads it, so its rows are the query's.
- Parameters and Keys: both empty. Nothing is read by name, and no Keys row is needed.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`, the database that holds `job_runs`, `jobs` and `run_alerts`, in each read of them.

### Hive
```sql
-- final: quiet_runs
SELECT t.run_id, t.job_id, t.status
FROM <database>.job_runs t
LEFT JOIN <database>.run_alerts u ON t.run_id = u.run_id
WHERE u.run_id IS NULL
```

```sql
-- final: slow_regions
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
- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (job_id, job_name, team, region); `run_alerts` (alert_id, run_id, severity, dt); `scheduler_runs` (run_id, job_id, dt); `job_owners` (job_id, team, owner, dt). Typed columns only, and no Table loads them.
- Steps: none.
- Finals:
  - `alert_status` (alert_id, severity, status), the Table loaded by query alert_status.
  - `run_check` (run_id, status, scheduled_run), the Table loaded by query run_check.
  - `teams` (team), the Table loaded by query teams, a distinct union of the team columns of `jobs` and `job_owners`.
  - No formula reads any of the three, so their rows are the queries'.
- Parameters and Keys: both empty. Nothing is read by name, and no Keys row is needed.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`, the database that holds the source Tables, in each read of them.

### Hive
```sql
-- final: alert_status
SELECT u.alert_id, u.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts u ON r.run_id = u.run_id
```

```sql
-- final: run_check
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

```sql
-- final: teams
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X50

### Map
- Sources: `job_owners` (job_id, team, owner, dt); `jobs` (job_id, job_name, team, region). Typed columns only, and no query loads them. `jobs` is read by the formula in owners.
- Steps: none.
- Finals: `owners` (job_id, owner, job_name, newest_first), the Table loaded by query owners. Its formula columns read only its own columns, and no other Table's formula or query reads it, so it is a final, and its rows are the query's: the distinct job_id and owner pairs of `job_owners`.
- Parameters and Keys: both empty. Nothing is read by name, and no Keys row is needed.
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: the Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- To fill in: `<database>`, the database that holds `job_owners` and `jobs`, in each read of them.

### Hive
```sql
-- final: owners
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X59

### Map

- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, long_runs, failed_mins, not_test); run_alerts (alert_id, run_id, severity, dt, alerts_so_far).
- **Values typed over a formula:** none; Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>` in each block.

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
) lr
  ON j.job_id = lr.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS failed_mins
  FROM <database>.job_runs
  WHERE LOWER(status) LIKE 'f%'
  GROUP BY job_id
) fm
  ON j.job_id = fm.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS not_test
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) nt
  ON j.job_id = nt.job_id
```

```sql
SELECT a.alert_id, a.run_id, a.severity, a.dt,
  COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts a
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X60

### Map

- **Sources:** none.
- **Steps:** none.
- **Finals:** region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region); region_budgets (Total Row) (job_id, budget_cents).
- **Values typed over a formula:** none; Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>` in each block.

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

- **Sources:** region_costs (job_id, cost_cents, region, dt).
- **Steps:** none.
- **Finals:** by_region (region, total_cents, entries, priciest), a summary whose typed groups eu and us are typed in, with region_costs read; by_region (Total Row) (total_cents, entries, priciest).
- **Values typed over a formula:** none; Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>` in each block.

### Hive

```sql
SELECT g.region,
  COALESCE(c.total_cents, 0) AS total_cents,
  COALESCE(c.entries, 0) AS entries,
  COALESCE(c.priciest, 0) AS priciest
FROM (SELECT 'eu' AS region UNION ALL SELECT 'us') g
LEFT JOIN (
  SELECT region, SUM(cost_cents) AS total_cents, COUNT(*) AS entries, MAX(cost_cents) AS priciest
  FROM <database>.region_costs
  GROUP BY region
) c
  ON g.region = c.region
```

```sql
WITH by_region AS (
  SELECT g.region,
    COALESCE(c.total_cents, 0) AS total_cents,
    COALESCE(c.entries, 0) AS entries,
    COALESCE(c.priciest, 0) AS priciest
  FROM (SELECT 'eu' AS region UNION ALL SELECT 'us') g
  LEFT JOIN (
    SELECT region, SUM(cost_cents) AS total_cents, COUNT(*) AS entries, MAX(cost_cents) AS priciest
    FROM <database>.region_costs
    GROUP BY region
  ) c
    ON g.region = c.region
)
SELECT SUM(total_cents) AS total_cents, SUM(entries) AS entries, MAX(priciest) AS priciest
FROM by_region
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X62

### Map

- **Sources:** none.
- **Steps:** none.
- **Finals:** team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short).
- **Values typed over a formula:** none; Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>` in the block.

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

- **Sources:** scheduler_runs (run_id, job_id, dt).
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded).
- **Values typed over a formula:** none; Keys is empty.
- **Marks:** blank: status is blank in run 98, and succeeded reads status in a SEARCH, which is not in an -IF(S) form or ISBLANK, so status is written as COALESCE(status, '').
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>` in the block.

### Hive

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  r.avg_retry_secs IS NULL AS no_retry,
  FLOOR(r.duration_mins / 4) AS quarters,
  LEAST(r.duration_mins, 25) AS capped,
  VAR_SAMP(r.duration_mins) OVER () AS variance,
  SUM(r.duration_mins * r.job_id) OVER () AS weighted,
  COALESCE(s.job_id, -1) AS scheduled_job,
  CONCAT('run ', r.run_id) AS label,
  INSTR(LOWER(COALESCE(r.status, '')), 'cess') > 0 AS succeeded
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs s
  ON r.run_id = s.run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X64

### Map

- **Sources:** `jobs` (job_id, job_name, team, region) and `region_costs` (job_id, cost_cents, region, dt). Both are read as `<database>.jobs` and `<database>.region_costs`.
- **Steps:** none. No query's M names another query.
- **Finals:**
  - `picked_costs` (job_id, cost_cents, region, size), loaded by query picked_costs.
  - `costed_jobs` (job_id, job_name, team, region), loaded by query costed_jobs.
  - `costs_filled` (job_id, cost_cents, dt, day), loaded by query costs_filled.
- **Values typed over a formula:** none. No Table has a formula column.
- **Marks:** `costs_filled`: blank. Row 29 of region_costs has a blank cost_cents. The query's Table.ReplaceValue makes it 0, so the block uses COALESCE(cost_cents, 0).
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty. Neither is a source, step or final.
- **To fill in:** `<database>` in each block.

### Hive

```sql
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT j.job_name LIKE 'n%'
```

```sql
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt, SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X65

### Map

- **Sources:**
  - `jobs` (job_id, job_name, team, region)
  - `region_budgets` (job_id, budget_cents, region)
  - `job_owners` (job_id, team, owner, dt)
  - `scheduler_runs` (run_id, job_id, dt)
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt)
- **Steps:** none.
- **Finals:**
  - `team_regions` (team, region), loaded by query team_regions.
  - `budget_places` (job_id, budget_cents, region, place), loaded by query budget_places.
  - `jobs_per_team` (team, jobs), loaded by query jobs_per_team.
  - `ran_as_scheduled` (run_id, dt), loaded by query ran_as_scheduled.
  - `run_measures` (run_id, job_id, measure, amount), loaded by query run_measures.
- **Values typed over a formula:** none. No Table has a formula column, and Keys is empty.
- **Marks:**
  - `team_regions`: order dropped. The Table.Sort has no FirstN or index after it, so the Hive has no ORDER BY.
  - `run_measures`: blank. job_runs row 98 has a blank avg_retry_secs, so it gives no row, as M's Table.Unpivot drops a null.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty.
- **To fill in:** `<database>` in each block.

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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X66

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
- **Steps:** none. Query ok_runs loads Table ok_runs, and nothing names the query, so its rows are the Table's final.
- **Finals:**
  - Table `ok_runs` (run_id, job_id, duration_mins, dt, running, share). Its formula columns are running and share.
  - `ok_runs (Total Row)` (duration_mins). Its Total Row holds one total, SUBTOTAL(109) over duration_mins.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty.
- **To fill in:** `<database>` in each block.

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
SELECT SUM(duration_mins) AS duration_mins FROM ok_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X69

### Map

- **Sources:**
  - `jobs` (job_id, job_name, team, region)
  - `region_budgets` (job_id, budget_cents, region)
- **Steps:** none. No query exists in this workbook.
- **Finals:** Table `region_costs` (job_id, cost_cents, region, dt, job_name, budget, over_budget, running_cost). It has formula columns and no query loads it. Nothing else reads it, and its own formulas reading its own row don't count, so it is a final.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:**
  - `over_budget`: blank. Row 29 (job 2, 20260924) has a blank cost_cents. The comparison reads it as 0, as Excel does, so the block uses COALESCE(cost_cents, 0).
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty.
- **To fill in:** `<database>` in the block.

### Hive

```sql
SELECT rc.job_id, rc.cost_cents, rc.region, rc.dt,
  j.job_name,
  rb.budget_cents AS budget,
  COALESCE(rc.cost_cents, 0) > rb.budget_cents AS over_budget,
  COALESCE(SUM(rc.cost_cents) OVER (PARTITION BY rc.job_id ORDER BY rc.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
FROM <database>.region_costs rc
LEFT JOIN <database>.jobs j ON rc.job_id = j.job_id
LEFT JOIN <database>.region_budgets rb ON rc.job_id = rb.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X70

### Map

- **Sources:**
  - `jobs` (job_id, job_name, team, region)
  - `job_owners` (job_id, team, owner, dt)
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt)
- **Steps:**
  - `staffed` (query, connection only). It loads nothing, but owner_load's M names it, so it is a step and a CTE in each final that reads it, not left out. Its columns are job_id, job_name, owner.
  - `owner_load` (query). It loads Table owner_load, and busiest_owner's M names it, so it is also a step. It is a CTE in busiest_owner's block and in the Total Row's block. Its rows are the Table's.
- **Finals:**
  - Table `owner_load` (owner, total_mins, runs, avg_mins). Its formula column is avg_mins.
  - `owner_load (Total Row)` (runs). Its Total Row holds one total, SUBTOTAL(109) over runs.
  - Table `busiest_owner` (owner, total_mins, runs), loaded by query busiest_owner.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty.
- **To fill in:** `<database>` in each block.

### Hive

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
    ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
)
SELECT g.owner, g.total_mins, g.runs, g.total_mins / g.runs AS avg_mins
FROM (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
) g
```

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
    ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT g.owner, g.total_mins, g.runs, g.total_mins / g.runs AS avg_mins
  FROM (
    SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
    FROM staffed s
    LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
    GROUP BY s.owner
  ) g
)
SELECT SUM(runs) AS runs FROM owner_load
```

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
    ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT g.owner, g.total_mins, g.runs
  FROM (
    SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
    FROM staffed s
    LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
    GROUP BY s.owner
  ) g
)
SELECT owner, total_mins, runs
FROM owner_load
ORDER BY runs DESC
LIMIT 1
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X73

### Map

- **Sources:** `region_budgets` (job_id, budget_cents, region); `jobs` (job_id, job_name, team, region).
- **Steps:** query `eu_budgets`, a CTE in the `eu_count` final. It is the query named in query `eu_count`'s M, so it is a step, not the Table of the same name. Columns: job_id, budget_cents, region, job_name. It keeps `region_budgets` rows where region is 'eu', inner-joined to `jobs` on job_id.
- **Finals:**
  - Table `eu_budgets` (job_id, budget_cents, region, job_name, dollars): loaded by query `eu_budgets`; no other Table's formula reads it. Its formula column dollars is budget_cents / 100.
  - Table `eu_count` (region, jobs, total_cents): loaded by query `eu_count`, which groups the step by region: COUNT(*) as jobs, SUM(budget_cents) as total_cents.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet (cells outside a Table); Parameters and Keys (empty Tables, never a source, step or final).
- **`<...>` to fill in:** `<database>`, in each block.

### Hive

```sql
SELECT r.job_id, r.budget_cents, r.region, j.job_name, r.budget_cents / 100 AS dollars
FROM <database>.region_budgets r
JOIN <database>.jobs j ON r.job_id = j.job_id
WHERE r.region = 'eu'
```

```sql
WITH eu_budgets AS (
  SELECT r.job_id, r.budget_cents, r.region, j.job_name
  FROM <database>.region_budgets r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  WHERE r.region = 'eu'
)
SELECT region, COUNT(*) AS jobs, SUM(budget_cents) AS total_cents
FROM eu_budgets
GROUP BY region
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X74

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- **Steps:** Table `run_alerts` (alert_id, run_id, severity, dt, status, job_id, alerts_so_far). It is a step because query `late_alerts` reads it and Table `by_status`'s formula reads `run_alerts[status]`, so it is a CTE in both finals. Its status and job_id are the XLOOKUPs, a LEFT JOIN of `job_runs` on run_id. Its alerts_so_far is the running count, COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), ties included.
- **Finals:**
  - Table `by_status` (status, alerts): a summary, since its only typed column is the one COUNTIFS matches on. Its final is a GROUP BY of the step `run_alerts`, with the typed statuses FAILED and SUCCESS typed in.
  - Table `late_alerts` (alert_id, run_id, alerts_so_far): loaded by query `late_alerts`, which reads the step, keeps alerts_so_far > 5, and keeps alert_id, run_id, alerts_so_far.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:**
  - blank: `job_runs` has a blank status on run 98 (sample row 5), and the status XLOOKUP reads that column, so the step writes `COALESCE(jr.status, '')`. No alert points at run 98, so no value in the sample changes.
- **Refusals:** none.
- **Left alone:** the Steps sheet (cells outside a Table); Parameters and Keys (empty Tables, never a source, step or final); the blank avg_retry_secs on run 98 in `job_runs`, which no formula reads.
- **`<...>` to fill in:** `<database>`, in each block.

### Hive

```sql
WITH run_alerts AS (
  SELECT ra.alert_id, ra.run_id, ra.severity, ra.dt,
    COALESCE(jr.status, '') AS status,
    jr.job_id,
    COUNT(*) OVER (ORDER BY ra.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts ra
  LEFT JOIN <database>.job_runs jr ON ra.run_id = jr.run_id
)
SELECT s.status, COALESCE(c.alerts, 0) AS alerts
FROM (SELECT 'FAILED' AS status UNION ALL SELECT 'SUCCESS') s
LEFT JOIN (SELECT status, COUNT(*) AS alerts FROM run_alerts GROUP BY status) c
  ON s.status = c.status
```

```sql
WITH run_alerts AS (
  SELECT ra.alert_id, ra.run_id, ra.severity, ra.dt,
    COALESCE(jr.status, '') AS status,
    jr.job_id,
    COUNT(*) OVER (ORDER BY ra.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts ra
  LEFT JOIN <database>.job_runs jr ON ra.run_id = jr.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM run_alerts
WHERE alerts_so_far > 5
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X77

### Map

- **Sources:** `run_alerts` (alert_id, run_id, severity, dt). No query loads it and it has no formula column, so it is a source.
- **Steps:** query `high_alerts`, a CTE in the `high_per_day` final. It is the query named in query `high_per_day`'s M, so it is a step, not the Table of the same name. Columns: alert_id, run_id, dt. It keeps `run_alerts` rows where severity is 'high'.
- **Finals:**
  - Table `high_alerts` (alert_id, run_id, dt, late_run): loaded by query `high_alerts`; no Table's formula reads it. Its formula column late_run is run_id > 100.
  - Table `high_per_day` (dt, alerts): loaded by query `high_per_day`, which groups the step by dt: COUNT(*) as alerts.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet (cells outside a Table); Parameters and Keys (empty Tables, never a source, step or final).
- **`<...>` to fill in:** `<database>`, in each block.

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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X78

### Map

- **Sources:** `region_costs` (job_id, cost_cents, region, dt).
- **Steps:** query `known_costs`, a CTE in the `cost_per_job` final. Columns: job_id, cost_cents, dt. It keeps `region_costs` rows where cost_cents IS NOT NULL, as M's `[cost_cents] <> null` does, so the one blank row (job 2, 20260924) is dropped.
- **Finals:**
  - Table `known_costs` (job_id, cost_cents, dt, dollars): loaded by query `known_costs`; no Table's formula reads it. Its formula column dollars is cost_cents / 100. Its rows are the query's rows.
  - Table `known_costs (Total Row)` (cost_cents): the Total Row's cells are the label "Total" (no column), SUBTOTAL(109, ...) on cost_cents (a SUM), and two empty cells (no column). It reads the Table's final as a CTE.
  - Table `cost_per_job` (job_id, total_cents): loaded by query `cost_per_job`, which groups the step by job_id: SUM(cost_cents) as total_cents.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet (cells outside a Table); Parameters and Keys (empty Tables, never a source, step or final); dt kept as typed (such as 20260911), since no formula or query reads it as a date.
- **`<...>` to fill in:** `<database>`, in each block.

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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

