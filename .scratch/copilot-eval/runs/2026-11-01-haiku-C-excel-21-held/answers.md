date: 2026-11-01
arm: C
model: haiku
files: 21-held

## X21

### Map

**Sources**
- `<database>.region_budgets`: typed columns job_id, budget_cents, region.

**Steps**
- None.

**Finals**
- Table region_budgets, with columns job_id, budget_cents, region, budget_dollars, with_margin. No query loads it and no other Table or query reads it, so it is a final. Its formula columns read only their own row.

**Values typed over a formula**
- None.

**Marks**
- None.

**Refusals**
- None.

**Left alone**
- Table Parameters (empty): no formula reads a fixed value, so nothing is read from it.
- Table Keys (empty): no value is typed over a formula, so no row is needed.
- Sheet Steps (instructions, no Table): cells outside a Table are left alone.

**To fill in**
- `<database>`, the database name, in the block below.

### Hive

#### region_budgets

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

**Sources**
- `<database>.jobs`: typed columns job_id, job_name, team.

**Steps**
- None.

**Finals**
- Table jobs, with columns job_id, job_name, team, is_finance, ratio. No query loads it and no other Table or query reads it, so it is a final.

**Values typed over a formula**
- None.

**Marks**
- is_finance: Excel's `=` ignores case and Hive's `=` does not. The sample's team values are all lower case, so the values match, but a team typed as "Finance" would give "no" in Hive. Check it against the sample.

**Converted, not a mark**
- ratio: IFERROR(a / b, 0) becomes COALESCE(job_id / (job_id - 2), 0). Job 2 divides by 0, which is NULL in Hive and 0 here, as Excel's IFERROR gives.

**Refusals**
- None.

**Left alone**
- Table Parameters (empty): no formula reads a fixed value.
- Table Keys (empty): no value is typed over a formula, so no row is needed.
- Sheet Steps (instructions, no Table): cells outside a Table are left alone.

**To fill in**
- `<database>`, the database name, in the block below.

### Hive

#### jobs

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

**Sources**
- `<database>.job_runs`: typed columns run_id, status, avg_retry_secs.

**Steps**
- None.

**Finals**
- Table job_runs, with columns run_id, status, avg_retry_secs, label, risky. No query loads it and no other Table or query reads it, so it is a final.

**Values typed over a formula**
- None.

**Marks**
- blank: run_id 98 has a blank status and a blank avg_retry_secs. label and risky read status, so they read COALESCE(status, ''); risky reads avg_retry_secs, so it reads COALESCE(avg_retry_secs, 0). The typed columns stay as they are in the SELECT.
- case: Excel's `=` and SWITCH ignore case and Hive's do not. The sample's statuses are all upper case, so the values match.
- label: `_xlfn.SWITCH` is read as SWITCH, with its default "other" as ELSE.

**Refusals**
- None.

**Left alone**
- Table Parameters (empty): no formula reads a fixed value.
- Table Keys (empty): no value is typed over a formula, so no row is needed.
- Sheet Steps (instructions, no Table): cells outside a Table are left alone.

**To fill in**
- `<database>`, the database name, in the block below.

### Hive

#### job_runs

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

**Sources**
- `<database>.team_notes`: typed columns team, note, written_on.

**Steps**
- None.

**Finals**
- Table team_notes, with columns team, note, written_on, first_word, shout, month, tens_of_chars. No query loads it and no other Table or query reads it, so it is a final.

**Values typed over a formula**
- None.

**Marks**
- None. Every note has a space, so first_word's FIND never fails. written_on is read as its typed date, and MONTH reads it as it is.

**Converted, not a mark**
- first_word: LEFT(note, FIND(" ", note)-1) becomes SUBSTR(note, 1, INSTR(note, ' ') - 1).
- tens_of_chars: LEN becomes LENGTH.

**Refusals**
- None.

**Left alone**
- Table Parameters (empty): no formula reads a fixed value.
- Table Keys (empty): no value is typed over a formula, so no row is needed.
- Sheet Steps (instructions, no Table): cells outside a Table are left alone.

**To fill in**
- `<database>`, the database name, in the block below.

### Hive

#### team_notes

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

**Sources**
- `<database>.Costs`: typed columns Job, `<cost_cents>` (header Cost (cents)), Region, `<day_key>` (header Day Key).
- `<database>.Budgets`: typed columns Job, Budget, Region.

**Steps**
- None.

**Finals**
- Table Costs, with columns Job, `<cost_cents>`, Region, `<day_key>`, Day. No query loads it and no other Table or query reads it, so it is a final.
- Table Budgets, with columns Job, Budget, Region, Dollars. No query loads it and no other Table or query reads it, so it is a final.

**Values typed over a formula**
- None.

**Marks**
- Costs, Day: a date held as text, as 20260911 is. DATE(LEFT(day_key, 4), MID(day_key, 5, 2), RIGHT(day_key, 2)) becomes CONCAT(SUBSTR(day_key, 1, 4), '-', SUBSTR(day_key, 5, 2), '-', SUBSTR(day_key, 7, 2)), a text date in yyyy-mm-dd and not an Excel date.

**Refusals**
- None.

**Left alone**
- Costs row 29 (Job 2, Day Key 20260924) has a blank Cost (cents). It is kept as NULL, since no formula reads that column, so no COALESCE is written.
- Table Parameters (empty): no formula reads a fixed value.
- Table Keys (empty): no value is typed over a formula, so no row is needed.
- Sheet Steps (instructions, no Table): cells outside a Table are left alone.

**To fill in**
- `<database>`, the database name.
- `<cost_cents>`, the header Cost (cents), in the Costs block.
- `<day_key>`, the header Day Key, in the Costs block.

### Hive

#### Costs

```sql
SELECT Job, <cost_cents>, Region, <day_key>,
  CONCAT(SUBSTR(<day_key>, 1, 4), '-', SUBSTR(<day_key>, 5, 2), '-', SUBSTR(<day_key>, 7, 2)) AS Day
FROM <database>.Costs
```

#### Budgets

```sql
SELECT Job, Budget, Region, Budget / 100 AS Dollars
FROM <database>.Budgets
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X26

### Map

- **Sources:** job_runs (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt); run_alerts (its typed columns: alert_id, run_id, severity).
- **Steps:** none.
- **Finals:** run_alerts (alert_id, run_id, severity, job_id, status, avg_mins). Its formula columns read job_runs. No query loads run_alerts and no other Table's formula reads it, so it is a final.
- **Parameters and Keys:** never a source, step or final. Both are empty: no fixed value is read, and no value is typed over a formula, so Keys needs no row.
- **Value typed over a formula:** none.
- **Marks:** blank. The sample's job_runs has a blank status (run 98), and run_alerts' status reads that column through VLOOKUP, so it is written COALESCE(status, ''). Excel reads a blank as 0 or "", Hive as NULL.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in cell D1 of each sheet, which are cells outside a Table.
- **To fill in:** `<database>`, the database name in each read.

### Hive

run_alerts

```sql
SELECT ra.alert_id, ra.run_id, ra.severity,
  jr.job_id AS job_id,
  COALESCE(jr.status, '') AS status,
  a.avg_mins AS avg_mins
