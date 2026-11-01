## Q1

**Map**

- Sources: `job_runs`, read as `<database>.job_runs` (columns run_id, job_id, status, duration_mins, avg_retry_secs, dt). Its note says it was copied from ops.job_runs, so `<database>` is probably `ops`. The final reads only dt, duration_mins and status; run_id, job_id and avg_retry_secs are read by no final, so the SQL leaves them out.
- Steps: `CleanRuns`, a Table loaded by the Power Query CleanRuns from job_runs. daily's formulas read this Table, so it is a step: its query becomes the CTE `CleanRuns` inside daily's query.
- Finals: `daily`, with columns dt, runs, total_duration_mins, in that order. Its only typed column, dt, is what its COUNTIFS and SUMIFS match on, so daily is a summary: a GROUP BY of CleanRuns. Nothing reads daily, so it is a final.
- Total Row of daily: SUBTOTAL(109, ...) on runs and on total_duration_mins, both sums. It needs no query of its own (see below).
- Typed over a formula: none. Keys and Parameters are empty.
- Refused: none.
- Left alone: the notes on the Steps, Parameters, Keys and Power Query sheets, which are text, not Tables or formulas. No charts or PivotTables.

Marks:

- The query's `[status] <> null` becomes `status IS NOT NULL`. Its `[status] <> "TEST"` would keep a null in M, but the IS NOT NULL test comes first, so `status <> 'TEST'` alone is right here and the `OR status IS NULL` part is not needed.
- The Power Query is not saved in the workbook, and the CleanRuns Table holds typed-in rows. I converted from the M on the Power Query sheet, not from the typed rows. The typed rows (95, 96, 97, 101, 102, 103, 104) are what the query gives on this sample, so the two agree.
- Row 98 has a blank status. The query drops it, so the Hive drops it too.
- dt is text already in yyyy-mm-dd form, so it is compared as it is.

Hive for the final daily:

```sql
WITH CleanRuns AS (
  SELECT dt, duration_mins
  FROM <database>.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
FROM CleanRuns
GROUP BY dt WITH ROLLUP
```

**Total Row**

daily's Total Row needs no query of its own, so it has no sql block of its own. `GROUP BY dt WITH ROLLUP` adds it as one more row, with dt NULL, holding the totals of runs and total_duration_mins. On this sample that row is runs 7 and total_duration_mins 160 (12 + 18 + 30 + 10 + 20 + 30 + 40). What to do with it:

- To keep the total in the saved table, leave `WITH ROLLUP` in. Read the total with `WHERE dt IS NULL`. The sample has no NULL dt in CleanRuns, so that row is the total alone.
- To leave it out, delete `WITH ROLLUP`, and the saved table holds the two day rows only.

Toolbox code, from files 03, 04 and 05:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived,
                              is_not_null, not_equals, rollup, statement, sum_of)
from references.<database>__job_runs import job_runs

# The workbook's Power Query reads every row of job_runs, so this reads every partition.
clean_runs = derived("clean_runs", statement(
    SELECT(job_runs.dt, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),
    WHERE(is_not_null(job_runs.status), not_equals(job_runs.status, "TEST")),
))

# rollup adds the Total Row as one row, with dt NULL.
s = statement(
    SELECT(clean_runs.dt, AS(count_rows(), "runs"),
           AS(sum_of(clean_runs.duration_mins), "total_duration_mins")),
    FROM(clean_runs),
    GROUP_BY(rollup(clean_runs.dt)),
)
```

Next steps: take out what you don't want, fill in each `<database>`, save the Hive as daily.hql (named for its Table) and run the convert Workflow on it as one batch (file 13), with DEV filled in. Where the checked code and this Hive differ, the checked code wins.
