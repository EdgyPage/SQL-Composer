WITH job_runs AS (
  SELECT r.job_id, r.duration_mins, j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
),
team_totals AS (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM job_runs
  GROUP BY team
),
teams AS (
  SELECT DISTINCT team
  FROM ops.jobs
)
SELECT t.team,
  COALESCE(tt.runs, 0) AS runs,
  COALESCE(tt.total_duration_mins, 0) AS total_duration_mins
FROM teams t
LEFT JOIN team_totals tt ON t.team = tt.team
