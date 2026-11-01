## Q1

**Map**

- Sources: `job_runs`, with typed columns run_id, job_id, status, duration_mins, avg_retry_secs and dt. Its A1 note says "Copied from ops.job_runs", so it reads `<database>.job_runs`.
- Steps: none.
- Finals: `job_report` (job_id, runs, failed_runs, avg_duration_mins). Its only typed column is job_id, which its COUNTIFS match on, so it is a summary: a GROUP BY of job_runs by job_id. Nothing reads job_report, so it is a final.
- Parameters and Keys are empty, so there are none.

**Hive for job_report**

```sql
SELECT job_id,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(COUNT(CASE WHEN status = 'FAILED' THEN 1 END), 0) AS failed_runs,
  AVG(duration_mins) AS avg_duration_mins
FROM <database>.job_runs
GROUP BY job_id
```

The GROUP BY gives one row per job_id in job_runs, which is job_id 1, 2 and 3 in the sample.

**Marks, refusals and what was left alone**

- Typed over a formula: none, so no Keys row is needed.
- Blank: job_runs row 98 has a blank status and a blank avg_retry_secs (shown as None). status is read only by COUNTIFS, which skips a blank, so it is not wrapped in COALESCE. avg_retry_secs is read by no formula, so it is left as it is.
- Dates: no filter on dt was added, as no formula filters on dt. The rows are the sample.
- Refused: none.
- Left alone: the note in F1 of the Report sheet ("One row per job: its runs, how many failed, its average minutes."), which sits outside the Table. The text on the Steps sheet is instructions, not a calculation, so it is not converted. The workbook has no charts or PivotTables.
- To fill in: `<database>`. The A1 note says ops, so write `ops`.

**Toolbox code, with `<database>` as ops**

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, average_of, count_rows, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(
        job_runs.job_id,
        AS(count_rows(), "runs"),
        AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
        AS(average_of(job_runs.duration_mins), "avg_duration_mins"),
    ),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's report counts every row of job_runs
    GROUP_BY(job_runs.job_id),
)
```

The Toolbox code leaves out COALESCE, as count_rows never gives NULL after a GROUP BY.

**What to do next**

1. Take out anything you don't want converted.
2. Fill in `<database>` as ops, as the A1 note says.
3. The Toolbox code reads every partition of job_runs, as file 12's example does for a workbook's query. If you want one day only, add `equals(job_runs.dt, "<day>")` to a WHERE and remove `reads_all_partitions=True`.
4. Save the Hive above as job_report.hql, and run the convert Workflow on it as one batch (file 13), with DEV filled in. Where the Hive and the checked Toolbox code differ, the checked code wins.
