## Q1

### Map

- **Sources**
  - `job_runs` (Excel Table on the Runs sheet), read as `<database>.job_runs`. Its columns are run_id, job_id, status, duration_mins, avg_retry_secs and dt. Its sample rows are not read; the warehouse table holds more rows. Your Runs source is ops.job_runs, so `<database>` is ops.
- **Steps**: none.
- **Finals**
  - `job_run_report`, the Table `run_report` (Report sheet), named as you asked. Its columns are job_id, runs, failed_runs and avg_duration_mins. Its only typed column, job_id, is the one its COUNTIFS match on, so it is a summary: a GROUP BY of job_runs, with job_id 1, 2 and 3 typed in as its groups.
  - runs: COUNTIFS of job_runs by job_id, as COUNT(*), with COALESCE to 0.
  - failed_runs: COUNTIFS of job_runs by job_id and status, the status value from Parameters typed in as 'FAILED', as COUNT(*), with COALESCE to 0.
  - avg_duration_mins: AVERAGEIFS of job_runs by job_id, as AVG, with no COALESCE, so a job with no runs is NULL where Excel shows #DIV/0!.
- **Not a source, step or final**
  - `Parameters` (failed_status = FAILED): read by failed_runs as its value.
  - `Keys`: empty (None), so no row is needed.
- **Power Query**: none in the workbook.
- **Total Row**: none.
- **Typed-over values**: none. Every cell in run_report's three formula columns holds a formula.
- **Marks**: none from the list.
- **Refusals**: none.
- **Blank**: run 98 has a blank status. The COUNTIFS form skips it, so it is written as it is, with no COALESCE and no mark.
- **Left alone**: the Steps sheet's text, Runs!A1, Report!F1, Parameters!D1 and Keys!D1, which are cells outside a Table.
- **To fill in**: `<database>` (ops, as you said).

### Hive

```sql
SELECT j.job_id,
  COALESCE(r.runs, 0) AS runs,
  COALESCE(f.failed_runs, 0) AS failed_runs,
  a.avg_duration_mins
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) r
  ON j.job_id = r.job_id
LEFT JOIN (SELECT job_id, COUNT(*) AS failed_runs FROM <database>.job_runs
  WHERE status = 'FAILED' GROUP BY job_id) f
  ON j.job_id = f.job_id
LEFT JOIN (SELECT job_id, AVG(duration_mins) AS avg_duration_mins FROM <database>.job_runs
  GROUP BY job_id) a
  ON j.job_id = a.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
