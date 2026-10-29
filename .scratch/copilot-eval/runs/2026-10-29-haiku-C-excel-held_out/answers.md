date: 2026-10-29
arm: C
model: haiku
files: 44f6c5d

## X21

Sources: region_budgets (typed job_id, budget_cents, region).
Steps: none.
Finals: region_budgets (job_id, budget_cents, region, budget_dollars, with_margin). It is a source and a final, since nothing reads it.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: none. The sample has no blanks.
Refused: none.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT r.job_id,
       r.budget_cents,
       r.region,
       r.budget_cents / 100 AS budget_dollars,
       r.budget_cents * 1.1 AS with_margin
FROM <database>.region_budgets r
```

## X22

Sources: jobs (typed job_id, job_name, team).
Steps: none.
Finals: jobs (job_id, job_name, team, is_finance, ratio). It is a source and a final.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: IFERROR(a / b, 0) becomes COALESCE(a / b, 0), because Hive gives NULL for a divide by 0 (job 2 row). IF is IF.
Refused: none.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT j.job_id,
       j.job_name,
       j.team,
       IF(j.team = 'finance', 'yes', 'no') AS is_finance,
       COALESCE(j.job_id / (j.job_id - 2), 0) AS ratio
FROM <database>.jobs j
```

## X23

Sources: job_runs (typed run_id, status, avg_retry_secs).
Steps: none.
Finals: job_runs (run_id, status, avg_retry_secs, label, risky). It is a source and a final.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: blank. Run 98 has a blank status and a blank avg_retry_secs, both read by the formulas, so both are wrapped inside label and risky: COALESCE(status, '') and COALESCE(avg_retry_secs, 0). _xlfn.SWITCH is SWITCH, which becomes a CASE with ELSE 'other'.
Refused: none.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT r.run_id,
       r.status,
       r.avg_retry_secs,
       CASE COALESCE(r.status, '')
            WHEN 'SUCCESS' THEN 'ok'
            WHEN 'FAILED' THEN 'bad'
            ELSE 'other' END AS label,
       (COALESCE(r.status, '') = 'FAILED' OR COALESCE(r.avg_retry_secs, 0) > 5) AS risky
FROM <database>.job_runs r
```

## X24

Sources: team_notes (typed team, note, written_on). written_on is read as a date, since its values are ISO dates and not digits-only text.
Steps: none.
Finals: team_notes (team, note, written_on, first_word, shout, month, tens_of_chars). It is a source and a final.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: none for blanks, since the sample has none. LEFT(note, FIND(" ", note) - 1) becomes SUBSTR(note, 1, INSTR(note, ' ') - 1). LEN becomes LENGTH. UPPER and MONTH are as they are. ROUND is as it is.
Refused: none.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT t.team,
       t.note,
       t.written_on,
       SUBSTR(t.note, 1, INSTR(t.note, ' ') - 1) AS first_word,
       UPPER(t.team) AS shout,
       MONTH(t.written_on) AS month,
       ROUND(LENGTH(t.note) / 10, 1) AS tens_of_chars
FROM <database>.team_notes t
```

## X25

Sources: Costs (typed Job, Cost (cents), Region, Day Key) and Budgets (typed Job, Budget, Region).
Steps: none.
Finals: Costs (Job, Cost (cents), Region, Day Key, Day), which is a source and a final. Budgets (Job, Budget, Region, Dollars), which is a source and a final.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: Day Key holds 20260911, a date held as text. Day is DATE(LEFT, MID, RIGHT) of it, so it becomes CONCAT(SUBSTR(day_key, 1, 4), '-', SUBSTR(day_key, 5, 2), '-', SUBSTR(day_key, 7, 2)), which gives a text date. Costs row 29 has a blank Cost (cents), but no formula reads that column, so it is left NULL and not wrapped.
Refused: none.
Left alone: none.
Fill in: `<database>`, `<cost_cents>` (the header Cost (cents)), `<day_key>` (the header Day Key).

