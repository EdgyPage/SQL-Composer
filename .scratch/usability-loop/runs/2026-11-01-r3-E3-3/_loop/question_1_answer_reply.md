## Q1

**The map**

- **Sources:** `ops.job_runs`, from the Table job_runs (run_id, job_id, status, duration_mins, avg_retry_secs, dt). It has no formulas and no query, so it stands for the database table.
- **Steps:** CleanRuns, the Power Query "CleanRuns". daily's COUNTIFS and SUMIFS read the Table that query loads, so it is a step: a CTE inside daily's query.
- **Finals:** daily (dt, runs, total_duration_mins), two rows: 2026-09-23 and 2026-09-24.
- **Total Row:** daily (Total Row), one row with runs and total_duration_mins and no label.
- **Parameters and Keys:** none. Nothing is typed over a formula, so no Keys row is needed.

Checked against the sample: 2026-09-23 has 3 clean runs (95, 96, 97; 98 has no status and 99 is TEST), 60 minutes. 2026-09-24 has 4 (101 to 104), 100 minutes. The Total Row gives 7 and 160.

**Hive: daily**

```sql
WITH CleanRuns AS (
  SELECT dt, duration_mins
  FROM ops.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
FROM CleanRuns
GROUP BY dt
```

**Hive: daily (Total Row)**

```sql
WITH CleanRuns AS (
  SELECT dt, duration_mins
  FROM ops.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
),
daily AS (
  SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM CleanRuns
  GROUP BY dt
)
SELECT SUM(runs) AS runs, SUM(total_duration_mins) AS total_duration_mins
FROM daily
```

**Toolbox code**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived,
                              is_not_null, not_equals, statement, sum_of)
from references.ops__job_runs import job_runs

# CleanRuns, the Power Query's step. A workbook's query reads every row of its sample,
# so the read is not bounded by dt: reads_all_partitions=True, as the workbook has no dates to bound by.
clean_runs = derived("CleanRuns", statement(
    SELECT(job_runs.dt, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(is_not_null(job_runs.status), not_equals(job_runs.status, "TEST")),
))

# daily: one row per day, the summary of CleanRuns
s = statement(
    SELECT(clean_runs.dt,
           AS(count_rows(), "runs"),
           AS(sum_of(clean_runs.duration_mins), "total_duration_mins")),
    FROM(clean_runs),
    GROUP_BY(clean_runs.dt),
)

# daily (Total Row): one row, a column per total, no label. It reads the summary alone.
# adds_up=True: the Total Row adds up figures the summary already added up.
by_day = derived("daily", s)
total_row = statement(
    SELECT(AS(sum_of(by_day.runs, adds_up=True), "runs"),
           AS(sum_of(by_day.total_duration_mins, adds_up=True), "total_duration_mins")),
    FROM(by_day),
)
```

**Marks: converted, and said so**

- **The Total row.** The Daily sheet has a row labelled "Total" inside its data range, with SUBTOTAL(109, ...) formulas. Your step 5 says a total typed as a row of its own is read as one more row of data. I have read it as the Total Row instead, because its cells are SUBTOTAL(109) totals. To make Excel agree, delete that typed row and turn on Total Row (Table Design > Total Row). If you want it kept as data, say so: its runs and total cells read daily's own column, which is circular, so they would come out NULL.
- **The Power Query's filter.** `[status] <> null` is `status IS NOT NULL`. M's `<> "TEST"` keeps a null, but the null is already dropped by the first test, so the Hive is `status IS NOT NULL AND status <> 'TEST'`. The blank status in row 98 is dropped, as the M drops it.
- **No COALESCE was needed.** The filter removes the blank status, and avg_retry_secs is not read by any final.
- **COUNTIFS and SUMIFS** over CleanRuns, matched on dt, become a GROUP BY dt with COUNT(*) and SUM. A day with no clean runs would show 0 in Excel and would be missing here. Both sample days have runs, so none is affected.
- **Power Query.** Excel can't save the query, so the M on its sheet is what is converted. The typed-in rows of the CleanRuns Table are the query's output and are not read.
- **Rows are a sample.** No date filter was added; daily covers every day in the sample.
- **The Total Row** is a separate query, reading the summary alone, as file 12 says.

**Refused:** none.

**Left out, and named**

- The typed-in rows of the CleanRuns Table, as the query's output (see above).
- avg_retry_secs, run_id and job_id: no final reads them, so they are not in any query.
- The notes: H1 on CleanRuns says it loads "from Raw", but its M reads job_runs, so the M was used. H2 and A1 on job_runs, A1 on the Power Query sheet, the Steps sheet, and E1 on Daily are read as notes only.
- Parameters and Keys: empty, so nothing to convert.
- Charts and PivotTables: none in this workbook.

**Your file name.** You asked for daily_runs.hql. File 11 says to name each .hql for its Table, which is daily, so daily.hql is the match. Choose which you want. For the Total Row query I suggest daily_total_row.hql.

**What to do next**

1. Take out what you don't want converted: the typed Total row, once Total Row is turned on in Excel.
2. Fill in each `<...>`: none in this conversion. `references/ops__job_runs.py` must be in your Project, from its Table reference.
3. Save daily's query as daily.hql (or daily_runs.hql, if you keep that name), and the Total Row query as daily_total_row.hql.
4. Run the convert Workflow (file 13) on those two files as one batch, with DEV filled in. Its checked code wins where it and this answer differ.
