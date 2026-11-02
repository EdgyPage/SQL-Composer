date: 2026-11-01
arm: C
model: haiku
files: 21chain-dev

## X71

### Map

**Sources**
- `<database>.job_runs`, the Table job_runs's typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. It has only typed columns and no query loads it, so it is a source, never a final. No piece reads avg_retry_secs or dt, so no final has them.

**Steps**
- Query `ok_runs`, as the CTE `ok_runs`: job_runs' rows where status = 'SUCCESS', columns run_id, job_id, duration_mins. Query ok_by_job's M names it (`Table.Group(ok_runs, ...)`), so it is a step.
- Table `ok_runs`, as the CTE `ok_runs_table` (the query and the Table share one name, so the Table's CTE takes `_table`): the query's rows with hours, columns run_id, job_id, duration_mins, hours (`duration_mins / 60`). Table ok_hours' formulas read it (`ok_runs[hours]`, `ok_runs[job_id]`), so the Table is a step.

**Finals**
- Table `ok_by_job`, loaded by query ok_by_job, whose M groups query ok_runs: columns job_id, total_mins. No formula reads Table ok_by_job, so it is a final. It has no Total Row.
- Table `ok_hours`: a summary. Its only typed column, job_id, is the one its SUMIFS match on, so its final is a GROUP BY of ok_runs_table, with its typed job_ids 1, 2, 3 typed in as groups. Columns job_id, hours (SUMIFS over another Table: a LEFT JOIN, COALESCE to 0). No query loads it, nothing reads it, and it has no Total Row, so it is a final.

**Not a source, step or final**
- Table `Parameters` (name, value; empty) and Table `Keys` (table, key_columns; empty): settings, never a source, step or final. No formula reads Parameters, and no value is typed over a formula, so Keys needs no row.

**Each value typed over a formula**: none. Keys is empty, so there is no CASE.

**Marks**: none. The formulas read only duration_mins and job_id, which have no blanks in the sample. The blank status in job_runs row 98 is dropped by the filter in both Excel and Hive, so it needs no change.

**Refusals**: none.

**Left alone**: the text of the Steps sheet, and the D1 notes on the Parameters and Keys sheets, as cells outside a Table. No charts or PivotTables are listed.

**To fill in**: `<database>`, the user's database name, in the two blocks below (each reads `<database>.job_runs`).

### Hive

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins FROM <database>.job_runs WHERE status = 'SUCCESS'
)
SELECT job_id, SUM(duration_mins) AS total_mins
FROM ok_runs
GROUP BY job_id
```

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins FROM <database>.job_runs WHERE status = 'SUCCESS'
),
ok_runs_table AS (
  SELECT run_id, job_id, duration_mins, duration_mins / 60 AS hours FROM ok_runs
)
SELECT j.job_id, COALESCE(c.hours, 0) AS hours
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3) j
LEFT JOIN (SELECT job_id, SUM(hours) AS hours FROM ok_runs_table GROUP BY job_id) c
  ON j.job_id = c.job_id
```

### Next

Take out what you don't want, fill in each `<...>`, save each query as a .hql file named for its final, and run the convert Workflow on them as one batch (file 13). It writes and checks the Toolbox code.
