date: 2026-11-01
arm: C
model: haiku
files: 18-held

## X21

### Map
- **Sources:** region_budgets (job_id, budget_cents, region), its typed columns.
- **Steps:** none.
- **Finals:** region_budgets (job_id, budget_cents, region, budget_dollars, with_margin). No query loads it and no other Table reads it, so it is a final of its own, with its formula columns.
- **Value typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table). Parameters and Keys are empty: no fixed value is read, and no Keys row is needed.
- **To fill in:** `<database>`, in the FROM.

### Hive

```sql
SELECT job_id, budget_cents, region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets
```

**Next:** Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X22

### Map
- **Sources:** jobs (job_id, job_name, team), its typed columns.
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, team, is_finance, ratio). No query loads it and no other Table reads it, so it is a final of its own, with its formula columns.
- **Value typed over a formula:** none.
- **Marks:** text equality. Excel's `=` ignores case and Hive's does not, so `team = 'finance'` in is_finance is written as it is; a team typed as "Finance" would count differently. The sample's teams are all lowercase.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table). Parameters and Keys are empty: no fixed value is read, and no Keys row is needed.
- **To fill in:** `<database>`, in the FROM.

### Hive

```sql
SELECT job_id, job_name, team,
  IF(team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(job_id / (job_id - 2), 0) AS ratio
FROM <database>.jobs
```

**Next:** Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X23

### Map
- **Sources:** job_runs (run_id, status, avg_retry_secs), its typed columns.
- **Steps:** none.
- **Finals:** job_runs (run_id, status, avg_retry_secs, label, risky). No query loads it and no other Table reads it, so it is a final of its own, with its formula columns.
- **Value typed over a formula:** none; label and risky are formulas in every row.
- **Marks:**
  - Blank: row 98 has a blank status and a blank avg_retry_secs. label reads status, so it is COALESCE(status, ''); risky reads status and avg_retry_secs, so they are COALESCE(status, '') and COALESCE(avg_retry_secs, 0). Each matches Excel's blank.
  - Text equality: Excel's `=` and SWITCH ignore case and Hive's do not. "SUCCESS", "FAILED" and the other values are written as they are; a status typed in another case would differ.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table). Parameters and Keys are empty: no fixed value is read, and no Keys row is needed.
- **To fill in:** `<database>`, in the FROM.

### Hive

```sql
SELECT run_id, status, avg_retry_secs,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label,
  (COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs
```

**Next:** Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X24

### Map
- **Sources:** team_notes (team, note, written_on), its typed columns.
- **Steps:** none.
- **Finals:** team_notes (team, note, written_on, first_word, shout, month, tens_of_chars). No query loads it and no other Table reads it, so it is a final of its own, with its formula columns.
- **Value typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table). Parameters and Keys are empty: no fixed value is read, and no Keys row is needed.
- **To fill in:** `<database>`, in the FROM.

### Hive

```sql
SELECT team, note, written_on,
  SUBSTR(note, 1, INSTR(note, ' ') - 1) AS first_word,
  UPPER(team) AS shout,
  MONTH(written_on) AS month,
  ROUND(LENGTH(note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes
```

**Next:** Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X25

### Map
- **Sources:** Costs (Job, Cost (cents) as `<cost_cents>`, Region, Day Key as `<day_key>`), its typed columns; Budgets (Job, Budget, Region), its typed columns.
- **Steps:** none.
- **Finals:** Costs (Job, `<cost_cents>`, Region, `<day_key>`, Day), with Day as its formula column; Budgets (Job, Budget, Region, Dollars), with Dollars as its formula column. No query loads either Table and no other Table reads them.
- **Value typed over a formula:** none.
- **Marks:**
  - Day in Costs: Day Key is a date held as text (such as 20260911), so Day is written as CONCAT of its parts, giving text such as 2026-09-11, not a date. Check Day's type in the Toolbox.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys (cells outside a Table). Parameters and Keys are empty: no fixed value is read, and no Keys row is needed.
- **To fill in:** `<database>`, in each FROM; `<cost_cents>` for the Cost (cents) column; `<day_key>` for the Day Key column.

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

**Next:** Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X26

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), typed only, no formula. Its rows are read from `<database>.job_runs`.
- **Steps:** none.
- **Finals:** `run_alerts` (alert_id, run_id, severity, job_id, status, avg_mins). Its formula columns are job_id (XLOOKUP on job_runs), status (VLOOKUP column 3 of job_runs, exact) and avg_mins (AVERAGEIFS on job_runs' job_id). Nothing reads it, so it is a final.
- **Values typed over a formula:** none, so the Keys row is not needed.
- **Marks:** blank. job_runs' status is blank at run 98, and the status formula reads that column, so status is written `COALESCE(jr.status, '')` and named blank. Excel gives 0 for a blank; this gives an empty string.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, which are empty settings and not pieces (no formula reads Parameters). The D1 notes and the Steps sheet are cells outside a Table, left alone.
- **To fill in:** `<database>`, the Dev Database name, in each FROM and JOIN.

### Hive

```sql
SELECT
  ra.alert_id,
  ra.run_id,
  ra.severity,
  jr.job_id AS job_id,
  COALESCE(jr.status, '') AS status,
  by_job.avg_mins AS avg_mins
FROM <database>.run_alerts ra
LEFT JOIN <database>.job_runs jr
  ON ra.run_id = jr.run_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) by_job
  ON jr.job_id = by_job.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X27

### Map

- **Sources:** `jobs` (job_id, job_name, team, region), typed only, no formula. Its rows are read from `<database>.jobs`.
- **Steps:** none.
- **Finals:** `by_team` (team, jobs_in_team, last_job_id, last_job_name). It is a summary: its only typed column, team, is the one its COUNTIFS match on. Its final is a GROUP BY of jobs, with its three typed rows kept as literals, as the summary example does.
- **Values typed over a formula:** none, so the Keys row is not needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, which are empty settings and not pieces. The D1 notes and the Steps sheet are cells outside a Table, left alone.
- **To fill in:** `<database>`, the Dev Database name, in each FROM and JOIN.

### Hive

```sql
SELECT
  t.team AS team,
  COALESCE(n.jobs_in_team, 0) AS jobs_in_team,
  COALESCE(m.last_job_id, 0) AS last_job_id,
  j.job_name AS last_job_name
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (
  SELECT team, COUNT(*) AS jobs_in_team FROM <database>.jobs GROUP BY team
) n
  ON t.team = n.team
LEFT JOIN (
  SELECT team, MAX(job_id) AS last_job_id FROM <database>.jobs GROUP BY team
) m
  ON t.team = m.team
LEFT JOIN <database>.jobs j
  ON COALESCE(m.last_job_id, 0) = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X28

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), typed only, no formula.
- **Steps:** none.
- **Finals:** `jobs` (job_id, job_name, ok_mins). Its one formula column is ok_mins (SUMIFS on job_runs). Nothing reads it, so it is a final.
- **Values typed over a formula:** jobs' ok_mins at job_id 3 (report_build), typed as 99. The Keys row names jobs with job_id, so the value is a CASE matched on job_id = 3.
- **Marks:** none. The blank status at run 98 sits inside a SUMIFS, which skips a blank, so it is written as it is, not with COALESCE.
- **Refusals:** none.
- **Left alone:** Parameters (empty) and Keys (a settings row, not a piece). The D1 notes and the Steps sheet are cells outside a Table, left alone.
- **To fill in:** `<database>`, the Dev Database name, in each FROM and JOIN.

