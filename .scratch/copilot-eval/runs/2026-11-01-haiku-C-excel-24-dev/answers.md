date: 2026-11-01
arm: C
model: haiku
files: 24-dev

## X01

**Map**
- Sources: `<database>.job_runs`, read for its typed columns run_id, job_id, duration_mins, dt.
- Steps: none.
- Finals: job_runs (run_id, job_id, duration_mins, dt, duration_hours). Its Table has a formula column, no query loads it, and nothing else reads it, so it is a final.
- Values written in: none. Parameters is empty and no formula reads it.
- Values typed over a formula: none. Keys is empty.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables, never a source, step or final.
- To fill in: `<database>` in the FROM line.

### Hive

```sql
SELECT run_id, job_id, duration_mins, dt,
  duration_mins / 60 AS duration_hours
FROM <database>.job_runs
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X02

**Map**
- Sources: `<database>.job_runs`, read for its typed columns run_id, job_id, status, duration_mins.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, slow_job1, flag). Its Table has formula columns, no query loads it, and nothing else reads it, so it is a final.
- Values written in: none. Parameters is empty and no formula reads it.
- Values typed over a formula: none. Keys is empty.
- Marks: none. The blank status on row 98 is read by no formula, so it is no mark.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables, never a source, step or final.
- To fill in: `<database>` in the FROM line.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins,
  (duration_mins > 10 AND job_id = 1) AS slow_job1,
  IF((duration_mins > 25 OR job_id = 3), 'check', 'ok') AS flag
FROM <database>.job_runs
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X03

**Map**
- Sources: `<database>.job_runs`, read for its typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt.
- Steps: none.
- Finals: job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, score, mins_per_retry, total_secs). Its Table has formula columns, no query loads it, and nothing else reads it, so it is a final.
- Values written in: none. Parameters is empty and no formula reads it.
- Values typed over a formula: none. Keys is empty.
- Marks:
  - blank: status is blank on row 98 (run_id 98), and score reads status, so score is written as CASE COALESCE(status, '') WHEN 'SUCCESS' ....
  - blank: avg_retry_secs is blank on row 98, and mins_per_retry and total_secs read it, so each is written with COALESCE(avg_retry_secs, 0). A divide by 0 is NULL in Hive, and COALESCE turns it into 0 as IFERROR does.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables, never a source, step or final.
- To fill in: `<database>` in the FROM line.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
  CASE COALESCE(status, '') WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS score,
  COALESCE(duration_mins / COALESCE(avg_retry_secs, 0), 0) AS mins_per_retry,
  duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM <database>.job_runs
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X04

**Map**
- Sources: `<database>.jobs`, read for its typed columns job_id, job_name, team, region.
- Steps: none.
- Finals: jobs (job_id, job_name, team, region, code, name_length, third, odd). Its Table has formula columns, no query loads it, and nothing else reads it, so it is a final.
- Values written in: none. Parameters is empty and no formula reads it.
- Values typed over a formula: none. Keys is empty.
- Marks: none.
- Refusals: none.
- Left alone: Parameters and Keys, both empty settings Tables, never a source, step or final.
- To fill in: `<database>` in the FROM line.

### Hive

```sql
SELECT job_id, job_name, team, region,
  CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-', region) AS code,
  LENGTH(job_name) AS name_length,
  ROUND(job_id / 3, 2) AS third,
  PMOD(job_id, 2) AS odd
FROM <database>.jobs
```

**Next**
Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X06

### Map

- **Sources:** jobs (job_id, job_name, team, region), its typed columns, read from `<database>.jobs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, duration_mins, job_name, runs_of_job). Its formula columns are job_name, an XLOOKUP into jobs, and runs_of_job, a COUNTIFS over its own job_id. Nothing else reads job_runs, so it is a final. It has no Total Row.
- **Settings, never a source, step or final:** Parameters and Keys, both empty. No formula reads Parameters, and no value is typed over a formula, so Keys needs no row.
- **Values written in:** none.
- **Values typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the D1 notes on Parameters and Keys, and the Steps sheet, as cells outside a Table.
- **To fill in:** `<database>`, in the reads of job_runs and of jobs.

### Hive

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  j.job_name AS job_name,
  COALESCE(COUNT(*) OVER (PARTITION BY r.job_id), 0) AS runs_of_job
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X07

### Map

- **Sources:** jobs (job_id, job_name, team, region), its typed columns, read from `<database>.jobs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, status, team, region). Its formula columns are team, a VLOOKUP into jobs at column 3, and region, an INDEX and MATCH on jobs. Both read jobs, and nothing reads job_runs, so it is a final. It has no Total Row.
- **Settings, never a source, step or final:** Parameters and Keys, both empty.
- **Values written in:** none.
- **Values typed over a formula:** none.
- **Marks:** none. The VLOOKUP and MATCH are exact (FALSE and 0). The blank status at run 98 is read by no formula, so it gets no COALESCE.
- **Refusals:** none.
- **Left alone:** the D1 notes on Parameters and Keys, and the Steps sheet, as cells outside a Table.
- **To fill in:** `<database>`, in the reads of job_runs and of jobs.

### Hive

```sql
SELECT r.run_id, r.job_id, r.status,
  j.team AS team,
  j.region AS region
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X08

### Map

- **Sources:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt), its typed columns, read from `<database>.job_runs`. Only by_job's formulas read it.
- **Steps:** none.
- **Finals:** by_job (job_id, total_mins, avg_retry, longest). Its only typed column, job_id, is the one its SUMIFS, AVERAGEIFS and MAXIFS match on, so it is a summary: its final is a GROUP BY of job_runs, with its typed job_ids kept as groups. Nothing else reads it, so it is a final. It has no Total Row.
- **Settings, never a source, step or final:** Parameters and Keys, both empty.
- **Values written in:** the summary's groups, job_id 1, 2 and 3, typed in. A job_id added to job_runs later won't be in this table.
- **Values typed over a formula:** none.
- **Marks:** avg_retry is AVG, left NULL where no run matches, as Excel shows #DIV/0! there and Hive shows NULL. The blank avg_retry_secs at run 98 is skipped by AVG, as AVERAGEIFS skips it in Excel, so it gets no COALESCE.
- **Refusals:** none.
- **Left alone:** the D1 notes on Parameters and Keys, and the Steps sheet, as cells outside a Table.
- **To fill in:** `<database>`, in the reads of job_runs.

### Hive

