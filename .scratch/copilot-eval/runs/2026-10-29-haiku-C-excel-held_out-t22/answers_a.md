date: 2026-10-29
arm: C
model: haiku
files: 423bc80

## X21

**Map**
- Sources: region_budgets (typed: job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin).

**Typed over a formula:** none, so no Keys row is needed (Keys is empty).
**Marks:** none.
**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`.

```sql
SELECT job_id, budget_cents, region,
  budget_cents / 100 AS budget_dollars,
  budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets
```

## X22

**Map**
- Sources: jobs (typed: job_id, job_name, team).
- Steps: none.
- Finals: jobs (job_id, job_name, team, is_finance, ratio).

**Typed over a formula:** none (Keys is empty).
**Marks:** IFERROR(job_id / (job_id - 2), 0) converted as COALESCE(job_id / (job_id - 2), 0). For job 2 the divisor is 0, so the division is NULL and COALESCE gives 0, as IFERROR does.
**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`.

```sql
SELECT job_id, job_name, team,
  IF(team = 'finance', 'yes', 'no') AS is_finance,
  COALESCE(job_id / (job_id - 2), 0) AS ratio
FROM <database>.jobs
```

## X23

**Map**
- Sources: job_runs (typed: run_id, status, avg_retry_secs).
- Steps: none.
- Finals: job_runs (run_id, status, avg_retry_secs, label, risky).

**Typed over a formula:** none (Keys is empty).
**Marks:**
- blank: run 98 has a blank status, read by SWITCH and OR, so it is wrapped as COALESCE(status, '').
- blank: run 98 has a blank avg_retry_secs, read by OR, so it is wrapped as COALESCE(avg_retry_secs, 0). Without the wrap, OR with a NULL comparison would give NULL where Excel gives FALSE.
- SWITCH(status, "SUCCESS", "ok", "FAILED", "bad", "other") converted as a CASE with ELSE 'other'.

**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`.

```sql
SELECT run_id, status, avg_retry_secs,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label,
  (COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs
```

## X24

**Map**
- Sources: team_notes (typed: team, note, written_on).
- Steps: none.
- Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars).

**Typed over a formula:** none (Keys is empty).
**Marks:** FIND(" ", note) converted as INSTR(note, ' '). LEFT(note, n) converted as SUBSTR(note, 1, n). No blanks in the sample.
**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`.

```sql
SELECT team, note, written_on,
  SUBSTR(note, 1, INSTR(note, ' ') - 1) AS first_word,
  UPPER(team) AS shout,
  MONTH(written_on) AS month,
  ROUND(LENGTH(note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes
```

## X25

**Map**
- Sources: Costs (typed: Job, Cost (cents) as `<cost_cents>`, Region, Day Key as `<day_key>`); Budgets (typed: Job, Budget, Region).
- Steps: none.
- Finals:
  - Costs (Job, `<cost_cents>`, Region, `<day_key>`, Day)
  - Budgets (Job, Budget, Region, Dollars)

**Typed over a formula:** none (Keys is empty).
**Marks:**
- A date held as text: Day Key holds 20260911 as text. Day's DATE(LEFT(...), MID(...), RIGHT(...)) is converted as CONCAT(SUBSTR(day_key, 1, 4), '-', SUBSTR(day_key, 5, 2), '-', SUBSTR(day_key, 7, 2)).
- blank: Cost (cents) is blank in row 29 (Job 2, 2026-09-24). No formula reads Cost, so nothing is wrapped and the value stays NULL.

**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`, `<cost_cents>` (header `Cost (cents)`), `<day_key>` (header `Day Key`).

```sql
SELECT Job, <cost_cents>, Region, <day_key>,
  CONCAT(SUBSTR(<day_key>, 1, 4), '-', SUBSTR(<day_key>, 5, 2), '-', SUBSTR(<day_key>, 7, 2)) AS Day
FROM <database>.Costs
```

```sql
SELECT Job, Budget, Region, Budget / 100 AS Dollars
FROM <database>.Budgets
```

## X26

**Map**
- Sources: run_alerts (typed: alert_id, run_id, severity); job_runs (typed: run_id, job_id, status, duration_mins).
- Steps: none.
- Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins).

**Typed over a formula:** none (Keys is empty).
**Marks:**
- XLOOKUP(run_id, job_runs[run_id], job_runs[job_id]) converted as a LEFT JOIN to job_runs on run_id, then job_id.
- VLOOKUP(run_id, job_runs, 3, FALSE) converted as the same LEFT JOIN, then status, with COALESCE(status, '') for the blank in job_runs run 98. No alert points at run 98, so the wrap changes nothing in the sample.
- AVERAGEIFS converted as AVG over job_runs grouped by job_id, joined on the job_id, left NULL with no COALESCE.

**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`.

```sql
SELECT a.alert_id, a.run_id, a.severity,
  j.job_id,
  COALESCE(j.status, '') AS status,
  m.avg_mins
FROM <database>.run_alerts a
LEFT JOIN <database>.job_runs j ON a.run_id = j.run_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) m ON j.job_id = m.job_id
```

## X27

**Map**
- Sources: jobs (typed: job_id, job_name, team, region).
- Steps: none.
- Finals: by_team (team, jobs_in_team, last_job_id, last_job_name).
- by_team is a summary: its only typed column, team, is what its COUNTIFS match on, so it is a GROUP BY team of jobs. Its MAXIFS and INDEX/MATCH are written in the same query.

**Typed over a formula:** none (Keys is empty).
**Marks:**
- COUNTIFS and MAXIFS are each wrapped in COALESCE, as Excel gives 0 where nothing matches. Inside the GROUP BY every team has rows, so the wrap changes nothing in the sample.
- INDEX(job_name, MATCH(last_job_id, job_id, 0)) converted as a LEFT JOIN on last_job_id = job_id, then job_name.

**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`.

```sql
WITH grouped AS (
  SELECT team,
    COALESCE(COUNT(*), 0) AS jobs_in_team,
    COALESCE(MAX(job_id), 0) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
)
SELECT g.team, g.jobs_in_team, g.last_job_id, j.job_name AS last_job_name
FROM grouped g
LEFT JOIN <database>.jobs j ON g.last_job_id = j.job_id
```

## X28

**Map**
- Sources: jobs (typed: job_id, job_name); job_runs (typed: run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: jobs (job_id, job_name, ok_mins).

**Typed over a formula:** ok_mins for report_build (job 3) is typed as 99. Keys holds jobs | job_id, so the row is matched on job_id = 3: CASE WHEN job_id = 3 THEN 99 ELSE ... END.
**Marks:**
- SUMIFS with job_id and status criteria converted as a LEFT JOIN to a grouped sum of duration_mins over status = 'SUCCESS', with COALESCE(total, 0).
- blank: run 98 has a blank status. It is a SUMIFS criterion, which skips a blank, so it is not wrapped.

**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`.

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

## X29

**Map**
- Sources: region_budgets (typed: job_id, budget_cents, region).
- Parameters: cents_per_dollar = 100. The XLOOKUP reads its value, 100, which is used as written.
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer).

