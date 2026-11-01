## Q1

**Map**

- Sources: `job_runs`, the Raw sheet's Table, typed, so it stands for the database table `<database>.job_runs` (ops.job_runs).
- Steps: `CleanRuns`, the Clean sheet's Table, loaded by Power Query "CleanRuns" from job_runs. The daily formulas read it, so it is a step: a CTE inside daily's query. Its query's steps: Source = job_runs; Kept = status not blank and status not "TEST"; TransformColumnTypes = nothing.
- Finals: `daily`, with the columns dt, runs, total_duration_mins. Its only typed column is dt, which its COUNTIFS and SUMIFS match on, so daily is a summary: a GROUP BY of CleanRuns.
- `daily (Total Row)`: one row, a column per total, runs and total_duration_mins, with no label.
- Parameters: none (the sheet is empty). Keys: none (the sheet is empty).

**Typed over a formula:** none. Keys holds no row, so no typed value needs one.

**Marks, converted and said:**

- The query's `[status] <> null` becomes `status IS NOT NULL`. M's `[status] <> "TEST"` keeps a null, as Hive's `<>` doesn't, so the IS NOT NULL goes in front and the two together read `status IS NOT NULL AND status <> 'TEST'`. The blank status in row 98 is left out, as the workbook leaves it out.
- dt is held as text (the query's `type text`), so the days are grouped as the text is held, such as '2026-09-23'.
- COUNTIFS becomes COUNT(*) in the GROUP BY. Every group has at least one row, so no COALESCE is needed on it.
- SUMIFS becomes SUM, with COALESCE(..., 0), as Excel gives 0 where nothing matches. The Python leaves that COALESCE out, because fill_null works on a column, not on a total; if a day's durations could all be blank, check the Python against the Hive.
- The Total Row's SUBTOTAL(109, ...) becomes a SUM over daily's rows. Its label "Total" is left out.
- avg_retry_secs is read by no formula or step, so it is left out of the Hive. Its blank in row 98 does not matter.

**Refused:** none.

**Left alone, and named:** the Steps sheet (instructions only); the notes in Raw A1 ("Copied from ops.job_runs in our warehouse."), Clean H1, Daily E1 and the title in Power Query sheet A1; the empty Parameters and Keys sheets. There are no charts and no PivotTables.

**To fill in:** `<database>` in both queries: write `ops`, the database that holds job_runs.

Hive, daily, as one query with CleanRuns as a CTE:

```sql
WITH CleanRuns AS (
  SELECT dt, duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT dt, COUNT(*) AS runs, COALESCE(SUM(duration_mins), 0) AS total_duration_mins
FROM CleanRuns
GROUP BY dt
```

Hive, daily (Total Row), its own query, one row with no label:

```sql
WITH CleanRuns AS (
  SELECT dt, duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
), daily AS (
  SELECT dt, COUNT(*) AS runs, COALESCE(SUM(duration_mins), 0) AS total_duration_mins
  FROM CleanRuns
  GROUP BY dt
)
SELECT SUM(runs) AS runs, SUM(total_duration_mins) AS total_duration_mins
FROM daily
```

Toolbox code, with file 03's Derived table, file 04 and file 05's grouping and total. The Table reference `references/ops__job_runs.py` (file 02) must be in the Project:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived,
                              is_not_null, not_equals, statement, sum_of)
from references.ops__job_runs import job_runs

# The workbook's query reads every row of job_runs, so every partition is read on purpose.
clean_runs = derived("CleanRuns", statement(
    SELECT(job_runs.dt, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(is_not_null(job_runs.status), not_equals(job_runs.status, "TEST")),
))

daily = statement(
    SELECT(clean_runs.dt, AS(count_rows(), "runs"),
           AS(sum_of(clean_runs.duration_mins), "total_duration_mins")),
    FROM(clean_runs),
    GROUP_BY(clean_runs.dt),
)

# The Total Row: one row, a column per total, no label.
daily_rows = derived("daily", daily)
daily_total_row = statement(
    SELECT(AS(sum_of(daily_rows.runs), "runs"),
           AS(sum_of(daily_rows.total_duration_mins), "total_duration_mins")),
    FROM(daily_rows),
)
```

Next steps for you:

- Take out anything you don't want converted, then fill in `<database>` with `ops` in both queries.
- Save daily's query as `daily.hql`. Save the Total Row's query as `daily_total_row.hql`; it is one row, not a Table, so leave it out of the convert batch unless you want it saved.
- Run the convert Workflow (file 13) on `daily.hql` as one batch, with DEV filled in. Where the Hive and the checked code differ, the checked code wins.
