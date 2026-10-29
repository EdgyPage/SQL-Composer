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

## X40

**Map**
- Sources: `Runs` (Run, Job, Mins), `jobs` (job_id, job_name, team, region).
- Steps: `Runs` (Team, Cost). It has formula columns and is read by two finals, so it is a CTE `runs` in each.
- Finals: `Teams` (Team, `<total_cost>`), a summary of `Runs`, since its only typed column, Team, is what SUMIFS matches on. And `run_alerts` (alert_id, run_id, severity, dt, `<run_mins>`).

**Final: Teams (summary, GROUP BY of Runs)**

```sql
WITH runs AS (
  SELECT r.Run, r.Job, r.Mins,
    j.team AS Team,
    r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON j.job_id = r.Job
)
SELECT Team,
  COALESCE(SUM(Cost), 0) AS <total_cost>
FROM runs
GROUP BY Team
```

**Final: run_alerts**

```sql
WITH runs AS (
  SELECT r.Run, r.Job, r.Mins,
    j.team AS Team,
    r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON j.job_id = r.Job
)
SELECT a.alert_id, a.run_id, a.severity, a.dt,
  r.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN runs r ON r.Run = a.run_id
```

**Marks**
- The rate in `Cost` is `XLOOKUP("rate", Parameters[name], Parameters[value])`, read as its value 2 from the sample. Parameters is not converted. If the rate changes, change the 2.
- Keys has no row for any Table. Nothing is typed over a formula, so no Keys row is needed.

**Refusals:** none.

**Left alone:** the PivotTable on sheet Pivot (from Runs, rows Team, values Sum of Cost). The Steps sheet holds no Table.

**Fill in:** `<database>`, `<total_cost>`, `<run_mins>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X46

**Map**
- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), `jobs` (job_id, job_name, team).
- Steps: none. `runs` is computed inside the final that reads it.
- Finals: `jobs` (job_id, job_name, team, shortest, runs, busiest).

**Final: jobs**

```sql
SELECT j.job_id, j.job_name, j.team,
  COALESCE(s.shortest, 0) AS shortest,
  COALESCE(c.runs, 0) AS runs,
  RANK() OVER (ORDER BY COALESCE(c.runs, 0) DESC) AS busiest
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, MIN(duration_mins) AS shortest
  FROM <database>.job_runs
  GROUP BY job_id
) s ON s.job_id = j.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS runs
  FROM <database>.job_runs
  GROUP BY job_id
) c ON c.job_id = j.job_id
```

**Marks**
- MINIFS and COUNTIF over `job_runs`, another Table, are LEFT JOINs. COALESCE gives 0 where nothing matches, as Excel does. That is job 4 (cache_warm), with shortest 0 and runs 0.
- `busiest` is RANK.EQ descending on `runs`. Equal counts share a rank.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X47

**Map**
- Sources: `region_budgets` (job_id, budget_cents, region).
- Steps: none.
- Finals: `region_budgets` (job_id, budget_cents, region, cheapest_first, region_total, region_avg).

**Final: region_budgets**

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

**Marks**
- `cheapest_first`: RANK.EQ with 1 as its third argument is ascending, over the whole column and not per region.
- `region_total`: SUMIF over its own Table, windowed by region, with COALESCE to 0.
- `region_avg`: AVERAGEIF is AVG by region and is left NULL where nothing matches, with no COALESCE.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X48

**Map**
- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), `run_alerts` (alert_id, run_id, severity, dt), `jobs` (job_id, job_name, team, region).
- Steps: none. Both Power Query queries load straight into their Tables, and no query reads another.
- Finals: `quiet_runs` (run_id, job_id, status), loaded by the query quiet_runs. And `slow_regions` (region, avg_mins, fastest), loaded by the query slow_regions.

**Final: quiet_runs**

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON a.run_id = r.run_id
WHERE a.run_id IS NULL
```

**Final: slow_regions**

```sql
SELECT j.region,
  AVG(r.duration_mins) AS avg_mins,
  MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON j.job_id = r.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

**Marks**
- quiet_runs: NestedJoin with LeftAnti is a LEFT JOIN with the WHERE that keeps only the rows with no match. Only run_id, job_id and status are kept.
- slow_regions: the filter after Table.Group is a HAVING that repeats the average.
- The blank status of run 98 is not read by any formula, so it stays NULL.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X49

**Map**
- Sources: `job_runs`, `run_alerts` (alert_id, run_id, severity, dt), `scheduler_runs` (run_id, job_id, dt), `job_owners` (job_id, team, owner, dt), `jobs` (job_id, job_name, team, region).
- Steps: none. No query reads another query.
- Finals: `alert_status` (alert_id, severity, status), `run_check` (run_id, status, scheduled_run), `teams` (team).

**Final: alert_status**

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON a.run_id = r.run_id
```

