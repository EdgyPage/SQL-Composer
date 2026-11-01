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
LEFT JOIN run_counts c ON t.team = c.team;
