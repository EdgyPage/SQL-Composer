date: 2026-11-01
arm: C
model: haiku
files: 24-held

## X21

### Map

- Sources: `<database>.region_budgets`, its typed columns job_id, budget_cents, region.
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin). No query loads region_budgets and nothing reads it but its own formula columns, so it is a final.
- Values written in: none.
- Values typed over a formula: none. Keys has no row, as no value is typed over a formula.
- Marks: none.
- Refusals: none.
- Left alone: Parameters (empty, no formula reads it, never a source, step or final); Keys (empty, never a source, step or final); the Steps sheet (text, not an Excel Table or Power Query).
- To fill in: `<database>` in the FROM.

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

- Sources: `<database>.jobs`, its typed columns job_id, job_name, team.
- Steps: none.
- Finals: jobs (job_id, job_name, team, is_finance, ratio). No query loads jobs and nothing reads it but its own formula columns, so it is a final.
- Values written in: none.
- Values typed over a formula: none. Keys has no row.
- Marks: none. Note, not a file 11 mark: Excel's `=` ignores case and Hive's does not. The sample's team values are all lowercase, so the Hive matches them; check the case of team in the full table.
- Refusals: none.
- Left alone: Parameters (empty, never a source, step or final); Keys (empty, never a source, step or final).
- To fill in: `<database>` in the FROM.

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

- Sources: `<database>.job_runs`, its typed columns run_id, status, avg_retry_secs.
- Steps: none.
- Finals: job_runs (run_id, status, avg_retry_secs, label, risky). No query loads job_runs and nothing reads it but its own formula columns, so it is a final.
- Values written in: none.
- Values typed over a formula: none. Keys has no row.
- Marks:
  - blank: run 98 has a blank status, which label and risky read, so `COALESCE(status, '')`; it has a blank avg_retry_secs, which risky reads in a plain comparison (not an -IF(S) form), so `COALESCE(avg_retry_secs, 0)`.
  - Note, not a file 11 mark: Excel's SWITCH and `=` ignore case and Hive's do not. The sample's statuses are all uppercase; check the full table.
- Refusals: none.
- Left alone: Parameters (empty, never a source, step or final); Keys (empty, never a source, step or final).
- To fill in: `<database>` in the FROM.

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

- Sources: `<database>.team_notes`, its typed columns team, note, written_on.
- Steps: none.
- Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars). No query loads team_notes and nothing reads it but its own formula columns, so it is a final.
- Values written in: none.
- Values typed over a formula: none. Keys has no row.
- Marks: none. Note: written_on's values are dates in the 2026-09-11 form, which MONTH reads as they are.
- Refusals: none.
- Left alone: Parameters (empty, never a source, step or final); Keys (empty, never a source, step or final).
- To fill in: `<database>` in the FROM.

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

## X26

### Map

- **Sources**: `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt); `run_alerts` (its typed columns: alert_id, run_id, severity), read by its final.
- **Steps**: none.
- **Finals**: Table `run_alerts` (alert_id, run_id, severity, job_id, status, avg_mins). No other Table's formula or query reads it, so it is a final. job_id is an XLOOKUP on job_runs, so a LEFT JOIN; status is a VLOOKUP on job_runs' column 3 (status), so a LEFT JOIN; avg_mins is an AVERAGEIFS over another Table, so a LEFT JOIN to a subquery of AVG, left NULL where no row matches.
- **Roles of the rest**: `job_runs` has only typed columns and no query loads it, so it is a source only. `Parameters` and `Keys` are settings Tables (both empty), never a source, step or final.
- **Values written in**: none, as Parameters is empty.
- **Values typed over a formula**: none. Every job_id, status and avg_mins cell of run_alerts is a formula, and Keys is empty, so no Keys row is needed.
- **Marks**: blank. job_runs' status is blank in the sample (run 98), and the VLOOKUP for status reads that column, so status is written `COALESCE(v.status, '')`.
- **Refusals**: none.
- **Left alone**: Parameters and Keys (empty settings Tables); sheet "Steps" (not a Table).
- **`<...>` to fill in**: `<database>`, in the FROM and in each join.

### Hive

```sql
SELECT r.alert_id, r.run_id, r.severity,
  j.job_id,
  COALESCE(v.status, '') AS status,
  a.avg_mins
FROM <database>.run_alerts r
LEFT JOIN <database>.job_runs j ON r.run_id = j.run_id
LEFT JOIN <database>.job_runs v ON r.run_id = v.run_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_mins FROM <database>.job_runs GROUP BY job_id) a
  ON j.job_id = a.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X27

### Map

- **Sources**: `jobs` (its typed columns: job_id, job_name, team, region). It has only typed columns and no query loads it, so it is a source only.
- **Steps**: none.
- **Finals**: Table `by_team`, a summary. Its only typed column, team, is the one its COUNTIFS match on, so its final is a GROUP BY of jobs with its typed groups kept (typed in). Columns: team, jobs_in_team, last_job_id, last_job_name. No other piece reads by_team, so it is a final.
- **Roles of the rest**: `Parameters` and `Keys` are settings Tables (both empty), never a source, step or final.
- **Values written in**: the summary's groups, `data`, `finance` and `web`, written into the Hive. A later team won't be in the table.
- **Values typed over a formula**: none. Every formula cell of by_team is a formula, and Keys is empty.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: Parameters and Keys (empty settings Tables); sheet "Steps" (not a Table).
- **`<...>` to fill in**: `<database>`, in each read of jobs.

### Hive

```sql
SELECT g.team,
  COALESCE(c.jobs_in_team, 0) AS jobs_in_team,
  COALESCE(m.last_job_id, 0) AS last_job_id,
  n.job_name AS last_job_name
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') g
LEFT JOIN (SELECT team, COUNT(*) AS jobs_in_team FROM <database>.jobs GROUP BY team) c
  ON g.team = c.team
LEFT JOIN (SELECT team, MAX(job_id) AS last_job_id FROM <database>.jobs GROUP BY team) m
  ON g.team = m.team
LEFT JOIN <database>.jobs n
  ON COALESCE(m.last_job_id, 0) = n.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X28

### Map

- **Sources**: `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt), read for ok_mins; `jobs` (its typed columns: job_id, job_name), read by its final.
- **Steps**: none.
- **Finals**: Table `jobs` (job_id, job_name, ok_mins). No other piece reads it, so it is a final. It is not a summary, as job_name is typed and its SUMIFS doesn't match on it. ok_mins is a SUMIFS over another Table, so a LEFT JOIN to a subquery of SUM where status is 'SUCCESS', with COALESCE to 0.
- **Roles of the rest**: `job_runs` has only typed columns and no query loads it, so it is a source only. `Parameters` is an empty settings Table, never a source, step or final. `Keys` is a settings Table; its one row (jobs, job_id) sets how the typed-over value is matched.
- **Values written in**: none.
- **Values typed over a formula**: ok_mins on the row for job_id 3 (report_build) is typed as 99. Keys names jobs with job_id, so the value is a CASE on job_id = 3.
- **Marks**: none converted. The blank status in run 98 is skipped by the `status = 'SUCCESS'` condition, as Excel skips it, so it is written as it is.
- **Refusals**: none.
- **Left alone**: Parameters (empty) and Keys (settings Tables); sheet "Steps" (not a Table).
- **`<...>` to fill in**: `<database>`, in each read of jobs and job_runs.

### Hive

