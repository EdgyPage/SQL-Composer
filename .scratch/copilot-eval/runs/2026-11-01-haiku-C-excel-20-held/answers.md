date: 2026-11-01
arm: C
model: haiku
files: 20-held

## X21

### Map
- **Sources:** region_budgets, its typed columns job_id, budget_cents, region.
- **Steps:** none.
- **Finals:** region_budgets (job_id, budget_cents, region, budget_dollars, with_margin). It has formula columns, no query loads it, and nothing reads it, so it is a final.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet, which holds the workbook's instructions and is not a Table. Parameters and Keys are both empty, so they are not a source, step or final, and no formula uses a fixed value.
- **To fill in:** `<database>`, the Dev database name.

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
- **Sources:** jobs, its typed columns job_id, job_name, team.
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, team, is_finance, ratio). It has formula columns, no query loads it, and nothing reads it, so it is a final.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet, which holds the workbook's instructions and is not a Table. Parameters and Keys are both empty and are left out.
- **To fill in:** `<database>`, the Dev database name.

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
- **Sources:** job_runs, its typed columns run_id, status, avg_retry_secs.
- **Steps:** none.
- **Finals:** job_runs (run_id, status, avg_retry_secs, label, risky). It has formula columns, no query loads it, and nothing reads it, so it is a final.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:**
  - **blank:** run 98 has a blank status and a blank avg_retry_secs. label reads status as COALESCE(status, '') and risky reads status as COALESCE(status, '') and avg_retry_secs as COALESCE(avg_retry_secs, 0), so a blank gives the result Excel gives (label "other", risky FALSE). The typed columns in the SELECT keep the blanks as NULL.
- **Refusals:** none. `_xlfn.SWITCH` is read as SWITCH, past its prefix.
- **Left alone:** the Steps sheet, which holds the workbook's instructions and is not a Table. Parameters and Keys are both empty and are left out.
- **To fill in:** `<database>`, the Dev database name.

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
- **Sources:** team_notes, its typed columns team, note, written_on.
- **Steps:** none.
- **Finals:** team_notes (team, note, written_on, first_word, shout, month, tens_of_chars). It has formula columns, no query loads it, and nothing reads it, so it is a final.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:** none. written_on holds dates (2026-09-11 and so on), not a date held as text, so MONTH reads it as it is.
- **Refusals:** none.
- **Left alone:** the Steps sheet, which holds the workbook's instructions and is not a Table. Parameters and Keys are both empty and are left out.
- **To fill in:** `<database>`, the Dev database name.

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
- **Sources:** Costs, its typed columns Job, Cost (cents), Region, Day Key; Budgets, its typed columns Job, Budget, Region.
- **Steps:** none.
- **Finals:** Costs (Job, Cost (cents), Region, Day Key, Day) and Budgets (Job, Budget, Region, Dollars). Each has formula columns, no query loads it, and nothing reads it, so each is a final.
- **Values typed over a formula:** none, so no Keys row is needed.
- **Marks:**
  - **date held as text:** Day Key holds 20260911 and so on. Costs' Day, DATE(LEFT, MID, RIGHT) of Day Key, is written by the date-as-text rule as CONCAT of the three parts. Day therefore comes out as text 'yyyy-mm-dd', not a date type.
- **Refusals:** none.
- **Left alone:** the Steps sheet, which holds the workbook's instructions and is not a Table. Parameters and Keys are both empty and are left out.
- **To fill in:** `<database>`, the Dev database name; `<cost_cents>`, for the header Cost (cents); `<day_key>`, for the header Day Key.

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

**Map**

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt; its typed columns, read from `<database>.job_runs`). `run_alerts` (alert_id, run_id, severity; its typed columns, read from `<database>.run_alerts`).
- **Steps:** none. No formula or query reads a Table into another.
- **Finals:** `run_alerts` (alert_id, run_id, severity, job_id, status, avg_mins). No query loads it and nothing else reads it.
- **Settings, neither a source, step nor final:** `Parameters` and `Keys`, both empty. No Parameters value is read in, and no Keys row is needed.
- **Typed over a formula:** none.
- **Marks:**
  - `status` (VLOOKUP into job_runs, column 3, exact): `blank`. The sample has a blank status on run 98, so the status is written `COALESCE(j.status, '')`.
  - `avg_mins` (AVERAGEIFS): AVG, left NULL where no run matches, as Excel shows #DIV/0! there.
- **Refusals:** none.
- **Left alone:** the Steps sheet, as it is text outside a Table.
- **To fill in:** `<database>`, in each read.

### Hive