```sql
SELECT j.job_id,
  COALESCE(g.total_mins, 0) AS total_mins,
  g.avg_retry AS avg_retry,
  COALESCE(g.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id,
    SUM(duration_mins) AS total_mins,
    AVG(avg_retry_secs) AS avg_retry,
    MAX(duration_mins) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
) g ON j.job_id = g.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X09

### Map

- **Sources:** jobs (job_id, job_name, team, region), its typed columns, read from `<database>.jobs`.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, duration_mins, avg_retry_secs, team, team_mins, cost). Its formula columns read jobs (team), its own team column (team_mins, a SUMIFS over its own Table), and Parameters (cost). Nothing else reads job_runs, and it has more typed columns than the ones a SUMIFS matches on, so it is a final, not a summary. It has no Total Row.
- **Settings, never a source, step or final:** Parameters (rate, 0.5) and Keys (job_runs, run_id).
- **Values written in:** rate, 0.5, from Parameters, written into cost's Hive as 0.5. Change it in Parameters and the table won't follow, so the Hive needs the new value too.
- **Values typed over a formula:** cost at run_id 97 holds 100 in place of its formula. It is matched on run_id, the column the Keys row names for job_runs, in a CASE.
- **Marks:**
  - blank: avg_retry_secs is blank at run 98, and cost reads it, so cost reads COALESCE(avg_retry_secs, 0) there.
- **Refusals:** none.
- **Left alone:** the D1 notes on Parameters and Keys, and the Steps sheet, as cells outside a Table.
- **To fill in:** `<database>`, in the reads of job_runs and of jobs.

### Hive

```sql
SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs,
  j.team AS team,
  COALESCE(SUM(r.duration_mins) OVER (PARTITION BY j.team), 0) AS team_mins,
  CASE WHEN r.run_id = 97 THEN 100
    ELSE (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * 0.5
  END AS cost
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X11

### Map

- **Sources:** `<database>.job_runs`, read for its typed columns run_id and duration_mins.
- **Steps:** none.
- **Finals:** job_runs (run_id, duration_mins, pick, scaled). Its formula columns pick and scaled are refused, so each is `NULL AS` its header.
- **Values written in:** none.
- **Values typed over a formula:** none. Keys is empty, so no Keys row is needed.
- **Marks:** none.
- **Refusals:**
  - pick: `=INDIRECT("B"&ROW())`. INDIRECT and ROW() hang on the sheet's rows, so `NULL AS pick`.
  - scaled: `=job_runs[[#This Row],[duration_mins]]*Summary!$C$2` reads Summary!C2, a cell outside a Table that isn't a defined name, so `NULL AS scaled`.
- **Left alone:** Parameters and Keys (settings Tables, never a source, step or final); cell C2 on Summary and the bar chart on Summary (a cell outside a Table, and a chart).
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, duration_mins, NULL AS pick, NULL AS scaled
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X12

### Map

- **Sources:** `<database>.job_runs`, read for its typed columns run_id and duration_mins.
- **Steps:** none.
- **Finals:** job_runs (run_id, duration_mins, running, loop, with_tax). running and loop are refused, so each is `NULL AS` its header.
- **Values written in:** tax_rate = 0.2, the defined name tax_rate on Summary!B3, written into with_tax as `duration_mins * 0.2`. Move tax_rate into Parameters: a change made there won't reach the Hive, so the Hive needs the new value too.
- **Values typed over a formula:** none. Keys is empty, so no Keys row is needed.
- **Marks:** none.
- **Refusals:**
  - running: `=SUM(OFFSET(...,ROW()-1,1))`. OFFSET and ROW() hang on the sheet's rows, so `NULL AS running`.
  - loop: `=job_runs[[#This Row],[loop]]+1` reads its own column (circular), so `NULL AS loop`.
- **Left alone:** Parameters and Keys (settings Tables, never a source, step or final); the rest of Summary apart from B3.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, duration_mins,
  NULL AS running,
  NULL AS loop,
  duration_mins * 0.2 AS with_tax
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X13

### Map

- **Sources:** `<database>.job_runs`, read for its typed columns run_id and job_id; `<database>.jobs`, read for its typed columns job_id and job_name. jobs has only typed columns and no query loads it, so it is a source, never a final.
- **Steps:** none.
- **Finals:** job_runs (run_id, job_id, name, doubled). Nothing reads job_runs, so it is a final.
- **Values written in:** none.
- **Values typed over a formula:** none. Keys is empty, so no Keys row is needed.
- **Marks:**
  - name: `=VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)` is approximate (TRUE). It is written as the exact match on job_id, a LEFT JOIN to jobs, column 2 being job_name.
- **Refusals:**
  - doubled: `=DOUBLE(job_runs[[#This Row],[job_id]])`. DOUBLE is a defined name holding a LAMBDA, so `NULL AS doubled`.
- **Left alone:** Parameters and Keys (settings Tables, never a source, step or final).
- **To fill in:** `<database>`.

### Hive

```sql
SELECT r.run_id, r.job_id, j.job_name AS name, NULL AS doubled
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X14

### Map

- **Sources:** `<database>.job_runs`, read for its typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt, by the step job_runs.
- **Steps:** job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt, hours). by_job's formula reads job_runs, so it is a step: a CTE in by_job's block. hours is `duration_mins / 60`.
- **Finals:** by_job (job_id, total_hours), a summary. Its only typed column, job_id, is the one its SUMIFS matches on, so its query is a GROUP BY of job_runs with its typed rows kept.
- **Values written in:** by_job's groups, job_ids 1, 2 and 3, are typed into the Hive. A later job_id won't be in by_job's table: add it to the query when a new group appears.
- **Values typed over a formula:** none. Keys is empty, so no Keys row is needed.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Parameters and Keys (settings Tables, never a source, step or final); the PivotTable on sheet "Pivot" from job_runs (rows job_id, Sum of duration_mins).
- **To fill in:** `<database>`.

### Hive

```sql
WITH job_runs AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt,
    duration_mins / 60 AS hours
  FROM <database>.job_runs
)
SELECT j.job_id, COALESCE(c.total_hours, 0) AS total_hours
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, SUM(hours) AS total_hours FROM job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X16

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), its typed columns, read from `<database>.job_runs`.
- **Steps:** none. No query names another query, so no CTE is needed.
- **Finals:** `long_runs` (run_id, job_id, minutes, hours). The Table `long_runs` is loaded by Power Query `long_runs`, and no formula reads that Table, so it is a final whose rows are the query's. The query and the Table are two things: the query's M is written out as the final's block below.
- **Settings, never a source, step or final:** `Parameters` and `Keys`. Both are empty, so no value is read in, no value is typed over a formula, and no Keys row is needed.
- **Values written in:** none.
- **Values typed over a formula:** none; the workbook has no formula.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table. No charts or PivotTables.
- **To fill in:** `<database>`, in the FROM of `long_runs`.

### Hive

```sql
SELECT run_id, job_id, duration_mins AS minutes, duration_mins / 60 AS hours
FROM <database>.job_runs
WHERE duration_mins > 15
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X17

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt), its typed columns, read from `<database>.job_runs`.
- **Steps:** `ok_runs` (Power Query, connection only). Power Query `ok_by_job` names it in `Source = ok_runs`, so it is a step: a CTE `WITH ok_runs AS (...)` in the final that reads it. It keeps every column of job_runs, since its M only filters rows.
- **Finals:** `ok_by_job` (job_id, runs, total_mins). The Table `ok_by_job` is loaded by Power Query `ok_by_job`, and no formula reads that Table, so it is a final whose rows are the query's.
- **Settings, never a source, step or final:** `Parameters` and `Keys`. Both are empty: no value is read in, no value is typed over a formula, and no Keys row is needed.
- **Values written in:** none.
- **Values typed over a formula:** none; the workbook has no formula.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table. No charts or PivotTables.
- **To fill in:** `<database>`, in the FROM of `ok_runs`.

### Hive

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X18

### Map

- **Sources:** `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and `jobs` (job_id, job_name, team, region), each its typed columns, read from `<database>.job_runs` and `<database>.jobs`.
- **Steps:** none. No query names another query, so no CTE is needed.
- **Finals:** `top_runs` (run_id, job_name, duration_mins). The Table `top_runs` is loaded by Power Query `top_runs`, and no formula reads that Table, so it is a final whose rows are the query's.
- **Settings, never a source, step or final:** `Parameters` and `Keys`. Both are empty, so no value is read in, no value is typed over a formula, and no Keys row is needed.
- **Values written in:** none.
- **Values typed over a formula:** none; the workbook has no formula.
- **Marks:** Table.Sort then FirstN becomes ORDER BY duration_mins DESC with LIMIT 3. Rows 97 and 103 tie at 30. Both are inside the top three, so the three rows are the same, but Excel keeps their sheet order where Hive may give either order.
- **Refusals:** none.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table. No charts or PivotTables.
- **To fill in:** `<database>`, in the FROM and JOIN of `top_runs`.

### Hive

```sql
SELECT r.run_id, j.job_name, r.duration_mins
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC
LIMIT 3
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X19

### Map

- **Sources:** `scheduler_runs` (run_id, job_id, dt), its typed columns, read from `<database>.scheduler_runs`. And `job_runs` (run_id, job_id, dt, the three columns the query keeps), read from the warehouse table the query names, `Sql.Database("dwh01", "ops")`, schema ops, table job_runs; read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:** `all_runs` (run_id, job_id, dt). The Table `all_runs` is loaded by Power Query `all_runs`, and no formula reads that Table, so it is a final whose rows are the query's: scheduler_runs stacked on job_runs with UNION ALL, duplicates kept.
- **Settings, never a source, step or final:** `Parameters` and `Keys`. Both are empty, so no value is read in, no value is typed over a formula, and no Keys row is needed.
- **Values written in:** none.
- **Values typed over a formula:** none; the workbook has no formula.
- **Marks:** `job_runs` is a source outside the workbook, read by Sql.Database("dwh01", "ops"). It is read as `<database>.job_runs`, for you to check that it is the same table as dwh01's ops.job_runs.
- **Refusals:** Power Query `holidays` reads Web.Contents from calendar.example.com, a web source, so it is refused and left out. It loads nothing and nothing reads it, so it has no place in a final.
- **Left alone:** the Steps sheet and the notes in D1 of Parameters and Keys, as cells outside a Table. No charts or PivotTables.
- **To fill in:** `<database>`, in both FROM clauses of `all_runs`.

### Hive

```sql
SELECT run_id, job_id, dt FROM <database>.scheduler_runs
UNION ALL
SELECT run_id, job_id, dt FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X41