FROM <database>.run_alerts ra
LEFT JOIN <database>.job_runs jr ON ra.run_id = jr.run_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) a ON jr.job_id = a.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X27

### Map

- **Sources:** jobs (its typed columns: job_id, job_name, team, region).
- **Steps:** none.
- **Finals:** by_team, a summary (team, jobs_in_team, last_job_id, last_job_name). Its only typed column is team, the one its COUNTIFS and MAXIFS match on, so it is a summary: its final is a GROUP BY of jobs, with its typed team values as the groups.
- **Typed-in groups:** by_team's team values data, finance and web.
- **Parameters and Keys:** never a source, step or final. Both are empty, and no value is typed over a formula.
- **Value typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in cell D1 of each sheet, which are cells outside a Table.
- **To fill in:** `<database>`, the database name in each read.

### Hive

by_team (summary)

```sql
SELECT t.team,
  COALESCE(c.jobs_in_team, 0) AS jobs_in_team,
  COALESCE(m.last_job_id, 0) AS last_job_id,
  j.job_name AS last_job_name
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (SELECT team, COUNT(*) AS jobs_in_team FROM <database>.jobs GROUP BY team) c
  ON t.team = c.team
LEFT JOIN (SELECT team, MAX(job_id) AS last_job_id FROM <database>.jobs GROUP BY team) m
  ON t.team = m.team
LEFT JOIN <database>.jobs j ON m.last_job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X28

### Map

- **Sources:** job_runs (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (its typed columns: job_id, job_name).
- **Steps:** none.
- **Finals:** jobs (job_id, job_name, ok_mins). Its formula column ok_mins reads job_runs; no query loads jobs and no other Table's formula reads it, so it is a final.
- **Parameters:** never a source, step or final. Empty.
- **Keys:** never a source, step or final. Its one row names jobs, job_id, which is the key for the typed-over value.
- **Value typed over a formula:** jobs ok_mins where job_id is 3 (report_build), typed as 99. Matched on jobs' Keys row, job_id.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the blank status in job_runs (run 98). The SUMIFS condition on status skips a blank, as the Hive WHERE does, so it is written as it is, with no COALESCE. The Steps sheet and the notes in cell D1 of each sheet are cells outside a Table, also left alone.
- **To fill in:** `<database>`, the database name in each read.

### Hive

jobs

```sql
SELECT j.job_id, j.job_name,
  CASE WHEN j.job_id = 3 THEN 99
    ELSE COALESCE(s.total, 0) END AS ok_mins
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

- **Sources:** region_budgets (its typed columns: job_id, budget_cents, region).
- **Steps:** none.
- **Finals:** region_budgets (job_id, budget_cents, region, in_dollars, pointer). Its formula columns read Parameters and INDIRECT; no query loads it and no other Table's formula reads it, so it is a final.
- **Parameters:** never a source, step or final. Its value cents_per_dollar is read in as 100 for in_dollars.
- **Keys:** never a source, step or final. It is empty, so no Keys row names region_budgets.
- **Value typed over a formula:** region_budgets in_dollars where job_id is 3, budget_cents is 350 and region is 'us', typed as 5. There is no Keys row for region_budgets, so the match uses every typed column of the row: job_id, budget_cents and region.
- **Marks:** none.
- **Refusals:** pointer, `=INDIRECT("A"&ROW())`. INDIRECT and ROW() hang on the sheet's rows, so pointer is `NULL AS pointer`.
- **Left alone:** the Steps sheet and the notes in cell D1 of each sheet, which are cells outside a Table.
- **To fill in:** `<database>`, the database name in each read.

### Hive

region_budgets

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

- **Sources:** scheduler_runs (its typed columns: run_id, job_id, dt).
- **Steps:** none.
- **Finals:** scheduler_runs (run_id, job_id, dt, day, prev_run, jitter). Its formula columns read its own row only, and nothing else reads the Table, so it is a final.
- **Parameters and Keys:** never a source, step or final. Both are empty, and no value is typed over a formula.
- **Value typed over a formula:** none.
- **Marks:** day. RIGHT(dt, 2) is written SUBSTR(dt, -2), reading dt as the text the sample shows (2026-09-23). If dt is a true Excel date, Excel reads its serial number and the day differs, so check dt's type before the batch runs.
- **Refusals:** prev_run, `=OFFSET(...)`, is `NULL AS prev_run`. jitter, `=RANDBETWEEN(1,5)`, is `NULL AS jitter`. Both are refused: OFFSET hangs on the sheet's rows and RANDBETWEEN is random.
- **Left alone:** the bar chart on the Summary sheet; the PivotTable on sheet Pivot, from scheduler_runs with rows job_id and values Count of run_id; the Steps sheet and the notes in cell D1 of each sheet.
- **To fill in:** `<database>`, the database name in each read.

### Hive

scheduler_runs

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

- **Sources:** `jobs`, its typed columns job_id and team, read as `<database>.jobs`.
- **Steps:** none.
- **Finals:** `jobs` (job_id, team, bump, tag, scaled, boosted). No other Table reads it, and no query loads it.
- **Settings, neither source, step nor final:** Parameters (empty) and Keys (empty). Nothing reads from them.
- **Values typed over a formula:** none.
- **Marks:**
  - boosted reads the defined name `boost`, which is Summary!B2 (a cell outside a Table, value 10). Written as its value, `job_id * 10`. Move boost into Parameters.
- **Refusals (NULL AS its header):**
  - bump: `=jobs[[#This Row],[bump]]*2` reads its own column (circular).
  - tag: `TAG` is a defined name holding a LAMBDA.
  - scaled: `Summary!$D$4` is a cell outside a Table and not a defined name (D4).
- **Left alone:** the Summary sheet's cells (B2 and D4, outside any Table) and the Steps sheet.
- **To fill in:** `<database>`, in the FROM.

### Hive

#### jobs

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
  - `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read as `<database>.job_runs`.
  - `jobs`, its typed columns job_id, job_name, team and region, read as `<database>.jobs`. It has no formula column, so it is a source only.
- **Steps:** `job_runs`. Its formula column job_name is read by by_name's COUNTIFS, so it is a step and a CTE in by_name's final. It has no final of its own.
- **Finals:** `by_name` (job_name, runs), a summary. Its only typed column, job_name, is what its COUNTIFS match on, so its final is a GROUP BY of job_runs, and its typed groups are typed in.
- **Settings, neither source, step nor final:** Parameters (empty) and Keys (empty).
- **Values typed over a formula:** none.
- **Marks:**
  - job_runs.job_name: VLOOKUP with TRUE is approximate. Written as the exact match, LEFT JOIN jobs ON job_id = job_id, returning job_name.
- **Refusals:** none.
- **Left alone:** the Steps sheet.
- **To fill in:** `<database>`, in each FROM and JOIN.

### Hive

#### by_name

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT g.job_name, COALESCE(c.runs, 0) AS runs
FROM (SELECT 'invoice_sync' AS job_name UNION ALL SELECT 'nightly_load' UNION ALL SELECT 'report_build') g
LEFT JOIN (SELECT job_name, COUNT(*) AS runs FROM job_runs GROUP BY job_name) c
  ON g.job_name = c.job_name
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X33

### Map

- **Sources:** `job_runs`, read from `<database>.job_runs`. The query reads Sql.Database("dwh01", "ops"), item job_runs in schema ops. Read the table it names, for you to check.
- **Steps:** none. Power Query "slow_runs" loads Table slow_runs, and no formula reads that Table, so the query is the final's query.
- **Finals:** `slow_runs` (run_id, duration_mins, over_by), its rows the rows of Power Query "slow_runs". Its typed rows are not read: its rows come from the query.
- **Settings, neither source, step nor final:** Parameters (empty) and Keys (empty).
- **Values typed over a formula:** none.
- **Marks:**
  - Sql source `job_runs`, named above for you to check.
  - M's `[status] <> "TEST"` keeps a null, as Hive's `<>` doesn't. Written as `(status <> 'TEST' OR status IS NULL)`.
- **Refusals:** none.
- **Left alone:** the Steps sheet.
- **To fill in:** `<database>`, in the FROM.

### Hive

#### slow_runs

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
  - `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read as `<database>.job_runs`.
  - `jobs`, its typed columns job_id, job_name, team and region, read as `<database>.jobs`.