Toolbox step: take out what you don't want converted, fill in the placeholders, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT c.Job,
       c.<cost_cents>,
       c.Region,
       c.<day_key>,
       CONCAT(SUBSTR(c.<day_key>, 1, 4), '-', SUBSTR(c.<day_key>, 5, 2), '-', SUBSTR(c.<day_key>, 7, 2)) AS Day
FROM <database>.Costs c
```

```sql
SELECT b.Job,
       b.Budget,
       b.Region,
       b.Budget / 100 AS Dollars
FROM <database>.Budgets b
```

## X26

Sources: run_alerts (typed alert_id, run_id, severity) and job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: none.
Finals: run_alerts (alert_id, run_id, severity, job_id, status, avg_mins). It is a source and a final.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: XLOOKUP(run_id, job_runs[run_id], job_runs[job_id]) becomes a LEFT JOIN of job_runs on run_id, then job_id. VLOOKUP(run_id, job_runs, 3, FALSE) is exact, and column 3 is status, so it uses the same join. AVERAGEIFS over another Table becomes a LEFT JOIN of a grouped AVG by job_id, matched on the row's job_id. AVG gets no COALESCE. Blank: job_runs row 98 has a blank status, which the VLOOKUP reads, so status is wrapped as COALESCE(status, '').
Refused: none.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT a.alert_id,
       a.run_id,
       a.severity,
       jr.job_id,
       COALESCE(jr.status, '') AS status,
       avg_by_job.avg_mins
FROM <database>.run_alerts a
LEFT JOIN <database>.job_runs jr ON a.run_id = jr.run_id
LEFT JOIN (
  SELECT job_id, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) avg_by_job ON avg_by_job.job_id = jr.job_id
```

## X27

Sources: jobs (typed job_id, job_name, team, region).
Steps: none.
Finals: by_team (team, jobs_in_team, last_job_id, last_job_name). by_team's only typed column is team, which COUNTIFS and MAXIFS match on, so it is a summary: a GROUP BY of jobs. It is also a final, since nothing reads it.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: COUNTIFS becomes COUNT(*). MAXIFS becomes MAX. INDEX(job_name, MATCH(last_job_id, job_id, 0)) is exact, so it becomes a LEFT JOIN of jobs on last_job_id, then job_name.
Refused: none.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT g.team,
       g.jobs_in_team,
       g.last_job_id,
       j.job_name AS last_job_name
FROM (
  SELECT team,
         COUNT(*) AS jobs_in_team,
         MAX(job_id) AS last_job_id
  FROM <database>.jobs
  GROUP BY team
) g
LEFT JOIN <database>.jobs j ON g.last_job_id = j.job_id
```

## X28

Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt).
Steps: none.
Finals: jobs (job_id, job_name, ok_mins). It is a source and a final.
Parameters: blank. Keys: jobs, job_id.
Typed over a formula: ok_mins in row 4 (report_build, job_id 3) is 99. It converts on the Keys column job_id.
Marks: SUMIFS over another Table becomes a LEFT JOIN of a grouped SUM over job_runs where status = 'SUCCESS', with COALESCE(total, 0). The blank status in job_runs row 98 is not wrapped, because SUMIFS skips a blank, and NULL = 'SUCCESS' also does not match.
Refused: none.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT j.job_id,
       j.job_name,
       CASE WHEN j.job_id = 3 THEN 99
            ELSE COALESCE(ok.total, 0) END AS ok_mins
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
  GROUP BY job_id
) ok ON ok.job_id = j.job_id
```

## X29

Sources: region_budgets (typed job_id, budget_cents, region).
Steps: none.
Finals: region_budgets (job_id, budget_cents, region, in_dollars, pointer). It is a source and a final.
Parameters: cents_per_dollar is 100, so the XLOOKUP on Parameters gives 100 and becomes budget_cents / 100.
Keys: blank, so there is no Keys row for region_budgets.
Typed over a formula: in_dollars in row 4 (job 3, 350 cents, us) is 5. With no Keys row, the match is on every typed column of that row: job_id, budget_cents and region.
Marks: none for blanks, since the sample has none.
Refused: pointer, which is INDIRECT, so it is NULL AS pointer.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT r.job_id,
       r.budget_cents,
       r.region,
       CASE WHEN r.job_id = 3 AND r.budget_cents = 350 AND r.region = 'us' THEN 5
            ELSE r.budget_cents / 100 END AS in_dollars,
       NULL AS pointer
