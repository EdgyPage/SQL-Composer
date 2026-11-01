## Q1

Map

- Sources: job_runs (read for job_id, status and duration_mins; avg_retry_secs and dt are not read by any formula).
- Steps: none.
- Finals: run_report (job_id, runs, failed_runs, avg_duration_mins). It is a summary: its only typed column, job_id, is what its COUNTIFS and AVERAGEIFS match on, so it is a GROUP BY of job_runs. Nothing reads it, so it is a final. It has no Total Row.
- Parameters: none (the sheet's table is empty). Keys: none (no value is typed over a formula, so no Keys row is needed).

Hive, one query for the final run_report:

```sql
SELECT job_id,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(COUNT(CASE WHEN status = 'FAILED' THEN 1 END), 0) AS failed_runs,
  AVG(duration_mins) AS avg_duration_mins
FROM <database>.job_runs
GROUP BY job_id
```

Values typed over a formula: none.

Marks

- run_report is a summary, so its rows are the job_id groups of job_runs. Its typed rows are 1, 2 and 3, which job_runs holds, so the GROUP BY gives the same three rows here. If the warehouse table holds other job_ids, the GROUP BY gives those rows too. Delete them, or add a WHERE on job_id IN (1, 2, 3), if the Table should hold only these three.
- COUNTIFS become COUNT with COALESCE. AVERAGEIFS becomes AVG, left NULL where nothing matches.
- job_runs' formulas read every row of their columns, not one day, so the query reads every day. The Python below says so.
- Row 98 of job_runs has a blank status. The FAILED count skips it, as Excel does, so no COALESCE is put on status.

Refusals: none.

Left alone, and named: the notes outside Tables. These are the Steps sheet's text, Runs A1 ("Copied from ops.job_runs in our warehouse."), Report F1, and the notes in Parameters D1 and Keys D1. There are no charts or PivotTables.

To fill in: `<database>`, in the SQL and in the Python import. The Runs note says ops.job_runs, so the database is probably ops, but fill it in yourself.

Toolbox code, by Copilot files 03 and 04:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, average_of, count_rows, equals,
                              statement)
from references.<database>__job_runs import job_runs

# The workbook's formulas read every row of job_runs, not one day, so every day is read.
s = statement(
    SELECT(
        job_runs.job_id,
        AS(count_rows(), "runs"),
        AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
        AS(average_of(job_runs.duration_mins), "avg_duration_mins"),
    ),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's formulas read every row
    GROUP_BY(job_runs.job_id),
)
```

What to do next

- Take out anything you don't want converted. Nothing in this workbook is marked for removal, but check the job_id rows as noted above.
- Fill in each `<database>`.
- Save the SQL above as a .hql file named for its Table, run_report.hql, and run the convert Workflow on it as one batch (Copilot file 13), with DEV filled in.
- Where the checked code and this reply differ, the checked code wins.