```sql
SELECT j.job_id, j.job_name,
  CASE WHEN j.job_id = 3 THEN 99 ELSE COALESCE(s.total, 0) END AS ok_mins
FROM <database>.jobs j
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total FROM <database>.job_runs WHERE status = 'SUCCESS' GROUP BY job_id) s
  ON j.job_id = s.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X29

### Map

- **Sources**: `region_budgets` (its typed columns: job_id, budget_cents, region), read by its final.
- **Steps**: none.
- **Finals**: Table `region_budgets` (job_id, budget_cents, region, in_dollars, pointer). No other piece reads it and it is not a summary, so it is a final.
- **Roles of the rest**: `Parameters` is a settings Table, never a source, step or final; its value is written into the Hive below. `Keys` is an empty settings Table.
- **Values written in**: `cents_per_dollar` = 100 from Parameters, written into in_dollars as `/ 100`. Change it in Parameters and this table won't follow, so the Hive's 100 needs the new value too.
- **Values typed over a formula**: in_dollars on the row for job_id 3 (budget_cents 350, region us) is typed as 5. Keys has no row for region_budgets, so there is no Keys row: the CASE matches every typed column of the row (job_id, budget_cents, region).
- **Marks**: none beyond the written-in value above.
- **Refusals**: `pointer`, written `NULL AS pointer`. Its formula is `INDIRECT("A"&ROW())`: INDIRECT is refused, and ROW() hangs on the order of the sheet's rows.
- **Left alone**: Parameters and Keys (settings Tables); sheet "Steps" (not a Table).
- **`<...>` to fill in**: `<database>`.

### Hive

```sql
SELECT job_id, budget_cents, region,
  CASE WHEN job_id = 3 AND budget_cents = 350 AND region = 'us' THEN 5 ELSE budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X31

### Map

- **Sources:** `jobs`, its typed columns `job_id` and `team`, read as `<database>.jobs`.
- **Steps:** none.
- **Finals:** `jobs` (`job_id`, `team`, `bump`, `tag`, `scaled`, `boosted`). Its Table has formula columns, no query loads it, and nothing else reads it, so it is a final. Parameters and Keys are never a source, step or final.
- **Values written in:** `boosted` reads the defined name `boost`, which is `Summary!B2`, a cell outside a Table. Its value 10 is written into the Hive. Move `boost` into Parameters, since a change to Summary won't reach the Hive.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** `boosted`, from the `boost` value written in above.
- **Refusals (NULL in its place):**
  - `bump`: `NULL AS bump`. Its formula reads its own column (circular).
  - `tag`: `NULL AS tag`. `TAG` is a LAMBDA, a defined name holding a formula.
  - `scaled`: `NULL AS scaled`. It reads `Summary!D4`, a cell outside a Table that is not a defined name.
- **Left alone:** Parameters and Keys, which are empty settings Tables. The rest of Summary and the Steps sheet's text, which are cells outside a Table.
- **To fill in:** `<database>`, the database that holds `jobs`.

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

- **Sources:** `jobs` (`job_id`, `job_name`, `team`, `region`) and `job_runs` (its typed columns `run_id`, `job_id`, `status`, `duration_mins`, `avg_retry_secs`, `dt`), read as `<database>.jobs` and `<database>.job_runs`.
- **Steps:** `job_runs` (`run_id`, `job_id`, `status`, `duration_mins`, `avg_retry_secs`, `dt`, `job_name`). Its formula column is read by `by_name`, so it is a CTE in `by_name`'s block.
- **Finals:** `by_name` (`job_name`, `runs`). Its only typed column is the one its COUNTIFS match on, so it is a summary: its final is a GROUP BY of `job_runs`, with its typed rows kept.
- **Values written in:** `by_name`'s typed groups `invoice_sync`, `nightly_load` and `report_build`. A later job won't be in this table, and `cache_warm` has no row here, so it is not in the Hive.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** `job_runs.job_name`. Its VLOOKUP has TRUE, which is approximate; it is written as the exact match on `job_id`.
- **Refusals:** none.
- **Left alone:** the blank `status` and `avg_retry_secs` in row 98. No formula reads them, so they stay as they are. Parameters and Keys are empty.
- **To fill in:** `<database>`, the database that holds `job_runs` and `jobs`.

### Hive

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

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X33

### Map

- **Sources:** `job_runs`, read as `<database>.job_runs`. It is the table `job_runs` in schema `ops`, which the M reads from `Sql.Database("dwh01", "ops")`.
- **Steps:** none. Parameters and Keys are empty.
- **Finals:** `slow_runs` (`run_id`, `duration_mins`, `over_by`). It is the Table loaded by Power Query `slow_runs`, and no formula reads it, so its rows are the query's rows. The typed sample rows are not typed in.
- **Values written in:** none.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** the `Sql.Database("dwh01", "ops")` read. The query reads table `ops.job_runs` on server `dwh01`, which is named here for you to check that it is the right table.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, which are empty.
- **To fill in:** `<database>`, the database that holds `job_runs` on `dwh01`.

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

- **Sources:** `job_runs` (`run_id`, `job_id`, `status`, `duration_mins`, `avg_retry_secs`, `dt`) and `jobs` (`job_id`, `job_name`, `team`, `region`), their typed columns, read as `<database>.job_runs` and `<database>.jobs`.
- **Steps:** `runs_with_team`, the Power Query that loads nothing and is read by `team_totals`. It is a CTE in `team_totals`' block, with columns `run_id`, `job_id`, `status`, `duration_mins`, `avg_retry_secs`, `dt`, `team`.
- **Finals:** `team_totals` (`team`, `total_mins`, `longest`). It is the Table loaded by Power Query `team_totals`, and no formula reads it, so its rows are the query's rows.
- **Values written in:** none. `team_totals` has no formula, so it is not a summary, and nothing is typed in.
- **Values typed over a formula:** none. Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys, which are empty.
- **To fill in:** `<database>`, the database that holds `job_runs` and `jobs`.

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

## X36

### Map

**Sources**
- `run_alerts` (alert_id, run_id, severity, dt): typed columns only, read as `<database>.run_alerts`. Read by job_runs' alerts formula and by Power Query severity_by_day.

**Steps**
- None. Power Query severity_by_day is the rows of its final, not a step.

**Finals**
- `job_runs` (run_id, status, alerts): alerts is COUNTIFS over run_alerts, written as a LEFT JOIN count over `<database>.run_alerts`, with COALESCE to 0. No other piece reads job_runs, so it is a final.
- `severity_by_day` (dt, high, low): the rows of Power Query severity_by_day, a pivot of run_alerts, read from `<database>.run_alerts`. No other Table's formula reads severity_by_day, so the Table is a final.

**Left alone**
- `Parameters`: empty, and no formula reads it; never a source, step or final.
- `Keys`: empty, with no value typed over a formula, so no row is needed.

**Values written in:** none.

**Values typed over a formula:** none.

**Marks**
- severity_by_day (Table.Pivot): the pivot's columns high and low are now fixed to the severities in the sample. A new severity needs its own column. The Hive counts THEN 1, as n is 1 on every row. A day with no row of a severity gives NULL, as M leaves it.

**Refusals:** none.

**Left to fill in:** `<database>` in both blocks.

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
- `Owners` (Job No, Team Name, Owner, Day): typed columns, read as `<database>.Owners`.

**Steps**
- None.

**Finals**
- `Owners` (`<job_no>`, `<team_name>`, owner, day, `<is_ana>`): its Is Ana formula reads only its own row's Owner, which does not count, and no query or other Table reads it, so it is a final.

**Left alone**
- `Parameters`: empty, and no formula reads it; never a source, step or final.
- `Keys`: empty, with no value typed over a formula, so no row is needed.

**Values written in:** none.

**Values typed over a formula:** none; every Is Ana cell holds the formula.

**Marks**
- blank: Owner is blank on the web rows (Job No 4), and the Is Ana formula reads Owner. Written as `COALESCE(owner, '')`, so a blank counts as not "ana", as Excel's blank = "ana" gives FALSE.

**Refusals:** none.

**Left to fill in:** `<database>`, `<job_no>`, `<team_name>`, `<is_ana>`.

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
- `jobs` (job_id, job_name, team, region): typed columns only, read as `<database>.jobs`.
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs): its typed columns, read as `<database>.job_runs`.

**Steps**
- None.

**Finals**
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost):
  - region: XLOOKUP of job_id into jobs, written as a LEFT JOIN on jobs, then jobs' region. `_xlfn.` is read past.
  - region_mins: SUMIFS over its own Table on region, written as a SUM window partitioned by the joined region, with COALESCE to 0.
  - retry_cost: its formula, with avg_retry_secs' blank written as COALESCE.
  - No other piece reads job_runs, so it is a final.

