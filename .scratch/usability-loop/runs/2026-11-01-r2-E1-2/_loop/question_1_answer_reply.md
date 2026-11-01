## Q1

Map, by file 11:

- Sources: job_runs, read as `ops.job_runs`. Its note in A1 says it was copied from ops.job_runs.
- Steps: none. No formula reads another formula's column.
- Finals: run_report (job_id, runs, failed_runs, avg_duration_mins). Its only typed column is job_id, which its COUNTIFS and AVERAGEIFS match on, so it is a summary: one GROUP BY job_id over job_runs. Nothing reads it, so it is a final, with one query.
- Parameters and Keys: both are empty, so there are none.
- Total Rows: none.

Values typed over a formula: none. Every row of run_report has the same formulas in each column, so no Keys row is needed.

Marks, converted and said so:

- The COUNTIFS and AVERAGEIFS over job_runs become the GROUP BY itself. runs is COUNT(*), failed_runs is a count of the rows whose status is FAILED, and avg_duration_mins is AVG. Both counts are wrapped in COALESCE(.., 0), as file 11 gives for COUNTIFS. AVERAGEIFS is left NULL where nothing matches.
- Blank: row 98 of job_runs has a blank status. The status test is inside an -IFS form, so it is not wrapped; the blank does not count as FAILED, as in Excel. Row 98 also has a blank avg_retry_secs, but no formula reads that column, so it is left out of the query.
- The workbook's formulas read every row of job_runs, so the Hive reads every row too. No date filter was added.

Refusals: none.

Left alone, and named: the Steps sheet's text (no Table on it); the cell notes outside a Table, job_runs A1, run_report F1, Parameters D1 and Keys D1. The workbook has no chart and no PivotTable.

Filled in: `<database>` is ops. No `<...>` is left.

Name: you asked for job_run_report.hql. The workbook's Table is run_report, and file 11 says to name each final's .hql for its Table. Either save the file as run_report.hql, or rename the Table to job_run_report (Table Design > Table Name) before converting, so the two match. Your choice.

Hive, the final run_report:

```sql
SELECT job_id,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(COUNT(CASE WHEN status = 'FAILED' THEN 1 END), 0) AS failed_runs,
  AVG(duration_mins) AS avg_duration_mins
FROM ops.job_runs
GROUP BY job_id
```

Toolbox code, with `references.ops__job_runs` from your Project's references/ folder (file 02):

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, average_of, count_rows, equals,
                              fill_null, statement)
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id,
           AS(fill_null(count_rows(), 0), "runs"),
           AS(fill_null(count_rows(where=equals(job_runs.status, "FAILED")), 0), "failed_runs"),
           AS(average_of(job_runs.duration_mins), "avg_duration_mins")),
    # the workbook's COUNTIFS and AVERAGEIFS read every row of job_runs, so no partition bound
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

Next steps: take out anything you don't want in the final. Save the Hive above as the .hql file named as you choose (see Name). Run the convert Workflow (file 13) on it as one batch, with your Dev database filled in. Where the Workflow's checked code differs from this Hive, its checked code wins.