- **Steps:** `runs_with_team` (connection only). It is named by Power Query "team_totals", so it is a step and a CTE in team_totals' final. It is a LEFT JOIN of job_runs to jobs, adding team.
- **Finals:** `team_totals` (team, total_mins, longest), its rows the rows of Power Query "team_totals". Nothing else reads the Table.
- **Settings, neither source, step nor final:** Parameters (empty) and Keys (empty).
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet.
- **To fill in:** `<database>`, in each FROM and JOIN.

### Hive

#### team_totals

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
  - `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read as `<database>.job_runs`. The query reads run_id and dt.
  - `scheduler_runs`, its typed columns run_id, job_id and dt, read as `<database>.scheduler_runs`. The query reads run_id and dt.
- **Steps:** none.
- **Finals:** `recent` (run_id, dt), its rows the rows of Power Query "recent", which Table.Combine stacks, sorts and keeps the first four of.
- **Left out:** Power Query "rates". It reads Web.Contents, a web source, so it is refused and left out. Nothing reads it either.
- **Settings, neither source, step nor final:** Parameters (empty) and Keys (empty).
- **Values typed over a formula:** none.
- **Marks:**
  - Table.Combine is UNION ALL.
  - Table.Sort then FirstN 4 is ORDER BY run_id DESC LIMIT 4. run_id 103 and 104 each appear in both sources with the same dt, so which copy Hive keeps among ties gives the same rows.
- **Refusals:** the Web.Contents query "rates" (left out, above).
- **Left alone:** the Steps sheet.
- **To fill in:** `<database>`, in each FROM.

### Hive

#### recent

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

- **Sources**: `<database>.job_runs` (its typed columns: run_id, status); `<database>.run_alerts` (its typed columns: alert_id, run_id, severity, dt).
- **Steps**: none.
- **Finals**:
  - Table job_runs, columns run_id, status, alerts. Its only formula column is alerts, a COUNTIFS over run_alerts, so alerts is a count read from `<database>.run_alerts`. job_runs is not a summary, as status is typed and not matched on.
  - Table severity_by_day, columns dt, high, low. Power Query severity_by_day loads it and reads run_alerts, so the Table is the final and its rows are the query's. The query is its loader, not a step, as no query names it.
- **Typed over a formula**: none. Keys is empty, and every alerts cell holds its formula.
- **Marks**: the pivot's columns high and low are now fixed to the severities in the sample; a new severity needs a new column.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, empty settings Tables that no formula reads. The blank status on run 98 is written as it is, as no formula reads status.
- **To fill in**: `<database>`, in each block.

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

- **Sources**: `<database>.Owners` (its typed columns: `<job_no>`, `<team_name>`, Owner, Day).
- **Steps**: none.
- **Finals**: Table Owners, columns `<job_no>`, `<team_name>`, Owner, Day, `<is_ana>`. Its only formula column, Is Ana, reads its own row and nothing else reads Owners, so Owners is a final. It is not a summary, as it has no SUMIFS or COUNTIFS.
- **Typed over a formula**: none. Keys is empty, and every Is Ana cell holds its formula.
- **Marks**:
  - blank: Owner is blank on the web rows (Job No 4). The formula reads Owner, so it is written COALESCE(Owner, '').
- **Refusals**: none.
- **Left alone**: Parameters and Keys, empty settings Tables that no formula reads.
- **To fill in**: `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

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

- **Sources**:
  - `<database>.job_runs`, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs. Job_runs is a final, so it reads its own typed columns from this source.
  - `<database>.jobs`, its typed columns: job_id, job_name, team, region.
- **Steps**: none.
- **Finals**: Table job_runs, columns run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost.
  - region: XLOOKUP on jobs, so a LEFT JOIN to `<database>.jobs` on job_id.
  - region_mins: SUMIFS over its own Table by region, so a windowed SUM of duration_mins partitioned by region, with COALESCE.
  - retry_cost: (avg_retry_secs + duration_mins) * 2.
- **Typed over a formula**: retry_cost on run 102 is typed as 1. Keys names job_runs with run_id, so it is a CASE matched on run_id.
- **Marks**:
  - blank: avg_retry_secs is blank on run 98, and retry_cost's formula reads it, so it is written COALESCE(avg_retry_secs, 0).
  - typed over: retry_cost on run 102, written as the CASE below.
- **Refusals**: none. The `_xlfn.` prefix is read past.
- **Left alone**: the blank status on run 98, as no formula reads status. Parameters is empty.
- **To fill in**: `<database>` only.

### Hive

