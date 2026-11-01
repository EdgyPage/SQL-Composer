## Q1

**Map**

- Sources: `ops.job_runs` (typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt) and `ops.jobs` (job_id, job_name, team, region).
- Steps: `job_runs`. Its team column is a formula that the Table teams reads, so it is a CTE that reads `ops.job_runs` and joins `ops.jobs` for team.
- Finals: `teams`, with columns team, runs, total_duration_mins. Nothing reads teams, so it is a final. Its formulas are a GROUP BY of job_runs by team, with the three team names kept from teams' own rows.

```sql
WITH job_runs AS (
  SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, r.dt,
    j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
),
per_team AS (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
)
SELECT t.team,
  COALESCE(p.runs, 0) AS runs,
  COALESCE(p.total_duration_mins, 0) AS total_duration_mins
FROM (
  SELECT 'data' AS team
  UNION ALL SELECT 'finance'
  UNION ALL SELECT 'web'
) t
LEFT JOIN per_team p ON t.team = p.team
```

**Marks**

- teams' COUNTIFS and SUMIFS read job_runs, another Table, so they became a LEFT JOIN to per-team totals, with COALESCE(..., 0) as Excel gives 0 where nothing matches. The web team keeps its row with 0 runs and 0 minutes, as you asked.
- The three team names are typed in teams, so the Hive writes them as the query's own rows. The Toolbox code reads them from ops.jobs instead, which holds the same three names. If teams ever gets a team that Jobs lacks, change the Toolbox list to match.
- job_runs' formulas count every row, with no date, so the Hive reads every partition. The Toolbox code opts out of the partition bound with `reads_all_partitions=True`, and says why in a comment.
- team comes from an XLOOKUP on job_id. The LEFT JOIN gives NULL where no job matches, where Excel would give #N/A. Every job_id in the sample has a jobs row, so no row is affected.
- blank: row 98 has a blank status and a blank avg_retry_secs. No formula reads either column, so they stay NULL and get no COALESCE.
- Nothing was typed over a formula. The Parameters and Keys sheets are empty, so there are none. The Steps sheet is instructions, so it is not converted.
- This workbook has no Power Query, Total Rows or whole-column totals, so file 12 adds nothing here.
- Refused: none. Left alone: none.
- Each `<...>`: none is left. `<database>` is written as `ops`, as you asked. Check that `references.ops__job_runs` and `references.ops__jobs` are in your Project.
- On this sample, teams should give data 4 runs and 67 minutes, finance 5 runs and 113 minutes, and web 0 runs and 0 minutes.

**Toolbox code**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, SELECT_DISTINCT,
                              count_rows, derived, equals, fill_null, statement, sum_of)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

# The workbook's COUNTIFS and SUMIFS count every row of job_runs, with no date,
# so every partition is read on purpose.
team_runs = derived("job_runs", statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.status, job_runs.duration_mins,
           job_runs.avg_retry_secs, job_runs.dt, jobs.team),
    FROM(job_runs, reads_all_partitions=True),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))

# The three teams are teams' typed rows; Jobs holds the same three.
team_list = derived("team_list", statement(
    SELECT_DISTINCT(jobs.team),
    FROM(jobs),
))

per_team = derived("per_team", statement(
    SELECT(team_runs.team, AS(count_rows(), "runs"),
           AS(sum_of(team_runs.duration_mins), "total_duration_mins")),
    FROM(team_runs),
    GROUP_BY(team_runs.team),
))

s = statement(
    SELECT(team_list.team,
           AS(fill_null(per_team.runs, 0), "runs"),
           AS(fill_null(per_team.total_duration_mins, 0), "total_duration_mins")),
    FROM(team_list),
    LEFT_JOIN(per_team, ON=equals(per_team.team, team_list.team)),
)
```

Next, take out nothing, since all three teams are wanted. Save the Hive above as `teams.hql`, then run the convert Workflow on it as one batch (file 13), with DEV set to `ops`. Where the checked code differs from these, the checked code wins.
