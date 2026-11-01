## Q1

### Map

- **Sources:** `job_runs`, the Table on the sheet job_runs (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt). Its Hive reads `<database>.job_runs`. The sheet's note says it was copied from ops.job_runs, so `<database>` may be `ops`; check it.
- **Steps:** `CleanRuns`, the Table loaded by the Power Query CleanRuns from job_runs. Daily's COUNTIFS and SUMIFS read it, so it is a step: a CTE inside Daily's query. The rows typed on the sheet CleanRuns are the query's output, not formulas; the query's M on the Power Query sheet is what converts.
- **Finals:** `Daily`, with the columns dt, runs, total_duration_mins. Daily's only typed column is dt, which its COUNTIFS and SUMIFS match on, so Daily is a summary: a GROUP BY of CleanRuns.
- **Daily (Total Row):** no query of its own. Its totals are SUBTOTAL(109) on runs and on total_duration_mins, both sums, so Daily's query ends `GROUP BY dt WITH ROLLUP`, and the row where dt is NULL is the Total Row.
- **Parameters and Keys:** both empty, so none.
- **Values typed over a formula:** none.

### Hive

Daily, the one final, with its Total Row inside the same query:

```sql
WITH CleanRuns AS (
  SELECT dt, duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT
  dt,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(SUM(duration_mins), 0) AS total_duration_mins
FROM CleanRuns
GROUP BY dt WITH ROLLUP
```

### Marks

- CleanRuns's query: Table.TransformColumnTypes changes no value, so it gives nothing. Table.SelectRows keeps a row whose status is not null and not 'TEST'. M's `[status] <> null` becomes `status IS NOT NULL`. M's `<>` keeps a null in the 'TEST' test, but the null test drops it first, so the Hive keeps the same rows as the query: 95, 96, 97, 101, 102, 103 and 104, the seven rows on the sheet CleanRuns.
- Row 98 has a blank status and a blank avg_retry_secs. The query drops row 98. No formula reads avg_retry_secs, so that blank needs no COALESCE.
- Excel gives 0 where COUNTIFS or SUMIFS match nothing, so both are wrapped in COALESCE.
- The Total Row's SUBTOTAL(109) formulas are converted by the WITH ROLLUP above. The label "Total" in A4 is not converted, as the NULL dt row is the total.
- Excel lists the rows in dt order. A Hive table holds no order, so there is no ORDER BY. Say so if the order matters.
- dt is text in the form 2026-09-23, so it needs no conversion as a date.
- The workbook does not say whether job_runs is partitioned by dt. The Hive reads all of job_runs; no bound to the sample's dates is added, as file 11 says not to filter to the sample's dates. If job_runs is partitioned by dt, the Toolbox refuses an unbounded read, so a bound on dt is needed when the Toolbox code is written.

### Refused

None.

### Left alone, and named

- The sheets Steps, Parameters, Keys and Power Query: instructions and empty Tables, not calculations.
- Notes outside any Table: the H1 notes on job_runs and CleanRuns, D1 on Parameters and Keys, E1 on Daily, the notes on Power Query, and the "Total" label in A4 on Daily.
- Charts and PivotTables: none in the workbook as given.

### To fill in

- `<database>` in `<database>.job_runs`.

### Next

Take out anything you don't want converted, fill in `<database>`, and save the Daily query as Daily.hql. Then run the convert Workflow on it as one batch (file 13), with DEV filled in. Where the Workflow's checked code and this differ, the checked code wins.

You asked for Hive, so no Python is given here. Ask for the Toolbox code and Copilot will write it with files 03, 04 and 05.
