## Q1

**Map**

- Sources: `job_runs`, the Table on the Raw sheet, with typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. Its note says "Copied from ops.job_runs", so the database is `ops`, which you fill in for `<database>`.
- Steps: `CleanRuns`, the Table on the Clean sheet, loaded by the Power Query on the Power Query sheet from `job_runs`. Daily's formulas read it (COUNTIFS and SUMIFS), so it is a step: a CTE in each query that reads it.
- Finals:
  - `Daily`: columns dt, runs, total_duration_mins. It is a summary: a GROUP BY of CleanRuns by dt. It covers every day the source holds, not only the two days in the sample.
  - `Daily (Total Row)`: columns runs, total_duration_mins, one row with no label. Its Total Row reads Daily, so Daily's query is also a CTE inside it.
- Parameters and Keys: both sheets are empty, so there are none.
- Typed over a formula: none. No cell holds a typed value over a formula.

**Marks**

- The Power Query's M, on the Power Query sheet, is converted. The 7 typed-in rows on the Clean sheet are the sample of that query's output, and they match it: runs 95, 96, 97, 101, 102, 103 and 104. They are not converted as data.
- The query's filter, `[status] <> null and [status] <> "TEST"`, becomes `status IS NOT NULL AND status <> 'TEST'`.
- Blank cells: run 98 in Raw has a blank status and a blank avg_retry_secs. The query drops the row, as its status check does. No formula reads avg_retry_secs, so it is not wrapped in COALESCE.
- dt is held as text in the form 2026-09-23. It is kept as it is, with no conversion.
- Summary blanks: COUNTIFS and SUMIFS give 0 where nothing matches, so both are wrapped in COALESCE(.., 0).
- The Total Row: Daily's last row, labelled "Total", is Excel's Total Row (SUBTOTAL 109 on each column), not a typed row. It is converted as its own query, with no label.
- No date bound: the workbook has no date filter, so the Hive reads every day of job_runs. The Toolbox code uses `reads_all_partitions=True` for this reason, as its comment says.

**Refusals**

- None.

**Left alone**

- The Steps, Parameters and Keys sheets, which hold instructions and empty Tables.
- The notes in the cells A1, D1, E1 and H1, and the note on the Power Query sheet.
- No charts, PivotTables, or cells outside a Table.

**Fill in**

- `<database>` in both queries. Use `ops`, as the Raw note says.

**Hive, one ```sql block per final and per Total Row**

Daily:

```sql
WITH clean_runs AS (
  SELECT dt, duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT dt,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(SUM(duration_mins), 0) AS total_duration_mins
FROM clean_runs
GROUP BY dt
```

Daily (Total Row):

```sql
WITH clean_runs AS (
  SELECT dt, duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
),
daily AS (
  SELECT dt,
    COALESCE(COUNT(*), 0) AS runs,
    COALESCE(SUM(duration_mins), 0) AS total_duration_mins
  FROM clean_runs
  GROUP BY dt
)
SELECT SUM(runs) AS runs,
  SUM(total_duration_mins) AS total_duration_mins
FROM daily
```

**Toolbox code, by files 03, 04 and 05**

This needs the Table reference `references/ops__job_runs.py`, which file 02 describes. Load file 02 in a new chat if you don't have it yet.

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived,
                              is_not_null, not_equals, statement, sum_of)
from references.ops__job_runs import job_runs

# The Power Query CleanRuns: runs with no status, and test runs, left out.
# The workbook's query has no date bound, so it reads every row; that is why of reads_all_partitions.
clean_runs = derived("clean_runs", statement(
    SELECT(job_runs.dt, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(is_not_null(job_runs.status), not_equals(job_runs.status, "TEST")),
))

# Daily: one row per day of the clean runs.
daily = derived("daily", statement(
    SELECT(clean_runs.dt, AS(count_rows(), "runs"),
           AS(sum_of(clean_runs.duration_mins), "total_duration_mins")),
    FROM(clean_runs),
    GROUP_BY(clean_runs.dt),
))

# Daily's rows, in the Table's order.
daily_rows = statement(
    SELECT(daily.dt, daily.runs, daily.total_duration_mins),
    FROM(daily),
)

# Daily (Total Row): one row, a column per total, with no label.
daily_total_row = statement(
    SELECT(AS(sum_of(daily.runs), "runs"),
           AS(sum_of(daily.total_duration_mins), "total_duration_mins")),
    FROM(daily),
)
```

**What to do next**

1. Take out what you don't want converted, such as the Total Row.
2. Fill in `<database>` with `ops`, or the database your team uses for job_runs.
3. Save the Daily query as a .hql file named for its Table, `daily.hql`, and the Total Row's query as `daily_total_row.hql`.
4. Run the convert Workflow on those .hql files as one batch, with DEV filled in, as file 13 describes.
5. Where the Hive above and the Toolbox code differ, the checked code wins.