### Hive

```sql
SELECT
  j.job_id AS job_id,
  j.job_name AS job_name,
  CASE WHEN j.job_id = 3 THEN 99 ELSE COALESCE(s.ok_mins, 0) END AS ok_mins
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS ok_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
  GROUP BY job_id
) s
  ON j.job_id = s.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X29

### Map

- **Sources:** none. The only Table with data is region_budgets, which is a final.
- **Steps:** none.
- **Finals:** `region_budgets` (job_id, budget_cents, region, in_dollars, pointer). Its formula columns are in_dollars and pointer. Nothing reads it, so it is a final. Its rows are read from `<database>.region_budgets`.
- **Values typed over a formula:** in_dollars at job_id 3 (budget_cents 350, region us), typed as 5. Keys is empty, so there is no Keys row for region_budgets. The CASE therefore matches on every typed column of that row: job_id, budget_cents and region.
- **Marks:** none. The Parameters read, cents_per_dollar, is taken as its value, 100, typed in as the divisor.
- **Refusals:** pointer, `=INDIRECT("A"&ROW())`, is refused: INDIRECT reads by address and ROW() by a row's place on the sheet. It is written `NULL AS pointer`.
- **Left alone:** Keys (empty). Parameters is read in as its value, not left alone. The D1 notes and the Steps sheet are cells outside a Table, left alone.
- **To fill in:** `<database>`, the Dev Database name, in the FROM.

### Hive

```sql
SELECT
  rb.job_id AS job_id,
  rb.budget_cents AS budget_cents,
  rb.region AS region,
  CASE
    WHEN rb.job_id = 3 AND rb.budget_cents = 350 AND rb.region = 'us' THEN 5
    ELSE rb.budget_cents / 100
  END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets rb
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X30

### Map

- **Sources:** none.
- **Steps:** none.
- **Finals:** `scheduler_runs` (run_id, job_id, dt, day, prev_run, jitter). Its formula columns are day, prev_run and jitter. Nothing reads it as a formula or query (the PivotTable is left alone), so it is a final. Its rows are read from `<database>.scheduler_runs`.
- **Values typed over a formula:** none, so the Keys row is not needed.
- **Marks:** day. `RIGHT(dt, 2)` is written `SUBSTR(dt, -2)`, as dt is held as text, shown as 2026-09-23. Check dt's type before the run: if the cells hold true dates, Excel's RIGHT reads the date's serial number, not the day.
- **Refusals:** prev_run, `=OFFSET(...)`, is refused: OFFSET moves by address from another cell, and is written `NULL AS prev_run`. jitter, `=RANDBETWEEN(1,5)`, is refused: it is random, and is written `NULL AS jitter`.
- **Left alone:** the bar chart on sheet "Summary" (charts), the PivotTable on sheet "Pivot" (PivotTables), Parameters and Keys (empty settings), and the D1 notes and Steps sheet (cells outside a Table).
- **To fill in:** `<database>`, the Dev Database name, in the FROM.

### Hive

```sql
SELECT
  run_id,
  job_id,
  dt,
  SUBSTR(dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X31

**Map**

- Sources: jobs (typed columns job_id, team), read as `<database>.jobs`.
- Steps: none.
- Finals: jobs (job_id, team, bump, tag, scaled, boosted).
- Values typed over a formula: none. Parameters and Keys are empty, so no Keys row is needed.
- Marks: boosted reads the defined name boost, which is a cell outside a Table (Summary!B2, value 10). It is written as its value, 10. Move it into Parameters.
- Refusals:
  - bump: `NULL AS bump`. Its formula reads its own column (circular).
  - tag: `NULL AS tag`. Its formula calls the defined name TAG, a LAMBDA (a defined name holding a formula).
  - scaled: `NULL AS scaled`. Its formula reads cell D4 on Summary by address, a cell outside a Table that is not a defined name.
- Left alone: the Summary sheet's cells outside a Table (B2 is read through boost; D4 is refused). Parameters and Keys are empty, never a source, step or final.
- To fill in: `<database>` in the block below.

**Hive**

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

- Sources: jobs (typed columns job_id, job_name, team, region), read as `<database>.jobs`.
- Steps: job_runs (its job_name formula reads jobs, and by_name's formula reads job_runs). It is a CTE in by_name's block. Columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name.
- Finals: by_name (job_name, runs), a summary: a GROUP BY of job_runs, typed rows kept.
- Values typed over a formula: none. Parameters and Keys are empty, so no Keys row is needed.
- Marks: job_runs' job_name is VLOOKUP with TRUE, which is approximate. It is written as the exact match on job_id = jobs.job_id, taking jobs' column 2 (job_name). Named here.
- Refusals: none.
- Left alone: the blank status and avg_retry_secs on run 98. No formula reads them, so they stay blank (NULL in Hive).
- To fill in: `<database>` in the block below.

**Hive**

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT n.job_name, COALESCE(c.runs, 0) AS runs
FROM (SELECT 'invoice_sync' AS job_name UNION ALL SELECT 'nightly_load' UNION ALL SELECT 'report_build') n
LEFT JOIN (SELECT job_name, COUNT(*) AS runs FROM job_runs GROUP BY job_name) c
  ON n.job_name = c.job_name
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X33

**Map**

- Sources: job_runs, outside the workbook. The query reads the table named by Sql.Database("dwh01", "ops") with Item "job_runs", written as `<database>.job_runs`. Named here for the user to check.
- Steps: none.
- Finals: slow_runs (run_id, duration_mins, over_by).
- Values typed over a formula: none. Parameters and Keys are empty.
- Marks:
  - The Sql.Database read of ops.job_runs from dwh01 is written as `<database>.job_runs`. Check that this is the same table.
  - `[status] <> "TEST"`: M keeps a null status and Hive does not, so it is written as `(status <> 'TEST' OR status IS NULL)`.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>` in the block below.

