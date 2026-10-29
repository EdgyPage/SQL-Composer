date: 2026-10-29
arm: C
model: haiku
files: 6fc91ff

## X21

**Map**
- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin).
- Parameters and Keys are empty, so none. The Steps sheet is not a Table and is left alone.

**Marks and refusals**
- No value is typed over a formula, and no blank is read by a formula. Nothing refused.
- To fill in: `<database>`.

```sql
SELECT r.job_id, r.budget_cents, r.region,
  r.budget_cents / 100 AS budget_dollars,
  r.budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets r
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X22

**Map**
- Sources: jobs (job_id, job_name, team).
- Steps: none.
- Finals: jobs (job_id, job_name, team, is_finance, ratio).
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- IFERROR(a / b, 0) converted as COALESCE(a / b, 0). A divide by 0 is NULL, so ratio is 0 for job 2, where job_id - 2 is 0.
- No value is typed over a formula, and no blank. Nothing refused.
- To fill in: `<database>`.

```sql
SELECT j.job_id, j.job_name, j.team,
  IF(j.team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(j.job_id / (j.job_id - 2), 0) AS ratio
FROM <database>.jobs j
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X23

**Map**
- Sources: job_runs (run_id, status, avg_retry_secs).
- Steps: none.
- Finals: job_runs (run_id, status, avg_retry_secs, label, risky).
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- SWITCH converted to CASE, with the formula's "other" as ELSE.
- Blank: row 98 has a blank status and a blank avg_retry_secs. Both are read by the formulas, so they are wrapped inside label and risky as COALESCE(status, '') and COALESCE(avg_retry_secs, 0). The output columns keep the sampled values.
- No value is typed over a formula. Nothing refused.
- To fill in: `<database>`.

```sql
SELECT r.run_id, r.status, r.avg_retry_secs,
  CASE COALESCE(r.status, '') WHEN 'SUCCESS' THEN 'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label,
  (COALESCE(r.status, '') = 'FAILED' OR COALESCE(r.avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs r
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X24

**Map**
- Sources: team_notes (team, note, written_on).
- Steps: none.
- Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars).
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- LEFT(note, FIND(" ", note) - 1) converted as SUBSTR(note, 1, INSTR(note, ' ') - 1).
- UPPER is written as it is, as file 12 gives it for Text.Upper.
- ROUND, LEN, MONTH kept as they are (LEN as LENGTH).
- No blanks, no value typed over a formula. Nothing refused.
- To fill in: `<database>`.

```sql
SELECT t.team, t.note, t.written_on,
  SUBSTR(t.note, 1, INSTR(t.note, ' ') - 1) AS first_word,
  UPPER(t.team) AS shout,
  MONTH(t.written_on) AS month,
  ROUND(LENGTH(t.note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes t
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X25

**Map**
- Sources: Costs (Job, Cost (cents), Region, Day Key); Budgets (Job, Budget, Region).
- Steps: none.
- Finals: Costs (Job, Cost (cents), Region, Day Key, Day); Budgets (Job, Budget, Region, Dollars).
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- Day Key is a date held as text (20260911), so Day is built as CONCAT(SUBSTR(...), '-', SUBSTR(...), '-', SUBSTR(...)), not DATE(LEFT, MID, RIGHT).
- Blank: Costs row 29 has a blank cost. No formula reads it, so it stays NULL and is not wrapped.
- Dollars is Budget / 100.
- No value is typed over a formula. Nothing refused.
- To fill in: `<database>`, `<cost_cents>` (header Cost (cents)), `<day_key>` (header Day Key).

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

Toolbox code comes next: take out what you don't want converted, fill in the `<...>` placeholders, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X26

**Map**
- Sources: run_alerts (alert_id, run_id, severity); job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins).
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- job_id (XLOOKUP) and status (VLOOKUP, column 3) both look up job_runs on run_id. One LEFT JOIN on run_id serves both. In the sample run_id is unique in job_runs. If the full table repeats a run_id, Excel takes the first match and this join would repeat the alert row.
- Blank: job_runs row 98 has a blank status. The status lookup reads it, so it is wrapped as COALESCE(jr.status, '').
- avg_mins (AVERAGEIFS) becomes AVG over job_runs by job_id, LEFT JOINed. NULL where nothing matches, as AVERAGEIFS gives, so no COALESCE.
- No value is typed over a formula. Nothing refused.
- To fill in: `<database>`.

```sql
SELECT a.alert_id, a.run_id, a.severity,
  jr.job_id,
  COALESCE(jr.status, '') AS status,
  ja.avg_mins
FROM <database>.run_alerts a
LEFT JOIN <database>.job_runs jr ON a.run_id = jr.run_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) ja ON jr.job_id = ja.job_id
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X27

**Map**
- Sources: jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: by_team (team, jobs_in_team, last_job_id, last_job_name). by_team's only typed column is what COUNTIFS matches on, so it is a summary: a GROUP BY team over jobs.
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- COUNTIFS becomes COUNT(*) and MAXIFS becomes MAX, each with COALESCE(..., 0), as Excel gives 0 where nothing matches.
- INDEX(jobs[job_name], MATCH(last_job_id, jobs[job_id], 0)) becomes a LEFT JOIN of jobs on last_job_id, then job_name.
- No blank, no value typed over a formula. Nothing refused.
- To fill in: `<database>`.

```sql
SELECT g.team, g.jobs_in_team, g.last_job_id, n.job_name AS last_job_name
FROM (
  SELECT j.team,
    COALESCE(COUNT(*), 0) AS jobs_in_team,
    COALESCE(MAX(j.job_id), 0) AS last_job_id
  FROM <database>.jobs j
  GROUP BY j.team
) g
LEFT JOIN <database>.jobs n ON g.last_job_id = n.job_id
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X28

**Map**
- Sources: jobs (job_id, job_name); job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: jobs (job_id, job_name, ok_mins).
- Keys: jobs holds job_id.
- Parameters are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- Typed over a formula: ok_mins in row 4 (job 3, report_build) is typed 99. Matched on the Keys column job_id = 3.
- SUMIFS over another Table becomes a LEFT JOIN on a subquery grouped by job_id, with COALESCE(..., 0).
- The blank status on run 98 is skipped by the SUMIFS form (status = 'SUCCESS' leaves it out), so no wrap is needed.
- Nothing refused.
- To fill in: `<database>`.

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

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X29

**Map**
- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer).
- Parameters: cents_per_dollar is 100. XLOOKUP("cents_per_dollar", ...) is read as its value, 100. Parameters itself is none.
- Keys: empty, so there is no Keys row for region_budgets. The typed row in row 4 matches on every typed column (job_id, budget_cents, region).
- The Steps sheet is left alone.

**Marks and refusals**
- Typed over a formula: in_dollars in row 4 (job 3, budget 350, us) is typed 5. There is no Keys row, so it matches on job_id, budget_cents and region together.
- Refused: pointer. INDIRECT and ROW() are refused, so the column is NULL AS pointer.
- To fill in: `<database>`.

```sql
SELECT r.job_id, r.budget_cents, r.region,
  CASE WHEN r.job_id = 3 AND r.budget_cents = 350 AND r.region = 'us' THEN 5
    ELSE r.budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets r
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X30

**Map**
- Sources: scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter).
- Parameters and Keys are empty, so none.

**Marks and refusals**
- day = RIGHT(dt, 2), converted as SUBSTR(dt, -2).
- Refused: prev_run (OFFSET) and jitter (RANDBETWEEN). Both are NULL AS in the SELECT.
- Left alone: the bar chart on the Summary sheet, and the PivotTable on the Pivot sheet, from scheduler_runs.
- To fill in: `<database>`.

```sql
SELECT s.run_id, s.job_id, s.dt,
  SUBSTR(s.dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs s
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X31

**Map**
- Sources: jobs (job_id, team).
- Steps: none.
- Finals: jobs (job_id, team, bump, tag, scaled, boosted).
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- Refused: bump, because its formula reads its own column (circular). NULL AS bump.
- Refused: tag, because the defined name TAG holds a LAMBDA. NULL AS tag.
- Refused: scaled, because it reads Summary!D4, a cell outside a Table that isn't a defined name. NULL AS scaled.
- boosted: the defined name boost is Summary!B2, a cell outside a Table, with value 10. Its value 10 is used, and you should move boost into Parameters.
- Left alone: the Summary sheet's cells B2 and D4, as cells outside a Table.
- To fill in: `<database>`.

```sql
SELECT j.job_id, j.team,
  NULL AS bump,
  NULL AS tag,
  NULL AS scaled,
  j.job_id * 10 AS boosted
FROM <database>.jobs j
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X32

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region).
- Steps: job_runs, which adds job_name from jobs, is read by by_name. It is a CTE, job_runs_step.
- Finals: by_name (job_name, runs). by_name's only typed column is what COUNTIFS matches on, so it is a summary: a GROUP BY job_name over the job_runs step.
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- VLOOKUP(job_id, jobs, 2, TRUE) is approximate. It is converted exactly, as a LEFT JOIN on job_id. The sample's job_ids (1 to 4) all match, so the results are the same here. A job_id missing from jobs would get the nearest lower name in Excel and NULL here.
- COUNTIFS becomes COUNT(*), with COALESCE(..., 0).
- No blank read by a formula, no value typed over a formula. Nothing refused.
- To fill in: `<database>`.

```sql
WITH job_runs_step AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT s.job_name, COALESCE(COUNT(*), 0) AS runs
FROM job_runs_step s
GROUP BY s.job_name
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X33

**Map**
- Sources: job_runs, the table Sql.Database names (server dwh01, schema ops, item job_runs). Written as `<database>.job_runs`.
- Steps: none.
- Finals: slow_runs (run_id, duration_mins, over_by), the query loaded into the Table slow_runs.
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- Sql.Database is not a workbook source. Its table is used as the Power Query names it. Check that `<database>` is `ops` on server `dwh01`.
- status <> 'TEST' keeps a null, as M does, so it is written (status <> 'TEST' OR status IS NULL).
- over_by is Table.AddColumn's expression, duration_mins - 20.
- No blank is read by a formula in the workbook, and no value is typed over a formula. Nothing refused.
- To fill in: `<database>`.

```sql
SELECT r.run_id, r.duration_mins, r.duration_mins - 20 AS over_by
FROM <database>.job_runs r
WHERE r.duration_mins >= 20
  AND (r.status <> 'TEST' OR r.status IS NULL)
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X34

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region).
- Steps: runs_with_team, the connection-only query that NestedJoins job_runs to jobs, LeftOuter, and expands team. It is read by team_totals, so it is a CTE.
- Finals: team_totals (team, total_mins, longest), the query loaded into the Table team_totals.
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- LeftOuter NestedJoin is a LEFT JOIN. List.Sum and List.Max become SUM and MAX.
- No blank read by a formula, no value typed over a formula. Nothing refused.
- To fill in: `<database>`.

```sql
WITH runs_with_team AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT t.team,
  SUM(t.duration_mins) AS total_mins,
  MAX(t.duration_mins) AS longest
FROM runs_with_team t
GROUP BY t.team
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X35

**Map**
- Sources: job_runs (run_id, dt); scheduler_runs (run_id, dt). Read for the two columns the query uses.
- Steps: none.
- Finals: recent (run_id, dt), the query loaded into the Table recent.
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- Table.Combine is UNION ALL. Table.Sort on run_id descending then Table.FirstN 4 becomes ORDER BY run_id DESC LIMIT 4.
- Left out, and named: the connection-only query rates. It reads Web.Contents (a web source), which is refused, and nothing reads it.
- To fill in: `<database>`.

```sql
WITH both_runs AS (
  SELECT r.run_id, r.dt FROM <database>.job_runs r
  UNION ALL
  SELECT s.run_id, s.dt FROM <database>.scheduler_runs s
)
SELECT b.run_id, b.dt
FROM both_runs b
ORDER BY b.run_id DESC
LIMIT 4
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X36

**Map**
- Sources: run_alerts (alert_id, run_id, severity, dt); job_runs (run_id, status).
- Steps: none.
- Finals: job_runs (run_id, status, alerts); severity_by_day (dt, high, low), the query loaded into its Table.
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- alerts (COUNTIFS over run_alerts) becomes COUNT(*) on a subquery grouped by run_id, LEFT JOINed, with COALESCE(..., 0).
- Table.Pivot: the pivot's columns are now fixed to high and low, the values in the sample. Each is SUM(CASE WHEN severity = '...' THEN 1 END), NULL where none, as M leaves it.
- Nothing refused.
- To fill in: `<database>`.

```sql
SELECT j.run_id, j.status,
  COALESCE(a.alerts, 0) AS alerts
FROM <database>.job_runs j
LEFT JOIN (
  SELECT run_id, COUNT(*) AS alerts
  FROM <database>.run_alerts
  GROUP BY run_id
) a ON j.run_id = a.run_id
```

```sql
SELECT p.dt,
  SUM(CASE WHEN p.severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN p.severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts p
GROUP BY p.dt
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X37

**Map**
- Sources: Owners (Job No, Team Name, Owner, Day).
- Steps: none.
- Finals: Owners (Job No, Team Name, Owner, Day, Is Ana).
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- Blank: Owner is blank on the web rows (job 4). Is Ana reads it, so it is wrapped as COALESCE(Owner, ''). This is a plain IF, not an -IF(S) form, so the wrap applies. Owner stays as sampled in the output.
- Is Ana is IF(Owner = "ana", 1, 0), converted as IF(... = 'ana', 1, 0).
- No value is typed over a formula. Nothing refused.
- To fill in: `<database>`, `<job_no>` (header Job No), `<team_name>` (header Team Name), `<is_ana>` (header Is Ana).

```sql
SELECT o.<job_no>, o.<team_name>, o.Owner, o.Day,
  IF(COALESCE(o.Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners o
```

Toolbox code comes next: take out what you don't want converted, fill in the `<...>` placeholders, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X38

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs); jobs (job_id, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost).
- Keys: job_runs holds run_id.
- Parameters are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- Typed over a formula: retry_cost in row 8 (run 102) is typed 1. Matched on the Keys column run_id = 102.
- region (XLOOKUP) becomes a LEFT JOIN of jobs on job_id, then region.
- region_mins (SUMIFS over its own Table, by region) becomes SUM(duration_mins) OVER (PARTITION BY region), with COALESCE(..., 0).
- Blank: avg_retry_secs is blank on run 98, and retry_cost reads it, so it is wrapped as COALESCE(avg_retry_secs, 0). The output keeps the sampled value.
- Nothing refused.
- To fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  j.region,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.region), 0) AS region_mins,
  CASE WHEN r.run_id = 102 THEN 1
    ELSE (COALESCE(r.avg_retry_secs, 0) + r.duration_mins) * 2 END AS retry_cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.

## X39

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins); jobs (job_id, job_name).
- Steps: none.
- Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise). The query filters to status = 'SUCCESS' and is loaded into the Table, which is read by nothing else, so the Table is the final.
- Parameters and Keys are empty, so none. The Steps sheet is left alone.

**Marks and refusals**
- Refused: noise, because RAND() is refused. NULL AS noise.
- job_name (XLOOKUP) becomes a LEFT JOIN of jobs on job_id.
- share (SUMIFS over its own Table, by job_id) becomes duration_mins / COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0). The window runs over the rows the query keeps, status = 'SUCCESS'.
- No blank read by a formula, no value typed over a formula.
- To fill in: `<database>`.

```sql
SELECT o.run_id, o.job_id, o.duration_mins,
  j.job_name,
  o.duration_mins / COALESCE(SUM(o.duration_mins) OVER (PARTITION BY o.job_id), 0) AS share,
  NULL AS noise
FROM (
  SELECT r.run_id, r.job_id, r.duration_mins
  FROM <database>.job_runs r
  WHERE r.status = 'SUCCESS'
) o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

Toolbox code comes next: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its checked code wins where the two differ.
