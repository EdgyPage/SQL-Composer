## Q1

**Map**

- Sources: `jobs` (from ops.jobs) and `job_runs` (from ops.job_runs). Their typed columns stand for the database tables.
- Steps: `job_runs` with `team`. Its formula column `team` is an XLOOKUP into `jobs`, and `teams` reads it, so it becomes a CTE inside the `teams` query.
- Finals: `teams`, giving the columns team, runs, total_duration_mins. Its only typed column, `team`, is what its COUNTIFS and SUMIFS match on, so it is a summary: a GROUP BY of `job_runs`.
- Parameters and Keys are empty, so there is nothing to convert from them. No value is typed over a formula, and there is no Total Row.

**Hive for `teams`**

```sql
WITH runs_with_team AS (
  SELECT r.job_id, r.duration_mins, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
),
totals AS (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM runs_with_team
  GROUP BY team
),
team_names AS (
  SELECT 'data' AS team
  UNION ALL SELECT 'finance'
  UNION ALL SELECT 'web'
)
SELECT n.team,
  COALESCE(t.runs, 0) AS runs,
  COALESCE(t.total_duration_mins, 0) AS total_duration_mins
FROM team_names n
LEFT JOIN totals t ON n.team = t.team
```

**Toolbox code for `teams`**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, SELECT_DISTINCT, count_rows,
                              derived, equals, fill_null, statement, sum_of)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

# The step: each run with its job's team, as the formula team reads it.
runs_with_team = derived("runs_with_team", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins, jobs.team),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))

# The group totals per team, from the step.
totals = derived("totals", statement(
    SELECT(runs_with_team.team, AS(count_rows(), "runs"),
           AS(sum_of(runs_with_team.duration_mins), "total_duration_mins")),
    FROM(runs_with_team),
    GROUP_BY(runs_with_team.team),
))

# The team names the Table holds. The Toolbox has no literal rows, so they come from jobs.
team_names = derived("team_names", statement(
    SELECT_DISTINCT(jobs.team),
    FROM(jobs),
))

s = statement(
    SELECT(team_names.team,
           AS(fill_null(totals.runs, 0), "runs"),
           AS(fill_null(totals.total_duration_mins, 0), "total_duration_mins")),
    FROM(team_names),
    LEFT_JOIN(totals, ON=equals(totals.team, team_names.team)),
)
```

**Marks, and what to check**

- Summary rows: the teams Table holds data, finance and web. No run in the sample belongs to web (its job, cache_warm, has no runs), so a GROUP BY alone would drop that row. The Hive lists the three names and LEFT JOINs the group totals onto them, and COALESCE gives web 0 runs and 0 minutes, as Excel does.
- Team names: the Hive lists the names as the Table holds them. The Toolbox code reads the distinct teams from `jobs` instead, because the Toolbox cannot write literal rows. On this sample the two give the same three teams. If they ever differ, the Hive list is the Table's own.
- Blank cells: run 98's status and avg_retry_secs are blank. No formula reads either, so they stay NULL and are not wrapped.
- Run 99 has status TEST. The formula doesn't filter on status, so the query counts it too.
- Dates: `job_runs` is partitioned by dt. The summary covers every row of the sample, so the query reads every partition, and no date filter is added. To cover a range of days, add a bound on `job_runs.dt` to the step (in the Hive's job_runs step, and with `equals` or `between` in the Toolbox FROM), and drop `reads_all_partitions=True`.
- Lookup: the LEFT JOIN to `jobs` matches the XLOOKUP on this sample, where every job_id is in `jobs`. A job_id missing from `jobs` gives NULL here, where Excel gives #N/A.
- Expected result on the sample, to check against the Excel: data 4 runs and 67 minutes; finance 5 runs and 113 minutes; web 0 and 0.

**Refused**

Nothing. XLOOKUP, COUNTIFS and SUMIFS all convert.

**Left alone**

The Steps sheet and the notes in A1 and D1 of each sheet, which are outside a Table.

**To fill in**

- `<database>` in the Hive: two places, `<database>.job_runs` and `<database>.jobs`. The notes say ops, so write `ops`.
- The Toolbox code needs the Table references `references/ops__job_runs.py` and `references/ops__jobs.py` in your Project (file 02).

**Next steps**

Take out what you don't want, fill in `<database>`, and save the `teams` query as `teams.hql`. Then run the convert Workflow on that file as one batch (file 13), with DEV filled in. Where its checked code differs from the Hive or Toolbox code above, its checked code wins.