**Typed over a formula:** in_dollars for row 4 (job 3, 350, us) is typed as 5. There is no Keys row for region_budgets, so the row is matched on every typed column: job_id = 3 AND budget_cents = 350 AND region = 'us'.
**Marks:** XLOOKUP into Parameters converted to its value, 100.
**Refused:**
- pointer: INDIRECT("A" & ROW()) reads by address and by ROW(), so it is refused as `NULL AS pointer`.

**Left alone:** none.
**Fill in:** `<database>`.

```sql
SELECT job_id, budget_cents, region,
  CASE WHEN job_id = 3 AND budget_cents = 350 AND region = 'us' THEN 5 ELSE budget_cents / 100 END AS in_dollars,
  NULL AS pointer
FROM <database>.region_budgets
```

## X30

**Map**
- Sources: scheduler_runs (typed: run_id, job_id, dt).
- Steps: none.
- Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter).

**Typed over a formula:** none (Keys is empty).
**Marks:** RIGHT(dt, 2) converted as SUBSTR(dt, -2).
**Refused:**
- prev_run: OFFSET(run_id, -1, 0) reads the row before, which is refused as `NULL AS prev_run`.
- jitter: RANDBETWEEN(1, 5) is random, refused as `NULL AS jitter`.

**Left alone:** the PivotTable on sheet "Pivot" (from scheduler_runs), and the bar chart on sheet "Summary".
**Fill in:** `<database>`.

```sql
SELECT run_id, job_id, dt,
  SUBSTR(dt, -2) AS day,
  NULL AS prev_run,
  NULL AS jitter
FROM <database>.scheduler_runs
```

## X31

**Map**
- Sources: jobs (typed: job_id, team).
- Steps: none.
- Finals: jobs (job_id, team, bump, tag, scaled, boosted).

**Typed over a formula:** none (Keys is empty).
**Marks:**
- Defined name `boost` = Summary!$B$2 (a cell outside a Table), used as its value, 10. Move it into Parameters.

**Refused:**
- bump: `=jobs[[#This Row],[bump]]*2` reads its own column (circular), so `NULL AS bump`.
- tag: the defined name TAG holds a LAMBDA, so `NULL AS tag`.
- scaled: reads Summary!D4, a cell outside a Table that is not a defined name, so `NULL AS scaled`.

