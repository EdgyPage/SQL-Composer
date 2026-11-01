## Q1

**Map**

- Sources: `jobs` (typed columns, so `<database>.jobs`) and `job_runs` (typed columns, so `<database>.job_runs`).
- Steps: `job_runs`. Its formula column `team` (an XLOOKUP into `jobs`) is read by `team_runs`, so `job_runs` is a step, and each final that reads it carries it as a CTE.
- Finals: `job_costs` (columns `job_id`, `cost_cents`) and `team_runs` (columns `team`, `runs`). Each is a summary: its typed column is what its SUMIFS or COUNTIFS match on (`job_id` and `team`), so each is a GROUP BY of `job_runs`, with its typed rows kept as a list.
- Parameters and Keys: none, as file 11 says. The Keys row for `job_costs` (job_id) is used for the typed value below.

**Typed over a formula**

- `job_costs`, `cost_cents` where `job_id` is 3: 1000, matched on `job_id` (Keys row: job_costs, job_id).

**Marks**

- `cents_a_minute` is read through `XLOOKUP` into Parameters, so it is written in as its value, 50.
- SUMIFS and COUNTIFS over `job_runs` become a LEFT JOIN to a GROUP BY, with COALESCE(..., 0), as Excel gives 0 where nothing matches. Job 4 has no runs, and the web team has none, so both come out 0.
- The rows of each summary are written as they are typed: job ids 1 to 4 for `job_costs`, and the teams data, finance and web for `team_runs`.
- COUNTIFS counts every run, TEST and FAILED rows included, as the workbook does. No status or date filter is added, as no formula has one and the rows are a sample.
- Blank: row 98 of `job_runs` holds None in `status` and `avg_retry_secs`. No final reads those columns, so nothing is wrapped.

**Refusals**

- None.

**Left alone, and named**

- The notes in D1 of `job_costs` and of `team_runs`, outside their Tables.
- The notes in A1 of `jobs` and `job_runs` ("Copied from ops.jobs..." and "Copied from ops.job_runs..."), outside their Tables. They show the database is ops.
- The text on the Steps sheet.
- No charts or PivotTables.

**To fill in**

- `<database>` in the Hive, in both `<database>.job_runs` and `<database>.jobs`. Its name is ops, from the notes.

**job_costs**

```sql
WITH job_runs AS (
  SELECT job_id, duration_mins
  FROM <database>.job_runs
)
SELECT c.job_id,
  CASE WHEN c.job_id = 3 THEN 1000 ELSE COALESCE(m.total_minutes, 0) * 50 END AS cost_cents
FROM (SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) c
LEFT JOIN (SELECT job_id, SUM(duration_mins) AS total_minutes
           FROM job_runs
           GROUP BY job_id) m ON c.job_id = m.job_id
```

**team_runs**

```sql
WITH job_runs AS (
  SELECT r.job_id, r.duration_mins, j.team
  FROM <database>.job_runs r
  LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
)
SELECT t.team, COALESCE(c.runs, 0) AS runs
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN (SELECT team, COUNT(*) AS runs
           FROM job_runs
           GROUP BY team) c ON t.team = c.team
```

**Toolbox code**

The Python needs the Table references `references/ops__job_runs.py` and `references/ops__jobs.py` in your Project. If you don't have them yet, file 02 adds them. The database is ops, from the notes.

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, SELECT_DISTINCT, count_rows,
                              derived, equals, fill_null, if_else, statement, sum_of)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

# The workbook's formulas read every row of job_runs, as its sample does, so no day bound.
runs = derived("runs", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins, jobs.team),
    FROM(job_runs, reads_all_partitions=True),
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))

# job_costs: each job's minutes times 50 (cents_a_minute), with job 3 typed in as 1000.
minutes = derived("minutes", statement(
    SELECT(runs.job_id, AS(sum_of(runs.duration_mins), "total_minutes")),
    FROM(runs),
    GROUP_BY(runs.job_id),
))
job_costs = statement(
    SELECT(jobs.job_id,
           AS(if_else(equals(jobs.job_id, 3), 1000,
                      fill_null(minutes.total_minutes, 0) * 50), "cost_cents")),
    FROM(jobs),
    LEFT_JOIN(minutes, ON=equals(minutes.job_id, jobs.job_id)),
)

# team_runs: each team of ops.jobs with its runs, 0 for a team with none.
teams = derived("teams", statement(
    SELECT_DISTINCT(jobs.team),
    FROM(jobs),
))
per_team = derived("per_team", statement(
    SELECT(runs.team, AS(count_rows(), "runs")),
    FROM(runs),
    GROUP_BY(runs.team),
))
team_runs = statement(
    SELECT(teams.team, AS(fill_null(per_team.runs, 0), "runs")),
    FROM(teams),
    LEFT_JOIN(per_team, ON=equals(per_team.team, teams.team)),
)
```

**To finish**

Take out anything you don't want converted. Fill in each `<database>` in the Hive. Save the two queries as `job_costs.hql` and `team_runs.hql`, and run the convert Workflow on them as one batch (file 13), with DEV filled in. Where the Toolbox code and the Hive differ, the checked code wins. The Toolbox takes the job ids and team names from ops.jobs, which hold the same four ids and three teams in this sample, while the Hive lists them as typed.