```sql
-- run_alerts
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

**Next:** Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X27

**Map**

- **Sources:** `jobs` (job_id, job_name, team, region; its typed columns, read from `<database>.jobs`). It has only typed columns and no query loads it.
- **Steps:** none.
- **Finals:** `by_team`, a summary (team, jobs_in_team, last_job_id, last_job_name). Its only typed column is team, which its COUNTIFS match on, so its typed teams (data, finance, web) are typed in as its groups, and `jobs` is read for the rest.
- **Settings, neither a source, step nor final:** `Parameters` and `Keys`, both empty.
- **Typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet, as it is text outside a Table.
- **To fill in:** `<database>`, in each read.

### Hive

```sql
-- by_team
SELECT
  t.team,
  COALESCE(c.jobs_in_team, 0) AS jobs_in_team,
  COALESCE(m.last_job_id, 0) AS last_job_id,
  n.job_name AS last_job_name
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (
  SELECT team, COUNT(*) AS jobs_in_team
  FROM <database>.jobs
  GROUP BY team
) c ON t.team = c.team
LEFT JOIN (
  SELECT team, MAX(job_id) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
) m ON t.team = m.team
LEFT JOIN <database>.jobs n ON m.last_job_id = n.job_id
```

**Next:** Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X28

**Map**

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt; its typed columns, read from `<database>.job_runs`). `jobs` (job_id, job_name; its typed columns, read from `<database>.jobs`).
- **Steps:** none.
- **Finals:** `jobs` (job_id, job_name, ok_mins). Not a summary, as job_name is typed and its SUMIFS doesn't match on it.
- **Settings, neither a source, step nor final:** `Parameters`, empty. `Keys`, with one row: jobs, job_id.
- **Typed over a formula:** `jobs`, row 4 (report_build, job_id 3): ok_mins is typed as 99 in place of its SUMIFS. The Keys row names job_id, so the value is a CASE matched on job_id.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the blank status on job_runs run 98. The SUMIFS form skips it, so it is written as it is, with no COALESCE. Also the Steps sheet.
- **To fill in:** `<database>`, in each read.

### Hive

```sql
-- jobs
SELECT
  j.job_id,
  j.job_name,
  CASE WHEN j.job_id = 3 THEN 99 ELSE COALESCE(s.total, 0) END AS ok_mins
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
  GROUP BY job_id
) s ON j.job_id = s.job_id
```

**Next:** Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X29

**Map**

- **Sources:** `region_budgets` (job_id, budget_cents, region; its typed columns, read from `<database>.region_budgets`).
- **Steps:** none.
- **Finals:** `region_budgets` (job_id, budget_cents, region, in_dollars, pointer). Nothing else reads it, and its formulas are not SUMIFS or COUNTIFS, so it is not a summary.
- **Settings, neither a source, step nor final:** `Parameters`, with cents_per_dollar = 100, read in as its value, so in_dollars divides by 100. `Keys`, empty.
- **Typed over a formula:** `region_budgets`, row 4 (job_id 3, budget_cents 350, region us): in_dollars is typed as 5. No Keys row names region_budgets, so there is no Keys row, and the CASE matches on every typed column of the row: job_id, budget_cents and region.
- **Marks:** none.
- **Refusals:** `pointer`, `=INDIRECT("A"&ROW())` in every row. INDIRECT and ROW() are refused, so it is `NULL AS pointer`.
- **Left alone:** the Steps sheet, as it is text outside a Table.
- **To fill in:** `<database>`, in each read.

### Hive

```sql
-- region_budgets
SELECT
  job_id,
  budget_cents,
  region,
  CASE WHEN job_id = 3 AND budget_cents = 350 AND region = 'us' THEN 5 ELSE budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets
