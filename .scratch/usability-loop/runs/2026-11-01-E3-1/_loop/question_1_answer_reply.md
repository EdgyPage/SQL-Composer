## Q1

**Map**

- Sources: `job_runs`, the Raw sheet's Table. Its note says it is copied from `ops.job_runs`. The finals read its `dt`, `duration_mins` and `status` columns.
- Steps: `CleanRuns`, the Clean sheet's Table. It is loaded by Power Query "CleanRuns", which reads `job_runs` and keeps the rows whose status is not blank and not TEST. The Daily formulas read it, so it is a step, written as a CTE.
- Finals: `daily_runs`, with the columns `dt`, `runs`, `total_duration_mins`, in the Table's order. It is a summary: its only typed column, `dt`, is what its COUNTIFS and SUMIFS match on, so it is a GROUP BY of `CleanRuns`.
- Total Row: `daily_runs (Total Row)` needs no query of its own. Its totals are SUBTOTAL(109), which are sums, so the summary's query ends `GROUP BY dt WITH ROLLUP`. The rollup adds the total as one more row, with `dt` NULL. So there is one sql block for `daily_runs`, and it holds the Total Row.
- Parameters: none. The Table is empty.
- Keys: none. The Table is empty, so the Keys rule does not apply.
- Typed over a formula: none.
- Refused: none. COUNTIFS becomes COUNT(*), SUMIFS becomes SUM over the GROUP BY, and SUBTOTAL(109) becomes the rollup.
- Left alone: the Steps sheet's instructions and the notes in cells D1, E1 and H1. They are text, not Tables.

**Marks, and what to check**

- Blank cells: Raw row 98 has a blank `status` and a blank `avg_retry_secs`. No formula reads `status` or `avg_retry_secs`, and the CleanRuns query drops row 98 as the Power Query does, so no COALESCE is written. `avg_retry_secs` is not used by any final, so it is left out of the query.
- Power Query `[status] <> null` becomes `status IS NOT NULL`, and `[status] <> "TEST"` becomes `status <> 'TEST'`. The first test already removes the null row, so M's null-keeping `<>` makes no difference here.
- The Power Query's Typed step (type changes) becomes nothing in Hive.
- COALESCE is left out of the sums and counts. A day's group exists only where it has rows, so no group is empty.
- Days come from the data. Daily lists the days the GROUP BY finds. If a day had no clean runs and was typed into Daily, Excel would show 0 for it, but the Hive does not list it.
- The Total Row's label "Total" is not a value. In the output, its row has `dt` NULL.
- Partitions: the query reads every day, since Daily has every day, so it has no date bound. If `ops.job_runs` is partitioned by `dt`, the Toolbox needs the opt-out shown below.

**Fill in**

- `<database>`: `ops`, from the Raw sheet's note (`ops.job_runs`).

**Hive for `daily_runs`** (save as `daily_runs.hql`)

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

**Toolbox code** (by files 03, 04 and 05; it needs the `ops.job_runs` Table reference from file 02)

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived,
                              is_not_null, not_equals, rollup, statement, sum_of)
from references.ops__job_runs import job_runs

# The Clean sheet's CleanRuns: no blank status, and no TEST runs.
clean_runs = derived("CleanRuns", statement(
    SELECT(job_runs.dt, job_runs.duration_mins),
    FROM(job_runs, reads_all_partitions=True),  # daily_runs has every day, so it reads every day
    WHERE(is_not_null(job_runs.status), not_equals(job_runs.status, "TEST")),
))

# The Daily sheet: one row per day, then the Total row, which the rollup adds with dt NULL.
s = statement(
    SELECT(clean_runs.dt, AS(count_rows(), "runs"),
           AS(sum_of(clean_runs.duration_mins), "total_duration_mins")),
    FROM(clean_runs),
    GROUP_BY(rollup(clean_runs.dt)),
)
```

**Next steps**

1. Open `daily_runs.hql` and fill in `<database>` with `ops`.
2. Take out anything you don't want converted, then save the file.
3. Run the convert Workflow on it as one batch, following file 13, with the Dev database filled in. Where the Workflow's checked code differs from the Python above, the checked code wins.