### Map

- **Sources:** job_runs, its typed columns: run_id, job_id, status, duration_mins.
- **Steps:** none. No Table or query is read as a step by another piece.
- **Finals:** Table job_runs (run_id, job_id, status, duration_mins, longest_first, shortest_ok, job_total). It has formula columns and no query loads it. Its own formulas read its own columns, which don't count, and no other Table reads it, so it is a final.
- **Values written in:** none. Parameters is empty, so no formula uses a fixed value.
- **Values typed over a formula:** none. Every row holds the same formulas, and Keys is empty, so no Keys row is needed.
- **Marks:** none. The blank status in row 5 is read only inside MINIFS's condition, so it is written as it is.
- **Refusals:** none.
- **Left alone:** Excel Table Parameters and Excel Table Keys, both empty, so never a source, step or final. The Steps sheet and the D1 notes on each sheet, which are cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins,
  RANK() OVER (ORDER BY duration_mins DESC) AS longest_first,
  COALESCE(MIN(CASE WHEN status = 'SUCCESS' THEN duration_mins END) OVER (PARTITION BY job_id), 0) AS shortest_ok,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id), 0) AS job_total
FROM <database>.job_runs
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X42

### Map

- **Sources:** job_runs, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. It is typed only and no query loads it, so it is a source, never a final. Also jobs, its typed columns: job_id, job_name.
- **Steps:** none.
- **Finals:** Table jobs (job_id, job_name, runs, avg_mins, id_order). It has formula columns, no query loads it, and no other Table's formula reads it, so it is a final. It is not a summary, because job_name is typed and no COUNTIF or AVERAGEIF matches it.
- **Values written in:** none. Parameters is empty.
- **Values typed over a formula:** none. Keys is empty, and every row holds the same formulas.
- **Marks:** none. runs and avg_mins read job_runs through a grouped LEFT JOIN. The `_xlfn.` prefix on id_order is read past. The blanks in status and avg_retry_secs are not read by any formula.
- **Refusals:** none.
- **Left alone:** Excel Table Parameters and Excel Table Keys, both empty. The Steps sheet and the D1 notes on each sheet, which are cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT j.job_id, j.job_name,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.avg_mins, 0) AS avg_mins,
  RANK() OVER (ORDER BY j.job_id ASC) AS id_order
FROM <database>.jobs j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS runs, AVG(duration_mins) AS avg_mins
  FROM <database>.job_runs
  GROUP BY job_id
) c ON j.job_id = c.job_id
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X43

### Map

- **Sources:** job_runs, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Also jobs, its typed columns: job_id, job_name, team, region. Both have no formulas and are read by queries that don't load them.
- **Steps:** none. Neither Power Query's name is named in another query's M.
- **Finals:**
  - Table busy_teams (team, runs, shortest, avg_mins), its rows the rows of Power Query busy_teams. No other Table's formula reads it, so it is a final.
  - Table statuses (job_id, status), its rows the rows of Power Query statuses. It is a final for the same reason.
- **Values written in:** none. The rows of busy_teams and statuses come from their queries, not typed in.
- **Values typed over a formula:** none. Neither Table has a formula, and Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Excel Table Parameters and Excel Table Keys, both empty. The Steps sheet and the D1 notes on each sheet, which are cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT j.team, COUNT(*) AS runs, MIN(r.duration_mins) AS shortest, AVG(r.duration_mins) AS avg_mins
FROM <database>.job_runs r
JOIN <database>.jobs j ON r.job_id = j.job_id
GROUP BY j.team
HAVING COUNT(*) > 4
```

```sql
SELECT DISTINCT job_id, status
FROM <database>.job_runs
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X44

### Map

- **Sources:** job_runs, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Also jobs, its typed columns: job_id, job_name, team, region. Also scheduler_runs, its typed columns: run_id, job_id, dt. All three have no formulas and are read by queries that don't load them.
- **Steps:** none. Neither Power Query's name is named in another query's M, and each reads sources only.
- **Finals:**
  - Table jobs_with_runs (run_id, job_name), its rows the rows of Power Query jobs_with_runs. No other Table's formula reads it, so it is a final.
  - Table never_scheduled (job_id, job_name, team), its rows the rows of Power Query never_scheduled. It is a final for the same reason.
- **Values written in:** none. The rows of both finals come from their queries, not typed in.
- **Values typed over a formula:** none. Neither Table has a formula, and Keys is empty.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** Excel Table Parameters and Excel Table Keys, both empty. The Steps sheet and the D1 notes on each sheet, which are cells outside a Table.
- **To fill in:** `<database>`.

### Hive

```sql
SELECT r.run_id, j.job_name
FROM <database>.jobs j
LEFT JOIN <database>.job_runs r ON j.job_id = r.job_id
```

```sql
SELECT j.job_id, j.job_name, j.team
FROM <database>.jobs j
LEFT JOIN <database>.scheduler_runs s ON j.job_id = s.job_id
WHERE s.job_id IS NULL
```

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X51

### Map

- **Sources:** job_runs, its typed columns (run_id, job_id, status, duration_mins, dt), read as `<database>.job_runs`.
- **Steps:** none. No query loads a Table, and no other Table's formula reads one.
- **Finals:** job_runs, with the columns run_id, job_id, status, duration_mins, dt, long_in_job, not_ok, failed_in_job, running_mins. It is a final: it has formula columns, no query loads it, and nothing else reads it. It is not a summary, since run_id is typed and no COUNTIFS or SUMIFS matches on it.
- **Settings, never a source, step or final:** Parameters (empty, and no formula reads it) and Keys (empty, with no value typed over a formula, so no row is needed).
- **Written in:** none.
- **Typed over a formula:** none.
- **Marks:** none. The blank status in row 98 needs no mark: not_ok's `<>` condition counts it, as Excel does.
- **Refusals:** none.
- **Left alone:** the Steps sheet, as cells outside a Table.
- **To fill in:** `<database>` in the FROM of the job_runs block.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins, dt,
  COALESCE(COUNT(CASE WHEN duration_mins > 15 THEN 1 END) OVER (PARTITION BY job_id), 0) AS long_in_job,
  COALESCE(COUNT(CASE WHEN (status <> 'SUCCESS' OR status IS NULL) THEN 1 END) OVER (), 0) AS not_ok,
  COALESCE(COUNT(CASE WHEN LOWER(status) LIKE '%ail%' THEN 1 END) OVER (PARTITION BY job_id), 0) AS failed_in_job,
  COALESCE(SUM(duration_mins) OVER (PARTITION BY job_id ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X52

### Map

- **Sources:** job_runs, its typed columns (run_id, job_id, duration_mins), read as `<database>.job_runs`.
- **Steps:** none.
- **Finals:**
  - job_runs, with the columns run_id, job_id, duration_mins, share, vs_avg, rank_in_job. It is a final: it has formula columns, no query loads it, and nothing else reads it. It is not a summary, since run_id is typed and no COUNTIFS or SUMIFS matches on it.
  - job_runs (Total Row), with the columns duration_mins and share. Those are the two Total Row cells that hold a SUBTOTAL(109) total. The "Total" label and the blank cells get no column.
- **Settings, never a source, step or final:** Parameters (empty, and no formula reads it) and Keys (empty, with no value typed over a formula, so no row is needed).
- **Written in:** none.
- **Typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet, as cells outside a Table.
- **To fill in:** `<database>` in the job_runs block and in the Total Row block.

### Hive

```sql
SELECT run_id, job_id, duration_mins,
  duration_mins / SUM(duration_mins) OVER () AS share,
  duration_mins - AVG(duration_mins) OVER () AS vs_avg,
  RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
FROM <database>.job_runs
```

```sql
WITH job_runs AS (
  SELECT run_id, job_id, duration_mins,
    duration_mins / SUM(duration_mins) OVER () AS share,
    duration_mins - AVG(duration_mins) OVER () AS vs_avg,
    RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) AS rank_in_job
  FROM <database>.job_runs
)
SELECT SUM(duration_mins) AS duration_mins, SUM(share) AS share
FROM job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X53

### Map

- **Sources:** job_runs, its typed columns (run_id, job_id, status, duration_mins, avg_retry_secs, dt), read as `<database>.job_runs`. No formula reads status or avg_retry_secs, so their blanks need no mark.
- **Steps:** none.
- **Finals:**
  - by_job, with the columns job_id, total_mins, runs, longest. It is a summary: its only typed column, job_id, is the one its SUMIFS, COUNTIFS and MAXIFS match on. Its final is a GROUP BY of job_runs, with its typed job_id groups kept. Nothing reads it, so it is a final.
  - by_job (Total Row), with the columns total_mins, runs and longest. Those are the three Total Row cells that hold a total: SUBTOTAL(109) on total_mins and runs, SUBTOTAL(104) on longest. The "Total" label and the blank job_id cell get no column.
- **Settings, never a source, step or final:** Parameters (empty, and no formula reads it) and Keys (empty, with no value typed over a formula, so no row is needed).
- **Written in:** by_job's groups, its typed job_id values 1, 2 and 3. They are typed into the Hive, so a job_id added to job_runs later won't be in this table until the groups are updated.
- **Typed over a formula:** none.
- **Marks:** none.
- **Refusals:** none. `_xlfn.` is read past.
- **Left alone:** the Steps sheet, as cells outside a Table.
- **To fill in:** `<database>` in the by_job block and in the by_job (Total Row) block.

### Hive

```sql
SELECT j.job_id,
  COALESCE(c.total_mins, 0) AS total_mins,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.longest, 0) AS longest
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS total_mins, COUNT(*) AS runs, MAX(duration_mins) AS longest
  FROM <database>.job_runs
  GROUP BY job_id
) c
  ON j.job_id = c.job_id
