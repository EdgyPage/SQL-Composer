WITH with_team AS (
  SELECT r.job_id, r.duration_mins, j.team
  FROM ops.job_runs r
  LEFT JOIN ops.jobs j ON r.job_id = j.job_id
),
per_team AS (
  SELECT team, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM with_team
  GROUP BY team
),
team_list AS (
  SELECT DISTINCT team
  FROM ops.jobs
)
SELECT t.team,
  COALESCE(p.runs, 0) AS runs,
  COALESCE(p.total_duration_mins, 0) AS total_duration_mins
FROM team_list t
LEFT JOIN per_team p ON t.team = p.team