```

**Next:** Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X30

**Map**

- **Sources:** `scheduler_runs` (run_id, job_id, dt; its typed columns, read from `<database>.scheduler_runs`).
- **Steps:** none.
- **Finals:** `scheduler_runs` (run_id, job_id, dt, day, prev_run, jitter). Nothing else reads it, and its formulas are not SUMIFS or COUNTIFS, so it is not a summary.
- **Settings, neither a source, step nor final:** `Parameters` and `Keys`, both empty.
- **Typed over a formula:** none.
- **Marks:**
  - `day`: `RIGHT(dt, 2)` as `SUBSTR(dt, -2)`. The sample shows dt as 2026-09-23, so day reads 23. If dt is an Excel date rather than text, Excel's RIGHT reads its serial number instead, so check the day column against the sample.
- **Refusals:**
  - `prev_run`: `=OFFSET(...)`, refused, as it hangs on the order of the sheet's rows; `NULL AS prev_run`.
  - `jitter`: `=RANDBETWEEN(1,5)`, refused, as it is random; `NULL AS jitter`.
- **Left alone:** the Summary sheet's bar chart (charts), the Pivot sheet's PivotTable from scheduler_runs (PivotTables), and the Steps sheet.
- **To fill in:** `<database>`, in each read.

### Hive

```sql
-- scheduler_runs
SELECT
  run_id,
  job_id,
  dt,
  SUBSTR(dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs
```

**Next:** Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X31

### Map

- **Sources:** jobs, its typed columns job_id and team, read as `<database>.jobs`.
- **Steps:** none.
- **Finals:** jobs (job_id, team, bump, tag, scaled, boosted). It has formula columns and nothing else reads it, so it is a final. Its typed columns are read from its source.
- **Values typed over a formula:** none. The Keys Table is empty.
- **Marks:** boosted. `boost` is a defined name for Summary!B2, a cell outside a Table, so its value 10 is written in. Move it into Parameters (name boost, value 10).
- **Refusals:**
  - bump: circular, the formula reads its own column. `NULL AS bump`.
  - tag: TAG is a defined name holding a LAMBDA. `NULL AS tag`.
  - scaled: reads Summary!D4, a cell outside a Table that is not a defined name. `NULL AS scaled`.
- **Left alone:** Parameters and Keys (both empty, so never a source, step or final); the Steps sheet; the rest of the Summary sheet.
- **To fill in:** `<database>` in the FROM.

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

- **Sources:**
  - jobs (job_id, job_name, team, region), read as `<database>.jobs`.
  - job_runs, its typed columns (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
- **Steps:** job_runs. Its job_name formula reads jobs, and by_name's COUNTIFS reads job_runs[job_name], so it is a step, a CTE in by_name. Its columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name.
- **Finals:** by_name (job_name, runs), a summary, since its only typed column is the one its COUNTIFS matches on. Its typed groups invoice_sync, nightly_load and report_build are typed in. It has no Total Row.
- **Values typed over a formula:** none. The Keys Table is empty.
- **Marks:**
  - job_runs.job_name: VLOOKUP with TRUE is approximate. Written as the exact match, `LEFT JOIN ... ON r.job_id = j.job_id`.
- **Refusals:** none.
- **Left alone:** Parameters and Keys (both empty); the Steps sheet. Blank status and avg_retry_secs in run 98 pass through as NULL, as no formula reads them.
- **To fill in:** `<database>` in each FROM and JOIN.

### Hive

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT b.job_name, COALESCE(c.runs, 0) AS runs
FROM (SELECT 'invoice_sync' AS job_name UNION ALL SELECT 'nightly_load' UNION ALL SELECT 'report_build') b
LEFT JOIN (SELECT job_name, COUNT(*) AS runs FROM job_runs GROUP BY job_name) c
  ON b.job_name = c.job_name
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X33

### Map

- **Sources:** job_runs, read by the slow_runs query. Its Power Query reads Sql.Database("dwh01", "ops"), the table ops.job_runs. Read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** slow_runs (run_id, duration_mins, over_by), loaded by Power Query slow_runs. No formula reads it, so it is a final, and its rows are the query's.
- **Values typed over a formula:** none. Its rows are the query's output, and the Keys Table is empty.
- **Marks:**
  - Sql.Database: the table it names, ops.job_runs on dwh01, is read as `<database>.job_runs`. Named for the user to check.
  - M's `<>` keeps a null, Hive's doesn't: written as `(status <> 'TEST' OR status IS NULL)`.
- **Refusals:** none.
- **Left alone:** Parameters and Keys (both empty).
- **To fill in:** `<database>` in the FROM.

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

- **Sources:**
  - job_runs, its typed columns (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`.
  - jobs, its typed columns (job_id, job_name, team, region), read as `<database>.jobs`.
- **Steps:** runs_with_team, a query that is connection only. team_totals names it, so it is a CTE in team_totals. Its columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt, team. The LeftOuter NestedJoin is a LEFT JOIN.
- **Finals:** team_totals (team, total_mins, longest), loaded by Power Query team_totals. No formula reads it, so it is a final, and its rows are the query's. It has no Total Row.
- **Values typed over a formula:** none. The Keys Table is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys (both empty). Blank status and avg_retry_secs in run 98 pass through as NULL, as no formula reads them.
- **To fill in:** `<database>` in each FROM and JOIN.

### Hive

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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X35

### Map

- **Sources:**
  - job_runs, its typed columns, read for run_id and dt as `<database>.job_runs`.
  - scheduler_runs, its typed columns (run_id, job_id, dt), read for run_id and dt as `<database>.scheduler_runs`.
- **Steps:** none. The recent query's own steps (Runs, Scheduled, Both, Sorted, Top) are its final's query.
- **Finals:** recent (run_id, dt), loaded by Power Query recent. No formula reads it, so it is a final, and its rows are the query's.
- **Values typed over a formula:** none. The Keys Table is empty.
- **Marks:** none.
- **Refusals:**
  - Power Query rates reads the web through Web.Contents. It loads nothing and nothing reads it, so the query is left out.
- **Left alone:** Parameters and Keys (both empty).
- **To fill in:** `<database>` in each FROM and UNION ALL branch.

### Hive

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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X36

### Map

- **Sources** (each read as `<database>.<table>`):
  - `run_alerts` (alert_id, run_id, severity, dt), its typed columns.
  - `job_runs` (run_id, status), its typed columns.
- **Steps:** none.
- **Finals:**
  - `job_runs` (run_id, status, alerts). Its only formula column is alerts, a COUNTIFS over run_alerts. No query loads job_runs and nothing reads it, so it is a final.
  - `severity_by_day` (dt, high, low). Power Query `severity_by_day` loads this Table, and no formula reads it, so the Table is the final and its rows are the query's. The query and the Table are two things, and the query's pivot is this final's block.
- **Values typed over a formula:** none. Keys is empty, so it has no row.
- **Marks:**
  - `severity_by_day`: the pivot's columns high and low are fixed to the severities in the sample. A new severity value needs a new column in the query.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty, so nothing is read from them (never a source, step or final); their notes in column D; the Steps sheet's text, which is not a Table.
- **To fill in:** `<database>`, in each block.

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

- **Sources** (each read as `<database>.<table>`):
  - `Owners` (Job No, Team Name, Owner, Day), its typed columns.
- **Steps:** none.
- **Finals:**
  - `Owners` (Job No, Team Name, Owner, Day, Is Ana). Its only formula column is Is Ana, which reads its own row. No query loads Owners and nothing else reads it, so it is a final. It has no SUMIFS or COUNTIFS, so it is not a summary.
- **Values typed over a formula:** none. Keys is empty, so it has no row.
- **Marks:**
  - `blank`: Owner is blank on the web rows (Job No 4, for example row 5), and Is Ana reads Owner. Plain IF is not an -IF(S) form, so Owner is written as COALESCE(Owner, '') and not as it is.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty (never a source, step or final); their notes in column D; the Steps sheet's text, which is not a Table.
- **To fill in:** `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

### Hive

```sql
SELECT <job_no>, <team_name>, Owner, Day,
  IF(COALESCE(Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X38

### Map

- **Sources** (each read as `<database>.<table>`):
  - `jobs` (job_id, job_name, team, region), its typed columns. Only job_runs' formula reads it, so it is a source only.
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs), its typed columns.
- **Steps:** none.
- **Finals:**
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost). Its formula columns read its own rows and its own whole columns, and nothing else reads job_runs, so it is a final. It is not a summary, because status is typed and no SUMIFS matches on it.
- **Values typed over a formula:**
  - `retry_cost` at run_id 102, typed as 1. Keys holds the row job_runs with run_id, so the CASE matches on run_id.
- **Marks:**
  - `blank`: avg_retry_secs is blank on run_id 98, and retry_cost reads it. Written as COALESCE(avg_retry_secs, 0). Status is also blank on run_id 98, but no formula reads status, so it gets no mark.
- **Refusals:** none.
- **Left alone:** Parameters (empty) and Keys (its one row, read as the setting, never a source, step or final); their notes in column D; the Steps sheet's text, which is not a Table.
- **To fill in:** `<database>`, in each block.

### Hive

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  j.region AS region,
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

- **Sources** (each read as `<database>.<table>`):
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), its typed columns. No formula reads it, and it is loaded by no Table, so it is a source. Power Query ok_runs reads it.
  - `jobs` (job_id, job_name, team, region), its typed columns. The ok_runs formula reads it.
- **Steps:** none.
- **Finals:**
  - `ok_runs` (run_id, job_id, duration_mins, job_name, share, noise). Power Query ok_runs loads this Table, and no other Table's formula reads it, so the Table is the final. Its rows are the query's: job_runs' SUCCESS rows. Its formula columns job_name and share are written over those rows.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:**
  - `noise` (=RAND()): NULL AS noise. RAND gives a new number on every recalculation, so no fixed Hive gives the same values.
- **Left alone:** Parameters and Keys, both empty (never a source, step or final); their notes in column D; the Steps sheet's text, which is not a Table.
- **To fill in:** `<database>`, in the block.

### Hive

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  j.job_name AS job_name,
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

- **Sources** (each read as `<database>.<table>`):
  - `Runs` (Run, Job, Mins), its typed columns.
  - `jobs` (job_id, job_name, team, region), its typed columns.