```

```sql
WITH by_job AS (
  SELECT j.job_id,
    COALESCE(c.total_mins, 0) AS total_mins,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(c.longest, 0) AS longest
  FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
  LEFT JOIN (
    SELECT job_id, SUM(duration_mins) AS total_mins, COUNT(*) AS runs, MAX(duration_mins) AS longest
    FROM <database>.job_runs
    GROUP BY job_id
  ) c
    ON j.job_id = c.job_id
)
SELECT SUM(total_mins) AS total_mins, SUM(runs) AS runs, MAX(longest) AS longest
FROM by_job
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X54

### Map

- **Sources:** job_runs, its typed columns (run_id, dt), read as `<database>.job_runs`. The dt values are dates, not dates held as text, so no mark.
- **Steps:** none.
- **Finals:** job_runs, with the columns run_id, dt, month_end, a_month_on, due, week_of, month_of, weekday, label. It is a final: it has formula columns, no query loads it, and nothing else reads it. It is not a summary, as no COUNTIFS or SUMIFS is in it.
- **Settings, never a source, step or final:** Parameters (empty, and no formula reads it) and Keys (empty, with no value typed over a formula, so no row is needed).
- **Written in:** none.
- **Typed over a formula:** none.
- **Marks:** a_month_on, EDATE as ADD_MONTHS, marked: a month's end stays one. Excel and Hive can differ at a month's end, so check that column.
- **Refusals:** none.
- **Left alone:** the Steps sheet, as cells outside a Table.
- **To fill in:** `<database>` in the FROM of the job_runs block.

### Hive

```sql
SELECT run_id, dt,
  LAST_DAY(dt) AS month_end,
  ADD_MONTHS(dt, 1) AS a_month_on,
  DATE_ADD(dt, 7) AS due,
  CAST(NEXT_DAY(DATE_ADD(dt, 7 * -1), 'MO') AS STRING) AS week_of,
  CAST(TRUNC(dt, 'MM') AS STRING) AS month_of,
  DAYOFWEEK(dt) AS weekday,
  DATE_FORMAT(dt, 'yyyy-MM') AS label
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X56

### Map

**Sources**
- scheduler_runs (run_id, job_id, dt): typed only, and no query loads it. Read as `<database>.scheduler_runs`, never as a CTE.

**Steps**
- None.

**Finals**
- job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, no_status, weeks, at_least_20, spread, weighted, scheduled_on). Its typed columns are read from `<database>.job_runs`. Nothing else reads it, so it is a final.

**Left out**
- Parameters and Keys are settings, empty, and never a source, step or final. No Keys row is needed.

**Column notes**
- no_status: ISBLANK(status) is `status IS NULL`; status is written as it is.
- weeks: INT is FLOOR.
- at_least_20: MAX of one row's cells is GREATEST.
- spread: STDEV.S over the whole column is STDDEV_SAMP over the whole column.
- weighted: SUMPRODUCT of two columns is `SUM(a * b) OVER ()`.
- scheduled_on: the XLOOKUP is a LEFT JOIN of scheduler_runs on run_id; its "unscheduled" fourth argument is COALESCE.

**Values written in**
- None. Parameters is empty, no formula reads a fixed value, and no defined name or summary is in the workbook.

**Values typed over a formula**
- None. No formula cell is typed over, so the Hive has no CASE.

**Marks**
- blank: weighted reads avg_retry_secs, which is blank in the sample on run 98. Written as `COALESCE(avg_retry_secs, 0)`, as Excel's SUMPRODUCT reads that blank as 0.
- first match: scheduled_on's XLOOKUP takes the first match, while the join gives every match. run_id is unique in the sample, so the two agree here. If run_id repeats in the database table, a job_runs row repeats too.

**Refusals**
- None.

**Left alone**
- The Steps sheet, and the notes in D1 of Parameters and Keys (cells outside a Table).

**To fill in**
- `<database>` in the two reads.

### Hive

#### job_runs

```sql
SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs,
  r.status IS NULL AS no_status,
  FLOOR(r.duration_mins / 7) AS weeks,
  GREATEST(r.duration_mins, 20) AS at_least_20,
  STDDEV_SAMP(r.duration_mins) OVER () AS spread,
  SUM(r.duration_mins * COALESCE(r.avg_retry_secs, 0)) OVER () AS weighted,
  COALESCE(s.dt, 'unscheduled') AS scheduled_on
FROM <database>.job_runs r
LEFT JOIN <database>.scheduler_runs s ON r.run_id = s.run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X57

### Map

**Sources**
- job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed only. Query picked reads it, and no query loads it. Read as `<database>.job_runs`.
- jobs (job_id, job_name, team, region): typed only. Query ran_jobs reads it. Read as `<database>.jobs`.

**Steps**
- None. Nothing reads picked or ran_jobs as a Table.

**Finals**
- picked (run_id, job_id, status, avg_retry_secs, status_lc): query picked loads it, and no formula reads it, so its rows are the query's.
- ran_jobs (job_id, job_name, team, region): query ran_jobs loads it, and no formula reads it, so its rows are the query's.

**Left out**
- Parameters and Keys are settings, empty, and never a source, step or final.

**Query notes**
- picked: SelectRows keeps job_id 1 or 2 with a blank status or a status starting with S. ReplaceValue sets a blank avg_retry_secs to 0. Text.Lower is LOWER, and SelectColumns is the SELECT list.
- ran_jobs: List.Contains(Runs[job_id], [job_id]) is a LEFT SEMI JOIN on job_runs. Text.Contains is `LIKE '%a%'`, case kept.

**Values written in**
- None.

**Values typed over a formula**
- None. The workbook has no formula columns.

**Marks**
- blank: avg_retry_secs is blank on run 98. The query writes it as `COALESCE(avg_retry_secs, 0)`, as M's ReplaceValue writes 0 there.

**Refusals**
- None.

**Left alone**
- The Steps sheet, and the notes in D1 of Parameters and Keys (cells outside a Table).

**To fill in**
- `<database>` in the two reads.

### Hive

#### picked