```sql
SELECT j.run_id, j.job_id, j.status, j.duration_mins, j.avg_retry_secs,
  jb.region,
  COALESCE(SUM(j.duration_mins) OVER (PARTITION BY jb.region), 0) AS region_mins,
  CASE WHEN j.run_id = 102 THEN 1
    ELSE (COALESCE(j.avg_retry_secs, 0) + j.duration_mins) * 2
  END AS retry_cost
FROM <database>.job_runs j
LEFT JOIN <database>.jobs jb ON j.job_id = jb.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X39

### Map

- **Sources**:
  - `<database>.job_runs`, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. It is typed only, so it is a source, read by query ok_runs.
  - `<database>.jobs`, its typed columns: job_id, job_name, team, region.
- **Steps**: none.
- **Finals**: Table ok_runs, columns run_id, job_id, duration_mins, job_name, share, noise. Power Query ok_runs loads it and reads job_runs; no other Table's formula reads ok_runs, so the Table is a final and its rows are the query's (the SUCCESS rows of job_runs). The query is its loader and its two steps are the WHERE and the column list.
  - job_name: XLOOKUP on jobs, so a LEFT JOIN to `<database>.jobs` on job_id.
  - share: duration_mins over SUMIFS of its own Table by job_id, so a windowed SUM over the rows the query keeps, partitioned by job_id, with COALESCE.
- **Typed over a formula**: none. Keys is empty.
- **Marks**: none.
- **Refusals**: noise is `=RAND()`, which is refused, so it is `NULL AS noise`.
- **Left alone**: Parameters and Keys, empty settings Tables.
- **To fill in**: `<database>` only.

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

- **Sources**: `<database>.jobs`, its typed columns: job_id, job_name, team, region.
- **Steps**: Table Runs, a step as the Teams summary's SUMIFS and run_alerts' XLOOKUP both read it. It is a CTE in each final that reads it. Its typed columns are read from `<database>.Runs`, and its formulas are:
  - Team: XLOOKUP on jobs, so a LEFT JOIN to `<database>.jobs` on Job.
  - Cost: Mins * rate, where rate is read in from Parameters as its value, 2.
- **Finals**:
  - Table Teams, a summary, columns Team, `<total_cost>`. Its only typed column, Team, is what its SUMIFS matches on, so its final is a GROUP BY over the Runs step, with its typed groups data and finance typed in.
  - Table run_alerts, columns alert_id, run_id, severity, dt, `<run_mins>`. Nothing else reads it, so it is a final.
- **Typed over a formula**: none. Keys is empty, and every formula cell holds its formula.
- **Marks**:
  - Parameters: rate is read in as its value, 2, typed in. Change the 2 if rate changes.
- **Refusals**: none. The `_xlfn.` prefix is read past.
- **Left alone**: the PivotTable on sheet "Pivot", from Runs with rows Team and values Sum of Cost. Its totals are in the Teams final. Keys is empty.
- **To fill in**: `<database>`, `<total_cost>`, `<run_mins>`.

### Hive

```sql
WITH Runs AS (
  SELECT r.Run, r.Job, r.Mins, jb.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs jb ON r.Job = jb.job_id
)
SELECT t.Team, COALESCE(c.total, 0) AS <total_cost>
FROM (SELECT 'data' AS Team UNION ALL SELECT 'finance') t
LEFT JOIN (SELECT Team, SUM(Cost) AS total FROM Runs GROUP BY Team) c
  ON t.Team = c.Team
```

```sql
WITH Runs AS (
  SELECT r.Run, r.Job, r.Mins, jb.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs jb ON r.Job = jb.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt, rn.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN Runs rn ON a.run_id = rn.Run
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X46

### Map

- **Sources**: `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. `jobs`, its typed columns job_id, job_name, team, read by final `jobs`.
- **Steps**: none.
- **Finals**: `jobs` (job_id, job_name, team, shortest, runs, busiest). It has formula columns, no query loads it, and no other formula reads it.
- **Typed over a formula**: none. Keys holds no row, as no value is typed over a formula.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet, and the D1 notes on Parameters and Keys (cells outside a Table). Parameters and Keys are empty and are never a source, step or final.
- **To fill in**: `<database>`, the database that holds `job_runs` and `jobs`.

### Hive

```sql
SELECT j.job_id, j.job_name, j.team,
  COALESCE(s.shortest, 0) AS shortest,
  COALESCE(r.runs, 0) AS runs,
  RANK() OVER (ORDER BY COALESCE(r.runs, 0) DESC) AS busiest
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, MIN(duration_mins) AS shortest FROM <database>.job_runs GROUP BY job_id) s
  ON j.job_id = s.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
  ON j.job_id = r.job_id
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X47

### Map

- **Sources**: `region_budgets`, its typed columns job_id, budget_cents, region, read by final `region_budgets`.
- **Steps**: none.
- **Finals**: `region_budgets` (job_id, budget_cents, region, cheapest_first, region_total, region_avg). It has formula columns, no query loads it, and no other formula reads it.
- **Typed over a formula**: none. Keys holds no row, as no value is typed over a formula.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet, and the D1 notes on Parameters and Keys (cells outside a Table). Parameters and Keys are empty and are never a source, step or final.
- **To fill in**: `<database>`, the database that holds `region_budgets`.

### Hive

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X48

### Map

- **Sources**: `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read by finals `quiet_runs` and `slow_regions`. `run_alerts`, its typed columns alert_id, run_id, severity, dt, read by final `quiet_runs`. `jobs`, its typed columns job_id, job_name, team, region, read by final `slow_regions`.
- **Steps**: none. No query's M names another query.
- **Finals**:
  - `quiet_runs` (run_id, job_id, status): the Table loaded by Power Query `quiet_runs`, which reads `job_runs` and `run_alerts`. No formula reads it, so its rows are the query's.
  - `slow_regions` (region, avg_mins, fastest): the Table loaded by Power Query `slow_regions`, which reads `job_runs` and `jobs`. No formula reads it, so its rows are the query's.
- **Typed over a formula**: none. Keys holds no row.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet, and the D1 notes on Parameters and Keys (cells outside a Table). Parameters and Keys are empty and are never a source, step or final.
- **To fill in**: `<database>`, the database that holds `job_runs`, `run_alerts` and `jobs`.

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

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X49

### Map

- **Sources**:
  - `job_runs`, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt, read by finals `alert_status` and `run_check`.
  - `run_alerts`, its typed columns alert_id, run_id, severity, dt, read by final `alert_status`.
  - `scheduler_runs`, its typed columns run_id, job_id, dt, read by final `run_check`.
  - `jobs`, its typed columns job_id, job_name, team, region, read by final `teams`.
  - `job_owners`, its typed columns job_id, team, owner, dt, read by final `teams`.
- **Steps**: none. No query's M names another query.
- **Finals**:
  - `alert_status` (alert_id, severity, status): the Table loaded by Power Query `alert_status`, which reads `run_alerts` and `job_runs`.
  - `run_check` (run_id, status, scheduled_run): the Table loaded by Power Query `run_check`, which reads `job_runs` and `scheduler_runs`.
  - `teams` (team): the Table loaded by Power Query `teams`, which reads `jobs` and `job_owners`.
- **Typed over a formula**: none. Keys holds no row.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet, and the D1 notes on Parameters and Keys (cells outside a Table). Parameters and Keys are empty and are never a source, step or final. Run 100, which `scheduler_runs` holds and `job_runs` does not, keeps the NULL run_id that the full outer join gives it in Power Query.
- **To fill in**: `<database>`, the database that holds the five source Tables.

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

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X50

### Map

- **Sources**:
  - `job_owners`, its typed columns job_id, team, owner, dt, read by final `owners`.
  - `jobs`, its typed columns job_id, job_name, team, region, read by final `owners`, through its formula column job_name.
- **Steps**: none. No query's M names another query.
- **Finals**: `owners` (job_id, owner, job_name, newest_first): the Table loaded by Power Query `owners`, which reads `job_owners` and removes duplicate rows. Its formula job_name reads `jobs`. Its formula newest_first reads its own job_id column, which does not count as a loop.
- **Typed over a formula**: none. Keys holds no row.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet, and the D1 notes on Parameters and Keys (cells outside a Table). Parameters and Keys are empty and are never a source, step or final.
- **To fill in**: `<database>`, the database that holds `job_owners` and `jobs`.

### Hive

```sql
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X59

### Map