**Hive**

```sql
SELECT run_id, duration_mins, duration_mins - 20 AS over_by
FROM <database>.job_runs
WHERE duration_mins >= 20 AND (status <> 'TEST' OR status IS NULL)
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X34

**Map**

- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (typed columns job_id, job_name, team, region), read as `<database>.job_runs` and `<database>.jobs`.
- Steps: runs_with_team, a query read by query team_totals. It is a CTE in team_totals' block. Its NestedJoin (LeftOuter on job_id) is a LEFT JOIN of jobs, expanded to team. Columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt, team. It is connection only, and it is kept because it is read.
- Finals: team_totals (team, total_mins, longest).
- Values typed over a formula: none.
- Marks: none.
- Refusals: none.
- Left alone: none.
- To fill in: `<database>` in the block below.

**Hive**

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

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X35

**Map**

- Sources: job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt) and scheduler_runs (typed columns run_id, job_id, dt), read as `<database>.job_runs` and `<database>.scheduler_runs`.
- Steps: none.
- Finals: recent (run_id, dt).
- Values typed over a formula: none.
- Marks: none.
- Refusals:
  - Query rates: `Web.Contents("https://rates.example.com/today.json")` is a web source. It is left out and named here. It is connection only, loads nothing, and nothing reads it.
- Left alone: none.
- To fill in: `<database>` in the block below.

**Hive**

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

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X36

### Map

**Sources**
- `run_alerts` (alert_id, run_id, severity, dt): a Table of typed columns only, read by query `severity_by_day` and by the `alerts` formula of `job_runs`.
- `job_runs` (run_id, status): the typed columns of Table `job_runs`, read by its own final.

**Steps**
- None. No Table's formula reads a Table that is a step, and no query is read by another query.

**Finals**
- `job_runs` (run_id, status, alerts): a Table with a formula column that no query loads and nothing else reads, so it is a final. `alerts` counts the `run_alerts` rows whose run_id matches.
- `severity_by_day` (dt, high, low): loaded by Power Query `severity_by_day`, and no other Table's formula reads it, so the Table is a final with the query's rows. The query is not read by another query, so it is not a step.

**Typed over a formula**
- None. Every `alerts` cell holds the formula, so Keys needs no row.

**Marks**
- Table.Pivot in query `severity_by_day`: the columns `high` and `low` are fixed to the severities in the sample (high, low). A severity that appears later gets no column.

**Refused**
- None.

**Left alone**
- Parameters and Keys: both empty, read by no formula, so neither is a source, step or final.

**To fill in**
- `<database>`, in both finals.

### Hive

#### job_runs

```sql
SELECT j.run_id, j.status, COALESCE(c.n, 0) AS alerts
FROM <database>.job_runs j
LEFT JOIN (SELECT run_id, COUNT(*) AS n FROM <database>.run_alerts GROUP BY run_id) c
  ON j.run_id = c.run_id
```

#### severity_by_day

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
- `Owners` (Job No, Team Name, Owner, Day): the typed columns of Table `Owners`, read by its own final.

**Steps**
- None.

**Finals**
- `Owners` (Job No, Team Name, Owner, Day, Is Ana): a Table with a formula column that no query loads and nothing else reads, so it is a final. `Is Ana` is `IF(Owner = "ana", 1, 0)` on its own row.

**Typed over a formula**
- None. All 56 `Is Ana` cells hold the formula, so Keys needs no row.

**Marks**
- blank: `Owner` is blank on the web rows, and `Is Ana` reads it, so the formula reads `COALESCE(Owner, '')`. Excel gives 0 on those rows, and so does this.

**Refused**
- None.

**Left alone**
- Parameters and Keys: both empty.

**To fill in**
- `<database>`, `<job_no>` (header Job No), `<team_name>` (header Team Name), `<is_ana>` (header Is Ana).

### Hive

#### Owners

```sql
SELECT <job_no>, <team_name>, Owner, Day, IF(COALESCE(Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X38

### Map

**Sources**
- `jobs` (job_id, job_name, team, region): the typed columns of Table `jobs`, read by the `region` formula of `job_runs`.
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs): the typed columns of Table `job_runs`, read by its own final.

**Steps**
- None.

**Finals**
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost): a Table with formula columns that no query loads and nothing else reads, so it is a final. `region` is the jobs lookup on job_id; `region_mins` is the sum of duration_mins over the same region; `retry_cost` is `(avg_retry_secs + duration_mins) * 2`.

**Typed over a formula**
- `retry_cost` on run 102 (sample row 8) is typed as 1, where the formula would give 52. Keys holds job_runs with run_id, so the CASE matches on `run_id = 102`.

**Marks**
- blank: `avg_retry_secs` is blank on run 98 (sample row 5), and `retry_cost` reads it, so the formula reads `COALESCE(avg_retry_secs, 0)`. Excel reads the blank as 0, which gives 30 on that row.

**Refused**
- None.

**Left alone**
- Parameters (empty) and Keys (job_runs, run_id, which the typed-over value uses). Neither is a source, step or final.

**To fill in**
- `<database>`.

### Hive

#### job_runs

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  j.region AS region,
  SUM(r.duration_mins) OVER (PARTITION BY j.region) AS region_mins,
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
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): the typed columns of Table `job_runs`, read by query `ok_runs`.
- `jobs` (job_id, job_name, team, region): the typed columns of Table `jobs`, read by the `job_name` formula of `ok_runs`.

