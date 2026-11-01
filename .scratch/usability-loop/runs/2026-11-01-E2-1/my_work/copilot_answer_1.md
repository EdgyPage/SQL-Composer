## Q1

**Map**

- Sources: `jobs` (typed columns job_id, job_name, team, region) is `ops.jobs`. `job_runs` (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt) is `ops.job_runs`. Its `team` column is a formula, not a source column.
- Steps: `job_runs`. It has a formula (`team`, an XLOOKUP into jobs) and `teams` reads it, so it becomes a CTE inside the final's query.
- Finals: `teams`, which becomes `mart_dev.team_report`, with the columns team, runs, total_duration_mins. `teams` is a summary (its only typed column is team, matched by its COUNTIFS and SUMIFS), so it is a GROUP BY of the `job_runs` step, with the team list joined on so every team row is kept.
- Parameters: none (the sheet's Table is empty). Keys: none (the sheet's Table is empty), so no typed-over value needs a Keys row.
- Typed over a formula: none found. Every formula in `job_runs` and `teams` is the same in each row of its column.

**Marks, converted and said so**

- `teams` has a `web` row. No job_runs row has team web (its only job, 4, has no runs in the sample), so Excel gives 0 runs and 0 minutes. A plain GROUP BY would drop that row, so the Hive takes the teams from a list and joins the runs onto it.
- COUNTIFS becomes a count of the matched `run_id`, not COUNT(*), so a team with no runs counts 0, not 1.
- SUMIFS where nothing matches becomes COALESCE(..., 0), as Excel gives 0.
- XLOOKUP becomes a LEFT JOIN on job_id, then `j.team`. A job_id with no jobs row gives NULL where Excel shows #N/A.
- Blank cells: run 98's status and avg_retry_secs are blank. No formula reads either, so both stay NULL and are not wrapped in COALESCE.
- The team list comes from typed values in the workbook. The Toolbox has no typed list, so its code (below) takes the distinct teams of ops.jobs instead; in this sample that is the same three teams.

**Refused:** none.

**Left alone, and named:** the text on the Steps, Parameters and Keys sheets; the notes in jobs!F1, job_runs!I1 and teams!E1, which sit outside a Table.

**Check against the workbook:** data 4 runs, 67 minutes; finance 5 runs, 113 minutes; web 0 runs, 0 minutes. Run 99 (status TEST) is counted, as the workbook does not filter it.

**To fill in:** nothing. The names are yours.

**Hive**, saved as `team_report.hql`:

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt, j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
),
team_keys AS (
  SELECT 'data' AS team
  UNION ALL SELECT 'finance'
  UNION ALL SELECT 'web'
)
SELECT k.team,
  COUNT(jr.run_id) AS runs,
  COALESCE(SUM(jr.duration_mins), 0) AS total_duration_mins
FROM team_keys k
LEFT JOIN job_runs jr ON jr.team = k.team
GROUP BY k.team
```

**Toolbox code**, with files 03, 04 and 05:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, SELECT_DISTINCT,
                              count_distinct, derived, equals, fill_null, statement, sum_of)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

# The job_runs step: each run with its job's team (the XLOOKUP).
# The workbook's SUMIFS and COUNTIFS read every row, so the opt-out is kept with this comment.
runs_with_team = derived("runs_with_team", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt, jobs.team),
    FROM(job_runs, reads_all_partitions=True),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))

# The team list: typed in the workbook; here the distinct teams of ops.jobs (see the map).
team_list = derived("team_list", statement(
    SELECT_DISTINCT(jobs.team),
    FROM(jobs),
))

# The final, teams: one row per team, 0 runs and 0 minutes where none match.
s = statement(
    SELECT(team_list.team,
           AS(count_distinct(runs_with_team.run_id), "runs"),
           AS(fill_null(sum_of(runs_with_team.duration_mins), 0), "total_duration_mins")),
    FROM(team_list),
    LEFT_JOIN(runs_with_team, ON=equals(runs_with_team.team, team_list.team)),
    GROUP_BY(team_list.team),
)
```

**What to do next**

1. Check that the Table references for `ops.jobs` and `ops.job_runs` are in your Project's references/ folder. If they are not, add them with `project.add_references(["ops.jobs", "ops.job_runs"], query=query)`. That call reaches the warehouse, so you run it.
2. Set DEV to `mart_dev` in admin/databases.py.
3. Take out anything you don't want converted. Save the Hive as `team_report.hql`, then run the convert Workflow on it as one batch in a new chat with file 13 loaded, with DEV filled in. Where the Hive and the checked code from the Workflow differ, the checked code wins.
4. If `ops.job_runs` or `ops.jobs` is partitioned, its Table reference will say so. The Toolbox code reads every partition of job_runs as the workbook does; if you want fewer days, replace that opt-out with a bound on dt.