**Final: run_check**

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM (SELECT run_id, status FROM <database>.job_runs) r
FULL OUTER JOIN <database>.scheduler_runs s ON s.run_id = r.run_id
```

**Final: teams**

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

**Marks**
- alert_status: the RightOuter join is a LEFT JOIN with the two tables swapped, so every job run is kept. Run 97 has two alerts and so two rows.
- run_check: FullOuter is FULL OUTER JOIN. Run 100 is in the scheduler only, so its run_id and status are NULL.
- teams: Table.Distinct over Table.Combine is UNION.
- This workbook has no formulas, so no blank is wrapped.
- Keys and Parameters are empty.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X50

**Map**
- Sources: `job_owners` (job_id, team, owner, dt), `jobs` (job_id, job_name, team, region).
- Steps: none. The query owners is read only by the Table it loads.
- Finals: `owners` (job_id, owner, job_name, newest_first), loaded by the query owners with its formula columns.

**Final: owners**

```sql
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
LEFT JOIN <database>.jobs j ON j.job_id = o.job_id
```

**Marks**
- The query is Table.Distinct over job_id and owner, so it is SELECT DISTINCT. The result is 5 rows.
- `newest_first` is RANK.EQ over the Table's own job_id, descending, taken over the distinct rows. Job 3 has two owners, and both rank 2.
- Job 4 has a blank owner, which stays NULL because no formula reads owner.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X59

**Map**
- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), `jobs` (job_id, job_name), `run_alerts` (alert_id, run_id, severity, dt).
- Steps: none.
- Finals: `jobs` (job_id, job_name, long_runs, failed_mins, not_test), and `run_alerts` (alert_id, run_id, severity, dt, alerts_so_far).

**Final: jobs**

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
) lr ON lr.job_id = j.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS failed_mins
  FROM <database>.job_runs
  WHERE LOWER(status) LIKE 'f%'
  GROUP BY job_id
) fm ON fm.job_id = j.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS not_test
  FROM <database>.job_runs
  WHERE (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) nt ON nt.job_id = j.job_id
```

**Final: run_alerts**

```sql
SELECT a.alert_id, a.run_id, a.severity, a.dt,
  COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
FROM <database>.run_alerts a
```

**Marks**
- The wildcard "f*" ignores case, so it is `LOWER(status) LIKE 'f%'`.
- "<>TEST" keeps the blank status of run 98 (job 2), as Excel counts a blank there. The blank is not wrapped, since it is inside COUNTIFS.
- The blank avg_retry_secs is not read by any formula.
- alerts_so_far is a running count of run_id values up to this row's, ties included, as RANGE gives.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X60

**Map**
- Sources: `region_budgets` (job_id, budget_cents, region).
- Steps: none.
- Finals: `region_budgets` (job_id, budget_cents, region, share, above_avg, rank_in_region).
- Total Row: `region_budgets (Total Row)`, a query of its own.

**Final: region_budgets**

```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

**Total Row: region_budgets (Total Row)**

```sql
SELECT COUNT(job_id) AS job_id,
  AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

**Marks**
- share is each budget over the sum of the whole column.
- above_avg compares each budget with the average of the whole column and gives TRUE or FALSE.
- rank_in_region: COUNTIFS with "<" plus 1 is the ascending RANK within region, with ties sharing the lower rank.
- Total Row: the "Total" label is text, not a total, so it is left out. SUBTOTAL(103) is COUNT of job_id and SUBTOTAL(101) is AVG of budget_cents. The row has no label.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X61