FROM <database>.region_budgets r
```

## X30

Sources: scheduler_runs (typed run_id, job_id, dt).
Steps: none.
Finals: scheduler_runs (run_id, job_id, dt, day, prev_run, jitter). It is a source and a final.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: RIGHT(dt, 2) becomes SUBSTR(dt, -2).
Refused: prev_run, which is OFFSET, so it is NULL AS prev_run. jitter, which is RANDBETWEEN, so it is NULL AS jitter.
Left alone: the bar chart on the Summary sheet, and the PivotTable on the Pivot sheet.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT s.run_id,
       s.job_id,
       s.dt,
       SUBSTR(s.dt, -2) AS day,
       NULL AS prev_run,
       NULL AS jitter
FROM <database>.scheduler_runs s
```

## X31

Sources: jobs (typed job_id, team).
Steps: none.
Finals: jobs (job_id, team, bump, tag, scaled, boosted). It is a source and a final.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: boost is a defined name for Summary!$B$2, a cell outside a Table, whose value is 10. boosted becomes job_id * 10, and the value should be moved into Parameters.
Refused:
- bump reads its own column, so it is circular: NULL AS bump.
- tag is TAG, a defined name holding a LAMBDA: NULL AS tag.
- scaled reads Summary!D4, a cell outside a Table that isn't a defined name: NULL AS scaled.
Left alone: the cells on the Summary sheet (B2 and D4), which are outside a Table.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT j.job_id,
       j.team,
       NULL AS bump,
       NULL AS tag,
       NULL AS scaled,
       j.job_id * 10 AS boosted
FROM <database>.jobs j
```

## X32

Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (typed job_id, job_name, team, region).
Steps: job_runs, with its job_name column, is read by by_name. It becomes the CTE job_runs_named.
Finals: by_name (job_name, runs). by_name's only typed column is job_name, which COUNTIFS matches on, so it is a summary: a GROUP BY of job_runs. It is also a final, since nothing reads it.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: VLOOKUP(job_id, jobs, 2, TRUE) is approximate. It is converted as an exact LEFT JOIN of jobs on job_id, then job_name, and that conversion is approximate in the source. COUNTIFS becomes COUNT(*).
Refused: none.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
WITH job_runs_named AS (
  SELECT r.run_id,
         r.job_id,
         j.job_name
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT n.job_name,
       COUNT(*) AS runs
FROM job_runs_named n
GROUP BY n.job_name
```

## X33

Sources: none in the workbook. The Power Query reads job_runs from Sql.Database("dwh01", "ops"), which I write as `<database>.job_runs`.
Steps: none.
Finals: slow_runs (run_id, duration_mins, over_by). The Table is loaded by its Power Query and nothing reads it.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: the Sql.Database source is replaced by the table it names, job_runs, as `<database>.job_runs`. Check that `<database>` is the database dwh01 holds in its ops schema, and that job_runs is the table to read. In M, <> keeps a null, so it becomes (status <> 'TEST' OR status IS NULL). AddColumn becomes an AS expression, and SelectColumns becomes the SELECT list.
Refused: none.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT r.run_id,
       r.duration_mins,
       r.duration_mins - 20 AS over_by
FROM <database>.job_runs r
WHERE r.duration_mins >= 20
  AND (r.status <> 'TEST' OR r.status IS NULL)