- **Steps:**
  - `Runs` (Run, Job, Mins, Team, Cost). Its formulas are read by Teams' SUMIFS and by run_alerts' XLOOKUP, so it is a step, a CTE in each of those two finals. Team is the jobs lookup of team; Cost is Mins times the rate.
- **Finals:**
  - `Teams` (Team, `<total_cost>`). It is a summary: its only typed column, Team, is the one its SUMIFS matches on. Its final is a GROUP BY of Runs, with its typed groups data and finance kept. No formula reads Teams, so it is a final.
  - `run_alerts` (alert_id, run_id, severity, dt, `<run_mins>`). Its only formula column is Run Mins, and nothing reads run_alerts, so it is a final.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:**
  - Parameters: `rate` is 2, read in as the value 2 in Runs' Cost, so Cost is Mins * 2. The Table itself is never a source, step or final. If the rate changes, change the 2.
  - Keys (empty), and the notes in column D of Parameters and Keys.
  - The PivotTable on sheet Pivot (from Runs, rows Team, values Sum of Cost). PivotTables are left alone.
  - The Steps sheet's text, which is not a Table.
- **To fill in:** `<database>`, `<total_cost>`, `<run_mins>`.

### Hive

```sql
WITH Runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT t.Team, COALESCE(c.<total_cost>, 0) AS <total_cost>
FROM (SELECT 'data' AS Team UNION ALL SELECT 'finance') t
LEFT JOIN (SELECT Team, SUM(Cost) AS <total_cost> FROM Runs GROUP BY Team) c
  ON t.Team = c.Team
```

```sql
WITH Runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt, n.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN Runs n ON a.run_id = n.Run
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X46

**Map**

- **Sources:** `jobs` (typed columns job_id, job_name, team); `job_runs` (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt). Both are typed only, and no query loads them.
- **Steps:** none.
- **Finals:** Table `jobs` (job_id, job_name, team, shortest, runs, busiest). It has formula columns, no query loads it, and nothing reads it, so it is a final. shortest is MINIFS as MIN, with 0 where nothing matches; runs is COUNTIF as COUNT(*), with 0 where nothing matches; busiest is RANK.EQ as a descending RANK over runs.
- **Settings:** `Parameters` and `Keys` are empty Tables, never a source, step or final. No formula reads a Parameters value, and no value is typed over a formula, so Keys needs no row.
- **Typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet's text, and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).
- **To fill in:** `<database>`, the database name, in each read.

**Hive**

### jobs

```sql
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

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X47

**Map**

- **Sources:** `region_budgets` (typed columns job_id, budget_cents, region).
- **Steps:** none.
- **Finals:** Table `region_budgets` (job_id, budget_cents, region, cheapest_first, region_total, region_avg). It has formula columns, no query loads it, and nothing reads it, so it is a final. It is not a summary, as its typed columns are not only the ones its SUMIF matches on. cheapest_first is RANK.EQ ascending; region_total is SUMIF as a windowed SUM with 0 where nothing matches; region_avg is AVERAGEIF as a windowed AVG, left NULL where nothing matches.
- **Settings:** `Parameters` and `Keys` are empty Tables, never a source, step or final. No value is typed over a formula, so Keys needs no row.
- **Typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet's text, and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).
- **To fill in:** `<database>`, the database name, in each read.

**Hive**

### region_budgets

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X48

**Map**

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (job_id, job_name, team, region); `run_alerts` (alert_id, run_id, severity, dt). All three are typed only, and no query loads them.
- **Steps:** none. No query names another query.
- **Finals:**
  - Table `quiet_runs` (run_id, job_id, status), loaded by query `quiet_runs`. No formula reads it, so it is a final, and its rows are the query's, not the sample's.
  - Table `slow_regions` (region, avg_mins, fastest), loaded by query `slow_regions`. No formula reads it, so it is a final, and its rows are the query's, not the sample's.
- **Settings:** `Parameters` and `Keys` are empty Tables, never a source, step or final. No value is typed over a formula, so Keys needs no row.
- **Typed over a formula:** none, as the workbook has no formulas.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet's text, and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).
- **To fill in:** `<database>`, the database name, in each read.

**Hive**

### quiet_runs

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

### slow_regions

```sql
SELECT j.region, AVG(r.duration_mins) AS avg_mins, MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X49

**Map**

- **Sources:**
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt)
  - `jobs` (job_id, job_name, team, region)
  - `run_alerts` (alert_id, run_id, severity, dt)
  - `scheduler_runs` (run_id, job_id, dt)
  - `job_owners` (job_id, team, owner, dt)

  All are typed only, and no query loads them.
- **Steps:** none. No query names another query.
- **Finals:**
  - Table `alert_status` (alert_id, severity, status), loaded by query `alert_status`. No formula reads it, so it is a final, and its rows are the query's.
  - Table `run_check` (run_id, status, scheduled_run), loaded by query `run_check`. It is a final, and its rows are the query's.
  - Table `teams` (team), loaded by query `teams`. It is a final, and its rows are the query's.
- **Settings:** `Parameters` and `Keys` are empty Tables, never a source, step or final. No value is typed over a formula, so Keys needs no row.
- **Typed over a formula:** none, as the workbook has no formulas.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet's text, and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).
- **To fill in:** `<database>`, the database name, in each read.

**Hive**

### alert_status

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON a.run_id = r.run_id
```

### run_check

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

### teams

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X50

**Map**

- **Sources:** `job_owners` (job_id, team, owner, dt); `jobs` (job_id, job_name, team, region). Both are typed only, and no query loads them.
- **Steps:** none.
- **Finals:** Table `owners` (job_id, owner, job_name, newest_first), loaded by query `owners`. No other Table's formula reads it, so it is a final, and its rows are the query's: the distinct job_id and owner pairs of job_owners. job_name is XLOOKUP as a LEFT JOIN to jobs; newest_first is RANK.EQ as a descending RANK over job_id.
- **Settings:** `Parameters` and `Keys` are empty Tables, never a source, step or final. No value is typed over a formula, so Keys needs no row.
- **Typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet's text, and the notes in D1 of the Parameters and Keys sheets (cells outside a Table).
- **To fill in:** `<database>`, the database name, in each read.