```sql
SELECT run_id, job_id, status, COALESCE(avg_retry_secs, 0) AS avg_retry_secs, LOWER(status) AS status_lc
FROM <database>.job_runs
WHERE job_id IN (1, 2) AND (status IS NULL OR status LIKE 'S%')
```

#### ran_jobs

```sql
SELECT j.job_id, j.job_name, j.team, j.region
FROM <database>.jobs j
LEFT SEMI JOIN <database>.job_runs r ON r.job_id = j.job_id
WHERE j.job_name LIKE '%a%'
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X58

### Map

**Sources**
- job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt): typed only. Read as `<database>.job_runs` by numbered, days_per_job, unrun and measures.
- jobs (job_id, job_name, team, region): typed only. Read as `<database>.jobs` by job_regions.
- scheduler_runs (run_id, job_id, dt): typed only. Read as `<database>.scheduler_runs` by unrun.
- region_budgets (job_id, budget_cents, region): typed only. Read as `<database>.region_budgets` by job_regions.

**Steps**
- None. No Table or query is read by another final.

**Finals**
- job_regions (job_id, region): query job_regions loads it. Its rows are jobs crossed with the distinct regions of region_budgets.
- numbered (run_id, dt, duration_mins, n): query numbered loads it.
- days_per_job (job_id, days): query days_per_job loads it.
- unrun (run_id, job_id): query unrun loads it.
- measures (run_id, measure, amount): query measures loads it.

No formula is in the workbook, so each loaded Table is a final with its query's rows.

**Left out**
- Parameters and Keys are settings, empty, and never a source, step or final.

**Query notes**
- job_regions: Table.AddColumn with each Regions, then expanded, is a CROSS JOIN. Table.Distinct alone is SELECT DISTINCT.
- numbered: Table.Sort then AddIndexColumn is a ROW_NUMBER ordered by duration_mins descending, then run_id ascending.
- days_per_job: Table.Group is GROUP BY job_id, and List.Count(List.Distinct([dt])) is COUNT(DISTINCT dt).
- unrun: the LeftAnti NestedJoin on run_id and job_id is a LEFT JOIN with `IS NULL`, and Table.Distinct is SELECT DISTINCT.
- measures: UnpivotOtherColumns of duration_mins and avg_retry_secs is two SELECTs stacked with UNION ALL, each with IS NOT NULL.

**Values written in**
- None.

**Values typed over a formula**
- None.

**Marks**
- Order dropped: days_per_job's sort by days, descending, has no FirstN or index after it, so the Hive has no ORDER BY. The order is dropped.
- blank: run 98's avg_retry_secs is blank in the sample, so measures has no avg_retry_secs row for 98, as M drops a null there.

**Refusals**
- None.

**Left alone**
- The Steps sheet, and the notes in D1 of Parameters and Keys (cells outside a Table).

**To fill in**
- `<database>` in each read.

### Hive

#### job_regions

```sql
SELECT j.job_id, r.region
FROM <database>.jobs j
CROSS JOIN (SELECT DISTINCT region FROM <database>.region_budgets) r
```

#### numbered

```sql
SELECT run_id, dt, duration_mins,
  ROW_NUMBER() OVER (ORDER BY duration_mins DESC, run_id ASC) AS n
FROM <database>.job_runs
```

#### days_per_job

```sql
SELECT job_id, COUNT(DISTINCT dt) AS days
FROM <database>.job_runs
GROUP BY job_id
```

#### unrun

```sql
SELECT DISTINCT s.run_id, s.job_id
FROM <database>.scheduler_runs s
LEFT JOIN <database>.job_runs r ON s.run_id = r.run_id AND s.job_id = r.job_id
WHERE r.run_id IS NULL
```

#### measures

```sql
SELECT run_id, 'duration_mins' AS measure, duration_mins AS amount
FROM <database>.job_runs
WHERE duration_mins IS NOT NULL
UNION ALL
SELECT run_id, 'avg_retry_secs' AS measure, avg_retry_secs AS amount
FROM <database>.job_runs
WHERE avg_retry_secs IS NOT NULL
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X67

### Map

**Sources**
- jobs (job_id, job_name, team, region): typed only. Read as `<database>.jobs` by job_runs' team.
- run_alerts (alert_id, run_id, severity, dt): typed only. Read as `<database>.run_alerts` by job_runs' alerts.

**Steps**
- job_runs (run_id, job_id, duration_mins, dt, team, alerts, running_mins): a Table with formula columns, read by by_team's formulas and by query noisy_runs. Its typed columns are read from `<database>.job_runs`. It is a CTE in each final below and has no block of its own.

**Finals**
- by_team (team, total_mins, alerted_runs): a summary. Its only typed column, team, is what its SUMIFS and COUNTIFS match on. Its final query groups job_runs.
- by_team (Total Row) (total_mins, alerted_runs): the Total Row. Its label Total gets no column, and each SUBTOTAL(109) is a SUM. It reads by_team's final query as a CTE.
- noisy_runs (run_id, team, alerts, running_mins): query noisy_runs loads it. No formula reads it, so its rows are the query's.

**Left out**
- Parameters and Keys are settings, empty, and never a source, step or final.

**Column notes**
- team: the XLOOKUP is a LEFT JOIN of jobs on job_id, then jobs.team.
- alerts: the COUNTIF of run_alerts is a COUNT(*) per run_id, joined in, with COALESCE to 0.
- running_mins: SUMIFS over its own Table with "<=" on dt is a running total: a SUM partitioned by job_id, ordered by dt, with RANGE so ties count as Excel's, and COALESCE to 0.
- by_team's total_mins and alerted_runs: the SUMIFS and COUNTIFS over job_runs, joined per team, with COALESCE to 0.

**Values written in**
- by_team's groups, data and finance, are typed into the Hive. A team added to the workbook later won't be in the table.

**Values typed over a formula**
- None.

**Marks**
- first match: team's XLOOKUP takes the first match in jobs, while the join gives every match. job_id is unique in the sample. If job_id repeats in the database table, job_runs rows repeat too.
- typed groups: data and finance, as above.
- Total Row: its Total label is dropped, and each total cell is one column.

**Refusals**
- None.

**Left alone**
- The Steps sheet, and the notes in D1 of Parameters and Keys (cells outside a Table).

**To fill in**
- `<database>` in each read.

### Hive

#### by_team

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alert_count, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alert_count FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
)
SELECT t.team,
  COALESCE(s.total_mins, 0) AS total_mins,
  COALESCE(c.alerted_runs, 0) AS alerted_runs
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance') t
LEFT JOIN (SELECT team, SUM(duration_mins) AS total_mins FROM job_runs GROUP BY team) s
  ON t.team = s.team
LEFT JOIN (SELECT team, COUNT(*) AS alerted_runs FROM job_runs WHERE alerts > 0 GROUP BY team) c
  ON t.team = c.team
```

#### by_team (Total Row)

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alert_count, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alert_count FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
),
by_team AS (
  SELECT t.team,
    COALESCE(s.total_mins, 0) AS total_mins,
    COALESCE(c.alerted_runs, 0) AS alerted_runs
  FROM (SELECT 'data' AS team UNION ALL SELECT 'finance') t
  LEFT JOIN (SELECT team, SUM(duration_mins) AS total_mins FROM job_runs GROUP BY team) s
    ON t.team = s.team
  LEFT JOIN (SELECT team, COUNT(*) AS alerted_runs FROM job_runs WHERE alerts > 0 GROUP BY team) c
    ON t.team = c.team
)
SELECT SUM(total_mins) AS total_mins, SUM(alerted_runs) AS alerted_runs
FROM by_team
```

#### noisy_runs

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.duration_mins, r.dt,
    j.team,
    COALESCE(a.alert_count, 0) AS alerts,
    COALESCE(SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS running_mins
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN (SELECT run_id, COUNT(*) AS alert_count FROM <database>.run_alerts GROUP BY run_id) a
    ON r.run_id = a.run_id
)
SELECT run_id, team, alerts, running_mins
FROM job_runs
WHERE alerts >= 2
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X71

### Map

- **Sources**
  - job_runs: its typed columns, read from `<database>.job_runs`. Only run_id, job_id, status and duration_mins are read.
