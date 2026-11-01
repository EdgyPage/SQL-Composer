## Q1

**Map**

- **Sources:** job_runs, which is ops.job_runs (the note in A1 of the job_runs sheet says so). Its typed columns are run_id, job_id, status, duration_mins, avg_retry_secs and dt. The final reads only job_id, status and duration_mins.
- **Steps:** none.
- **Finals:** job_report, as you asked, job_run_report: job_id, runs, failed_runs, avg_duration_mins. Its only typed column is job_id, which its COUNTIFS match on, so it is a summary: a GROUP BY of job_runs by job_id. Nothing reads it, so it is a final. Its three rows (1, 2, 3) all appear in job_runs.
- **Parameters:** none, the sheet is empty. **Keys:** none, the sheet is empty.
- **Typed over a formula:** none. Every formula cell in job_report is a formula.
- **Total Row:** none on job_report.

**Marks**

- **Blank:** job_runs row 98 has a blank status. The formulas read status only inside COUNTIFS, which skips a blank, so it is not wrapped. Its blank avg_retry_secs is read by no formula and is left out of the query.
- **Zero where nothing matches:** runs and failed_runs are wrapped in COALESCE, as Excel gives 0 where nothing matches. avg_duration_mins is left NULL where nothing matches, as AVERAGEIFS does.
- **Whole table:** the formulas count every row of job_runs, with no date filter, so the query has no date filter either. The sample's two days stay as they are.

**Refusals:** none.

**Left alone, and named:** the Steps sheet (instructions, not a Table), and the cells outside a Table: A1 and H2 on job_runs, D1 on Parameters, D1 on Keys and F1 on Report.

**Hive**

Save this as job_run_report.hql.

```sql
SELECT r.job_id,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(COUNT(CASE WHEN r.status = 'FAILED' THEN 1 END), 0) AS failed_runs,
  AVG(r.duration_mins) AS avg_duration_mins
FROM <database>.job_runs r
GROUP BY r.job_id
```

**Toolbox code**

Files 04 and 05 are not needed, as there is no join, window or subtotal.

```python
from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, average_of, count_rows, equals, statement
from references.ops__job_runs import job_runs

job_run_report = statement(
    SELECT(
        job_runs.job_id,
        AS(count_rows(), "runs"),
        AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
        AS(average_of(job_runs.duration_mins), "avg_duration_mins"),
    ),
    # the workbook's COUNTIFS and AVERAGEIFS count every row of job_runs, so no day is bounded
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
```

**What to do next**

1. Take out anything you don't want converted.
2. Fill in each `<database>`, which is the Dev database for the source. The Hive source reads ops.job_runs, so write your Dev database's name there.
3. Save the Hive as job_run_report.hql, named for the Table you asked for.
4. If the Project has no references/ops__job_runs.py yet, add it first (file 02), since the Toolbox code imports it.
5. Run the convert Workflow on job_run_report.hql as one batch (file 13), with DEV filled in. Where its checked code and this answer differ, the checked code wins.

If you want one day of job_runs rather than every day, say which day, and the Toolbox code will bound it on dt. I have not guessed one.
