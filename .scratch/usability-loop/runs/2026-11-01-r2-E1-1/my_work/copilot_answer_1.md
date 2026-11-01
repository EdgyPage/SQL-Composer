## Q1

**Map**

- Sources: `job_runs`, read as `ops.job_runs`. The final uses its `job_id`, `status` and `duration_mins` columns.
- Steps: none.
- Finals: `run_report` (job_id, runs, failed_runs, avg_duration_mins). It is a summary: one row per job_id, a GROUP BY of `job_runs`. Nothing reads it, so it is one query.
- Parameters and Keys: none. Both sheets are empty.

**Marks**

- Blank: run 98 has a blank `status`. It is read by the `FAILED` count, which is an -IFS form, so it is left as NULL and not wrapped in COALESCE. The `FAILED` count skips it, as COUNTIFS does.
- COUNTIFS gives 0 where nothing matches, so `runs` and `failed_runs` are wrapped in COALESCE. AVERAGEIFS is left NULL where nothing matches.
- Nothing was typed over a formula, so no Keys row is needed.
- No Table has a Total Row.
- The job_id rows come from `job_runs`. A job with no runs in `job_runs` gets no row, unlike a row typed by hand in `run_report`.

**Refused**

- None. Every formula converts.

**Left alone**

- The Steps sheet (instructions), the note in Runs A1, the note in Report F1, and the notes in Parameters D1 and Keys D1.
- `run_id`, `avg_retry_secs` and `dt` of `job_runs`: no formula reads them, so the final leaves them out.

**To fill in**

- Nothing. The database is `ops` in both the Hive and the Toolbox code, as you said.

**Hive, one query for `run_report`**

```sql
WITH by_job AS (
  SELECT job_id, COUNT(*) AS runs, AVG(duration_mins) AS avg_duration_mins
  FROM ops.job_runs
  GROUP BY job_id
),
failed_by_job AS (
  SELECT job_id, COUNT(*) AS failed_runs
  FROM ops.job_runs
  WHERE status = 'FAILED'
  GROUP BY job_id
)
SELECT b.job_id,
  COALESCE(b.runs, 0) AS runs,
  COALESCE(f.failed_runs, 0) AS failed_runs,
  b.avg_duration_mins AS avg_duration_mins
FROM by_job b
LEFT JOIN failed_by_job f ON b.job_id = f.job_id
```

**Toolbox code, the same table in one Statement**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, average_of, count_rows, equals,
                              statement)
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id,
           AS(count_rows(), "runs"),
           AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
           AS(average_of(job_runs.duration_mins), "avg_duration_mins")),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's Report counts every row of job_runs
    GROUP_BY(job_runs.job_id),
)
```

The Toolbox code needs `ops__job_runs` in your references/ folder. If you don't have that Table reference yet, add it first (file 02).

**What to do next**

1. Save the Hive query as `run_report.hql`. File 11 names each final's file for its Table, so use the Table's name rather than `job_run_report.hql`. If you want the other name, say so, but the batch convert may match the file to its Table.
2. Take out anything you don't want converted. Nothing else needs changing.
3. Run the convert Workflow on it as one batch (file 13), with DEV filled in. If the Hive and the Toolbox code differ, the convert Workflow's checked code wins.