**Steps**
- None. Query `ok_runs` is read by no query, and Table `ok_runs` is read by no other Table's formula.

**Finals**
- `ok_runs` (run_id, job_id, duration_mins, job_name, share, noise): loaded by Power Query `ok_runs`, and no other Table's formula reads it, so the Table is a final with the query's rows (runs 95, 96, 101, 103, 104). The query's steps Source, Succeeded and Kept become the `succeeded` CTE and the SELECT list. `job_name` is the jobs lookup on job_id. `share` is duration_mins over the sum of duration_mins for its job_id among these rows.

**Typed over a formula**
- None.

**Marks**
- None.

**Refused**
- `noise` (`=RAND()`): written as `NULL AS noise`. RAND gives a new number on every calculation, so no Hive gives the same values.

**Left alone**
- Parameters and Keys: both empty.

**To fill in**
- `<database>`.

### Hive

#### ok_runs

```sql
WITH succeeded AS (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT s.run_id, s.job_id, s.duration_mins, j.job_name AS job_name,
  s.duration_mins / SUM(s.duration_mins) OVER (PARTITION BY s.job_id) AS share,
  NULL AS noise
FROM succeeded s
LEFT JOIN <database>.jobs j ON s.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X40

### Map

**Sources**
- `jobs` (job_id, job_name, team, region): the typed columns of Table `jobs`, read by the `Team` formula of `Runs`.
- `Runs` (Run, Job, Mins): the typed columns of Table `Runs`, read by the Runs step.
- `run_alerts` (alert_id, run_id, severity, dt): the typed columns of Table `run_alerts`, read by its own final.

**Steps**
- `Runs` (Run, Job, Mins, Team, Cost): a Table with formula columns, read by the `Total Cost` formula of `Teams` and the `Run Mins` formula of `run_alerts`, so it is a step and a CTE `runs` in each of those two finals. `Team` is the jobs lookup on Job; `Cost` is `Mins * 2`, where 2 is the value of `rate` in Parameters.

**Finals**
- `Teams` (Team, Total Cost): a summary, since its only typed column, Team, is what its SUMIFS matches on. Its final is a GROUP BY of the `runs` step, with the typed rows data and finance kept.
- `run_alerts` (alert_id, run_id, severity, dt, Run Mins): a Table with a formula column that no query loads and nothing else reads, so it is a final. `Run Mins` is the Mins of the `runs` row whose Run matches run_id.

**Typed over a formula**
- None. Keys is empty.

**Marks**
- None.

**Refused**
- None.

**Left alone**
- The PivotTable on sheet `Pivot` (from Runs, rows Team, Sum of Cost). It is not a Table, so it gets no Hive.
- Parameters holds `rate` = 2, read in as 2. Keys is empty.

**To fill in**
- `<database>`, `<total_cost>` (header Total Cost), `<run_mins>` (header Run Mins).

### Hive

#### Teams

```sql
WITH runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT t.team AS Team, COALESCE(c.total, 0) AS <total_cost>
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance') t
LEFT JOIN (SELECT team, SUM(Cost) AS total FROM runs GROUP BY team) c
  ON t.team = c.team
```

#### run_alerts

```sql
WITH runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt, rn.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN runs rn ON a.run_id = rn.Run
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X46

### Map
- **Sources:** `jobs` (job_id, job_name, team), `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- **Steps:** none.
- **Finals:** `jobs` (job_id, job_name, team, shortest, runs, busiest). It holds formula columns, no query loads it, and no other Table or query reads it.
- **Value typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the D1 notes on Parameters and Keys (text outside a Table). Parameters and Keys are empty settings Tables, so they read no values and have no role.
- **To fill in:** `<database>`.

### Hive
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

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X47

### Map
- **Sources:** `region_budgets` (job_id, budget_cents, region).
- **Steps:** none.
- **Finals:** `region_budgets` (job_id, budget_cents, region, cheapest_first, region_total, region_avg). It holds formula columns, no query loads it, and no other Table or query reads it.
- **Value typed over a formula:** none. Keys is empty.
- **Marks:** none. `region_avg` is an AVERAGEIF, so it is AVG left NULL, with no COALESCE, as file 11 gives.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the D1 notes on Parameters and Keys (text outside a Table). Parameters and Keys are empty settings Tables, so they read no values and have no role.
- **To fill in:** `<database>`.

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
- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), `jobs` (job_id, job_name, team, region), `run_alerts` (alert_id, run_id, severity, dt).
- **Steps:** none. Neither query is read by another query.
- **Finals:**
  - Table `quiet_runs` (run_id, job_id, status), loaded by Power Query `quiet_runs`. No other Table's formula reads it.
  - Table `slow_regions` (region, avg_mins, fastest), loaded by Power Query `slow_regions`. No other Table's formula reads it.
- **Value typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the D1 notes on Parameters and Keys (text outside a Table). Parameters and Keys are empty settings Tables, so they read no values and have no role.
- **To fill in:** `<database>`.

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
- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), `jobs` (job_id, job_name, team, region), `run_alerts` (alert_id, run_id, severity, dt), `scheduler_runs` (run_id, job_id, dt), `job_owners` (job_id, team, owner, dt).
- **Steps:** none. No query is read by another query.
- **Finals:**
  - Table `alert_status` (alert_id, severity, status), loaded by Power Query `alert_status`.
  - Table `run_check` (run_id, status, scheduled_run), loaded by Power Query `run_check`.
  - Table `teams` (team), loaded by Power Query `teams`.
- **Value typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the D1 notes on Parameters and Keys (text outside a Table). Parameters and Keys are empty settings Tables, so they read no values and have no role.
- **To fill in:** `<database>`.

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
- **Sources:** `job_owners` (job_id, team, owner, dt), `jobs` (job_id, job_name, team, region).
- **Steps:** none.
- **Finals:** `owners` (job_id, owner, job_name, newest_first), loaded by Power Query `owners`. Its rows are the query's. No other Table's formula or query reads it.
- **Value typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the D1 notes on Parameters and Keys (text outside a Table). Parameters and Keys are empty settings Tables, so they read no values and have no role.
- **To fill in:** `<database>`.

### Hive
```sql
SELECT k.job_id, k.owner, j.job_name,
  RANK() OVER (ORDER BY k.job_id DESC) AS newest_first
