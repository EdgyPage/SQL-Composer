## Q1

**Map**

- Sources: `job_runs` (run_id, job_id, status, duration_mins, avg_retry_secs, dt) and `jobs` (job_id, job_name, team, region). Both are typed in the workbook, so each stands for a database table of its name.
- Steps: `job_runs` also has a formula column, `team` (an XLOOKUP into `jobs`), which Teams reads. It is a step: a CTE named `with_team` that LEFT JOINs `jobs`.
- Finals: `teams`, the Teams summary you named, for mart_dev.team_report. Its columns, in order: team, runs, total_duration_mins. Teams is a summary: its only typed column, team, is what its COUNTIFS and SUMIFS match on, so it is a GROUP BY of `job_runs`. Its team rows come from `team_list` (see the first mark below).

```sql
WITH with_team AS (
  SELECT r.job_id, r.duration_mins, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
),
per_team AS (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM with_team
  GROUP BY team
),
team_list AS (
  SELECT DISTINCT team
  FROM <database>.jobs
)
SELECT t.team,
  COALESCE(p.runs, 0) AS runs,
  COALESCE(p.total_duration_mins, 0) AS total_duration_mins
FROM team_list t
LEFT JOIN per_team p ON t.team = p.team
```

**Marks, converted and said**

- Team rows: Teams types three rows (data, finance, web). Web has no runs in the sample, since no run has job_id 4, so a GROUP BY over the runs alone would drop it and Excel would show 0. The team rows therefore come from the distinct teams in `jobs`, which here are these same three. The Toolbox has no name for typed rows, so this is the route. If a team is typed into Teams that `jobs` does not hold, it will be missing: add it to `jobs`, or load this file again with that sample.
- SUMIFS and COUNTIFS: each is COALESCE(.., 0), as Excel gives 0 where nothing matches. Web shows 0 runs and 0 minutes.
- XLOOKUP: it has no fourth argument, so Excel gives #N/A where no job matches. Hive gives NULL there, and a run with a NULL team matches no team row, so it is left out of Teams. The sample has no such run.
- Blanks: run 98 has a blank status and a blank avg_retry_secs. No formula reads either, so nothing is wrapped, and neither is in the query.
- Typed-over values: none. Every cell in team, runs and total_duration_mins is a formula, so Keys needs no row. Keys and Parameters are both empty.
- No day filter: the sample holds 2026-09-23 and 2026-09-24, but the Steps sheet filters by no day, so the final totals every row. The Toolbox code reads every row of both tables for that reason.

**Refused:** none.

**Total Row:** Teams has none, so there is no Total Row query.

**Left alone, and named:** the notes outside any Table: Runs A1, Jobs A1, Teams E1, Parameters D1 and Keys D1. None is read by the final.

**To fill in:** `<database>` in the Hive is `ops`, as the notes say (ops.job_runs and ops.jobs).

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, SELECT_DISTINCT,
                              count_rows, derived, equals, fill_null, statement, sum_of)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

# The workbook has no day filter, so each read takes every row of its table.
with_team = derived("with_team", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins, jobs.team),
    FROM(job_runs, reads_all_partitions=True),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), reads_all_partitions=True),
))

per_team = derived("per_team", statement(
    SELECT(with_team.team, AS(count_rows(), "runs"),
           AS(sum_of(with_team.duration_mins), "total_duration_mins")),
    FROM(with_team),
    GROUP_BY(with_team.team),
))

team_list = derived("team_list", statement(
    SELECT_DISTINCT(jobs.team),
    FROM(jobs, reads_all_partitions=True),
))

team_report = statement(
    SELECT(team_list.team,
           AS(fill_null(per_team.runs, 0), "runs"),
           AS(fill_null(per_team.total_duration_mins, 0), "total_duration_mins")),
    FROM(team_list),
    LEFT_JOIN(per_team, ON=equals(per_team.team, team_list.team)),
)
```

Take out anything you don't want converted: nothing in Teams needs taking out, and the columns of `job_runs` that Teams doesn't read (run_id, status, avg_retry_secs, dt) are left out of the query. Fill in `<database>` as ops.

The Table is named `teams`, but you asked for mart_dev.team_report. Rename the Table to `team_report` in Table Design (Excel updates any formula that reads it), then save the query as `team_report.hql`, named for its Table. Then run the convert Workflow on it as one batch, which is file 13. File 13 is not loaded in this chat, so load it in a new chat for the Workflow's steps, with DEV filled in: mart_dev, if that is your Dev database. Its checked code wins where the Hive above and the Toolbox code differ.