**Hive**

### owners

```sql
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X59

### Map

- **Sources:** job_runs (typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed columns: job_id, job_name); run_alerts (typed columns: alert_id, run_id, severity, dt). Each is read as `<database>.<table>`.
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, long_runs, failed_mins, not_test); run_alerts (alert_id, run_id, severity, dt, alerts_so_far). Nothing reads either Table but its own formulas.
- **Typed over a formula:** none. The Keys Table is empty.
- **Marks:** none. The blank status in job_runs (run 98) is read only inside the -IFS forms, so it is written as it is and skipped as Excel skips it.
- **Refusals:** none.
- **Left alone:** the Parameters and Keys Tables, which are empty and are never a source, step or final; the notes in D1 on those sheets and the Steps sheet.
- **To fill in:** `<database>` in each query.

### Hive

```sql
SELECT j.job_id, j.job_name,
  COALESCE(lr.long_runs, 0) AS long_runs,
  COALESCE(fm.failed_mins, 0) AS failed_mins,
  COALESCE(nt.not_test, 0) AS not_test
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, COUNT(*) AS long_runs FROM <database>.job_runs WHERE duration_mins >= 20 GROUP BY job_id) lr
  ON j.job_id = lr.job_id
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS failed_mins FROM <database>.job_runs WHERE LOWER(status) LIKE 'f%' GROUP BY job_id) fm
  ON j.job_id = fm.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS not_test FROM <database>.job_runs WHERE (status <> 'TEST' OR status IS NULL) GROUP BY job_id) nt
  ON j.job_id = nt.job_id
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

- **Sources:** region_budgets (typed columns: job_id, budget_cents, region), read as `<database>.region_budgets`.
- **Steps:** none.
- **Finals:** region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region); region_budgets (Total Row) (job_id, budget_cents).
- **Typed over a formula:** none. The Keys Table is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Parameters and Keys Tables, which are empty and are never a source, step or final. In the Total Row, the label "Total" and the empty cells (region, share, above_avg, rank_in_region) get no column.
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

- **Sources:** region_costs (typed columns: job_id, cost_cents, region, dt), read as `<database>.region_costs`.
- **Steps:** none.
- **Finals:** by_region, a summary, with its groups typed in as eu and us and its values read from region_costs (region, total_cents, entries, priciest); by_region (Total Row) (total_cents, entries, priciest).
- **Typed over a formula:** none. The Keys Table is empty.
- **Marks:** none. The blank cost_cents in region_costs (row 29, job 2, eu) sits inside SUMIFS and MAXIFS, so it is written as it is and skipped as Excel skips it; COUNTIFS still counts its row.
- **Refusals:** none.
- **Left alone:** the Parameters and Keys Tables, which are empty and are never a source, step or final. In the Total Row, the label "Total" gets no column.
- **To fill in:** `<database>` in each query.

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
) c ON g.region = c.region
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
  ) c ON g.region = c.region
)
SELECT SUM(total_cents) AS total_cents, SUM(entries) AS entries, MAX(priciest) AS priciest
FROM by_region
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X62

### Map

- **Sources:** team_notes (typed columns: team, note, written_on), read as `<database>.team_notes`.
- **Steps:** none.
- **Finals:** team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short). Nothing reads it but its own formulas.
- **Typed over a formula:** none. The Keys Table is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Parameters and Keys Tables, which are empty and are never a source, step or final.
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

- **Sources:** job_runs (typed columns: run_id, job_id, status, duration_mins, avg_retry_secs), and scheduler_runs (typed columns: run_id, job_id, dt), which scheduled_job reads; each is read as `<database>.<table>`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded). Nothing reads it but its own formulas.
- **Typed over a formula:** none. The Keys Table is empty.
- **Marks:** blank: the status of job_runs run 98 is blank, and succeeds reads it outside an -IFS form or ISBLANK, so it is written as COALESCE(status, ''). The blank avg_retry_secs of run 98 is read only by ISBLANK, so it is written as it is.
- **Refusals:** none.
- **Left alone:** the Parameters and Keys Tables, which are empty and are never a source, step or final. Not a mark: run 99 has no scheduler_runs row, so scheduled_job gives -1 as Excel's XLOOKUP does.
- **To fill in:** `<database>` in the query.

### Hive

```sql
SELECT jr.run_id, jr.job_id, jr.status, jr.duration_mins, jr.avg_retry_secs,
  jr.avg_retry_secs IS NULL AS no_retry,
  FLOOR(jr.duration_mins / 4) AS quarters,
  LEAST(jr.duration_mins, 25) AS capped,
  VAR_SAMP(jr.duration_mins) OVER () AS variance,
  SUM(jr.duration_mins * jr.job_id) OVER () AS weighted,
  COALESCE(sr.job_id, -1) AS scheduled_job,
  CONCAT('run ', jr.run_id) AS label,
  INSTR(LOWER(COALESCE(jr.status, '')), LOWER('cess')) > 0 AS succeeded
FROM <database>.job_runs jr
LEFT JOIN <database>.scheduler_runs sr
  ON jr.run_id = sr.run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X64

### Map

- **Sources**: `jobs` (job_id, job_name, team, region); `region_costs` (job_id, cost_cents, region, dt). Each is a typed Table that no query loads, read from `<database>.<table>`.
- **Steps**: none. No query names another query, and no Table's formula reads a Table.
- **Finals**:
  - `picked_costs` (job_id, cost_cents, region, size), loaded by query `picked_costs`, which reads `region_costs`.
  - `costed_jobs` (job_id, job_name, team, region), loaded by query `costed_jobs`, which reads `jobs` and `region_costs`.
  - `costs_filled` (job_id, cost_cents, dt, day), loaded by query `costs_filled`, which reads `region_costs`.
- **Values typed over a formula**: none. The workbook has no formula columns.
- **Marks**: none.
- **Blank**: `region_costs` row 29 (job 2, 20260924) has a blank cost_cents. `costs_filled` makes it 0 (`COALESCE(cost_cents, 0)`, from `Table.ReplaceValue`). `picked_costs` drops it (`cost_cents IS NOT NULL`, from the `<> null` filter), and `costed_jobs` has no cost_cents.
- **Refusals**: none.
- **Left alone**: `Parameters` and `Keys` (both empty; no formula uses a fixed value, so no Keys row is needed), and the Steps sheet.
- **To fill in**: `<database>`, in each FROM and JOIN.

### Hive

```sql
-- final: picked_costs
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

