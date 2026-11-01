## Q1

**Map**

- Sources: `job_runs`, which is `ops.job_runs` (your message names it, and the sheet's note says it was copied from there). Its Table reference is `references/ops__job_runs.py`. The query reads the columns the final uses: job_id, status and duration_mins. run_id, avg_retry_secs and dt are not read by any formula.
- Steps: none. No Table or query is read by another before the final, so there is no CTE.
- Finals: `run_report`, which becomes mart_dev.job_run_report, with the columns job_id, runs, failed_runs and avg_duration_mins. Its only typed column is job_id, the column its COUNTIFS and AVERAGEIFS match on, so it is a summary: a GROUP BY of job_runs by job_id.
- Typed over a formula: none. The Keys and Parameters sheets are empty, so there is no Keys row to use.
- Power Query, Total Rows, PivotTables and charts: none in this workbook. Files 12, 04 and 05 are not needed for it, since there is no query, no Total Row, no join and no window.

**Marks**

- Blank: row 98 has a blank status (shown as None). COUNTIFS skips a blank, as Excel does, so it is not wrapped in COALESCE. Row 98's blank avg_retry_secs is not read, so nothing is wrapped for it.
- Case: Excel's COUNTIFS matches "FAILED" whatever its case, and Hive's `=` does not. The sample holds only upper case, so `status = 'FAILED'` is kept. If the table also holds values such as 'failed', write `UPPER(status) = 'FAILED'` instead.
- Sample dates: the rows are for 2026-09-23 and 2026-09-24. Nothing filters on date, because no formula does, so no date filter is added.
- The job ids 1, 2 and 3 typed in the Report sheet are the groups, not a filter. The query covers every job_id in ops.job_runs. A job with no rows at all gets no row here, where a typed row would show 0 in Excel.

**Refusals:** none.

**Left alone:** none. The sheets' notes (Steps, Report's F1 and job_runs' H1) are text, not converted.

**Left out:** avg_retry_secs, because no formula reads it.

**To fill in:** nothing is left. ops and mart_dev come from your message. The code assumes `references/ops__job_runs.py` exists in your Project. If it doesn't, add it first with file 02, from its import line and columns, since your message doesn't give them.

**Hive**

```sql
SELECT job_id,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(COUNT(CASE WHEN status = 'FAILED' THEN 1 END), 0) AS failed_runs,
  AVG(duration_mins) AS avg_duration_mins
FROM ops.job_runs
GROUP BY job_id
```

**Toolbox code**

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
    # The workbook's formulas read every row of job_runs and give no date.
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

The Toolbox code uses file 03 only. `reads_all_partitions=True` is there because the workbook's COUNTIFS and AVERAGEIFS read the whole table. If you want one day rather than every partition, drop that opt-out and add `WHERE(equals(job_runs.dt, "2026-09-24"))` after FROM.

**What to do next**

1. Take out anything you don't want converted. Nothing here needs taking out, since avg_retry_secs is already left out.
2. Save the Hive above as `run_report.hql`, named for its Table, and run the convert Workflow (file 13) on it as one batch, with DEV filled in, so it writes mart_dev.job_run_report. Check that the Workflow names the target job_run_report, since the Table is called run_report.
3. Where the Hive and the Toolbox code differ, the convert Workflow's checked code wins.