FROM (SELECT DISTINCT job_id, owner FROM <database>.job_owners) k
LEFT JOIN <database>.jobs j ON k.job_id = j.job_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X59

### Map
- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, long_runs, failed_mins, not_test); run_alerts (alert_id, run_id, severity, dt, alerts_so_far). Both have formula columns that no query and no other Table's formula reads, so each is a final. Neither is a summary: jobs has job_name typed, which no COUNTIFS or SUMIFS matches on.
- **Typed over a formula:** none. Keys is empty, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty and never a source, step or final; the Steps sheet.
- **To fill in:** `<database>`, for job_runs, in the jobs block.

### Hive

```sql
-- jobs
SELECT j.job_id, j.job_name,
  COALESCE(l.long_runs, 0) AS long_runs,
  COALESCE(f.failed_mins, 0) AS failed_mins,
  COALESCE(n.not_test, 0) AS not_test
FROM (
  SELECT 1 AS job_id, 'nightly_load' AS job_name
  UNION ALL SELECT 2, 'invoice_sync'
  UNION ALL SELECT 3, 'report_build'
  UNION ALL SELECT 4, 'cache_warm'
) j
LEFT JOIN (SELECT job_id, COUNT(*) AS long_runs FROM <database>.job_runs WHERE duration_mins >= 20 GROUP BY job_id) l
  ON j.job_id = l.job_id
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS failed_mins FROM <database>.job_runs WHERE LOWER(status) LIKE 'f%' GROUP BY job_id) f
  ON j.job_id = f.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS not_test FROM <database>.job_runs WHERE status <> 'TEST' OR status IS NULL GROUP BY job_id) n
  ON j.job_id = n.job_id
```

```sql
-- run_alerts
SELECT alert_id, run_id, severity, dt,
  COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM (
  SELECT 1 AS alert_id, 97 AS run_id, 'high' AS severity, '2026-09-23' AS dt
  UNION ALL SELECT 2, 97, 'low', '2026-09-23'
  UNION ALL SELECT 3, 101, 'low', '2026-09-24'
  UNION ALL SELECT 4, 101, 'low', '2026-09-24'
  UNION ALL SELECT 5, 101, 'high', '2026-09-24'
  UNION ALL SELECT 6, 102, 'high', '2026-09-24'
  UNION ALL SELECT 7, 103, 'low', '2026-09-24'
  UNION ALL SELECT 8, 103, 'low', '2026-09-24'
  UNION ALL SELECT 9, 104, 'low', '2026-09-24'
) run_alerts
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X60

### Map
- **Sources:** none. region_budgets has formula columns, so it is a final, not a source.
- **Steps:** none.
- **Finals:** region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region); region_budgets (Total Row) (job_id, budget_cents, region, share, above_avg, rank_in_region), one row: COUNT of job_id, AVG of budget_cents, and NULL AS for the other four columns, which have no total.
- **Typed over a formula:** none. Keys is empty, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Total Row's "Total" label, as a Total Row final has no label; Parameters and Keys, both empty.
- **To fill in:** none. The rows are written in, and no source is read.

### Hive

```sql
-- region_budgets
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM (
  SELECT 1 AS job_id, 150 AS budget_cents, 'eu' AS region
  UNION ALL SELECT 2, 200, 'eu'
  UNION ALL SELECT 3, 350, 'us'
  UNION ALL SELECT 4, 50, 'eu'
) region_budgets
```

```sql
-- region_budgets (Total Row)
WITH region_budgets AS (
  SELECT job_id, budget_cents, region,
    budget_cents / SUM(budget_cents) OVER () AS share,
    budget_cents > AVG(budget_cents) OVER () AS above_avg,
    RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
  FROM (
    SELECT 1 AS job_id, 150 AS budget_cents, 'eu' AS region
    UNION ALL SELECT 2, 200, 'eu'
    UNION ALL SELECT 3, 350, 'us'
    UNION ALL SELECT 4, 50, 'eu'
  ) t
)
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents,
  NULL AS region, NULL AS share, NULL AS above_avg, NULL AS rank_in_region
FROM region_budgets
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X61

### Map
- **Sources:** region_costs (job_id, cost_cents, region, dt).
- **Steps:** none.
- **Finals:** by_region (region, total_cents, entries, priciest), a summary: its only typed column, region, is what its SUMIFS, COUNTIFS and MAXIFS match on, so its final is a GROUP BY of region_costs with its typed rows (eu, us) kept; by_region (Total Row) (region, total_cents, entries, priciest), one row: NULL AS region, SUM of total_cents, SUM of entries, MAX of priciest.
- **Typed over a formula:** none. Keys is empty, so no Keys row is needed.
- **Marks:** none. Note: region_costs row 29 has a blank cost_cents. SUMIFS and MAXIFS skip it, as Excel does, so it is written as it is, with no COALESCE.
- **Refusals:** none.
- **Left alone:** the Total Row's "Total" label, as a Total Row final has no label; Parameters and Keys, both empty.
- **To fill in:** `<database>`, for region_costs.

### Hive

```sql
-- by_region
SELECT b.region,
  COALESCE(t.total_cents, 0) AS total_cents,
  COALESCE(e.entries, 0) AS entries,
  COALESCE(p.priciest, 0) AS priciest
FROM (SELECT 'eu' AS region UNION ALL SELECT 'us') b
LEFT JOIN (SELECT region, SUM(cost_cents) AS total_cents FROM <database>.region_costs GROUP BY region) t
  ON b.region = t.region
LEFT JOIN (SELECT region, COUNT(*) AS entries FROM <database>.region_costs GROUP BY region) e
  ON b.region = e.region
LEFT JOIN (SELECT region, MAX(cost_cents) AS priciest FROM <database>.region_costs GROUP BY region) p
  ON b.region = p.region
```