**Left alone**
- `Parameters`: empty, and no formula reads it; never a source, step or final.
- `Keys`: read for the typed-over value below (job_runs, run_id).

**Values written in:** none.

**Values typed over a formula**
- retry_cost where run_id is 102 is typed as 1. The CASE matches on run_id, the column Keys names for job_runs.

**Marks**
- blank: avg_retry_secs is blank at run_id 98, and retry_cost reads it. Written as `COALESCE(r.avg_retry_secs, 0)`, so that row gives 30.

**Refusals:** none.

**Left to fill in:** `<database>`.

### Hive

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, j.region,
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
- `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed columns only, read as `<database>.job_runs`.
- `jobs` (job_id, job_name, team, region): typed columns only, read as `<database>.jobs`.

**Steps**
- None.

**Finals**
- `ok_runs` (run_id, job_id, duration_mins, job_name, share, noise): the rows of Power Query ok_runs, which are the job_runs rows with status SUCCESS. Read from `<database>.job_runs`, filtered by WHERE, so the Power Query is folded into this final and is not a step.
  - job_name: XLOOKUP of job_id into jobs, written as a LEFT JOIN on jobs.
  - share: SUMIFS over its own rows by job_id, written as a SUM window partitioned by job_id after the filter, with COALESCE to 0.
  - noise: refused.

**Left alone**
- `Parameters`: empty, and no formula reads it; never a source, step or final.
- `Keys`: empty, with no value typed over a formula, so no row is needed.

**Values written in:** none.

**Values typed over a formula:** none.

**Marks**
- None. Run 98's blank status is left out by the WHERE, as M's `=` leaves it out too.

**Refusals**
- noise: `=RAND()` is random and has no Hive, so `NULL AS noise`.

**Left to fill in:** `<database>`.

### Hive

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name,
  r.duration_mins / COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id), 0) AS share,
  NULL AS noise
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
WHERE r.status = 'SUCCESS'
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X46

### Map
- **Sources**: `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (its typed columns: job_id, job_name, team), read by the final below.
- **Steps**: none.
- **Finals**: `jobs` (job_id, job_name, team, shortest, runs, busiest). No query loads it and no other Table's formula reads it, so it is a final. Its formulas: `shortest` is `_xlfn.MINIFS` over job_runs, a LEFT JOIN with COALESCE(.., 0); `runs` is COUNTIF over job_runs, a LEFT JOIN with COALESCE(.., 0); `busiest` is RANK.EQ over `runs`, ascending order not asked, so `RANK() OVER (ORDER BY runs DESC)`.
- **Settings, never a source, step or final**: `Parameters` (name, value) and `Keys` (table, key_columns). Both are empty, so no value is read in and no Keys row is needed.
- **Values written in**: none.
- **Values typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet, and the D1 notes of the Parameters and Keys sheets (cells outside a Table).
- **To fill in**: `<database>`, the database name in each FROM and JOIN.

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
- **Sources**: `region_budgets` (its typed columns: job_id, budget_cents, region), read by the final below.
- **Steps**: none.
- **Finals**: `region_budgets` (job_id, budget_cents, region, cheapest_first, region_total, region_avg). No query loads it and no other Table's formula reads it, so it is a final. Its formulas: `cheapest_first` is RANK.EQ with 1 as the third argument, so ascending: `RANK() OVER (ORDER BY budget_cents ASC)`; `region_total` is SUMIF over its own region column, a window SUM with COALESCE(.., 0); `region_avg` is AVERAGEIF over its own region column, a window AVG, left NULL with no COALESCE.
- **Settings, never a source, step or final**: `Parameters` (name, value) and `Keys` (table, key_columns). Both are empty, so no value is read in and no Keys row is needed.
- **Values written in**: none.
- **Values typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet, and the D1 notes of the Parameters and Keys sheets (cells outside a Table).
- **To fill in**: `<database>`, the database name in the FROM.

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
- **Sources**: `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt); `jobs` (its typed columns: job_id, job_name, team, region); `run_alerts` (its typed columns: alert_id, run_id, severity, dt). No query loads any of them.
- **Steps**: none. Power Query `quiet_runs` and Power Query `slow_regions` are named in no other query's M, so neither is a step.
- **Finals**:
  - `quiet_runs` (run_id, job_id, status). Excel Table `quiet_runs` is loaded by Power Query `quiet_runs`, and no formula reads it, so the Table is a final with the query's rows: job_runs rows with no run_alerts row (a LeftAnti join, job_runs' columns only).
  - `slow_regions` (region, avg_mins, fastest). Excel Table `slow_regions` is loaded by Power Query `slow_regions`, and no formula reads it, so the Table is a final with the query's rows: job_runs inner-joined to jobs, grouped by region, kept where avg_mins is at least 20.
- **Settings, never a source, step or final**: `Parameters` and `Keys`, both empty.
- **Values written in**: none.
- **Values typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet, and the D1 notes of the Parameters and Keys sheets (cells outside a Table).
- **To fill in**: `<database>`, the database name in each FROM and JOIN.

### Hive
```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a
  ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

```sql
SELECT j.region, AVG(r.duration_mins) AS avg_mins, MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j
  ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X49

### Map
- **Sources**: `job_runs` (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt); `run_alerts` (alert_id, run_id, severity, dt); `scheduler_runs` (run_id, job_id, dt); `jobs` (job_id, job_name, team, region); `job_owners` (job_id, team, owner, dt). No query loads any of them.
- **Steps**: none. Power Query `alert_status`, `run_check` and `teams` are named in no other query's M, so none is a step.
- **Finals**:
  - `alert_status` (alert_id, severity, status). Excel Table `alert_status` is loaded by Power Query `alert_status`, and no formula reads it, so the Table is a final with the query's rows: job_runs right-joined to run_alerts, so FROM job_runs LEFT JOIN run_alerts, keeping alert_id, severity and status.
  - `run_check` (run_id, status, scheduled_run). Excel Table `run_check` is loaded by Power Query `run_check`, and no formula reads it, so it is a final: job_runs (run_id, status) full-outer-joined to scheduler_runs on run_id; scheduled_run is scheduler_runs' run_id.
  - `teams` (team). Excel Table `teams` is loaded by Power Query `teams`, and no formula reads it, so it is a final: the distinct team values of jobs and job_owners, a UNION.
- **Settings, never a source, step or final**: `Parameters` and `Keys`, both empty.
- **Values written in**: none.
- **Values typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**: the Steps sheet, and the D1 notes of the Parameters and Keys sheets (cells outside a Table).
- **To fill in**: `<database>`, the database name in each FROM and JOIN.

### Hive
```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a
  ON a.run_id = r.run_id
```

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM (SELECT run_id, status FROM <database>.job_runs) r
FULL OUTER JOIN <database>.scheduler_runs s
  ON r.run_id = s.run_id
```

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X59