```sql
-- final: costed_jobs
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT j.job_name LIKE 'n%'
```

```sql
-- final: costs_filled
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt, SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X65

### Map

- **Sources**: `jobs` (job_id, job_name, team, region); `region_budgets` (job_id, budget_cents, region); `job_owners` (job_id, team, owner, dt); `scheduler_runs` (run_id, job_id, dt); `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Each is a typed Table that no query loads, read from `<database>.<table>`.
- **Steps**: none.
- **Finals**:
  - `team_regions` (team, region), loaded by query `team_regions`.
  - `budget_places` (job_id, budget_cents, region, place), loaded by query `budget_places`.
  - `jobs_per_team` (team, jobs), loaded by query `jobs_per_team`.
  - `ran_as_scheduled` (run_id, dt), loaded by query `ran_as_scheduled`.
  - `run_measures` (run_id, job_id, measure, amount), loaded by query `run_measures`.
- **Values typed over a formula**: none. The workbook has no formula columns.
- **Marks**:
  - `team_regions`: `Table.Sort` by team has no FirstN or index after it, so the order is dropped and the block has no ORDER BY.
  - `ran_as_scheduled`: `Table.Distinct` over an inner join on every column, its new column removed, is INTERSECT.
  - `run_measures`: row 98's blank avg_retry_secs is dropped by the unpivot (`avg_retry_secs IS NOT NULL`), as M drops it.
- **Refusals**: none.
- **Left alone**: `Parameters` and `Keys` (both empty), and the Steps sheet.
- **To fill in**: `<database>`, in each FROM and JOIN.

### Hive

```sql
-- final: team_regions
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

```sql
-- final: budget_places
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

```sql
-- final: jobs_per_team
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

```sql
-- final: ran_as_scheduled
SELECT run_id, dt FROM <database>.scheduler_runs
INTERSECT
SELECT run_id, dt FROM <database>.job_runs
```

```sql
-- final: run_measures
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

- **Sources**: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), a typed Table that no query loads, read from `<database>.job_runs`.
- **Steps**: none. The query `ok_runs` is the Table `ok_runs`'s own query, and no other piece reads it.
- **Finals**:
  - `ok_runs` (run_id, job_id, duration_mins, dt, running, share), loaded by query `ok_runs`, which reads `job_runs`.
  - `ok_runs (Total Row)` (duration_mins), the Total Row's one total cell.
- **Values typed over a formula**: none. Every row of `running` and `share` holds its formula.
- **Marks**: none.
- **Conversions named**: `running` is the running-total form of SUMIFS over its own Table (`"<="&dt`, ties included), written as SUM OVER with RANGE. `share` is `duration_mins / SUM(duration_mins) OVER ()`, the whole-column SUM by file 11.
- **Refusals**: none.
- **Left alone**: `Parameters` and `Keys` (both empty), and the Steps sheet.
- **To fill in**: `<database>`, in each FROM.

### Hive

```sql
-- final: ok_runs
SELECT run_id, job_id, duration_mins, dt,
  SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

```sql
-- final: ok_runs (Total Row)
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins, dt,
    SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,
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

- **Sources**: `jobs` (job_id, job_name, team, region); `region_budgets` (job_id, budget_cents, region). Each is a typed Table that no query loads, read from `<database>.<table>`.
- **Steps**:
  - `region_costs` (job_id, cost_cents, region, dt, job_name, budget, over_budget, running_cost). It has formula columns and is read by the formulas of `job_totals` and by query `late_costs`, so it is a step. Its typed columns are read from `<database>.region_costs`, and it is a CTE in each final that reads it.
- **Finals**:
  - `job_totals` (job_id, total_cents, over_count). Nothing else reads it. Its only typed column is job_id, which its SUMIFS and COUNTIFS match on, so it is a summary: a GROUP BY of `region_costs`, with its typed job_ids kept.
  - `job_totals (Total Row)` (total_cents, over_count), the Total Row's two total cells.
  - `late_costs` (job_id, dt, running_cost), loaded by query `late_costs`, which reads the step `region_costs`. Its filter sits outside the step's SELECT because running_cost is a window.
- **Values typed over a formula**: none.
- **Marks**:
  - Blank: `region_costs` row 29 (job 2, 20260924) has a blank cost_cents. `over_budget` reads it as `COALESCE(cost_cents, 0) > budget`. `running_cost`, `total_cents` and `over_count` are -IFS forms, so cost_cents is written as it is and SUM skips the blank.
  - Summary: job_totals' typed job_ids 1, 2 and 3 are typed in as its groups; `region_costs` is read.
- **Refusals**: none.
- **Left alone**: `Parameters` and `Keys` (both empty), and the Steps sheet.
- **To fill in**: `<database>`, in each FROM and JOIN.

### Hive

```sql
-- final: job_totals
WITH region_costs AS (
  SELECT rc.job_id, rc.cost_cents, rc.region, rc.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(rc.cost_cents, 0) > b.budget_cents AS over_budget,
    SUM(rc.cost_cents) OVER (PARTITION BY rc.job_id ORDER BY rc.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
  FROM <database>.region_costs rc
  LEFT JOIN <database>.jobs j ON rc.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON rc.job_id = b.job_id
)
SELECT j.job_id, COALESCE(c.total_cents, 0) AS total_cents, COALESCE(c.over_count, 0) AS over_count
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, SUM(cost_cents) AS total_cents,
    COUNT(CASE WHEN over_budget = TRUE THEN 1 END) AS over_count
  FROM region_costs
  GROUP BY job_id
) c ON j.job_id = c.job_id
```