**Left alone:** the Summary sheet's cells outside a Table: B2 (read through the name boost) and D4 (refused, see scaled).
**Fill in:** `<database>`.

```sql
SELECT job_id, team,
  NULL AS bump,
  NULL AS tag,
  NULL AS scaled,
  job_id * 10 AS boosted
FROM <database>.jobs
```

## X32

**Map**
- Sources: job_runs (typed: run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed: job_id, job_name, team, region).
- Steps: job_runs, whose formula job_name is read by by_name, so it is a CTE in by_name's query.
- Finals: by_name (job_name, runs).
- by_name is a summary: its only typed column, job_name, is what its COUNTIFS match on, so it is a GROUP BY job_name of the step.

**Typed over a formula:** none (Keys is empty).
**Marks:**
- VLOOKUP(job_id, jobs, 2, TRUE) is approximate. It is converted exactly, as a LEFT JOIN on job_id = job_id, then job_name. Stated here: this is an exact match, not the approximate lookup the formula asks for.
- COUNTIFS is wrapped in COALESCE, as Excel gives 0 where nothing matches.

**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`.

```sql
WITH job_runs_step AS (
  SELECT j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT job_name, COALESCE(COUNT(*), 0) AS runs
FROM job_runs_step
GROUP BY job_name
```

## X33

**Map**
- Sources: `<database>.job_runs`, the table job_runs that Power Query reads from Sql.Database("dwh01", "ops"). Check that `<database>` is the Hive database that holds ops.job_runs from dwh01.
- Steps: none.
- Finals: slow_runs (run_id, duration_mins, over_by), loaded by Power Query "slow_runs".

**Typed over a formula:** none (Keys is empty).
**Marks:**
- Sql.Database source: the query names the table job_runs in schema ops on server dwh01. Check the database and table name before running.
- M's `<>` keeps a null, so `[status] <> "TEST"` is written as `(status <> 'TEST' OR status IS NULL)`.
- Table.AddColumn `over_by` converted as `duration_mins - 20 AS over_by`.

**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`.

```sql
SELECT run_id, duration_mins, duration_mins - 20 AS over_by
FROM <database>.job_runs
WHERE duration_mins >= 20 AND (status <> 'TEST' OR status IS NULL)
```

## X34

**Map**
- Sources: job_runs (typed: run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed: job_id, job_name, team, region).
- Steps: runs_with_team, a connection-only query that team_totals reads, so it is a CTE in team_totals' query.
- Finals: team_totals (team, total_mins, longest), loaded by Power Query "team_totals".

**Typed over a formula:** none (Keys is empty).
**Marks:**
- Table.NestedJoin with JoinKind.LeftOuter converted as LEFT JOIN, then the team column expanded.
- Table.Group: List.Sum as SUM, List.Max as MAX.

**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`.

```sql
WITH runs_with_team AS (
  SELECT r.duration_mins, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT team, SUM(duration_mins) AS total_mins, MAX(duration_mins) AS longest
FROM runs_with_team
GROUP BY team
```

## X35

**Map**
- Sources: job_runs (typed: run_id, job_id, status, duration_mins, avg_retry_secs, dt); scheduler_runs (typed: run_id, job_id, dt).
- Steps: none.
- Finals: recent (run_id, dt), loaded by Power Query "recent".
- Left out, and named: the Power Query "rates", a connection-only query that nothing reads and that reads a web source (Web.Contents).

**Typed over a formula:** none.
**Marks:**
- Table.Combine converted as UNION ALL.
- Table.Sort by run_id descending, then Table.FirstN 4, converted as ORDER BY run_id DESC LIMIT 4.

**Refused:** none. The web query "rates" is left out (see Map).
**Left alone:** none.
**Fill in:** `<database>`.

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

## X36

**Map**
- Sources: run_alerts (typed: alert_id, run_id, severity, dt); job_runs (typed: run_id, status).
- Steps: none.
- Finals:
  - job_runs (run_id, status, alerts)
  - severity_by_day (dt, high, low), loaded by Power Query "severity_by_day"

**Typed over a formula:** none (Keys is empty).
**Marks:**
- COUNTIFS over run_alerts, matched on run_id, converted as a LEFT JOIN to a grouped count, with COALESCE(n, 0).
- Table.Pivot on severity: the pivot's columns are now fixed to high and low, the values in the sample. The count uses THEN 1, as the column n is always 1. NULL where a severity has no rows.

**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`.

```sql
SELECT j.run_id, j.status, COALESCE(c.n, 0) AS alerts
FROM <database>.job_runs j
LEFT JOIN (
  SELECT run_id, COUNT(*) AS n
  FROM <database>.run_alerts
  GROUP BY run_id
) c ON j.run_id = c.run_id
```

```sql
SELECT dt,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
GROUP BY dt
```

## X37

**Map**
- Sources: Owners (typed: `<job_no>` (header `Job No`), `<team_name>` (header `Team Name`), Owner, Day).
- Steps: none.
- Finals: Owners (`<job_no>`, `<team_name>`, Owner, Day, `<is_ana>`).

**Typed over a formula:** none, since every Is Ana row has the same formula.
**Marks:**
- blank: 14 rows have a blank Owner (Job 4, web, every day). The IF reads Owner, so it is wrapped as COALESCE(Owner, '').
- IF([@Owner] = "ana", 1, 0) converted as IF(owner = 'ana', 1, 0).

**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`, `<job_no>` (header `Job No`), `<team_name>` (header `Team Name`), `<is_ana>` (header `Is Ana`).

```sql
SELECT <job_no>, <team_name>, Owner, Day,
  IF(COALESCE(Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners
```

## X38

**Map**
- Sources: job_runs (typed: run_id, job_id, status, duration_mins, avg_retry_secs); jobs (typed: job_id, job_name, team, region).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost).

**Typed over a formula:** retry_cost for run 102 is typed as 1. Keys holds job_runs | run_id, so the row is matched on run_id = 102.
**Marks:**
- blank: run 98 has a blank avg_retry_secs, which retry_cost reads, so it is wrapped as COALESCE(avg_retry_secs, 0).
- XLOOKUP(job_id, jobs[job_id], jobs[region]) converted as a LEFT JOIN to jobs on job_id, then region.
- SUMIFS over job_runs matched on its own region column converted as SUM(duration_mins) OVER (PARTITION BY region), with COALESCE(.., 0).

**Refused:** none.
**Left alone:** none.
**Fill in:** `<database>`.

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  j.region AS region,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.region), 0) AS region_mins,
  CASE WHEN r.run_id = 102 THEN 1
    ELSE (COALESCE(r.avg_retry_secs, 0) + r.duration_mins) * 2 END AS retry_cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

## X39

**Map**
- Sources: job_runs (typed: run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (typed: job_id, job_name, team, region).
- Steps: none.
- Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise), loaded by Power Query "ok_runs" with its formula columns.

**Typed over a formula:** none (Keys is empty).
**Marks:**
- Table.SelectRows with `[status] = "SUCCESS"` converted as WHERE status = 'SUCCESS'. The blank status in run 98 is dropped, as M's `=` drops a blank.
- XLOOKUP(job_id, jobs[job_id], jobs[job_name]) converted as a LEFT JOIN to jobs, then job_name.
- SUMIFS over the Table's own rows, matched on job_id, converted as SUM(duration_mins) OVER (PARTITION BY job_id) over the query's rows, with COALESCE(.., 0). The window runs after the WHERE, so it sees only the loaded rows.

**Refused:**
- noise: RAND() is random, so `NULL AS noise`.

**Left alone:** none.
**Fill in:** `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  j.job_name AS job_name,
  r.duration_mins / COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id), 0) AS share,
  NULL AS noise
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
WHERE r.status = 'SUCCESS'
```

## X40

**Map**
- Sources:
  - Runs (typed: Run, Job, Mins)
  - jobs (typed: job_id, job_name, team, region)
  - run_alerts (typed: alert_id, run_id, severity, dt)
- Parameters: rate = 2. The XLOOKUP reads its value, 2, used as written.
- Steps: Runs, whose formula columns Team and Cost are read by Teams and by run_alerts, so it is a CTE in each of their queries.
- Finals:
  - Teams (Team, `<total_cost>` (header `Total Cost`))
  - run_alerts (alert_id, run_id, severity, dt, `<run_mins>` (header `Run Mins`))

**Typed over a formula:** none (Keys is empty).
**Marks:**
- XLOOKUP(Job, jobs[job_id], jobs[team]) converted as a LEFT JOIN to jobs on Job = job_id, then team.
- XLOOKUP("rate", ...) converted to its value, 2, so Cost = Mins * 2.
- Teams: SUMIFS of Cost matched on Team is a summary, so it is a GROUP BY Team of the Runs step, with COALESCE(SUM(Cost), 0).

**Refused:** none.
**Left alone:** the PivotTable on sheet "Pivot" (from Runs, rows Team, values Sum of Cost).
**Fill in:** `<database>`, `<total_cost>`, `<run_mins>`.

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
  x.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN runs_step x ON a.run_id = x.Run
```