### Map
- Sources: job_runs (its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (its typed columns: job_id, job_name); run_alerts (its typed columns: alert_id, run_id, severity, dt).
- Steps: none.
- Finals: run_alerts (alert_id, run_id, severity, dt, alerts_so_far), a running count over its own run_id with ties counted as Excel does; jobs (job_id, job_name, long_runs, failed_mins, not_test), its three COUNTIFS and SUMIFS read job_runs by a LEFT JOIN.
- Values written in: none. Parameters is empty, so no fixed value is written in.
- Values typed over a formula: none. Keys is empty.
- Marks: none. The blank status in job_runs (run 98) sits inside COUNTIFS's "<>TEST" form, so it is written as it is, and the form counts it as Excel does.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables, never a source, step or final, so no block.
- To fill in: `<database>`, in each block.

### Hive

```sql
SELECT alert_id, run_id, severity, dt,
  COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts
```

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

### Next
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X60

### Map
- Sources: region_budgets (its typed columns: job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region); region_budgets (Total Row) (job_id, budget_cents), its Total Row's COUNT of job_id and AVG of budget_cents. The "Total" label and the empty cells get no column.
- Values written in: none. Parameters is empty.
- Values typed over a formula: none. Keys is empty.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables, never a source, step or final, so no block.
- Note: share, above_avg and the Total Row's whole-column totals read `<database>.region_budgets`, the whole table, not the sample in the workbook.
- To fill in: `<database>`, in each block.

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
- Sources: region_costs (its typed columns: job_id, cost_cents, region, dt).
- Steps: none.
- Finals: by_region (region, total_cents, entries, priciest), a summary of region_costs, since its only typed column, region, is the one its SUMIFS, COUNTIFS and MAXIFS match on; by_region (Total Row) (total_cents, entries, priciest): SUM of total_cents, SUM of entries, MAX of priciest. The "Total" label gets no column.
- Values written in: the summary's groups, 'eu' and 'us', typed into the Hive from by_region's typed rows. A later region won't be in the table.
- Values typed over a formula: none. Keys and Parameters are empty.
- Marks: none. The blank cost_cents in region_costs (job 2, eu, 2026-09-24) sits inside SUMIFS and MAXIFS, so it is written as it is; SUM and MAX skip it, as Excel does. The _xlfn. prefix on MAXIFS is read past.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables, never a source, step or final, so no block.
- To fill in: `<database>`, in each block.

### Hive

```sql
SELECT g.region,
  COALESCE(s.total_cents, 0) AS total_cents,
  COALESCE(c.entries, 0) AS entries,
  COALESCE(m.priciest, 0) AS priciest
FROM (SELECT 'eu' AS region UNION ALL SELECT 'us') g
LEFT JOIN (SELECT region, SUM(cost_cents) AS total_cents FROM <database>.region_costs GROUP BY region) s
  ON g.region = s.region
LEFT JOIN (SELECT region, COUNT(*) AS entries FROM <database>.region_costs GROUP BY region) c
  ON g.region = c.region
LEFT JOIN (SELECT region, MAX(cost_cents) AS priciest FROM <database>.region_costs GROUP BY region) m
  ON g.region = m.region
```

```sql
WITH by_region AS (
  SELECT g.region,
    COALESCE(s.total_cents, 0) AS total_cents,
    COALESCE(c.entries, 0) AS entries,
    COALESCE(m.priciest, 0) AS priciest
  FROM (SELECT 'eu' AS region UNION ALL SELECT 'us') g
  LEFT JOIN (SELECT region, SUM(cost_cents) AS total_cents FROM <database>.region_costs GROUP BY region) s
    ON g.region = s.region
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
- Sources: team_notes (its typed columns: team, note, written_on).
- Steps: none.
- Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short). Its formulas are over its own row, and nothing else reads it, so it is a final.
- Values written in: none. Parameters is empty.
- Values typed over a formula: none. Keys is empty.
- Marks: none. written_on holds ISO dates with dashes, so no text-date conversion applies.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables, never a source, step or final, so no block.
- To fill in: `<database>`, in the block.

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

## X64

### Map

- **Sources** (read as `<database>.<table>`; no query loads them, so they are never finals):
  - `jobs`: job_id, job_name, team, region
  - `region_costs`: job_id, cost_cents, region, dt
- **Steps**: none. No query's M names another query, and no formula reads a Table.
- **Finals** (each Table is loaded by a query, and no formula reads it, so each is a final with the query's rows):
  - `picked_costs`: job_id, cost_cents, region, size
  - `costed_jobs`: job_id, job_name, team, region
  - `costs_filled`: job_id, cost_cents, dt, day
- **Values written in**: none. Parameters is empty and no formula reads it.
- **Values typed over a formula**: none. There are no formula columns, and Keys is empty, so no Keys row is needed.
- **Marks**:
  - `costs_filled`: the blank cost_cents on region_costs row 29 becomes 0, as the query's Table.ReplaceValue does (COALESCE(cost_cents, 0)). Hive gives NULL for that blank without it.
  - `costs_filled`: dt is read as text (Text.End), so keep dt a STRING column.
- **Refusals**: none.
- **Left alone**: the Steps sheet and the D1 notes, which are cells outside a Table. Parameters and Keys are empty settings Tables and are never a source, step or final. The workbook has no charts, PivotTables or Total Rows.
- **To fill in**: `<database>`, in the FROM of each final (both sources live in it).

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

**Sources** (each read as `<database>.<table>`, never from its sample rows):
- `<database>.jobs`: job_id, job_name, team, region. Read by team_regions.
- `<database>.region_budgets`: job_id, budget_cents, region. Read by budget_places.
- `<database>.job_owners`: job_id, team, owner, dt. Read by jobs_per_team.
- `<database>.scheduler_runs`: run_id, job_id, dt. Read by ran_as_scheduled.
- `<database>.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read by ran_as_scheduled and run_measures.

**Steps:** none. No Table has a formula column, and no query's M names another query.

**Finals** (each is a Table loaded by its own query; its rows are the query's; columns in the Table's order):
- `team_regions` (team, region), loaded by Power Query team_regions.
- `budget_places` (job_id, budget_cents, region, place), loaded by Power Query budget_places.
- `jobs_per_team` (team, jobs), loaded by Power Query jobs_per_team.
- `ran_as_scheduled` (run_id, dt), loaded by Power Query ran_as_scheduled.
- `run_measures` (run_id, job_id, measure, amount), loaded by Power Query run_measures.

No Table has a Total Row, so there is no `(Total Row)` final. No Table is a summary.

**Settings, never a source, step or final:** Parameters (name, value) and Keys (table, key_columns). Both are empty.

**Values written in:** none. No Parameters value is read, and no summary's groups are typed in.

**Values typed over a formula:** none. No Table has a formula column, so no Keys row is needed.

**Marks:** none.

**Refusals:** none.

**Sort orders dropped (no ORDER BY):** team_regions, by team. In budget_places the sort by budget_cents descending is kept only in the place numbers (ROW_NUMBER), so the final's row order is dropped.

**run_measures:** the M's Unpivot drops each NULL avg_retry_secs, as its WHERE IS NOT NULL does. The sample's run 98 has a blank there, so it gets no avg_retry_secs row.

**Left alone:** the D1 notes on the Parameters and Keys sheets, and the Steps sheet. These are cells outside a Table. The attached copy describes the Steps sheet only as the empty workbook's steps, so its text is not read. No charts or PivotTables are attached.

**`<...>` to fill in:** `<database>` in every block, the database that holds each source. The table names are plain, so they stay as they are.

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

## X73

### Map

Sources (typed only, no query loads them), each read as `<database>.<table>`:
- `region_budgets`: job_id, budget_cents, region.
- `jobs`: job_id, job_name, team, region.

Steps:
- Query `eu_budgets` (reads `region_budgets` and `jobs`; keeps region = 'eu', inner join on job_id, adds job_name). Named by query `eu_count`'s M, so a CTE in the `eu_count` final.

Finals:
- Table `eu_budgets` (loaded by query `eu_budgets`; no other Table's formula reads it, and its own `dollars` reads its own row, which doesn't count): job_id, budget_cents, region, job_name, dollars. Its rows are the query's, so its block is the query's body with `dollars`.
- Table `eu_count` (loaded by query `eu_count`, which reads the query `eu_budgets`): region, jobs, total_cents. Its block groups the `eu_budgets` step.

Parameters: left alone. It is empty and no formula reads a fixed value, so no value is written in. It is never a source, step or final.

Keys: left alone. It is empty; no value is typed over a formula, so no row is needed.

Values written in: none.
Values typed over a formula: none.
Marks: none.
Refusals: none.
Left alone, also: `jobs` team and region columns (no piece reads them); the `region_budgets` row for region us (row 4), which the query's filter drops, as M does.
`<...>` to fill in: `<database>`, in each source read (the Table and column names are plain, so nothing else).

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

"Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code."

## X74

### Map

Sources (typed only), each read as `<database>.<table>`:
- `job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read by the `run_alerts` step's formulas.

Steps:
- Table `run_alerts` (no query loads it; its formulas are read by `by_status`, and query `late_alerts` reads it, so it is a step): alert_id, run_id, severity, dt, status, job_id, alerts_so_far. Its typed columns are read from `<database>.run_alerts`. It is a CTE in each final that reads it.
  - status and job_id: XLOOKUP into `job_runs` on run_id, so `LEFT JOIN <database>.job_runs` on run_id, one join for both.
  - alerts_so_far: COUNTIFS of run_id "<=" this row's run_id over its own Table, so a running count with ties included: `COUNT(*) OVER (ORDER BY run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`.

Finals:
- Summary `by_status` (typed status, FAILED and SUCCESS; alerts = COUNTIFS on status, the only typed column): status, alerts. Its groups are typed in. Nothing else reads it.
- Table `late_alerts` (loaded by query `late_alerts`, which reads the `run_alerts` step; no Table formula reads it): alert_id, run_id, alerts_so_far. Its rows are the query's.

Values written in: by_status groups FAILED and SUCCESS, typed in. A later status won't be in the table, so the groups must be checked.
Values typed over a formula: none. Every formula cell holds its formula; Keys is empty, so no Keys row is needed.
Marks:
- blank: the sample has a blank status in job_runs (run 98), and status's XLOOKUP reads that column, so it is written as `COALESCE(j.status, '')`.
Refusals: none.
Left alone:
- Parameters: empty, never a source, step or final.
- Keys: empty, no row needed.
- job_runs duration_mins and avg_retry_secs: no piece reads them, so they are not in any block.
`<...>` to fill in: `<database>`, in each source and step read.

### Hive

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    COALESCE(j.status, '') AS status, j.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
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

"Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code."

## X77

### Map

Sources (typed only), read as `<database>.<table>`:
- `run_alerts`: alert_id, run_id, severity, dt. Read by query `high_alerts`.

Steps:
- Query `high_alerts` (reads `run_alerts`; keeps severity = 'high'; keeps alert_id, run_id, dt). Named by query `high_per_day`'s M, so a CTE in the `high_per_day` final.

Finals:
- Table `high_alerts` (loaded by query `high_alerts`; no other Table's formula reads it; its `late_run` formula reads its own row, which doesn't count): alert_id, run_id, dt, late_run. Its block is the query's body with `late_run` added as `run_id > 100`.
- Table `high_per_day` (loaded by query `high_per_day`, which reads the `high_alerts` step): dt, alerts. Its rows are the query's grouping.

Values written in: none. No summary, and no Parameters value is read.
Values typed over a formula: none. Every late_run cell holds its formula; Keys is empty, so no Keys row is needed.
Marks: none.
Refusals: none.
Left alone: Parameters and Keys (empty, never a source, step or final).
`<...>` to fill in: `<database>`, in the source read.

### Hive

```sql
SELECT a.alert_id, a.run_id, a.dt, a.run_id > 100 AS late_run
FROM <database>.run_alerts a
WHERE a.severity = 'high'
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

"Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code."

## X78

### Map

Sources (typed only), read as `<database>.<table>`:
- `region_costs`: job_id, cost_cents, region, dt. Read by query `known_costs`. Its region column is read by no piece.

Steps:
- Query `known_costs` (reads `region_costs`; keeps cost_cents IS NOT NULL, as `[cost_cents] <> null` does; keeps job_id, cost_cents, dt). Named by query `cost_per_job`'s M, so a CTE in each final that reads `cost_per_job`.
- Table `cost_per_job` (loaded by query `cost_per_job`, which reads the `known_costs` step; `job_dollars`'s SUMIFS reads this Table, so it is a step): job_id, total_cents. A CTE in the `job_dollars` final; it gets no block of its own.

Finals:
- Table `known_costs` (loaded by query `known_costs`; no other Table's formula reads it): job_id, cost_cents, dt, dollars. Its block is the query's body with `dollars` = cost_cents / 100. It holds only its rows, no Total Row.
- `known_costs (Total Row)`: one column, cost_cents, from SUBTOTAL(109, ...), which is a SUM. The Total label and the empty cells get no column. It reads the `known_costs` Table's final as a CTE.
- Summary `job_dollars` (typed job_id, the only typed column, which its SUMIFS matches on; dollars = SUMIFS(cost_per_job total_cents, job_id) / 100): job_id, dollars. Its groups are typed in, and it reads the `cost_per_job` step.

Values written in: job_dollars groups 1, 2 and 3, typed in. A later job won't be in the table, so the groups must be checked.
Values typed over a formula: none. Keys is empty, so no Keys row is needed.
Marks: none. The dt column holds values such as 20260911; no formula reads dt, so it is written as it is, not converted from text.
Refusals: none.
Left alone:
- Parameters and Keys: empty, never a source, step or final.
- The region_costs row for job 2 on 20260924, whose cost_cents is blank: the query's IS NOT NULL filter drops it, as M's `<> null` does.
- The region_costs region column: no piece reads it.
`<...>` to fill in: `<database>`, in the source read.

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
),
cost_per_job AS (
  SELECT job_id, SUM(cost_cents) AS total_cents
  FROM known_costs
  GROUP BY job_id
)
SELECT j.job_id, COALESCE(c.total, 0) / 100 AS dollars
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, SUM(total_cents) AS total FROM cost_per_job GROUP BY job_id) c
  ON j.job_id = c.job_id
```

### Next

"Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code."

## X83

### Map

**Sources**
- `<database>.job_runs`: columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. Its typed columns only, and no query loads it, so it is a source. Its rows here are a sample; the query reads the database table.

**Steps**
- None. No query is in the workbook, and no Table is read as a CTE.

**Finals**
- `by_day` (a summary): dt, kept_runs, short_mins, success_or_failed. Its only typed column, dt, is the one its COUNTIFS and SUMIFS match on, so its final is a GROUP BY of `job_runs`, with its typed groups kept.
  - kept_runs: COUNTIFS on dt, status "<>TEST" and status "<>", as COUNT(*) with `(status <> 'TEST' OR status IS NULL) AND status IS NOT NULL`, wrapped in COALESCE.
  - short_mins: SUMIFS of duration_mins on dt, with duration_mins "<"&20, as SUM(duration_mins) with `duration_mins < 20`, wrapped in COALESCE.
  - success_or_failed: two COUNTIFS on dt and status that differ only in the status value ("SUCCESS" and "FAILED"), so the value is an OR: COUNT(*) with `status IN ('SUCCESS', 'FAILED')`, wrapped in COALESCE.

**Values written in**
- by_day's typed groups, dt '2026-09-23' and '2026-09-24', are typed into the Hive as the summary's groups. A later day won't be in the table: add its date to the UNION ALL line of the query.

**Values typed over a formula**
- None. Keys has no row, as no value in the workbook is typed over a formula.

**Marks**
- None.

**Refusals**
- None. Every formula in the workbook has a Hive form here.

**Left alone**
- Excel Table `Parameters` (settings): neither a source, step nor final. No formula reads it, so it is not in the Hive.
- Excel Table `Keys` (settings): neither a source, step nor final. No value is typed over a formula, so it needs no row.
- The `Steps` sheet: the Formula workbook's own instructions, not a Table or Power Query.
- Cells outside a Table: the D1 notes on the Parameters and Keys sheets.
- Blank status on row 98 of job_runs (dt 2026-09-23): written as it is, with no COALESCE, as the -IFS forms skip a blank.

**To fill in**
- `<database>` in each of the three `<database>.job_runs` reads of by_day's query.

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

## X25

### Map

**Sources**
- `<database>.Costs`: Job, `<cost_cents>`, Region, `<day_key>` (Costs' typed columns)
- `<database>.Budgets`: Job, Budget, Region (Budgets' typed columns)

**Steps**
- None. No Table or query is read by another formula or query.

**Finals**
- Costs: Job, `<cost_cents>`, Region, `<day_key>`, Day. Reads `<database>.Costs`.
- Budgets: Job, Budget, Region, Dollars. Reads `<database>.Budgets`.

**Other pieces**
- Parameters: a settings Table, never a source, step or final. It is empty, so no value is read in.
- Keys: a settings Table, never a source, step or final. It is empty, and no value is typed over a formula, so no Keys row is needed.

**Values written in:** none.

**Values typed over a formula:** none.

**Marks**
- Costs, Day: `DATE(LEFT(...), MID(...), RIGHT(...))` of Day Key, a date held as text (20260911), becomes the text date `CONCAT(SUBSTR(...), '-', SUBSTR(...), '-', SUBSTR(...))`, so Day is 'yyyy-mm-dd' text, not a date value.

**Refusals:** none.

**Left alone**
- The Steps sheet and the D1 notes on the Parameters and Keys sheets: cells outside a Table.
- Costs row 29's blank Cost cell stays NULL, as the sample holds it. No formula reads Cost, so no COALESCE is written.

**To fill in**
- `<database>`: the database both sources are read from.
- `<cost_cents>`: the header Cost (cents).
- `<day_key>`: the header Day Key.

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

## X30

### Map

**Sources**
- `<database>.scheduler_runs`: run_id, job_id, dt (its typed columns)

**Steps**
- None.

**Finals**
- scheduler_runs: run_id, job_id, dt, day, prev_run, jitter. It has a formula column and no query loads it, and nothing else reads it, so it is a final. Reads `<database>.scheduler_runs`.

**Other pieces**
- Parameters: a settings Table, never a source, step or final. It is empty, so no value is read in.
- Keys: a settings Table, never a source, step or final. It is empty, and no value is typed over a formula, so no Keys row is needed.

**Values written in:** none.

**Values typed over a formula:** none.

**Marks**
- scheduler_runs, day: `RIGHT(dt, 2)` becomes `SUBSTR(dt, -2)`. dt is read as the text 2026-09-23. If the dt cells are real Excel dates, check day, as Excel's RIGHT reads a date's serial number.

**Refusals**
- prev_run: `OFFSET(...)` reads the row before, which hangs on the order of the sheet's rows. Written as `NULL AS prev_run`.
- jitter: `RANDBETWEEN(1,5)` is random. Written as `NULL AS jitter`.

**Left alone**
- The Summary sheet's bar chart: a chart.
- The Pivot sheet's PivotTable, from scheduler_runs with rows job_id and values Count of run_id: a PivotTable.
- The Steps sheet and its D1 notes: cells outside a Table.

**To fill in**
- `<database>`: the database the source is read from.

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

## X35

### Map

Sources:
- job_runs: run_id, job_id, status, duration_mins, avg_retry_secs, dt (typed columns, read as `<database>.job_runs`). No final reads its blank status or avg_retry_secs cells, so no COALESCE is written.
- scheduler_runs: run_id, job_id, dt (typed columns, read as `<database>.scheduler_runs`).

Steps: none.

Finals:
- recent: run_id, dt. Table recent is loaded by Power Query recent, and no formula reads it, so it is a final whose rows are the query's. Power Query recent reads job_runs and scheduler_runs; its M is recent's final, with no block of its own.

Settings, never a source, step or final:
- Parameters: empty, so no value is written in.
- Keys: empty, so no value is typed over a formula.

Left out, and named:
- Power Query rates (connection only): it loads nothing and nothing reads it. It reads Web.Contents("https://rates.example.com/today.json"), a web source, so the query is left out.

Values written in: none.
Values typed over a formula: none; the workbook has no formula column.
Marks: none.
Refusals: none in the final. The rates query is left out, as above.
Left alone: the Steps sheet and the D1 notes on Parameters and Keys (cells outside a Table). The workbook has no chart or PivotTable.
To fill in: `<database>`, the database that holds job_runs and scheduler_runs, in the recent block.

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

## X40

### Map

Sources:
- jobs: job_id, job_name, team, region (typed columns, read as `<database>.jobs`). Runs' Team formula reads it.
- Runs: its typed columns Run, Job, Mins, read as `<database>.Runs`.

Steps:
- Runs: Run, Job, Mins (typed); Team (XLOOKUP of Job in jobs, so LEFT JOIN `<database>.jobs` on Job, then team); Cost (Mins * the rate value 2). No query loads Runs, but Teams' and run_alerts' formulas read it, so it is a step.

Finals:
- Teams: Team, `<total_cost>` (header Total Cost). Its only typed column, Team, is what its SUMIFS matches on, so it is a summary: a GROUP BY of Runs, with its typed groups data and finance kept and typed in. Nothing reads Teams and no query loads it.
- run_alerts: alert_id, run_id, severity, dt, `<run_mins>` (header Run Mins). No query loads it and nothing reads it; its formula reads Runs. It is a final.

Settings, never a source, step or final:
- Parameters: rate = 2, read in as its value (see below).
- Keys: empty, so no value is typed over a formula.

Left out: none.

Values written in:
- rate = 2 from Parameters, into Runs' Cost as Mins * 2. Change it in Parameters and the table won't follow, so the Hive needs the new value too.
- Teams' typed groups data and finance, written into the Hive as a summary's groups. A later team won't be in the table.

Values typed over a formula: none.
Marks: none.
Refusals: none; each formula is a supported XLOOKUP or SUMIFS.
Left alone: the PivotTable on sheet "Pivot" (rows Team, values Sum of Cost from Runs). The Steps sheet and the D1 notes on Parameters and Keys (cells outside a Table).
To fill in: `<database>` in each block; `<total_cost>`, the Teams column that holds Total Cost; `<run_mins>`, the run_alerts column that holds Run Mins.

### Hive

#### Teams

```sql
WITH Runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT t.Team, COALESCE(c.total, 0) AS <total_cost>
FROM (SELECT 'data' AS Team UNION ALL SELECT 'finance') t
LEFT JOIN (SELECT Team, SUM(Cost) AS total FROM Runs GROUP BY Team) c
  ON t.Team = c.Team
```

#### run_alerts

```sql
WITH Runs AS (
  SELECT r.Run, r.Job, r.Mins, j.team AS Team, r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT a.alert_id, a.run_id, a.severity, a.dt, m.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN Runs m ON a.run_id = m.Run
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X50

### Map

**Sources**
- `job_owners`: its typed columns (job_id, team, owner, dt), read from `<database>.job_owners`. Power Query "owners" reads it.
- `jobs`: its typed columns (job_id, job_name, team, region), read from `<database>.jobs`. The owners formula job_name reads it.

**Steps**
- None. Power Query "owners" loads Table "owners", and no other Table's formula reads "owners", so Table "owners" is a final. The query's rows are the CTE `owners_load` inside that final's block.

**Finals**
- Table `owners` (job_id, owner, job_name, newest_first), its rows the rows of Power Query "owners" (`SELECT DISTINCT job_id, owner` from `job_owners`).
  - job_id, owner: the query's columns.
  - job_name: XLOOKUP on jobs, written as a LEFT JOIN to `<database>.jobs`, then jobs' job_name.
  - newest_first: RANK.EQ on job_id, written as `RANK() OVER (ORDER BY job_id DESC)`, over the final's rows.

**Values written in**
- None. No Parameters value is read.

**Values typed over a formula**
- None. Keys is empty, so no Table has a value typed over a formula.

**Marks**
- None.

**Refusals**
- None.

**Left alone**
- Parameters (empty) and Keys (empty): settings Tables, never a source, step or final. No formula reads Parameters, and Keys needs no row.
- The owner cell that is blank for job_id 4 is kept as NULL. No formula reads owner, so no COALESCE and no mark.
- The Steps sheet and the D1 notes on each sheet: cells outside a Table.

**To fill in**
- `<database>` in `<database>.job_owners` and `<database>.jobs`.

### Hive

```sql
WITH owners_load AS (
  SELECT DISTINCT job_id, owner FROM <database>.job_owners
)
SELECT o.job_id, o.owner, j.job_name AS job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM owners_load o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X63

### Map

**Sources**
- `job_runs`: its typed columns (run_id, job_id, status, duration_mins, avg_retry_secs), read from `<database>.job_runs`.
- `scheduler_runs`: its typed columns (run_id, job_id, dt), read from `<database>.scheduler_runs`. The scheduled_job formula reads it.

**Steps**
- None.

**Finals**
- Table `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded). No query loads it, and no other Table's formula reads it, so it is a final. Its typed columns come from `<database>.job_runs`.
  - no_retry: ISBLANK on avg_retry_secs, written as `avg_retry_secs IS NULL`, with no COALESCE.
  - quarters: INT, written as `FLOOR(duration_mins / 4)`.
  - capped: MIN of one row's cell and 25, written as `LEAST(duration_mins, 25)`.
  - variance: VAR.S over the whole column, written as `VAR_SAMP(duration_mins) OVER ()`.
  - weighted: SUMPRODUCT of two columns, written as `SUM(duration_mins * job_id) OVER ()`.
  - scheduled_job: XLOOKUP on scheduler_runs with a fourth argument of -1, written as a LEFT JOIN to `<database>.scheduler_runs` with `COALESCE(s.job_id, -1)`.
  - label: CONCATENATE, written as `CONCAT('run ', run_id)`.
  - succeeded: ISNUMBER(SEARCH), written as `INSTR(LOWER(COALESCE(status, '')), LOWER('cess')) > 0`.

**Values written in**
- None. No Parameters value is read.

**Values typed over a formula**
- None. Keys is empty, so no Table has a value typed over a formula.

**Marks**
- blank: status is blank on run_id 98 in the sample, and succeeded reads status, so it is written `COALESCE(status, '')` in succeeded.

**Refusals**
- None. Every formula is one that files 11 and 12 list.

**Left alone**
- Parameters (empty) and Keys (empty): settings Tables, never a source, step or final. Keys needs no row.
- The avg_retry_secs blank on run_id 98 is written as it is, with no COALESCE, because ISBLANK skips a blank.
- The Steps sheet and the D1 notes on each sheet: cells outside a Table.

**To fill in**
- `<database>` in `<database>.job_runs` and `<database>.scheduler_runs`.

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
  INSTR(LOWER(COALESCE(r.status, '')), LOWER('cess')) > 0 AS succeeded
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X66

### Map

- **Sources** (read as `<database>.<table>`):
  - `job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read by query ok_runs and by the formulas of Table ok_runs.
- **Steps**: none. Query ok_runs names no other query, and no Table's formula reads ok_runs except its own.
- **Finals**:
  - `ok_runs` (run_id, job_id, duration_mins, dt, running, share): loaded by Power Query ok_runs, which reads job_runs, keeps the rows whose status is not null and starts with "SUCC", and selects run_id, job_id, duration_mins, dt. Nothing else reads this Table, so it is a final. Its rows are the query's, and the query is folded into this block, not a step.
    - `running` = SUMIFS over its own Table, matched on job_id with dt "<=" this row's dt: a running total per job_id, ties included, written as a window.
    - `share` = duration_mins / SUM of the whole column: written as SUM(...) OVER ().
  - `ok_runs (Total Row)` (duration_mins): the Total Row's SUBTOTAL(109) over duration_mins, as a SUM. The Total Row's label cell and empty cells get no column.
- **Neither** (never a source, step or final): `Parameters` and `Keys`. Both are empty: no fixed value is read, and no value is typed over a formula, so no Keys row is needed.
- **Values written in**: none. No summary, no Parameters value, no defined name.
- **Values typed over a formula**: none. Every formula cell of ok_runs holds its formula.
- **Marks**: none. The blank status on job_runs row 98 is dropped by the query's filter, as M drops it and as IS NOT NULL does.
- **Refusals**: none.
- **Left alone**: the `Steps` sheet, which holds the workbook's instructions and is not a Table or query. `Parameters` and `Keys` as above.
- **`<...>` to fill in**: `<database>` in each FROM. Every table and column name is plain, so there is no other.

### Hive

```sql
SELECT run_id, job_id, duration_mins, dt,
  SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins, dt,
    SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,
    duration_mins / SUM(duration_mins) OVER () AS share
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT SUM(duration_mins) AS duration_mins
FROM ok_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X69

### Map

- **Sources** (read as `<database>.<table>`):
  - `region_costs`: its typed columns job_id, cost_cents, region, dt. The step below reads them.
  - `jobs`: job_id, job_name, team, region. Source only, read by region_costs's XLOOKUP for job_name.
  - `region_budgets`: job_id, budget_cents, region. Source only, read by region_costs's XLOOKUP for budget.
- **Steps** (a CTE in each final that reads it):
  - `region_costs`: job_id, cost_cents, region, dt, job_name, budget, over_budget, running_cost. Read by Table job_totals's formulas and by query late_costs, so it is a step, not a final.
    - `job_name` = XLOOKUP on jobs: LEFT JOIN `<database>.jobs` on job_id.
    - `budget` = XLOOKUP on region_budgets: LEFT JOIN `<database>.region_budgets` on job_id. `_xlfn.` is read past.
    - `over_budget` = cost_cents > budget, with the blank mark below.
    - `running_cost` = SUMIFS over its own Table, matched on job_id with dt "<=" this row's dt: a running total per job_id, ties included, written as a window.
- **Finals**:
  - `job_totals` (job_id, total_cents, over_count): a summary, since its only typed column, job_id, is the one its SUMIFS and COUNTIFS match on. Its final query groups the step region_costs and is left-joined on its typed groups. total_cents is SUMIFS over region_costs, and over_count is COUNTIFS of over_budget = TRUE, each with COALESCE(..., 0).
  - `job_totals (Total Row)` (total_cents, over_count): one SUM per cell that holds a total. The label cell gets no column.
  - `late_costs` (job_id, dt, running_cost): loaded by Power Query late_costs, which reads region_costs, keeps running_cost > 1500, and selects job_id, dt, running_cost. No formula reads late_costs, so the Table is the final and its query is folded into its block, not a step.
- **Neither** (never a source, step or final): `Parameters` and `Keys`. Both are empty: no fixed value is read, and no value is typed over a formula, so no Keys row is needed.
- **Values written in**: job_totals's typed groups job_id 1, 2 and 3. A later job won't be in this table. Job 4 (cache_warm) is in `jobs` but not in job_totals, so it has no row here.
- **Values typed over a formula**: none.
- **Marks**:
  - **blank**: region_costs row 29 has a blank cost_cents (job 2, eu, 20260924). over_budget reads it as COALESCE(cost_cents, 0), as Excel reads the blank as 0. running_cost and total_cents sit inside SUMIFS, so their cost_cents is written as it is and skips the blank, as Excel does.
  - **date held as text**: dt holds 8-digit values such as 20260911. Each is converted to '2026-09-11' with CONCAT in region_costs, so late_costs's dt is converted too. If your dt is a real date in the workbook, drop that CONCAT. running_cost orders by the raw dt, which sorts the same either way.
- **Refusals**: none.
- **Left alone**: the `Steps` sheet, which holds the workbook's instructions and is not a Table or query. `Parameters` and `Keys` as above.
- **`<...>` to fill in**: `<database>` in each FROM, the one database that holds region_costs, jobs and region_budgets. Every table and column name is plain, so there is no other.

### Hive

```sql
WITH region_costs AS (
  SELECT rc.job_id, rc.cost_cents, rc.region,
    CONCAT(SUBSTR(rc.dt, 1, 4), '-', SUBSTR(rc.dt, 5, 2), '-', SUBSTR(rc.dt, 7, 2)) AS dt,
    j.job_name,
    rb.budget_cents AS budget,
    COALESCE(rc.cost_cents, 0) > rb.budget_cents AS over_budget,
    SUM(rc.cost_cents) OVER (PARTITION BY rc.job_id ORDER BY rc.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
  FROM <database>.region_costs rc
  LEFT JOIN <database>.jobs j ON rc.job_id = j.job_id
  LEFT JOIN <database>.region_budgets rb ON rc.job_id = rb.job_id
)
SELECT j.job_id, COALESCE(s.total_cents, 0) AS total_cents, COALESCE(c.over_count, 0) AS over_count
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, SUM(cost_cents) AS total_cents FROM region_costs GROUP BY job_id) s
  ON j.job_id = s.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS over_count FROM region_costs WHERE over_budget = TRUE GROUP BY job_id) c
  ON j.job_id = c.job_id
```

```sql
WITH region_costs AS (
  SELECT rc.job_id, rc.cost_cents, rc.region,
    CONCAT(SUBSTR(rc.dt, 1, 4), '-', SUBSTR(rc.dt, 5, 2), '-', SUBSTR(rc.dt, 7, 2)) AS dt,
    j.job_name,
    rb.budget_cents AS budget,
    COALESCE(rc.cost_cents, 0) > rb.budget_cents AS over_budget,
    SUM(rc.cost_cents) OVER (PARTITION BY rc.job_id ORDER BY rc.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
  FROM <database>.region_costs rc
  LEFT JOIN <database>.jobs j ON rc.job_id = j.job_id
  LEFT JOIN <database>.region_budgets rb ON rc.job_id = rb.job_id
),
job_totals AS (
  SELECT j.job_id, COALESCE(s.total_cents, 0) AS total_cents, COALESCE(c.over_count, 0) AS over_count
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
WITH region_costs AS (
  SELECT rc.job_id, rc.cost_cents, rc.region,
    CONCAT(SUBSTR(rc.dt, 1, 4), '-', SUBSTR(rc.dt, 5, 2), '-', SUBSTR(rc.dt, 7, 2)) AS dt,
    j.job_name,
    rb.budget_cents AS budget,
    COALESCE(rc.cost_cents, 0) > rb.budget_cents AS over_budget,
    SUM(rc.cost_cents) OVER (PARTITION BY rc.job_id ORDER BY rc.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cost
  FROM <database>.region_costs rc
  LEFT JOIN <database>.jobs j ON rc.job_id = j.job_id
  LEFT JOIN <database>.region_budgets rb ON rc.job_id = rb.job_id
)
SELECT job_id, dt, running_cost
FROM region_costs
WHERE running_cost > 1500
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X70

### Map

**Sources** (each read as `<database>.<table>`, its typed columns)
- `<database>.jobs`: job_id, job_name, team, region
- `<database>.job_owners`: job_id, team, owner, dt
- `<database>.job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt

**Steps** (each a CTE in each final that reads it)
- Query `staffed` (connection only): job_id, job_name, owner. Read by query `owner_load`, so it is a CTE in each final that reads it. Job 4 has no owner in the sample, so it drops out, as M's `<> null` drops it. Job 3 has two owners in the sample (ana, chloe), so its runs count under both, as M does.
- Query `owner_load`: owner, total_mins, runs. Read by query `busiest_owner`, so it is a CTE in that final.

**Finals**
- Table `owner_load` (owner, total_mins, runs, avg_mins): loaded by query `owner_load`, so its rows are the query's. Its avg_mins is `total_mins / runs`, reading its own row.
- Table `owner_load (Total Row)` (runs): one row, `runs` = SUM(runs). The Total Row's "Total" label and its blank cells get no column.
- Table `busiest_owner` (owner, total_mins, runs): loaded by query `busiest_owner`, so its rows are the query's. The query sorts `owner_load` by runs, descending, and keeps 1 row.

**Left alone**
- Parameters and Keys: empty Excel Tables, never a source, step or final. No Parameters value is written in, and no value is typed over a formula, so no Keys row is needed.
- Columns no final reads, which stay in the source tables only: jobs.team, jobs.region, job_owners.team, job_owners.dt, job_runs.run_id, job_runs.status, job_runs.avg_retry_secs, job_runs.dt.

**Values and marks**
- Values written in: none. There is no summary and no Parameters value.
- Values typed over a formula: none. Keys is empty.
- Marks: none.
- Refusals: none.

**`<...>` to fill in**
- `<database>` in each of the three source reads (`<database>.jobs`, `<database>.job_owners`, `<database>.job_runs`).
- The Total Row's file name: `owner_load (Total Row)` has a space and brackets, so save it as `<owner_load_total_row>.hql`.

### Hive

```sql
-- Final: Table owner_load
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
-- Final: Table owner_load (Total Row)
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
SELECT SUM(runs) AS runs FROM owner_load
```
```sql
-- Final: Table busiest_owner
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

## X84

### Map

**Sources** (read as `<database>.<table>`, its typed columns)
- `<database>.job_runs`: run_id, job_id, status, duration_mins

**Steps**
- None. No query loads or names a piece, and no other Table's formula reads job_runs.

**Finals**
- Table `job_runs` (run_id, job_id, status, duration_mins, flag, job2_short, failed_or_test_mins): it has formula columns and nothing else reads it. Its own formulas don't count, so it is a final, not a step. Its typed columns are read from `<database>.job_runs`. It has no Total Row.
  - flag: IF over OR and AND, written by file 11 as `(a AND b OR c AND d)` inside IF.
  - job2_short: a SUMPRODUCT of conditions over its own whole column, written as `COUNT(CASE WHEN .. THEN 1 END) OVER ()`, as each row shows the same total.
  - failed_or_test_mins: a SUMPRODUCT of a status OR over duration_mins, written as `SUM(CASE WHEN .. THEN duration_mins ELSE 0 END) OVER ()`.

**Left alone**
- Parameters and Keys: empty Excel Tables, never a source, step or final. No value is written in and none is typed over a formula, so no Keys row is needed.

**Values and marks**
- Values written in: none. There is no summary and no Parameters value.
- Values typed over a formula: none. Keys is empty.
- Marks: blank. The sample has a blank status (run_id 98), and failed_or_test_mins reads status, so that formula reads `COALESCE(status, '')`. The typed status column itself is read as it is.
- Refusals: none.

**`<...>` to fill in**
- `<database>` in the one FROM (`<database>.job_runs`).

### Hive

```sql
-- Final: Table job_runs
SELECT run_id, job_id, status, duration_mins,
  IF((job_id = 2 AND duration_mins < 20 OR job_id = 3 AND NOT (duration_mins >= 30)), 'review', '') AS flag,
  COUNT(CASE WHEN job_id = 2 AND duration_mins < 20 THEN 1 END) OVER () AS job2_short,
  SUM(CASE WHEN COALESCE(status, '') = 'FAILED' OR COALESCE(status, '') = 'TEST' THEN duration_mins ELSE 0 END) OVER () AS failed_or_test_mins
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X80

### Map

- **Sources:** `job_runs`, its typed columns (run_id, job_id, duration_mins), read as `<database>.job_runs`. Its 9 typed rows are a sample: the Hive reads the table, never the sample.
- **Steps:** none. No query loads a Table, and no Table's formula reads job_runs except its own row, which doesn't count.
- **Finals:** `job_runs`, with columns run_id, job_id, duration_mins, look, in the Table's order. Nothing else reads it, so it is a final.
- **Settings, never a source, step or final:** `Parameters` (name | value, empty) and `Keys` (table | key_columns, empty).
- **Values written in:** none. Parameters is empty, so no XLOOKUP reads a value into the Hive.
- **Values typed over a formula:** none. Keys is empty, and every `look` cell holds the same formula, so no row is typed over.
- **Marks:** none. The sample has no blank in a column the formula reads, and every comparison is numeric.
- **Refusals:** none.
- **Left alone:** Parameters and Keys (settings, as above), their D1 notes, and the Steps sheet's text, all cells outside a Table. No chart, PivotTable or defined name is listed in the workbook. No Total Row on job_runs.
- **To fill in:** `<database>`, the database that holds job_runs, in the FROM of the job_runs block.

### Hive

### job_runs

```sql
SELECT run_id, job_id, duration_mins,
  IF((duration_mins > 20 AND job_id <> 3 OR NOT job_id = 2), 'look', 'fine') AS look
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
