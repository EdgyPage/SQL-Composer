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

## X46

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team).
- Steps: none.
- Finals: jobs (job_id, job_name, team, shortest, runs, busiest).
- Typed over a formula: none.
- Marks: none. No blank sits in a column a formula reads.
- Refused: none.
- Left alone: none. Parameters and Keys are empty, so none.
- Fill in: `<database>`.

```sql
WITH counted AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(s.shortest, 0) AS shortest,
    COALESCE(c.runs, 0) AS runs
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, MIN(duration_mins) AS shortest
    FROM <database>.job_runs
    GROUP BY job_id
  ) s ON j.job_id = s.job_id
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS runs
    FROM <database>.job_runs
    GROUP BY job_id
  ) c ON j.job_id = c.job_id
)
SELECT job_id, job_name, team, shortest, runs,
  RANK() OVER (ORDER BY runs DESC) AS busiest
FROM counted
```

## X47

**Map**
- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, cheapest_first, region_total, region_avg).
- Typed over a formula: none.
- Marks: region_avg is AVERAGEIF, so AVG, left NULL. region_total is SUMIF over its own Table, so a window with COALESCE.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT job_id, budget_cents, region,
  RANK() OVER (ORDER BY budget_cents ASC) AS cheapest_first,
  COALESCE(SUM(budget_cents) OVER (PARTITION BY region), 0) AS region_total,
  AVG(budget_cents) OVER (PARTITION BY region) AS region_avg
FROM <database>.region_budgets
```

## X48

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name, team, region); run_alerts (alert_id, run_id, severity, dt).
- Steps: none.
- Finals: quiet_runs (run_id, job_id, status); slow_regions (region, avg_mins, fastest).
- Typed over a formula: none.
- Marks: none. No formula reads a blank.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final quiet_runs (Power Query LeftAnti, then select):

```sql
SELECT r.run_id, r.job_id, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
WHERE a.run_id IS NULL
```

Final slow_regions (Power Query inner join, group, then the HAVING on the averaged value):

```sql
SELECT j.region,
  AVG(r.duration_mins) AS avg_mins,
  MIN(r.duration_mins) AS fastest
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.region
HAVING AVG(r.duration_mins) >= 20
```

## X49

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); run_alerts (alert_id, run_id, severity, dt); jobs (job_id, job_name, team, region); scheduler_runs (run_id, job_id, dt); job_owners (job_id, team, owner, dt).
- Steps: none. No query is read by another query or by a formula.
- Finals: alert_status (alert_id, severity, status); run_check (run_id, status, scheduled_run); teams (team).
- Typed over a formula: none.
- Marks: none. Blank status (run 98), blank owner and blank severity are kept as NULL; no formula reads them.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final alert_status (RightOuter, so the two tables swap to a LEFT JOIN from job_runs):

```sql
SELECT a.alert_id, a.severity, r.status
FROM <database>.job_runs r
LEFT JOIN <database>.run_alerts a ON r.run_id = a.run_id
```

Final run_check (FullOuter):

```sql
SELECT r.run_id, r.status, s.run_id AS scheduled_run
FROM <database>.job_runs r
FULL OUTER JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

Final teams (Table.Combine inside Table.Distinct, so UNION):

```sql
SELECT team FROM <database>.jobs
UNION
SELECT team FROM <database>.job_owners
```

## X50

**Map**
- Sources: job_owners (job_id, team, owner, dt); jobs (job_id, job_name, team, region).
- Steps: none.
- Finals: owners (job_id, owner, job_name, newest_first).
- Typed over a formula: none.
- Marks: none. The blank owner for job 4 stays NULL; no formula reads owner.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

