## Q1

**Map**

- Sources: `job_runs`, the workbook's Table of six typed columns, read as the database table `<database>.job_runs`. The note on its sheet says ops.job_runs, so fill in `ops`.
- Steps: `CleanRuns`, the Table the Power Query loads, which `daily`'s formulas read. Its query, CleanRuns, reads `job_runs` and becomes a CTE inside `daily`'s query. The typed-in rows are not converted; the query is.
- Finals:
  - `daily`, saved as `mart_dev.daily_runs`, giving `dt`, `runs`, `total_duration_mins`. Its only typed column is `dt`, which its COUNTIFS and SUMIFS match on, so it is a summary: a GROUP BY of `CleanRuns`.
  - `daily (Total Row)`: one row, a column for `runs` and one for `total_duration_mins`, no label. It is a query of its own, not a saved table.
- Parameters and Keys are both empty, so there are none.

**Typed over a formula:** none. No Keys row is needed.

**Marks**

- CleanRuns: its typed-in rows agree with its query on this sample. The query drops row 98 (blank status) and row 99 (TEST), which leaves 95 to 97 and 101 to 104, as the Table holds. Table.TransformColumnTypes gives nothing in Hive.
- Blank: row 98 of job_runs has a blank status and a blank avg_retry_secs. Excel's null status and Hive's NULL status are the same, and the query's filter removes that row, so no COALESCE is written for it. avg_retry_secs is read by no final, so it is not carried into any query.
- M's `[status] <> "TEST"` keeps a null, as Hive's `<>` doesn't, so it is written `(status <> 'TEST' OR status IS NULL)`. M's `[status] <> null` is `status IS NOT NULL`.
- `runs` (COUNTIFS) and `total_duration_mins` (SUMIFS) each take COALESCE, as Excel gives 0 where nothing matches.
- SUBTOTAL(109, ...) on the Total Row is a SUM, written as SUM over the summary's rows.
- The workbook has no date filter, so the Hive reads every day. The Toolbox read takes every partition for the same reason; see the comment in the Toolbox code.

**Refused:** none.

**Left alone, and named:** the text on the Steps sheet, the Parameters and Keys sheets' notes (D1), the "Copied from ops.job_runs" note on job_runs (A1), the Power Query sheet's text (A1 and A3), the note on Daily (E1), and the "Total" label in the Total Row (it is a label, not a dt value, so it gives no column).

**To fill in:** `<database>` is `ops` in both the Hive and the Toolbox import. The Table reference `references/ops__job_runs.py` must exist in the Project (file 02).

```sql
WITH clean_runs AS (
  SELECT dt, duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
)
SELECT dt,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(SUM(duration_mins), 0) AS total_duration_mins
FROM clean_runs
GROUP BY dt
```

```sql
WITH clean_runs AS (
  SELECT dt, duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND (status <> 'TEST' OR status IS NULL)
),
daily AS (
  SELECT dt,
    COALESCE(COUNT(*), 0) AS runs,
    COALESCE(SUM(duration_mins), 0) AS total_duration_mins
  FROM clean_runs
  GROUP BY dt
)
SELECT SUM(runs) AS runs, SUM(total_duration_mins) AS total_duration_mins
FROM daily
```

Toolbox code, by files 03, 04 and 05:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, any_of, count_rows, derived,
                              fill_null, is_not_null, is_null, not_equals, statement, sum_of)
from references.ops__job_runs import job_runs

# clean_runs: the Power Query CleanRuns, a step that daily reads as a Derived table.
# The workbook's query has no date filter, so it reads every partition (file 12's example).
clean_runs = derived("clean_runs", statement(
    SELECT(job_runs.dt, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(is_not_null(job_runs.status),
          any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
))

# daily: a summary, one row per dt, a GROUP BY of clean_runs. Saved as mart_dev.daily_runs.
daily = statement(
    SELECT(clean_runs.dt,
           AS(fill_null(count_rows(), 0), "runs"),
           AS(fill_null(sum_of(clean_runs.duration_mins), 0), "total_duration_mins")),
    FROM(clean_runs),
    GROUP_BY(clean_runs.dt),
)

# daily (Total Row): one row, a column per total, no label. Not saved; run it to read the total.
daily_rows = derived("daily_rows", daily)
daily_total = statement(
    SELECT(AS(sum_of(daily_rows.runs), "runs"),
           AS(sum_of(daily_rows.total_duration_mins), "total_duration_mins")),
    FROM(daily_rows),
)
```

The convert Workflow's names cell and its first step, with DEV filled in. Check that DEV in admin/databases.py is mart_dev, and that the copy's name in convert's report is mart_dev.daily_runs; if the report names the table differently, change RENAME's key to match.

```python
NAME = "daily_runs"
FILES = ["daily.hql"]
HIVE = None
DATABASE = "mart_dev"
RENAME = {"mart_dev.daily": "daily_runs"}
STAGING = {}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

**What to do**

1. Take out anything you don't want converted. The Total Row's query is not a .hql file, so leave it out of FILES.
2. Fill in `<database>` as `ops`, and check that the Table reference for ops.job_runs is in references/.
3. Save the `daily` query above as daily.hql in admin/workflows/convert/, beside the convert notebook. Run `run_query(daily_total, query)` after `from warehouse import query` to read the Total Row. Do not save it.
4. Run the convert Workflow (file 13) as one batch, with the names cell and the convert cell above. Then, in words: answer the table's open Decisions in the decisions cell (its location and key are yours to answer), write the answers, create the table in dev, skip the seed step because the table reads no table it writes, write it in dev, and compare it with its original.
5. Where the checked code from convert differs from the Toolbox code above, the checked code wins.
