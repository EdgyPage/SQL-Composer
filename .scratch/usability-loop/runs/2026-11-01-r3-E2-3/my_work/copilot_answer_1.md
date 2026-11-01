## Q1

**Map**

- Sources: `jobs` (typed: job_id, job_name, team, region; its note in A1 says it was copied from ops.jobs) and `job_runs` (typed: run_id, job_id, status, duration_mins, avg_retry_secs, dt; its note in A1 says it was copied from ops.job_runs).
- Steps: `job_runs`. Its team column is a formula (an XLOOKUP into jobs), and teams reads it, so the table is a step. Its typed columns stand for the source.
- Finals: `teams` (team, runs, total_duration_mins). Its only typed column is team, the column its COUNTIFS and SUMIFS match on, so it is a summary: a GROUP BY of the table it reads, job_runs. Nothing reads it, so it is a final.
- `jobs` is a source read by job_runs' formula, not a final.
- Parameters: none, the sheet's table is empty. Keys: none, the sheet's table is empty, and no value is typed over a formula.
- Total Row: none turned on. Power Query: none. Defined names: none. Charts and PivotTables: none. Refusals: none.

**Marks, converted and said so**

- Teams has three typed teams: data, finance, web. web has no runs, so a GROUP BY alone would drop its row. The Hive lists the three teams and LEFT JOINs the group to them, so web stays with 0 runs and 0 minutes, as Excel gives 0 where nothing matches. The Toolbox code takes its team list from jobs' team column instead, because the Toolbox has no way to write a literal list of rows. In this sample jobs holds the same three teams, so check the list against Teams.
- Run 98 has a blank status and a blank avg_retry_secs. No formula reads either column, so both stay NULL and are not wrapped.

**Left alone, and named**

- The notes in Jobs A1 and Runs A1, Teams E1, and the notes in Parameters D1 and Keys D1.
- The Steps sheet, which is instructions only and holds no Table.

**To fill in**

- `<database>` in the Hive below (four places). The notes say ops, so `<database>` is probably ops.

**Expected result on this sample, to check the Hive against:** data 4 runs and 67 minutes; finance 5 runs and 113 minutes; web 0 runs and 0 minutes.

**Hive, the final teams**

```sql
WITH job_runs AS (
  SELECT r.job_id, r.duration_mins, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
), typed_teams AS (
  SELECT 'data' AS team
  UNION ALL SELECT 'finance'
  UNION ALL SELECT 'web'
)
SELECT t.team,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM typed_teams t
LEFT JOIN (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
) c ON t.team = c.team
```

**Toolbox code, the same final**

The Python imports references/ops__job_runs.py and references/ops__jobs.py, from the ops.job_runs and ops.jobs Table references. If you don't have them yet, add them with the Table reference steps in file 02.

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, SELECT_DISTINCT,
                              count_rows, derived, equals, fill_null, statement, sum_of)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

# Teams has three typed teams, and web has no runs. The Toolbox has no literal rows,
# so the team list comes from jobs' team column, which holds the same three teams in
# this sample: check it against Teams.
team_list = derived("team_list", statement(
    SELECT_DISTINCT(jobs.team),
    FROM(jobs),
))

# The job_runs step: each run with its job's team, the XLOOKUP as a LEFT JOIN.
# The workbook's sample has no date filter, so every partition is read.
job_runs_step = derived("job_runs", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins, jobs.team),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))

per_team = derived("per_team", statement(
    SELECT(job_runs_step.team,
           AS(count_rows(), "runs"),
           AS(sum_of(job_runs_step.duration_mins), "total_duration_mins")),
    FROM(job_runs_step),
    GROUP_BY(job_runs_step.team),
))

# Teams: one row per team, 0 where no run has it, as Excel's COUNTIFS and SUMIFS give 0.
s = statement(
    SELECT(team_list.team,
           AS(fill_null(per_team.runs, 0), "runs"),
           AS(fill_null(per_team.total_duration_mins, 0), "total_duration_mins")),
    FROM(team_list),
    LEFT_JOIN(per_team, ON=equals(per_team.team, team_list.team)),
)
```

**What to do next**

- Take out anything you don't want converted. Nothing here needs a value typed over a formula, a Keys row or a Parameters row.
- Fill in `<database>` in the Hive.
- Save the Hive as teams.hql, named for its Table, and run the convert Workflow on it, with file 13 loaded, DEV filled in. Where the Hive and the checked Toolbox code differ, the checked code wins.
