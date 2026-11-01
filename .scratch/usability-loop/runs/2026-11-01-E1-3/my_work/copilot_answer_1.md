## Q1

**Map**

- **Sources:** `job_runs`, read as `ops.job_runs` (the database you named). Its typed columns are run_id, job_id, status, duration_mins, avg_retry_secs and dt. The final reads only job_id, status and duration_mins.
- **Steps:** none. No Table or query is read by another Table or query.
- **Finals:** `run_report`, one query, which you will save as job_run_report. Its columns, in order: job_id, runs, failed_runs, avg_duration_mins. Its only typed column is job_id, which its COUNTIFS and AVERAGEIFS match on, so it is a summary: a GROUP BY job_id over job_runs.
- **Typed over a formula:** none.
- **Keys:** none (no row, as nothing is typed over). **Parameters:** none (the Table is empty).
- **Marks:**
  - `runs`: COUNTIFS becomes COUNT(*). No COALESCE is needed, as every group holds at least one row.
  - `failed_runs`: COUNTIFS with "FAILED" becomes COALESCE(SUM(CASE WHEN status = 'FAILED' THEN 1 END), 0), as Excel shows 0 where no run failed.
  - `avg_duration_mins`: AVERAGEIFS becomes AVG, left NULL where a group is empty (none here).
  - Blank: job_runs row 98 (job 2, dt 2026-09-23) has a blank status. The FAILED test skips it, as COUNTIFS does, so it needs no wrap. job_id and duration_mins have no blanks.
  - Days: the sample holds 2026-09-23 and 2026-09-24. No formula filters a date, so the query reads every day, and filters nothing.
  - Rows: run_report's rows are job_ids 1, 2 and 3, the same three job_runs holds, so the query gives the same rows. A job_id in run_report with no run in job_runs would be missing from the query, where Excel shows 0 runs. Check this when you compare the query with the workbook.
- **Refused:** none.
- **Left alone, and named:** the notes outside Tables, the text on the Steps sheet, H1 on job_runs ("Copied from ops.job_runs...") and F1 on run_report.
- **To fill in:** none. The database is `ops`, as you named it.

```sql
SELECT job_id,
  COUNT(*) AS runs,
  COALESCE(SUM(CASE WHEN status = 'FAILED' THEN 1 END), 0) AS failed_runs,
  AVG(duration_mins) AS avg_duration_mins
FROM ops.job_runs
GROUP BY job_id
```

Toolbox code, with files 03, 04 and 05:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, average_of, count_rows, equals,
                              statement)
from references.ops__job_runs import job_runs

s = statement(
    SELECT(
        job_runs.job_id,
        AS(count_rows(), "runs"),
        AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
        AS(average_of(job_runs.duration_mins), "avg_duration_mins"),
    ),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's formulas read every row, both days
    GROUP_BY(job_runs.job_id),
)
```

Next steps:

1. Take out anything you don't want. Nothing here needs filling in.
2. Check that `references/ops__job_runs.py` has the column duration_mins and the partition dt, with Key run_id. The example line in your message lists no duration_mins. If it is missing, add the Table reference again from the warehouse (file 02).
3. Save the query as `job_run_report.hql`, the name it will be saved under. Then run the convert Workflow on it as one batch, with DEV filled in (file 13, in a new chat). Where its checked code and this one differ, the checked code wins.
4. To read the result now, run `run_query(s, query)` after `from warehouse import query`.
