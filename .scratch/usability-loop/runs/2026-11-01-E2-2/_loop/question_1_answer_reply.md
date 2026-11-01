## Q1

Map first.

**Sources**
- `jobs`: typed columns job_id, job_name, team, region. The sheet's note says ops.jobs.
- `job_runs`: typed columns run_id, job_id, status, duration_mins, avg_retry_secs, dt. The sheet's note says ops.job_runs.

**Steps**
- `job_runs`'s `team` column, an XLOOKUP on `jobs`, read by `teams`. It becomes the CTE `job_runs` in the final's query, a LEFT JOIN of `jobs` that keeps every run.

**Finals**
- `teams`, written to mart_dev.team_report as you asked. Its columns, in order: team, runs, total_duration_mins.

**Values typed over a formula:** none. **Parameters:** none. **Keys:** none.

**Marks, converted and said so**
- Team rows: the usual rule for a summary like this is a GROUP BY of job_runs by team. That would drop web, which has no runs. So the team rows come from the distinct `team` of ops.jobs: data, finance, web, the same three teams the sheet types.
- Web shows 0 and 0. COUNTIFS and SUMIFS give 0 where nothing matches, so each is wrapped as COALESCE(..., 0). In the Toolbox code that is fill_null(..., 0).
- Blank cells: run 98 has a blank status and a blank avg_retry_secs. No formula reads either column, so they stay NULL and are not wrapped.
- Every run counts: COUNTIFS and SUMIFS have no status or date filter. TEST, FAILED and blank-status runs are counted too, as the sheet counts them.
- Every partition: the sheet's formulas read every run of job_runs, so the Toolbox code reads all partitions with `reads_all_partitions=True`, with a comment. A date bound would change the totals, so add one only if you want a day or a range.
- Key check: confirm that the Key of ops.jobs is job_id (file 02). If it is not, one run can match more than one job and the counts may come out too big.
- Names: the sheet's Table is named `teams`. The output is mart_dev.team_report, as you asked, so save the query as team_report.hql.
- Order: a Hive table holds no order, so the sheet's row order (data, finance, web) is not kept.

**Refused:** none.

**Left alone:** the Steps sheet (its instructions), the empty Parameters and Keys Tables, and the text notes F1 on jobs, I1 on job_runs and E1 on teams.

**Hive for the final, team_report** (fill in each `<database>` with ops, the database the sheet's notes name)

```sql
WITH job_runs AS (
  SELECT r.job_id, r.duration_mins, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
),
team_totals AS (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
),
teams AS (
  SELECT DISTINCT team
  FROM <database>.jobs
)
SELECT t.team,
  COALESCE(tt.runs, 0) AS runs,
  COALESCE(tt.total_duration_mins, 0) AS total_duration_mins
FROM teams t
LEFT JOIN team_totals tt ON t.team = tt.team
```

**Toolbox code** (files 03, 04 and 05). It needs references/ops__job_runs.py and references/ops__jobs.py in your Project. If you don't have them, make them with file 02.

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, SELECT_DISTINCT, count_rows,
                              derived, equals, fill_null, statement, sum_of)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

# The sheet's team formula on job_runs: XLOOKUP of job_id in jobs, so a LEFT_JOIN keeps every run.
# reads_all_partitions=True: the sheet's COUNTIFS and SUMIFS count every run, on every day.
runs_with_team = derived("runs_with_team", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins, jobs.team),
    FROM(job_runs, reads_all_partitions=True),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))

# The sheet's runs and total_duration_mins: COUNTIFS and SUMIFS by team over job_runs.
team_totals = derived("team_totals", statement(
    SELECT(runs_with_team.team,
           AS(count_rows(), "runs"),
           AS(sum_of(runs_with_team.duration_mins), "total_duration_mins")),
    FROM(runs_with_team),
    GROUP_BY(runs_with_team.team),
))

# The team rows come from ops.jobs, so web stays even though it has no runs.
teams = derived("teams", statement(
    SELECT_DISTINCT(jobs.team),
    FROM(jobs),
))

s = statement(
    SELECT(teams.team,
           AS(fill_null(team_totals.runs, 0), "runs"),
           AS(fill_null(team_totals.total_duration_mins, 0), "total_duration_mins")),
    FROM(teams),
    LEFT_JOIN(team_totals, ON=equals(team_totals.team, teams.team)),
)
```

**What to do next**
1. Take out anything you don't want. Nothing in this sheet is unwanted unless you want a team row out.
2. Fill in each `<database>` with ops.
3. Save the Hive above as team_report.hql.
4. Run the convert Workflow (file 13) on that file as one batch, with DEV filled in. Its checked code wins wherever it differs from the Toolbox code above.