```sql
-- final: job_totals (Total Row)
WITH region_costs AS (
  SELECT rc.job_id, rc.cost_cents, rc.region, rc.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(rc.cost_cents, 0) > b.budget_cents AS over_budget,
    SUM(rc.cost_cents) OVER (PARTITION BY rc.job_id ORDER BY rc.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
  FROM <database>.region_costs rc
  LEFT JOIN <database>.jobs j ON rc.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON rc.job_id = b.job_id
),
job_totals AS (
  SELECT j.job_id, COALESCE(c.total_cents, 0) AS total_cents, COALESCE(c.over_count, 0) AS over_count
  FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
  LEFT JOIN (
    SELECT job_id, SUM(cost_cents) AS total_cents,
      COUNT(CASE WHEN over_budget = TRUE THEN 1 END) AS over_count
    FROM region_costs
    GROUP BY job_id
  ) c ON j.job_id = c.job_id
)
SELECT SUM(total_cents) AS total_cents, SUM(over_count) AS over_count
FROM job_totals
```

```sql
-- final: late_costs
WITH region_costs AS (
  SELECT rc.job_id, rc.cost_cents, rc.region, rc.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(rc.cost_cents, 0) > b.budget_cents AS over_budget,
    SUM(rc.cost_cents) OVER (PARTITION BY rc.job_id ORDER BY rc.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
  FROM <database>.region_costs rc
  LEFT JOIN <database>.jobs j ON rc.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON rc.job_id = b.job_id
)
SELECT job_id, dt, running_cost
FROM region_costs
WHERE running_cost > 1500
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X70

### Map

- **Sources**: `jobs` (job_id, job_name, team, region); `job_owners` (job_id, team, owner, dt); `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt). Each is a typed Table that no query loads, read from `<database>.<table>`.
- **Steps**:
  - `staffed`, the connection-only query. Query `owner_load` names it, so it is a CTE in each final that reads it.
  - `owner_load`, the query (not the Table). Query `busiest_owner` names it in `Table.Sort(owner_load, ...)`, so it is a CTE in `busiest_owner`. Its Table is a separate final.
- **Finals**:
  - `owner_load` (owner, total_mins, runs, avg_mins), the Table loaded by query `owner_load`. No formula of another Table reads it, so its rows are the query's, with `avg_mins` added as `total_mins / runs`.
  - `owner_load (Total Row)` (runs), the Total Row's one total cell.
  - `busiest_owner` (owner, total_mins, runs), loaded by query `busiest_owner`.
- **Values typed over a formula**: none.
- **Marks**: none.
- **Conversions named**: the blank owner of job 4 in `job_owners` is dropped by `owner IS NOT NULL`, from M's `<> null`. `owner_load` counts every job_runs row, with no status filter, as M does.
- **Refusals**: none.
- **Left alone**: `Parameters` and `Keys` (both empty), and the Steps sheet.
- **To fill in**: `<database>`, in each FROM and JOIN.

### Hive

```sql
-- final: owner_load
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
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
-- final: owner_load (Total Row)
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON j.job_id = o.job_id
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
-- final: busiest_owner
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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X73

### Map

- **Sources:** `<database>.region_budgets` (job_id, budget_cents, region) and `<database>.jobs` (job_id, job_name, team, region). Both are typed-only Tables that no query loads.
- **Steps:** query `eu_budgets`, because query `eu_count`'s M names it (`Table.Group(eu_budgets, ...)`). It is a CTE in the final `eu_count` only. Columns: job_id, budget_cents, region, job_name.
- **Finals:**
  - Table `eu_budgets` (job_id, budget_cents, region, job_name, dollars). Its query loads it, and no other Table's formula reads it, so its rows are the query's.
  - Table `eu_count` (region, jobs, total_cents). Query `eu_count` loads it, and nothing reads it.
- **Settings:** Parameters and Keys are both empty. They are never a source, step or final, and no formula reads them.
- **Values typed over a formula:** none. The `dollars` formula is the same on all three rows.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet (the workbook's own instructions).
- **To fill in:** `<database>`, in each read of `region_budgets` and `jobs`.

### Hive

```sql
-- final eu_budgets
SELECT r.job_id, r.budget_cents, r.region, j.job_name, r.budget_cents / 100 AS dollars
FROM <database>.region_budgets r
JOIN <database>.jobs j ON r.job_id = j.job_id
WHERE r.region = 'eu'
```
```sql
-- final eu_count
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