- **Sources**: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), `jobs` (job_id, job_name) and `run_alerts` (alert_id, run_id, severity, dt), each its typed columns, read as `<database>.<table>`.
- **Steps**: none.
- **Finals**:
  - `jobs` (job_id, job_name, long_runs, failed_mins, not_test). No query loads it and no other formula reads it, so it is a final. Its typed columns come from `<database>.jobs`. Its three formulas count and sum over `job_runs`, so each is a LEFT JOIN to an aggregate of `job_runs`, with COALESCE(.., 0).
  - `run_alerts` (alert_id, run_id, severity, dt, alerts_so_far). No query loads it and nothing else reads it, so it is a final. Its typed columns come from `<database>.run_alerts`. alerts_so_far is a running count over its own Table, ties included, so it is COUNT(*) OVER with RANGE.
- **Typed over a formula**: none. Keys is empty, so it needs no row.
- **Marks**: none written. The blank status on job_runs row 98 is read by failed_mins and not_test, both inside -IFS forms, so status is written as it is and no COALESCE is needed. not_test counts that row, as Excel does.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty settings Tables. They are never a source, step or final, no formula reads Parameters, and no value is typed over a formula.
- **To fill in**: `<database>` in each read (`job_runs`, `jobs`, `run_alerts`).

### Hive

```sql
-- final: jobs
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
-- final: run_alerts
SELECT alert_id, run_id, severity, dt,
  COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X60

### Map

- **Sources**: `region_budgets` (job_id, budget_cents, region), its typed columns, read as `<database>.region_budgets`.
- **Steps**: none.
- **Finals**:
  - `region_budgets` (job_id, budget_cents, region, share, above_avg, rank_in_region). It is not a summary, since job_id is typed and never matched on. share divides by the whole-column SUM, above_avg compares with the whole-column AVG, both as OVER (). rank_in_region is an ascending RANK partitioned by region, which is what COUNTIFS with "<" plus 1 gives.
  - `region_budgets (Total Row)` (job_id, budget_cents). The Total Row has a total in two cells: job_id (SUBTOTAL 103, a COUNT) and budget_cents (SUBTOTAL 101, an AVG). It has no column for the "Total" label or the empty cells of share, above_avg and rank_in_region.
- **Typed over a formula**: none. Keys is empty.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty settings Tables, never a source, step or final.
- **To fill in**: `<database>` in each read (`region_budgets`, in the final and in its Total Row's CTE).

### Hive

```sql
-- final: region_budgets
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

```sql
-- final: region_budgets (Total Row)
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

- **Sources**: `region_costs` (job_id, cost_cents, region, dt), its typed columns, read as `<database>.region_costs`.
- **Steps**: none.
- **Finals**:
  - `by_region` (region, total_cents, entries, priciest). It is a summary: its only typed column, region, is the one its SUMIFS, COUNTIFS and MAXIFS match on. Its final query groups `region_costs` by region, with the typed groups 'eu' and 'us' typed in. total_cents is a SUM, entries a COUNT(*), priciest a MAX, each COALESCE(.., 0).
  - `by_region (Total Row)` (total_cents, entries, priciest). It has a total in each of its three numeric cells: SUBTOTAL 109 (SUM), 109 (SUM) and 104 (MAX). It has no column for the "Total" label.
- **Typed over a formula**: none. Keys is empty.
- **Marks**: none written. cost_cents is blank on region_costs row 29 (job 2, eu, 20260924). It is read only inside SUMIFS, COUNTIFS and MAXIFS, so it is written as it is: the sum and max skip it, and the count still counts that row, as Excel does.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty settings Tables, never a source, step or final.
- **To fill in**: `<database>` in each read (`region_costs`, in the summary's three subqueries and in the Total Row's CTE).

### Hive

```sql
-- final: by_region
SELECT g.region,
  COALESCE(s.total_cents, 0) AS total_cents,
  COALESCE(c.entries, 0) AS entries,
  COALESCE(m.priciest, 0) AS priciest
FROM (SELECT 'eu' AS region UNION ALL SELECT 'us') g
LEFT JOIN (
  SELECT region, SUM(cost_cents) AS total_cents
  FROM <database>.region_costs
  GROUP BY region
) s ON g.region = s.region
LEFT JOIN (
  SELECT region, COUNT(*) AS entries
  FROM <database>.region_costs
  GROUP BY region
) c ON g.region = c.region
LEFT JOIN (
  SELECT region, MAX(cost_cents) AS priciest
  FROM <database>.region_costs
  GROUP BY region
) m ON g.region = m.region
```

```sql
-- final: by_region (Total Row)
WITH by_region AS (
  SELECT g.region,
    COALESCE(s.total_cents, 0) AS total_cents,
    COALESCE(c.entries, 0) AS entries,
    COALESCE(m.priciest, 0) AS priciest
  FROM (SELECT 'eu' AS region UNION ALL SELECT 'us') g
  LEFT JOIN (
    SELECT region, SUM(cost_cents) AS total_cents
    FROM <database>.region_costs
    GROUP BY region
  ) s ON g.region = s.region
  LEFT JOIN (
    SELECT region, COUNT(*) AS entries
    FROM <database>.region_costs
    GROUP BY region
  ) c ON g.region = c.region
  LEFT JOIN (
    SELECT region, MAX(cost_cents) AS priciest
    FROM <database>.region_costs
    GROUP BY region
  ) m ON g.region = m.region
)
SELECT SUM(total_cents) AS total_cents, SUM(entries) AS entries, MAX(priciest) AS priciest
FROM by_region
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X62

### Map

- **Sources**: `team_notes` (team, note, written_on), its typed columns, read as `<database>.team_notes`.
- **Steps**: none.
- **Finals**:
  - `team_notes` (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short). No query loads it and nothing else reads it, so it is a final. Every formula reads only its own row or the Table's own typed dates, so the final is a plain SELECT with no join.
- **Typed over a formula**: none. Keys is empty.
- **Marks**: none. written_on is read as a date by the EOMONTH, DATEDIF and WEEKDAY formulas, and no formula reads a date held as text.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty settings Tables, never a source, step or final.
- **To fill in**: `<database>` in the read (`team_notes`).

### Hive

```sql
-- final: team_notes
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

- **Sources**:
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs), its typed columns, read as `<database>.job_runs`.
  - `scheduler_runs` (run_id, job_id, dt), its typed columns, read as `<database>.scheduler_runs`. Only run_id and job_id are used, by scheduled_job's lookup.
- **Steps**: none.
- **Finals**:
  - `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded). No query loads it and nothing else reads it, so it is a final. Its formulas:
    - no_retry: `avg_retry_secs IS NULL`, ISBLANK as it is.
    - quarters: FLOOR(duration_mins / 4), INT as FLOOR.
    - capped: LEAST(duration_mins, 25), MIN of one row's cells.
    - variance: VAR_SAMP(duration_mins) OVER (), VAR.S over the whole column.
    - weighted: SUM(duration_mins * job_id) OVER (), SUMPRODUCT over the whole column.
    - scheduled_job: a LEFT JOIN to scheduler_runs on run_id, with COALESCE(.., -1), since the XLOOKUP's fourth argument, -1, is the not-found value. Run 99 has no scheduler_runs row, so it gets -1.
    - label: CONCAT('run ', run_id).
    - succeeded: `INSTR(LOWER(COALESCE(status, '')), 'cess') > 0`, from ISNUMBER(SEARCH(..)).