**Map**
- Sources: `region_costs` (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: `by_region` (region, total_cents, entries, priciest). It is a summary of region_costs, since its only typed column, region, is what SUMIFS, COUNTIFS and MAXIFS match on.
- Total Row: `by_region (Total Row)` needs no query of its own. The summary's query ends with WITH ROLLUP.

**Final: by_region**

```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(*), 0) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

The rollup adds the Total row as one more row, with region NULL (a Subtotal row). Its total_cents is a SUM of the SUMs, entries a SUM of the COUNTs, and priciest a MAX of the MAXes, as SUBTOTAL 109 and 104 give.

**Marks**
- cost_cents is blank in one row (job 2, 20260924). SUMIFS and MAXIFS skip it, as SUM and MAX skip NULL, so it is not wrapped.
- dt is held as text (20260911). No formula reads it, so it is kept as held.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X62

**Map**
- Sources: `team_notes` (team, note, written_on).
- Steps: none.
- Finals: `team_notes` (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short).

**Final: team_notes**

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

**Marks**
- week_of is `written_on - WEEKDAY(written_on, 2) + 1`, the Monday on or before the date, written with NEXT_DAY.
- month_of is `EOMONTH(written_on, -1) + 1`, the first day of the month, cast to a string.
- months_in: DATE(2026,1,1) is '2026-01-01'. DATEDIF "m" is FLOOR(MONTHS_BETWEEN).
- short: TEXTJOIN with TRUE skips an empty part, as CONCAT_WS does. LEFT(note, 5) is SUBSTR(note, 1, 5).
- who is PROPER(team), which is INITCAP.
- written_on is read as a date.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X63

**Map**
- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs), `scheduler_runs` (run_id, job_id, dt).
- Steps: none.
- Finals: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded).

**Final: job_runs**

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
LEFT JOIN <database>.scheduler_runs s ON s.run_id = r.run_id
```

**Marks**
- status is blank in run 98. The formula succeeded reads it, so it is wrapped as COALESCE(status, ''), and the blank is not succeeded.
- avg_retry_secs is blank in run 98. no_retry is ISBLANK, which is IS NULL, so it is not wrapped.
- scheduled_job: XLOOKUP's fourth argument, -1, is COALESCE. Run 99 has no scheduler row, so it gets -1.
- variance is VAR.S over the whole column, VAR_SAMP. weighted is SUMPRODUCT, SUM(a * b) OVER (). Both give the same value on every row.
- INT is FLOOR. MIN of two cells of one row is LEAST.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X64

**Map**
- Sources: `jobs` (job_id, job_name, team, region), `region_costs` (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: `picked_costs` (job_id, cost_cents, region, size), `costed_jobs` (job_id, job_name, team, region), `costs_filled` (job_id, cost_cents, dt, day). Each is loaded by its Power Query, and no query reads another.

**Final: picked_costs**

```sql
SELECT job_id, cost_cents,
  UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

**Final: costed_jobs**

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

**Final: costs_filled**

```sql
SELECT job_id,
  COALESCE(cost_cents, 0) AS cost_cents,
  dt,
  SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

**Marks**
- picked_costs: `<> null` is IS NOT NULL. List.Contains({1, 3}) is IN (1, 3). Text.Upper is UPPER. The if is IF.
- costed_jobs: List.Contains on another Table's job_id is LEFT SEMI JOIN. Text.StartsWith "n" is LIKE 'n%', case kept, and not is NOT.
- costs_filled: the blank cost_cents of job 2 on 20260924 is replaced by 0 with COALESCE, as the Power Query replaces null with 0.
- dt is held as text (20260911). Text.End of 2 is SUBSTR(dt, -2), which reads the text as text.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X65

**Map**
- Sources: `jobs` (job_id, job_name, team, region), `region_budgets` (job_id, budget_cents, region), `job_owners` (job_id, team, owner, dt), `scheduler_runs` (run_id, job_id, dt), `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none. No query reads another query.
- Finals: `team_regions` (team, region), `budget_places` (job_id, budget_cents, region, place), `jobs_per_team` (team, jobs), `ran_as_scheduled` (run_id, dt), `run_measures` (run_id, job_id, measure, amount).

**Final: team_regions**

```sql
SELECT t.team, r.region
FROM (SELECT DISTINCT team FROM <database>.jobs) t
CROSS JOIN (SELECT DISTINCT region FROM <database>.jobs) r
```

**Final: budget_places**

```sql
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

**Final: jobs_per_team**

```sql
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

**Final: ran_as_scheduled**

```sql
SELECT run_id, dt FROM <database>.scheduler_runs
INTERSECT
SELECT run_id, dt FROM <database>.job_runs
```

**Final: run_measures**

```sql
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

**Marks**
- team_regions: Table.AddColumn of the whole Regions table, then expanded, is a CROSS JOIN. The Table.Sort has no FirstN or index after it, so the sort order is dropped. A Hive table holds no order.
- budget_places: the Table.Sort then Table.AddIndexColumn is ROW_NUMBER() OVER (ORDER BY budget_cents DESC). The final has no ORDER BY, and place 1 is the largest budget.
- jobs_per_team: List.Count(List.Distinct) is COUNT(DISTINCT job_id). job_id has no blank in the sample.
- ran_as_scheduled: the inner join on both kept columns, with Table.Distinct, is INTERSECT.
- run_measures: Table.Unpivot is one SELECT per measure, stacked with UNION ALL. Each has WHERE NOT NULL, so the blank avg_retry_secs of run 98 is dropped.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X66

**Map**
- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none. The query ok_runs is loaded into its Table and nothing else reads it.
- Finals: `ok_runs` (run_id, job_id, duration_mins, dt, running, share).
- Total Row: `ok_runs (Total Row)`, a query of its own.

**Final: ok_runs**

```sql
SELECT o.run_id, o.job_id, o.duration_mins, o.dt,
  COALESCE(SUM(o.duration_mins) OVER (PARTITION BY o.job_id ORDER BY o.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  o.duration_mins / SUM(o.duration_mins) OVER () AS share
FROM (
  SELECT run_id, job_id, duration_mins, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
) o
```

**Total Row: ok_runs (Total Row)**

```sql
SELECT SUM(duration_mins) AS duration_mins
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

**Marks**
- The query's filter is `[status] <> null and Text.StartsWith([status], "SUCC")`, which is `status IS NOT NULL AND status LIKE 'SUCC%'`.
- running is SUMIFS over the same job_id with dt "<=" this row's dt, which is a running total per job with ties included.
- share is each duration over the sum of the whole column.
- Total Row: the "Total" label is left out, and SUBTOTAL(109) is SUM of duration_mins.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X69

**Map**
- Sources: `region_costs` (job_id, cost_cents, region, dt), `jobs` (job_id, job_name, team, region), `region_budgets` (job_id, budget_cents, region).
- Steps: `region_costs` (job_name, budget, over_budget, running_cost). It has formula columns and two finals read it, so it is a CTE `region_costs` in each.
- Finals: `job_totals` (job_id, total_cents, over_count), a summary of region_costs, since its only typed column, job_id, is what SUMIFS and COUNTIFS match on. And `late_costs` (job_id, dt, running_cost), loaded by its Power Query.
- Total Row: `job_totals (Total Row)` needs no query of its own. The summary's query ends with WITH ROLLUP.

**Final: job_totals**

```sql
WITH region_costs AS (
  SELECT r.job_id, r.cost_cents, r.region, r.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(r.cost_cents) OVER (PARTITION BY r.job_id
      ORDER BY CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON j.job_id = r.job_id
  LEFT JOIN <database>.region_budgets b ON b.job_id = r.job_id
)
SELECT job_id,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(CASE WHEN over_budget = TRUE THEN 1 END), 0) AS over_count
FROM region_costs
GROUP BY job_id WITH ROLLUP
```

The rollup row has job_id NULL. Its total_cents is a SUM of the SUMs and its over_count a SUM of the COUNTs, as SUBTOTAL 109 gives.

**Final: late_costs**

```sql
WITH region_costs AS (
  SELECT r.job_id, r.cost_cents, r.region, r.dt,
    j.job_name,
    b.budget_cents AS budget,
    COALESCE(r.cost_cents, 0) > b.budget_cents AS over_budget,
    COALESCE(SUM(r.cost_cents) OVER (PARTITION BY r.job_id
      ORDER BY CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2))
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON j.job_id = r.job_id
  LEFT JOIN <database>.region_budgets b ON b.job_id = r.job_id
)
SELECT job_id, dt, running_cost
FROM region_costs
WHERE running_cost > 1500
```

**Marks**
- cost_cents is blank in one row (job 2, 20260924). over_budget is a comparison, not inside an -IFS form, so the blank is wrapped as COALESCE(cost_cents, 0). The totals and the running total skip it.
- dt is held as text (20260911). The running total orders on it converted to yyyy-mm-dd, with CONCAT and SUBSTR. late_costs keeps dt as held.
- running_cost is SUMIFS over the same job_id with dt "<=" this row's dt, a running total per job with ties included.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X70

**Map**
- Sources: `jobs` (job_id, job_name, team, region), `job_owners` (job_id, team, owner, dt), `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: `staffed` (connection only, but owner_load reads it, so it is a step and not left out), and `owner_load` (the query, which busiest_owner reads).
- Finals: `owner_load` (owner, total_mins, runs, avg_mins), loaded by its query, and `busiest_owner` (owner, total_mins, runs).
- Total Row: `owner_load (Total Row)`, a query of its own.

**Final: owner_load**

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON o.job_id = j.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON r.job_id = s.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs, total_mins / runs AS avg_mins
FROM owner_load
```

**Total Row: owner_load (Total Row)**

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON o.job_id = j.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON r.job_id = s.job_id
  GROUP BY s.owner
)
SELECT SUM(runs) AS runs
FROM owner_load
```

**Final: busiest_owner**

```sql
WITH staffed AS (
  SELECT j.job_id, j.job_name, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o ON o.job_id = j.job_id
  WHERE o.owner IS NOT NULL
),
owner_load AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON r.job_id = s.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs
FROM owner_load
ORDER BY runs DESC
LIMIT 1
```

**Marks**
- staffed: Table.Distinct over job_id and owner is SELECT DISTINCT. Owner not null is IS NOT NULL, which drops the blank owner of job 4.
- owner_load: the NestedJoin is a LEFT JOIN, Table.RowCount is COUNT(*), and List.Sum is SUM. avg_mins is total_mins / runs.
- busiest_owner: Table.Sort by runs descending then FirstN 1 is ORDER BY runs DESC LIMIT 1.
- Total Row: the "Total" label is left out, and SUBTOTAL(109) on runs is SUM.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X73

**Map**
- Sources: `region_budgets` (job_id, budget_cents, region), `jobs` (job_id, job_name, team, region).
- Steps: `eu_budgets` (job_id, budget_cents, region, job_name, dollars). It is read by the query eu_count, so it is a CTE and not a final.
- Finals: `eu_count` (region, jobs, total_cents), loaded by its Power Query.

**Final: eu_count**

```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name,
    b.budget_cents / 100 AS dollars
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON j.job_id = b.job_id
  WHERE b.region = 'eu'
)
SELECT region, COUNT(*) AS jobs, SUM(budget_cents) AS total_cents
FROM eu_budgets
GROUP BY region
```

**Marks**
- eu_budgets: region = "eu" is `region = 'eu'`, and the NestedJoin with Inner is an inner JOIN on job_id, with job_name expanded.
- dollars is budget_cents / 100. It sits in the step only, since eu_budgets is read and so is not a final, and it does not appear in eu_count.
- count of rows is COUNT(*), and total is SUM(budget_cents).
- There are no blanks.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.

## X74

**Map**
- Sources: `run_alerts` (alert_id, run_id, severity, dt), `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: `run_alerts` (status, job_id, alerts_so_far). It has formula columns and two finals read it, so it is a CTE `run_alerts` in each.
- Finals: `by_status` (status, alerts), a summary of run_alerts, since its only typed column, status, is what COUNTIFS matches on. And `late_alerts` (alert_id, run_id, alerts_so_far), loaded by its Power Query.

**Final: by_status**

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    r.status, r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON r.run_id = a.run_id
)
SELECT status, COALESCE(COUNT(*), 0) AS alerts
FROM run_alerts
GROUP BY status
```

**Final: late_alerts**

```sql
WITH run_alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    r.status, r.job_id,
    COUNT(*) OVER (ORDER BY a.run_id RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON r.run_id = a.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM run_alerts
WHERE alerts_so_far > 5
```

**Marks**
- status and job_id are XLOOKUPs with no fourth argument, so they are LEFT JOINs on job_runs. Every alert's run is in job_runs.
- alerts_so_far is COUNTIFS with "<=" of this row's run_id, a running count with ties included.
- by_status is GROUP BY status, as COUNTIFS matches on it. Its two rows are FAILED and SUCCESS.
- late_alerts: Table.SelectRows on alerts_so_far is a WHERE on the step.
- Keys has no row and nothing is typed over a formula.

**Refusals:** none.

**Left alone:** the Steps sheet holds no Table.

**Fill in:** `<database>`.

Before you run `project.convert` on this Hive, take out anything you don't want converted and fill in each `<...>`. Toolbox code is not written in this answer.