```sql
-- by_region (Total Row)
WITH by_region AS (
  SELECT b.region,
    COALESCE(t.total_cents, 0) AS total_cents,
    COALESCE(e.entries, 0) AS entries,
    COALESCE(p.priciest, 0) AS priciest
  FROM (SELECT 'eu' AS region UNION ALL SELECT 'us') b
  LEFT JOIN (SELECT region, SUM(cost_cents) AS total_cents FROM <database>.region_costs GROUP BY region) t
    ON b.region = t.region
  LEFT JOIN (SELECT region, COUNT(*) AS entries FROM <database>.region_costs GROUP BY region) e
    ON b.region = e.region
  LEFT JOIN (SELECT region, MAX(cost_cents) AS priciest FROM <database>.region_costs GROUP BY region) p
    ON b.region = p.region
)
SELECT NULL AS region, SUM(total_cents) AS total_cents, SUM(entries) AS entries, MAX(priciest) AS priciest
FROM by_region
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X62

### Map
- **Sources:** none.
- **Steps:** none.
- **Finals:** team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short). It has formula columns that nothing else reads, so it is a final. Its typed rows are written in.
- **Typed over a formula:** none. Keys is empty, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty.
- **To fill in:** none.

### Hive

```sql
-- team_notes
SELECT team, note, written_on,
  CAST(NEXT_DAY(DATE_ADD(written_on, 7 * -1), 'MO') AS STRING) AS week_of,
  LAST_DAY(written_on) AS month_end,
  CAST(TRUNC(written_on, 'MM') AS STRING) AS month_of,
  FLOOR(MONTHS_BETWEEN(written_on, '2026-01-01')) AS months_in,
  DATE_SUB(written_on, 3) AS three_before,
  INITCAP(team) AS who,
  CONCAT_WS(': ', team, SUBSTR(note, 1, 5)) AS short
FROM (
  SELECT 'web' AS team, 'cache_warm is paused until October' AS note, '2026-09-11' AS written_on
  UNION ALL SELECT 'data', 'nightly_load runs long at the end of a month', '2026-09-15'
  UNION ALL SELECT 'data', 'ask ana before changing nightly_load', '2026-09-18'
  UNION ALL SELECT 'finance', 'report_build came over from data today', '2026-09-18'
  UNION ALL SELECT 'finance', 'invoice_sync\'s bill comes in a day late', '2026-09-21'
) team_notes
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X63

### Map
- **Sources:** scheduler_runs (run_id, job_id, dt). Typed only, read by job_runs' scheduled_job, so it is a source.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded). Nothing reads it, so it is a final.
- **Typed over a formula:** none. Keys is empty, so no Keys row is needed.
- **Marks:** blank. Run 98's status is blank and succeeded reads it through SEARCH, a formula that is not an -IF(S) form or ISBLANK, so it is written as COALESCE(status, ''). Excel's SEARCH gives an error on a blank, so succeeded is FALSE there. Run 98's avg_retry_secs is also blank, but no_retry reads it through ISBLANK, so it is written as it is.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, both empty.
- **To fill in:** `<database>`, for scheduler_runs.

### Hive

```sql
-- job_runs
SELECT j.run_id, j.job_id, j.status, j.duration_mins, j.avg_retry_secs,
  j.avg_retry_secs IS NULL AS no_retry,
  FLOOR(j.duration_mins / 4) AS quarters,
  LEAST(j.duration_mins, 25) AS capped,
  VAR_SAMP(j.duration_mins) OVER () AS variance,
  SUM(j.duration_mins * j.job_id) OVER () AS weighted,
  COALESCE(s.job_id, -1) AS scheduled_job,
  CONCAT('run ', j.run_id) AS label,
  INSTR(LOWER(COALESCE(j.status, '')), 'cess') > 0 AS succeeded
FROM (
  SELECT 95 AS run_id, 1 AS job_id, 'SUCCESS' AS status, 12 AS duration_mins, 2 AS avg_retry_secs
  UNION ALL SELECT 96, 2, 'SUCCESS', 18, 0
  UNION ALL SELECT 97, 3, 'FAILED', 30, 8
  UNION ALL SELECT 98, 2, NULL, 15, NULL
  UNION ALL SELECT 99, 1, 'TEST', 5, 0
  UNION ALL SELECT 101, 1, 'SUCCESS', 10, 1
  UNION ALL SELECT 102, 2, 'FAILED', 20, 6
  UNION ALL SELECT 103, 3, 'SUCCESS', 30, 0
  UNION ALL SELECT 104, 1, 'SUCCESS', 40, 3
) j
LEFT JOIN <database>.scheduler_runs s
  ON j.run_id = s.run_id
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X64

### Map

- **Sources**
  - `jobs` (job_id, job_name, team, region), typed; no query loads it.
  - `region_costs` (job_id, cost_cents, region, dt), typed; no query loads it.
- **Steps**: none.
- **Finals**
  - `picked_costs` (job_id, cost_cents, region, size), loaded by query picked_costs.
  - `costed_jobs` (job_id, job_name, team, region), loaded by query costed_jobs.
  - `costs_filled` (job_id, cost_cents, dt, day), loaded by query costs_filled.
- **Value typed over a formula**: none, so no Keys row is needed.
- **Marks**
  - blank: `costs_filled` reads `region_costs.cost_cents`, which is blank on job 2's 20260924 row; COALESCE(cost_cents, 0) writes it as 0, as Table.ReplaceValue does.
- **Refusals**: none.
- **Left alone**: Parameters and Keys (both empty; no formula reads them).
- **To fill in**: `<database>`, the database that holds `jobs` and `region_costs`, in each block.

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
WHERE NOT (j.job_name LIKE 'n%')
```

