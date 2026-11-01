## Q1

**Map**

- Sources: `ops.job_runs`, from the Raw sheet (its note says "Copied from ops.job_runs"). Typed columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt.
- Steps: `CleanRuns`, the Clean sheet's Table, loaded by the Power Query CleanRuns. The Daily formulas read it (COUNTIFS and SUMIFS), so it is a CTE in Daily's query.
- Finals:
  - `daily`, saved as `mart_dev.daily_runs`, with the columns dt, runs, total_duration_mins. It is a GROUP BY of CleanRuns by dt.
  - `daily (Total Row)`, one row with runs and total_duration_mins, no label. It is a query of its own and is not a Table, so it is not saved to mart_dev.daily_runs.
- Parameters and Keys are empty, so there are no Keys rows.

**Hive: daily, into mart_dev.daily_runs**

```sql
WITH CleanRuns AS (
  SELECT dt, duration_mins
  FROM ops.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
)
SELECT dt,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(SUM(duration_mins), 0) AS total_duration_mins
FROM CleanRuns
GROUP BY dt
```

**Hive: daily (Total Row)**

```sql
WITH CleanRuns AS (
  SELECT dt, duration_mins
  FROM ops.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
),
daily AS (
  SELECT dt,
    COALESCE(COUNT(*), 0) AS runs,
    COALESCE(SUM(duration_mins), 0) AS total_duration_mins
  FROM CleanRuns
  GROUP BY dt
)
SELECT SUM(runs) AS runs, SUM(total_duration_mins) AS total_duration_mins
FROM daily
```

**Toolbox code, for daily**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, any_of, count_rows, derived,
                              is_not_null, is_null, not_equals, statement, sum_of)
from references.ops__job_runs import job_runs

# The workbook's query reads every day of job_runs, so the opt-out says so. To read fewer
# days, drop it and bound job_runs.dt, such as between(job_runs.dt, "2026-09-23", "2026-09-24").
clean_runs = derived("CleanRuns", statement(
    SELECT(job_runs.dt, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(is_not_null(job_runs.status),
          any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
))

# daily: one row per day of CleanRuns, saved as mart_dev.daily_runs
s = statement(
    SELECT(clean_runs.dt, AS(count_rows(), "runs"),
           AS(sum_of(clean_runs.duration_mins), "total_duration_mins")),
    FROM(clean_runs),
    GROUP_BY(clean_runs.dt),
)

# daily (Total Row): one row, not saved
daily = derived("daily", s)
total = statement(
    SELECT(AS(sum_of(daily.runs), "runs"),
           AS(sum_of(daily.total_duration_mins), "total_duration_mins")),
    FROM(daily),
)
```

**Marks, and what I did**

1. The Daily table's last row, "Total", is not a day. Its SUBTOTAL(109, ...) formulas read their own column, so as a data row it would be circular. I converted it as daily (Total Row) instead. Step 5 of the Steps sheet says a typed total is read as one more row of data, so if you want the workbook's total as a Total Row, take that typed row out of the table and turn on Total Row (Table Design > Total Row).
2. The Power Query's `[status] <> null` became `status IS NOT NULL`. Its `[status] <> "TEST"` became `(status <> 'TEST' OR status IS NULL)`, as M keeps a null. The first test already drops nulls, so the OR changes nothing. The rows left out are 98 (status None) and 99 (TEST), as on the Clean sheet.
3. The typed-in rows on the Clean sheet are not converted. The query is, since the Table is reloaded from it.
4. The blank avg_retry_secs in row 98 is read by no formula, so it is not converted.
5. The COALESCE wrappers are in the Hive. The Toolbox code leaves them out: each day has at least one row, so COUNT is never NULL, and the Toolbox code does not wrap a total. Where the two differ, the checked code wins.
6. The workbook reads every day, so the Toolbox code uses `reads_all_partitions=True`, with its reason in a comment. Pick a dt range if you want fewer days.
7. Nothing typed over a formula was found, so no Keys row is needed. Nothing was refused. Left alone: no charts or PivotTables.
8. dt is held as text, already in the form 2026-09-23, so it compares as text with no conversion.
9. Check: from the Clean sheet's rows, 2026-09-23 gives 3 runs and 60 minutes, 2026-09-24 gives 4 runs and 100 minutes, and the Total Row gives 7 and 160.

**Next steps**

- Take out anything you don't want converted.
- No `<...>` needs filling in. The names are the ones you and the workbook give: ops.job_runs and mart_dev.daily_runs. If mart_dev is not your Dev Database, change the name.
- Save the daily query as `daily.hql`, named for its Table. Keep the Total Row query out of the batch: it is not a Table, so check it by hand.
- Run the convert Workflow on `daily.hql` as one batch, with DEV filled in (file 13). For its steps, load file 13 in a new chat.
