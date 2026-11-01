## Q1

**Map**

- Sources: `job_runs`, the Raw sheet's Table of typed rows. Its note says it was copied from ops.job_runs. Written `<database>.job_runs`.
- Steps: `CleanRuns`. The Power Query "CleanRuns" loads it into the Table CleanRuns on Clean, and the Daily formulas read it, so it is a step: a CTE inside each final's query.
- Summary: `daily_runs` on Daily. Its only typed column, dt, is what its COUNTIFS match on, so it is a GROUP BY of CleanRuns.
- Finals: `daily_runs (dt, runs, total_duration_mins)`, to be written to mart_dev.daily_runs; and `daily_runs (Total Row)`, a query of its own.

**Marks**

- Power Query, Table.TransformColumnTypes: nothing.
- `[status] <> null` becomes `status IS NOT NULL`, and `[status] <> "TEST"` becomes `status <> 'TEST'`. The null check comes first, so the blank status of run 98 is dropped.
- Source: Excel.CurrentWorkbook reads the workbook's job_runs, not a database. The note says ops, so check the database name.
- dt is text in yyyy-mm-dd form, which Hive reads as it is. The date is held as text, and it is kept as it is.
- avg_retry_secs is blank in run 98, but no formula reads it and the query drops that row, so no COALESCE(x, 0) for a blank is needed.
- COUNTIFS and SUMIFS over CleanRuns become COUNT(*) and SUM(duration_mins) per dt, each with COALESCE(.., 0), as Excel gives 0 where nothing matches. The days come from CleanRuns, so a day with no runs would have no row here, where Excel's day would show 0. The sample has runs on both days, so nothing is missing.
- Total Row: SUBTOTAL(109, ...) becomes SUM. The Total Row has no label, so its "Total" text is dropped.

**Refused:** none.

**Left alone:** nothing. There are no charts, PivotTables or cells outside a Table. The Steps, Clean and Daily notes are text.

**Values typed over a formula:** none. Keys is empty, so no row is needed.

**Parameters:** empty, so none.

**To fill in:** `<database>`, the database that holds job_runs. The note says ops. It appears in the query's FROM and in the Table reference import.

```sql
-- daily_runs (final), target mart_dev.daily_runs
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT dt,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(SUM(duration_mins), 0) AS total_duration_mins
FROM CleanRuns
GROUP BY dt
```

```sql
-- daily_runs (Total Row): one row, a column per total, no label
WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
),
daily_runs AS (
  SELECT dt,
    COALESCE(COUNT(*), 0) AS runs,
    COALESCE(SUM(duration_mins), 0) AS total_duration_mins
  FROM CleanRuns
  GROUP BY dt
)
SELECT SUM(runs) AS runs, SUM(total_duration_mins) AS total_duration_mins
FROM daily_runs
```

Toolbox code, with `<database>` as the database that holds job_runs:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, all_columns, count_rows, derived,
                              is_not_null, not_equals, statement, sum_of)
from references.<database>__job_runs import job_runs

# CleanRuns: the Power Query's rows, a step that daily_runs reads
clean_runs = derived("CleanRuns", statement(
    SELECT(*all_columns(job_runs)),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's query reads every row
    WHERE(is_not_null(job_runs.status), not_equals(job_runs.status, "TEST")),
))

# daily_runs: one row per day, the summary's GROUP BY
daily = statement(
    SELECT(clean_runs.dt, AS(count_rows(), "runs"),
           AS(sum_of(clean_runs.duration_mins), "total_duration_mins")),
    FROM(clean_runs),
    GROUP_BY(clean_runs.dt),
)

# daily_runs (Total Row): one row, a column per total, no label
daily_runs = derived("daily_runs", daily)
total_row = statement(
    SELECT(AS(sum_of(daily_runs.runs), "runs"),
           AS(sum_of(daily_runs.total_duration_mins), "total_duration_mins")),
    FROM(daily_runs),
)
```

The Toolbox code leaves out COALESCE, as files 03 to 05 name no function that wraps a total. Every day in CleanRuns has runs in this sample, so no day comes out 0.

**What to do next**

1. Take out anything you don't want converted. Nothing in this workbook is marked for removal.
2. Fill in `<database>` with ops, in the query and in the import line.
3. Save the daily_runs query as daily_runs.hql, and run the convert Workflow (file 13) on it, with DEV filled in as mart_dev. The Workflow's checked code wins where it and this answer differ.
4. The Total Row is a check, not a table. Run its query in the notebook. On this sample it should give runs 7 and total_duration_mins 160, the same as the Excel Total Row (3 + 4 runs; 60 + 100 minutes).