```sql
SELECT o.job_id, o.owner, j.job_name,
  RANK() OVER (ORDER BY o.job_id DESC) AS newest_first
FROM (
  SELECT DISTINCT job_id, owner
  FROM <database>.job_owners
) o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

## X59

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); jobs (job_id, job_name); run_alerts (alert_id, run_id, severity, dt).
- Steps: none.
- Finals: jobs (job_id, job_name, long_runs, failed_mins, not_test); run_alerts (alert_id, run_id, severity, dt, alerts_so_far).
- Typed over a formula: none.
- Marks: blank status (run 98) is not wrapped. not_test counts it, as Excel counts a blank under "<>TEST", and failed_mins skips it, as the "f*" match does. No COALESCE on status.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final jobs (COUNTIFS and SUMIFS over another Table, so LEFT JOINs to grouped subqueries):

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

Final run_alerts (running count over its own Table, ties included):

```sql
SELECT alert_id, run_id, severity, dt,
  COALESCE(COUNT(*) OVER (ORDER BY run_id
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
FROM <database>.run_alerts
```

## X60

**Map**
- Sources: region_budgets (job_id, budget_cents, region).
- Steps: none.
- Finals: region_budgets (job_id, budget_cents, region, share, above_avg, rank_in_region); region_budgets (Total Row) (one row: COUNT of job_id, AVG of budget_cents, no label).
- Typed over a formula: none.
- Marks: none. No blanks in the sample.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final region_budgets (SUM and AVERAGE over the whole column are windows; COUNTIFS "<" +1 is RANK ASC within region):

```sql
SELECT job_id, budget_cents, region,
  budget_cents / SUM(budget_cents) OVER () AS share,
  budget_cents > AVG(budget_cents) OVER () AS above_avg,
  RANK() OVER (PARTITION BY region ORDER BY budget_cents ASC) AS rank_in_region
FROM <database>.region_budgets
```

Total Row region_budgets (Total Row):

```sql
SELECT COUNT(job_id) AS job_id, AVG(budget_cents) AS budget_cents
FROM <database>.region_budgets
```

## X61

**Map**
- Sources: region_costs (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: by_region (region, total_cents, entries, priciest). It is a summary of region_costs, since its only typed column is region.
- Total Row of by_region: folded into by_region's query by GROUP BY ... WITH ROLLUP. Its row is the one with region NULL (the Subtotal row). No separate query.
- Typed over a formula: none.
- Marks: blank cost_cents (job 2, 20260924) stays NULL. SUMIFS and MAXIFS skip it, and COUNTIFS counts the row, as Excel does. dt is held as text (20260911), but no formula reads it, so it is not converted.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final by_region (summary with the Total Row folded in):

```sql
SELECT region,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(*), 0) AS entries,
  COALESCE(MAX(cost_cents), 0) AS priciest
FROM <database>.region_costs
GROUP BY region WITH ROLLUP
```

## X62

**Map**
- Sources: team_notes (team, note, written_on).
- Steps: none.
- Finals: team_notes (team, note, written_on, week_of, month_end, month_of, months_in, three_before, who, short).
- Typed over a formula: none.
- Marks: week_of and month_of are CAST to STRING, as file 11 writes the week and month starts.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

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

## X63

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs); scheduler_runs (run_id, job_id, dt).
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_retry, quarters, capped, variance, weighted, scheduled_job, label, succeeded).
- Typed over a formula: none.
- Marks: blank status (run 98) is wrapped as COALESCE(status, '') in succeeded, because SEARCH on a blank is not a match in Excel. blank avg_retry_secs is not wrapped, since no_retry is ISBLANK and becomes IS NULL. Run 99 has no scheduler row, so scheduled_job is -1 by the XLOOKUP fourth argument.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

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

## X64

**Map**
- Sources: jobs (job_id, job_name, team, region); region_costs (job_id, cost_cents, region, dt).
- Steps: none.
- Finals: picked_costs (job_id, cost_cents, region, size); costed_jobs (job_id, job_name, team, region); costs_filled (job_id, cost_cents, dt, day).
- Typed over a formula: none.
- Marks: in costs_filled, the blank cost_cents (job 2, 20260924) becomes 0 by COALESCE, as Table.ReplaceValue does. dt is held as text (20260911), so it is converted to 2026-09-11 with CONCAT(SUBSTR...). day reads the last two characters, as Text.End does.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final picked_costs:

```sql
SELECT job_id, cost_cents, UPPER(region) AS region,
  IF(cost_cents >= 200, 'big', 'small') AS size
FROM <database>.region_costs
WHERE cost_cents IS NOT NULL AND job_id IN (1, 3)
```

Final costed_jobs (List.Contains on another Table is a LEFT SEMI JOIN; "and not" is NOT):

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.region_costs c ON c.job_id = j.job_id
WHERE NOT (j.job_name LIKE 'n%')
```

Final costs_filled:

```sql
SELECT job_id,
  COALESCE(cost_cents, 0) AS cost_cents,
  CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS dt,
  SUBSTR(dt, -2) AS day
FROM <database>.region_costs
```

## X65

**Map**
- Sources: jobs (job_id, job_name, team, region); region_budgets (job_id, budget_cents, region); job_owners (job_id, team, owner, dt); scheduler_runs (run_id, job_id, dt); job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: team_regions (team, region); budget_places (job_id, budget_cents, region, place); jobs_per_team (team, jobs); ran_as_scheduled (run_id, dt); run_measures (run_id, job_id, measure, amount).
- Typed over a formula: none.
- Marks: team_regions sorts by team with no FirstN and no index after it, so the order was dropped and there is no ORDER BY. run_measures drops run 98's blank avg_retry_secs, as Table.Unpivot drops a null. jobs_per_team counts COUNT(DISTINCT job_id); no job_id is blank.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final team_regions (AddColumn then expand is a CROSS JOIN):

```sql
SELECT t.team, u.region
FROM (SELECT DISTINCT team FROM <database>.jobs) t
CROSS JOIN (SELECT DISTINCT region FROM <database>.jobs) u
```

Final budget_places (Table.Sort then AddIndexColumn, so ROW_NUMBER with the sort's order):

```sql
SELECT job_id, budget_cents, region,
  ROW_NUMBER() OVER (ORDER BY budget_cents DESC) AS place
FROM <database>.region_budgets
```

Final jobs_per_team:

```sql
SELECT team, COUNT(DISTINCT job_id) AS jobs
FROM <database>.job_owners
GROUP BY team
```

Final ran_as_scheduled (inner join on both keys, then distinct):

```sql
SELECT DISTINCT s.run_id, s.dt
FROM <database>.scheduler_runs s
JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.dt = r.dt
```

Final run_measures (Table.Unpivot as one SELECT per column, stacked, each with a NOT NULL filter):

```sql
SELECT run_id, job_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, job_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

## X66

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: none.
- Finals: ok_runs (run_id, job_id, duration_mins, dt, running, share); ok_runs (Total Row) (duration_mins, one column, no label).
- Typed over a formula: none.
- Marks: the blank status (run 98) is dropped by status IS NOT NULL, as the M does. Text.StartsWith is LIKE 'SUCC%', case kept. running is SUMIFS over its own Table with "<=", so a RANGE window that counts ties.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final ok_runs:

```sql
SELECT run_id, job_id, duration_mins, dt,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running,
  duration_mins / SUM(duration_mins) OVER () AS share
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
```

Total Row ok_runs (Total Row):

```sql
WITH ok_runs AS (
  SELECT duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status LIKE 'SUCC%'
)
SELECT SUM(duration_mins) AS duration_mins
FROM ok_runs
```

## X69

**Map**
- Sources: jobs (job_id, job_name, team, region); region_budgets (job_id, budget_cents, region).
- Steps: region_costs, a Table with formulas that job_totals and late_costs read. It is kept as the CTEs dated and costs inside each final's query.
- Finals: job_totals (job_id, total_cents, over_count), a summary of costs; late_costs (job_id, dt, running_cost).
- Typed over a formula: none.
- Marks: dt is held as text (20260911) and is converted with CONCAT(SUBSTR...) in dated, since the running total orders by it. Blank cost_cents (job 2, 20260924): over_budget uses COALESCE(cost_cents, 0), a comparison and not an -IFS form. running_cost and total_cents skip the blank, as SUMIFS does.
- Refused: none.
- Left alone: none.
- Total Row of job_totals: folded into its query by GROUP BY job_id WITH ROLLUP. Its row has job_id NULL.
- late_costs tests a window's value in the outer statement, reading the costs CTE.
- Fill in: `<database>`.

Final job_totals:

```sql
WITH dated AS (
  SELECT r.job_id, r.cost_cents, r.region,
    CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) AS dt,
    j.job_name,
    b.budget_cents AS budget
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
costs AS (
  SELECT job_id, cost_cents, region, dt, job_name, budget,
    COALESCE(cost_cents, 0) > budget AS over_budget,
    COALESCE(SUM(cost_cents) OVER (PARTITION BY job_id ORDER BY dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM dated
)
SELECT job_id,
  COALESCE(SUM(cost_cents), 0) AS total_cents,
  COALESCE(COUNT(CASE WHEN over_budget = TRUE THEN 1 END), 0) AS over_count
FROM costs
GROUP BY job_id WITH ROLLUP
```

Final late_costs (the same dated and costs CTEs, then the filter):

```sql
WITH dated AS (
  SELECT r.job_id, r.cost_cents, r.region,
    CONCAT(SUBSTR(r.dt, 1, 4), '-', SUBSTR(r.dt, 5, 2), '-', SUBSTR(r.dt, 7, 2)) AS dt,
    j.job_name,
    b.budget_cents AS budget
  FROM <database>.region_costs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
costs AS (
  SELECT job_id, cost_cents, region, dt, job_name, budget,
    COALESCE(cost_cents, 0) > budget AS over_budget,
    COALESCE(SUM(cost_cents) OVER (PARTITION BY job_id ORDER BY dt
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_cost
  FROM dated
)
SELECT job_id, dt, running_cost
FROM costs
WHERE running_cost > 1500
```

## X70

**Map**
- Sources: jobs (job_id, job_name, team, region); job_owners (job_id, team, owner, dt); job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt).
- Steps: staffed, a connection-only query that owner_load's query reads, so it is kept as a CTE; and the owner_load query, which busiest_owner reads, kept as the CTE grouped.
- Finals: owner_load (owner, total_mins, runs, avg_mins); owner_load (Total Row) (runs, one column, no label); busiest_owner (owner, total_mins, runs).
- Typed over a formula: none.
- Marks: the blank owner for job 4 is dropped by owner IS NOT NULL, as the M's <> null does. avg_mins is total_mins / runs.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final owner_load:

```sql
WITH staffed AS (
  SELECT j.job_id, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
    ON j.job_id = o.job_id
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

Total Row owner_load (Total Row):

```sql
WITH staffed AS (
  SELECT j.job_id, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
    ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
grouped AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT SUM(runs) AS runs
FROM grouped
```

Final busiest_owner (Table.Sort then FirstN 1):

```sql
WITH staffed AS (
  SELECT j.job_id, o.owner
  FROM <database>.jobs j
  JOIN (SELECT DISTINCT job_id, owner FROM <database>.job_owners) o
    ON j.job_id = o.job_id
  WHERE o.owner IS NOT NULL
),
grouped AS (
  SELECT s.owner, SUM(r.duration_mins) AS total_mins, COUNT(*) AS runs
  FROM staffed s
  LEFT JOIN <database>.job_runs r ON s.job_id = r.job_id
  GROUP BY s.owner
)
SELECT owner, total_mins, runs
FROM grouped
ORDER BY runs DESC
LIMIT 1
```

## X73

**Map**
- Sources: region_budgets (job_id, budget_cents, region); jobs (job_id, job_name, team, region).
- Steps: eu_budgets, the query that eu_count's query reads, kept as the CTE eu_budgets.
- Finals: eu_budgets (job_id, budget_cents, region, job_name, dollars); eu_count (region, jobs, total_cents).
- Typed over a formula: none.
- Marks: none. No blanks in the sample.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final eu_budgets:

```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT job_id, budget_cents, region, job_name,
  budget_cents / 100 AS dollars
FROM eu_budgets
```

Final eu_count:

```sql
WITH eu_budgets AS (
  SELECT b.job_id, b.budget_cents, b.region, j.job_name
  FROM <database>.region_budgets b
  JOIN <database>.jobs j ON b.job_id = j.job_id
  WHERE b.region = 'eu'
)
SELECT region,
  COUNT(*) AS jobs,
  SUM(budget_cents) AS total_cents
FROM eu_budgets
GROUP BY region
```

## X74

**Map**
- Sources: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt); run_alerts (alert_id, run_id, severity, dt).
- Steps: run_alerts, a Table with formulas (status, job_id, alerts_so_far) that by_status and late_alerts read. It is kept as the CTE alerts.
- Finals: by_status (status, alerts), a summary of the step since its only typed column is status; late_alerts (alert_id, run_id, alerts_so_far).
- Typed over a formula: none.
- Marks: none. The only blank status (run 98) is not an alert's run.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

The CTE used by both finals:

```sql
WITH alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    r.status, r.job_id,
    COALESCE(COUNT(*) OVER (ORDER BY a.run_id
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
```

Final by_status:

```sql
WITH alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    r.status, r.job_id,
    COALESCE(COUNT(*) OVER (ORDER BY a.run_id
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT status, COALESCE(COUNT(*), 0) AS alerts
FROM alerts
GROUP BY status
```

Final late_alerts (the window is computed in the CTE, then tested in the outer statement):

```sql
WITH alerts AS (
  SELECT a.alert_id, a.run_id, a.severity, a.dt,
    r.status, r.job_id,
    COALESCE(COUNT(*) OVER (ORDER BY a.run_id
      RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS alerts_so_far
  FROM <database>.run_alerts a
  LEFT JOIN <database>.job_runs r ON a.run_id = r.run_id
)
SELECT alert_id, run_id, alerts_so_far
FROM alerts
WHERE alerts_so_far > 5
```

## X77

**Map**
- Sources: run_alerts (alert_id, run_id, severity, dt).
- Steps: the high_alerts query, which high_per_day's query reads, kept as the CTE high_alerts.
- Finals: high_alerts (alert_id, run_id, dt, late_run); high_per_day (dt, alerts).
- Typed over a formula: none.
- Marks: none.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final high_alerts:

```sql
WITH high_alerts AS (
  SELECT alert_id, run_id, dt
  FROM <database>.run_alerts
  WHERE severity = 'high'
)
SELECT alert_id, run_id, dt,
  run_id > 100 AS late_run
FROM high_alerts
```

Final high_per_day:

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

## X78

**Map**
- Sources: region_costs (job_id, cost_cents, region, dt).
- Steps: known_costs, the query that cost_per_job's query reads, kept as the CTE known_costs.
- Finals: known_costs (job_id, cost_cents, dt, dollars); known_costs (Total Row) (cost_cents, one column, no label); cost_per_job (job_id, total_cents).
- Typed over a formula: none.
- Marks: the blank cost_cents (job 2, 20260924) is dropped by cost_cents IS NOT NULL, as the M's <> null does. So known_costs has 27 rows, and job 2's total leaves that row out. dt is held as text, but no formula reads it, so it is not converted.
- Refused: none.
- Left alone: none.
- Fill in: `<database>`.

Final known_costs:

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT job_id, cost_cents, dt,
  cost_cents / 100 AS dollars
FROM known_costs
```

Total Row known_costs (Total Row):

```sql
WITH known_costs AS (
  SELECT job_id, cost_cents, dt
  FROM <database>.region_costs
  WHERE cost_cents IS NOT NULL
)
SELECT SUM(cost_cents) AS cost_cents
FROM known_costs
```

Final cost_per_job (Table.Group, List.Sum):

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