```sql
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt, SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X65

### Map

- **Sources** (typed; no query loads them)
  - `jobs` (job_id, job_name, team, region).
  - `region_budgets` (job_id, budget_cents, region).
  - `job_owners` (job_id, team, owner, dt).
  - `scheduler_runs` (run_id, job_id, dt).
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- **Steps**: none.
- **Finals**
  - `team_regions` (team, region), loaded by query team_regions.
  - `budget_places` (job_id, budget_cents, region, place), loaded by query budget_places.
  - `jobs_per_team` (team, jobs), loaded by query jobs_per_team.
  - `ran_as_scheduled` (run_id, dt), loaded by query ran_as_scheduled.
  - `run_measures` (run_id, job_id, measure, amount), loaded by query run_measures.
- **Value typed over a formula**: none, so no Keys row is needed.
- **Marks**
  - order dropped: `team_regions` sorts by team, but no FirstN or index follows the Table.Sort, so the Hive has no ORDER BY and the order is dropped.
  - blank: run 98's avg_retry_secs is blank in `job_runs`; the WHERE in `run_measures` leaves it out, as Table.Unpivot drops a null there.
- **Refusals**: none.
- **Left alone**: Parameters and Keys (both empty; no formula reads them).
- **To fill in**: `<database>`, the database that holds the source Tables, in each block.

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

- **Sources**
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), typed; no query loads it.
- **Steps**: none.
- **Finals**
  - `ok_runs` (run_id, job_id, duration_mins, dt, running, share), loaded by query ok_runs. Its formula columns read only its own rows, so it is a final. `running` is the running total of duration_mins per job_id by dt, ties included; `share` is each duration over the column's sum.
  - `ok_runs (Total Row)` (duration_mins), the Total Row's SUBTOTAL over duration_mins; its label "Total" is dropped.
- **Value typed over a formula**: none, so no Keys row is needed.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: Parameters and Keys (both empty; no formula reads them).
- **To fill in**: `<database>`, the database that holds `job_runs`, in each block.

### Hive

```sql
SELECT run_id, job_id, duration_mins, dt,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
) ok
```

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins, dt,
    COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
    duration_mins / SUM(duration_mins) OVER () AS share
  FROM (
    SELECT run_id, job_id, duration_mins, dt
    FROM <database>.job_runs
    WHERE status IS NOT NULL AND status LIKE 'SUCC%'
  ) ok
)
SELECT SUM(duration_mins) AS duration_mins FROM ok_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X69

### Map

- **Sources** (typed; no query loads them)
  - `jobs` (job_id, job_name, team, region).
  - `region_budgets` (job_id, budget_cents, region).
- **Steps**
  - `region_costs` (job_id, cost_cents, region, dt, job_name, budget, over_budget, running_cost). It has formula columns and is read by job_totals' formulas and by query late_costs, so it is a CTE in each block that reads it.
- **Finals**
  - `job_totals` (job_id, total_cents, over_count). Its only typed column, job_id, is what its SUMIFS and COUNTIFS match on, so it is a summary: a GROUP BY of region_costs with its typed rows kept.
  - `job_totals (Total Row)` (total_cents, over_count), the two SUBTOTALs; its label "Total" is dropped.
  - `late_costs` (job_id, dt, running_cost), loaded by query late_costs.
- **Value typed over a formula**: none, so no Keys row is needed.
- **Marks**
  - blank: region_costs' cost_cents is blank on job 2's 20260924 row; over_budget reads it as 0 through COALESCE(cost_cents, 0), as the Excel comparison does. The SUMIFS and running_cost read the column as it is, as they skip a blank.
  - text date: dt is held as text (20260911). running_cost orders its running total by that date, written as CONCAT of its parts; dt itself is kept as held.
- **Refusals**: none.
- **Left alone**: Parameters and Keys (both empty; no formula reads them).
- **To fill in**: `<database>`, the database that holds the source Tables, in each block.

### Hive

```sql
WITH region_costs AS (
  SELECT r.job_id, r.cost_cents, r.region, r.dt, j.job_name,
    b.budget_cents AS budget,
    COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(r.cost_cents) OVER (
      PARTITION BY r.job_id
      ORDER BY CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 0) AS running_cost
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON j.job_id = r.job_id
  LEFT JOIN <database>.region_budgets b ON b.job_id = r.job_id
)
SELECT j.job_id,
  COALESCE(t.total_cents, 0) AS total_cents,
  COALESCE(c.over_count, 0) AS over_count
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, SUM(cost_cents) AS total_cents FROM region_costs GROUP BY job_id) t
  ON j.job_id = t.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS over_count FROM region_costs WHERE over_budget = TRUE GROUP BY job_id) c
  ON j.job_id = c.job_id
```

```sql
WITH region_costs AS (
  SELECT r.job_id, r.cost_cents, r.region, r.dt, j.job_name,
    b.budget_cents AS budget,
    COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(r.cost_cents) OVER (
      PARTITION BY r.job_id
      ORDER BY CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 0) AS running_cost
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON j.job_id = r.job_id
  LEFT JOIN <database>.region_budgets b ON b.job_id = r.job_id
),
job_totals AS (
  SELECT j.job_id,
    COALESCE(t.total_cents, 0) AS total_cents,
    COALESCE(c.over_count, 0) AS over_count
  FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
  LEFT JOIN (SELECT job_id, SUM(cost_cents) AS total_cents FROM region_costs GROUP BY job_id) t
    ON j.job_id = t.job_id
  LEFT JOIN (SELECT job_id, COUNT(*) AS over_count FROM region_costs WHERE over_budget = TRUE GROUP BY job_id) c
    ON j.job_id = c.job_id
)
SELECT SUM(total_cents) AS total_cents, SUM(over_count) AS over_count FROM job_totals
```

```sql
WITH region_costs AS (
  SELECT r.job_id, r.cost_cents, r.region, r.dt, j.job_name,
    b.budget_cents AS budget,
    COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(r.cost_cents) OVER (
      PARTITION BY r.job_id
      ORDER BY CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 0) AS running_cost
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON j.job_id = r.job_id
  LEFT JOIN <database>.region_budgets b ON b.job_id = r.job_id
)
SELECT job_id, dt, running_cost
FROM region_costs
WHERE running_cost > 1500
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X70

### Map

- **Sources** (typed; no query loads them)
  - `jobs` (job_id, job_name, team, region).
  - `job_owners` (job_id, team, owner, dt).
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- **Steps**
  - `staffed` (job_id, job_name, owner), the connection-only query. It is read by query owner_load, so it is a CTE in that block.
- **Finals**
  - `owner_load` (owner, total_mins, runs, avg_mins), loaded by query owner_load. Its avg_mins reads its own row, so it is a final.
  - `owner_load (Total Row)` (runs), the SUBTOTAL over runs; its label "Total" is dropped.
  - `busiest_owner` (owner, total_mins, runs), loaded by query busiest_owner. It reads the rows of Table `owner_load`, which is a final and not a step, since only a Table's formula makes a Table a step.