- **Sources:** `<database>.job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read in full as typed. `<database>.run_alerts` (alert_id, run_id, severity, dt), the typed columns of the Table `run_alerts`.
- **Steps:** Table `run_alerts` (alert_id, run_id, severity, dt, status, job_id, alerts_so_far). It has formula columns, and by_status's formula and query late_alerts both read it, so it is a step. It is a CTE in both finals below.
- **Finals:**
  - Table `by_status` (status, alerts). Its only typed column, status, is the one its COUNTIFS matches on, so it is a summary: a GROUP BY of `run_alerts`, with its typed groups FAILED and SUCCESS kept. Nothing reads it.
  - Table `late_alerts` (alert_id, run_id, alerts_so_far). Query `late_alerts` loads it, and nothing reads it.
- **Queries:** `late_alerts` loads the final Table `late_alerts`. It is named by no other query, so it is not a step.
- **Settings:** Parameters and Keys are both empty and are neither a source, step nor final. Keys needs no row, as no value is typed over a formula.
- **Values typed over a formula:** none. Every formula is the same on each row.
- **Marks:**
  - **blank:** job_runs' run 98 has a blank `status`, and the `status` formula reads that column. So the step writes `COALESCE(jr.status, '')`. No alert sits on run 98, so no sample row changes.
- **Refusals:** none.
- **Left alone:** none. The `alerts_so_far` running count is written with ties included, as Excel's COUNTIFS gives.
- **To fill in:** `<database>`, in each read of `run_alerts` and `job_runs`.

### Hive

```sql
-- final by_status
WITH run_alerts AS (
  SELECT r.alert_id, r.run_id, r.severity, r.dt,
    COALESCE(jr.status, '') AS status,
    jr.job_id AS job_id,
    COUNT(*) OVER (ORDER BY r.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts r
  LEFT JOIN <database>.job_runs jr ON r.run_id = jr.run_id
)
SELECT s.status, COALESCE(c.alerts, 0) AS alerts
FROM (SELECT 'FAILED' AS status UNION ALL SELECT 'SUCCESS') s
LEFT JOIN (SELECT status, COUNT(*) AS alerts FROM run_alerts GROUP BY status) c
  ON s.status = c.status
```
```sql
-- final late_alerts
WITH run_alerts AS (
  SELECT r.alert_id, r.run_id, r.severity, r.dt,
    COALESCE(jr.status, '') AS status,
    jr.job_id AS job_id,
    COUNT(*) OVER (ORDER BY r.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts r
  LEFT JOIN <database>.job_runs jr ON r.run_id = jr.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM run_alerts
WHERE alerts_so_far > 5
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X77

### Map

- **Sources:** `<database>.run_alerts` (alert_id, run_id, severity, dt). It is a typed-only Table that no query loads.
- **Steps:** query `high_alerts`, because query `high_per_day`'s M names it (`Table.Group(high_alerts, ...)`). It is a CTE in the final `high_per_day` only. Columns: alert_id, run_id, dt.
- **Finals:**
  - Table `high_alerts` (alert_id, run_id, dt, late_run). Query `high_alerts` loads it, and no other Table's formula reads it. Its `late_run` formula reads its own row, which does not count.
  - Table `high_per_day` (dt, alerts). Query `high_per_day` loads it, and nothing reads it.
- **Settings:** Parameters and Keys are both empty and are neither a source, step nor final.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>`, in each read of `run_alerts`.

### Hive

```sql
-- final high_alerts
SELECT alert_id, run_id, dt, run_id > 100 AS late_run
FROM <database>.run_alerts
WHERE severity = 'high'
```
```sql
-- final high_per_day
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

- **Sources:** `<database>.region_costs` (job_id, cost_cents, region, dt). It is a typed-only Table that no query loads. `region` is not read by any final, since the query drops it.
- **Steps:** query `known_costs`, because query `cost_per_job`'s M names it (`Table.Group(known_costs, ...)`). It keeps job_id, cost_cents and dt, and filters out a blank cost_cents as M's `<> null` does. It is a CTE in the final `cost_per_job` only.
- **Finals:**
  - Table `known_costs` (job_id, cost_cents, dt, dollars). Query `known_costs` loads it, and no other Table's formula reads it. Its `dollars` formula reads its own row, which does not count.
  - `known_costs (Total Row)` (cost_cents). The Total Row's only total is the `SUBTOTAL(109, ...)` under cost_cents. The label "Total" and the empty cells get no column.
  - Table `cost_per_job` (job_id, total_cents). Query `cost_per_job` loads it, and nothing reads it.
- **Settings:** Parameters and Keys are both empty and are neither a source, step nor final.
- **Values typed over a formula:** none. Every `dollars` cell holds the formula.
- **Marks:** none. The blank cost_cents row (job 2, 20260924) drops out of the `IS NOT NULL` filter, as M drops it, so no formula sees a blank and no COALESCE is written.
- **Refusals:** none.
- **Left alone:** `dt` is kept as typed. No formula reads it as a date, so the text-date CONCAT is not applied.
- **To fill in:** `<database>`, in each read of `region_costs`.

### Hive

```sql
-- final known_costs
SELECT job_id, cost_cents, dt, cost_cents / 100 AS dollars
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL
```
```sql
-- final known_costs (Total Row)
WITH known_costs AS (
  SELECT job_id, cost_cents, dt, cost_cents / 100 AS dollars
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT SUM(cost_cents) AS cost_cents
FROM known_costs
```
```sql
-- final cost_per_job
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

## X80

### Map

- **Sources:** `<database>.job_runs` (run_id, job_id, duration_mins), the typed columns of the Table `job_runs`.
- **Steps:** none.
- **Finals:** Table `job_runs` (run_id, job_id, duration_mins, look). No query loads it and nothing else reads it, so it is a final. Its `look` formula reads its own row, which does not count.
- **Settings:** Parameters and Keys are both empty and are neither a source, step nor final.
- **Values typed over a formula:** none. All nine `look` formulas are the same.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** none.
- **To fill in:** `<database>`, in the read of `job_runs`.

### Hive

```sql
-- final job_runs
SELECT run_id, job_id, duration_mins,
  IF((duration_mins > 20 AND job_id <> 3) OR NOT (job_id = 2), 'look', 'fine') AS look
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X83

### Map

- **Sources:** job_runs, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. No query loads it and it has only typed columns, so it is a source.
- **Steps:** none.
- **Finals:** by_day (dt, kept_runs, short_mins, success_or_failed), a summary. Its only typed column, dt, is the one its COUNTIFS and SUMIFS match on, so its final is a GROUP BY of job_runs. Its typed rows are kept as the summary's groups: 2026-09-23 and 2026-09-24, typed in. Nothing else reads by_day, so it is a final.
- **Each value typed over a formula:** none. Keys has no row.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables, never a source, step or final. The Steps sheet holds instructions, not a Table.
- **To fill in:** `<database>`, in each read of job_runs.

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

- **Sources:** job_runs, its typed columns: run_id, job_id, status, duration_mins. Its formula columns read its own rows, not another Table, so they do not make it a step.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, flag, job2_short, failed_or_test_mins). It has formula columns and nothing else reads it, so it is a final. Its typed columns are read from `<database>.job_runs`.
- **Each value typed over a formula:** none. Keys has no row.
- **Marks:**
  - blank: failed_or_test_mins reads status, which is blank in the sample (run_id 98), so it is written as COALESCE(status, '') inside the SUMPRODUCT's condition.
  - job2_short and failed_or_test_mins read the whole column, so each is written as a window over all rows with OVER (), as each row shows the same total.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty settings Tables, never a source, step or final.
- **To fill in:** `<database>`, in the read of job_runs.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins,
  IF((job_id = 2 AND duration_mins < 20) OR (job_id = 3 AND NOT (duration_mins >= 30)), 'review', '') AS flag,
  COUNT(CASE WHEN job_id = 2 AND duration_mins < 20 THEN 1 END) OVER () AS job2_short,
  SUM(CASE WHEN COALESCE(status, '') IN ('FAILED', 'TEST') THEN duration_mins ELSE 0 END) OVER () AS failed_or_test_mins
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