```

## X34

Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (typed job_id, job_name, team, region).
Steps: runs_with_team is a connection-only query that team_totals reads, so it is a CTE. Its NestedJoin with JoinKind.LeftOuter and ExpandTableColumn is a LEFT JOIN of jobs for team.
Finals: team_totals (team, total_mins, longest). Nothing reads it.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: Table.Group becomes GROUP BY team, with List.Sum as SUM and List.Max as MAX.
Refused: none.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
WITH runs_with_team AS (
  SELECT r.run_id,
         r.job_id,
         r.status,
         r.duration_mins,
         r.avg_retry_secs,
         r.dt,
         j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT t.team,
       SUM(t.duration_mins) AS total_mins,
       MAX(t.duration_mins) AS longest
FROM runs_with_team t
GROUP BY t.team
```

## X35

Sources: job_runs (typed run_id, dt, among others) and scheduler_runs (typed run_id, job_id, dt).
Steps: none.
Finals: recent (run_id, dt). It is loaded by its Power Query and nothing reads it.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: Table.Combine becomes UNION ALL. Table.Sort by run_id descending becomes ORDER BY run_id DESC, and Table.FirstN(4) becomes LIMIT 4.
Refused: none.
Left alone: none.
Left out: the connection-only query "rates" reads Web.Contents from an online address, so it is left out.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT p.run_id,
       p.dt
FROM (
  SELECT run_id, dt FROM <database>.job_runs
  UNION ALL
  SELECT run_id, dt FROM <database>.scheduler_runs
) p
ORDER BY p.run_id DESC
LIMIT 4
```

## X36

Sources: run_alerts (typed alert_id, run_id, severity, dt) and job_runs (typed run_id, status).
Steps: none.
Finals: job_runs (run_id, status, alerts) and severity_by_day (dt, high, low). job_runs is a source and a final.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: COUNTIFS over another Table becomes a LEFT JOIN of a grouped COUNT(*) over run_alerts, with COALESCE(n, 0). Table.Pivot becomes one SUM(CASE WHEN severity = ... THEN 1 END) column per value in the sample, which is high and low. NULL is left where there is no match, as M leaves it. The pivot's columns are now fixed to high and low.
Refused: none.
Left alone: none.
Left out: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT r.run_id,
       r.status,
       COALESCE(a.n, 0) AS alerts
FROM <database>.job_runs r
LEFT JOIN (
  SELECT run_id, COUNT(*) AS n
  FROM <database>.run_alerts
  GROUP BY run_id
) a ON a.run_id = r.run_id
```

```sql
SELECT a.dt,
       SUM(CASE WHEN a.severity = 'high' THEN 1 END) AS high,
       SUM(CASE WHEN a.severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts a
GROUP BY a.dt
```

## X37

Sources: Owners (typed Job No, Team Name, Owner, Day).
Steps: none.
Finals: Owners (Job No, Team Name, Owner, Day, Is Ana). It is a source and a final.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: blank. Owner is blank on the web rows, and Is Ana reads it, so it is wrapped as COALESCE(Owner, ''). IF(Owner = "ana", 1, 0) becomes IF(... = 'ana', 1, 0).
Refused: none.
Left alone: none.
Fill in: `<database>`, `<job_no>` (the header Job No), `<team_name>` (the header Team Name), `<is_ana>` (the header Is Ana).

Toolbox step: take out what you don't want converted, fill in the placeholders, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT o.<job_no>,
       o.<team_name>,
       o.Owner,
       o.Day,
       IF(COALESCE(o.Owner, '') = 'ana', 1, 0) AS <is_ana>