- **Typed over a formula**: none. Keys is empty.
- **Marks**:
  - blank: status is blank on job_runs row 98. succeeded reads it inside SEARCH, not inside an -IF(S) form or ISBLANK, so status is written as COALESCE(status, ''). Excel's SEARCH gives an error there, so the result is FALSE, which this gives too.
- **Refusals**: none.
- **Left alone**: Parameters and Keys, both empty settings Tables, never a source, step or final. scheduler_runs' run 100 has no job_runs row, so no block reads it.
- **To fill in**: `<database>` in each read (`job_runs` and `scheduler_runs`).

### Hive

```sql
-- final: job_runs
SELECT jr.run_id, jr.job_id, jr.status, jr.duration_mins, jr.avg_retry_secs,
  jr.avg_retry_secs IS NULL AS no_retry,
  FLOOR(jr.duration_mins / 4) AS quarters,
  LEAST(jr.duration_mins, 25) AS capped,
  VAR_SAMP(jr.duration_mins) OVER () AS variance,
  SUM(jr.duration_mins * jr.job_id) OVER () AS weighted,
  COALESCE(sr.job_id, -1) AS scheduled_job,
  CONCAT('run ', jr.run_id) AS label,
  INSTR(LOWER(COALESCE(jr.status, '')), 'cess') > 0 AS succeeded
FROM <database>.job_runs jr
LEFT JOIN <database>.scheduler_runs sr ON jr.run_id = sr.run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X64

### Map

- Sources:
  - `<database>.jobs`: job_id, job_name, team, region (typed; no query loads it, so a source)
  - `<database>.region_costs`: job_id, cost_cents, region, dt (typed; no query loads it, so a source)
- Steps: none.
- Finals:
  - picked_costs (Table loaded by Power Query picked_costs): job_id, cost_cents, region, size
  - costed_jobs (Table loaded by Power Query costed_jobs): job_id, job_name, team, region
  - costs_filled (Table loaded by Power Query costs_filled): job_id, cost_cents, dt, day
- Each query's M names only Excel Tables, so no query is a step; each query is the query of its final Table.
- Typed over a formula: none (no formula column in this workbook).
- Marks:
  - blank: costs_filled reads cost_cents, which is blank in row 29 (job 2, 20260924); M's ReplaceValue fills it with 0, so COALESCE(cost_cents, 0).
- Refusals: none.
- Left alone: Parameters and Keys, both empty. No formula uses a fixed value and no value is typed over a formula, so neither is a source, step or final.
- `<...>` to fill in: `<database>` in each read of a source.

### Hive

```sql
-- picked_costs
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```
```sql
-- costed_jobs
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```
```sql
-- costs_filled
SELECT job_id, COALESCE(cost_cents, 0) AS cost_cents, dt, SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X65

### Map

- Sources:
  - `<database>.jobs`: job_id, job_name, team, region
  - `<database>.region_budgets`: job_id, budget_cents, region
  - `<database>.job_owners`: job_id, team, owner, dt
  - `<database>.scheduler_runs`: run_id, job_id, dt
  - `<database>.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt
- Steps: none (no Table has a formula column, and no query is named by another query's M).
- Finals:
  - team_regions (Table loaded by Power Query team_regions): team, region
  - budget_places (Table loaded by Power Query budget_places): job_id, budget_cents, region, place
  - jobs_per_team (Table loaded by Power Query jobs_per_team): team, jobs
  - ran_as_scheduled (Table loaded by Power Query ran_as_scheduled): run_id, dt
  - run_measures (Table loaded by Power Query run_measures): run_id, job_id, measure, amount
- Typed over a formula: none.
- Marks:
  - team_regions: the Table.Sort by team has no FirstN or index after it, so the order is dropped: no ORDER BY, and the sort is named as dropped.
  - run_measures: the Unpivot's nulls are dropped, as M drops them: each half has WHERE ... IS NOT NULL (the blank avg_retry_secs of run 98 has no row).
- Refusals: none.
- Left alone: Parameters and Keys, both empty.
- `<...>` to fill in: `<database>` in each read of a source.

### Hive

```sql
-- team_regions
SELECT t.team, r.region
FROM (SELECT DISTINCT team FROM <database>.jobs) t
CROSS JOIN (SELECT DISTINCT region FROM <database>.jobs) r
```
```sql
-- budget_places
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```
```sql
-- jobs_per_team
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```
```sql
-- ran_as_scheduled
SELECT run_id, dt FROM <database>.scheduler_runs
INTERSECT
SELECT run_id, dt FROM <database>.job_runs
```
```sql
-- run_measures
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

