WITH runs_with_team AS (
  SELECT r.job_id, r.duration_mins, j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
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