- **Steps**
  - ok_runs: query ok_runs keeps job_runs' SUCCESS rows (run_id, job_id, duration_mins). It is a step because query ok_by_job's M names it. Table ok_runs (run_id, job_id, duration_mins, hours) is a step, not a final, because ok_hours' formulas read it. Both are one CTE named ok_runs, with the hours formula in it, in each final that reads them (ok_by_job and ok_hours).
- **Finals**
  - ok_by_job (job_id, total_mins): Table loaded by query ok_by_job, read by no formula, so it is a final with the query's rows. Query ok_by_job groups ok_runs by job_id and sums duration_mins.
  - ok_hours (job_id, hours): a summary, since its only typed column, job_id, is what its SUMIFS matches on. Its final is a GROUP BY of ok_runs, with its typed job_ids kept as groups.
- **Values written in**
  - ok_hours' groups: job_id 1, 2 and 3, from its typed rows. A job added later won't be in the table.
- **Values typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**
  - Parameters and Keys, both empty. Neither is a source, step or final. No formula reads a fixed value, and no Keys row is needed.
  - job_runs' avg_retry_secs and dt, which no piece reads.
- **To fill in**: `<database>`, in each read of job_runs and each CTE's source.

### Hive

-- final: ok_by_job

```sql
-- final: ok_by_job
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins, duration_mins / 60 AS hours
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT job_id, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

```sql
-- final: ok_hours
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins, duration_mins / 60 AS hours
  FROM <database>.job_runs
  WHERE status = 'SUCCESS'
)
SELECT g.job_id, COALESCE(s.hours_total, 0) AS hours
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) g
LEFT JOIN (SELECT job_id, SUM(hours) AS hours_total FROM ok_runs GROUP BY job_id) s
  ON g.job_id = s.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X72

### Map

- **Sources**
  - job_runs: its typed columns, read from `<database>.job_runs`. Only job_id and duration_mins are read.
  - jobs: its typed columns job_id, job_name and team, read from `<database>.jobs`, inside the step below.
- **Steps**
  - jobs (job_id, job_name, team, runs, total): a Table with formula columns that Table by_team's formulas and query busy_jobs read, so it is a step, not a final. Its runs is COUNTIF over job_runs by job_id, and its total is SUMIF of duration_mins over job_runs by job_id, each a LEFT JOIN with COALESCE to 0. One CTE named jobs.
- **Finals**
  - by_team (team, team_total): a summary, since its only typed column, team, is what its SUMIFS matches on. Its final is a GROUP BY of jobs' total by team, with its typed teams kept as groups.
  - busy_jobs (job_id, job_name, runs): Table loaded by query busy_jobs, read by no formula, so it is a final with the query's rows. Query busy_jobs keeps jobs rows with runs of 3 or more.
- **Values written in**
  - by_team's groups: data, finance and web, from its typed rows. A team added later won't be in the table.
- **Values typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**
  - Parameters and Keys, both empty. Neither is a source, step or final.
  - job_runs' run_id, status, avg_retry_secs and dt, which no piece reads.
- **To fill in**: `<database>`, in each read of jobs and job_runs.

### Hive

```sql
-- final: by_team
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(c.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total
    FROM <database>.job_runs
    GROUP BY job_id
  ) c
    ON j.job_id = c.job_id
)
SELECT g.team, COALESCE(s.team_total, 0) AS team_total
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') g
LEFT JOIN (SELECT team, SUM(total) AS team_total FROM jobs GROUP BY team) s
  ON g.team = s.team
```

```sql
-- final: busy_jobs
WITH jobs AS (
  SELECT j.job_id, j.job_name, j.team,
    COALESCE(c.runs, 0) AS runs,
    COALESCE(c.total, 0) AS total
  FROM <database>.jobs j
  LEFT JOIN (
    SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total
    FROM <database>.job_runs
    GROUP BY job_id
  ) c
    ON j.job_id = c.job_id
)
SELECT job_id, job_name, runs
FROM jobs
WHERE runs >= 3
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X75

### Map

- **Sources**
  - job_runs: its typed columns, read from `<database>.job_runs`. Only run_id, dt and duration_mins are read.
- **Steps**
  - long_runs: query long_runs keeps job_runs rows with duration_mins of 15 or more (run_id, dt, duration_mins). It is a step because query long_per_day's M names it. One CTE named long_runs in long_per_day's block.
- **Finals**
  - long_runs (run_id, dt, duration_mins, over): Table loaded by query long_runs. No other Table's formula reads it, so it is a final with the query's rows, and its formula over is duration_mins - 15. Its own formula reads its own row, which does not count.
  - long_per_day (dt, runs): Table loaded by query long_per_day, read by no formula, so it is a final with the query's rows. Query long_per_day groups long_runs by dt and counts the rows.
- **Values written in**: none.
- **Values typed over a formula**: none.
- **Marks**
  - over is a Hive reserved word, so the column is written in backticks as `` `over` ``.
- **Refusals**: none.
- **Left alone**
  - Parameters and Keys, both empty. Neither is a source, step or final.
  - job_runs' job_id, status and avg_retry_secs, which no piece reads.
- **To fill in**: `<database>`, in each read of job_runs.

### Hive

```sql
-- final: long_runs
SELECT run_id, dt, duration_mins, duration_mins - 15 AS `over`
FROM <database>.job_runs
WHERE duration_mins >= 15
```

```sql
-- final: long_per_day
WITH long_runs AS (
  SELECT run_id, dt, duration_mins
  FROM <database>.job_runs
  WHERE duration_mins >= 15
)
SELECT dt, COUNT(*) AS runs
FROM long_runs
GROUP BY dt
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X76

### Map

- **Sources**
  - jobs: its typed columns job_id, job_name and team, read from `<database>.jobs`.
  - job_runs: its typed columns run_id, job_id and duration_mins, read from `<database>.job_runs`.
- **Steps**
  - finance_jobs: query finance_jobs keeps jobs rows with team "finance" (job_id, job_name). It is a step because query finance_runs' M names it. One CTE named finance_jobs in finance_runs' block.
- **Finals**
  - finance_jobs (job_id, job_name, label): Table loaded by query finance_jobs. No formula or other query reads this Table, so it is a final with the query's rows. Its formula label is UPPER(job_name). Its block inlines the query.
  - finance_runs (run_id, job_name, duration_mins): Table loaded by query finance_runs, read by no formula, so it is a final with the query's rows. Query finance_runs joins job_runs to the finance_jobs step on job_id, inner, and keeps run_id, job_name and duration_mins.
- **Values written in**: none.
- **Values typed over a formula**: none.
- **Marks**: none.
- **Refusals**: none.
- **Left alone**
  - Parameters and Keys, both empty. Neither is a source, step or final.
  - jobs' region, and job_runs' status, avg_retry_secs and dt, which no piece reads.
- **To fill in**: `<database>`, in each read of jobs and job_runs.

### Hive

```sql
-- final: finance_jobs
SELECT job_id, job_name, UPPER(job_name) AS label
FROM <database>.jobs
WHERE team = 'finance'
```