- Sources:
  - `<database>.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt
- Steps: none (Power Query ok_runs loads Table ok_runs and no other query names it).
- Finals:
  - ok_runs (Table loaded by Power Query ok_runs): run_id, job_id, duration_mins, dt, running, share
  - ok_runs (Total Row): duration_mins
- Table ok_runs is a final: no other Table's formula reads it, and its own formulas read its own row, which doesn't count.
- Typed over a formula: none.
- Marks:
  - running: SUMIFS over its own Table with job_id equal to this row's and dt "<=" this row's dt is a running total, written as a window with RANGE so ties are included as Excel's; COALESCE(.., 0) as Excel gives 0 where nothing matches.
  - share: the whole-column SUM(duration_mins) is written as SUM(...) OVER ().
  - Total Row: SUBTOTAL(109, ...) is a SUM; only duration_mins holds a total, so only that column is in its block.
- Refusals: none.
- Left alone: Parameters and Keys, both empty.
- `<...>` to fill in: `<database>`.

### Hive

```sql
-- ok_runs
WITH ok_rows AS (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT run_id, job_id, duration_mins, dt,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM ok_rows
```
```sql
-- ok_runs (Total Row)
WITH ok_rows AS (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
),
ok_runs AS (
  SELECT run_id, job_id, duration_mins, dt,
    COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
    duration_mins / SUM(duration_mins) OVER () AS share
  FROM ok_rows
)
SELECT SUM(duration_mins) AS duration_mins
FROM ok_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X69

### Map

- Sources:
  - `<database>.jobs`: job_id, job_name, team, region
  - `<database>.region_budgets`: job_id, budget_cents, region
  - `<database>.region_costs`: job_id, cost_cents, region, dt (its typed columns)
- Steps:
  - region_costs (Table with formula columns job_name, budget, over_budget, running_cost): read by the formulas of job_totals and by the query late_costs, so it is a step, a CTE in each final that reads it. Its columns: job_id, cost_cents, region, dt, job_name, budget, over_budget, running_cost.
- Finals:
  - job_totals (Table with formula columns total_cents and over_count; its only typed column is job_id, and its SUMIFS and COUNTIFS match on it, so it is a summary): job_id, total_cents, over_count
  - job_totals (Total Row): total_cents, over_count
  - late_costs (Table loaded by Power Query late_costs; no formula reads it): job_id, dt, running_cost
- Typed over a formula: none.
- Marks:
  - blank: region_costs' cost_cents is blank in row 29 (job 2, 20260924). over_budget compares it as Excel does, a blank as 0: COALESCE(cost_cents, 0) > budget. The SUMIFS sums (total_cents and running_cost) take the column as it is, as SUM skips NULL.
  - date held as text: dt is 20260911 text, read by running_cost's "<=" criteria. It is converted to 2026-09-11 with CONCAT(SUBSTR(..)) for the date order, so late_costs' dt shows 2026-09-22 where the sample shows 20260922.
  - summary: job_totals' typed job_ids 1, 2 and 3 are typed in, and its totals are GROUP BYs of region_costs.
  - running_cost: a running total over its own Table, ties included as Excel's (RANGE), with COALESCE(.., 0).
  - Total Row: total_cents and over_count each hold a SUBTOTAL(109, ...), so each is a column of the Total Row's block.
- Refusals: none.
- Left alone: Parameters and Keys, both empty.
- `<...>` to fill in: `<database>` in each read of a source.

### Hive

```sql
-- job_totals
WITH region_costs AS (
  SELECT job_id, cost_cents, region, dt, job_name, budget, over_budget,
    COALESCE(SUM(cost_cents) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM (
    SELECT r.job_id, r.cost_cents, r.region,
      CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) AS dt,
      j.job_name, b.budget_cents AS budget,
      COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget
    FROM <database>.region_costs r
    LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
    LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
  ) x
)
SELECT j.job_id,
  COALESCE(s.total_cents, 0) AS total_cents,
  COALESCE(c.over_count, 0) AS over_count
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, SUM(cost_cents) AS total_cents FROM region_costs GROUP BY job_id) s
  ON j.job_id = s.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS over_count FROM region_costs WHERE over_budget = TRUE GROUP BY job_id) c
  ON j.job_id = c.job_id
```
```sql
-- job_totals (Total Row)
WITH region_costs AS (
  SELECT job_id, cost_cents, region, dt, job_name, budget, over_budget,
    COALESCE(SUM(cost_cents) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM (
    SELECT r.job_id, r.cost_cents, r.region,
      CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) AS dt,
      j.job_name, b.budget_cents AS budget,
      COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget
    FROM <database>.region_costs r
    LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
    LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
  ) x
),
job_totals AS (
  SELECT j.job_id,
    COALESCE(s.total_cents, 0) AS total_cents,
    COALESCE(c.over_count, 0) AS over_count
  FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
  LEFT JOIN (SELECT job_id, SUM(cost_cents) AS total_cents FROM region_costs GROUP BY job_id) s
    ON j.job_id = s.job_id
  LEFT JOIN (SELECT job_id, COUNT(*) AS over_count FROM region_costs WHERE over_budget = TRUE GROUP BY job_id) c
    ON j.job_id = c.job_id
)
SELECT SUM(total_cents) AS total_cents, SUM(over_count) AS over_count
FROM job_totals
```
```sql
-- late_costs
WITH region_costs AS (
  SELECT job_id, cost_cents, region, dt, job_name, budget, over_budget,
    COALESCE(SUM(cost_cents) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM (
    SELECT r.job_id, r.cost_cents, r.region,
      CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) AS dt,
      j.job_name, b.budget_cents AS budget,
      COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget
    FROM <database>.region_costs r
    LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
    LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
  ) x
)
SELECT job_id, dt, running_cost
FROM region_costs
WHERE running_cost > 1500
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X70

### Map

- Sources:
  - `<database>.jobs`: job_id, job_name, team, region
  - `<database>.job_owners`: job_id, team, owner, dt
  - `<database>.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt
- Steps:
  - staffed (Power Query, connection only, named by owner_load's M): job_id, job_name, owner
  - owner_load (Power Query, named by busiest_owner's M, so a step; it also loads Table owner_load): owner, total_mins, runs
- Finals:
  - owner_load (Table loaded by query owner_load; no formula reads it, and its avg_mins reads its own row): owner, total_mins, runs, avg_mins
  - owner_load (Total Row): runs
  - busiest_owner (Table loaded by Power Query busiest_owner): owner, total_mins, runs
- Typed over a formula: none.
- Marks:
  - staffed: Table.Distinct with no column list is SELECT DISTINCT over job_id and owner; NestedJoin Inner is JOIN; the owner blank is dropped as M's `<> null` drops it: WHERE owner IS NOT NULL.
  - busiest_owner: Table.Sort by runs descending then FirstN 1: ORDER BY runs DESC LIMIT 1.
  - Total Row: SUBTOTAL(109, ...) is a SUM; only runs holds a total.
- Refusals: none.
- Left alone: Parameters and Keys, both empty.
- `<...>` to fill in: `<database>` in each read of a source.

### Hive

```sql
-- owner_load
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
```sql
-- owner_load (Total Row)
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
),
owner_load_table AS (
  SELECT owner, total_mins, runs, total_mins / runs AS avg_mins
  FROM owner_load
)
SELECT SUM(runs) AS runs
FROM owner_load_table
```
```sql
-- busiest_owner
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

- **Sources**: `region_budgets` (job_id, budget_cents, region) and `jobs` (job_id, job_name, team, region), read as `<database>.region_budgets` and `<database>.jobs`.
- **Steps**: query `eu_budgets` (job_id, budget_cents, region, job_name). Query `eu_count` names it in its M, so it is a CTE in the `eu_count` final. Its loaded Table is a final, not a step, since no formula reads it from another Table.
- **Finals**:
  - Table `eu_budgets` (job_id, budget_cents, region, job_name, dollars), loaded by query `eu_budgets`. Its rows are the query's, with `dollars` added.
  - Table `eu_count` (region, jobs, total_cents), loaded by query `eu_count`, a Table.Group over the step.
- **Typed over a formula**: none. Every `dollars` cell holds its formula.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: `Parameters` and `Keys`, both empty. No fixed value is read and no value is typed over a formula, so `Keys` needs no row. Neither has a role.
- **`<...>` to fill in**: `<database>`, in each source read.

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

- **Sources**: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), its typed columns, read as `<database>.job_runs` by the formulas of `run_alerts`.
- **Steps**: Table `run_alerts` (alert_id, run_id, severity, dt, status, job_id, alerts_so_far). Its formulas are read by the `by_status` formula and by query `late_alerts`, so it is a CTE in both finals. Its formulas read `job_runs` and its own typed `run_id`, not its own formula columns, so nothing is circular.
- **Finals**:
  - `by_status` (status, alerts). Its only typed column is the one its COUNTIFS match on, so it is a summary: a GROUP BY of `run_alerts`, with its typed statuses FAILED and SUCCESS typed in.
  - Table `late_alerts` (alert_id, run_id, alerts_so_far), loaded by query `late_alerts`. That query reads `run_alerts` and keeps alerts_so_far above 5. Nothing names the query, so it is not a step.
- **Typed over a formula**: none. Every formula cell in `run_alerts` and `by_status` holds its formula.
- **Marks**:
  - **blank**: `job_runs` row 98 has a blank status. The `run_alerts` status formula reads `job_runs[status]`, so the status is written `COALESCE(j.status, '')`.
- **Refusals**: none.
- **Left alone**: `Parameters` and `Keys`, both empty. Also `job_runs` row 98's blank avg_retry_secs, since no formula reads it.
- **`<...>` to fill in**: `<database>`, in each source read.

### Hive

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(j.status, '') AS status,
    j.job_id,
    COALESCE(COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs j ON a.run_id = j.run_id
)
SELECT g.status, COALESCE(c.alerts, 0) AS alerts
FROM (SELECT 'FAILED' AS status UNION ALL SELECT 'SUCCESS') g
LEFT JOIN (SELECT status, COUNT(*) AS alerts FROM run_alerts GROUP BY status) c
  ON g.status = c.status
```

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(j.status, '') AS status,
    j.job_id,
    COALESCE(COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
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

- **Sources**: `run_alerts` (alert_id, run_id, severity, dt), its typed columns, read as `<database>.run_alerts`.
- **Steps**: query `high_alerts` (alert_id, run_id, dt). Query `high_per_day` names it in its M, so it is a CTE in the `high_per_day` final.
- **Finals**:
  - Table `high_alerts` (alert_id, run_id, dt, late_run), loaded by query `high_alerts`. Its rows are the query's. `late_run` is a formula column, `run_id > 100` on the same row.
  - Table `high_per_day` (dt, alerts), loaded by query `high_per_day`, a Table.Group over the step. It has only typed columns and no COUNTIFS or SUMIFS, so it is not a summary.
- **Typed over a formula**: none. Every `late_run` cell holds its formula.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: `Parameters` and `Keys`, both empty. Neither has a role.
- **`<...>` to fill in**: `<database>`, in each source read.

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

- **Sources**: `region_costs` (job_id, cost_cents, region, dt), its typed columns, read as `<database>.region_costs`.
- **Steps**: query `known_costs` (job_id, cost_cents, dt). Query `cost_per_job` names it in its M, so it is a CTE in the `cost_per_job` final. The Table `known_costs` is not a step, since no formula reads it from another Table.
- **Finals**:
  - Table `known_costs` (job_id, cost_cents, dt, dollars), loaded by query `known_costs`. Its rows are the query's, with `dollars` added. All 27 `dollars` cells hold their formula.
  - `known_costs (Total Row)` (cost_cents). The Total Row's cells are a label, "Total", then `SUBTOTAL(109, known_costs[cost_cents])`, then two empty cells. So it has one column, cost_cents, as a SUM, and reads the Table's final query as a CTE.
  - Table `cost_per_job` (job_id, total_cents), loaded by query `cost_per_job`, a Table.Group over the step.
- **Typed over a formula**: none.
- **Marks**: none. `dt` holds dates as text such as 20260911, but no formula reads it, so it is kept as typed.
- **Refusals**: none.
- **Left alone**: `Parameters` and `Keys`, both empty. Neither has a role. Not marks: row 29 of `region_costs` has a blank cost_cents and is left out by the query's `cost_cents IS NOT NULL`, which is M's `<> null`. The query also drops `region`.
- **`<...>` to fill in**: `<database>`, in each source read.

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

## X80

### Map

- **Sources**: `job_runs` (run_id, job_id, duration_mins), its typed columns, read as `<database>.job_runs`.
- **Steps**: none.
- **Finals**: Table `job_runs` (run_id, job_id, duration_mins, look). Its `look` formula reads only its own row, and no other Table or query reads the Table, so it is a final.
- **Typed over a formula**: none. Every `look` cell holds its formula.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: `Parameters` and `Keys`, both empty. Neither has a role.
- **`<...>` to fill in**: `<database>`, in the source read.

### Hive

```sql
SELECT run_id, job_id, duration_mins,
  IF(((duration_mins > 20 AND job_id <> 3) OR NOT (job_id = 2)), 'look', 'fine') AS look
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X83

**Map**

- **Sources:** job_runs, its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, read as `<database>.job_runs`. No query loads it and it has no formula column, so it is a source only.
- **Steps:** none.
- **Finals:** by_day, a summary. Its only typed column, dt, is the one its COUNTIFS and SUMIFS match on, and nothing else reads it. Columns: dt, kept_runs, short_mins, success_or_failed. Its typed rows are kept as its groups, '2026-09-23' and '2026-09-24', typed in.
- **Settings, never a source, step or final:** Parameters (empty; no formula reads it) and Keys (empty; no value typed over a formula, so no row is needed).
- **Values typed over a formula:** none.
- **Marks:** none. The blank status in job_runs row 98 is left as it is, since it sits inside COUNTIFS conditions, which skip a blank as written.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the D1 notes on the Parameters and Keys sheets, as cells outside a Table.
- **To fill in:** `<database>`, in each of the three subqueries of the by_day block.

**Hive**

```sql
SELECT d.dt,
  COALESCE(k.kept_runs, 0) AS kept_runs,
  COALESCE(s.short_mins, 0) AS short_mins,
  COALESCE(f.success_or_failed, 0) AS success_or_failed
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (
  SELECT dt, COUNT(*) AS kept_runs
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL) AND status IS NOT NULL
  GROUP BY dt
) k ON d.dt = k.dt
LEFT JOIN (
  SELECT dt, SUM(duration_mins) AS short_mins
  FROM <database>.job_runs
  WHERE duration_mins < 20
  GROUP BY dt
) s ON d.dt = s.dt
LEFT JOIN (
  SELECT dt, COUNT(*) AS success_or_failed
  FROM <database>.job_runs
  WHERE status IN ('SUCCESS', 'FAILED')
  GROUP BY dt
) f ON d.dt = f.dt
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X84

**Map**

- **Sources:** job_runs, its typed columns run_id, job_id, status and duration_mins, read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** job_runs, columns run_id, job_id, status, duration_mins, flag, job2_short and failed_or_test_mins. No other Table's formula or query reads it, so it is a final. Its formulas use IF and SUMPRODUCT, not SUMIFS or COUNTIFS, so it is not a summary. Its formulas read its own rows and columns only.
- **Settings, never a source, step or final:** Parameters (empty; no formula reads it) and Keys (empty; no value typed over a formula, so no row is needed).
- **Values typed over a formula:** none. Every formula cell holds its formula.
- **Marks:** blank. The status cell in job_runs row 98 is blank, and failed_or_test_mins reads status, so it is written as COALESCE(status, '').
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the D1 notes on the Parameters and Keys sheets, as cells outside a Table.
- **To fill in:** `<database>`, in the FROM of the job_runs block.

**Hive**

```sql
SELECT run_id, job_id, status, duration_mins,
  IF((job_id = 2 AND duration_mins < 20 OR job_id = 3 AND NOT duration_mins >= 30), 'review', '') AS flag,
  COUNT(CASE WHEN job_id = 2 AND duration_mins < 20 THEN 1 END) OVER () AS job2_short,
  SUM(CASE WHEN COALESCE(status, '') IN ('FAILED', 'TEST') THEN duration_mins ELSE 0 END) OVER () AS failed_or_test_mins
FROM <database>.job_runs
```

**Next**

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