- **Value typed over a formula**: none, so no Keys row is needed.
- **Marks**
  - none. The blank owner of job 4 in `job_owners` is left out by the owner filter, as the M null check leaves it out.
- **Refusals**: none.
- **Left alone**: Parameters and Keys (both empty; no formula reads them).
- **To fill in**: `<database>`, the database that holds the source Tables, in each block. The `busiest_owner` block reads `<database>.owner_load`, so `owner_load` must exist under that name.

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
SELECT owner, total_mins, runs
FROM <database>.owner_load
ORDER BY runs DESC
LIMIT 1
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X73

### Map

**Sources**
- `region_budgets` (job_id, budget_cents, region): typed only, read by query eu_budgets.
- `jobs` (job_id, job_name, team, region): typed only, read by query eu_budgets.

**Steps**
- Query `eu_budgets` (job_id, budget_cents, region, job_name): read by query eu_count, so it is a CTE in eu_count's block.

**Finals**
- Table `eu_budgets` (job_id, budget_cents, region, job_name, dollars): its rows are query eu_budgets' rows; `dollars` is the formula `budget_cents / 100`.
- Table `eu_count` (region, jobs, total_cents): its rows are query eu_count's rows.

**Values typed over a formula:** none. Every formula cell holds its formula, so no Keys row is needed.

**Marks:** none.

**Refusals:** none.

**Left alone:** Parameters and Keys are empty, so neither is a source, step or final. The Steps sheet holds no Table.

**To fill in:** `<database>`, in each read of region_budgets and jobs.

### Hive

```sql
SELECT b.job_id, b.budget_cents, b.region, j.job_name, b.budget_cents / 100 AS dollars
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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X74

### Map

**Sources**
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed only, read by the XLOOKUP formulas of run_alerts.

**Steps**
- Table `run_alerts` (alert_id, run_id, severity, dt, status, job_id, alerts_so_far): it has formula columns, and by_status's formula and query late_alerts both read it, so it is a step. It is a CTE in each block that reads it. Its typed rows are read from `<database>.run_alerts`, the Hive table of that name, for you to check.

**Finals**
- Table `by_status` (status, alerts): a summary, since its only typed column, status, is what its COUNTIFS match on. Its final is a GROUP BY of run_alerts with its typed rows kept.
- Table `late_alerts` (alert_id, run_id, alerts_so_far): its rows are query late_alerts' rows.

**Values typed over a formula:** none.

**Marks:**
- blank: job_runs' status is blank on run 98, and the XLOOKUP reads that column, so the status lookup is `COALESCE(j.status, '')`. Run 98 is not in run_alerts, so no row changes.
- The cumulative count `alerts_so_far` is written as a window COUNT(*) with ties included, as Excel's COUNTIFS gives them.

**Refusals:** none.

**Left alone:** Parameters and Keys are empty, so neither is a source, step or final. The Steps sheet holds no Table.

**To fill in:** `<database>`, in each read of run_alerts and job_runs.

### Hive

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(j.status, '') AS status, j.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs j ON a.run_id = j.run_id
)
SELECT s.status, COALESCE(c.alerts, 0) AS alerts
FROM (SELECT 'FAILED' AS status UNION ALL SELECT 'SUCCESS') s
LEFT JOIN (SELECT status, COUNT(*) AS alerts FROM run_alerts GROUP BY status) c
  ON s.status = c.status
```

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(j.status, '') AS status, j.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs j ON a.run_id = j.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM run_alerts
WHERE alerts_so_far > 5
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X77

### Map

**Sources**
- `run_alerts` (alert_id, run_id, severity, dt): typed only, and no query loads it, so it is a source. Read by query high_alerts.

**Steps**
- Query `high_alerts` (alert_id, run_id, dt): read by query high_per_day, so it is a CTE in high_per_day's block.

**Finals**
- Table `high_alerts` (alert_id, run_id, dt, late_run): its rows are query high_alerts' rows; `late_run` is the formula `run_id > 100`. Its own formula reads its own row, so the Table stays a final.
- Table `high_per_day` (dt, alerts): its rows are query high_per_day's rows.

**Values typed over a formula:** none.

**Marks:** none.

**Refusals:** none.

**Left alone:** Parameters and Keys are empty, so neither is a source, step or final. The Steps sheet holds no Table.

**To fill in:** `<database>`, in each read of run_alerts.

### Hive

```sql
SELECT r.alert_id, r.run_id, r.dt, r.run_id > 100 AS late_run
FROM <database>.run_alerts r
WHERE r.severity = 'high'
```

```sql
WITH high_alerts AS (
  SELECT r.alert_id, r.run_id, r.dt
  FROM <database>.run_alerts r
  WHERE r.severity = 'high'
)
SELECT dt, COUNT(*) AS alerts
FROM high_alerts
GROUP BY dt
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X78

### Map

**Sources**
- `region_costs` (job_id, cost_cents, region, dt): typed only, read by query known_costs.

**Steps**
- Query `known_costs` (job_id, cost_cents, dt): read by query cost_per_job, so it is a CTE in cost_per_job's block. Its rows are the rows of region_costs whose cost_cents is not blank.

**Finals**
- Table `known_costs` (job_id, cost_cents, dt, dollars): its rows are query known_costs' rows; `dollars` is the formula `cost_cents / 100`.
- Table `known_costs (Total Row)`: one row, with `cost_cents` as SUM(cost_cents). Its job_id, dt and dollars cells are NULL, as the Total Row gives no total there, and its "Total" label is left out.
- Table `cost_per_job` (job_id, total_cents): its rows are query cost_per_job's rows.

**Values typed over a formula:** none.

**Marks:**
- blank: row 29 of region_costs (job 2, dt 20260924) has a blank cost_cents. The known_costs query drops it, as M's `<> null` is `IS NOT NULL` in Hive. The result is 27 rows, which is what the Table holds.
- `dt` is carried through as typed (values such as 20260911). No formula reads it, so the text-date CONCAT does not apply.

**Refusals:** none.

**Left alone:** Parameters and Keys are empty, so neither is a source, step or final. The Steps sheet holds no Table.

**To fill in:** `<database>`, in each read of region_costs.

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
SELECT NULL AS job_id, SUM(cost_cents) AS cost_cents, NULL AS dt, NULL AS dollars
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