```sql
-- final: finance_runs
WITH finance_jobs AS (
  SELECT job_id, job_name
  FROM <database>.jobs
  WHERE team = 'finance'
)
SELECT r.run_id, f.job_name, r.duration_mins
FROM <database>.job_runs r
JOIN finance_jobs f
  ON r.job_id = f.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X81

### Map

**Sources**
- job_runs, its typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read as `<database>.job_runs`. It has no formula column and no query loads it, so it is a source only.

**Steps**
- None. No query exists in the workbook, and no formula reads a Table that is a step.

**Finals**
- by_job, columns job_id, long_failed, mid_mins, failed_or_test. It is a summary: its only typed column, job_id, is the one its COUNTIFS and SUMIFS match on, so its final is a GROUP BY of job_runs with its typed job_id rows kept. Nothing else reads it, so it is a final.
- by_job (Total Row): none. The workbook shows no Total Row for by_job.

**Left out**
- Parameters: a setting, never a source, step or final. It is empty, and no formula reads it.
- Keys: a setting, never a source, step or final. It is empty. No value is typed over a formula, so no Keys row is needed.

**Values written in**
- by_job's typed job_id groups, 1, 2 and 3, are typed into its final (file 15 summary groups). A job_id added to job_runs later won't appear in by_job until it is added to these groups.

**Values typed over a formula**
- None.

**Marks**
- None.

**Refusals**
- None.

**Left alone**
- The Steps sheet and the D1 notes on Parameters and Keys, which are cells outside a Table.
- The blank status on run 98 is kept as it is. The `status <> 'TEST' OR status IS NULL` condition counts it as Excel does, so no COALESCE is added.

**To fill in**
- `<database>`, the Dev database name, in each FROM of the final's block.

### Hive

```sql
SELECT j.job_id,
  COALESCE(f.long_failed, 0) AS long_failed,
  COALESCE(m.mid_mins, 0) AS mid_mins,
  COALESCE(t.failed_or_test, 0) AS failed_or_test
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (
  SELECT job_id, COUNT(*) AS long_failed
  FROM <database>.job_runs
  WHERE status = 'FAILED' AND duration_mins >= 20
  GROUP BY job_id
) f ON j.job_id = f.job_id
LEFT JOIN (
  SELECT job_id, SUM(duration_mins) AS mid_mins
  FROM <database>.job_runs
  WHERE duration_mins > 10 AND duration_mins <= 30
    AND (status <> 'TEST' OR status IS NULL)
  GROUP BY job_id
) m ON j.job_id = m.job_id
LEFT JOIN (
  SELECT job_id, COUNT(*) AS failed_or_test
  FROM <database>.job_runs
  WHERE status IN ('FAILED', 'TEST')
  GROUP BY job_id
) t ON j.job_id = t.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X05

### Map

**Sources**
- job_runs, its typed columns (run_id, dt), read from `<database>.job_runs`.
- region_costs, its typed columns (job_id, cost_cents, region, dt), read from `<database>.region_costs`.

**Steps**
- None. No query is in the workbook, and no Table's formula reads another Table.

**Finals**
- job_runs (run_id, dt, month, days_since). Its formulas read its own row, and nothing else reads it, so it is a final.
- region_costs (job_id, cost_cents, region, dt, day). Nothing reads it, so it is a final.

**Settings, neither a source, step nor final**
- Parameters: empty, and no formula reads it. Left out.
- Keys: empty, and no value is typed over a formula, so no row is needed. Left out.

**Values written in**
- None. Parameters is empty and no summary is in the workbook.

**Values typed over a formula**
- None. Every formula cell holds its formula.

**Marks**
- region_costs, day: dt holds dates as text (20260911), so day is built from its parts with CONCAT and SUBSTR, as text in the form yyyy-mm-dd, not as a date type.

**Refusals**
- None.

**Left alone**
- Parameters and Keys, as above.
- The Steps sheet and the D1 notes on the Parameters and Keys sheets: cells outside a Table.

**<...> to fill in**
- `<database>` in the FROM line of each final.

### Hive

```sql
SELECT run_id, dt, MONTH(dt) AS month, DATEDIFF(dt, '2026-09-01') AS days_since
FROM <database>.job_runs
```

```sql
SELECT job_id, cost_cents, region, dt,
  CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS day
FROM <database>.region_costs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X10

### Map

**Sources**
- job_runs, its typed columns (run_id, job_id, duration_mins, dt), read from `<database>.job_runs`.

**Steps**
- None.

**Finals**
- job_runs (run_id, job_id, duration_mins, dt, hours, sample). Its formulas read its own row, and nothing else reads it, so it is a final.

**Settings, neither a source, step nor final**
- Parameters: empty, and no formula reads it. Left out.
- Keys: empty. There is no Keys row for job_runs, although one value is typed over a formula. So the typed-over value is matched on every typed column of its row (run_id, job_id, duration_mins, dt), and the map says there is no Keys row. A Keys row for job_runs with run_id would let the match use run_id alone.

**Values written in**
- None.

**Values typed over a formula**
- job_runs, hours, at run_id 103 (run_id 103, job_id 3, duration_mins 30, dt 2026-09-24): typed as 9, where the formula gives 30 / 60. Matched on every typed column, as there is no Keys row.

**Marks**
- None.

**Refusals**
- job_runs, sample (`=RAND()`): `NULL AS sample`. RAND has no Hive here, and its value changes on each calculation.

**Left alone**
- Parameters and Keys, as above.
- The Steps sheet and the D1 notes on the Parameters and Keys sheets: cells outside a Table.

**<...> to fill in**
- `<database>` in the FROM line.

### Hive

```sql
SELECT run_id, job_id, duration_mins, dt,
  CASE WHEN run_id = 103 AND job_id = 3 AND duration_mins = 30 AND dt = '2026-09-24' THEN 9 ELSE duration_mins / 60 END AS hours,
  NULL AS sample
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X15

### Map

- **Sources:** `<database>.tblRuns`, its typed columns: `<run_id>` (Run ID), `<job_id>` (Job ID), `<duration_mins>` (Duration (mins)).
- **Steps:** none.
- **Finals:** tblRuns (`<run_id>`, `<job_id>`, `<duration_mins>`, hours). It has a formula column, no query loads it, and no other Table's formula or query reads it, so it is a final. Its formula column hours reads its own row only.
- **Settings, never a source, step or final:** Parameters (empty, and no formula reads it) and Keys (empty, since no value is typed over a formula, so no Keys row is needed).
- **Values written in:** none.
- **Values typed over a formula:** none. Every Hours cell holds the formula.
- **Marks:** none.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the D1 notes on the Parameters and Keys sheets, as cells outside a Table.
- **`<...>` to fill in:** `<database>`, `<run_id>`, `<job_id>`, `<duration_mins>`.

### Hive

```sql
SELECT <run_id>, <job_id>, <duration_mins>,
  <duration_mins> / 60 AS hours
FROM <database>.tblRuns
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X20

### Map

- **Sources:** `<database>.run_alerts`, its typed columns: alert_id, run_id, severity, dt. No query loads it, and it has no formula, so it is a source.
- **Steps:** none. Query alert_pivot names no other query, so its steps are flattened into its final's SELECT.
- **Finals:** alert_pivot (run_id, high, low), the Table that Power Query alert_pivot loads. No formula reads it, so it is a final, and its rows are the query's. The query and the Table are two pieces, the query's Hive is the Table's final block.
- **Settings, never a source, step or final:** Parameters (empty, and no formula reads it) and Keys (empty, since no value is typed over a formula, so no Keys row is needed).
- **Values written in:** none. The Table alert_pivot is not a summary, so its rows are not typed in; they come from the query.
- **Values typed over a formula:** none.
- **Marks:**
  - Table.Pivot: the pivot's columns high and low are fixed now, as the severity values in the sample, so a new severity will not get a column. Each run with no row for a severity is NULL there, as M leaves it.
  - Table.Pivot groups by run_id, the one column it does not pivot.
- **Refusals:** none.
- **Left alone:** the Steps sheet, and the D1 notes on the Parameters and Keys sheets, as cells outside a Table.
- **`<...>` to fill in:** `<database>`.

### Hive

```sql
SELECT run_id,
  SUM(CASE WHEN severity = 'high' THEN 1 END) AS high,
  SUM(CASE WHEN severity = 'low' THEN 1 END) AS low
FROM <database>.run_alerts
WHERE run_id = 97 OR run_id = 101
GROUP BY run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X45

### Map

**Sources**
- `job_runs`: run_id, job_id, status, duration_mins, avg_retry_secs, dt (its typed columns, read as `<database>.job_runs`)
- `scheduler_runs`: run_id, job_id, dt (its typed columns, read as `<database>.scheduler_runs`)

**Steps**
- None. No formula reads a Table, and no query is read by another query, so nothing is a CTE.

**Finals**
- Table `run_days` (run_id, dt), loaded by query `run_days`. Its rows are the query's. The query's M is the block itself, not a CTE, as nothing reads the query. Table.Combine inside Table.Distinct makes a UNION.
- Table `matched` (run_id, job_id, dt, status), loaded by query `matched`. Its rows are the full outer join of scheduler_runs with job_runs, with status expanded from job_runs.

**Values written in:** none.

**Values typed over a formula:** none. The workbook has no formula column.

**Marks:** none.

**Refusals:** none.

**Left alone:** Parameters and Keys, the two settings Tables, both empty. They are never a source, step or final, and Keys needs no row because no value is typed over a formula. Also left alone are the cells outside a Table: the Steps sheet, and the D1 notes on the Parameters and Keys sheets.

