## Q1

**Map**

- Sources: `ops.jobs` (Table jobs: job_id, job_name, team, region; read for job_id and team) and `ops.job_runs` (Table job_runs: run_id, job_id, status, duration_mins, avg_retry_secs, dt; read for job_id and duration_mins).
- Steps: job_runs. Its team column is an XLOOKUP of jobs by job_id, and job_costs and team_runs both read it, so it is a step: a CTE named `runs` in each final's query.
- Finals: job_costs (job_id, cost_cents) and team_runs (team, runs). Each is a GROUP BY summary of runs (SUMIFS and COUNTIFS match on job_id and team).
- Parameters and Keys: none as Tables. Keys is read only for job_costs.

**Typed over a formula**

- job_costs, cost_cents, job_id 3: typed as 1000. Matched on its Keys row (job_costs, job_id), so only job 3 changes. The formula would give 3000 (60 minutes times 50). Converted as typed.
- team_runs: nothing typed over.

**Marks**

- Parameters: cents_a_minute is 50. Both SUMIFS formulas read it by XLOOKUP, so it is written in as its value, 50. If the rate changes, change the 50 in job_costs.
- Rows: job_costs takes its rows from ops.jobs (jobs 1 to 4), and team_runs takes its rows from the distinct teams of ops.jobs (data, finance, web), the same rows as the typed columns. A GROUP BY alone would drop job 4 and the web team, which have no runs in the sample, so they are kept at 0, as Excel gives 0 where nothing matches.
- Partitions: ops.job_runs is partitioned by dt. The workbook's formulas read every row of its sample, so the Hive reads every partition with no dt bound. If you want one day or a range, say so and I will add the bound. The Toolbox code opts out with `reads_all_partitions=True` for the same reason.
- Blanks: none. Row 98 has "None" in status and avg_retry_secs, but no final reads those columns, so nothing is wrapped.
- Dates: 2026-09-23 and 2026-09-24 are both kept. No formula filters on dt, so no filter is written.

**Refused**

- None. No formula here is on the refused list.

**Left alone, and named**

- The text on the Steps sheet, and the notes in F1 (Jobs), H1 (Runs), D1 (Parameters), D1 (Keys), D1 (Job costs) and D1 (Team runs). None is inside a Table.
- No charts and no PivotTables.

**To fill in**

- Nothing in the Hive: the database is ops, as you asked.
- The Toolbox code needs two Table references, references/ops__jobs.py and references/ops__job_runs.py, made by the references Workflow (file 02).

**Hive**

job_costs:

```sql
WITH runs AS (
  SELECT r.job_id, r.duration_mins
  FROM ops.job_runs r
),
run_totals AS (
  SELECT job_id, SUM(duration_mins) AS total_mins
  FROM runs
  GROUP BY job_id
)
SELECT j.job_id,
  CASE WHEN j.job_id = 3 THEN 1000
    ELSE COALESCE(t.total_mins, 0) * 50
  END AS cost_cents
FROM ops.jobs j
LEFT JOIN run_totals t ON j.job_id = t.job_id
```

team_runs:

```sql
WITH runs AS (
  SELECT r.job_id, r.duration_mins, j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
),
run_counts AS (
  SELECT team, COUNT(*) AS runs
  FROM runs
  GROUP BY team
),
teams AS (
  SELECT DISTINCT team FROM ops.jobs
)
SELECT t.team, COALESCE(c.runs, 0) AS runs
FROM teams t
LEFT JOIN run_counts c ON t.team = c.team
```

**Toolbox code**

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, SELECT_DISTINCT, count_rows,
                              derived, equals, fill_null, first_match, statement, sum_of)
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

# job_runs as a step: its duration, and the team looked up from jobs (XLOOKUP).
# The workbook's formulas read every row, so every partition is read.
runs = derived("runs", statement(
    SELECT(job_runs.job_id, job_runs.duration_mins, jobs.team),
    FROM(job_runs, reads_all_partitions=True),  # the workbook's formulas read every row
    LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
))

# job_costs: each job's minutes times 50 (cents_a_minute), 0 where it has no runs.
# Rows are the jobs in ops.jobs; job 3 is typed over as 1000 (Keys: job_id).
run_totals = derived("run_totals", statement(
    SELECT(runs.job_id, AS(sum_of(runs.duration_mins), "total_mins")),
    FROM(runs),
    GROUP_BY(runs.job_id),
))
job_costs = statement(
    SELECT(jobs.job_id,
           AS(first_match([(equals(jobs.job_id, 3), 1000)],
                          otherwise=fill_null(run_totals.total_mins, 0) * 50), "cost_cents")),
    FROM(jobs),
    LEFT_JOIN(run_totals, ON=equals(run_totals.job_id, jobs.job_id)),
)

# team_runs: the runs of each team, 0 for a team with none. Teams are ops.jobs' teams.
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

Take out anything you don't want. Nothing needs filling in. Save each final's query as a .hql file named for its Table, job_costs.hql and team_runs.hql, and run the convert Workflow on them as one batch (file 13), DEV filled in. If the Hive and the Toolbox code differ, the Toolbox code, once the Toolbox has checked it, wins.
