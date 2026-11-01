## Q1

**Map**

- Sources: `job_runs`, a typed Table, so it stands for `<database>.job_runs`. The query reads its columns `job_id`, `status` and `duration_mins`. `run_id`, `avg_retry_secs` and `dt` are not read by any formula, so the Hive leaves them out.
- Steps: none.
- Finals: `run_report`. Its only typed column, `job_id`, is what its COUNTIFS and AVERAGEIFS match on, so it is a summary: a GROUP BY of `job_runs`. Nothing reads it, so it is a final. Its columns, in its Table's order: `job_id`, `runs`, `failed_runs`, `avg_duration_mins`.
- Parameters: none. Keys: none (the sheet is empty).
- Values typed over a formula: none.

**Marks, and what each means**

- Blank: `job_runs` row 98 has a blank `status`. `failed_runs` is a COUNTIFS with "FAILED", which skips a blank as Excel does, so no COALESCE wraps `status`.
- Every partition: the workbook counts every row of both days in its sample. The Toolbox code reads all partitions with `reads_all_partitions=True`, as a workbook's query does, and says why in a comment. If you want one day only, bound `job_runs` with `equals(job_runs.dt, ...)` and remove that opt-out.
- AVERAGEIFS became AVG and is left NULL where a job has no runs, as Excel gives an error there rather than a 0.
- Missing rows: `run_report` has typed rows for jobs 1, 2 and 3. The GROUP BY gives one row per `job_id` found in `job_runs`. A job with no runs would show a 0 row in Excel and is absent here. All three jobs have runs in the sample, so the results match.

**Refusals:** none.

**Left alone, and named:** no charts. Cells outside a Table, left alone: the text of the Steps, Parameters and Keys sheets, the H1 note on `job_runs` ("Copied from ops.job_runs in our warehouse") and the F1 note on `run_report`.

**To fill in:** `<database>`. The H1 note says `ops.job_runs`, so if your database is `ops`, `<database>` is `ops`.

**Hive for the final `run_report`** (one query, no CTE, as it has no steps):

```sql
SELECT job_id,
  COALESCE(COUNT(*), 0) AS runs,
  COALESCE(SUM(CASE WHEN status = 'FAILED' THEN 1 END), 0) AS failed_runs,
  AVG(duration_mins) AS avg_duration_mins
FROM <database>.job_runs
GROUP BY job_id
```

**Toolbox code, to make `run_report` a Saved table** (its Table notebook's logic cell, file 06):

```python
# logic
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, Clause, Statement,
                              average_of, count_rows, create_table, equals, statement)
from references.<database>__job_runs import job_runs
from references.<database>__run_report import run_report

PARTITIONED_BY = []  # run_report is not partitioned; it reads every row, so no READS


def create() -> Statement:
    return create_table(run_report, may_exist=True)


def rows() -> list[Clause]:
    return [
        SELECT(job_runs.job_id,
               AS(count_rows(), "runs"),
               AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed_runs"),
               AS(average_of(job_runs.duration_mins), "avg_duration_mins")),
        # the workbook counts every row of every day, so this reads every partition
        FROM(job_runs, reads_all_partitions=True),
        GROUP_BY(job_runs.job_id),
    ]


def preview() -> Statement:
    return statement(*rows())


def write() -> Statement:
    return statement(INSERT_OVERWRITE(run_report), *rows())
```

**Next steps**

1. Take out anything you don't want converted. Fill in each `<database>`.
2. Create the Table with `project.new_table("<database>.run_report")` in the new_table Workflow (admin/workflows/new_table/new_table.ipynb, file 14). That makes its Table notebook and a stand-in Table reference, which the import line above needs. Its Key is `job_id`, since the GROUP BY gives one row per `job_id`; answer that in the Workflow's decisions cell.
3. Save the Hive above as `run_report.hql`, and run the convert Workflow on it (file 13) as one batch, with DEV filled in. Where the Toolbox's checked code and this code differ, the checked code wins.