**To fill in:** `<database>`, the database that holds job_runs and scheduler_runs, in both blocks.

### Hive

```sql
SELECT run_id, dt FROM <database>.job_runs
UNION
SELECT run_id, dt FROM <database>.scheduler_runs
```

```sql
SELECT s.run_id, s.job_id, s.dt, r.status
FROM <database>.scheduler_runs s
FULL OUTER JOIN <database>.job_runs r ON s.run_id = r.run_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X55

### Map

**Sources**
- `jobs`: job_id, job_name, team, region (its typed columns, read as `<database>.jobs`)

**Steps**
- None.

**Finals**
- Table `jobs` (job_id, job_name, team, region, title, tag, code, has_sync, tens). Its formula columns read only its own row, so they don't make it a step, and nothing else reads it: it is a final.

**Values written in:** none.

**Values typed over a formula:** none.

**Marks:** none.

**Refusals:** none.

**Left alone:** Parameters and Keys, the two settings Tables, both empty. They are never a source, step or final, and Keys needs no row because no value is typed over a formula. Also left alone are the cells outside a Table: the Steps sheet, and the D1 notes on the Parameters and Keys sheets.

**To fill in:** `<database>`, the database that holds jobs, in the block below.

### Hive

```sql
SELECT job_id, job_name, team, region,
  INITCAP(REPLACE(job_name, '_', ' ')) AS title,
  CONCAT_WS('/', team, region) AS tag,
  CONCAT(region, '-', job_id) AS code,
  INSTR(LOWER(job_name), LOWER('SYNC')) > 0 AS has_sync,
  CAST(CONCAT(job_id, '0') AS DOUBLE) AS tens
FROM <database>.jobs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X68

### Map

**Sources**
- `<database>.job_runs`: typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. Read by step base.
- `<database>.jobs`: typed columns job_id, job_name, team, region. Read by step base: job_id, job_name.
- `<database>.region_budgets`: typed columns job_id, budget_cents, region. Read by step base: job_id, region.

**Steps**
- Query base, a CTE `base` in the blocks of Table by_region (its final and its Total Row) and Table top_runs. It reads the three sources: job_runs inner joined to jobs, then left joined to region_budgets, as M's Inner and LeftOuter joins. Columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt, job_name, region.

**Finals** (Hive blocks in this order)
1. Table by_region: columns region, total_mins, runs, share. Its rows are query by_region's: base grouped by region, keeping the groups with at least 2 runs. Query by_region loads only this Table and nothing reads it, so it is this final's query and has no block of its own. share is a formula column by file 11: `total_mins / SUM(total_mins) OVER ()`, over the Table's rows.
2. Table by_region (Total Row): total_mins only. The Total Row's region cell is the label Total, and its runs and share cells are empty, so there is no column for them. SUBTOTAL(109, ...) is a SUM.
3. Table top_runs: columns run_id, job_name, region. Its rows are query top_runs': base sorted by duration_mins descending, then run_id ascending, the first 2 rows, with those three columns. Query top_runs loads only this Table, so it is this final's query and has no block of its own.

**Values written in**: none. Parameters is empty, so no XLOOKUP value is written in. by_region is grouped by a query, not a summary typed in.

**Values typed over a formula**: none. Keys is empty, so no Keys row is needed.

**Marks**: none.

**Refusals**: none.

**Left alone**: Parameters and Keys. Both are empty settings Tables, never a source, step or final.

**`<...>` to fill in**: `<database>` in each read of job_runs, jobs and region_budgets (in base, so in each block).

### Hive

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
grouped AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
)
SELECT region, total_mins, runs, total_mins / SUM(total_mins) OVER () AS share
FROM grouped
```

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
),
grouped AS (
  SELECT region, SUM(duration_mins) AS total_mins, COUNT(*) AS runs
  FROM base
  GROUP BY region
  HAVING COUNT(*) >= 2
),
by_region AS (
  SELECT region, total_mins, runs, total_mins / SUM(total_mins) OVER () AS share
  FROM grouped
)
SELECT SUM(total_mins) AS total_mins
FROM by_region
```

```sql
WITH base AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.job_name, b.region
  FROM <database>.job_runs r
  JOIN <database>.jobs j ON r.job_id = j.job_id
  LEFT JOIN <database>.region_budgets b ON r.job_id = b.job_id
)
SELECT run_id, job_name, region
FROM base
ORDER BY duration_mins DESC, run_id ASC
LIMIT 2
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X79

### Map

**Sources**: none. job_runs has formula columns and nothing else reads it, so it is a final, not a source.

**Steps**: none.

**Finals**
1. Table job_runs: columns run_id, job_id, status, duration_mins (typed, read from `<database>.job_runs`), kept and long_or_failed (formula columns, by file 11). Nothing loads or reads job_runs apart from its own formulas, so it is a final, its rows read from the database.

**Values written in**: none.

**Values typed over a formula**: none. Keys is empty, so no Keys row is needed.

**Marks**: blank. The sample has a blank status (run 98, Row 5), and both formulas read status, so each writes COALESCE(status, '') in place of status. IF is not an -IF(S) form, so the column is not left as it is.

**Refusals**: none.

**Left alone**: Parameters and Keys. Both are empty settings Tables, never a source, step or final.

**`<...>` to fill in**: `<database>` in the FROM.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins,
  IF(COALESCE(status, '') <> '' AND COALESCE(status, '') <> 'TEST', 1, 0) AS kept,
  IF((duration_mins > 25 OR COALESCE(status, '') = 'FAILED'), 'yes', 'no') AS long_or_failed
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.

## X82

### Map

**Sources**
- job_runs: its typed columns run_id, job_id, status, duration_mins and dt, read from `<database>.job_runs`.

**Steps**
- None.

**Finals**
- job_runs (run_id, job_id, status, duration_mins, dt, needs_look, failed_long_mins, failed_or_late): no query loads it, and no Table formula reads it, so it is a final. It has formula columns, so it is not a source alone. Its query reads the source directly, with no CTE.
- Parameters and Keys are never a source, step or final.

**Values written in**
- None. No formula reads Parameters, and there is no summary.

**Values typed over a formula**
- None. Every formula cell holds its formula, and Keys is empty, so there is no Keys row and no CASE.

**Marks**
- blank: needs_look reads status, which is blank in run_id 98 (row 5). Written as `COALESCE(status, '')`, so the blank is not FAILED, as in Excel. failed_long_mins and failed_or_late compare status inside SUMPRODUCT conditions, which skip a blank, so they are written as they are.
- whole-column totals: failed_long_mins and failed_or_late read their own Table, so each is written with `OVER ()`, and every row shows the same total, as Excel's SUMPRODUCT does.
- failed_or_late: the `+` in `((..)+(..)>0)` is an OR, so it is written as `status = 'FAILED' OR dt = '2026-09-24'`.
- check: dt is compared with the text '2026-09-24', as Excel's formula does. If dt holds a real date in the workbook rather than text, Excel's comparison never matches, so confirm dt is text before the run.

**Refusals**
- None. No formula in the workbook is refused.

**Left alone**
- Parameters: an empty settings Table, which no formula reads.
- Keys: an empty settings Table, as no value is typed over a formula.
- The Steps sheet, and the notes in D1 of the Parameters and Keys sheets: text outside a Table, not calculations.
- No charts, PivotTables or defined names are listed in the workbook.

**To fill in**
- `<database>` in job_runs's FROM clause.

### Hive

```sql
SELECT run_id, job_id, status, duration_mins, dt,
  IF((COALESCE(status, '') = 'FAILED' OR duration_mins > 25) AND NOT (job_id = 1), 1, 0) AS needs_look,
  SUM(CASE WHEN status = 'FAILED' AND duration_mins > 15 THEN duration_mins ELSE 0 END) OVER () AS failed_long_mins,
  COUNT(CASE WHEN status = 'FAILED' OR dt = '2026-09-24' THEN 1 END) OVER () AS failed_or_late
FROM <database>.job_runs
```

### Next

Take out what you don't want, fill in `<database>`, save the query as a .hql file named job_runs.hql, and run the convert Workflow on it as one batch (file 13). It writes and checks the Toolbox code.