FROM <database>.Owners o
```

## X38

Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs) and jobs (typed job_id, job_name, team, region).
Steps: job_runs joined to jobs for region, as the CTE runs_with_region. region_mins needs this region column, so it has to come first.
Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, region, region_mins, retry_cost). It is a source and a final.
Parameters: blank. Keys: job_runs, run_id.
Typed over a formula: retry_cost in row 8 (run 102) is 1. It converts on the Keys column run_id.
Marks: XLOOKUP(job_id, jobs[job_id], jobs[region]) becomes a LEFT JOIN of jobs, then region. SUMIFS over its own Table becomes SUM(duration_mins) OVER (PARTITION BY region). Blank: avg_retry_secs in run 98 is blank and read by retry_cost, so it is wrapped as COALESCE(avg_retry_secs, 0). The blank status is not read by a formula, so it is left NULL.
Refused: none.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
WITH runs_with_region AS (
  SELECT r.run_id,
         r.job_id,
         r.status,
         r.duration_mins,
         r.avg_retry_secs,
         j.region
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT run_id,
       job_id,
       status,
       duration_mins,
       avg_retry_secs,
       region,
       SUM(duration_mins) OVER (PARTITION BY region) AS region_mins,
       CASE WHEN run_id = 102 THEN 1
            ELSE (COALESCE(avg_retry_secs, 0) + duration_mins) * 2 END AS retry_cost
FROM runs_with_region
```

## X39

Sources: job_runs (typed run_id, job_id, status, duration_mins, avg_retry_secs, dt) and jobs (typed job_id, job_name, team, region).
Steps: none.
Finals: ok_runs (run_id, job_id, duration_mins, job_name, share, noise). It is loaded by its Power Query and nothing reads it.
Parameters and Keys: blank, so neither is used.
Typed over a formula: none.
Marks: the Power Query's SelectRows where status = 'SUCCESS' becomes its WHERE, and SelectColumns becomes the SELECT list. XLOOKUP becomes a LEFT JOIN of jobs, then job_name. SUMIFS over its own Table becomes SUM(duration_mins) OVER (PARTITION BY job_id).
Refused: noise, which is RAND(), so it is NULL AS noise.
Left alone: none.
Fill in: `<database>`.

Toolbox step: take out what you don't want converted, fill in `<database>`, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
SELECT o.run_id,
       o.job_id,
       o.duration_mins,
       j.job_name,
       o.duration_mins / SUM(o.duration_mins) OVER (PARTITION BY o.job_id) AS share,
       NULL AS noise
FROM (
  SELECT run_id, job_id, duration_mins
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
) o
LEFT JOIN <database>.jobs j ON o.job_id = j.job_id
```

## X40

Sources: Runs (typed Run, Job, Mins), jobs (typed job_id, job_name, team, region) and run_alerts (typed alert_id, run_id, severity, dt).
Steps: Runs with its Team and Cost columns is read by Teams, so it is the CTE runs_costed.
Finals: Teams (Team, Total Cost), which is a summary: its only typed column is Team, which SUMIFS matches on, so it is a GROUP BY of Runs. run_alerts (alert_id, run_id, severity, dt, Run Mins), which is a source and a final.
Parameters: rate is 2, so XLOOKUP("rate", ...) gives 2 and Cost becomes Mins * 2.
Keys: blank, so neither is used.
Typed over a formula: none.
Marks: XLOOKUP(Job, jobs[job_id], jobs[team]) becomes a LEFT JOIN of jobs, then team. XLOOKUP(run_id, Runs[Run], Runs[Mins]) becomes a LEFT JOIN of Runs on run_id.
Refused: none.
Left alone: the PivotTable on the Pivot sheet.
Fill in: `<database>`, `<total_cost>` (the header Total Cost), `<run_mins>` (the header Run Mins).

Toolbox step: take out what you don't want converted, fill in the placeholders, then run `project.convert` on this Hive. Its code is checked and wins where the two differ.

```sql
WITH runs_costed AS (
  SELECT r.Run,
         r.Job,
         r.Mins,
         j.team AS Team,
         r.Mins * 2 AS Cost
  FROM <database>.Runs r
  LEFT JOIN <database>.jobs j ON r.Job = j.job_id
)
SELECT c.Team,
       SUM(c.Cost) AS <total_cost>
FROM runs_costed c
GROUP BY c.Team
```

```sql
SELECT a.alert_id,
       a.run_id,
       a.severity,
       a.dt,
       r.Mins AS <run_mins>
FROM <database>.run_alerts a
LEFT JOIN <database>.Runs r ON a.run_id = r.Run
```
